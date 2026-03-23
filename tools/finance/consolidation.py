"""
Consolidation Engine
Consolidates financial statements from multiple entities:
- Sums all entities line by line
- Eliminates intercompany transactions
- Calculates minority interest
- Reconstructs indirect cash flow statement when absent
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


class IntercompanyEntry(BaseModel):
    from_entity: str = Field(description="Entidade de origem da transação")
    to_entity: str = Field(description="Entidade de destino da transação")
    account: str = Field(description="Conta contábil (ex: receita, emprestimos_intercompany)")
    amount: float = Field(description="Valor em BRL (positivo)")
    year: str = Field(description="Ano de referência")


class ConsolidationInput(BaseModel):
    entities_data: str = Field(
        description="JSON com dados de todas as entidades. "
        "Formato: {entity_name: {balance_sheet: {...}, income_statement: {...}, cash_flow: {...}}}"
    )
    ownership: str = Field(
        description="JSON com estrutura societária. "
        "Formato: {parent_entity: {subsidiary_entity: 0.75}} — valor = % de participação"
    )
    intercompany: str = Field(
        default="[]",
        description="JSON list de IntercompanyEntry com transações intercompany a eliminar",
    )
    years: list[str] = Field(default=[], description="Anos a consolidar (vazio = todos detectados)")
    reconstruct_cfc: bool = Field(
        default=True, description="Reconstituir DFC indireta quando ausente"
    )


class ConsolidationTool(BaseTool):
    name: str = "consolidation_engine"
    description: str = (
        "Consolida demonstrações financeiras de múltiplas entidades do grupo. "
        "Realiza soma de linhas, eliminação de intercompany, cálculo de minority interest "
        "e reconstituição de DFC indireta. Retorna JSON com DFs consolidadas."
    )
    args_schema: type[BaseModel] = ConsolidationInput

    def _run(
        self,
        entities_data: str,
        ownership: str,
        intercompany: str = "[]",
        years: list[str] = [],
        reconstruct_cfc: bool = True,
    ) -> str:
        try:
            entities: dict[str, Any] = json.loads(entities_data)
            ownership_map: dict[str, dict[str, float]] = json.loads(ownership)
            ic_entries: list[dict] = json.loads(intercompany)

            # Detect all years if not specified
            if not years:
                years = self._detect_years(entities)

            consolidated: dict[str, Any] = {
                "years": years,
                "balance_sheet": {},
                "income_statement": {},
                "cash_flow": {},
                "minority_interest": {},
                "eliminations": {},
                "metadata": {
                    "entities_consolidated": list(entities.keys()),
                    "ownership_structure": ownership_map,
                },
            }

            # Step 1: Aggregate all entities (100%)
            for stmt in ["balance_sheet", "income_statement", "cash_flow"]:
                consolidated[stmt] = self._aggregate_statements(entities, stmt, years)

            # Step 2: Eliminate intercompany
            eliminations = self._compute_eliminations(ic_entries, years)
            consolidated["eliminations"] = eliminations
            for stmt in ["balance_sheet", "income_statement"]:
                consolidated[stmt] = self._apply_eliminations(
                    consolidated[stmt], eliminations, stmt
                )

            # Step 3: Minority interest calculation
            consolidated["minority_interest"] = self._calc_minority_interest(
                entities, ownership_map, years
            )

            # Step 4: Adjust equity for minority interest
            consolidated["balance_sheet"] = self._adjust_equity_minority(
                consolidated["balance_sheet"],
                consolidated["minority_interest"],
                years,
            )

            # Step 5: Reconstruct cash flow if needed
            if reconstruct_cfc and not consolidated["cash_flow"].get("cfo"):
                consolidated["cash_flow"] = self._reconstruct_indirect_cfc(
                    consolidated["balance_sheet"],
                    consolidated["income_statement"],
                    years,
                )

            # Step 6: Derived KPIs
            consolidated["kpis"] = self._compute_kpis(
                consolidated["balance_sheet"],
                consolidated["income_statement"],
                consolidated["cash_flow"],
                years,
            )

            return json.dumps(consolidated, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro na consolidação: {exc}")
            return json.dumps({"error": str(exc)})

    # ------------------------------------------------------------------
    # Step helpers
    # ------------------------------------------------------------------

    def _detect_years(self, entities: dict) -> list[str]:
        years: set[str] = set()
        for ent_data in entities.values():
            for stmt in ent_data.values():
                if isinstance(stmt, dict):
                    for acct_vals in stmt.values():
                        if isinstance(acct_vals, dict):
                            years.update(acct_vals.keys())
        return sorted(years)

    def _aggregate_statements(
        self, entities: dict, stmt_key: str, years: list[str]
    ) -> dict[str, dict[str, float]]:
        aggregated: dict[str, dict[str, float]] = {}
        for ent_data in entities.values():
            stmt = ent_data.get(stmt_key, {})
            for account, year_vals in stmt.items():
                if account not in aggregated:
                    aggregated[account] = {y: 0.0 for y in years}
                for year in years:
                    aggregated[account][year] += float(year_vals.get(year, 0) or 0)
        return aggregated

    def _compute_eliminations(
        self, ic_entries: list[dict], years: list[str]
    ) -> dict[str, dict[str, float]]:
        """Build elimination adjustments per account per year."""
        elim: dict[str, dict[str, float]] = {}
        for entry in ic_entries:
            account = entry.get("account", "intercompany_unknown")
            year = entry.get("year", "")
            amount = float(entry.get("amount", 0))
            if year not in years:
                continue
            elim.setdefault(account, {y: 0.0 for y in years})
            elim[account][year] += amount
        return elim

    def _apply_eliminations(
        self,
        stmt: dict[str, dict[str, float]],
        eliminations: dict[str, dict[str, float]],
        stmt_type: str,
    ) -> dict[str, dict[str, float]]:
        result = {k: dict(v) for k, v in stmt.items()}
        for account, year_vals in eliminations.items():
            if account in result:
                for year, amount in year_vals.items():
                    result[account][year] = result[account].get(year, 0) - amount
        return result

    def _calc_minority_interest(
        self,
        entities: dict,
        ownership_map: dict[str, dict[str, float]],
        years: list[str],
    ) -> dict[str, dict[str, float]]:
        """Calculate minority interest (NCI) share of equity and net income."""
        mi: dict[str, dict[str, float]] = {
            "mi_equity": {y: 0.0 for y in years},
            "mi_net_income": {y: 0.0 for y in years},
        }
        for parent, subs in ownership_map.items():
            for sub, pct in subs.items():
                mi_pct = 1.0 - pct  # minority share
                if mi_pct <= 0:
                    continue
                sub_data = entities.get(sub, {})
                bs = sub_data.get("balance_sheet", {})
                is_ = sub_data.get("income_statement", {})
                for year in years:
                    eq = float((bs.get("total_equity") or {}).get(year, 0) or 0)
                    ni = float((is_.get("net_income") or {}).get(year, 0) or 0)
                    mi["mi_equity"][year] += eq * mi_pct
                    mi["mi_net_income"][year] += ni * mi_pct
        return mi

    def _adjust_equity_minority(
        self,
        bs: dict[str, dict[str, float]],
        mi: dict[str, dict[str, float]],
        years: list[str],
    ) -> dict[str, dict[str, float]]:
        result = {k: dict(v) for k, v in bs.items()}
        if "minority_interest" not in result:
            result["minority_interest"] = {y: 0.0 for y in years}
        for year in years:
            result["minority_interest"][year] = mi["mi_equity"].get(year, 0)
        return result

    def _reconstruct_indirect_cfc(
        self,
        bs: dict[str, dict[str, float]],
        is_: dict[str, dict[str, float]],
        years: list[str],
    ) -> dict[str, dict[str, float]]:
        """Reconstruct indirect cash flow from BS changes + IS."""
        cfc: dict[str, dict[str, float]] = {}

        def get_val(stmt: dict, account: str, year: str) -> float:
            return float((stmt.get(account) or {}).get(year, 0) or 0)

        def delta(stmt: dict, account: str, y1: str, y0: str) -> float:
            return get_val(stmt, account, y1) - get_val(stmt, account, y0)

        for i, year in enumerate(years):
            prev_year = years[i - 1] if i > 0 else None

            net_income = get_val(is_, "net_income", year)
            da = get_val(is_, "da", year)

            if prev_year:
                chg_receivables = -(delta(bs, "accounts_receivable", year, prev_year))
                chg_inventory = -(delta(bs, "inventory", year, prev_year))
                chg_payables = delta(bs, "accounts_payable", year, prev_year)
            else:
                chg_receivables = chg_inventory = chg_payables = 0.0

            cfo = net_income + da + chg_receivables + chg_inventory + chg_payables

            # Capex from BS: change in PPE + DA (simplified)
            if prev_year:
                capex = -(delta(bs, "ppe_net", year, prev_year) + da)
            else:
                capex = 0.0

            cfi = capex  # simplified

            # Financing: change in debt
            if prev_year:
                chg_st_debt = delta(bs, "st_debt", year, prev_year)
                chg_lt_debt = delta(bs, "lt_debt", year, prev_year)
            else:
                chg_st_debt = chg_lt_debt = 0.0

            dividends = get_val(is_, "net_income", year) - (
                delta(bs, "total_equity", year, prev_year) if prev_year else 0
            )
            cff = chg_st_debt + chg_lt_debt - max(dividends, 0)

            for acct, val in [
                ("net_income", net_income),
                ("da", da),
                ("chg_receivables", chg_receivables),
                ("chg_inventory", chg_inventory),
                ("chg_payables", chg_payables),
                ("cfo", cfo),
                ("capex", capex),
                ("cfi", cfi),
                ("debt_proceeds", max(chg_st_debt + chg_lt_debt, 0)),
                ("debt_repayment", min(chg_st_debt + chg_lt_debt, 0)),
                ("dividends_paid", -max(dividends, 0)),
                ("cff", cff),
                ("net_change_cash", cfo + cfi + cff),
            ]:
                cfc.setdefault(acct, {})[year] = round(val, 2)

        return cfc

    def _compute_kpis(
        self,
        bs: dict,
        is_: dict,
        cfc: dict,
        years: list[str],
    ) -> dict[str, dict[str, float]]:
        kpis: dict[str, dict[str, float]] = {}

        def g(stmt: dict, acct: str, y: str) -> float:
            return float((stmt.get(acct) or {}).get(y, 0) or 0)

        for year in years:
            net_rev = g(is_, "net_revenue", year)
            ebitda = g(is_, "ebitda", year) or (
                g(is_, "ebit", year) + g(is_, "da", year)
            )
            ebit = g(is_, "ebit", year)
            net_income = g(is_, "net_income", year)
            total_assets = g(bs, "total_assets", year)
            total_equity = g(bs, "total_equity", year)
            st_debt = g(bs, "st_debt", year)
            lt_debt = g(bs, "lt_debt", year)
            cash = g(bs, "cash", year)
            cfo = g(cfc, "cfo", year)
            capex = g(cfc, "capex", year)

            gross_debt = st_debt + lt_debt
            net_debt = gross_debt - cash
            fcf = cfo + capex  # capex negative

            kpis.setdefault("ebitda_margin", {})[year] = round(ebitda / net_rev, 4) if net_rev else 0
            kpis.setdefault("net_margin", {})[year] = round(net_income / net_rev, 4) if net_rev else 0
            kpis.setdefault("gross_debt", {})[year] = round(gross_debt, 2)
            kpis.setdefault("net_debt", {})[year] = round(net_debt, 2)
            kpis.setdefault("net_leverage", {})[year] = round(net_debt / ebitda, 2) if ebitda else 0
            kpis.setdefault("roa", {})[year] = round(net_income / total_assets, 4) if total_assets else 0
            kpis.setdefault("roe", {})[year] = round(net_income / total_equity, 4) if total_equity else 0
            kpis.setdefault("fcf", {})[year] = round(fcf, 2)
            kpis.setdefault("fcf_conversion", {})[year] = round(fcf / ebitda, 4) if ebitda else 0

        return kpis
