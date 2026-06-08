FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OXYTAIL_DATABASE_URL=sqlite:////data/oxytail.db \
    OXYTAIL_SECRET_KEY=change-me-in-production

WORKDIR /app

COPY pyproject.toml README.md package.json package-lock.json ./
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

RUN pip install --upgrade pip \
    && pip install -e ".[demo]"

RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000

CMD ["uvicorn", "examples.demo.main:app", "--host", "0.0.0.0", "--port", "8000"]
