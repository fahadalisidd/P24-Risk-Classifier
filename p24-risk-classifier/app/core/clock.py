"""Clock abstraction for deterministic time handling in tests and production."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional


class Clock(ABC):
    """Abstract clock interface."""

    @abstractmethod
    def now(self) -> datetime:
        """Return current datetime with UTC timezone."""
        raise NotImplementedError


class SystemClock(Clock):
    """Production system clock returning current UTC datetime."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class ControllableClock(Clock):
    """Test clock that can be set or advanced deterministically."""

    def __init__(self, initial_time: Optional[datetime] = None):
        if initial_time is None:
            self._current_time = datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc)
        else:
            if initial_time.tzinfo is None:
                self._current_time = initial_time.replace(tzinfo=timezone.utc)
            else:
                self._current_time = initial_time

    def now(self) -> datetime:
        return self._current_time

    def set_time(self, new_time: datetime) -> None:
        if new_time.tzinfo is None:
            self._current_time = new_time.replace(tzinfo=timezone.utc)
        else:
            self._current_time = new_time

    def advance(self, **kwargs) -> None:
        from datetime import timedelta
        self._current_time += timedelta(**kwargs)


# Global default clock instance (can be overridden in tests/app setup)
_default_clock: Clock = SystemClock()


def get_clock() -> Clock:
    """Retrieve current active clock instance."""
    return _default_clock


def set_global_clock(clock: Clock) -> None:
    """Override global clock instance (useful in tests)."""
    global _default_clock
    _default_clock = clock
