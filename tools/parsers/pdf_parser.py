"""
PDF Parser Tool
Extracts financial tables and narrative text from PDF documents using pdfplumber
and camelot-py as fallback for complex table layouts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


class PDFParserInput(BaseModel):
    file_path: str = Field(description="Caminho absoluto para o arquivo PDF")
    extract_tables: bool = Field(default=True, description="Extrair tabelas")
    extract_text: bool = Field(default=True, description="Extrair texto narrativo")
    pages: str = Field(default="all", description="Páginas a extrair: 'all', '1-5', '2,4,6'")


class PDFParserTool(BaseTool):
    name: str = "pdf_parser"
    description: str = (
        "Extrai tabelas e texto de arquivos PDF de demonstrações financeiras. "
        "Utiliza pdfplumber para extração primária e camelot como fallback. "
        "Retorna JSON com tabelas estruturadas e texto por página."
    )
    args_schema: type[BaseModel] = PDFParserInput

    def _run(
        self,
        file_path: str,
        extract_tables: bool = True,
        extract_text: bool = True,
        pages: str = "all",
    ) -> str:
        path = Path(file_path)
        if not path.exists():
            return json.dumps({"error": f"Arquivo não encontrado: {file_path}"})

        try:
            import pdfplumber

            result: dict[str, Any] = {
                "file": path.name,
                "pages": [],
                "tables": [],
                "text_blocks": [],
            }

            page_nums = self._parse_page_range(pages)

            with pdfplumber.open(str(path)) as pdf:
                total_pages = len(pdf.pages)
                target_pages = (
                    range(total_pages)
                    if page_nums is None
                    else [p - 1 for p in page_nums if 0 < p <= total_pages]
                )

                for page_idx in target_pages:
                    page = pdf.pages[page_idx]
                    page_num = page_idx + 1
                    page_data: dict[str, Any] = {"page": page_num}

                    if extract_text:
                        text = page.extract_text() or ""
                        page_data["text"] = text
                        result["text_blocks"].append({"page": page_num, "text": text})

                    if extract_tables:
                        tables = page.extract_tables()
                        for t_idx, table in enumerate(tables):
                            cleaned = self._clean_table(table)
                            if cleaned:
                                result["tables"].append({
                                    "page": page_num,
                                    "table_index": t_idx,
                                    "data": cleaned,
                                    "statement_type": self._classify_table(cleaned),
                                })

                    result["pages"].append(page_data)

            # Try camelot if no tables found via pdfplumber
            if extract_tables and not result["tables"]:
                result["tables"] = self._extract_with_camelot(str(path), pages)

            # Post-process: detect financial data blocks
            result["financial_summary"] = self._extract_financial_data(result["tables"])

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro ao parsear PDF: {exc}")
            return json.dumps({"error": str(exc)})

    # ------------------------------------------------------------------

    def _parse_page_range(self, pages: str) -> list[int] | None:
        if pages.lower() == "all":
            return None
        nums: list[int] = []
        for part in pages.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                nums.extend(range(int(start), int(end) + 1))
            else:
                nums.append(int(part))
        return nums

    def _clean_table(self, table: list) -> list[list[str]]:
        if not table:
            return []
        cleaned = []
        for row in table:
            if row is None:
                continue
            cleaned_row = [str(cell or "").strip() for cell in row]
            if any(cell for cell in cleaned_row):
                cleaned.append(cleaned_row)
        return cleaned

    def _classify_table(self, table: list[list[str]]) -> str:
        flat = " ".join(cell.lower() for row in table for cell in row)
        if any(kw in flat for kw in ["receita", "lucro bruto", "ebitda", "resultado"]):
            return "income_statement"
        if any(kw in flat for kw in ["ativo", "passivo", "patrimônio"]):
            return "balance_sheet"
        if any(kw in flat for kw in ["fluxo de caixa", "cfo", "capex", "atividades"]):
            return "cash_flow"
        if any(kw in flat for kw in ["dívida", "amortização", "saldo devedor"]):
            return "debt_schedule"
        return "unknown"

    def _extract_with_camelot(self, file_path: str, pages: str) -> list[dict]:
        try:
            import camelot

            page_str = "all" if pages == "all" else pages
            tables = camelot.read_pdf(file_path, pages=page_str, flavor="lattice")
            if not tables:
                tables = camelot.read_pdf(file_path, pages=page_str, flavor="stream")

            result = []
            for i, table in enumerate(tables):
                df = table.df
                data = [list(row) for _, row in df.iterrows()]
                result.append({
                    "page": table.page,
                    "table_index": i,
                    "data": data,
                    "statement_type": self._classify_table(data),
                    "source": "camelot",
                    "accuracy": table.accuracy,
                })
            return result
        except Exception as exc:
            logger.warning(f"Camelot fallback falhou: {exc}")
            return []

    def _extract_financial_data(self, tables: list[dict]) -> dict[str, Any]:
        """Attempt to extract key financial metrics from parsed tables."""
        metrics: dict[str, float] = {}
        number_pattern = re.compile(r"[\d.,]+")

        def parse_br_number(s: str) -> float | None:
            s = s.replace("R$", "").replace(" ", "").replace("(", "-").replace(")", "")
            if not number_pattern.search(s):
                return None
            try:
                if "," in s:
                    s = s.replace(".", "").replace(",", ".")
                return float(s)
            except ValueError:
                return None

        keyword_metric_map = {
            "receita líquida": "net_revenue",
            "ebitda": "ebitda",
            "lucro líquido": "net_income",
            "total ativo": "total_assets",
            "dívida líquida": "net_debt",
        }

        for table in tables:
            for row in table.get("data", []):
                if len(row) < 2:
                    continue
                label = row[0].lower().strip()
                for kw, metric in keyword_metric_map.items():
                    if kw in label:
                        # Take the last numeric value in the row
                        for cell in reversed(row[1:]):
                            val = parse_br_number(cell)
                            if val is not None and val != 0:
                                metrics[metric] = val
                                break

        return metrics
