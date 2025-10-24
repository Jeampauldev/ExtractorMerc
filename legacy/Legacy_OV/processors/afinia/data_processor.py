"""
Procesador de datos para Afinia.

Este módulo maneja el procesamiento de archivos JSON de PQR de Afinia,
incluyendo validación, inserción en base de datos y generación de reportes.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib

from src.config.config import OficinaVirtualConfig
from src.processors.afinia.config import AFINIA_CONFIG
from src.processors.afinia.database_manager import AfiniaDatabaseManager
from src.processors.afinia.validators import JSONValidator, validate_single_json
from src.processors.afinia.models import AfiniaPQRData, ProcessingResult, BatchProcessingResult


class AfiniaDataProcessor:
    """
    Procesador principal para datos de PQR de Afinia.
    
    Maneja la validación, procesamiento e inserción de datos de PQR
    desde archivos JSON hacia la base de datos.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa el procesador de datos.

        Args:
            config: Configuración personalizada. Si no se proporciona, usa AFINIA_CONFIG.
        """
        self.config = config or AFINIA_CONFIG
        self.db_manager = AfiniaDatabaseManager(self.config['database'])
        self.validator = JSONValidator()
        self.logger = self._setup_logging()
        
        # Estadísticas de procesamiento
        self.stats = {
            'files_processed': 0,
            'records_processed': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'validation_errors': 0,
            'database_errors': 0
        }

    def _setup_logging(self) -> logging.Logger:
        """Configura el sistema de logging."""
        logger = logging.getLogger(f"{__name__}.AfiniaDataProcessor")
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger

    def process_json_file(self, file_path: str) -> ProcessingResult:
        """
        Procesa un archivo JSON individual.

        Args:
            file_path: Ruta al archivo JSON a procesar.

        Returns:
            ProcessingResult: Resultado del procesamiento.
        """
        start_time = time.time()
        file_name = Path(file_path).name
        
        result = ProcessingResult(
            archivo=file_name,
            total_registros=0,
            registros_validos=0,
            registros_invalidos=0,
            registros_insertados=0,
            registros_actualizados=0
        )
        
        try:
            self.logger.info(f"Iniciando procesamiento de {file_name}")
            
            # Validar archivo JSON
            is_valid, errors, pqr_data = validate_single_json(file_path)
            result.total_registros = 1  # Un archivo = un registro PQR
            
            if not is_valid:
                result.registros_invalidos = 1
                result.errores = errors
                self.stats['validation_errors'] += 1
                self.logger.warning(f"Archivo {file_name} inválido: {errors}")
                return result
            
            result.registros_validos = 1
            
            # Cargar datos JSON y generar hash
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            pqr_data.hash_registro = self.validator.generate_data_hash(json_data)
            pqr_data.archivo_origen = file_name
            
            # Insertar en base de datos
            success, db_errors = self._insert_pqr_data(pqr_data)
            
            if success:
                result.registros_insertados = 1
                self.stats['records_inserted'] += 1
                self.logger.info(f"Registro de {file_name} insertado exitosamente")
            else:
                result.errores.extend(db_errors)
                self.stats['database_errors'] += 1
                self.logger.error(f"Error al insertar {file_name}: {db_errors}")
        
        except Exception as e:
            error_msg = f"Error inesperado procesando {file_name}: {str(e)}"
            result.errores.append(error_msg)
            self.logger.error(error_msg)
        
        finally:
            result.tiempo_procesamiento = time.time() - start_time
            self.stats['files_processed'] += 1
            self.stats['records_processed'] += result.total_registros
        
        return result

    def _insert_pqr_data(self, pqr_data: AfiniaPQRData) -> Tuple[bool, List[str]]:
        """
        Inserta datos de PQR en la base de datos.

        Args:
            pqr_data: Datos de PQR a insertar.

        Returns:
            Tuple[bool, List[str]]: (éxito, lista de errores)
        """
        try:
            # Verificar conexión
            if not self.db_manager.test_connection():
                return False, ["No se pudo conectar a la base de datos"]
            
            # Crear tabla si no existe
            if not self.db_manager.create_pqr_table():
                return False, ["No se pudo crear/verificar la tabla PQR"]
            
            # Insertar registro
            success = self.db_manager.insert_pqr_record(pqr_data.to_dict())
            
            if success:
                return True, []
            else:
                return False, ["Error al insertar registro en la base de datos"]
        
        except Exception as e:
            return False, [f"Error de base de datos: {str(e)}"]

    def process_directory(self, directory_path: str, pattern: str = "pqr_*.json") -> BatchProcessingResult:
        """
        Procesa todos los archivos JSON en un directorio.

        Args:
            directory_path: Ruta al directorio a procesar.
            pattern: Patrón de archivos a buscar.

        Returns:
            BatchProcessingResult: Resultado del procesamiento en lote.
        """
        batch_result = BatchProcessingResult()
        
        try:
            self.logger.info(f"Iniciando procesamiento en lote de {directory_path}")
            
            directory = Path(directory_path)
            if not directory.exists():
                self.logger.error(f"Directorio no existe: {directory_path}")
                return batch_result
            
            json_files = list(directory.glob(pattern))
            self.logger.info(f"Encontrados {len(json_files)} archivos para procesar")
            
            if not json_files:
                self.logger.warning(f"No se encontraron archivos con patrón {pattern}")
                return batch_result
            
            # Procesar cada archivo
            for file_path in json_files:
                try:
                    result = self.process_json_file(str(file_path))
                    batch_result.archivos_procesados.append(result)
                    
                    # Log de progreso cada 10 archivos
                    if len(batch_result.archivos_procesados) % 10 == 0:
                        self.logger.info(f"Procesados {len(batch_result.archivos_procesados)}/{len(json_files)} archivos")
                
                except Exception as e:
                    error_result = ProcessingResult(
                        archivo=file_path.name,
                        total_registros=0,
                        registros_validos=0,
                        registros_invalidos=1,
                        registros_insertados=0,
                        registros_actualizados=0,
                        errores=[f"Error crítico: {str(e)}"]
                    )
                    batch_result.archivos_procesados.append(error_result)
                    self.logger.error(f"Error crítico procesando {file_path.name}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Error en procesamiento en lote: {str(e)}")
        
        finally:
            batch_result.fin_procesamiento = datetime.now()
            self._log_batch_summary(batch_result)
        
        return batch_result

    def _log_batch_summary(self, batch_result: BatchProcessingResult) -> None:
        """Registra un resumen del procesamiento en lote."""
        self.logger.info("=== RESUMEN DE PROCESAMIENTO ===")
        self.logger.info(f"Archivos procesados: {batch_result.total_archivos}")
        self.logger.info(f"Registros totales: {batch_result.total_registros}")
        self.logger.info(f"Registros insertados: {batch_result.total_insertados}")
        self.logger.info(f"Registros actualizados: {batch_result.total_actualizados}")
        self.logger.info(f"Tasa de éxito: {batch_result.tasa_exito_global:.2f}%")
        
        if batch_result.inicio_procesamiento and batch_result.fin_procesamiento:
            duration = batch_result.fin_procesamiento - batch_result.inicio_procesamiento
            self.logger.info(f"Tiempo total: {duration.total_seconds():.2f} segundos")

    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del procesamiento.

        Returns:
            Dict con estadísticas de procesamiento.
        """
        return {
            **self.stats,
            'success_rate': (
                (self.stats['records_inserted'] + self.stats['records_updated']) / 
                max(self.stats['records_processed'], 1) * 100
            ),
            'database_stats': self.db_manager.get_table_stats()
        }

    def validate_directory(self, directory_path: str, pattern: str = "pqr_*.json") -> Dict[str, Any]:
        """
        Valida archivos JSON en un directorio sin procesarlos.

        Args:
            directory_path: Ruta al directorio.
            pattern: Patrón de archivos.

        Returns:
            Dict con resultados de validación.
        """
        from .validators import validate_json_files
        return validate_json_files(directory_path, pattern)

    def process_new_files(self, directory_path: str, pattern: str = "pqr_*.json") -> BatchProcessingResult:
        """
        Procesa solo archivos nuevos (no procesados anteriormente).

        Args:
            directory_path: Ruta al directorio.
            pattern: Patrón de archivos.

        Returns:
            BatchProcessingResult: Resultado del procesamiento.
        """
        batch_result = BatchProcessingResult()
        
        try:
            directory = Path(directory_path)
            if not directory.exists():
                return batch_result
            
            json_files = list(directory.glob(pattern))
            processed_files = self._get_processed_files()
            
            new_files = [f for f in json_files if f.name not in processed_files]
            
            self.logger.info(f"Encontrados {len(new_files)} archivos nuevos de {len(json_files)} totales")
            
            for file_path in new_files:
                result = self.process_json_file(str(file_path))
                batch_result.archivos_procesados.append(result)
        
        except Exception as e:
            self.logger.error(f"Error procesando archivos nuevos: {str(e)}")
        
        finally:
            batch_result.fin_procesamiento = datetime.now()
        
        return batch_result

    def _get_processed_files(self) -> set:
        """
        Obtiene la lista de archivos ya procesados desde la base de datos.

        Returns:
            Set con nombres de archivos procesados.
        """
        try:
            if not self.db_manager.test_connection():
                return set()
            
            query = "SELECT DISTINCT archivo_origen FROM afinia_pqr WHERE archivo_origen IS NOT NULL"
            results = self.db_manager.execute_query(query)
            
            return {row[0] for row in results if row[0]}
        
        except Exception as e:
            self.logger.error(f"Error obteniendo archivos procesados: {str(e)}")
            return set()

    def remove_duplicates(self) -> Dict[str, Any]:
        """
        Elimina registros duplicados basados en hash_registro.

        Returns:
            Dict con estadísticas de eliminación.
        """
        try:
            if not self.db_manager.test_connection():
                return {'error': 'No connection to database'}
            
            # Encontrar duplicados
            query = """
            SELECT hash_registro, COUNT(*) as count, MIN(id) as keep_id
            FROM afinia_pqr 
            WHERE hash_registro IS NOT NULL 
            GROUP BY hash_registro 
            HAVING COUNT(*) > 1
            """
            
            duplicates = self.db_manager.execute_query(query)
            removed_count = 0
            
            # Eliminar duplicados manteniendo el registro más antiguo
            for hash_registro, count, keep_id in duplicates:
                delete_query = """
                DELETE FROM afinia_pqr 
                WHERE hash_registro = %s AND id != %s
                """
                self.db_manager.execute_query(delete_query, (hash_registro, keep_id))
                removed_count += count - 1
            
            return {
                'duplicates_found': len(duplicates),
                'records_removed': removed_count
            }
        
        except Exception as e:
            return {'error': f'Error removing duplicates: {str(e)}'}

    def close(self) -> None:
        """Cierra el procesador y libera recursos."""
        try:
            self.db_manager.close()
            self.logger.info("Procesador cerrado correctamente")
        except Exception as e:
            self.logger.error(f"Error cerrando procesador: {str(e)}")


def process_afinia_data(directory_path: str, pattern: str = "pqr_*.json") -> BatchProcessingResult:
    """
    Función de conveniencia para procesar datos de Afinia.

    Args:
        directory_path: Ruta al directorio con archivos JSON.
        pattern: Patrón de archivos a procesar.

    Returns:
        BatchProcessingResult: Resultado del procesamiento.
    """
    processor = AfiniaDataProcessor()
    try:
        return processor.process_directory(directory_path, pattern)
    finally:
        processor.close()


def validate_afinia_data(directory_path: str, pattern: str = "pqr_*.json") -> Dict[str, Any]:
    """
    Función de conveniencia para validar datos de Afinia.

    Args:
        directory_path: Ruta al directorio con archivos JSON.
        pattern: Patrón de archivos a validar.

    Returns:
        Dict con resultados de validación.
    """
    processor = AfiniaDataProcessor()
    try:
        return processor.validate_directory(directory_path, pattern)
    finally:
        processor.close()
