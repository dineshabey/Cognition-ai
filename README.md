# wiki-category-wordfreq

Compute the cumulative frequency of non-common words across every page in a
Wikipedia category, using the [MediaWiki API](https://www.mediawiki.org/wiki/API:Main_page).

The script:

1. Resolves all member pages of the given category (`list=categorymembers`,
   with continuation so categories of any size are fully paged).
2. Fetches each page's plain-text content (`prop=extracts&explaintext=1`).
3. Tokenizes the text, drops a built-in list of common English stop words,
   and accumulates word counts across all pages.
4. Prints the most frequent remaining ("non-common") words.

No third-party dependencies — only the Python 3 standard library.

## Usage

```bash
python3 category_wordfreq.py <Category_Name> [options]
```

The `Category:` prefix is optional and underscores are treated as spaces, so
`Large_language_models`, `Large language models`, and
`Category:Large language models` are equivalent.

### Options

| Option | Default | Description |
| --- | --- | --- |
| `--top N` | `50` | Show the top `N` words (`0` = show all). |
| `--min-length N` | `2` | Ignore words shorter than `N` characters. |
| `--namespace N` | `0` | Category member namespace (`0` = articles). |
| `--delay S` | `0.1` | Delay in seconds between page requests (be polite to the API). |
| `--quiet` | off | Suppress progress output on stderr. |

The script retries automatically with exponential backoff on rate limiting
(HTTP 429) and transient errors, honoring the API's `Retry-After` header.

## Example

```bash
python3 category_wordfreq.py Large_language_models --top 40 --delay 0.3
```

Sample output (top of the list):

```
Category: Large language models
Pages analyzed: 96
Total non-common word occurrences: 61063
Unique non-common words: 9192

 #  WORD          COUNT
 1  model         916
 2  ai            772
 3  models        713
 4  gpt           690
 5  language      518
 ...
```
