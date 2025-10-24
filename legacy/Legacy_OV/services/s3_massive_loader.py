#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de Carga Masiva S3
===========================

Servicio para realizar carga masiva inicial de datos desde la base de datos
al bucket S3, y carga incremental de datos nuevos por horas.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config.rds_config import RDSConnectionManager
from src.services.unified_s3_service import UnifiedS3Service, S3PathStructure, S3UploadResult

logger = logging.getLogger(__name__)

@dataclass
class LoaderStats:
    """Estadísticas del loader"""
    total_records_bd: int = 0
    records_to_process: int = 0
    successful_uploads: int = 0
    pre_existing_files: int = 0
    failed_uploads: int = 0
    errors: List[str] = None
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class S3MassiveLoader:
    """
    Servicio para carga masiva y incremental de datos OV a S3
    """
    
    def __init__(self):
        self.rds_manager = RDSConnectionManager()
        self.s3_service = UnifiedS3Service(path_structure=S3PathStructure.LEGACY)
        
    def get_unprocessed_records(self, empresa: str, hours_back: int = None) -> List[Dict]:
        """
        Obtener registros no procesados desde la BD
        
        Args:
            empresa: 'afinia' o 'aire'
            hours_back: Horas hacia atrás para buscar (None = todos los registros)
            
        Returns:
            Lista de registros para procesar
        """
        session = self.rds_manager.get_session()
        
        try:
            # Query base para obtener registros no cargados a S3
            base_query = f"""
                SELECT 
                    ov.numero_radicado,
                    ov.fecha,
                    '{empresa}' as empresa,
                    ov.hash_registro,
                    ov.fecha_creacion,
                    COALESCE(ov.numero_reclamo_sgc, ov.numero_radicado) as numero_reclamo_sgc,
                    ov.fecha_actualizacion,
                    s3.id as s3_registro_id
                FROM data_general.ov_{empresa} ov
                LEFT JOIN data_general.registros_ov_s3 s3 
                    ON s3.numero_reclamo_sgc = ov.numero_radicado 
                    AND s3.empresa = :empresa
                WHERE s3.id IS NULL
            """
            
            # Agregar filtro temporal si se especifica
            if hours_back:
                base_query += f" AND ov.fecha_creacion >= :fecha_limite"
                
            base_query += " ORDER BY ov.fecha_creacion DESC"
            
            params = {'empresa': empresa}
            if hours_back:
                fecha_limite = datetime.now() - timedelta(hours=hours_back)
                params['fecha_limite'] = fecha_limite
                
            result = session.execute(text(base_query), params)
            records = result.fetchall()
            
            # Convertir a lista de diccionarios
            record_list = []
            for record in records:
                record_list.append({
                    'numero_radicado': record[0],
                    'fecha': record[1],
                    'empresa': record[2],
                    'hash_registro': record[3],
                    'fecha_creacion': record[4],
                    'numero_reclamo_sgc': record[5],
                    'fecha_actualizacion': record[6],
                    's3_registro_id': record[7]
                })
                
            logger.info(f"[s3_loader] Encontrados {len(record_list)} registros de {empresa} para procesar")
            return record_list
            
        except Exception as e:
            logger.error(f"[s3_loader] Error obteniendo registros no procesados: {e}")
            return []
        finally:
            session.close()
    
    def create_json_file_for_record(self, record: Dict) -> Optional[Path]:
        """
        Crear archivo JSON temporal para un registro de BD
        
        Args:
            record: Registro de la base de datos
            
        Returns:
            Path del archivo JSON creado o None si falla
        """
        try:
            empresa = record['empresa']
            numero_radicado = record['numero_radicado']
            
            # Crear directorio temporal
            temp_dir = Path(f"data/temp_s3_upload/{empresa}")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Nombre del archivo JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{numero_radicado}_data_{timestamp}.json"
            json_file = temp_dir / filename
            
            # Obtener datos completos del registro desde BD
            full_record = self.get_full_record_data(record)
            
            # Guardar como JSON
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(full_record, f, indent=2, ensure_ascii=False, default=str)
                
            logger.debug(f"[s3_loader] Archivo JSON creado: {json_file}")
            return json_file
            
        except Exception as e:
            logger.error(f"[s3_loader] Error creando archivo JSON para {record['numero_radicado']}: {e}")
            return None
    
    def get_full_record_data(self, record: Dict) -> Dict:
        """
        Obtener datos completos del registro desde BD
        
        Args:
            record: Registro básico
            
        Returns:
            Datos completos del registro
        """
        session = self.rds_manager.get_session()
        
        try:
            empresa = record['empresa']
            numero_radicado = record['numero_radicado']
            
            # Query para obtener todos los campos
            query = text(f"""
                SELECT *
                FROM data_general.ov_{empresa}
                WHERE numero_radicado = :numero_radicado
                LIMIT 1
            """)
            
            result = session.execute(query, {'numero_radicado': numero_radicado})
            full_record = result.fetchone()
            
            if full_record:
                # Convertir a diccionario
                columns = result.keys()
                record_dict = dict(zip(columns, full_record))
                
                # Agregar metadatos
                record_dict.update({
                    'metadata_carga': {
                        'origen': 'base_datos',
                        'fecha_carga_s3': datetime.now().isoformat(),
                        'tipo_carga': 'masiva_inicial',
                        'procesado_por': 'S3MassiveLoader'
                    }
                })
                
                return record_dict
            else:
                return record
                
        except Exception as e:
            logger.error(f"[s3_loader] Error obteniendo datos completos: {e}")
            return record
        finally:
            session.close()
    
    def process_record_to_s3(self, record: Dict) -> S3UploadResult:
        """
        Procesar un registro individual a S3
        
        Args:
            record: Registro de BD
            
        Returns:
            Resultado de la carga
        """
        try:
            # Crear archivo JSON temporal
            json_file = self.create_json_file_for_record(record)
            if not json_file:
                return S3UploadResult(
                    success=False,
                    error_message=f"Error creando archivo JSON para {record['numero_radicado']}"
                )
            
            # Cargar a S3
            result = self.s3_service.upload_file_with_registry(
                file_path=json_file,
                empresa=record['empresa'],
                numero_reclamo_sgc=record['numero_radicado']
            )
            
            # Limpiar archivo temporal
            try:
                json_file.unlink()
                json_file.parent.rmdir()  # Intentar eliminar directorio si está vacío
            except:
                pass  # No es crítico si no se puede limpiar
            
            # Marcar como sincronizado en BD si fue exitoso
            if result.success:
                self.mark_record_as_synchronized(record, result.registry_id)
                
            return result
            
        except Exception as e:
            error_msg = f"Error procesando registro {record['numero_radicado']}: {e}"
            logger.error(f"[s3_loader] {error_msg}")
            return S3UploadResult(
                success=False,
                error_message=error_msg
            )
    
    def mark_record_as_synchronized(self, record: Dict, s3_registry_id: int):
        """
        Marcar registro como sincronizado con S3
        
        Args:
            record: Registro de BD
            s3_registry_id: ID del registro en tabla S3
        """
        session = self.rds_manager.get_session()
        
        try:
            # Actualizar flag de sincronización en tabla S3
            update_query = text("""
                UPDATE data_general.registros_ov_s3 
                SET sincronizado_bd = TRUE,
                    fecha_actualizacion = NOW(),
                    observaciones = COALESCE(observaciones || '; ', '') || 'Sincronizado con BD'
                WHERE id = :s3_registry_id
            """)
            
            session.execute(update_query, {'s3_registry_id': s3_registry_id})
            session.commit()
            
            logger.debug(f"[s3_loader] Registro {record['numero_radicado']} marcado como sincronizado")
            
        except Exception as e:
            session.rollback()
            logger.error(f"[s3_loader] Error marcando como sincronizado: {e}")
        finally:
            session.close()
    
    def run_massive_load(self, empresa: str) -> LoaderStats:
        """
        Ejecutar carga masiva inicial para una empresa
        
        Args:
            empresa: 'afinia' o 'aire'
            
        Returns:
            Estadísticas de la carga
        """
        start_time = datetime.now()
        stats = LoaderStats()
        
        logger.info(f"[s3_loader] Iniciando carga masiva para {empresa}")
        
        try:
            # Obtener registros no procesados
            records = self.get_unprocessed_records(empresa)
            stats.records_to_process = len(records)
            
            if not records:
                logger.info(f"[s3_loader] No hay registros para procesar en {empresa}")
                return stats
            
            # Procesar cada registro
            for i, record in enumerate(records, 1):
                logger.info(f"[s3_loader] Procesando {i}/{len(records)}: {record['numero_radicado']}")
                
                result = self.process_record_to_s3(record)
                
                if result.success:
                    if result.upload_source == "bot":
                        stats.successful_uploads += 1
                    else:
                        stats.pre_existing_files += 1
                else:
                    stats.failed_uploads += 1
                    stats.errors.append(f"{record['numero_radicado']}: {result.error_message}")
            
            stats.processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"[s3_loader] Carga masiva completada para {empresa}: "
                       f"{stats.successful_uploads} subidos, {stats.pre_existing_files} existentes, "
                       f"{stats.failed_uploads} errores")
            
            return stats
            
        except Exception as e:
            logger.error(f"[s3_loader] Error en carga masiva: {e}")
            stats.errors.append(f"Error general: {str(e)}")
            return stats
    
    def run_incremental_load(self, empresa: str, hours_back: int = 1) -> LoaderStats:
        """
        Ejecutar carga incremental (solo nuevos registros)
        
        Args:
            empresa: 'afinia' o 'aire'
            hours_back: Horas hacia atrás para buscar nuevos registros
            
        Returns:
            Estadísticas de la carga
        """
        start_time = datetime.now()
        stats = LoaderStats()
        
        logger.info(f"[s3_loader] Iniciando carga incremental para {empresa} (últimas {hours_back} horas)")
        
        try:
            # Obtener solo registros nuevos de las últimas X horas
            records = self.get_unprocessed_records(empresa, hours_back=hours_back)
            stats.records_to_process = len(records)
            
            if not records:
                logger.info(f"[s3_loader] No hay registros nuevos en {empresa}")
                return stats
            
            # Procesar cada registro nuevo
            for record in records:
                logger.info(f"[s3_loader] Procesando nuevo registro: {record['numero_radicado']}")
                
                result = self.process_record_to_s3(record)
                
                if result.success:
                    if result.upload_source == "bot":
                        stats.successful_uploads += 1
                    else:
                        stats.pre_existing_files += 1
                else:
                    stats.failed_uploads += 1
                    stats.errors.append(f"{record['numero_radicado']}: {result.error_message}")
            
            stats.processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"[s3_loader] Carga incremental completada para {empresa}: "
                       f"{stats.successful_uploads} subidos, {stats.pre_existing_files} existentes, "
                       f"{stats.failed_uploads} errores")
            
            return stats
            
        except Exception as e:
            logger.error(f"[s3_loader] Error en carga incremental: {e}")
            stats.errors.append(f"Error general: {str(e)}")
            return stats


def run_massive_load_all_companies() -> Dict[str, LoaderStats]:
    """
    Ejecutar carga masiva para todas las empresas
    
    Returns:
        Estadísticas por empresa
    """
    loader = S3MassiveLoader()
    results = {}
    
    for empresa in ['afinia', 'aire']:
        logger.info(f"Procesando carga masiva para {empresa}")
        results[empresa] = loader.run_massive_load(empresa)
    
    return results


def run_incremental_load_all_companies(hours_back: int = 1) -> Dict[str, LoaderStats]:
    """
    Ejecutar carga incremental para todas las empresas
    
    Args:
        hours_back: Horas hacia atrás para buscar
        
    Returns:
        Estadísticas por empresa
    """
    loader = S3MassiveLoader()
    results = {}
    
    for empresa in ['afinia', 'aire']:
        logger.info(f"Procesando carga incremental para {empresa}")
        results[empresa] = loader.run_incremental_load(empresa, hours_back)
    
    return results


if __name__ == "__main__":
    # Test del servicio
    logger.info("Iniciando test de S3MassiveLoader")
    
    # Test incremental (últimas 24 horas)
    print("[EMOJI_REMOVIDO] Ejecutando carga incremental (últimas 24 horas)...")
    incremental_results = run_incremental_load_all_companies(hours_back=24)
    
    print("\n[DATOS] RESULTADOS CARGA INCREMENTAL")
    print("=" * 50)
    for empresa, stats in incremental_results.items():
        print(f"\n{empresa.upper()}:")
        print(f"  Registros a procesar: {stats.records_to_process}")
        print(f"  Subidos nuevos: {stats.successful_uploads}")
        print(f"  Pre-existentes: {stats.pre_existing_files}")
        print(f"  Errores: {stats.failed_uploads}")
        print(f"  Tiempo: {stats.processing_time:.2f}s")
        
        if stats.errors:
            print(f"  Errores encontrados:")
            for error in stats.errors[:3]:  # Mostrar solo los primeros 3
                print(f"    - {error}")