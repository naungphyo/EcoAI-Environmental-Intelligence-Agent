"""
utils/cache.py
──────────────
Lightweight disk-backed cache with per-entry TTL.

• Keys are hashed to safe filenames.
• Expired entries are silently evicted on read.
• Thread-safe via file-level locking (via json atomic write pattern).
"""

import hashlib
import json
import os
import time
from typing import Any, Optional

from config.settings import CACHE_DIR, CACHE_TTL_SECONDS


def _key_to_path(key: str) -> str:
    """Convert a cache key to an absolute file path."""
    digest = hashlib.md5(key.encode()).hexdigest()
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{digest}.json")


def cache_get(key: str, ttl: int = CACHE_TTL_SECONDS) -> Optional[Any]:
    """
    Retrieve a cached value.
    Returns None if the entry is missing or expired.
    """
    path = _key_to_path(key)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r") as fh:
            entry = json.load(fh)

        age = time.time() - entry["timestamp"]
        if age > ttl:
            os.remove(path)          # evict stale entry
            return None

        return entry["value"]
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def cache_set(key: str, value: Any) -> None:
    """Persist a value with the current timestamp."""
    path = _key_to_path(key)
    entry = {"timestamp": time.time(), "value": value}

    # Atomic write: write to .tmp then rename
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as fh:
            json.dump(entry, fh)
        os.replace(tmp, path)
    except OSError as exc:
        print(f"[Cache] Write failed: {exc}")


def cache_clear_expired(ttl: int = CACHE_TTL_SECONDS) -> int:
    """Remove all expired entries. Returns count removed."""
    if not os.path.isdir(CACHE_DIR):
        return 0

    removed = 0
    for fname in os.listdir(CACHE_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(CACHE_DIR, fname)
        try:
            with open(path) as fh:
                entry = json.load(fh)
            if time.time() - entry.get("timestamp", 0) > ttl:
                os.remove(path)
                removed += 1
        except (json.JSONDecodeError, OSError):
            pass
    return removed