import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, StringConstraints, TypeAdapter, ValidationError

from pawnlink.api.anatomy import url_parts
from pawnlink.api.model import PhishingModel
from pawnlink.api.prediction_log import log_predictions
from pawnlink.api.pubsub import decode_url, verify_push_token
from pawnlink.api.stats import StatsCache

MAX_BATCH = 100
DEMO_PAGE = (Path(__file__).parent / "static" / "index.html").read_text()

Url = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2048)]


class PredictRequest(BaseModel):
    url: Url


class PubSubMessage(BaseModel):
    data: str = ""
    messageId: str = ""  # Pub/Sub's own field name, hence camelCase


class PushEnvelope(BaseModel):
    message: PubSubMessage
    subscription: str = ""


class BatchRequest(BaseModel):
    urls: list[Url] = Field(min_length=1, max_length=MAX_BATCH)


class Prediction(BaseModel):
    url: str
    score: float
    is_phishing: bool


class Reason(BaseModel):
    feature: str
    value: float
    contribution: float  # SHAP value in log odds; positive pushes toward phishing


class UrlPart(BaseModel):
    text: str
    kind: str


class PredictResponse(Prediction):
    model_version: str
    threshold: float
    latency_ms: float
    reasons: list[Reason] | None = None
    parts: list[UrlPart] | None = None


class BatchResponse(BaseModel):
    predictions: list[Prediction]
    model_version: str
    latency_ms: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = PhishingModel.load(Path(os.environ.get("MODEL_DIR", "models")))
    app.state.stats = StatsCache()
    yield


app = FastAPI(title="PawnLink", description="Paste a link. Pawn it.", lifespan=lifespan)


def _predict(model: PhishingModel, urls: list[str]) -> list[Prediction]:
    return [
        Prediction(url=u, score=s, is_phishing=s >= model.threshold)
        for u, s in zip(urls, model.score(urls), strict=True)
    ]


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def demo() -> str:
    return DEMO_PAGE


@app.get("/health")
def health(request: Request) -> dict:
    return {"status": "ok", "model_version": request.app.state.model.version}


@app.post("/predict")
def predict(body: PredictRequest, request: Request, explain: bool = False) -> PredictResponse:
    start = time.perf_counter()
    model = request.app.state.model
    [prediction] = _predict(model, [body.url])
    log_predictions([prediction], model.version, "predict")
    extra = {"reasons": model.explain(body.url), "parts": url_parts(body.url)} if explain else {}
    return PredictResponse(
        **prediction.model_dump(),
        model_version=model.version,
        threshold=model.threshold,
        latency_ms=(time.perf_counter() - start) * 1000,
        **extra,
    )


@app.get("/api/stats")
def stats(request: Request) -> dict:
    try:
        data = request.app.state.stats.get()
    except Exception as e:
        # Stats are a nice-to-have: the scanner keeps working when BigQuery is unreachable.
        raise HTTPException(status_code=503, detail="stats unavailable") from e
    return data | {"model_version": request.app.state.model.version}


@app.post("/predict/batch")
def predict_batch(body: BatchRequest, request: Request) -> BatchResponse:
    start = time.perf_counter()
    model = request.app.state.model
    predictions = _predict(model, body.urls)
    log_predictions(predictions, model.version, "batch")
    return BatchResponse(
        predictions=predictions,
        model_version=model.version,
        latency_ms=(time.perf_counter() - start) * 1000,
    )


@app.post("/pubsub/predict", status_code=204, include_in_schema=False)
def pubsub_predict(
    envelope: PushEnvelope,
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    # Off unless the deploy sets both, so a local run never accepts unsigned pushes.
    audience = os.environ.get("PUBSUB_AUDIENCE")
    push_sa = os.environ.get("PUBSUB_PUSH_SA")
    if not audience or not push_sa:
        raise HTTPException(status_code=404)
    verify_push_token(authorization, audience, push_sa)

    try:
        url = TypeAdapter(Url).validate_python(decode_url(envelope.message.data))
    except ValidationError:
        # Acknowledge anyway: a bad message never gets better, and an error status
        # would make Pub/Sub redeliver it forever.
        warning = {"severity": "WARNING", "event": "pubsub_bad_message"}
        print(json.dumps(warning | {"message_id": envelope.message.messageId}), flush=True)
        return Response(status_code=204)

    model = request.app.state.model
    log_predictions(_predict(model, [url]), model.version, "stream")
    return Response(status_code=204)
