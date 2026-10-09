"""Lexical features computed from a raw URL string.

This module is the single source of truth for features: training applies
`extract_features` to every row, and the API calls it on each request.
"""

import ipaddress
import math
import posixpath
import re
from collections import Counter
from urllib.parse import SplitResult, urlsplit

import tldextract

# Use the Public Suffix List bundled with the installed tldextract version
# instead of downloading the latest one, so features are identical in
# training, CI, and serving, and no network call happens per process.
_tld_extract = tldextract.TLDExtract(suffix_list_urls=())

POPULAR_TLDS = frozenset(
    {"com", "org", "net", "edu", "gov", "io", "co", "uk", "de", "jp", "id", "co.id"}
)

# File types that are executed or unpacked on the victim's machine, plus the
# CPU-architecture suffixes used by IoT botnet droppers (e.g. Mirai).
# Chosen from security knowledge, not mined from the training labels.
SUSPICIOUS_EXTENSIONS = frozenset(
    {
        "exe", "scr", "dll", "msi", "bat", "cmd", "ps1", "vbs", "js", "jar",
        "apk", "lnk", "sh", "bin", "elf", "zip", "rar", "7z", "iso",
        "arm", "arm5", "arm6", "arm7", "mips", "mpsl", "x86", "i686",
        "ppc", "m68k", "sh4", "spc",
    }
)  # fmt: skip


_EMPTY_SPLIT = SplitResult("", "", "", "", "")
_PERCENT_ENCODED = re.compile(r"%[0-9A-Fa-f]{2}")


def _split(url: str) -> tuple[SplitResult, bool]:
    """Parse a URL, assuming http:// when the scheme is missing.

    Returns the parts and whether parsing failed (e.g. "http://[abc").
    """
    if "://" not in url:
        url = "http://" + url
    try:
        return urlsplit(url), False
    except ValueError:
        return _EMPTY_SPLIT, True


def _is_malformed(url: str, host: str, parse_failed: bool) -> bool:
    """URLs that no browser would open as typed: unparseable, no host,
    a repeated scheme ("http://http://..."), or a dotless non-IP host."""
    return (
        parse_failed
        or not host
        or url.lower().count("://") > 1
        or ("." not in host and not _is_ip(host) and host != "localhost")
    )


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
    parts, parse_failed = _split(url)
    host = parts.hostname or ""
    domain = _tld_extract(host)
    extension = posixpath.splitext(parts.path)[1].lower().lstrip(".")

    n = len(url)
    num_digits = sum(ch.isdigit() for ch in url)
    num_alpha = sum(ch.isalpha() for ch in url)
    num_special = n - num_digits - num_alpha

    def pct(count: int) -> float:
        return count / n if n else 0.0

    return {
        "url_length": n,
        "num_dots": url.count("."),
        "num_digits": num_digits,
        "pct_digits": pct(num_digits),
        "pct_alpha": pct(num_alpha),
        "num_special": num_special,
        "pct_special": pct(num_special),
        "unique_char_ratio": pct(len(set(url))),
        "num_percent_encoded": len(_PERCENT_ENCODED.findall(url)),
        "url_entropy": _entropy(url),
        "is_malformed": int(_is_malformed(url, host, parse_failed)),
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
        "has_file_extension": int(bool(extension)),
        "has_suspicious_extension": int(extension in SUSPICIOUS_EXTENSIONS),
    }


# Column order of the model's input; training and serving must both use it.
FEATURE_NAMES: tuple[str, ...] = tuple(extract_features(""))
