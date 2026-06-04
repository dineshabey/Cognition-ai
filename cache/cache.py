"""On-disk JSON cache used by the word-frequency script.

This module lives in the ``cache/`` package so that all cache-related logic is
grouped in one folder, separate from the retrieval/CLI code.
"""

import hashlib
import json
import os

# Default cache lives next to the project (one level up from this package), so
# all cached data is created under the project folder regardless of the current
# working directory.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CACHE_DIR = os.path.join(_PROJECT_ROOT, ".wikicache")


class Cache:
    """A tiny on-disk JSON cache so retrieval is not rerun for the same input.

    Category member lists and page extracts are stored as individual JSON
    files under ``<cache_dir>/categories`` and ``<cache_dir>/pages``. Keys are
    hashed to keep filenames safe regardless of the title's characters.

    When ``enabled`` is False the cache is a no-op (always a miss, never
    writes), which lets callers ignore caching without special-casing it.
    When ``refresh`` is True existing entries are ignored on read but still
    overwritten on write, forcing a re-fetch of fresh data.
    """

    def __init__(self, cache_dir=DEFAULT_CACHE_DIR, enabled=True, refresh=False):
        self.cache_dir = cache_dir
        self.enabled = enabled
        self.refresh = refresh
        if self.enabled:
            os.makedirs(os.path.join(cache_dir, "categories"), exist_ok=True)
            os.makedirs(os.path.join(cache_dir, "pages"), exist_ok=True)

    def _path(self, kind, key):
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return os.path.join(self.cache_dir, kind, digest + ".json")

    def get(self, kind, key):
        """Return the cached payload for ``key`` or None on a miss."""
        if not self.enabled or self.refresh:
            return None
        path = self._path(kind, key)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)["value"]
        except (OSError, ValueError, KeyError):
            return None

    def set(self, kind, key, value):
        """Persist ``value`` for ``key`` (best effort; ignores write errors)."""
        if not self.enabled:
            return
        path = self._path(kind, key)
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump({"key": key, "value": value}, fh)
            os.replace(tmp, path)
        except OSError:
            pass


def make_cache(cache_dir=None, enabled=True, refresh=False):
    """Build a :class:`Cache`, defaulting to :data:`DEFAULT_CACHE_DIR`.

    Convenience factory so callers can create a cache without importing the
    default-directory constant themselves.
    """
    return Cache(
        cache_dir=cache_dir or DEFAULT_CACHE_DIR,
        enabled=enabled,
        refresh=refresh,
    )
