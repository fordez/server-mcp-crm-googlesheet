import os
import logging
from dotenv import load_dotenv
from services.google_sheet.gspread_helper import (
    get_gspread_client,
)  # ✅ usamos tu módulo compartido

load_dotenv()
logger = logging.getLogger(__name__)

# ====================================================
# 🔧 CONFIGURACIÓN
# ====================================================
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "secrets/credentials.json")
SCOPES = [os.getenv("SCOPES", "https://www.googleapis.com/auth/spreadsheets")]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME_CATALOG", "Services")

# Inicializamos el cliente compartido
gc = get_gspread_client(SERVICE_ACCOUNT_FILE, SCOPES, service_name="CatalogService")


class CatalogService:
    @staticmethod
    def get_all_services() -> dict:
        """
        Obtiene todos los servicios del catálogo desde Google Sheets.
        """
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()
            return {"success": True, "services": all_records}
        except Exception as e:
            logger.error(f"❌ Error al obtener todos los servicios: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_service_by_name(service_name: str) -> dict:
        """
        Busca un servicio por su nombre dentro del catálogo.
        """
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()

            for row in all_records:
                if str(row.get("Nombre")).strip().lower() == service_name.lower():
                    return {"success": True, "service": row}

            return {"success": False, "error": "Servicio no encontrado"}
        except Exception as e:
            logger.error(f"❌ Error al obtener servicio '{service_name}': {e}")
            return {"success": False, "error": str(e)}
