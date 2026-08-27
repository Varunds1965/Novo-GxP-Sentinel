"""Canonical hashing used by the audit chain and every provenance record."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

ZERO_HASH = "0" * 64


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def _default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone().isoformat()
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, (set, frozenset, tuple)):
        return list(value)
    raise TypeError(f"cannot canonicalise {type(value)!r}")


def canonical_json(payload: dict[str, Any]) -> str:
    """Stable canonicalisation: sorted keys, no whitespace, UTF-8 (SEC-R-041)."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_default,
    )


def chain_hash(event_without_hash: dict[str, Any], previous_hash: str) -> str:
    return sha256_text(canonical_json(event_without_hash) + previous_hash)
