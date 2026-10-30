import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np

from pawnlink.features.extract import FEATURE_NAMES


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    booster = lgb.train(
        {"objective": "binary", "verbose": -1},
        lgb.Dataset(
            rng.random((200, len(FEATURE_NAMES))),
            rng.integers(0, 2, 200),
            feature_name=list(FEATURE_NAMES),
        ),
        num_boost_round=5,
    )
    booster.save_model(str(out / "model.txt"))
    (out / "metadata.json").write_text(json.dumps({"model_version": "dummy", "threshold": 0.5}))
    print(f"Wrote dummy model to {out}/")


if __name__ == "__main__":
    main()
