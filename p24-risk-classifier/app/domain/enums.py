"""Domain enumeration definitions."""
from enum import Enum, IntEnum


class Scope(str, Enum):
    """Scope dimension for risk evaluation."""
    LOCAL = "LOCAL"
    TEAM = "TEAM"
    ORGANIZATION = "ORGANIZATION"
    GLOBAL = "GLOBAL"


class Reversibility(str, Enum):
    """Reversibility dimension for risk evaluation."""
    REVERSIBLE = "REVERSIBLE"
    PARTIALLY_REVERSIBLE = "PARTIALLY_REVERSIBLE"
    IRREVERSIBLE = "IRREVERSIBLE"


class Persistence(str, Enum):
    """Persistence dimension for risk evaluation."""
    TEMPORARY = "TEMPORARY"
    LONG_TERM = "LONG_TERM"
    PERMANENT = "PERMANENT"


class RiskCategory(IntEnum):
    """Four distinct risk categories."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def label(self) -> str:
        return self.name

    @classmethod
    def from_value(cls, val: int) -> "RiskCategory":
        for cat in cls:
            if cat.value == val:
                return cat
        raise ValueError(f"Invalid RiskCategory value: {val}. Must be 1, 2, 3, or 4.")


class PinStatus(str, Enum):
    """Status lifecycle of a policy pin."""
    ACTIVE = "ACTIVE"
    REVIEW_OVERDUE = "REVIEW_OVERDUE"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"


class ReviewStatus(str, Enum):
    """Outcome of reviewer scoring comparisons."""
    PENDING_SECOND_REVIEW = "PENDING_SECOND_REVIEW"
    AGREEMENT = "AGREEMENT"
    DISAGREEMENT = "DISAGREEMENT"


class RuleAction(str, Enum):
    """Action taken when dynamic rubric rule matches."""
    SET_MIN_CATEGORY = "SET_MIN_CATEGORY"
    ESCALATE_TO = "ESCALATE_TO"
    SET_EXACT_CATEGORY = "SET_EXACT_CATEGORY"
