import json
import sys
from datetime import UTC, datetime


def log_predictions(predictions, model_version: str, endpoint: str) -> None:
    ts = datetime.now(UTC).isoformat()
    for p in predictions:
        record = {
            "event": "prediction",
            "message": f"prediction {p.score:.3f} {p.url[:80]}",
            "ts": ts,
            "endpoint": endpoint,
            "model_version": model_version,
            "url": p.url,
            "score": p.score,
            "is_phishing": p.is_phishing,
        }
        sys.stdout.write(json.dumps(record) + "\n")
    sys.stdout.flush()
