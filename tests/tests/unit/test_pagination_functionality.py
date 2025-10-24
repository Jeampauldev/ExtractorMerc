"""
PRUEBA DE PAGINACIÓN AUTOMÁTICA - AFINIA
Valida que el sistema puede detectar y navegar entre páginas automáticamente
"""

import os
import asyncio
import logging
from pathlib import Path

# Configurar logging detallado
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test.pagination')

from src.config.env_loader import get_afinia_credentials, load_environment
from src.core.browser_manager import BrowserManager
from src.core.authentication import AuthenticationManager
from src.components.afinia_pqr_processor import AfiniaPQRProcessor

async def test_pagination_detection():
    """Test para validar detección de paginación"""
    logger.info("🧪 === PRUEBA DE DETECCIÓN DE PAGINACIÓN ===")
    
    try:
        # Configurar navegador
        browser_manager = BrowserManager(
            headless=False,  # Visual para poder ver qué pasa
            viewport={'width': 1920, 'height': 1080},
            timeout=90000
        )
        
        await browser_manager.setup_browser()
        page = browser_manager.page
        
        # Autenticación
        load_environment()
        creds = get_afinia_credentials()
        auth_manager = AuthenticationManager(page, Path("screenshots"))
        
        # Navegar a login
        logger.info("[EMOJI_REMOVIDO] Navegando a login...")
        await page.goto("https://caribemar.facture.co/login")
        await page.wait_for_load_state('networkidle')
        
        logger.info("[EMOJI_REMOVIDO] Autenticando...")
        login_success = await auth_manager.login(
            username=creds['username'],
            password=creds['password']
        )
        
        if not login_success:
            logger.error("[ERROR] Error en autenticación")
            return
            
        # Navegar a PQR
        logger.info("[EMOJI_REMOVIDO] Navegando a PQR...")
        await page.goto("https://caribemar.facture.co/Listado-Radicaci%C3%B3n-PQR#/Detail")
        await page.wait_for_load_state('networkidle')
        
        # Inicializar procesador
        base_dir = Path(__file__).parent / "m_downloads_13" / "afinia" / "oficina_virtual"
        pqr_processor = AfiniaPQRProcessor(
            page=page,
            download_path=str(base_dir),
            screenshots_dir=str(base_dir / "screenshots")
        )
        
        # **AHORA PROBAMOS LA PAGINACIÓN**
        logger.info("[ARCHIVO] === INICIANDO PRUEBA DE PAGINACIÓN AUTOMÁTICA ===")
        
        # 1. Probar detección de información de paginación
        start_num, end_num, total_records = await pqr_processor.pagination_manager.extract_pagination_info(page)
        logger.info(f"[DATOS] Información de paginación detectada:")
        logger.info(f"   [METRICAS] Rango: {start_num} - {end_num}")
        logger.info(f"   [EMOJI_REMOVIDO] Total registros: {total_records:,}")
        
        # 2. Probar detección de botón "Next"
        has_next = await pqr_processor.pagination_manager.has_next_page(page)
        logger.info(f"[EMOJI_REMOVIDO] ¿Hay página siguiente?: {has_next}")
        
        # 3. **Procesar con paginación activada** (solo 2 registros para prueba rápida)
        logger.info("[INICIANDO] Ejecutando procesamiento CON PAGINACIÓN AUTOMÁTICA...")
        logger.info("[ADVERTENCIA]  Procesaremos solo 2 registros por página para la prueba")
        
        total_processed = await pqr_processor.process_all_pqr_records(
            max_records=2,  # Solo 2 por página para prueba rápida
            enable_pagination=True  # [EMOJI_REMOVIDO] ¡ACTIVAR PAGINACIÓN!
        )
        
        logger.info(f"[COMPLETADO] Prueba completada - Total procesados: {total_processed}")
        
    except Exception as e:
        logger.error(f"[ERROR] Error en prueba: {e}")
        
    finally:
        try:
            await browser_manager.cleanup()
        except:
            pass

async def main():
    """Ejecutar prueba de paginación"""
    logger.info("[RESULTADO] PRUEBA: Validar funcionamiento de paginación automática")
    logger.info("[INFO] Esta prueba procesará 2 registros por página y continuará a la siguiente")
    
    await test_pagination_detection()

if __name__ == "__main__":
    asyncio.run(main())