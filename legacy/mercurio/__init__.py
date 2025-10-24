"""
Módulo ExtractorMerc - Extracción desde Plataforma Mercurio
===============================================

Sistema ExtractorMerc desarrollado por ISES para automatizar la extracción
de Informes de Pérdidas Operacionales desde la plataforma externa Mercurio.

Implementaciones específicas por empresa:
- Aire: Extracción ExtractorMerc desde Mercurio para Air-e
- Afinia: Extracción ExtractorMerc desde Mercurio para Afinia

Funcionalidades principales:
- Extracción automatizada de datos desde Mercurio
- Carga y transformación de datos extraídos
- Generación de reportes
- Auditoría de cartas
- Procesamiento de verbales
- Integración con AWS S3
"""

from .aire import *
from .afinia import *
from .base import *