"""
Módulo compartido para inicializar clientes de gspread.
Evita duplicación de código entre servicios.
"""

import gspread
import json
import os
import logging
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


def get_gspread_client(
    service_account_file: str, scopes: list, service_name: str = "Service"
) -> gspread.Client:
    """
    Inicializa un cliente de gspread con credenciales desde archivo o JSON.

    Args:
        service_account_file: Ruta al archivo o JSON string de credenciales
        scopes: Lista de scopes de Google API
        service_name: Nombre del servicio (para logging)

    Returns:
        gspread.Client: Cliente autenticado de gspread

    Raises:
        ValueError: Si las credenciales no son válidas
        FileNotFoundError: Si el archivo no existe
    """
    try:
        logger.info(
            f"Inicializando gspread para {service_name}: {service_account_file[:50]}..."
        )

        # Convertir a ruta absoluta si es relativa
        account_file = service_account_file
        if not os.path.isabs(account_file):
            account_file = os.path.abspath(account_file)

        # Intentar cargar como archivo primero
        if os.path.isfile(account_file):
            logger.info(f"📁 Cargando credenciales desde archivo: {account_file}")
            creds = Credentials.from_service_account_file(account_file, scopes=scopes)
        else:
            # Si no es un archivo, intentar como JSON string
            logger.info("🔐 Intentando cargar credenciales desde JSON string")
            try:
                service_account_info = json.loads(service_account_file)
                if not isinstance(service_account_info, dict):
                    raise ValueError("JSON no es un diccionario válido")
                creds = Credentials.from_service_account_info(
                    service_account_info, scopes=scopes
                )
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"❌ Credenciales inválidas")
                logger.error(f"   Ruta absoluta buscada: {account_file}")
                logger.error(f"   Archivo existe: {os.path.exists(account_file)}")
                logger.error(f"   Es archivo: {os.path.isfile(account_file)}")
                logger.error(f"   Directorio actual: {os.getcwd()}")

                # Listar archivos en el directorio secrets si existe
                secrets_dir = os.path.join(os.getcwd(), "secrets")
                if os.path.exists(secrets_dir):
                    logger.error(f"   Archivos en secrets/: {os.listdir(secrets_dir)}")

                raise ValueError(
                    f"SERVICE_ACCOUNT_FILE debe ser una ruta de archivo válido o JSON string. "
                    f"Ruta: {account_file} | Existe: {os.path.exists(account_file)} | "
                    f"Error: {str(e)}"
                )

        gc = gspread.authorize(creds)
        logger.info(f"✅ Cliente gspread inicializado para {service_name}")
        return gc

    except Exception as e:
        logger.error(f"❌ Error inicializando gspread para {service_name}: {e}")
        raise
