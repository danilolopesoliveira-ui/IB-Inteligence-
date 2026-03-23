"""
Excel Parser Tool
Reads financial statements (BP, DRE, DFC) from Excel files with variable layouts.
Supports multi-entity workbooks with one tab per entity or structured data ranges.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schema maps — standard Portuguese account names to canonical keys
# ---------------------------------------------------------------------------

BP_ASSET_MAP = {
    # Ativo Circulante
    "caixa e equivalentes": "cash",
    "caixa e equivalentes de caixa": "cash",
    "aplicações financeiras": "short_term_investments",
    "contas a receber": "accounts_receivable",
    "clientes": "accounts_receivable",
    "estoques": "inventory",
    "estoque": "inventory",
    "outros ativos circulantes": "other_current_assets",
    "total ativo circulante": "total_current_assets",
    "ativo circulante": "total_current_assets",
    # Ativo Não Circulante
    "imobilizado": "ppe_net",
    "imobilizado líquido": "ppe_net",
    "intangível": "intangibles",
    "intangíveis": "intangibles",
    "goodwill": "goodwill",
    "investimentos": "investments_lt",
    "direito de uso": "right_of_use",
    "outros ativos não circulantes": "other_noncurrent_assets",
    "total ativo não circulante": "total_noncurrent_assets",
    "ativo não circulante": "total_noncurrent_assets",
    "total ativo": "total_assets",
    "ativo total": "total_assets",
}

BP_LIABILITY_MAP = {
    # Passivo Circulante
    "fornecedores": "accounts_payable",
    "contas a pagar": "accounts_payable",
    "empréstimos e financiamentos cp": "st_debt",
    "empréstimos cp": "st_debt",
    "financiamentos cp": "st_debt",
    "salários e encargos": "accrued_salaries",
    "impostos a pagar": "taxes_payable",
    "adiantamentos de clientes": "deferred_revenue",
    "outros passivos circulantes": "other_current_liabilities",
    "total passivo circulante": "total_current_liabilities",
    "passivo circulante": "total_current_liabilities",
    # Passivo Não Circulante
    "empréstimos e financiamentos lp": "lt_debt",
    "empréstimos lp": "lt_debt",
    "financiamentos lp": "lt_debt",
    "debêntures": "debentures",
    "provisão para contingências": "contingencies_provision",
    "outros passivos não circulantes": "other_noncurrent_liabilities",
    "total passivo não circulante": "total_noncurrent_liabilities",
    "passivo não circulante": "total_noncurrent_liabilities",
    # Patrimônio Líquido
    "capital social": "share_capital",
    "reservas de lucro": "retained_earnings",
    "reservas de capital": "capital_reserves",
    "lucros acumulados": "accumulated_profits",
    "prejuízos acumulados": "accumulated_losses",
    "participação de não controladores": "minority_interest",
    "total patrimônio líquido": "total_equity",
    "patrimônio líquido": "total_equity",
    "total passivo e patrimônio líquido": "total_liabilities_equity",
}

DRE_MAP = {
    "receita bruta": "gross_revenue",
    "receita bruta de vendas": "gross_revenue",
    "deduções da receita": "revenue_deductions",
    "impostos sobre vendas": "revenue_deductions",
    "receita líquida": "net_revenue",
    "receita operacional líquida": "net_revenue",
    "custo dos produtos vendidos": "cogs",
    "custo das mercadorias vendidas": "cogs",
    "custo dos serviços prestados": "cogs",
    "cpv": "cogs",
    "lucro bruto": "gross_profit",
    "despesas com vendas": "selling_expenses",
    "despesas gerais e administrativas": "ga_expenses",
    "despesas administrativas": "ga_expenses",
    "outras despesas operacionais": "other_operating_expenses",
    "outras receitas operacionais": "other_operating_income",
    "ebitda": "ebitda",
    "depreciação e amortização": "da",
    "depreciação": "da",
    "ebit": "ebit",
    "resultado financeiro": "financial_result",
    "receitas financeiras": "financial_income",
    "despesas financeiras": "financial_expenses",
    "lair": "ebt",
    "resultado antes do ir": "ebt",
    "irpj e csll": "income_tax",
    "imposto de renda": "income_tax",
    "lucro líquido": "net_income",
    "resultado líquido": "net_income",
}

DFC_MAP = {
    "lucro líquido": "net_income",
    "depreciação e amortização": "da",
    "variação de contas a receber": "chg_receivables",
    "variação de estoques": "chg_inventory",
    "variação de fornecedores": "chg_payables",
    "variação de capital de giro": "chg_working_capital",
    "caixa gerado pelas operações": "cfo",
    "fluxo de caixa operacional": "cfo",
    "capex": "capex",
    "aquisição de imobilizado": "capex",
    "investimentos em imobilizado": "capex",
    "caixa das atividades de investimento": "cfi",
    "fluxo de caixa de investimento": "cfi",
    "captação de empréstimos": "debt_proceeds",
    "pagamento de empréstimos": "debt_repayment",
    "dividendos pagos": "dividends_paid",
    "caixa das atividades de financiamento": "cff",
    "fluxo de caixa de financiamento": "cff",
    "variação de caixa": "net_change_cash",
}


class ExcelParserInput(BaseModel):
    file_path: str = Field(description="Caminho absoluto para o arquivo Excel")
    entity_name: str = Field(default="", description="Nome da entidade (deixar vazio para auto-detectar)")
    sheets: list[str] = Field(default=[], description="Abas específicas para ler (vazio = todas)")


class ExcelParserTool(BaseTool):
    name: str = "excel_parser"
    description: str = (
        "Lê e estrutura demonstrações financeiras (BP, DRE, DFC) de arquivos Excel. "
        "Suporta layouts variados e múltiplas entidades em abas separadas. "
        "Retorna JSON estruturado com os dados financeiros normalizados."
    )
    args_schema: type[BaseModel] = ExcelParserInput

    def _run(self, file_path: str, entity_name: str = "", sheets: list[str] = []) -> str:
        path = Path(file_path)
        if not path.exists():
            return json.dumps({"error": f"Arquivo não encontrado: {file_path}"})

        try:
            xl = pd.ExcelFile(path)
            available_sheets = xl.sheet_names
            target_sheets = sheets if sheets else available_sheets

            result: dict[str, Any] = {
                "file": path.name,
                "entities": {},
            }

            for sheet in target_sheets:
                if sheet not in available_sheets:
                    logger.warning(f"Aba '{sheet}' não encontrada; ignorando.")
                    continue

                df = pd.read_excel(path, sheet_name=sheet, header=None, dtype=str)
                df = df.fillna("")
                parsed = self._parse_sheet(df, sheet, entity_name or sheet)
                if parsed:
                    entity = parsed.pop("entity")
                    result["entities"].setdefault(entity, {}).update(parsed)

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro ao parsear Excel: {exc}")
            return json.dumps({"error": str(exc)})

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_sheet(self, df: pd.DataFrame, sheet_name: str, entity_name: str) -> dict | None:
        sheet_lower = sheet_name.lower()
        if any(kw in sheet_lower for kw in ["bp", "balanço", "balanco", "balance"]):
            return self._parse_bp(df, entity_name)
        elif any(kw in sheet_lower for kw in ["dre", "resultado", "p&l", "income"]):
            return self._parse_dre(df, entity_name)
        elif any(kw in sheet_lower for kw in ["dfc", "caixa", "cash flow"]):
            return self._parse_dfc(df, entity_name)
        else:
            # Try to auto-detect
            for kw in ["receita", "lucro", "ebitda"]:
                if self._df_contains_keyword(df, kw):
                    return self._parse_dre(df, entity_name)
            for kw in ["ativo", "passivo", "patrimônio"]:
                if self._df_contains_keyword(df, kw):
                    return self._parse_bp(df, entity_name)
        return None

    def _df_contains_keyword(self, df: pd.DataFrame, keyword: str) -> bool:
        return df.apply(lambda col: col.str.lower().str.contains(keyword, na=False)).any().any()

    def _extract_years(self, df: pd.DataFrame) -> list[str]:
        """Detect year columns from header rows."""
        years = []
        for row_idx in range(min(5, len(df))):
            row = df.iloc[row_idx]
            for val in row:
                val_str = str(val).strip()
                if val_str.isdigit() and 2015 <= int(val_str) <= 2030:
                    if val_str not in years:
                        years.append(val_str)
        return years

    def _find_label_col(self, df: pd.DataFrame) -> int:
        """Find which column contains account labels (most string-like)."""
        for col_idx in range(min(3, len(df.columns))):
            col = df.iloc[:, col_idx]
            non_empty = col[col.str.strip() != ""]
            if len(non_empty) > 5:
                return col_idx
        return 0

    def _parse_statement(
        self, df: pd.DataFrame, entity_name: str, account_map: dict, statement_type: str
    ) -> dict:
        years = self._extract_years(df)
        label_col = self._find_label_col(df)

        # Detect value columns (numeric-ish columns after the label col)
        value_cols: list[int] = []
        for col_idx in range(label_col + 1, len(df.columns)):
            col = df.iloc[:, col_idx]
            numeric_count = col.apply(lambda x: self._is_numeric(x)).sum()
            if numeric_count > 3:
                value_cols.append(col_idx)

        data: dict[str, dict[str, float]] = {}
        for row_idx, row in df.iterrows():
            label = str(row.iloc[label_col]).strip().lower()
            canonical = account_map.get(label)
            if not canonical:
                # fuzzy match: check if any key is contained in label
                for k, v in account_map.items():
                    if k in label or label in k:
                        canonical = v
                        break
            if not canonical:
                continue

            data[canonical] = {}
            for i, col_idx in enumerate(value_cols):
                year = years[i] if i < len(years) else f"col_{i}"
                raw = str(row.iloc[col_idx]).strip()
                data[canonical][year] = self._to_float(raw)

        return {
            "entity": entity_name,
            statement_type: data,
            "years_detected": years,
        }

    def _parse_bp(self, df: pd.DataFrame, entity_name: str) -> dict:
        combined_map = {**BP_ASSET_MAP, **BP_LIABILITY_MAP}
        return self._parse_statement(df, entity_name, combined_map, "balance_sheet")

    def _parse_dre(self, df: pd.DataFrame, entity_name: str) -> dict:
        return self._parse_statement(df, entity_name, DRE_MAP, "income_statement")

    def _parse_dfc(self, df: pd.DataFrame, entity_name: str) -> dict:
        return self._parse_statement(df, entity_name, DFC_MAP, "cash_flow")

    def _is_numeric(self, val: Any) -> bool:
        try:
            float(str(val).replace(".", "").replace(",", ".").replace("(", "-").replace(")", "").replace("R$", "").strip())
            return True
        except (ValueError, AttributeError):
            return False

    def _to_float(self, val: str) -> float:
        """Convert Brazilian number format to float."""
        val = val.replace("R$", "").replace(" ", "").strip()
        # Handle parentheses as negative: (1.000,00) → -1000.00
        negative = val.startswith("(") and val.endswith(")")
        val = val.strip("()")
        # Brazilian format: 1.234.567,89
        if "," in val:
            val = val.replace(".", "").replace(",", ".")
        else:
            val = val.replace(".", "")
        try:
            result = float(val)
            return -result if negative else result
        except ValueError:
            return 0.0
