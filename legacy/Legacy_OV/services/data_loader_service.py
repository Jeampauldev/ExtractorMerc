#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de Carga Masiva de Datos - ExtractorOV
===============================================

Este servicio maneja la carga masiva de archivos JSON generados por los
extractores de Afinia y Aire hacia las tablas correspondientes en RDS.

Características:
- Procesamiento por lotes de múltiples archivos
- Detección automática del tipo de servicio (Afinia/Aire)
- Control de duplicados inteligente
- Estadísticas detalladas de procesamiento
- Reintentos automáticos en caso de errores
- Logging detallado con métricas
"""

import logging
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Importar servicio de base de datos
from .database_service import create_database_service, DataLoadResult


@dataclass
class ProcessingStats:
    """Estadísticas de procesamiento masivo"""
    total_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    total_records: int = 0
    inserted_records: int = 0
    skipped_records: int = 0
    processing_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    file_details: Dict[str, Dict] = field(default_factory=dict)


@dataclass
class FileProcessingResult:
    """Resultado del procesamiento de un archivo"""
    file_path: str
    success: bool
    service_type: str = ""
    data_result: Optional[DataLoadResult] = None
    error_message: str = ""
    processing_time: float = 0.0


class DataLoaderService:
    """
    Servicio para carga masiva de datos desde archivos JSON
    
    Procesa archivos JSON generados por los extractores y los carga
    a las tablas correspondientes en RDS.
    """
    
    def __init__(self, db_config: Optional[Dict] = None, max_workers: int = 4):
        """
        Inicializa el servicio de carga de datos
        
        Args:
            db_config: Configuración de base de datos
            max_workers: Número máximo de workers para procesamiento paralelo
        """
        self.db_service = create_database_service(db_config)
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
        self._processing_lock = threading.Lock()
        
        self.logger.info(f"DataLoaderService inicializado con {max_workers} workers")
    
    def detect_service_type(self, file_path: str) -> Optional[str]:
        """
        Detecta automáticamente el tipo de servicio basado en la ruta del archivo
        
        Args:
            file_path: Ruta del archivo JSON
            
        Returns:
            str: 'afinia' o 'aire', None si no se puede determinar
        """
        path_lower = file_path.lower()
        
        if 'afinia' in path_lower:
            return 'afinia'
        elif 'aire' in path_lower:
            return 'aire'
        else:
            # Intentar detectar por contenido del archivo
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    sample = f.read(1000)  # Leer muestra pequeña
                    sample_lower = sample.lower()
                    
                    if 'afinia' in sample_lower:
                        return 'afinia'
                    elif 'aire' in sample_lower:
                        return 'aire'
            except Exception as e:
                self.logger.warning(f"No se pudo detectar tipo de servicio para {file_path}: {e}")
        
        return None
    
    def validate_json_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Valida que el archivo JSON sea válido y contenga datos
        
        Args:
            file_path: Ruta del archivo JSON
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_error)
        """
        try:
            path = Path(file_path)
            
            # Verificar que el archivo existe
            if not path.exists():
                return False, "Archivo no encontrado"
            
            # Verificar que no esté vacío
            if path.stat().st_size == 0:
                return False, "Archivo vacío"
            
            # Verificar que sea JSON válido
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verificar que contenga datos
            if isinstance(data, list) and len(data) == 0:
                return False, "Archivo JSON vacío (array sin elementos)"
            
            if isinstance(data, dict) and len(data) == 0:
                return False, "Archivo JSON vacío (objeto sin campos)"
            
            return True, ""
            
        except json.JSONDecodeError as e:
            return False, f"JSON inválido: {e}"
        except Exception as e:
            return False, f"Error validando archivo: {e}"
    
    def process_single_file(self, file_path: str, service_type: Optional[str] = None,
                          check_duplicates: bool = True) -> FileProcessingResult:
        """
        Procesa un único archivo JSON
        
        Args:
            file_path: Ruta del archivo a procesar
            service_type: Tipo de servicio ('afinia' o 'aire'), se autodetecta si es None
            check_duplicates: Si verificar duplicados
            
        Returns:
            FileProcessingResult: Resultado del procesamiento
        """
        start_time = time.time()
        result = FileProcessingResult(file_path=file_path, success=False)
        
        try:
            self.logger.info(f"Procesando archivo: {file_path}")
            
            # Validar archivo
            is_valid, error_msg = self.validate_json_file(file_path)
            if not is_valid:
                result.error_message = f"Validación fallida: {error_msg}"
                return result
            
            # Detectar tipo de servicio si no se proporciona
            if service_type is None:
                service_type = self.detect_service_type(file_path)
                if service_type is None:
                    result.error_message = "No se pudo detectar el tipo de servicio"
                    return result
            
            result.service_type = service_type
            
            # Cargar datos usando el servicio de base de datos
            data_result = self.db_service.load_data_from_json(
                service_type, file_path, check_duplicates
            )
            
            result.data_result = data_result
            result.success = data_result.success
            
            if not data_result.success:
                result.error_message = "; ".join(data_result.errors)
            else:
                self.logger.info(
                    f"Archivo procesado exitosamente: {file_path} - "
                    f"{data_result.records_inserted} registros insertados"
                )
            
        except Exception as e:
            result.error_message = f"Error inesperado: {e}"
            self.logger.error(f"Error procesando {file_path}: {e}")
        
        finally:
            result.processing_time = time.time() - start_time
        
        return result
    
    def find_json_files(self, directory: str, service_type: Optional[str] = None,
                       recursive: bool = True) -> List[str]:
        """
        Busca archivos JSON en un directorio
        
        Args:
            directory: Directorio donde buscar
            service_type: Filtrar por tipo de servicio ('afinia' o 'aire')
            recursive: Si buscar recursivamente en subdirectorios
            
        Returns:
            List[str]: Lista de rutas de archivos JSON encontrados
        """
        json_files = []
        search_path = Path(directory)
        
        if not search_path.exists():
            self.logger.warning(f"Directorio no encontrado: {directory}")
            return json_files
        
        try:
            # Buscar archivos JSON
            pattern = "**/*.json" if recursive else "*.json"
            
            for json_file in search_path.glob(pattern):
                if json_file.is_file():
                    # Filtrar por tipo de servicio si se especifica
                    if service_type:
                        detected_type = self.detect_service_type(str(json_file))
                        if detected_type != service_type:
                            continue
                    
                    json_files.append(str(json_file))
            
            self.logger.info(f"Encontrados {len(json_files)} archivos JSON en {directory}")
            
        except Exception as e:
            self.logger.error(f"Error buscando archivos JSON en {directory}: {e}")
        
        return json_files
    
    def process_batch(self, file_paths: List[str], service_type: Optional[str] = None,
                     check_duplicates: bool = True, parallel: bool = True) -> ProcessingStats:
        """
        Procesa un lote de archivos JSON
        
        Args:
            file_paths: Lista de rutas de archivos a procesar
            service_type: Tipo de servicio específico (opcional)
            check_duplicates: Si verificar duplicados
            parallel: Si procesar en paralelo
            
        Returns:
            ProcessingStats: Estadísticas del procesamiento
        """
        start_time = time.time()
        stats = ProcessingStats()
        stats.total_files = len(file_paths)
        
        self.logger.info(f"Iniciando procesamiento de {len(file_paths)} archivos")
        
        if parallel and len(file_paths) > 1:
            # Procesamiento paralelo
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Enviar tareas
                future_to_file = {
                    executor.submit(
                        self.process_single_file, file_path, service_type, check_duplicates
                    ): file_path for file_path in file_paths
                }
                
                # Recoger resultados
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        self._update_stats_with_result(stats, result)
                    except Exception as e:
                        self.logger.error(f"Error procesando {file_path}: {e}")
                        stats.failed_files += 1
                        stats.errors.append(f"{file_path}: {e}")
        else:
            # Procesamiento secuencial
            for file_path in file_paths:
                result = self.process_single_file(file_path, service_type, check_duplicates)
                self._update_stats_with_result(stats, result)
        
        stats.processing_time_seconds = time.time() - start_time
        
        self.logger.info(
            f"Procesamiento completado: {stats.processed_files}/{stats.total_files} archivos exitosos "
            f"en {stats.processing_time_seconds:.2f}s"
        )
        
        return stats
    
    def _update_stats_with_result(self, stats: ProcessingStats, result: FileProcessingResult):
        """Actualiza las estadísticas con el resultado de un archivo"""
        with self._processing_lock:
            if result.success:
                stats.processed_files += 1
                if result.data_result:
                    stats.total_records += result.data_result.records_processed
                    stats.inserted_records += result.data_result.records_inserted
                    stats.skipped_records += result.data_result.records_skipped
            else:
                stats.failed_files += 1
                if result.error_message:
                    stats.errors.append(f"{result.file_path}: {result.error_message}")
            
            # Guardar detalles del archivo
            stats.file_details[result.file_path] = {
                'success': result.success,
                'service_type': result.service_type,
                'processing_time': result.processing_time,
                'error': result.error_message if not result.success else None,
                'records_processed': result.data_result.records_processed if result.data_result else 0,
                'records_inserted': result.data_result.records_inserted if result.data_result else 0,
                'records_skipped': result.data_result.records_skipped if result.data_result else 0
            }
    
    def process_directory(self, directory: str, service_type: Optional[str] = None,
                         check_duplicates: bool = True, recursive: bool = True,
                         parallel: bool = True) -> ProcessingStats:
        """
        Procesa todos los archivos JSON en un directorio
        
        Args:
            directory: Directorio a procesar
            service_type: Tipo de servicio específico (opcional)
            check_duplicates: Si verificar duplicados
            recursive: Si buscar archivos recursivamente
            parallel: Si procesar en paralelo
            
        Returns:
            ProcessingStats: Estadísticas del procesamiento
        """
        self.logger.info(f"Procesando directorio: {directory}")
        
        # Encontrar archivos JSON
        json_files = self.find_json_files(directory, service_type, recursive)
        
        if not json_files:
            self.logger.warning(f"No se encontraron archivos JSON en {directory}")
            stats = ProcessingStats()
            stats.errors.append(f"No se encontraron archivos JSON en {directory}")
            return stats
        
        # Procesar archivos
        return self.process_batch(json_files, service_type, check_duplicates, parallel)
    
    def generate_processing_report(self, stats: ProcessingStats, 
                                 output_file: Optional[str] = None) -> str:
        """
        Genera un reporte detallado del procesamiento
        
        Args:
            stats: Estadísticas del procesamiento
            output_file: Archivo donde guardar el reporte (opcional)
            
        Returns:
            str: Reporte en formato texto
        """
        report = []
        report.append("=" * 80)
        report.append("REPORTE DE PROCESAMIENTO DE DATOS - ExtractorOV")
        report.append("=" * 80)
        report.append(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Resumen general
        report.append("PROCESADOS RESUMEN GENERAL")
        report.append("-" * 40)
        report.append(f"Total archivos:        {stats.total_files}")
        report.append(f"Procesados exitosos:   {stats.processed_files}")
        report.append(f"Archivos fallidos:     {stats.failed_files}")
        report.append(f"Archivos saltados:     {stats.skipped_files}")
        report.append(f"Tiempo total:          {stats.processing_time_seconds:.2f}s")
        report.append("")
        
        # Estadísticas de registros
        report.append(" ESTADÍSTICAS DE REGISTROS")
        report.append("-" * 40)
        report.append(f"Total registros procesados: {stats.total_records}")
        report.append(f"Registros insertados:       {stats.inserted_records}")
        report.append(f"Registros saltados:         {stats.skipped_records}")
        if stats.total_records > 0:
            success_rate = (stats.inserted_records / stats.total_records) * 100
            report.append(f"Tasa de éxito:              {success_rate:.1f}%")
        report.append("")
        
        # Errores
        if stats.errors:
            report.append("ERROR ERRORES ENCONTRADOS")
            report.append("-" * 40)
            for error in stats.errors[:10]:  # Mostrar máximo 10 errores
                report.append(f"• {error}")
            if len(stats.errors) > 10:
                report.append(f"... y {len(stats.errors) - 10} errores más")
            report.append("")
        
        # Detalles por archivo (muestra)
        if stats.file_details:
            report.append("ARCHIVOS DETALLES DE ARCHIVOS (MUESTRA)")
            report.append("-" * 40)
            successful_files = [f for f, d in stats.file_details.items() if d['success']]
            failed_files = [f for f, d in stats.file_details.items() if not d['success']]
            
            if successful_files:
                report.append("EXITOSO Archivos exitosos:")
                for file_path in successful_files[:5]:
                    details = stats.file_details[file_path]
                    report.append(
                        f"   {Path(file_path).name} - "
                        f"Tipo: {details['service_type']}, "
                        f"Insertados: {details['records_inserted']}, "
                        f"Tiempo: {details['processing_time']:.2f}s"
                    )
                if len(successful_files) > 5:
                    report.append(f"   ... y {len(successful_files) - 5} más")
                report.append("")
            
            if failed_files:
                report.append("ERROR Archivos con errores:")
                for file_path in failed_files[:5]:
                    details = stats.file_details[file_path]
                    report.append(f"   {Path(file_path).name} - Error: {details['error']}")
                if len(failed_files) > 5:
                    report.append(f"   ... y {len(failed_files) - 5} más")
                report.append("")
        
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Guardar en archivo si se especifica
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                self.logger.info(f"Reporte guardado en: {output_file}")
            except Exception as e:
                self.logger.error(f"Error guardando reporte en {output_file}: {e}")
        
        return report_text
    
    def validate_environment(self) -> Dict[str, Any]:
        """
        Valida que el entorno esté listo para procesar datos
        
        Returns:
            Dict[str, Any]: Estado de validación
        """
        return self.db_service.validate_environment()


# Funciones de utilidad para uso directo

def process_json_files(file_paths: List[str], service_type: Optional[str] = None,
                      check_duplicates: bool = True, parallel: bool = True,
                      db_config: Optional[Dict] = None) -> ProcessingStats:
    """
    Función de utilidad para procesar una lista de archivos JSON
    
    Args:
        file_paths: Lista de rutas de archivos
        service_type: Tipo de servicio específico
        check_duplicates: Si verificar duplicados
        parallel: Si procesar en paralelo
        db_config: Configuración de base de datos
        
    Returns:
        ProcessingStats: Estadísticas del procesamiento
    """
    loader_service = DataLoaderService(db_config)
    return loader_service.process_batch(file_paths, service_type, check_duplicates, parallel)


def process_data_directory(directory: str, service_type: Optional[str] = None,
                          check_duplicates: bool = True, recursive: bool = True,
                          parallel: bool = True, db_config: Optional[Dict] = None) -> ProcessingStats:
    """
    Función de utilidad para procesar un directorio completo
    
    Args:
        directory: Directorio a procesar
        service_type: Tipo de servicio específico
        check_duplicates: Si verificar duplicados
        recursive: Si buscar archivos recursivamente
        parallel: Si procesar en paralelo
        db_config: Configuración de base de datos
        
    Returns:
        ProcessingStats: Estadísticas del procesamiento
    """
    loader_service = DataLoaderService(db_config)
    return loader_service.process_directory(directory, service_type, check_duplicates, recursive, parallel)


if __name__ == "__main__":
    # CLI para el servicio
    import argparse
    
    parser = argparse.ArgumentParser(description='Servicio de Carga Masiva de Datos - ExtractorOV')
    parser.add_argument('--directory', '-d', help='Directorio a procesar')
    parser.add_argument('--files', '-f', nargs='+', help='Archivos específicos a procesar')
    parser.add_argument('--service-type', '-s', choices=['afinia', 'aire'], 
                       help='Tipo de servicio específico')
    parser.add_argument('--no-duplicates-check', action='store_true', 
                       help='No verificar duplicados')
    parser.add_argument('--no-recursive', action='store_true', 
                       help='No buscar archivos recursivamente')
    parser.add_argument('--sequential', action='store_true', 
                       help='Procesamiento secuencial (no paralelo)')
    parser.add_argument('--validate-env', action='store_true', 
                       help='Validar entorno antes de procesar')
    parser.add_argument('--report-file', '-r', 
                       help='Archivo donde guardar el reporte')
    parser.add_argument('--max-workers', type=int, default=4,
                       help='Número máximo de workers paralelos')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear servicio
    loader_service = DataLoaderService(max_workers=args.max_workers)
    
    # Validar entorno si se solicita
    if args.validate_env:
        print("VERIFICANDO Validando entorno...")
        validation = loader_service.validate_environment()
        print(f"Conexión RDS: {'EXITOSO' if validation['connection'] else 'ERROR'}")
        print(f"Esquema 'data': {'EXITOSO' if validation['schema'] else 'ERROR'}")
        for table, exists in validation['tables'].items():
            print(f"Tabla {table}: {'EXITOSO' if exists else 'ERROR'}")
        print()
        
        if not all([validation['connection'], validation['schema']] + 
                  list(validation['tables'].values())):
            print("ADVERTENCIA El entorno no está completamente configurado")
            exit(1)
    
    # Procesar archivos o directorio
    stats = None
    
    if args.files:
        print(f"DESCARGANDO Procesando {len(args.files)} archivos específicos...")
        stats = loader_service.process_batch(
            args.files,
            service_type=args.service_type,
            check_duplicates=not args.no_duplicates_check,
            parallel=not args.sequential
        )
    
    elif args.directory:
        print(f"ARCHIVOS Procesando directorio: {args.directory}")
        stats = loader_service.process_directory(
            args.directory,
            service_type=args.service_type,
            check_duplicates=not args.no_duplicates_check,
            recursive=not args.no_recursive,
            parallel=not args.sequential
        )
    
    else:
        print("ERROR Debe especificar --directory o --files")
        parser.print_help()
        exit(1)
    
    # Generar y mostrar reporte
    if stats:
        report = loader_service.generate_processing_report(stats, args.report_file)
        print("\n" + report)
        
        # Código de salida basado en el éxito
        if stats.failed_files > 0:
            exit(1)
    else:
        print("ERROR No se pudieron procesar los datos")
        exit(1)