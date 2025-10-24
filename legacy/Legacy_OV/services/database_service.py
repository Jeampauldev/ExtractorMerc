#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio Unificado de Base de Datos - ExtractorOV
==================================================

Este servicio maneja todas las operaciones de base de datos para cargar
datos extraídos de Afinia y Aire al esquema 'data' en RDS.

Características:
- Conexión unificada a RDS
- Carga de datos a tablas ov_afinia y ov_aire
- Validación de datos antes de inserción
- Control de duplicados
- Transacciones seguras
- Logging detallado
"""

import logging
import pymysql
import json
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import hashlib

# Importar configuración de entorno
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.env_loader import get_rds_config


@dataclass
class DataLoadResult:
    """Resultado de carga de datos"""
    success: bool
    records_processed: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    errors: List[str] = None
    duration_seconds: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DatabaseService:
    """
    Servicio unificado para operaciones de base de datos
    
    Maneja la conexión y operaciones CRUD para las tablas ov_afinia y ov_aire
    en el esquema 'data' de RDS.
    """
    
    # Definición de esquemas de tablas
    TABLE_SCHEMAS = {
        'ov_afinia': {
            'table_name': 'ov_afinia',
            'schema': 'data',
            'fields': {
                'id': {'type': 'INT', 'primary_key': True, 'auto_increment': True},
                'nic': {'type': 'VARCHAR(50)', 'nullable': True},
                'fecha': {'type': 'DATE', 'nullable': True},
                'documento_identidad': {'type': 'VARCHAR(20)', 'nullable': True},
                'nombres_apellidos': {'type': 'VARCHAR(200)', 'nullable': True},
                'correo_electronico': {'type': 'VARCHAR(100)', 'nullable': True},
                'telefono': {'type': 'VARCHAR(20)', 'nullable': True},
                'celular': {'type': 'VARCHAR(20)', 'nullable': True},
                'tipo_pqr': {'type': 'VARCHAR(100)', 'nullable': True},
                'canal_respuesta': {'type': 'VARCHAR(50)', 'nullable': True},
                'numero_radicado': {'type': 'VARCHAR(50)', 'nullable': True, 'index': True},
                'estado_solicitud': {'type': 'VARCHAR(50)', 'nullable': True, 'index': True},
                'lectura': {'type': 'VARCHAR(50)', 'nullable': True},
                'documento_prueba': {'type': 'VARCHAR(255)', 'nullable': True},
                'cuerpo_reclamacion': {'type': 'TEXT', 'nullable': True},
                'finalizar': {'type': 'VARCHAR(50)', 'nullable': True},
                'adjuntar_archivo': {'type': 'VARCHAR(255)', 'nullable': True},
                'numero_reclamo_sgc': {'type': 'VARCHAR(50)', 'nullable': True, 'index': True},
                'comentarios': {'type': 'TEXT', 'nullable': True},
                'extraction_timestamp': {'type': 'DATETIME', 'nullable': True},
                'page_url': {'type': 'VARCHAR(500)', 'nullable': True},
                'data_hash': {'type': 'VARCHAR(32)', 'nullable': True, 'index': True},
                'file_source': {'type': 'VARCHAR(255)', 'nullable': True},
                'processed_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'},
                'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'},
                'updated_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'}
            }
        },
        'ov_aire': {
            'table_name': 'ov_aire',
            'schema': 'data',
            'fields': {
                'id': {'type': 'INT', 'primary_key': True, 'auto_increment': True},
                'nic': {'type': 'VARCHAR(50)', 'nullable': True},
                'fecha': {'type': 'DATE', 'nullable': True},
                'documento_identidad': {'type': 'VARCHAR(20)', 'nullable': True},
                'nombres_apellidos': {'type': 'VARCHAR(200)', 'nullable': True},
                'correo_electronico': {'type': 'VARCHAR(100)', 'nullable': True},
                'telefono': {'type': 'VARCHAR(20)', 'nullable': True},
                'celular': {'type': 'VARCHAR(20)', 'nullable': True},
                'tipo_pqr': {'type': 'VARCHAR(100)', 'nullable': True},
                'canal_respuesta': {'type': 'VARCHAR(50)', 'nullable': True},
                'numero_radicado': {'type': 'VARCHAR(50)', 'nullable': True, 'index': True},
                'estado_solicitud': {'type': 'VARCHAR(50)', 'nullable': True, 'index': True},
                'lectura': {'type': 'VARCHAR(50)', 'nullable': True},
                'documento_prueba': {'type': 'VARCHAR(255)', 'nullable': True},
                'cuerpo_reclamacion': {'type': 'TEXT', 'nullable': True},
                'finalizar': {'type': 'VARCHAR(50)', 'nullable': True},
                'adjuntar_archivo': {'type': 'VARCHAR(255)', 'nullable': True},
                'numero_reclamo_sgc': {'type': 'VARCHAR(50)', 'nullable': True, 'index': True},
                'comentarios': {'type': 'TEXT', 'nullable': True},
                'extraction_timestamp': {'type': 'DATETIME', 'nullable': True},
                'page_url': {'type': 'VARCHAR(500)', 'nullable': True},
                'data_hash': {'type': 'VARCHAR(32)', 'nullable': True, 'index': True},
                'file_source': {'type': 'VARCHAR(255)', 'nullable': True},
                'processed_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'},
                'created_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP'},
                'updated_at': {'type': 'DATETIME', 'default': 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'}
            }
        }
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el servicio de base de datos
        
        Args:
            config: Configuración personalizada de base de datos
        """
        self.config = config or get_rds_config()
        self.logger = logging.getLogger(__name__)
        self._connection = None
        
        # Validar configuración
        self._validate_config()
        
        self.logger.info("DatabaseService inicializado")
        self.logger.info(f"Host: {self.config.get('host', 'NOT_SET')}")
        self.logger.info(f"Database: {self.config.get('database', 'NOT_SET')}")
        self.logger.info(f"Username: {self.config.get('username', 'NOT_SET')}")
    
    def _validate_config(self) -> None:
        """Valida la configuración de base de datos"""
        required_fields = ['host', 'database', 'username', 'password']
        missing = [field for field in required_fields if not self.config.get(field)]
        
        if missing:
            raise ValueError(f"Configuración de RDS incompleta. Campos faltantes: {missing}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener una conexión a la base de datos
        
        Yields:
            pymysql.Connection: Conexión a la base de datos
        """
        connection = None
        try:
            connection = pymysql.connect(
                host=self.config['host'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database'],
                port=self.config.get('port', 3306),
                charset=self.config.get('charset', 'utf8mb4'),
                connect_timeout=30,
                read_timeout=60,
                write_timeout=60,
                autocommit=False
            )
            
            self.logger.debug("Conexión a RDS establecida")
            yield connection
            
        except Exception as e:
            self.logger.error(f"Error estableciendo conexión a RDS: {e}")
            raise
        finally:
            if connection:
                connection.close()
                self.logger.debug("Conexión a RDS cerrada")
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión a la base de datos
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            self.logger.info("Probando conexión a RDS...")
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
            
            self.logger.info("EXITOSO Conexión a RDS exitosa")
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR Error conectando a RDS: {e}")
            return False
    
    def verify_schema_exists(self) -> bool:
        """
        Verifica que el esquema 'data' existe
        
        Returns:
            bool: True si el esquema existe
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = 'data'")
                    result = cursor.fetchone()
                    
                    if result:
                        self.logger.info("EXITOSO Esquema 'data' encontrado")
                        return True
                    else:
                        self.logger.error("ERROR Esquema 'data' no encontrado")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error verificando esquema 'data': {e}")
            return False
    
    def verify_tables_exist(self) -> Dict[str, bool]:
        """
        Verifica que las tablas ov_afinia y ov_aire existen
        
        Returns:
            Dict[str, bool]: Estado de cada tabla
        """
        tables_status = {}
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for table_name in self.TABLE_SCHEMAS.keys():
                        cursor.execute(
                            """
                            SELECT TABLE_NAME 
                            FROM information_schema.TABLES 
                            WHERE TABLE_SCHEMA = 'data' AND TABLE_NAME = %s
                            """,
                            (table_name,)
                        )
                        result = cursor.fetchone()
                        tables_status[table_name] = result is not None
                        
                        if result:
                            self.logger.info(f"EXITOSO Tabla {table_name} encontrada")
                        else:
                            self.logger.warning(f"ADVERTENCIA Tabla {table_name} no encontrada")
                            
        except Exception as e:
            self.logger.error(f"Error verificando tablas: {e}")
            for table_name in self.TABLE_SCHEMAS.keys():
                tables_status[table_name] = False
        
        return tables_status
    
    def generate_data_hash(self, data: Dict[str, Any]) -> str:
        """
        Genera un hash MD5 para los datos
        
        Args:
            data: Diccionario con los datos
            
        Returns:
            str: Hash MD5 de los datos
        """
        # Usar campos clave para generar hash único
        key_fields = [
            str(data.get('nic', '')),
            str(data.get('fecha', '')),
            str(data.get('documento_identidad', '')),
            str(data.get('numero_radicado', ''))
        ]
        
        key_string = '|'.join(key_fields)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def check_duplicate_by_hash(self, table_name: str, data_hash: str) -> bool:
        """
        Verifica si existe un registro con el mismo hash
        
        Args:
            table_name: Nombre de la tabla (ov_afinia o ov_aire)
            data_hash: Hash de los datos
            
        Returns:
            bool: True si existe duplicado
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"SELECT id FROM data.{table_name} WHERE data_hash = %s LIMIT 1",
                        (data_hash,)
                    )
                    result = cursor.fetchone()
                    return result is not None
                    
        except Exception as e:
            self.logger.error(f"Error verificando duplicado por hash: {e}")
            return False
    
    def check_duplicate_by_radicado(self, table_name: str, numero_radicado: str) -> bool:
        """
        Verifica si existe un registro con el mismo número de radicado
        
        Args:
            table_name: Nombre de la tabla (ov_afinia o ov_aire)
            numero_radicado: Número de radicado
            
        Returns:
            bool: True si existe duplicado
        """
        if not numero_radicado or numero_radicado.strip() == '':
            return False
            
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"SELECT id FROM data.{table_name} WHERE numero_radicado = %s LIMIT 1",
                        (numero_radicado.strip(),)
                    )
                    result = cursor.fetchone()
                    return result is not None
                    
        except Exception as e:
            self.logger.error(f"Error verificando duplicado por radicado: {e}")
            return False
    
    def load_data_from_json(self, service_type: str, json_file_path: str, check_duplicates: bool = True) -> DataLoadResult:
        """
        Carga datos desde un archivo JSON a la tabla correspondiente
        
        Args:
            service_type: 'afinia' o 'aire'
            json_file_path: Ruta al archivo JSON
            check_duplicates: Si verificar duplicados antes de insertar
            
        Returns:
            DataLoadResult: Resultado de la carga
        """
        start_time = datetime.now()
        result = DataLoadResult(success=False)
        table_name = f'ov_{service_type}'
        
        if table_name not in self.TABLE_SCHEMAS:
            result.errors.append(f"Tipo de servicio inválido: {service_type}")
            return result
        
        try:
            # Leer archivo JSON
            json_path = Path(json_file_path)
            if not json_path.exists():
                result.errors.append(f"Archivo no encontrado: {json_file_path}")
                return result
            
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Determinar si es un array o un objeto único
            if isinstance(json_data, dict):
                records = [json_data]
            elif isinstance(json_data, list):
                records = json_data
            else:
                result.errors.append("Formato JSON inválido")
                return result
            
            result.records_processed = len(records)
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for record in records:
                        try:
                            # Generar hash de datos
                            data_hash = self.generate_data_hash(record)
                            
                            # Verificar duplicados si está habilitado
                            if check_duplicates:
                                if self.check_duplicate_by_hash(table_name, data_hash):
                                    self.logger.debug(f"Registro duplicado por hash (saltado): {data_hash}")
                                    result.records_skipped += 1
                                    continue
                                
                                numero_radicado = record.get('numero_radicado', '').strip()
                                if numero_radicado and self.check_duplicate_by_radicado(table_name, numero_radicado):
                                    self.logger.debug(f"Registro duplicado por radicado (saltado): {numero_radicado}")
                                    result.records_skipped += 1
                                    continue
                            
                            # Preparar datos para inserción
                            insert_data = self._prepare_insert_data(record, json_path.name, data_hash)
                            
                            # Insertar registro
                            if self._insert_record(cursor, table_name, insert_data):
                                result.records_inserted += 1
                            else:
                                result.records_skipped += 1
                                
                        except Exception as e:
                            error_msg = f"Error procesando registro: {e}"
                            result.errors.append(error_msg)
                            self.logger.error(error_msg)
                            result.records_skipped += 1
                    
                    # Commit transacción
                    conn.commit()
                    
            result.success = True
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                f"Carga completada para {service_type}: "
                f"{result.records_inserted} insertados, "
                f"{result.records_skipped} saltados, "
                f"{len(result.errors)} errores en {result.duration_seconds:.2f}s"
            )
            
        except Exception as e:
            error_msg = f"Error en carga de datos: {e}"
            result.errors.append(error_msg)
            self.logger.error(error_msg)
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
        
        return result
    
    def _prepare_insert_data(self, record: Dict[str, Any], file_source: str, data_hash: str) -> Dict[str, Any]:
        """
        Prepara los datos para inserción en la base de datos
        
        Args:
            record: Registro JSON
            file_source: Nombre del archivo fuente
            data_hash: Hash de los datos
            
        Returns:
            Dict[str, Any]: Datos preparados para inserción
        """
        # Mapear campos del JSON a campos de la tabla
        insert_data = {
            'nic': record.get('nic', ''),
            'fecha': self._parse_date(record.get('fecha', '')),
            'documento_identidad': record.get('documento_identidad', ''),
            'nombres_apellidos': record.get('nombres_apellidos', ''),
            'correo_electronico': record.get('correo_electronico', ''),
            'telefono': record.get('telefono', ''),
            'celular': record.get('celular', ''),
            'tipo_pqr': record.get('tipo_pqr', ''),
            'canal_respuesta': record.get('canal_respuesta', ''),
            'numero_radicado': record.get('numero_radicado', ''),
            'estado_solicitud': record.get('estado_solicitud', ''),
            'lectura': record.get('lectura', ''),
            'documento_prueba': record.get('documento_prueba', ''),
            'cuerpo_reclamacion': record.get('cuerpo_reclamacion', ''),
            'finalizar': record.get('finalizar', ''),
            'adjuntar_archivo': record.get('adjuntar_archivo', ''),
            'numero_reclamo_sgc': record.get('numero_reclamo_sgc', ''),
            'comentarios': record.get('comentarios', ''),
            'extraction_timestamp': self._parse_datetime(record.get('extraction_timestamp', '')),
            'page_url': record.get('page_url', ''),
            'data_hash': data_hash,
            'file_source': file_source
        }
        
        # Limpiar valores None y vacíos
        return {k: v if v != '' else None for k, v in insert_data.items()}
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parsea una fecha en formato string a formato MySQL DATE"""
        if not date_str or date_str.strip() == '':
            return None
        
        try:
            # Intentar varios formatos de fecha
            formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Si no coincide con ningún formato, retornar None
            self.logger.warning(f"Formato de fecha no reconocido: {date_str}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error parseando fecha '{date_str}': {e}")
            return None
    
    def _parse_datetime(self, datetime_str: str) -> Optional[str]:
        """Parsea una fecha-hora en formato string a formato MySQL DATETIME"""
        if not datetime_str or datetime_str.strip() == '':
            return None
        
        try:
            # Intentar varios formatos de fecha-hora
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%d/%m/%Y %H:%M:%S',
                '%d-%m-%Y %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(datetime_str.strip(), fmt)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
            
            # Si no coincide con ningún formato, retornar None
            self.logger.warning(f"Formato de fecha-hora no reconocido: {datetime_str}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error parseando fecha-hora '{datetime_str}': {e}")
            return None
    
    def _insert_record(self, cursor, table_name: str, data: Dict[str, Any]) -> bool:
        """
        Inserta un registro en la tabla especificada
        
        Args:
            cursor: Cursor de la base de datos
            table_name: Nombre de la tabla
            data: Datos a insertar
            
        Returns:
            bool: True si se insertó exitosamente
        """
        try:
            # Preparar query de inserción
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            values = list(data.values())
            
            query = f"INSERT INTO data.{table_name} ({columns}) VALUES ({placeholders})"
            
            cursor.execute(query, values)
            return True
            
        except Exception as e:
            self.logger.error(f"Error insertando registro en {table_name}: {e}")
            return False
    
    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una tabla
        
        Args:
            table_name: Nombre de la tabla (ov_afinia o ov_aire)
            
        Returns:
            Dict[str, Any]: Estadísticas de la tabla
        """
        stats = {
            'table_name': table_name,
            'total_records': 0,
            'latest_record': None,
            'date_range': {'min': None, 'max': None},
            'unique_radicados': 0,
            'error': None
        }
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Total de registros
                    cursor.execute(f"SELECT COUNT(*) as total FROM data.{table_name}")
                    result = cursor.fetchone()
                    stats['total_records'] = result[0] if result else 0
                    
                    # Último registro procesado
                    cursor.execute(f"SELECT MAX(processed_at) as latest FROM data.{table_name}")
                    result = cursor.fetchone()
                    stats['latest_record'] = result[0] if result and result[0] else None
                    
                    # Rango de fechas
                    cursor.execute(f"SELECT MIN(fecha) as min_date, MAX(fecha) as max_date FROM data.{table_name}")
                    result = cursor.fetchone()
                    if result:
                        stats['date_range']['min'] = result[0]
                        stats['date_range']['max'] = result[1]
                    
                    # Número de radicados únicos
                    cursor.execute(f"SELECT COUNT(DISTINCT numero_radicado) as unique_radicados FROM data.{table_name} WHERE numero_radicado IS NOT NULL")
                    result = cursor.fetchone()
                    stats['unique_radicados'] = result[0] if result else 0
                    
        except Exception as e:
            stats['error'] = str(e)
            self.logger.error(f"Error obteniendo estadísticas de {table_name}: {e}")
        
        return stats
    
    def validate_environment(self) -> Dict[str, bool]:
        """
        Valida que el entorno esté correctamente configurado
        
        Returns:
            Dict[str, bool]: Estado de validación
        """
        validation = {
            'connection': False,
            'schema': False,
            'tables': {}
        }
        
        try:
            # Probar conexión
            validation['connection'] = self.test_connection()
            
            if validation['connection']:
                # Verificar esquema
                validation['schema'] = self.verify_schema_exists()
                
                if validation['schema']:
                    # Verificar tablas
                    validation['tables'] = self.verify_tables_exist()
            
        except Exception as e:
            self.logger.error(f"Error en validación del entorno: {e}")
        
        return validation


# Factory function para crear instancia del servicio
def create_database_service(config: Optional[Dict] = None) -> DatabaseService:
    """
    Crea una instancia del servicio de base de datos
    
    Args:
        config: Configuración personalizada
        
    Returns:
        DatabaseService: Instancia del servicio
    """
    return DatabaseService(config)


# Funciones de utilidad
def load_json_to_database(service_type: str, json_file_path: str, 
                         config: Optional[Dict] = None, 
                         check_duplicates: bool = True) -> DataLoadResult:
    """
    Función de utilidad para cargar un archivo JSON a la base de datos
    
    Args:
        service_type: 'afinia' o 'aire'
        json_file_path: Ruta al archivo JSON
        config: Configuración de base de datos opcional
        check_duplicates: Si verificar duplicados
        
    Returns:
        DataLoadResult: Resultado de la carga
    """
    db_service = create_database_service(config)
    return db_service.load_data_from_json(service_type, json_file_path, check_duplicates)


if __name__ == "__main__":
    # Test del servicio
    import argparse
    
    parser = argparse.ArgumentParser(description='Servicio de Base de Datos - ExtractorOV')
    parser.add_argument('--test-connection', action='store_true', help='Probar conexión a RDS')
    parser.add_argument('--validate-env', action='store_true', help='Validar entorno')
    parser.add_argument('--table-stats', choices=['ov_afinia', 'ov_aire'], help='Mostrar estadísticas de tabla')
    parser.add_argument('--load-json', help='Cargar archivo JSON')
    parser.add_argument('--service-type', choices=['afinia', 'aire'], help='Tipo de servicio para carga')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Crear servicio
    db_service = create_database_service()
    
    if args.test_connection:
        print("VERIFICANDO Probando conexión a RDS...")
        success = db_service.test_connection()
        print(f"Resultado: {'EXITOSO Éxito' if success else 'ERROR Error'}")
    
    elif args.validate_env:
        print("VERIFICANDO Validando entorno...")
        validation = db_service.validate_environment()
        print(f"Conexión: {'EXITOSO' if validation['connection'] else 'ERROR'}")
        print(f"Esquema 'data': {'EXITOSO' if validation['schema'] else 'ERROR'}")
        for table, exists in validation['tables'].items():
            print(f"Tabla {table}: {'EXITOSO' if exists else 'ERROR'}")
    
    elif args.table_stats:
        print(f"PROCESADOS Estadísticas de tabla {args.table_stats}...")
        stats = db_service.get_table_stats(args.table_stats)
        if stats['error']:
            print(f"ERROR Error: {stats['error']}")
        else:
            print(f"Total registros: {stats['total_records']}")
            print(f"Último procesado: {stats['latest_record']}")
            print(f"Rango fechas: {stats['date_range']['min']} - {stats['date_range']['max']}")
            print(f"Radicados únicos: {stats['unique_radicados']}")
    
    elif args.load_json and args.service_type:
        print(f"DESCARGANDO Cargando datos de {args.service_type} desde {args.load_json}...")
        result = db_service.load_data_from_json(args.service_type, args.load_json)
        
        if result.success:
            print(f"EXITOSO Carga exitosa:")
            print(f"   Procesados: {result.records_processed}")
            print(f"   Insertados: {result.records_inserted}")
            print(f"   Saltados: {result.records_skipped}")
            print(f"   Duración: {result.duration_seconds:.2f}s")
        else:
            print(f"ERROR Error en carga:")
            for error in result.errors:
                print(f"   • {error}")
    
    else:
        parser.print_help()