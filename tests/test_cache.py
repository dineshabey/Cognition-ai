"""Tests for the on-disk cache."""

from cache import Cache, make_cache


def test_get_miss_returns_none(cache):
    assert cache.get("pages", "Missing Page") is None


def test_set_and_get_round_trip(cache):
    cache.set("pages", "Example Page", "hello world")
    assert cache.get("pages", "Example Page") == "hello world"


def test_disabled_cache_is_no_op(tmp_cache_dir):
    c = Cache(cache_dir=tmp_cache_dir, enabled=False)
    c.set("pages", "Page", "text")
    assert c.get("pages", "Page") is None


def test_refresh_ignores_reads_but_writes(cache):
    cache.set("pages", "Stale", "old")
    c = Cache(cache_dir=cache.cache_dir, enabled=True, refresh=True)
    assert c.get("pages", "Stale") is None
    c.set("pages", "Stale", "new")
    c2 = Cache(cache_dir=cache.cache_dir, enabled=True, refresh=False)
    assert c2.get("pages", "Stale") == "new"


def test_results_kind_persisted(cache):
    payload = {"words": [{"word": "x", "count": 1}]}
    cache.set("results", "Category:Foo|ns=0|min=2", payload)
    assert cache.get("results", "Category:Foo|ns=0|min=2") == payload


def test_make_cache_uses_tmp_dir(tmp_cache_dir):
    c = make_cache(cache_dir=tmp_cache_dir)
    assert c.cache_dir == tmp_cache_dir
    assert c.enabled is True
