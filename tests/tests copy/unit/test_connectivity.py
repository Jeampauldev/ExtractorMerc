#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de prueba de conectividad para Afinia OV
Verifica si las URLs están accesibles antes de ejecutar el extractor completo
"""

import asyncio
import logging
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def test_url_connectivity(url: str, timeout: int = 30000) -> bool:
    """
    Prueba la conectividad a una URL específica
    
    Args:
        url: URL a probar
        timeout: Timeout en milisegundos
        
    Returns:
        bool: True si la URL es accesible
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            logger.info(f"[EMOJI_REMOVIDO] Probando conectividad a: {url}")
            logger.info(f"[TIEMPO] Timeout configurado: {timeout}ms")
            
            response = await page.goto(url, timeout=timeout, wait_until='domcontentloaded')
            
            if response:
                status = response.status
                logger.info(f"[EXITOSO] Respuesta recibida - Status: {status}")
                
                if status == 200:
                    logger.info("[EXITOSO] URL accesible correctamente")
                    
                    # Verificar si hay contenido de login
                    title = await page.title()
                    logger.info(f"[ARCHIVO] Título de la página: {title}")
                    
                    # Buscar elementos de login comunes
                    login_elements = await page.query_selector_all('input[type="text"], input[type="password"], input[name*="user"], input[name*="pass"]')
                    logger.info(f"[EMOJI_REMOVIDO] Elementos de login encontrados: {len(login_elements)}")
                    
                    await browser.close()
                    return True
                else:
                    logger.warning(f"[ADVERTENCIA] Status HTTP no exitoso: {status}")
                    await browser.close()
                    return False
            else:
                logger.error("[ERROR] No se recibió respuesta")
                await browser.close()
                return False
                
    except Exception as e:
        logger.error(f"[ERROR] Error probando conectividad: {e}")
        return False

async def main():
    """Función principal de prueba"""
    logger.info("=== PRUEBA DE CONECTIVIDAD AFINIA OV ===")
    
    # URLs a probar
    urls_to_test = [
        "https://caribemar.facture.co/",
        "https://caribemar.facture.co/login",
        "https://oficinavirtual.afinia.com.co/",
        "https://oficinavirtual.afinia.com.co/login"
    ]
    
    results = {}
    
    for url in urls_to_test:
        logger.info(f"\n{'='*60}")
        result = await test_url_connectivity(url, timeout=90000)  # 90 segundos
        results[url] = result
        
        if result:
            logger.info(f"[EXITOSO] {url} - ACCESIBLE")
        else:
            logger.error(f"[ERROR] {url} - NO ACCESIBLE")
    
    # Resumen final
    logger.info(f"\n{'='*60}")
    logger.info("[DATOS] RESUMEN DE CONECTIVIDAD:")
    
    accessible_urls = [url for url, accessible in results.items() if accessible]
    
    if accessible_urls:
        logger.info("[EXITOSO] URLs accesibles:")
        for url in accessible_urls:
            logger.info(f"  - {url}")
    else:
        logger.error("[ERROR] Ninguna URL es accesible")
    
    non_accessible_urls = [url for url, accessible in results.items() if not accessible]
    if non_accessible_urls:
        logger.warning("[ADVERTENCIA] URLs no accesibles:")
        for url in non_accessible_urls:
            logger.warning(f"  - {url}")
    
    # Recomendaciones
    logger.info(f"\n{'='*60}")
    logger.info("[INFO] RECOMENDACIONES:")
    
    if accessible_urls:
        recommended_url = accessible_urls[0]
        logger.info(f"[EXITOSO] Usar esta URL en la configuración: {recommended_url}")
        logger.info("[EXITOSO] Las correcciones de timeout deberían funcionar")
    else:
        logger.error("[ERROR] Verificar conexión a internet")
        logger.error("[ERROR] Verificar si las URLs han cambiado")
        logger.error("[ERROR] Verificar firewall/proxy corporativo")

if __name__ == '__main__':
    asyncio.run(main())
