import gspread
from google.oauth2.service_account import Credentials
import pytz
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================
# 🔧 CONFIGURACIÓN
# ==========================
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "credentials.json")
SCOPES = [os.getenv("SCOPES", "https://www.googleapis.com/auth/spreadsheets")]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME_MEETINGS = os.getenv("SHEET_NAME_MEETINGS", "Meetings")
TIMEZONE = os.getenv("TIMEZONE", "America/Argentina/Buenos_Aires")

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)


# ==========================
# 🧩 SERVICIO DE REUNIONES
# ==========================
class MeetingService:
    @staticmethod
    def create_meeting(
        calendar_id: str,
        asunto: str,
        fecha_inicio: str,
        id_cliente: str,
        detalles: str = None,
        meet_link: str = None,
        calendar_link: str = None,
        estado: str = "Programada",
    ) -> dict:
        """
        Crea una nueva reunión en la hoja de Meetings.
        Usa el calendar_id como ID principal.
        """
        try:
            if not calendar_id or not asunto or not fecha_inicio or not id_cliente:
                return {
                    "success": False,
                    "error": "Campos requeridos: calendar_id, asunto, fecha_inicio e id_cliente",
                }

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_MEETINGS)
            all_records = worksheet.get_all_records()

            tz = pytz.timezone(TIMEZONE)
            fecha_creada = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            next_row = len(all_records) + 2

            # Columnas: Id | Asunto | Detalles | Fecha Inicio | Meet_Link | Calendar_Link | Estado | Fecha Creada | Id Cliente
            worksheet.update_cell(next_row, 1, calendar_id)
            worksheet.update_cell(next_row, 2, asunto)
            worksheet.update_cell(next_row, 3, detalles or "")
            worksheet.update_cell(next_row, 4, fecha_inicio)
            worksheet.update_cell(next_row, 5, meet_link or "")
            worksheet.update_cell(next_row, 6, calendar_link or "")
            worksheet.update_cell(next_row, 7, estado)
            worksheet.update_cell(next_row, 8, fecha_creada)
            worksheet.update_cell(next_row, 9, id_cliente)

            return {
                "success": True,
                "calendar_id": calendar_id,
                "asunto": asunto,
                "fecha_inicio": fecha_inicio,
                "id_cliente": id_cliente,
                "estado": estado,
                "fecha_creada": fecha_creada,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================
    # 🔍 CONSULTAS
    # ==========================
    @staticmethod
    def get_meeting_by_id(calendar_id: str) -> dict:
        """Consulta una reunión por su ID (Calendar ID)."""
        try:
            if not calendar_id:
                return {"success": False, "error": "calendar_id requerido"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_MEETINGS)
            all_records = worksheet.get_all_records()

            for row in all_records:
                if str(row.get("Id")) == str(calendar_id):
                    return {"success": True, "meeting": row}

            return {
                "success": False,
                "error": f"No se encontró reunión con ID '{calendar_id}'",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_meetings_by_client(id_cliente: str) -> dict:
        """Consulta todas las reuniones de un cliente específico."""
        try:
            if not id_cliente:
                return {"success": False, "error": "id_cliente requerido"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_MEETINGS)
            all_records = worksheet.get_all_records()

            meetings = [
                row
                for row in all_records
                if str(row.get("Id Cliente")) == str(id_cliente)
            ]

            return {"success": True, "count": len(meetings), "meetings": meetings}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_meetings_by_date(fecha_inicio: str) -> dict:
        """Consulta reuniones por fecha de inicio."""
        try:
            if not fecha_inicio:
                return {"success": False, "error": "fecha_inicio requerida"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_MEETINGS)
            all_records = worksheet.get_all_records()

            fecha_busqueda = fecha_inicio[:10]
            meetings = [
                row
                for row in all_records
                if str(row.get("Fecha Inicio"))[:10] == fecha_busqueda
            ]

            return {
                "success": True,
                "fecha": fecha_busqueda,
                "count": len(meetings),
                "meetings": meetings,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================
    # ✏️ ACTUALIZAR / ELIMINAR
    # ==========================
    @staticmethod
    def update_meeting(calendar_id: str, fields: dict) -> dict:
        """Actualiza campos de una reunión usando el Calendar ID."""
        try:
            if not calendar_id:
                return {"success": False, "error": "calendar_id requerido"}
            if not fields:
                return {"success": False, "error": "No se proporcionaron campos"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_MEETINGS)
            all_records = worksheet.get_all_records()

            col_map = {
                "Id": 1,
                "Asunto": 2,
                "Detalles": 3,
                "Fecha Inicio": 4,
                "Meet_Link": 5,
                "Calendar_Link": 6,
                "Estado": 7,
                "Fecha Creada": 8,
                "Id Cliente": 9,
            }

            for idx, row in enumerate(all_records, start=2):
                if str(row.get("Id")) == str(calendar_id):
                    for key, value in fields.items():
                        col = col_map.get(key)
                        if col:
                            worksheet.update_cell(idx, col, value)
                    return {
                        "success": True,
                        "calendar_id": calendar_id,
                        "updated_fields": list(fields.keys()),
                    }

            return {
                "success": False,
                "error": f"No se encontró reunión con ID '{calendar_id}'",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_meeting(calendar_id: str) -> dict:
        """Elimina una reunión usando el Calendar ID."""
        try:
            if not calendar_id:
                return {"success": False, "error": "calendar_id requerido"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_MEETINGS)
            all_records = worksheet.get_all_records()

            for idx, row in enumerate(all_records, start=2):
                if str(row.get("Id")) == str(calendar_id):
                    worksheet.delete_rows(idx)
                    return {
                        "success": True,
                        "message": f"Reunión '{calendar_id}' eliminada",
                    }

            return {
                "success": False,
                "error": f"No se encontró reunión con ID '{calendar_id}'",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
