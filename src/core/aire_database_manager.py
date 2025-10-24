#!/usr/bin/env python3
"""
Database Manager para Mercurio Aire
===================================

Maneja las operaciones de base de datos específicas para Mercurio Aire.
"""

import logging
import pymysql
from typing import Dict, List, Optional, Any
from e5_processors.aire.database_manager import AfiniaDatabaseManager

logger = logging.getLogger(__name__)

class DatabaseManager(AfiniaDatabaseManager):
    """
    Database Manager específico para Mercurio Aire
    Hereda de AfiniaDatabaseManager y añade funcionalidades específicas
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa el Database Manager para Mercurio Aire
        
        Args:
            config: Configuración de base de datos (opcional)
        """
        super().__init__()
        if config:
            self.config.update(config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("🔧 DatabaseManager para Mercurio Aire inicializado")
    
    def insert_mercurio_record(self, record: Dict[str, Any]) -> bool:
        """
        Inserta un registro específico de Mercurio Aire
        
        Args:
            record: Registro a insertar
            
        Returns:
            bool: True si la inserción fue exitosa
        """
        try:
            # Agregar metadatos específicos de Mercurio
            record['source_system'] = 'mercurio_aire'
            record['extraction_method'] = 'automated'
            
            result = self.insert_pqr_record(record)
            return result is not None
            
        except Exception as e:
            self.logger.error(f"❌ Error insertando registro Mercurio Aire: {e}")
            return False
    
    def get_mercurio_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas específicas de Mercurio Aire
        
        Returns:
            Dict con estadísticas
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                
                query = """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT numero_radicado) as unique_radicados,
                    MAX(processed_at) as last_processed
                FROM afinia_pqr 
                WHERE source_system = 'mercurio_aire'
                """
                
                cursor.execute(query)
                result = cursor.fetchone()
                return result if result else {}
                
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo estadísticas Mercurio Aire: {e}")
            return {}