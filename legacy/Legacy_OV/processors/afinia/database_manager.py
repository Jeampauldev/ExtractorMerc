"""
Gestor de base de datos para operaciones de Afinia.

Este módulo maneja todas las operaciones de base de datos relacionadas
con el procesamiento de datos PQR de Afinia.
"""

import logging
import pymysql
import time
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from .config import RDS_CONFIG, AFINIA_PQR_SCHEMA, PROCESSING_CONFIG

logger = logging.getLogger(__name__)


class AfiniaDatabaseManager:
    """Gestor de base de datos para operaciones de Afinia."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            config: Configuración personalizada de base de datos.
        """
        self.config = config or RDS_CONFIG.copy()
        self.schema = AFINIA_PQR_SCHEMA
        self.processing_config = PROCESSING_CONFIG
        self._connection = None
        
        logger.info("Inicializando AfiniaDatabaseManager")
        logger.info(f"Host: {self.config['host']}")
        logger.info(f"Database: {self.config['database']}")
        logger.info(f"Username: {self.config['username']}")

    def test_connection(self) -> bool:
        """
        Prueba la conexión a la base de datos.
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario.
        """
        try:
            logger.info("Probando conexión a RDS AWS...")
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
            
            logger.info("[EMOJI_REMOVIDO] Conexión a RDS AWS exitosa")
            return True
        
        except Exception as e:
            logger.error(f"[EMOJI_REMOVIDO] Error conectando a RDS AWS: {str(e)}")
            return False

    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener una conexión a la base de datos.
        
        Yields:
            pymysql.Connection: Conexión a la base de datos.
        """
        connection = None
        try:
            connection = pymysql.connect(
                host=self.config['host'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database'],
                port=self.config['port'],
                charset=self.config['charset'],
                connect_timeout=self.config['connect_timeout'],
                read_timeout=self.config['read_timeout'],
                write_timeout=self.config['write_timeout'],
                autocommit=False
            )
            
            logger.debug("Conexión a base de datos establecida")
            yield connection
        
        except Exception as e:
            logger.error(f"Error estableciendo conexión: {str(e)}")
            raise
        finally:
            if connection:
                connection.close()
                logger.debug("Conexión a base de datos cerrada")

    def create_pqr_table(self) -> bool:
        """
        Crea la tabla de PQR si no existe.
        
        Returns:
            bool: True si la tabla fue creada/verificada exitosamente.
        """
        try:
            logger.info("Verificando/creando tabla de PQR de Afinia...")
            
            # Obtener configuración de la tabla
            table_name = self.schema['table_name']
            fields = self.schema['fields']
            
            # Construir definiciones de campos
            field_definitions = []
            for field_name, field_config in fields.items():
                definition = f"`{field_name}` {field_config['type']}"
                
                if field_config.get('nullable', True):
                    definition += " NULL"
                else:
                    definition += " NOT NULL"
                
                if field_config.get('auto_increment', False):
                    definition += " AUTO_INCREMENT"
                
                if field_config.get('default'):
                    if field_config['default'] == 'CURRENT_TIMESTAMP':
                        definition += " DEFAULT CURRENT_TIMESTAMP"
                    elif field_config['default'] == 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP':
                        definition += " DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
                    else:
                        definition += f" DEFAULT '{field_config['default']}'"
                
                if field_config.get('unique', False):
                    definition += " UNIQUE"
                
                field_definitions.append(definition)
            
            # Agregar clave primaria
            primary_keys = [field for field, config in fields.items() if config.get('primary_key', False)]
            if primary_keys:
                field_definitions.append(f"PRIMARY KEY ({', '.join([f'`{pk}`' for pk in primary_keys])})")
            
            # Crear SQL de creación de tabla
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                {', '.join(field_definitions)}
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(create_sql)
                    conn.commit()
            
            logger.info(f"[EMOJI_REMOVIDO] Tabla {table_name} verificada/creada exitosamente")
            
            # Crear índices si están definidos
            self._create_indexes()
            
            return True
        
        except Exception as e:
            logger.error(f"Error creando tabla PQR: {str(e)}")
            return False

    def _create_indexes(self) -> None:
        """Crea los índices definidos en el schema."""
        try:
            table_name = self.schema['table_name']
            indexes = self.schema.get('indexes', [])
            
            if not indexes:
                return
            
            for index in indexes:
                index_name = index['name']
                columns = index['columns']
                
                # Verificar si el índice ya existe
                check_sql = f"""
                SELECT COUNT(*) FROM information_schema.statistics 
                WHERE table_schema = '{self.config['database']}' 
                AND table_name = '{table_name}' 
                AND index_name = '{index_name}'
                """
                
                with self.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(check_sql)
                        exists = cursor.fetchone()[0] > 0
                        
                        if not exists:
                            create_index_sql = f"""
                            CREATE INDEX `{index_name}` ON `{table_name}` 
                            ({', '.join([f'`{col}`' for col in columns])})
                            """
                            cursor.execute(create_index_sql)
                            conn.commit()
                            logger.info(f"[EMOJI_REMOVIDO] Índice {index_name} creado")
        
        except Exception as e:
            logger.error(f"Error creando índices: {str(e)}")

    def insert_pqr_record(self, pqr_data: Dict[str, Any]) -> Optional[int]:
        """
        Inserta un registro de PQR en la base de datos.
        
        Args:
            pqr_data: Diccionario con los datos del PQR.
        
        Returns:
            Optional[int]: ID del registro insertado o None si falló.
        """
        try:
            # Preparar datos para inserción
            prepared_data = self._prepare_data_for_insertion(pqr_data)
            
            table_name = self.schema['table_name']
            columns = list(prepared_data.keys())
            values = list(prepared_data.values())
            
            # Construir SQL de inserción con ON DUPLICATE KEY UPDATE
            column_names = ', '.join([f'`{col}`' for col in columns])
            placeholders = ', '.join(['%s'] * len(values))
            
            insert_sql = f"""
            INSERT INTO `{table_name}` ({column_names}) 
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE
            {', '.join([f'`{col}` = VALUES(`{col}`)' for col in columns if col != 'id'])}
            """
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(insert_sql, values)
                    conn.commit()
                    
                    record_id = cursor.lastrowid or self._get_existing_record_id(
                        prepared_data.get('numero_radicado'), 
                        prepared_data.get('numero_reclamo_sgc')
                    )
                    
                    logger.debug(f"Registro PQR insertado/actualizado con ID: {record_id}")
                    return record_id
        
        except Exception as e:
            logger.error(f"Error insertando registro PQR: {str(e)}")
            return None

    def _prepare_data_for_insertion(self, pqr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara los datos para inserción en la base de datos.
        
        Args:
            pqr_data: Datos originales del PQR.
        
        Returns:
            Dict[str, Any]: Datos preparados para inserción.
        """
        prepared = {}
        fields = self.schema['fields']
        
        for field_name, field_config in fields.items():
            if field_name == 'id':  # Skip auto-increment ID
                continue
            
            value = pqr_data.get(field_name)
            
            # Manejar campos de fecha
            if field_config['type'].startswith('DATETIME') and value:
                if isinstance(value, str):
                    value = self._parse_date(value)
            
            # Manejar campos JSON
            elif field_config['type'] == 'JSON' and value:
                if not isinstance(value, str):
                    value = json.dumps(value, ensure_ascii=False)
            
            # Agregar timestamp de procesamiento
            elif field_name == 'processed_at':
                value = datetime.now()
            
            prepared[field_name] = value
        
        return prepared

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parsea una fecha desde string a datetime.
        
        Args:
            date_str: String de fecha.
        
        Returns:
            Optional[datetime]: Fecha parseada o None si no se pudo parsear.
        """
        if not date_str:
            return None
        
        # Formatos de fecha comunes
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
            '%d-%m-%Y %H:%M:%S',
            '%d-%m-%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"No se pudo parsear la fecha: {date_str}")
        return None

    def _get_existing_record_id(self, numero_radicado: str, numero_reclamo_sgc: str) -> Optional[int]:
        """
        Obtiene el ID de un registro existente.
        
        Args:
            numero_radicado: Número de radicado.
            numero_reclamo_sgc: Número de reclamo SGC.
        
        Returns:
            Optional[int]: ID del registro o None si no existe.
        """
        try:
            table_name = self.schema['table_name']
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"SELECT id FROM `{table_name}` WHERE numero_radicado = %s OR numero_reclamo_sgc = %s LIMIT 1",
                        (numero_radicado, numero_reclamo_sgc)
                    )
                    result = cursor.fetchone()
                    return result[0] if result else None
        
        except Exception as e:
            logger.error(f"Error obteniendo ID de registro existente: {str(e)}")
            return None

    def get_pqr_by_radicado(self, numero_radicado: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un registro por número de radicado.
        
        Args:
            numero_radicado: Número de radicado a buscar.
        
        Returns:
            Optional[Dict[str, Any]]: Registro encontrado o None.
        """
        try:
            table_name = self.schema['table_name']
            
            with self.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(
                        f"SELECT * FROM `{table_name}` WHERE numero_radicado = %s",
                        (numero_radicado,)
                    )
                    return cursor.fetchone()
        
        except Exception as e:
            logger.error(f"Error obteniendo PQR por radicado: {str(e)}")
            return None

    def get_table_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de procesamiento.
        
        Returns:
            Dict[str, Any]: Estadísticas de la tabla.
        """
        try:
            table_name = self.schema['table_name']
            
            stats_sql = f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT numero_radicado) as unique_radicados,
                COUNT(DISTINCT numero_reclamo_sgc) as unique_sgc,
                MIN(processed_at) as first_processed,
                MAX(processed_at) as last_processed,
                COUNT(CASE WHEN processed_at >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) as processed_last_24h
            FROM `{table_name}`
            """
            
            with self.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(stats_sql)
                    return cursor.fetchone() or {}
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {}

    def execute_query(self, query: str, params: Tuple = None) -> List[Tuple]:
        """
        Ejecuta una consulta SQL personalizada.
        
        Args:
            query: Consulta SQL a ejecutar.
            params: Parámetros para la consulta.
        
        Returns:
            List[Tuple]: Resultados de la consulta.
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return cursor.fetchall()
        
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {str(e)}")
            return []

    def close(self) -> None:
        """Cierra el gestor de base de datos."""
        if self._connection:
            self._connection.close()
            self._connection = None
        logger.info("Gestor de base de datos cerrado")
