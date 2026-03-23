"""
Research Report AI — Relatorio completo de equity research
Claude API (analise) + ReportLab (PDF profissional) + matplotlib (graficos)
Case ficticio: Vetta Logistica S.A. — Setor Logistica/Transporte
Padrao: Itau BBA / BTG Research / XP Investimentos
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
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

OUT=Path("./templates/models"); OUT.mkdir(parents=True,exist_ok=True)
w,h=A4

# Paleta
NAV='#0A2342'; INS='#1E5F8C'; GLD='#C9A84C'; TXT='#1A1A2E'; MUT='#8492A6'
GRN='#2D7A4F'; RED='#C0392B'; BG='#FFFFFF'; LT='#F5F7FA'; BD='#D0D8E0'

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1 — Claude generates full research
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 1: Claude gerando analise de research...\n")
client=anthropic.Anthropic()

PROMPT="""Voce e um analista senior de equity research de um banco brasileiro (Itau BBA / BTG).
Gere um relatorio COMPLETO de initiation of coverage para:

EMPRESA: Vetta Logistica S.A.
TICKER: VETT3
SETOR: Logistica integrada — transporte rodoviario, armazenagem e last-mile
LISTADA: B3 — Novo Mercado
MARKET CAP: ~R$ 4,2 Bi
COTACAO ATUAL: R$ 18,50

Gere JSON com esta estrutura:
{
  "meta": {
    "company":"Vetta Logistica S.A.","ticker":"VETT3","sector":"Logistica Integrada",
    "recommendation":"COMPRA/NEUTRO/VENDA","target_price":numero,"current_price":18.50,
    "upside":"XX%","date":"marco 2026","analyst":"IB-Agents Research"
  },
  "executive_summary":"4-5 frases resumindo a tese com dados concretos",
  "investment_thesis":{
    "bull_points":["5 razoes para comprar com dados"],
    "bear_points":["3 riscos principais com dados"]
  },
  "company":{
    "description":"3-4 frases descrevendo a empresa",
    "history":"timeline resumida fundacao ate hoje",
    "business_model":"como gera receita — 3 segmentos com % da receita",
    "competitive_advantages":["4 vantagens com dados"],
    "management":"resumo C-level e board",
    "esg":"resumo ESG com metricas"
  },
  "market":{
    "tam_brl_bi":numero,"cagr":"X%",
    "overview":"3-4 frases do setor logistica Brasil",
    "drivers":["4 drivers com dados de fonte"],
    "competitive_landscape":"descricao com market shares",
    "source":"fontes"
  },
  "financials":{
    "years":["2022","2023","2024","2025E","2026E"],
    "revenue":[nums R$M],"revenue_growth":[decimais],
    "gross_profit":[nums],"gross_margin":[decimais],
    "ebitda":[nums],"ebitda_margin":[decimais],
    "net_income":[nums],"net_margin":[decimais],
    "eps":[nums R$ por acao],
    "net_debt":[nums],"dl_ebitda":[decimais],
    "roe":[decimais],"roic":[decimais],
    "fcf":[nums],"dividend_yield":[decimais],
    "capex":[nums],
    "ev_ebitda_implied":[decimais multiplo]
  },
  "valuation":{
    "dcf":{"wacc":numero,"g":numero,"ev":numero,"equity_value":numero,"price_per_share":numero},
    "comps":{
      "peers":[
        {"name":"empresa REAL B3","ticker":"","ev_ebitda":numero,"pe":numero,"ev_rev":numero},
        ...5 peers REAIS do setor logistica
      ],
      "median_ev_ebitda":numero,"implied_price":numero
    },
    "football_field":{"low":numero,"mid":numero,"high":numero},
    "sensitivity":{
      "wacc_range":["11%","12%","13%","14%"],
      "g_range":["3%","4%","5%"],
      "prices":[[nums 4x3 matrix]]
    }
  },
  "risks":[
    {"risk":"descricao","probability":"Alta/Media/Baixa","impact":"Alto/Medio/Baixo","mitigant":"mitigante"},
    ...5 riscos
  ],
  "catalysts":["4 catalisadores de curto/medio prazo com timeline"]
}

REGRAS: dados REALISTAS para logistica BR 2025-2026, peers REAIS da B3, metricas consistentes.
Responda APENAS com JSON."""

resp=client.messages.create(model="claude-sonnet-4-6",max_tokens=8000,messages=[{"role":"user","content":PROMPT}])
raw=resp.content[0].text.strip()
if raw.startswith("```"): raw=raw.split("\n",1)[1].rsplit("```",1)[0]
D=json.loads(raw)
print(f"  Tokens: {resp.usage.input_tokens}in/{resp.usage.output_tokens}out")
print(f"  {D['meta']['company']} | {D['meta']['recommendation']} | Target: R${D['meta']['target_price']}\n")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2 — Charts
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 2: Gerando graficos...\n")
fin=D['financials']; yrs=fin['years']
# Sanitize None values
for k in fin:
    if isinstance(fin[k],list):
        fin[k]=[v if v is not None else 0 for v in fin[k]]

def mfig(w=8,h=3.5):
    fig,ax=plt.subplots(figsize=(w,h))
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
ax2.set_ylabel('Crescimento (%)',fontsize=9,color=MUT)
ax1.legend(['Receita'],fontsize=8,frameon=False,loc='upper left');ax2.legend(['Crescimento YoY'],fontsize=8,frameon=False,loc='upper right')
ax1.spines['right'].set_color(BD)
for a in [ax1,ax2]: a.spines['top'].set_visible(False);a.tick_params(colors=MUT,labelsize=9)
ch1=sf(fig);print("  ch_revenue OK")

# 2. EBITDA + margin
fig,ax1=mfig()
ax1.bar(yrs,fin['ebitda'],color=INS,width=0.5,alpha=0.85)
for i,v in enumerate(fin['ebitda']): ax1.text(i,v+max(fin['ebitda'])*0.02,f'{v:,.0f}',ha='center',fontsize=9,color=INS,fontweight='bold')
ax1.set_ylabel('EBITDA (R$ M)',fontsize=9,color=MUT)
ax2=ax1.twinx()
mg=[m*100 for m in fin['ebitda_margin']]
ax2.plot(yrs,mg,'o-',color=GRN,linewidth=2,markersize=7)
for i,v in enumerate(mg): ax2.annotate(f'{v:.1f}%',(yrs[i],v),textcoords="offset points",xytext=(0,10),fontsize=9,ha='center',color=GRN,fontweight='bold')
ax2.set_ylabel('Margem EBITDA (%)',fontsize=9,color=MUT)
ax1.spines['right'].set_color(BD)
for a in [ax1,ax2]: a.spines['top'].set_visible(False);a.tick_params(colors=MUT,labelsize=9)
ch2=sf(fig);print("  ch_ebitda OK")

# 3. ROE + ROIC
fig,ax=mfig()
roe=[r*100 for r in fin['roe']]; roic=[r*100 for r in fin['roic']]
ax.plot(yrs,roe,'s-',color=NAV,linewidth=2,markersize=7,label='ROE (%)')
ax.plot(yrs,roic,'D-',color=GRN,linewidth=2,markersize=7,label='ROIC (%)')
for i,v in enumerate(roe): ax.annotate(f'{v:.1f}%',(yrs[i],v),textcoords="offset points",xytext=(0,10),fontsize=8,ha='center',color=NAV)
for i,v in enumerate(roic): ax.annotate(f'{v:.1f}%',(yrs[i],v),textcoords="offset points",xytext=(0,-15),fontsize=8,ha='center',color=GRN)
ax.legend(fontsize=9,frameon=False);ax.set_ylabel('%',fontsize=9,color=MUT)
ch3=sf(fig);print("  ch_returns OK")

# 4. Football field
fig,ax=mfig(w=8,h=3)
ff=D['valuation']['football_field']
methods=['DCF','EV/EBITDA Comps','P/E Comps','52-Week Range']
lows=[ff['low']*0.85,ff['low']*0.9,ff['low']*0.88,D['meta']['current_price']*0.82]
mids=[D['valuation']['dcf']['price_per_share'],D['valuation']['comps']['implied_price'],ff['mid']*0.95,D['meta']['current_price']]
highs=[ff['high']*1.05,ff['high'],ff['high']*0.98,D['meta']['current_price']*1.15]
for i in range(len(methods)):
    ax.barh(i,highs[i]-lows[i],left=lows[i],height=0.4,color=NAV,alpha=0.2)
    ax.plot(mids[i],i,'D',color=NAV,markersize=8)
    ax.text(highs[i]+0.3,i,f'R$ {mids[i]:.2f}',va='center',fontsize=9,color=NAV,fontweight='bold')
ax.axvline(x=D['meta']['target_price'],color=GRN,linestyle='--',linewidth=2,label=f'Target R$ {D["meta"]["target_price"]:.2f}')
ax.axvline(x=D['meta']['current_price'],color=RED,linestyle=':',linewidth=1.5,label=f'Atual R$ {D["meta"]["current_price"]:.2f}')
ax.set_yticks(range(len(methods)));ax.set_yticklabels(methods,fontsize=10)
ax.set_xlabel('R$ / Acao',fontsize=9,color=MUT)
ax.legend(fontsize=8,frameon=False)
ch4=sf(fig);print("  ch_football OK")

# 5. EV/EBITDA trend
fig,ax=mfig()
ev=[e for e in fin['ev_ebitda_implied']]
ax.bar(yrs,ev,color=GLD,width=0.5,alpha=0.8)
for i,v in enumerate(ev): ax.text(i,v+0.1,f'{v:.1f}x',ha='center',fontsize=10,color='#8B7330',fontweight='bold')
ax.axhline(y=D['valuation']['comps']['median_ev_ebitda'],color=NAV,linestyle='--',linewidth=1.5,label=f'Mediana Peers ({D["valuation"]["comps"]["median_ev_ebitda"]:.1f}x)')
ax.set_ylabel('EV/EBITDA (x)',fontsize=9,color=MUT);ax.legend(fontsize=9,frameon=False)
ch5=sf(fig);print("  ch_eveb OK\n")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3 — Build PDF (ReportLab)
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 3: Construindo PDF profissional...\n")

fn="research_report_vetta_logistica.pdf"
c=canvas.Canvas(str(OUT/fn),pagesize=A4)
pg=[0]
meta=D['meta']

def navy(): return HexColor(NAV)
def ins(): return HexColor(INS)
def gold(): return HexColor(GLD)
def txt_c(): return HexColor(TXT)
def mut(): return HexColor(MUT)
def bg_c(): return HexColor(BG)

def header_bar():
    c.setFillColor(navy());c.rect(0,h-1.2*cm,w,1.2*cm,fill=1)
    c.setFont("Helvetica-Bold",8);c.setFillColor(HexColor('#FFFFFF'))
    c.drawString(1.5*cm,h-0.85*cm,f"{meta['company']}  |  {meta['ticker']}  |  {meta['recommendation']}  |  Target: R$ {meta['target_price']:.2f}  |  Upside: {meta['upside']}")
    c.drawRightString(w-1.5*cm,h-0.85*cm,f"IB-Agents Research  |  {meta['date']}")

def footer():
    pg[0]+=1
    c.setStrokeColor(HexColor(BD));c.setLineWidth(0.3);c.line(1.5*cm,1.3*cm,w-1.5*cm,1.3*cm)
    c.setFont("Helvetica",6);c.setFillColor(mut())
    c.drawString(1.5*cm,0.8*cm,"Confidencial  |  IB-Agents Intelligence Platform  |  Este relatorio nao constitui recomendacao de investimento")
    c.drawRightString(w-1.5*cm,0.8*cm,str(pg[0]))

def section_title(title,y):
    c.setFont("Helvetica-Bold",14);c.setFillColor(navy())
    c.drawString(1.5*cm,y,title)
    c.setStrokeColor(gold());c.setLineWidth(1.5);c.line(1.5*cm,y-0.25*cm,8*cm,y-0.25*cm)
    return y-0.7*cm

def write_para(text,y,font="Helvetica",size=10,color=TXT,indent=1.5,max_w=17):
    c.setFont(font,size);c.setFillColor(HexColor(color))
    words=text.split();line="";lines=[]
    for word in words:
        if c.stringWidth(line+" "+word,font,size)>max_w*cm:
            lines.append(line);line=word
        else: line=(line+" "+word).strip()
    if line: lines.append(line)
    for l in lines:
        if y<2.5*cm: c.showPage();header_bar();footer();y=h-2.5*cm
        c.drawString(indent*cm,y,l);y-=size*1.4/28.35*cm
    return y

def write_bullet(text,y,size=10):
    y=write_para(f"•  {text}",y,size=size,indent=2.0)
    return y

def add_chart(buf,y,cw=16,ch_h=7):
    if y-ch_h*cm<2.5*cm: c.showPage();header_bar();footer();y=h-2.5*cm
    from reportlab.lib.utils import ImageReader
    img=ImageReader(buf)
    c.drawImage(img,1.5*cm,y-ch_h*cm,width=cw*cm,height=ch_h*cm)
    return y-ch_h*cm-0.5*cm

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 1 — COVER
# ═══════════════════════════════════════════════════════════════════════════
c.setFillColor(navy());c.rect(0,h-10*cm,w,10*cm,fill=1)
c.setFillColor(gold());c.rect(1.5*cm,h-10.2*cm,5*cm,0.15*cm,fill=1)

c.setFont("Helvetica-Bold",11);c.setFillColor(HexColor('#FFFFFF'))
c.drawString(1.5*cm,h-2*cm,"EQUITY RESEARCH  |  INITIATION OF COVERAGE")

c.setFont("Helvetica-Bold",32);c.drawString(1.5*cm,h-4*cm,meta['company'])
c.setFont("Helvetica",16);c.setFillColor(gold())
c.drawString(1.5*cm,h-5.2*cm,f"{meta['ticker']}  |  B3 — Novo Mercado  |  {meta['sector']}")

c.setFont("Helvetica-Bold",22);c.setFillColor(HexColor('#FFFFFF'))
c.drawString(1.5*cm,h-7*cm,f"Recomendacao: {meta['recommendation']}")
c.setFont("Helvetica-Bold",18);c.setFillColor(gold())
c.drawString(1.5*cm,h-8*cm,f"Preco-Alvo: R$ {meta['target_price']:.2f}  |  Upside: {meta['upside']}")
c.setFont("Helvetica",11);c.setFillColor(HexColor('#A0B0C8'))
c.drawString(1.5*cm,h-9*cm,f"Cotacao Atual: R$ {meta['current_price']:.2f}  |  Market Cap: ~R$ 4,2 Bi")

c.setFont("Helvetica",10);c.setFillColor(mut())
c.drawString(1.5*cm,h-11.5*cm,f"IB-Agents Intelligence Platform  |  {meta['date']}")
c.drawString(1.5*cm,h-12.2*cm,"Estritamente Privado e Confidencial — RCVM 160/2022")
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2 — EXECUTIVE SUMMARY + KPIs
# ═══════════════════════════════════════════════════════════════════════════
header_bar();footer()
y=h-2.5*cm
y=section_title("Executive Summary",y)
y=write_para(D['executive_summary'],y,size=11)-0.3*cm

# KPI boxes
kpis=[
    (f"R$ {meta['target_price']:.2f}","Preco-Alvo"),
    (meta['upside'],"Upside"),
    (f"{fin['ebitda_margin'][-2]*100:.1f}%","Margem EBITDA"),
    (f"{fin['dl_ebitda'][-2]:.1f}x","DL/EBITDA"),
    (f"{fin['roe'][-2]*100:.1f}%","ROE"),
    (f"{fin['dividend_yield'][-2]*100:.1f}%","Div. Yield"),
]
box_w=2.6*cm;box_h=1.5*cm;gap=0.3*cm;start_x=1.5*cm
y-=0.3*cm
for i,(val,label) in enumerate(kpis):
    bx=start_x+i*(box_w+gap)
    c.setFillColor(HexColor(LT));c.roundRect(bx,y-box_h,box_w,box_h,3,fill=1,stroke=0)
    c.setFont("Helvetica-Bold",14);c.setFillColor(navy());c.drawCentredString(bx+box_w/2,y-0.6*cm,val)
    c.setFont("Helvetica",7);c.setFillColor(mut());c.drawCentredString(bx+box_w/2,y-1.1*cm,label)
y-=box_h+0.5*cm

y=section_title("Tese de Investimento — Bull Case",y)
for pt in D['investment_thesis']['bull_points']:
    y=write_bullet(pt,y,size=10)
y-=0.3*cm
y=section_title("Principais Riscos — Bear Case",y)
for pt in D['investment_thesis']['bear_points']:
    y=write_bullet(pt,y,size=10)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3 — COMPANY OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
header_bar();footer()
y=h-2.5*cm
y=section_title("Visao Geral da Empresa",y)
y=write_para(D['company']['description'],y,size=10)-0.3*cm

y=section_title("Modelo de Negocios",y)
y=write_para(D['company']['business_model'],y,size=10)-0.3*cm

y=section_title("Vantagens Competitivas",y)
for adv in D['company']['competitive_advantages']:
    y=write_bullet(adv,y,size=10)
y-=0.3*cm

y=section_title("Gestao",y)
y=write_para(D['company']['management'],y,size=10)-0.3*cm

y=section_title("ESG",y)
y=write_para(D['company']['esg'],y,size=10)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 4 — MERCADO + CHART RECEITA
# ═══════════════════════════════════════════════════════════════════════════
header_bar();footer()
y=h-2.5*cm
y=section_title(f"Analise de Mercado — TAM R$ {D['market']['tam_brl_bi']}Bi ({D['market']['cagr']})",y)
y=write_para(D['market']['overview'],y,size=10)-0.3*cm
for dr in D['market']['drivers']:
    y=write_bullet(dr,y,size=9)
y-=0.2*cm
y=write_para(f"Landscape: {D['market']['competitive_landscape']}",y,size=9,color=MUT)-0.2*cm
y=write_para(f"[Fonte: {D['market']['source']}]",y,font="Helvetica-Oblique",size=8,color=MUT)-0.5*cm

y=section_title("Evolucao de Receita e Crescimento",y)
y=add_chart(ch1,y,cw=17,ch_h=7)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 5 — FINANCIALS + CHARTS
# ═══════════════════════════════════════════════════════════════════════════
header_bar();footer()
y=h-2.5*cm
y=section_title("EBITDA e Margem — Expansao consistente reflete ganhos de escala",y)
y=add_chart(ch2,y,cw=17,ch_h=7)-0.3*cm

y=section_title("Retorno sobre Capital — ROE e ROIC acima do custo de capital",y)
y=add_chart(ch3,y,cw=17,ch_h=7)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 6 — TABELA FINANCEIRA COMPLETA
# ═══════════════════════════════════════════════════════════════════════════
header_bar();footer()
y=h-2.5*cm
y=section_title("Demonstracoes Financeiras Consolidadas (R$ Milhoes)",y)-0.2*cm

# Build table data
def fmt(v):
    if isinstance(v,float):
        if abs(v)<1: return f"{v*100:.1f}%"
        if abs(v)<10: return f"{v:.1f}x"
        return f"{v:,.0f}"
    return str(v)

rows=[["",]+yrs,
    ["Receita Liquida"]+[f"{v:,.0f}" for v in fin['revenue']],
    ["Cresc. Receita"]+[f"{v*100:.1f}%" for v in fin['revenue_growth']],
    ["Lucro Bruto"]+[f"{v:,.0f}" for v in fin['gross_profit']],
    ["Margem Bruta"]+[f"{v*100:.1f}%" for v in fin['gross_margin']],
    ["EBITDA"]+[f"{v:,.0f}" for v in fin['ebitda']],
    ["Margem EBITDA"]+[f"{v*100:.1f}%" for v in fin['ebitda_margin']],
    ["Lucro Liquido"]+[f"{v:,.0f}" for v in fin['net_income']],
    ["Margem Liquida"]+[f"{v*100:.1f}%" for v in fin['net_margin']],
    ["LPA (R$/acao)"]+[f"R$ {v:.2f}" for v in fin['eps']],
    ["","","","","",""],
    ["Divida Liquida"]+[f"{v:,.0f}" for v in fin['net_debt']],
    ["DL/EBITDA"]+[f"{v:.1f}x" for v in fin['dl_ebitda']],
    ["ROE"]+[f"{v*100:.1f}%" for v in fin['roe']],
    ["ROIC"]+[f"{v*100:.1f}%" for v in fin['roic']],
    ["FCF"]+[f"{v:,.0f}" for v in fin['fcf']],
    ["Div. Yield"]+[f"{v*100:.1f}%" for v in fin['dividend_yield']],
    ["EV/EBITDA"]+[f"{v:.1f}x" for v in fin['ev_ebitda_implied']],
]

col_w=[3.5*cm]+[2.8*cm]*len(yrs)
t=Table(rows,colWidths=col_w)
style=[
    ('BACKGROUND',(0,0),(-1,0),HexColor(NAV)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),
    ('ALIGN',(1,0),(-1,-1),'RIGHT'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ('GRID',(0,0),(-1,-1),0.3,HexColor(BD)),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor(LT)]),
    ('FONTNAME',(0,1),(0,-1),'Helvetica-Bold'),('TEXTCOLOR',(0,1),(0,-1),HexColor(NAV)),
]
t.setStyle(TableStyle(style))
tw,th=t.wrap(0,0);t.drawOn(c,1.5*cm,y-th)
y=y-th-0.5*cm

c.setFont("Helvetica-Oblique",7);c.setFillColor(mut())
c.drawString(1.5*cm,y,"[Fonte: DFs IFRS auditadas. Projecoes 2025E-2026E: IB-Agents Research. LPA baseado em 227M acoes.]")
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 7 — VALUATION
# ═══════════════════════════════════════════════════════════════════════════
header_bar();footer()
y=h-2.5*cm
y=section_title(f"Valuation — Preco-Alvo R$ {meta['target_price']:.2f} ({meta['upside']} upside)",y)

dcf=D['valuation']['dcf']
y=write_para(f"DCF (WACC {dcf['wacc']}%, g {dcf['g']}%): EV R$ {dcf['ev']:,.0f}M → Equity R$ {dcf['equity_value']:,.0f}M → R$ {dcf['price_per_share']:.2f}/acao",y,font="Helvetica-Bold",size=10,color=NAV)-0.3*cm

# Comps table
y=section_title("Trading Comps — Peers B3",y)-0.1*cm
comp_rows=[["Empresa","Ticker","EV/EBITDA","P/E","EV/Receita"]]
for p in D['valuation']['comps']['peers']:
    comp_rows.append([p['name'],p['ticker'],f"{p['ev_ebitda']:.1f}x",f"{p['pe']:.1f}x",f"{p['ev_rev']:.1f}x"])
comp_rows.append(["Mediana","",f"{D['valuation']['comps']['median_ev_ebitda']:.1f}x","",""])
comp_rows.append([meta['company'],meta['ticker'],f"{fin['ev_ebitda_implied'][-2]:.1f}x","",""])

ct=Table(comp_rows,colWidths=[4.5*cm,2.5*cm,2.5*cm,2.5*cm,2.5*cm])
ct.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),HexColor(NAV)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
    ('ALIGN',(2,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.3,HexColor(BD)),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,HexColor(LT)]),
    ('BACKGROUND',(0,-1),(-1,-1),HexColor('#E8F0FE')),('FONTNAME',(0,-1),(-1,-1),'Helvetica-Bold'),
]))
ctw,cth=ct.wrap(0,0);ct.drawOn(c,1.5*cm,y-cth);y=y-cth-0.5*cm

y=section_title("Football Field — Range de Valuation",y)
y=add_chart(ch4,y,cw=17,ch_h=6)
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 8 — EV/EBITDA + SENSITIVITY
# ═══════════════════════════════════════════════════════════════════════════
header_bar();footer()
y=h-2.5*cm
y=section_title("EV/EBITDA Historico e Projetado — Desconto vs Peers",y)
y=add_chart(ch5,y,cw=17,ch_h=7)-0.3*cm

# Sensitivity table
sens=D['valuation']['sensitivity']
y=section_title("Sensibilidade — Preco/Acao por WACC x Crescimento Perpetuidade",y)-0.1*cm
srows=[["WACC \\ g"]+sens['g_range']]
for i,wacc in enumerate(sens['wacc_range']):
    row=[wacc]+[f"R$ {p:.2f}" for p in sens['prices'][i]]
    srows.append(row)
st=Table(srows,colWidths=[3*cm]+[3.5*cm]*len(sens['g_range']))
st.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),HexColor(NAV)),('TEXTCOLOR',(0,0),(-1,0),colors.white),
    ('BACKGROUND',(0,1),(0,-1),HexColor(NAV)),('TEXTCOLOR',(0,1),(0,-1),colors.white),
    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
    ('FONTSIZE',(0,0),(-1,-1),10),('ALIGN',(0,0),(-1,-1),'CENTER'),
    ('GRID',(0,0),(-1,-1),0.3,HexColor(BD)),
    ('ROWBACKGROUNDS',(1,1),(-1,-1),[colors.white,HexColor(LT)]),
]))
stw,sth=st.wrap(0,0);st.drawOn(c,1.5*cm,y-sth);y=y-sth-0.3*cm
c.setFont("Helvetica-Oblique",7);c.setFillColor(mut())
c.drawString(1.5*cm,y,"[Caso base destacado. Premissas: projecao 5 anos, terminal value perpetuidade, dados Damodaran para beta/ERP.]")
c.showPage()

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 9 — RISCOS + CATALISADORES
# ═══════════════════════════════════════════════════════════════════════════
header_bar();footer()
y=h-2.5*cm
y=section_title("Fatores de Risco",y)
for ri in D['risks']:
    y=write_para(f"• {ri['risk']}",y,font="Helvetica-Bold",size=10,color=TXT)
    y=write_para(f"  Probabilidade: {ri['probability']} | Impacto: {ri['impact']} | Mitigante: {ri['mitigant']}",y,size=9,color=MUT,indent=2.3)
    y-=0.15*cm

y-=0.3*cm
y=section_title("Catalisadores de Curto/Medio Prazo",y)
for cat in D['catalysts']:
    y=write_bullet(cat,y,size=10)

y-=0.5*cm
y=section_title("Disclaimer",y)
y=write_para("Este relatorio foi preparado pelo IB-Agents Intelligence Platform com finalidade exclusivamente informativa e nao constitui recomendacao de investimento. As projecoes sao baseadas em premissas que podem nao se concretizar. Investidores devem conduzir sua propria analise antes de tomar decisoes. Rendimentos passados nao sao garantia de resultados futuros.",y,size=8,color=MUT)
y=write_para("[RCVM 160/2022 | RCVM 30/2021 | Codigo ANBIMA | Lei 6.385/1976]",y,font="Helvetica-Oblique",size=7,color=MUT)

c.save()
print(f"\nGerado: {fn} ({pg[0]} paginas)")
print(f"Local: {(OUT/fn).resolve()}")
