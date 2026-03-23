"""
Credit Analysis Tool
Computes leverage, coverage, and liquidity ratios for credit assessment.
"""

from __future__ import annotations

import json
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


class CreditAnalysisInput(BaseModel):
    financials: str = Field(description="JSON com DFs consolidadas (output do consolidation_engine)")
    debt_schedule: str = Field(
        default="[]",
        description=(
            "JSON list com tabela de amortização. "
            'Formato: [{"year": "2025", "principal": 1000000, "interest": 140000, "tranche": "CCB"}]'
        ),
    )


class CreditAnalysisTool(BaseTool):
    name: str = "credit_tool"
    description: str = (
        "Análise de crédito completa: leverage ratios, coverage ratios, liquidez, "
        "debt capacity e debt schedule. Retorna scorecard de crédito por ano."
    )
    args_schema: type[BaseModel] = CreditAnalysisInput

    def _run(self, financials: str, debt_schedule: str = "[]") -> str:
        try:
            fin = json.loads(financials)
            schedule = json.loads(debt_schedule)

            is_ = fin.get("income_statement", {})
            bs = fin.get("balance_sheet", {})
            cfc = fin.get("cash_flow", {})
            kpis = fin.get("kpis", {})
            years = fin.get("years", [])

            def g(stmt, acct, y):
                return float((stmt.get(acct) or {}).get(y, 0) or 0)

            credit_metrics: dict[str, dict] = {}

            for year in years:
                ebitda = g(is_, "ebitda", year) or (g(is_, "ebit", year) + g(is_, "da", year))
                ebit = g(is_, "ebit", year)
                net_income = g(is_, "net_income", year)
                fin_exp = abs(g(is_, "financial_expenses", year))
                fin_inc = g(is_, "financial_income", year)
                net_fin = fin_exp - fin_inc

                total_assets = g(bs, "total_assets", year)
                total_equity = g(bs, "total_equity", year)
                total_curr_assets = g(bs, "total_current_assets", year)
                total_curr_liab = g(bs, "total_current_liabilities", year)
                cash = g(bs, "cash", year)
                st_debt = g(bs, "st_debt", year)
                lt_debt = g(bs, "lt_debt", year)
                ar = g(bs, "accounts_receivable", year)
                inventory = g(bs, "inventory", year)
                ap = g(bs, "accounts_payable", year)
                net_rev = g(is_, "net_revenue", year)
                cogs = abs(g(is_, "cogs", year))
                cfo = g(cfc, "cfo", year)

                gross_debt = st_debt + lt_debt
                net_debt = gross_debt - cash
                total_liab = total_assets - total_equity

                # Leverage
                gross_leverage = gross_debt / ebitda if ebitda else None
                net_leverage = net_debt / ebitda if ebitda else None
                debt_to_equity = gross_debt / total_equity if total_equity > 0 else None
                debt_to_assets = total_liab / total_assets if total_assets else None

                # Coverage
                ebitda_coverage = ebitda / net_fin if net_fin > 0 else None
                ebit_coverage = ebit / net_fin if net_fin > 0 else None
                dscr = cfo / (net_fin + st_debt) if (net_fin + st_debt) > 0 else None

                # Liquidity
                current_ratio = total_curr_assets / total_curr_liab if total_curr_liab else None
                quick_ratio = (total_curr_assets - inventory) / total_curr_liab if total_curr_liab else None
                cash_ratio = cash / total_curr_liab if total_curr_liab else None

                # Working capital days
                dso = (ar / net_rev * 365) if net_rev else None        # days sales outstanding
                dpo = (ap / cogs * 365) if cogs else None              # days payable outstanding
                dio = (inventory / cogs * 365) if cogs else None       # days inventory outstanding
                ccc = (dso or 0) + (dio or 0) - (dpo or 0)            # cash conversion cycle

                # Debt capacity (max debt at 3.5x EBITDA)
                debt_capacity = ebitda * 3.5 if ebitda else 0
                additional_debt_capacity = max(debt_capacity - gross_debt, 0)

                # Schedule match
                year_schedule = [s for s in schedule if str(s.get("year")) == str(year)]

                def r(val):
                    return round(val, 3) if val is not None else None

                credit_metrics[year] = {
                    "leverage": {
                        "gross_debt": round(gross_debt, 0),
                        "net_debt": round(net_debt, 0),
                        "ebitda": round(ebitda, 0),
                        "gross_leverage": r(gross_leverage),
                        "net_leverage": r(net_leverage),
                        "debt_to_equity": r(debt_to_equity),
                        "debt_to_assets": r(debt_to_assets),
                    },
                    "coverage": {
                        "ebitda_interest_coverage": r(ebitda_coverage),
                        "ebit_interest_coverage": r(ebit_coverage),
                        "dscr": r(dscr),
                    },
                    "liquidity": {
                        "current_ratio": r(current_ratio),
                        "quick_ratio": r(quick_ratio),
                        "cash_ratio": r(cash_ratio),
                        "working_capital": round(total_curr_assets - total_curr_liab, 0),
                    },
                    "working_capital_days": {
                        "dso_days": r(dso),
                        "dpo_days": r(dpo),
                        "dio_days": r(dio),
                        "cash_conversion_cycle_days": r(ccc),
                    },
                    "debt_capacity": {
                        "max_debt_3_5x": round(debt_capacity, 0),
                        "current_gross_debt": round(gross_debt, 0),
                        "additional_capacity": round(additional_debt_capacity, 0),
                    },
                    "debt_schedule": year_schedule,
                    "credit_score": self._score_credit(
                        net_leverage, ebitda_coverage, current_ratio, dscr
                    ),
                }

            # Net financial expenses by year (needed for stress test)
            net_fin_by_year = {}
            for year in years:
                fin_exp = abs(g(is_, "financial_expenses", year))
                fin_inc = g(is_, "financial_income", year)
                net_fin_by_year[year] = fin_exp - fin_inc

            stress = self._stress_test(credit_metrics, years, net_fin_by_year)

            return json.dumps(
                {
                    "years": years,
                    "credit_analysis": credit_metrics,
                    "stress_test": stress,
                },
                ensure_ascii=False, indent=2, default=str,
            )

        except Exception as exc:
            logger.error(f"Erro na análise de crédito: {exc}")
            return json.dumps({"error": str(exc)})

    def _score_credit(
        self,
        net_leverage: float | None,
        coverage: float | None,
        current_ratio: float | None,
        dscr: float | None,
    ) -> dict:
        score = 100
        flags = []

        if net_leverage is not None:
            if net_leverage > 5: score -= 30; flags.append("Alavancagem crítica >5x")
            elif net_leverage > 4: score -= 20; flags.append("Alavancagem elevada >4x")
            elif net_leverage > 3: score -= 10; flags.append("Alavancagem moderada >3x")

        if coverage is not None:
            if coverage < 1.5: score -= 25; flags.append("Cobertura de juros insuficiente <1.5x")
            elif coverage < 2.5: score -= 10; flags.append("Cobertura de juros baixa <2.5x")

        if current_ratio is not None:
            if current_ratio < 1.0: score -= 20; flags.append("Liquidez corrente <1.0 — risco de insolvência CP")
            elif current_ratio < 1.2: score -= 5; flags.append("Liquidez corrente apertada")

        if dscr is not None:
            if dscr < 1.0: score -= 20; flags.append("DSCR <1.0 — caixa insuficiente para serviço da dívida")
            elif dscr < 1.25: score -= 10; flags.append("DSCR baixo <1.25")

        score = max(score, 0)
        rating = (
            "AAA-AA" if score >= 90 else
            "A" if score >= 80 else
            "BBB" if score >= 70 else
            "BB" if score >= 60 else
            "B" if score >= 50 else
            "CCC-D"
        )

        return {"score": score, "implied_rating": rating, "flags": flags}

    def _stress_test(
        self,
        credit_metrics: dict,
        years: list,
        net_fin_by_year: dict,
        covenant_leverage_max: float = 3.5,
        covenant_coverage_min: float = 2.5,
    ) -> dict:
        """
        Runs EBITDA stress scenarios (bull/base/bear/stressed) and identifies
        at which shock level each covenant is breached.
        """
        scenarios = {
            "bull":     +0.15,   # EBITDA +15%
            "base":      0.00,   # sem alteração
            "bear":     -0.15,   # EBITDA -15%
            "stressed": -0.30,   # EBITDA -30%
        }

        results = {}
        breach_threshold = {}  # metric -> minimum EBITDA shock that causes breach

        for scenario_name, shock in scenarios.items():
            scenario_years = {}
            for year in years:
                base = credit_metrics.get(year, {})
                base_ebitda = base.get("leverage", {}).get("ebitda", 0)
                gross_debt = base.get("leverage", {}).get("gross_debt", 0)
                net_debt = base.get("leverage", {}).get("net_debt", 0)
                net_fin = net_fin_by_year.get(year, 0)

                stressed_ebitda = base_ebitda * (1 + shock)

                net_lev = round(net_debt / stressed_ebitda, 3) if stressed_ebitda else None
                ebitda_cov = round(stressed_ebitda / net_fin, 3) if net_fin > 0 else None

                lev_breach = net_lev is not None and net_lev > covenant_leverage_max
                cov_breach = ebitda_cov is not None and ebitda_cov < covenant_coverage_min

                scenario_years[year] = {
                    "ebitda_shocked": round(stressed_ebitda, 0),
                    "ebitda_change_pct": f"{shock*100:+.0f}%",
                    "net_leverage": net_lev,
                    "ebitda_interest_coverage": ebitda_cov,
                    "covenant_leverage_breach": lev_breach,
                    "covenant_coverage_breach": cov_breach,
                    "status": "BREACH" if (lev_breach or cov_breach) else "OK",
                }
            results[scenario_name] = scenario_years

        # Find breach threshold: how much EBITDA can fall before covenant breach
        for year in years:
            base = credit_metrics.get(year, {})
            base_ebitda = base.get("leverage", {}).get("ebitda", 0)
            net_debt = base.get("leverage", {}).get("net_debt", 0)
            net_fin = net_fin_by_year.get(year, 0)

            # Leverage: net_debt / (ebitda * (1+x)) = max → x = net_debt/(max*ebitda) - 1
            lev_break = None
            if base_ebitda and covenant_leverage_max:
                lev_break_ebitda = net_debt / covenant_leverage_max
                lev_break = round((lev_break_ebitda - base_ebitda) / base_ebitda * 100, 1) if base_ebitda else None

            # Coverage: (ebitda * (1+x)) / net_fin = min → x = (min*net_fin/ebitda) - 1
            cov_break = None
            if base_ebitda and net_fin:
                cov_break_ebitda = covenant_coverage_min * net_fin
                cov_break = round((cov_break_ebitda - base_ebitda) / base_ebitda * 100, 1)

            breach_threshold[year] = {
                "leverage_breach_at_ebitda_change_pct": f"{lev_break:+.1f}%" if lev_break is not None else "N/A",
                "coverage_breach_at_ebitda_change_pct": f"{cov_break:+.1f}%" if cov_break is not None else "N/A",
                "interpretation": (
                    f"Covenant de alavancagem breachado se EBITDA cair {abs(lev_break):.1f}%"
                    if lev_break is not None and lev_break < 0 else
                    "Alavancagem confortável mesmo em cenário estressado"
                ),
            }

        return {
            "scenarios": results,
            "covenant_breach_thresholds": breach_threshold,
            "covenants_tested": {
                "net_leverage_max": covenant_leverage_max,
                "ebitda_interest_coverage_min": covenant_coverage_min,
            },
        }
