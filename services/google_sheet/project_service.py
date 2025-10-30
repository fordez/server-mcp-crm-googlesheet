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
SHEET_NAME_PROJECTS = os.getenv("SHEET_NAME_PROJECTS", "Projects")
TIMEZONE = os.getenv("TIMEZONE", "America/Argentina/Buenos_Aires")

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)


# ==========================
# 🧩 SERVICIO DE PROYECTOS
# ==========================
class ProjectService:
    @staticmethod
    def create_project(
        nombre: str,
        id_cliente: str,
        servicio: str = None,
        descripcion: str = None,
        fecha_inicio: str = None,
        fecha_fin: str = None,
        estado: str = "En Progreso",
        nota: str = None,
    ) -> dict:
        """
        Crea un nuevo proyecto en la hoja de Projects.

        Args:
            nombre: Nombre del proyecto (requerido)
            id_cliente: ID del cliente asociado (requerido)
            servicio: Servicio relacionado con el proyecto
            descripcion: Descripción del proyecto
            fecha_inicio: Fecha de inicio del proyecto (formato: YYYY-MM-DD HH:MM:SS)
            fecha_fin: Fecha estimada de fin (formato: YYYY-MM-DD HH:MM:SS)
            estado: Estado del proyecto (default: "En Progreso")
            nota: Notas adicionales sobre el proyecto

        Returns:
            dict: Información del proyecto creado incluyendo:
                - success: bool indicando si la operación fue exitosa
                - project_id: ID único generado para el proyecto
                - nombre, id_cliente, estado: Datos básicos del proyecto
                - fecha_creada: Timestamp de creación
        """
        try:
            if not nombre or not id_cliente:
                return {
                    "success": False,
                    "error": "Campos requeridos: nombre e id_cliente",
                }

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_PROJECTS)
            all_records = worksheet.get_all_records()

            tz = pytz.timezone(TIMEZONE)
            fecha_creada = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

            # Generar ID único basado en timestamp
            project_id = f"PRJ-{datetime.now(tz).strftime('%Y%m%d%H%M%S')}"
            next_row = len(all_records) + 2

            # Columnas: Id | Nombre | Descripcion | Servicio | Estado | Nota | Fecha_Inicio | Fecha_Fin | Id_Cliente
            worksheet.update_cell(next_row, 1, project_id)
            worksheet.update_cell(next_row, 2, nombre)
            worksheet.update_cell(next_row, 3, descripcion or "")
            worksheet.update_cell(next_row, 4, servicio or "")
            worksheet.update_cell(next_row, 5, estado)
            worksheet.update_cell(next_row, 6, nota or "")
            worksheet.update_cell(next_row, 7, fecha_inicio or fecha_creada)
            worksheet.update_cell(next_row, 8, fecha_fin or "")
            worksheet.update_cell(next_row, 9, id_cliente)

            return {
                "success": True,
                "project_id": project_id,
                "nombre": nombre,
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
    def get_project_by_id(project_id: str) -> dict:
        """
        Consulta un proyecto específico por su ID.

        Args:
            project_id: ID único del proyecto

        Returns:
            dict: Información completa del proyecto o error si no existe
        """
        try:
            if not project_id:
                return {"success": False, "error": "project_id requerido"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_PROJECTS)
            all_records = worksheet.get_all_records()

            for row in all_records:
                if str(row.get("Id")) == str(project_id):
                    return {"success": True, "project": row}

            return {
                "success": False,
                "error": f"No se encontró proyecto con ID '{project_id}'",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_projects_by_client(id_cliente: str) -> dict:
        """
        Consulta todos los proyectos asociados a un cliente específico.

        Args:
            id_cliente: ID del cliente

        Returns:
            dict: Lista de proyectos del cliente con conteo total
        """
        try:
            if not id_cliente:
                return {"success": False, "error": "id_cliente requerido"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_PROJECTS)
            all_records = worksheet.get_all_records()

            projects = [
                row
                for row in all_records
                if str(row.get("Id_Cliente")) == str(id_cliente)
            ]

            return {"success": True, "count": len(projects), "projects": projects}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_projects_by_date(fecha_inicio: str) -> dict:
        """
        Consulta proyectos por fecha de inicio.

        Args:
            fecha_inicio: Fecha en formato YYYY-MM-DD

        Returns:
            dict: Lista de proyectos que inician en la fecha especificada
        """
        try:
            if not fecha_inicio:
                return {"success": False, "error": "fecha_inicio requerida"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_PROJECTS)
            all_records = worksheet.get_all_records()

            fecha_busqueda = fecha_inicio[:10]
            projects = [
                row
                for row in all_records
                if str(row.get("Fecha_Inicio"))[:10] == fecha_busqueda
            ]

            return {
                "success": True,
                "fecha": fecha_busqueda,
                "count": len(projects),
                "projects": projects,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================
    # ✏️ ACTUALIZAR / ELIMINAR
    # ==========================
    @staticmethod
    def update_project(project_id: str, fields: dict) -> dict:
        """
        Actualiza campos de un proyecto existente.

        Args:
            project_id: ID del proyecto a actualizar
            fields: Diccionario con los campos a actualizar
                Campos disponibles: "Nombre", "Descripcion", "Servicio", "Estado",
                "Nota", "Fecha_Inicio", "Fecha_Fin", "Id_Cliente"
                Ejemplo: {"Estado": "Completado", "Nota": "Proyecto finalizado exitosamente"}

        Returns:
            dict: Resultado de la actualización con lista de campos modificados
        """
        try:
            if not project_id:
                return {"success": False, "error": "project_id requerido"}
            if not fields:
                return {"success": False, "error": "No se proporcionaron campos"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_PROJECTS)
            all_records = worksheet.get_all_records()

            col_map = {
                "Id": 1,
                "Nombre": 2,
                "Descripcion": 3,
                "Servicio": 4,
                "Estado": 5,
                "Nota": 6,
                "Fecha_Inicio": 7,
                "Fecha_Fin": 8,
                "Id_Cliente": 9,
            }

            for idx, row in enumerate(all_records, start=2):
                if str(row.get("Id")) == str(project_id):
                    for key, value in fields.items():
                        col = col_map.get(key)
                        if col:
                            worksheet.update_cell(idx, col, value)
                    return {
                        "success": True,
                        "project_id": project_id,
                        "updated_fields": list(fields.keys()),
                    }

            return {
                "success": False,
                "error": f"No se encontró proyecto con ID '{project_id}'",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_project_note_by_client(id_cliente: str, nota: str) -> dict:
        """
        Actualiza la nota de todos los proyectos asociados a un cliente.

        Args:
            id_cliente: ID del cliente cuyos proyectos se actualizarán
            nota: Nueva nota a agregar a todos los proyectos del cliente

        Returns:
            dict: Resultado indicando cuántos proyectos fueron actualizados
        """
        try:
            if not id_cliente:
                return {"success": False, "error": "id_cliente requerido"}
            if not nota:
                return {"success": False, "error": "nota requerida"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_PROJECTS)
            all_records = worksheet.get_all_records()

            updated_count = 0
            updated_projects = []

            for idx, row in enumerate(all_records, start=2):
                if str(row.get("Id_Cliente")) == str(id_cliente):
                    worksheet.update_cell(idx, 6, nota)  # Columna 6 = Nota
                    updated_count += 1
                    updated_projects.append(row.get("Id"))

            if updated_count == 0:
                return {
                    "success": False,
                    "error": f"No se encontraron proyectos para el cliente '{id_cliente}'",
                }

            return {
                "success": True,
                "id_cliente": id_cliente,
                "updated_count": updated_count,
                "updated_projects": updated_projects,
                "nota": nota,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def delete_project(project_id: str) -> dict:
        """
        Elimina un proyecto de la hoja de Projects.

        Args:
            project_id: ID del proyecto a eliminar

        Returns:
            dict: Confirmación de eliminación o error si no existe
        """
        try:
            if not project_id:
                return {"success": False, "error": "project_id requerido"}

            sh = gc.open_by_key(SPREADSHEET_ID)
            worksheet = sh.worksheet(SHEET_NAME_PROJECTS)
            all_records = worksheet.get_all_records()

            for idx, row in enumerate(all_records, start=2):
                if str(row.get("Id")) == str(project_id):
                    worksheet.delete_rows(idx)
                    return {
                        "success": True,
                        "message": f"Proyecto '{project_id}' eliminado",
                    }

            return {
                "success": False,
                "error": f"No se encontró proyecto con ID '{project_id}'",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
