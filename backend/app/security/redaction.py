"""Log redaction applied by a logging filter, never by call sites (SEC-R-006)."""

from __future__ import annotations

import logging
import re

_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)\b(api[_-]?key|apikey|token|secret|password|passwd|bearer|authorization)\b\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\bsk-[A-Za-z0-9]{16,}\b"), "[REDACTED_KEY]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}\b"), "[REDACTED_BLOB]"),
)


def redact(message: str) -> str:
    for pattern, replacement in _PATTERNS:
        message = pattern.sub(replacement, message)
    return message


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.msg))
        if record.args:
            record.args = tuple(redact(str(a)) for a in record.args)
        return True
