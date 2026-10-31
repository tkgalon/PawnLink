# Site stage: build the React pages into static files.
FROM node:22-slim AS site
WORKDIR /site

# Packages first so this layer is cached until package-lock.json changes.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npx vite build


# Build stage: resolve and install dependencies with uv.
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.24 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# The API image installs no extra groups; the monthly job image passes
# --build-arg UV_GROUPS="--group monitor" for Evidently and the GCP clients.
ARG UV_GROUPS=""

# Dependencies first so this layer is cached until uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-default-groups $UV_GROUPS --no-install-project --no-editable

COPY README.md ./
COPY src ./src
RUN uv sync --frozen --no-default-groups $UV_GROUPS --no-editable


# Runtime stage: only the virtualenv, the model and the built site, no uv, no source tree.
FROM python:3.11-slim

# LightGBM needs OpenMP at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY models ./models
COPY --from=site /site/dist ./web

ENV PATH="/app/.venv/bin:$PATH" \
    MODEL_DIR=/app/models \
    WEB_DIR=/app/web \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 8080

# Cloud Run passes the port in $PORT.
CMD ["sh", "-c", "exec uvicorn pawnlink.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
