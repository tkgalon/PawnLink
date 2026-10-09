"""Lexical features computed from a raw URL string.

This module is the single source of truth for features: training applies
`extract_features` to every row, and the API calls it on each request.
"""

import ipaddress
import math
from collections import Counter
from urllib.parse import urlsplit

import tldextract

# Use the Public Suffix List bundled with the installed tldextract version
# instead of downloading the latest one, so features are identical in
# training, CI, and serving, and no network call happens per process.
_tld_extract = tldextract.TLDExtract(suffix_list_urls=())

POPULAR_TLDS = frozenset(
    {"com", "org", "net", "edu", "gov", "io", "co", "uk", "de", "jp", "id", "co.id"}
)


def _split(url: str):
    """Parse a URL, assuming http:// when the scheme is missing."""
    if "://" not in url:
        url = "http://" + url
    return urlsplit(url)


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _entropy(text: str) -> float:
    """Shannon entropy of the characters in `text`."""
    if not text:
        return 0.0
    n = len(text)
    return -sum(c / n * math.log2(c / n) for c in Counter(text).values())


def extract_features(url: str) -> dict[str, float]:
    url = url.strip()
    parts = _split(url)
    host = parts.hostname or ""
    domain = _tld_extract(host)

    num_digits = sum(ch.isdigit() for ch in url)
    return {
        "url_length": len(url),
        "num_dots": url.count("."),
        "num_digits": num_digits,
        "pct_digits": num_digits / len(url) if url else 0.0,
        "url_entropy": _entropy(url),
        "has_ip": int(_is_ip(host)),
        "has_https": int(parts.scheme == "https"),
        "host_length": len(host),
        "path_length": len(parts.path),
        "num_query_params": len([p for p in parts.query.split("&") if p]),
        "has_hyphen_in_host": int("-" in host),
        "domain_length": len(domain.domain),
        "tld_length": len(domain.suffix),
        "subdomain_count": len(domain.subdomain.split(".")) if domain.subdomain else 0,
        "is_popular_tld": int(domain.suffix in POPULAR_TLDS),
    }
