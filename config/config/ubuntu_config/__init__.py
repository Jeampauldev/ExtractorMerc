#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ubuntu Configuration Module for ExtractorOV
===========================================

Este módulo proporciona configuraciones específicas para Ubuntu Server,
incluyendo detección de entorno, gestión de rutas, y configuración de navegador.

Módulos incluidos:
- environment_detector: Detecta el entorno del sistema y configura variables
- ubuntu_paths: Gestiona rutas multiplataforma para diferentes sistemas
- ubuntu_browser: Configura el navegador para modo headless en Ubuntu Server

Uso básico:
    from ubuntu_config import UbuntuBrowserConfig, get_ubuntu_paths, print_system_info
    
    # Configurar navegador
    config = UbuntuBrowserConfig()
    playwright_config = config.get_playwright_config()
    
    # Obtener rutas del sistema
    paths = get_ubuntu_paths()
    print(f"Directorio de descargas: {paths.downloads_dir}")
    
    # Mostrar información del sistema
    print_system_info()
"""

from .environment_detector import (
    is_ubuntu_server,
    is_headless_required,
    get_recommended_environment_vars,
    get_system_info,
    print_system_info
)

from .ubuntu_paths import (
    PathManager,
    get_ubuntu_paths,
    create_project_directories
)

from .ubuntu_browser import (
    UbuntuBrowserConfig,
    get_browser_config,
    get_chrome_args,
    setup_xvfb_env,
    print_browser_info,
    browser_config
)

__version__ = "1.0.0"
__author__ = "ExtractorOV Team"
__description__ = "Configuraciones específicas para Ubuntu Server"

# Exports principales
__all__ = [
    # Environment detection
    'is_ubuntu_server',
    'is_headless_required', 
    'get_recommended_environment_vars',
    'get_system_info',
    'print_system_info',
    
    # Path management
    'PathManager',
    'get_ubuntu_paths',
    'create_project_directories',
    
    # Browser configuration
    'UbuntuBrowserConfig',
    'get_browser_config',
    'get_chrome_args',
    'setup_xvfb_env',
    'print_browser_info',
    'browser_config',
]

def setup_ubuntu_environment():
    """
    Función de conveniencia para configurar el entorno completo de Ubuntu
    
    Returns:
        dict: Configuración completa del entorno
    """
    from .environment_detector import get_system_info, get_recommended_environment_vars
    from .ubuntu_paths import get_ubuntu_paths
    from .ubuntu_browser import get_browser_config
    
    system_info = get_system_info()
    paths = get_ubuntu_paths()
    browser_config = get_browser_config()
    env_vars = get_recommended_environment_vars()
    
    return {
        'system_info': system_info,
        'paths': paths,
        'browser_config': browser_config,
        'environment_vars': env_vars,
        'is_ubuntu_server': system_info.get('is_ubuntu_server', False),
        'headless_required': system_info.get('headless_required', False)
    }

def print_complete_setup_info():
    """Imprime información completa de configuración del sistema"""
    print("=" * 80)
    print("[INICIANDO] ExtractorOV - Configuración Completa del Entorno Ubuntu")
    print("=" * 80)
    
    # Información del sistema
    print_system_info()
    print()
    
    # Información del navegador
    print_browser_info()
    print()
    
    # Información de rutas
    paths = get_ubuntu_paths()
    paths.print_paths_summary()
    
    print("=" * 80)
    print("[EXITOSO] Configuración completa mostrada")
    print("=" * 80)

# Configuración automática al importar el módulo
if is_ubuntu_server():
    import os
    import logging
    
    # Configurar logging básico
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("[EMOJI_REMOVIDO] Módulo ubuntu_config cargado en Ubuntu Server")
    
    # Configurar variables de entorno básicas si no están definidas
    env_vars = get_recommended_environment_vars()
    for key, value in env_vars.items():
        if not os.getenv(key):
            os.environ[key] = str(value)
            logger.debug(f"Variable de entorno configurada: {key}={value}")