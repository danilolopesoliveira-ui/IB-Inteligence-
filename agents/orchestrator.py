"""
MD Orchestrator Agent (Managing Director)
Top-level coordinator: routes tasks, manages crew sequencing,
performs final quality review of all outputs.
"""

from __future__ import annotations

import os

from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import json
import chromadb
from loguru import logger


# ---------------------------------------------------------------------------
# Memory / RAG Tool
# ---------------------------------------------------------------------------

class MemorySearchInput(BaseModel):
    query: str = Field(description="Consulta em linguagem natural para buscar análises anteriores")
    n_results: int = Field(default=3, description="Número de resultados a retornar")


class MemorySearchTool(BaseTool):
    name: str = "memory_search"
    description: str = (
        "Busca no histórico de análises anteriores (RAG local via ChromaDB) por contexto relevante: "
        "múltiplos setoriais históricos, benchmarks de margens, casos similares de M&A."
    )
    args_schema: type[BaseModel] = MemorySearchInput

    def _run(self, query: str, n_results: int = 3) -> str:
        try:
            db_path = os.getenv("CHROMA_DB_PATH", "./memory/chroma_db")
            collection_name = os.getenv("CHROMA_COLLECTION_NAME", "ib_analyses")

            client = chromadb.PersistentClient(path=db_path)
            try:
                collection = client.get_collection(collection_name)
            except Exception:
                return json.dumps({"results": [], "message": "Nenhuma análise anterior encontrada na memória."})

            results = collection.query(query_texts=[query], n_results=n_results)
            docs = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            formatted = []
            for doc, meta, dist in zip(docs, metadatas, distances):
                formatted.append({
                    "relevance_score": round(1 - dist, 3),
                    "metadata": meta,
                    "excerpt": doc[:500] if doc else "",
                })

            return json.dumps({"results": formatted}, ensure_ascii=False, indent=2)

        except Exception as exc:
            logger.error(f"Erro na busca de memória: {exc}")
            return json.dumps({"error": str(exc)})


class MemoryStoreInput(BaseModel):
    content: str = Field(description="Conteúdo da análise a armazenar")
    metadata: str = Field(
        default="{}",
        description='JSON com metadados: {"company": "X", "sector": "Y", "year": "2024", "analysis_type": "DCF"}',
    )
    document_id: str = Field(default="", description="ID único (deixar vazio para auto-gerar)")


class MemoryStoreTool(BaseTool):
    name: str = "memory_store"
    description: str = (
        "Armazena resultados de análise na memória RAG local (ChromaDB) "
        "para referência em análises futuras de empresas similares."
    )
    args_schema: type[BaseModel] = MemoryStoreInput

    def _run(self, content: str, metadata: str = "{}", document_id: str = "") -> str:
        try:
            import uuid
            db_path = os.getenv("CHROMA_DB_PATH", "./memory/chroma_db")
            collection_name = os.getenv("CHROMA_COLLECTION_NAME", "ib_analyses")
            meta = json.loads(metadata)

            client = chromadb.PersistentClient(path=db_path)
            collection = client.get_or_create_collection(collection_name)

            doc_id = document_id or str(uuid.uuid4())
            collection.add(documents=[content], metadatas=[meta], ids=[doc_id])

            return json.dumps({
                "stored": True,
                "document_id": doc_id,
                "collection": collection_name,
            })

        except Exception as exc:
            logger.error(f"Erro ao armazenar na memória: {exc}")
            return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def build_orchestrator_agent() -> Agent:
    model = os.getenv("ORCHESTRATOR_MODEL", "claude-opus-4-6")

    return Agent(
        role="Managing Director — Deal Orchestrator",
        goal=(
            "Coordenar o time de agentes para produzir análise financeira completa "
            "de M&A/PE de qualidade institucional, garantindo que cada etapa seja "
            "executada na ordem correta, com os inputs adequados e revisão final "
            "antes da entrega dos materiais ao cliente."
        ),
        backstory=(
            "Você é um Managing Director com 20 anos de experiência em investment banking no Brasil, "
            "tendo liderado mais de 500 transações de M&A, IPO e captação de dívida. "
            "Passou por Goldman Sachs, Morgan Stanley e BTG Pactual. "
            "Seu papel é garantir que o time funcione como uma máquina bem azeitada: "
            "o Research Analyst coleta e estrutura; o Contador revisa e ajusta as DFs; "
            "o Financial Modeler consolida e modela; o Quant Analyst valida via comps; "
            "o Risk Officer sinaliza red flags; e o Deck Builder entrega os materiais finais. "
            "Você revisa tudo antes de apresentar ao cliente e tem tolerância zero "
            "para erros numéricos ou premissas injustificadas.\n\n"
            "PROTOCOLO OBRIGATORIO DE PREMISSAS:\n"
            "No início de CADA projeto, você deve instruir todos os agentes a consultarem o\n"
            "Repositório de Premissas Base (knowledge/base/premissas_projecoes_base.md) antes\n"
            "de qualquer modelagem. Na revisão final, verifique se:\n"
            "  [ ] WACC utilizado está dentro do range do Módulo 5.2 para o setor\n"
            "  [ ] Múltiplos calibrados com Módulo 2.1 (ajuste por tamanho/liquidez documentado)\n"
            "  [ ] IPCA/SELIC/câmbio alinhados com Módulo 1 (não inventados)\n"
            "  [ ] Taxa g na perpetuidade dentro dos limites do Módulo 5.3\n"
            "  [ ] Stress test usando cenários do Módulo 7\n"
            "  [ ] Todo output indica versão do repositório utilizada\n"
            "Rejeite qualquer output que use premissas não rastreáveis ao repositório ou aos dados do cliente."
        ),
        tools=[
            MemorySearchTool(),
            MemoryStoreTool(),
        ],
        llm=model,
        verbose=True,
        allow_delegation=True,
        max_iter=10,
    )


OrchestratorAgent = build_orchestrator_agent
