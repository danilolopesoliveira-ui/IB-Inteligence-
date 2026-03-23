"""
IB-Agents — Investment Banking Multi-Agent System
Entry point for full analysis pipeline.

Usage:
    python main.py --input ./data/empresa.xlsx --company "Empresa XYZ" --deal-type M&A
    python main.py --input ./data/empresa.pdf --company "Empresa ABC" --deal-type PE_Investment
    python main.py --demo  # runs with synthetic data
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

load_dotenv()

app = typer.Typer(help="IB-Agents — Investment Banking Multi-Agent System")
console = Console()


def validate_env():
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or not key.startswith("sk-"):
        console.print("[bold red]ANTHROPIC_API_KEY não configurada ou inválida.[/bold red]")
        console.print("Configure no arquivo .env: ANTHROPIC_API_KEY=sk-ant-...")
        raise typer.Exit(1)


@app.command()
def analyze(
    input_file: str = typer.Option("", "--input", "-i", help="Caminho para o arquivo Excel ou PDF"),
    company: str = typer.Option("", "--company", "-c", help="Nome da empresa alvo"),
    deal_type: str = typer.Option(
        "M&A", "--deal-type", "-d",
        help="Tipo de transação: M&A | PE_Investment | Debt_Advisory | IPO_Readiness",
    ),
    sector: str = typer.Option("industria", "--sector", "-s", help="Setor da empresa"),
    mode: str = typer.Option(
        "full_analysis", "--mode", "-m",
        help="Modo: full_analysis | parsing_only | valuation_only | output_only",
    ),
    demo: bool = typer.Option(False, "--demo", help="Rodar com dados sintéticos de demonstração"),
    output_dir: str = typer.Option("./output", "--output-dir", "-o", help="Diretório de saída"),
):
    """Executa análise financeira completa via multi-agent system."""

    validate_env()
    os.environ["OUTPUT_DIR"] = output_dir
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        "[bold navy]IB-Agents — Investment Banking Multi-Agent System[/bold navy]\n"
        f"Empresa: [gold1]{company or 'Demo Company'}[/gold1] | "
        f"Deal: [gold1]{deal_type}[/gold1] | Setor: [gold1]{sector}[/gold1]",
        border_style="blue",
    ))

    if demo:
        input_data = _generate_demo_data(company or "Demo Indústria S.A.", sector)
        company = company or "Demo Indústria S.A."
    elif not input_file:
        console.print("[red]Forneça --input ou use --demo para dados de demonstração.[/red]")
        raise typer.Exit(1)
    else:
        if not Path(input_file).exists():
            console.print(f"[red]Arquivo não encontrado: {input_file}[/red]")
            raise typer.Exit(1)
        input_data = {"file_path": input_file, "company": company}

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Inicializando agentes...", total=None)

        try:
            from crew import IBAnalysisCrew
            crew_instance = IBAnalysisCrew(
                company_name=company,
                deal_type=deal_type,
                sector=sector,
                input_data=input_data,
                mode=mode,
            )

            progress.update(task, description="Executando pipeline de análise...")
            result = crew_instance.run()

            progress.update(task, description="Finalizando outputs...")

        except Exception as exc:
            logger.error(f"Erro na execução: {exc}")
            console.print(f"[red]Erro: {exc}[/red]")
            raise typer.Exit(1)

    console.print("\n[bold green]Análise concluída![/bold green]")
    console.print(f"Outputs salvos em: [cyan]{output_dir}[/cyan]")
    if isinstance(result, dict):
        for key, val in result.items():
            if "path" in str(val):
                console.print(f"  • {key}: [cyan]{val}[/cyan]")


def _generate_demo_data(company_name: str, sector: str) -> dict:
    """Generate synthetic financial data for demo/testing."""
    return {
        "demo": True,
        "company": company_name,
        "sector": sector,
        "entities": {
            company_name: {
                "balance_sheet": {
                    "cash": {"2022": 5_000_000, "2023": 7_500_000, "2024": 9_000_000},
                    "accounts_receivable": {"2022": 18_000_000, "2023": 22_000_000, "2024": 26_000_000},
                    "inventory": {"2022": 8_000_000, "2023": 9_500_000, "2024": 11_000_000},
                    "total_current_assets": {"2022": 32_000_000, "2023": 40_000_000, "2024": 48_000_000},
                    "ppe_net": {"2022": 25_000_000, "2023": 30_000_000, "2024": 35_000_000},
                    "intangibles": {"2022": 3_000_000, "2023": 3_500_000, "2024": 4_000_000},
                    "total_noncurrent_assets": {"2022": 28_000_000, "2023": 33_500_000, "2024": 39_000_000},
                    "total_assets": {"2022": 60_000_000, "2023": 73_500_000, "2024": 87_000_000},
                    "accounts_payable": {"2022": 9_000_000, "2023": 10_500_000, "2024": 12_000_000},
                    "st_debt": {"2022": 5_000_000, "2023": 6_000_000, "2024": 5_500_000},
                    "total_current_liabilities": {"2022": 16_000_000, "2023": 19_000_000, "2024": 22_000_000},
                    "lt_debt": {"2022": 20_000_000, "2023": 22_000_000, "2024": 24_000_000},
                    "total_noncurrent_liabilities": {"2022": 22_000_000, "2023": 24_500_000, "2024": 27_000_000},
                    "total_equity": {"2022": 22_000_000, "2023": 30_000_000, "2024": 38_000_000},
                    "total_liabilities_equity": {"2022": 60_000_000, "2023": 73_500_000, "2024": 87_000_000},
                },
                "income_statement": {
                    "gross_revenue": {"2022": 90_000_000, "2023": 108_000_000, "2024": 130_000_000},
                    "revenue_deductions": {"2022": -10_000_000, "2023": -12_000_000, "2024": -14_000_000},
                    "net_revenue": {"2022": 80_000_000, "2023": 96_000_000, "2024": 116_000_000},
                    "cogs": {"2022": -48_000_000, "2023": -56_000_000, "2024": -67_000_000},
                    "gross_profit": {"2022": 32_000_000, "2023": 40_000_000, "2024": 49_000_000},
                    "selling_expenses": {"2022": -8_000_000, "2023": -9_500_000, "2024": -11_500_000},
                    "ga_expenses": {"2022": -6_000_000, "2023": -7_000_000, "2024": -8_500_000},
                    "ebitda": {"2022": 18_000_000, "2023": 23_500_000, "2024": 29_000_000},
                    "da": {"2022": -4_000_000, "2023": -4_800_000, "2024": -5_800_000},
                    "ebit": {"2022": 14_000_000, "2023": 18_700_000, "2024": 23_200_000},
                    "financial_income": {"2022": 500_000, "2023": 700_000, "2024": 900_000},
                    "financial_expenses": {"2022": -3_500_000, "2023": -4_000_000, "2024": -4_500_000},
                    "ebt": {"2022": 11_000_000, "2023": 15_400_000, "2024": 19_600_000},
                    "income_tax": {"2022": -3_740_000, "2023": -5_236_000, "2024": -6_664_000},
                    "net_income": {"2022": 7_260_000, "2023": 10_164_000, "2024": 12_936_000},
                },
                "cash_flow": {
                    "cfo": {"2022": 14_000_000, "2023": 18_000_000, "2024": 22_000_000},
                    "capex": {"2022": -6_000_000, "2023": -8_000_000, "2024": -9_000_000},
                    "cfi": {"2022": -6_000_000, "2023": -8_000_000, "2024": -9_000_000},
                    "cff": {"2022": -4_000_000, "2023": -2_000_000, "2024": -4_500_000},
                    "net_change_cash": {"2022": 4_000_000, "2023": 8_000_000, "2024": 8_500_000},
                },
            }
        },
        "years": ["2022", "2023", "2024"],
        "ownership": {company_name: {}},
    }


if __name__ == "__main__":
    app()
