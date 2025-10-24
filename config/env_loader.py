"""
Módulo para cargar y gestionar las variables de entorno para la aplicación Merc.
Centraliza el acceso a todas las credenciales y configuraciones del sistema.
"""
import os
from pathlib import Path
import logging
from dotenv import load_dotenv

# Configuración inicial del logger
logger = logging.getLogger(__name__)

# --- Constantes ---
# La ruta base es la carpeta 'Merc' que contiene este archivo de configuración
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BASE_DIR / '.env'

# --- Funciones de Carga ---

def load_merc_env():
    """
    Carga las variables de entorno desde el archivo .env ubicado en la raíz de 'Merc'.
    Esta función es llamada automáticamente al importar el módulo.
    """
    if ENV_FILE_PATH.exists():
        load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)
        logger.info(f"Variables de entorno cargadas desde: {ENV_FILE_PATH}")
    else:
        logger.warning(f"Archivo .env no encontrado en: {ENV_FILE_PATH}. Se usarán las variables del sistema.")

# --- Funciones de Acceso a Configuración ---

def get_ov_credentials(empresa: str) -> dict:
    """
    Obtiene las credenciales de la Oficina Virtual para una empresa específica.

    Args:
        empresa (str): 'afinia' or 'aire'.

    Returns:
        dict: Diccionario con 'username' y 'password'.
    """
    empresa = empresa.upper()
    return {
        'username': os.getenv(f'OV_{empresa}_USERNAME'),
        'password': os.getenv(f'OV_{empresa}_PASSWORD'),
    }

def get_mercurio_credentials(empresa: str) -> dict:
    """
    Obtiene las credenciales de la plataforma Mercurio para una empresa específica.

    Args:
        empresa (str): 'afinia' or 'aire'.

    Returns:
        dict: Diccionario con 'username' y 'password'.
    """
    empresa = empresa.upper()
    return {
        'username': os.getenv(f'MERCURIO_{empresa}_USERNAME'),
        'password': os.getenv(f'MERCURIO_{empresa}_PASSWORD'),
    }

def get_rds_config() -> dict:
    """
    Obtiene la configuración de la base de datos RDS.
    """
    return {
        'host': os.getenv('RDS_HOST'),
        'port': int(os.getenv('RDS_PORT', 5432)),
        'database': os.getenv('RDS_DATABASE'),
        'username': os.getenv('RDS_USERNAME'),
        'password': os.getenv('RDS_PASSWORD'),
    }

def get_s3_config() -> dict:
    """
    Obtiene la configuración de AWS S3.
    """
    return {
        'access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
        'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'region': os.getenv('AWS_REGION'),
        'bucket_name': os.getenv('S3_BUCKET_NAME'),
    }

def get_app_config() -> dict:
    """
    Obtiene la configuración general de la aplicación (logging, navegador, etc.).
    """
    return {
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'log_to_file': os.getenv('LOG_TO_FILE', 'true').lower() == 'true',
        'log_to_console': os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true',
        'browser_headless': os.getenv('BROWSER_HEADLESS', 'false').lower() == 'true',
        'enable_screenshots': os.getenv('ENABLE_SCREENSHOTS', 'true').lower() == 'true',
    }

# --- Ejecución Automática ---
# Carga las variables de entorno tan pronto como se importa este módulo.
load_merc_env()
