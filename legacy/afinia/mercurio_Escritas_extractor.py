#!/usr/bin/env python3
"""
Script para extraer PQR escritas de Mercurio usando Playwright.
Navega directamente al enlace específico de PQR escritas después del login.
Basado en mercurio_playwright.py pero adaptado para PQR escritas.
"""

import time
import logging
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
from functools import wraps
from dotenv import load_dotenv
import sys
# Agregar directorios al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'config'))

from metrics.metrics_logger import create_metrics_logger
try:
    from config import reports_pipeline
except ImportError:
    # Configuración por defecto si no se puede importar
    reports_pipeline = {
        "afinia": {
            "pqr_escritas_pendientes": {"id_consulta": "00000015"},
            "verbales_pendientes": {"id_consulta": "00000066"}
        }
    }

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar sistema de métricas globalmente
metrics = create_metrics_logger('afinia_pqr_escritas')

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
    """Configura el navegador Playwright con opciones optimizadas"""
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
        logger.info("Navegador Playwright configurado exitosamente")
        return playwright, browser, context, page
    except Exception as e:
        logger.error(f"Error configurando navegador: {e}")
        raise

@performance_monitor
def login_to_mercurio(page, username, password):
    """Realiza login en Mercurio"""
    try:
        logger.info("Iniciando proceso de login")
        page.goto("https://serviciospqrs.afinia.com.co/mercurio/")
        
        # Manejar posibles alertas de sesión activa
        page.on("dialog", lambda dialog: dialog.accept())
        
        # Screenshot inicial solo para debugging de errores
        page.screenshot(path="downloads/afinia/pqr_escritas/login_page_initial_afinia.png")
        logger.info("Screenshot inicial Afinia guardado")
        
        # Esperar a que cargue la página de login y establecer zoom inicial
        page.wait_for_selector("input[name='usuario']", timeout=10000)
        page.evaluate("document.body.style.zoom = '1.0'")
        
        # Buscar todos los campos de entrada disponibles
        all_inputs = page.query_selector_all("input")
        logger.info(f"Encontrados {len(all_inputs)} campos de entrada")
        
        for i, input_elem in enumerate(all_inputs):
            input_type = input_elem.get_attribute("type") or "text"
            input_name = input_elem.get_attribute("name") or "sin_nombre"
            logger.info(f"Campo {i+1}: tipo='{input_type}', nombre='{input_name}'")
        
        # Llenar credenciales con tiempos optimizados
        username_filled = False
        password_filled = False
        
        # Estrategia 1: Por nombre de campo (tiempo reducido)
        try:
            page.fill("input[name='usuario']", username)
            username_filled = True
            logger.info("Usuario llenado por nombre")
        except:
            # Estrategia 2: Por índice
            try:
                page.fill("input:nth-of-type(1)", username)
                username_filled = True
                logger.info("Usuario llenado por índice")
            except:
                pass
        
        page.wait_for_timeout(100)  # Optimizado: reducido de 200ms a 100ms
        
        # Llenar contraseña (tiempo reducido)
        try:
            # Estrategia 1: Por nombre
            page.fill("input[name='clave']", password)
            password_filled = True
            logger.info("Contraseña llenada por nombre")
        except:
            try:
                # Estrategia 2: Por tipo password
                page.fill("input[type='password']", password)
                password_filled = True
                logger.info("Contraseña llenada por tipo")
            except:
                try:
                    # Estrategia 3: Por índice
                    page.fill("input:nth-of-type(2)", password)
                    password_filled = True
                    logger.info("Contraseña llenada por índice")
                except:
                    pass
        
        # Validar que los campos se llenaron correctamente
        if not username_filled or not password_filled:
            logger.error(f"Credenciales no completadas - Usuario: {username_filled}, Contraseña: {password_filled}")
            return False
        
        # Verificar que los valores se guardaron correctamente
        try:
            username_value = page.input_value("input[name='usuario']") or page.input_value("input:nth-of-type(1)")
            password_value = page.input_value("input[type='password']") or page.input_value("input:nth-of-type(2)")
            if not username_value or not password_value:
                logger.warning("Campos parecen vacíos después del llenado")
        except:
            pass
        
        page.wait_for_timeout(100)  # Optimizado: reducido de 200ms a 100ms
        
        # Screenshot con credenciales (esencial para debugging)
        page.screenshot(path="downloads/afinia/pqr_escritas/login_page_filled_afinia.png")
        logger.info("Screenshot con credenciales Afinia guardado")
        
        # Buscar y hacer clic en el botón de login con múltiples estrategias
        login_success = False
        
        # Lista de selectores para el botón de login
        login_selectors = [
            "input[type='submit'][value='Ingresar']",
            "input[type='submit']",
            "input[type='button']",
            "button[type='submit']",
            "button",
            "input[name='Submit']",
            "*:has-text('Ingresar')",
            "*:has-text('Login')",
            "*:has-text('Entrar')"
        ]
        
        for selector in login_selectors:
            try:
                logger.info(f"Intentando selector: {selector}")
                login_button = page.wait_for_selector(selector, timeout=3000)
                if login_button:
                    logger.info(f"Botón encontrado con selector: {selector}")
                    login_button.click()
                    logger.info("Botón de login presionado")
                    login_success = True
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} falló: {str(e)}")
                continue
        
        if not login_success:
            # Último intento: buscar todos los botones y hacer clic en el primero
            try:
                all_buttons = page.query_selector_all("input[type='submit'], input[type='button'], button")
                logger.info(f"Encontrados {len(all_buttons)} botones en total")
                if all_buttons:
                    all_buttons[0].click()
                    logger.info("Clic en primer botón disponible")
                    login_success = True
            except Exception as e:
                logger.error(f"Error en último intento de login: {str(e)}")
        
        if not login_success:
            logger.error("No se pudo encontrar el botón de login")
            return False
        
        # Esperar a que se complete el login usando intelligent wait optimizado
        try:
            page.wait_for_load_state('networkidle', timeout=3000)  # Reducido de 5000ms a 3000ms
        except:
            # Si networkidle falla, usar domcontentloaded como respaldo
            page.wait_for_load_state('domcontentloaded', timeout=2000)
        
        # Manejar posibles alertas de sesión activa
        try:
            page.on("dialog", lambda dialog: dialog.accept())
        except:
            pass
        
        # Verificar si el login fue exitoso con múltiples estrategias
        login_verified = False
        
        # Estrategia 1: Buscar elementos típicos de la página principal
        verification_selectors = [
            "a:has-text('Consultas')",
            "*:has-text('Consultas')",
            "a:has-text('CONSULTAS')",
            "*:has-text('CONSULTAS')",
            "a[href*='consulta']",
            "frame",
            "iframe",
            "table"
        ]
        
        for selector in verification_selectors:
            try:
                logger.info(f"Verificando login con selector: {selector}")
                element = page.wait_for_selector(selector, timeout=8000)
                if element:
                    logger.info(f"Login exitoso - elemento encontrado: {selector}")
                    login_verified = True
                    break
            except Exception as e:
                logger.debug(f"Selector de verificación {selector} falló: {str(e)}")
                continue
        
        # Estrategia 2: Verificar por URL
        if not login_verified:
            current_url = page.url
            logger.info(f"URL actual después del login: {current_url}")
            if "Principal" in current_url or "principal" in current_url or "mercurio" in current_url:
                logger.info("Login exitoso - URL indica página principal")
                login_verified = True
        
        # Estrategia 3: Tomar screenshot y esperar más tiempo
        if not login_verified:
            page.screenshot(path="downloads/afinia/pqr_escritas/post_login_debug_afinia.png")
            logger.info("Screenshot post-login Afinia guardado para debugging")
            page.wait_for_timeout(5000)  # Esperar más tiempo por si la página está cargando
            
            # Intentar una vez más
            try:
                all_links = page.query_selector_all("a")
                logger.info(f"Enlaces encontrados después del login: {len(all_links)}")
                for i, link in enumerate(all_links[:10]):
                    text = link.text_content().strip()
                    if text:
                        logger.info(f"Enlace {i+1}: '{text}'")
                        if "consulta" in text.lower():
                            logger.info("Login exitoso - enlace de consultas encontrado")
                            login_verified = True
                            break
            except Exception as e:
                logger.error(f"Error verificando enlaces: {str(e)}")
        
        if login_verified:
            # Establecer zoom al 100% para evitar problemas de escalado
            page.evaluate("document.body.style.zoom = '1.0'")
            page.evaluate("document.body.style.transform = 'scale(1.0)'")
            page.evaluate("document.body.style.transformOrigin = 'top left'")
            
            logger.info("Login exitoso y zoom configurado")
            return True
        else:
            logger.error("Login falló o página principal no cargó")
            page.screenshot(path="downloads/afinia/pqr_escritas/login_failed_afinia.png")
            return False
        
    except Exception as e:
        logger.error(f"Error en login: {e}")
        page.screenshot(path="downloads/afinia/pqr_escritas/login_exception_afinia.png")
        return False

@performance_monitor
def navigate_to_pqr_escritas_page(page):
    """Navega directamente a la página de PQR escritas usando el enlace específico"""
    try:
        logger.info("Navegando directamente a la página de PQR escritas")
        
        # Obtener ID de consulta desde configuración
        id_consulta = reports_pipeline["afinia"]["pqr_escritas_pendientes"]["id_consulta"]
        
        # URL específica para PQR escritas
        pqr_escritas_url = f"https://serviciospqrs.afinia.com.co/mercurio/servlet/ControllerMercurio?command=consultaEspecial&tipoOperacion=parametros&idCnslta={id_consulta}"
        
        # Navegar a la URL de PQR escritas
        page.goto(pqr_escritas_url)
        logger.info(f"Navegando a: {pqr_escritas_url}")
        
        # Esperar a que la página cargue completamente
        page.wait_for_load_state('networkidle', timeout=10000)
        
        # Screenshot solo para debugging de errores
        # page.screenshot(path="downloads/afinia/pqr_escritas/pqr_escritas_page_loaded_afinia.png")
        # logger.info("Screenshot de página de PQR escritas Afinia guardado")
        
        # Verificar que la página se cargó correctamente
        try:
            # Buscar elementos típicos de la página de PQR escritas
            verification_selectors = [
                "form",
                "input[type='text']",
                "input[type='date']",
                "select",
                "table",
                "*:has-text('Fecha')",
                "*:has-text('Consulta')",
                "*:has-text('Generar')",
                "*:has-text('Excel')",
                "*:has-text('PQR')",
                "*:has-text('Escrita')"
            ]
            
            page_verified = False
            for selector in verification_selectors:
                try:
                    element = page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Página de PQR escritas verificada - elemento encontrado: {selector}")
                        page_verified = True
                        break
                except:
                    continue
            
            if not page_verified:
                logger.warning("No se pudieron encontrar elementos típicos de la página de PQR escritas")
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando página de PQR escritas: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Error navegando a página de PQR escritas: {e}")
        return False

@performance_monitor
def configure_date_range_pqr_escritas(page, start_date="01/08/2025", end_date="03/09/2025"):
    """Configura el rango de fechas para la consulta de PQR escritas"""
    try:
        logger.info(f"Configurando rango de fechas: {start_date} - {end_date}")
        
        # Esperar a que la página esté completamente cargada
        page.wait_for_load_state('domcontentloaded', timeout=3000)
        
        # Screenshot del formulario de fechas (esencial para debugging)
        page.screenshot(path="downloads/afinia/pqr_escritas/formulario_fechas_afinia.png")
        logger.info("Screenshot del formulario de fechas Afinia guardado")
        
        # Estrategia 1: Buscar todos los inputs de texto (como en el script original)
        all_inputs = page.query_selector_all('input')
        logger.info(f"Total de inputs encontrados: {len(all_inputs)}")
        
        # Analizar cada input
        text_inputs = []
        for i, input_elem in enumerate(all_inputs):
            try:
                input_type = input_elem.get_attribute('type') or 'text'
                input_name = input_elem.get_attribute('name') or ''
                input_id = input_elem.get_attribute('id') or ''
                is_visible = input_elem.is_visible()
                
                logger.info(f"Input {i}: tipo='{input_type}', nombre='{input_name}', id='{input_id}', visible={is_visible}")
                
                if input_type == 'text' and is_visible:
                    text_inputs.append(input_elem)
            except Exception as e:
                logger.warning(f"Error analizando input {i}: {str(e)}")
        
        logger.info(f"Inputs de texto visibles encontrados: {len(text_inputs)}")
        
        # Estrategia 2: Llenar campos si encontramos al menos 2
        if len(text_inputs) >= 2:
            try:
                # Llenar fecha desde en el primer campo
                text_inputs[0].click()
                text_inputs[0].fill('')
                page.wait_for_timeout(200)
                text_inputs[0].type(start_date, delay=100)
                logger.info(f"✅ Fecha desde configurada: {start_date}")
                
                # Llenar fecha hasta en el segundo campo
                text_inputs[1].click()
                text_inputs[1].fill('')
                page.wait_for_timeout(200)
                text_inputs[1].type(end_date, delay=100)
                logger.info(f"✅ Fecha hasta configurada: {end_date}")
                
                # Verificar que las fechas se llenaron correctamente
                fecha_desde_value = text_inputs[0].input_value()
                fecha_hasta_value = text_inputs[1].input_value()
                
                logger.info(f"Verificación - Fecha desde: '{fecha_desde_value}'")
                logger.info(f"Verificación - Fecha hasta: '{fecha_hasta_value}'")
                
                # Screenshot solo para debugging de errores
                # page.screenshot(path="downloads/afinia/pqr_escritas/fechas_configuradas_final_afinia.png")
                # logger.info("Screenshot final de fechas configuradas Afinia guardado")
                
                return True
                
            except Exception as fill_error:
                logger.error(f"Error llenando campos de fecha: {str(fill_error)}")
        
        # Estrategia 3: Usar JavaScript directo para llenar campos (como en el script original)
        logger.info("Intentando llenar fechas con JavaScript directo")
        
        js_result = page.evaluate(f"""
            () => {{
                try {{
                    // Buscar todos los inputs de texto
                    const inputs = document.querySelectorAll('input[type="text"], input:not([type])');
                    console.log('Inputs encontrados:', inputs.length);
                    
                    if (inputs.length >= 2) {{
                        // Llenar primer campo (fecha desde)
                        inputs[0].value = '{start_date}';
                        inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inputs[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        // Llenar segundo campo (fecha hasta)
                        inputs[1].value = '{end_date}';
                        inputs[1].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inputs[1].dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        return {{
                            success: true,
                            fechaDesde: inputs[0].value,
                            fechaHasta: inputs[1].value
                        }};
                    }}
                    
                    return {{ success: false, error: 'No se encontraron suficientes campos' }};
                }} catch (error) {{
                    return {{ success: false, error: error.message }};
                }}
            }}
        """)
        
        if js_result and js_result.get('success'):
            logger.info(f"✅ Fechas configuradas con JavaScript - Desde: {js_result.get('fechaDesde')}, Hasta: {js_result.get('fechaHasta')}")
            # page.screenshot(path="downloads/afinia/pqr_escritas/fechas_js_configuradas_afinia.png")
            return True
        else:
            logger.error(f"❌ Error con JavaScript: {js_result.get('error') if js_result else 'Sin resultado'}")
            return False
        
    except Exception as e:
        logger.error(f"Error configurando fechas: {e}")
        page.screenshot(path="downloads/afinia/pqr_escritas/error_fechas_afinia.png")
        return False

def generate_and_download_pqr_escritas(page):
    """Genera y descarga el reporte de PQR escritas"""
    try:
        logger.info("Iniciando generación y descarga de PQR escritas")
        
        # Screenshot solo para debugging de errores
        # page.screenshot(path="downloads/afinia/pqr_escritas/before_generate_afinia.png")
        # logger.info("Screenshot antes de generar Afinia guardado")
        
        # Buscar botón de generar/consultar con múltiples estrategias
        generate_button_found = False
        
        # Selectores optimizados: solo los más específicos y confiables
        generate_selectors = [
            # Selectores específicos para 'Generar en Excel' (más prioritarios)
            "*:has-text('Generar en Excel')",
            "input[value*='Generar en Excel']",
            "input[type='button'][value*='Generar en Excel']",
            # Selectores de respaldo más generales
            "input[type='submit'][value*='Generar']",
            "input[type='button'][value*='Generar']",
            "*:has-text('Generar Excel')",
            # Último recurso: botones genéricos
            "input[type='submit']",
            "input[type='button']"
        ]
        
        # Configurar timeout más largo para descargas
        download_timeout = 30000  # 30 segundos
        
        for selector in generate_selectors:
            try:
                logger.info(f"Buscando botón con selector: {selector}")
                button = page.wait_for_selector(selector, timeout=3000)
                if button:
                    logger.info(f"Botón encontrado con selector: {selector}")
                    
                    # Configurar listener de descarga antes del clic con timeout extendido
                    try:
                        with page.expect_download(timeout=download_timeout) as download_info:
                            button.click()
                            logger.info("Botón de generar presionado")
                            
                            # Esperar un poco para que se procese la solicitud
                            page.wait_for_timeout(2000)
                        
                        # Obtener la descarga
                        download = download_info.value
                        logger.info(f"Descarga iniciada: {download.suggested_filename}")
                        
                        # Procesar la descarga exitosa
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        original_extension = os.path.splitext(download.suggested_filename)[1] if download.suggested_filename else '.xlsx'
                        filename = f"afinia_pqr_escritas_{timestamp}{original_extension}"
                        
                        # Guardar el archivo en carpeta organizada
                        downloads_dir = "downloads/afinia/pqr_escritas"
                        if not os.path.exists(downloads_dir):
                            os.makedirs(downloads_dir)
                        
                        filepath = os.path.join(downloads_dir, filename)
                        download.save_as(filepath)
                        
                        # Registrar descarga en métricas
                        try:
                            file_size = os.path.getsize(filepath)
                            metrics.log_download(filename, file_size)
                        except:
                            metrics.log_download(filename)
                        
                        logger.info(f"PQR escritas descargadas exitosamente: {filepath}")
                        generate_button_found = True
                        break
                        
                    except Exception as download_error:
                        logger.warning(f"Error esperando descarga con {selector}: {str(download_error)}")
                        # Intentar clic simple sin esperar descarga
                        button.click()
                        logger.info("Botón presionado sin esperar descarga")
                        page.wait_for_timeout(5000)  # Esperar 5 segundos
                        continue
                    
            except Exception as e:
                logger.debug(f"Selector {selector} falló: {str(e)}")
                continue
        
        if not generate_button_found:
            logger.error("No se pudo encontrar el botón de generar/descargar")
            
            # Screenshot para debugging de errores
            page.screenshot(path="downloads/afinia/pqr_escritas/generate_button_not_found_afinia.png")
            logger.info("Screenshot de debugging Afinia guardado")
            
            # Intentar buscar todos los botones disponibles
            try:
                all_buttons = page.query_selector_all("input[type='submit'], input[type='button'], button")
                logger.info(f"Botones disponibles en la página: {len(all_buttons)}")
                
                for i, button in enumerate(all_buttons[:5]):
                    value = button.get_attribute("value") or button.text_content() or "sin_texto"
                    logger.info(f"Botón {i+1}: '{value.strip()}'")
                
                # Intentar con el primer botón disponible
                if all_buttons:
                    logger.info("Intentando con el primer botón disponible")
                    try:
                        # Intentar sin esperar descarga primero
                        all_buttons[0].click()
                        logger.info("Primer botón presionado")
                        
                        # Esperar un poco para ver si se inicia descarga
                        page.wait_for_timeout(3000)
                        
                        # Verificar si hay algún archivo nuevo en la carpeta de descargas
                        downloads_dir = "downloads/afinia/pqr_escritas"
                        if not os.path.exists(downloads_dir):
                            os.makedirs(downloads_dir)
                        
                        # Buscar archivos recientes (últimos 30 segundos)
                        import time
                        current_time = time.time()
                        recent_files = []
                        
                        if os.path.exists(downloads_dir):
                             for file in os.listdir(downloads_dir):
                                 file_path = os.path.join(downloads_dir, file)
                                 if os.path.isfile(file_path):
                                     # Solo considerar archivos Excel
                                     if file.lower().endswith(('.xls', '.xlsx')):
                                         file_time = os.path.getmtime(file_path)
                                         if current_time - file_time < 30:  # Archivo creado en los últimos 30 segundos
                                             recent_files.append((file, file_path))
                        
                        if recent_files:
                            # Usar el archivo más reciente
                            recent_files.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
                            filename, filepath = recent_files[0]
                            logger.info(f"Archivo descargado detectado: {filepath}")
                            
                            # Registrar descarga en métricas
                            try:
                                file_size = os.path.getsize(filepath)
                                metrics.log_download(filename, file_size)
                            except:
                                metrics.log_download(filename)
                            
                            logger.info(f"PQR escritas descargadas exitosamente (detección automática): {filepath}")
                            generate_button_found = True
                        else:
                            logger.warning("No se detectaron archivos descargados recientemente")
                        
                        # Si no se detectó archivo, el proceso ya falló arriba
                        # No necesitamos procesar download object aquí
                        
                    except Exception as alt_error:
                        logger.error(f"Error con método alternativo: {str(alt_error)}")
                        
            except Exception as e:
                logger.error(f"Error buscando botones alternativos: {str(e)}")
            
            return False
        
        # Screenshot solo para debugging de errores
        # page.screenshot(path="downloads/afinia/pqr_escritas/after_download_afinia.png")
        # logger.info("Screenshot después de descarga Afinia guardado")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generando y descargando PQR escritas: {e}")
        return False

@performance_monitor
def main():
    """Función principal que ejecuta todo el proceso de extracción de PQR escritas"""
    total_start_time = time.time()
    
    # Obtener credenciales desde configuración
    try:
        from config.config import mercurio
        username = mercurio['afinia']['user_reports']['user']
        password = mercurio['afinia']['user_reports']['password']
    except ImportError:
        # Fallback a variables de entorno si no se puede importar config
        username = os.getenv('AFINIA_USERNAME', '281005131')
        password = os.getenv('AFINIA_PASSWORD', '123')
    
    logging.info(f"Usando credenciales de Afinia para usuario: {username}")
    
    playwright = None
    browser = None
    
    try:
        logger.info("=== INICIANDO EXTRACCIÓN DE PQR ESCRITAS DE MERCURIO ===")
        
        # Registrar inicio de sesión
        session_step = metrics.log_step_start('session', 'Extracción completa de PQR escritas Afinia')
        
        # Configurar navegador
        browser_step = metrics.log_step_start('browser_setup', 'Configuración del navegador Playwright')
        playwright, browser, context, page = setup_browser()
        metrics.log_step_end(browser_step, 'completed')
        
        # Realizar login
        login_step = metrics.log_step_start('login', f'Login con usuario {username}')
        if not login_to_mercurio(page, username, password):
            logger.error("Login falló, abortando proceso")
            metrics.log_step_end(login_step, 'failed')
            metrics.log_error('LoginError', 'Fallo en el proceso de login', 'login')
            return False
        metrics.log_step_end(login_step, 'completed')
        
        # Navegar directamente a página de PQR escritas (optimizado)
        nav_step = metrics.log_step_start('direct_navigation', 'Navegación directa a página de PQR escritas')
        if not navigate_to_pqr_escritas_page(page):
            logger.error("Navegación directa a página de PQR escritas falló")
            metrics.log_step_end(nav_step, 'failed')
            metrics.log_error('NavigationError', 'No se pudo navegar directamente a PQR escritas', 'navigation')
            return False
        metrics.log_step_end(nav_step, 'completed')
        logger.info("✅ Navegación directa a PQR escritas exitosa")
        
        # Configurar fechas
        dates_step = metrics.log_step_start('date_config', 'Configuración de rango de fechas')
        if not configure_date_range_pqr_escritas(page):
            logger.warning("Configuración de fechas falló, continuando con valores por defecto")
            metrics.log_step_end(dates_step, 'failed')
            metrics.log_error('DateConfigError', 'No se pudieron configurar las fechas', 'date_config')
        else:
            logger.info("✅ Configuración de fechas exitosa")
            metrics.log_step_end(dates_step, 'completed')
        
        # Generar y descargar PQR escritas
        download_step = metrics.log_step_start('download', 'Generación y descarga de PQR escritas')
        if not generate_and_download_pqr_escritas(page):
            logger.error("Generación y descarga de PQR escritas falló")
            metrics.log_step_end(download_step, 'failed')
            metrics.log_error('DownloadError', 'Fallo en generación/descarga', 'download')
            return False
        
        metrics.log_step_end(download_step, 'completed')
        logger.info("✅ Descarga de PQR escritas exitosa")
        
        # Calcular tiempo total
        total_end_time = time.time()
        total_execution_time = total_end_time - total_start_time
        
        metrics.log_step_end(download_step, 'completed')
        metrics.log_step_end(session_step, 'completed')
        metrics.log_performance_stat('total_execution_time', total_execution_time)
        metrics.finalize_session('completed')
        
        logger.info(f"🎉 PROCESO COMPLETADO EXITOSAMENTE en {total_execution_time:.2f} segundos")
        
        return True
        
    except Exception as e:
        total_end_time = time.time()
        total_execution_time = total_end_time - total_start_time
        logger.error(f"💥 ERROR EN PROCESO PRINCIPAL después de {total_execution_time:.2f} segundos: {str(e)}")
        metrics.log_error('GeneralError', str(e), 'main')
        metrics.finalize_session('failed')
        return False
        
    finally:
        # Limpiar recursos
        try:
            if browser:
                browser.close()
            if playwright:
                playwright.stop()
            logger.info("Recursos del navegador liberados")
        except Exception as cleanup_error:
            logger.error(f"Error liberando recursos: {str(cleanup_error)}")

if __name__ == "__main__":
    # Crear estructura de directorios organizados
    os.makedirs("downloads/afinia/pqr_escritas", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    success = main()
    if success:
        print("\n✅ Proceso Afinia PQR Escritas completado exitosamente")
        logger.info("✅ Script ejecutado exitosamente")
    else:
        print("\n❌ Proceso Afinia PQR Escritas falló")
        logger.error("❌ Script falló")
        exit(1)