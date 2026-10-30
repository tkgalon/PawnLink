import pandas as pd

from pawnlink.monitoring.monthly import summarize


def test_summarize_splits_recall_and_false_alarms():
    batch = pd.DataFrame(
        {
            "url": ["https://a.xyz", "http://b.xyz", "https://c.xyz", "https://ok.com/x"],
            "label": [1, 1, 1, 0],
            "is_phishing": [True, True, False, True],
        }
    )
    m = summarize(batch)
    assert m["openphish_n"] == 3
    assert m["openphish_recall"] == 2 / 3
    assert m["openphish_https_recall"] == 1 / 2
    assert m["legit_fpr"] == 1.0
