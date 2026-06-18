FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    RAGTAIL_DATABASE_URL=sqlite:////data/ragtail.db \
    RAGTAIL_SECRET_KEY=change-me-in-production

WORKDIR /app

COPY pyproject.toml uv.lock README.md package.json package-lock.json oxyde_config.py ./
COPY scripts ./scripts
COPY styles ./styles
COPY tailwind.config.js ./
COPY src ./src
COPY examples/demo ./examples/demo

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates nodejs npm \
    && rm -rf /var/lib/apt/lists/* \
    && npm ci \
    && npm run build:css

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --extra demo --no-editable

RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "examples.demo.main:app", "--host", "0.0.0.0", "--port", "8000"]
