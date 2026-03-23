"""
LBO Model (basic)
- Entry: purchase price = entry EV/EBITDA multiple
- Debt structure: senior + subordinated tranches
- Hold period: 5 years with debt amortization schedule
- Exit: exit EV/EBITDA multiple
- Returns: IRR, MOIC, equity waterfall
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


class LBOInput(BaseModel):
    financials: str = Field(description="JSON financeiro consolidado (output do consolidation_engine)")
    entry_multiple: float = Field(default=7.0, description="Múltiplo de entrada EV/EBITDA")
    exit_multiple: float = Field(default=8.0, description="Múltiplo de saída EV/EBITDA")
    hold_years: int = Field(default=5, description="Período de investimento (anos)")
    debt_structure: str = Field(
        default='{"senior": {"amount_pct_ev": 0.50, "rate": 0.14, "amort_years": 7}, '
        '"mezz": {"amount_pct_ev": 0.15, "rate": 0.18, "amort_years": 7}}',
        description="JSON com estrutura de dívida LBO",
    )
    revenue_cagr: float = Field(default=0.10, description="CAGR de receita durante o hold")
    ebitda_margin_exit: float = Field(default=0.25, description="Margem EBITDA no ano de saída")
    management_fees_pct: float = Field(default=0.02, description="Taxa de gestão anual sobre equity investido")
    transaction_costs_pct: float = Field(default=0.03, description="Custos de transação (% sobre EV de entrada)")


class LBOTool(BaseTool):
    name: str = "lbo_tool"
    description: str = (
        "Modelo LBO simplificado: entrada via múltiplo EV/EBITDA, estrutura de dívida configurável, "
        "saída via múltiplo de saída. Retorna IRR, MOIC, equity waterfall e debt paydown schedule."
    )
    args_schema: type[BaseModel] = LBOInput

    def _run(
        self,
        financials: str,
        entry_multiple: float = 7.0,
        exit_multiple: float = 8.0,
        hold_years: int = 5,
        debt_structure: str = '{"senior": {"amount_pct_ev": 0.50, "rate": 0.14, "amort_years": 7}}',
        revenue_cagr: float = 0.10,
        ebitda_margin_exit: float = 0.25,
        management_fees_pct: float = 0.02,
        transaction_costs_pct: float = 0.03,
    ) -> str:
        try:
            fin: dict = json.loads(financials)
            debt_struct: dict = json.loads(debt_structure)

            is_ = fin.get("income_statement", {})
            years = fin.get("years", [])
            base_year = years[-1] if years else "2024"

            def g(stmt: dict, acct: str, y: str) -> float:
                return float((stmt.get(acct) or {}).get(y, 0) or 0)

            entry_ebitda = g(is_, "ebitda", base_year)
            if not entry_ebitda:
                entry_ebitda = (
                    g(is_, "ebit", base_year) + g(is_, "da", base_year)
                )

            entry_ev = entry_ebitda * entry_multiple
            transaction_costs = entry_ev * transaction_costs_pct

            # Debt tranches
            total_debt = 0.0
            tranches: list[dict] = []
            for tranche_name, params in debt_struct.items():
                amount = entry_ev * params["amount_pct_ev"]
                total_debt += amount
                tranches.append({
                    "name": tranche_name,
                    "amount": amount,
                    "rate": params["rate"],
                    "amort_years": params.get("amort_years", hold_years),
                    "outstanding": amount,
                })

            equity_invested = entry_ev + transaction_costs - total_debt
            if equity_invested <= 0:
                return json.dumps({"error": "Equity investido negativo — reduzir dívida."})

            # Annual projections
            annual_data = []
            cash_flows: list[float] = [-equity_invested]  # Year 0

            entry_revenue = g(is_, "net_revenue", base_year)

            for year in range(1, hold_years + 1):
                rev = entry_revenue * (1 + revenue_cagr) ** year
                margin = (
                    ebitda_margin_exit
                    if year == hold_years
                    else g(is_, "ebitda", base_year) / entry_revenue * (1 + (ebitda_margin_exit - g(is_, "ebitda", base_year) / entry_revenue) * year / hold_years)
                    if entry_revenue else ebitda_margin_exit
                )
                ebitda = rev * margin

                # Interest and amortization
                total_interest = 0.0
                total_amort = 0.0
                for t in tranches:
                    if t["outstanding"] > 0:
                        interest = t["outstanding"] * t["rate"]
                        annual_amort = t["amount"] / t["amort_years"]
                        actual_amort = min(annual_amort, t["outstanding"])
                        t["outstanding"] = max(t["outstanding"] - actual_amort, 0)
                        total_interest += interest
                        total_amort += actual_amort

                mgt_fee = equity_invested * management_fees_pct
                levered_fcf = ebitda - total_interest - total_amort - mgt_fee

                annual_data.append({
                    "year": year,
                    "revenue": round(rev, 0),
                    "ebitda": round(ebitda, 0),
                    "ebitda_margin": round(margin, 4),
                    "interest": round(total_interest, 0),
                    "amortization": round(total_amort, 0),
                    "management_fee": round(mgt_fee, 0),
                    "levered_fcf": round(levered_fcf, 0),
                    "total_debt_outstanding": round(sum(t["outstanding"] for t in tranches), 0),
                })

                # No interim distributions assumed (all CF goes to debt service)
                cash_flows.append(0.0)

            # Exit
            exit_ebitda = annual_data[-1]["ebitda"]
            exit_ev = exit_ebitda * exit_multiple
            remaining_debt = sum(t["outstanding"] for t in tranches)
            exit_equity_proceeds = exit_ev - remaining_debt

            cash_flows[-1] += exit_equity_proceeds

            # IRR and MOIC
            irr = self._calc_irr(cash_flows)
            moic = exit_equity_proceeds / equity_invested if equity_invested else 0

            result = {
                "entry": {
                    "entry_ebitda": round(entry_ebitda, 0),
                    "entry_multiple": entry_multiple,
                    "entry_ev": round(entry_ev, 0),
                    "total_debt": round(total_debt, 0),
                    "transaction_costs": round(transaction_costs, 0),
                    "equity_invested": round(equity_invested, 0),
                    "leverage_ratio": round(total_debt / entry_ebitda, 2) if entry_ebitda else 0,
                },
                "projections": annual_data,
                "exit": {
                    "exit_year": hold_years,
                    "exit_ebitda": round(exit_ebitda, 0),
                    "exit_multiple": exit_multiple,
                    "exit_ev": round(exit_ev, 0),
                    "remaining_debt": round(remaining_debt, 0),
                    "exit_equity_proceeds": round(exit_equity_proceeds, 0),
                },
                "returns": {
                    "irr": round(irr, 4) if irr else None,
                    "irr_pct": f"{round(irr * 100, 1)}%" if irr else "N/A",
                    "moic": round(moic, 2),
                    "equity_invested": round(equity_invested, 0),
                    "exit_equity_proceeds": round(exit_equity_proceeds, 0),
                },
                "cash_flows": [round(cf, 0) for cf in cash_flows],
            }

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro no LBO: {exc}")
            return json.dumps({"error": str(exc)})

    def _calc_irr(self, cash_flows: list[float]) -> float | None:
        """Newton-Raphson IRR calculation."""
        if not cash_flows or cash_flows[0] >= 0:
            return None
        rate = 0.10
        for _ in range(1000):
            npv = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
            d_npv = sum(
                -i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows)
            )
            if abs(d_npv) < 1e-10:
                break
            new_rate = rate - npv / d_npv
            if abs(new_rate - rate) < 1e-8:
                return new_rate
            rate = new_rate
        return rate if -5 < rate < 10 else None
