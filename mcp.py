# mcp_server.py
from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_context
from services.google_sheet.crm_service import CRMService
import os
import logging
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configurar logging detallado
log_dir = os.getenv("LOG_DIR", "./logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{log_dir}/mcp_server.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Crear instancia MCP
mcp = FastMCP(name="CRM Server")


@mcp.tool()
async def verify_client(
    telefono: Optional[str] = None,
    correo: Optional[str] = None,
    usuario: Optional[str] = None,
    ctx: Context = None,
) -> dict:
    """
    Verifica si un cliente existe en el CRM.
    Busca por teléfono, correo o usuario. Al menos uno debe proporcionarse.

    Args:
        telefono: Número de teléfono con código de país (ej: +5491123456789)
        correo: Correo electrónico del cliente
        usuario: Usuario o agente asignado
    """
    logger.info("=" * 80)
    logger.info("🔍 LLAMADA A verify_client")
    logger.info(f"   telefono: {telefono}")
    logger.info(f"   correo: {correo}")
    logger.info(f"   usuario: {usuario}")
    logger.info("=" * 80)

    ctx = ctx or get_context()
    result = CRMService.verify_client(telefono=telefono, correo=correo, usuario=usuario)

    logger.info(f"📤 RESPUESTA verify_client: {result}")
    return result


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
    Crea un nuevo cliente (lead) en el CRM con ID autogenerado.

    Args:
        nombre: Nombre completo del cliente (REQUERIDO)
        canal: Canal de origen - debe ser 'whatsapp' o 'web' (REQUERIDO)
        telefono: Número de teléfono con código de país
        correo: Correo electrónico del cliente
        nota: Observaciones iniciales sobre el lead
        usuario: Usuario o agente que registra el lead
    """
    logger.info("=" * 80)
    logger.info("✨ LLAMADA A create_client")
    logger.info(f"   nombre: {nombre}")
    logger.info(f"   canal: {canal}")
    logger.info(f"   telefono: {telefono}")
    logger.info(f"   correo: {correo}")
    logger.info(f"   nota: {nota}")
    logger.info(f"   usuario: {usuario}")
    logger.info("=" * 80)

    ctx = ctx or get_context()
    result = CRMService.create_client(
        nombre=nombre,
        canal=canal,
        telefono=telefono,
        correo=correo,
        nota=nota,
        usuario=usuario,
    )

    logger.info(f"📤 RESPUESTA create_client: {result}")
    return result


@mcp.tool()
async def update_client(
    client_id: str,
    nombre: Optional[str] = None,
    telefono: Optional[str] = None,
    correo: Optional[str] = None,
    tipo: Optional[str] = None,
    estado: Optional[str] = None,
    nota: Optional[str] = None,
    usuario: Optional[str] = None,
    fecha_conversion: Optional[str] = None,
    ctx: Context = None,
) -> dict:
    """
    Actualiza los datos de un cliente existente.
    Solo actualiza los campos proporcionados.

    Args:
        client_id: ID único del cliente (obtenido de verify_client) - REQUERIDO
        nombre: Actualizar nombre del cliente
        telefono: Actualizar número de teléfono
        correo: Actualizar correo electrónico
        tipo: Tipo de cliente (Lead o Cliente)
        estado: Estado del lead (Nuevo, Contactado, Calificado, Negociación, Ganado, Perdido)
        nota: Notas de seguimiento o actualización
        usuario: Reasignar a otro usuario o agente
        fecha_conversion: Fecha de conversión a cliente (formato: YYYY-MM-DD HH:MM:SS)
    """
    logger.info("=" * 80)
    logger.info("🔄 LLAMADA A update_client")
    logger.info(f"   client_id: {client_id}")
    logger.info(f"   nombre: {nombre}")
    logger.info(f"   telefono: {telefono}")
    logger.info(f"   correo: {correo}")
    logger.info(f"   tipo: {tipo}")
    logger.info(f"   estado: {estado}")
    logger.info(f"   nota: {nota}")
    logger.info(f"   usuario: {usuario}")
    logger.info(f"   fecha_conversion: {fecha_conversion}")
    logger.info("=" * 80)

    ctx = ctx or get_context()

    try:
        result = CRMService.update_client(
            client_id=client_id,
            nombre=nombre,
            telefono=telefono,
            correo=correo,
            tipo=tipo,
            estado=estado,
            nota=nota,
            usuario=usuario,
            fecha_conversion=fecha_conversion,
        )
        logger.info(f"📤 RESPUESTA update_client: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ ERROR en update_client: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8000))
    logger.info("=" * 80)
    logger.info(f"🚀 INICIANDO MCP SERVER en puerto {port}")
    logger.info(f"📁 Logs en: {log_dir}/mcp_server.log")
    logger.info("=" * 80)
    mcp.run(transport="http", port=port)
