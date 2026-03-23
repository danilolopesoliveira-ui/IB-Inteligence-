# Pricing de Divida, Covenants e Analise de Credito — DCM Brasil

Fonte: ANBIMA (metodologia de precificacao), pratica de mercado

---

## 1. Formula de Pricing

  Taxa Debenture = Taxa Livre de Risco + Spread de Credito + Premios

- IPCA+: referencia NTN-B do prazo equivalente
- CDI+: referencia Swap DI x Pre

## 2. Spread por Rating (Orientativo — Mercado BR)

| Rating Nacional | Spread IPCA+ (bps) | Spread CDI+ (% a.a.) |
|----------------|-------------------|---------------------|
| brAAA | 80-150 | 0,50-1,20 |
| brAA | 150-250 | 1,20-2,00 |
| brA | 250-500 | 2,00-4,50 |
| brBBB | 500-700 | 4,50-6,00 |
| Abaixo grau invest. | 700+ | 6,00+ |

## 3. Determinantes do Spread

- Alavancagem (DL/EBITDA): cada 0,5x adicional = ~30-80 bps de spread
- Garantias reais: reduzem spread (maior recuperacao em default)
- Covenants robustos: reduzem spread
- Subordinacao: aumenta spread
- Iliquidez no secundario: premio de 20-50 bps
- Setor regulado (energia, saneamento): spread menor por fluxo previsivel

## 4. Metricas de Credito para Grau de Investimento

| Metrica | Threshold |
|---------|-----------|
| Divida Liq. / EBITDA | < 3,5x |
| EBITDA / Desp. Financeira | > 2,5x |
| DSCR (FCO / Servico Divida) | > 1,2x |
| Divida CP / Divida Total | < 30% |

## 5. Duration e Sensibilidade

  Duration Modificada = Duracao Macaulay / (1 + taxa)
  Delta_Preco (%) = -Duration_Mod x Delta_taxa
  DV01 = Preco x Duration_Mod / 10.000

DV01: variacao em R$ por 1 basis point de taxa. Usado para hedge via futuros de DI ou NTN-B.

## 6. Convencao DU252

  PU = VN x (fator_indice) x (1 + spread)^(DU/252)

Todos os titulos de renda fixa privada no Brasil usam base 252 dias uteis.

## 7. Covenants Tipicos

### Financeiros
- DL/EBITDA maximo (ex: 3,5x) — testado semestralmente
- EBITDA/Despesa Financeira minimo (ex: 2,0x)
- Restricao de distribuicao de dividendos acima de 25% se DL/EBITDA > X

### Nao Financeiros
- Cross-default: vencimento antecipado se default em outras dividas > R$ X
- Change of control: vencimento antecipado em mudanca de controle
- Alienacao de ativos relevantes: vedada sem consentimento acima de % do ativo total
- Manutencao de rating minimo (ex: grau de investimento)

### Periodo de Cura (Grace Period)
- Pagamento: 1-5 dias uteis
- Covenant financeiro: 30-60 dias para cure ou waiver

## 8. Bookbuilding DCM — Fluxo

1. Pre-marketing (1-2 semanas): one-on-ones com investidores-ancora (seguradoras, previdencia)
2. Lancamento do prospecto preliminar com range de taxa
3. Bookbuilding aberto (5-10 dias uteis): ordens com volume e taxa minima
4. Definicao do preco: emissora + coordenador analisam o livro
5. Liquidacao: D+2 ou D+3

Oversubscription = demanda excede oferta = spread comprimido.

## 9. Fees DCM

| Componente | Range |
|-----------|-------|
| Coordenacao | 0,15-0,40% |
| Distribuicao | 0,30-0,80% |
| Garantia firme (se aplicavel) | +0,10-0,30% |
| Total tipico | 0,50-1,50% |
