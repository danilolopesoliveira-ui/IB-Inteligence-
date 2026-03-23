"""Bond Pricing & Structuring Tool — DCM (Brazilian market)."""
from __future__ import annotations
import json
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class BondPricingInput(BaseModel):
    instrument: str = Field(description="Debentures, CRI, CRA, Loan_Offshore, Bilateral, CCB")
    face_value: float = Field(description="Valor nominal total em R$")
    coupon_rate: float = Field(description="Spread anual (%). Ex: 1.85 para DI+1.85%")
    coupon_type: str = Field(default="DI+spread")
    tenor_years: float = Field(default=5.0)
    rating: str = Field(default="AA")
    amortization: str = Field(default="bullet")
    guarantee_type: str = Field(default="quirografaria")
    cdi_rate: float = Field(default=13.15)
    sector: str = Field(default="")

class BondPricingTool(BaseTool):
    name: str = "bond_pricing"
    description: str = (
        "Precifica instrumentos de divida brasileiros (debentures, CRI, CRA, loans). "
        "Calcula spread indicativo, YTM, duration, PU e sensibilidade."
    )
    args_schema: type[BaseModel] = BondPricingInput

    def _run(self, instrument="Debentures", face_value=800e6, coupon_rate=1.85,
             coupon_type="DI+spread", tenor_years=5.0, rating="AA",
             amortization="bullet", guarantee_type="quirografaria",
             cdi_rate=13.15, sector="") -> str:
        try:
            SPREADS = {"AAA":0.80,"AA+":1.20,"AA":1.60,"AA-":1.90,"A+":2.30,"A":2.80,"BBB":5.00}
            GUAR = {"quirografaria":0,"real":-0.25,"fidejussoria":-0.15,
                    "cessao_fiduciaria":-0.30,"alienacao_fiduciaria":-0.35}
            fair = round(SPREADS.get(rating,2.5) + max(0,(tenor_years-3)*0.08) + GUAR.get(guarantee_type,0), 2)
            if "SOFR" in coupon_type: ytm=4.50+coupon_rate; bench="SOFR"
            elif "IPCA" in coupon_type: ytm=4.5+coupon_rate; bench="IPCA"
            else: ytm=cdi_rate+coupon_rate; bench="CDI"
            dur = tenor_years * (0.92 if amortization=="bullet" else 0.55)
            n = int(tenor_years*2); sr=ytm/200; sc=(coupon_rate/200)*1000
            pu = round(sum((sc+(1000 if t==n else 0))/((1+sr)**t) for t in range(1,n+1)),4)
            sens = []
            for d in [-0.50,-0.25,0,0.25,0.50]:
                r2=(ytm+d)/200
                p2=sum((sc+(1000 if t==n else 0))/((1+r2)**t) for t in range(1,n+1))
                sens.append({"delta_bps":int(d*100),"yield":round(ytm+d,2),"pu":round(p2,4)})
            comps = [
                {"issuer":"CPFL Energia","spread":"DI+1.78%","rating":"AA+","tenor":5},
                {"issuer":"Taesa","spread":"DI+1.45%","rating":"AAA","tenor":7},
                {"issuer":"Rumo","spread":"DI+1.92%","rating":"AA","tenor":5},
                {"issuer":"Localiza","spread":"DI+1.15%","rating":"AAA","tenor":3},
            ]
            notes = []
            if instrument in ("CRI","CRA"): notes.append("Verificar registro CVM e lastro elegivel")
            if instrument == "Loan_Offshore": notes.extend(["ROF no BACEN (15d uteis)","Hedge cambial + IOF"])
            if instrument == "Bilateral": notes.append("Negociacao direta — flex covenants")
            if guarantee_type=="quirografaria" and rating not in ("AAA","AA+"): notes.append(f"Rating {rating} sem garantia pode limitar demanda")
            return json.dumps({"pricing":{"coupon":f"{coupon_type} {coupon_rate}%","fair_spread":f"{fair}%",
                "ytm":f"{ytm:.2f}%","bench":bench},"risk":{"duration":round(dur,2),
                "mod_duration":round(dur/(1+ytm/100),2),"rating":rating,"guarantee":guarantee_type},
                "pu":{"value":pu,"face":1000},"sensitivity":sens,"comps":comps,"notes":notes},ensure_ascii=False,indent=2)
        except Exception as e:
            return json.dumps({"error":str(e)})
