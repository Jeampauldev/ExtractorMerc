#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prueba simple del procesador PQR para identificar por qué no se generan archivos
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Cargar variables de entorno
env_path = project_root / 'p16_env' / '.env'
load_dotenv(env_path)

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('test_pqr_simple')

async def test_pdf_generation():
    """Prueba simple de generación de PDF"""
    try:
        logger.info("=== PRUEBA DE GENERACIÓN DE PDF ===")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Crear browser
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navegar a una página simple
            await page.goto("https://www.google.com")
            await page.wait_for_load_state('networkidle')
            
            # Configurar rutas
            download_path = Path(__file__).parent / 'm_downloads_13' / 'afinia' / 'oficina_virtual' / 'processed'
            download_path.mkdir(parents=True, exist_ok=True)
            
            # Generar PDF de prueba
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = download_path / f"test_pdf_{timestamp}.pdf"
            
            logger.info(f"[ARCHIVO] Generando PDF de prueba: {pdf_filename}")
            
            await page.pdf(
                path=str(pdf_filename),
                format='A4',
                print_background=True,
                margin={
                    'top': '1cm',
                    'right': '1cm',
                    'bottom': '1cm',
                    'left': '1cm'
                }
            )
            
            if pdf_filename.exists():
                logger.info(f"[EXITOSO] PDF generado exitosamente: {pdf_filename}")
                logger.info(f"[DATOS] Tamaño: {pdf_filename.stat().st_size} bytes")
                return True
            else:
                logger.error("[ERROR] PDF no se generó")
                return False
            
    except Exception as e:
        logger.error(f"[ERROR] Error en prueba de PDF: {e}")
        return False
    finally:
        try:
            await browser.close()
        except:
            pass

async def test_json_generation():
    """Prueba simple de generación de JSON"""
    try:
        logger.info("=== PRUEBA DE GENERACIÓN DE JSON ===")
        
        import json
        
        # Configurar rutas
        data_dir = Path(__file__).parent / 'm_downloads_13' / 'afinia' / 'oficina_virtual' / 'processed'
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Datos de prueba
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_data = {
            'record_number': 1,
            'sgc_number': f'TEST_{timestamp}',
            'extraction_timestamp': timestamp,
            'test_field_1': 'Valor de prueba 1',
            'test_field_2': 'Valor de prueba 2',
            'campos_extraidos': 5
        }
        
        # Generar archivo JSON
        json_filename = data_dir / f"test_data_{timestamp}.json"
        
        logger.info(f"[EMOJI_REMOVIDO] Generando JSON de prueba: {json_filename}")
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        if json_filename.exists():
            logger.info(f"[EXITOSO] JSON generado exitosamente: {json_filename}")
            logger.info(f"[DATOS] Tamaño: {json_filename.stat().st_size} bytes")
            return True
        else:
            logger.error("[ERROR] JSON no se generó")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Error en prueba de JSON: {e}")
        return False

async def test_screenshot_generation():
    """Prueba simple de generación de screenshot"""
    try:
        logger.info("=== PRUEBA DE GENERACIÓN DE SCREENSHOT ===")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Crear browser
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navegar a una página simple
            await page.goto("https://www.google.com")
            await page.wait_for_load_state('networkidle')
            
            # Configurar rutas
            screenshots_dir = Path(__file__).parent / 'm_downloads_13' / 'afinia' / 'oficina_virtual' / 'screenshots'
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            # Generar screenshot de prueba
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = screenshots_dir / f"test_screenshot_{timestamp}.png"
            
            logger.info(f"[EMOJI_REMOVIDO] Generando screenshot de prueba: {screenshot_filename}")
            
            await page.screenshot(path=str(screenshot_filename), full_page=True)
            
            if screenshot_filename.exists():
                logger.info(f"[EXITOSO] Screenshot generado exitosamente: {screenshot_filename}")
                logger.info(f"[DATOS] Tamaño: {screenshot_filename.stat().st_size} bytes")
                return True
            else:
                logger.error("[ERROR] Screenshot no se generó")
                return False
            
    except Exception as e:
        logger.error(f"[ERROR] Error en prueba de screenshot: {e}")
        return False
    finally:
        try:
            await browser.close()
        except:
            pass

async def main():
    """Función principal de pruebas"""
    logger.info("🧪 INICIANDO PRUEBAS SIMPLES DE GENERACIÓN DE ARCHIVOS")
    
    tests_passed = 0
    total_tests = 3
    
    # Prueba 1: Generación de PDF
    if await test_pdf_generation():
        tests_passed += 1
        logger.info("[EXITOSO] PRUEBA PDF: PASADA")
    else:
        logger.error("[ERROR] PRUEBA PDF: FALLIDA")
    
    print("\n" + "="*50)
    
    # Prueba 2: Generación de JSON
    if await test_json_generation():
        tests_passed += 1
        logger.info("[EXITOSO] PRUEBA JSON: PASADA")
    else:
        logger.error("[ERROR] PRUEBA JSON: FALLIDA")
    
    print("\n" + "="*50)
    
    # Prueba 3: Generación de Screenshot
    if await test_screenshot_generation():
        tests_passed += 1
        logger.info("[EXITOSO] PRUEBA SCREENSHOT: PASADA")
    else:
        logger.error("[ERROR] PRUEBA SCREENSHOT: FALLIDA")
    
    print("\n" + "="*60)
    logger.info(f"[EMOJI_REMOVIDO] RESULTADOS: {tests_passed}/{total_tests} pruebas pasadas")
    
    if tests_passed == total_tests:
        logger.info("[COMPLETADO] TODAS LAS PRUEBAS PASARON - GENERACIÓN DE ARCHIVOS FUNCIONA")
        logger.info("[INFO] El problema puede estar en la lógica del procesador PQR")
    else:
        logger.error("[ERROR] ALGUNAS PRUEBAS FALLARON - PROBLEMA EN GENERACIÓN DE ARCHIVOS")
    
    return tests_passed == total_tests

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
