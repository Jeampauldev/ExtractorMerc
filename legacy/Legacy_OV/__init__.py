#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ExtractorOV Modular - Source Package
====================================

Este paquete contiene todos los componentes principales del sistema ExtractorOV.

Módulos disponibles:
- core: Componentes fundamentales (BrowserManager, Authentication)
- components: Componentes específicos de procesamiento
- extractors: Extractores principales de Aire y Afinia
- processors: Procesadores de datos
- config: Configuraciones del sistema
- utils: Utilidades generales
"""

__version__ = "2.0.0"
__author__ = "ExtractorOV Team"
__description__ = "Sistema modular de extracción de datos para oficinas virtuales"

# Imports principales para facilitar el acceso
try:
    from .core.browser_manager import BrowserManager
    from .core.authentication import AuthenticationManager
except ImportError:
    # Fallback si no se pueden importar
    pass

# Información del paquete
__all__ = [
    'BrowserManager',
    'AuthenticationManager',
]

def get_version():
    """Obtiene la versión del paquete"""
    return __version__

def get_extractors():
    """Lista los extractores disponibles"""
    return ['aire', 'afinia']