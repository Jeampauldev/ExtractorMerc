"""
Procesador de Datos de Aire
============================

Este módulo procesa los datos JSON extraídos de la Oficina Virtual de Aire
y los carga en la base de datos RDS de AWS.

Componentes principales:
- data_processor.py: Procesador principal de datos
- database_manager.py: Gestor de conexiones y operaciones de BD
- models.py: Modelos de datos y esquemas
- validators.py: Validadores de datos JSON
- config.py: Configuración específica de Aire
"""

from .data_processor import AireDataProcessor
from .database_manager import AireDatabaseManager

__version__ = "1.0.0"
__all__ = ["AireDataProcessor", "AireDatabaseManager"]
