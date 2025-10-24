#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de prueba para validar la secuencia específica de PQR en Afinia
Ejecuta una prueba controlada con pocos registros para verificar funcionamiento
"""

import os
import sys
import asyncio
import logging
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

logger = logging.getLogger('test_afinia_sequence')

# Importar el extractor específico
from examples.specialized_sequences.run_afinia_ov_specific_sequence import AfiniaSpecificSequenceExtractor

async def test_specific_sequence():
    """
    Prueba la secuencia específica con configuración de test
    """
    try:
        logger.info("🧪 INICIANDO PRUEBA DE SECUENCIA ESPECÍFICA")
        logger.info("=" * 60)
        
        # Configuración de prueba
        test_config = {
            'headless': False,  # Modo visual para ver qué pasa
            'max_records': 2    # Solo 2 registros para prueba
        }
        
        logger.info(f"[EMOJI_REMOVIDO] Configuración de prueba:")
        logger.info(f"   - Modo visual: {not test_config['headless']}")
        logger.info(f"   - Máximo registros: {test_config['max_records']}")
        logger.info("=" * 60)
        
        # Verificar credenciales
        username = os.getenv('OV_AFINIA_USERNAME')
        password = os.getenv('OV_AFINIA_PASSWORD')
        
        if not username or not password:
            logger.error("[ERROR] Credenciales no encontradas en variables de entorno")
            logger.error("   Asegúrate de tener OV_AFINIA_USERNAME y OV_AFINIA_PASSWORD en .env")
            return False
        
        logger.info(f"[EXITOSO] Credenciales encontradas para usuario: {username[:3]}***")
        
        # Crear extractor de prueba
        extractor = AfiniaSpecificSequenceExtractor(
            headless=test_config['headless'],
            max_records=test_config['max_records']
        )
        
        # Ejecutar prueba
        logger.info("[INICIANDO] Ejecutando extracción de prueba...")
        result = await extractor.run_specific_sequence_extraction()
        
        # Analizar resultados
        logger.info("=" * 60)
        logger.info("[DATOS] RESULTADOS DE LA PRUEBA:")
        
        if result['success']:
            logger.info("[EXITOSO] PRUEBA EXITOSA")
            logger.info(f"   [EMOJI_REMOVIDO] Registros procesados: {result['processed_records']}")
            logger.info(f"   [TIEMPO] Tiempo de ejecución: {result['execution_time']:.2f} segundos")
            logger.info(f"   [EMOJI_REMOVIDO] Archivos guardados en: {result['config_used']['download_path']}")
            
            # Verificar archivos generados
            download_path = Path(result['config_used']['download_path'])
            if download_path.exists():
                pdf_files = list(download_path.glob("*.pdf"))
                json_files = list(download_path.glob("*.json"))
                attachment_files = list(download_path.glob("*adjunto*"))
                
                logger.info(f"   [ARCHIVO] PDFs generados: {len(pdf_files)}")
                logger.info(f"   [EMOJI_REMOVIDO] JSONs generados: {len(json_files)}")
                logger.info(f"   [EMOJI_REMOVIDO] Adjuntos descargados: {len(attachment_files)}")
                
                if pdf_files:
                    logger.info("   [ARCHIVO] Archivos PDF encontrados:")
                    for pdf in pdf_files[:3]:  # Mostrar solo los primeros 3
                        logger.info(f"      - {pdf.name}")
                        
            return True
            
        else:
            logger.error("[ERROR] PRUEBA FALLIDA")
            logger.error(f"   Error: {result['error']}")
            logger.error(f"   Tiempo antes del error: {result['execution_time']:.2f} segundos")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Error en prueba: {e}")
        return False

async def test_components_individually():
    """
    Prueba los componentes individualmente para diagnóstico
    """
    try:
        logger.info("[CONFIGURANDO] PRUEBA DE COMPONENTES INDIVIDUALES")
        logger.info("=" * 60)
        
        # Importar componentes
        from c_components_03.afinia_pqr_processor import AfiniaPQRProcessor
        from a_core_01.browser_manager import BrowserManager
        
        # Configuración básica
        download_path = str(project_root / 'm_downloads_13' / 'afinia' / 'test')
        screenshots_dir = str(project_root / 'm_downloads_13' / 'afinia' / 'test' / 'screenshots')
        
        os.makedirs(download_path, exist_ok=True)
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Prueba 1: BrowserManager
        logger.info("[EMOJI_REMOVIDO] Probando BrowserManager...")
        browser_manager = BrowserManager(
            headless=False,
            timeout=30000,
            screenshots_dir=screenshots_dir
        )
        
        await browser_manager.__aenter__()
        page = browser_manager.page
        
        if page:
            logger.info("[EXITOSO] BrowserManager inicializado correctamente")
            
            # Prueba 2: AfiniaPQRProcessor
            logger.info("[EMOJI_REMOVIDO] Probando AfiniaPQRProcessor...")
            pqr_processor = AfiniaPQRProcessor(page, download_path, screenshots_dir)
            logger.info("[EXITOSO] AfiniaPQRProcessor inicializado correctamente")
            
            # Navegar a una página de prueba
            logger.info("[EMOJI_REMOVIDO] Navegando a página de prueba...")
            await page.goto("https://www.google.com")
            logger.info("[EXITOSO] Navegación de prueba exitosa")
            
        else:
            logger.error("[ERROR] Error inicializando BrowserManager")
            return False
            
        # Limpiar
        await browser_manager.cleanup()
        logger.info("🧹 Componentes limpiados")
        
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Error en prueba de componentes: {e}")
        return False

def show_test_menu():
    """Muestra menú de opciones de prueba"""
    print("\n" + "=" * 60)
    print("🧪 MENÚ DE PRUEBAS - AFINIA SECUENCIA ESPECÍFICA")
    print("=" * 60)
    print("1. Prueba completa de secuencia específica")
    print("2. Prueba de componentes individuales")
    print("3. Verificar configuración")
    print("4. Salir")
    print("=" * 60)

def verify_configuration():
    """Verifica la configuración del sistema"""
    logger.info("[EMOJI_REMOVIDO] VERIFICANDO CONFIGURACIÓN")
    logger.info("=" * 60)
    
    # Verificar variables de entorno
    required_vars = [
        'OV_AFINIA_USERNAME',
        'OV_AFINIA_PASSWORD',
        'OV_AFINIA_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                logger.info(f"[EXITOSO] {var}: ***")
            else:
                logger.info(f"[EXITOSO] {var}: {value}")
        else:
            missing_vars.append(var)
            logger.error(f"[ERROR] {var}: No encontrada")
    
    # Verificar directorios
    logger.info("\n[EMOJI_REMOVIDO] Verificando directorios:")
    test_dirs = [
        project_root / 'm_downloads_13' / 'afinia',
        project_root / 'p16_env',
        project_root / "data/logs"
    ]
    
    for dir_path in test_dirs:
        if dir_path.exists():
            logger.info(f"[EXITOSO] {dir_path}: Existe")
        else:
            logger.warning(f"[ADVERTENCIA] {dir_path}: No existe (se creará automáticamente)")
    
    # Verificar archivos de configuración
    logger.info("\n[ARCHIVO] Verificando archivos:")
    config_files = [
        project_root / 'p16_env' / '.env',
        project_root / 'c_components_03' / 'afinia_pqr_processor.py',
        project_root / 'run_afinia_ov_specific_sequence.py'
    ]
    
    for file_path in config_files:
        if file_path.exists():
            logger.info(f"[EXITOSO] {file_path.name}: Existe")
        else:
            logger.error(f"[ERROR] {file_path.name}: No encontrado")
    
    if missing_vars:
        logger.error(f"\n[ERROR] Variables faltantes: {', '.join(missing_vars)}")
        logger.error("   Configúralas en p16_env/.env")
        return False
    else:
        logger.info("\n[EXITOSO] Configuración completa")
        return True

async def main():
    """Función principal del script de prueba"""
    try:
        while True:
            show_test_menu()
            choice = input("\nSelecciona una opción (1-4): ").strip()
            
            if choice == '1':
                print("\n🧪 Ejecutando prueba completa...")
                success = await test_specific_sequence()
                if success:
                    print("\n[EXITOSO] Prueba completada exitosamente")
                else:
                    print("\n[ERROR] Prueba falló")
                    
            elif choice == '2':
                print("\n[CONFIGURANDO] Ejecutando prueba de componentes...")
                success = await test_components_individually()
                if success:
                    print("\n[EXITOSO] Componentes funcionan correctamente")
                else:
                    print("\n[ERROR] Error en componentes")
                    
            elif choice == '3':
                print("\n[EMOJI_REMOVIDO] Verificando configuración...")
                verify_configuration()
                
            elif choice == '4':
                print("\n[EMOJI_REMOVIDO] Saliendo...")
                break
                
            else:
                print("\n[ERROR] Opción inválida")
            
            input("\nPresiona Enter para continuar...")
            
    except KeyboardInterrupt:
        print("\n\n[EMOJI_REMOVIDO] Saliendo por interrupción del usuario...")
    except Exception as e:
        logger.error(f"[ERROR] Error en main: {e}")

if __name__ == '__main__':
    asyncio.run(main())
