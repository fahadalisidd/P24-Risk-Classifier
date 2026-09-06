"""Static Rubric: Scope × Reversibility × Persistence scoring engine."""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from app.domain.enums import Scope, Reversibility, Persistence, RiskCategory
from app.core.config import settings


@dataclass(frozen=True)
class StaticRubricWeights:
    """Configurable weights for each rubric dimension."""

    scope_weights: Dict[Scope, int] = None  # type: ignore
    reversibility_weights: Dict[Reversibility, int] = None  # type: ignore
    persistence_weights: Dict[Persistence, int] = None  # type: ignore

    def __post_init__(self):
        if self.scope_weights is None:
            object.__setattr__(self, 'scope_weights', {
                Scope.LOCAL: 1,
                Scope.TEAM: 2,
                Scope.ORGANIZATION: 3,
                Scope.GLOBAL: 4,
            })
        if self.reversibility_weights is None:
            object.__setattr__(self, 'reversibility_weights', {
                Reversibility.REVERSIBLE: 1,
                Reversibility.PARTIALLY_REVERSIBLE: 2,
                Reversibility.IRREVERSIBLE: 4,
            })
        if self.persistence_weights is None:
            object.__setattr__(self, 'persistence_weights', {
                Persistence.TEMPORARY: 1,
                Persistence.LONG_TERM: 2,
                Persistence.PERMANENT: 4,
            })


class StaticRubric:
    """Evaluates base risk score and maps to deterministic risk category."""

    def __init__(self, weights: StaticRubricWeights = StaticRubricWeights()):
        self.weights = weights

    def calculate_score(
        self, scope: Scope, reversibility: Reversibility, persistence: Persistence
    ) -> int:
        """Calculate score: Scope × Reversibility × Persistence."""
        w_scope = self.weights.scope_weights[scope]
        w_rev = self.weights.reversibility_weights[reversibility]
        w_pers = self.weights.persistence_weights[persistence]
        return w_scope * w_rev * w_pers

    def map_score_to_category(self, score: int) -> RiskCategory:
        """Map score into Category 1..4 based on configured thresholds."""
        if score <= settings.CATEGORY_1_MAX:
            return RiskCategory.LOW
        elif score <= settings.CATEGORY_2_MAX:
            return RiskCategory.MEDIUM
        elif score <= settings.CATEGORY_3_MAX:
            return RiskCategory.HIGH
        else:
            return RiskCategory.CRITICAL

    def evaluate(
        self, scope: Scope, reversibility: Reversibility, persistence: Persistence
    ) -> Tuple[int, RiskCategory, List[str]]:
        """Evaluate static rubric and return (score, category, explanation_lines)."""
        w_scope = self.weights.scope_weights[scope]
        w_rev = self.weights.reversibility_weights[reversibility]
        w_pers = self.weights.persistence_weights[persistence]

        score = w_scope * w_rev * w_pers
        category = self.map_score_to_category(score)

        explanation = [
            f"Static Rubric: Scope {scope.value} ({w_scope}) × Reversibility {reversibility.value} ({w_rev}) × Persistence {persistence.value} ({w_pers}) = Score {score}",
            f"Score {score} mapped to Base Category {category.value} ({category.name})"
        ]

        return score, category, explanation
