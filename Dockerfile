# ====================================================
# 🐍 Base image
# ====================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# ====================================================
# 📦 Instalar dependencias del sistema
# ====================================================
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc g++ build-essential curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# ====================================================
# 📥 Copiar e instalar dependencias de Python
# ====================================================
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# ====================================================
# 📂 Copiar código fuente
# ====================================================
COPY . /app

# Crear directorios necesarios
RUN mkdir -p /tmp /app/cache /app/logs \
 && chmod 777 /tmp /app/cache /app/logs

# ====================================================
# 👤 Usuario no-root
# ====================================================
RUN groupadd -r app && useradd -r -g app app \
 && chown -R app:app /app /tmp
USER app

# ====================================================
# 🚀 Entrada
# ====================================================
EXPOSE 8080

CMD echo "🚀 Starting AG-CRM MCP Server..." && \
    echo "PORT=$PORT" && \
    echo "ENVIRONMENT=$ENVIRONMENT" && \
    python main.py
