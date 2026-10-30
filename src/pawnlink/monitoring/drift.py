import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset

from pawnlink.api.model import PhishingModel
from pawnlink.features.extract import FEATURE_NAMES, extract_features

REFERENCE_PATH = Path("data/processed/train.csv")
REFERENCE_SIZE = 5000
# Below this, any two distributions look different and every column "drifts".
MIN_CURRENT = 100
SEED = 42
REPORT_DIR = Path("reports/drift")
BQ_TABLE = "pawnlink-tkgalon.pawnlink.run_googleapis_com_stdout"


def load_reference() -> list[str]:
    df = pd.read_csv(REFERENCE_PATH)
    return df["url"].sample(n=min(REFERENCE_SIZE, len(df)), random_state=SEED).tolist()


def load_urls_file(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def load_urls_bigquery(days: int) -> list[str]:
    from google.cloud import bigquery

    client = bigquery.Client(project="pawnlink-tkgalon")
    # The timestamp filter lets BigQuery skip old partitions, so the scan stays small.
    query = f"""
        SELECT jsonPayload.url AS url
        FROM `{BQ_TABLE}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
    """
    config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("days", "INT64", days)]
    )
    return [row.url for row in client.query(query, job_config=config).result()]


def to_frame(urls: list[str], model: PhishingModel) -> pd.DataFrame:
    # Features are recomputed from the URL with the same code the API uses.
    df = pd.DataFrame([extract_features(u) for u in urls], columns=list(FEATURE_NAMES))
    df["score"] = model.score(urls)
    return df


def run_drift(reference: pd.DataFrame, current: pd.DataFrame):
    definition = DataDefinition(numerical_columns=list(reference.columns))
    # Constant columns (e.g. is_malformed) make numpy warn while computing correlations.
    with np.errstate(divide="ignore", invalid="ignore"):
        snapshot = Report([DataDriftPreset()]).run(
            Dataset.from_pandas(current, data_definition=definition),
            Dataset.from_pandas(reference, data_definition=definition),
        )
    rows = []
    for metric in snapshot.dict()["metrics"]:
        config = metric["config"]
        if "column" not in config:
            continue
        method, threshold, value = config["method"], config["threshold"], metric["value"]
        # p-value tests flag drift when small, distance metrics when large.
        drifted = value < threshold if "p_value" in method else value >= threshold
        rows.append(
            {
                "column": config["column"],
                "method": method,
                "value": value,
                "threshold": threshold,
                "drifted": drifted,
            }
        )
    table = pd.DataFrame(rows).sort_values(["drifted", "column"], ascending=[False, True])
    return snapshot, table.reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True, help="'bq' or a file with one URL per line")
    parser.add_argument("--days", type=int, default=7, help="window for --current bq")
    parser.add_argument("--model-dir", type=Path, default=Path("models"))
    args = parser.parse_args()

    if args.current == "bq":
        current_urls = load_urls_bigquery(args.days)
        name = f"bq-{args.days}d"
    else:
        current_urls = load_urls_file(Path(args.current))
        name = Path(args.current).stem
    if len(current_urls) < MIN_CURRENT:
        raise SystemExit(
            f"Only {len(current_urls)} current URLs ({name}); need at least {MIN_CURRENT} "
            "for a meaningful drift report."
        )

    model = PhishingModel.load(args.model_dir)
    snapshot, table = run_drift(to_frame(load_reference(), model), to_frame(current_urls, model))

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / f"{datetime.now():%Y%m%d-%H%M}-{name}.html"
    snapshot.save_html(str(out))

    print(f"Reference: {REFERENCE_SIZE} train URLs. Current: {len(current_urls)} URLs ({name}).")
    print(f"Drifted columns: {table['drifted'].sum()} of {len(table)}\n")
    print(table.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(f"\nHTML report: {out}")


if __name__ == "__main__":
    main()
