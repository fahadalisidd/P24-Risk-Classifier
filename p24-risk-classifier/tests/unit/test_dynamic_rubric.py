"""Unit tests for Dynamic Rubric rule engine."""
import pytest
from app.classifier.dynamic_rubric import DynamicRubricEngine, DynamicRule
from app.domain.enums import Scope, Reversibility, Persistence, RiskCategory, RuleAction
from app.schemas.operation import OperationPayload


class TestDynamicRubric:
    @pytest.fixture
    def engine(self):
        rules = [
            DynamicRule(
                rule_id="PRODUCTION_IRREVERSIBLE_DELETE",
                name="Irreversible Delete in Production",
                conditions={
                    "operationType": "DELETE",
                    "payload.environment": "PRODUCTION",
                    "reversibility": "IRREVERSIBLE",
                },
                result_action=RuleAction.SET_MIN_CATEGORY,
                target_category=4,
                priority=200,
                enabled=True,
            ),
            DynamicRule(
                rule_id="HIGH_VOLUME_DELETE",
                name="Delete with > 10,000 records",
                conditions={
                    "operationType": "DELETE",
                    "payload.recordCount": {"gte": 10000},
                },
                result_action=RuleAction.SET_MIN_CATEGORY,
                target_category=3,
                priority=100,
                enabled=True,
            ),
            DynamicRule(
                rule_id="DISABLED_RULE",
                name="Disabled Rule Test",
                conditions={"operationType": "DELETE"},
                result_action=RuleAction.SET_MIN_CATEGORY,
                target_category=4,
                priority=300,
                enabled=False,
            ),
        ]
        return DynamicRubricEngine(rules=rules)

    def test_dynamic_escalation_to_category_4(self, engine):
        op = OperationPayload(
            operationId="op-1",
            operationType="DELETE",
            scope=Scope.LOCAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={"environment": "PRODUCTION"},
        )
        # Base category is 1 (LOCAL * IRREVERSIBLE * TEMPORARY = 1*4*1 = 4 -> Cat 1)
        base_cat = RiskCategory.LOW
        result_cat, matched_rules, reasons = engine.evaluate(base_cat, op)

        assert result_cat == RiskCategory.CRITICAL
        assert "PRODUCTION_IRREVERSIBLE_DELETE" in matched_rules
        assert any("Escalated category from 1 to 4" in r for r in reasons)

    def test_no_rule_match(self, engine):
        op = OperationPayload(
            operationId="op-2",
            operationType="READ",
            scope=Scope.LOCAL,
            reversibility=Reversibility.REVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={"environment": "DEVELOPMENT"},
        )
        result_cat, matched_rules, reasons = engine.evaluate(RiskCategory.LOW, op)
        assert result_cat == RiskCategory.LOW
        assert len(matched_rules) == 0

    def test_priority_and_multiple_matches(self, engine):
        op = OperationPayload(
            operationId="op-3",
            operationType="DELETE",
            scope=Scope.LOCAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={"environment": "PRODUCTION", "recordCount": 50000},
        )
        result_cat, matched_rules, reasons = engine.evaluate(RiskCategory.LOW, op)
        assert result_cat == RiskCategory.CRITICAL
        # Both rules matched, higher priority 200 evaluated first
        assert "PRODUCTION_IRREVERSIBLE_DELETE" in matched_rules
        assert "HIGH_VOLUME_DELETE" in matched_rules
