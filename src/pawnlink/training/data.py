from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

RAW_PATH = Path("data/raw/train.csv")
# Legit URLs with paths from Tranco + Common Crawl (scripts/fetch_legit_urls.py).
EXTERNAL_PATH = Path("data/external/legit_paths.csv")
PROCESSED_DIR = Path("data/processed")
SEED = 42
VAL_SIZE = 0.15
TEST_SIZE = 0.15


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """Keep only the raw URL and label; dataset feature columns are ignored."""
    df = pd.read_csv(path, usecols=["URL", "ClassLabel"])
    return df.rename(columns={"URL": "url"})


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """One row per URL. When the same URL has conflicting labels, keep the
    phishing one: missing a phishing URL costs more than a false alarm."""
    df = df.assign(url=df["url"].str.strip())
    df = df.sort_values(["url", "ClassLabel"])  # 0 (phishing) sorts first
    return df.drop_duplicates(subset="url", keep="first").reset_index(drop=True)


def add_target(df: pd.DataFrame) -> pd.DataFrame:
    """The dataset uses 0 = phishing; the service scores phishing as 1."""
    df = df.assign(is_phishing=(df["ClassLabel"] == 0).astype(int))
    return df.drop(columns="ClassLabel")


def split(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Stratified 70/15/15 split with a fixed seed."""
    train_val, test = train_test_split(
        df, test_size=TEST_SIZE, stratify=df["is_phishing"], random_state=SEED
    )
    train, val = train_test_split(
        train_val,
        test_size=VAL_SIZE / (1 - TEST_SIZE),
        stratify=train_val["is_phishing"],
        random_state=SEED,
    )
    return {"train": train, "val": val, "test": test}


def split_by_domain(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """70/15/15 by domain, so evaluation domains are never seen in training."""
    domains = np.array(sorted(df["domain"].unique()))
    np.random.default_rng(SEED).shuffle(domains)
    n_test, n_val = int(len(domains) * TEST_SIZE), int(len(domains) * VAL_SIZE)
    groups = {
        "legit_paths_test": domains[:n_test],
        "val": domains[n_test : n_test + n_val],
        "train": domains[n_test + n_val :],
    }
    return {name: df[df["domain"].isin(d)] for name, d in groups.items()}


def load_external(known_urls: set[str], path: Path = EXTERNAL_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=["url", "domain"])
    df = df[~df["url"].isin(known_urls)].drop_duplicates("url")
    return df.assign(is_phishing=0)


def main() -> None:
    df = add_target(deduplicate(load_raw()))
    parts = split(df)
    if EXTERNAL_PATH.exists():
        external = split_by_domain(load_external(set(df["url"])))
        for name, part in external.items():
            part = part[["url", "is_phishing"]]
            parts[name] = pd.concat([parts[name], part]) if name in parts else part
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, part in parts.items():
        part.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
        print(f"{name:16s} {len(part):6d} rows, phishing {part['is_phishing'].mean():.1%}")


if __name__ == "__main__":
    main()
