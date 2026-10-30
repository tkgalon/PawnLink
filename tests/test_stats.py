from pawnlink.api.stats import StatsCache, fetch_stats


def _bq(fields, rows):
    return {
        "schema": {"fields": [{"name": f} for f in fields]},
        "rows": [{"f": [{"v": v} for v in row]} for row in rows],
    }


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


class FakeSession:
    def __init__(self):
        self.queries = []

    def post(self, url, json, timeout):
        sql = json["query"]
        self.queries.append(sql)
        if "monthly_metrics" in sql:
            return FakeResponse(
                _bq(
                    ["run_date", "model_version", "openphish_n", "openphish_recall",
                     "openphish_https_recall", "legit_n", "legit_fpr", "api_urls",
                     "drifted_columns"],
                    [["2026-10-30", "4", "300", "0.68", "0.552", "232", "0.026", "30", "21"]],
                )
            )  # fmt: skip
        if "STARTS_WITH" in sql:
            return FakeResponse(
                _bq(["https", "n", "recall"], [["true", "210", "0.552"], ["false", "90", "0.978"]])
            )
        return FakeResponse(_bq(["live", "batch"], [["34", "532"]]))


def test_fetch_stats_parses_bigquery_rows():
    stats = fetch_stats(FakeSession())
    [month] = stats["months"]
    assert month["run_date"] == "2026-10-30"
    assert month["openphish_recall"] == 0.68
    assert month["legit_n"] == 232
    assert stats["latest_by_scheme"]["https"] == {"n": 210, "recall": 0.552}
    assert stats["latest_by_scheme"]["http"]["n"] == 90
    assert (stats["live_predictions"], stats["batch_predictions"]) == (34, 532)


def test_cache_queries_once_within_ttl():
    calls = []
    cache = StatsCache(fetch=lambda: calls.append(1) or {"n": len(calls)}, ttl=60)
    assert cache.get() == cache.get() == {"n": 1}
    assert len(calls) == 1


def test_cache_refreshes_after_ttl():
    calls = []
    cache = StatsCache(fetch=lambda: calls.append(1) or {"n": len(calls)}, ttl=0)
    cache.get()
    assert cache.get() == {"n": 2}
