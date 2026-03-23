"""
Crew orchestration — defines agents, tasks, and execution flow.

Pipeline order:
  1. MD Orchestrator    — coordination + RAG memory
  2. Accountant         — review, organize and validate incoming documents
  3. Research Analyst   — parse structured data from validated docs
  4. Financial Modeler  — consolidate + build models
  5. DCM Specialist     — (conditional, parallel) bond pricing
     ECM Specialist     — (conditional, parallel) IPO valuation
  6. Quant Analyst      — (parallel) comps and charts
     Risk/Compliance    — (parallel) red flags and covenants
  7. Deck Builder       — generate outputs
"""

from __future__ import annotations

import json
import os
from typing import Any

from crewai import Crew, Task
from loguru import logger

from agents.orchestrator import build_orchestrator_agent
from agents.research_analyst import build_research_analyst_agent
from agents.accountant import build_accountant_agent
from agents.financial_modeler import build_financial_modeler_agent
from agents.dcm_specialist import build_dcm_specialist_agent
from agents.ecm_specialist import build_ecm_specialist_agent
from agents.quant_analyst import build_quant_analyst_agent
from agents.risk_compliance import build_risk_compliance_agent
from agents.deck_builder import build_deck_builder_agent

# Deal types that trigger each specialist
DCM_DEAL_TYPES = {"Debentures", "CRI", "CRA", "CCB", "Loan_Offshore", "Bilateral", "Debt_Advisory"}
ECM_DEAL_TYPES = {"IPO", "Follow-on", "Block_Trade", "IPO_Readiness"}


class IBAnalysisCrew:
    def __init__(
        self,
        company_name: str,
        deal_type: str = "M&A",
        sector: str = "industria",
        input_data: dict | None = None,
        mode: str = "full_analysis",
    ):
        self.company_name = company_name
        self.deal_type = deal_type
        self.sector = sector
        self.input_data = input_data or {}
        self.mode = mode
        self.is_dcm = deal_type in DCM_DEAL_TYPES
        self.is_ecm = deal_type in ECM_DEAL_TYPES

        # Core agents (always present)
        self.orchestrator = build_orchestrator_agent()
        self.research_analyst = build_research_analyst_agent()
        self.accountant = build_accountant_agent()
        self.financial_modeler = build_financial_modeler_agent()
        self.quant_analyst = build_quant_analyst_agent()
        self.risk_officer = build_risk_compliance_agent()
        self.deck_builder = build_deck_builder_agent()

        # Specialist agents (conditional)
        self.dcm_specialist = build_dcm_specialist_agent() if self.is_dcm else None
        self.ecm_specialist = build_ecm_specialist_agent() if self.is_ecm else None

    def run(self) -> dict[str, Any]:
        tasks = self._build_tasks()
        agents = [
            self.orchestrator, self.accountant, self.research_analyst,
            self.financial_modeler, self.quant_analyst, self.risk_officer,
            self.deck_builder,
        ]
        if self.dcm_specialist:
            agents.insert(4, self.dcm_specialist)
        if self.ecm_specialist:
            agents.insert(4 + (1 if self.dcm_specialist else 0), self.ecm_specialist)

        crew = Crew(agents=agents, tasks=tasks, verbose=True, memory=True)
        result = crew.kickoff()
        logger.info(f"Crew finalizada. Resultado: {str(result)[:200]}...")
        return {"status": "completed", "result": str(result)}

    def _build_tasks(self) -> list[Task]:
        is_demo = self.input_data.get("demo", False)
        file_path = self.input_data.get("file_path", "")
        demo_data_json = json.dumps(self.input_data, ensure_ascii=False) if is_demo else ""

        # ---- TASK 1: Accounting Review & Organization ----
        if is_demo:
            task_accounting = Task(
                description=(
                    f"Revise e organize os dados financeiros recebidos de '{self.company_name}' "
                    f"(modo demo):\n\n{demo_data_json}\n\n"
                    "1. Verifique completude: BP, DRE e DFC presentes para todos os periodos\n"
                    "2. Identifique inconsistencias contabeis obvias (BP desbalanceado, sinais invertidos)\n"
                    "3. Classifique a qualidade dos dados: alta/media/baixa\n"
                    "4. Emita parecer preliminar sobre ajustes que serao necessarios (IFRS 16, EBITDA, etc.)\n"
                    "5. Organize as informacoes de forma estruturada para o Research Analyst fazer o parsing."
                ),
                expected_output="JSON com: data_quality_assessment, preliminary_issues, organized_data, accounting_notes.",
                agent=self.accountant,
            )
        else:
            task_accounting = Task(
                description=(
                    f"Revise e organize os documentos financeiros recebidos de '{self.company_name}'.\n"
                    f"Arquivo: {file_path}\n\n"
                    "1. Faca uma leitura preliminar do arquivo para entender a estrutura\n"
                    "2. Identifique quais demonstracoes estao presentes (BP, DRE, DFC, DVA, DMPL)\n"
                    "3. Verifique periodos cobertos e consistencia entre demonstracoes\n"
                    "4. Sinalize problemas de qualidade: dados faltantes, formatos inconsistentes\n"
                    "5. Classifique o nivel de auditoria: auditado, revisado, gerencial\n"
                    "6. Emita orientacoes para o Research Analyst sobre como parsear o arquivo\n"
                    "7. Liste ajustes contabeis que serao necessarios apos o parsing (IFRS 16, normalizacao, etc.)"
                ),
                expected_output="JSON com: data_quality_assessment, documents_found, periods, preliminary_adjustments_needed, parsing_instructions.",
                agent=self.accountant,
            )

        # ---- TASK 2: Data Ingestion (guided by Accountant) ----
        if is_demo:
            task_research = Task(
                description=(
                    f"Usando as orientacoes do Contador, estruture os dados de '{self.company_name}' "
                    "no formato padrao: entities_data (BP, DRE, DFC por entidade), ownership, years.\n"
                    "Aplique as correcoes preliminares indicadas pelo Contador durante o parsing."
                ),
                expected_output="JSON com: entities_data, ownership, years, parsing_notes.",
                agent=self.research_analyst,
                context=[task_accounting],
            )
        else:
            task_research = Task(
                description=(
                    f"Faca o parsing do arquivo de '{self.company_name}' seguindo as instrucoes do Contador.\n"
                    f"Arquivo: {file_path}\n\n"
                    "Use excel_parser e/ou pdf_parser. Siga as orientacoes do Contador sobre:\n"
                    "- Quais abas/paginas sao relevantes\n"
                    "- Periodos a extrair\n"
                    "- Correcoes de formato a aplicar durante o parsing\n"
                    "Mapeie para campos canonicos. Documente premissas."
                ),
                expected_output="JSON com: entities_data, ownership, years, parsing_notes.",
                agent=self.research_analyst,
                context=[task_accounting],
            )

        # ---- TASK 3: Accounting Adjustments (post-parsing) ----
        task_adjustments = Task(
            description=(
                f"Agora com os dados parseados, aplique os ajustes contabeis a '{self.company_name}':\n"
                "1. IFRS 16 (leases)\n2. Normalizacao EBITDA\n"
                "3. Provisoes (PDD, contingencias)\n4. Depreciacao\n"
                "5. Reconhecimento de receita\n6. Validacao BP balanceado\n"
                "Emita memorando de ajustes com justificativa contabil."
            ),
            expected_output="JSON com: adjusted_entities, adjustment_memo, validation, summary.",
            agent=self.accountant,
            context=[task_research],
        )

        # ---- TASK 4: Financial Models ----
        task_modeling = Task(
            description=(
                f"Usando DFs ajustadas pelo Contador, execute:\n"
                "1. CONSOLIDACAO (eliminar intercompany)\n"
                "2. RECONSTITUICAO DFC (se necessario)\n"
                f"3. DCF (FCFF) — setor {self.sector}, WACC brasileiro\n"
                "4. ANALISE DE CREDITO (leverage, coverage, liquidez)\n"
                f"5. LBO (se deal_type={self.deal_type} == PE_Investment)"
            ),
            expected_output="JSON com: financials, dcf_output, credit_analysis, lbo_output.",
            agent=self.financial_modeler,
            context=[task_research, task_adjustments],
        )

        # ---- TASK 4 (conditional): DCM Specialist ----
        task_dcm = None
        if self.is_dcm and self.dcm_specialist:
            task_dcm = Task(
                description=(
                    f"Estruture e precifique a operacao de {self.deal_type} para '{self.company_name}':\n\n"
                    "1. PRICING: Calcule spread indicativo com base no rating, prazo, garantias "
                    "e benchmarks de mercado. Use a ferramenta bond_pricing.\n\n"
                    "2. COMPARAVEIS: Levante emissoes recentes comparaveis (mesmo rating, setor, prazo).\n\n"
                    "3. SENSIBILIDADE: Gere cenarios de spread (+/- 25bps, +/- 50bps) com impacto no PU.\n\n"
                    "4. COVENANTS: Proponha pacote de covenants de mercado (Net Leverage, Coverage, "
                    "Restricted Payments) com base na analise de credito do Financial Modeler.\n\n"
                    "5. ESTRUTURACAO: Recomende: serie unica vs multiplas series, amortizacao "
                    "(bullet vs linear), tipo de garantia otimo, e prazo sugerido.\n\n"
                    "6. GARANTIAS: Para cada garantia informada no input_data.guarantees, "
                    "use a ferramenta guarantee_analysis para calcular valor elegivel, "
                    "cobertura (LTV) e qualidade. Aceite arquivos PDF (matriculas, laudos) "
                    "e Excel/CSV (carteiras de recebiveis). "
                    "Consolide o pacote de garantias e calcule a cobertura total sobre a operacao.\n\n"
                    "7. NOTAS: Requisitos regulatorios especificos (CVM, BACEN, B3)."
                ),
                expected_output=(
                    "JSON com: pricing_analysis (spread, YTM, PU, sensibilidade), "
                    "comparable_issuances, proposed_covenants, structuring_recommendation, "
                    "guarantee_package (por garantia: valor, cobertura, qualidade; total_coverage_ratio), "
                    "regulatory_notes."
                ),
                agent=self.dcm_specialist,
                context=[task_adjustments, task_modeling],
            )

        # ---- TASK 4 (conditional): ECM Specialist ----
        task_ecm = None
        if self.is_ecm and self.ecm_specialist:
            task_ecm = Task(
                description=(
                    f"Conduza a analise de ECM para o {self.deal_type} de '{self.company_name}':\n\n"
                    "1. VALUATION: Defina price range por acao usando multiplos setoriais, "
                    "DCF e precedent transactions. Use a ferramenta ipo_valuation.\n\n"
                    "2. DILUICAO: Calcule impacto da oferta primaria no capital existente.\n\n"
                    "3. BOOKBUILDING: Defina estrategia — ancoragem institucional, "
                    "alocacao varejo, greenshoe, estabilizacao.\n\n"
                    "4. EQUITY STORY: Prepare os key selling points para investidores:\n"
                    "   - Tese de crescimento\n   - Vantagens competitivas\n"
                    "   - Uso de recursos (se primaria)\n   - Comparativo vs peers\n\n"
                    "5. LOCK-UP: Recomende estrutura de lock-up para controladores e management."
                ),
                expected_output=(
                    "JSON com: valuation_range (low/mid/high por metodo), "
                    "offering_structure (tamanho, diluicao, greenshoe), "
                    "bookbuilding_strategy, equity_story_points, lock_up_recommendation."
                ),
                agent=self.ecm_specialist,
                context=[task_adjustments, task_modeling],
            )

        # ---- TASK 5: Comps & Charts ----
        quant_context = [task_modeling]
        if task_dcm:
            quant_context.append(task_dcm)
        if task_ecm:
            quant_context.append(task_ecm)

        task_quant = Task(
            description=(
                f"Execute analise de comparaveis para {self.company_name} ({self.sector}):\n"
                "1. TRADING COMPS (B3) — mediana, Q1, Q3 de EV/EBITDA, P/E, EV/Receita\n"
                "2. IMPLIED EV pelo multiplo mediano\n"
                "3. FOOTBALL FIELD (DCF + comps"
                + (" + pricing DCM" if task_dcm else "")
                + (" + valuation ECM" if task_ecm else "")
                + ")\n4. GRAFICOS: receita/EBITDA, margens, football field, heatmap"
            ),
            expected_output="JSON com: comps_output, football_field, charts_paths.",
            agent=self.quant_analyst,
            context=quant_context,
        )

        # ---- TASK 6: Risk & Compliance ----
        risk_context = [task_accounting, task_modeling, task_quant]
        if task_dcm:
            risk_context.append(task_dcm)
        if task_ecm:
            risk_context.append(task_ecm)

        task_risk = Task(
            description=(
                f"Revisao completa de riscos para {self.company_name}:\n"
                "1. RED FLAGS (alavancagem, margens, FCF, concentracao, liquidez CP)\n"
                "2. PREMISSAS DCF (razoabilidade do WACC, crescimento, margem terminal)\n"
                "3. RISCO DOS AJUSTES CONTABEIS (IFRS 16, normalizacoes relevantes)\n"
                "4. COVENANTS: verifique Net Leverage <= 3.5x e EBITDA/Juros >= 2.5x "
                "usando a ferramenta covenant_checker.\n"
                "5. ANALISE DE CENARIOS — use os resultados do stress_test do credit_analysis:\n"
                "   a) Cenario BASE: metricas sem alteracao\n"
                "   b) Cenario BEAR (-15% EBITDA): identifique quais covenants entram em breach\n"
                "   c) Cenario STRESSED (-30% EBITDA): avalie viabilidade de servico da divida\n"
                "   d) Breach threshold: indique em qual percentual de queda de EBITDA "
                "cada covenant e violado\n"
                + ("6. RISCO DCM: spread vs benchmark de mercado, risco de demanda insuficiente, "
                   "risco de refinanciamento, adequacao dos covenants propostos\n" if task_dcm else "")
                + ("6. RISCO ECM: timing de mercado (janela IPO), risco de diluicao excessiva, "
                   "risco de lock-up insuficiente, sensibilidade do price range\n" if task_ecm else "")
                + "PARECER FINAL ESTRUTURADO:\n"
                "   - Recomendacao: GO / NO-GO / CONDITIONAL\n"
                "   - Condicoes (se CONDITIONAL): mitigantes exigidos\n"
                "   - Rating de risco da operacao: BAIXO / MEDIO / ALTO / MUITO ALTO\n"
                "   - Principais riscos residuais apos mitigacao"
            ),
            expected_output=(
                "JSON com: red_flags, covenant_results, accounting_risk, "
                "scenario_analysis (base/bear/stressed + breach_thresholds), "
                "investment_opinion (recommendation, risk_rating, conditions, residual_risks)."
            ),
            agent=self.risk_officer,
            context=risk_context,
        )

        # ---- TASK 7: Output Generation ----
        output_context = [task_research, task_adjustments, task_modeling, task_quant, task_risk]
        if task_dcm:
            output_context.append(task_dcm)
        if task_ecm:
            output_context.append(task_ecm)

        task_outputs = Task(
            description=(
                f"Gere todos os materiais para {self.company_name} ({self.deal_type}).\n"
                "Use knowledge_search para consultar modelos de referencia antes de cada output.\n\n"
                "OUTPUTS OBRIGATORIOS (toda operacao):\n"
                "1. PITCH BOOK (PPTX) — executive summary, tese de investimento, "
                "overview da empresa, demonstracoes financeiras, valuation, estrutura da operacao\n"
                "2. MODELO FINANCEIRO (XLSX) — DFs historicas ajustadas, projecoes, "
                "KPIs, DCF, analise de credito com cenarios base/bear/stressed\n"
                "3. RESEARCH REPORT (PDF) — analise setorial, posicionamento competitivo, "
                "highlights financeiros, valuation range\n"
                "4. EXECUTIVE MEMO (PDF) — resumo executivo de 2 paginas para MD e comite\n\n"
                + (
                    "OUTPUTS DCM ADICIONAIS:\n"
                    "5. PARECER DE CREDITO (PDF) — documento formal com:\n"
                    "   - Sumario executivo da operacao (emissor, instrumento, volume, prazo)\n"
                    "   - Analise de credito: leverage, coverage, DSCR historicos\n"
                    "   - ANALISE DE CENARIOS: tabela base/bear/stressed com metricas e status de covenant\n"
                    "   - Breach threshold: percentual de queda de EBITDA que viola cada covenant\n"
                    "   - Covenants propostos com justificativa\n"
                    "   - Risco de refinanciamento e perfil de amortizacao\n"
                    "   - Rating implicito e comparativo com emissores equivalentes\n"
                    "   - Parecer final: GO / NO-GO / CONDITIONAL com condicoes\n"
                    "6. TERM SHEET indicativo (PDF) — instrumento, volume, prazo, spread, "
                    "garantias, covenants, cronograma indicativo\n"
                    if task_dcm else ""
                )
                + (
                    "OUTPUTS ECM ADICIONAIS:\n"
                    "5. EQUITY OPINION (PDF) — documento formal com:\n"
                    "   - Sumario da operacao (emissor, tipo de oferta, volume estimado)\n"
                    "   - Valuation range por metodologia: trading comps, DCF, precedent transactions\n"
                    "   - Football field consolidado com price range por acao (low/mid/high)\n"
                    "   - Analise de diluicao: pre e pos-oferta, impacto nos minoritarios\n"
                    "   - Sensibilidade do valuation: impacto de +/- 1x EBITDA e +/- 1% WACC\n"
                    "   - Equity story: tese de crescimento, vantagens competitivas, uso de recursos\n"
                    "   - Conclusao: faixa de preco recomendada e racional\n"
                    "6. INVESTOR PRESENTATION (PPTX) — deck para roadshow com 15-20 slides\n"
                    if task_ecm else ""
                )
                + "Todos os documentos devem referenciar os ajustes contabeis realizados."
            ),
            expected_output=(
                "JSON com paths de todos os arquivos gerados: "
                "pitch_book, financial_model, research_report, executive_memo"
                + (", credit_opinion, term_sheet" if task_dcm else "")
                + (", equity_opinion, investor_presentation" if task_ecm else "")
                + "."
            ),
            agent=self.deck_builder,
            context=output_context,
        )

        # ---- TASK 8: MD Final Review ----
        md_context = output_context + [task_outputs]
        task_md_review = Task(
            description=(
                f"Revisao final como MD de {self.company_name}:\n"
                "1. Consistencia entre outputs\n2. Ajustes contabeis refletidos\n"
                "3. Valuation em range razoavel\n4. Materiais completos\n"
                f"5. Armazenar findings na memoria RAG (setor: {self.sector})\n"
                "Parecer final de MD."
            ),
            expected_output="Parecer final: outputs confirmados, highlights, recomendacao GO/NO-GO/CONDITIONAL.",
            agent=self.orchestrator,
            context=md_context,
        )

        # ---- Pipeline assembly by mode ----
        if self.mode == "parsing_only":
            return [task_accounting, task_research, task_adjustments]
        elif self.mode == "valuation_only":
            tasks = [task_accounting, task_research, task_adjustments, task_modeling]
            if task_dcm:
                tasks.append(task_dcm)
            if task_ecm:
                tasks.append(task_ecm)
            tasks.append(task_quant)
            return tasks
        elif self.mode == "output_only":
            return [task_outputs]
        else:  # full_analysis
            tasks = [task_accounting, task_research, task_adjustments, task_modeling]
            if task_dcm:
                tasks.append(task_dcm)
            if task_ecm:
                tasks.append(task_ecm)
            tasks.extend([task_quant, task_risk, task_outputs, task_md_review])
            return tasks
