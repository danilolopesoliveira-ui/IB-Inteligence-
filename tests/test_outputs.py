"""Tests for output generators (Excel, PDF)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def make_full_analysis_data():
    return {
        "financials": {
            "years": ["2022", "2023", "2024"],
            "income_statement": {
                "net_revenue": {"2022": 80_000_000, "2023": 96_000_000, "2024": 116_000_000},
                "ebitda": {"2022": 18_000_000, "2023": 23_500_000, "2024": 29_000_000},
                "da": {"2022": -4_000_000, "2023": -4_800_000, "2024": -5_800_000},
                "ebit": {"2022": 14_000_000, "2023": 18_700_000, "2024": 23_200_000},
                "financial_expenses": {"2022": -3_500_000, "2023": -4_000_000, "2024": -4_500_000},
                "net_income": {"2022": 7_260_000, "2023": 10_164_000, "2024": 12_936_000},
                "cogs": {"2022": -48_000_000, "2023": -56_000_000, "2024": -67_000_000},
            },
            "balance_sheet": {
                "cash": {"2022": 5_000_000, "2023": 7_500_000, "2024": 9_000_000},
                "total_assets": {"2022": 60_000_000, "2023": 73_500_000, "2024": 87_000_000},
                "st_debt": {"2022": 5_000_000, "2023": 6_000_000, "2024": 5_500_000},
                "lt_debt": {"2022": 20_000_000, "2023": 22_000_000, "2024": 24_000_000},
                "total_equity": {"2022": 22_000_000, "2023": 30_000_000, "2024": 38_000_000},
                "total_current_assets": {"2022": 32_000_000, "2023": 40_000_000, "2024": 48_000_000},
                "total_current_liabilities": {"2022": 16_000_000, "2023": 19_000_000, "2024": 22_000_000},
            },
            "kpis": {
                "ebitda_margin": {"2022": 0.225, "2023": 0.245, "2024": 0.25},
                "net_margin": {"2022": 0.091, "2023": 0.106, "2024": 0.111},
                "net_debt": {"2022": 20_000_000, "2023": 20_500_000, "2024": 20_500_000},
                "net_leverage": {"2022": 1.11, "2023": 0.87, "2024": 0.71},
                "fcf": {"2022": 8_000_000, "2023": 10_000_000, "2024": 13_000_000},
            },
        },
        "dcf_output": {
            "wacc": 0.155,
            "enterprise_value": 180_000_000,
            "equity_value": 150_500_000,
            "pv_fcff": 60_000_000,
            "pv_terminal_value": 120_000_000,
            "implied_ev_ebitda": 6.2,
            "gross_debt": 29_500_000,
            "cash": 9_000_000,
            "minority_interest": 0,
            "projection": [
                {"year": "P1", "revenue": 133_400_000, "ebitda": 33_350_000,
                 "ebitda_margin": 0.25, "da": -5_336_000, "ebit": 28_014_000,
                 "nopat": 18_489_000, "capex": -8_004_000, "delta_nwc": -1_442_000, "fcff": 14_043_000},
            ],
            "sensitivity_ev": {},
        },
        "adjustment_memo": [
            {
                "type": "IFRS_16",
                "entity": "Empresa Demo",
                "year": "2024",
                "rou_asset": 4_000_000,
                "lease_liability": 4_000_000,
                "ebitda_addback": 1_200_000,
                "description": "Capitalização de arrendamento de galpão logístico.",
            }
        ],
        "adjustment_summary": {
            "adjustments_by_type": {"IFRS_16": 1},
            "entities_affected": ["Empresa Demo"],
            "total_adjustments": 1,
        },
        "red_flags": {
            "total_flags": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "red_flags": [],
            "investment_grade": True,
        },
        "comps_output": {
            "trading_comps": {
                "sector": "industria",
                "universe": [
                    {"name": "WEG", "ev_ebitda": 22.0, "p_e": 35.0, "ev_revenue": 4.5},
                    {"name": "Romi", "ev_ebitda": 7.5, "p_e": 13.0, "ev_revenue": 1.2},
                ],
                "ev_ebitda_stats": {"min": 7.5, "q1": 7.5, "median": 14.75, "mean": 14.75, "q3": 22.0, "max": 22.0},
                "implied_ev_from_ebitda": {"median": 215_000_000, "q1": 109_000_000, "q3": 320_000_000},
            },
            "transaction_comps": {"transactions": [], "ev_ebitda_stats": {}, "implied_ev": {}},
            "football_field": [
                {"method": "Trading Comps — EV/EBITDA", "low": 109_000_000, "mid": 215_000_000, "high": 320_000_000},
            ],
        },
        "credit_analysis": {
            "years": ["2022", "2023", "2024"],
            "credit_analysis": {
                "2024": {
                    "leverage": {"gross_debt": 29_500_000, "net_debt": 20_500_000, "net_leverage": 0.71},
                    "coverage": {"ebitda_interest_coverage": 6.44, "dscr": 2.5},
                    "liquidity": {"current_ratio": 2.18, "quick_ratio": 1.7, "cash_ratio": 0.41},
                    "credit_score": {"score": 90, "implied_rating": "AAA-AA", "flags": []},
                }
            },
        },
    }


class TestExcelBuilder:
    def test_generates_excel_file(self, tmp_path):
        pytest.importorskip("openpyxl")

        from tools.output.excel_builder import ExcelBuilderTool

        tool = ExcelBuilderTool()
        data = make_full_analysis_data()
        output_path = str(tmp_path / "test_model.xlsx")

        result = json.loads(tool._run(
            analysis_data=json.dumps(data),
            company_name="Empresa Demo",
            output_path=output_path,
        ))

        assert result.get("saved") is True
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 1000  # non-empty file

    def test_excel_has_expected_sheets(self, tmp_path):
        pytest.importorskip("openpyxl")
        import openpyxl

        from tools.output.excel_builder import ExcelBuilderTool

        tool = ExcelBuilderTool()
        data = make_full_analysis_data()
        output_path = str(tmp_path / "test_sheets.xlsx")

        result = json.loads(tool._run(
            analysis_data=json.dumps(data),
            company_name="Empresa Demo",
            output_path=output_path,
        ))

        wb = openpyxl.load_workbook(output_path)
        sheet_names = wb.sheetnames
        assert "Cover" in sheet_names
        assert "Financials" in sheet_names
        assert "DCF" in sheet_names


class TestPDFBuilder:
    def test_generates_executive_memo(self, tmp_path):
        pytest.importorskip("reportlab")

        from tools.output.pdf_builder import PDFBuilderTool

        tool = PDFBuilderTool()
        data = make_full_analysis_data()
        output_path = str(tmp_path / "test_memo.pdf")

        result = json.loads(tool._run(
            analysis_data=json.dumps(data),
            company_name="Empresa Demo",
            document_type="executive_memo",
            output_path=output_path,
        ))

        assert result.get("saved") is True
        assert Path(output_path).exists()
        assert Path(output_path).stat().st_size > 500

    def test_generates_research_report(self, tmp_path):
        pytest.importorskip("reportlab")

        from tools.output.pdf_builder import PDFBuilderTool

        tool = PDFBuilderTool()
        data = make_full_analysis_data()
        output_path = str(tmp_path / "test_report.pdf")

        result = json.loads(tool._run(
            analysis_data=json.dumps(data),
            company_name="Empresa Demo",
            document_type="research_report",
            output_path=output_path,
        ))

        assert result.get("saved") is True
        assert Path(output_path).exists()
