"""
FastAPI micro-service that exposes real cost data to the React frontend.

Run standalone:  uvicorn cost_api:app --port 8090 --reload
Or integrate into the main NiceGUI app as a mounted sub-app.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from cost_tracker import tracker

TEMPLATES_DIR = Path("./templates/models")
UPLOADS_DIR   = Path("./uploads")
FRONTEND_DIST = Path("./frontend/dist")
UPLOADS_DIR.mkdir(exist_ok=True)


def _slug(name: str) -> str:
    """Converte nome de empresa em slug seguro para pasta."""
    s = name.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "_", s)
    return s[:60] or "empresa"


def _find_template(filename: str) -> Path | None:
    """Busca arquivo de template recursivamente em todas as subpastas."""
    if not TEMPLATES_DIR.exists():
        return None
    for f in TEMPLATES_DIR.rglob(filename):
        if f.is_file():
            return f
    return None

app = FastAPI(title="IB-Agents Cost API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/costs")
def get_costs():
    """Full cost dashboard payload."""
    return tracker.get_dashboard_data()


@app.get("/api/costs/by-agent")
def get_costs_by_agent():
    return tracker.get_cost_by_agent()


@app.get("/api/costs/by-operation")
def get_costs_by_operation():
    return tracker.get_cost_by_operation()


@app.get("/api/costs/timeline")
def get_costs_timeline():
    return tracker.get_cost_timeline()


@app.get("/api/costs/session")
def get_current_session():
    return tracker.get_session_summary()


@app.get("/api/costs/calls")
def get_all_calls():
    """Raw call log — all LLM calls recorded."""
    return tracker.get_all_calls()


@app.post("/api/costs/rate")
def set_usd_brl(rate: float):
    """Update USD→BRL exchange rate."""
    tracker.set_usd_brl(rate)
    return {"usd_brl_rate": rate}


# ── Template Downloads ────────────────────────────────────────────────────────

MEDIA_TYPES = {
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pdf":  "application/pdf",
}

FOLDER_LABELS = {
    "pitch_books":     "Pitch Books",
    "financial_models":"Modelos Financeiros",
    "memos_reports":   "Memos & Reports",
    "term_sheets":     "Term Sheets",
    "pareceres":       "Pareceres de Credito",
}


@app.get("/api/templates")
def list_templates():
    """Lista todos os templates recursivamente, com categoria (subfolder)."""
    if not TEMPLATES_DIR.exists():
        return []
    results = []
    for f in sorted(TEMPLATES_DIR.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(TEMPLATES_DIR)
        parts = rel.parts
        category = FOLDER_LABELS.get(parts[0], parts[0]) if len(parts) > 1 else "Geral"
        results.append({
            "filename":  f.name,
            "category":  category,
            "subfolder": parts[0] if len(parts) > 1 else "",
            "size_kb":   round(f.stat().st_size / 1024, 1),
            "format":    f.suffix.upper().strip("."),
        })
    return results


@app.get("/api/templates/download/{filename}")
def download_template(filename: str):
    """Download de template — busca recursiva em todas as subpastas."""
    filepath = _find_template(filename)
    if filepath is None:
        raise HTTPException(status_code=404, detail=f"Template '{filename}' nao encontrado.")
    return FileResponse(
        path=str(filepath),
        filename=filename,
        media_type=MEDIA_TYPES.get(filepath.suffix, "application/octet-stream"),
    )


# ── Uploads por Analise ───────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    company: str = Form("empresa"),
):
    """
    Salva o arquivo em uploads/{slug_empresa}/.
    Cria a pasta automaticamente se nao existir.
    """
    slug = _slug(company)
    dest_dir = UPLOADS_DIR / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Sanitiza nome do arquivo
    safe_name = re.sub(r"[^\w.\-]", "_", file.filename or "arquivo")
    dest = dest_dir / safe_name

    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    return {
        "ok":      True,
        "company": company,
        "folder":  str(dest_dir),
        "file":    safe_name,
        "size_kb": round(dest.stat().st_size / 1024, 1),
    }


@app.get("/api/upload/{company}")
def list_uploads(company: str):
    """Lista os arquivos salvos na pasta de uma empresa."""
    slug = _slug(company)
    folder = UPLOADS_DIR / slug
    if not folder.exists():
        return {"company": company, "files": []}
    return {
        "company": company,
        "folder":  str(folder),
        "files": [
            {"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)}
            for f in sorted(folder.iterdir()) if f.is_file()
        ],
    }


@app.get("/api/uploads")
def list_all_uploads():
    """Lista todas as pastas de empresa criadas em uploads/."""
    if not UPLOADS_DIR.exists():
        return []
    return [
        {
            "company_slug": d.name,
            "files": [f.name for f in sorted(d.iterdir()) if f.is_file()],
            "count": sum(1 for f in d.iterdir() if f.is_file()),
        }
        for d in sorted(UPLOADS_DIR.iterdir()) if d.is_dir()
    ]


# ── Chat com MD Orchestrator (Claude API) ─────────────────────────────────────

import os
import anthropic as _anthropic

MD_SYSTEM_PROMPT = """Voce e o MD Orchestrator — Managing Director Senior com 20 anos de experiencia em investment banking no Brasil, tendo liderado mais de 500 transacoes de DCM e ECM.

Sua personalidade: direto, preciso, exigente com qualidade. Voce coordena um time de agentes de IA especializados (Contador, Juridico, Research Analyst, Financial Modeler, DCM Specialist, ECM Specialist, Quant Analyst, Risk & Compliance, Deck Builder).

Pipeline que voce supervisiona:
- Etapa 1: Contador (revisao de DFs em XLSX) + Legal Advisor (Due Diligence em PDF) — em paralelo
- Etapa 2: Research Analyst (Relatorio de Research em PDF)
- Etapa 3: Financial Modeler (Modelagem Financeira em XLSX — padrao VCA)
- Etapa 4: DCM/ECM Specialist + Quant Analyst + Risk & Compliance + Juridico (Relatorio de Viabilidade em XLSX+PPT) — em paralelo
- Etapa 5: Deck Builder (Book de Credito / CIM / Teaser em PPT)

Responda sempre em portugues brasileiro, de forma objetiva e institucional. Quando nao souber algo especifico do contexto do usuario, peca mais detalhes antes de opinar. Mantenha o padrao de qualidade de um MD de banco de investimento de primeira linha."""


@app.post("/api/chat")
async def chat_with_md(payload: dict):
    """Chat com MD Orchestrator via Claude API."""
    try:
        client = _anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        history = payload.get("messages", [])
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=MD_SYSTEM_PROMPT,
            messages=history,
        )
        return {"text": response.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── React SPA — serve o build do Vite em producao ────────────────────────────

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")
    app.mount("/knowledge", StaticFiles(directory=str(FRONTEND_DIST / "knowledge")), name="knowledge")

    @app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
    def serve_spa(full_path: str):
        """Catch-all: redireciona qualquer rota desconhecida para o index.html do React."""
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return HTMLResponse(content=index.read_text(encoding="utf-8"))
        return HTMLResponse(content="Frontend nao encontrado. Execute: cd frontend && npm run build", status_code=404)
