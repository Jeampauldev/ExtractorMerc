"""
Módulo para cargar y gestionar variables de entorno
Centraliza el acceso a credenciales y configuraciones
"""
import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Flag para saber si ya se cargaron las variables
_ENV_LOADED = False

def load_environment(env_file: Optional[str] = None) -> bool:
    """
    Carga las variables de entorno desde el archivo .env
    
    Args:
        env_file: Ruta al archivo .env (opcional, usa ubicación por defecto)
    
    Returns:
        bool: True si se cargó exitosamente
    """
    global _ENV_LOADED
    
    if _ENV_LOADED:
        logger.debug("Variables de entorno ya cargadas")
        return True
    
    try:
        # Intentar importar python-dotenv
        try:
            from dotenv import load_dotenv
        except ImportError:
            logger.warning("python-dotenv no instalado. Usando variables de sistema.")
            _ENV_LOADED = True
            return True
        
        # Determinar ruta del archivo .env
        if env_file:
            env_path = Path(env_file)
        else:
            # Buscar en config/env/
            project_root = Path(__file__).parent.parent.parent
            env_path = project_root / 'config' / 'env' / '.env'
        
        # Cargar variables
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            logger.info(f"[EMOJI_REMOVIDO] Variables de entorno cargadas desde: {env_path}")
            _ENV_LOADED = True
            return True
        else:
            logger.warning(f"[EMOJI_REMOVIDO] Archivo .env no encontrado en: {env_path}")
            logger.info("Usando variables de entorno del sistema")
            _ENV_LOADED = True
            return False
            
    except Exception as e:
        logger.error(f"Error cargando variables de entorno: {e}")
        return False

def get_rds_config() -> Dict[str, any]:
    """
    Obtiene la configuración de RDS AWS
    
    Returns:
        Dict con configuración de base de datos
    """
    load_environment()
    
    return {
        'host': os.getenv('RDS_HOST') or os.getenv('DB_HOST'),
        'database': os.getenv('RDS_DATABASE') or os.getenv('DB_NAME'),
        'username': os.getenv('RDS_USERNAME') or os.getenv('DB_USER'),
        'password': os.getenv('RDS_PASSWORD') or os.getenv('DB_PASSWORD'),
        'port': int(os.getenv('RDS_PORT', os.getenv('DB_PORT', 5432))),
        'charset': os.getenv('RDS_CHARSET', 'utf8')
    }

def get_s3_config() -> Dict[str, str]:
    """
    Obtiene la configuración de AWS S3
    
    Returns:
        Dict con configuración de S3
    """
    load_environment()
    
    return {
        'bucket_name': os.getenv('AWS_S3_BUCKET_NAME'),
        'access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
        'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'region': os.getenv('AWS_REGION', os.getenv('AWS_DEFAULT_REGION', 'us-west-2')),
        'iam_user': os.getenv('AWS_S3_IAM_USER')
    }

def get_afinia_credentials() -> Dict[str, str]:
    """
    Obtiene las credenciales de Oficina Virtual Afinia
    
    Returns:
        Dict con username y password
    """
    load_environment()
    
    return {
        'username': os.getenv('OV_AFINIA_USERNAME') or os.getenv('AFINIA_USERNAME'),
        'password': os.getenv('OV_AFINIA_PASSWORD') or os.getenv('AFINIA_PASSWORD'),
        'url': os.getenv('OV_AFINIA_URL', 'https://caribemar.facture.co/Mi-Perfil/')
    }

def get_aire_credentials() -> Dict[str, str]:
    """
    Obtiene las credenciales de Oficina Virtual Aire
    
    Returns:
        Dict con username y password
    """
    load_environment()
    
    return {
        'username': os.getenv('OV_AIRE_USERNAME'),
        'password': os.getenv('OV_AIRE_PASSWORD'),
        'url': os.getenv('OV_AIRE_URL', 'https://caribemar.facture.co/Listado-Radicaci%C3%B3n-PQR#/Detail')
    }

def get_app_config() -> Dict[str, any]:
    """
    Obtiene la configuración general de la aplicación
    
    Returns:
        Dict con configuración de la app
    """
    load_environment()
    
    return {
        'env': os.getenv('APP_ENV', 'production'),
        'debug': os.getenv('DEBUG', 'False').lower() == 'true',
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'download_path': os.getenv('DOWNLOAD_PATH', './data/downloads'),
        'log_path': os.getenv('LOG_PATH', './data/logs'),
        'metrics_path': os.getenv('METRICS_PATH', './data/metrics'),
        'browser_timeout': int(os.getenv('BROWSER_TIMEOUT', 30)),
        'login_timeout': int(os.getenv('LOGIN_TIMEOUT', 30)),
        'download_timeout': int(os.getenv('DOWNLOAD_TIMEOUT', 60)),
        'page_load_timeout': int(os.getenv('PAGE_LOAD_TIMEOUT', 45)),
        'max_records_per_session': int(os.getenv('MAX_RECORDS_PER_SESSION', 50)),
        'retry_attempts': int(os.getenv('RETRY_ATTEMPTS', 3)),
        'screenshot_on_error': os.getenv('SCREENSHOT_ON_ERROR', 'True').lower() == 'true'
    }

def validate_credentials() -> Dict[str, bool]:
    """
    Valida que todas las credenciales necesarias estén configuradas
    
    Returns:
        Dict con el estado de validación de cada grupo de credenciales
    """
    load_environment()
    
    validation = {
        'rds': False,
        's3': False,
        'afinia': False,
        'aire': False
    }
    
    # Validar RDS
    rds_config = get_rds_config()
    validation['rds'] = all([
        rds_config.get('host'),
        rds_config.get('database'),
        rds_config.get('username'),
        rds_config.get('password')
    ])
    
    # Validar S3
    s3_config = get_s3_config()
    validation['s3'] = all([
        s3_config.get('bucket_name'),
        s3_config.get('access_key_id'),
        s3_config.get('secret_access_key')
    ])
    
    # Validar Afinia
    afinia_creds = get_afinia_credentials()
    validation['afinia'] = all([
        afinia_creds.get('username'),
        afinia_creds.get('password')
    ])
    
    # Validar Aire
    aire_creds = get_aire_credentials()
    validation['aire'] = all([
        aire_creds.get('username'),
        aire_creds.get('password')
    ])
    
    return validation

def print_config_status():
    """
    Imprime el estado de la configuración (útil para debugging)
    """
    load_environment()
    
    print("\n" + "=" * 60)
    print("ESTADO DE CONFIGURACIÓN")
    print("=" * 60)
    
    validation = validate_credentials()
    
    print("\n[EMOJI_REMOVIDO] Credenciales:")
    print(f"  RDS Database:    {'[EMOJI_REMOVIDO] Configurado' if validation['rds'] else '[EMOJI_REMOVIDO] Falta configurar'}")
    print(f"  AWS S3:          {'[EMOJI_REMOVIDO] Configurado' if validation['s3'] else '[EMOJI_REMOVIDO] Falta configurar'}")
    print(f"  Afinia OV:       {'[EMOJI_REMOVIDO] Configurado' if validation['afinia'] else '[EMOJI_REMOVIDO] Falta configurar'}")
    print(f"  Aire OV:         {'[EMOJI_REMOVIDO] Configurado' if validation['aire'] else '[EMOJI_REMOVIDO] Falta configurar'}")
    
    app_config = get_app_config()
    print(f"\n[CONFIGURACION]  Configuración de App:")
    print(f"  Entorno:         {app_config['env']}")
    print(f"  Debug:           {app_config['debug']}")
    print(f"  Log Level:       {app_config['log_level']}")
    print(f"  Max Records:     {app_config['max_records_per_session']}")
    print(f"  Retry Attempts:  {app_config['retry_attempts']}")
    
    print("\n" + "=" * 60)

# Auto-cargar al importar el módulo
load_environment()

if __name__ == "__main__":
    # Test del módulo
    print("Probando carga de variables de entorno...")
    print_config_status()
    
    print("\n[EMOJI_REMOVIDO] Detalles de configuración:")
    
    print("\n[DATOS] RDS Config:")
    rds = get_rds_config()
    print(f"  Host: {rds['host']}")
    print(f"  Database: {rds['database']}")
    print(f"  Username: {rds['username']}")
    print(f"  Password: {'*' * len(rds['password']) if rds['password'] else 'NO CONFIGURADO'}")
    
    print("\n[S3]  S3 Config:")
    s3 = get_s3_config()
    print(f"  Bucket: {s3['bucket_name']}")
    print(f"  Region: {s3['region']}")
    print(f"  Access Key: {s3['access_key_id'][:10]}..." if s3['access_key_id'] else "NO CONFIGURADO")
    
    print("\n[EMOJI_REMOVIDO] Afinia Credentials:")
    afinia = get_afinia_credentials()
    print(f"  Username: {afinia['username']}")
    print(f"  Password: {'*' * 10 if afinia['password'] else 'NO CONFIGURADO'}")
    
    print("\n[EMOJI_REMOVIDO] Aire Credentials:")
    aire = get_aire_credentials()
    print(f"  Username: {aire['username']}")
    print(f"  Password: {'*' * 10 if aire['password'] else 'NO CONFIGURADO'}")
