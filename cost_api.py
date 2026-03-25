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


def _extract_file_text(path: Path) -> str:
    """Extract readable text from an uploaded file, max 5000 chars."""
    suffix = path.suffix.lower()
    try:
        if suffix in ('.xlsx', '.xls'):
            import openpyxl
            wb = openpyxl.load_workbook(path, data_only=True)
            lines = []
            for sheet_name in wb.sheetnames[:6]:
                ws = wb[sheet_name]
                lines.append(f"[Planilha: {sheet_name}]")
                for row in ws.iter_rows(max_row=80, values_only=True):
                    vals = [str(c) for c in row if c is not None and str(c).strip()]
                    if vals:
                        lines.append(' | '.join(vals))
            return '\n'.join(lines)[:5000]
        elif suffix == '.pdf':
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                pages = [p.extract_text() or '' for p in reader.pages[:15]]
                return '\n'.join(pages)[:5000]
            except Exception:
                return f"[PDF {path.name}: extracao indisponivel]"
        elif suffix in ('.pptx', '.ppt'):
            from pptx import Presentation
            prs = Presentation(str(path))
            lines = []
            for slide in prs.slides[:20]:
                for shape in slide.shapes:
                    if hasattr(shape, 'text') and shape.text.strip():
                        lines.append(shape.text.strip())
            return '\n'.join(lines)[:5000]
        elif suffix in ('.txt', '.csv', '.md'):
            return path.read_text(encoding='utf-8', errors='ignore')[:5000]
        else:
            return f"[{path.name}: tipo {suffix} sem suporte a extracao de texto]"
    except Exception as e:
        return f"[{path.name}: erro — {str(e)[:120]}]"


AGENT_PROMPTS = {
    "accountant": """Voce e o Contador do time de Investment Banking — especialista em IFRS, CVM e analise de demonstracoes financeiras corporativas.

Sua tarefa: revisar as demonstracoes financeiras da empresa, normalizar EBITDA, identificar ajustes IFRS 16, destacar distorcoes e avaliar qualidade do resultado reportado. Analise receita, custos, capital de giro, alavancagem e covenants. Seja objetivo e direto, como um colega senior de banco.""",

    "legal_advisor": """Voce e o Legal Advisor do time de Investment Banking — especialista em direito societario, CVM, ANBIMA e estruturacao de operacoes de mercado de capitais.

Sua tarefa: conduzir due diligence juridica — revisar documentos societarios, contratos relevantes, contingencias, garantias e compliance regulatorio. Identifique e hierarquize os riscos juridicos relevantes para a operacao.""",

    "research_analyst": """Voce e o Research Analyst do time de Investment Banking. Sua funcao e elaborar dossies analiticos sobre empresas para alimentar o pipeline interno de estruturacao.

Sua tarefa: elaborar um relatorio de research corporativo — perfil da empresa, posicionamento setorial, analise de mercado, principais drivers e riscos, historico financeiro e perspectivas de crescimento.""",

    "financial_modeler": """Voce e o Financial Modeler do time de Investment Banking — especialista em modelagem DCF, LBO, precedent transactions e modelos de credito.

Sua tarefa: estruturar a modelagem financeira da operacao — projecoes de receita, EBITDA, capex, free cash flow, metricas de credito (Divida/EBITDA, cobertura de juros), e indicadores de valuation.""",

    "dcm_specialist": """Voce e o DCM Specialist (Debt Capital Markets) do time de Investment Banking.

Sua tarefa: elaborar o relatorio de viabilidade para a operacao de divida — estrutura da emissao, pricing indicativo (spread vs benchmarks), analise do mercado de credito, comparativos de emissoes recentes, condicoes e prazos recomendados.""",

    "ecm_specialist": """Voce e o ECM Specialist (Equity Capital Markets) do time de Investment Banking.

Sua tarefa: elaborar o relatorio de viabilidade para a oferta de acoes — janela de mercado, indicativo de preco/faixa, valuation por multiplos e DCF, comparativos de ofertas recentes, estrutura recomendada (primaria/secundaria).""",

    "risk_compliance": """Voce e o Risk & Compliance Officer do time de Investment Banking.

Sua tarefa: revisar os riscos regulatorios e de compliance da operacao — adequacao a normas CVM/ANBIMA, riscos de mercado, credito e liquidez, covenants recomendados, exposicoes relevantes e mitigacoes propostas.""",

    "deck_builder": """Voce e o Deck Builder do time de Investment Banking — especialista em materiais de distribuicao para investidores institucionais.

Sua tarefa: estruturar o roteiro e conteudo do material de distribuicao (Book de Credito, CIM ou Teaser) — sumario executivo, tese de investimento, posicionamento competitivo, financeiros-chave e termos da operacao.""",

    "quant_analyst": """Voce e o Quant Analyst do time de Investment Banking — especialista em quantificacao de risco, pricing de ativos e modelagem estatistica.

Sua tarefa: realizar analise quantitativa da operacao — pricing de risco, simulacoes de cenario, analise de sensibilidade, metricas de risco de credito e de mercado.""",
}


@app.post("/api/run-agent-task")
async def run_agent_task(payload: dict):
    """Executa um agente especifico em uma tarefa de pipeline."""
    try:
        agent_id = payload.get("agent_id", "")
        operation = payload.get("operation", {})
        file_context = payload.get("file_context", "")
        task_title = payload.get("task_title", "")
        additional_context = payload.get("additional_context", "")

        base_prompt = AGENT_PROMPTS.get(agent_id, MD_SYSTEM_PROMPT)

        op_summary = f"""
OPERACAO SENDO ANALISADA:
- Empresa: {operation.get('company', 'N/D')}
- Tipo: {operation.get('type', 'N/D')} — {operation.get('instrument', operation.get('opType', 'N/D'))}
- Valor estimado: R$ {operation.get('value', 'N/D')}
- Setor: {operation.get('sector', 'N/D')}
- Rating atual: {operation.get('rating', 'N/D')}
- Prazo: {operation.get('deadline', 'N/D')} meses
- Garantias: {', '.join(operation.get('guarantees', [])) or 'Nao informadas'}
- Tarefa atual: {task_title}
{f'- Instrucoes adicionais: {additional_context}' if additional_context else ''}
"""

        file_section = (
            f"\n\nDOCUMENTOS DISPONÍVEIS PARA ANÁLISE:\n{file_context}"
            if file_context
            else "\n\nNenhum documento enviado ainda. Conduza a analise com base nas informacoes da operacao e liste os documentos especificos que precisaria para aprofundar."
        )

        system = base_prompt + op_summary + file_section + CHAT_FORMAT_RULES

        client = _anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": f"Execute sua tarefa: {task_title}"}],
        )
        return {"text": response.content[0].text, "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files-context/{company}")
def get_files_context(company: str):
    """Return extracted text from all uploaded files for a company."""
    slug = _slug(company)
    folder = UPLOADS_DIR / slug
    if not folder.exists():
        return {"context": "", "files": []}
    results = []
    for f in sorted(folder.iterdir()):
        if f.is_file():
            content = _extract_file_text(f)
            results.append({"name": f.name, "content": content})
    context = "\n\n".join(f"=== {r['name']} ===\n{r['content']}" for r in results)
    return {"context": context[:20000], "files": [r["name"] for r in results]}


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

CHAT_FORMAT_RULES = """

REGRAS DE FORMATO PARA ESTE CHAT (obrigatorio, sem excecoes):
- Escreva de forma conversacional e fluida, como uma troca direta entre colegas senior de um banco de investimento.
- NUNCA use titulos markdown (##, ###, ####), linhas horizontais (---) ou tabelas markdown.
- NUNCA use blockquotes (>) nem itens em negrito excessivo para estruturar a resposta.
- Use paragrafos curtos e diretos. Listas com hifen simples apenas quando realmente necessario.
- Nao assine a mensagem ao final.
- Tom: direto, objetivo, profissional — como uma mensagem no chat de trabalho, nao um relatorio formal."""

MD_SYSTEM_PROMPT = """Voce e o MD Orchestrator — Managing Director Senior com 20 anos de experiencia em investment banking no Brasil, tendo liderado mais de 500 transacoes de DCM e ECM.

Sua personalidade: direto, preciso, exigente com qualidade. Voce coordena um time de agentes de IA especializados (Contador, Juridico, Research Analyst, Financial Modeler, DCM Specialist, ECM Specialist, Quant Analyst, Risk & Compliance, Deck Builder).

Pipeline que voce supervisiona:
- Etapa 1: Contador (revisao de DFs em XLSX) + Legal Advisor (Due Diligence em PDF) — em paralelo
- Etapa 2: Research Analyst (Relatorio de Research em PDF)
- Etapa 3: Financial Modeler (Modelagem Financeira em XLSX — padrao VCA)
- Etapa 4: DCM/ECM Specialist + Quant Analyst + Risk & Compliance + Juridico (Relatorio de Viabilidade em XLSX+PPT) — em paralelo
- Etapa 5: Deck Builder (Book de Credito / CIM / Teaser em PPT)

Responda sempre em portugues brasileiro, de forma objetiva e institucional. Quando nao souber algo especifico do contexto do usuario, peca mais detalhes antes de opinar. Mantenha o padrao de qualidade de um MD de banco de investimento de primeira linha.""" + CHAT_FORMAT_RULES


@app.post("/api/chat")
async def chat_with_md(payload: dict):
    """Chat com MD Orchestrator via Claude API."""
    try:
        client = _anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        history = payload.get("messages", [])
        base_prompt = payload.get("system_prompt") or MD_SYSTEM_PROMPT
        ops_context = payload.get("operations_context", "")
        system = base_prompt + (ops_context if ops_context else "") + CHAT_FORMAT_RULES
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
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
