"""Turn the raw competition CSV into fixed train/validation/test splits.

Run with: uv run python -m pawnlink.training.data
"""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

RAW_PATH = Path("data/raw/train.csv")
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


def main() -> None:
    df = add_target(deduplicate(load_raw()))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, part in split(df).items():
        part.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
        print(f"{name:5s} {len(part):6d} rows, phishing {part['is_phishing'].mean():.1%}")


if __name__ == "__main__":
    main()
