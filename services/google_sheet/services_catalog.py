import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "credentials.json")
SCOPES = [os.getenv("SCOPES", "https://www.googleapis.com/auth/spreadsheets")]

# Usar la hoja correcta del catálogo
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")  # Puede ser la misma que CRM
SHEET_NAME = os.getenv("SHEET_NAME_CATALOG", "Services")  # <- Aquí cambió

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)


class CatalogService:
    @staticmethod
    def get_all_services() -> dict:
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()
            return {"success": True, "services": all_records}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_service_by_name(service_name: str) -> dict:
        try:
            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()
            for row in all_records:
                if str(row.get("Nombre")).lower() == service_name.lower():
                    return {"success": True, "service": row}
            return {"success": False, "error": "Servicio no encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
