#!/usr/bin/env python3
"""
Procesador de Datos para Mercurio Afinia
========================================

Procesador específico para datos extraídos de Mercurio de Afinia.
Adapta el sistema de procesamiento base para las particularidades
de los datos de Mercurio vs Oficina Virtual.

Características:
- Adaptado para estructura de datos de Mercurio
- Validaciones específicas para campos de Mercurio
- Mapeo de campos apropiado para esquema de BD
- Manejo de duplicados específico para Mercurio
- Logging y métricas especializadas
"""

import logging
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Imports del sistema base
from e5_processors.afinia.validators import JSONValidator
from e5_processors.mercurio_afinia.database_manager import DatabaseManager
from e5_processors.mercurio_afinia.logger import MetricsCollector
from g7_utils.file_utils import FileUtils
from f6_config.config import Config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[MERCURIO-AFINIA-PROCESSOR] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class MercurioAfiniaDataProcessor:
    """
    Procesador de datos específico para Mercurio Afinia
    
    Maneja la validación, transformación y carga de datos JSON
    extraídos de Mercurio Afinia hacia RDS AWS.
    """
    
    def __init__(self):
        """Inicializa el procesador de Mercurio Afinia"""
        self.config = MERCURIO_AFINIA_CONFIG
        self.schema = MERCURIO_PQR_SCHEMA
        self.field_mapping = FIELD_MAPPING_MERCURIO
        
        # Inicializar componentes
        self.db_manager = MercurioAfiniaDatabaseManager()
        self.validator = MercurioJSONValidator()
        
        # Contadores y métricas
        self.processing_stats = {
            'files_processed': 0,
            'records_processed': 0,
            'records_inserted': 0,
            'duplicates_found': 0,
            'validation_errors': 0,
            'database_errors': 0,
            'processing_start': None,
            'processing_end': None
        }
        
        logger.info("✅ MercurioAfiniaDataProcessor inicializado")
    
    def process_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Procesa un archivo JSON de Mercurio Afinia
        
        Args:
            file_path: Ruta al archivo JSON
            
        Returns:
            Dict con resultados del procesamiento
        """
        logger.info(f"📁 Procesando archivo: {file_path}")
        
        # Inicializar métricas de procesamiento
        self.processing_stats['processing_start'] = datetime.now()
        
        result = {
            'success': False,
            'processed_count': 0,
            'duplicates_found': 0,
            'validation_errors': 0,
            'database_errors': 0,
            'error': None
        }
        
        try:
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                error_msg = f"Archivo no encontrado: {file_path}"
                logger.error(error_msg)
                result['error'] = error_msg
                return result
            
            # Cargar datos JSON
            logger.info("📄 Cargando datos JSON...")
            json_data = self._load_json_file(file_path)
            
            if not json_data:
                error_msg = "No se pudieron cargar datos del archivo JSON"
                result['error'] = error_msg
                return result
            
            # Determinar si es una lista o un diccionario único
            if isinstance(json_data, list):
                records = json_data
            elif isinstance(json_data, dict):
                # Si es un dict, puede tener diferentes estructuras
                # Buscar el array de datos
                if 'data' in json_data:
                    records = json_data['data']
                elif 'records' in json_data:
                    records = json_data['records']
                elif 'pqr' in json_data:
                    records = json_data['pqr']
                else:
                    # Tratar como registro único
                    records = [json_data]
            else:
                records = [json_data]
            
            logger.info(f"📊 Total de registros a procesar: {len(records)}")
            
            # Procesar cada registro
            for i, record in enumerate(records):
                try:
                    logger.debug(f"Procesando registro {i+1}/{len(records)}")
                    
                    # Validar registro
                    validation_result = self.validator.validate_record(record)
                    
                    if not validation_result['is_valid']:
                        logger.warning(f"⚠️ Registro {i+1} no válido: {validation_result['errors']}")
                        result['validation_errors'] += 1
                        self.processing_stats['validation_errors'] += 1
                        continue
                    
                    # Transformar y mapear campos
                    transformed_record = self._transform_record(record)
                    
                    # Verificar duplicados
                    if self._is_duplicate(transformed_record):
                        logger.debug(f"🔄 Registro {i+1} es duplicado, omitiendo")
                        result['duplicates_found'] += 1
                        self.processing_stats['duplicates_found'] += 1
                        continue
                    
                    # Insertar en base de datos
                    insert_result = self.db_manager.insert_pqr_record(transformed_record)
                    
                    if insert_result:
                        result['processed_count'] += 1
                        self.processing_stats['records_processed'] += 1
                        self.processing_stats['records_inserted'] += 1
                        logger.debug(f"✅ Registro {i+1} insertado con ID: {insert_result}")
                    else:
                        result['database_errors'] += 1
                        self.processing_stats['database_errors'] += 1
                        logger.error(f"❌ Error insertando registro {i+1}")
                
                except Exception as e:
                    logger.error(f"💥 Error procesando registro {i+1}: {str(e)}")
                    result['database_errors'] += 1
                    self.processing_stats['database_errors'] += 1
                    continue
            
            # Marcar como exitoso si se procesó al menos un registro
            if result['processed_count'] > 0:
                result['success'] = True
                logger.info(f"✅ Procesamiento exitoso: {result['processed_count']} registros procesados")
            else:
                logger.warning("⚠️ No se procesó ningún registro válido")
                result['error'] = "No se procesaron registros válidos"
            
            # Actualizar estadísticas del archivo
            self.processing_stats['files_processed'] += 1
            
        except Exception as e:
            error_msg = f"Error general procesando archivo: {str(e)}"
            logger.error(f"💥 {error_msg}")
            result['error'] = error_msg
        
        finally:
            self.processing_stats['processing_end'] = datetime.now()
        
        return result
    
    def process_directory(self, directory_path: str, file_pattern: str = "*.json") -> Dict[str, Any]:
        """
        Procesa todos los archivos JSON en un directorio
        
        Args:
            directory_path: Ruta al directorio
            file_pattern: Patrón de archivos a procesar
            
        Returns:
            Dict con resultados del procesamiento
        """
        logger.info(f"📂 Procesando directorio: {directory_path}")
        
        # Inicializar resultado
        result = {
            'success': False,
            'files_processed': 0,
            'total_records': 0,
            'total_duplicates': 0,
            'total_validation_errors': 0,
            'total_database_errors': 0,
            'processed_files': [],
            'failed_files': [],
            'errors': []
        }
        
        try:
            # Buscar archivos JSON
            directory = Path(directory_path)
            if not directory.exists():
                error_msg = f"Directorio no encontrado: {directory_path}"
                logger.error(error_msg)
                result['errors'].append(error_msg)
                return result
            
            json_files = list(directory.glob(file_pattern))
            logger.info(f"📁 Encontrados {len(json_files)} archivos para procesar")
            
            if not json_files:
                logger.warning("⚠️ No se encontraron archivos JSON en el directorio")
                result['success'] = True  # No es error, simplemente no hay archivos
                return result
            
            # Procesar cada archivo
            for file_path in json_files:
                logger.info(f"🔄 Procesando archivo: {file_path.name}")
                
                try:
                    file_result = self.process_json_file(str(file_path))
                    
                    if file_result['success']:
                        result['files_processed'] += 1
                        result['processed_files'].append({
                            'file': str(file_path),
                            'records': file_result['processed_count'],
                            'duplicates': file_result['duplicates_found'],
                            'validation_errors': file_result['validation_errors']
                        })
                    else:
                        result['failed_files'].append({
                            'file': str(file_path),
                            'error': file_result.get('error', 'Error desconocido')
                        })
                        result['errors'].append(f"Error procesando {file_path.name}: {file_result.get('error', 'Error desconocido')}")
                    
                    # Acumular estadísticas
                    result['total_records'] += file_result['processed_count']
                    result['total_duplicates'] += file_result['duplicates_found']
                    result['total_validation_errors'] += file_result['validation_errors']
                    result['total_database_errors'] += file_result['database_errors']
                
                except Exception as e:
                    error_msg = f"Error procesando {file_path.name}: {str(e)}"
                    logger.error(f"💥 {error_msg}")
                    result['failed_files'].append({
                        'file': str(file_path),
                        'error': error_msg
                    })
                    result['errors'].append(error_msg)
            
            # Determinar éxito general
            result['success'] = result['files_processed'] > 0
            
            # Log resumen
            logger.info("📊 RESUMEN DE PROCESAMIENTO DE DIRECTORIO:")
            logger.info(f"   - Archivos procesados: {result['files_processed']}")
            logger.info(f"   - Archivos fallidos: {len(result['failed_files'])}")
            logger.info(f"   - Total registros: {result['total_records']}")
            logger.info(f"   - Total duplicados: {result['total_duplicates']}")
            logger.info(f"   - Errores de validación: {result['total_validation_errors']}")
            
        except Exception as e:
            error_msg = f"Error general procesando directorio: {str(e)}"
            logger.error(f"💥 {error_msg}")
            result['errors'].append(error_msg)
        
        return result
    
    def _load_json_file(self, file_path: str) -> Optional[Any]:
        """Carga un archivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error cargando archivo JSON: {e}")
            return None
    
    def _transform_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforma un registro según el mapeo de campos de Mercurio
        
        Args:
            record: Registro original de Mercurio
            
        Returns:
            Registro transformado para BD
        """
        transformed = {}
        
        # Aplicar mapeo de campos
        for mercurio_field, db_field in self.field_mapping.items():
            value = record.get(mercurio_field, '')
            
            # Limpiar y transformar valor
            if value is None or value == '':
                transformed[db_field] = None
            elif isinstance(value, str):
                # Limpiar strings
                cleaned_value = value.strip()
                transformed[db_field] = cleaned_value if cleaned_value != '' else None
            else:
                transformed[db_field] = value
        
        # Agregar metadatos de procesamiento
        transformed['extraction_source'] = 'mercurio'
        transformed['extraction_timestamp'] = datetime.now()
        
        return transformed
    
    def _is_duplicate(self, record: Dict[str, Any]) -> bool:
        """
        Verifica si un registro es duplicado basado en campos únicos
        
        Args:
            record: Registro a verificar
            
        Returns:
            True si es duplicado
        """
        # Verificar por número de radicado (campo único principal)
        numero_radicado = record.get('numero_radicado')
        if numero_radicado:
            existing = self.db_manager.get_record_by_radicado(numero_radicado)
            if existing:
                return True
        
        # Verificar por hash de contenido (como backup)
        content_hash = self.validator.generate_content_hash(record)
        if content_hash:
            existing = self.db_manager.get_record_by_hash(content_hash)
            if existing:
                return True
        
        return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del procesamiento
        
        Returns:
            Dict con estadísticas
        """
        stats = self.processing_stats.copy()
        
        # Calcular duración si está disponible
        if stats['processing_start'] and stats['processing_end']:
            duration = stats['processing_end'] - stats['processing_start']
            stats['processing_duration_seconds'] = duration.total_seconds()
        
        # Agregar estadísticas de BD
        db_stats = self.db_manager.get_processing_stats()
        stats['database_stats'] = db_stats
        
        return stats
    
    def reset_stats(self):
        """Reinicia las estadísticas de procesamiento"""
        self.processing_stats = {
            'files_processed': 0,
            'records_processed': 0,
            'records_inserted': 0,
            'duplicates_found': 0,
            'validation_errors': 0,
            'database_errors': 0,
            'processing_start': None,
            'processing_end': None
        }
        logger.info("🔄 Estadísticas de procesamiento reiniciadas")


def process_mercurio_afinia_file(file_path: str) -> Dict[str, Any]:
    """
    Función de conveniencia para procesar un archivo de Mercurio Afinia
    
    Args:
        file_path: Ruta al archivo JSON
        
    Returns:
        Resultado del procesamiento
    """
    processor = MercurioAfiniaDataProcessor()
    return processor.process_json_file(file_path)


def process_mercurio_afinia_directory(directory_path: str) -> Dict[str, Any]:
    """
    Función de conveniencia para procesar un directorio de archivos de Mercurio Afinia
    
    Args:
        directory_path: Ruta al directorio
        
    Returns:
        Resultado del procesamiento
    """
    processor = MercurioAfiniaDataProcessor()
    return processor.process_directory(directory_path)


if __name__ == "__main__":
    # Test básico del procesador
    logger.info("🧪 Ejecutando test básico del procesador de Mercurio Afinia")
    
    processor = MercurioAfiniaDataProcessor()
    
    # Test de conectividad BD
    if processor.db_manager.test_connection():
        logger.info("✅ Conexión a BD exitosa")
        
        # Test de creación de tablas
        if processor.db_manager.create_table_if_not_exists():
            logger.info("✅ Tablas verificadas/creadas")
        else:
            logger.error("❌ Error creando tablas")
    else:
        logger.error("❌ Error de conexión a BD")
    
    logger.info("🏁 Test básico completado")
