"""
demo_run.py — Geração de relatório de crédito e pitch book com dados fictícios.
Roda toda a cadeia de tools sem necessidade de API key.

Empresa fictícia: Grupo Vértice Indústria S.A.
Setor: Indústria de Embalagens Plásticas
Estrutura: Holding + 2 subsidiárias operacionais + 1 SPE imobiliária
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Garante que o diretório do projeto está no path
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

console = Console()

OUTPUT_DIR = PROJECT_ROOT / "output" / "demo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
os.environ["OUTPUT_DIR"] = str(OUTPUT_DIR)


# ===========================================================================
# DADOS FICTÍCIOS — Grupo Vértice Indústria S.A.
# ===========================================================================

COMPANY_NAME = "Grupo Vértice Indústria S.A."
SECTOR = "industria"
DEAL_TYPE = "PE_Investment"

ENTITIES_DATA = {
    "Vértice Holding S.A.": {
        "balance_sheet": {
            "cash":                      {"2022": 2_100_000,  "2023": 3_400_000,  "2024": 4_800_000},
            "accounts_receivable":        {"2022": 4_500_000,  "2023": 5_200_000,  "2024": 6_100_000},
            "inventory":                  {"2022": 800_000,    "2023": 900_000,    "2024": 1_000_000},
            "other_current_assets":       {"2022": 400_000,    "2023": 500_000,    "2024": 600_000},
            "total_current_assets":       {"2022": 7_800_000,  "2023": 10_000_000, "2024": 12_500_000},
            "ppe_net":                    {"2022": 5_000_000,  "2023": 5_500_000,  "2024": 6_000_000},
            "intangibles":                {"2022": 800_000,    "2023": 750_000,    "2024": 700_000},
            "investments_lt":             {"2022": 12_000_000, "2023": 14_000_000, "2024": 16_000_000},
            "total_noncurrent_assets":    {"2022": 17_800_000, "2023": 20_250_000, "2024": 22_700_000},
            "total_assets":               {"2022": 25_600_000, "2023": 30_250_000, "2024": 35_200_000},
            "accounts_payable":           {"2022": 1_200_000,  "2023": 1_400_000,  "2024": 1_600_000},
            "st_debt":                    {"2022": 2_000_000,  "2023": 2_500_000,  "2024": 2_000_000},
            "taxes_payable":              {"2022": 600_000,    "2023": 700_000,    "2024": 800_000},
            "total_current_liabilities":  {"2022": 4_200_000,  "2023": 5_100_000,  "2024": 5_200_000},
            "lt_debt":                    {"2022": 8_000_000,  "2023": 8_500_000,  "2024": 8_000_000},
            "total_noncurrent_liabilities":{"2022": 8_000_000, "2023": 8_500_000,  "2024": 8_000_000},
            "total_equity":               {"2022": 13_400_000, "2023": 16_650_000, "2024": 22_000_000},
        },
        "income_statement": {
            "gross_revenue":              {"2022": 6_000_000,  "2023": 7_000_000,  "2024": 8_500_000},
            "revenue_deductions":         {"2022": -600_000,   "2023": -700_000,   "2024": -850_000},
            "net_revenue":                {"2022": 5_400_000,  "2023": 6_300_000,  "2024": 7_650_000},
            "cogs":                       {"2022": -2_160_000, "2023": -2_520_000, "2024": -3_060_000},
            "gross_profit":               {"2022": 3_240_000,  "2023": 3_780_000,  "2024": 4_590_000},
            "selling_expenses":           {"2022": -500_000,   "2023": -580_000,   "2024": -700_000},
            "ga_expenses":                {"2022": -900_000,   "2023": -1_020_000, "2024": -1_200_000},
            "ebitda":                     {"2022": 1_840_000,  "2023": 2_180_000,  "2024": 2_690_000},
            "da":                         {"2022": -420_000,   "2023": -450_000,   "2024": -480_000},
            "ebit":                       {"2022": 1_420_000,  "2023": 1_730_000,  "2024": 2_210_000},
            "financial_income":           {"2022": 180_000,    "2023": 260_000,    "2024": 340_000},
            "financial_expenses":         {"2022": -980_000,   "2023": -1_050_000, "2024": -1_020_000},
            "ebt":                        {"2022": 620_000,    "2023": 940_000,    "2024": 1_530_000},
            "income_tax":                 {"2022": -211_000,   "2023": -320_000,   "2024": -520_000},
            "net_income":                 {"2022": 409_000,    "2023": 620_000,    "2024": 1_010_000},
        },
    },

    "Vértice Embalagens Ltda": {
        "balance_sheet": {
            "cash":                      {"2022": 3_500_000,  "2023": 5_200_000,  "2024": 7_400_000},
            "accounts_receivable":        {"2022": 22_000_000, "2023": 26_500_000, "2024": 31_000_000},
            "inventory":                  {"2022": 9_000_000,  "2023": 10_500_000, "2024": 12_000_000},
            "other_current_assets":       {"2022": 1_500_000,  "2023": 1_800_000,  "2024": 2_100_000},
            "total_current_assets":       {"2022": 36_000_000, "2023": 44_000_000, "2024": 52_500_000},
            "ppe_net":                    {"2022": 28_000_000, "2023": 32_000_000, "2024": 36_000_000},
            "intangibles":                {"2022": 1_200_000,  "2023": 1_100_000,  "2024": 1_000_000},
            "total_noncurrent_assets":    {"2022": 29_200_000, "2023": 33_100_000, "2024": 37_000_000},
            "total_assets":               {"2022": 65_200_000, "2023": 77_100_000, "2024": 89_500_000},
            "accounts_payable":           {"2022": 8_500_000,  "2023": 10_000_000, "2024": 11_500_000},
            "st_debt":                    {"2022": 6_000_000,  "2023": 7_000_000,  "2024": 6_500_000},
            "accrued_salaries":           {"2022": 2_000_000,  "2023": 2_200_000,  "2024": 2_400_000},
            "taxes_payable":              {"2022": 1_500_000,  "2023": 1_800_000,  "2024": 2_100_000},
            "total_current_liabilities":  {"2022": 18_500_000, "2023": 21_500_000, "2024": 23_500_000},
            "lt_debt":                    {"2022": 22_000_000, "2023": 24_000_000, "2024": 26_000_000},
            "contingencies_provision":    {"2022": 1_000_000,  "2023": 1_200_000,  "2024": 1_400_000},
            "total_noncurrent_liabilities":{"2022": 23_000_000,"2023": 25_200_000, "2024": 27_400_000},
            "total_equity":               {"2022": 23_700_000, "2023": 30_400_000, "2024": 38_600_000},
        },
        "income_statement": {
            "gross_revenue":              {"2022": 98_000_000, "2023": 118_000_000,"2024": 142_000_000},
            "revenue_deductions":         {"2022": -14_700_000,"2023": -17_700_000,"2024": -21_300_000},
            "net_revenue":                {"2022": 83_300_000, "2023": 100_300_000,"2024": 120_700_000},
            "cogs":                       {"2022": -54_145_000,"2023": -65_195_000,"2024": -78_455_000},
            "gross_profit":               {"2022": 29_155_000, "2023": 35_105_000, "2024": 42_245_000},
            "selling_expenses":           {"2022": -7_497_000, "2023": -9_027_000, "2024": -10_863_000},
            "ga_expenses":                {"2022": -4_998_000, "2023": -6_018_000, "2024": -7_242_000},
            "ebitda":                     {"2022": 16_660_000, "2023": 20_060_000, "2024": 24_140_000},
            "da":                         {"2022": -3_600_000, "2023": -4_200_000, "2024": -5_000_000},
            "ebit":                       {"2022": 13_060_000, "2023": 15_860_000, "2024": 19_140_000},
            "financial_income":           {"2022": 280_000,    "2023": 410_000,    "2024": 590_000},
            "financial_expenses":         {"2022": -3_850_000, "2023": -4_340_000, "2024": -4_680_000},
            "ebt":                        {"2022": 9_490_000,  "2023": 11_930_000, "2024": 15_050_000},
            "income_tax":                 {"2022": -3_227_000, "2023": -4_056_000, "2024": -5_117_000},
            "net_income":                 {"2022": 6_263_000,  "2023": 7_874_000,  "2024": 9_933_000},
        },
    },

    "Vértice Logística Ltda": {
        "balance_sheet": {
            "cash":                      {"2022": 800_000,    "2023": 1_100_000,  "2024": 1_600_000},
            "accounts_receivable":        {"2022": 5_500_000,  "2023": 6_800_000,  "2024": 8_200_000},
            "inventory":                  {"2022": 600_000,    "2023": 700_000,    "2024": 800_000},
            "total_current_assets":       {"2022": 6_900_000,  "2023": 8_600_000,  "2024": 10_600_000},
            "ppe_net":                    {"2022": 8_000_000,  "2023": 9_000_000,  "2024": 10_200_000},
            "total_noncurrent_assets":    {"2022": 8_000_000,  "2023": 9_000_000,  "2024": 10_200_000},
            "total_assets":               {"2022": 14_900_000, "2023": 17_600_000, "2024": 20_800_000},
            "accounts_payable":           {"2022": 1_800_000,  "2023": 2_100_000,  "2024": 2_400_000},
            "st_debt":                    {"2022": 1_500_000,  "2023": 1_800_000,  "2024": 1_500_000},
            "total_current_liabilities":  {"2022": 3_900_000,  "2023": 4_500_000,  "2024": 4_800_000},
            "lt_debt":                    {"2022": 5_000_000,  "2023": 5_500_000,  "2024": 6_000_000},
            "total_noncurrent_liabilities":{"2022": 5_000_000, "2023": 5_500_000,  "2024": 6_000_000},
            "total_equity":               {"2022": 6_000_000,  "2023": 7_600_000,  "2024": 10_000_000},
        },
        "income_statement": {
            "gross_revenue":              {"2022": 22_000_000, "2023": 27_000_000, "2024": 33_000_000},
            "revenue_deductions":         {"2022": -2_200_000, "2023": -2_700_000, "2024": -3_300_000},
            "net_revenue":                {"2022": 19_800_000, "2023": 24_300_000, "2024": 29_700_000},
            "cogs":                       {"2022": -13_860_000,"2023": -17_010_000,"2024": -20_790_000},
            "gross_profit":               {"2022": 5_940_000,  "2023": 7_290_000,  "2024": 8_910_000},
            "selling_expenses":           {"2022": -990_000,   "2023": -1_215_000, "2024": -1_485_000},
            "ga_expenses":                {"2022": -990_000,   "2023": -1_215_000, "2024": -1_485_000},
            "ebitda":                     {"2022": 3_960_000,  "2023": 4_860_000,  "2024": 5_940_000},
            "da":                         {"2022": -900_000,   "2023": -1_050_000, "2024": -1_200_000},
            "ebit":                       {"2022": 3_060_000,  "2023": 3_810_000,  "2024": 4_740_000},
            "financial_income":           {"2022": 60_000,     "2023": 80_000,     "2024": 110_000},
            "financial_expenses":         {"2022": -820_000,   "2023": -950_000,   "2024": -1_020_000},
            "ebt":                        {"2022": 2_300_000,  "2023": 2_940_000,  "2024": 3_830_000},
            "income_tax":                 {"2022": -782_000,   "2023": -1_000_000, "2024": -1_302_000},
            "net_income":                 {"2022": 1_518_000,  "2023": 1_940_000,  "2024": 2_528_000},
        },
    },

    "Vértice Imóveis SPE Ltda": {
        "balance_sheet": {
            "cash":                      {"2022": 200_000,    "2023": 300_000,    "2024": 400_000},
            "total_current_assets":       {"2022": 200_000,    "2023": 300_000,    "2024": 400_000},
            "ppe_net":                    {"2022": 15_000_000, "2023": 14_800_000, "2024": 14_600_000},
            "total_noncurrent_assets":    {"2022": 15_000_000, "2023": 14_800_000, "2024": 14_600_000},
            "total_assets":               {"2022": 15_200_000, "2023": 15_100_000, "2024": 15_000_000},
            "st_debt":                    {"2022": 500_000,    "2023": 500_000,    "2024": 500_000},
            "total_current_liabilities":  {"2022": 600_000,    "2023": 600_000,    "2024": 600_000},
            "lt_debt":                    {"2022": 9_000_000,  "2023": 8_500_000,  "2024": 8_000_000},
            "total_noncurrent_liabilities":{"2022": 9_000_000, "2023": 8_500_000,  "2024": 8_000_000},
            "total_equity":               {"2022": 5_600_000,  "2023": 6_000_000,  "2024": 6_400_000},
        },
        "income_statement": {
            "net_revenue":                {"2022": 2_400_000,  "2023": 2_600_000,  "2024": 2_800_000},
            "cogs":                       {"2022": -480_000,   "2023": -520_000,   "2024": -560_000},
            "gross_profit":               {"2022": 1_920_000,  "2023": 2_080_000,  "2024": 2_240_000},
            "ga_expenses":                {"2022": -300_000,   "2023": -320_000,   "2024": -340_000},
            "ebitda":                     {"2022": 1_620_000,  "2023": 1_760_000,  "2024": 1_900_000},
            "da":                         {"2022": -200_000,   "2023": -200_000,   "2024": -200_000},
            "ebit":                       {"2022": 1_420_000,  "2023": 1_560_000,  "2024": 1_700_000},
            "financial_expenses":         {"2022": -720_000,   "2023": -680_000,   "2024": -640_000},
            "ebt":                        {"2022": 700_000,    "2023": 880_000,    "2024": 1_060_000},
            "income_tax":                 {"2022": -238_000,   "2023": -299_000,   "2024": -360_000},
            "net_income":                 {"2022": 462_000,    "2023": 581_000,    "2024": 700_000},
        },
    },
}

OWNERSHIP = {
    "Vértice Holding S.A.": {
        "Vértice Embalagens Ltda": 1.00,
        "Vértice Logística Ltda": 0.75,
        "Vértice Imóveis SPE Ltda": 1.00,
    }
}

# Intercompany: Holding cobra management fee das subsidiárias
# e a SPE cobra aluguel da Embalagens
INTERCOMPANY = [
    {"from_entity": "Vértice Embalagens Ltda", "to_entity": "Vértice Holding S.A.",
     "account": "ga_expenses", "amount": 1_200_000, "year": "2024"},
    {"from_entity": "Vértice Logística Ltda",  "to_entity": "Vértice Holding S.A.",
     "account": "ga_expenses", "amount": 400_000,   "year": "2024"},
    {"from_entity": "Vértice Embalagens Ltda", "to_entity": "Vértice Imóveis SPE Ltda",
     "account": "net_revenue", "amount": 2_400_000, "year": "2024"},
    # Mesmo ajuste para anos anteriores
    {"from_entity": "Vértice Embalagens Ltda", "to_entity": "Vértice Holding S.A.",
     "account": "ga_expenses", "amount": 1_000_000, "year": "2023"},
    {"from_entity": "Vértice Logística Ltda",  "to_entity": "Vértice Holding S.A.",
     "account": "ga_expenses", "amount": 350_000,   "year": "2023"},
    {"from_entity": "Vértice Embalagens Ltda", "to_entity": "Vértice Imóveis SPE Ltda",
     "account": "net_revenue", "amount": 2_200_000, "year": "2023"},
]

# Ajustes contábeis a aplicar
IFRS16_LEASES = [
    # Embalagens: galpão de produção alugado (não era capitalizado)
    {"entity": "Vértice Embalagens Ltda", "annual_lease_payment": 2_400_000,
     "remaining_term_years": 7, "discount_rate": 0.14, "year": "2024"},
    # Logística: frota de caminhões em leasing operacional
    {"entity": "Vértice Logística Ltda", "annual_lease_payment": 1_800_000,
     "remaining_term_years": 4, "discount_rate": 0.15, "year": "2024"},
]

NON_RECURRING_ITEMS = [
    # Embalagens: ganho de venda de máquina obsoleta em 2024
    {"entity": "Vértice Embalagens Ltda", "description": "Ganho na venda de ativo imobilizado",
     "amount": 1_500_000, "account": "ebitda", "year": "2024"},
    # Embalagens: provisão extraordinária para rescisão de executivo em 2023
    {"entity": "Vértice Embalagens Ltda", "description": "Provisão rescisão CEO",
     "amount": -800_000, "account": "ebitda", "year": "2023"},
]

PROVISION_ADJUSTMENTS = [
    # PDD: 8% dos recebíveis da Embalagens (empresa não provisionava)
    {"entity": "Vértice Embalagens Ltda", "provision_type": "bad_debt",
     "current_provision": 0, "recommended_provision": 2_480_000, "year": "2024"},
    # Contingência trabalhista (ação coletiva em andamento)
    {"entity": "Vértice Embalagens Ltda", "provision_type": "contingency_labor",
     "current_provision": 500_000, "recommended_provision": 1_800_000, "year": "2024"},
]

DEBT_SCHEDULE = [
    {"year": "2024", "principal": 4_000_000, "interest": 5_740_000, "tranche": "CCB Bradesco"},
    {"year": "2025", "principal": 5_000_000, "interest": 5_180_000, "tranche": "CCB Bradesco"},
    {"year": "2026", "principal": 6_000_000, "interest": 4_480_000, "tranche": "CCB Bradesco + CRI"},
    {"year": "2027", "principal": 6_000_000, "interest": 3_640_000, "tranche": "CRI"},
    {"year": "2028", "principal": 6_500_000, "interest": 2_730_000, "tranche": "CRI"},
    {"year": "2029", "principal": 7_000_000, "interest": 1_820_000, "tranche": "Debentures"},
    {"year": "2030", "principal": 7_500_000, "interest": 780_000,   "tranche": "Debentures"},
]


# ===========================================================================
# PIPELINE
# ===========================================================================

def run_pipeline():
    console.print(Panel.fit(
        f"[bold]Grupo Vértice Indústria S.A.[/bold]\n"
        "Relatório de Crédito + Pitch Book — Dados Fictícios\n"
        f"Output: [cyan]{OUTPUT_DIR}[/cyan]",
        title="IB-Agents Demo", border_style="blue",
    ))

    results = {}

    # ------------------------------------------------------------------
    # 1. Ajustes Contábeis
    # ------------------------------------------------------------------
    console.print("\n[bold yellow]1/6  Ajustes Contábeis (Contador)[/bold yellow]")
    from tools.finance.accounting_adjustments import AccountingAdjustmentsTool

    adj_tool = AccountingAdjustmentsTool()
    adj_result = json.loads(adj_tool._run(
        entities_data=json.dumps(ENTITIES_DATA),
        ifrs16_leases=json.dumps(IFRS16_LEASES),
        non_recurring_items=json.dumps(NON_RECURRING_ITEMS),
        provision_adjustments=json.dumps(PROVISION_ADJUSTMENTS),
    ))

    results["adjustment_memo"] = adj_result["adjustment_memo"]
    results["adjustment_summary"] = adj_result["summary"]
    adjusted_entities = adj_result["adjusted_entities"]

    _print_adjustment_summary(adj_result)

    # ------------------------------------------------------------------
    # 2. Consolidação
    # ------------------------------------------------------------------
    console.print("\n[bold yellow]2/6  Consolidação (Financial Modeler)[/bold yellow]")
    from tools.finance.consolidation import ConsolidationTool

    cons_tool = ConsolidationTool()
    cons_result = json.loads(cons_tool._run(
        entities_data=json.dumps(adjusted_entities),
        ownership=json.dumps(OWNERSHIP),
        intercompany=json.dumps(INTERCOMPANY),
        years=["2022", "2023", "2024"],
        reconstruct_cfc=True,
    ))

    results["financials"] = cons_result
    _print_consolidated_summary(cons_result)

    # ------------------------------------------------------------------
    # 3. Análise de Crédito
    # ------------------------------------------------------------------
    console.print("\n[bold yellow]3/6  Análise de Crédito[/bold yellow]")
    from tools.finance.credit_analysis import CreditAnalysisTool

    cred_tool = CreditAnalysisTool()
    cred_result = json.loads(cred_tool._run(
        financials=json.dumps(cons_result),
        debt_schedule=json.dumps(DEBT_SCHEDULE),
    ))

    results["credit_analysis"] = cred_result
    _print_credit_summary(cred_result)

    # ------------------------------------------------------------------
    # 4. DCF
    # ------------------------------------------------------------------
    console.print("\n[bold yellow]4/6  Valuation DCF (FCFF)[/bold yellow]")
    from tools.finance.dcf import DCFTool

    dcf_tool = DCFTool()
    dcf_result = json.loads(dcf_tool._run(
        financials=json.dumps(cons_result),
        projections=json.dumps({
            "revenue_growth":   [0.17, 0.15, 0.13, 0.11, 0.09],
            "ebitda_margin":    [0.215, 0.220, 0.225, 0.230, 0.235],
            "da_pct_revenue":   0.042,
            "capex_pct_revenue":0.065,
            "nwc_pct_revenue":  0.120,
            "tax_rate":         0.34,
        }),
        wacc_inputs=json.dumps({
            "risk_free_rate": 0.1375,
            "beta": 1.05,
            "erp": 0.055,
            "country_risk": 0.028,
            "cost_of_debt": 0.145,
            "tax_rate": 0.34,
            "debt_weight": 0.40,
        }),
        terminal_growth=0.045,
        terminal_method="gordon",
        base_year="2024",
        projection_years=5,
    ))

    results["dcf_output"] = dcf_result
    _print_dcf_summary(dcf_result)

    # ------------------------------------------------------------------
    # 5. LBO
    # ------------------------------------------------------------------
    console.print("\n[bold yellow]5/6  Análise LBO[/bold yellow]")
    from tools.finance.lbo import LBOTool

    lbo_tool = LBOTool()
    lbo_result = json.loads(lbo_tool._run(
        financials=json.dumps(cons_result),
        entry_multiple=7.5,
        exit_multiple=9.0,
        hold_years=5,
        debt_structure=json.dumps({
            "senior_ccb": {"amount_pct_ev": 0.45, "rate": 0.145, "amort_years": 7},
            "mezz":        {"amount_pct_ev": 0.10, "rate": 0.180, "amort_years": 7},
        }),
        revenue_cagr=0.13,
        ebitda_margin_exit=0.235,
        management_fees_pct=0.02,
        transaction_costs_pct=0.025,
    ))

    results["lbo_output"] = lbo_result
    _print_lbo_summary(lbo_result)

    # ------------------------------------------------------------------
    # 5b. Comps
    # ------------------------------------------------------------------
    from tools.quant.comps import CompsTool
    comps_tool = CompsTool()
    comps_result = json.loads(comps_tool._run(
        target_financials=json.dumps(cons_result),
        sector=SECTOR,
        valuation_year="2024",
        custom_comps=json.dumps([
            {"name": "Braskem", "ev_ebitda": 8.5, "p_e": None, "ev_revenue": 0.9, "ebitda_margin": 0.12},
            {"name": "Irani", "ev_ebitda": 7.2, "p_e": 14.0, "ev_revenue": 1.3, "ebitda_margin": 0.20},
            {"name": "Klabin", "ev_ebitda": 9.8, "p_e": 18.0, "ev_revenue": 2.1, "ebitda_margin": 0.32},
        ]),
    ))
    results["comps_output"] = comps_result

    # ------------------------------------------------------------------
    # 6. Red Flags
    # ------------------------------------------------------------------
    from agents.risk_compliance import RedFlagCheckerTool, CovenantCheckerTool

    rf_tool = RedFlagCheckerTool()
    rf_result = json.loads(rf_tool._run(
        financials=json.dumps(cons_result),
        dcf_output=json.dumps(dcf_result),
        lbo_output=json.dumps(lbo_result),
    ))
    results["red_flags"] = rf_result

    cov_tool = CovenantCheckerTool()
    cov_result = json.loads(cov_tool._run(
        financials=json.dumps(cons_result),
        covenants=json.dumps([
            {"name": "Net Leverage", "metric": "net_leverage", "max": 3.5},
            {"name": "Interest Coverage (EBITDA/Juros)", "metric": "interest_coverage", "min": 2.5},
            {"name": "Current Ratio", "metric": "current_ratio", "min": 1.1},
        ]),
    ))
    results["covenant_results"] = cov_result

    # ------------------------------------------------------------------
    # 7. Gerar Outputs
    # ------------------------------------------------------------------
    console.print("\n[bold yellow]6/6  Gerando outputs (Excel + PDF + PPTX)[/bold yellow]")
    outputs = _generate_outputs(results)

    # Sumário final
    console.print("\n")
    console.print(Panel.fit(
        "\n".join(f"  [green]✓[/green] {k}: [cyan]{v}[/cyan]" for k, v in outputs.items()),
        title="[bold green]Outputs gerados[/bold green]",
        border_style="green",
    ))

    return results, outputs


# ===========================================================================
# OUTPUT GENERATION
# ===========================================================================

def _generate_outputs(results: dict) -> dict:
    outputs = {}

    # Excel
    try:
        from tools.output.excel_builder import ExcelBuilderTool
        xl_tool = ExcelBuilderTool()
        xl_path = str(OUTPUT_DIR / "modelo_financeiro_vertice.xlsx")
        xl_res = json.loads(xl_tool._run(
            analysis_data=json.dumps(results),
            company_name=COMPANY_NAME,
            output_path=xl_path,
        ))
        outputs["Excel (Modelo Financeiro)"] = xl_res.get("path", xl_path)
    except Exception as e:
        outputs["Excel"] = f"ERRO: {e}"

    # PDF — Research Report
    try:
        from tools.output.pdf_builder import PDFBuilderTool
        pdf_tool = PDFBuilderTool()
        rr_path = str(OUTPUT_DIR / "research_report_vertice.pdf")
        pdf_res = json.loads(pdf_tool._run(
            analysis_data=json.dumps(results),
            company_name=COMPANY_NAME,
            document_type="research_report",
            output_path=rr_path,
            analyst_name="Equipe IB-Agents (Demo)",
        ))
        outputs["PDF (Research Report)"] = pdf_res.get("path", rr_path)
    except Exception as e:
        outputs["PDF Research Report"] = f"ERRO: {e}"

    # PDF — Executive Memo
    try:
        from tools.output.pdf_builder import PDFBuilderTool
        pdf_tool = PDFBuilderTool()
        memo_path = str(OUTPUT_DIR / "executive_memo_vertice.pdf")
        memo_res = json.loads(pdf_tool._run(
            analysis_data=json.dumps(results),
            company_name=COMPANY_NAME,
            document_type="executive_memo",
            output_path=memo_path,
            analyst_name="Equipe IB-Agents (Demo)",
        ))
        outputs["PDF (Executive Memo)"] = memo_res.get("path", memo_path)
    except Exception as e:
        outputs["PDF Executive Memo"] = f"ERRO: {e}"

    # PPTX
    try:
        from tools.output.pptx_builder import PPTXBuilderTool
        pptx_tool = PPTXBuilderTool()
        pptx_path = str(OUTPUT_DIR / "pitch_book_vertice.pptx")
        pptx_res = json.loads(pptx_tool._run(
            analysis_data=json.dumps(results),
            company_name=COMPANY_NAME,
            deal_type=DEAL_TYPE,
            output_path=pptx_path,
        ))
        outputs["PPTX (Pitch Book)"] = pptx_res.get("path", pptx_path)
    except Exception as e:
        outputs["PPTX"] = f"ERRO: {e}"

    return outputs


# ===========================================================================
# CONSOLE PRINTERS
# ===========================================================================

def _print_adjustment_summary(adj: dict):
    summary = adj.get("summary", {})
    memo = adj.get("adjustment_memo", [])
    issues = adj.get("validation", [])

    t = Table(title="Ajustes Contábeis Aplicados", show_lines=True)
    t.add_column("Tipo", style="cyan")
    t.add_column("Entidade")
    t.add_column("Ano")
    t.add_column("Impacto Principal", style="yellow")

    impact_keys = ["ebitda_addback", "delta", "revenue_deferred",
                   "depreciation_adjustment", "rou_asset", "amount_removed"]
    for adj_item in memo:
        impact = next((f"R${adj_item[k]:,.0f}" for k in impact_keys if k in adj_item), "—")
        t.add_row(
            adj_item.get("type", ""),
            adj_item.get("entity", "")[:25],
            adj_item.get("year", ""),
            impact,
        )
    console.print(t)

    if issues:
        console.print(f"  [red]⚠ {len(issues)} issue(s) de validação encontrado(s)[/red]")
    else:
        console.print("  [green]✓ BP balanceado em todas as entidades[/green]")


def _print_consolidated_summary(cons: dict):
    is_ = cons.get("income_statement", {})
    kpis = cons.get("kpis", {})
    years = cons.get("years", [])

    def g(stmt, k, y): return float((stmt.get(k) or {}).get(y, 0) or 0)

    t = Table(title="DFs Consolidadas — Resumo", show_lines=True)
    t.add_column("Métrica", style="cyan")
    for y in years:
        t.add_column(y, justify="right")

    rows = [
        ("Receita Líquida (R$k)", is_, "net_revenue"),
        ("EBITDA (R$k)", is_, "ebitda"),
        ("Margem EBITDA", kpis, "ebitda_margin"),
        ("Lucro Líquido (R$k)", is_, "net_income"),
        ("Dívida Líquida (R$k)", kpis, "net_debt"),
        ("Net Leverage (x)", kpis, "net_leverage"),
        ("FCF (R$k)", kpis, "fcf"),
    ]
    for label, stmt, key in rows:
        vals = []
        for y in years:
            v = g(stmt, key, y)
            if "margin" in key:
                vals.append(f"{v*100:.1f}%")
            elif "leverage" in key:
                vals.append(f"{v:.1f}x")
            else:
                vals.append(f"{v/1000:,.0f}")
        t.add_row(label, *vals)
    console.print(t)


def _print_credit_summary(cred: dict):
    years = cred.get("years", [])
    ca = cred.get("credit_analysis", {})

    t = Table(title="Análise de Crédito", show_lines=True)
    t.add_column("Indicador", style="cyan")
    for y in years:
        t.add_column(y, justify="right")

    metric_paths = [
        ("Net Leverage (x)",    "leverage.net_leverage"),
        ("EBITDA/Juros (x)",    "coverage.ebitda_interest_coverage"),
        ("DSCR (x)",            "coverage.dscr"),
        ("Current Ratio",       "liquidity.current_ratio"),
        ("CCC (dias)",          "working_capital_days.cash_conversion_cycle_days"),
        ("Rating Implícito",    "credit_score.implied_rating"),
        ("Score (0-100)",       "credit_score.score"),
    ]

    def get_nested(d, path):
        for k in path.split("."):
            if isinstance(d, dict): d = d.get(k)
            else: return None
        return d

    for label, path in metric_paths:
        vals = []
        for y in years:
            v = get_nested(ca.get(y, {}), path)
            if v is None:
                vals.append("—")
            elif isinstance(v, float):
                vals.append(f"{v:.2f}")
            else:
                vals.append(str(v))
        t.add_row(label, *vals)
    console.print(t)

    # Rating final
    last = ca.get(years[-1], {})
    rating = (last.get("credit_score") or {}).get("implied_rating", "N/A")
    score = (last.get("credit_score") or {}).get("score", 0)
    color = "green" if score >= 70 else "yellow" if score >= 50 else "red"
    console.print(f"\n  Rating implícito 2024: [{color}]{rating}[/{color}] ({score}/100)")


def _print_dcf_summary(dcf: dict):
    ev = dcf.get("enterprise_value", 0)
    eq = dcf.get("equity_value", 0)
    wacc = dcf.get("wacc", 0)
    pv_fcff = dcf.get("pv_fcff", 0)
    pv_tv = dcf.get("pv_terminal_value", 0)
    tv_pct = pv_tv / ev * 100 if ev else 0

    t = Table(title="DCF — Resultados", show_lines=True)
    t.add_column("Item", style="cyan")
    t.add_column("Valor", justify="right", style="yellow")

    t.add_row("WACC", f"{wacc*100:.2f}%")
    t.add_row("PV FCFF (período explícito)", f"R${pv_fcff/1e6:,.1f}M")
    t.add_row("PV Terminal Value", f"R${pv_tv/1e6:,.1f}M ({tv_pct:.0f}%)")
    t.add_row("Enterprise Value", f"R${ev/1e6:,.1f}M")
    t.add_row("(-) Dívida Bruta", f"R${dcf.get('gross_debt',0)/1e6:,.1f}M")
    t.add_row("(+) Caixa", f"R${dcf.get('cash',0)/1e6:,.1f}M")
    t.add_row("Equity Value", f"R${eq/1e6:,.1f}M")
    t.add_row("EV/EBITDA implícito", f"{dcf.get('implied_ev_ebitda','—')}x")
    console.print(t)


def _print_lbo_summary(lbo: dict):
    ret = lbo.get("returns", {})
    entry = lbo.get("entry", {})
    exit_ = lbo.get("exit", {})

    t = Table(title="LBO — Retornos", show_lines=True)
    t.add_column("Item", style="cyan")
    t.add_column("Valor", justify="right", style="yellow")

    t.add_row("EV Entrada", f"R${entry.get('entry_ev',0)/1e6:,.1f}M ({entry.get('entry_multiple','—')}x EBITDA)")
    t.add_row("Equity Investido", f"R${entry.get('equity_invested',0)/1e6:,.1f}M")
    t.add_row("Alavancagem Entrada", f"{entry.get('leverage_ratio','—')}x")
    t.add_row("EV Saída", f"R${exit_.get('exit_ev',0)/1e6:,.1f}M ({exit_.get('exit_multiple','—')}x EBITDA)")
    t.add_row("IRR", f"[bold green]{ret.get('irr_pct','N/A')}[/bold green]")
    t.add_row("MOIC", f"[bold green]{ret.get('moic','—')}x[/bold green]")
    console.print(t)


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    import types
    import logging
    from unittest.mock import MagicMock

    logging.basicConfig(level=logging.WARNING)

    # ---- Stub leve para deps opcionais (plotly, camelot, etc.) ----
    class _AutoMock(types.ModuleType):
        def __getattr__(self, name):
            m = MagicMock(); setattr(self, name, m); return m

    for mod in ["chromadb", "pdfplumber", "camelot",
                "plotly", "plotly.graph_objects", "plotly.io",
                "sentence_transformers"]:
        if mod not in sys.modules:
            sys.modules[mod] = _AutoMock(mod)

    # ---- loguru: usa logging padrão ----
    loguru_mod = types.ModuleType("loguru")
    loguru_mod.logger = logging.getLogger("ib_agents")
    sys.modules.setdefault("loguru", loguru_mod)

    # ---- crewai: BaseTool real baseado em pydantic ----
    from pydantic import BaseModel

    class _BaseTool(BaseModel):
        name: str = ""
        description: str = ""
        args_schema: type = type(None)
        model_config = {"arbitrary_types_allowed": True}
        def _run(self, *a, **kw): raise NotImplementedError
        def run(self, *a, **kw): return self._run(*a, **kw)

    tools_mod = types.ModuleType("crewai.tools")
    tools_mod.BaseTool = _BaseTool
    tools_mod.tool = lambda f: f

    crewai_mod = types.ModuleType("crewai")
    crewai_mod.Agent = MagicMock()
    crewai_mod.Crew = MagicMock()
    crewai_mod.Task = MagicMock()
    crewai_mod.tools = tools_mod

    crewai_tools_mod = types.ModuleType("crewai_tools")
    crewai_tools_mod.tool = lambda f: f

    sys.modules["crewai"] = crewai_mod
    sys.modules["crewai.tools"] = tools_mod
    sys.modules["crewai_tools"] = crewai_tools_mod

    # Check output deps
    missing = []
    for dep, label in [("openpyxl", "openpyxl"), ("reportlab", "reportlab"), ("pptx", "python-pptx")]:
        try:
            __import__(dep)
        except ImportError:
            missing.append(label)

    if missing:
        console.print(f"[yellow]Dependências de output não instaladas: {', '.join(missing)}[/yellow]")
        console.print(f"[dim]Instale com: py -m pip install {' '.join(missing)}[/dim]\n")

    run_pipeline()
