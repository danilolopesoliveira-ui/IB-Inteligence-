"""
Comps Tool — Trading Comps & Transaction Comps
Builds comparable company / transaction analysis for relative valuation.
"""

from __future__ import annotations

import json
import statistics
from typing import Any

from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


# Default B3 trading comps by sector (EV/EBITDA, P/E, EV/Revenue)
# Updated with approximate 2024 market data — user should update with live data
DEFAULT_COMPS: dict[str, list[dict]] = {
    "varejo": [
        {"ticker": "MGLU3", "name": "Magazine Luiza", "ev_ebitda": 8.5, "p_e": 25.0, "ev_revenue": 0.4},
        {"ticker": "LREN3", "name": "Lojas Renner", "ev_ebitda": 9.2, "p_e": 18.5, "ev_revenue": 1.8},
        {"ticker": "AMER3", "name": "Americanas", "ev_ebitda": None, "p_e": None, "ev_revenue": 0.3},
    ],
    "saude": [
        {"ticker": "HAPV3", "name": "Hapvida", "ev_ebitda": 11.0, "p_e": 22.0, "ev_revenue": 1.5},
        {"ticker": "RDOR3", "name": "Rede D'Or", "ev_ebitda": 12.5, "p_e": 28.0, "ev_revenue": 2.1},
        {"ticker": "FLRY3", "name": "Fleury", "ev_ebitda": 8.8, "p_e": 16.0, "ev_revenue": 1.9},
    ],
    "tecnologia": [
        {"ticker": "TOTS3", "name": "Totvs", "ev_ebitda": 18.5, "p_e": 35.0, "ev_revenue": 4.2},
        {"ticker": "LWSA3", "name": "Locaweb", "ev_ebitda": 14.0, "p_e": 30.0, "ev_revenue": 3.1},
        {"ticker": "CASH3", "name": "Méliuz", "ev_ebitda": 12.0, "p_e": None, "ev_revenue": 2.5},
    ],
    "agronegocio": [
        {"ticker": "SLCE3", "name": "SLC Agrícola", "ev_ebitda": 7.2, "p_e": 12.0, "ev_revenue": 2.0},
        {"ticker": "AGRO3", "name": "BrasilAgro", "ev_ebitda": 8.0, "p_e": 10.5, "ev_revenue": 2.8},
        {"ticker": "TTEN3", "name": "3Tentos", "ev_ebitda": 6.5, "p_e": 11.0, "ev_revenue": 0.8},
    ],
    "industria": [
        {"ticker": "WEGE3", "name": "WEG", "ev_ebitda": 22.0, "p_e": 35.0, "ev_revenue": 4.5},
        {"ticker": "ROMI3", "name": "Romi", "ev_ebitda": 7.5, "p_e": 13.0, "ev_revenue": 1.2},
        {"ticker": "FRAS3", "name": "Fras-le", "ev_ebitda": 8.0, "p_e": 14.0, "ev_revenue": 1.0},
    ],
    "logistica": [
        {"ticker": "RAIL3", "name": "Rumo", "ev_ebitda": 9.5, "p_e": 20.0, "ev_revenue": 3.5},
        {"ticker": "VAMO3", "name": "Vamos", "ev_ebitda": 10.5, "p_e": 22.0, "ev_revenue": 2.8},
        {"ticker": "GETT11", "name": "JSL", "ev_ebitda": 7.8, "p_e": 15.0, "ev_revenue": 0.8},
    ],
    "educacao": [
        {"ticker": "COGN3", "name": "Cogna", "ev_ebitda": 6.5, "p_e": None, "ev_revenue": 1.0},
        {"ticker": "YDUQ3", "name": "Yduqs", "ev_ebitda": 7.2, "p_e": 12.0, "ev_revenue": 1.8},
        {"ticker": "ANIM3", "name": "Ânima", "ev_ebitda": 6.8, "p_e": None, "ev_revenue": 1.5},
    ],
    "financeiro": [
        {"ticker": "ITUB4", "name": "Itaú", "ev_ebitda": None, "p_e": 8.5, "p_bv": 1.8},
        {"ticker": "BBDC4", "name": "Bradesco", "ev_ebitda": None, "p_e": 7.2, "p_bv": 1.1},
        {"ticker": "BBAS3", "name": "Banco do Brasil", "ev_ebitda": None, "p_e": 5.0, "p_bv": 0.9},
    ],
}


class CompsInput(BaseModel):
    target_financials: str = Field(description="JSON com DFs consolidadas da empresa-alvo")
    sector: str = Field(description="Setor da empresa: varejo, saude, tecnologia, agronegocio, industria, logistica, educacao, financeiro")
    custom_comps: str = Field(
        default="[]",
        description=(
            "JSON list de comparáveis customizados. "
            'Formato: [{"name": "Empresa X", "ev_ebitda": 8.5, "p_e": 15.0, "ev_revenue": 2.0, '
            '"ebitda_margin": 0.22, "revenue_growth": 0.15}]'
        ),
    )
    valuation_year: str = Field(default="", description="Ano base para valuation (vazio = último disponível)")
    transaction_comps: str = Field(
        default="[]",
        description=(
            "JSON list de transações comparáveis (M&A). "
            'Formato: [{"target": "Empresa Y", "acquirer": "Fundo Z", "year": 2023, '
            '"ev_ebitda_entry": 9.0, "sector": "saude"}]'
        ),
    )


class CompsTool(BaseTool):
    name: str = "comps_tool"
    description: str = (
        "Análise de comparáveis: trading comps (empresas listadas B3) e transaction comps (M&A). "
        "Calcula implied EV da empresa-alvo via múltiplos medianos e gera football field de valuation."
    )
    args_schema: type[BaseModel] = CompsInput

    def _run(
        self,
        target_financials: str,
        sector: str,
        custom_comps: str = "[]",
        valuation_year: str = "",
        transaction_comps: str = "[]",
    ) -> str:
        try:
            fin = json.loads(target_financials)
            custom = json.loads(custom_comps)
            tx_comps = json.loads(transaction_comps)

            is_ = fin.get("income_statement", {})
            years = fin.get("years", [])
            val_year = valuation_year or (years[-1] if years else "2024")

            def g(stmt, acct, y):
                return float((stmt.get(acct) or {}).get(y, 0) or 0)

            target_ebitda = g(is_, "ebitda", val_year)
            target_revenue = g(is_, "net_revenue", val_year)
            target_net_income = g(is_, "net_income", val_year)

            # Get sector comps
            sector_lower = sector.lower()
            trading_universe = list(DEFAULT_COMPS.get(sector_lower, []))
            trading_universe.extend(custom)

            # Compute statistics
            ev_ebitda_vals = [c["ev_ebitda"] for c in trading_universe if c.get("ev_ebitda")]
            p_e_vals = [c["p_e"] for c in trading_universe if c.get("p_e")]
            ev_rev_vals = [c["ev_revenue"] for c in trading_universe if c.get("ev_revenue")]

            def stats(vals: list[float]) -> dict:
                if not vals:
                    return {"min": None, "q1": None, "median": None, "mean": None, "q3": None, "max": None}
                s = sorted(vals)
                n = len(s)
                return {
                    "min": round(min(s), 2),
                    "q1": round(s[n // 4], 2),
                    "median": round(statistics.median(s), 2),
                    "mean": round(statistics.mean(s), 2),
                    "q3": round(s[3 * n // 4], 2),
                    "max": round(max(s), 2),
                }

            ev_ebitda_stats = stats(ev_ebitda_vals)
            p_e_stats = stats(p_e_vals)
            ev_rev_stats = stats(ev_rev_vals)

            # Implied EV
            implied_ev_from_ebitda = {}
            for label in ["min", "q1", "median", "mean", "q3", "max"]:
                mult = ev_ebitda_stats.get(label)
                if mult and target_ebitda:
                    implied_ev_from_ebitda[label] = round(target_ebitda * mult, 0)

            implied_ev_from_revenue = {}
            for label in ["min", "q1", "median", "mean", "q3", "max"]:
                mult = ev_rev_stats.get(label)
                if mult and target_revenue:
                    implied_ev_from_revenue[label] = round(target_revenue * mult, 0)

            # Transaction comps
            tx_ev_ebitda_vals = [t["ev_ebitda_entry"] for t in tx_comps if t.get("ev_ebitda_entry")]
            tx_stats = stats(tx_ev_ebitda_vals)
            implied_ev_from_tx = {}
            for label in ["min", "q1", "median", "mean", "q3", "max"]:
                mult = tx_stats.get(label)
                if mult and target_ebitda:
                    implied_ev_from_tx[label] = round(target_ebitda * mult, 0)

            # Football field (valuation range summary)
            football_field = []
            if implied_ev_from_ebitda.get("q1") and implied_ev_from_ebitda.get("q3"):
                football_field.append({
                    "method": "Trading Comps — EV/EBITDA",
                    "low": implied_ev_from_ebitda["q1"],
                    "mid": implied_ev_from_ebitda["median"],
                    "high": implied_ev_from_ebitda["q3"],
                    "multiple_range": f"{ev_ebitda_stats['q1']}x – {ev_ebitda_stats['q3']}x",
                })
            if implied_ev_from_revenue.get("q1") and implied_ev_from_revenue.get("q3"):
                football_field.append({
                    "method": "Trading Comps — EV/Revenue",
                    "low": implied_ev_from_revenue["q1"],
                    "mid": implied_ev_from_revenue["median"],
                    "high": implied_ev_from_revenue["q3"],
                    "multiple_range": f"{ev_rev_stats['q1']}x – {ev_rev_stats['q3']}x",
                })
            if implied_ev_from_tx.get("q1") and implied_ev_from_tx.get("q3"):
                football_field.append({
                    "method": "Transaction Comps — EV/EBITDA",
                    "low": implied_ev_from_tx["q1"],
                    "mid": implied_ev_from_tx["median"],
                    "high": implied_ev_from_tx["q3"],
                    "multiple_range": f"{tx_stats['q1']}x – {tx_stats['q3']}x",
                })

            result = {
                "target": {
                    "year": val_year,
                    "ebitda": round(target_ebitda, 0),
                    "net_revenue": round(target_revenue, 0),
                    "net_income": round(target_net_income, 0),
                    "ebitda_margin": round(target_ebitda / target_revenue, 4) if target_revenue else None,
                },
                "trading_comps": {
                    "universe": trading_universe,
                    "sector": sector,
                    "ev_ebitda_stats": ev_ebitda_stats,
                    "p_e_stats": p_e_stats,
                    "ev_revenue_stats": ev_rev_stats,
                    "implied_ev_from_ebitda": implied_ev_from_ebitda,
                    "implied_ev_from_revenue": implied_ev_from_revenue,
                },
                "transaction_comps": {
                    "transactions": tx_comps,
                    "ev_ebitda_stats": tx_stats,
                    "implied_ev": implied_ev_from_tx,
                },
                "football_field": football_field,
            }

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro nos comps: {exc}")
            return json.dumps({"error": str(exc)})
