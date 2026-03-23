# Modelo de Referencia — Estrutura de Planilha de Debenture (DCM)

Este documento descreve a logica e estrutura das abas de um modelo financeiro padrao de precificacao e analise de debentures.

---

## Aba 1: Capa / Term Sheet

Campos padrao de um term sheet de debenture:

| Campo | Exemplo |
|-------|---------|
| Emissor | Empresa XYZ S.A. |
| CNPJ | 00.000.000/0001-00 |
| Tipo | 3a Emissao de Debentures Simples, Nao Conversiveis |
| Especie | Quirografaria |
| Volume Total | R$ 500.000.000,00 |
| Valor Nominal Unitario (VNe) | R$ 1.000,00 |
| Numero de Debentures | 500.000 |
| Serie | Serie Unica |
| Data de Emissao | [data] |
| Data de Vencimento | [data + 5 anos] |
| Prazo | 60 meses |
| Remuneracao | CDI + 1,75% a.a. |
| Pagamento de Juros | Semestral |
| Amortizacao | Bullet (100% no vencimento) |
| Rating | brAA+ (Fitch Ratings) |
| Coordenador Lider | Banco BTG Pactual S.A. |
| Agente Fiduciario | [Nome] |
| Custodiante | B3 S.A. |
| Regime de Oferta | Distribuicao Publica (RCVM 160) |
| Destinacao dos Recursos | Reperfilamento de divida (70%) + Capex (30%) |

---

## Aba 2: Fluxo de Caixa da Debenture

Colunas:
- Data do Evento
- Dias Corridos (DC)
- Dias Uteis (DU)
- Fator DI acumulado no periodo
- Juros Brutos (VNe x fator_juros)
- IR (aliquota regressiva x juros brutos)
- Juros Liquidos
- Amortizacao do Principal
- Fluxo Total Bruto
- Fluxo Total Liquido

Formulas chave:
- Fator DI diario = (1 + CDI_anual)^(1/252)
- Fator acumulado = produto dos fatores diarios no periodo
- Juros = VNe x [(fator_DI x (1 + spread)^(DU/252)) - 1]

---

## Aba 3: Precificacao (MTM — Mark-to-Market)

Objetivo: calcular o PU (preco unitario) a mercado dado uma taxa de desconto.

Campos de entrada:
- Data de Calculo
- Taxa de Desconto (CDI + X% a.a.) = taxa de mercado atual
- VNe Atualizado = VNe x fator_DI_acumulado_ate_hoje

Calculo do PU:
  PU = Sum[Fluxo_i / (1 + taxa_desconto)^(DU_i / 252)]

Saidas:
- PU (valor de mercado)
- Duracao Modificada
- DV01
- PU / VNe Atualizado (para identificar debentures acima ou abaixo do par)

---

## Aba 4: Analise de Credito / Covenants

Campos monitorados trimestralmente:

| Covenant | Formula | Limite | Status |
|----------|---------|--------|--------|
| DL / EBITDA LTM | (Divida Bruta - Caixa) / EBITDA 12m | <= 3,5x | OK / BREACH |
| EBITDA / Desp. Fin. | EBITDA LTM / Despesa Financeira Liquida LTM | >= 2,0x | OK / BREACH |
| DL / PL | Divida Liquida / Patrimonio Liquido | <= 1,5x | OK / BREACH |

Fonte dos dados: DFs trimestrais do emissor (ITR/IAN na CVM).

Alerta de breach: se qualquer covenant romper, o modelo deve sinalizar para analise de vencimento antecipado ou waiver.

---

## Aba 5: Cenarios de Stress

Variaveis de sensibilidade:
- CDI base: +100bps, +200bps, -100bps
- EBITDA: -20%, -30%
- Receita: -10%, -20%
- Capex adicional: +50%

Impactos calculados:
- DL/EBITDA em cada cenario
- DSCR (Debt Service Coverage Ratio)
- Headroom para covenant breach (distancia percentual ate o limite)

---

## Aba 6: Comparativo de Debentures do Mesmo Emissor

Para emissores frequentes:

| Emissao | Vencimento | Indexador | Spread | Rating | PU/VNe | YTM |
|---------|-----------|-----------|--------|--------|--------|-----|
| 1a Emissao | [data] | CDI+ | 1,20% | brAAA | 101,5% | CDI+1,10% |
| 2a Emissao | [data] | IPCA+ | 6,50% | brAAA | 98,2% | IPCA+6,85% |
| 3a Emissao | [data] | CDI+ | 1,75% | brAA+ | 99,5% | CDI+1,80% |

---

## Aba 7: Curva de Credito Setorial

Comparativo de spreads de mercado para o setor do emissor:

| Empresa | Rating | Prazo | Indexador | Spread Atual |
|---------|--------|-------|-----------|-------------|
| Emissor A | brAAA | 5 anos | CDI+ | 1,10% |
| Emissor B | brAA+ | 5 anos | CDI+ | 1,65% |
| Emissor C | brAA | 5 anos | CDI+ | 2,10% |
| Emissor D | brA+ | 5 anos | CDI+ | 3,20% |

Permite ao DCM banker posicionar o spread da nova emissao dentro da curva de credito do setor.
