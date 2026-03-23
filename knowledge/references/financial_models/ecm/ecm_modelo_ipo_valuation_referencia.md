# Modelo de Referencia — Estrutura de Planilha de Valuation para IPO (ECM)

Este documento descreve a logica e estrutura das abas de um modelo de valuation para IPO.

---

## Aba 1: Capa / Sumario da Oferta

| Campo | Exemplo |
|-------|---------|
| Companhia | Empresa ABC S.A. |
| Setor | Logistica e Transporte |
| Tipo de Oferta | IPO — Oferta Publica Inicial |
| Modalidade | Primaria + Secundaria (mista) |
| Volume Estimado | R$ 800 milhoes a R$ 1,2 bilhao |
| Range de Preco por Acao | R$ 14,00 a R$ 18,00 |
| Acoes Pre-IPO | 400 milhoes |
| Acoes Novas (Primaria) | 50 milhoes |
| Acoes Secundarias | 30 milhoes |
| Acoes Totais Pos-IPO | 450 milhoes |
| Free Float Estimado | 17,8% |
| Segmento B3 | Novo Mercado |
| Coordenador Lider | [Banco] |
| Coordenadores | [Bancos] |

---

## Aba 2: Premissas e Projecoes Financeiras

Projecoes para os proximos 5 anos (base do DCF e multiplos forward):

| Linha | Ano 1 | Ano 2 | Ano 3 | Ano 4 | Ano 5 |
|-------|-------|-------|-------|-------|-------|
| Receita Bruta | [X] | [X x 1,15] | ... | | |
| (-) Deducoes | | | | | |
| Receita Liquida | | | | | |
| Margem Bruta (%) | | | | | |
| EBITDA | | | | | |
| Margem EBITDA (%) | | | | | |
| EBIT | | | | | |
| Lucro Liquido | | | | | |
| CAPEX | | | | | |
| Variacao Capital de Giro | | | | | |
| FCF (Free Cash Flow to Firm) | | | | | |

---

## Aba 3: Trading Comps (Multiplos de Mercado)

Lista de empresas comparaveis com multiplos LTM e NTM (proximo ano):

| Empresa | Ticker | Mkt Cap | EV | EV/EBITDA LTM | EV/EBITDA NTM | P/L LTM | P/L NTM | Crescimento Receita |
|---------|--------|---------|-----|---------------|---------------|---------|---------|---------------------|
| Peer 1 | [TICK3] | R$ X bi | R$ Y bi | Xx | Xx | Xx | Xx | XX% |
| Peer 2 | [TICK3] | | | | | | | |
| Peer 3 | [TICK3] | | | | | | | |
| Media | | | | Xx | Xx | | | |
| Mediana | | | | Xx | Xx | | | |

Valuation implicito pela mediana:
  EV = Mediana EV/EBITDA x EBITDA da empresa
  Equity Value = EV - DL
  Preco / Acao = Equity Value / Acoes Diluidas

---

## Aba 4: Transaction Comps (M&A Comparaveis)

| Transacao | Ano | Alvo | Comprador | EV/EBITDA | Premio de Controle |
|-----------|-----|------|-----------|-----------|-------------------|
| [Nome] | [Ano] | [Empresa] | [Adquirente] | Xx | XX% |

---

## Aba 5: DCF — Fluxo de Caixa Descontado

### Premissas de WACC

| Parametro | Valor | Fonte |
|-----------|-------|-------|
| Rf (Taxa Livre de Risco) | X% | NTN-B longa ou US Treasury + basis |
| Beta Desalavancado (peers) | X | Calculado dos peers |
| Beta Re-alavancado | X | Ajustado para estrutura de capital alvo |
| Premio de Risco de Mercado | 5,5% | Estimativa historica BR |
| Country Risk Premium | X% | EMBI+ Brasil |
| Custo do Equity (Ke) | X% | CAPM |
| Custo da Divida Bruta (Kd) | X% | Media ponderada das dividas |
| Aliquota IR/CSLL | 34% | Padrao Brasil |
| Kd pos-IR | X% | Kd x (1 - 34%) |
| D/(D+E) alvo | X% | Estrutura de capital de longo prazo |
| WACC | X% | Formula WACC |

### Calculo do DCF

  Ano 1: FCF / (1+WACC)^1
  Ano 2: FCF / (1+WACC)^2
  ...
  Ano N: FCF / (1+WACC)^N
  Valor Terminal = FCF_N x (1+g) / (WACC - g)
  VT Descontado = VT / (1+WACC)^N

  EV = Soma FCFs Descontados + VT Descontado
  Equity Value = EV - Divida Liquida
  Preco / Acao = Equity Value / Acoes Diluidas

### Tabela de Sensibilidade WACC x g

|  | g=2,0% | g=2,5% | g=3,0% | g=3,5% | g=4,0% |
|--|--------|--------|--------|--------|--------|
| WACC-1% | R$ | R$ | R$ | R$ | R$ |
| WACC | R$ | **R$ (base)** | R$ | R$ | R$ |
| WACC+1% | R$ | R$ | R$ | R$ | R$ |

---

## Aba 6: Football Field (Resumo de Valuation)

Apresenta o range de preco implicito por cada metodologia:

| Metodologia | Preco Minimo | Preco Maximo |
|-------------|-------------|-------------|
| EV/EBITDA LTM (P25-P75 peers) | R$ X | R$ X |
| EV/EBITDA NTM (P25-P75 peers) | R$ X | R$ X |
| P/L NTM (P25-P75 peers) | R$ X | R$ X |
| Transaction Comps | R$ X | R$ X |
| DCF (sensibilidades) | R$ X | R$ X |
| Range de Oferta Proposto | **R$ X** | **R$ X** |

O football field permite visualizar onde o range de preco do IPO se encaixa vis-a-vis as diferentes metodologias.

---

## Aba 7: Analise de Dilucao

| Cenario | Volume Primario | Acoes Novas | Dilucao | Preco | Equity Value Post-money |
|---------|----------------|-------------|---------|-------|------------------------|
| Minimo (R$ 14/acao) | R$ 700 mi | 50 mi | 11,1% | R$ 14 | R$ X bi |
| Base (R$ 16/acao) | R$ 800 mi | 50 mi | 11,1% | R$ 16 | R$ X bi |
| Maximo (R$ 18/acao) | R$ 900 mi | 50 mi | 11,1% | R$ 18 | R$ X bi |

---

## Aba 8: Cronograma da Oferta

| Etapa | Data Prevista |
|-------|--------------|
| Aprovacao do Conselho | [data] |
| Protocolo na CVM/ANBIMA | [data] |
| Registro concedido | [data] |
| Inicio do Roadshow | [data] |
| Precificacao (Pricing Night) | [data] |
| Liquidacao | [data + 2] |
| Debut na B3 | [data + 3] |
| Fim do Greenshoe | [data + 30 dias] |
| Fim do Lock-up Vendedores | [data + 90/180 dias] |
