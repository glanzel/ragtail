FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OXYTAIL_DATABASE_URL=sqlite:////data/oxytail.db \
    OXYTAIL_SECRET_KEY=change-me-in-production

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY examples/demo ./examples/demo

RUN pip install --upgrade pip \
    && pip install -e ".[demo]"

RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000

CMD ["uvicorn", "examples.demo.main:app", "--host", "0.0.0.0", "--port", "8000"]
