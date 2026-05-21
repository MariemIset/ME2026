FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libgomp1 libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY pyproject.toml ./
COPY src ./src
COPY sql ./sql
COPY scripts ./scripts

RUN pip install -e .

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "churn_ml.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
