import base64
import json

import lightgbm as lgb
import numpy as np
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from pawnlink.api.main import MAX_BATCH, app
from pawnlink.api.model import PhishingModel
from pawnlink.api.model import _matrix as model_matrix
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


@pytest.mark.parametrize(("path", "text"), [("/", "main page"), ("/stats/", "stats page")])
def test_site_pages(client, path, text):
    resp = client.get(path)
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert text in resp.text


def test_site_does_not_shadow_the_api(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/docs").status_code == 200
    assert client.get("/nope").status_code == 404


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


def _logged(capsys):
    lines = capsys.readouterr().out.splitlines()
    return [json.loads(line) for line in lines if line.startswith("{")]


def test_predict_logs_one_line(client, capsys):
    capsys.readouterr()
    body = client.post("/predict", json={"url": "https://example.com/a"}).json()
    [record] = _logged(capsys)
    assert record["event"] == "prediction"
    assert record["endpoint"] == "predict"
    assert record["url"] == "https://example.com/a"
    assert record["score"] == body["score"]
    assert record["model_version"] == "test"


def test_batch_logs_one_line_per_url(client, capsys):
    capsys.readouterr()
    urls = ["https://a.com", "https://b.com", "https://c.com"]
    client.post("/predict/batch", json={"urls": urls})
    records = _logged(capsys)
    assert [r["url"] for r in records] == urls
    assert {r["endpoint"] for r in records} == {"batch"}


def test_invalid_request_is_not_logged(client, capsys):
    capsys.readouterr()
    client.post("/predict", json={"url": ""})
    assert _logged(capsys) == []


def _push(client, data, token="Bearer good"):
    return client.post(
        "/pubsub/predict",
        json={"message": {"data": data, "messageId": "m1"}, "subscription": "s"},
        headers={"Authorization": token},
    )


@pytest.fixture
def pubsub(client, monkeypatch):
    monkeypatch.setenv("PUBSUB_AUDIENCE", "https://example.test/pubsub/predict")
    monkeypatch.setenv("PUBSUB_PUSH_SA", "push@example.iam.gserviceaccount.com")

    def fake_verify(authorization, audience, service_account):
        if authorization != "Bearer good":
            raise HTTPException(status_code=401)

    monkeypatch.setattr("pawnlink.api.main.verify_push_token", fake_verify)
    return client


def _b64(text):
    return base64.b64encode(text.encode()).decode()


def test_pubsub_is_off_without_config(client):
    assert _push(client, _b64("https://a.com")).status_code == 404


def test_pubsub_rejects_bad_token(pubsub):
    assert _push(pubsub, _b64("https://a.com"), token="Bearer forged").status_code == 401


def test_pubsub_scores_and_logs_as_stream(pubsub, capsys):
    capsys.readouterr()
    assert _push(pubsub, _b64('{"url": "https://a.com/login"}')).status_code == 204
    [record] = _logged(capsys)
    assert record["endpoint"] == "stream"
    assert record["url"] == "https://a.com/login"


def test_pubsub_acks_bad_message_without_scoring(pubsub, capsys):
    capsys.readouterr()
    assert _push(pubsub, _b64("")).status_code == 204
    assert _push(pubsub, "not base64!!").status_code == 204
    records = _logged(capsys)
    assert [r["event"] for r in records] == ["pubsub_bad_message", "pubsub_bad_message"]


def test_predict_without_explain_has_no_reasons(client):
    body = client.post("/predict", json={"url": "https://a.com/x"}).json()
    assert body["threshold"] == 0.5
    assert body["reasons"] is None and body["parts"] is None


def test_predict_explain_adds_reasons_and_parts(client):
    url = "https://mu.qmmafe.com/"
    body = client.post("/predict?explain=true", json={"url": url}).json()
    assert "".join(p["text"] for p in body["parts"]) == url
    assert 1 <= len(body["reasons"]) <= 5
    assert {"feature", "value", "contribution"} <= body["reasons"][0].keys()
    sizes = [abs(r["contribution"]) for r in body["reasons"]]
    assert sizes == sorted(sizes, reverse=True)


def test_shap_contributions_add_up_to_the_score(tmp_path):
    _write_model(tmp_path)
    model = PhishingModel.load(tmp_path)
    url = "http://paypal-verify.xyz/login"
    reasons = model.explain(url, top=len(FEATURE_NAMES))
    raw = model.booster.predict(model_matrix([url]), raw_score=True)[0]
    base = model.booster.predict(model_matrix([url]), pred_contrib=True)[0][-1]
    assert abs(sum(r["contribution"] for r in reasons) + base - raw) < 1e-6


def test_stats_endpoint_returns_503_when_bigquery_fails(client):
    def boom():
        raise RuntimeError("no credentials")

    client.app.state.stats._fetch = boom
    assert client.get("/api/stats").status_code == 503


def test_stats_endpoint_adds_model_version(client):
    client.app.state.stats._fetch = lambda: {"months": []}
    assert client.get("/api/stats").json() == {"months": [], "model_version": "test"}
