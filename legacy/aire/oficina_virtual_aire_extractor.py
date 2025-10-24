#!/usr/bin/env python3
"""
Extractor para Oficina Virtual de Aire
======================================

Script para extraer reportes de PQR desde la Oficina Virtual de Aire usando Playwright.
Implementa el flujo específico:
1. Login en https://caribesol.facture.co/
2. Navegación a LISTADO RADICACIÓN PQR
3. Configuración de filtros (estado: finalizado, fechas: ayer-hoy)
4. Descarga de reportes

Adaptado específicamente para la plataforma de Oficina Virtual de Aire.
"""

import time
import logging
import os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from functools import wraps
import sys

# Agregar paths para importaciones
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from metrics.metrics_logger import create_metrics_logger
from config.config import OFICINA_VIRTUAL_AIRE

# Configurar logging específico para Oficina Virtual Aire
logging.basicConfig(
    level=logging.INFO,
    format='[OV-AIRE %(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar sistema de métricas
metrics = create_metrics_logger('oficina_virtual_aire')

# Performance monitoring decorator
def performance_monitor(func):
    """Decorator para medir tiempos de ejecución de funciones"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"🚀 Iniciando {func.__name__}")
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"✅ {func.__name__} completado en {execution_time:.2f} segundos")
            return result
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(f"❌ {func.__name__} falló después de {execution_time:.2f} segundos: {str(e)}")
            raise
    return wrapper

def setup_browser():
    """Configura el navegador Playwright con opciones optimizadas para Oficina Virtual"""
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--start-maximized",
                "--force-device-scale-factor=1",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection"
            ]
        )
        context = browser.new_context(
            viewport={'width': 1366, 'height': 768},
            device_scale_factor=1.0,
            accept_downloads=True,
            ignore_https_errors=True
        )
        page = context.new_page()
        logger.info("Navegador Playwright configurado exitosamente para Oficina Virtual Aire")
        return playwright, browser, context, page
    except Exception as e:
        logger.error(f"Error configurando navegador: {e}")
        raise

@performance_monitor
def login_to_oficina_virtual_aire(page):
    """Realiza login en Oficina Virtual Aire"""
    try:
        logger.info("Iniciando proceso de login en Oficina Virtual Aire")
        
        # Navegar a la URL de Oficina Virtual Aire
        page.goto(OFICINA_VIRTUAL_AIRE["url"])
        
        # Manejar posibles alertas
        page.on("dialog", lambda dialog: dialog.accept())
        
        # Tomar screenshot inicial
        os.makedirs("downloads/aire", exist_ok=True)
        page.screenshot(path="downloads/aire/ov_login_page_initial_aire.png")
        
        # Esperar a que la página cargue completamente
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Buscar campos de login (pueden tener diferentes selectores)
        username_selectors = [
            'input[name="username"]',
            'input[name="email"]',
            'input[type="email"]',
            'input[placeholder*="usuario"]',
            'input[placeholder*="Usuario"]',
            'input[placeholder*="email"]',
            '#username',
            '#email',
            '.username',
            '.email'
        ]
        
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[placeholder*="contraseña"]',
            'input[placeholder*="Contraseña"]',
            '#password',
            '.password'
        ]
        
        # Intentar encontrar campo de usuario
        username_field = None
        for selector in username_selectors:
            try:
                username_field = page.wait_for_selector(selector, timeout=3000)
                if username_field:
                    logger.info(f"Campo de usuario encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                continue
        
        if not username_field:
            raise Exception("No se pudo encontrar el campo de usuario")
        
        # Intentar encontrar campo de contraseña
        password_field = None
        for selector in password_selectors:
            try:
                password_field = page.wait_for_selector(selector, timeout=3000)
                if password_field:
                    logger.info(f"Campo de contraseña encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                continue
        
        if not password_field:
            raise Exception("No se pudo encontrar el campo de contraseña")
        
        # Llenar credenciales
        username_field.fill(OFICINA_VIRTUAL_AIRE["username"])
        password_field.fill(OFICINA_VIRTUAL_AIRE["password"])
        
        # Tomar screenshot después de llenar credenciales
        page.screenshot(path="downloads/aire/ov_login_page_filled_aire.png")
        
        # Buscar y hacer clic en botón de login
        login_button_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Ingresar")',
            'button:has-text("Login")',
            'button:has-text("Entrar")',
            '.btn-login',
            '#login-button',
            '.login-button'
        ]
        
        login_button = None
        for selector in login_button_selectors:
            try:
                login_button = page.wait_for_selector(selector, timeout=3000)
                if login_button:
                    logger.info(f"Botón de login encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                continue
        
        if not login_button:
            raise Exception("No se pudo encontrar el botón de login")
        
        # Hacer clic en login
        login_button.click()
        
        # Esperar a que se complete el login
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # Verificar si el login fue exitoso
        current_url = page.url
        logger.info(f"URL después del login: {current_url}")
        
        # Tomar screenshot después del login
        page.screenshot(path="downloads/aire/ov_after_login_aire.png")
        
        logger.info("✅ Login exitoso en Oficina Virtual Aire")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en login: {str(e)}")
        page.screenshot(path="downloads/aire/ov_login_error_aire.png")
        raise

@performance_monitor
def navigate_to_listado_radicacion_pqr(page):
    """Navega a la sección LISTADO RADICACIÓN PQR"""
    try:
        logger.info("Navegando a LISTADO RADICACIÓN PQR")
        
        # Buscar el enlace o botón de LISTADO RADICACIÓN PQR en el menú lateral izquierdo
        menu_selectors = [
            'a:has-text("LISTADO RADICACIÓN PQR")',
            'button:has-text("LISTADO RADICACIÓN PQR")',
            'li:has-text("LISTADO RADICACIÓN PQR")',
            '[data-menu="listado-radicacion-pqr"]',
            '.menu-item:has-text("LISTADO")',
            '.sidebar a:has-text("LISTADO")',
            '.nav-link:has-text("LISTADO")',
            'a[href*="listado"]',
            'a[href*="radicacion"]',
            'a[href*="pqr"]'
        ]
        
        menu_item = None
        for selector in menu_selectors:
            try:
                menu_item = page.wait_for_selector(selector, timeout=5000)
                if menu_item:
                    logger.info(f"Menú LISTADO RADICACIÓN PQR encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                continue
        
        if not menu_item:
            # Si no encontramos el menú específico, buscar en toda la página
            logger.warning("No se encontró el menú específico, buscando en toda la página")
            page.screenshot(path="downloads/aire/ov_menu_search_aire.png")
            
            # Intentar hacer clic en cualquier elemento que contenga "LISTADO" o "PQR"
            try:
                page.click('text="LISTADO"', timeout=5000)
            except:
                try:
                    page.click('text="PQR"', timeout=5000)
                except:
                    raise Exception("No se pudo encontrar la sección LISTADO RADICACIÓN PQR")
        else:
            menu_item.click()
        
        # Esperar a que cargue la nueva página
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # Tomar screenshot de la página de listado
        page.screenshot(path="downloads/aire/ov_listado_pqr_page_aire.png")
        
        logger.info("✅ Navegación exitosa a LISTADO RADICACIÓN PQR")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error navegando a LISTADO RADICACIÓN PQR: {str(e)}")
        page.screenshot(path="downloads/aire/ov_navigation_error_aire.png")
        raise

@performance_monitor
def configure_filters(page):
    """Configura los filtros: estado=finalizado, fechas=ayer a hoy"""
    try:
        logger.info("Configurando filtros de búsqueda")
        
        # Calcular fechas (ayer y hoy)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        fecha_inicial = yesterday.strftime("%d/%m/%Y")
        fecha_final = today.strftime("%d/%m/%Y")
        
        logger.info(f"Configurando fechas: {fecha_inicial} - {fecha_final}")
        
        # 1. Configurar filtro de estado a "finalizado"
        estado_selectors = [
            'select[name="estado"]',
            'select[name="status"]',
            'select:has(option:text("finalizado"))',
            'select:has(option:text("Finalizado"))',
            '.estado-select',
            '#estado',
            '#status'
        ]
        
        estado_dropdown = None
        for selector in estado_selectors:
            try:
                estado_dropdown = page.wait_for_selector(selector, timeout=5000)
                if estado_dropdown:
                    logger.info(f"Dropdown de estado encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                continue
        
        if estado_dropdown:
            # Seleccionar "finalizado"
            try:
                page.select_option(estado_dropdown, label="finalizado")
            except:
                try:
                    page.select_option(estado_dropdown, label="Finalizado")
                except:
                    try:
                        page.select_option(estado_dropdown, value="finalizado")
                    except:
                        logger.warning("No se pudo seleccionar 'finalizado' en el dropdown de estado")
        else:
            logger.warning("No se encontró el dropdown de estado")
        
        # 2. Configurar fecha inicial
        fecha_inicial_selectors = [
            'input[name="fecha_inicial"]',
            'input[name="fechaInicial"]',
            'input[name="fecha_inicio"]',
            'input[name="start_date"]',
            'input[type="date"]:first-of-type',
            '.fecha-inicial',
            '#fecha_inicial',
            '#fechaInicial'
        ]
        
        fecha_inicial_field = None
        for selector in fecha_inicial_selectors:
            try:
                fecha_inicial_field = page.wait_for_selector(selector, timeout=3000)
                if fecha_inicial_field:
                    logger.info(f"Campo fecha inicial encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                continue
        
        if fecha_inicial_field:
            fecha_inicial_field.fill(fecha_inicial)
        else:
            logger.warning("No se encontró el campo de fecha inicial")
        
        # 3. Configurar fecha final
        fecha_final_selectors = [
            'input[name="fecha_final"]',
            'input[name="fechaFinal"]',
            'input[name="fecha_fin"]',
            'input[name="end_date"]',
            'input[type="date"]:last-of-type',
            '.fecha-final',
            '#fecha_final',
            '#fechaFinal'
        ]
        
        fecha_final_field = None
        for selector in fecha_final_selectors:
            try:
                fecha_final_field = page.wait_for_selector(selector, timeout=3000)
                if fecha_final_field:
                    logger.info(f"Campo fecha final encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                continue
        
        if fecha_final_field:
            fecha_final_field.fill(fecha_final)
        else:
            logger.warning("No se encontró el campo de fecha final")
        
        # Tomar screenshot después de configurar filtros
        page.screenshot(path="downloads/aire/ov_filters_configured_aire.png")
        
        # 4. Aplicar filtros (buscar botón de búsqueda/filtrar)
        search_button_selectors = [
            'button[type="submit"]',
            'button:has-text("Buscar")',
            'button:has-text("Filtrar")',
            'button:has-text("Consultar")',
            'input[type="submit"]',
            '.btn-search',
            '.btn-filter',
            '#search-button',
            '#filter-button'
        ]
        
        search_button = None
        for selector in search_button_selectors:
            try:
                search_button = page.wait_for_selector(selector, timeout=3000)
                if search_button:
                    logger.info(f"Botón de búsqueda encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                continue
        
        if search_button:
            search_button.click()
            page.wait_for_load_state("networkidle")
            time.sleep(3)
        else:
            logger.warning("No se encontró botón de búsqueda, los filtros pueden aplicarse automáticamente")
        
        # Tomar screenshot después de aplicar filtros
        page.screenshot(path="downloads/aire/ov_results_after_filter_aire.png")
        
        logger.info("✅ Filtros configurados exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error configurando filtros: {str(e)}")
        page.screenshot(path="downloads/aire/ov_filter_error_aire.png")
        raise

@performance_monitor
def download_report(page):
    """Descarga el reporte de PQR"""
    try:
        logger.info("Iniciando descarga de reporte")
        
        # Buscar botón de descarga/exportar
        download_selectors = [
            'button:has-text("Descargar")',
            'button:has-text("Exportar")',
            'button:has-text("Excel")',
            'a:has-text("Descargar")',
            'a:has-text("Exportar")',
            '.btn-download',
            '.btn-export',
            '#download-button',
            '#export-button',
            'button[title*="descargar"]',
            'button[title*="exportar"]'
        ]
        
        download_button = None
        for selector in download_selectors:
            try:
                download_button = page.wait_for_selector(selector, timeout=5000)
                if download_button:
                    logger.info(f"Botón de descarga encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                continue
        
        if not download_button:
            raise Exception("No se pudo encontrar el botón de descarga")
        
        # Configurar listener para descarga
        download_info = None
        
        def handle_download(download):
            nonlocal download_info
            download_info = download
            logger.info(f"Descarga iniciada: {download.suggested_filename}")
        
        page.on("download", handle_download)
        
        # Hacer clic en descargar
        download_button.click()
        
        # Esperar a que inicie la descarga
        time.sleep(5)
        
        if download_info:
            # Generar nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aire_ov_pqr_finalizado_{timestamp}.xlsx"
            filepath = os.path.join("downloads", "aire", filename)
            
            # Guardar archivo
            download_info.save_as(filepath)
            logger.info(f"✅ Archivo descargado exitosamente: {filepath}")
            
            # Registrar métricas
            metrics.log_download_success({
                'company': 'aire',
                'report_type': 'pqr_finalizado',
                'filename': filename,
                'filepath': filepath,
                'timestamp': timestamp
            })
            
            return filepath
        else:
            raise Exception("No se detectó ninguna descarga")
        
    except Exception as e:
        logger.error(f"❌ Error en descarga: {str(e)}")
        page.screenshot(path="downloads/aire/ov_download_error_aire.png")
        metrics.log_error({
            'function': 'download_report',
            'error': str(e),
            'company': 'aire'
        })
        raise

def main():
    """Función principal del extractor de Oficina Virtual Aire"""
    playwright = None
    browser = None
    
    try:
        logger.info("🚀 Iniciando Extractor de Oficina Virtual Aire")
        
        # Configurar navegador
        playwright, browser, context, page = setup_browser()
        
        # Ejecutar flujo completo
        login_to_oficina_virtual_aire(page)
        navigate_to_listado_radicacion_pqr(page)
        configure_filters(page)
        filepath = download_report(page)
        
        logger.info(f"🎉 Extracción completada exitosamente. Archivo: {filepath}")
        
        # Registrar métricas finales
        metrics.log_extraction_complete({
            'company': 'aire',
            'status': 'success',
            'file_path': filepath
        })
        
        return filepath
        
    except Exception as e:
        logger.error(f"💥 Error en extracción: {str(e)}")
        metrics.log_error('main_execution_error', str(e), 'main')
        raise
    
    finally:
        # Limpiar recursos
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
        logger.info("🧹 Recursos liberados")

if __name__ == "__main__":
    main()