#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Limpieza Completa - RDS y S3
======================================

Script para limpiar completamente las tablas RDS y archivos S3 antes de
implementar el nuevo flujo de carga directa de Afinia.

Funcionalidades:
- Limpieza de tablas data_general.ov_afinia y data_general.ov_aire
- Limpieza de archivos S3 en bucket extractorov-data
- Verificación de limpieza
- Logging detallado de todas las operaciones

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import sys
import logging
import boto3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from sqlalchemy import text

# Agregar src al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from config.env_loader import get_s3_config, get_rds_config
from config.rds_config import RDSConnectionManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/clean_rds_s3_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RDSAndS3Cleaner:
    """Limpiador completo de RDS y S3"""
    
    def __init__(self):
        """Inicializar el limpiador"""
        self.rds_manager = RDSConnectionManager()
        self.s3_config = get_s3_config()
        self.s3_client = None
        
        # Prefijos S3 a limpiar
        self.s3_prefixes_to_clean = [
            'afinia/oficina_virtual/pdfs/',
            'afinia/oficina_virtual/data/',
            'afinia/oficina_virtual/screenshots/',
            'afinia/reports/',
            'afinia/logs/',
            'aire/oficina_virtual/pdfs/',
            'aire/oficina_virtual/data/',
            'aire/oficina_virtual/screenshots/',
            'aire/reports/',
            'aire/logs/',
            'general/reports/',
            'raw_data/'  # Datos consolidados anteriores
        ]
        
        self._initialize_s3_client()
    
    def _initialize_s3_client(self):
        """Inicializar cliente S3"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.s3_config['access_key_id'],
                aws_secret_access_key=self.s3_config['secret_access_key'],
                region_name=self.s3_config['region']
            )
            logger.info(f"[EMOJI_REMOVIDO] Cliente S3 inicializado para bucket: {self.s3_config['bucket_name']}")
        except Exception as e:
            logger.error(f"[EMOJI_REMOVIDO] Error inicializando cliente S3: {e}")
            raise
    
    def verify_rds_tables(self) -> Dict[str, Any]:
        """Verificar estado actual de las tablas RDS"""
        logger.info("[EMOJI_REMOVIDO] Verificando estado actual de tablas RDS...")
        
        result = {
            'schema_exists': False,
            'tables': {},
            'counts': {},
            'error': None
        }
        
        try:
            with self.rds_manager.get_session() as session:
                # Verificar esquema
                schema_query = text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = 'data_general'
                """)
                schema_result = session.execute(schema_query).fetchone()
                result['schema_exists'] = schema_result is not None
                
                if result['schema_exists']:
                    # Verificar tablas
                    table_query = text("""
                        SELECT table_name, table_rows
                        FROM information_schema.tables 
                        WHERE table_schema = 'data_general' 
                        AND table_name IN ('ov_afinia', 'ov_aire')
                    """)
                    table_results = session.execute(table_query).fetchall()
                    
                    for row in table_results:
                        table_name = row[0]
                        table_rows = row[1] or 0
                        result['tables'][table_name] = True
                        result['counts'][table_name] = table_rows
                    
                    # Verificar tablas que no existen
                    for table in ['ov_afinia', 'ov_aire']:
                        if table not in result['tables']:
                            result['tables'][table] = False
                            result['counts'][table] = 0
                
                logger.info(f"[EMOJI_REMOVIDO] Verificación RDS completada: {result}")
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"[EMOJI_REMOVIDO] Error verificando RDS: {e}")
        
        return result
    
    def clean_rds_tables(self) -> bool:
        """Limpiar tablas RDS"""
        logger.info("🧹 Iniciando limpieza de tablas RDS...")
        
        try:
            with self.rds_manager.get_session() as session:
                # Truncar tablas
                tables_to_clean = ['ov_afinia', 'ov_aire']
                
                for table in tables_to_clean:
                    try:
                        # Verificar si la tabla existe
                        check_query = text(f"""
                            SELECT COUNT(*) as count 
                            FROM information_schema.tables 
                            WHERE table_schema = 'data_general' 
                            AND table_name = '{table}'
                        """)
                        exists = session.execute(check_query).fetchone()[0] > 0
                        
                        if exists:
                            # Obtener conteo antes de limpiar
                            count_query = text(f"SELECT COUNT(*) FROM data_general.{table}")
                            before_count = session.execute(count_query).fetchone()[0]
                            
                            # Truncar tabla
                            truncate_query = text(f"TRUNCATE TABLE data_general.{table}")
                            session.execute(truncate_query)
                            
                            # Resetear AUTO_INCREMENT
                            reset_query = text(f"ALTER TABLE data_general.{table} AUTO_INCREMENT = 1")
                            session.execute(reset_query)
                            
                            # Verificar limpieza
                            after_count = session.execute(count_query).fetchone()[0]
                            
                            logger.info(f"[EMOJI_REMOVIDO] Tabla {table}: {before_count} → {after_count} registros")
                        else:
                            logger.warning(f"[ADVERTENCIA] Tabla {table} no existe")
                    
                    except Exception as e:
                        logger.error(f"[EMOJI_REMOVIDO] Error limpiando tabla {table}: {e}")
                        return False
                
                session.commit()
                logger.info("[EMOJI_REMOVIDO] Limpieza de tablas RDS completada")
                return True
                
        except Exception as e:
            logger.error(f"[EMOJI_REMOVIDO] Error en limpieza RDS: {e}")
            return False
    
    def verify_s3_bucket(self) -> Dict[str, Any]:
        """Verificar estado actual del bucket S3"""
        logger.info("[EMOJI_REMOVIDO] Verificando estado actual del bucket S3...")
        
        result = {
            'bucket_exists': False,
            'total_objects': 0,
            'prefixes': {},
            'error': None
        }
        
        try:
            bucket_name = self.s3_config['bucket_name']
            
            # Verificar si el bucket existe
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                result['bucket_exists'] = True
            except:
                result['bucket_exists'] = False
                return result
            
            # Contar objetos por prefijo
            for prefix in self.s3_prefixes_to_clean:
                try:
                    response = self.s3_client.list_objects_v2(
                        Bucket=bucket_name, 
                        Prefix=prefix
                    )
                    
                    count = len(response.get('Contents', []))
                    result['prefixes'][prefix] = count
                    result['total_objects'] += count
                    
                except Exception as e:
                    logger.warning(f"[ADVERTENCIA] Error verificando prefijo {prefix}: {e}")
                    result['prefixes'][prefix] = 0
            
            logger.info(f"[EMOJI_REMOVIDO] Verificación S3 completada: {result['total_objects']} objetos totales")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"[EMOJI_REMOVIDO] Error verificando S3: {e}")
        
        return result
    
    def clean_s3_bucket(self) -> bool:
        """Limpiar archivos del bucket S3"""
        logger.info("🧹 Iniciando limpieza del bucket S3...")
        
        try:
            bucket_name = self.s3_config['bucket_name']
            total_deleted = 0
            
            for prefix in self.s3_prefixes_to_clean:
                try:
                    # Listar objetos con el prefijo
                    response = self.s3_client.list_objects_v2(
                        Bucket=bucket_name, 
                        Prefix=prefix
                    )
                    
                    if 'Contents' in response:
                        # Eliminar objetos en lotes
                        objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                        
                        if objects_to_delete:
                            delete_response = self.s3_client.delete_objects(
                                Bucket=bucket_name,
                                Delete={'Objects': objects_to_delete}
                            )
                            
                            deleted_count = len(delete_response.get('Deleted', []))
                            total_deleted += deleted_count
                            
                            logger.info(f"[EMOJI_REMOVIDO] Eliminados {deleted_count} objetos con prefijo: {prefix}")
                    else:
                        logger.info(f"[INFO] No hay objetos con prefijo: {prefix}")
                
                except Exception as e:
                    logger.error(f"[EMOJI_REMOVIDO] Error limpiando prefijo {prefix}: {e}")
                    return False
            
            logger.info(f"[EMOJI_REMOVIDO] Limpieza S3 completada: {total_deleted} objetos eliminados")
            return True
            
        except Exception as e:
            logger.error(f"[EMOJI_REMOVIDO] Error en limpieza S3: {e}")
            return False
    
    def run_complete_cleanup(self) -> Dict[str, Any]:
        """Ejecutar limpieza completa"""
        logger.info("[INICIANDO] Iniciando limpieza completa de RDS y S3...")
        
        result = {
            'start_time': datetime.now(),
            'rds_verification': {},
            's3_verification': {},
            'rds_cleanup': False,
            's3_cleanup': False,
            'success': False,
            'error': None
        }
        
        try:
            # 1. Verificar estado inicial
            logger.info("=" * 60)
            logger.info("FASE 1: VERIFICACIÓN INICIAL")
            logger.info("=" * 60)
            
            result['rds_verification'] = self.verify_rds_tables()
            result['s3_verification'] = self.verify_s3_bucket()
            
            # 2. Limpiar RDS
            logger.info("\n" + "=" * 60)
            logger.info("FASE 2: LIMPIEZA RDS")
            logger.info("=" * 60)
            
            result['rds_cleanup'] = self.clean_rds_tables()
            
            # 3. Limpiar S3
            logger.info("\n" + "=" * 60)
            logger.info("FASE 3: LIMPIEZA S3")
            logger.info("=" * 60)
            
            result['s3_cleanup'] = self.clean_s3_bucket()
            
            # 4. Verificar limpieza final
            logger.info("\n" + "=" * 60)
            logger.info("FASE 4: VERIFICACIÓN FINAL")
            logger.info("=" * 60)
            
            final_rds = self.verify_rds_tables()
            final_s3 = self.verify_s3_bucket()
            
            # Determinar éxito
            result['success'] = (
                result['rds_cleanup'] and 
                result['s3_cleanup'] and
                sum(final_rds['counts'].values()) == 0 and
                final_s3['total_objects'] == 0
            )
            
            result['end_time'] = datetime.now()
            result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
            
            # Reporte final
            logger.info("\n" + "=" * 60)
            logger.info("[DATOS] REPORTE FINAL DE LIMPIEZA")
            logger.info("=" * 60)
            logger.info(f"[EMOJI_REMOVIDO] Duración: {result['duration']:.2f} segundos")
            logger.info(f"[EMOJI_REMOVIDO] RDS Limpieza: {'EXITOSA' if result['rds_cleanup'] else 'FALLIDA'}")
            logger.info(f"[EMOJI_REMOVIDO] S3 Limpieza: {'EXITOSA' if result['s3_cleanup'] else 'FALLIDA'}")
            logger.info(f"[EMOJI_REMOVIDO] Estado Final: {'LIMPIEZA COMPLETA' if result['success'] else 'LIMPIEZA PARCIAL'}")
            
            if result['success']:
                logger.info("[COMPLETADO] LIMPIEZA COMPLETA EXITOSA - Sistema listo para nuevo flujo")
            else:
                logger.warning("[ADVERTENCIA] LIMPIEZA PARCIAL - Revisar logs para detalles")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"[EMOJI_REMOVIDO] Error en limpieza completa: {e}")
        
        return result

def main():
    """Función principal"""
    print("🧹 SCRIPT DE LIMPIEZA COMPLETA - RDS Y S3")
    print("=" * 60)
    print("Este script eliminará TODOS los datos de:")
    print("- Tablas: data_general.ov_afinia, data_general.ov_aire")
    print("- S3 Bucket: extractorov-data (prefijos afinia/, aire/, etc.)")
    print("=" * 60)
    
    # Confirmación del usuario
    confirm = input("¿Está seguro de continuar? (escriba 'CONFIRMAR' para proceder): ")
    if confirm != 'CONFIRMAR':
        print("[ERROR] Operación cancelada por el usuario")
        return
    
    try:
        # Crear directorio de logs si no existe
        Path('logs').mkdir(exist_ok=True)
        
        # Ejecutar limpieza
        cleaner = RDSAndS3Cleaner()
        result = cleaner.run_complete_cleanup()
        
        # Guardar reporte
        import json
        report_file = f"logs/cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convertir datetime a string para JSON
        result_json = result.copy()
        for key in ['start_time', 'end_time']:
            if key in result_json and result_json[key]:
                result_json[key] = result_json[key].isoformat()
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[ARCHIVO] Reporte guardado en: {report_file}")
        
        # Código de salida
        exit_code = 0 if result['success'] else 1
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"[EMOJI_REMOVIDO] Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()