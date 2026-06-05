"""Shared pytest fixtures."""

import pytest

from cache import Cache


@pytest.fixture
def tmp_cache_dir(tmp_path):
    return str(tmp_path / "wikicache")


@pytest.fixture
def cache(tmp_cache_dir):
    return Cache(cache_dir=tmp_cache_dir, enabled=True)


@pytest.fixture
def sample_results_payload():
    return {
        "category": "Test category",
        "pages_analyzed": 2,
        "total_occurrences": 5,
        "unique_words": 3,
        "words": [
            {"word": "alpha", "count": 3},
            {"word": "beta", "count": 1},
            {"word": "gamma", "count": 1},
        ],
    }
