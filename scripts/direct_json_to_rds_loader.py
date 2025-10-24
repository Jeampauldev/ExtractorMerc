#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cargador Directo JSON → RDS con Deduplicación
=============================================

Script para cargar datos JSON de Afinia directamente a RDS sin almacenamiento
local intermedio, implementando deduplicación por numero_reclamo_sgc.

Características:
- Carga directa desde JSON descargado a RDS
- Deduplicación por numero_reclamo_sgc (numero_radicado)
- Validación de datos antes de inserción
- Control de transacciones con rollback
- Logging detallado y métricas
- Carga simultánea a S3 de archivos adjuntos

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import sys
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy import text

# Agregar src al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from config.rds_config import RDSConnectionManager
from services.s3_uploader_service import S3UploaderService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/direct_loader_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingStats:
    """Estadísticas de procesamiento"""
    total_records: int = 0
    processed_records: int = 0
    duplicated_records: int = 0
    failed_records: int = 0
    s3_uploads: int = 0
    s3_failures: int = 0
    processing_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class DirectJSONToRDSLoader:
    """Cargador directo de JSON a RDS con deduplicación"""
    
    def __init__(self):
        """Inicializar el cargador"""
        self.rds_manager = RDSConnectionManager()
        self.s3_uploader = S3UploaderService()
        
        # Cache de SGCs existentes para deduplicación
        self.existing_sgcs = set()
        
        # Mapeo de campos JSON a campos RDS
        self.field_mapping = {
            'numero_radicado': 'numero_radicado',
            'fecha': 'fecha',
            'estado_solicitud': 'estado_solicitud',
            'tipo_pqr': 'tipo_pqr',
            'nic': 'nic',
            'nombres_apellidos': 'nombres_apellidos',
            'telefono': 'telefono',
            'celular': 'celular',
            'correo_electronico': 'correo_electronico',
            'documento_identidad': 'documento_identidad',
            'canal_respuesta': 'canal_respuesta'
        }
    
    def load_existing_sgcs(self, service_type: str = 'afinia') -> None:
        """Cargar SGCs existentes en RDS para deduplicación"""
        logger.info(f"Cargando SGCs existentes para {service_type}...")
        
        table_name = f'ov_{service_type}'
        
        try:
            with self.rds_manager.get_session() as session:
                query = text(f"SELECT numero_radicado FROM data_general.{table_name}")
                result = session.execute(query)
                
                self.existing_sgcs = {row[0] for row in result if row[0]}
                logger.info(f"Cargados {len(self.existing_sgcs)} SGCs existentes")
                
        except Exception as e:
            logger.error(f"Error cargando SGCs existentes: {e}")
            self.existing_sgcs = set()
    
    def generate_record_hash(self, record: Dict[str, Any]) -> str:
        """Generar hash único para el registro"""
        # Usar campos clave para generar hash
        key_fields = [
            record.get('numero_radicado', ''),
            record.get('fecha', ''),
            record.get('nic', ''),
            record.get('nombres_apellidos', '')
        ]
        
        hash_input = '|'.join(str(field) for field in key_fields)
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validar registro antes de inserción"""
        errors = []
        
        # Validaciones obligatorias
        if not record.get('numero_radicado'):
            errors.append("numero_radicado es obligatorio")
        
        if not record.get('fecha'):
            errors.append("fecha es obligatoria")
        
        # Validar formato de fecha
        if record.get('fecha'):
            try:
                # Intentar parsear la fecha
                if isinstance(record['fecha'], str):
                    datetime.strptime(record['fecha'], '%Y/%m/%d %H:%M')
            except ValueError:
                try:
                    datetime.strptime(record['fecha'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    errors.append("formato de fecha inválido")
        
        # Validar longitudes de campos
        field_limits = {
            'numero_radicado': 50,
            'estado_solicitud': 100,
            'tipo_pqr': 200,
            'nic': 20,
            'nombres_apellidos': 200,
            'telefono': 20,
            'celular': 20,
            'correo_electronico': 100,
            'documento_identidad': 20,
            'canal_respuesta': 100
        }
        
        for field, limit in field_limits.items():
            value = record.get(field)
            if value and len(str(value)) > limit:
                errors.append(f"{field} excede {limit} caracteres")
        
        return len(errors) == 0, errors
    
    def prepare_record_for_insertion(self, record: Dict[str, Any], 
                                   source_file: str) -> Dict[str, Any]:
        """Preparar registro para inserción en RDS"""
        prepared = {}
        
        # Mapear campos
        for json_field, rds_field in self.field_mapping.items():
            value = record.get(json_field)
            if value is not None:
                prepared[rds_field] = value
        
        # Campos adicionales
        prepared['hash_registro'] = self.generate_record_hash(record)
        prepared['fecha_extraccion'] = datetime.now()
        prepared['archivo_origen'] = source_file
        prepared['procesado_flag'] = False
        prepared['created_at'] = datetime.now()
        prepared['updated_at'] = datetime.now()
        
        # Procesar archivos S3 si existen
        archivos_s3 = []
        if 'archivos_adjuntos' in record:
            for archivo in record['archivos_adjuntos']:
                if isinstance(archivo, str):
                    archivos_s3.append(archivo)
        
        prepared['archivos_s3_urls'] = json.dumps(archivos_s3) if archivos_s3 else None
        
        return prepared
    
    def insert_record_to_rds(self, session, record: Dict[str, Any], 
                           service_type: str = 'afinia') -> bool:
        """Insertar registro en RDS"""
        table_name = f'ov_{service_type}'
        
        try:
            # Construir query de inserción
            fields = list(record.keys())
            placeholders = [f":{field}" for field in fields]
            
            insert_query = text(f"""
                INSERT INTO data_general.{table_name} 
                ({', '.join(fields)}) 
                VALUES ({', '.join(placeholders)})
            """)
            
            session.execute(insert_query, record)
            return True
            
        except Exception as e:
            logger.error(f"Error insertando registro: {e}")
            return False
    
    def process_json_file(self, json_file_path: Path, 
                         service_type: str = 'afinia') -> ProcessingStats:
        """Procesar un archivo JSON completo"""
        logger.info(f"Procesando archivo: {json_file_path.name}")
        
        stats = ProcessingStats()
        start_time = datetime.now()
        
        try:
            # Cargar JSON
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer registros
            records = []
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # Buscar registros en diferentes estructuras
                if 'data' in data:
                    records = data['data']
                elif 'records' in data:
                    records = data['records']
                elif 'pqrs' in data:
                    records = data['pqrs']
                else:
                    # Asumir que el dict es un solo registro
                    records = [data]
            
            stats.total_records = len(records)
            logger.info(f"Total de registros en archivo: {stats.total_records}")
            
            # Procesar registros
            with self.rds_manager.get_session() as session:
                for i, record in enumerate(records, 1):
                    try:
                        # Validar registro
                        is_valid, validation_errors = self.validate_record(record)
                        if not is_valid:
                            stats.failed_records += 1
                            stats.errors.extend(validation_errors)
                            logger.warning(f"Registro {i} inválido: {validation_errors}")
                            continue
                        
                        # Verificar duplicado por SGC
                        sgc = record.get('numero_radicado')
                        if sgc in self.existing_sgcs:
                            stats.duplicated_records += 1
                            logger.debug(f"SGC duplicado omitido: {sgc}")
                            continue
                        
                        # Preparar para inserción
                        prepared_record = self.prepare_record_for_insertion(
                            record, json_file_path.name
                        )
                        
                        # Insertar en RDS
                        if self.insert_record_to_rds(session, prepared_record, service_type):
                            stats.processed_records += 1
                            self.existing_sgcs.add(sgc)  # Agregar al cache
                            
                            if stats.processed_records % 100 == 0:
                                logger.info(f"Procesados {stats.processed_records}/{stats.total_records} registros")
                        else:
                            stats.failed_records += 1
                    
                    except Exception as e:
                        stats.failed_records += 1
                        error_msg = f"Error procesando registro {i}: {e}"
                        stats.errors.append(error_msg)
                        logger.error(f"{error_msg}")
                
                # Commit de la transacción
                session.commit()
                logger.info("Transacción confirmada en RDS")
        
        except Exception as e:
            stats.errors.append(f"Error procesando archivo {json_file_path.name}: {e}")
            logger.error(f"Error crítico procesando archivo: {e}")
        
        # Calcular tiempo de procesamiento
        stats.processing_time = (datetime.now() - start_time).total_seconds()
        
        # Log de estadísticas
        logger.info(f"Estadísticas de procesamiento:")
        logger.info(f"   Total: {stats.total_records}")
        logger.info(f"   Procesados: {stats.processed_records}")
        logger.info(f"   Duplicados: {stats.duplicated_records}")
        logger.info(f"   Fallidos: {stats.failed_records}")
        logger.info(f"   Tiempo: {stats.processing_time:.2f}s")
        
        return stats
    
    def process_directory(self, directory_path: Path, 
                         service_type: str = 'afinia') -> ProcessingStats:
        """Procesar todos los archivos JSON en un directorio"""
        logger.info(f"Procesando directorio: {directory_path}")
        
        # Cargar SGCs existentes
        self.load_existing_sgcs(service_type)
        
        # Buscar archivos JSON con diferentes patrones
        json_files = []
        
        # Patrón estándar
        json_pattern = f"{service_type}_pqr_data_*.json"
        json_files.extend(list(directory_path.glob(json_pattern)))
        
        # Patrón alternativo para Air-e (archivos individuales)
        if service_type == 'aire':
            alternative_pattern = "*_data_*.json"
            alternative_files = list(directory_path.glob(alternative_pattern))
            # Filtrar solo archivos que no estén ya incluidos
            for file in alternative_files:
                if file not in json_files:
                    json_files.append(file)
        
        if not json_files:
            logger.warning(f"No se encontraron archivos JSON con patrones: {json_pattern} o *_data_*.json")
            return ProcessingStats()
        
        logger.info(f"Encontrados {len(json_files)} archivos JSON")
        
        # Estadísticas consolidadas
        total_stats = ProcessingStats()
        
        # Procesar cada archivo
        for json_file in sorted(json_files):
            file_stats = self.process_json_file(json_file, service_type)
            
            # Consolidar estadísticas
            total_stats.total_records += file_stats.total_records
            total_stats.processed_records += file_stats.processed_records
            total_stats.duplicated_records += file_stats.duplicated_records
            total_stats.failed_records += file_stats.failed_records
            total_stats.processing_time += file_stats.processing_time
            total_stats.errors.extend(file_stats.errors)
        
        return total_stats
    
    def generate_processing_report(self, stats: ProcessingStats, 
                                 output_file: Optional[Path] = None) -> Dict[str, Any]:
        """Generar reporte de procesamiento"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_records': stats.total_records,
                'processed_records': stats.processed_records,
                'duplicated_records': stats.duplicated_records,
                'failed_records': stats.failed_records,
                'success_rate': (stats.processed_records / stats.total_records * 100) if stats.total_records > 0 else 0,
                'processing_time_seconds': stats.processing_time
            },
            'errors': stats.errors[:50],  # Limitar errores en reporte
            'recommendations': []
        }
        
        # Generar recomendaciones
        if stats.duplicated_records > 0:
            report['recommendations'].append(
                f"Se encontraron {stats.duplicated_records} registros duplicados. "
                "Considere implementar limpieza de datos en origen."
            )
        
        if stats.failed_records > 0:
            report['recommendations'].append(
                f"Se fallaron {stats.failed_records} registros. "
                "Revise los errores para identificar patrones de validación."
            )
        
        if len(stats.errors) > 50:
            report['recommendations'].append(
                f"Se generaron {len(stats.errors)} errores. "
                "Solo se muestran los primeros 50 en este reporte."
            )
        
        # Guardar reporte si se especifica archivo
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Reporte guardado en: {output_file}")
        
        return report

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cargador Directo JSON → RDS')
    parser.add_argument('--directory', '-d', type=str, required=True,
                       help='Directorio con archivos JSON')
    parser.add_argument('--service-type', '-s', type=str, default='afinia',
                       choices=['afinia', 'aire'],
                       help='Tipo de servicio (afinia/aire)')
    parser.add_argument('--report-file', '-r', type=str,
                       help='Archivo para guardar reporte JSON')
    
    args = parser.parse_args()
    
    try:
        # Crear directorio de logs si no existe
        Path('logs').mkdir(exist_ok=True)
        
        # Validar directorio
        directory_path = Path(args.directory)
        if not directory_path.exists():
            logger.error(f"Directorio no existe: {directory_path}")
            sys.exit(1)
        
        # Crear cargador
        loader = DirectJSONToRDSLoader()
        
        # Procesar directorio
        logger.info("Iniciando carga directa JSON -> RDS")
        stats = loader.process_directory(directory_path, args.service_type)
        
        # Generar reporte
        report_file = None
        if args.report_file:
            report_file = Path(args.report_file)
        else:
            report_file = Path(f'logs/direct_load_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        report = loader.generate_processing_report(stats, report_file)
        
        # Mostrar resumen final
        logger.info("\n" + "=" * 60)
        logger.info("RESUMEN FINAL DE CARGA DIRECTA")
        logger.info("=" * 60)
        logger.info(f"Total registros: {stats.total_records}")
        logger.info(f"Procesados: {stats.processed_records}")
        logger.info(f"Duplicados omitidos: {stats.duplicated_records}")
        logger.info(f"Fallidos: {stats.failed_records}")
        logger.info(f"Tasa de éxito: {report['summary']['success_rate']:.1f}%")
        logger.info(f"Tiempo total: {stats.processing_time:.2f}s")
        
        # Código de salida
        exit_code = 0 if stats.failed_records == 0 else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()