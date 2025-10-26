# crm_service.py
import gspread
from google.oauth2.service_account import Credentials
import pytz
from datetime import datetime
import shortuuid
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración desde .env
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "credentials.json")
SCOPES = [os.getenv("SCOPES", "https://www.googleapis.com/auth/spreadsheets")]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Lead")
TIMEZONE = os.getenv("TIMEZONE", "America/Argentina/Buenos_Aires")

# Inicializar cliente de Google Sheets
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)


class CRMService:
    """
    Servicio para gestionar operaciones del CRM en Google Sheets.

    Estructura de la hoja:
    Columna 1: Id
    Columna 2: Nombre
    Columna 3: Telefono
    Columna 4: Correo
    Columna 5: Tipo
    Columna 6: Estado
    Columna 7: Nota
    Columna 8: Usuario
    Columna 9: Canal
    Columna 10: Fecha Adquisición
    Columna 11: Fecha Conversion
    """

    @staticmethod
    def verify_client(
        telefono: str = None, correo: str = None, usuario: str = None
    ) -> dict:
        """
        Verifica si un cliente (lead) ya existe en el CRM buscando por cualquier identificador.
        """
        try:
            if not telefono and not correo and not usuario:
                return {
                    "error": "Debe proporcionar al menos un identificador: telefono, correo o usuario"
                }

            def normalize_phone(phone: str) -> str:
                """Elimina símbolos, espacios y deja solo los números."""
                if not phone:
                    return ""
                return "".join(filter(str.isdigit, str(phone)))

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()

            telefono_normalizado = normalize_phone(telefono)

            for row in all_records:
                matched_by = None

                # 🔹 Búsqueda por teléfono (normalizado)
                if (
                    telefono
                    and normalize_phone(row.get("Telefono")) == telefono_normalizado
                ):
                    matched_by = "telefono"

                # 🔹 Búsqueda por correo (insensible a mayúsculas)
                elif correo and str(row.get("Correo")).lower() == str(correo).lower():
                    matched_by = "correo"

                # 🔹 Búsqueda por usuario asignado
                elif usuario and str(row.get("Usuario")) == str(usuario):
                    matched_by = "usuario"

                if matched_by:
                    print(
                        f"[LOG] Cliente encontrado por {matched_by}: {row.get('Nombre')}"
                    )
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

            print("[LOG] Cliente no encontrado en el sistema")
            return {
                "exists": False,
                "client_id": None,
                "nombre": None,
                "telefono": None,
                "correo": None,
                "tipo": None,
                "estado": None,
                "canal": None,
                "nota": None,
                "usuario": None,
                "matched_by": None,
            }

        except Exception as e:
            print(f"[ERROR] verify_client: {e}")
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
        """Crea un nuevo cliente (lead) en el CRM con ID autogenerado."""
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

            # Generar ID único de 6 caracteres alfanuméricos
            client_id = shortuuid.ShortUUID().random(length=6)

            # Determinar la próxima fila disponible
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

            print(f"[LOG] Cliente creado: {nombre} (ID: {client_id}, Canal: {canal})")
            return {
                "success": True,
                "client_id": client_id,
                "nombre": nombre,
                "canal": canal,
                "message": "Cliente creado exitosamente",
            }

        except Exception as e:
            print(f"[ERROR] create_client: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_client(
        client_id: str,
        nombre: str = None,
        telefono: str = None,
        correo: str = None,
        tipo: str = None,
        estado: str = None,
        nota: str = None,
        usuario: str = None,
        fecha_conversion: str = None,
    ) -> dict:
        """Actualiza los datos de un cliente existente usando su ID único."""
        try:
            if not client_id:
                return {"success": False, "error": "El campo 'client_id' es requerido"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()

            updated_fields = []

            for idx, row in enumerate(all_records, start=2):
                if str(row.get("Id")) == str(client_id):
                    if nombre is not None:
                        worksheet.update_cell(idx, 2, nombre)
                        updated_fields.append("Nombre")
                    if telefono is not None:
                        worksheet.update_cell(idx, 3, telefono)
                        updated_fields.append("Telefono")
                    if correo is not None:
                        worksheet.update_cell(idx, 4, correo)
                        updated_fields.append("Correo")
                    if tipo is not None:
                        worksheet.update_cell(idx, 5, tipo)
                        updated_fields.append("Tipo")
                    if estado is not None:
                        worksheet.update_cell(idx, 6, estado)
                        updated_fields.append("Estado")
                    if nota is not None:
                        worksheet.update_cell(idx, 7, nota)
                        updated_fields.append("Nota")
                    if usuario is not None:
                        worksheet.update_cell(idx, 8, usuario)
                        updated_fields.append("Usuario")
                    if fecha_conversion is not None:
                        worksheet.update_cell(idx, 11, fecha_conversion)
                        updated_fields.append("Fecha Conversion")

                    print(
                        f"[LOG] Cliente actualizado: {client_id} - Campos: {updated_fields}"
                    )
                    return {
                        "success": True,
                        "client_id": client_id,
                        "updated_fields": updated_fields,
                        "message": f"Cliente actualizado: {len(updated_fields)} campos modificados",
                    }

            print(f"[LOG] Cliente no encontrado: {client_id}")
            return {
                "success": False,
                "error": f"Cliente con ID '{client_id}' no encontrado",
            }

        except Exception as e:
            print(f"[ERROR] update_client: {e}")
            return {"success": False, "error": str(e)}
