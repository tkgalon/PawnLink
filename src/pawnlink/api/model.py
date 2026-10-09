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
        features = [extract_features(u) for u in urls]
        X = np.array([[f[name] for name in FEATURE_NAMES] for f in features], dtype=float)
        return self.booster.predict(X).tolist()
