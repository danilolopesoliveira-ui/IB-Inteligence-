"""
DCM Tools — Bond Pricing & Debt Structuring
Ferramentas para o agente DCM Specialist:
- BondPricingTool: precificacao de debentures (PU, YTM, Duration, DV01, sensibilidade)
- DebtStructuringTool: recomendacao de estrutura e covenants de mercado
"""

from __future__ import annotations

import json
import math
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# BOND PRICING TOOL
# ---------------------------------------------------------------------------

class BondPricingInput(BaseModel):
    face_value: float = Field(
        default=1000.0,
        description="Valor nominal unitario da debenture (VNe), em R$. Padrao: 1000.00",
    )
    coupon_rate: float = Field(
        description=(
            "Taxa de juros do cupom em % a.a. Para CDI+, informar apenas o spread (ex: 1.75 para CDI+1.75%). "
            "Para IPCA+, informar a taxa real (ex: 6.50 para IPCA+6.50%). "
            "Para prefixado, informar a taxa total (ex: 13.75)."
        )
    )
    indexer: str = Field(
        default="CDI+",
        description="Indexador da remuneracao: 'CDI+', 'IPCA+', 'PRE' (prefixado)",
    )
    base_rate: float = Field(
        default=0.0,
        description=(
            "Taxa base do indexador em % a.a. Para CDI+: CDI atual (ex: 10.50). "
            "Para IPCA+: IPCA acumulado 12m (ex: 4.50). Para PRE: deixar 0."
        ),
    )
    maturity_years: float = Field(
        description="Prazo ate o vencimento em anos (ex: 5.0 para 5 anos)",
    )
    coupon_frequency: int = Field(
        default=2,
        description="Frequencia de pagamento de cupons por ano: 1 (anual), 2 (semestral), 4 (trimestral)",
    )
    discount_rate: float = Field(
        default=0.0,
        description=(
            "Taxa de desconto de mercado em % a.a. (taxa total, incluindo base + spread). "
            "Se 0, usa a taxa de emissao como taxa de desconto (PU = par)."
        ),
    )
    amortization: str = Field(
        default="bullet",
        description="Perfil de amortizacao: 'bullet' (pagamento unico no vencimento) ou 'linear' (amortizacoes iguais)",
    )


class BondPricingTool(BaseTool):
    name: str = "bond_pricing"
    description: str = (
        "Precifica debentures e titulos de renda fixa privada: calcula PU (preco unitario), "
        "YTM (yield to maturity), Duration de Macaulay, Duration Modificada e DV01. "
        "Tambem gera tabela de sensibilidade de preco por variacao de taxa (+/- 25, 50, 100 bps). "
        "Suporta CDI+, IPCA+ e taxa prefixada, amortizacao bullet ou linear, "
        "qualquer frequencia de cupom. "
        "Use para: (1) definir spread indicativo em novas emissoes, "
        "(2) calcular MTM de papeis existentes, "
        "(3) apresentar sensibilidade de preco a investidores."
    )
    args_schema: type[BaseModel] = BondPricingInput

    def _run(
        self,
        face_value: float = 1000.0,
        coupon_rate: float = 0.0,
        indexer: str = "CDI+",
        base_rate: float = 0.0,
        maturity_years: float = 5.0,
        coupon_frequency: int = 2,
        discount_rate: float = 0.0,
        amortization: str = "bullet",
    ) -> str:
        try:
            # Determine total coupon rate per period
            if indexer.upper() in ("CDI+", "IPCA+"):
                total_annual = base_rate + coupon_rate
            else:  # PRE / prefixado
                total_annual = coupon_rate

            # If no discount rate provided, price at par (discount = emission rate)
            if discount_rate == 0.0:
                discount_rate = total_annual

            periods = int(round(maturity_years * coupon_frequency))
            coupon_per_period = (total_annual / 100) / coupon_frequency
            discount_per_period = (discount_rate / 100) / coupon_frequency

            # Build cash flow schedule
            cash_flows: list[tuple[int, float, float]] = []  # (period, coupon, principal)
            for p in range(1, periods + 1):
                if amortization == "bullet":
                    principal = face_value if p == periods else 0.0
                else:  # linear
                    principal = face_value / periods

                # Coupon on outstanding balance
                outstanding = face_value - (face_value / periods * (p - 1)) if amortization == "linear" else face_value
                coupon = outstanding * coupon_per_period
                cash_flows.append((p, coupon, principal))

            # Price (PU) = PV of all cash flows at discount rate
            pu = 0.0
            for p, coupon, principal in cash_flows:
                cf = coupon + principal
                pu += cf / ((1 + discount_per_period) ** p)

            # Duration (Macaulay) = weighted average time of cash flows
            weighted_time = 0.0
            for p, coupon, principal in cash_flows:
                cf = coupon + principal
                pv_cf = cf / ((1 + discount_per_period) ** p)
                weighted_time += (p / coupon_frequency) * pv_cf
            macaulay_duration = weighted_time / pu if pu > 0 else 0.0

            # Modified Duration
            modified_duration = macaulay_duration / (1 + discount_per_period)

            # DV01 (value of 1 basis point)
            dv01 = pu * modified_duration / 10000

            # Sensitivity table: price at +/-25, +/-50, +/-100 bps
            sensitivity: dict[str, float] = {}
            for shift_bps in [-100, -50, -25, 25, 50, 100]:
                new_disc = (discount_rate + shift_bps / 100) / 100 / coupon_frequency
                new_pu = 0.0
                remaining = face_value
                for p, coupon, principal in cash_flows:
                    outstanding_bal = (
                        face_value - (face_value / periods * (p - 1))
                        if amortization == "linear" else face_value
                    )
                    adj_coupon = outstanding_bal * coupon_per_period
                    cf = adj_coupon + principal
                    new_pu += cf / ((1 + new_disc) ** p)
                pct_change = (new_pu - pu) / pu * 100
                key = f"{'+' if shift_bps > 0 else ''}{shift_bps}bps"
                sensitivity[key] = {
                    "pu": round(new_pu, 4),
                    "pu_change": round(new_pu - pu, 4),
                    "pct_change": round(pct_change, 4),
                }

            # Spread implied by PU (if PU != par) — just informational
            pu_pct_of_par = pu / face_value * 100

            result = {
                "summary": {
                    "indexer": indexer,
                    "coupon_rate_spread": coupon_rate,
                    "base_rate": base_rate,
                    "total_rate_pa": total_annual,
                    "discount_rate_pa": discount_rate,
                    "maturity_years": maturity_years,
                    "coupon_frequency_pa": coupon_frequency,
                    "amortization": amortization,
                    "periods": periods,
                },
                "pricing": {
                    "face_value": round(face_value, 2),
                    "pu_market": round(pu, 4),
                    "pu_pct_of_par": round(pu_pct_of_par, 4),
                    "pu_above_par": pu > face_value,
                },
                "duration_risk": {
                    "macaulay_duration_years": round(macaulay_duration, 4),
                    "modified_duration": round(modified_duration, 4),
                    "dv01_brl": round(dv01, 6),
                    "interpretation": (
                        f"Para cada 1% de alta na taxa, o PU cai aprox. {round(modified_duration, 2)}%. "
                        f"Para cada 1 bp, varia R$ {round(dv01, 4)}."
                    ),
                },
                "sensitivity_table": sensitivity,
                "cash_flow_summary": [
                    {
                        "period": p,
                        "year": round(p / coupon_frequency, 2),
                        "coupon": round(coupon, 2),
                        "principal": round(principal, 2),
                        "total_cf": round(coupon + principal, 2),
                    }
                    for p, coupon, principal in cash_flows
                ],
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as exc:
            logger.error(f"Erro no bond_pricing: {exc}")
            return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# DEBT STRUCTURING TOOL
# ---------------------------------------------------------------------------

class DebtStructuringInput(BaseModel):
    credit_analysis_json: str = Field(
        description=(
            "JSON com a analise de credito do emissor (output do credit_tool). "
            "Deve conter: leverage (net_leverage, gross_leverage), coverage (ebitda_interest_coverage, dscr), "
            "liquidity (current_ratio) e credit_score (implied_rating)."
        )
    )
    deal_type: str = Field(
        description="Tipo de instrumento: 'Debentures', 'CRI', 'CRA', 'CCB', 'Notas_Comerciais', 'Bond_Externo'",
    )
    sector: str = Field(
        default="industria",
        description="Setor do emissor: 'energia', 'logistica', 'agronegocio', 'saude', 'varejo', 'imobiliario', 'industria', 'financeiro'",
    )
    desired_volume_brl: float = Field(
        description="Volume desejado da emissao em R$ (ex: 500000000 para R$ 500 milhoes)",
    )
    use_of_proceeds: str = Field(
        default="geral",
        description="Destinacao dos recursos: 'capex', 'reperfilamento_divida', 'aquisicao', 'capital_giro', 'infraestrutura', 'geral'",
    )


class DebtStructuringTool(BaseTool):
    name: str = "debt_structuring"
    description: str = (
        "Recomenda a estrutura otima de uma emissao de divida (debentures, CRI, CRA, CCB, bond externo) "
        "com base na analise de credito do emissor. "
        "Gera: (1) spread indicativo de mercado por rating implicito, "
        "(2) prazo recomendado, (3) tipo de garantia, (4) indexador sugerido, "
        "(5) pacote de covenants de mercado com thresholds, "
        "(6) elegibilidade a incentivos fiscais (Lei 12.431/14.801), "
        "(7) estrutura de amortizacao recomendada."
    )
    args_schema: type[BaseModel] = DebtStructuringInput

    # Spread table (basis points) por rating implicito
    _SPREAD_CDI = {
        "AAA-AA": (50, 150),
        "A": (150, 300),
        "BBB": (300, 500),
        "BB": (500, 700),
        "B": (700, 1000),
        "CCC-D": (1000, 1500),
    }
    _SPREAD_IPCA = {
        "AAA-AA": (80, 180),
        "A": (200, 350),
        "BBB": (350, 550),
        "BB": (550, 750),
        "B": (750, 1100),
        "CCC-D": (1100, 1600),
    }

    # Covenant thresholds por rating
    _COVENANTS = {
        "AAA-AA": {"net_leverage_max": 3.0, "ebitda_coverage_min": 3.0, "dscr_min": 1.3},
        "A":      {"net_leverage_max": 3.5, "ebitda_coverage_min": 2.5, "dscr_min": 1.2},
        "BBB":    {"net_leverage_max": 4.0, "ebitda_coverage_min": 2.0, "dscr_min": 1.1},
        "BB":     {"net_leverage_max": 4.5, "ebitda_coverage_min": 1.75, "dscr_min": 1.0},
        "B":      {"net_leverage_max": 5.0, "ebitda_coverage_min": 1.5, "dscr_min": 1.0},
        "CCC-D":  {"net_leverage_max": 5.5, "ebitda_coverage_min": 1.2, "dscr_min": 0.9},
    }

    _INFRA_SECTORS = {"energia", "logistica", "saneamento", "saude", "telecom", "infraestrutura"}

    def _run(
        self,
        credit_analysis_json: str,
        deal_type: str,
        sector: str = "industria",
        desired_volume_brl: float = 500_000_000,
        use_of_proceeds: str = "geral",
    ) -> str:
        try:
            ca = json.loads(credit_analysis_json)

            # Extract latest year metrics
            years = ca.get("years", [])
            latest = years[-1] if years else None
            metrics = ca.get("credit_analysis", {}).get(latest or "", {}) if latest else {}
            score_data = metrics.get("credit_score", {})
            implied_rating = score_data.get("implied_rating", "BBB")
            credit_score = score_data.get("score", 70)
            net_leverage = (metrics.get("leverage") or {}).get("net_leverage")
            coverage = (metrics.get("coverage") or {}).get("ebitda_interest_coverage")

            # Spread recommendation
            spread_cdi = self._SPREAD_CDI.get(implied_rating, (300, 500))
            spread_ipca = self._SPREAD_IPCA.get(implied_rating, (350, 550))
            spread_cdi_mid = (spread_cdi[0] + spread_cdi[1]) / 2 / 100
            spread_ipca_mid = (spread_ipca[0] + spread_ipca[1]) / 2 / 100

            # Indexer recommendation
            is_infra = sector.lower() in self._INFRA_SECTORS
            is_long = use_of_proceeds in ("capex", "infraestrutura")
            recommended_indexer = "IPCA+" if (is_infra or is_long) else "CDI+"
            incentivized_eligible = is_infra and use_of_proceeds == "infraestrutura"

            # Tenor recommendation
            tenor_map = {
                "capex": "5 a 8 anos",
                "infraestrutura": "8 a 15 anos (incentivada Lei 12.431)",
                "reperfilamento_divida": "3 a 7 anos",
                "aquisicao": "4 a 7 anos",
                "capital_giro": "1 a 3 anos",
                "geral": "3 a 5 anos",
            }
            recommended_tenor = tenor_map.get(use_of_proceeds, "3 a 5 anos")

            # Guarantee recommendation
            guarantee = (
                "Garantia Real (hipoteca ou alienacao fiduciaria)"
                if credit_score < 65 else
                "Quirografaria com covenants robustos"
                if credit_score < 80 else
                "Quirografaria — rating e posicionamento dispensam garantia real"
            )

            # Amortization recommendation
            amortization = (
                "Bullet (pagamento unico no vencimento)"
                if use_of_proceeds in ("aquisicao", "reperfilamento_divida", "infraestrutura")
                else "Linear anual (reducao de exposicao para o credor)"
            )

            # Covenants
            cv = self._COVENANTS.get(implied_rating, self._COVENANTS["BBB"])

            covenants = {
                "financeiros": {
                    "divida_liquida_ebitda_max": cv["net_leverage_max"],
                    "ebitda_despesa_financeira_min": cv["ebitda_coverage_min"],
                    "dscr_min": cv["dscr_min"],
                    "frequencia_teste": "Semestral (com base nas DFs auditadas / ITR)",
                    "grace_period_cura_dias_uteis": 30,
                },
                "nao_financeiros": [
                    "Cross-default: vencimento antecipado se default em dividas > 15% do PL",
                    "Change of control: vencimento antecipado em mudanca de controle direto",
                    "Restricao de alienacao de ativos essenciais (> 10% do Ativo Total) sem consentimento",
                    "Obrigacao de manutencao de seguros sobre ativos relevantes",
                    "Vedacao de distribuicao de dividendos acima do minimo obrigatorio se DL/EBITDA > "
                    + str(cv["net_leverage_max"] - 0.5) + "x",
                ],
            }

            # Volume feasibility
            ebitda_latest = (metrics.get("leverage") or {}).get("ebitda", 0)
            max_debt_capacity = ebitda_latest * cv["net_leverage_max"] if ebitda_latest else None
            current_gross_debt = (metrics.get("leverage") or {}).get("gross_debt", 0)
            available_capacity = (
                max(max_debt_capacity - current_gross_debt, 0)
                if max_debt_capacity is not None else None
            )
            volume_feasible = (
                desired_volume_brl <= (available_capacity or float("inf"))
            )

            result = {
                "emissor_credit_profile": {
                    "implied_rating": implied_rating,
                    "credit_score": credit_score,
                    "net_leverage_latest": net_leverage,
                    "coverage_latest": coverage,
                },
                "structuring_recommendation": {
                    "deal_type": deal_type,
                    "recommended_indexer": recommended_indexer,
                    "recommended_tenor": recommended_tenor,
                    "guarantee_type": guarantee,
                    "amortization": amortization,
                    "incentivized_eligible": incentivized_eligible,
                    "incentive_law": "Lei 12.431/2011" if incentivized_eligible else "N/A",
                },
                "pricing_indication": {
                    "spread_cdi_plus_bps": {
                        "min": spread_cdi[0],
                        "mid": round(spread_cdi_mid * 100, 0),
                        "max": spread_cdi[1],
                        "description": f"CDI + {spread_cdi[0]/100:.2f}% a CDI + {spread_cdi[1]/100:.2f}% a.a.",
                    },
                    "spread_ipca_plus_bps": {
                        "min": spread_ipca[0],
                        "mid": round(spread_ipca_mid * 100, 0),
                        "max": spread_ipca[1],
                        "description": f"IPCA + {spread_ipca[0]/100:.2f}% a IPCA + {spread_ipca[1]/100:.2f}% a.a.",
                    },
                    "recommended_spread": (
                        f"IPCA + {spread_ipca[0]/100:.2f}% a {spread_ipca[1]/100:.2f}% a.a."
                        if recommended_indexer == "IPCA+"
                        else f"CDI + {spread_cdi[0]/100:.2f}% a {spread_cdi[1]/100:.2f}% a.a."
                    ),
                },
                "proposed_covenants": covenants,
                "volume_analysis": {
                    "desired_volume_brl": desired_volume_brl,
                    "ebitda_latest_brl": ebitda_latest,
                    "covenant_max_debt_brl": round(max_debt_capacity, 0) if max_debt_capacity else None,
                    "current_gross_debt_brl": current_gross_debt,
                    "available_capacity_brl": round(available_capacity, 0) if available_capacity else None,
                    "volume_feasible": volume_feasible,
                    "warning": (
                        "Volume desejado excede capacidade de divida pelo covenant proposto. "
                        "Reduzir volume ou negociar covenant mais permissivo."
                        if not volume_feasible else None
                    ),
                },
                "regulatory_notes": {
                    "registro": "RCVM 160 — Registro Automatico (EFRF) ou via ANBIMA",
                    "agente_fiduciario": "Obrigatorio (RCVM 17)",
                    "custodia": "B3 (CETIP21)",
                    "rating": "Recomendado para emissoes > R$ 100 mi ou oferta ao varejo",
                },
            }

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro no debt_structuring: {exc}")
            return json.dumps({"error": str(exc)})
