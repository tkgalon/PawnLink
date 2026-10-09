"""Usage: uv run uvicorn pawnlink.api.main:app --port 8080

Set MODEL_DIR to load the model from somewhere other than ./models.
"""

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field, StringConstraints

from pawnlink.api.model import PhishingModel

MAX_BATCH = 100

Url = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2048)]


class PredictRequest(BaseModel):
    url: Url


class BatchRequest(BaseModel):
    urls: list[Url] = Field(min_length=1, max_length=MAX_BATCH)


class Prediction(BaseModel):
    url: str
    score: float
    is_phishing: bool


class PredictResponse(Prediction):
    model_version: str
    latency_ms: float


class BatchResponse(BaseModel):
    predictions: list[Prediction]
    model_version: str
    latency_ms: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = PhishingModel.load(Path(os.environ.get("MODEL_DIR", "models")))
    yield


app = FastAPI(title="PawnLink", description="Paste a link. Pawn it.", lifespan=lifespan)


def _predict(model: PhishingModel, urls: list[str]) -> list[Prediction]:
    return [
        Prediction(url=u, score=s, is_phishing=s >= model.threshold)
        for u, s in zip(urls, model.score(urls))
    ]


@app.get("/health")
def health(request: Request) -> dict:
    return {"status": "ok", "model_version": request.app.state.model.version}


@app.post("/predict")
def predict(body: PredictRequest, request: Request) -> PredictResponse:
    start = time.perf_counter()
    model = request.app.state.model
    [prediction] = _predict(model, [body.url])
    return PredictResponse(
        **prediction.model_dump(),
        model_version=model.version,
        latency_ms=(time.perf_counter() - start) * 1000,
    )


@app.post("/predict/batch")
def predict_batch(body: BatchRequest, request: Request) -> BatchResponse:
    start = time.perf_counter()
    model = request.app.state.model
    return BatchResponse(
        predictions=_predict(model, body.urls),
        model_version=model.version,
        latency_ms=(time.perf_counter() - start) * 1000,
    )
