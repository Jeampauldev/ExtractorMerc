#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de Carga Masiva a Base de Datos
========================================

Servicio robusto para carga masiva de datos consolidados de Afinia y Aire
a las tablas ov_afinia y ov_aire en el esquema data_general.

Incluye control de duplicados, validaciones, manejo de errores y rollback.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import hashlib

from sqlalchemy import text, exc as sa_exc
from sqlalchemy.orm import Session
from src.config.rds_config import RDSConnectionManager, get_rds_session

logger = logging.getLogger(__name__)

@dataclass
class LoadStats:
    """Estadísticas de carga masiva"""
    total_records: int = 0
    inserted_records: int = 0
    updated_records: int = 0
    skipped_duplicates: int = 0
    error_records: int = 0
    processing_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

@dataclass
class DuplicateCheckResult:
    """Resultado de verificación de duplicados"""
    is_duplicate: bool
    duplicate_type: str  # 'hash', 'numero_radicado', 'none'
    existing_id: Optional[int] = None
    needs_update: bool = False

class BulkDatabaseLoader:
    """
    Servicio para carga masiva de datos a base de datos RDS
    """
    
    def __init__(self, batch_size: int = 100):
        """
        Inicializar el servicio de carga
        
        Args:
            batch_size: Tamaño de lotes para carga masiva
        """
        self.batch_size = batch_size
        self.rds_manager = RDSConnectionManager()
        
        # Mapeo de campos JSON a BD (estructura real de los archivos JSON individuales)
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
            'canal_respuesta': 'canal_respuesta',
            'lectura': 'lectura',
            'documento_prueba': 'documento_prueba',
            'cuerpo_reclamacion': 'cuerpo_reclamacion',
            'finalizar': 'finalizar',
            'adjuntar_archivo': 'adjuntar_archivo',
            'numero_reclamo_sgc': 'numero_reclamo_sgc',
            'comentarios': 'comentarios'
        }
        
    def prepare_record_for_db(self, record: Dict, company: str) -> Dict:
        """
        Prepara un registro para inserción en BD
        
        Args:
            record: Registro del CSV consolidado
            company: 'afinia' o 'aire'
            
        Returns:
            Dict preparado para BD
        """
        db_record = {}
        
        # Mapear campos básicos desde JSON
        for json_field, db_field in self.field_mapping.items():
            if json_field in record:
                value = record[json_field]
                
                # Conversiones específicas
                if json_field == 'fecha':
                    # Convertir fecha string a timestamp
                    if isinstance(value, str) and value.strip():
                        try:
                            db_record[db_field] = datetime.strptime(value, "%Y/%m/%d %H:%M")
                        except ValueError:
                            # Intentar otros formatos
                            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
                                try:
                                    db_record[db_field] = datetime.strptime(value, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                db_record[db_field] = None
                    else:
                        db_record[db_field] = value if value else None
                        
                elif json_field in ['cuerpo_reclamacion', 'comentarios']:
                    # Campos de texto largo
                    db_record[db_field] = str(value).strip() if value else None
                        
                else:
                    # Campo directo - limpiar valores vacíos
                    if value in ['', 'nan', 'NaN', None]:
                        db_record[db_field] = None
                    else:
                        db_record[db_field] = str(value).strip() if isinstance(value, str) else value
        
        # Los campos de metadata no existen en la estructura actual
        # Se omiten: fecha_extraccion, procesado_flag, created_at, updated_at
        # Las tablas usan fecha_creacion y fecha_actualizacion automáticamente
        
        return db_record
    
    def _generate_record_hash(self, record: Dict) -> str:
        """
        Generar hash SHA-256 del registro basado en campos clave
        
        Args:
            record: Registro de datos
            
        Returns:
            Hash SHA-256 del registro
        """
        # Campos clave para el hash (ordenados para consistencia)
        key_fields = ['numero_radicado', 'fecha', 'tipo_pqr', 'nic', 'documento_identidad']
        
        # Extraer valores de campos clave
        hash_data = []
        for field in key_fields:
            value = record.get(field)
            if value is not None:
                if isinstance(value, datetime):
                    hash_data.append(value.isoformat())
                else:
                    hash_data.append(str(value))
            else:
                hash_data.append('')
        
        # Generar hash
        hash_string = '|'.join(hash_data)
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    def check_duplicate(self, session: Session, record: Dict, table_name: str) -> DuplicateCheckResult:
        """
        Verificar si un registro es duplicado
        
        Args:
            session: Sesión de BD
            record: Registro a verificar
            table_name: 'ov_afinia' o 'ov_aire'
            
        Returns:
            Resultado de verificación de duplicados
        """
        numero_radicado = record.get('numero_radicado')
        
        hash_registro = record.get('hash_registro')
        
        try:
            # Verificar por hash exacto (primera prioridad)
            if hash_registro:
                hash_query = text(f"""
                    SELECT id FROM data_general.{table_name} 
                    WHERE hash_registro = :hash_registro
                """)
                hash_result = session.execute(hash_query, {'hash_registro': hash_registro}).fetchone()
                
                if hash_result:
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        duplicate_type='hash',
                        existing_id=hash_result[0],
                        needs_update=False  # Hash idéntico = no cambios
                    )
            
            # Verificar por numero_radicado (segunda prioridad)
            if numero_radicado:
                radicado_query = text(f"""
                    SELECT id, hash_registro FROM data_general.{table_name} 
                    WHERE numero_radicado = :numero_radicado
                """)
                radicado_result = session.execute(radicado_query, {'numero_radicado': numero_radicado}).fetchone()
                
                if radicado_result:
                    existing_hash = radicado_result[1]
                    needs_update = existing_hash != hash_registro
                    
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        duplicate_type='numero_radicado',
                        existing_id=radicado_result[0],
                        needs_update=needs_update  # Actualizar solo si hash cambió
                    )
            
            return DuplicateCheckResult(
                is_duplicate=False,
                duplicate_type='none'
            )
            
        except Exception as e:
            logger.error(f"[2025-10-10_05:32:20][{table_name}][bulk_loader][check_duplicate][ERROR] - Error verificando duplicado: {e}")
            return DuplicateCheckResult(
                is_duplicate=False,
                duplicate_type='none'
            )
    
    def insert_record(self, session: Session, record: Dict, table_name: str) -> bool:
        """
        Insertar un registro en la tabla
        
        Args:
            session: Sesión de BD
            record: Registro a insertar
            table_name: 'ov_afinia' o 'ov_aire'
            
        Returns:
            True si la inserción fue exitosa
        """
        try:
            # Construir query de inserción
            fields = list(record.keys())
            placeholders = [f":{field}" for field in fields]
            
            insert_query = text(f"""
                INSERT INTO data_general.{table_name} ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
            """)
            
            session.execute(insert_query, record)
            return True
            
        except Exception as e:
            logger.error(f"[2025-10-10_05:32:20][{table_name}][bulk_loader][insert_record][ERROR] - Error insertando: {e}")
            return False
    
    def update_record(self, session: Session, record: Dict, existing_id: int, table_name: str) -> bool:
        """
        Actualizar un registro existente
        
        Args:
            session: Sesión de BD
            record: Registro con datos actualizados
            existing_id: ID del registro existente
            table_name: 'ov_afinia' o 'ov_aire'
            
        Returns:
            True si la actualización fue exitosa
        """
        try:
            # Agregar timestamp de actualización
            record['fecha_actualizacion'] = datetime.now()
            
            # Construir query de actualización
            set_clauses = [f"{field} = :{field}" for field in record.keys()]
            
            update_query = text(f"""
                UPDATE data_general.{table_name}
                SET {', '.join(set_clauses)}
                WHERE id = :existing_id
            """)
            
            record['existing_id'] = existing_id
            session.execute(update_query, record)
            return True
            
        except Exception as e:
            logger.error(f"[2025-10-10_05:32:20][{table_name}][bulk_loader][update_record][ERROR] - Error actualizando: {e}")
            return False
    
    def scan_processed_json_files(self, company: str) -> List[Path]:
        """
        Escanea archivos JSON individuales procesados
        
        Args:
            company: 'afinia' o 'aire'
            
        Returns:
            Lista de rutas de archivos JSON procesados
        """
        processed_path = Path(f"data/downloads/{company}/oficina_virtual/processed")
        
        if not processed_path.exists():
            logger.warning(f"[2025-10-10_05:32:20][{company}][bulk_loader][scan_processed_json_files][WARNING] - Directorio no encontrado: {processed_path}")
            return []
        
        # Buscar archivos _data_*.json
        json_files = list(processed_path.glob("*_data_*.json"))
        logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][scan_processed_json_files][INFO] - Encontrados {len(json_files)} archivos JSON procesados")
        
        return json_files
    
    def load_processed_json_to_database(self, company: str) -> LoadStats:
        """
        Cargar archivos JSON procesados individuales a base de datos
        
        Args:
            company: 'afinia' o 'aire'
            
        Returns:
            Estadísticas de carga
        """
        start_time = datetime.now()
        stats = LoadStats()
        table_name = f"ov_{company}"
        
        logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_processed_json_to_database][INFO] - Iniciando carga de archivos JSON procesados")
        
        # Escanear archivos JSON procesados
        json_files = self.scan_processed_json_files(company)
        stats.total_records = len(json_files)
        
        if not json_files:
            logger.warning(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_processed_json_to_database][WARNING] - No se encontraron archivos JSON procesados")
            return stats
        
        session = self.rds_manager.get_session()
        
        try:
            for json_file in json_files:
                try:
                    # Cargar archivo JSON
                    with open(json_file, 'r', encoding='utf-8') as f:
                        pqr_data = json.load(f)
                    
                    # Preparar registro para BD
                    db_record = self.prepare_record_for_db(pqr_data, company)
                    
                    # Generar hash del registro
                    hash_registro = self._generate_record_hash(db_record)
                    db_record['hash_registro'] = hash_registro
                    
                    # Verificar duplicados
                    dup_result = self.check_duplicate(session, db_record, table_name)
                    
                    if dup_result.is_duplicate:
                        if dup_result.needs_update:
                            # Actualizar registro existente
                            if self.update_record(session, db_record, dup_result.existing_id, table_name):
                                stats.updated_records += 1
                                logger.debug(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_processed_json_to_database][DEBUG] - Actualizado: {db_record.get('numero_radicado')}")
                            else:
                                stats.error_records += 1
                        else:
                            # Registro duplicado exacto
                            stats.skipped_duplicates += 1
                            logger.debug(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_processed_json_to_database][DEBUG] - Duplicado: {db_record.get('numero_radicado')}")
                    else:
                        # Insertar nuevo registro
                        if self.insert_record(session, db_record, table_name):
                            stats.inserted_records += 1
                            logger.debug(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_processed_json_to_database][DEBUG] - Insertado: {db_record.get('numero_radicado')}")
                        else:
                            stats.error_records += 1
                    
                    # Commit cada cierto número de registros
                    if (stats.inserted_records + stats.updated_records) % self.batch_size == 0:
                        session.commit()
                        
                except Exception as e:
                    stats.error_records += 1
                    error_msg = f"Error procesando {json_file.name}: {e}"
                    stats.errors.append(error_msg)
                    logger.error(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_processed_json_to_database][ERROR] - {error_msg}")
            
            # Commit final
            session.commit()
            
        except Exception as e:
            session.rollback()
            error_msg = f"Error en transacción: {e}"
            stats.errors.append(error_msg)
            logger.error(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_processed_json_to_database][ERROR] - {error_msg}")
        finally:
            session.close()
        
        # Calcular tiempo de procesamiento
        stats.processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_processed_json_to_database][INFO] - Carga completada: {stats.inserted_records} insertados, {stats.updated_records} actualizados, {stats.skipped_duplicates} duplicados")
        
        return stats
        
    def load_csv_to_database(self, csv_file_path: str, company: str) -> LoadStats:
        """
        Cargar archivo CSV consolidado a base de datos
        
        Args:
            csv_file_path: Ruta del archivo CSV consolidado
            company: 'afinia' o 'aire'
            
        Returns:
            Estadísticas de carga
        """
        start_time = datetime.now()
        stats = LoadStats()
        table_name = f"ov_{company}"
        
        logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][INFO] - Iniciando carga masiva desde {csv_file_path}")
        
        if not Path(csv_file_path).exists():
            stats.errors.append(f"Archivo CSV no encontrado: {csv_file_path}")
            return stats
        
        try:
            # Leer CSV
            df = pd.read_csv(csv_file_path, encoding='utf-8')
            stats.total_records = len(df)
            
            if stats.total_records == 0:
                logger.warning(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][WARNING] - CSV vacío")
                return stats
            
            logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][INFO] - Cargando {stats.total_records} registros")
            
            # Procesar en lotes
            session = self.rds_manager.get_session()
            
            try:
                for i in range(0, len(df), self.batch_size):
                    batch = df.iloc[i:i+self.batch_size]
                    batch_start = i + 1
                    batch_end = min(i + self.batch_size, len(df))
                    
                    logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][INFO] - Procesando lote {batch_start}-{batch_end}")
                    
                    # Procesar cada registro del lote
                    for _, row in batch.iterrows():
                        try:
                            # Preparar registro
                            record_dict = row.to_dict()
                            db_record = self.prepare_record_for_db(record_dict, company)
                            
                            # Verificar duplicados
                            dup_result = self.check_duplicate(session, db_record, table_name)
                            
                            if dup_result.is_duplicate:
                                if dup_result.needs_update:
                                    # Actualizar registro existente
                                    if self.update_record(session, db_record, dup_result.existing_id, table_name):
                                        stats.updated_records += 1
                                        logger.debug(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][DEBUG] - Actualizado: {db_record.get('numero_radicado')}")
                                    else:
                                        stats.error_records += 1
                                else:
                                    # Registro duplicado exacto
                                    stats.skipped_duplicates += 1
                                    logger.debug(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][DEBUG] - Duplicado: {db_record.get('numero_radicado')}")
                            else:
                                # Insertar nuevo registro
                                if self.insert_record(session, db_record, table_name):
                                    stats.inserted_records += 1
                                    logger.debug(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][DEBUG] - Insertado: {db_record.get('numero_radicado')}")
                                else:
                                    stats.error_records += 1
                                    
                        except Exception as e:
                            stats.error_records += 1
                            error_msg = f"Error procesando registro {row.get('numero_radicado', 'desconocido')}: {e}"
                            stats.errors.append(error_msg)
                            logger.error(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][ERROR] - {error_msg}")
                    
                    # Commit del lote
                    session.commit()
                    logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][INFO] - Lote {batch_start}-{batch_end} completado")
                
            except Exception as e:
                session.rollback()
                error_msg = f"Error en transacción: {e}"
                stats.errors.append(error_msg)
                logger.error(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][ERROR] - {error_msg}")
            finally:
                session.close()
                
        except Exception as e:
            error_msg = f"Error leyendo CSV: {e}"
            stats.errors.append(error_msg)
            logger.error(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][ERROR] - {error_msg}")
        
        # Calcular tiempo de procesamiento
        stats.processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_csv_to_database][INFO] - Carga completada: {stats.inserted_records} insertados, {stats.updated_records} actualizados, {stats.skipped_duplicates} duplicados")
        
        return stats
    
    def load_multiple_csv_files(self, csv_files: Dict[str, str]) -> Dict[str, LoadStats]:
        """
        Cargar múltiples archivos CSV
        
        Args:
            csv_files: Dict con {'company': 'csv_path'}
            
        Returns:
            Dict con estadísticas por empresa
        """
        results = {}
        
        for company, csv_path in csv_files.items():
            if company in ['afinia', 'aire']:
                logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_multiple_csv_files][INFO] - Procesando {company}")
                results[company] = self.load_csv_to_database(csv_path, company)
            else:
                logger.warning(f"[2025-10-10_05:32:20][system][bulk_loader][load_multiple_csv_files][WARNING] - Empresa no soportada: {company}")
        
        return results
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas actuales de la base de datos
        
        Returns:
            Dict con conteos por tabla
        """
        stats = {
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        
        session = self.rds_manager.get_session()
        
        try:
            for table_name in ['ov_afinia', 'ov_aire']:
                count_query = text(f"SELECT COUNT(*) FROM data_general.{table_name}")
                count_result = session.execute(count_query).scalar()
                
                latest_query = text(f"""
                    SELECT MAX(fecha_creacion) as latest_insert,
                           MAX(fecha_actualizacion) as latest_update
                    FROM data_general.{table_name}
                """)
                latest_result = session.execute(latest_query).fetchone()
                
                stats['tables'][table_name] = {
                    'total_records': count_result,
                    'latest_insert': latest_result[0].isoformat() if latest_result[0] else None,
                    'latest_update': latest_result[1].isoformat() if latest_result[1] else None
                }
                
        except Exception as e:
            logger.error(f"[2025-10-10_05:32:20][system][bulk_loader][get_database_stats][ERROR] - Error obteniendo estadísticas: {e}")
            stats['error'] = str(e)
        finally:
            session.close()
        
        return stats
    
    def save_load_report(self, stats: LoadStats, company: str, csv_path: str) -> str:
        """
        Guardar reporte de carga
        
        Args:
            stats: Estadísticas de carga
            company: Empresa procesada
            csv_path: Ruta del CSV procesado
            
        Returns:
            Ruta del archivo de reporte
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path("data/processed") / f"{company}_load_report_{timestamp}.json"
        
        report_data = {
            'company': company,
            'csv_file': str(csv_path),
            'timestamp': datetime.now().isoformat(),
            'statistics': asdict(stats),
            'database_stats': self.get_database_stats()
        }
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][save_load_report][INFO] - Reporte guardado: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"[2025-10-10_05:32:20][{company}][bulk_loader][save_load_report][ERROR] - Error guardando reporte: {e}")
            return ""


# Funciones de conveniencia

def load_consolidated_csv(company: str, csv_path: str, batch_size: int = 100) -> LoadStats:
    """
    Cargar CSV consolidado a base de datos
    
    Args:
        company: 'afinia' o 'aire'
        csv_path: Ruta del archivo CSV
        batch_size: Tamaño de lotes
        
    Returns:
        Estadísticas de carga
    """
    loader = BulkDatabaseLoader(batch_size=batch_size)
    return loader.load_csv_to_database(csv_path, company)


def load_processed_json_files() -> Dict[str, LoadStats]:
    """
    Cargar archivos JSON procesados de Afinia y Aire a base de datos
    
    Returns:
        Estadísticas de carga por empresa
    """
    loader = BulkDatabaseLoader()
    results = {}
    
    for company in ['afinia', 'aire']:
        logger.info(f"[2025-10-10_05:32:20][{company}][bulk_loader][load_processed_json_files][INFO] - Procesando archivos JSON de {company}")
        results[company] = loader.load_processed_json_to_database(company)
    
    return results


def load_latest_consolidated_files() -> Dict[str, LoadStats]:
    """
    Buscar y cargar los archivos CSV consolidados más recientes
    Solo procesa Afinia según solicitud del usuario
    
    Returns:
        Estadísticas de carga por empresa
    """
    processed_path = Path("data/processed")
    csv_files = {}
    
    # Buscar CSVs consolidados más recientes - Solo Afinia
    for company in ['afinia']:  # Solo procesar Afinia
        pattern = f"{company}_consolidated_*.csv"
        matching_files = list(processed_path.glob(pattern))
        
        if matching_files:
            # Ordenar por fecha de modificación (más reciente primero)
            latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
            csv_files[company] = str(latest_file)
    
    if csv_files:
        loader = BulkDatabaseLoader()
        return loader.load_multiple_csv_files(csv_files)
    else:
        logger.warning("[2025-10-10_05:32:20][system][bulk_loader][load_latest_consolidated_files][WARNING] - No se encontraron archivos CSV consolidados")
        return {}


if __name__ == "__main__":
    # Test del servicio de carga
    logger.info("[2025-10-10_05:32:20][system][bulk_loader][main][INFO] - Iniciando test de carga masiva")
    
    # Cargar archivos más recientes
    results = load_latest_consolidated_files()
    
    print("=" * 70)
    print("RESULTADO DE CARGA MASIVA A BASE DE DATOS")
    print("=" * 70)
    
    if results:
        total_inserted = 0
        total_updated = 0
        total_duplicates = 0
        total_errors = 0
        
        for company, stats in results.items():
            print(f"\n{company.upper()}:")
            print(f"  - Total registros: {stats.total_records}")
            print(f"  - Insertados: {stats.inserted_records}")
            print(f"  - Actualizados: {stats.updated_records}")
            print(f"  - Duplicados: {stats.skipped_duplicates}")
            print(f"  - Errores: {stats.error_records}")
            print(f"  - Tiempo: {stats.processing_time:.2f}s")
            
            total_inserted += stats.inserted_records
            total_updated += stats.updated_records
            total_duplicates += stats.skipped_duplicates
            total_errors += stats.error_records
            
            if stats.errors:
                print(f"  - Errores encontrados: {len(stats.errors)}")
                for error in stats.errors[:3]:  # Mostrar solo los primeros 3
                    print(f"    * {error}")
        
        print(f"\nRESUMEN TOTAL:")
        print(f"  - Total insertados: {total_inserted}")
        print(f"  - Total actualizados: {total_updated}")
        print(f"  - Total duplicados: {total_duplicates}")
        print(f"  - Total errores: {total_errors}")
        
        # Mostrar estadísticas de BD
        loader = BulkDatabaseLoader()
        db_stats = loader.get_database_stats()
        
        print(f"\nESTADÍSTICAS DE BASE DE DATOS:")
        for table, info in db_stats.get('tables', {}).items():
            print(f"  - {table}: {info['total_records']} registros")
    else:
        print("No se encontraron archivos CSV consolidados para cargar")
    
    print("\n" + "=" * 70)