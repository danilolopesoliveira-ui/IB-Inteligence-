"""Tests for the Accounting Adjustments Tool."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.finance.accounting_adjustments import AccountingAdjustmentsTool


def make_base_entities():
    return {
        "Empresa ABC": {
            "balance_sheet": {
                "cash": {"2024": 5_000_000},
                "accounts_receivable": {"2024": 15_000_000},
                "total_current_assets": {"2024": 22_000_000},
                "ppe_net": {"2024": 20_000_000},
                "total_noncurrent_assets": {"2024": 20_000_000},
                "total_assets": {"2024": 42_000_000},
                "accounts_payable": {"2024": 6_000_000},
                "st_debt": {"2024": 4_000_000},
                "total_current_liabilities": {"2024": 12_000_000},
                "lt_debt": {"2024": 10_000_000},
                "total_noncurrent_liabilities": {"2024": 10_000_000},
                "total_equity": {"2024": 20_000_000},
            },
            "income_statement": {
                "net_revenue": {"2024": 50_000_000},
                "cogs": {"2024": -30_000_000},
                "gross_profit": {"2024": 20_000_000},
                "ebitda": {"2024": 10_000_000},
                "da": {"2024": -2_000_000},
                "ebit": {"2024": 8_000_000},
                "financial_expenses": {"2024": -1_400_000},
                "net_income": {"2024": 4_300_000},
            },
        }
    }


class TestAccountingAdjustments:
    def test_ifrs16_basic(self):
        """IFRS 16 should create ROU asset and increase EBITDA."""
        tool = AccountingAdjustmentsTool()
        entities = make_base_entities()

        leases = [{
            "entity": "Empresa ABC",
            "annual_lease_payment": 1_200_000,
            "remaining_term_years": 5,
            "discount_rate": 0.14,
            "year": "2024",
        }]

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            ifrs16_leases=json.dumps(leases),
        ))

        adj_entities = result["adjusted_entities"]
        bs = adj_entities["Empresa ABC"]["balance_sheet"]
        is_ = adj_entities["Empresa ABC"]["income_statement"]

        # ROU asset should be added
        assert bs["right_of_use"]["2024"] > 0
        # Lease liability should be added
        assert bs["lease_liability_lt"]["2024"] > 0
        # EBITDA should increase (rent addback)
        assert is_["ebitda"]["2024"] > 10_000_000
        # D&A should increase
        assert abs(is_["da"]["2024"]) > 2_000_000

    def test_non_recurring_normalization(self):
        """Non-recurring item should reduce EBITDA when removed."""
        tool = AccountingAdjustmentsTool()
        entities = make_base_entities()

        # Assume a one-off gain of 2M was included in EBITDA
        nri = [{
            "entity": "Empresa ABC",
            "description": "Ganho na venda de ativo imobilizado",
            "amount": 2_000_000,  # positive = gain/income to remove
            "account": "ebitda",
            "year": "2024",
        }]

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            non_recurring_items=json.dumps(nri),
        ))

        adj_is = result["adjusted_entities"]["Empresa ABC"]["income_statement"]
        # EBITDA normalized should be 10M - 2M = 8M
        assert adj_is["ebitda"]["2024"] == pytest.approx(8_000_000)

    def test_provision_adjustment(self):
        """Provision increase should hit P&L and BS."""
        tool = AccountingAdjustmentsTool()
        entities = make_base_entities()

        provisions = [{
            "entity": "Empresa ABC",
            "provision_type": "bad_debt",
            "current_provision": 0,
            "recommended_provision": 750_000,  # 5% PDD on 15M AR
            "year": "2024",
        }]

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            provision_adjustments=json.dumps(provisions),
        ))

        adj_bs = result["adjusted_entities"]["Empresa ABC"]["balance_sheet"]
        adj_is = result["adjusted_entities"]["Empresa ABC"]["income_statement"]

        # Provision appears on BS
        assert adj_bs["allowance_doubtful_accounts"]["2024"] == pytest.approx(750_000)
        # Expense hits P&L (negative)
        assert adj_is["other_operating_expenses"]["2024"] < 0

    def test_depreciation_harmonization(self):
        """Different useful life should adjust D&A."""
        tool = AccountingAdjustmentsTool()
        entities = make_base_entities()

        dep_policies = [{
            "entity": "Empresa ABC",
            "asset_class": "machinery",
            "useful_life_current": 10,
            "useful_life_standard": 8,
            "gross_asset_value": 8_000_000,
            "year": "2024",
        }]

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            depreciation_policies=json.dumps(dep_policies),
        ))

        adj_is = result["adjusted_entities"]["Empresa ABC"]["income_statement"]
        # D&A should increase (shorter useful life = more depreciation)
        # Original: 8M/10 = 800k/year
        # Standard: 8M/8 = 1M/year → delta = +200k
        expected_da_original = abs(entities["Empresa ABC"]["income_statement"]["da"]["2024"])
        adjusted_da = abs(adj_is["da"]["2024"])
        assert adjusted_da > expected_da_original

    def test_validation_flags_unbalanced_bs(self):
        """Validation should flag a significantly unbalanced balance sheet."""
        tool = AccountingAdjustmentsTool()
        # Create intentionally unbalanced BS
        bad_entities = {
            "Bad Corp": {
                "balance_sheet": {
                    "total_assets": {"2024": 100_000_000},
                    "total_equity": {"2024": 20_000_000},
                    "total_current_liabilities": {"2024": 10_000_000},
                    "total_noncurrent_liabilities": {"2024": 10_000_000},  # Total L+E = 40M ≠ 100M
                },
                "income_statement": {
                    "net_revenue": {"2024": 50_000_000},
                },
            }
        }

        result = json.loads(tool._run(entities_data=json.dumps(bad_entities)))
        validation = result["validation"]
        assert any(v["issue"] == "BALANCO_DESBALANCEADO" for v in validation)

    def test_memo_documents_adjustments(self):
        """Adjustment memo should record each applied adjustment."""
        tool = AccountingAdjustmentsTool()
        entities = make_base_entities()

        leases = [{"entity": "Empresa ABC", "annual_lease_payment": 500_000,
                   "remaining_term_years": 3, "discount_rate": 0.14, "year": "2024"}]
        nri = [{"entity": "Empresa ABC", "description": "Item NR",
                "amount": 500_000, "account": "ebitda", "year": "2024"}]

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            ifrs16_leases=json.dumps(leases),
            non_recurring_items=json.dumps(nri),
        ))

        memo = result["adjustment_memo"]
        types = {m["type"] for m in memo}
        assert "IFRS_16" in types
        assert "NON_RECURRING_NORMALIZATION" in types
        assert result["total_adjustments"] == 2

    def test_unknown_entity_skipped(self):
        """Adjustments for unknown entities should be silently skipped."""
        tool = AccountingAdjustmentsTool()
        entities = make_base_entities()

        leases = [{"entity": "ENTIDADE_INEXISTENTE", "annual_lease_payment": 1_000_000,
                   "remaining_term_years": 5, "discount_rate": 0.14, "year": "2024"}]

        result = json.loads(tool._run(
            entities_data=json.dumps(entities),
            ifrs16_leases=json.dumps(leases),
        ))

        # No error, no adjustments applied
        assert "error" not in result
        assert result["total_adjustments"] == 0
