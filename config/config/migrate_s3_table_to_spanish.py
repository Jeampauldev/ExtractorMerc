#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrar Tabla S3 a Español
========================

Script para migrar la tabla s3_files_registry a español:
s3_files_registry -> registros_ov_s3

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.config.rds_config import RDSConnectionManager
    from sqlalchemy import text
except ImportError as e:
    print(f"[ERROR] Error importando módulos: {e}")
    sys.exit(1)

def print_banner():
    """Imprimir banner del script"""
    print("=" * 70)
    print("[EMOJI_REMOVIDO] MIGRAR TABLA S3 A ESPAÑOL")
    print("=" * 70)
    print("s3_files_registry -> registros_ov_s3")
    print()

def check_existing_tables():
    """Verificar estado de las tablas"""
    rds_manager = RDSConnectionManager()
    session = rds_manager.get_session()
    
    try:
        print("[EMOJI_REMOVIDO] Verificando tablas existentes...")
        
        # Verificar tabla actual
        check_old_sql = text("""
            SELECT COUNT(*) as count,
                   (SELECT COUNT(*) FROM data_general.s3_files_registry) as records
            FROM information_schema.tables 
            WHERE table_schema = 'data_general' 
            AND table_name = 's3_files_registry'
        """)
        
        old_result = session.execute(check_old_sql).fetchone()
        
        # Verificar nueva tabla
        check_new_sql = text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'data_general' 
            AND table_name = 'registros_ov_s3'
        """)
        
        new_exists = session.execute(check_new_sql).scalar()
        
        status = {
            'old_table_exists': old_result[0] > 0,
            'old_table_records': old_result[1] if old_result[0] > 0 else 0,
            'new_table_exists': new_exists > 0,
            'new_table_records': 0
        }
        
        if new_exists:
            count_new_sql = text("SELECT COUNT(*) FROM data_general.registros_ov_s3")
            status['new_table_records'] = session.execute(count_new_sql).scalar()
        
        print(f"[DATOS] ESTADO ACTUAL:")
        print(f"  Tabla antigua (s3_files_registry): {'[EXITOSO] Existe' if status['old_table_exists'] else '[ERROR] No existe'}")
        if status['old_table_exists']:
            print(f"    Registros: {status['old_table_records']}")
        print(f"  Tabla nueva (registros_ov_s3): {'[EXITOSO] Existe' if status['new_table_exists'] else '[ERROR] No existe'}")
        if status['new_table_exists']:
            print(f"    Registros: {status['new_table_records']}")
        
        return status
        
    finally:
        session.close()

def create_new_table():
    """Crear la nueva tabla en español"""
    rds_manager = RDSConnectionManager()
    session = rds_manager.get_session()
    
    try:
        print("\n[EMOJI_REMOVIDO] Creando tabla registros_ov_s3...")
        
        # DDL para tabla en español con campos mejorados
        create_sql = text("""
            CREATE TABLE IF NOT EXISTS data_general.registros_ov_s3 (
                id SERIAL PRIMARY KEY,
                
                -- Información del archivo
                nombre_archivo VARCHAR(255) NOT NULL,
                ruta_original VARCHAR(500),
                tamano_archivo BIGINT DEFAULT 0,
                tipo_archivo VARCHAR(10),
                hash_archivo VARCHAR(64) UNIQUE,
                
                -- Información S3
                bucket_s3 VARCHAR(100) NOT NULL,
                clave_s3 VARCHAR(500) NOT NULL UNIQUE,
                url_s3 VARCHAR(1000),
                region_s3 VARCHAR(50) DEFAULT 'us-west-2',
                
                -- Información de negocio
                numero_reclamo_sgc VARCHAR(50),
                empresa VARCHAR(20) NOT NULL CHECK (empresa IN ('afinia', 'aire')),
                tipo_contenido VARCHAR(100),
                
                -- Estado y control
                estado_carga VARCHAR(20) DEFAULT 'subido' 
                    CHECK (estado_carga IN ('subido', 'pre_existente', 'error', 'pendiente')),
                origen_carga VARCHAR(20) DEFAULT 'bot' 
                    CHECK (origen_carga IN ('bot', 'pre_existente', 'manual', 'migracion')),
                
                -- Flags de control
                procesado BOOLEAN DEFAULT TRUE,
                sincronizado_bd BOOLEAN DEFAULT FALSE,
                requiere_resubida BOOLEAN DEFAULT FALSE,
                
                -- Metadatos y auditoría
                metadatos JSONB,
                observaciones TEXT,
                intentos_carga INTEGER DEFAULT 1,
                ultimo_error TEXT,
                
                -- Fechas
                fecha_carga TIMESTAMP DEFAULT NOW(),
                fecha_archivo TIMESTAMP,
                fecha_creacion TIMESTAMP DEFAULT NOW(),
                fecha_actualizacion TIMESTAMP DEFAULT NOW()
            )
        """)
        
        session.execute(create_sql)
        session.commit()
        print("[EXITOSO] Tabla registros_ov_s3 creada")
        
        # Crear índices optimizados
        print("[EMOJI_REMOVIDO] Creando índices...")
        indices = [
            # Índices principales
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_numero_reclamo ON data_general.registros_ov_s3 (numero_reclamo_sgc)",
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_empresa ON data_general.registros_ov_s3 (empresa)",
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_estado ON data_general.registros_ov_s3 (estado_carga)",
            
            # Índices de control
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_procesado ON data_general.registros_ov_s3 (procesado)",
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_sincronizado ON data_general.registros_ov_s3 (sincronizado_bd)",
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_resubida ON data_general.registros_ov_s3 (requiere_resubida)",
            
            # Índices de fechas
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_fecha_carga ON data_general.registros_ov_s3 (fecha_carga DESC)",
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_fecha_actualizacion ON data_general.registros_ov_s3 (fecha_actualizacion DESC)",
            
            # Índices técnicos
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_hash ON data_general.registros_ov_s3 (hash_archivo)",
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_clave_s3 ON data_general.registros_ov_s3 (clave_s3)",
            
            # Índice compuesto para búsquedas frecuentes
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_empresa_fecha ON data_general.registros_ov_s3 (empresa, fecha_carga DESC)",
            "CREATE INDEX IF NOT EXISTS idx_rov_s3_empresa_procesado ON data_general.registros_ov_s3 (empresa, procesado, sincronizado_bd)"
        ]
        
        for idx_sql in indices:
            session.execute(text(idx_sql))
            
        session.commit()
        print("[EXITOSO] Índices creados")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Error creando tabla nueva: {e}")
        return False
    finally:
        session.close()

def migrate_data(status):
    """Migrar datos de tabla antigua a nueva"""
    if not status['old_table_exists']:
        print("[INFO] No hay datos para migrar")
        return True
        
    rds_manager = RDSConnectionManager()
    session = rds_manager.get_session()
    
    try:
        print(f"\n[EMOJI_REMOVIDO] Migrando {status['old_table_records']} registros...")
        
        # Mapear campos de tabla antigua a nueva
        migrate_sql = text("""
            INSERT INTO data_general.registros_ov_s3 (
                nombre_archivo, bucket_s3, clave_s3, url_s3, 
                numero_reclamo_sgc, empresa, tamano_archivo, 
                tipo_archivo, tipo_contenido, estado_carga, 
                origen_carga, hash_archivo, fecha_carga, 
                metadatos, procesado, fecha_creacion, fecha_actualizacion
            )
            SELECT 
                filename,
                s3_bucket,
                s3_key,
                s3_url,
                numero_reclamo_sgc,
                empresa,
                file_size,
                file_type,
                content_type,
                CASE upload_status
                    WHEN 'uploaded' THEN 'subido'
                    WHEN 'pre_existing' THEN 'pre_existente' 
                    ELSE 'error'
                END,
                CASE upload_source
                    WHEN 'pre_existing' THEN 'pre_existente'
                    ELSE 'bot'
                END,
                file_hash,
                uploaded_at,
                metadata,
                TRUE,
                created_at,
                updated_at
            FROM data_general.s3_files_registry
            ON CONFLICT (hash_archivo) DO UPDATE SET
                fecha_actualizacion = NOW(),
                observaciones = 'Actualizado durante migración'
        """)
        
        result = session.execute(migrate_sql)
        migrated_count = result.rowcount
        session.commit()
        
        print(f"[EXITOSO] {migrated_count} registros migrados exitosamente")
        
        # Verificar migración
        verify_sql = text("SELECT COUNT(*) FROM data_general.registros_ov_s3")
        final_count = session.execute(verify_sql).scalar()
        print(f"[DATOS] Total registros en nueva tabla: {final_count}")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Error migrando datos: {e}")
        return False
    finally:
        session.close()

def create_backup_table():
    """Crear tabla de respaldo de la antigua"""
    rds_manager = RDSConnectionManager()
    session = rds_manager.get_session()
    
    try:
        print("\n[EMOJI_REMOVIDO] Creando tabla de respaldo...")
        
        backup_sql = text("""
            CREATE TABLE IF NOT EXISTS data_general.s3_files_registry_backup AS 
            SELECT *, NOW() as backup_fecha 
            FROM data_general.s3_files_registry
        """)
        
        session.execute(backup_sql)
        session.commit()
        print("[EXITOSO] Backup creado: s3_files_registry_backup")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Error creando backup: {e}")
        return False
    finally:
        session.close()

def show_table_structure():
    """Mostrar estructura de la nueva tabla"""
    rds_manager = RDSConnectionManager()
    session = rds_manager.get_session()
    
    try:
        print("\n[EMOJI_REMOVIDO] ESTRUCTURA DE LA NUEVA TABLA")
        print("-" * 70)
        
        structure_sql = text("""
            SELECT column_name, data_type, 
                   CASE WHEN is_nullable = 'YES' THEN 'NULL' ELSE 'NOT NULL' END as nullable,
                   column_default
            FROM information_schema.columns 
            WHERE table_schema = 'data_general' 
            AND table_name = 'registros_ov_s3'
            ORDER BY ordinal_position
        """)
        
        columns = session.execute(structure_sql).fetchall()
        
        for col in columns:
            default = f" DEFAULT {col[3]}" if col[3] else ""
            print(f"  {col[0]:<25} {col[1]:<20} {col[2]:<10}{default}")
            
    except Exception as e:
        print(f"[ERROR] Error mostrando estructura: {e}")
    finally:
        session.close()

def main():
    """Función principal"""
    print_banner()
    
    try:
        # 1. Verificar estado actual
        status = check_existing_tables()
        
        # 2. Crear backup si hay datos
        if status['old_table_exists'] and status['old_table_records'] > 0:
            if not create_backup_table():
                print("[ERROR] Error creando backup - abortando migración")
                return False
        
        # 3. Crear nueva tabla
        if not create_new_table():
            print("[ERROR] Error creando nueva tabla")
            return False
        
        # 4. Migrar datos
        if not migrate_data(status):
            print("[ERROR] Error migrando datos")
            return False
        
        # 5. Mostrar estructura final
        show_table_structure()
        
        print("\n[COMPLETADO] MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        print("[EXITOSO] Nueva tabla: data_general.registros_ov_s3")
        print("[EXITOSO] Datos migrados correctamente")
        print("[EXITOSO] Backup creado: s3_files_registry_backup")
        print("[EXITOSO] Índices optimizados")
        print("\nPróximos pasos:")
        print("  1. Actualizar servicios para usar nueva tabla")
        print("  2. Probar funcionamiento")
        print("  3. Eliminar tabla antigua cuando esté todo verificado")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error general: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)