"""
DCF Model (FCFF approach)
- Projections: revenue growth, margins, reinvestment rate
- WACC: Kd * (1-t) * D/V + Ke * E/V (CAPM)
- Terminal Value: Gordon growth or exit multiple
- Sensitivity analysis: WACC vs. terminal growth rate
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


class DCFInput(BaseModel):
    financials: str = Field(
        description="JSON com histórico financeiro consolidado (output do consolidation_engine)"
    )
    projections: str = Field(
        description=(
            "JSON com premissas de projeção. Exemplo: "
            '{"revenue_growth": [0.15, 0.12, 0.10, 0.08, 0.07], '
            '"ebitda_margin": [0.22, 0.23, 0.24, 0.25, 0.25], '
            '"da_pct_revenue": 0.04, "capex_pct_revenue": 0.06, '
            '"nwc_pct_revenue": 0.08, "tax_rate": 0.34}'
        )
    )
    wacc_inputs: str = Field(
        description=(
            "JSON com inputs para WACC. Exemplo: "
            '{"risk_free_rate": 0.1375, "beta": 1.1, "erp": 0.055, '
            '"country_risk": 0.028, "cost_of_debt": 0.14, "tax_rate": 0.34, '
            '"debt_weight": 0.35}'
        )
    )
    terminal_growth: float = Field(default=0.04, description="Taxa de crescimento na perpetuidade")
    terminal_method: str = Field(
        default="gordon", description="Método de terminal value: 'gordon' ou 'exit_multiple'"
    )
    exit_multiple: float = Field(default=7.0, description="Múltiplo EV/EBITDA de saída (se exit_multiple)")
    base_year: str = Field(default="", description="Ano base histórico (ex: '2024')")
    projection_years: int = Field(default=5, description="Número de anos de projeção explícita")


class DCFTool(BaseTool):
    name: str = "dcf_tool"
    description: str = (
        "Modelo DCF (FCFF) completo com WACC, terminal value e análise de sensibilidade. "
        "Retorna Enterprise Value, Equity Value, range de avaliação e tabela de sensibilidade."
    )
    args_schema: type[BaseModel] = DCFInput

    def _run(
        self,
        financials: str,
        projections: str,
        wacc_inputs: str,
        terminal_growth: float = 0.04,
        terminal_method: str = "gordon",
        exit_multiple: float = 7.0,
        base_year: str = "",
        projection_years: int = 5,
    ) -> str:
        try:
            fin: dict = json.loads(financials)
            proj: dict = json.loads(projections)
            wacc_inp: dict = json.loads(wacc_inputs)

            # Extract base metrics
            hist_is = fin.get("income_statement", {})
            hist_bs = fin.get("balance_sheet", {})
            hist_cfc = fin.get("cash_flow", {})
            years = fin.get("years", [])
            base_year = base_year or (years[-1] if years else "2024")

            def g(stmt: dict, acct: str, y: str) -> float:
                return float((stmt.get(acct) or {}).get(y, 0) or 0)

            base_revenue = g(hist_is, "net_revenue", base_year)
            base_ebitda_margin = (
                g(hist_is, "ebitda", base_year) / base_revenue if base_revenue else 0
            )
            gross_debt = g(hist_bs, "st_debt", base_year) + g(hist_bs, "lt_debt", base_year)
            cash = g(hist_bs, "cash", base_year)
            minority_interest = g(hist_bs, "minority_interest", base_year)
            shares_outstanding = float(fin.get("shares_outstanding", 1_000_000))

            # WACC calculation
            wacc = self._calc_wacc(wacc_inp)

            # Projection
            fcff_list, proj_data = self._project_fcff(
                base_revenue=base_revenue,
                revenue_growth=proj.get("revenue_growth", [0.10] * projection_years),
                ebitda_margin=proj.get("ebitda_margin", [base_ebitda_margin] * projection_years),
                da_pct=proj.get("da_pct_revenue", 0.04),
                capex_pct=proj.get("capex_pct_revenue", 0.06),
                nwc_pct=proj.get("nwc_pct_revenue", 0.08),
                tax_rate=proj.get("tax_rate", 0.34),
                n_years=projection_years,
            )

            # Terminal Value
            last_ebitda = proj_data[-1]["ebitda"]
            last_fcff = fcff_list[-1]
            if terminal_method == "gordon":
                tv = last_fcff * (1 + terminal_growth) / (wacc - terminal_growth)
            else:
                tv = last_ebitda * exit_multiple

            # DCF calculation
            pv_fcff = sum(
                fcff / (1 + wacc) ** (i + 1) for i, fcff in enumerate(fcff_list)
            )
            pv_tv = tv / (1 + wacc) ** projection_years
            enterprise_value = pv_fcff + pv_tv

            # Bridge to equity
            equity_value = enterprise_value - gross_debt + cash - minority_interest

            # Sensitivity table (WACC ± 150bps vs. g ± 100bps)
            sensitivity = self._sensitivity_table(
                fcff_list, tv, terminal_method, terminal_growth,
                exit_multiple, wacc, projection_years, gross_debt, cash, minority_interest
            )

            result = {
                "base_year": base_year,
                "wacc": round(wacc, 4),
                "wacc_components": self._wacc_breakdown(wacc_inp),
                "projection": proj_data,
                "fcff_list": [round(f, 0) for f in fcff_list],
                "pv_fcff": round(pv_fcff, 0),
                "terminal_value": round(tv, 0),
                "pv_terminal_value": round(pv_tv, 0),
                "enterprise_value": round(enterprise_value, 0),
                "gross_debt": round(gross_debt, 0),
                "cash": round(cash, 0),
                "minority_interest": round(minority_interest, 0),
                "equity_value": round(equity_value, 0),
                "implied_ev_ebitda": round(enterprise_value / last_ebitda, 2) if last_ebitda else None,
                "sensitivity_ev": sensitivity,
            }

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro no DCF: {exc}")
            return json.dumps({"error": str(exc)})

    def _calc_wacc(self, inp: dict) -> float:
        rf = inp.get("risk_free_rate", 0.1375)
        beta = inp.get("beta", 1.0)
        erp = inp.get("erp", 0.055)
        crp = inp.get("country_risk", 0.028)
        kd = inp.get("cost_of_debt", 0.14)
        tax = inp.get("tax_rate", 0.34)
        d_weight = inp.get("debt_weight", 0.30)
        e_weight = 1 - d_weight

        ke = rf + beta * erp + crp
        wacc = ke * e_weight + kd * (1 - tax) * d_weight
        return wacc

    def _wacc_breakdown(self, inp: dict) -> dict:
        rf = inp.get("risk_free_rate", 0.1375)
        beta = inp.get("beta", 1.0)
        erp = inp.get("erp", 0.055)
        crp = inp.get("country_risk", 0.028)
        kd = inp.get("cost_of_debt", 0.14)
        tax = inp.get("tax_rate", 0.34)
        d_weight = inp.get("debt_weight", 0.30)
        e_weight = 1 - d_weight
        ke = rf + beta * erp + crp
        return {
            "ke": round(ke, 4),
            "kd_after_tax": round(kd * (1 - tax), 4),
            "e_weight": round(e_weight, 4),
            "d_weight": round(d_weight, 4),
            "wacc": round(self._calc_wacc(inp), 4),
        }

    def _project_fcff(
        self,
        base_revenue: float,
        revenue_growth: list[float],
        ebitda_margin: list[float],
        da_pct: float,
        capex_pct: float,
        nwc_pct: float,
        tax_rate: float,
        n_years: int,
    ) -> tuple[list[float], list[dict]]:
        proj_data = []
        fcff_list = []
        prev_nwc = base_revenue * nwc_pct
        rev = base_revenue

        for i in range(n_years):
            growth = revenue_growth[i] if i < len(revenue_growth) else revenue_growth[-1]
            margin = ebitda_margin[i] if i < len(ebitda_margin) else ebitda_margin[-1]

            rev = rev * (1 + growth)
            ebitda = rev * margin
            da = rev * da_pct
            ebit = ebitda - da
            nopat = ebit * (1 - tax_rate)
            capex = rev * capex_pct
            nwc = rev * nwc_pct
            delta_nwc = nwc - prev_nwc
            fcff = nopat + da - capex - delta_nwc
            prev_nwc = nwc

            proj_data.append({
                "year": f"P{i+1}",
                "revenue": round(rev, 0),
                "ebitda": round(ebitda, 0),
                "ebitda_margin": round(margin, 4),
                "da": round(da, 0),
                "ebit": round(ebit, 0),
                "nopat": round(nopat, 0),
                "capex": round(-capex, 0),
                "delta_nwc": round(-delta_nwc, 0),
                "fcff": round(fcff, 0),
            })
            fcff_list.append(fcff)

        return fcff_list, proj_data

    def _sensitivity_table(
        self,
        fcff_list: list[float],
        tv: float,
        terminal_method: str,
        terminal_growth: float,
        exit_multiple: float,
        base_wacc: float,
        projection_years: int,
        gross_debt: float,
        cash: float,
        minority_interest: float,
    ) -> dict:
        wacc_deltas = [-0.015, -0.010, -0.005, 0, 0.005, 0.010, 0.015]
        g_deltas = [-0.010, -0.005, 0, 0.005, 0.010]
        last_fcff = fcff_list[-1]

        table: dict[str, dict[str, float]] = {}
        for dg in g_deltas:
            g_val = round(terminal_growth + dg, 4)
            row = {}
            for dw in wacc_deltas:
                w = base_wacc + dw
                if terminal_method == "gordon" and w > g_val:
                    tv_adj = last_fcff * (1 + g_val) / (w - g_val)
                else:
                    tv_adj = tv  # exit multiple unchanged

                pv_fcff = sum(f / (1 + w) ** (i + 1) for i, f in enumerate(fcff_list))
                pv_tv = tv_adj / (1 + w) ** projection_years
                ev = pv_fcff + pv_tv
                eq = ev - gross_debt + cash - minority_interest
                row[f"wacc_{round(w*100,1)}%"] = round(ev, 0)
            table[f"g_{round(g_val*100,1)}%"] = row

        return table
