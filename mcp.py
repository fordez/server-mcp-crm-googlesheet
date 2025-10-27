from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_context
from services.google_sheet.crm_service import CRMService
from services.google_sheet.services_catalog import CatalogService
from services.google_calendar_meet.calendar_service import CalendarService
import os
import logging
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime

load_dotenv()

# Logs resumidos
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

mcp = FastMCP(name="CRM + Catalog Server")


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
    logger.info(
        f"🔍 LLAMADA A verify_client | tel: {telefono}, correo: {correo}, usuario: {usuario}"
    )
    ctx = ctx or get_context()
    result = CRMService.verify_client(telefono=telefono, correo=correo, usuario=usuario)
    logger.info(
        f"📤 RESPUESTA verify_client: exists={result.get('exists')}, id={result.get('client_id')}"
    )
    return result


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
    logger.info(f"✨ LLAMADA A create_client | nombre: {nombre}, canal: {canal}")
    ctx = ctx or get_context()
    result = CRMService.create_client(
        nombre=nombre,
        canal=canal,
        telefono=telefono,
        correo=correo,
        nota=nota,
        usuario=usuario,
    )
    logger.info(
        f"📤 RESPUESTA create_client: success={result.get('success')}, id={result.get('client_id')}"
    )
    return result


# -----------------------
# TOOL 3: UPDATE CLIENT (general)
# -----------------------
@mcp.tool()
async def update_client(
    client_id: str,
    nombre: Optional[str] = None,
    telefono: Optional[str] = None,
    correo: Optional[str] = None,
    tipo: Optional[str] = None,
    usuario: Optional[str] = None,
    fecha_conversion: Optional[str] = None,
    ctx: Context = None,
) -> dict:
    logger.info(f"🔄 LLAMADA A update_client | client_id: {client_id}")
    ctx = ctx or get_context()
    try:
        result = CRMService.update_client(
            client_id=client_id,
            nombre=nombre,
            telefono=telefono,
            correo=correo,
            tipo=tipo,
            usuario=usuario,
            fecha_conversion=fecha_conversion,
        )
        logger.info(
            f"📤 RESPUESTA update_client: success={result.get('success')}, updated_fields={result.get('updated_fields')}"
        )
        return result
    except Exception as e:
        logger.error(f"❌ ERROR update_client: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


# -----------------------
# TOOL 4: UPDATE CLIENT NOTE
# -----------------------
@mcp.tool()
async def update_client_note(
    client_id: str,
    nota: str,
    ctx: Context = None,
) -> dict:
    logger.info(f"✏️ LLAMADA A update_client_note | client_id: {client_id}")
    ctx = ctx or get_context()
    try:
        result = CRMService.update_client_dynamic(
            client_id=client_id, fields={"Nota": nota}
        )
        logger.info(
            f"📤 RESPUESTA update_client_note: success={result.get('success')}, updated_fields={result.get('updated_fields')}"
        )
        return result
    except Exception as e:
        logger.error(f"❌ ERROR update_client_note: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


# -----------------------
# TOOL 5: UPDATE CLIENT STATUS
# -----------------------
@mcp.tool()
async def update_client_status(
    client_id: str,
    estado: str,
    ctx: Context = None,
) -> dict:
    logger.info(
        f"🔄 LLAMADA A update_client_status | client_id: {client_id}, estado: {estado}"
    )
    ctx = ctx or get_context()
    try:
        result = CRMService.update_client_dynamic(
            client_id=client_id, fields={"Estado": estado}
        )
        logger.info(
            f"📤 RESPUESTA update_client_status: success={result.get('success')}, updated_fields={result.get('updated_fields')}"
        )
        return result
    except Exception as e:
        logger.error(f"❌ ERROR update_client_status: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


# -----------------------
# TOOL 6: GET ALL SERVICES
# -----------------------
@mcp.tool()
async def get_all_services(ctx: Context = None) -> dict:
    """Retorna todos los servicios disponibles de la hoja 'Services'."""
    logger.info("🔍 LLAMADA A get_all_services")
    ctx = ctx or get_context()
    result = CatalogService.get_all_services()
    logger.info(f"📤 RESPUESTA get_all_services: success={result.get('success')}")
    return result


# -----------------------
# TOOL 7: GET SERVICE BY NAME
# -----------------------
@mcp.tool()
async def get_service_by_name(service_name: str, ctx: Context = None) -> dict:
    """Retorna un servicio específico por nombre."""
    logger.info(f"🔍 LLAMADA A get_service_by_name | service_name={service_name}")
    ctx = ctx or get_context()
    result = CatalogService.get_service_by_name(service_name)
    logger.info(f"📤 RESPUESTA get_service_by_name: success={result.get('success')}")
    return result


# -----------------------
# TOOL 8: check_availability
# -----------------------
@mcp.tool()
async def calendar_check_availability(ctx: Context = None) -> dict:
    """Devuelve los espacios libres de los próximos 3 días hábiles disponibles."""
    logger.info("🕓 LLAMADA A calendar_check_availability")
    result = CalendarService.check_availability()
    logger.info("📤 RESPUESTA calendar_check_availability enviada.")
    return {"success": True, "data": result}


# -----------------------
# TOOL 9: calendar_create_meet
# -----------------------
@mcp.tool()
async def calendar_create_meet(
    summary: str,
    start_time: str,
    end_time: str,
    attendees: Optional[list[str]] = None,
    description: Optional[str] = None,
    ctx: Context = None,
) -> dict:
    """Crea un evento de Google Calendar con enlace de Meet."""
    logger.info(f"📅 LLAMADA A calendar_create_meet | summary={summary}")
    start_dt = datetime.fromisoformat(start_time)
    end_dt = datetime.fromisoformat(end_time)
    result = CalendarService.create_meet_event(
        summary=summary,
        start_time=start_dt,
        end_time=end_dt,
        attendees=attendees,
        description=description,
    )
    return {"success": True, "data": result}


# -----------------------
# TOOL 10: calendar_get_event_details
# -----------------------
@mcp.tool()
async def calendar_get_event_details(event_id: str, ctx: Context = None) -> dict:
    """Obtiene los detalles de un evento por su ID."""
    logger.info(f"📄 LLAMADA A calendar_get_event_details | event_id={event_id}")
    result = CalendarService.get_event_details(event_id)
    return {"success": True, "data": result}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MCP_SERVER_PORT", 8000))
    logger.info(f"🚀 Iniciando MCP Server en el puerto {port}...")

    uvicorn.run("mcp_server:app", host="0.0.0.0", port=port, log_level="info")
