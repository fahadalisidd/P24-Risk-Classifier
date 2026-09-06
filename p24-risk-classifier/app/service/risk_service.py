"""Risk Classification Orchestrator Service.

Coordinates:
1. Structural Payload Validation
2. Static Rubric Evaluation (Scope × Reversibility × Persistence)
3. Dynamic Rubric Rules on Payload
4. Policy Pin Resolution
5. Policy Override Resolution
6. Final Risk Category Determination
7. Obligation Evaluation (POST-classification)
8. AI Model Risk & Justification Analysis
9. Evaluation Persistence / Audit Trail
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.ai.ai_advisor import AIRiskAdvisor
from app.classifier.static_rubric import StaticRubric
from app.classifier.dynamic_rubric import DynamicRubricEngine, DynamicRule
from app.classifier.rubric_engine import RubricEngine
from app.core.clock import Clock, get_clock
from app.domain.enums import RiskCategory, RuleAction
from app.domain.models import (
    RiskRuleModel,
    PolicyOverrideModel,
    PolicyPinModel,
    RiskEvaluationModel,
)
from app.obligation.obligation_evaluator import ObligationEvaluator
from app.policy.override_resolver import OverrideResolver, PolicyOverride
from app.policy.pin_registry import PinRegistry, PolicyPin
from app.policy.policy_resolver import PolicyResolver
from app.schemas.evaluation import RiskEvaluationRequest, RiskEvaluationResponse


class RiskClassificationService:
    """Service orchestrating the complete end-to-end risk evaluation workflow."""

    def __init__(self, db: Optional[Session] = None, clock: Optional[Clock] = None):
        self.db = db
        self._clock = clock
        self.static_rubric = StaticRubric()
        self.dynamic_engine = DynamicRubricEngine()
        self.rubric_engine = RubricEngine(
            static_rubric=self.static_rubric,
            dynamic_engine=self.dynamic_engine,
        )
        self.override_resolver = OverrideResolver(clock=self.clock)
        self.pin_registry = PinRegistry(clock=self.clock)
        self.policy_resolver = PolicyResolver(
            override_resolver=self.override_resolver,
            pin_registry=self.pin_registry,
            clock=self.clock,
        )
        self.obligation_evaluator = ObligationEvaluator()
        self.ai_advisor = AIRiskAdvisor()

        if self.db:
            self._load_from_db()

    @property
    def clock(self) -> Clock:
        return self._clock or get_clock()

    def _load_from_db(self) -> None:
        """Load configured rules, overrides, and pins from the database."""
        if not self.db:
            return

        # Load Dynamic Rules
        db_rules = self.db.query(RiskRuleModel).filter(RiskRuleModel.enabled == True).all()
        rules = [
            DynamicRule(
                rule_id=r.rule_id,
                name=r.name,
                conditions=r.conditions,
                result_action=RuleAction(r.result_action),
                target_category=r.target_category,
                priority=r.priority,
                enabled=r.enabled,
            )
            for r in db_rules
        ]
        self.dynamic_engine.set_rules(rules)

        # Load Policy Overrides
        db_overrides = self.db.query(PolicyOverrideModel).filter(PolicyOverrideModel.enabled == True).all()
        overrides = [
            PolicyOverride(
                id=o.id,
                name=o.name,
                conditions=o.conditions,
                forced_category=o.forced_category,
                reason=o.reason,
                enabled=o.enabled,
                created_at=o.created_at,
                expires_at=o.expires_at,
            )
            for o in db_overrides
        ]
        self.override_resolver.set_overrides(overrides)

        # Load Policy Pins
        db_pins = self.db.query(PolicyPinModel).filter(PolicyPinModel.enabled == True).all()
        pins = [
            PolicyPin(
                pin_id=p.pin_id,
                policy_id=p.policy_id,
                reason=p.reason,
                review_date=p.review_date,
                expires_at=p.expires_at,
                enabled=p.enabled,
                created_at=p.created_at,
            )
            for p in db_pins
        ]
        self.pin_registry.set_pins(pins)

    def evaluate(self, request: RiskEvaluationRequest, include_ai: bool = True) -> RiskEvaluationResponse:
        """Execute deterministic risk classification pipeline with optional AI assessment."""
        now = self.clock.now()

        # Step 1 & 2: Rubric Engine (Static + Dynamic)
        rubric_res = self.rubric_engine.evaluate(request)

        # Step 3 & 4: Policy Resolution (Pins + Overrides)
        policy_res = self.policy_resolver.resolve(
            rubric_category=rubric_res.rubric_category,
            operation=request,
        )

        all_reasons = list(rubric_res.classification_reasons)
        all_reasons.extend(policy_res.resolution_reasons)

        final_category = policy_res.final_category

        # Step 5: Post-classification Obligation Evaluation
        obligation_res = self.obligation_evaluator.evaluate(
            final_category=final_category,
            operation=request,
        )

        # Step 6: AI Model Risk Advisor & Justification Analysis
        ai_assessment = None
        if include_ai:
            ai_assessment = self.ai_advisor.analyze(request, rule_category=final_category.value)

        # Step 7: Persist evaluation audit log if DB is available
        if self.db:
            audit_record = RiskEvaluationModel(
                operation_id=request.operationId,
                operation_type=request.operationType,
                scope=request.scope.value,
                reversibility=request.reversibility.value,
                persistence=request.persistence.value,
                payload=request.payload,
                risk_score=rubric_res.risk_score,
                base_category=rubric_res.base_category.value,
                rubric_category=rubric_res.rubric_category.value,
                final_category=final_category.value,
                matched_rules=rubric_res.matched_rules,
                override_applied=policy_res.override_applied,
                override_category=policy_res.override_category,
                override_reason=policy_res.override_reason,
                classification_reasons=all_reasons,
                required_obligations=obligation_res.required_obligations,
                obligations_satisfied=obligation_res.obligations_satisfied,
                missing_obligations=obligation_res.missing_obligations,
                evaluated_at=now,
            )
            self.db.add(audit_record)
            self.db.commit()

        # Step 8: Build explainable response
        return RiskEvaluationResponse(
            operationId=request.operationId,
            riskScore=rubric_res.risk_score,
            baseCategory=rubric_res.base_category.value,
            rubricCategory=rubric_res.rubric_category.value,
            finalCategory=final_category.value,
            matchedRules=rubric_res.matched_rules,
            overrideApplied=policy_res.override_applied,
            overrideCategory=policy_res.override_category,
            overrideReason=policy_res.override_reason,
            classificationReasons=all_reasons,
            requiredObligations=obligation_res.required_obligations,
            obligationsSatisfied=obligation_res.obligations_satisfied,
            missingObligations=obligation_res.missing_obligations,
            aiAssessment=ai_assessment,
            evaluatedAt=now,
        )
