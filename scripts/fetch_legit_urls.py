import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from pawnlink.sources import ClusterIndex, legit_urls_with_paths, registered_domain, tranco_domains

OUT_DIR = Path("data/external")
PROCESSED = Path("data/processed")
# Pinned so a rerun samples the same crawl the v4 training data came from.
CRAWL = "CC-MAIN-2026-43"
SEED = 42


def phishing_domains() -> set[str]:
    urls = pd.concat(pd.read_csv(PROCESSED / f"{s}.csv") for s in ("train", "val", "test"))
    return {registered_domain(u) for u in urls.loc[urls["is_phishing"] == 1, "url"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", type=int, default=1000)
    parser.add_argument("--per-domain", type=int, default=15)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    list_id, ranked = tranco_domains(OUT_DIR)
    skip = phishing_domains()
    domains = [d for d in ranked if d not in skip][: args.domains]
    print(f"Tranco {list_id}: {len(skip)} phishing domains skipped, {len(domains)} to query")

    pairs = legit_urls_with_paths(ClusterIndex(CRAWL, OUT_DIR), domains, args.per_domain, SEED)
    rank = {d: i for i, d in enumerate(ranked, 1)}
    out = pd.DataFrame(pairs, columns=["url", "domain"]).drop_duplicates("url")
    out["rank"] = out["domain"].map(rank)
    out.to_csv(OUT_DIR / "legit_paths.csv", index=False)

    meta = {
        "tranco_list_id": list_id,
        "common_crawl": CRAWL,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "domains_queried": len(domains),
        "domains_with_urls": int(out["domain"].nunique()),
        "urls": len(out),
    }
    (OUT_DIR / "legit_paths.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
