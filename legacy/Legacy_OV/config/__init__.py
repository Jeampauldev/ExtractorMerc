"""
Módulo de Configuración - Gestión Centralizada de Configuraciones
=================================================================

Este módulo contiene todas las configuraciones centralizadas del sistema
ExtractorOV Modular, incluyendo configuraciones por empresa, selectores CSS,
URLs, timeouts y parámetros de extracción.

Componentes Principales:
-----------------------
- config.py: Configuración general del sistema
 * URLs base de las plataformas
 * Timeouts y reintentos
 * Configuración de logging
 * Parámetros globales del sistema

- afinia_config.py: Configuración específica de Afinia
 * Selectores CSS específicos
 * URLs de navegación
 * Configuración de filtros
 * Parámetros de extracción

- default_configs.py: Configuraciones por defecto
 * Valores predeterminados
 * Configuraciones fallback
 * Constantes del sistema

- extractor_config.py: Configuración de extractores
 * Parámetros de cada extractor
 * Configuración de componentes
 * Mapeo de empresas a extractores

Uso:
----
```python
from f_config_06 import get_config, AFINIA_CONFIG

# Obtener configuración general
config = get_config()

# Usar configuración específica de Afinia
afinia_urls = AFINIA_CONFIG['urls']
afinia_selectors = AFINIA_CONFIG['selectors']
```

Características:
---------------
- Configuración centralizada y organizada
- Fácil mantenimiento y actualización
- Separación por empresa y funcionalidad
- Soporte para múltiples ambientes
- Validación de configuraciones

Notas:
------
Las credenciales sensibles (usuarios, contraseñas, API keys) NO se
almacenan aquí. Se gestionan mediante variables de entorno usando
python-dotenv para mayor seguridad.

Versión: 1.0.0
Autor: ExtractorOV Team
Fecha: Octubre 2025
"""

from .config import get_extractor_config, ExtractorConfig
from .afinia_config import AFINIA_SPECIFIC_CONFIG
# from .extractor_config import EXTRACTOR_CONFIGS # Comentado temporalmente

__version__ = "1.0.0"
__author__ = "ExtractorOV Team"

__all__ = [
 "get_config",
 "Config",
 "AFINIA_CONFIG",
 "EXTRACTOR_CONFIGS",
]
