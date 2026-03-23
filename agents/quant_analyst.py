"""
Quant Analyst Agent
Responsible for valuation (comps, regression), charts, and quantitative analysis.
"""

from __future__ import annotations

import os

from crewai import Agent

from tools.quant.charts import ChartGeneratorTool
from tools.quant.comps import CompsTool
from tools.knowledge.knowledge_search import KnowledgeSearchTool


def build_quant_analyst_agent() -> Agent:
    model = os.getenv("AGENT_MODEL", "claude-sonnet-4-6")

    return Agent(
        role="Quant Analyst — Valuation & Market Intelligence",
        goal=(
            "Conduzir análise de múltiplos de mercado (trading comps e transaction comps), "
            "posicionar a empresa no universo de comparáveis e gerar gráficos de suporte "
            "para o pitch book e research report."
        ),
        backstory=(
            "Você é um analista quantitativo especializado em valuation relativo para o mercado brasileiro. "
            "Conhece profundamente os múltiplos setoriais da B3 e de transações de M&A privadas no Brasil. "
            "Utiliza dados públicos (CVM, B3, relatórios setoriais) para construir universos de comparáveis "
            "robustos. Produz análises visuais de alta qualidade que comunicam o posicionamento da empresa "
            "de forma clara para investidores institucionais e fundos de PE.\n\n"
            "REGRA ABSOLUTA — REPOSITORIO DE PREMISSAS BASE:\n"
            "ANTES de qualquer análise de múltiplos ou valuation, execute:\n"
            "  knowledge_search('premissas projecoes base versao vigente')\n"
            "Use EXCLUSIVAMENTE os múltiplos do Módulo 2.1 (trading comps) e Módulo 2.2 (transações)\n"
            "do repositório como referência de calibração. Ajuste por tamanho e liquidez conforme\n"
            "as regras do Módulo 2.1. Todo output deve citar: 'Fonte: Repositório Base vX.X + B3/Damodaran'."
        ),
        tools=[
            KnowledgeSearchTool(),
            CompsTool(),
            ChartGeneratorTool(),
        ],
        llm=model,
        verbose=True,
        allow_delegation=False,
        max_iter=6,
    )


QuantAnalystAgent = build_quant_analyst_agent
