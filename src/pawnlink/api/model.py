import json
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np

from pawnlink.features.extract import FEATURE_NAMES, extract_features


@dataclass(frozen=True)
class PhishingModel:
    booster: lgb.Booster
    threshold: float
    version: str

    @classmethod
    def load(cls, model_dir: Path) -> "PhishingModel":
        metadata = json.loads((model_dir / "metadata.json").read_text())
        booster = lgb.Booster(model_file=str(model_dir / "model.txt"))
        if booster.feature_name() != list(FEATURE_NAMES):
            raise RuntimeError("Model features don't match pawnlink.features; re-export the model.")
        return cls(booster, float(metadata["threshold"]), str(metadata["model_version"]))

    def score(self, urls: list[str]) -> list[float]:
        return self.booster.predict(_matrix(urls)).tolist()

    def explain(self, url: str, top: int = 5) -> list[dict]:
        """The features that moved this URL's score most, as SHAP values in log odds.

        Positive pushes toward phishing, negative toward safe.
        """
        features = extract_features(url)
        contrib = self.booster.predict(_matrix([url]), pred_contrib=True)[0][:-1]
        ranked = sorted(zip(FEATURE_NAMES, contrib, strict=True), key=lambda p: -abs(p[1]))
        return [
            {"feature": name, "value": features[name], "contribution": float(c)}
            for name, c in ranked[:top]
        ]


def _matrix(urls: list[str]) -> np.ndarray:
    features = [extract_features(u) for u in urls]
    return np.array([[f[name] for name in FEATURE_NAMES] for f in features], dtype=float)
