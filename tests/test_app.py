"""Tests for the Flask web app."""

from unittest.mock import patch

import pytest

from app import (
    _normalize_category,
    _results_cache_key,
    app,
    compute_frequencies,
)
from cache import Cache


@pytest.fixture
def client():
    return app.test_client()


def test_normalize_category():
    assert _normalize_category("  Foo_Bar  ") == "Foo Bar"


def test_results_cache_key():
    assert _results_cache_key("Test", 0, 2) == "Category:Test|ns=0|min=2"
    assert _results_cache_key("Category:Test", 1, 3) == "Category:Test|ns=1|min=3"


def test_compute_frequencies_empty_category_raises():
    with pytest.raises(ValueError, match="required"):
        compute_frequencies("   ", no_cache=True)


def test_compute_frequencies_returns_results_cache(
    tmp_cache_dir, sample_results_payload
):
    cache = Cache(cache_dir=tmp_cache_dir)
    key = _results_cache_key("Test category", 0, 2)
    cache.set("results", key, sample_results_payload)

    data = compute_frequencies(
        "Test category",
        top=2,
        cache_dir=tmp_cache_dir,
    )
    assert data["source"] == "results_cache"
    assert data["pages_analyzed"] == 2
    assert len(data["words"]) == 2
    assert data["words"][0]["word"] == "alpha"


@patch("app.count_words")
@patch("app.get_category_members")
def test_compute_frequencies_computes_and_caches(
    mock_members, mock_count, tmp_cache_dir
):
    from collections import Counter

    mock_members.return_value = ["Page One"]
    mock_count.return_value = Counter({"neural": 5, "network": 2})

    data = compute_frequencies(
        "ML",
        top=10,
        cache_dir=tmp_cache_dir,
        delay=0,
    )
    assert data["source"] == "computed"
    assert data["retrieval"] == "api"
    assert data["pages_analyzed"] == 1
    assert data["words"][0] == {"word": "neural", "count": 5}

    cache = Cache(cache_dir=tmp_cache_dir)
    key = _results_cache_key("ML", 0, 2)
    cached = cache.get("results", key)
    assert cached is not None
    assert cached["unique_words"] == 2


@patch("app.count_words")
@patch("app.get_category_members")
def test_compute_frequencies_retrieval_cache_label(
    mock_members, mock_count, tmp_cache_dir
):
    from collections import Counter

    cache = Cache(cache_dir=tmp_cache_dir)
    cache.set("pages", "Cached Page", "neural networks")
    mock_members.return_value = ["Cached Page"]
    mock_count.return_value = Counter({"neural": 1})

    data = compute_frequencies("AI", cache_dir=tmp_cache_dir, delay=0)
    assert data["retrieval"] == "retrieval_cache"


@patch("app.get_category_members")
def test_compute_frequencies_empty_category_lookup(mock_members, tmp_cache_dir):
    mock_members.return_value = []
    with pytest.raises(LookupError, match="No pages found"):
        compute_frequencies("Empty", cache_dir=tmp_cache_dir)


def test_index_returns_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Wikipedia Category Word Cloud" in response.data
    assert b'id="palette-input"' in response.data
    assert b"midnight" in response.data
    assert b"palette-preview" in response.data
    assert b'id="category-suggestions"' in response.data
    assert b"role=\"combobox\"" in response.data


@patch("app.search_category_suggestions")
def test_api_category_suggestions(mock_search, client):
    mock_search.return_value = ["Machine learning", "Machine learning researchers"]
    response = client.get("/api/category-suggestions?q=machine")
    assert response.status_code == 200
    body = response.get_json()
    assert body["query"] == "machine"
    assert len(body["suggestions"]) == 2
    mock_search.assert_called_once_with("machine", limit=10)


@patch("app.search_category_suggestions")
def test_api_category_suggestions_popular(mock_search, client):
    mock_search.return_value = ["Large language models"]
    response = client.get("/api/category-suggestions")
    assert response.status_code == 200
    mock_search.assert_called_once_with("", limit=10)


def test_api_palettes(client):
    response = client.get("/api/palettes")
    assert response.status_code == 200
    body = response.get_json()
    names = [p["name"] for p in body["palettes"]]
    assert "ocean" in names
    assert "midnight" in names
    assert len(body["palettes"][0]["colors"]) == 6


def test_api_palette_by_name(client):
    response = client.get("/api/palettes/midnight")
    assert response.status_code == 200
    body = response.get_json()
    assert body["name"] == "midnight"
    assert len(body["colors"]) == 6


def test_api_palette_unknown(client):
    response = client.get("/api/palettes/not-real")
    assert response.status_code == 404


def test_api_frequencies_missing_category(client):
    response = client.get("/api/frequencies")
    assert response.status_code == 400
    assert response.get_json()["error"] == "Missing required parameter: category"


def test_api_frequencies_invalid_top(client):
    response = client.get("/api/frequencies?category=Foo&top=abc")
    assert response.status_code == 400
    assert "Invalid numeric" in response.get_json()["error"]


@patch("app.compute_frequencies")
def test_api_frequencies_success(mock_compute, client):
    mock_compute.return_value = {
        "category": "Foo",
        "pages_analyzed": 1,
        "total_occurrences": 10,
        "unique_words": 5,
        "words": [{"word": "bar", "count": 10}],
        "source": "results_cache",
    }
    response = client.get("/api/frequencies?category=Foo&top=5")
    assert response.status_code == 200
    body = response.get_json()
    assert body["category"] == "Foo"
    assert body["words"][0]["word"] == "bar"
    mock_compute.assert_called_once()


@patch("app.compute_frequencies")
def test_api_frequencies_not_found(mock_compute, client):
    mock_compute.side_effect = LookupError("No pages found in category 'X'.")
    response = client.get("/api/frequencies?category=X")
    assert response.status_code == 404


@patch("app.compute_frequencies")
def test_api_frequencies_passes_refresh_and_no_cache(mock_compute, client):
    mock_compute.return_value = {
        "category": "Foo",
        "pages_analyzed": 0,
        "total_occurrences": 0,
        "unique_words": 0,
        "words": [],
        "source": "computed",
        "retrieval": "api",
    }
    client.get("/api/frequencies?category=Foo&refresh=true&no_cache=1")
    _, kwargs = mock_compute.call_args
    assert kwargs["refresh"] is True
    assert kwargs["no_cache"] is True
