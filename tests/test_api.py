import json

import lightgbm as lgb
import numpy as np
import pytest
from fastapi.testclient import TestClient

from pawnlink.api.main import MAX_BATCH, app
from pawnlink.api.model import PhishingModel
from pawnlink.features.extract import FEATURE_NAMES


def _write_model(model_dir, feature_names=FEATURE_NAMES, threshold=0.5):
    # Tiny model on random data: tests check the API, not model quality,
    # and must not depend on the real model being exported.
    rng = np.random.default_rng(0)
    X = rng.random((200, len(feature_names)))
    y = rng.integers(0, 2, 200)
    booster = lgb.train(
        {"objective": "binary", "verbose": -1},
        lgb.Dataset(X, y, feature_name=list(feature_names)),
        num_boost_round=5,
    )
    booster.save_model(str(model_dir / "model.txt"))
    (model_dir / "metadata.json").write_text(
        json.dumps({"model_version": "test", "threshold": threshold})
    )


@pytest.fixture
def client(tmp_path, monkeypatch):
    _write_model(tmp_path)
    monkeypatch.setenv("MODEL_DIR", str(tmp_path))
    with TestClient(app) as c:
        yield c


def test_demo_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Pawn it" in resp.text


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "model_version": "test"}


def test_predict(client):
    body = client.post("/predict", json={"url": "http://login.paypal.com.evil.xyz/verify"}).json()
    assert 0.0 <= body["score"] <= 1.0
    assert body["is_phishing"] == (body["score"] >= 0.5)
    assert body["model_version"] == "test"
    assert body["latency_ms"] >= 0


def test_predict_strips_whitespace(client):
    body = client.post("/predict", json={"url": "  https://example.com  "}).json()
    assert body["url"] == "https://example.com"


def test_malformed_url_is_scored_not_500(client):
    assert client.post("/predict", json={"url": "http://[abc/x"}).status_code == 200


@pytest.mark.parametrize(
    "payload",
    [{}, {"url": ""}, {"url": "   "}, {"url": "a" * 2049}, {"url": 123}],
)
def test_invalid_input_is_422(client, payload):
    assert client.post("/predict", json=payload).status_code == 422


def test_batch_keeps_order(client):
    urls = ["https://a.com", "http://1.2.3.4/x.exe", "https://b.org/login"]
    body = client.post("/predict/batch", json={"urls": urls}).json()
    assert [p["url"] for p in body["predictions"]] == urls


@pytest.mark.parametrize("n", [0, MAX_BATCH + 1])
def test_batch_size_limits(client, n):
    resp = client.post("/predict/batch", json={"urls": ["https://a.com"] * n})
    assert resp.status_code == 422


def test_load_rejects_model_with_other_features(tmp_path):
    _write_model(tmp_path, feature_names=[f"f{i}" for i in range(len(FEATURE_NAMES))])
    with pytest.raises(RuntimeError, match="re-export"):
        PhishingModel.load(tmp_path)
