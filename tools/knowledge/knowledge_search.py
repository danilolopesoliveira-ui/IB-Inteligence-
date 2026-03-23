"""
KnowledgeSearchTool
Permite que os agentes consultem a base de conhecimento de referência (RAG)
para buscar padrões, estruturas e metodologias dos modelos de referência.
"""

from __future__ import annotations

import json
import os
from typing import ClassVar

from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field

from tools.knowledge.ingestor import KnowledgeIngestor, KNOWLEDGE_DB_PATH


class KnowledgeSearchInput(BaseModel):
    query: str = Field(
        description=(
            "Consulta em linguagem natural. Exemplos: "
            "'estrutura de slides de pitch book para M&A', "
            "'como apresentar sensitivity analysis no DCF', "
            "'formato de executive summary para PE', "
            "'benchmarks de margem EBITDA setor industrial Brasil'"
        )
    )
    category: str = Field(
        default="",
        description="Filtrar por categoria: 'pitch_book', 'financial_model', 'research_report', '' (todas)",
    )
    n_results: int = Field(default=4, description="Número de trechos a retornar")


class KnowledgeSearchTool(BaseTool):
    name: str = "knowledge_search"
    description: str = (
        "Busca na base de conhecimento de modelos de referência de IB (pitch books, "
        "financial models, research reports) para encontrar padrões de estrutura, "
        "linguagem, metodologias de análise e benchmarks setoriais. "
        "Use ANTES de gerar qualquer output para alinhar com os padrões de mercado.\n\n"
        "IMPORTANTE: Resultados marcados com is_modelo=true vêm da pasta 'Modelo' de cada "
        "categoria — estes são os arquivos de referência primária para formatação e raciocínio. "
        "SEMPRE priorize esses resultados ao estruturar apresentações, modelos e análises. "
        "Os demais resultados servem como base de conhecimento complementar."
    )
    args_schema: type[BaseModel] = KnowledgeSearchInput

    _ingestor: ClassVar[KnowledgeIngestor | None] = None

    def _run(self, query: str, category: str = "", n_results: int = 4) -> str:
        try:
            ingestor = self._get_ingestor()
            results = ingestor.search(query=query, n_results=n_results, category=category)

            if not results:
                return json.dumps({
                    "found": 0,
                    "message": (
                        "Nenhum resultado encontrado na base de conhecimento. "
                        "Certifique-se de que os modelos de referência foram indexados "
                        "executando: py ingest_knowledge.py"
                    ),
                    "results": [],
                })

            modelo_count = sum(1 for r in results if r.get("is_modelo"))
            return json.dumps({
                "found": len(results),
                "modelo_results": modelo_count,
                "query": query,
                "category_filter": category or "all",
                "instruction": (
                    f"{modelo_count} resultado(s) da pasta Modelo (referencia primaria de formatacao). "
                    "Use-os como base estrutural do output. Os demais são referência complementar."
                ) if modelo_count > 0 else "Nenhum arquivo da pasta Modelo encontrado para esta query.",
                "results": results,
            }, ensure_ascii=False, indent=2)

        except Exception as exc:
            logger.error(f"Erro no knowledge_search: {exc}")
            return json.dumps({"error": str(exc), "results": []})

    @classmethod
    def _get_ingestor(cls) -> KnowledgeIngestor:
        if cls._ingestor is None:
            cls._ingestor = KnowledgeIngestor(db_path=KNOWLEDGE_DB_PATH)
        return cls._ingestor
