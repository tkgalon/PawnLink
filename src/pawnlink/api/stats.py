import threading
import time
from datetime import UTC, datetime

import google.auth
from google.auth.transport.requests import AuthorizedSession

PROJECT = "pawnlink-tkgalon"
DATASET = "pawnlink"
LOCATION = "us-central1"
CACHE_SECONDS = 3600

MONTHS_SQL = f"""
SELECT run_date, model_version, openphish_n, openphish_recall, openphish_https_recall,
       legit_n, legit_fpr, api_urls, drifted_columns
FROM `{PROJECT}.{DATASET}.monthly_metrics`
QUALIFY ROW_NUMBER() OVER (PARTITION BY FORMAT_DATE('%Y-%m', run_date) ORDER BY run_date DESC) = 1
ORDER BY run_date
"""

# Recall split by scheme for the latest run; monthly_metrics only keeps the HTTPS share.
SCHEME_SQL = f"""
SELECT STARTS_WITH(url, 'https://') AS https, COUNT(*) AS n,
       AVG(CAST(is_phishing AS INT64)) AS recall
FROM `{PROJECT}.{DATASET}.batch_predictions`
WHERE label = 1 AND run_date = (SELECT MAX(run_date) FROM `{PROJECT}.{DATASET}.batch_predictions`)
GROUP BY https
"""

COUNTS_SQL = f"""
SELECT
  (SELECT COUNT(*) FROM `{PROJECT}.{DATASET}.run_googleapis_com_stdout`) AS live,
  (SELECT COUNT(*) FROM `{PROJECT}.{DATASET}.batch_predictions`) AS batch
"""


def _query(session: AuthorizedSession, sql: str) -> list[dict]:
    resp = session.post(
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT}/queries",
        json={"query": sql, "useLegacySql": False, "location": LOCATION, "timeoutMs": 20000},
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    names = [f["name"] for f in body["schema"]["fields"]]
    rows = body.get("rows", [])
    return [dict(zip(names, (c["v"] for c in row["f"]), strict=True)) for row in rows]


def _num(value: str | None, kind=float):
    return None if value is None else kind(value)


def fetch_stats(session: AuthorizedSession) -> dict:
    months = [
        {
            "run_date": r["run_date"],
            "model_version": r["model_version"],
            "openphish_n": _num(r["openphish_n"], int),
            "openphish_recall": _num(r["openphish_recall"]),
            "openphish_https_recall": _num(r["openphish_https_recall"]),
            "legit_n": _num(r["legit_n"], int),
            "legit_fpr": _num(r["legit_fpr"]),
            "api_urls": _num(r["api_urls"], int),
            "drifted_columns": _num(r["drifted_columns"], int),
        }
        for r in _query(session, MONTHS_SQL)
    ]
    by_scheme = {
        ("https" if r["https"] == "true" else "http"): {
            "n": int(r["n"]),
            "recall": float(r["recall"]),
        }
        for r in _query(session, SCHEME_SQL)
    }
    [counts] = _query(session, COUNTS_SQL)
    return {
        "months": months,
        "latest_by_scheme": by_scheme,
        "live_predictions": int(counts["live"]),
        "batch_predictions": int(counts["batch"]),
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


class StatsCache:
    """BigQuery is queried at most once an hour, however often the page is opened."""

    def __init__(self, fetch=None, ttl: float = CACHE_SECONDS):
        self._fetch = fetch or self._fetch_with_default_credentials
        self._ttl = ttl
        self._lock = threading.Lock()
        self._value = None
        self._at = 0.0

    @staticmethod
    def _fetch_with_default_credentials() -> dict:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/bigquery.readonly"]
        )
        return fetch_stats(AuthorizedSession(credentials))

    def get(self) -> dict:
        with self._lock:
            if self._value is None or time.monotonic() - self._at > self._ttl:
                self._value = self._fetch()
                self._at = time.monotonic()
            return self._value
