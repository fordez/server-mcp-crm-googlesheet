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
    def resolve_client_id(client_id_or_phone: str) -> str | None:
        """
        Resuelve el client_id real a partir de un UUID o un teléfono.
        Retorna el client_id si existe, sino None.
        """
        if not client_id_or_phone:
            return None

        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.worksheet(SHEET_NAME)
        all_records = worksheet.get_all_records()
        phone_norm = "".join(filter(str.isdigit, str(client_id_or_phone)))

        for row in all_records:
            if str(row.get("Id")) == str(client_id_or_phone):
                return row.get("Id")
            if "".join(filter(str.isdigit, str(row.get("Telefono")))) == phone_norm:
                return row.get("Id")
        return None

    @staticmethod
    def verify_client(telefono=None, correo=None, usuario=None) -> dict:
        """
        Verifica si un cliente existe en el CRM usando teléfono, correo o usuario.

        Args:
            telefono: Número de teléfono del cliente
            correo: Email del cliente
            usuario: Usuario del cliente

        Returns:
            dict: Información completa del cliente si existe, incluyendo:
                - exists: bool indicando si el cliente existe
                - client_id: ID único del cliente
                - nombre, telefono, correo, tipo, estado, canal, nota, usuario
                - fecha_creacion: Fecha de creación del registro
                - fecha_conversion: Fecha de conversión (si aplica)
                - thread_id: ID del hilo de conversación
                - matched_by: Campo por el cual se encontró el cliente
        """
        try:
            if not telefono and not correo and not usuario:
                return {"error": "Debe proporcionar al menos un identificador"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()
            telefono_norm = (
                "".join(filter(str.isdigit, str(telefono))) if telefono else ""
            )

            for row in all_records:
                matched_by = None
                if (
                    telefono
                    and "".join(filter(str.isdigit, str(row.get("Telefono"))))
                    == telefono_norm
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
                        "fecha_creacion": row.get("Fecha Creacion"),
                        "fecha_conversion": row.get("Fecha Conversion"),
                        "thread_id": row.get("Thread_Id"),
                        "matched_by": matched_by,
                    }

            return {"exists": False, "client_id": None}

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def create_client(
        nombre,
        canal,
        telefono=None,
        correo=None,
        nota=None,
        usuario=None,
        thread_id=None,
    ) -> dict:
        """
        Crea un nuevo cliente en el CRM.

        Args:
            nombre: Nombre completo del cliente (requerido)
            canal: Canal de origen (requerido)
            telefono: Número de teléfono del cliente
            correo: Email del cliente
            nota: Notas adicionales sobre el cliente
            usuario: Usuario asociado al cliente
            thread_id: ID del hilo de conversación

        Returns:
            dict: Información del cliente creado incluyendo:
                - success: bool indicando si la operación fue exitosa
                - client_id: ID único generado para el cliente
                - nombre, canal: Datos básicos del cliente
                - thread_id: ID del hilo asignado
        """
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

            # Columnas: Id | Nombre | Telefono | Correo | Tipo | Estado | Nota | Usuario | Canal | Fecha Creacion | Fecha Conversion | Thread_Id
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
            worksheet.update_cell(next_row, 12, thread_id or "")

            return {
                "success": True,
                "client_id": client_id,
                "nombre": nombre,
                "canal": canal,
                "thread_id": thread_id,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_client_dynamic(client_id: str, fields: dict) -> dict:
        """
        Actualiza campos dinámicamente de un cliente existente.

        Args:
            client_id: ID del cliente o número de teléfono
            fields: Diccionario con los campos a actualizar
                Campos disponibles: "Nombre", "Telefono", "Correo", "Tipo", "Estado",
                "Nota", "Usuario", "Canal", "Fecha Creacion", "Fecha Conversion", "Thread_Id"
                Ejemplo: {"Estado": "Activo", "Nota": "Cliente interesado"}

        Returns:
            dict: Resultado de la actualización incluyendo:
                - success: bool indicando si la operación fue exitosa
                - client_id: ID del cliente actualizado
                - updated_fields: Lista de campos que fueron actualizados
        """
        try:
            if not client_id:
                return {"success": False, "error": "client_id requerido"}
            if not fields:
                return {"success": False, "error": "No se proporcionaron campos"}

            resolved_id = CRMService.resolve_client_id(client_id)
            if not resolved_id:
                return {
                    "success": False,
                    "error": f"No se encontró cliente con ID o teléfono '{client_id}'",
                }

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME)
            all_records = worksheet.get_all_records()
            updated_fields = []

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
                "Thread_Id": 12,
            }

            for idx, row in enumerate(all_records, start=2):
                if str(row.get("Id")) == str(resolved_id):
                    for key, value in fields.items():
                        col = col_map.get(key)
                        if col:
                            worksheet.update_cell(idx, col, value)
                            updated_fields.append(key)
                    return {
                        "success": True,
                        "client_id": resolved_id,
                        "updated_fields": updated_fields,
                    }

            return {
                "success": False,
                "error": f"Cliente con ID '{resolved_id}' no encontrado",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
