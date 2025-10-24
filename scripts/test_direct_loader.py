#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba - Cargador Directo JSON → RDS
==============================================

Script para probar el cargador directo con datos de ejemplo,
validando la funcionalidad de deduplicación y carga.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Agregar src y scripts al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from scripts.direct_json_to_rds_loader import DirectJSONToRDSLoader

# Configurar logging sin emojis para evitar problemas de encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_test_json_data():
    """Crear datos JSON de prueba"""
    test_data = [
        {
            "numero_radicado": "TEST001",
            "fecha": "2024/10/12 10:30",
            "estado_solicitud": "En proceso",
            "tipo_pqr": "Petición",
            "nic": "12345678",
            "nombres_apellidos": "Juan Pérez García",
            "telefono": "3001234567",
            "celular": "3001234567",
            "correo_electronico": "juan.perez@email.com",
            "documento_identidad": "12345678",
            "canal_respuesta": "Email"
        },
        {
            "numero_radicado": "TEST002",
            "fecha": "2024/10/12 11:15",
            "estado_solicitud": "Resuelto",
            "tipo_pqr": "Queja",
            "nic": "87654321",
            "nombres_apellidos": "María González López",
            "telefono": "3009876543",
            "celular": "3009876543",
            "correo_electronico": "maria.gonzalez@email.com",
            "documento_identidad": "87654321",
            "canal_respuesta": "Teléfono"
        },
        # Registro duplicado (mismo numero_radicado)
        {
            "numero_radicado": "TEST001",
            "fecha": "2024/10/12 10:30",
            "estado_solicitud": "En proceso",
            "tipo_pqr": "Petición",
            "nic": "12345678",
            "nombres_apellidos": "Juan Pérez García",
            "telefono": "3001234567",
            "celular": "3001234567",
            "correo_electronico": "juan.perez@email.com",
            "documento_identidad": "12345678",
            "canal_respuesta": "Email"
        },
        # Registro con datos inválidos
        {
            "numero_radicado": "",  # Campo obligatorio vacío
            "fecha": "fecha_inválida",
            "estado_solicitud": "Estado muy largo que excede el límite de caracteres permitido para este campo en la base de datos y debería generar un error de validación",
            "tipo_pqr": "Reclamo",
            "nic": "11111111",
            "nombres_apellidos": "Pedro Inválido",
            "telefono": "300111111",
            "celular": "300111111",
            "correo_electronico": "pedro@email.com",
            "documento_identidad": "11111111",
            "canal_respuesta": "Presencial"
        }
    ]
    
    return test_data

def create_test_files():
    """Crear archivos JSON de prueba"""
    test_dir = Path("data/test_direct_loader")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Crear primer archivo
    file1_data = create_test_json_data()[:2]  # Primeros 2 registros
    file1_path = test_dir / "afinia_pqr_data_20241012_103000.json"
    
    with open(file1_path, 'w', encoding='utf-8') as f:
        json.dump(file1_data, f, indent=2, ensure_ascii=False)
    
    # Crear segundo archivo con duplicados
    file2_data = create_test_json_data()[2:]  # Registros duplicados e inválidos
    file2_path = test_dir / "afinia_pqr_data_20241012_113000.json"
    
    with open(file2_path, 'w', encoding='utf-8') as f:
        json.dump(file2_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"[EMOJI_REMOVIDO] Archivos de prueba creados en: {test_dir}")
    logger.info(f"  - {file1_path.name}: {len(file1_data)} registros")
    logger.info(f"  - {file2_path.name}: {len(file2_data)} registros")
    
    return test_dir

def test_validation():
    """Probar funciones de validación"""
    logger.info("Probando validaciones...")
    
    loader = DirectJSONToRDSLoader()
    
    # Registro válido
    valid_record = {
        "numero_radicado": "TEST001",
        "fecha": "2024/10/12 10:30",
        "estado_solicitud": "En proceso",
        "nic": "12345678"
    }
    
    is_valid, errors = loader.validate_record(valid_record)
    assert is_valid, f"Registro válido falló validación: {errors}"
    logger.info("Validación de registro válido: PASS")
    
    # Registro inválido
    invalid_record = {
        "numero_radicado": "",  # Campo obligatorio vacío
        "fecha": "fecha_inválida",
        "estado_solicitud": "x" * 150  # Muy largo
    }
    
    is_valid, errors = loader.validate_record(invalid_record)
    assert not is_valid, "Registro inválido pasó validación"
    assert len(errors) > 0, "No se generaron errores para registro inválido"
    logger.info(f"Validación de registro inválido: PASS ({len(errors)} errores detectados)")

def test_hash_generation():
    """Probar generación de hash"""
    logger.info("Probando generación de hash...")
    
    loader = DirectJSONToRDSLoader()
    
    record1 = {
        "numero_radicado": "TEST001",
        "fecha": "2024/10/12 10:30",
        "nic": "12345678",
        "nombres_apellidos": "Juan Pérez"
    }
    
    record2 = {
        "numero_radicado": "TEST001",
        "fecha": "2024/10/12 10:30",
        "nic": "12345678",
        "nombres_apellidos": "Juan Pérez"
    }
    
    record3 = {
        "numero_radicado": "TEST002",
        "fecha": "2024/10/12 10:30",
        "nic": "12345678",
        "nombres_apellidos": "Juan Pérez"
    }
    
    hash1 = loader.generate_record_hash(record1)
    hash2 = loader.generate_record_hash(record2)
    hash3 = loader.generate_record_hash(record3)
    
    assert hash1 == hash2, "Registros idénticos generaron hash diferentes"
    assert hash1 != hash3, "Registros diferentes generaron el mismo hash"
    
    logger.info("Generación de hash: PASS")

def test_record_preparation():
    """Probar preparación de registros"""
    logger.info("Probando preparación de registros...")
    
    loader = DirectJSONToRDSLoader()
    
    original_record = {
        "numero_radicado": "TEST001",
        "fecha": "2024/10/12 10:30",
        "estado_solicitud": "En proceso",
        "tipo_pqr": "Petición",
        "nic": "12345678",
        "nombres_apellidos": "Juan Pérez García"
    }
    
    prepared = loader.prepare_record_for_insertion(original_record, "test_file.json")
    
    # Verificar campos mapeados
    assert prepared['numero_radicado'] == "TEST001"
    assert prepared['fecha'] == "2024/10/12 10:30"
    
    # Verificar campos adicionales
    assert 'hash_registro' in prepared
    assert 'fecha_extraccion' in prepared
    assert prepared['archivo_origen'] == "test_file.json"
    assert prepared['procesado_flag'] is False
    
    logger.info("Preparación de registros: PASS")

def run_integration_test():
    """Ejecutar prueba de integración completa"""
    logger.info("Ejecutando prueba de integración...")
    
    try:
        # Crear archivos de prueba
        test_dir = create_test_files()
        
        # Crear cargador
        loader = DirectJSONToRDSLoader()
        
        # Procesar directorio de prueba
        stats = loader.process_directory(test_dir, 'afinia')
        
        # Verificar resultados
        logger.info("Resultados de la prueba:")
        logger.info(f"  Total registros: {stats.total_records}")
        logger.info(f"  Procesados: {stats.processed_records}")
        logger.info(f"  Duplicados: {stats.duplicated_records}")
        logger.info(f"  Fallidos: {stats.failed_records}")
        logger.info(f"  Errores: {len(stats.errors)}")
        
        # Generar reporte
        report_file = Path(f"logs/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        report = loader.generate_processing_report(stats, report_file)
        
        logger.info(f"Reporte generado: {report_file}")
        
        # Limpiar archivos de prueba
        import shutil
        shutil.rmtree(test_dir)
        logger.info("Archivos de prueba eliminados")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error en prueba de integración: {e}")
        raise

def main():
    """Función principal de pruebas"""
    logger.info("Iniciando pruebas del cargador directo JSON -> RDS")
    logger.info("=" * 60)
    
    try:
        # Crear directorio de logs
        Path('logs').mkdir(exist_ok=True)
        
        # Ejecutar pruebas unitarias
        test_validation()
        test_hash_generation()
        test_record_preparation()
        
        logger.info("Todas las pruebas unitarias pasaron")
        
        # Ejecutar prueba de integración
        stats = run_integration_test()
        
        logger.info("\n" + "=" * 60)
        logger.info("TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        logger.info("=" * 60)
        
        # Mostrar resumen
        if stats:
            success_rate = (stats.processed_records / stats.total_records * 100) if stats.total_records > 0 else 0
            logger.info(f"Tasa de éxito: {success_rate:.1f}%")
            logger.info(f"Duplicados detectados: {stats.duplicated_records}")
            logger.info(f"Registros fallidos: {stats.failed_records}")
        
    except Exception as e:
        logger.error(f"Error en las pruebas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()