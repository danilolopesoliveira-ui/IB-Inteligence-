"""
ingest_knowledge.py
Processa e indexa os modelos de referência na base de conhecimento RAG.

Uso:
    py ingest_knowledge.py                    # Indexa tudo em knowledge/references/
    py ingest_knowledge.py --list             # Lista o que já está indexado
    py ingest_knowledge.py --reset            # Apaga e reindexar do zero
    py ingest_knowledge.py --file arquivo.pdf # Indexa um arquivo específico
    py ingest_knowledge.py --search "query"   # Testa uma busca
"""

from __future__ import annotations

import sys
import types
import logging
from pathlib import Path
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Stubs para rodar sem crewai instalado
# ---------------------------------------------------------------------------
class _AutoMock(types.ModuleType):
    def __getattr__(self, name):
        m = MagicMock(); setattr(self, name, m); return m

for mod in ["crewai", "crewai.tools", "crewai_tools",
            "sentence_transformers", "plotly", "plotly.graph_objects",
            "plotly.io", "pdfplumber", "camelot"]:
    if mod not in sys.modules:
        sys.modules[mod] = _AutoMock(mod)

from pydantic import BaseModel as _BaseModel
class _BaseTool(_BaseModel):
    name: str = ""; description: str = ""; args_schema: type = type(None)
    model_config = {"arbitrary_types_allowed": True}
    def _run(self, *a, **kw): raise NotImplementedError

_tools_mod = types.ModuleType("crewai.tools")
_tools_mod.BaseTool = _BaseTool
_tools_mod.tool = lambda f: f
_crewai_mod = types.ModuleType("crewai")
_crewai_mod.tools = _tools_mod
sys.modules["crewai"] = _crewai_mod
sys.modules["crewai.tools"] = _tools_mod

loguru_mod = types.ModuleType("loguru")
loguru_mod.logger = logging.getLogger("ingest")
sys.modules["loguru"] = loguru_mod

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

REFERENCES_DIR = PROJECT_ROOT / "knowledge" / "references"
BASE_DIR = PROJECT_ROOT / "knowledge" / "base"


def cmd_ingest(file_arg: str = ""):
    from tools.knowledge.ingestor import KnowledgeIngestor
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
    from rich.panel import Panel

    console = Console()
    ingestor = KnowledgeIngestor()

    if file_arg:
        path = Path(file_arg)
        if not path.exists():
            console.print(f"[red]Arquivo não encontrado: {file_arg}[/red]")
            sys.exit(1)
        console.print(f"Indexando: [cyan]{path.name}[/cyan]")
        n = ingestor.ingest_file(str(path))
        console.print(f"[green]✓ {n} chunks indexados.[/green]")
        return

    if not REFERENCES_DIR.exists():
        console.print(f"[red]Pasta não encontrada: {REFERENCES_DIR}[/red]")
        sys.exit(1)

    # Count files — varre references/ e base/
    supported = {".pdf", ".xlsx", ".xls", ".docx", ".txt", ".md"}
    scan_dirs = [REFERENCES_DIR]
    if BASE_DIR.exists():
        scan_dirs.append(BASE_DIR)

    def _collect(dirs):
        modelo, resto = [], []
        for d in dirs:
            for f in d.rglob("*"):
                if f.suffix.lower() not in supported: continue
                if f.name.startswith(".") or f.name.startswith("~"): continue
                if f.name == "LEIA-ME.txt": continue
                if "Modelo" in f.parts:
                    modelo.append(f)
                else:
                    resto.append(f)
        # Arquivos da pasta Modelo vêm primeiro (prioridade de indexação)
        return modelo + resto

    all_files = _collect(scan_dirs)

    if not all_files:
        console.print(Panel(
            "[yellow]Nenhum arquivo encontrado em:[/yellow]\n"
            f"[cyan]{REFERENCES_DIR}[/cyan]\n\n"
            "Coloque seus modelos de referência nas subpastas:\n"
            "  • [cyan]pitch_books/[/cyan]      — PDFs de pitch books\n"
            "  • [cyan]financial_models/[/cyan]  — Excel de modelos financeiros\n"
            "  • [cyan]research_reports/[/cyan]  — Research reports e memos\n\n"
            "Depois execute novamente: [bold]py ingest_knowledge.py[/bold]",
            title="Base de conhecimento vazia",
            border_style="yellow",
        ))
        return

    base_info = f"\n  • [cyan]knowledge/base/[/cyan]      — Premissas base e forecasts ({sum(1 for f in all_files if BASE_DIR in f.parents)} arquivo(s))" if BASE_DIR.exists() else ""
    console.print(Panel.fit(
        f"[bold]Indexando {len(all_files)} arquivo(s)[/bold]\n"
        f"Pastas:\n"
        f"  • [cyan]knowledge/references/[/cyan] — Modelos de referencia ({sum(1 for f in all_files if REFERENCES_DIR in f.parents)} arquivo(s))"
        f"{base_info}\n"
        f"ChromaDB: [cyan]{ingestor.db_path}[/cyan]",
        title="IB-Agents Knowledge Ingestor",
        border_style="blue",
    ))

    stats = {"processed": 0, "chunks_added": 0, "skipped": 0, "errors": []}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processando...", total=len(all_files))

        for file_path in all_files:
            progress.update(task, description=f"[cyan]{file_path.name[:50]}[/cyan]")
            try:
                n = ingestor.ingest_file(str(file_path))
                stats["chunks_added"] += n
                stats["processed"] += 1
            except Exception as exc:
                stats["errors"].append({"file": file_path.name, "error": str(exc)})
                stats["skipped"] += 1
            progress.advance(task)

    # Summary table
    t = Table(title="Resultado da Indexação", show_lines=True)
    t.add_column("Métrica", style="cyan")
    t.add_column("Valor", justify="right", style="bold")
    t.add_row("Arquivos processados", str(stats["processed"]))
    t.add_row("Chunks indexados", str(stats["chunks_added"]))
    t.add_row("Arquivos ignorados", str(stats["skipped"]))
    console.print(t)

    if stats["errors"]:
        console.print("\n[yellow]Erros:[/yellow]")
        for e in stats["errors"]:
            console.print(f"  [red]✗[/red] {e['file']}: {e['error']}")

    console.print(f"\n[green]✓ Base de conhecimento pronta.[/green] "
                  f"Execute [bold]py ingest_knowledge.py --list[/bold] para verificar.")


def cmd_list():
    from tools.knowledge.ingestor import KnowledgeIngestor
    from rich.console import Console
    from rich.table import Table

    console = Console()
    ingestor = KnowledgeIngestor()
    indexed = ingestor.list_indexed()

    if not indexed or (len(indexed) == 1 and "error" in indexed[0]):
        console.print("[yellow]Base de conhecimento vazia ou não inicializada.[/yellow]")
        console.print("Execute: [bold]py ingest_knowledge.py[/bold]")
        return

    t = Table(title=f"Documentos Indexados ({len(indexed)} arquivos)", show_lines=True)
    t.add_column("Arquivo", style="cyan")
    t.add_column("Categoria")
    t.add_column("Chunks", justify="right")

    by_category: dict[str, int] = {}
    for doc in indexed:
        t.add_row(doc["file"], doc["category"], str(doc["chunks"]))
        by_category[doc["category"]] = by_category.get(doc["category"], 0) + doc["chunks"]

    console.print(t)
    console.print("\n[bold]Por categoria:[/bold]")
    for cat, chunks in sorted(by_category.items()):
        console.print(f"  {cat}: {chunks} chunks")


def cmd_reset():
    from tools.knowledge.ingestor import KnowledgeIngestor
    from rich.console import Console

    console = Console()
    console.print("[yellow]Resetando base de conhecimento...[/yellow]")
    ingestor = KnowledgeIngestor()
    ok = ingestor.reset()
    if ok:
        console.print("[green]✓ Base resetada. Execute py ingest_knowledge.py para reindexar.[/green]")
    else:
        console.print("[red]Erro ao resetar.[/red]")


def cmd_search(query: str):
    from tools.knowledge.ingestor import KnowledgeIngestor
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    ingestor = KnowledgeIngestor()
    results = ingestor.search(query=query, n_results=5)

    if not results:
        console.print("[yellow]Nenhum resultado encontrado.[/yellow]")
        return

    console.print(f"\n[bold]Resultados para:[/bold] [cyan]{query}[/cyan]\n")
    for i, r in enumerate(results, 1):
        console.print(Panel(
            r["text"][:400] + ("..." if len(r["text"]) > 400 else ""),
            title=f"[{i}] {r['source']} | {r['category']} | relevância: {r['relevance']}",
            border_style="blue",
        ))


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--list" in args:
        cmd_list()
    elif "--reset" in args:
        cmd_reset()
    elif "--search" in args:
        idx = args.index("--search")
        query = args[idx + 1] if idx + 1 < len(args) else ""
        if not query:
            print("Uso: py ingest_knowledge.py --search 'sua consulta aqui'")
            sys.exit(1)
        cmd_search(query)
    elif "--file" in args:
        idx = args.index("--file")
        file_arg = args[idx + 1] if idx + 1 < len(args) else ""
        cmd_ingest(file_arg=file_arg)
    else:
        cmd_ingest()
