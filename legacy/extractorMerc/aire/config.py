"""
Configuración para Mercurio Aire
================================

Configuración específica generada automáticamente.

Generado: 2025-09-26
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
env_file = Path(__file__).parent.parent.parent.parent / "env" / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=str(env_file), override=True)

# Configuración específica para AIRE
AIRE_MERCURIO_CONFIG = {
    "company": "aire",
    "platform": "mercurio",
    "url": "https://mercurio.aire.com.co/Mercurio/",
    "username": os.getenv("MERCURIO_AIRE_USERNAME", ""),
    "password": os.getenv("MERCURIO_AIRE_PASSWORD", ""),
    
    # Timeouts específicos
    "timeouts": {
        "navigation": 30000,
        "login": 45000,  
        "download": 60000,
        "element_wait": 10000
    },
    
    # Selectores específicos para AIRE
    "selectors": {
        "username": ["input[name=\"ctl00$ContentPlaceHolder1$txtUsuario\"]", "input[type=\"text\"]"],
        "password": ["input[name=\"ctl00$ContentPlaceHolder1$txtPassword\"]", "input[type=\"password\"]"],
        "login_button": ["input[name=\"ctl00$ContentPlaceHolder1$btnIngresar\"]", "input[type=\"submit\"]"],
        "sections": {
            "pqrsescritas": [
                'a:has-text("PQRsEscritas")',
                'button:has-text("PQRsEscritas")',
                'li:has-text("PQRsEscritas")'
            ],            "pqrsverbales": [
                'a:has-text("PQRsVerbales")',
                'button:has-text("PQRsVerbales")',
                'li:has-text("PQRsVerbales")'
            ],            "reportes": [
                'a:has-text("Reportes")',
                'button:has-text("Reportes")',
                'li:has-text("Reportes")'
            ]        }
    },
    
    # Configuraciones de descarga
    "download": {
        "base_dir": "downloads/aire/mercurio",
        "timeout": 60000,
        "max_retries": 3,
        "formats": ["xlsx", "csv", "json"]
    },
    
    # Configuraciones de screenshots
    "screenshots": {
        "enabled": true,
        "dir": "downloads/aire/mercurio/screenshots",
        "on_error": True,
        "on_success": False
    }
}

# Configuraciones adicionales específicas por empresa
# Configuraciones específicas para AIRE
AIRE_SPECIFIC_CONFIG = {
    "nic_prefix": "27",  # NICs de AIRE empiezan con 27
    "typical_reports": ["pqr_pendientes", "reclamos_comerciales", "quejas_tecnicas"],
    "custom_fields": {
        "area_responsable": "Área Comercial",
        "region": "Costa Atlántica"
    }
}

AIRE_MERCURIO_CONFIG.update(AIRE_SPECIFIC_CONFIG)

# Función para obtener configuración
def get_aire_mercurio_config():
    """
    Obtiene la configuración para AIRE Mercurio
    
    Returns:
        Dict con configuración completa
    """
    return AIRE_MERCURIO_CONFIG.copy()

# Validar configuración al importar
def validate_config():
    """Valida que la configuración esté completa"""
    config = AIRE_MERCURIO_CONFIG
    required_fields = ["username", "password", "url"]
    
    missing = [field for field in required_fields if not config.get(field)]
    
    if missing:
        print(f"⚠️ Configuración incompleta para AIRE: {missing}")
        print("   Verificar variables de entorno:")
        for field in missing:
            env_var = f"MERCURIO_AIRE_{field.upper()}"
            print(f"   - {env_var}")
    else:
        print(f"✅ Configuración AIRE Mercurio válida")

# Validar al importar el módulo
if __name__ == "__main__":
    validate_config()
else:
    # Solo validar si no estamos en modo test
    import sys
    if "pytest" not in sys.modules:
        validate_config()
