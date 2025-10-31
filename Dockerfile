# Use a slim official Python image
FROM python:3.11-slim

# Avoid Python writing .pyc files and buffer stdout (useful for logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    POETRY_VIRTUALENVS_CREATE=false

# Cloud Run provides a PORT env var; default to 8000 for local runs
ENV PORT=8000

WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install system deps if needed (add here if your requirements need build tools)
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential curl ca-certificates \
  && pip install --upgrade pip \
  && pip install -r requirements.txt \
  && apt-get remove -y build-essential \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/*

# Copy app code
COPY . /app

# Create non-root user
RUN groupadd -r app && useradd -r -g app app \
    && chown -R app:app /app

USER app

# Expose the port (informational)
EXPOSE 8000

# Entrypoint: use PORT env var set by Cloud Run, default to 8000 locally
# Use sh -c so env substitution ${PORT} works
CMD ["sh", "-c", "fastmcp run mcp.py:mcp --transport http --port ${PORT:-8000}"]
