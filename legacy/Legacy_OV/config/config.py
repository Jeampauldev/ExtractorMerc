#!/usr/bin/env python3
"""
Configuración Central - ExtractorOV Modular
=========================================

Configuración centralizada y optimizada para todos los extractores modulares.
Separación clara entre configuraciones de producción, desarrollo y testing.
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, Optional

# Cargar variables de entorno
project_root = Path(__file__).parent.parent.parent
env_file = project_root / "config" / "env" / ".env"

if env_file.exists():
    load_dotenv(dotenv_path=str(env_file), override=True)
    print(f"OK Variables de entorno cargadas desde: {env_file}")
else:
    print(f"Warning: Archivo .env no encontrado en: {env_file}")

# ============================================================================
# CONFIGURACIÓN BASE
# ============================================================================

class ExtractorConfig:
    """Configuración base para todos los extractores"""

    # Directorios del proyecto
    PROJECT_ROOT = project_root
    DOWNLOADS_DIR = PROJECT_ROOT / "data" / "downloads"
    LOGS_DIR = PROJECT_ROOT / "data" / "logs"
    SCREENSHOTS_DIR = PROJECT_ROOT / "data" / "downloads" / "screenshots"

    # Configuración de timeouts (en milisegundos)
    TIMEOUTS = {
        "navigation": 30000,  # 30 segundos para navegación
        "login": 60000,       # 60 segundos para login
        "element_wait": 15000, # 15 segundos para esperar elementos
        "download": 120000,   # 120 segundos para descargas
        "page_load": 45000    # 45 segundos para carga de página
    }

    # Configuración del navegador optimizada para mejor visualización
    BROWSER_CONFIG = {
        "headless": os.getenv("BROWSER_HEADLESS", "false").lower() == "true",
        "viewport": {"width": 1920, "height": 1080},  # Viewport más grande para ver contenido completo
        "device_scale_factor": 0.8,  # Factor de escala optimizado
        "args": [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--start-maximized",  # Maximizar ventana para ver página completa
            "--window-size=1920,1080",  # Tamaño de ventana específico
            "--force-device-scale-factor=0.8",  # Zoom optimizado para ver más contenido
            "--disable-features=TranslateUI",
            "--enable-automation",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding"
        ]
    }


# ============================================================================
# CONFIGURACIÓN OFICINA VIRTUAL
# ============================================================================

class OficinaVirtualConfig:
    """Configuración específica para extractores Oficina Virtual"""

    AFINIA = {
        "url": "https://caribemar.facture.co/login",
        "username": os.getenv("OV_AFINIA_USERNAME"),
        "password": os.getenv("OV_AFINIA_PASSWORD"),
        "company_name": "afinia",
        "platform": "oficina_virtual",
        "timeout": 90000,  # Timeout principal para navegación y operaciones
        "selectors": {
            "username": [
                "input[name='username']",
                "input[type='text']",
                "#username",
                "#user"
            ],
            "password": [
                "input[name='password']", 
                "input[type='password']",
                "#password",
                "#pass"
            ],
            "submit": [
                "button[type='submit']",
                "input[type='submit']",
                ".btn-login"
            ]
        },
        "timeouts": {
            "navigation": 90000,  # Aumentado para mejor conectividad
            "login": 45000,
            "download": 60000
        },
        "options": {
            "pqr_url_suffix": "/Listado-Radicaci%C3%B3n-PQR#",
            "pqr_download_selector": "#btnGenerarExcel"
        }
    }

    AIRE = {
        "url": "https://caribesol.facture.co/Listado-Radicaci%C3%B3n-PQR#/Detail",
        "username": os.getenv("OV_AIRE_USERNAME"),
        "password": os.getenv("OV_AIRE_PASSWORD"),
        "company_name": "aire",
        "platform": "oficina_virtual",
        "selectors": {
            "username": [
                "input[name='username']",
                "input[type='text']",
                "#username",
                "#user"
            ],
            "password": [
                "input[name='password']",
                "input[type='password']", 
                "#password",
                "#pass"
            ],
            "submit": [
                "button[type='submit']",
                "input[type='submit']",
                "#login-button",
                ".btn-login",
                "button:has-text('Iniciar sesión')",
                "button:has-text('Ingresar')"
            ],
            "menu_radicacion_pqr": [
                "a:has-text('Radicación PQR')",
                "a[href*='Radicacion-PQR']",
                "a[href*='radicacion-pqr']"
            ],
            "filtro_fecha_desde": "input[name='fechaInicial']",
            "filtro_fecha_hasta": "input[name='fechaFinal']",
            "boton_buscar": "button:has-text('Buscar')",
            "tabla_resultados": "table tbody tr",
            "boton_descargar": "button:has-text('Exportar'):not([disabled])",
            "cerrar_sesion": "a:has-text('Cerrar sesión')"
        },
        "timeouts": {
            "navigation": 30000,
            "login": 45000,
            "download": 60000
        },
        "options": {
            "rango_dias_descarga": 7,
            "formato_fecha": "%Y-%m-%d",
            "tiempo_espera_descarga": 30  # segundos
        }
    }


# ============================================================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================================================

def validate_config(config_dict: Dict[str, Any], config_name: str) -> bool:
    """Valida que la configuración tenga las credenciales necesarias"""
    required_fields = ["username", "password", "url"]

    missing_fields = []
    for field in required_fields:
        if not config_dict.get(field):
            missing_fields.append(field)

    if missing_fields:
        print(f"ERROR: Configuración {config_name} incompleta. Faltan: {missing_fields}")
        return False

    print(f"OK: Configuración {config_name} válida")
    return True


# ============================================================================
# CONFIGURACIÓN PARA CADA EXTRACTOR
# ============================================================================

def get_extractor_config(company: str, platform: str) -> Optional[Dict[str, Any]]:
    """Obtiene la configuración para un extractor específico"""

    configs = {
        ("afinia", "oficina_virtual"): OficinaVirtualConfig.AFINIA,
        ("aire", "oficina_virtual"): OficinaVirtualConfig.AIRE
    }

    config = configs.get((company.lower(), platform.lower()))

    if not config:
        print(f"ERROR: Configuración no encontrada para: {company} - {platform}")
        return None

    # Validar configuración
    config_name = f"{company.upper()} {platform.replace('_', ' ').title()}"
    if validate_config(config, config_name):
        return config
    else:
        return None


# ============================================================================
# CONFIGURACIÓN RÁPIDA PARA TESTING
# ============================================================================

# Configuraciones de testing (solo para desarrollo)
TESTING_CONFIG = {
    "use_mock_data": os.getenv("USE_MOCK_DATA", "false").lower() == "true",
    "mock_delay": int(os.getenv("MOCK_DELAY", "2")),
    "enable_screenshots": os.getenv("ENABLE_SCREENSHOTS", "true").lower() == "true"
}

if __name__ == "__main__":
    # Prueba de configuración al ejecutar directamente
    print("[CONFIGURANDO] Probando configuraciones...")

    test_configs = [
        ("afinia", "oficina_virtual"),
        ("aire", "oficina_virtual")
    ]

    for company, platform in test_configs:
        config = get_extractor_config(company, platform)
        if config:
            print(f"[EMOJI_REMOVIDO] {company.upper()} {platform.replace('_', ' ').title()}: OK")
        else:
            print(f"[ERROR] {company.upper()} {platform.replace('_', ' ').title()}: FALLA")
