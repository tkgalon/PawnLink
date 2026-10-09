"""Train the LightGBM model on the fixed splits and log the run to MLflow.

Run with: uv run python -m pawnlink.training.train
Prerequisite: uv run python -m pawnlink.training.data
View runs:    uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
"""

import argparse
import hashlib
import subprocess
from pathlib import Path

import lightgbm as lgb
import mlflow
import pandas as pd
from sklearn.metrics import roc_auc_score

from pawnlink.features.extract import FEATURE_NAMES, extract_features

PROCESSED_DIR = Path("data/processed")
TRACKING_URI = "sqlite:///mlflow.db"
EXPERIMENT = "pawnlink"
MODEL_NAME = "pawnlink-lgbm"

PARAMS = {
    "objective": "binary",
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_child_samples": 20,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.9,
    "bagging_freq": 1,
    "seed": 42,
    "verbose": -1,
}
NUM_BOOST_ROUND = 2000
EARLY_STOPPING_ROUNDS = 100

# Legitimate URLs with paths and file extensions. The training data's legit
# URLs are mostly bare homepages, so these probe for "has a path = phishing".
SANITY_URLS = [
    "https://en.wikipedia.org/wiki/Phishing",
    "https://github.com/microsoft/LightGBM/releases/download/v4.6.0/lightgbm.zip",
    "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe",
    "https://docs.python.org/3/library/urllib.parse.html",
    "https://www.tokopedia.com/search?q=laptop&page=2",
]


def to_matrix(urls: pd.Series) -> pd.DataFrame:
    rows = [extract_features(u) for u in urls]
    return pd.DataFrame(rows, columns=list(FEATURE_NAMES))


def load_split(name: str) -> tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(PROCESSED_DIR / f"{name}.csv")
    return to_matrix(df["url"]), df["is_phishing"]


def git_is_dirty() -> bool:
    status = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
    )
    return bool(status.stdout.strip())


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-dirty", action="store_true", help="train even with uncommitted changes"
    )
    args = parser.parse_args()

    # MLflow tags the run with the current commit, which is only true if the tree is clean.
    dirty = git_is_dirty()
    if dirty and not args.allow_dirty:
        raise SystemExit(
            "Uncommitted changes found. Commit first, or pass --allow-dirty for a throwaway run."
        )

    X_train, y_train = load_split("train")
    X_val, y_val = load_split("val")
    X_test, y_test = load_split("test")

    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)

    with mlflow.start_run():
        mlflow.set_tags(
            {f"data.{name}.sha256": file_sha256(PROCESSED_DIR / f"{name}.csv")
             for name in ("train", "val", "test")}
            | {"git.dirty": str(dirty).lower()}
        )  # fmt: skip
        mlflow.log_params(PARAMS | {"num_features": len(FEATURE_NAMES)})

        booster = lgb.train(
            PARAMS,
            lgb.Dataset(X_train, y_train),
            num_boost_round=NUM_BOOST_ROUND,
            valid_sets=[lgb.Dataset(X_val, y_val)],
            callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)],
        )

        metrics = {
            "best_iteration": booster.best_iteration,
            "train_auc": roc_auc_score(y_train, booster.predict(X_train)),
            "val_auc": roc_auc_score(y_val, booster.predict(X_val)),
            "test_auc": roc_auc_score(y_test, booster.predict(X_test)),
        }
        mlflow.log_metrics(metrics)

        importance = pd.DataFrame(
            {"feature": FEATURE_NAMES, "gain": booster.feature_importance("gain")}
        ).sort_values("gain", ascending=False)
        mlflow.log_table(importance, "feature_importance.json")

        sanity = pd.DataFrame(
            {"url": SANITY_URLS, "phishing_score": booster.predict(to_matrix(pd.Series(SANITY_URLS)))}
        )
        mlflow.log_table(sanity, "sanity_legit_urls.json")

        mlflow.lightgbm.log_model(
            booster,
            name="model",
            input_example=X_val.head(3),
            registered_model_name=MODEL_NAME,
        )

    for key, value in metrics.items():
        print(f"{key:15s} {value:.5f}" if isinstance(value, float) else f"{key:15s} {value}")
    print("\nTop features by gain:\n", importance.head(8).to_string(index=False))
    print("\nSanity check, legit URLs (want low scores):\n", sanity.to_string(index=False))


if __name__ == "__main__":
    main()
