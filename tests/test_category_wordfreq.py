"""Tests for word-frequency analysis helpers."""

from unittest.mock import patch

import pytest

from category_wordfreq import (
    COMMON_WORDS,
    count_words,
    get_category_members,
    tokenize,
)


def test_tokenize_lowercases_and_extracts_words():
    text = "GPT Models and AI-driven NLP."
    assert tokenize(text) == ["gpt", "models", "and", "ai", "driven", "nlp"]


def test_tokenize_handles_contractions():
    assert tokenize("It's a test") == ["it's", "a", "test"]


@patch("category_wordfreq.api_get")
def test_get_category_members_adds_category_prefix(mock_api_get, cache):
    mock_api_get.return_value = {
        "query": {"categorymembers": [{"title": "Page A"}, {"title": "Page B"}]},
    }
    titles = get_category_members("Test_Category", cache=cache)
    assert titles == ["Page A", "Page B"]
    mock_api_get.assert_called_once()
    assert mock_api_get.call_args[0][0]["cmtitle"] == "Category:Test_Category"


@patch("category_wordfreq.api_get")
def test_get_category_members_uses_cache(mock_api_get, cache):
    cache.set("categories", "Category:Foo|ns=0", ["Cached"])
    titles = get_category_members("Foo", cache=cache)
    assert titles == ["Cached"]
    mock_api_get.assert_not_called()


@patch("category_wordfreq.get_page_extract")
def test_count_words_filters_stop_words_and_short_words(mock_extract, cache):
    mock_extract.side_effect = lambda title, cache=None: {
        "Alpha": "alpha alpha the",
        "Beta": "beta ai",
    }[title]
    counter = count_words(
        ["Alpha", "Beta"],
        min_length=2,
        delay=0,
        verbose=False,
        cache=cache,
    )
    assert counter["alpha"] == 2
    assert counter["beta"] == 1
    assert counter["ai"] == 1
    assert "the" not in counter
    assert "the" in COMMON_WORDS


@patch("category_wordfreq.get_page_extract")
def test_count_words_respects_min_length(mock_extract, cache):
    mock_extract.return_value = "gpt ab x neural"
    counter = count_words(
        ["Page"],
        min_length=3,
        delay=0,
        verbose=False,
        cache=cache,
    )
    assert counter["gpt"] == 1
    assert counter["neural"] == 1
    assert "ab" not in counter
    assert "x" not in counter
