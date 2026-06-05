"""Flask web app: word cloud from Wikipedia category word frequencies."""

import os

from flask import Flask, jsonify, render_template, request

from cache import DEFAULT_CACHE_DIR, Cache
from category_wordfreq import (
    POPULAR_CATEGORIES,
    count_words,
    get_category_members,
    search_category_suggestions,
)
from templates.color_palette import get_all_palettes, get_palette

app = Flask(__name__)


def _normalize_category(name):
    return name.replace("_", " ").strip()


def _results_cache_key(category, namespace, min_length):
    if category.lower().startswith("category:"):
        cmtitle = category
    else:
        cmtitle = "Category:" + category
    return "{}|ns={}|min={}".format(cmtitle, namespace, min_length)


def compute_frequencies(
    category,
    *,
    namespace=0,
    min_length=2,
    top=150,
    delay=0.1,
    cache_dir=None,
    refresh=False,
    no_cache=False,
):
    """Return frequency data, using results cache when available."""
    category = _normalize_category(category)
    if not category:
        raise ValueError("Category name is required.")

    cache = Cache(
        cache_dir=cache_dir or DEFAULT_CACHE_DIR,
        enabled=not no_cache,
        refresh=refresh,
    )
    result_key = _results_cache_key(category, namespace, min_length)

    if cache.enabled and not refresh:
        cached = cache.get("results", result_key)
        if cached is not None:
            words = cached.get("words", [])
            if top and top > 0:
                words = words[:top]
            return {
                "category": category,
                "pages_analyzed": cached.get("pages_analyzed", 0),
                "total_occurrences": cached.get("total_occurrences", 0),
                "unique_words": cached.get("unique_words", 0),
                "words": words,
                "source": "results_cache",
            }

    titles = get_category_members(category, namespace=namespace, cache=cache)
    if not titles:
        raise LookupError(
            "No pages found in category '{}'. Check the spelling.".format(category)
        )

    if cache.enabled:
        pages_cached = sum(1 for t in titles if cache.get("pages", t) is not None)
        if pages_cached == len(titles):
            retrieval = "retrieval_cache"
        elif pages_cached == 0:
            retrieval = "api"
        else:
            retrieval = "mixed"
    else:
        retrieval = "api"

    counter = count_words(
        titles,
        min_length=min_length,
        delay=delay,
        verbose=False,
        cache=cache,
    )

    all_words = [{"word": w, "count": c} for w, c in counter.most_common()]
    total_occurrences = sum(counter.values())
    unique_words = len(counter)

    if cache.enabled:
        cache.set(
            "results",
            result_key,
            {
                "category": category,
                "pages_analyzed": len(titles),
                "total_occurrences": total_occurrences,
                "unique_words": unique_words,
                "words": all_words,
            },
        )

    display_words = all_words if not top or top <= 0 else all_words[:top]

    return {
        "category": category,
        "pages_analyzed": len(titles),
        "total_occurrences": total_occurrences,
        "unique_words": unique_words,
        "words": display_words,
        "source": "computed",
        "retrieval": retrieval,
    }


@app.route("/")
def index():
    return render_template(
        "index.html",
        palettes=get_all_palettes(),
        default_palette="midnight",
        popular_categories=POPULAR_CATEGORIES,
    )


@app.route("/api/category-suggestions")
def api_category_suggestions():
    query = request.args.get("q", "").strip()
    try:
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({"error": "Invalid limit parameter"}), 400

    try:
        suggestions = search_category_suggestions(query, limit=limit)
        return jsonify({"query": query, "suggestions": suggestions})
    except Exception as exc:
        return jsonify(
            {"error": "Failed to fetch suggestions: {}".format(exc)}
        ), 500


@app.route("/api/palettes")
def api_palettes():
    return jsonify({"palettes": get_all_palettes()})


@app.route("/api/palettes/<name>")
def api_palette(name):
    try:
        palette = get_palette(name)
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify(
        {"name": palette.name, "colors": palette.as_list()}
    )


@app.route("/api/frequencies")
def api_frequencies():
    category = request.args.get("category", "").strip()
    if not category:
        return jsonify({"error": "Missing required parameter: category"}), 400

    try:
        top = int(request.args.get("top", 150))
        min_length = int(request.args.get("min_length", 2))
        namespace = int(request.args.get("namespace", 0))
        delay = float(request.args.get("delay", 0.1))
    except ValueError:
        return jsonify({"error": "Invalid numeric parameter"}), 400

    refresh = request.args.get("refresh", "").lower() in ("1", "true", "yes")
    no_cache = request.args.get("no_cache", "").lower() in ("1", "true", "yes")
    cache_dir = request.args.get("cache_dir") or None

    try:
        data = compute_frequencies(
            category,
            namespace=namespace,
            min_length=min_length,
            top=top,
            delay=delay,
            cache_dir=cache_dir,
            refresh=refresh,
            no_cache=no_cache,
        )
        return jsonify(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": "Failed to compute frequencies: {}".format(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
