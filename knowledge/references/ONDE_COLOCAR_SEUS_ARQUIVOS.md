# Guia de Arquivos de Treinamento — Onde Colocar Seus Documentos

Este arquivo indica onde voce deve adicionar seus proprios materiais de treinamento
para aprimorar os agentes DCM e ECM do IB-Agents.

---

## Estrutura de Pastas

knowledge/references/
|
|-- research_reports/
|   |-- dcm/          <- COLOQUE AQUI seus relatorios e materiais de DCM
|   |-- ecm/          <- COLOQUE AQUI seus relatorios e materiais de ECM
|
|-- financial_models/
|   |-- dcm/          <- COLOQUE AQUI seus modelos Excel de renda fixa
|   |-- ecm/          <- COLOQUE AQUI seus modelos Excel de IPO e valuation
|
|-- pitch_books/
|   |-- dcm/          <- COLOQUE AQUI seus pitch books de debentures
|   |-- ecm/          <- COLOQUE AQUI seus pitch books de IPO
|
|-- geral/            <- Para documentos que nao se encaixam em DCM ou ECM

---

## O Que Colocar em Cada Pasta

### research_reports/dcm/
- Relatorios de credito (S&P, Moodys, Fitch, Kroll)
- Research de renda fixa de corretoras (BTG, XP, Itau BBA)
- Boletins da ANBIMA sobre mercado de capitais
- Relatorios setoriais com analise de credito
- Memos de due diligence de debentures

### research_reports/ecm/
- Research de equity (initiation of coverage, updates)
- Relatorios de IPO pos-estreia
- Relatorios setoriais de equity research
- Analises de mercado ECM (bancos, ANBIMA)
- Memos de due diligence de acoes

### financial_models/dcm/
- Modelos Excel de pricing de debentures (fluxo, MTM, DV01)
- Modelos de CRI e CRA com fluxo de recebíveis
- Modelos de FIDC (analise de carteira, cotas)
- Planilhas de analise de credito / covenants
- Modelos de bond externo (bonds em USD)

### financial_models/ecm/
- Modelos de valuation (DCF, Trading Comps, Transaction Comps)
- Modelos de IPO (diluicao, football field, uso de recursos)
- Modelos de follow-on e block trade
- Planilhas de accretion/dilution para M&A de capital aberto
- LBO de empresa listada (take-private)

### pitch_books/dcm/
- Pitch books de emissoes de debentures
- Prospectos definitivos de debentures (publicos — CVM)
- CIMs de ofertas de renda fixa
- Tombstones e credenciais de DCM
- Apresentacoes de roadshow de bonds externos

### pitch_books/ecm/
- Prospectos definitivos de IPOs (publicos — CVM)
- Investor presentations de roadshow de IPO
- Pitch books de follow-on
- Teaser decks de abertura de capital
- Tombstones de ECM

---

## Formatos Suportados

- PDF (.pdf) — recomendado para prospectos e relatorios
- Excel (.xlsx, .xls) — para modelos financeiros
- Word (.docx) — para memos e relatorios em Word
- Texto (.txt, .md) — para documentos de texto simples

---

## Apos Adicionar os Arquivos

Execute no terminal (dentro da pasta ib-agents):

  py ingest_knowledge.py

Para verificar o que foi indexado:

  py ingest_knowledge.py --list

Para reprocessar do zero:

  py ingest_knowledge.py --reset

---

## Fontes Publicas Recomendadas para Buscar Documentos

### DCM
- Prospectos de debentures: sistemas.cvm.gov.br (Central de Sistemas — Ofertas Publicas)
- Boletins ANBIMA: data.anbima.com.br
- Relatorios de rating: moodyslocal.com.br, fitchratings.com/brasil

### ECM
- Prospectos de IPO/follow-on: sistemas.cvm.gov.br
- Formularios de Referencia: sistemas.cvm.gov.br (busca por empresa)
- Relatorios de equity: paginas de RI das empresas listadas

---

## Dicas de Qualidade

- Prefira documentos em portugues para contexto brasileiro
- Nao e necessario dados de clientes reais — estrutura e metodologia sao suficientes
- Quanto mais documentos, melhor a qualidade dos outputs
- Mínimo recomendado por area: 3 prospectos + 1 modelo Excel + 3 relatorios
