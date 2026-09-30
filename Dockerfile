# Dockerfile for kite-python-x402-template
#
# Multi-stage build:
#   1. base     — install OS deps + create venv
#   2. lint     — run ruff + mypy (CI gate)
#   3. test     — run pytest
#   4. runtime  — production image (copy venv + source only)
#
# Build & run:
#   docker build -t kite-x402-py .
#   docker run -p 8080:8080 --env-file .env kite-x402-py

# ---- Base stage ----
FROM python:3.14-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Production stage ----
FROM base AS runtime

COPY kite.py server.py service.yaml ./
COPY test/ ./test/

EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
