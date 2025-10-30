"""
Módulo de configuración para gestionar entornos de producción y desarrollo.
Selecciona automáticamente las credenciales y configuraciones según ENVIRONMENT.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Clase de configuración que maneja entornos prod/dev automáticamente."""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "production").lower()
        self._load_environment_config()

    def _load_environment_config(self):
        """Carga configuración según el entorno activo."""
        is_prod = self.environment == "production"

        # ====================================================
        # Google Sheets Configuration
        # ====================================================
        self.service_account_file = os.getenv(
            f"SERVICE_ACCOUNT_FILE_{'PROD' if is_prod else 'DEV'}", "credentials.json"
        )
        self.spreadsheet_id = os.getenv(
            f"SPREADSHEET_ID_{'PROD' if is_prod else 'DEV'}"
        )
        self.scopes = [
            os.getenv("SCOPES", "https://www.googleapis.com/auth/spreadsheets")
        ]

        # Sheet names
        self.sheet_name = os.getenv("SHEET_NAME", "Lead")
        self.sheet_name_crm = os.getenv("SHEET_NAME_CRM", "Lead")
        self.sheet_name_catalog = os.getenv("SHEET_NAME_CATALOG", "Services")
        self.sheet_name_meetings = os.getenv("SHEET_NAME_MEETINGS", "Meetings")
        self.sheet_name_projects = os.getenv("SHEET_NAME_PROJECTS", "Projects")

        # ====================================================
        # Google Calendar & Meet Configuration
        # ====================================================
        self.client_secret_file = os.getenv(
            f"CLIENT_SECRET_FILE_{'PROD' if is_prod else 'DEV'}",
            "meet-credentials.json",
        )
        self.token_file = os.getenv(
            f"TOKEN_FILE_{'PROD' if is_prod else 'DEV'}", "token.json"
        )
        self.gcal_calendar_id = os.getenv(
            f"GCAL_CALENDAR_ID_{'PROD' if is_prod else 'DEV'}"
        )

        # ====================================================
        # Server Configuration
        # ====================================================
        self.mcp_server_port = int(os.getenv("MCP_SERVER_PORT", 8000))
        self.timezone = os.getenv("TIMEZONE", "America/Argentina/Buenos_Aires")

        # ====================================================
        # Cache & Logs
        # ====================================================
        self.cache_dir = os.getenv("CACHE_DIR", "./cache")
        self.log_dir = os.getenv("LOG_DIR", "./logs")

        # Crear directorios si no existen
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

    def is_production(self) -> bool:
        """Verifica si el entorno actual es producción."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Verifica si el entorno actual es desarrollo."""
        return self.environment == "development"

    def get_environment(self) -> str:
        """Retorna el entorno actual."""
        return self.environment

    def print_config(self):
        """Imprime la configuración actual (útil para debugging)."""
        print("\n" + "=" * 60)
        print(f"🔧 CONFIGURACIÓN DEL SERVIDOR MCP")
        print("=" * 60)
        print(f"🌍 Entorno: {self.environment.upper()}")
        print(f"📋 Spreadsheet ID: {self.spreadsheet_id}")
        print(f"🔑 Service Account: {self.service_account_file}")
        print(f"📅 Calendar ID: {self.gcal_calendar_id}")
        print(f"🔌 Puerto: {self.mcp_server_port}")
        print(f"🕐 Timezone: {self.timezone}")
        print(f"📂 Logs: {self.log_dir}")
        print("=" * 60 + "\n")


# Instancia global de configuración
config = Config()


# Función helper para obtener configuración
def get_config() -> Config:
    """Retorna la instancia global de configuración."""
    return config


# Validación de configuración al importar
if not config.spreadsheet_id:
    raise ValueError(
        f"❌ ERROR: SPREADSHEET_ID_{config.environment.upper()} no está configurado en .env"
    )

if not config.gcal_calendar_id:
    raise ValueError(
        f"❌ ERROR: GCAL_CALENDAR_ID_{config.environment.upper()} no está configurado en .env"
    )
