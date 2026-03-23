"""IPO / Equity Valuation Tool — ECM operations (Brazilian market)."""
from __future__ import annotations
import json
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class IPOValuationInput(BaseModel):
    company: str = Field(description="Nome da empresa")
    instrument: str = Field(default="Follow-on", description="IPO, Follow-on, Block_Trade")
    shares_outstanding: float = Field(description="Acoes em circulacao (milhoes)")
    current_price: float = Field(default=0, description="Preco atual por acao (R$) — 0 se IPO")
    net_income: float = Field(description="Lucro liquido LTM em R$")
    ebitda: float = Field(description="EBITDA LTM em R$")
    revenue: float = Field(description="Receita liquida LTM em R$")
    net_debt: float = Field(default=0, description="Divida liquida em R$")
    equity_value_dcf: float = Field(default=0, description="Equity value do DCF (se disponivel)")
    sector: str = Field(default="")
    offering_pct: float = Field(default=15.0, description="% do capital ofertado")
    primary_pct: float = Field(default=50.0, description="% da oferta que e primaria")

class IPOValuationTool(BaseTool):
    name: str = "ipo_valuation"
    description: str = (
        "Valuation para operacoes de ECM (IPO, Follow-on, Block Trade). "
        "Calcula multiplos implied, price range, diluicao e bookbuilding strategy."
    )
    args_schema: type[BaseModel] = IPOValuationInput

    def _run(self, company="", instrument="Follow-on", shares_outstanding=100,
             current_price=0, net_income=0, ebitda=0, revenue=0, net_debt=0,
             equity_value_dcf=0, sector="", offering_pct=15.0, primary_pct=50.0) -> str:
        try:
            shares_m = shares_outstanding
            # Peer multiples (realistic B3 2025)
            SECTOR_MULTIPLES = {
                "Agronegocio": {"ev_ebitda":7.5,"pe":12.0,"ev_rev":1.8},
                "Energia": {"ev_ebitda":8.2,"pe":14.0,"ev_rev":2.5},
                "Varejo": {"ev_ebitda":6.0,"pe":10.0,"ev_rev":0.8},
                "Tech": {"ev_ebitda":15.0,"pe":25.0,"ev_rev":5.0},
                "Saude": {"ev_ebitda":10.0,"pe":18.0,"ev_rev":2.0},
                "Logistica": {"ev_ebitda":7.0,"pe":11.0,"ev_rev":1.5},
                "default": {"ev_ebitda":8.0,"pe":13.0,"ev_rev":1.8},
            }
            mult = SECTOR_MULTIPLES.get(sector, SECTOR_MULTIPLES["default"])

            # Implied valuations
            ev_by_ebitda = ebitda * mult["ev_ebitda"] if ebitda else 0
            ev_by_rev = revenue * mult["ev_rev"] if revenue else 0
            eq_by_pe = net_income * mult["pe"] if net_income else 0
            eq_by_ebitda = ev_by_ebitda - net_debt if ev_by_ebitda else 0
            eq_by_rev = ev_by_rev - net_debt if ev_by_rev else 0

            # Price per share from each method
            methods = {}
            if eq_by_ebitda > 0: methods["EV/EBITDA"] = eq_by_ebitda / (shares_m * 1e6)
            if eq_by_pe > 0: methods["P/E"] = eq_by_pe / (shares_m * 1e6)
            if eq_by_rev > 0: methods["EV/Revenue"] = eq_by_rev / (shares_m * 1e6)
            if equity_value_dcf > 0: methods["DCF"] = equity_value_dcf / (shares_m * 1e6)

            prices = list(methods.values())
            if not prices:
                return json.dumps({"error": "Dados insuficientes para valuation"})

            price_low = round(min(prices), 2)
            price_high = round(max(prices), 2)
            price_mid = round(sum(prices) / len(prices), 2)

            # IPO discount (typical)
            discount = 0.10 if instrument == "IPO" else 0.05 if instrument == "Follow-on" else 0.03
            offer_low = round(price_low * (1 - discount), 2)
            offer_high = round(price_mid, 2)

            # Offering size
            new_shares = shares_m * (offering_pct / 100)
            offer_value_low = new_shares * 1e6 * offer_low
            offer_value_high = new_shares * 1e6 * offer_high
            primary_value = offer_value_high * (primary_pct / 100)

            # Dilution
            post_shares = shares_m + new_shares * (primary_pct / 100)
            dilution_pct = round((1 - shares_m / post_shares) * 100, 2) if primary_pct > 0 else 0

            # Implied multiples at offer price
            impl_ev = price_mid * shares_m * 1e6 + net_debt
            impl = {}
            if ebitda > 0: impl["EV/EBITDA"] = round(impl_ev / ebitda, 1)
            if net_income > 0: impl["P/E"] = round(price_mid * shares_m * 1e6 / net_income, 1)
            if revenue > 0: impl["EV/Revenue"] = round(impl_ev / revenue, 2)

            # Bookbuilding
            book = {"demand_estimate": "1.5-2.5x (base case)",
                    "anchor_investors": "Target 30-40% com ancoras institucionais",
                    "retail_allocation": "10-15% varejo" if instrument == "IPO" else "N/A",
                    "lock_up": "180 dias (acionistas vendedores)" if instrument != "Block_Trade" else "Sem lock-up"}

            if instrument == "Block_Trade":
                book = {"execution": "Accelerated bookbuilding (1-2 dias)",
                        "discount": f"{discount*100:.0f}% vs VWAP",
                        "lock_up": "Sem lock-up padrao"}

            # Upside/downside vs current
            updown = {}
            if current_price > 0:
                updown = {"vs_current": f"R$ {current_price:.2f}",
                          "upside_to_mid": f"{((price_mid/current_price)-1)*100:.1f}%",
                          "upside_to_high": f"{((price_high/current_price)-1)*100:.1f}%"}

            return json.dumps({
                "company": company, "instrument": instrument,
                "valuation_range": {"low": price_low, "mid": price_mid, "high": price_high,
                    "methods": {k: round(v, 2) for k, v in methods.items()}},
                "offering": {"shares_offered_m": round(new_shares, 2),
                    "offer_range": f"R$ {offer_low} - R$ {offer_high}",
                    "offer_value_range": f"R$ {offer_value_low/1e6:.0f}M - R$ {offer_value_high/1e6:.0f}M",
                    "primary_proceeds": f"R$ {primary_value/1e6:.0f}M",
                    "dilution_pct": dilution_pct, "offering_pct": offering_pct},
                "implied_multiples": impl,
                "peer_multiples_reference": mult,
                "bookbuilding_strategy": book,
                "current_price_analysis": updown,
                "sector_multiples_used": sector or "default",
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
