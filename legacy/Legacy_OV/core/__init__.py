"""
Módulo Core - Núcleo del Sistema ExtractorOV Modular
====================================================

Este módulo contiene las clases fundamentales y componentes base del sistema
de extracción automatizada de datos desde plataformas de Oficina Virtual.

Componentes Principales:
-----------------------
- authentication.py: Gestión de autenticación y sesiones de usuario
 * Manejo de credenciales desde variables de entorno
 * Login automático con detección de errores
 * Gestión de sesiones y cookies

- base_extractor.py: Clase base abstracta para todos los extractores
 * Define la interfaz común para extractores
 * Implementa métodos compartidos de navegación
 * Gestiona el ciclo de vida del extractor

- browser_manager.py: Administración de instancias de navegador
 * Configuración de Playwright (Chromium/Firefox/WebKit)
 * Manejo de contextos y páginas
 * Gestión de viewport y configuraciones de navegador
 * Soporte para modo headless y visual

- download_manager.py: Gestión de descargas de archivos
 * Configuración de directorios de descarga
 * Monitoreo de archivos descargados
 * Validación de descargas completadas
 * Limpieza y organización de archivos

Uso:
----
```python
from a_core_01 import BrowserManager, AuthenticationManager

# Inicializar gestor de navegador
browser_mgr = BrowserManager(headless=False)
page = await browser_mgr.get_page()

# Autenticar usuario
auth_mgr = AuthenticationManager(page)
success = await auth_mgr.login(username, password)
```

Dependencias:
------------
- playwright: Automatización de navegadores
- loguru: Sistema de logging avanzado
- python-dotenv: Gestión de variables de entorno

Notas:
------
Este módulo es la base sobre la cual se construyen todos los extractores
específicos de empresas (Afinia, Aire, etc.). Proporciona funcionalidad
reutilizable y estandarizada para interactuar con navegadores web.

Versión: 1.0.0
Autor: ExtractorOV Team
Fecha: Octubre 2025
"""

from .authentication import AuthenticationManager
from .base_extractor import BaseExtractor
from .browser_manager import BrowserManager
from .download_manager import DownloadManager

__version__ = "1.0.0"
__author__ = "ExtractorOV Team"

__all__ = [
 "AuthenticationManager",
 "BaseExtractor",
 "BrowserManager",
 "DownloadManager",
]
