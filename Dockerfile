# Imagen base ligera
FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . .

# Copiar archivo .env (para entorno local o debug)
# Cloud Run puede inyectar sus propias variables, pero esto asegura fallback
COPY .env .env

# Establecer variable de entorno para el puerto (Cloud Run la usa)
ENV PORT=8080

# Exponer el puerto
EXPOSE 8080

# Comando para ejecutar el servidor MCP
# Aquí cargamos las variables del .env automáticamente con python-dotenv
CMD ["bash", "-c", "export $(grep -v '^#' .env | xargs) && fastmcp run mcp.py:mcp --transport http --port ${PORT}"]
