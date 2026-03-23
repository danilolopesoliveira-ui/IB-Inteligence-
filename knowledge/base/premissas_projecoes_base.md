# Repositorio de Premissas e Projecoes Base
# VERSAO: 1.0 | DATA DE REFERENCIA: Marco / 2026
# STATUS: VIGENTE — Todos os projetos devem utilizar esta versao

> **INSTRUCAO AOS AGENTES:** Este e o documento de premissas canonico do sistema.
> Antes de elaborar qualquer projecao financeira, modelo ou apresentacao, consulte este repositorio.
> Em caso de conflito com dados de outra fonte, esta versao prevalece.
> Versao mais recente disponivel em: `knowledge/base/premissas_projecoes_base.md`

---

## CONTROLE DE VERSOES

| Versao | Data | Alteracoes Principais | Responsavel |
|---|---|---|---|
| 1.0 | Mar/2026 | Versao inicial — premissas macro, setoriais e de credito | IB Agents Capital |

---

## MODULO 1 — MACROECONOMIA BRASIL

### 1.1 Taxas de Referencia (Fonte: BACEN Focus — ultima divulgacao disponivel)

| Indicador | 2025 Realizado | 2026 Projetado | 2027 Projetado | 2028 Projetado |
|---|---|---|---|---|
| SELIC (% a.a.) | 13,75% | 14,75% | 13,00% | 11,50% |
| CDI (% a.a.) | 13,65% | 14,65% | 12,90% | 11,40% |
| IPCA (% a.a.) | 5,83% | 5,50% | 4,20% | 3,80% |
| IGP-M (% a.a.) | 6,12% | 5,80% | 4,50% | 4,00% |
| TJLP (% a.a.) | 7,00% | 7,00% | 6,50% | 6,00% |
| TR (% a.a.) | 0,95% | 0,80% | 0,50% | 0,30% |

**Regra de uso:** Para projecoes em termos reais, deflacionar pelo IPCA. Para nominalizar, aplicar IPCA projetado do ano correspondente.

### 1.2 Cambio BRL/USD (Fonte: BACEN Focus)

| Periodo | Taxa BRL/USD | Observacao |
|---|---|---|
| Dez/2025 (realizado) | R$ 5,82 | Fechamento ano |
| Mar/2026 (spot) | R$ 5,78 | Data de referencia deste documento |
| Dez/2026 (projetado) | R$ 5,90 | Mediana Focus |
| Dez/2027 (projetado) | R$ 5,70 | Mediana Focus |
| Dez/2028 (projetado) | R$ 5,60 | Mediana Focus |

**Regra de uso:** Usar spot para conversoes de data-base. Usar projecao anual para modelagem de receitas/custos em USD.

### 1.3 PIB Brasil (Fonte: IBGE / BACEN Focus)

| Periodo | PIB Real (%) | PIB Nominal (R$ Bi) | Observacao |
|---|---|---|---|
| 2024 | 3,4% | R$ 11.682 Bi | IBGE divulgacao fev/2026 |
| 2025E | 2,1% | R$ 12.384 Bi | Estimativa Focus |
| 2026P | 1,8% | R$ 13.062 Bi | Projecao Focus |
| 2027P | 2,0% | R$ 13.811 Bi | Projecao Focus |
| 2028P | 2,2% | R$ 14.615 Bi | Projecao Focus |

### 1.4 Curva de Juros NTN-B (Tesouro Nacional — Mar/2026)

| Vencimento | Taxa Real (IPCA+) | Prazo |
|---|---|---|
| NTN-B 2027 | IPCA + 6,85% | ~1 ano |
| NTN-B 2029 | IPCA + 7,10% | ~3 anos |
| NTN-B 2032 | IPCA + 7,35% | ~6 anos |
| NTN-B 2035 | IPCA + 7,48% | ~9 anos |
| NTN-B 2040 | IPCA + 7,55% | ~14 anos |
| NTN-B 2050 | IPCA + 7,62% | ~24 anos |
| NTN-B 2060 | IPCA + 7,65% | ~34 anos |

**Uso:** Base para calculo de WACC, pricing de CRA/CRI e taxa livre de risco em DCF.

### 1.5 DI Futuro (B3 — Mar/2026)

| Vencimento | Taxa DI Futuro (% a.a.) |
|---|---|
| Jan/2027 | 14,82% |
| Jan/2028 | 13,45% |
| Jan/2029 | 12,90% |
| Jan/2030 | 12,55% |
| Jan/2031 | 12,30% |

---

## MODULO 2 — MULTIPLOS DE MERCADO POR SETOR

### 2.1 Multiplos Brasil — Empresas Listadas B3 (Fonte: Damodaran Jan/2026 + B3 Mar/2026)

| Setor | EV/EBITDA LTM | EV/EBITDA NTM | P/L NTM | EV/Receita | Beta Alavancado | WACC Nominal |
|---|---|---|---|---|---|---|
| Agronegocio / Graos | 7,2x | 6,8x | 11,5x | 0,8x | 0,85 | 13,8% |
| Proteinas Animais (JBS/Marfrig/Minerva) | 5,8x | 5,4x | 9,2x | 0,4x | 1,15 | 15,2% |
| Varejo Alimentar | 8,5x | 7,8x | 14,2x | 0,4x | 0,92 | 14,1% |
| Varejo Nao Alimentar | 10,2x | 9,1x | 16,8x | 0,7x | 1,18 | 15,6% |
| Energia Eletrica (Geracao) | 9,8x | 9,2x | 15,4x | 4,2x | 0,65 | 12,8% |
| Energia Eletrica (Distribuicao) | 7,5x | 7,0x | 11,8x | 1,2x | 0,72 | 13,2% |
| Infraestrutura / Concessoes | 11,2x | 10,5x | 18,2x | 3,8x | 0,68 | 12,9% |
| Saude / Hospitais | 12,5x | 11,2x | 22,4x | 1,8x | 0,88 | 14,0% |
| Saude / Planos | 9,8x | 8,9x | 16,5x | 0,9x | 0,82 | 13,7% |
| Educacao | 10,8x | 9,5x | 18,8x | 1,4x | 1,05 | 14,8% |
| Tecnologia / SaaS | 18,5x | 15,2x | 32,8x | 4,5x | 1,32 | 16,2% |
| E-commerce | 22,4x | 17,8x | N/A | 1,2x | 1,45 | 17,0% |
| Financeiro / Bancos | 8,2x | 7,5x | 8,8x | N/A | 1,22 | 15,8% |
| Financeiro / Seguros | 11,5x | 10,2x | 14,5x | N/A | 0,95 | 14,4% |
| Real Estate / Incorporacao | 8,8x | 7,9x | 12,2x | 0,9x | 1,05 | 14,8% |
| Real Estate / FII | N/A | N/A | 14,8x | N/A | 0,58 | 12,4% |
| Logistica / Transporte | 8,2x | 7,6x | 13,5x | 0,7x | 0,98 | 14,5% |
| Mineracao | 6,8x | 6,2x | 9,8x | 2,2x | 1,28 | 16,0% |
| Petroleo e Gas | 5,2x | 4,8x | 8,5x | 1,1x | 1,35 | 16,5% |
| Saneamento | 9,5x | 8,8x | 16,2x | 3,2x | 0,62 | 12,6% |
| Telecomunicacoes | 6,8x | 6,4x | 12,5x | 1,4x | 0,75 | 13,4% |

**Regra de uso:**
- Aplicar mediana do setor como multiplo base
- Ajustar +/- 10-15% por tamanho (small cap desconto, large cap premio)
- Ajustar por liquidez: empresas nao listadas: desconto de 20-30% vs comparaveis listados
- Fontes: Damodaran (pages.stern.nyu.edu/~adamodar/), B3 relatorio de multiplos, Research BTG/XP/Itau

### 2.2 Multiplos de Transacoes Precedentes Brasil (M&A — 2023-2025)

| Setor | EV/EBITDA Medio | EV/EBITDA Mediana | N Transacoes | Periodo |
|---|---|---|---|---|
| Proteinas Animais | 7,2x | 6,8x | 8 | 2023-2025 |
| Agronegocio (plataformas) | 9,5x | 8,8x | 12 | 2023-2025 |
| Saude (hospitais) | 13,8x | 12,5x | 15 | 2023-2025 |
| Educacao (plataformas) | 12,2x | 10,8x | 9 | 2023-2025 |
| Tecnologia (SaaS) | 21,5x | 18,2x | 22 | 2023-2025 |
| Logistica | 9,2x | 8,5x | 7 | 2023-2025 |
| Varejo (regional) | 8,5x | 7,8x | 11 | 2023-2025 |
| Energia (PCH/solar) | 12,8x | 11,5x | 18 | 2023-2025 |
| Real Estate (loteamento) | 9,5x | 8,2x | 6 | 2023-2025 |

**Fonte:** ANBIMA Fusoes e Aquisicoes | KPMG M&A Survey 2025 | PwC Deals Brazil

---

## MODULO 3 — PARAMETROS DE CREDITO

### 3.1 Spreads por Rating — Mercado Primario Brasil (ANBIMA — Mar/2026)

| Rating | Spread CDI | Spread IPCA+ | Spread IGPM+ | Prazo Tipico |
|---|---|---|---|---|
| AAA | CDI + 0,60% | IPCA + 5,80% | IGPM + 5,20% | 3-7 anos |
| AA+ | CDI + 0,85% | IPCA + 6,10% | IGPM + 5,50% | 3-7 anos |
| AA | CDI + 1,10% | IPCA + 6,35% | IGPM + 5,75% | 3-7 anos |
| AA- | CDI + 1,35% | IPCA + 6,60% | IGPM + 6,00% | 3-5 anos |
| A+ | CDI + 1,65% | IPCA + 6,90% | IGPM + 6,30% | 3-5 anos |
| A | CDI + 2,00% | IPCA + 7,25% | IGPM + 6,65% | 2-5 anos |
| A- | CDI + 2,40% | IPCA + 7,65% | IGPM + 7,05% | 2-4 anos |
| BBB+ | CDI + 3,00% | IPCA + 8,25% | IGPM + 7,65% | 2-4 anos |
| BBB | CDI + 3,75% | IPCA + 9,00% | IGPM + 8,40% | 2-3 anos |
| BBB- | CDI + 4,75% | IPCA + 10,00% | IGPM + 9,40% | 1-3 anos |
| BB+ | CDI + 6,00% | IPCA + 11,25% | — | 1-3 anos |
| Sem rating | CDI + 7,00%+ | IPCA + 12,00%+ | — | 1-2 anos |

**Fonte:** ANBIMA mercado secundario de debentures | Emissoes primarias Jan-Mar/2026

### 3.2 Covenants Padrao de Mercado por Instrumento

| Instrumento | Divida Liq./EBITDA max | EBITDA/Juros min | DSCR min | FCO/EBITDA min |
|---|---|---|---|---|
| Debenture Infra (Lei 12.431) | 4,5x | 1,8x | 1,3x | 55% |
| Debenture Comum (investment grade) | 3,5x | 2,0x | 1,5x | 60% |
| Debenture Comum (high yield) | 5,0x | 1,5x | 1,2x | 50% |
| CRA / CRI (investment grade) | 3,5x | 2,0x | 1,5x | 60% |
| CRA / CRI (sem rating) | 4,0x | 1,8x | 1,3x | 55% |
| FIDC Senior | 3,0x | 2,5x | 1,8x | 65% |
| Bond Internacional (investment grade) | 4,0x | 2,0x | 1,4x | 55% |

### 3.3 Haircuts Padrao de Garantias

| Tipo de Garantia | Haircut | Advance Rate | Observacoes |
|---|---|---|---|
| Imovel Urbano — comercial | 40% | 60% | Sobre valor de laudo independente |
| Imovel Rural — terra nua | 35% | 65% | Sobre valor INCRA/laudo |
| Imovel Rural — com benfeitorias | 30% | 70% | Inclui instalacoes agroindustriais |
| Recebiveis — diversificados | 20% | 80% | Concentracao max 10% por devedor |
| Recebiveis — concentrados | 25% | 75% | Concentracao 10-20% por devedor |
| Recebiveis — muito concentrados | 35% | 65% | Concentracao > 20% por devedor |
| Estoque — produtos acabados | 50% | 50% | Bens de rapida comercializacao |
| Estoque — materias-primas | 55% | 45% | Commodities com mercado ativo |
| Equipamentos industriais | 45% | 55% | Sobre valor de laudo tecnico |
| Participacoes societarias | 40% | 60% | Sobre valor patrimonial auditado |
| Producao agricola (CPR) | 30% | 70% | Sobre valor CONAB na data de contrato |
| Aval pessoal | — | — | Complementar, nao standalone |

### 3.4 Parametros de Inadimplencia por Setor (Historico BACEN/ANBIMA)

| Setor | Inadimplencia Media 90d | Perda Esperada | Perda em Estresse |
|---|---|---|---|
| Grandes empresas (investment grade) | 0,3% | 0,8% | 3,5% |
| Grandes empresas (speculative) | 1,2% | 3,0% | 9,5% |
| Agronegocio (recebiveis) | 0,5% | 1,2% | 4,0% |
| Real Estate (CRI) | 0,8% | 2,0% | 6,5% |
| Consumo (FIDC varejo) | 4,5% | 8,0% | 18,0% |
| PME geral | 3,8% | 7,5% | 22,0% |

---

## MODULO 4 — PREMISSAS SETORIAIS

### 4.1 Agronegocio e Proteinas Animais

| Premissa | Valor | Fonte | Validade |
|---|---|---|---|
| CAGR receita setor proteinas 5a | 8,3% a.a. | ABPA 2025 | 2026-2030 |
| CAGR exportacoes carne frango | 6,5% a.a. | SECEX/MDIC | 2026-2030 |
| Preco medio frango inteiro (frigorificado) | R$ 8,90/kg | CEPEA Mar/2026 | Revisao trimestral |
| Preco medio cortes especiais | R$ 18,50/kg | CEPEA Mar/2026 | Revisao trimestral |
| Custo medio racao (milho+soja) | R$ 1,42/kg | CEPEA/CONAB Mar/2026 | Revisao mensal |
| Milho (tonelada) | R$ 68,50/sc 60kg | CEPEA Mar/2026 | Revisao mensal |
| Soja (tonelada) | R$ 135,00/sc 60kg | CEPEA Mar/2026 | Revisao mensal |
| Abate nacional de frangos | 14,2M ton/ano | ABPA 2025 | Anual |
| Exportacoes de frango Brasil | US$ 10,2Bi | SECEX 2025 | Anual |
| Crescimento consumo domestico | 2,8% a.a. | IBGE POF 2025 | 2026-2030 |
| CAGR area plantada graos | 2,1% a.a. | CONAB 2025 | 2026-2030 |
| Produtividade soja (sc/ha) | 59,8 sc/ha | CONAB Safra 25/26 | Anual |

### 4.2 Energia Eletrica e Infraestrutura

| Premissa | Valor | Fonte | Validade |
|---|---|---|---|
| IPCA energia (tarifa media) | +8,2% em 2025 | ANEEL | Revisao anual |
| Tarifa media industrial (media Brasil) | R$ 0,58/kWh | ANEEL Mar/2026 | Revisao trimestral |
| Tarifa media residencial | R$ 0,82/kWh | ANEEL Mar/2026 | Revisao trimestral |
| Capacidade instalada nacional | 220 GW | ANEEL Jan/2026 | Anual |
| PLD medio NE (2025) | R$ 82,50/MWh | CCEE 2025 | Revisao mensal |
| PLD medio SE/CO (2025) | R$ 96,80/MWh | CCEE 2025 | Revisao mensal |
| CAGR demanda energia 5a | 3,2% a.a. | PDE 2032/EPE | 2026-2031 |
| Participacao renovaveis na matriz | 88,5% | ANEEL Jan/2026 | Anual |

### 4.3 Real Estate e Construcao

| Premissa | Valor | Fonte | Validade |
|---|---|---|---|
| INCC (indice de custo construcao) | 6,8% a.a. | FGV 2025 | Revisao anual |
| CUB medio Brasil (m2) | R$ 2.450/m2 | SINDUSCON Mar/2026 | Revisao mensal |
| Lancamentos residenciais (unidades) | 142.000 | CBIC/ABRAINC 2025 | Anual |
| VGV total Brasil | R$ 122Bi | ABRAINC 2025 | Anual |
| CAGR lancamentos 5a | 4,5% a.a. | CBIC | 2026-2030 |
| Taxa de vacancia escritorios SP | 22,5% | CBRE Mar/2026 | Trimestral |
| Cap rate FII logistica | 8,2% a.a. | CBRE/Cushman Mar/2026 | Trimestral |
| Cap rate FII escritorio AAA SP | 9,5% a.a. | CBRE Mar/2026 | Trimestral |

### 4.4 Saude

| Premissa | Valor | Fonte | Validade |
|---|---|---|---|
| CAGR receita hospitalar 5a | 9,8% a.a. | ANS/Anahp 2025 | 2026-2030 |
| Sinistralidade media planos | 88,2% | ANS 2025 | Revisao anual |
| Ticket medio plano individual | R$ 892/mes | ANS Mar/2026 | Revisao trimestral |
| PMOC (prazo medio de recebimento) | 42 dias | Anahp benchmark | Revisao anual |
| Populacao com plano de saude | 51,2M | ANS Dez/2025 | Anual |
| CAGR populacao coberta 5a | 2,8% a.a. | ANS | 2026-2030 |

### 4.5 Varejo

| Premissa | Valor | Fonte | Validade |
|---|---|---|---|
| CAGR varejo ampliado 5a | 4,2% a.a. | IBGE PMC | 2026-2030 |
| SSS (same store sales) benchmark | 5,5% a.a. | ABRAS 2025 | Revisao anual |
| Custo de aluguel (% receita) benchmark | 8-12% | ABRASCE | Revisao anual |
| Ticket medio supermercado | R$ 148 | NielsenIQ Mar/2026 | Revisao trimestral |
| Penetracao e-commerce varejo | 18,2% | ABComm 2025 | Anual |
| CAGR e-commerce 5a | 12,5% a.a. | ABComm | 2026-2030 |

### 4.6 Tecnologia e SaaS

| Premissa | Valor | Fonte | Validade |
|---|---|---|---|
| CAGR mercado tech Brasil 5a | 14,2% a.a. | ABES 2025 | 2026-2030 |
| Benchmark CAC/LTV ratio | min 3x | SaaStr / ABES | Revisao anual |
| Churn anual aceitavel (SaaS B2B) | < 8% | Benchmarks SaaStr | Revisao anual |
| NRR (Net Revenue Retention) benchmark | > 110% | Benchmarks SaaStr | Revisao anual |
| Multiplo ARR (SaaS > R$50M ARR) | 8-12x | Transacoes 2024-25 | Revisao anual |

---

## MODULO 5 — PARAMETROS DE WACC

### 5.1 Componentes do WACC — Metodologia Padrao

```
WACC = Ke x [E/(D+E)] + Kd x (1-t) x [D/(D+E)]

Ke (Custo do Capital Proprio) = Rf + Beta x Premio de Risco de Mercado + Premio Brasil
Kd (Custo da Divida) = Taxa de captacao media ponderada da empresa

Parametros:
  Rf (Taxa livre de risco):  NTN-B do prazo mais proximo ao DCF (ver Modulo 1.4)
  Premio de Risco de Mercado Brasil:  6,5% (Damodaran Jan/2026 — Emerging Markets)
  Premio Pais (CDS Brasil 5a):  1,85% (Bloomberg Mar/2026)
  Beta: ver tabela 2.1 por setor (alavancado pela estrutura de capital alvo)
  Aliquota IR/CSLL: 34% (regime padrao) | 15% para empresas no Simples/lucro presumido
```

### 5.2 WACC de Referencia por Setor (Nominal BRL)

| Setor | WACC Minimo | WACC Base | WACC Maximo | Obs |
|---|---|---|---|---|
| Infraestrutura concessionada | 11,5% | 12,8% | 14,0% | Fluxo regulado |
| Energia renovavel (contrato) | 11,8% | 13,0% | 14,5% | PPA de longo prazo |
| Saneamento | 11,5% | 12,6% | 13,8% | Concessao regulada |
| Real Estate (FII) | 11,0% | 12,4% | 13,5% | Cap rate benchmark |
| Agronegocio | 12,5% | 13,8% | 15,5% | Risco commodity |
| Proteinas Animais | 13,5% | 15,2% | 17,0% | Risco sanitario |
| Saude | 12,8% | 14,0% | 15,5% | Risco regulatorio ANS |
| Varejo | 13,0% | 14,5% | 16,5% | Risco ciclico |
| Tecnologia | 14,5% | 16,2% | 19,0% | Risco de crescimento |
| Logistica | 13,0% | 14,5% | 16,0% | Risco operacional |

### 5.3 Taxa de Crescimento na Perpetuidade (g)

| Cenario | Taxa g | Base |
|---|---|---|
| Conservador | 3,0% a.a. | IPCA longo prazo target BACEN |
| Base | 3,5% a.a. | IPCA + crescimento real setor |
| Otimista | 4,0% a.a. | IPCA + crescimento acima da media |
| Maximo permitido | 4,5% a.a. | Nao utilizar acima sem justificativa formal |

**Regra:** g nunca pode ser maior que o crescimento nominal esperado de longo prazo da economia (GDP nominal projetado = ~6,5% a.a. para o Brasil no longo prazo). Usar no maximo 50% do PIB nominal projetado.

---

## MODULO 6 — PREMISSAS OPERACIONAIS PADRAO

### 6.1 Capital de Giro (Working Capital) — Benchmarks por Setor

| Setor | DSO (Recebiveis) | DIO (Estoque) | DPO (Fornecedores) | CCC (Ciclo Caixa) |
|---|---|---|---|---|
| Proteinas Animais | 28 dias | 18 dias | 35 dias | 11 dias |
| Varejo Alimentar | 12 dias | 22 dias | 45 dias | -11 dias |
| Varejo Nao Alimentar | 35 dias | 55 dias | 42 dias | 48 dias |
| Saude / Hospitais | 42 dias | 35 dias | 38 dias | 39 dias |
| Tecnologia SaaS | 35 dias | — | 30 dias | 5 dias |
| Logistica | 38 dias | 8 dias | 32 dias | 14 dias |
| Construcao / Incorporacao | 180 dias | 365 dias | 60 dias | 485 dias |
| Agronegocio (trading) | 45 dias | 90 dias | 60 dias | 75 dias |

### 6.2 CAPEX de Manutencao — Benchmarks

| Setor | Manutencao (% Receita) | Expansao (% Receita) | D&A (% Receita) |
|---|---|---|---|
| Proteinas Animais | 3,5-4,5% | Variavel | 3,0-4,0% |
| Energia Eletrica | 4,0-6,0% | Variavel | 5,0-7,0% |
| Logistica / Transporte | 6,0-9,0% | Variavel | 7,0-10,0% |
| Saude (hospitais) | 5,0-7,0% | Variavel | 5,0-6,5% |
| Varejo | 2,5-4,0% | Variavel | 2,5-3,5% |
| Tecnologia | 1,5-3,0% | Variavel | 2,0-4,0% |
| Saneamento | 8,0-12,0% | Variavel | 6,0-9,0% |

### 6.3 Margens Operacionais — Benchmarks por Setor

| Setor | Margem Bruta | Margem EBITDA | Margem EBIT | Margem Liquida |
|---|---|---|---|---|
| Proteinas Animais | 18-26% | 8-16% | 5-12% | 2-7% |
| Agronegocio (plataforma) | 25-38% | 14-22% | 10-18% | 5-12% |
| Saude (hospital) | 35-48% | 18-28% | 12-20% | 5-12% |
| Saude (plano) | 10-16% | 8-14% | 5-10% | 3-8% |
| Varejo Alimentar | 22-28% | 6-10% | 4-8% | 2-5% |
| Varejo Nao Alimentar | 45-65% | 12-22% | 8-16% | 4-10% |
| Tecnologia SaaS | 65-80% | 20-35% | 15-28% | 10-20% |
| Logistica | 28-38% | 12-20% | 8-15% | 3-8% |
| Energia (geracao) | 55-70% | 48-62% | 30-45% | 18-32% |

---

## MODULO 7 — CENARIOS MACRO PARA STRESS TEST

### 7.1 Cenarios Padrao de Stress

| Parametro | Bull | Base | Bear | Stressed |
|---|---|---|---|---|
| EBITDA (vs base) | +15% | 0% | -15% | -30% |
| Receita (vs base) | +12% | 0% | -10% | -20% |
| SELIC | -200bps | Base | +200bps | +400bps |
| IPCA | -150bps | Base | +200bps | +400bps |
| BRL/USD | R$ 5,40 | R$ 5,78 | R$ 6,20 | R$ 6,80 |
| Volume/demanda | +10% | 0% | -8% | -18% |
| Custo de racao/insumos | -5% | 0% | +12% | +25% |

### 7.2 Probabilidades de Cenario (Referencia)

| Cenario | Probabilidade Implicita | Uso |
|---|---|---|
| Bull | 15% | Upside case em valuation |
| Base | 60% | Caso central em todas as analises |
| Bear | 20% | Downside razoavel |
| Stressed | 5% | Tail risk / covenant breach analysis |

---

## MODULO 8 — REGRAS DE USO E ATUALIZACAO

### 8.1 Hierarquia de Fontes

1. **Este repositorio** (versao vigente) — fonte primaria para todos os projetos
2. **Dados fornecidos pelo cliente** (DFs auditadas, contratos, laudos) — sobrepoe este repositorio para dados especificos da empresa
3. **Dados de mercado em tempo real** (Bloomberg, BACEN, ANBIMA) — atualiza este repositorio na proxima versao
4. **Estimativas do agente** — somente quando nenhuma das fontes acima estiver disponivel, com indicacao explicita de "estimativa"

### 8.2 Protocolo de Atualizacao

- **Frequencia minima:** trimestral (marco, junho, setembro, dezembro)
- **Gatilhos de atualizacao imediata:** variacao de SELIC > 50bps, IPCA acumulado > 1% no mes, cambio > 5% em 30 dias
- **Responsavel:** MD Orchestrator valida atualizacoes antes de publicar nova versao
- **Notificacao:** ao publicar nova versao, todos os projetos ativos devem ser revisados nas premissas

### 8.3 Sinalizacao Obrigatoria nos Outputs

Todo material produzido deve incluir:
```
Premissas: Repositorio Base v1.0 (Mar/2026) | Dados especificos: [fonte da empresa]
Para dados atualizados: knowledge/base/premissas_projecoes_base.md
```

### 8.4 O que NAO esta neste repositorio

- Dados especificos da empresa (DRE, balanco, KPIs operacionais) — devem ser fornecidos pelo cliente
- Projecoes especificas de projeto — derivadas deste repositorio + dados do cliente
- Analise de credito especifica — usa este repositorio como calibracao

---

*Repositorio de Premissas Base | IB Agents Capital | Versao 1.0 | Marco/2026*
*Proxima revisao programada: Junho/2026*
