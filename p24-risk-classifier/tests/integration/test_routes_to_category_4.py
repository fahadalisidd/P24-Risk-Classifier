"""Mandatory Verification: EVERY Route to Category 4 has an automated test.

Routes Tested:
1. Route 1: Static Rubric natural score calculation (Scope × Reversibility × Persistence >= 17)
2. Route 2: Dynamic Rubric payload-specific rule escalation
3. Route 3: Policy Override forced category assignment
4. Route 4: Policy Pin activation of critical policy
5. Precedence and multi-mechanism resolution
"""
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.orm import Session

from app.core.clock import ControllableClock
from app.domain.enums import Scope, Reversibility, Persistence, RiskCategory, RuleAction
from app.domain.models import RiskRuleModel, PolicyOverrideModel, PolicyPinModel
from app.schemas.evaluation import RiskEvaluationRequest
from app.service.risk_service import RiskClassificationService


class TestAllRoutesToCategory4:
    @pytest.fixture
    def clock(self):
        return ControllableClock(datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc))

    def test_route_1_static_rubric_category_4(self, db_session: Session, clock: ControllableClock):
        """Route 1: Pure static rubric natural calculation yields score >= 17 -> Category 4."""
        service = RiskClassificationService(db=db_session, clock=clock)

        req = RiskEvaluationRequest(
            operationId="op-cat4-route1",
            operationType="DATABASE_MIGRATION",
            scope=Scope.GLOBAL,              # weight 4
            reversibility=Reversibility.IRREVERSIBLE,  # weight 4
            persistence=Persistence.PERMANENT,        # weight 4
            # 4 * 4 * 4 = 64 (>= 17)
            payload={
                "approval": "sec-approval-99",
                "justification": "Global migration",
                "rollbackPlan": "Full restore point",
            },
        )

        res = service.evaluate(req)

        assert res.riskScore == 64
        assert res.baseCategory == 4
        assert res.rubricCategory == 4
        assert res.finalCategory == 4
        assert res.overrideApplied is False
        assert len(res.matchedRules) == 0
        assert res.obligationsSatisfied is True
        assert any("Score 64 mapped to Base Category 4" in r for r in res.classificationReasons)

    def test_route_2_dynamic_rule_category_4(self, db_session: Session, clock: ControllableClock):
        """Route 2: Base score is low (Cat 1), but payload triggers dynamic rule escalation to Category 4."""
        # Insert dynamic rule
        rule = RiskRuleModel(
            rule_id="PRODUCTION_IRREVERSIBLE_DELETE",
            name="Irreversible Delete in Production",
            conditions={
                "operationType": "DELETE",
                "payload.environment": "PRODUCTION",
                "reversibility": "IRREVERSIBLE",
            },
            result_action=RuleAction.SET_MIN_CATEGORY.value,
            target_category=4,
            priority=200,
            enabled=True,
            created_at=clock.now(),
        )
        db_session.add(rule)
        db_session.commit()

        service = RiskClassificationService(db=db_session, clock=clock)

        # LOCAL (1) * IRREVERSIBLE (4) * TEMPORARY (1) = Score 4 -> Base Category 1
        req = RiskEvaluationRequest(
            operationId="op-cat4-route2",
            operationType="DELETE",
            scope=Scope.LOCAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={
                "environment": "PRODUCTION",
                "approval": "appr-123",
                "justification": "Temp file purge",
                "rollbackPlan": "Backup available",
            },
        )

        res = service.evaluate(req)

        assert res.riskScore == 4
        assert res.baseCategory == 1
        assert res.rubricCategory == 4
        assert res.finalCategory == 4
        assert "PRODUCTION_IRREVERSIBLE_DELETE" in res.matchedRules
        assert res.overrideApplied is False

    def test_route_3_policy_override_category_4(self, db_session: Session, clock: ControllableClock):
        """Route 3: Low base score and no dynamic escalation, but active policy override forces Category 4."""
        override = PolicyOverrideModel(
            name="Emergency Security Freeze Override",
            conditions={"payload.securityCritical": True},
            forced_category=4,
            reason="Emergency security audit in progress",
            enabled=True,
            created_at=clock.now() - timedelta(days=1),
            expires_at=clock.now() + timedelta(days=5),
        )
        db_session.add(override)
        db_session.commit()

        service = RiskClassificationService(db=db_session, clock=clock)

        # LOCAL (1) * REVERSIBLE (1) * TEMPORARY (1) = Score 1 -> Base Category 1
        req = RiskEvaluationRequest(
            operationId="op-cat4-route3",
            operationType="CONFIG_UPDATE",
            scope=Scope.LOCAL,
            reversibility=Reversibility.REVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={
                "securityCritical": True,
                "approval": "sec-lead",
                "justification": "Firewall tweak",
                "rollbackPlan": "Revert commit",
            },
        )

        res = service.evaluate(req)

        assert res.riskScore == 1
        assert res.baseCategory == 1
        assert res.rubricCategory == 1
        assert res.finalCategory == 4
        assert res.overrideApplied is True
        assert res.overrideCategory == 4
        assert res.overrideReason == "Emergency security audit in progress"

    def test_route_4_policy_pin_category_4(self, db_session: Session, clock: ControllableClock):
        """Route 4: Active Policy Pin pins a critical policy and forces Category 4."""
        pin = PolicyPinModel(
            pin_id="pin-freeze-cat4",
            policy_id="STRICT_CRITICAL_FREEZE",
            reason="Q4 Production Freeze Pin",
            created_at=clock.now() - timedelta(days=10),
            review_date=clock.now() - timedelta(days=2),  # Review overdue but still usable
            expires_at=clock.now() + timedelta(days=10),
            enabled=True,
        )
        db_session.add(pin)
        db_session.commit()

        service = RiskClassificationService(db=db_session, clock=clock)

        # Base score 1
        req = RiskEvaluationRequest(
            operationId="op-cat4-route4",
            operationType="PATCH",
            scope=Scope.LOCAL,
            reversibility=Reversibility.REVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={
                "pinId": "pin-freeze-cat4",
                "approval": "director-signoff",
                "justification": "Emergency hotfix",
                "rollbackPlan": "Immediate redeploy previous image",
            },
        )

        res = service.evaluate(req)

        assert res.baseCategory == 1
        assert res.finalCategory == 4
        assert any("Policy Pin 'pin-freeze-cat4'" in r for r in res.classificationReasons)

    def test_precedence_policy_override_over_rubric(self, db_session: Session, clock: ControllableClock):
        """Test precedence when multiple mechanisms apply."""
        # Add dynamic rule setting min category 3
        rule = RiskRuleModel(
            rule_id="RULE_CAT_3",
            name="Set Cat 3",
            conditions={"operationType": "UPDATE"},
            result_action=RuleAction.SET_MIN_CATEGORY.value,
            target_category=3,
            priority=100,
            enabled=True,
            created_at=clock.now(),
        )
        # Add override forcing category 4
        override = PolicyOverrideModel(
            name="Override to Cat 4",
            conditions={"operationType": "UPDATE"},
            forced_category=4,
            reason="Executive override",
            enabled=True,
            created_at=clock.now(),
        )
        db_session.add_all([rule, override])
        db_session.commit()

        service = RiskClassificationService(db=db_session, clock=clock)

        req = RiskEvaluationRequest(
            operationId="op-prec",
            operationType="UPDATE",
            scope=Scope.LOCAL,
            reversibility=Reversibility.REVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={"approval": "a", "justification": "j", "rollbackPlan": "r"},
        )

        res = service.evaluate(req)
        assert res.baseCategory == 1
        assert res.rubricCategory == 3
        assert res.finalCategory == 4
        assert res.overrideApplied is True
