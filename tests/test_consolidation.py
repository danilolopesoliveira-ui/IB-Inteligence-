"""Tests for the consolidation engine."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.finance.consolidation import ConsolidationTool


def make_entities(include_intercompany=False):
    entities = {
        "Holding SA": {
            "balance_sheet": {
                "cash": {"2023": 3_000_000, "2024": 4_000_000},
                "accounts_receivable": {"2023": 5_000_000, "2024": 6_000_000},
                "total_current_assets": {"2023": 8_000_000, "2024": 10_000_000},
                "ppe_net": {"2023": 10_000_000, "2024": 12_000_000},
                "total_noncurrent_assets": {"2023": 10_000_000, "2024": 12_000_000},
                "total_assets": {"2023": 18_000_000, "2024": 22_000_000},
                "accounts_payable": {"2023": 3_000_000, "2024": 3_500_000},
                "st_debt": {"2023": 2_000_000, "2024": 2_000_000},
                "total_current_liabilities": {"2023": 5_000_000, "2024": 6_000_000},
                "lt_debt": {"2023": 5_000_000, "2024": 6_000_000},
                "total_noncurrent_liabilities": {"2023": 5_000_000, "2024": 6_000_000},
                "total_equity": {"2023": 8_000_000, "2024": 10_000_000},
            },
            "income_statement": {
                "net_revenue": {"2023": 20_000_000, "2024": 24_000_000},
                "cogs": {"2023": -12_000_000, "2024": -14_000_000},
                "gross_profit": {"2023": 8_000_000, "2024": 10_000_000},
                "ebitda": {"2023": 5_000_000, "2024": 6_000_000},
                "da": {"2023": -1_000_000, "2024": -1_200_000},
                "ebit": {"2023": 4_000_000, "2024": 4_800_000},
                "net_income": {"2023": 2_500_000, "2024": 3_000_000},
            },
        },
        "Subsidiaria Ltda": {
            "balance_sheet": {
                "cash": {"2023": 1_000_000, "2024": 1_500_000},
                "accounts_receivable": {"2023": 3_000_000, "2024": 4_000_000},
                "total_current_assets": {"2023": 4_000_000, "2024": 5_500_000},
                "ppe_net": {"2023": 5_000_000, "2024": 6_000_000},
                "total_noncurrent_assets": {"2023": 5_000_000, "2024": 6_000_000},
                "total_assets": {"2023": 9_000_000, "2024": 11_500_000},
                "accounts_payable": {"2023": 1_500_000, "2024": 2_000_000},
                "st_debt": {"2023": 1_000_000, "2024": 1_000_000},
                "total_current_liabilities": {"2023": 2_500_000, "2024": 3_000_000},
                "lt_debt": {"2023": 2_000_000, "2024": 2_500_000},
                "total_noncurrent_liabilities": {"2023": 2_000_000, "2024": 2_500_000},
                "total_equity": {"2023": 4_500_000, "2024": 6_000_000},
            },
            "income_statement": {
                "net_revenue": {"2023": 10_000_000, "2024": 13_000_000},
                "cogs": {"2023": -6_000_000, "2024": -7_500_000},
                "gross_profit": {"2023": 4_000_000, "2024": 5_500_000},
                "ebitda": {"2023": 2_500_000, "2024": 3_200_000},
                "da": {"2023": -500_000, "2024": -600_000},
                "ebit": {"2023": 2_000_000, "2024": 2_600_000},
                "net_income": {"2023": 1_200_000, "2024": 1_600_000},
            },
        },
    }
    return entities


class TestConsolidation:
    def test_basic_consolidation_sums(self):
        entities = make_entities()
        tool = ConsolidationTool()

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            ownership=json.dumps({"Holding SA": {"Subsidiaria Ltda": 0.80}}),
            years=["2023", "2024"],
        ))

        assert "income_statement" in result
        is_ = result["income_statement"]
        # Net revenue should be sum of both entities
        assert is_["net_revenue"]["2023"] == pytest.approx(30_000_000)
        assert is_["net_revenue"]["2024"] == pytest.approx(37_000_000)

    def test_minority_interest_calculation(self):
        entities = make_entities()
        tool = ConsolidationTool()

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            ownership=json.dumps({"Holding SA": {"Subsidiaria Ltda": 0.75}}),
            years=["2023", "2024"],
        ))

        mi = result["minority_interest"]
        # 25% of subsidiary equity
        expected_mi_2024 = 6_000_000 * 0.25
        assert mi["mi_equity"]["2024"] == pytest.approx(expected_mi_2024)

    def test_intercompany_elimination(self):
        entities = make_entities()
        tool = ConsolidationTool()

        intercompany = [
            {
                "from_entity": "Holding SA",
                "to_entity": "Subsidiaria Ltda",
                "account": "net_revenue",
                "amount": 2_000_000,
                "year": "2024",
            }
        ]

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            ownership=json.dumps({"Holding SA": {"Subsidiaria Ltda": 1.0}}),
            intercompany=json.dumps(intercompany),
            years=["2023", "2024"],
        ))

        is_ = result["income_statement"]
        # 2024 net_revenue = 24M + 13M - 2M elimination = 35M
        assert is_["net_revenue"]["2024"] == pytest.approx(35_000_000)

    def test_kpis_computed(self):
        entities = make_entities()
        tool = ConsolidationTool()

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            ownership=json.dumps({"Holding SA": {"Subsidiaria Ltda": 1.0}}),
            years=["2023", "2024"],
        ))

        kpis = result["kpis"]
        assert "ebitda_margin" in kpis
        assert "net_leverage" in kpis
        assert "fcf" in kpis
        # EBITDA margin should be between 0 and 1
        margin_2024 = kpis["ebitda_margin"]["2024"]
        assert 0 < margin_2024 < 1

    def test_dfc_reconstruction(self):
        entities = make_entities()
        tool = ConsolidationTool()

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            ownership=json.dumps({}),
            years=["2023", "2024"],
            reconstruct_cfc=True,
        ))

        assert "cash_flow" in result
        cfc = result["cash_flow"]
        assert "cfo" in cfc
        assert "net_change_cash" in cfc
