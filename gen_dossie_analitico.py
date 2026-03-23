"""
Dossie Analitico Completo — Base de trabalho para o pipeline de agentes
Claude API (analise) + ReportLab (PDF) + matplotlib (graficos)
NAO e equity research — e um documento factual e analitico
Case: Solaris Energia Renovavel S.A. — Geracao solar + eolica
"""
import sys,os,json
sys.path.insert(0,os.path.dirname(__file__))
from dotenv import load_dotenv; load_dotenv()
from pathlib import Path
from datetime import datetime
from io import BytesIO
import anthropic
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

OUT=Path("./templates/models"); OUT.mkdir(parents=True,exist_ok=True)
w,h=A4
NAV='#0A2342';INS='#1E5F8C';GLD='#C9A84C';TXT='#1A1A2E';MUT='#8492A6'
GRN='#2D7A4F';RED='#C0392B';LT='#F5F7FA';BD='#D0D8E0'

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — Claude generates full analytical dossier
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 1: Claude gerando dossie analitico...\n")
client=anthropic.Anthropic()

PROMPT="""Voce e um analista de investment banking preparando um DOSSIE ANALITICO COMPLETO
sobre uma empresa para servir de base de trabalho para a equipe de agentes.

Este NAO e um equity research com recomendacao de compra/venda.
E um documento FACTUAL e ANALITICO que permite que qualquer profissional entenda
o case por completo: empresa, mercado, financials, riscos, contexto regulatorio.

EMPRESA: Solaris Energia Renovavel S.A.
SETOR: Geracao de energia renovavel — solar fotovoltaica e eolica
SEDE: Fortaleza-CE
PORTE: Mid-cap — Receita ~R$ 1,8Bi

Gere JSON com esta estrutura:
{
  "meta":{
    "company":"Solaris Energia Renovavel S.A.","sector":"Energia Renovavel — Solar e Eolica",
    "date":"marco 2026","purpose":"Dossie Analitico — Base de trabalho para pipeline de agentes"
  },
  "executive_overview":"5-6 frases de sintese factual da empresa — posicao no mercado, porte, modelo, diferenciais, momento atual. SEM recomendacao de investimento.",
  "company":{
    "full_description":"descricao completa — 6-8 frases cobrindo historia, operacao, modelo, posicao competitiva",
    "founded":"ano","hq":"cidade-UF","employees":numero,
    "history_timeline":["2012: fundacao...","2015: ...","2018: ...","2020: ...","2023: ...","2025: ..."],
    "business_model":{
      "segments":[
        {"name":"nome","pct_revenue":XX,"description":"descricao"},
        {"name":"nome","pct_revenue":XX,"description":"descricao"},
        {"name":"nome","pct_revenue":XX,"description":"descricao"}
      ],
      "revenue_model":"como gera receita — PPAs, mercado livre, GD",
      "cost_structure":"principais custos — O&M, arrendamento, depreciacao"
    },
    "competitive_position":{
      "strengths":["4 pontos fortes com dados"],
      "weaknesses":["3 pontos fracos com dados"],
      "market_share":"X% do mercado de geracao renovavel"
    },
    "governance":{
      "structure":"descricao da estrutura societaria",
      "board":"composicao do conselho com independentes",
      "controls":"auditoria, compliance, comites"
    },
    "esg":{
      "environmental":"metricas ambientais — emissoes evitadas, area preservada",
      "social":"metricas sociais — colaboradores, comunidades",
      "governance_esg":"metricas de governanca — independencia, diversidade"
    }
  },
  "market":{
    "tam_brl_bi":numero,"cagr":"X%",
    "overview":"4-5 frases — contexto do setor de energia renovavel no Brasil",
    "regulatory_framework":"marco regulatorio: ANEEL, leiloes, GD, mercado livre, Resolucao normativa",
    "drivers":["5 drivers com dados e fontes"],
    "headwinds":["3 riscos setoriais com dados"],
    "competitive_landscape":{
      "major_players":[
        {"name":"empresa real","capacity_gw":num,"type":"solar/eolica/mista"},
        ...5 players reais
      ],
      "company_position":"posicao da Solaris vs concorrentes com dados"
    },
    "pricing_environment":"evolucao de precos de energia — PLD, ACL, ACR",
    "sources":"fontes dos dados"
  },
  "financials":{
    "years":["2022","2023","2024","2025E","2026E"],
    "revenue":[nums R$M],"revenue_growth":[decimais],
    "cogs":[nums],"gross_profit":[nums],"gross_margin":[decimais],
    "opex":[nums],"ebitda":[nums],"ebitda_margin":[decimais],
    "depreciation":[nums],"ebit":[nums],
    "financial_expenses":[nums],"net_income":[nums],"net_margin":[decimais],
    "total_assets":[nums],"total_equity":[nums],
    "gross_debt":[nums],"cash":[nums],"net_debt":[nums],"dl_ebitda":[decimais],
    "ebitda_coverage":[decimais],
    "capex":[nums],"fcf":[nums],
    "roe":[decimais],"roic":[decimais],
    "installed_capacity_mw":[nums operacional],
    "generation_gwh":[nums],
    "availability_factor":[decimais]
  },
  "debt_profile":{
    "total_gross_debt":numero,"total_net_debt":numero,
    "instruments":[
      {"type":"Debentures/BNDES/etc","amount":numero,"rate":"CDI+X%","maturity":"ano","status":"ativo"},
      ...4 instrumentos
    ],
    "maturity_profile":{"2026":numero,"2027":numero,"2028":numero,"2029":numero,"2030+":numero},
    "weighted_avg_cost":"custo medio ponderado",
    "refinancing_risk":"avaliacao do risco de refinanciamento"
  },
  "operational_kpis":{
    "capacity_mw":numero,"under_construction_mw":numero,
    "ppa_contracted_pct":numero,"avg_ppa_remaining_years":numero,
    "solar_pct":numero,"wind_pct":numero,
    "avg_tariff_mwh":numero,"pld_reference":numero,
    "o_m_cost_mwh":numero
  },
  "risk_assessment":[
    {"category":"Operacional/Mercado/Regulatorio/Financeiro/ESG",
     "risk":"descricao detalhada","probability":"Alta/Media/Baixa",
     "impact":"Alto/Medio/Baixo","mitigant":"mitigante detalhado",
     "monitoring":"como monitorar este risco"},
    ...8 riscos cobrindo todas as categorias
  ],
  "key_questions":"5 perguntas-chave que os agentes devem investigar sobre este case",
  "data_gaps":"3 lacunas de informacao identificadas — dados que precisam ser obtidos"
}

REGRAS: dados REALISTAS para geradora renovavel brasileira mid-cap 2025-2026.
Players de mercado devem ser REAIS (Omega, AES, Engie, Atlas, Casa dos Ventos).
Responda APENAS com JSON."""

resp=client.messages.create(model="claude-sonnet-4-6",max_tokens=16000,messages=[{"role":"user","content":PROMPT}])
raw=resp.content[0].text.strip()
if raw.startswith("```"): raw=raw.split("\n",1)[1].rsplit("```",1)[0]
D=json.loads(raw)
print(f"  Tokens: {resp.usage.input_tokens}in/{resp.usage.output_tokens}out")
print(f"  {D['meta']['company']}\n")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — Charts
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 2: Gerando graficos...\n")
fin=D['financials'];yrs=fin['years']
for k in fin:
    if isinstance(fin[k],list): fin[k]=[v if v is not None else 0 for v in fin[k]]

def mfig(fw=8.5,fh=3.5):
    fig,ax=plt.subplots(figsize=(fw,fh))
    ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(BD);ax.spines['bottom'].set_color(BD)
    ax.tick_params(colors=MUT,labelsize=9);ax.grid(axis='y',color='#E8ECF0',linewidth=0.5)
    return fig,ax
def sf(fig):
    buf=BytesIO();fig.savefig(buf,format='png',dpi=200,bbox_inches='tight',facecolor='white');buf.seek(0);plt.close(fig);return buf

# 1. Revenue + growth
fig,ax1=mfig()
ax1.bar(yrs,fin['revenue'],color=NAV,width=0.5,alpha=0.85)
for i,v in enumerate(fin['revenue']): ax1.text(i,v+max(fin['revenue'])*0.02,f'{v:,.0f}',ha='center',fontsize=9,color=NAV,fontweight='bold')
ax1.set_ylabel('Receita (R$ M)',fontsize=9,color=MUT)
ax2=ax1.twinx()
gr=[g*100 for g in fin['revenue_growth']]
ax2.plot(yrs,gr,'D-',color=GLD,linewidth=2,markersize=7)
for i,v in enumerate(gr): ax2.annotate(f'{v:.0f}%',(yrs[i],v),textcoords="offset points",xytext=(0,10),fontsize=9,ha='center',color='#8B7330',fontweight='bold')
ax2.set_ylabel('Crescimento (%)',fontsize=9,color=MUT);ax1.spines['right'].set_color(BD)
for a in [ax1,ax2]: a.spines['top'].set_visible(False);a.tick_params(colors=MUT,labelsize=9)
ch_rev=sf(fig);print("  ch_revenue OK")

# 2. EBITDA + margin
fig,ax1=mfig()
ax1.bar(yrs,fin['ebitda'],color=INS,width=0.5,alpha=0.85)
for i,v in enumerate(fin['ebitda']): ax1.text(i,v+max(fin['ebitda'])*0.02,f'{v:,.0f}',ha='center',fontsize=9,color=INS,fontweight='bold')
ax1.set_ylabel('EBITDA (R$ M)',fontsize=9,color=MUT)
ax2=ax1.twinx()
mg=[m*100 for m in fin['ebitda_margin']]
ax2.plot(yrs,mg,'o-',color=GRN,linewidth=2,markersize=7)
for i,v in enumerate(mg): ax2.annotate(f'{v:.1f}%',(yrs[i],v),textcoords="offset points",xytext=(0,10),fontsize=9,ha='center',color=GRN,fontweight='bold')
ax2.set_ylabel('Margem EBITDA (%)',fontsize=9,color=MUT);ax1.spines['right'].set_color(BD)
for a in [ax1,ax2]: a.spines['top'].set_visible(False);a.tick_params(colors=MUT,labelsize=9)
ch_ebitda=sf(fig);print("  ch_ebitda OK")

# 3. Leverage
fig,ax1=mfig()
ax1.bar(yrs,fin['dl_ebitda'],color=NAV,width=0.5,alpha=0.85)
for i,v in enumerate(fin['dl_ebitda']): ax1.text(i,v+0.05,f'{v:.1f}x',ha='center',fontsize=10,color=NAV,fontweight='bold')
ax1.set_ylabel('DL/EBITDA (x)',fontsize=9,color=MUT)
ax2=ax1.twinx()
ax2.plot(yrs,fin['ebitda_coverage'],'D-',color=GRN,linewidth=2,markersize=7)
for i,v in enumerate(fin['ebitda_coverage']): ax2.annotate(f'{v:.1f}x',(yrs[i],v),textcoords="offset points",xytext=(0,10),fontsize=9,ha='center',color=GRN,fontweight='bold')
ax2.set_ylabel('Coverage (x)',fontsize=9,color=MUT);ax1.spines['right'].set_color(BD)
for a in [ax1,ax2]: a.spines['top'].set_visible(False);a.tick_params(colors=MUT,labelsize=9)
ch_lev=sf(fig);print("  ch_leverage OK")

# 4. Capacity + Generation
fig,ax1=mfig()
cap=fin.get('installed_capacity_mw',fin['revenue'])
gen=fin.get('generation_gwh',fin['ebitda'])
ax1.bar(yrs,cap,color=GLD,width=0.5,alpha=0.8,label='Capacidade (MW)')
for i,v in enumerate(cap): ax1.text(i,v+max(cap)*0.02,f'{v:,.0f}',ha='center',fontsize=9,color='#8B7330',fontweight='bold')
ax1.set_ylabel('MW Instalado',fontsize=9,color=MUT)
ax2=ax1.twinx()
ax2.plot(yrs,gen,'s-',color=NAV,linewidth=2,markersize=7,label='Geracao (GWh)')
for i,v in enumerate(gen): ax2.annotate(f'{v:,.0f}',(yrs[i],v),textcoords="offset points",xytext=(0,10),fontsize=8,ha='center',color=NAV)
ax2.set_ylabel('GWh',fontsize=9,color=MUT)
l1,la1=ax1.get_legend_handles_labels();l2,la2=ax2.get_legend_handles_labels()
ax1.legend(l1+l2,la1+la2,fontsize=8,frameon=False);ax1.spines['right'].set_color(BD)
for a in [ax1,ax2]: a.spines['top'].set_visible(False);a.tick_params(colors=MUT,labelsize=9)
ch_cap=sf(fig);print("  ch_capacity OK")

# 5. Debt maturity
dp=D.get('debt_profile',{}).get('maturity_profile',{})
if dp:
    fig,ax=mfig(fw=8.5,fh=3)
    dyr=list(dp.keys());dval=list(dp.values())
    bars=ax.bar(dyr,dval,color=[NAV if v<max(dval)*0.8 else RED for v in dval],width=0.5,alpha=0.85)
    for bar,v in zip(bars,dval): ax.text(bar.get_x()+bar.get_width()/2,v+max(dval)*0.03,f'R${v}M',ha='center',fontsize=9,fontweight='bold',color=NAV)
    ax.set_ylabel('R$ Milhoes',fontsize=9,color=MUT);ax.set_xlabel('Vencimento',fontsize=9,color=MUT)
    ch_debt=sf(fig);print("  ch_debt_maturity OK")
else: ch_debt=None

print()

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — Build PDF
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 3: Construindo PDF...\n")
fn="dossie_analitico_solaris_energia.pdf"
c=canvas.Canvas(str(OUT/fn),pagesize=A4)
pg=[0];co=D['company'];mkt=D['market'];meta=D['meta']

def hbar():
    c.setFillColor(HexColor(NAV));c.rect(0,h-1.2*cm,w,1.2*cm,fill=1)
    c.setFont("Helvetica-Bold",8);c.setFillColor(HexColor('#FFFFFF'))
    c.drawString(1.5*cm,h-0.85*cm,f"DOSSIE ANALITICO  |  {meta['company']}  |  {meta['sector']}")
    c.drawRightString(w-1.5*cm,h-0.85*cm,f"IB-Agents  |  {meta['date']}")

def foot():
    pg[0]+=1;c.setStrokeColor(HexColor(BD));c.setLineWidth(0.3);c.line(1.5*cm,1.3*cm,w-1.5*cm,1.3*cm)
    c.setFont("Helvetica",6);c.setFillColor(HexColor(MUT))
    c.drawString(1.5*cm,0.8*cm,"Confidencial  |  IB-Agents Intelligence Platform  |  Documento analitico para uso interno — nao constitui recomendacao de investimento")
    c.drawRightString(w-1.5*cm,0.8*cm,str(pg[0]))

def stitle(title,y):
    c.setFont("Helvetica-Bold",13);c.setFillColor(HexColor(NAV));c.drawString(1.5*cm,y,title)
    c.setStrokeColor(HexColor(GLD));c.setLineWidth(1.5);c.line(1.5*cm,y-0.2*cm,8*cm,y-0.2*cm)
    return y-0.65*cm

def wpara(text,y,font="Helvetica",size=10,color=TXT,indent=1.5):
    c.setFont(font,size);c.setFillColor(HexColor(color))
    words=text.split();line="";lines=[]
    for word in words:
        if c.stringWidth(line+" "+word,font,size)>17*cm: lines.append(line);line=word
        else: line=(line+" "+word).strip()
    if line: lines.append(line)
    for l in lines:
        if y<2.5*cm: c.showPage();hbar();foot();y=h-2.5*cm
        c.drawString(indent*cm,y,l);y-=size*1.4/28.35*cm
    return y

def wbullet(text,y,size=10):
    return wpara(f"•  {text}",y,size=size,indent=2.0)

def addimg(buf,y,cw=17,ch=7):
    if not buf: return y
    if y-ch*cm<2.5*cm: c.showPage();hbar();foot();y=h-2.5*cm
    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(buf),1.5*cm,y-ch*cm,width=cw*cm,height=ch*cm)
    return y-ch*cm-0.4*cm

# ═══════════════════════════════════════════════════════════════════════════
# COVER
c.setFillColor(HexColor(NAV));c.rect(0,h-10*cm,w,10*cm,fill=1)
c.setFillColor(HexColor(GLD));c.rect(1.5*cm,h-10.2*cm,5*cm,0.15*cm,fill=1)
c.setFont("Helvetica-Bold",10);c.setFillColor(HexColor('#FFFFFF'))
c.drawString(1.5*cm,h-2*cm,"DOSSIE ANALITICO COMPLETO")
c.setFont("Helvetica",9);c.setFillColor(HexColor(GLD))
c.drawString(1.5*cm,h-2.6*cm,"Base de trabalho para pipeline de agentes — Documento interno")
c.setFont("Helvetica-Bold",30);c.setFillColor(HexColor('#FFFFFF'))
c.drawString(1.5*cm,h-4.5*cm,meta['company'])
c.setFont("Helvetica",15);c.setFillColor(HexColor(GLD))
c.drawString(1.5*cm,h-5.5*cm,meta['sector'])
c.setFont("Helvetica",10);c.setFillColor(HexColor('#A0B0C8'))
c.drawString(1.5*cm,h-6.8*cm,"Sede: Fortaleza-CE  |  Setor: Energia Renovavel  |  Porte: Mid-Cap")
c.drawString(1.5*cm,h-7.5*cm,f"Data-base: {meta['date']}  |  Finalidade: Alimentar pipeline analise IB")
c.setFont("Helvetica",9);c.setFillColor(HexColor(MUT))
c.drawString(1.5*cm,h-11.5*cm,"IB-Agents Intelligence Platform  |  Estritamente Confidencial")
c.drawString(1.5*cm,h-12*cm,"Este documento NAO constitui recomendacao de investimento.")
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2 — SINTESE EXECUTIVA
hbar();foot();y=h-2.5*cm
y=stitle("Sintese Executiva",y)
y=wpara(D['executive_overview'],y,size=11)-0.3*cm

# KPI boxes
okpis=D.get('operational_kpis',{})
kpis=[
    (f"R$ {fin['revenue'][-2]:,.0f}M","Receita 2024"),
    (f"{fin['ebitda_margin'][-2]*100:.0f}%","Margem EBITDA"),
    (f"{fin['dl_ebitda'][-2]:.1f}x","DL/EBITDA"),
    (f"{okpis.get('capacity_mw',0):,} MW","Capacidade"),
    (f"{okpis.get('ppa_contracted_pct',0)}%","PPAs Contratados"),
    (f"{co['employees']:,}","Colaboradores"),
]
bw=2.6*cm;bh=1.4*cm;gap=0.25*cm;sx=1.5*cm;y-=0.2*cm
for i,(val,label) in enumerate(kpis):
    bx=sx+i*(bw+gap)
    c.setFillColor(HexColor(LT));c.roundRect(bx,y-bh,bw,bh,3,fill=1,stroke=0)
    c.setFont("Helvetica-Bold",13);c.setFillColor(HexColor(NAV));c.drawCentredString(bx+bw/2,y-0.55*cm,val)
    c.setFont("Helvetica",7);c.setFillColor(HexColor(MUT));c.drawCentredString(bx+bw/2,y-1.0*cm,label)
y-=bh+0.5*cm

y=stitle("Pontos Fortes",y)
for s in co['competitive_position']['strengths']: y=wbullet(s,y,size=9)
y-=0.2*cm
y=stitle("Pontos Fracos / Atencao",y)
for w2 in co['competitive_position']['weaknesses']: y=wbullet(w2,y,size=9)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3 — EMPRESA
hbar();foot();y=h-2.5*cm
y=stitle("Descricao da Empresa",y)
y=wpara(co['full_description'],y,size=10)-0.3*cm

y=stitle("Trajetoria",y)
for evt in co['history_timeline']: y=wbullet(evt,y,size=9)
y-=0.2*cm

y=stitle("Modelo de Negocios",y)
bm=co['business_model']
for seg in bm['segments']:
    y=wpara(f"• {seg['name']} ({seg['pct_revenue']}% da receita): {seg['description']}",y,size=9,indent=2.0)
y-=0.15*cm
y=wpara(f"Receita: {bm['revenue_model']}",y,size=9,color=MUT)
y=wpara(f"Custos: {bm['cost_structure']}",y,size=9,color=MUT)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 4 — GOVERNANCA + ESG
hbar();foot();y=h-2.5*cm
y=stitle("Governanca Corporativa",y)
gov=co['governance']
y=wpara(f"Estrutura: {gov['structure']}",y,size=10)-0.1*cm
y=wpara(f"Conselho: {gov['board']}",y,size=10)-0.1*cm
y=wpara(f"Controles: {gov['controls']}",y,size=10)-0.3*cm

y=stitle("ESG — Ambiental, Social e Governanca",y)
esg=co['esg']
y=wpara(f"Ambiental: {esg['environmental']}",y,size=10)-0.1*cm
y=wpara(f"Social: {esg['social']}",y,size=10)-0.1*cm
y=wpara(f"Governanca: {esg['governance_esg']}",y,size=10)-0.5*cm

y=stitle("Capacidade Instalada e Geracao",y)
y=addimg(ch_cap,y,cw=17,ch=7)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 5 — MERCADO
hbar();foot();y=h-2.5*cm
y=stitle(f"Analise de Mercado — TAM R$ {mkt['tam_brl_bi']}Bi ({mkt['cagr']})",y)
y=wpara(mkt['overview'],y,size=10)-0.2*cm

y=stitle("Marco Regulatorio",y)
y=wpara(mkt['regulatory_framework'],y,size=9)-0.2*cm

y=stitle("Drivers de Crescimento",y)
for dr in mkt['drivers']: y=wbullet(dr,y,size=9)
y-=0.2*cm

y=stitle("Ventos Contrarios (Headwinds)",y)
for hw in mkt['headwinds']: y=wbullet(hw,y,size=9)
y-=0.2*cm

y=stitle("Landscape Competitivo",y)
y=wpara(mkt['competitive_landscape']['company_position'],y,size=9)
y=wpara(f"[Fonte: {mkt['sources']}]",y,font="Helvetica-Oblique",size=7,color=MUT)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 6 — FINANCIALS CHARTS
hbar();foot();y=h-2.5*cm
y=stitle("Evolucao de Receita e Crescimento",y)
y=addimg(ch_rev,y,cw=17,ch=7)-0.3*cm
y=stitle("EBITDA e Margem — Evolucao da Rentabilidade Operacional",y)
y=addimg(ch_ebitda,y,cw=17,ch=7)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 7 — TABELA FINANCEIRA COMPLETA
hbar();foot();y=h-2.5*cm
y=stitle("Demonstracoes Financeiras Consolidadas (R$ Milhoes)",y)-0.1*cm

def fmtn(v):
    if v is None: return "—"
    if isinstance(v,float) and abs(v)<1: return f"{v*100:.1f}%"
    if isinstance(v,float) and abs(v)<10: return f"{v:.1f}x"
    return f"{v:,.0f}"

rows=[[""]+ yrs]
metrics=[
    ("Receita Liquida","revenue"),("Cresc. Receita","revenue_growth"),
    ("Lucro Bruto","gross_profit"),("Margem Bruta","gross_margin"),
    ("EBITDA","ebitda"),("Margem EBITDA","ebitda_margin"),
    ("Lucro Liquido","net_income"),("Margem Liquida","net_margin"),
    ("",""),
    ("Divida Bruta","gross_debt"),("Caixa","cash"),("Divida Liquida","net_debt"),
    ("DL/EBITDA","dl_ebitda"),("Coverage","ebitda_coverage"),
    ("Capex","capex"),("FCF","fcf"),
    ("ROE","roe"),("ROIC","roic"),
]
for label,key in metrics:
    if key=="": rows.append([""]*6);continue
    vals=fin.get(key,[0]*5)
    rows.append([label]+[fmtn(v) for v in vals])

cw=[3.5*cm]+[2.7*cm]*len(yrs)
t=Table(rows,colWidths=cw)
t.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),HexColor(NAV)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7.5),
    ('ALIGN',(1,0),(-1,-1),'RIGHT'),('GRID',(0,0),(-1,-1),0.3,HexColor(BD)),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor(LT)]),
    ('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),('TEXTCOLOR',(0,1),(0,-1),HexColor(NAV)),
]))
tw2,th2=t.wrap(0,0);t.drawOn(c,1.5*cm,y-th2)
y=y-th2-0.3*cm
c.setFont("Helvetica-Oblique",7);c.setFillColor(HexColor(MUT))
c.drawString(1.5*cm,y,"[Fonte: DFs consolidadas IFRS. Projecoes 2025E-2026E: IB-Agents. Auditoria: EY.]")
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 8 — CREDITO + DIVIDA
hbar();foot();y=h-2.5*cm
y=stitle("Estrutura de Capital e Alavancagem",y)
y=addimg(ch_lev,y,cw=17,ch=7)-0.3*cm

y=stitle("Perfil de Vencimento da Divida",y)
if ch_debt: y=addimg(ch_debt,y,cw=17,ch=6)
dp2=D.get('debt_profile',{})
if dp2.get('instruments'):
    y-=0.2*cm
    y=stitle("Composicao da Divida",y)-0.1*cm
    for inst in dp2['instruments']:
        y=wpara(f"• {inst['type']}: R$ {inst['amount']}M | {inst['rate']} | Venc: {inst['maturity']}",y,size=9)
    y-=0.1*cm
    y=wpara(f"Custo medio ponderado: {dp2.get('weighted_avg_cost','N/D')}",y,size=9,color=MUT)
    y=wpara(f"Risco de refinanciamento: {dp2.get('refinancing_risk','N/D')}",y,size=9,color=MUT)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 9 — RISCOS
hbar();foot();y=h-2.5*cm
y=stitle("Avaliacao de Riscos — 8 Dimensoes",y)
for ri in D['risk_assessment']:
    cat=ri.get('category','')
    y=wpara(f"{cat}: {ri['risk']}",y,font="Helvetica-Bold",size=9.5,color=TXT)
    y=wpara(f"Probabilidade: {ri['probability']} | Impacto: {ri['impact']}",y,size=8,color=MUT,indent=2.3)
    y=wpara(f"Mitigante: {ri['mitigant']}",y,size=8,color=MUT,indent=2.3)
    y=wpara(f"Monitoramento: {ri.get('monitoring','N/D')}",y,size=8,color=MUT,indent=2.3)
    y-=0.15*cm
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 10 — PERGUNTAS-CHAVE + LACUNAS + DISCLAIMER
hbar();foot();y=h-2.5*cm
y=stitle("Perguntas-Chave para Investigacao pelos Agentes",y)
if isinstance(D.get('key_questions'),list):
    for q in D['key_questions']: y=wbullet(q,y,size=10)
else:
    y=wpara(D.get('key_questions',''),y,size=10)
y-=0.3*cm

y=stitle("Lacunas de Informacao Identificadas",y)
if isinstance(D.get('data_gaps'),list):
    for g in D['data_gaps']: y=wbullet(g,y,size=10)
else:
    y=wpara(D.get('data_gaps',''),y,size=10)
y-=0.5*cm

y=stitle("Nota sobre este Documento",y)
y=wpara("Este dossie analitico foi preparado pelo IB-Agents Intelligence Platform como base de trabalho para o pipeline de agentes de investment banking. O documento tem finalidade exclusivamente analitica e informativa — NAO constitui recomendacao de investimento, oferta ou solicitacao para aquisicao de valores mobiliarios.",y,size=9,color=MUT)
y-=0.2*cm
y=wpara("Os dados financeiros projetados sao estimativas baseadas em premissas que podem nao se concretizar. Todas as fontes estao identificadas ao longo do documento.",y,size=9,color=MUT)
y-=0.2*cm
y=wpara("[RCVM 160/2022 | Codigo ANBIMA | Lei 6.385/1976]",y,font="Helvetica-Oblique",size=7,color=MUT)

c.save()
print(f"\nGerado: {fn} ({pg[0]} paginas)")
print(f"Local: {(OUT/fn).resolve()}")
