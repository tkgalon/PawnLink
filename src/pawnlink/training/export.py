"""Usage: uv run python -m pawnlink.training.export [--version N]

Writes models/model.txt and models/metadata.json for the API.
"""

import argparse
import json
from pathlib import Path

import mlflow
from mlflow import MlflowClient

from pawnlink.features.extract import FEATURE_NAMES
from pawnlink.training.train import MODEL_NAME, TRACKING_URI

MODEL_DIR = Path("models")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", help="registry version, default: latest")
    args = parser.parse_args()

    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()
    if args.version:
        mv = client.get_model_version(MODEL_NAME, args.version)
    else:
        mv = max(client.search_model_versions(f"name='{MODEL_NAME}'"), key=lambda m: int(m.version))
    run = client.get_run(mv.run_id)

    if "threshold" not in run.data.metrics:
        raise SystemExit(f"v{mv.version} has no threshold metric; retrain with the current train.py.")

    booster = mlflow.lightgbm.load_model(f"models:/{MODEL_NAME}/{mv.version}")
    if booster.feature_name() != list(FEATURE_NAMES):
        raise SystemExit(f"v{mv.version} was trained on different features than the current code.")

    MODEL_DIR.mkdir(exist_ok=True)
    booster.save_model(MODEL_DIR / "model.txt")
    metadata = {
        "model_name": MODEL_NAME,
        "model_version": mv.version,
        "run_id": mv.run_id,
        "git_commit": run.data.tags.get("mlflow.source.git.commit"),
        "threshold": run.data.metrics["threshold"],
        "test_auc": run.data.metrics["test_auc"],
        "feature_names": list(FEATURE_NAMES),
    }
    (MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Exported {MODEL_NAME} v{mv.version} to {MODEL_DIR}/")


if __name__ == "__main__":
    main()
