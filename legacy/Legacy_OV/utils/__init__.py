"""
Módulo de Utilidades - Herramientas y Funciones Auxiliares
==========================================================

Este módulo contiene utilidades de propósito general que son utilizadas
a través de todo el sistema ExtractorOV Modular. Proporciona funciones
auxiliares, decoradores y herramientas comunes.

Componentes Principales:
-----------------------
- performance_monitor.py: Monitoreo de rendimiento
 * Decoradores para medir tiempos de ejecución
 * Tracking de métricas de performance
 * Generación de reportes de rendimiento
 * Detección de cuellos de botella

- file_utils.py: Utilidades para manejo de archivos
 * Operaciones de lectura/escritura
 * Gestión de directorios
 * Validación de archivos
 * Limpieza y organización

- dashboard_logger.py: Logger especializado para dashboard
 * Logging estructurado para visualización
 * Formateo de mensajes para UI
 * Niveles de log personalizados
 * Integración con sistema de métricas

Funcionalidad:
-------------
Las utilidades proporcionan funcionalidad transversal que es
necesaria en múltiples partes del sistema, evitando duplicación
de código y promoviendo la reutilización.

Uso:
----
```python
from g_utils_07 import performance_monitor, file_utils

# Usar decorador de performance
@performance_monitor.track_time
async def mi_funcion():
 pass

# Usar utilidades de archivos
file_utils.ensure_directory_exists('downloads')
files = file_utils.list_files_by_extension('downloads', '.pdf')
```

Características:
---------------
- Funciones genéricas y reutilizables
- Decoradores para funcionalidad transversal
- Manejo robusto de errores
- Logging integrado
- Documentación completa

Versión: 1.0.0
Autor: ExtractorOV Team
Fecha: Octubre 2025
"""

from .performance_monitor import PerformanceMonitor
from .file_utils import FileUtils
from .dashboard_logger import DashboardLogger

__version__ = "1.0.0"
__author__ = "ExtractorOV Team"

__all__ = [
 "PerformanceMonitor",
 "track_time",
 "FileUtils",
 "DashboardLogger",
]
