# syntax=docker/dockerfile:1.6
FROM python:3.12-slim

# ---------- системные зависимости ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---------- poetry + сопутствующие зависимости ----------
ENV POETRY_VIRTUALENVS_CREATE=false
RUN pip install --no-cache-dir poetry==1.8.2

WORKDIR /app
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-interaction --no-root

# ---------- приложение ----------
COPY . /app
EXPOSE 8000
CMD ["bash", "scripts/start.sh"]