import gspread
from google.oauth2.service_account import Credentials
import pytz
from datetime import datetime
import shortuuid
import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "credentials.json")
SCOPES = [os.getenv("SCOPES", "https://www.googleapis.com/auth/spreadsheets")]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Lead")
TIMEZONE = os.getenv("TIMEZONE", "America/Argentina/Buenos_Aires")

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)


class CRMService:
    @staticmethod
    def verify_client(
        telefono: str = None, correo: str = None, usuario: str = None
    ) -> dict:
        """Verifica si un cliente existe."""
        try:
            if not telefono and not correo and not usuario:
                return {
                    "error": "Debe proporcionar al menos un identificador: telefono, correo o usuario"
                }

            def normalize_phone(phone: str) -> str:
                return "".join(filter(str.isdigit, str(phone))) if phone else ""

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()
            telefono_normalizado = normalize_phone(telefono)

            for row in all_records:
                matched_by = None
                if (
                    telefono
                    and normalize_phone(row.get("Telefono")) == telefono_normalizado
                ):
                    matched_by = "telefono"
                elif correo and str(row.get("Correo")).lower() == str(correo).lower():
                    matched_by = "correo"
                elif usuario and str(row.get("Usuario")) == str(usuario):
                    matched_by = "usuario"

                if matched_by:
                    return {
                        "exists": True,
                        "client_id": row.get("Id"),
                        "nombre": row.get("Nombre"),
                        "telefono": row.get("Telefono"),
                        "correo": row.get("Correo"),
                        "tipo": row.get("Tipo"),
                        "estado": row.get("Estado"),
                        "canal": row.get("Canal"),
                        "nota": row.get("Nota"),
                        "usuario": row.get("Usuario"),
                        "matched_by": matched_by,
                    }

            return {"exists": False, "client_id": None}

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def create_client(
        nombre: str,
        canal: str,
        telefono: str = None,
        correo: str = None,
        nota: str = None,
        usuario: str = None,
    ) -> dict:
        """Crea un nuevo cliente (lead)."""
        try:
            if not nombre or not canal:
                return {
                    "success": False,
                    "error": "Los campos 'nombre' y 'canal' son requeridos",
                }

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()

            tz = pytz.timezone(TIMEZONE)
            fecha_actual = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            client_id = shortuuid.ShortUUID().random(length=6)
            next_row = len(all_records) + 2

            worksheet.update_cell(next_row, 1, client_id)
            worksheet.update_cell(next_row, 2, nombre)
            worksheet.update_cell(next_row, 3, telefono or "")
            worksheet.update_cell(next_row, 4, correo or "")
            worksheet.update_cell(next_row, 5, "Lead")
            worksheet.update_cell(next_row, 6, "Nuevo")
            worksheet.update_cell(next_row, 7, nota or "")
            worksheet.update_cell(next_row, 8, usuario or "")
            worksheet.update_cell(next_row, 9, canal)
            worksheet.update_cell(next_row, 10, fecha_actual)
            worksheet.update_cell(next_row, 11, "")

            return {
                "success": True,
                "client_id": client_id,
                "nombre": nombre,
                "canal": canal,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_client(
        client_id: str,
        nombre: str = None,
        telefono: str = None,
        correo: str = None,
        tipo: str = None,
        usuario: str = None,
        fecha_conversion: str = None,
    ) -> dict:
        """Actualiza solo datos generales, sin tocar estado ni nota."""
        try:
            if not client_id:
                return {"success": False, "error": "El campo 'client_id' es requerido"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()
            updated_fields = []

            for idx, row in enumerate(all_records, start=2):
                if str(row.get("Id")) == str(client_id):
                    if nombre:
                        worksheet.update_cell(idx, 2, nombre)
                        updated_fields.append("Nombre")
                    if telefono:
                        worksheet.update_cell(idx, 3, telefono)
                        updated_fields.append("Telefono")
                    if correo:
                        worksheet.update_cell(idx, 4, correo)
                        updated_fields.append("Correo")
                    if tipo:
                        worksheet.update_cell(idx, 5, tipo)
                        updated_fields.append("Tipo")
                    if usuario:
                        worksheet.update_cell(idx, 8, usuario)
                        updated_fields.append("Usuario")
                    if fecha_conversion:
                        worksheet.update_cell(idx, 11, fecha_conversion)
                        updated_fields.append("Fecha Conversion")
                    return {
                        "success": True,
                        "client_id": client_id,
                        "updated_fields": updated_fields,
                    }

            return {
                "success": False,
                "error": f"Cliente con ID '{client_id}' no encontrado",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_client_dynamic(client_id: str, fields: dict) -> dict:
        """Actualiza cualquier campo dinámicamente según el diccionario `fields`."""
        try:
            if not client_id:
                return {"success": False, "error": "El campo 'client_id' es requerido"}
            if not fields:
                return {
                    "success": False,
                    "error": "No se proporcionaron campos para actualizar",
                }

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()
            updated_fields = []

            # Mapeo de columnas
            col_map = {
                "Id": 1,
                "Nombre": 2,
                "Telefono": 3,
                "Correo": 4,
                "Tipo": 5,
                "Estado": 6,
                "Nota": 7,
                "Usuario": 8,
                "Canal": 9,
                "Fecha Creacion": 10,
                "Fecha Conversion": 11,
            }

            for idx, row in enumerate(all_records, start=2):
                if str(row.get("Id")) == str(client_id):
                    for key, value in fields.items():
                        col = col_map.get(key)
                        if col:
                            worksheet.update_cell(idx, col, value)
                            updated_fields.append(key)
                    return {
                        "success": True,
                        "client_id": client_id,
                        "updated_fields": updated_fields,
                    }

            return {
                "success": False,
                "error": f"Cliente con ID '{client_id}' no encontrado",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
