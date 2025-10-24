"""
Módulo de Componentes - Funcionalidades Especializadas
======================================================

Este módulo contiene componentes reutilizables que implementan
funcionalidades específicas y especializadas para la extracción
de datos desde interfaces web de Oficina Virtual.

Componentes Principales:
-----------------------
- date_configurator.py: Configuración de rangos de fechas
 * Manejo de calendarios y date pickers
 * Configuración de fechas inicio y fin
 * Validación de rangos de fechas
 * Soporte para diferentes formatos de fecha

- filter_manager.py: Gestión de filtros y búsquedas
 * Configuración de filtros de estado (abierto, cerrado, etc.)
 * Aplicación de filtros de fecha
 * Expansión y colapso de paneles de filtros
 * Validación de filtros aplicados

- popup_handler.py: Manejo de ventanas emergentes y modales
 * Detección automática de popups
 * Múltiples estrategias de cierre
 * Manejo de alertas y confirmaciones
 * Gestión de overlays y modales

- pqr_detail_extractor.py: Extracción de detalles de PQR
 * Navegación a detalles de registros
 * Extracción de información completa
 * Manejo de tabs y secciones
 * Captura de datos estructurados

- report_processor.py: Procesamiento de reportes descargados
 * Validación de archivos descargados
 * Extracción de datos de Excel/PDF
 * Transformación de formatos
 * Limpieza y normalización de datos

Uso:
----
```python
from c_components_03 import FilterManager, PopupHandler

# Configurar filtros
filter_mgr = FilterManager(page)
await filter_mgr.set_date_range(start_date, end_date)
await filter_mgr.set_status_filter('abierto')

# Manejar popups
popup_handler = PopupHandler(page)
await popup_handler.close_all_popups()
```

Características:
---------------
- Componentes desacoplados y reutilizables
- Manejo robusto de errores
- Logging detallado de operaciones
- Configuración flexible por componente
- Soporte para múltiples plataformas

Versión: 1.0.0
Autor: ExtractorOV Team
Fecha: Octubre 2025
"""

from .date_configurator import DateConfigurator
from .filter_manager import FilterManager
from .popup_handler import PopupHandler
from .pqr_detail_extractor import PQRDetailExtractor
from .report_processor import ReportProcessor

__version__ = "1.0.0"
__author__ = "ExtractorOV Team"

__all__ = [
 "DateConfigurator",
 "FilterManager",
 "PopupHandler",
 "PQRDetailExtractor",
 "ReportProcessor",
]
