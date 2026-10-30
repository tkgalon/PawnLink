"""Usage: uv run python scripts/fetch_legit_urls.py [--domains 1000] [--per-domain 15]

Collects real legitimate URLs that have a path, which the competition data barely has.
Domains come from the Tranco top list; URLs for each domain come from the Common Crawl
CDX index files on data.commoncrawl.org (range requests against cluster.idx blocks; the
index.commoncrawl.org query server times out on large domains). Domains that appear
anywhere in our phishing data are skipped.

Writes data/external/legit_paths.csv (url, domain, rank) and legit_paths.json (sources).
Progress is cached per domain in data/external/cc_cache.jsonl, so a rerun resumes.
"""

import argparse
import bisect
import gzip
import io
import json
import random
import time
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import tldextract

OUT_DIR = Path("data/external")
CACHE = OUT_DIR / "cc_cache.jsonl"
PROCESSED = Path("data/processed")
CRAWL = "CC-MAIN-2026-43"
CC_INDEX = f"https://data.commoncrawl.org/cc-index/collections/{CRAWL}/indexes"
SEED = 42
MAX_URL_LENGTH = 2048

_extract = tldextract.TLDExtract(suffix_list_urls=())


def registered_domain(url: str) -> str:
    return _extract(url).top_domain_under_public_suffix


def get(url: str, retries: int = 4, byte_range: tuple[int, int] | None = None) -> bytes:
    headers = {"User-Agent": "pawnlink-research/0.1"}
    if byte_range:
        headers["Range"] = f"bytes={byte_range[0]}-{byte_range[0] + byte_range[1] - 1}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError:
            time.sleep(5 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError):
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"giving up on {url}")


def tranco_domains() -> tuple[str, list[str]]:
    latest = json.loads(get("https://tranco-list.eu/api/lists/date/latest"))
    list_id = latest["list_id"]
    path = OUT_DIR / f"tranco-{list_id}.csv"
    if not path.exists():
        data = get(latest["download"])
        if data[:2] == b"PK":
            data = zipfile.ZipFile(io.BytesIO(data)).read("top-1m.csv")
        path.write_bytes(data)
    df = pd.read_csv(path, header=None, names=["rank", "domain"])
    return list_id, df["domain"].tolist()


def phishing_domains() -> set[str]:
    urls = pd.concat(pd.read_csv(PROCESSED / f"{s}.csv") for s in ("train", "val", "test"))
    return {registered_domain(u) for u in urls.loc[urls["is_phishing"] == 1, "url"]}


def has_path(url: str) -> bool:
    parts = urllib.parse.urlsplit(url)
    return parts.path.strip("/") != "" or parts.query != ""


class ClusterIndex:
    """cluster.idx: the first SURT key of every ~3000-line block in the cdx-*.gz files."""

    def __init__(self) -> None:
        path = OUT_DIR / f"cluster-{CRAWL}.idx"
        if not path.exists():
            path.write_bytes(get(f"{CC_INDEX}/cluster.idx"))
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


def surt(domain: str) -> str:
    return ",".join(reversed(domain.split(".")))


def fetch_domain(index: ClusterIndex, domain: str, rng: random.Random) -> list[str]:
    key = surt(domain)
    blocks = list(index.block_range(key))
    urls = []
    for i in rng.sample(blocks, min(2, len(blocks))):
        file, offset, length = index.blocks[i]
        for line in (
            gzip.decompress(get(f"{CC_INDEX}/{file}", byte_range=(offset, length)))
            .decode(errors="replace")
            .splitlines()
        ):
            line_key, _, payload = line.split(" ", 2)
            if not (line_key.startswith(key + ")") or line_key.startswith(key + ",")):
                continue
            rec = json.loads(payload)
            if rec.get("status") == "200" and rec.get("mime") == "text/html":
                urls.append(rec["url"])
    return urls


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", type=int, default=1000, help="how many usable domains")
    parser.add_argument("--per-domain", type=int, default=15)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    list_id, ranked = tranco_domains()
    skip = phishing_domains()
    candidates = [(rank, d) for rank, d in enumerate(ranked, 1) if d not in skip][: args.domains]
    print(f"Tranco {list_id}: {len(skip)} phishing domains skipped, {len(candidates)} to query")

    done = {}
    if CACHE.exists():
        for line in CACHE.read_text().splitlines():
            rec = json.loads(line)
            done[rec["domain"]] = rec["urls"]
    todo = [(rank, d) for rank, d in candidates if d not in done]
    print(f"{len(done)} cached, {len(todo)} left")

    index = ClusterIndex()
    with CACHE.open("a") as cache, ThreadPoolExecutor(args.workers) as pool:
        futures = {
            pool.submit(fetch_domain, index, d, random.Random(f"{SEED}-{d}")): d for _, d in todo
        }
        for i, fut in enumerate(as_completed(futures), 1):
            domain = futures[fut]
            try:
                urls = fut.result()
            except RuntimeError as e:
                print(f"  skip {domain}: {e}")
                continue
            done[domain] = urls
            cache.write(json.dumps({"domain": domain, "urls": urls}) + "\n")
            cache.flush()
            if i % 50 == 0:
                print(f"  {i}/{len(todo)} domains queried")

    rng = random.Random(SEED)
    rows = []
    for rank, domain in candidates:
        urls = sorted(
            {
                u
                for u in done.get(domain, [])
                if has_path(u) and len(u) <= MAX_URL_LENGTH and registered_domain(u) == domain
            }
        )
        for u in rng.sample(urls, min(args.per_domain, len(urls))):
            rows.append({"url": u, "domain": domain, "rank": rank})

    out = pd.DataFrame(rows).drop_duplicates("url")
    out.to_csv(OUT_DIR / "legit_paths.csv", index=False)
    meta = {
        "tranco_list_id": list_id,
        "common_crawl": CRAWL,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "domains_queried": len(candidates),
        "domains_with_urls": int(out["domain"].nunique()),
        "urls": len(out),
    }
    (OUT_DIR / "legit_paths.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
