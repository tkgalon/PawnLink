import argparse

import mlflow
import numpy as np
from mlflow import MlflowClient
from sklearn.metrics import recall_score, roc_auc_score

from pawnlink.training.train import MODEL_NAME, TRACKING_URI, load_split

ALIAS = "champion"
# A candidate may trade a little ranking quality for fewer false alarms, but not more.
MAX_AUC_DROP = 0.005
MAX_RECALL_DROP = 0.01


def evaluate(client: MlflowClient, version: str, data: dict) -> dict:
    mv = client.get_model_version(MODEL_NAME, version)
    threshold = client.get_run(mv.run_id).data.metrics["threshold"]
    booster = mlflow.lightgbm.load_model(f"models:/{MODEL_NAME}/{version}")
    X_test, y_test = data["test"]
    X_legit, _ = data["legit_paths_test"]
    test_scores = booster.predict(X_test)
    return {
        "version": version,
        "test_auc": roc_auc_score(y_test, test_scores),
        "test_recall": recall_score(y_test, (test_scores >= threshold).astype(int)),
        "legit_paths_fpr": float(np.mean(booster.predict(X_legit) >= threshold)),
    }


def gate(candidate: dict, champion: dict) -> list[tuple[str, bool]]:
    return [
        (
            f"test AUC drops at most {MAX_AUC_DROP}",
            candidate["test_auc"] >= champion["test_auc"] - MAX_AUC_DROP,
        ),
        (
            f"test recall drops at most {MAX_RECALL_DROP}",
            candidate["test_recall"] >= champion["test_recall"] - MAX_RECALL_DROP,
        ),
        (
            "fewer legit URLs with paths flagged",
            candidate["legit_paths_fpr"] < champion["legit_paths_fpr"],
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", help="registry version, default: latest")
    parser.add_argument(
        "--init", metavar="VERSION", help="set the first champion without a gate, then exit"
    )
    args = parser.parse_args()

    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()
    if args.init:
        client.set_registered_model_alias(MODEL_NAME, ALIAS, args.init)
        print(f"{MODEL_NAME}@{ALIAS} -> v{args.init}")
        return

    champion_version = client.get_model_version_by_alias(MODEL_NAME, ALIAS).version
    candidate_version = args.candidate or max(
        (m.version for m in client.search_model_versions(f"name='{MODEL_NAME}'")), key=int
    )
    if candidate_version == champion_version:
        raise SystemExit(f"v{candidate_version} is already @{ALIAS}.")

    # Both models are scored on the same current files, so the comparison is fair
    # even though the champion was trained before legit_paths_test existed.
    data = {name: load_split(name) for name in ("test", "legit_paths_test")}
    champion = evaluate(client, champion_version, data)
    candidate = evaluate(client, candidate_version, data)

    print(f"{'':18s} {'champion':>10s} {'candidate':>10s}")
    for key in ("version", "test_auc", "test_recall", "legit_paths_fpr"):
        c, n = champion[key], candidate[key]
        fmt = (lambda v: f"v{v}") if key == "version" else (lambda v: f"{v:.4f}")
        print(f"{key:18s} {fmt(c):>10s} {fmt(n):>10s}")

    checks = gate(candidate, champion)
    print()
    for name, ok in checks:
        print(f"  [{'pass' if ok else 'FAIL'}] {name}")

    if not all(ok for _, ok in checks):
        raise SystemExit(
            f"\nv{candidate_version} stays a candidate; @{ALIAS} is still v{champion_version}."
        )
    client.set_registered_model_alias(MODEL_NAME, ALIAS, candidate_version)
    print(f"\n{MODEL_NAME}@{ALIAS} -> v{candidate_version} (was v{champion_version})")


if __name__ == "__main__":
    main()
