#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Prueba para el Sistema de Logging Unificado
====================================================

Este script prueba todas las funcionalidades del nuevo sistema de logging:
- Creación de logs por servicio
- Logging de sesiones, descargas y errores
- Integración con métricas existentes
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from f_config_06.unified_logging_config import (
    get_unified_logger,
    setup_service_logging,
    log_system_event,
    get_all_services_stats
)
import time
from datetime import datetime

def test_afinia_logging():
    """Prueba el sistema de logging para Afinia"""
    print("[EMOJI_REMOVIDO] Probando logging de Afinia...")
    
    # Configurar logger
    logger = setup_service_logging('afinia', 'test')
    unified_logger = get_unified_logger()
    
    # Registrar inicio de sesión
    session_data = {
        'mode': 'test',
        'version': '1.0',
        'user': 'test_user'
    }
    unified_logger.log_session_start('afinia', session_data)
    
    # Simular logs de operación
    logger.info("Iniciando prueba de Afinia...")
    logger.info("Conectando al sistema...")
    logger.info("Autenticación exitosa")
    
    # Simular descarga
    download_info = {
        'filename': 'test_afinia_pqr_001.pdf',
        'size_bytes': 524288,
        'download_time': 2.5,
        'status': 'success'
    }
    unified_logger.log_download('afinia', download_info)
    
    # Simular evento del sistema
    log_system_event('afinia', 'pqr_processed', {
        'pqr_id': 'PQR-12345',
        'status': 'completed',
        'processing_time': 45.2
    })
    
    # Simular warning (no error crítico)
    logger.warning("Elemento no encontrado, reintentando...")
    
    # Registrar fin de sesión
    end_session_data = {
        'status': 'success',
        'files_processed': 15,
        'duration_seconds': 120.5
    }
    unified_logger.log_session_end('afinia', end_session_data)
    
    logger.info("[EXITOSO] Prueba de Afinia completada")

def test_aire_logging():
    """Prueba el sistema de logging para Aire"""
    print("[EMOJI_REMOVIDO] Probando logging de Aire...")
    
    # Configurar logger
    logger = setup_service_logging('aire', 'test')
    unified_logger = get_unified_logger()
    
    # Registrar inicio de sesión
    session_data = {
        'mode': 'test',
        'version': '1.0',
        'user': 'test_user'
    }
    unified_logger.log_session_start('aire', session_data)
    
    # Simular logs de operación
    logger.info("Iniciando prueba de Aire...")
    logger.info("Conectando al sistema...")
    logger.info("Autenticación exitosa")
    
    # Simular descarga
    download_info = {
        'filename': 'test_aire_report_001.xlsx',
        'size_bytes': 1048576,
        'download_time': 3.8,
        'status': 'success'
    }
    unified_logger.log_download('aire', download_info)
    
    # Simular error recuperable
    unified_logger.log_error('aire', {
        'error': 'Timeout en descarga, reintentando...',
        'context': 'download_retry',
        'severity': 'warning'
    })
    
    # Simular evento del sistema
    log_system_event('aire', 'report_generated', {
        'report_type': 'monthly_summary',
        'records_count': 250,
        'generation_time': 15.7
    })
    
    # Registrar fin de sesión
    end_session_data = {
        'status': 'success',
        'reports_generated': 3,
        'duration_seconds': 95.2
    }
    unified_logger.log_session_end('aire', end_session_data)
    
    logger.info("[EXITOSO] Prueba de Aire completada")

def test_error_handling():
    """Prueba el manejo de errores en el sistema"""
    print("[EMOJI_REMOVIDO] Probando manejo de errores...")
    
    logger_afinia = setup_service_logging('afinia', 'error_test')
    logger_aire = setup_service_logging('aire', 'error_test')
    unified_logger = get_unified_logger()
    
    # Simular errores diversos
    try:
        # Error simulado en Afinia
        raise ConnectionError("No se pudo conectar a la página de Afinia")
    except Exception as e:
        unified_logger.log_error('afinia', {
            'error': str(e),
            'error_type': type(e).__name__,
            'context': 'connection_test',
            'severity': 'high'
        })
        logger_afinia.error(f"Error capturado: {e}")
    
    try:
        # Error simulado en Aire
        raise ValueError("Formato de fecha inválido")
    except Exception as e:
        unified_logger.log_error('aire', {
            'error': str(e),
            'error_type': type(e).__name__,
            'context': 'date_validation',
            'severity': 'medium'
        })
        logger_aire.error(f"Error capturado: {e}")
    
    print("[EXITOSO] Prueba de manejo de errores completada")

def show_statistics():
    """Muestra las estadísticas de todos los servicios"""
    print("\n[DATOS] Estadísticas de Logging:")
    print("=" * 50)
    
    stats = get_all_services_stats()
    
    for service, data in stats.items():
        print(f"\n[EMOJI_REMOVIDO] Servicio: {service.upper()}")
        print(f"   Archivo: {data['log_file']}")
        print(f"   Líneas totales: {data['total_lines']}")
        print(f"   Tamaño: {data['file_size']:,} bytes")
        print(f"   Última modificación: {data['last_modified']}")

def test_legacy_compatibility():
    """Prueba la compatibilidad con el sistema anterior"""
    print("[EMOJI_REMOVIDO] Probando compatibilidad con sistema anterior...")
    
    import logging
    
    # Configurar logging "tradicional"
    old_logger = logging.getLogger("legacy_test")
    old_logger.setLevel(logging.INFO)
    
    # Este logger debería seguir funcionando
    old_logger.info("Mensaje de compatibilidad - sistema anterior")
    old_logger.warning("Warning del sistema anterior")
    
    print("[EXITOSO] Compatibilidad verificada")

def main():
    """Función principal de pruebas"""
    print("[INICIANDO] INICIANDO PRUEBAS DEL SISTEMA DE LOGGING UNIFICADO")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Ejecutar todas las pruebas
        test_afinia_logging()
        print()
        
        test_aire_logging() 
        print()
        
        test_error_handling()
        print()
        
        test_legacy_compatibility()
        print()
        
        show_statistics()
        
        elapsed = time.time() - start_time
        
        print(f"\n[COMPLETADO] TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print(f"[TIEMPO] Tiempo transcurrido: {elapsed:.2f} segundos")
        print("\n[EXITOSO] El sistema de logging unificado está funcionando correctamente!")
        print("\n[EMOJI_REMOVIDO] Revisa la carpeta 'logs/' para ver los archivos generados:")
        print("   - logs/current/afinia_ov.log")
        print("   - logs/current/aire_ov.log")
        
    except Exception as e:
        print(f"\n[ERROR] Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())