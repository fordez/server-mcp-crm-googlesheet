from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_context
from services.google_sheet.crm_service import CRMService
from services.google_sheet.catalog_service import CatalogService
from services.google_calendar_meet.calendar_service import CalendarService
import os
import logging
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime

# ====================================================
# ⚙️ Cargar variables de entorno
# ====================================================
load_dotenv()

# ====================================================
# 🧾 Logging
# ====================================================
log_dir = os.getenv("LOG_DIR", "./logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{log_dir}/mcp_server.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ====================================================
# 🚀 Inicializar MCP
# ====================================================
mcp = FastMCP(name="CRM + Catalog Server")


# ====================================================
# -----------------------
# TOOL 1: VERIFY CLIENT
# -----------------------
@mcp.tool()
async def verify_client(
    telefono: Optional[str] = None,
    correo: Optional[str] = None,
    usuario: Optional[str] = None,
    ctx: Context = None,
) -> dict:
    """
    Verifica si un cliente existe en el CRM usando teléfono, correo o usuario.
    Retorna información completa del cliente si se encuentra.
    """
    ctx = ctx or get_context()
    logger.info(
        f"🔍 verify_client | tel={telefono}, correo={correo}, usuario={usuario}"
    )
    result = CRMService.verify_client(telefono=telefono, correo=correo, usuario=usuario)
    logger.info(f"📤 verify_client response: {result}")
    return {"success": True, "data": result}


# ====================================================
# -----------------------
# TOOL 2: CREATE CLIENT
# -----------------------
@mcp.tool()
async def create_client(
    nombre: str,
    canal: str,
    telefono: Optional[str] = None,
    correo: Optional[str] = None,
    nota: Optional[str] = None,
    usuario: Optional[str] = None,
    ctx: Context = None,
) -> dict:
    """
    Crea un nuevo cliente en el CRM.
    """
    ctx = ctx or get_context()
    logger.info(f"✨ create_client | nombre={nombre}, canal={canal}")
    result = CRMService.create_client(
        nombre=nombre,
        canal=canal,
        telefono=telefono,
        correo=correo,
        nota=nota,
        usuario=usuario,
    )
    logger.info(f"📤 create_client response: {result}")
    return {"success": True, "data": result}


# ====================================================
# -----------------------
# TOOL 3: UPDATE CLIENT
# -----------------------
@mcp.tool()
async def update_client(
    client_id: str,
    fields: dict,
    ctx: Context = None,
) -> dict:
    """
    Actualiza cualquier campo dinámicamente usando un diccionario `fields`.
    Ejemplo de fields: {"Nombre": "Juan", "Telefono": "123456"}
    El `client_id` puede ser UUID interno o el teléfono del cliente.
    """
    ctx = ctx or get_context()
    logger.info(f"🔄 update_client | client_id={client_id}, fields={fields}")

    if not fields:
        return {
            "success": False,
            "error": "No se proporcionaron campos para actualizar",
        }

    try:
        result = CRMService.update_client_dynamic(client_id=client_id, fields=fields)
        logger.info(f"📤 update_client response: {result}")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"❌ update_client error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


# ====================================================
# -----------------------
# TOOL 4: UPDATE CLIENT NOTE
# -----------------------
@mcp.tool()
async def update_client_note(client_id: str, nota: str, ctx: Context = None) -> dict:
    """
    Actualiza la nota de un cliente existente.
    El `client_id` puede ser UUID interno o el teléfono del cliente.
    """
    ctx = ctx or get_context()
    logger.info(f"✏️ update_client_note | client_id={client_id}")
    try:
        result = CRMService.update_client_dynamic(
            client_id=client_id, fields={"Nota": nota}
        )
        logger.info(f"📤 update_client_note response: {result}")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"❌ update_client_note error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


# ====================================================
# -----------------------
# TOOL 5: UPDATE CLIENT STATUS
# -----------------------
@mcp.tool()
async def update_client_status(
    client_id: str, estado: str, ctx: Context = None
) -> dict:
    """
    Actualiza el estado de un cliente existente.
    El `client_id` puede ser UUID interno o el teléfono del cliente.
    """
    ctx = ctx or get_context()
    logger.info(f"🔄 update_client_status | client_id={client_id}, estado={estado}")
    try:
        result = CRMService.update_client_dynamic(
            client_id=client_id, fields={"Estado": estado}
        )
        logger.info(f"📤 update_client_status response: {result}")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"❌ update_client_status error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


# ====================================================
# -----------------------
# TOOL 6: GET ALL SERVICES
# -----------------------
@mcp.tool()
async def get_all_services(ctx: Context = None) -> dict:
    """
    Retorna todos los servicios disponibles en el catálogo.
    """
    ctx = ctx or get_context()
    logger.info("🔍 get_all_services")
    result = CatalogService.get_all_services()
    logger.info(f"📤 get_all_services response: {result}")
    return {"success": True, "data": result}


# ====================================================
# -----------------------
# TOOL 7: GET SERVICE BY NAME
# -----------------------
@mcp.tool()
async def get_service_by_name(service_name: str, ctx: Context = None) -> dict:
    """
    Busca un servicio por su nombre en el catálogo.
    """
    ctx = ctx or get_context()
    logger.info(f"🔍 get_service_by_name | service_name={service_name}")
    result = CatalogService.get_service_by_name(service_name)
    logger.info(f"📤 get_service_by_name response: {result}")
    return {"success": True, "data": result}


# ====================================================
# -----------------------
# TOOL 8: CALENDAR CHECK AVAILABILITY
# -----------------------
@mcp.tool()
async def calendar_check_availability(ctx: Context = None) -> dict:
    """
    Consulta disponibilidad de calendario para crear eventos.
    """
    ctx = ctx or get_context()
    logger.info("🕓 calendar_check_availability")
    result = CalendarService.check_availability()
    return {"success": True, "data": result}


# ====================================================
# -----------------------
# TOOL 9: CALENDAR CREATE MEET
# -----------------------
@mcp.tool()
async def calendar_create_meet(
    summary: str,
    start_time: str,
    end_time: str,
    attendees: Optional[List[str]] = None,
    description: Optional[str] = None,
    ctx: Context = None,
) -> dict:
    """
    Crea un evento de Google Meet en el calendario.
    """
    ctx = ctx or get_context()
    logger.info(f"📅 calendar_create_meet | summary={summary}")
    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time)
    meet_link = CalendarService.create_meet_event(
        summary=summary,
        start_time=start_dt,
        end_time=end_dt,
        attendees=attendees,
        description=description,
    )
    return {"success": True, "data": meet_link}


# ====================================================
# -----------------------
# TOOL 10: GET EVENT DETAILS
# -----------------------
@mcp.tool()
async def calendar_get_event_details(event_id: str, ctx: Context = None) -> dict:
    """
    Obtiene los detalles de un evento de calendario por su ID.
    """
    ctx = ctx or get_context()
    logger.info(f"📄 calendar_get_event_details | event_id={event_id}")
    result = CalendarService.get_event_details(event_id)
    return {"success": True, "data": result}


# ====================================================
# 🚀 RUN SERVER
# ====================================================
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MCP_SERVER_PORT", 8000))
    logger.info(f"🚀 Iniciando MCP Server en puerto {port}...")
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=port, log_level="info")
