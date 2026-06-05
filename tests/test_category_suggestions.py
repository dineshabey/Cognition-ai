"""Tests for category name autocomplete."""

from unittest.mock import patch

from category_wordfreq import POPULAR_CATEGORIES, search_category_suggestions


@patch("category_wordfreq.api_get")
def test_search_short_query_returns_popular(mock_api_get):
    results = search_category_suggestions("", limit=5)
    assert results == list(POPULAR_CATEGORIES[:5])
    mock_api_get.assert_not_called()


@patch("category_wordfreq.api_get")
def test_search_filters_popular_before_api(mock_api_get):
    mock_api_get.return_value = {
        "query": {
            "allcategories": [
                {"*": "Machine learning researchers"},
                {"*": "Machine learning algorithms"},
            ]
        }
    }
    results = search_category_suggestions("machine", limit=10)
    assert "Machine learning" in results
    assert "Machine learning researchers" in results
    mock_api_get.assert_called_once()
    assert mock_api_get.call_args[0][0]["acprefix"] == "machine"


@patch("category_wordfreq.api_get")
def test_search_dedupes_results(mock_api_get):
    mock_api_get.return_value = {
        "query": {
            "allcategories": [
                {"*": "Machine learning"},
                {"*": "Machine learning"},
            ]
        }
    }
    results = search_category_suggestions("machine", limit=10)
    assert results.count("Machine learning") == 1
