from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_context
from services.google_sheet.crm_service import CRMService
import os
import logging
from dotenv import load_dotenv
from typing import Optional

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

mcp = FastMCP(name="CRM Server")


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
