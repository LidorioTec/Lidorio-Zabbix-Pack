"""LT Samba FS - orchestrator com cache TTL por categoria."""

import json
import time

CACHE_FILE = "/tmp/lt_samba_fs.cache.json"


def _read():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _write(cache):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass


def get_cached(key, ttl, fn):
    cache = _read()
    entry = cache.get(key)
    now = time.time()
    if entry and now - entry.get("ts", 0) < ttl:
        return entry["val"]
    val = fn()
    cache[key] = {"ts": now, "val": val}
    _write(cache)
    return val
