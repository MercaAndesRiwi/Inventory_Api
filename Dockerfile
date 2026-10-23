# ============================================================
# Dockerfile - api-inventory
# Image for deterministic inventory and seller catalog (F3)
# ============================================================
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY src ./src
RUN uv sync --frozen --no-dev

ENV APP_ENV=production
ENV PYTHONPATH=/app/src

ENTRYPOINT ["uv", "run", "uvicorn", "inventory.presentation.fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
