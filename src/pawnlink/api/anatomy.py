import re

import tldextract

# Same offline suffix list as the features, so the parts match what the model saw.
_tld_extract = tldextract.TLDExtract(suffix_list_urls=())
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def url_parts(url: str) -> list[dict]:
    """Split a URL into labelled pieces that join back into the exact input.

    Kinds: scheme, userinfo, subdomain, domain, TLD, host, port, path, query, fragment.
    """
    parts = []
    rest = url
    if m := _SCHEME.match(rest):
        parts.append((m.group(), "scheme"))
        rest = rest[m.end() :]

    host_end = min((i for i in (rest.find(c) for c in "/?#") if i != -1), default=len(rest))
    hostport, tail = rest[:host_end], rest[host_end:]

    if "@" in hostport:
        userinfo, hostport = hostport.rsplit("@", 1)
        parts.append((userinfo + "@", "userinfo"))
    host, port = hostport, ""
    if not host.startswith("[") and host.count(":") == 1:
        host, port = host.split(":")
        port = ":" + port
    parts += _host_parts(host)
    if port:
        parts.append((port, "port"))

    fragment_at = tail.find("#")
    fragment = tail[fragment_at:] if fragment_at != -1 else ""
    tail = tail[:fragment_at] if fragment_at != -1 else tail
    query_at = tail.find("?")
    path, query = (tail[:query_at], tail[query_at:]) if query_at != -1 else (tail, "")
    parts += [(path, "path"), (query, "query"), (fragment, "fragment")]

    return [{"text": text, "kind": kind} for text, kind in parts if text]


def _host_parts(host: str) -> list[tuple[str, str]]:
    ext = _tld_extract(host)
    if not ext.domain or not ext.suffix:
        return [(host, "host")]
    pieces = [(ext.subdomain + ".", "subdomain")] if ext.subdomain else []
    pieces += [(ext.domain, "domain"), ("." + ext.suffix, "TLD")]
    # tldextract lowercases nothing but may normalise odd hosts; fall back if it no longer joins.
    if "".join(text for text, _ in pieces) != host:
        return [(host, "host")]
    return pieces
