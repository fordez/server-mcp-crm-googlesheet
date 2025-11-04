import os
import json
import logging

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        is_prod = self.environment == "production"

        # SECRETOS
        if is_prod:
            # Leer los JSON directamente desde las variables de entorno
            self.service_account_json = json.loads(os.getenv("SERVICE_ACCOUNT_FILE"))
            self.client_secret_json = json.loads(os.getenv("CLIENT_SECRET_FILE"))
            self.token_json = json.loads(os.getenv("TOKEN_FILE"))
        else:
            # Local/desarrollo: leer desde archivos
            import pathlib

            with open(
                os.getenv("SERVICE_ACCOUNT_FILE", "secrets/credentials-dev.json")
            ) as f:
                self.service_account_json = json.load(f)
            with open(
                os.getenv("CLIENT_SECRET_FILE", "secrets/meet-credentials-dev.json")
            ) as f:
                self.client_secret_json = json.load(f)
            with open(os.getenv("TOKEN_FILE", "secrets/token-dev.json")) as f:
                self.token_json = json.load(f)

        # Variables no sensibles desde .env
        self.spreadsheet_id = os.getenv("SPREADSHEET_ID")
        self.sheet_name = os.getenv("SHEET_NAME")
        self.sheet_name_catalog = os.getenv("SHEET_NAME_CATALOG")
        self.sheet_name_meetings = os.getenv("SHEET_NAME_MEETINGS")
        self.sheet_name_projects = os.getenv("SHEET_NAME_PROJECTS")
        self.scopes = [os.getenv("SCOPES")]
        self.timezone = os.getenv("TIMEZONE")
        self.mcp_server_port = int(os.getenv("MCP_SERVER_PORT", 8080))
        self.cache_dir = os.getenv("CACHE_DIR", "./cache")
        self.log_dir = os.getenv("LOG_DIR", "./logs")

        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)


logger.info("✅ Configuración cargada correctamente")
config = Config()
