"""
Procesador de Datos de Afinia
=============================

Este módulo procesa los datos JSON extraídos de la Oficina Virtual de Afinia
y los carga en la base de datos RDS de AWS.

Componentes principales:
- data_processor.py: Procesador principal de datos
- database_manager.py: Gestor de conexiones y operaciones de BD
- models.py: Modelos de datos y esquemas
- validators.py: Validadores de datos JSON
- config.py: Configuración específica de Afinia
"""

from .data_processor import AfiniaDataProcessor
from .database_manager import AfiniaDatabaseManager

__version__ = "1.0.0"
__all__ = ["AfiniaDataProcessor", "AfiniaDatabaseManager"]
