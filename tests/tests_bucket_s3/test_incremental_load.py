#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de Carga Incremental BD -> S3
==================================

Test para cargar 2 registros desde la BD al bucket S3
y verificar que se registren correctamente en la tabla.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.s3_massive_loader import S3MassiveLoader
from src.config.rds_config import RDSConnectionManager
from sqlalchemy import text

def print_banner():
    print("=" * 70)
    print("🧪 TEST CARGA INCREMENTAL BD -> S3")
    print("=" * 70)
    print("Probando carga de 2 registros desde BD al bucket S3...")
    print()

def check_initial_state():
    """Verificar estado inicial de registros S3"""
    print("[DATOS] ESTADO INICIAL")
    print("-" * 40)
    
    rds_manager = RDSConnectionManager()
    session = rds_manager.get_session()
    
    try:
        # Contar registros en tabla S3
        count_query = text("SELECT COUNT(*) FROM data_general.registros_ov_s3")
        count_s3 = session.execute(count_query).scalar()
        print(f"Registros en tabla S3: {count_s3}")
        
        # Contar registros BD Afinia no procesados
        unprocessed_query = text("""
            SELECT COUNT(*)
            FROM data_general.ov_afinia ov
            LEFT JOIN data_general.registros_ov_s3 s3 
                ON s3.numero_reclamo_sgc = ov.numero_radicado 
                AND s3.empresa = 'afinia'
            WHERE s3.id IS NULL
        """)
        count_unprocessed = session.execute(unprocessed_query).scalar()
        print(f"Registros Afinia sin procesar: {count_unprocessed}")
        
        return count_s3, count_unprocessed
        
    finally:
        session.close()

def run_test_load():
    """Ejecutar test de carga"""
    print("\n[INICIANDO] EJECUTANDO CARGA DE PRUEBA")
    print("-" * 40)
    
    loader = S3MassiveLoader()
    
    # Obtener solo 2 registros para prueba
    records = loader.get_unprocessed_records('afinia')
    if not records:
        print("[ERROR] No hay registros para procesar")
        return False
    
    # Tomar solo los primeros 2
    test_records = records[:2]
    print(f"[EMOJI_REMOVIDO] Procesando {len(test_records)} registros de prueba:")
    
    for i, record in enumerate(test_records, 1):
        print(f"  {i}. {record['numero_radicado']} (Fecha: {record['fecha']})")
    
    # Procesar registros individualmente
    results = []
    for i, record in enumerate(test_records, 1):
        print(f"\n[ARCHIVO] [{i}/2] Procesando: {record['numero_radicado']}")
        
        result = loader.process_record_to_s3(record)
        results.append(result)
        
        if result.success:
            print(f"  [EXITOSO] Éxito: {result.upload_source}")
            if result.registry_id:
                print(f"  [EMOJI_REMOVIDO] Registry ID: {result.registry_id}")
        else:
            print(f"  [ERROR] Error: {result.error_message}")
    
    return results

def check_final_state(initial_count_s3):
    """Verificar estado final después de la carga"""
    print(f"\n[DATOS] ESTADO FINAL")
    print("-" * 40)
    
    rds_manager = RDSConnectionManager()
    session = rds_manager.get_session()
    
    try:
        # Contar registros actuales en tabla S3
        count_query = text("SELECT COUNT(*) FROM data_general.registros_ov_s3")
        final_count_s3 = session.execute(count_query).scalar()
        
        print(f"Registros en tabla S3 (antes): {initial_count_s3}")
        print(f"Registros en tabla S3 (después): {final_count_s3}")
        print(f"Incremento: +{final_count_s3 - initial_count_s3}")
        
        # Mostrar los últimos 3 registros creados
        latest_query = text("""
            SELECT nombre_archivo, numero_reclamo_sgc, empresa, estado_carga, 
                   fecha_carga, sincronizado_bd
            FROM data_general.registros_ov_s3
            ORDER BY fecha_creacion DESC
            LIMIT 3
        """)
        
        latest_records = session.execute(latest_query).fetchall()
        
        if latest_records:
            print(f"\n[EMOJI_REMOVIDO] ÚLTIMOS REGISTROS CREADOS:")
            for i, record in enumerate(latest_records, 1):
                print(f"  {i}. {record[0]}")
                print(f"     PQR: {record[1]} | Empresa: {record[2]}")
                print(f"     Estado: {record[3]} | Sincronizado: {record[5]}")
        
        return final_count_s3 - initial_count_s3
        
    finally:
        session.close()

def main():
    """Función principal"""
    print_banner()
    
    try:
        # 1. Estado inicial
        initial_count_s3, unprocessed_count = check_initial_state()
        
        if unprocessed_count == 0:
            print("[INFO] No hay registros sin procesar para test")
            return True
        
        # 2. Ejecutar carga de prueba
        results = run_test_load()
        
        if not results:
            print("[ERROR] No se ejecutó la carga")
            return False
        
        # 3. Estado final
        increment = check_final_state(initial_count_s3)
        
        # 4. Resumen
        print(f"\n[RESULTADO] RESUMEN DEL TEST")
        print("=" * 70)
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        print(f"[EXITOSO] Cargas exitosas: {len(successful_results)}")
        print(f"[ERROR] Cargas fallidas: {len(failed_results)}")
        print(f"[METRICAS] Registros agregados a tabla S3: {increment}")
        
        if len(successful_results) > 0 and increment > 0:
            print(f"\n[COMPLETADO] TEST EXITOSO")
            print("[EXITOSO] Los registros se cargaron al bucket S3")
            print("[EXITOSO] Los registros se registraron en la tabla registros_ov_s3")
            print("[EXITOSO] El flujo BD -> S3 -> Tabla funciona correctamente")
            return True
        else:
            print(f"\n[ADVERTENCIA] TEST INCOMPLETO")
            if len(successful_results) == 0:
                print("[ERROR] No se pudieron cargar archivos al bucket")
            if increment == 0:
                print("[ERROR] No se registraron en la tabla")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error durante el test: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)