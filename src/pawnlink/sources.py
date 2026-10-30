import bisect
import contextlib
import gzip
import io
import json
import random
import re
import time
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import tldextract

MAX_URL_LENGTH = 2048
OPENPHISH_FEED = "https://openphish.com/feed.txt"

_extract = tldextract.TLDExtract(suffix_list_urls=())


def registered_domain(url: str) -> str:
    return _extract(url).top_domain_under_public_suffix


def has_path(url: str) -> bool:
    parts = urllib.parse.urlsplit(url)
    return parts.path.strip("/") != "" or parts.query != ""


def get(url: str, retries: int = 4, byte_range: tuple[int, int] | None = None) -> bytes:
    headers = {"User-Agent": "pawnlink-research/0.1"}
    if byte_range:
        headers["Range"] = f"bytes={byte_range[0]}-{byte_range[0] + byte_range[1] - 1}"
    error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as e:
            error = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"giving up on {url}: {error}")


def openphish_urls() -> list[str]:
    # Community feed: the phishing URLs active right now. Free for non-commercial use.
    lines = get(OPENPHISH_FEED).decode(errors="replace").splitlines()
    return [u.strip() for u in lines if u.strip().startswith(("http://", "https://"))]


def tranco_domains(cache_dir: Path) -> tuple[str, list[str]]:
    latest = json.loads(get("https://tranco-list.eu/api/lists/date/latest"))
    list_id = latest["list_id"]
    path = cache_dir / f"tranco-{list_id}.csv"
    if not path.exists():
        data = get(latest["download"])
        if data[:2] == b"PK":
            data = zipfile.ZipFile(io.BytesIO(data)).read("top-1m.csv")
        path.write_bytes(data)
    domains = [line.split(",", 1)[1] for line in path.read_text().splitlines() if "," in line]
    return list_id, domains


def latest_crawl() -> str:
    # The CDN copy of the crawl list; index.commoncrawl.org refuses requests from Cloud Run.
    page = get("https://data.commoncrawl.org/cc-index/collections/index.html").decode()
    return max(re.findall(r"CC-MAIN-\d{4}-\d{2}", page))


class ClusterIndex:
    """cluster.idx: the first SURT key of every ~3000-line block in a crawl's cdx-*.gz files.

    Reads the index files on data.commoncrawl.org with range requests; the
    index.commoncrawl.org query server times out on large domains.
    """

    def __init__(self, crawl: str, cache_dir: Path) -> None:
        self.base = f"https://data.commoncrawl.org/cc-index/collections/{crawl}/indexes"
        path = cache_dir / f"cluster-{crawl}.idx"
        if not path.exists():
            path.write_bytes(get(f"{self.base}/cluster.idx"))
        self.keys, self.blocks = [], []
        for line in path.read_text().splitlines():
            key, file, offset, length, _ = line.split("\t")
            self.keys.append(key)
            self.blocks.append((file, int(offset), int(length)))

    def block_range(self, surt_domain: str) -> range:
        # A domain's captures sort between "com,example)" and "com,example,~" (subdomains).
        first = max(bisect.bisect_right(self.keys, surt_domain + ")") - 1, 0)
        last = max(bisect.bisect_right(self.keys, surt_domain + ",~") - 1, 0)
        return range(first, last + 1)

    def html_urls(self, domain: str, rng: random.Random) -> list[str]:
        key = ",".join(reversed(domain.split(".")))
        blocks = list(self.block_range(key))
        urls = []
        for i in rng.sample(blocks, min(2, len(blocks))):
            file, offset, length = self.blocks[i]
            data = get(f"{self.base}/{file}", byte_range=(offset, length))
            for line in gzip.decompress(data).decode(errors="replace").splitlines():
                line_key, _, payload = line.split(" ", 2)
                if not (line_key.startswith(key + ")") or line_key.startswith(key + ",")):
                    continue
                rec = json.loads(payload)
                if rec.get("status") == "200" and rec.get("mime") == "text/html":
                    urls.append(rec["url"])
        return urls


def legit_urls_with_paths(
    index: ClusterIndex, domains: list[str], per_domain: int, seed: int, workers: int = 8
) -> list[tuple[str, str]]:
    """Up to per_domain (url, domain) pairs per domain, URLs with a path only."""
    found = {}
    with ThreadPoolExecutor(workers) as pool:
        futures = {
            pool.submit(index.html_urls, d, random.Random(f"{seed}-{d}")): d for d in domains
        }
        for fut in as_completed(futures):
            # A domain the CDN keeps failing on is skipped, not fatal.
            with contextlib.suppress(RuntimeError):
                found[futures[fut]] = fut.result()
    rng = random.Random(seed)
    pairs = []
    for domain in domains:
        urls = sorted(
            {
                u
                for u in found.get(domain, [])
                if has_path(u) and len(u) <= MAX_URL_LENGTH and registered_domain(u) == domain
            }
        )
        pairs += [(u, domain) for u in rng.sample(urls, min(per_domain, len(urls)))]
    return pairs
