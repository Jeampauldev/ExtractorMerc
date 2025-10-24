"""
Gestor de Base de Datos para Mercurio Afinia
============================================

Maneja operaciones de BD específicas para datos de Mercurio Afinia.
Hereda funcionalidad base pero usa esquema específico para Mercurio.
"""

import logging
from typing import Dict, List, Optional, Any

# Importar el database manager base de Afinia
from e5_processors.afinia.database_manager import AfiniaDatabaseManager
from .config import MERCURIO_PQR_SCHEMA, MERCURIO_AFINIA_CONFIG

logger = logging.getLogger(__name__)

class MercurioAfiniaDatabaseManager(AfiniaDatabaseManager):
    """
    Gestor de base de datos específico para Mercurio Afinia
    
    Hereda funcionalidad del gestor base de Afinia pero usa
    esquema y configuración específica para datos de Mercurio.
    """
    
    def __init__(self):
        """Inicializa el gestor usando configuración de Mercurio"""
        # Llamar al constructor padre pero sobrescribir esquema
        super().__init__()
        
        # Usar esquema específico de Mercurio
        self.schema = MERCURIO_PQR_SCHEMA
        self.processing_config = MERCURIO_AFINIA_CONFIG
        
        logger.info("✅ MercurioAfiniaDatabaseManager inicializado")
        logger.info(f"Tabla: {self.schema['table_name']}")
    
    def get_record_by_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un registro por hash de contenido
        
        Args:
            content_hash: Hash del contenido
            
        Returns:
            Registro encontrado o None
        """
        try:
            table_name = self.schema['table_name']
            
            # Por ahora usar un campo de identificación alternativo
            # En el futuro se podría agregar un campo hash específico
            select_sql = f"""
                SELECT * FROM `{table_name}` 
                WHERE MD5(CONCAT(
                    COALESCE(numero_radicado, ''),
                    COALESCE(numero_reclamo_sgc, ''),
                    COALESCE(cuerpo_reclamacion, '')
                )) = %s
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(select_sql, (content_hash,))
                    result = cursor.fetchone()
            
            return result
            
        except Exception as e:
            logger.error(f"Error consultando registro por hash: {str(e)}")
            return None
