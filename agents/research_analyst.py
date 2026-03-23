"""
Research Analyst Agent
Responsible for data ingestion, parsing, and structuring of all financial inputs.
"""

from __future__ import annotations

import os

from crewai import Agent

from tools.parsers.excel_parser import ExcelParserTool
from tools.parsers.pdf_parser import PDFParserTool


def build_research_analyst_agent() -> Agent:
    model = os.getenv("AGENT_MODEL", "claude-sonnet-4-6")

    return Agent(
        role="Research Analyst — Data Ingestion",
        goal=(
            "Coletar, parsear e estruturar todos os documentos financeiros fornecidos "
            "(Excel, PDF) em JSON normalizado, mapeando BP, DRE e DFC por entidade, "
            "pronto para revisão contábil e consolidação."
        ),
        backstory=(
            "Você é um analista de pesquisa sênior especializado em due diligence financeira "
            "para M&A no Brasil. Tem experiência em lidar com DFs de empresas não auditadas, "
            "planilhas gerenciais inconsistentes e relatórios contábeis em formatos variados. "
            "Seu trabalho é transformar dados brutos em informação estruturada e confiável, "
            "sinalizando qualquer lacuna ou inconsistência imediatamente. "
            "Você documenta todas as premissas de mapeamento para que o contador e o modelador "
            "possam auditar seu trabalho."
        ),
        tools=[
            ExcelParserTool(),
            PDFParserTool(),
        ],
        llm=model,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


ResearchAnalystAgent = build_research_analyst_agent
