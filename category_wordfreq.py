#!/usr/bin/env python3
"""Compute cumulative frequency of non-common words across all pages in a
Wikipedia category, using the MediaWiki API.

Usage:
    python category_wordfreq.py <Category_Name> [options]

Example:
    python category_wordfreq.py Large_language_models --top 40
"""

import argparse
import re
import sys
import time
from collections import Counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json

from cache import DEFAULT_CACHE_DIR, Cache

API_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = (
    "category-wordfreq/1.0 (word-frequency analysis script; "
    "contact: aidinabey@gmail.com)"
)

# A compact list of common English "stop" words to exclude. These are the
# high-frequency function words that carry little topical meaning.
COMMON_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't",
    "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers",
    "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its",
    "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no",
    "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd",
    "they'll", "they're", "they've", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll",
    "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why",
    "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves",
    # Additional very common words not in the classic stoplist.
    "also", "may", "many", "one", "two", "three", "first", "second", "new",
    "used", "use", "using", "based", "however", "within", "often", "well",
    "include", "including", "included", "another", "make", "made", "much",
    "see", "etc", "via",
}


def api_get(params, max_retries=5):
    """Perform a GET request against the MediaWiki API and return parsed JSON.

    Retries with exponential backoff on rate limiting (HTTP 429), server
    errors (5xx) and transient network failures, honoring any Retry-After
    header the server sends.
    """
    params = dict(params)
    params["format"] = "json"
    url = API_URL + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": USER_AGENT})

    backoff = 1.0
    for attempt in range(max_retries + 1):
        try:
            with urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    wait = float(retry_after) if retry_after else backoff
                except ValueError:
                    wait = backoff
                print(
                    f"  API returned HTTP {exc.code}; retrying in {wait:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})",
                    file=sys.stderr,
                )
                time.sleep(wait)
                backoff = min(backoff * 2, 60.0)
                continue
            raise
        except URLError as exc:
            if attempt < max_retries:
                print(
                    f"  Network error ({exc.reason}); retrying in {backoff:.1f}s "
                    f"(attempt {attempt + 1}/{max_retries})",
                    file=sys.stderr,
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, 60.0)
                continue
            raise
    raise RuntimeError("Exhausted retries contacting the MediaWiki API")


def get_category_members(category, namespace=0, cache=None):
    """Yield page titles belonging to a category (handling continuation)."""
    if category.lower().startswith("category:"):
        cmtitle = category
    else:
        cmtitle = "Category:" + category

    cache_key = "{}|ns={}".format(cmtitle, namespace)
    if cache is not None:
        cached = cache.get("categories", cache_key)
        if cached is not None:
            return cached

    titles = []
    cont = {}
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cmtitle,
            "cmlimit": "500",
            "cmnamespace": str(namespace),
        }
        params.update(cont)
        data = api_get(params)
        for member in data.get("query", {}).get("categorymembers", []):
            titles.append(member["title"])
        if "continue" in data:
            cont = data["continue"]
        else:
            break
    if cache is not None:
        cache.set("categories", cache_key, titles)
    return titles


def get_page_extract(title, cache=None):
    """Return the plain-text extract of a single page."""
    if cache is not None:
        cached = cache.get("pages", title)
        if cached is not None:
            return cached

    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "redirects": "1",
        "titles": title,
    }
    data = api_get(params)
    pages = data.get("query", {}).get("pages", {})
    extract = ""
    for page in pages.values():
        extract = page.get("extract", "") or ""
        break
    if cache is not None:
        cache.set("pages", title, extract)
    return extract


WORD_RE = re.compile(r"[a-z]+(?:'[a-z]+)?")


def tokenize(text):
    """Lowercase and split text into word tokens."""
    return WORD_RE.findall(text.lower())


def count_words(titles, min_length=2, delay=0.1, verbose=True, cache=None):
    """Accumulate non-common word frequencies across all given page titles."""
    counter = Counter()
    total = len(titles)
    for i, title in enumerate(titles, 1):
        cached = cache is not None and cache.get("pages", title) is not None
        if verbose:
            status = "cached" if cached else "fetching"
            print(f"[{i}/{total}] {status}: {title}", file=sys.stderr)
        text = get_page_extract(title, cache=cache)
        for word in tokenize(text):
            if len(word) < min_length:
                continue
            if word in COMMON_WORDS:
                continue
            counter[word] += 1
        if delay and not cached:
            time.sleep(delay)
    return counter


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Cumulative frequency of non-common words across all pages "
        "in a Wikipedia category (via the MediaWiki API)."
    )
    parser.add_argument(
        "category",
        help="Wikipedia category name, e.g. Large_language_models "
        "(the 'Category:' prefix is optional).",
    )
    parser.add_argument(
        "--top", type=int, default=50,
        help="Number of top words to display (default: 50; use 0 for all).",
    )
    parser.add_argument(
        "--min-length", type=int, default=2,
        help="Ignore words shorter than this length (default: 2).",
    )
    parser.add_argument(
        "--namespace", type=int, default=0,
        help="Category member namespace to include (default: 0 = articles).",
    )
    parser.add_argument(
        "--delay", type=float, default=0.1,
        help="Delay in seconds between page requests (default: 0.1).",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress progress output on stderr.",
    )
    parser.add_argument(
        "--cache-dir", default=DEFAULT_CACHE_DIR,
        help="Directory for the local retrieval cache "
        "(default: a '.wikicache' folder next to this script).",
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Disable the local cache (always fetch from the API).",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Ignore cached data and re-fetch, overwriting the cache.",
    )
    args = parser.parse_args(argv)

    cache = Cache(
        cache_dir=args.cache_dir,
        enabled=not args.no_cache,
        refresh=args.refresh,
    )

    category = args.category.replace("_", " ")
    if not args.quiet:
        print(f"Fetching members of category: {category}", file=sys.stderr)

    titles = get_category_members(
        category, namespace=args.namespace, cache=cache
    )
    if not titles:
        print(
            f"No pages found in category '{category}'. "
            "Check the spelling or try another category.",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(f"Found {len(titles)} pages.", file=sys.stderr)

    counter = count_words(
        titles,
        min_length=args.min_length,
        delay=args.delay,
        verbose=not args.quiet,
        cache=cache,
    )

    total_tokens = sum(counter.values())
    unique_words = len(counter)

    print()
    print(f"Category: {category}")
    print(f"Pages analyzed: {len(titles)}")
    print(f"Total non-common word occurrences: {total_tokens}")
    print(f"Unique non-common words: {unique_words}")
    print()

    items = counter.most_common(None if args.top == 0 else args.top)
    rank_width = len(str(len(items)))
    word_width = max((len(w) for w, _ in items), default=4)
    print(f"{'#'.rjust(rank_width)}  {'WORD'.ljust(word_width)}  COUNT")
    for rank, (word, count) in enumerate(items, 1):
        print(f"{str(rank).rjust(rank_width)}  {word.ljust(word_width)}  {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
