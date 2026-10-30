import pandas as pd

from pawnlink.features.extract import FEATURE_NAMES, extract_features
from pawnlink.monitoring.drift import run_drift


def _features(urls):
    return pd.DataFrame([extract_features(u) for u in urls], columns=list(FEATURE_NAMES))


HOMEPAGES = [f"https://www.site{i}.com" for i in range(300)]


def test_same_traffic_has_no_path_drift():
    _, table = run_drift(_features(HOMEPAGES), _features(HOMEPAGES))
    assert not table["drifted"].any()


def test_paths_show_up_as_drift():
    with_paths = [f"{u}/docs/page-{i}" for i, u in enumerate(HOMEPAGES)]
    _, table = run_drift(_features(HOMEPAGES), _features(with_paths))
    drifted = set(table.loc[table["drifted"], "column"])
    assert "path_length" in drifted
    assert "url_length" in drifted
