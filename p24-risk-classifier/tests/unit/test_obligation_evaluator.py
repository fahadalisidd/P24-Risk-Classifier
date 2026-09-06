"""Unit tests for Post-Classification Obligation Evaluator."""
import pytest
from app.domain.enums import Scope, Reversibility, Persistence, RiskCategory
from app.obligation.obligation_evaluator import ObligationEvaluator
from app.schemas.operation import OperationPayload


class TestObligationEvaluator:
    @pytest.fixture
    def evaluator(self):
        return ObligationEvaluator()

    def test_schema_validates_without_obligation_fields(self):
        # Verification that OperationPayload does NOT require obligation fields upfront
        op = OperationPayload(
            operationId="op-raw",
            operationType="DELETE",
            scope=Scope.GLOBAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.PERMANENT,
            payload={},  # completely empty payload
        )
        assert op.operationId == "op-raw"

    def test_category_1_no_obligations(self, evaluator):
        op = OperationPayload(
            operationId="op-cat1",
            operationType="READ",
            scope=Scope.LOCAL,
            reversibility=Reversibility.REVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={},
        )
        res = evaluator.evaluate(RiskCategory.LOW, op)
        assert res.required_obligations == []
        assert res.obligations_satisfied is True
        assert res.missing_obligations == []

    def test_category_4_missing_all_obligations(self, evaluator):
        op = OperationPayload(
            operationId="op-cat4-empty",
            operationType="DELETE",
            scope=Scope.GLOBAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.PERMANENT,
            payload={},
        )
        res = evaluator.evaluate(RiskCategory.CRITICAL, op)
        assert res.required_obligations == ["approval", "justification", "rollbackPlan"]
        assert res.obligations_satisfied is False
        assert set(res.missing_obligations) == {"approval", "justification", "rollbackPlan"}

    def test_category_4_partial_obligations(self, evaluator):
        op = OperationPayload(
            operationId="op-cat4-partial",
            operationType="DELETE",
            scope=Scope.GLOBAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.PERMANENT,
            payload={
                "justification": "Emergency migration fix",
                # missing approval and rollbackPlan
            },
        )
        res = evaluator.evaluate(RiskCategory.CRITICAL, op)
        assert res.obligations_satisfied is False
        assert set(res.missing_obligations) == {"approval", "rollbackPlan"}

    def test_category_4_all_obligations_satisfied(self, evaluator):
        op = OperationPayload(
            operationId="op-cat4-full",
            operationType="DELETE",
            scope=Scope.GLOBAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.PERMANENT,
            payload={
                "approval": "ticket-appr-456",
                "justification": "Approved DB clean-up",
                "rollbackPlan": "Restore from snapshot snap-2026-08",
            },
        )
        res = evaluator.evaluate(RiskCategory.CRITICAL, op)
        assert res.obligations_satisfied is True
        assert res.missing_obligations == []
