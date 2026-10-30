import argparse
import json
import os
import random
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from pawnlink.api.model import PhishingModel
from pawnlink.monitoring.drift import MIN_CURRENT, load_urls_bigquery, run_drift, to_frame
from pawnlink.sources import (
    ClusterIndex,
    latest_crawl,
    legit_urls_with_paths,
    openphish_urls,
    tranco_domains,
)

PROJECT = "pawnlink-tkgalon"
DATASET = "pawnlink"
BUCKET = "pawnlink-tkgalon-models"
# Tranco ranks past the top 1000 used for v4's training data, so these domains are unseen.
LEGIT_RANKS = slice(1000, 10000)
LEGIT_DOMAINS = 150
PER_DOMAIN = 3
API_WINDOW_DAYS = 30

BATCH_SCHEMA = [
    ("run_date", "DATE"),
    ("source", "STRING"),
    ("url", "STRING"),
    ("label", "INT64"),
    ("score", "FLOAT64"),
    ("is_phishing", "BOOL"),
    ("model_version", "STRING"),
]
METRICS_SCHEMA = [
    ("run_date", "DATE"),
    ("model_version", "STRING"),
    ("openphish_n", "INT64"),
    ("openphish_recall", "FLOAT64"),
    ("openphish_https_recall", "FLOAT64"),
    ("legit_n", "INT64"),
    ("legit_fpr", "FLOAT64"),
    ("api_urls", "INT64"),
    ("drifted_columns", "INT64"),
    ("drift_report", "STRING"),
    ("sources", "STRING"),
]


def collect(run_date: date, cache_dir: Path) -> tuple[pd.DataFrame, dict]:
    phishing = openphish_urls()
    crawl = latest_crawl()
    tranco_id, ranked = tranco_domains(cache_dir)
    domains = random.Random(run_date.isoformat()).sample(ranked[LEGIT_RANKS], LEGIT_DOMAINS)
    legit = legit_urls_with_paths(
        ClusterIndex(crawl, cache_dir), domains, PER_DOMAIN, seed=run_date.toordinal()
    )
    batch = pd.DataFrame(
        [("openphish", u, 1) for u in phishing] + [("commoncrawl", u, 0) for u, _ in legit],
        columns=["source", "url", "label"],
    ).drop_duplicates("url")
    return batch, {"openphish": "community feed", "tranco": tranco_id, "common_crawl": crawl}


def summarize(batch: pd.DataFrame) -> dict:
    phish = batch[batch["label"] == 1]
    legit = batch[batch["label"] == 0]
    https = phish[phish["url"].str.startswith("https://")]
    return {
        "openphish_n": len(phish),
        "openphish_recall": float(phish["is_phishing"].mean()),
        "openphish_https_recall": float(https["is_phishing"].mean()) if len(https) else None,
        "legit_n": len(legit),
        "legit_fpr": float(legit["is_phishing"].mean()),
    }


def write_bigquery(table: str, rows: list[dict], schema: list[tuple[str, str]]) -> None:
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT)
    config = bigquery.LoadJobConfig(
        schema=[bigquery.SchemaField(name, kind) for name, kind in schema],
        write_disposition="WRITE_APPEND",
        time_partitioning=bigquery.TimePartitioning(field="run_date"),
    )
    # A load job, not streaming inserts: free, and the table is created on first run.
    client.load_table_from_json(rows, f"{PROJECT}.{DATASET}.{table}", job_config=config).result()


def upload_report(local: Path, run_date: date) -> str:
    from google.cloud import storage

    name = f"reports/drift/{run_date:%Y-%m}.html"
    storage.Client(project=PROJECT).bucket(BUCKET).blob(name).upload_from_filename(str(local))
    return f"gs://{BUCKET}/{name}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="write to reports/monthly/ only")
    args = parser.parse_args()

    run_date = datetime.now(UTC).date()
    model_dir = Path(os.environ.get("MODEL_DIR", "models"))
    model = PhishingModel.load(model_dir)
    cache_dir = Path(tempfile.mkdtemp())

    batch, sources = collect(run_date, cache_dir)
    batch["score"] = model.score(batch["url"].tolist())
    batch["is_phishing"] = batch["score"] >= model.threshold
    metrics = summarize(batch)

    reference = (model_dir / "reference_urls.txt").read_text().split()
    api_urls = [] if args.dry_run else load_urls_bigquery(API_WINDOW_DAYS)
    current = batch["url"].tolist() + api_urls
    drifted, report = None, None
    if len(current) >= MIN_CURRENT:
        snapshot, table = run_drift(to_frame(reference, model), to_frame(current, model))
        drifted = int(table["drifted"].sum())
        local = cache_dir / "drift.html"
        snapshot.save_html(str(local))
        if args.dry_run:
            out = Path("reports/monthly") / f"{run_date:%Y-%m}-drift.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(local.read_bytes())
            report = str(out)
        else:
            report = upload_report(local, run_date)

    summary = {
        "run_date": run_date.isoformat(),
        "model_version": model.version,
        **metrics,
        "api_urls": len(api_urls),
        "drifted_columns": drifted,
        "drift_report": report,
        "sources": json.dumps(sources),
    }
    if args.dry_run:
        batch.to_csv(Path("reports/monthly") / f"{run_date:%Y-%m}-batch.csv", index=False)
    else:
        rows = batch.assign(run_date=run_date.isoformat(), model_version=model.version)
        rows = rows.replace({np.nan: None}).to_dict("records")
        write_bigquery("batch_predictions", rows, BATCH_SCHEMA)
        write_bigquery("monthly_metrics", [summary], METRICS_SCHEMA)
    # One JSON line, so Cloud Logging shows the run's result as structured fields.
    print(json.dumps({"event": "monthly_run", "message": "monthly run done", **summary}))


if __name__ == "__main__":
    main()
