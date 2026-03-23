"""
ECM Tools — IPO Valuation & Offering Structure
Ferramentas para o agente ECM Specialist:
- IPOValuationTool: valuation por trading comps, DCF e football field
- OfferingStructureTool: estrutura da oferta, dilucao, greenshoe, lock-up
"""

from __future__ import annotations

import json
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# IPO VALUATION TOOL
# ---------------------------------------------------------------------------

class IPOValuationInput(BaseModel):
    financials_json: str = Field(
        description=(
            "JSON com as DFs consolidadas do emissor. "
            "Deve conter income_statement com: net_revenue, ebitda, ebit, net_income; "
            "e balance_sheet com: total_equity, gross_debt, cash."
        )
    )
    sector: str = Field(
        description=(
            "Setor da empresa para selecao dos multiplos de referencia: "
            "'varejo', 'tecnologia', 'saude', 'energia', 'logistica', 'agronegocio', "
            "'financeiro', 'imobiliario', 'industria', 'telecom'"
        )
    )
    shares_outstanding: float = Field(
        description="Numero de acoes existentes pre-IPO (em unidades)",
    )
    dcf_wacc: float = Field(
        default=12.0,
        description="WACC para o DCF em % a.a. (ex: 12.0 para 12%)",
    )
    dcf_terminal_growth: float = Field(
        default=3.0,
        description="Taxa de crescimento na perpetuidade em % a.a. (ex: 3.0)",
    )
    revenue_growth_yr1: float = Field(
        default=15.0,
        description="Crescimento de receita projetado no Ano 1 pos-IPO em % (ex: 15.0)",
    )
    ebitda_margin_target: float = Field(
        default=0.0,
        description="Margem EBITDA alvo para projecao em % (0 = usa margem LTM atual)",
    )


class IPOValuationTool(BaseTool):
    name: str = "ipo_valuation"
    description: str = (
        "Calcula o range de valuation para IPO ou follow-on usando tres metodologias: "
        "(1) Trading Comps — multiplos setoriais de empresas listadas na B3, "
        "(2) DCF simplificado — FCFF com WACC e crescimento na perpetuidade, "
        "(3) Football Field — consolidacao dos ranges por metodologia. "
        "Retorna: price range por acao (low/mid/high), EV e equity value implicitos, "
        "e metricas de entrada (net leverage, crescimento, margens). "
        "Use para definir o range de preco de oferta em IPOs e follow-ons."
    )
    args_schema: type[BaseModel] = IPOValuationInput

    # Multiplos setoriais de referencia (mediana de peers Brasil + LatAm, orientativos)
    _SECTOR_MULTIPLES: dict[str, dict] = {
        "varejo":      {"ev_ebitda_ltm": 8.0,  "ev_ebitda_ntm": 7.0,  "pe_ntm": 18.0, "ev_rev": 0.8},
        "tecnologia":  {"ev_ebitda_ltm": 20.0, "ev_ebitda_ntm": 15.0, "pe_ntm": 35.0, "ev_rev": 5.0},
        "saude":       {"ev_ebitda_ltm": 12.0, "ev_ebitda_ntm": 10.0, "pe_ntm": 22.0, "ev_rev": 2.0},
        "energia":     {"ev_ebitda_ltm": 7.0,  "ev_ebitda_ntm": 6.5,  "pe_ntm": 12.0, "ev_rev": 2.5},
        "logistica":   {"ev_ebitda_ltm": 8.5,  "ev_ebitda_ntm": 7.5,  "pe_ntm": 16.0, "ev_rev": 1.2},
        "agronegocio": {"ev_ebitda_ltm": 7.0,  "ev_ebitda_ntm": 6.5,  "pe_ntm": 14.0, "ev_rev": 1.0},
        "financeiro":  {"ev_ebitda_ltm": 10.0, "ev_ebitda_ntm": 9.0,  "pe_ntm": 12.0, "ev_rev": 3.0},
        "imobiliario": {"ev_ebitda_ltm": 12.0, "ev_ebitda_ntm": 10.0, "pe_ntm": 20.0, "ev_rev": 4.0},
        "industria":   {"ev_ebitda_ltm": 7.5,  "ev_ebitda_ntm": 6.8,  "pe_ntm": 15.0, "ev_rev": 1.0},
        "telecom":     {"ev_ebitda_ltm": 6.0,  "ev_ebitda_ntm": 5.5,  "pe_ntm": 14.0, "ev_rev": 1.5},
    }
    _IPO_DISCOUNT = 0.10  # desconto tipico de IPO (10-15%) vs fair value para garantir demanda

    def _run(
        self,
        financials_json: str,
        sector: str,
        shares_outstanding: float,
        dcf_wacc: float = 12.0,
        dcf_terminal_growth: float = 3.0,
        revenue_growth_yr1: float = 15.0,
        ebitda_margin_target: float = 0.0,
    ) -> str:
        try:
            fin = json.loads(financials_json)
            is_ = fin.get("income_statement", {})
            bs = fin.get("balance_sheet", {})
            years = fin.get("years", [])
            latest = years[-1] if years else None

            def g(stmt, acct):
                if not latest:
                    return 0.0
                return float((stmt.get(acct) or {}).get(latest, 0) or 0)

            net_revenue = g(is_, "net_revenue")
            ebitda = g(is_, "ebitda") or (g(is_, "ebit") + g(is_, "da"))
            ebit = g(is_, "ebit")
            net_income = g(is_, "net_income")
            total_equity = g(bs, "total_equity")
            gross_debt = g(bs, "st_debt") + g(bs, "lt_debt")
            cash = g(bs, "cash")
            net_debt = gross_debt - cash

            ebitda_margin_ltm = ebitda / net_revenue if net_revenue else 0.0
            ebitda_margin_used = ebitda_margin_target / 100 if ebitda_margin_target > 0 else ebitda_margin_ltm

            # --- Trading Comps ---
            mults = self._SECTOR_MULTIPLES.get(sector.lower(), self._SECTOR_MULTIPLES["industria"])

            # LTM
            ev_by_ebitda_ltm = ebitda * mults["ev_ebitda_ltm"]
            equity_by_ebitda_ltm = ev_by_ebitda_ltm - net_debt
            price_ebitda_ltm = equity_by_ebitda_ltm / shares_outstanding if shares_outstanding else 0

            # NTM (projeta 1 ano a frente)
            ebitda_ntm = net_revenue * (1 + revenue_growth_yr1 / 100) * ebitda_margin_used
            ev_by_ebitda_ntm = ebitda_ntm * mults["ev_ebitda_ntm"]
            equity_by_ebitda_ntm = ev_by_ebitda_ntm - net_debt
            price_ebitda_ntm = equity_by_ebitda_ntm / shares_outstanding if shares_outstanding else 0

            # P/E NTM
            net_income_ntm = ebitda_ntm * 0.55  # rough: 55% conversion EBITDA->NI
            equity_by_pe = net_income_ntm * mults["pe_ntm"]
            price_pe_ntm = equity_by_pe / shares_outstanding if shares_outstanding else 0

            # EV/Revenue
            rev_ntm = net_revenue * (1 + revenue_growth_yr1 / 100)
            ev_by_rev = rev_ntm * mults["ev_rev"]
            equity_by_rev = ev_by_rev - net_debt
            price_rev = equity_by_rev / shares_outstanding if shares_outstanding else 0

            comps_prices = [p for p in [price_ebitda_ltm, price_ebitda_ntm, price_pe_ntm, price_rev] if p > 0]
            comps_mid = sum(comps_prices) / len(comps_prices) if comps_prices else 0

            # --- DCF ---
            # Simplified 5-year projection
            fcfs = []
            rev = net_revenue
            for yr in range(1, 6):
                growth = revenue_growth_yr1 / 100 if yr == 1 else max(revenue_growth_yr1 / 100 - 0.02 * (yr - 1), dcf_terminal_growth / 100)
                rev = rev * (1 + growth)
                ebitda_proj = rev * ebitda_margin_used
                tax_rate = 0.34
                ebit_proj = ebitda_proj * 0.8  # rough D&A assumption
                capex = rev * 0.05
                delta_wc = rev * 0.01
                fcf = ebitda_proj - ebit_proj * tax_rate - capex - delta_wc
                fcfs.append(fcf)

            wacc = dcf_wacc / 100
            g_term = dcf_terminal_growth / 100

            pv_fcfs = sum(fcf / (1 + wacc) ** yr for yr, fcf in enumerate(fcfs, 1))
            terminal_value = fcfs[-1] * (1 + g_term) / (wacc - g_term)
            pv_terminal = terminal_value / (1 + wacc) ** 5

            ev_dcf = pv_fcfs + pv_terminal
            equity_dcf = ev_dcf - net_debt
            price_dcf = equity_dcf / shares_outstanding if shares_outstanding else 0

            # --- Football Field ---
            all_prices = {
                "EV/EBITDA LTM": price_ebitda_ltm,
                "EV/EBITDA NTM": price_ebitda_ntm,
                "P/L NTM": price_pe_ntm,
                "EV/Receita NTM": price_rev,
                "DCF": price_dcf,
            }
            valid_prices = {k: v for k, v in all_prices.items() if v > 0}

            if valid_prices:
                overall_min = min(valid_prices.values())
                overall_max = max(valid_prices.values())
                overall_mid = sum(valid_prices.values()) / len(valid_prices)
            else:
                overall_min = overall_max = overall_mid = 0.0

            # Apply IPO discount for offer price range
            offer_low = overall_mid * (1 - self._IPO_DISCOUNT - 0.05)
            offer_mid = overall_mid * (1 - self._IPO_DISCOUNT)
            offer_high = overall_mid * (1 - self._IPO_DISCOUNT / 2)

            result = {
                "inputs": {
                    "sector": sector,
                    "shares_outstanding": shares_outstanding,
                    "net_revenue_ltm": round(net_revenue, 0),
                    "ebitda_ltm": round(ebitda, 0),
                    "ebitda_margin_ltm_pct": round(ebitda_margin_ltm * 100, 2),
                    "net_income_ltm": round(net_income, 0),
                    "net_debt": round(net_debt, 0),
                    "net_leverage": round(net_debt / ebitda, 2) if ebitda else None,
                    "dcf_wacc_pct": dcf_wacc,
                    "dcf_terminal_growth_pct": dcf_terminal_growth,
                    "revenue_growth_yr1_pct": revenue_growth_yr1,
                },
                "trading_comps": {
                    "sector_multiples_used": mults,
                    "by_method": {
                        k: {
                            "price_per_share": round(v, 2),
                            "equity_value_brl": round(v * shares_outstanding, 0),
                        }
                        for k, v in valid_prices.items()
                    },
                    "comps_mid_price": round(comps_mid, 2),
                },
                "dcf": {
                    "pv_fcfs": round(pv_fcfs, 0),
                    "pv_terminal_value": round(pv_terminal, 0),
                    "ev_dcf": round(ev_dcf, 0),
                    "equity_value_dcf": round(equity_dcf, 0),
                    "price_per_share_dcf": round(price_dcf, 2),
                },
                "football_field": {
                    "fair_value_min": round(overall_min, 2),
                    "fair_value_mid": round(overall_mid, 2),
                    "fair_value_max": round(overall_max, 2),
                    "by_methodology": {k: round(v, 2) for k, v in valid_prices.items()},
                },
                "offer_price_range": {
                    "low": round(offer_low, 2),
                    "mid": round(offer_mid, 2),
                    "high": round(offer_high, 2),
                    "ipo_discount_applied_pct": round(self._IPO_DISCOUNT * 100, 1),
                    "implied_market_cap_mid_brl": round(offer_mid * shares_outstanding, 0),
                    "implied_ev_mid_brl": round(offer_mid * shares_outstanding + net_debt, 0),
                    "implied_ev_ebitda_mid": round((offer_mid * shares_outstanding + net_debt) / ebitda, 1) if ebitda else None,
                },
                "notes": (
                    "Multiplos setoriais sao medianas orientativas de peers Brasil/LatAm. "
                    "Para maior precisao, substituir pelos multiplos reais dos peers selecionados. "
                    "Desconto de IPO aplicado para refletir pratica de mercado (underpricing estrutural)."
                ),
            }

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro no ipo_valuation: {exc}")
            return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# OFFERING STRUCTURE TOOL
# ---------------------------------------------------------------------------

class OfferingStructureInput(BaseModel):
    equity_value_brl: float = Field(
        description="Equity value implicito pre-money em R$ (output do ipo_valuation)",
    )
    primary_offering_pct: float = Field(
        default=15.0,
        description="Percentual do equity pre-money que sera emitido como oferta primaria (novas acoes). Ex: 15.0 = 15%",
    )
    secondary_selling_pct: float = Field(
        default=10.0,
        description="Percentual das acoes pre-IPO que os acionistas vendedores venderao. Ex: 10.0 = 10%",
    )
    shares_outstanding_pre: float = Field(
        description="Numero de acoes pre-IPO",
    )
    offer_price: float = Field(
        description="Preco por acao proposto (use o mid do offer_price_range do ipo_valuation)",
    )
    deal_type: str = Field(
        default="IPO",
        description="Tipo: 'IPO', 'Follow-on', 'Block_Trade'",
    )


class OfferingStructureTool(BaseTool):
    name: str = "offering_structure"
    description: str = (
        "Calcula a estrutura completa de uma oferta de acoes (IPO ou follow-on): "
        "numero de acoes primarias e secundarias, percentual de diluicao, "
        "tamanho total da oferta, free float pos-IPO, greenshoe (lote suplementar), "
        "e recomendacao de lock-up. "
        "Use apos o ipo_valuation para definir os parametros concretos da oferta."
    )
    args_schema: type[BaseModel] = OfferingStructureInput

    def _run(
        self,
        equity_value_brl: float,
        primary_offering_pct: float = 15.0,
        secondary_selling_pct: float = 10.0,
        shares_outstanding_pre: float = 0,
        offer_price: float = 0,
        deal_type: str = "IPO",
    ) -> str:
        try:
            if offer_price <= 0 or shares_outstanding_pre <= 0:
                return json.dumps({"error": "offer_price e shares_outstanding_pre devem ser maiores que zero."})

            # Primary shares
            primary_volume = equity_value_brl * (primary_offering_pct / 100)
            new_shares = primary_volume / offer_price

            # Secondary shares
            secondary_shares = shares_outstanding_pre * (secondary_selling_pct / 100)
            secondary_volume = secondary_shares * offer_price

            # Post-IPO totals
            total_shares_post = shares_outstanding_pre + new_shares
            total_offer_volume = primary_volume + secondary_volume
            total_offer_shares = new_shares + secondary_shares

            # Dilution
            dilution_pct = new_shares / total_shares_post * 100

            # Free float
            free_float_shares = total_offer_shares  # assumes all sold shares become free float
            free_float_pct = free_float_shares / total_shares_post * 100

            # Market cap post-IPO
            market_cap_post = offer_price * total_shares_post

            # Greenshoe (lote suplementar — max 15% do total da oferta)
            greenshoe_shares = total_offer_shares * 0.15
            greenshoe_volume = greenshoe_shares * offer_price

            # Lock-up recommendation
            lockup = {
                "controladores": "180 dias pos-liquidacao",
                "acionistas_vendedores": "90 a 180 dias pos-liquidacao",
                "administradores": "90 dias pos-liquidacao (acoes de programas de equity)",
                "nota": (
                    "Fim do lock-up pode gerar pressao vendedora. "
                    "Monitorar calendario de expiracao de lock-up para gestao de expectativas."
                ),
            }

            # CVM/B3 requirements
            novo_mercado_ok = free_float_pct >= 25.0

            result = {
                "deal_type": deal_type,
                "offer_price_per_share": round(offer_price, 2),
                "pre_ipo": {
                    "shares": round(shares_outstanding_pre, 0),
                    "equity_value_brl": round(equity_value_brl, 0),
                },
                "primary_offering": {
                    "shares_new": round(new_shares, 0),
                    "volume_brl": round(primary_volume, 0),
                    "pct_of_pre_equity": round(primary_offering_pct, 2),
                    "capital_goes_to": "Empresa (caixa para capex / deleverage / geral)",
                },
                "secondary_offering": {
                    "shares_sold": round(secondary_shares, 0),
                    "volume_brl": round(secondary_volume, 0),
                    "pct_of_pre_shares": round(secondary_selling_pct, 2),
                    "capital_goes_to": "Acionistas vendedores",
                },
                "total_offering": {
                    "total_shares_offered": round(total_offer_shares, 0),
                    "total_volume_brl": round(total_offer_volume, 0),
                },
                "post_ipo": {
                    "total_shares": round(total_shares_post, 0),
                    "dilution_from_primary_pct": round(dilution_pct, 2),
                    "free_float_shares": round(free_float_shares, 0),
                    "free_float_pct": round(free_float_pct, 2),
                    "market_cap_brl": round(market_cap_post, 0),
                    "novo_mercado_25pct_requirement_met": novo_mercado_ok,
                },
                "greenshoe_lote_suplementar": {
                    "shares": round(greenshoe_shares, 0),
                    "max_additional_volume_brl": round(greenshoe_volume, 0),
                    "pct_of_offer": 15.0,
                    "condition": "Ativado apenas se oversubscribed; usado tambem para estabilizacao de preco",
                },
                "lock_up_recommendation": lockup,
                "investor_allocation_suggestion": {
                    "institucional_local": "40-50% (fundos, previdencia, seguradoras)",
                    "institucional_internacional": "25-35% (via Reg S / 144A)",
                    "varejo": "10-20% (via reservas online em corretoras)",
                    "ancora": "5-15% (se cornerstone investor identificado)",
                },
                "regulatory": {
                    "registro": "RCVM 160 — via ANBIMA (convenio) para IPO",
                    "periodo_silencio": "30 dias antes do protocolo na CVM",
                    "segmento_b3_sugerido": "Novo Mercado" if novo_mercado_ok else "Nivel 2 ou Bovespa Mais",
                    "nota_free_float": (
                        "Free float de " + str(round(free_float_pct, 1)) + "% "
                        + ("atende" if novo_mercado_ok else "NAO atende")
                        + " o minimo de 25% do Novo Mercado."
                    ),
                },
            }

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro no offering_structure: {exc}")
            return json.dumps({"error": str(exc)})
