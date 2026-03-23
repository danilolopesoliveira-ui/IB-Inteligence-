"""
Accounting Adjustments Tool
Applies technical accounting adjustments to financial statements before consolidation.

Adjustments covered:
  1. IFRS 16 — operating leases → right-of-use asset + lease liability
  2. Non-recurring normalization — remove one-off items from EBITDA
  3. Revenue recognition (competência vs. caixa)
  4. Accounting policy harmonization across entities (depreciation, inventory method)
  5. Provision adequacy (contingências, devedores duvidosos)
  6. Related-party / intercompany reclassification
  7. Tax reconciliation (fiscal vs. accounting basis)
  8. BR GAAP → IFRS conversion flags
"""

from __future__ import annotations

import json
from typing import Any

from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------

class IFRS16Lease(BaseModel):
    entity: str
    annual_lease_payment: float = Field(description="Pagamento anual de aluguel (R$)")
    remaining_term_years: int = Field(description="Prazo remanescente do contrato (anos)")
    discount_rate: float = Field(default=0.14, description="Taxa de desconto incremental do tomador")
    year: str = Field(description="Ano de aplicação do ajuste")


class NonRecurringItem(BaseModel):
    entity: str
    description: str
    amount: float = Field(description="Valor do item (positivo = receita/ganho; negativo = despesa/perda)")
    account: str = Field(description="Conta afetada: 'ebitda', 'ebit', 'net_income', 'gross_profit'")
    year: str


class ProvisionAdjustment(BaseModel):
    entity: str
    provision_type: str = Field(description="Tipo: 'bad_debt', 'contingency_labor', 'contingency_tax', 'other'")
    current_provision: float
    recommended_provision: float
    year: str


class DepreciationPolicy(BaseModel):
    entity: str
    asset_class: str = Field(description="Ex: 'machinery', 'buildings', 'vehicles', 'software'")
    useful_life_current: int = Field(description="Vida útil atual usada pela empresa (anos)")
    useful_life_standard: int = Field(description="Vida útil padrão de mercado (anos)")
    gross_asset_value: float
    year: str


class AccountingAdjustmentsInput(BaseModel):
    entities_data: str = Field(
        description="JSON com DFs por entidade (output do excel_parser / pdf_parser)"
    )
    ifrs16_leases: str = Field(
        default="[]",
        description="JSON list de IFRS16Lease — contratos de arrendamento a capitalizar",
    )
    non_recurring_items: str = Field(
        default="[]",
        description="JSON list de NonRecurringItem — itens a normalizar no EBITDA",
    )
    provision_adjustments: str = Field(
        default="[]",
        description="JSON list de ProvisionAdjustment — ajustes de provisões",
    )
    depreciation_policies: str = Field(
        default="[]",
        description="JSON list de DepreciationPolicy — harmonização de vida útil",
    )
    revenue_recognition_adjustments: str = Field(
        default="[]",
        description=(
            "JSON list de ajustes de reconhecimento de receita. "
            'Formato: [{"entity": "X", "year": "2023", "amount": 500000, '
            '"description": "Receita antecipada a diferir"}]'
        ),
    )
    target_standard: str = Field(
        default="IFRS",
        description="Padrão contábil alvo: 'IFRS' ou 'BR_GAAP'",
    )


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class AccountingAdjustmentsTool(BaseTool):
    name: str = "accounting_adjustments"
    description: str = (
        "Aplica ajustes contábeis técnicos nas DFs antes da consolidação: "
        "IFRS 16, normalização de EBITDA (itens não recorrentes), ajustes de provisões, "
        "harmonização de políticas de depreciação e reconhecimento de receita. "
        "Retorna DFs ajustadas por entidade e memorando de ajustes para auditoria."
    )
    args_schema: type[BaseModel] = AccountingAdjustmentsInput

    def _run(
        self,
        entities_data: str,
        ifrs16_leases: str = "[]",
        non_recurring_items: str = "[]",
        provision_adjustments: str = "[]",
        depreciation_policies: str = "[]",
        revenue_recognition_adjustments: str = "[]",
        target_standard: str = "IFRS",
    ) -> str:
        try:
            entities: dict[str, Any] = json.loads(entities_data)
            leases: list[dict] = json.loads(ifrs16_leases)
            nri: list[dict] = json.loads(non_recurring_items)
            provisions: list[dict] = json.loads(provision_adjustments)
            dep_policies: list[dict] = json.loads(depreciation_policies)
            rev_adj: list[dict] = json.loads(revenue_recognition_adjustments)

            # Deep copy entities to avoid mutation
            import copy
            adjusted = copy.deepcopy(entities)
            memo: list[dict] = []  # adjustment log for audit trail

            # Apply each adjustment category
            adjusted, m1 = self._apply_ifrs16(adjusted, leases)
            adjusted, m2 = self._apply_non_recurring(adjusted, nri)
            adjusted, m3 = self._apply_provisions(adjusted, provisions)
            adjusted, m4 = self._apply_depreciation_harmonization(adjusted, dep_policies)
            adjusted, m5 = self._apply_revenue_recognition(adjusted, rev_adj)

            memo = m1 + m2 + m3 + m4 + m5

            # Recompute derived lines after adjustments
            adjusted = self._recompute_subtotals(adjusted)

            # Validation checks
            validation = self._validate_adjustments(adjusted)

            result = {
                "adjusted_entities": adjusted,
                "adjustment_memo": memo,
                "total_adjustments": len(memo),
                "validation": validation,
                "target_standard": target_standard,
                "summary": self._build_summary(memo),
            }

            return json.dumps(result, ensure_ascii=False, indent=2, default=str)

        except Exception as exc:
            logger.error(f"Erro nos ajustes contábeis: {exc}")
            return json.dumps({"error": str(exc)})

    # ------------------------------------------------------------------
    # IFRS 16 — Operating lease capitalization
    # ------------------------------------------------------------------

    def _apply_ifrs16(
        self, entities: dict, leases: list[dict]
    ) -> tuple[dict, list[dict]]:
        memo = []
        for lease in leases:
            entity = lease.get("entity", "")
            if entity not in entities:
                logger.warning(f"IFRS 16: entidade '{entity}' não encontrada.")
                continue

            pmt = float(lease.get("annual_lease_payment", 0))
            n = int(lease.get("remaining_term_years", 1))
            r = float(lease.get("discount_rate", 0.14))
            year = lease.get("year", "")

            # Right-of-use asset (PV of lease payments)
            if r > 0:
                rou_asset = pmt * (1 - (1 + r) ** -n) / r
            else:
                rou_asset = pmt * n

            # Lease liability = same as ROU at inception
            lease_liability = rou_asset

            # Depreciation of ROU (straight-line over term)
            rou_depreciation = rou_asset / n if n > 0 else 0

            # Interest on lease liability (year 1)
            interest_expense = lease_liability * r

            # Remove operating lease from OpEx (rent expense → add back to EBITDA)
            rent_addback = pmt

            # Apply to BS
            bs = entities[entity].setdefault("balance_sheet", {})
            is_ = entities[entity].setdefault("income_statement", {})

            self._bs_add(bs, "right_of_use", year, rou_asset)
            self._bs_add(bs, "lease_liability_lt", year, lease_liability)

            # IS adjustments
            # 1. Remove rent from OpEx (add back to EBITDA)
            self._is_add(is_, "ebitda", year, rent_addback)
            # 2. Add depreciation of ROU — DA is stored as negative (expense), so subtract
            self._is_add(is_, "da", year, -rou_depreciation)
            # 3. Add interest on lease (financial expenses stored as negative)
            self._is_add(is_, "financial_expenses", year, -interest_expense)

            memo.append({
                "type": "IFRS_16",
                "entity": entity,
                "year": year,
                "rou_asset": round(rou_asset, 0),
                "lease_liability": round(lease_liability, 0),
                "rou_depreciation_annual": round(rou_depreciation, 0),
                "interest_expense_year1": round(interest_expense, 0),
                "ebitda_addback": round(rent_addback, 0),
                "description": (
                    f"Capitalização de arrendamento operacional: ROU R${rou_asset:,.0f}, "
                    f"passivo R${lease_liability:,.0f}. EBITDA +R${rent_addback:,.0f} "
                    f"(remoção de aluguel); D&A +R${rou_depreciation:,.0f}; "
                    f"Despesa financeira +R${interest_expense:,.0f}."
                ),
            })

        return entities, memo

    # ------------------------------------------------------------------
    # Non-recurring normalization
    # ------------------------------------------------------------------

    def _apply_non_recurring(
        self, entities: dict, items: list[dict]
    ) -> tuple[dict, list[dict]]:
        memo = []
        for item in items:
            entity = item.get("entity", "")
            if entity not in entities:
                continue
            account = item.get("account", "ebitda")
            amount = float(item.get("amount", 0))
            year = item.get("year", "")
            description = item.get("description", "")

            is_ = entities[entity].setdefault("income_statement", {})
            # Remove non-recurring item (negate it to normalize)
            self._is_add(is_, f"{account}_normalized", year, -amount)
            self._is_add(is_, account, year, -amount)

            memo.append({
                "type": "NON_RECURRING_NORMALIZATION",
                "entity": entity,
                "year": year,
                "account": account,
                "amount_removed": round(-amount, 0),
                "description": f"Normalização: {description}. Ajuste de R${-amount:,.0f} em {account}.",
            })

        return entities, memo

    # ------------------------------------------------------------------
    # Provision adjustments
    # ------------------------------------------------------------------

    def _apply_provisions(
        self, entities: dict, provisions: list[dict]
    ) -> tuple[dict, list[dict]]:
        memo = []
        for prov in provisions:
            entity = prov.get("entity", "")
            if entity not in entities:
                continue
            ptype = prov.get("provision_type", "other")
            current = float(prov.get("current_provision", 0))
            recommended = float(prov.get("recommended_provision", 0))
            year = prov.get("year", "")
            delta = recommended - current

            is_ = entities[entity].setdefault("income_statement", {})
            bs = entities[entity].setdefault("balance_sheet", {})

            account_map = {
                "bad_debt": ("other_operating_expenses", "allowance_doubtful_accounts"),
                "contingency_labor": ("other_operating_expenses", "contingencies_provision"),
                "contingency_tax": ("other_operating_expenses", "contingencies_provision"),
                "other": ("other_operating_expenses", "other_provisions"),
            }
            is_account, bs_account = account_map.get(ptype, ("other_operating_expenses", "other_provisions"))

            # Increase provision → expense on IS, liability on BS
            self._is_add(is_, is_account, year, -delta)  # negative = expense
            self._bs_add(bs, bs_account, year, delta)

            memo.append({
                "type": "PROVISION_ADJUSTMENT",
                "entity": entity,
                "year": year,
                "provision_type": ptype,
                "current": round(current, 0),
                "recommended": round(recommended, 0),
                "delta": round(delta, 0),
                "description": (
                    f"Ajuste de provisão ({ptype}): de R${current:,.0f} para R${recommended:,.0f}. "
                    f"{'Constituição' if delta > 0 else 'Reversão'} de R${abs(delta):,.0f}."
                ),
            })

        return entities, memo

    # ------------------------------------------------------------------
    # Depreciation policy harmonization
    # ------------------------------------------------------------------

    def _apply_depreciation_harmonization(
        self, entities: dict, policies: list[dict]
    ) -> tuple[dict, list[dict]]:
        memo = []
        for pol in policies:
            entity = pol.get("entity", "")
            if entity not in entities:
                continue
            asset_class = pol.get("asset_class", "")
            life_current = int(pol.get("useful_life_current", 1))
            life_standard = int(pol.get("useful_life_standard", 1))
            gross_value = float(pol.get("gross_asset_value", 0))
            year = pol.get("year", "")

            if life_current == life_standard or life_current == 0:
                continue

            # Depreciation difference
            dep_current = gross_value / life_current
            dep_standard = gross_value / life_standard
            dep_delta = dep_standard - dep_current  # positive = more depreciation needed

            is_ = entities[entity].setdefault("income_statement", {})
            # DA is stored as negative (expense); dep_delta > 0 means more depreciation needed
            self._is_add(is_, "da", year, -dep_delta)
            # Reduce net book value of PPE on BS
            bs = entities[entity].setdefault("balance_sheet", {})
            self._bs_add(bs, "ppe_net", year, -dep_delta)

            memo.append({
                "type": "DEPRECIATION_HARMONIZATION",
                "entity": entity,
                "year": year,
                "asset_class": asset_class,
                "life_current_years": life_current,
                "life_standard_years": life_standard,
                "gross_asset_value": round(gross_value, 0),
                "depreciation_adjustment": round(dep_delta, 0),
                "description": (
                    f"Harmonização de vida útil ({asset_class}): {life_current}a → {life_standard}a. "
                    f"Ajuste de D&A: R${dep_delta:,.0f}."
                ),
            })

        return entities, memo

    # ------------------------------------------------------------------
    # Revenue recognition
    # ------------------------------------------------------------------

    def _apply_revenue_recognition(
        self, entities: dict, adjustments: list[dict]
    ) -> tuple[dict, list[dict]]:
        memo = []
        for adj in adjustments:
            entity = adj.get("entity", "")
            if entity not in entities:
                continue
            amount = float(adj.get("amount", 0))
            year = adj.get("year", "")
            description = adj.get("description", "")

            is_ = entities[entity].setdefault("income_statement", {})
            bs = entities[entity].setdefault("balance_sheet", {})

            # Adjust recognized revenue and create deferred revenue on BS
            self._is_add(is_, "net_revenue", year, -amount)
            self._bs_add(bs, "deferred_revenue", year, amount)

            memo.append({
                "type": "REVENUE_RECOGNITION",
                "entity": entity,
                "year": year,
                "revenue_deferred": round(amount, 0),
                "description": f"Competência de receita: {description}. R${amount:,.0f} diferido.",
            })

        return entities, memo

    # ------------------------------------------------------------------
    # Recompute derived lines
    # ------------------------------------------------------------------

    def _recompute_subtotals(self, entities: dict) -> dict:
        for entity, data in entities.items():
            is_ = data.get("income_statement", {})

            def g(acct: str, year: str) -> float:
                return float((is_.get(acct) or {}).get(year, 0) or 0)

            all_years = set()
            for vals in is_.values():
                if isinstance(vals, dict):
                    all_years.update(vals.keys())

            for year in all_years:
                # Gross profit
                gp = g("net_revenue", year) - abs(g("cogs", year))
                if "gross_profit" in is_:
                    is_["gross_profit"][year] = gp

                # EBIT = EBITDA - D&A
                if "ebitda" in is_ and "da" in is_:
                    ebit = g("ebitda", year) - abs(g("da", year))
                    is_.setdefault("ebit", {})[year] = ebit

                # EBT = EBIT + financial result
                if "ebit" in is_:
                    fin_result = g("financial_income", year) - abs(g("financial_expenses", year))
                    ebt = g("ebit", year) + fin_result
                    is_.setdefault("ebt", {})[year] = ebt

        return entities

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_adjustments(self, entities: dict) -> list[dict]:
        issues = []
        for entity, data in entities.items():
            bs = data.get("balance_sheet", {})
            is_ = data.get("income_statement", {})

            all_years = set()
            for vals in bs.values():
                if isinstance(vals, dict):
                    all_years.update(vals.keys())

            def g_bs(acct: str, y: str) -> float:
                return float((bs.get(acct) or {}).get(y, 0) or 0)

            def g_is(acct: str, y: str) -> float:
                return float((is_.get(acct) or {}).get(y, 0) or 0)

            for year in sorted(all_years):
                total_assets = g_bs("total_assets", year)
                total_eq = g_bs("total_equity", year)
                total_curr_liab = g_bs("total_current_liabilities", year)
                total_noncurr_liab = g_bs("total_noncurrent_liabilities", year)
                total_liab_eq = total_eq + total_curr_liab + total_noncurr_liab

                # BP equation check
                if total_assets and total_liab_eq:
                    diff = abs(total_assets - total_liab_eq)
                    if diff / total_assets > 0.01:  # >1% tolerance
                        issues.append({
                            "entity": entity,
                            "year": year,
                            "issue": "BALANCO_DESBALANCEADO",
                            "detail": (
                                f"Ativo Total R${total_assets:,.0f} ≠ "
                                f"Passivo+PL R${total_liab_eq:,.0f} "
                                f"(diferença R${diff:,.0f})"
                            ),
                            "severity": "HIGH",
                        })

                # Negative equity warning
                if total_eq < 0:
                    issues.append({
                        "entity": entity,
                        "year": year,
                        "issue": "PATRIMONIO_LIQUIDO_NEGATIVO",
                        "detail": f"PL negativo: R${total_eq:,.0f}",
                        "severity": "MEDIUM",
                    })

                # Negative revenue
                net_rev = g_is("net_revenue", year)
                if net_rev < 0:
                    issues.append({
                        "entity": entity,
                        "year": year,
                        "issue": "RECEITA_NEGATIVA",
                        "detail": f"Receita líquida negativa: R${net_rev:,.0f}",
                        "severity": "HIGH",
                    })

        return issues

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _build_summary(self, memo: list[dict]) -> dict:
        from collections import Counter
        type_counts = Counter(m["type"] for m in memo)
        entities_affected = list({m["entity"] for m in memo})
        return {
            "adjustments_by_type": dict(type_counts),
            "entities_affected": entities_affected,
            "total_adjustments": len(memo),
        }

    # ------------------------------------------------------------------
    # Helper mutators
    # ------------------------------------------------------------------

    def _bs_add(self, bs: dict, account: str, year: str, amount: float) -> None:
        bs.setdefault(account, {})
        bs[account][year] = float(bs[account].get(year, 0) or 0) + amount

    def _is_add(self, is_: dict, account: str, year: str, amount: float) -> None:
        is_.setdefault(account, {})
        is_[account][year] = float(is_[account].get(year, 0) or 0) + amount
