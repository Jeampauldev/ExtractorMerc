"""
Core Components - Componentes Fundamentales del Sistema Mercurio
===============================================================

Módulo que contiene los componentes base y fundamentales para el sistema
de extracción de datos de Mercurio (Afinia y Aire).

Componentes incluidos:
- Base classes y abstracciones
- Managers de navegador y autenticación  
- Adaptadores de datos
- Utilidades compartidas
"""

__version__ = "2.0.0"
__author__ = "ExtractorMerc Team"

# Exportar componentes principales
from .base_extractor import BaseExtractor
from .browser_manager import BrowserManager
from .authentication_manager import AuthenticationManager

__all__ = [
    'BaseExtractor',
    'BrowserManager', 
    'AuthenticationManager'
]