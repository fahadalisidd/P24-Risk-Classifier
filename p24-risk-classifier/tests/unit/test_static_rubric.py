"""Unit tests for Static Rubric scoring engine."""
import pytest
from app.classifier.static_rubric import StaticRubric, StaticRubricWeights
from app.domain.enums import Scope, Reversibility, Persistence, RiskCategory


class TestStaticRubric:
    @pytest.fixture
    def rubric(self):
        return StaticRubric()

    def test_lowest_possible_risk(self, rubric):
        # 1 * 1 * 1 = 1 -> Category 1 (LOW)
        score, cat, reasons = rubric.evaluate(
            Scope.LOCAL, Reversibility.REVERSIBLE, Persistence.TEMPORARY
        )
        assert score == 1
        assert cat == RiskCategory.LOW
        assert len(reasons) >= 2

    def test_category_2_scoring(self, rubric):
        # TEAM (2) * PARTIALLY_REVERSIBLE (2) * LONG_TERM (2) = 8 -> Category 2 (MEDIUM)
        score, cat, _ = rubric.evaluate(
            Scope.TEAM, Reversibility.PARTIALLY_REVERSIBLE, Persistence.LONG_TERM
        )
        assert score == 8
        assert cat == RiskCategory.MEDIUM

    def test_category_3_scoring(self, rubric):
        # GLOBAL (4) * REVERSIBLE (1) * PERMANENT (4) = 16 -> Category 3 (HIGH)
        score, cat, _ = rubric.evaluate(
            Scope.GLOBAL, Reversibility.REVERSIBLE, Persistence.PERMANENT
        )
        assert score == 16
        assert cat == RiskCategory.HIGH

    def test_category_4_highest_risk(self, rubric):
        # GLOBAL (4) * IRREVERSIBLE (4) * PERMANENT (4) = 64 -> Category 4 (CRITICAL)
        score, cat, reasons = rubric.evaluate(
            Scope.GLOBAL, Reversibility.IRREVERSIBLE, Persistence.PERMANENT
        )
        assert score == 64
        assert cat == RiskCategory.CRITICAL
        assert "Base Category 4" in reasons[1]

    def test_boundary_values(self, rubric):
        assert rubric.map_score_to_category(1) == RiskCategory.LOW
        assert rubric.map_score_to_category(6) == RiskCategory.LOW
        assert rubric.map_score_to_category(7) == RiskCategory.MEDIUM
        assert rubric.map_score_to_category(11) == RiskCategory.MEDIUM
        assert rubric.map_score_to_category(12) == RiskCategory.HIGH
        assert rubric.map_score_to_category(16) == RiskCategory.HIGH
        assert rubric.map_score_to_category(17) == RiskCategory.CRITICAL
        assert rubric.map_score_to_category(64) == RiskCategory.CRITICAL

    def test_custom_weights(self):
        custom_weights = StaticRubricWeights(
            scope_weights={Scope.LOCAL: 10, Scope.TEAM: 20, Scope.ORGANIZATION: 30, Scope.GLOBAL: 40}
        )
        custom_rubric = StaticRubric(weights=custom_weights)
        score, cat, _ = custom_rubric.evaluate(
            Scope.LOCAL, Reversibility.REVERSIBLE, Persistence.TEMPORARY
        )
        assert score == 10
        assert cat == RiskCategory.MEDIUM
