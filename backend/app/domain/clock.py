"""Time is always injected (ARCH-R-008)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


class ClockPort(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    """The only place in the codebase permitted to read the wall clock."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    """Deterministic clock for tests and reproducible demo seeding."""

    def __init__(self, fixed: datetime) -> None:
        if fixed.tzinfo is None:
            raise ValueError("FrozenClock requires a timezone-aware datetime")
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed

    def advance(self, **delta: float) -> None:
        from datetime import timedelta

        self._fixed = self._fixed + timedelta(**delta)
