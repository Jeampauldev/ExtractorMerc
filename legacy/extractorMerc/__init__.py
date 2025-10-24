#!/usr/bin/env python3
"""
ExtractorMerc - Módulo de Extractores Mercurio
==============================================

Contiene todos los extractores modulares para la plataforma Mercurio
de diferentes empresas (Afinia, Aire, etc.)

Estructura:
- afinia/: Extractores Mercurio para Afinia
- aire/: Extractores Mercurio para Aire
"""

__version__ = "1.0.0"
__author__ = "ExtractorOV Team"

# Importaciones de conveniencia para acceso directo
try:
    from .afinia.mercurio_afinia_modular import MercurioAfiniaModular, extract_afinia_mercurio
    _afinia_available = True
except ImportError as e:
    print(f"Warning: No se pudo importar MercurioAfiniaModular: {e}")
    MercurioAfiniaModular = None
    extract_afinia_mercurio = None
    _afinia_available = False

try:
    from .aire.mercurio_aire_modular import MercurioAireModular, extract_aire_mercurio
    _aire_available = True
except ImportError as e:
    print(f"Warning: No se pudo importar MercurioAireModular: {e}")
    MercurioAireModular = None
    extract_aire_mercurio = None
    _aire_available = False

# Solo exportar lo que está disponible
__all__ = []
if _afinia_available:
    __all__.extend(['MercurioAfiniaModular', 'extract_afinia_mercurio'])
if _aire_available:
    __all__.extend(['MercurioAireModular', 'extract_aire_mercurio'])
