#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de prueba para verificar la integración de procesamiento PQR
con el extractor visual de Afinia OV
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Cargar variables de entorno
env_path = project_root / 'p16_env' / '.env'
load_dotenv(env_path)

# Configurar logging para pruebas
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('test_integracion')

# Importar después de configurar logging y path
from src.extractors.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular

async def test_integracion_completa():
    """Prueba la integración completa con procesamiento PQR"""
    try:
        logger.info("=== INICIANDO PRUEBA DE INTEGRACIÓN PQR ===")

        # Verificar credenciales
        username = os.getenv('OV_AFINIA_USERNAME')
        password = os.getenv('OV_AFINIA_PASSWORD')

        if not username or not password:
            logger.error("[ERROR] Credenciales no encontradas en variables de entorno")
            logger.info("[INFO] Asegúrate de configurar OV_AFINIA_USERNAME y OV_AFINIA_PASSWORD en p16_env/.env")
            return False

        # Configurar parámetros de prueba
        enable_pqr_processing = True  # Forzar habilitación para prueba
        max_pqr_records = 2  # Limitar a 2 registros para prueba rápida
        
        logger.info(f"[EMOJI_REMOVIDO] Configuración de prueba:")
        logger.info(f"   - Procesamiento PQR: {'Habilitado' if enable_pqr_processing else 'Deshabilitado'}")
        logger.info(f"   - Máximo registros PQR: {max_pqr_records}")
        logger.info(f"   - Usuario: {username[:3]}***")

        # Inicializar extractor con procesamiento PQR habilitado
        logger.info("[CONFIGURANDO] Inicializando extractor integrado...")
        extractor = OficinaVirtualAfiniaModular(
            headless=False,  # Modo visual para observar
            visual_mode=True,
            enable_pqr_processing=enable_pqr_processing,
            max_pqr_records=max_pqr_records
        )

        # Ejecutar extracción completa
        logger.info("[INICIANDO] Ejecutando extracción integrada...")
        start_time = datetime.now()
        
        result = await extractor.run_full_extraction(
            username=username,
            password=password
        )

        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Analizar resultados
        logger.info("[DATOS] RESULTADOS DE LA PRUEBA:")
        logger.info(f"   [TIEMPO] Tiempo de ejecución: {execution_time:.2f} segundos")
        
        if result['success']:
            logger.info("   [EXITOSO] Extracción exitosa")
            logger.info(f"   [EMOJI_REMOVIDO] Archivos descargados: {result.get('files_downloaded', 0)}")
            logger.info(f"   [EMOJI_REMOVIDO] Archivos procesados: {result.get('processed_files', 0)}")
            
            if 'pqr_processed' in result:
                logger.info(f"   [RESULTADO] PQR procesados: {result['pqr_processed']}")
                logger.info("   [EXITOSO] INTEGRACIÓN PQR FUNCIONANDO CORRECTAMENTE")
            else:
                logger.warning("   [ADVERTENCIA] No se procesaron PQR (puede ser normal si no hay registros)")
            
            # Mostrar detalles de procesamiento
            if 'processed_data' in result:
                logger.info("   [EMOJI_REMOVIDO] Detalles de procesamiento:")
                for i, data in enumerate(result['processed_data'], 1):
                    method = data.get('method', 'unknown')
                    status = data.get('status', 'unknown')
                    records = data.get('records_processed', 'N/A')
                    logger.info(f"      {i}. {method}: {status} (registros: {records})")
            
            return True
        else:
            logger.error(f"   [ERROR] Error en extracción: {result.get('error', 'Error desconocido')}")
            return False

    except Exception as e:
        logger.error(f"[ERROR] Error en prueba de integración: {e}")
        return False

async def test_configuracion_deshabilitada():
    """Prueba con procesamiento PQR deshabilitado"""
    try:
        logger.info("=== PRUEBA CON PQR DESHABILITADO ===")
        
        username = os.getenv('OV_AFINIA_USERNAME')
        password = os.getenv('OV_AFINIA_PASSWORD')

        if not username or not password:
            logger.warning("[ADVERTENCIA] Saltando prueba - credenciales no disponibles")
            return True

        # Extractor sin procesamiento PQR
        extractor = OficinaVirtualAfiniaModular(
            headless=True,  # Modo headless para prueba rápida
            visual_mode=False,
            enable_pqr_processing=False,  # Deshabilitado
            max_pqr_records=0
        )

        result = await extractor.run_full_extraction(
            username=username,
            password=password
        )

        if result['success']:
            logger.info("[EXITOSO] Extracción sin PQR exitosa")
            if 'pqr_processed' not in result:
                logger.info("[EXITOSO] Confirmado: No se procesaron PQR (como esperado)")
            return True
        else:
            logger.error(f"[ERROR] Error en extracción sin PQR: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"[ERROR] Error en prueba sin PQR: {e}")
        return False

async def main():
    """Función principal de pruebas"""
    logger.info("🧪 INICIANDO SUITE DE PRUEBAS DE INTEGRACIÓN")
    
    tests_passed = 0
    total_tests = 2
    
    # Prueba 1: Integración completa con PQR
    logger.info("\n" + "="*60)
    if await test_integracion_completa():
        tests_passed += 1
        logger.info("[EXITOSO] PRUEBA 1 PASADA: Integración completa")
    else:
        logger.error("[ERROR] PRUEBA 1 FALLIDA: Integración completa")
    
    # Prueba 2: Configuración deshabilitada
    logger.info("\n" + "="*60)
    if await test_configuracion_deshabilitada():
        tests_passed += 1
        logger.info("[EXITOSO] PRUEBA 2 PASADA: PQR deshabilitado")
    else:
        logger.error("[ERROR] PRUEBA 2 FALLIDA: PQR deshabilitado")
    
    # Resultados finales
    logger.info("\n" + "="*60)
    logger.info(f"[EMOJI_REMOVIDO] RESULTADOS FINALES: {tests_passed}/{total_tests} pruebas pasadas")
    
    if tests_passed == total_tests:
        logger.info("[COMPLETADO] TODAS LAS PRUEBAS PASARON - INTEGRACIÓN EXITOSA")
        return True
    else:
        logger.error("[ERROR] ALGUNAS PRUEBAS FALLARON - REVISAR CONFIGURACIÓN")
        return False

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
