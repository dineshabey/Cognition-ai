"""Cache package for the wiki-category-wordfreq script."""

from .cache import DEFAULT_CACHE_DIR, Cache, make_cache

__all__ = ["Cache", "DEFAULT_CACHE_DIR", "make_cache"]
