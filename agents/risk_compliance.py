"""
Risk & Compliance Agent
Reviews financial model assumptions, flags red flags, checks covenant compliance,
and validates contingent liabilities and off-balance-sheet risks.
"""

from __future__ import annotations

import os

from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import json
from loguru import logger
from tools.finance.guarantee_analysis import GuaranteeAnalysisTool


# ---------------------------------------------------------------------------
# Red Flag Checker Tool
# ---------------------------------------------------------------------------

class RedFlagInput(BaseModel):
    financials: str = Field(description="JSON com DFs consolidadas ajustadas")
    dcf_output: str = Field(default="{}", description="JSON output do DCF")
    lbo_output: str = Field(default="{}", description="JSON output do LBO")
    stress_test: str = Field(default="{}", description="JSON stress_test do credit_analysis (cenarios base/bear/stressed e breach thresholds)")


class RedFlagCheckerTool(BaseTool):
    name: str = "red_flag_checker"
    description: str = (
        "Analisa DFs consolidadas e outputs de modelos financeiros em busca de red flags: "
        "alavancagem excessiva, deterioração de margens, concentração de receita, "
        "capital de giro negativo, contingências materiais e premissas agressivas de valuation."
    )
    args_schema: type[BaseModel] = RedFlagInput

    def _run(self, financials: str, dcf_output: str = "{}", lbo_output: str = "{}", stress_test: str = "{}") -> str:
        try:
            fin = json.loads(financials)
            dcf = json.loads(dcf_output)
            lbo = json.loads(lbo_output)
            stress = json.loads(stress_test)

            flags = []
            is_ = fin.get("income_statement", {})
            bs = fin.get("balance_sheet", {})
            kpis = fin.get("kpis", {})
            years = fin.get("years", [])

            def g(stmt, acct, y):
                return float((stmt.get(acct) or {}).get(y, 0) or 0)

            def gk(acct, y):
                return float((kpis.get(acct) or {}).get(y, 0) or 0)

            for year in years:
                # Leverage
                net_lev = gk("net_leverage", year)
                if net_lev > 4.0:
                    flags.append({
                        "year": year, "severity": "HIGH",
                        "category": "ALAVANCAGEM",
                        "flag": f"Alavancagem líquida elevada: {net_lev:.1f}x (threshold: 4.0x). "
                                "Risco de covenant breach e refinanciamento.",
                    })
                elif net_lev > 3.0:
                    flags.append({
                        "year": year, "severity": "MEDIUM",
                        "category": "ALAVANCAGEM",
                        "flag": f"Alavancagem líquida moderada: {net_lev:.1f}x.",
                    })

                # EBITDA margin
                margin = gk("ebitda_margin", year)
                if 0 < margin < 0.05:
                    flags.append({
                        "year": year, "severity": "HIGH",
                        "category": "RENTABILIDADE",
                        "flag": f"Margem EBITDA muito baixa: {margin*100:.1f}%. "
                                "Negócio com baixa geração de caixa operacional.",
                    })

                # Negative FCF
                fcf = gk("fcf", year)
                ebitda = g(is_, "ebitda", year)
                if fcf < 0 and ebitda > 0:
                    flags.append({
                        "year": year, "severity": "MEDIUM",
                        "category": "FLUXO_DE_CAIXA",
                        "flag": f"FCF negativo (R${fcf:,.0f}) com EBITDA positivo. "
                                "Verificar CAPEX excessivo ou deterioração de capital de giro.",
                    })

                # Negative working capital
                curr_assets = g(bs, "total_current_assets", year)
                curr_liab = g(bs, "total_current_liabilities", year)
                if curr_assets and curr_liab and curr_assets < curr_liab:
                    flags.append({
                        "year": year, "severity": "HIGH",
                        "category": "LIQUIDEZ",
                        "flag": f"Capital de giro negativo: ativo circ. R${curr_assets:,.0f} < "
                                f"passivo circ. R${curr_liab:,.0f}. Risco de liquidez de curto prazo.",
                    })

                # Cash coverage
                cash = g(bs, "cash", year)
                st_debt = g(bs, "st_debt", year)
                if st_debt > 0 and cash < st_debt * 0.5:
                    flags.append({
                        "year": year, "severity": "HIGH",
                        "category": "LIQUIDEZ",
                        "flag": f"Caixa (R${cash:,.0f}) cobre menos de 50% da dívida CP "
                                f"(R${st_debt:,.0f}). Risco de refinanciamento iminente.",
                    })

            # DCF assumption check
            if dcf:
                wacc = dcf.get("wacc", 0)
                proj = dcf.get("projection", [])
                if wacc < 0.08:
                    flags.append({
                        "year": "N/A", "severity": "HIGH",
                        "category": "VALUATION",
                        "flag": f"WACC muito baixo: {wacc*100:.1f}%. Verificar inputs de custo de capital.",
                    })
                if proj:
                    last_margin = proj[-1].get("ebitda_margin", 0)
                    first_margin = proj[0].get("ebitda_margin", 0)
                    if last_margin - first_margin > 0.10:
                        flags.append({
                            "year": "Projeção", "severity": "MEDIUM",
                            "category": "VALUATION",
                            "flag": f"Expansão de margem EBITDA de {first_margin*100:.1f}% "
                                    f"→ {last_margin*100:.1f}% parece agressiva. "
                                    "Validar benchmarks setoriais.",
                        })

            # LBO check
            if lbo:
                irr = (lbo.get("returns") or {}).get("irr", 0) or 0
                if irr and irr < 0.15:
                    flags.append({
                        "year": "LBO", "severity": "HIGH",
                        "category": "RETORNO_PE",
                        "flag": f"IRR do LBO abaixo de threshold PE ({irr*100:.1f}% < 15%). "
                                "Dificuldade de atrair capital de fundo.",
                    })

            # Stress test flags
            scenario_summary = []
            if stress:
                scenarios = stress.get("scenarios", {})
                thresholds = stress.get("covenant_breach_thresholds", {})
                for scenario_name in ["bear", "stressed"]:
                    s_data = scenarios.get(scenario_name, {})
                    for year, yr_data in s_data.items():
                        if yr_data.get("status") == "BREACH":
                            lev_b = yr_data.get("covenant_leverage_breach", False)
                            cov_b = yr_data.get("covenant_coverage_breach", False)
                            breached = []
                            if lev_b:
                                breached.append(f"Net Leverage {yr_data.get('net_leverage')}x > max")
                            if cov_b:
                                breached.append(f"Coverage {yr_data.get('ebitda_interest_coverage')}x < min")
                            severity = "HIGH" if scenario_name == "stressed" else "MEDIUM"
                            flags.append({
                                "year": year, "severity": severity,
                                "category": "STRESS_SCENARIO",
                                "flag": (
                                    f"Cenario {scenario_name.upper()} ({yr_data.get('ebitda_change_pct')} EBITDA): "
                                    f"covenant breach em {', '.join(breached)}."
                                ),
                            })

                for year, thr in thresholds.items():
                    lev_thr = thr.get("leverage_breach_at_ebitda_change_pct", "N/A")
                    cov_thr = thr.get("coverage_breach_at_ebitda_change_pct", "N/A")
                    scenario_summary.append({
                        "year": year,
                        "leverage_covenant_breach_at": lev_thr,
                        "coverage_covenant_breach_at": cov_thr,
                        "interpretation": thr.get("interpretation", ""),
                    })

            summary = {
                "total_flags": len(flags),
                "high_severity": sum(1 for f in flags if f["severity"] == "HIGH"),
                "medium_severity": sum(1 for f in flags if f["severity"] == "MEDIUM"),
                "red_flags": flags,
                "investment_grade": len([f for f in flags if f["severity"] == "HIGH"]) == 0,
                "scenario_analysis": scenario_summary,
            }

            return json.dumps(summary, ensure_ascii=False, indent=2)

        except Exception as exc:
            logger.error(f"Erro no red flag checker: {exc}")
            return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Covenant Checker Tool
# ---------------------------------------------------------------------------

class CovenantInput(BaseModel):
    financials: str = Field(description="JSON com DFs consolidadas")
    covenants: str = Field(
        default='[{"name": "Net Leverage", "metric": "net_leverage", "max": 3.5}, '
                '{"name": "Interest Coverage", "metric": "interest_coverage", "min": 2.5}]',
        description="JSON list de covenants financeiros a verificar",
    )


class CovenantCheckerTool(BaseTool):
    name: str = "covenant_checker"
    description: str = (
        "Verifica compliance com covenants financeiros de contratos de dívida. "
        "Compara métricas reais (leverage, cobertura, liquidez) contra thresholds contratuais."
    )
    args_schema: type[BaseModel] = CovenantInput

    def _run(self, financials: str, covenants: str = "[]") -> str:
        try:
            fin = json.loads(financials)
            cov_list = json.loads(covenants)
            kpis = fin.get("kpis", {})
            is_ = fin.get("income_statement", {})
            years = fin.get("years", [])

            def g(stmt, acct, y):
                return float((stmt.get(acct) or {}).get(y, 0) or 0)

            # Compute additional metrics not in KPIs
            def get_metric(metric: str, year: str) -> float | None:
                kpi_val = (kpis.get(metric) or {}).get(year)
                if kpi_val is not None:
                    return float(kpi_val)
                if metric == "interest_coverage":
                    ebitda = g(is_, "ebitda", year)
                    fin_exp = abs(g(is_, "financial_expenses", year))
                    return ebitda / fin_exp if fin_exp else None
                return None

            results = []
            for covenant in cov_list:
                cov_name = covenant.get("name", "")
                metric = covenant.get("metric", "")
                max_val = covenant.get("max")
                min_val = covenant.get("min")

                for year in years:
                    actual = get_metric(metric, year)
                    if actual is None:
                        continue

                    breach = False
                    headroom = None
                    if max_val is not None:
                        breach = actual > max_val
                        headroom = max_val - actual
                    elif min_val is not None:
                        breach = actual < min_val
                        headroom = actual - min_val

                    results.append({
                        "covenant": cov_name,
                        "metric": metric,
                        "year": year,
                        "actual": round(actual, 3),
                        "threshold": max_val if max_val is not None else min_val,
                        "type": "max" if max_val is not None else "min",
                        "breach": breach,
                        "headroom": round(headroom, 3) if headroom is not None else None,
                        "status": "BREACH" if breach else ("WARNING" if headroom is not None and abs(headroom) < 0.3 else "OK"),
                    })

            summary = {
                "total_covenants_checked": len(cov_list) * len(years),
                "breaches": sum(1 for r in results if r["breach"]),
                "warnings": sum(1 for r in results if r["status"] == "WARNING"),
                "results": results,
            }
            return json.dumps(summary, ensure_ascii=False, indent=2)

        except Exception as exc:
            logger.error(f"Erro no covenant checker: {exc}")
            return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def build_risk_compliance_agent() -> Agent:
    model = os.getenv("AGENT_MODEL", "claude-sonnet-4-6")

    from tools.knowledge.knowledge_search import KnowledgeSearchTool

    return Agent(
        role="Risk & Compliance Officer",
        goal=(
            "Identificar red flags financeiros, operacionais e de compliance nas DFs e modelos, "
            "verificar covenant compliance e emitir parecer de riscos para o comite de investimentos. "
            "OBRIGATORIO: a analise de risco DCM DEVE aplicar o Guia Perfeccionista Sec.12 do "
            "Manual_Analise_Credito_v4_1.docx (analise forense de DRE: Receita, CPV, SGA, EBITDA, "
            "Resultado Financeiro, IR, Qualidade do Lucro; e Balanco: Caixa, Recebiveis, Estoques, "
            "Imobilizado, Partes Relacionadas, Liquidez). "
            "A analise de risco ECM DEVE verificar os 10 Red Flags e 5 Yellow Flags do "
            "Manual_ECM_IB.docx Sec.10 e 12, mais compliance B3/CVM (Sec.8). "
            "Consulte knowledge_search no inicio de cada analise para alinhar com os Modelos."
        ),
        backstory=(
            "Voce e um especialista em risco de credito e compliance com experiencia em "
            "analise de due diligence para bancos de investimento e fundos de PE. "
            "Ja participou de mais de 150 processos de credito e ECM no Brasil, com foco em "
            "identificar riscos ocultos que nao aparecem nos headlines do modelo financeiro. "
            "FRAMEWORK DCM — Guia Perfeccionista (Manual_Analise_Credito_v4_1.docx Sec.12): "
            "voce inspeciona CADA linha da DRE com flags especificos: "
            "(Receita) crescimento organico vs aquisicoes, concentracao top-5 clientes >40%, antecipacao; "
            "(CPV) variacao vs benchmark setorial, mudanca de criterio contabil, obsolescencia; "
            "(SGA) variacao acima de receita, custos nao recorrentes mascarados, capitalizacao; "
            "(EBITDA) ajustes nao recorrentes >5% receita, EBITDA ajustado vs reportado gap >15%; "
            "(Resultado Financeiro) juros capitalizados, derivativos especulativos, passivo oculto; "
            "(IR) ETR vs aliquota nominal >5pp, beneficio fiscal nao sustentavel, diferido crescente; "
            "(Qualidade Lucro) accruals >10% receita, CFO/EBITDA <0.7 por 2+ anos, ciclo conversao caixa. "
            "E CADA linha do Balanco: "
            "(Caixa) aplicacoes restritas, caixa de BNDES com restricoes, concentracao bancaria; "
            "(Recebiveis) provisao vs perda historica, concentracao, aging >90 dias >15%; "
            "(Estoques) giro abaixo do setor, provisao obsolescencia, FIFO vs media ponderada; "
            "(Imobilizado) CAPEX vs D&A ratio, laudos independentes, ativos ociosos; "
            "(Partes Relacionadas) transacoes >5% receita, precos de mercado, aprovacao conselho; "
            "(Liquidez) corrente <1.0x, DSCR <1.2x, ciclo financeiro deteriorando. "
            "FRAMEWORK ECM — Manual_ECM_IB.docx Sec.10 (10 Red Flags que impedem a operacao): "
            "contingencias juridicas >20% equity, EBITDA negativo 2+ anos, concentracao receita >50%, "
            "controlador sem free float plan, governanca (tag along <100% Novo Mercado), "
            "auditoria qualificada, passivo ambiental material, LGPD/regulatorio critico, "
            "litigio CVM/BACEN pendente, modelo de negocio em disrupcao sem plano claro. "
            "5 Yellow Flags (disclosure obrigatorio no prospecto): alavancagem >3x, margem em queda "
            "2 anos, dependencia de subsidio/incentivo fiscal, mercado concentrado (HHI>2500), "
            "capex relevante sem retorno comprovado. "
            "Seu parecer e o ultimo filtro antes da apresentacao ao comite — "
            "voce e conhecido por ser rigoroso e independente, nunca flexibilizando "
            "analise de risco por pressao comercial."
        ),
        tools=[
            KnowledgeSearchTool(),
            RedFlagCheckerTool(),
            CovenantCheckerTool(),
            GuaranteeAnalysisTool(),
        ],
        llm=model,
        verbose=True,
        allow_delegation=False,
        max_iter=4,
    )


RiskComplianceAgent = build_risk_compliance_agent
