# Valuation para ECM — Metodologias Usadas em IPOs e Follow-ons

Fonte: pratica de mercado (Goldman Sachs, BTG, Morgan Stanley), CFA Institute, Damodaran

---

## 1. Abordagens de Valuation em ECM

Em um IPO ou follow-on, os bancos tipicamente usam 3 metodologias em paralelo e triangulam:

1. Trading Comps (Comparaveis de Mercado)
2. Transaction Comps (Comparaveis de Transacoes)
3. DCF (Fluxo de Caixa Descontado)

---

## 2. Trading Comps — Multiplos de Mercado

### Logica
Valorizar a empresa-alvo com base nos multiplos de negociacao de empresas publicas comparaveis (peers).

### Multiplos Mais Usados por Setor

| Setor | Multiplo Principal | Secundario |
|-------|-------------------|-----------|
| Varejo | EV/EBITDA; P/L | EV/Receita Liquida |
| Tecnologia (growth) | EV/Receita; EV/GMV | P/L futuro |
| Bancos/Financeiro | P/BV (Preco/Valor Patrimonial) | P/L; ROE |
| Utilities / Energia | EV/EBITDA; P/L | EV/RAB |
| Saude | EV/EBITDA | P/L; EV/Leitos |
| Real Estate | P/FFO; P/NAV | Dividend Yield |
| Commodities | EV/EBITDA; EV/t de capacidade | P/L |
| Agronegocio | EV/EBITDA; EV/ha | — |

### Calculo

  Valor da Empresa (EV) = Multiplo x Metrica
  Equity Value = EV - Divida Liquida + Caixa + Minoritarios

  Preco por Acao = Equity Value / Acoes Diluidas (fully diluted)

### Selecao dos Peers
- Mesmo setor e segmento de atuacao
- Porte similar (receita, EBITDA)
- Perfil de crescimento similar
- Geografias comparaveis
- Desconto de iliquidez: empresas menores ou com menos free float negociam com desconto de 10-20%

---

## 3. Transaction Comps — Multiplos de M&A

### Logica
Multiplos pagos em aquisicoes recentes de empresas comparaveis. Geralmente mais altos que trading comps pelo premio de controle.

### Premio de Controle
- Aquisicoes tipicamente pagam 20-40% acima do preco de mercado (control premium)
- Em IPOs, o preco de oferta costuma refletir desconto de IPO (10-20% abaixo do fair value) para garantir demanda e performance no debut

### Uso em ECM
- Serve como teto do range de preco
- Justifica a tese quando ha M&A recente no setor

---

## 4. DCF — Fluxo de Caixa Descontado

### Formula

  VPL (Firma) = Sum[FCF_t / (1+WACC)^t] + Valor Terminal / (1+WACC)^n

  FCF = EBITDA - Impostos sobre EBIT - CAPEX - Variacao de Capital de Giro

  Valor Terminal = FCF_n x (1+g) / (WACC - g)   [metodo Gordon Growth]

### WACC (Custo Medio Ponderado de Capital)

  WACC = Ke x E/(E+D) + Kd x (1-t) x D/(E+D)

- Ke = custo do equity (CAPM)
- Kd = custo da divida (taxa media da divida da empresa)
- t = aliquota de IR efetiva

### CAPM para Brasil

  Ke = Rf + Beta x (Rm - Rf) + Country Risk Premium

- Rf: taxa livre de risco (US 10Y Treasury + basis para BRL; ou NTNB longa)
- Beta: sensibilidade ao mercado (desalavancado do peer + re-alavancado para a empresa)
- Rm - Rf: premio de risco de mercado (historicamente 5-7% no Brasil)
- Country Risk Premium: CDS Brasil soberano ou EMBI+ Brasil

### Sensibilidades Tipicas Reportadas em Pitch Book
- WACC: +/- 1%
- Taxa de crescimento terminal (g): +/- 0,5%

---

## 5. Sum-of-the-Parts (SOTP)

Usado para conglomerados ou empresas com divisoes de negocios distintos:

  Valor Total = Valor Divisao A + Valor Divisao B + ... + Holdco Discount

- Cada divisao e valorada pelo multiplo do setor correspondente ou DCF proprio
- Holdco discount: 10-30% tipico pela complexidade e custo de administracao

---

## 6. Outros Multiplos Relevantes para ECM Brasil

| Multiplo | Formula | Uso |
|----------|---------|-----|
| EV/EBITDA | (Mkt Cap + Div. Liq.) / EBITDA | Universal |
| P/L (PER) | Preco por Acao / LPA | Financeiro, consumo |
| P/BV | Preco por Acao / VPA | Bancos, seguradoras |
| EV/Receita | EV / Receita Bruta ou Liquida | Empresas de alto crescimento (tech) |
| EV/EBIT | EV / EBIT | Empresas sem D&A relevante |
| P/FFO | Preco / Funds from Operations | FIIs, real estate |
| Dividend Yield | DPA / Preco | Utilities, acoes de renda |

---

## 7. Desconto de IPO e Underpricing

Fenomeno empirico documentado globalmente: acoes tendem a subir no dia do IPO (underpricing medio de 15-20% internacionalmente).

Razoes:
- Assimetria de informacao: emissores aceitam preco abaixo para garantir demanda
- Risco de distribuicao: coordenadores preferem oversubscription a deal quebrado
- Incentivo dos investidores de longo prazo: entrada abaixo do fair value gera retorno inicial

Para o banco:
- IPO com forte performance no debut = reputacao + facilidade para proximas operacoes
- IPO com queda no debut = dificuldade em futuras operacoes do mesmo setor

---

## 8. Dilucao em Ofertas Primarias

Se a empresa emite novas acoes no IPO:

  Dilucao = Novas Acoes / (Acoes Pre-IPO + Novas Acoes)

Exemplo:
- Pre-IPO: 100 milhoes de acoes
- IPO primario: 25 milhoes de novas acoes
- Post-IPO: 125 milhoes de acoes
- Dilucao: 20%

A lamina de oferta (RCVM 160) exige divulgacao do % de diluicao pos-oferta.

---

## 9. Metricas de Retorno para o Investidor de IPO

- **Retorno no primeiro dia (First Day Return)**: preco fechamento D1 / preco IPO - 1
- **Retorno relativo ao Ibovespa**: alpha gerado vs. benchmark
- **Retorno ate 1 ano**: medida padrao de performance de IPO
- **Calendarizacao de lockup**: impacto na oferta de acoes 90-180 dias pos-IPO
