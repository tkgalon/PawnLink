import pandas as pd

from pawnlink.training.data import add_target, deduplicate, split, split_by_domain


def test_deduplicate_keeps_phishing_on_label_conflict():
    df = pd.DataFrame(
        {
            "url": ["a.com", "a.com", "b.com", "b.com", " c.com", "c.com"],
            "ClassLabel": [1, 0, 1, 1, 1, 1],
        }
    )
    out = deduplicate(df).set_index("url")["ClassLabel"]
    assert out.to_dict() == {"a.com": 0, "b.com": 1, "c.com": 1}


def test_add_target_flips_label():
    df = pd.DataFrame({"url": ["x", "y"], "ClassLabel": [0, 1]})
    out = add_target(df)
    assert out["is_phishing"].tolist() == [1, 0]
    assert "ClassLabel" not in out.columns


def _toy(n=200):
    return pd.DataFrame(
        {"url": [f"u{i}.com" for i in range(n)], "is_phishing": [i % 3 == 0 for i in range(n)]}
    ).astype({"is_phishing": int})


def test_split_has_no_url_overlap_and_covers_all_rows():
    df = _toy()
    parts = split(df)
    urls = [set(p["url"]) for p in parts.values()]
    assert sum(len(u) for u in urls) == len(df)
    assert not (urls[0] & urls[1] or urls[0] & urls[2] or urls[1] & urls[2])


def test_split_is_reproducible():
    df = _toy()
    assert split(df)["test"]["url"].tolist() == split(df)["test"]["url"].tolist()


def test_split_by_domain_keeps_domains_apart():
    df = pd.DataFrame(
        {
            "url": [f"https://d{i % 40}.com/p{i}" for i in range(400)],
            "domain": [f"d{i % 40}.com" for i in range(400)],
        }
    )
    parts = split_by_domain(df)
    domains = {name: set(p["domain"]) for name, p in parts.items()}
    assert sum(len(p) for p in parts.values()) == len(df)
    assert not domains["train"] & domains["val"]
    assert not domains["train"] & domains["legit_paths_test"]
    assert not domains["val"] & domains["legit_paths_test"]
