#!/usr/bin/env python3
"""
Extractor para Oficina Virtual de Afinia - Nueva Versión
======================================================

Script para extraer reportes de PQR desde la nueva Oficina Virtual de Afinia usando Playwright.
Esta versión está adaptada para la nueva interfaz web de Afinia.

Desarrollo paso a paso:
1. Configuración inicial del navegador
2. Navegación a la nueva URL
3. Análisis de la nueva estructura de login
4. Implementación del proceso de autenticación
5. Navegación a sección de reportes
6. Configuración de filtros
7. Descarga de reportes

Adaptado específicamente para la nueva plataforma de Oficina Virtual de Afinia.
"""

import time
import logging
import os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from functools import wraps
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
project_root = Path(__file__).parent.parent.parent
env_file = project_root / "env" / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=str(env_file), override=True)
    print(f"✅ Variables de entorno cargadas desde: {env_file}")
else:
    print(f"❌ No se encontró archivo .env en: {env_file}")

# Agregar paths para importaciones
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from metrics.metrics_logger import create_metrics_logger
from config.config import OFICINA_VIRTUAL_AFINIA

# Configurar logging específico para Nueva Oficina Virtual Afinia
logging.basicConfig(
    level=logging.INFO,
    format='[NEW-OV-AFINIA %(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar sistema de métricas
metrics = create_metrics_logger('nueva_oficina_virtual_afinia')

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
    """Configura el navegador Playwright optimizado para la nueva Oficina Virtual"""
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=False,  # Mantener visible para desarrollo paso a paso
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--start-maximized",
                "--force-device-scale-factor=1",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--disable-web-security",  # Para desarrollo
                "--allow-running-insecure-content"
            ]
        )
        context = browser.new_context(
            viewport={'width': 1366, 'height': 768},  # Mismo viewport que extractores exitosos
            device_scale_factor=1.0,
            accept_downloads=True,
            ignore_https_errors=True
        )
        page = context.new_page()
        
        # Configurar timeouts más largos para desarrollo
        page.set_default_timeout(60000)
        
        logger.info("Navegador Playwright configurado exitosamente para Nueva Oficina Virtual Afinia")
        return playwright, browser, context, page
    except Exception as e:
        logger.error(f"Error configurando navegador: {e}")
        raise

@performance_monitor
def navigate_to_new_afinia_portal(page):
    """Navega a la nueva URL de Oficina Virtual Afinia y analiza la estructura"""
    try:
        logger.info("=== PASO 1: Navegando a la nueva Oficina Virtual de Afinia ===")
        
        # URL base de la oficina virtual de Afinia - usar la página de login directamente
        base_url = "https://caribemar.facture.co/"
        login_url = "https://caribemar.facture.co/login"
        
        # Intentar primero la página de login directamente
        url = login_url
        logger.info(f"Navegando a página de login: {url}")
        
        # Crear directorio para screenshots de desarrollo
        os.makedirs("downloads/afinia/new_version", exist_ok=True)
        
        # Navegar con manejo de errores mejorado
        try:
            page.goto(url, timeout=90000, wait_until="domcontentloaded")
            logger.info("✅ Navegación inicial exitosa")
        except Exception as e:
            logger.warning(f"Error en navegación inicial: {e}")
            # Intentar con networkidle como fallback
            page.goto(url, timeout=90000, wait_until="networkidle")
        
        # Esperar a que la página cargue completamente
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # Tomar screenshot inicial para análisis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=f"downloads/afinia/new_version/step1_initial_page_{timestamp}.png")
        
        # Guardar HTML de la página para análisis
        html_content = page.content()
        with open(f"downloads/afinia/new_version/step1_page_source_{timestamp}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Analizar la estructura de la página
        logger.info("=== Analizando estructura de la nueva página ===")
        
        # Verificar título de la página
        title = page.title()
        logger.info(f"Título de la página: {title}")
        
        # Verificar URL actual
        current_url = page.url
        logger.info(f"URL actual: {current_url}")
        
        # Buscar elementos de login en la nueva estructura
        logger.info("Buscando elementos de login...")
        
        # Buscar campos de entrada (input)
        inputs = page.query_selector_all("input")
        logger.info(f"Encontrados {len(inputs)} campos de entrada")
        
        for i, input_elem in enumerate(inputs[:10]):  # Limitar a los primeros 10
            try:
                input_type = input_elem.get_attribute("type") or "text"
                input_name = input_elem.get_attribute("name") or "sin_nombre"
                input_id = input_elem.get_attribute("id") or "sin_id"
                input_placeholder = input_elem.get_attribute("placeholder") or "sin_placeholder"
                logger.info(f"  Input {i+1}: type='{input_type}', name='{input_name}', id='{input_id}', placeholder='{input_placeholder}'")
            except Exception as e:
                logger.warning(f"Error analizando input {i+1}: {e}")
        
        # Buscar botones
        buttons = page.query_selector_all("button")
        logger.info(f"Encontrados {len(buttons)} botones")
        
        for i, button in enumerate(buttons[:10]):  # Limitar a los primeros 10
            try:
                button_text = button.inner_text().strip()
                button_type = button.get_attribute("type") or "button"
                button_class = button.get_attribute("class") or "sin_clase"
                if button_text:
                    logger.info(f"  Botón {i+1}: texto='{button_text}', type='{button_type}', class='{button_class}'")
            except Exception as e:
                logger.warning(f"Error analizando botón {i+1}: {e}")
        
        # Buscar formularios
        forms = page.query_selector_all("form")
        logger.info(f"Encontrados {len(forms)} formularios")
        
        # Buscar enlaces importantes
        links = page.query_selector_all("a")
        logger.info(f"Encontrados {len(links)} enlaces")
        
        important_links = []
        for link in links[:20]:  # Limitar a los primeros 20
            try:
                link_text = link.inner_text().strip()
                link_href = link.get_attribute("href")
                if link_text and any(keyword in link_text.lower() for keyword in ["login", "ingresar", "entrar", "acceso", "iniciar"]):
                    important_links.append({"text": link_text, "href": link_href})
            except:
                continue
        
        if important_links:
            logger.info("Enlaces importantes encontrados:")
            for link in important_links:
                logger.info(f"  - '{link['text']}' -> {link['href']}")
        
        logger.info("✅ Análisis inicial completado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en navegación inicial: {str(e)}")
        page.screenshot(path=f"downloads/afinia/new_version/step1_error_{timestamp}.png")
        raise

@performance_monitor
def perform_login(page):
    """Realiza el login en la nueva Oficina Virtual de Afinia"""
    try:
        logger.info("=== PASO 2: Realizando login en Nueva Oficina Virtual ===")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Manejar popup inicial específico de Afinia ANTES del login
        # Basado en el análisis del HTML del popup
        logger.info("🔍 Verificando si existe popup inicial...")
        
        # Esperar a que la página cargue completamente
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        
        # Selectores específicos basados en el HTML del popup de Afinia
        popup_selectors = [
            '#myModal a.closePopUp i[ng-click="closeDialog()"]',  # Selector más específico del botón de cierre
            '#myModal i.material-icons[ng-click="closeDialog()"]',  # Icono con ng-click
            'a.closePopUp i.material-icons',  # Contenedor del botón de cierre
            '#myModal .closePopUp',  # Enlace contenedor
            'i[ng-click="closeDialog()"]',  # Selector directo del ng-click
            '.modal-content i.material-icons:has-text("close")',  # Por el texto "close"
            '#myModal.modal[style*="display: block"] i.material-icons',  # Modal visible con icono
            'div[id="myModal"] a.closePopUp',  # Contenedor específico del modal
            '.closePopUp[style*="cursor: pointer"]'  # Por el estilo cursor pointer
        ]
        
        popup_closed = False
        attempts = 0
        max_attempts = 5  # Aumentar intentos para mayor robustez
        
        # Primero verificar si el modal está presente y visible
        try:
            modal_present = page.is_visible('#myModal')
            logger.info(f"Modal #myModal presente: {modal_present}")
            
            if modal_present:
                # Verificar el estilo display del modal
                modal_style = page.get_attribute('#myModal', 'style')
                logger.info(f"Estilo del modal: {modal_style}")
        except Exception as e:
            logger.warning(f"Error verificando modal: {e}")
        
        while not popup_closed and attempts < max_attempts:
            attempts += 1
            logger.info(f"🔄 Intento {attempts} de cerrar popup...")
            
            # Verificar si hay popup visible usando los selectores específicos
            for i, selector in enumerate(popup_selectors):
                try:
                    logger.info(f"Probando selector {i+1}: {selector}")
                    
                    # Esperar por el elemento con timeout corto
                    popup_element = page.wait_for_selector(selector, timeout=2000)
                    
                    if popup_element and popup_element.is_visible():
                        logger.info(f"✅ Popup encontrado con selector: {selector}")
                        
                        # Intentar diferentes métodos de click
                        try:
                            # Método 1: Click normal
                            popup_element.click()
                            logger.info("Click normal ejecutado")
                        except Exception as e1:
                            logger.warning(f"Click normal falló: {e1}")
                            try:
                                # Método 2: Click forzado
                                popup_element.click(force=True)
                                logger.info("Click forzado ejecutado")
                            except Exception as e2:
                                logger.warning(f"Click forzado falló: {e2}")
                                try:
                                    # Método 3: Dispatch click event
                                    popup_element.dispatch_event('click')
                                    logger.info("Dispatch click ejecutado")
                                except Exception as e3:
                                    logger.warning(f"Dispatch click falló: {e3}")
                                    continue
                        
                        # Esperar a que el popup desaparezca
                        try:
                            page.wait_for_selector('#myModal', state='hidden', timeout=5000)
                            popup_closed = True
                            logger.info("✅ Popup cerrado exitosamente")
                            break
                        except PlaywrightTimeoutError:
                            # Verificar si el modal sigue visible
                            still_visible = page.is_visible('#myModal')
                            if not still_visible:
                                popup_closed = True
                                logger.info("✅ Popup cerrado (verificación manual)")
                                break
                            else:
                                logger.warning("Popup aún visible después del click")
                                continue
                        
                except PlaywrightTimeoutError:
                    logger.info(f"Selector {selector} no encontrado (timeout)")
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Error al cerrar popup con {selector}: {e}")
                    continue
            
            # Si no se encontró popup o no se pudo cerrar, verificar estado
            if not popup_closed:
                try:
                    # Verificar si realmente hay un popup visible
                    modal_visible = page.is_visible('#myModal')
                    if not modal_visible:
                        logger.info("ℹ️ No se detectó popup visible")
                        popup_closed = True
                        break
                    else:
                        logger.warning(f"Popup aún visible en intento {attempts}")
                        # Intentar método alternativo: JavaScript directo
                        try:
                            page.evaluate('''
                                const modal = document.getElementById('myModal');
                                if (modal) {
                                    modal.style.display = 'none';
                                    modal.remove();
                                }
                            ''')
                            logger.info("Popup cerrado usando JavaScript directo")
                            popup_closed = True
                            break
                        except Exception as js_error:
                            logger.warning(f"Error con JavaScript directo: {js_error}")
                except Exception as check_error:
                    logger.warning(f"Error verificando estado del popup: {check_error}")
            
            time.sleep(2)  # Esperar más tiempo entre intentos
        
        # Verificación final del estado del popup
        try:
            final_modal_visible = page.is_visible('#myModal')
            logger.info(f"Estado final del popup: {'Visible' if final_modal_visible else 'Oculto'}")
            
            if final_modal_visible:
                logger.warning("⚠️ ADVERTENCIA: El popup aún está visible después de todos los intentos")
                # Último intento con JavaScript más agresivo
                page.evaluate('''
                    // Remover todos los modales y popups
                    const modals = document.querySelectorAll('#myModal, .modal, [class*="popup"]');
                    modals.forEach(modal => {
                        modal.style.display = 'none';
                        modal.style.visibility = 'hidden';
                        modal.remove();
                    });
                    
                    // Remover overlays
                    const overlays = document.querySelectorAll('[class*="overlay"], [class*="backdrop"]');
                    overlays.forEach(overlay => overlay.remove());
                ''')
                logger.info("Ejecutado JavaScript de limpieza final")
            else:
                logger.info("✅ Popup manejado correctamente")
        except Exception as e:
            logger.warning(f"Error en verificación final: {e}")
        
        # Tomar screenshot después de manejar popup
        page.screenshot(path=f"downloads/afinia/new_version/step2_after_popup_{timestamp}.png")
        logger.info("📸 Screenshot tomado después de manejar popup")
        
        # Obtener credenciales desde config
        username = OFICINA_VIRTUAL_AFINIA["username"]
        password = OFICINA_VIRTUAL_AFINIA["password"]
        
        # Logging detallado de credenciales (sin mostrar contraseña completa)
        logger.info(f"📋 Credenciales obtenidas desde configuración:")
        logger.info(f"   - Usuario: '{username}' (longitud: {len(username)})")
        logger.info(f"   - Contraseña: {'*' * len(password)} (longitud: {len(password)})")
        logger.info(f"   - URL: {OFICINA_VIRTUAL_AFINIA['url']}")
        
        # Validar que las credenciales no estén vacías
        if not username or not password:
            raise Exception(f"Credenciales incompletas - Usuario: {'✓' if username else '✗'}, Contraseña: {'✓' if password else '✗'}")
        
        logger.info(f"🔐 Iniciando login con usuario: {username[:10]}...")
        
        # Selectores específicos basados en el HTML del formulario de login de Afinia
        username_selector = "input[name='dnn$ctr$Login$Login_DotNetNuke.Membership.GatewayMembershipProvider$txtUsername']"
        password_selector = "input[name='dnn$ctr$Login$Login_DotNetNuke.Membership.GatewayMembershipProvider$txtPassword']"
        login_button_selector = "button[id='dnn_ctr_Login_Login_DotNetNuke.Membership.GatewayMembershipProvider_cmdLogin']"
        
        # Selectores alternativos para mayor robustez
        username_selectors = [
            "input[name='dnn$ctr$Login$Login_DotNetNuke.Membership.GatewayMembershipProvider$txtUsername']",
            "input[id='dnn_ctr_Login_Login_DotNetNuke.Membership.GatewayMembershipProvider_txtUsername']",
            "input[type='text'][class='form-control']",
            "input[autocomplete='off'][type='text']"
        ]
        
        password_selectors = [
            "input[name='dnn$ctr$Login$Login_DotNetNuke.Membership.GatewayMembershipProvider$txtPassword']",
            "input[id='dnn_ctr_Login_Login_DotNetNuke.Membership.GatewayMembershipProvider_txtPassword']",
            "input[type='password'][class='form-control']",
            "input[type='password'][autocomplete='off']"
        ]
        
        login_button_selectors = [
            "button[id='dnn_ctr_Login_Login_DotNetNuke.Membership.GatewayMembershipProvider_cmdLogin']",
            "button:has-text('Ingresar')",
            "button[class*='btn-success']",
            "button[onclick*='SubmitsEncry']"
        ]
        
        # Buscar elementos de login usando múltiples selectores
        logger.info("Buscando elementos de login...")
        
        username_field = None
        password_field = None
        login_button = None
        
        # Buscar campo de usuario
        for i, selector in enumerate(username_selectors):
            try:
                logger.info(f"Probando selector de usuario {i+1}: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element and element.is_visible():
                    username_field = element
                    logger.info(f"✅ Campo de usuario encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                logger.info(f"Selector de usuario {selector} no encontrado")
                continue
            except Exception as e:
                logger.warning(f"Error con selector de usuario {selector}: {e}")
                continue
        
        # Buscar campo de contraseña
        for i, selector in enumerate(password_selectors):
            try:
                logger.info(f"Probando selector de contraseña {i+1}: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element and element.is_visible():
                    password_field = element
                    logger.info(f"✅ Campo de contraseña encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                logger.info(f"Selector de contraseña {selector} no encontrado")
                continue
            except Exception as e:
                logger.warning(f"Error con selector de contraseña {selector}: {e}")
                continue
        
        # Buscar botón de login
        for i, selector in enumerate(login_button_selectors):
            try:
                logger.info(f"Probando selector de botón {i+1}: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element and element.is_visible():
                    login_button = element
                    logger.info(f"✅ Botón de login encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                logger.info(f"Selector de botón {selector} no encontrado")
                continue
            except Exception as e:
                logger.warning(f"Error con selector de botón {selector}: {e}")
                continue
        
        # Verificar que todos los elementos fueron encontrados
        if not username_field:
            raise Exception("Campo de usuario no encontrado con ningún selector")
        if not password_field:
            raise Exception("Campo de contraseña no encontrado con ningún selector")
        if not login_button:
            raise Exception("Botón de login no encontrado con ningún selector")
        
        logger.info("✅ Todos los elementos de login están disponibles")
        
        # Limpiar y llenar campos de login con manejo robusto
        logger.info("Preparando campos de login...")
        
        # Limpiar y llenar campo de usuario con validación mejorada
        try:
            logger.info("Llenando campo de usuario...")
            
            # Hacer foco en el campo
            username_field.focus()
            time.sleep(0.3)
            
            # Limpiar campo completamente
            username_field.click()
            username_field.fill("")  # Limpiar campo
            time.sleep(0.5)
            
            # Seleccionar todo el contenido y borrarlo
            username_field.press("Control+a")
            username_field.press("Delete")
            time.sleep(0.3)
            
            # Escribir el username con delay
            username_field.type(username, delay=100)  # Delay más lento para asegurar escritura
            time.sleep(0.5)
            
            # Verificar que se llenó correctamente
            filled_value = username_field.input_value()
            logger.info(f"Valor en campo usuario: '{filled_value[:10]}...' (longitud: {len(filled_value)})")
            
            # Validar que el campo no esté vacío
            if not filled_value or len(filled_value.strip()) == 0:
                logger.error("❌ Campo de usuario está vacío después del llenado")
                # Intentar llenar nuevamente
                logger.info("Reintentando llenar campo de usuario...")
                username_field.click()
                username_field.fill(username)
                time.sleep(0.5)
                filled_value = username_field.input_value()
                logger.info(f"Segundo intento - Valor: '{filled_value[:10]}...' (longitud: {len(filled_value)})")
                
                if not filled_value or len(filled_value.strip()) == 0:
                    raise Exception("No se pudo llenar el campo de usuario después de múltiples intentos")
            
            logger.info("✅ Campo de usuario llenado correctamente")
            
        except Exception as e:
            logger.error(f"Error llenando campo de usuario: {e}")
            raise
        
        time.sleep(1)
        
        # Limpiar y llenar campo de contraseña con validación mejorada
        try:
            logger.info("Llenando campo de contraseña...")
            
            # Hacer foco en el campo
            password_field.focus()
            time.sleep(0.3)
            
            # Limpiar campo completamente
            password_field.click()
            password_field.fill("")  # Limpiar campo
            time.sleep(0.5)
            
            # Seleccionar todo el contenido y borrarlo
            password_field.press("Control+a")
            password_field.press("Delete")
            time.sleep(0.3)
            
            # Escribir la contraseña con delay
            password_field.type(password, delay=100)  # Delay más lento para asegurar escritura
            time.sleep(0.5)
            
            # Verificar que se llenó (sin mostrar la contraseña)
            filled_password = password_field.input_value()
            logger.info(f"Campo contraseña llenado: {'Sí' if filled_password else 'No'} (longitud: {len(filled_password) if filled_password else 0})")
            
            # Validar que el campo no esté vacío
            if not filled_password or len(filled_password.strip()) == 0:
                logger.error("❌ Campo de contraseña está vacío después del llenado")
                # Intentar llenar nuevamente
                logger.info("Reintentando llenar campo de contraseña...")
                password_field.click()
                password_field.fill(password)
                time.sleep(0.5)
                filled_password = password_field.input_value()
                logger.info(f"Segundo intento - Campo contraseña: {'Sí' if filled_password else 'No'} (longitud: {len(filled_password) if filled_password else 0})")
                
                if not filled_password or len(filled_password.strip()) == 0:
                    raise Exception("No se pudo llenar el campo de contraseña después de múltiples intentos")
            
            logger.info("✅ Campo de contraseña llenado correctamente")
            
        except Exception as e:
            logger.error(f"Error llenando campo de contraseña: {e}")
            raise
        
        time.sleep(1)
        
        # Tomar screenshot antes del login
        page.screenshot(path=f"downloads/afinia/new_version/step2_before_login_{timestamp}.png")
        
        # Hacer clic en el botón de login con múltiples métodos
        logger.info("Haciendo clic en botón de login...")
        
        try:
            # Método 1: Click normal
            login_button.click()
            logger.info("Click normal en botón de login ejecutado")
        except Exception as e1:
            logger.warning(f"Click normal falló: {e1}")
            try:
                # Método 2: Click forzado
                login_button.click(force=True)
                logger.info("Click forzado en botón de login ejecutado")
            except Exception as e2:
                logger.warning(f"Click forzado falló: {e2}")
                try:
                    # Método 3: Dispatch click event
                    login_button.dispatch_event('click')
                    logger.info("Dispatch click en botón de login ejecutado")
                except Exception as e3:
                    logger.error(f"Todos los métodos de click fallaron: {e3}")
                    raise
        
        # Esperar navegación o cambio de página
        logger.info("Esperando respuesta del login...")
        try:
            # Esperar a que la URL cambie o aparezca contenido post-login
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(3)
        except Exception as e:
            logger.warning(f"Timeout esperando navegación: {e}")
        
        # Verificar si el login fue exitoso
        current_url = page.url
        logger.info(f"URL después del login: {current_url}")
        
        # Tomar screenshot después del login
        page.screenshot(path=f"downloads/afinia/new_version/step2_after_login_{timestamp}.png")
        
        # Verificar si el popup vuelve a aparecer después del login
        logger.info("Verificando si el popup vuelve a aparecer...")
        time.sleep(2)
        
        # Intentar cerrar popup nuevamente si aparece
        popup_selectors = [
            "button[id='closePopUp']",
            "button.close",
            "[data-dismiss='modal']",
            ".modal-header .close",
            "button:has-text('Cerrar')",
            "button:has-text('×')"
        ]
        
        popup_closed_again = False
        for selector in popup_selectors:
            try:
                popup_element = page.wait_for_selector(selector, timeout=3000)
                if popup_element and popup_element.is_visible():
                    logger.info(f"⚠️ Popup detectado nuevamente después del login con selector: {selector}")
                    popup_element.click()
                    time.sleep(1)
                    popup_closed_again = True
                    logger.info("✅ Popup cerrado nuevamente después del login")
                    break
            except:
                continue
        
        if not popup_closed_again:
            logger.info("✅ No se detectó popup después del login")
        
        # Verificar indicadores de login exitoso
        success_indicators = [
            "dashboard",
            "inicio",
            "home",
            "bienvenido",
            "welcome",
            "menu",
            "logout",
            "cerrar sesión",
            "mi perfil",
            "perfil"
        ]
        
        page_content = page.content().lower()
        login_success = False
        
        for indicator in success_indicators:
            if indicator in page_content or indicator in current_url.lower():
                logger.info(f"✅ Indicador de login exitoso encontrado: '{indicator}'")
                login_success = True
                break
        
        # Verificar si hay mensajes de error
        error_selectors = [
            ".error",
            ".alert-danger",
            ".message-error",
            "[class*='error']",
            "[class*='invalid']"
        ]
        
        for error_selector in error_selectors:
            try:
                error_elem = page.query_selector(error_selector)
                if error_elem and error_elem.is_visible():
                    error_text = error_elem.inner_text().strip()
                    if error_text:
                        logger.warning(f"Posible mensaje de error: {error_text}")
            except:
                continue
        
        if login_success:
            logger.info("✅ Login completado exitosamente")
            step_id = metrics.log_step_start("login_exitoso", "Login realizado correctamente")
            metrics.log_step_end(step_id, "completed")
            
            # Navegar automáticamente a la página de listado de PQR
            target_url = "https://caribemar.facture.co/Listado-Radicaci%C3%B3n-PQR#/List"
            logger.info(f"🔄 Navegando automáticamente a: {target_url}")
            
            try:
                page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle")
                time.sleep(3)
                
                # Tomar screenshot de la página de PQR
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                page.screenshot(path=f"downloads/afinia/new_version/step3_pqr_page_{timestamp}.png")
                
                # Guardar HTML de la página de PQR
                html_content = page.content()
                with open(f"downloads/afinia/new_version/step3_pqr_page_{timestamp}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                logger.info("✅ Navegación a página de PQR completada exitosamente")
                step_id = metrics.log_step_start("navegacion_pqr", "Navegación a listado PQR exitosa")
                metrics.log_step_end(step_id, "completed")
                
            except Exception as nav_error:
                logger.error(f"❌ Error navegando a página de PQR: {nav_error}")
                step_id = metrics.log_step_start("navegacion_pqr_error", f"Error navegando a PQR: {nav_error}")
                metrics.log_step_end(step_id, "error")
                # Continuar con el flujo normal aunque falle la navegación automática
            
            return True
        else:
            logger.warning("⚠️ Login completado pero sin confirmación clara de éxito")
            return True  # Continuar para análisis
        
    except Exception as e:
        logger.error(f"❌ Error en login: {str(e)}")
        page.screenshot(path=f"downloads/afinia/new_version/step2_login_error_{timestamp}.png")
        step_id = metrics.log_step_start("login_error", str(e))
        metrics.log_step_end(step_id, "error")
        raise

@performance_monitor
def configure_page_zoom(page):
    """Configura el zoom de la página al 50% para ver la tabla completa"""
    try:
        logger.info("=== PASO 3: Configurando zoom de página ===")
        
        # Reducir zoom al 50% para ver la tabla completa
        page.evaluate("document.body.style.zoom = '0.5'")
        logger.info("✅ Zoom configurado al 50%")
        
        # Esperar un momento para que se aplique el zoom
        time.sleep(2)
        
        # Tomar screenshot con el nuevo zoom
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=f"downloads/afinia/new_version/step3_zoom_configured_{timestamp}.png")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error configurando zoom: {str(e)}")
        raise

@performance_monitor
def expand_filters_panel(page):
    """Expande el panel de filtros haciendo clic en el botón 'Filtrar'"""
    try:
        logger.info("=== PASO 4: Expandiendo panel de filtros ===")
        
        # Selectores para el botón de filtrar basados en el HTML proporcionado
        filter_button_selectors = [
            "a.accordion-toggle[ng-click='toggleOpen()']",
            "a[accordion-transclude='heading']",
            "a:has-text('Filtrar')",
            ".accordion-toggle:has-text('Filtrar')",
            "accordion .panel-heading a"
        ]
        
        filter_button = None
        
        # Buscar el botón de filtrar
        for i, selector in enumerate(filter_button_selectors):
            try:
                logger.info(f"Probando selector de filtrar {i+1}: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element and element.is_visible():
                    filter_button = element
                    logger.info(f"✅ Botón de filtrar encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                logger.info(f"Selector {selector} no encontrado")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue
        
        if not filter_button:
            raise Exception("Botón de filtrar no encontrado")
        
        # Hacer clic en el botón de filtrar
        logger.info("Haciendo clic en botón 'Filtrar'...")
        filter_button.click()
        
        # Esperar a que se expanda el panel
        time.sleep(3)
        
        # Verificar que el panel se expandió
        try:
            panel_expanded = page.wait_for_selector(".panel-collapse.collapse[style*='height']", timeout=5000)
            if panel_expanded:
                logger.info("✅ Panel de filtros expandido exitosamente")
        except:
            logger.warning("No se pudo verificar la expansión del panel, continuando...")
        
        # Tomar screenshot del panel expandido
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(os.getcwd(), "downloads", "afinia", "new_version", f"step4_filters_expanded_{timestamp}.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Screenshot guardado en: {screenshot_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error expandiendo filtros: {str(e)}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=f"downloads/afinia/new_version/step4_filters_error_{timestamp}.png")
        raise

@performance_monitor
def configure_status_filter(page):
    """Configura el filtro de estado a 'Finalizado'"""
    try:
        logger.info("=== PASO 5: Configurando filtro de estado ===")
        
        # Selectores para el campo de estado basados en el HTML proporcionado
        status_selectors = [
            "md-select[ng-model='filtros.Estado']",
            "md-select[name='Estado']",
            "#select_3",
            "md-select[aria-label*='Estado']"
        ]
        
        status_field = None
        
        # Buscar el campo de estado
        for i, selector in enumerate(status_selectors):
            try:
                logger.info(f"Probando selector de estado {i+1}: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element and element.is_visible():
                    status_field = element
                    logger.info(f"✅ Campo de estado encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                logger.info(f"Selector {selector} no encontrado")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue
        
        if not status_field:
            raise Exception("Campo de estado no encontrado")
        
        # Hacer clic en el campo de estado para abrirlo
        logger.info("Abriendo selector de estado...")
        status_field.click()
        time.sleep(2)
        
        # Buscar y seleccionar la opción 'Finalizado'
        finalizado_selectors = [
            "md-option:has-text('Finalizado')",
            "md-option[value='Finalizado']",
            "[role='option']:has-text('Finalizado')",
            "md-select-menu md-option:has-text('Finalizado')"
        ]
        
        finalizado_option = None
        
        for i, selector in enumerate(finalizado_selectors):
            try:
                logger.info(f"Probando selector de opción Finalizado {i+1}: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element and element.is_visible():
                    finalizado_option = element
                    logger.info(f"✅ Opción 'Finalizado' encontrada con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                logger.info(f"Selector {selector} no encontrado")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue
        
        if not finalizado_option:
            raise Exception("Opción 'Finalizado' no encontrada")
        
        # Seleccionar 'Finalizado'
        logger.info("Seleccionando 'Finalizado'...")
        finalizado_option.click()
        time.sleep(2)
        
        # Tomar screenshot del estado configurado
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(os.getcwd(), "downloads", "afinia", "new_version", f"step5_status_configured_{timestamp}.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Screenshot guardado en: {screenshot_path}")
        
        logger.info("✅ Estado 'Finalizado' configurado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error configurando estado: {str(e)}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=f"downloads/afinia/new_version/step5_status_error_{timestamp}.png")
        raise

@performance_monitor
def configure_date_filters(page):
    """Configura los filtros de fecha inicial (día anterior) y fecha final (día actual)"""
    try:
        logger.info("=== PASO 6: Configurando filtros de fecha ===")
        
        # Calcular fechas
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        fecha_inicial = yesterday.strftime("%Y-%m-%d")
        fecha_final = today.strftime("%Y-%m-%d")
        
        logger.info(f"Configurando fechas: Inicial={fecha_inicial}, Final={fecha_final}")
        
        # Configurar fecha inicial
        logger.info("Configurando fecha inicial...")
        
        # Selectores para fecha inicial basados en el HTML proporcionado
        fecha_inicial_selectors = [
            "md-datepicker[ng-model='filtros.fechaInicial'] input",
            "input.md-datepicker-input[placeholder='YYYY-MM-DD']",
            "md-datepicker[name='Fecha inicial'] input",
            ".campo-fecha input[placeholder*='YYYY-MM-DD']"
        ]
        
        fecha_inicial_field = None
        
        for i, selector in enumerate(fecha_inicial_selectors):
            try:
                logger.info(f"Probando selector de fecha inicial {i+1}: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element and element.is_visible():
                    fecha_inicial_field = element
                    logger.info(f"✅ Campo de fecha inicial encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                logger.info(f"Selector {selector} no encontrado")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue
        
        if fecha_inicial_field:
            # Limpiar y llenar fecha inicial
            fecha_inicial_field.click()
            fecha_inicial_field.fill("")
            fecha_inicial_field.type(fecha_inicial)
            logger.info(f"✅ Fecha inicial configurada: {fecha_inicial}")
            time.sleep(1)
        else:
            logger.warning("Campo de fecha inicial no encontrado")
        
        # Configurar fecha final
        logger.info("Configurando fecha final...")
        
        # Selectores para fecha final
        fecha_final_selectors = [
            "md-datepicker[ng-model='filtros.fechaFinal'] input",
            "md-datepicker[name='Fecha inicial']:nth-of-type(2) input",  # Segundo datepicker
            ".campo-fecha:nth-of-type(2) input[placeholder*='YYYY-MM-DD']"
        ]
        
        fecha_final_field = None
        
        for i, selector in enumerate(fecha_final_selectors):
            try:
                logger.info(f"Probando selector de fecha final {i+1}: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element and element.is_visible():
                    fecha_final_field = element
                    logger.info(f"✅ Campo de fecha final encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                logger.info(f"Selector {selector} no encontrado")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue
        
        if fecha_final_field:
            # Limpiar y llenar fecha final
            fecha_final_field.click()
            fecha_final_field.fill("")
            fecha_final_field.type(fecha_final)
            logger.info(f"✅ Fecha final configurada: {fecha_final}")
            time.sleep(1)
        else:
            logger.warning("Campo de fecha final no encontrado")
        
        # Tomar screenshot de las fechas configuradas
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(os.getcwd(), "downloads", "afinia", "new_version", f"step6_dates_configured_{timestamp}.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"Screenshot guardado en: {screenshot_path}")
        
        logger.info("✅ Filtros de fecha configurados exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error configurando fechas: {str(e)}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=f"downloads/afinia/new_version/step6_dates_error_{timestamp}.png")
        raise

@performance_monitor
def execute_search_with_filters(page):
    """Ejecuta la búsqueda con los filtros aplicados"""
    try:
        logger.info("=== PASO 7: Ejecutando búsqueda con filtros ===")
        
        # Selectores para el botón de buscar basados en el HTML proporcionado
        search_button_selectors = [
            "button[ng-click='Search()'][aria-label='Buscar']",
            "button.md-raised.md-primary:has-text('Buscar')",
            "button[aria-label='Buscar']",
            "button:has-text('Buscar')"
        ]
        
        search_button = None
        
        # Buscar el botón de búsqueda
        for i, selector in enumerate(search_button_selectors):
            try:
                logger.info(f"Probando selector de búsqueda {i+1}: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element and element.is_visible():
                    search_button = element
                    logger.info(f"✅ Botón de búsqueda encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                logger.info(f"Selector {selector} no encontrado")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue
        
        if not search_button:
            raise Exception("Botón de búsqueda no encontrado")
        
        # Hacer clic en el botón de búsqueda
        logger.info("Ejecutando búsqueda...")
        search_button.click()
        
        # Esperar a que se procese la búsqueda
        logger.info("Esperando resultados de búsqueda...")
        time.sleep(5)
        
        # Esperar a que la tabla se actualice
        try:
            page.wait_for_selector("md-table tbody tr", timeout=15000)
            logger.info("✅ Tabla actualizada con resultados")
        except PlaywrightTimeoutError:
            logger.warning("Timeout esperando resultados, continuando...")
        
        # Tomar screenshot de los resultados filtrados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=f"downloads/afinia/new_version/step7_search_results_{timestamp}.png")
        
        # Verificar si hay resultados
        try:
            rows = page.query_selector_all("md-table tbody tr")
            logger.info(f"Resultados encontrados: {len(rows)} filas")
            
            # Verificar información de paginación
            pagination_info = page.query_selector(".buttons .label")
            if pagination_info:
                pagination_text = pagination_info.inner_text().strip()
                logger.info(f"Información de paginación: {pagination_text}")
        except Exception as e:
            logger.warning(f"Error verificando resultados: {e}")
        
        logger.info("✅ Búsqueda con filtros ejecutada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando búsqueda: {str(e)}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=f"downloads/afinia/new_version/step7_search_error_{timestamp}.png")
        raise

@performance_monitor
def collapse_filters_panel(page):
    """Colapsa el panel de filtros para mejorar la visualización de la tabla"""
    try:
        logger.info("=== PASO 7.5: Colapsando panel de filtros ===")
        
        # Selectores para el botón de filtrar basados en el HTML proporcionado
        filter_toggle_selectors = [
            "a.accordion-toggle[ng-click='toggleOpen()']",
            ".accordion-toggle:has-text('Filtrar')",
            ".panel-title a.accordion-toggle",
            "a[accordion-transclude='heading']:has-text('Filtrar')"
        ]
        
        filter_toggle = None
        
        # Buscar el botón toggle de filtros
        for i, selector in enumerate(filter_toggle_selectors):
            try:
                logger.info(f"Probando selector de toggle filtros {i+1}: {selector}")
                element = page.wait_for_selector(selector, timeout=5000)
                if element and element.is_visible():
                    filter_toggle = element
                    logger.info(f"✅ Botón toggle de filtros encontrado con selector: {selector}")
                    break
            except PlaywrightTimeoutError:
                logger.info(f"Selector {selector} no encontrado")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue
        
        if not filter_toggle:
            logger.warning("Botón toggle de filtros no encontrado, continuando sin colapsar...")
            return True
        
        # Verificar si el panel está expandido antes de colapsarlo
        try:
            panel_expanded = page.query_selector(".panel-collapse.collapse[style*='height']")
            if panel_expanded:
                panel_style = panel_expanded.get_attribute("style")
                if "height: 0px" not in panel_style:
                    logger.info("Panel de filtros está expandido, colapsando...")
                    filter_toggle.click()
                    time.sleep(2)
                    
                    # Tomar screenshot después de colapsar
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(os.getcwd(), "downloads", "afinia", "new_version", f"step7_5_filters_collapsed_{timestamp}.png")
                    page.screenshot(path=screenshot_path)
                    logger.info(f"Screenshot guardado en: {screenshot_path}")
                    logger.info("✅ Panel de filtros colapsado exitosamente")
                else:
                    logger.info("Panel de filtros ya está colapsado")
            else:
                logger.info("No se pudo verificar el estado del panel, intentando colapsar...")
                filter_toggle.click()
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Error verificando estado del panel: {e}")
            # Intentar colapsar de todas formas
            filter_toggle.click()
            time.sleep(2)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error colapsando panel de filtros: {str(e)}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=f"downloads/afinia/new_version/step7_5_collapse_error_{timestamp}.png")
        # No lanzar excepción ya que esto no es crítico para el flujo principal
        return False

@performance_monitor
def process_pqr_records(page, max_records=2):
    """Procesa los registros de PQR haciendo clic derecho en el botón del ojo"""
    try:
        logger.info(f"=== PASO 8: Procesando registros de PQR (máximo {max_records}) ===")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Selectores para los botones del ojo en la tabla
        eye_button_selectors = [
            'a.md-primary[tooltip="Ver PQR"]',
            'td.md-actions a[tooltip="Ver PQR"]',
            'a[href*="#Detail/"]',
            'td.md-cell.md-actions a.md-primary'
        ]
        
        processed_records = 0
        
        # Buscar todos los botones del ojo disponibles
        for selector in eye_button_selectors:
            try:
                logger.info(f"Probando selector de botones ojo: {selector}")
                
                # Usar locator en lugar de query_selector_all para mejor compatibilidad
                eye_buttons = page.locator(selector)
                button_count = eye_buttons.count()
                
                if button_count > 0:
                    logger.info(f"✅ Encontrados {button_count} botones del ojo con selector: {selector}")
                    
                    # Procesar solo los primeros registros según el límite
                    for i in range(min(button_count, max_records)):
                        if processed_records >= max_records:
                            break
                            
                        try:
                            logger.info(f"🔍 Procesando registro {i+1}/{min(button_count, max_records)}")
                            
                            # Obtener el botón específico
                            current_button = eye_buttons.nth(i)
                            
                            # Hacer clic derecho para abrir en nueva pestaña
                            logger.info("Haciendo clic derecho para abrir en nueva pestaña...")
                            
                            try:
                                # Primero intentar clic derecho
                                current_button.click(button='right')
                                logger.info("✅ Clic derecho ejecutado")
                                
                                # Esperar un momento para que aparezca el menú contextual
                                time.sleep(1)
                                
                                # Buscar y hacer clic en "Abrir en pestaña nueva" o similar
                                try:
                                    # Intentar diferentes textos del menú contextual
                                    context_menu_options = [
                                        'text="Abrir en pestaña nueva"',
                                        'text="Open in new tab"',
                                        'text="Abrir en nueva pestaña"',
                                        '[role="menuitem"]:has-text("nueva")',
                                        '[role="menuitem"]:has-text("new")'
                                    ]
                                    
                                    menu_clicked = False
                                    for option in context_menu_options:
                                        try:
                                            menu_item = page.locator(option).first
                                            if menu_item.is_visible():
                                                menu_item.click()
                                                logger.info(f"✅ Menú contextual clickeado: {option}")
                                                menu_clicked = True
                                                break
                                        except:
                                            continue
                                    
                                    if not menu_clicked:
                                        # Fallback: usar JavaScript para abrir en nueva pestaña
                                        href = current_button.get_attribute('href')
                                        if href:
                                            page.evaluate(f"window.open('{href}', '_blank')")
                                            logger.info("✅ Nueva pestaña abierta con JavaScript (fallback)")
                                        else:
                                            logger.warning("No se pudo obtener href del botón")
                                            continue
                                            
                                except Exception as menu_error:
                                    logger.warning(f"Error con menú contextual: {menu_error}")
                                    # Fallback: usar JavaScript
                                    href = current_button.get_attribute('href')
                                    if href:
                                        page.evaluate(f"window.open('{href}', '_blank')")
                                        logger.info("✅ Nueva pestaña abierta con JavaScript (fallback)")
                                    else:
                                        logger.warning("No se pudo obtener href del botón")
                                        continue
                                        
                            except Exception as right_click_error:
                                logger.warning(f"Error con clic derecho: {right_click_error}")
                                # Fallback: obtener href y abrir manualmente
                                try:
                                    href = current_button.get_attribute('href')
                                    if href:
                                        # Abrir nueva pestaña con JavaScript
                                        page.evaluate(f"window.open('{href}', '_blank')")
                                        logger.info("✅ Nueva pestaña abierta con JavaScript")
                                    else:
                                        logger.warning("No se pudo obtener href del botón")
                                        continue
                                except Exception as href_error:
                                    logger.error(f"Error obteniendo href: {href_error}")
                                    continue
                            
                            time.sleep(3)  # Esperar a que se abra la nueva pestaña
                            
                            # Obtener todas las páginas (pestañas) del contexto
                            context = page.context
                            pages = context.pages
                            
                            if len(pages) > 1:
                                # Cambiar a la nueva pestaña (la última abierta)
                                new_page = pages[-1]
                                logger.info(f"✅ Cambiando a nueva pestaña. Total pestañas: {len(pages)}")
                                
                                # Procesar la PQR en la nueva pestaña
                                pqr_data = extract_pqr_data(new_page, i+1)
                                
                                # Cerrar la pestaña después del procesamiento
                                new_page.close()
                                logger.info("✅ Pestaña cerrada después del procesamiento")
                                
                                processed_records += 1
                                
                            else:
                                logger.warning("No se detectó nueva pestaña abierta")
                                
                        except Exception as record_error:
                            logger.error(f"❌ Error procesando registro {i+1}: {record_error}")
                            continue
                    
                    break  # Salir del bucle de selectores si encontramos botones
                    
            except Exception as selector_error:
                logger.warning(f"Error con selector {selector}: {selector_error}")
                continue
        
        if processed_records == 0:
            logger.warning("⚠️ No se pudieron procesar registros de PQR")
            page.screenshot(path=f"downloads/afinia/new_version/step8_no_records_{timestamp}.png")
        else:
            logger.info(f"✅ Procesados {processed_records} registros de PQR exitosamente")
            page.screenshot(path=f"downloads/afinia/new_version/step8_records_processed_{timestamp}.png")
        
        return processed_records
        
    except Exception as e:
        logger.error(f"❌ Error procesando registros de PQR: {str(e)}")
        page.screenshot(path=f"downloads/afinia/new_version/step8_process_error_{timestamp}.png")
        return 0

@performance_monitor
def extract_pqr_data(page, record_number):
    """Extrae los datos de PQR en formato JSON desde la página interna"""
    try:
        logger.info(f"=== Extrayendo datos de PQR #{record_number} ===")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Esperar a que la página cargue completamente
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        
        # Tomar screenshot inicial de la página de PQR
        page.screenshot(path=f"downloads/afinia/new_version/pqr_{record_number}_initial_{timestamp}.png")
        
        # Verificar si estamos en la página de detalle o en la lista
        # Si estamos en la lista, los datos están en la tabla md-data-table
        is_detail_page = False
        try:
            # Buscar elementos específicos de página de detalle
            detail_indicators = [
                "md-card",
                ".detail-container", 
                "[ng-controller*='Detail']",
                "td.text-td-label"  # Selector original que indica página de detalle
            ]
            
            for indicator in detail_indicators:
                if page.locator(indicator).count() > 0:
                    is_detail_page = True
                    logger.info(f"Detectada página de detalle por: {indicator}")
                    break
                    
        except Exception as e:
            logger.warning(f"Error verificando tipo de página: {e}")
        
        # Selectores corregidos basados en la estructura real de Angular Material
        if is_detail_page:
            # Selectores para página de detalle (estructura original)
            data_selectors = {
                "nic": "td.text-td-label:has-text('NIC') + td.ng-binding",
                "fecha": "td.text-td-label:has-text('Fecha') + td.ng-binding",
                "documento_identidad": "td.text-td-label:has-text('Documento de identidad') + td.ng-binding",
                "nombres_apellidos": "td.text-td-label:has-text('Nombres y Apellidos') + td.ng-binding",
                "lectura": "td.text-td-label:has-text('Lectura') + td.ng-binding",
                "correo_electronico": "td.text-td-label:has-text('Correo electrónico') + td.ng-binding",
                "telefono": "td.text-td-label:has-text('Teléfono') + td.ng-binding",
                "celular": "td.text-td-label:has-text('Celular') + td.ng-binding",
                "tipo_pqr": "td.text-td-label:has-text('Tipo de PQR') + td.ng-binding",
                "canal_respuesta": "td.text-td-label:has-text('Canal de respuesta') + td",
                "documento_prueba": "td.text-td-label:has-text('Documento/prueba') + td",
                "cuerpo_reclamacion": "td.text-td-label:has-text('Cuerpo de la reclamación') + td",
                "numero_radicado": "td.text-td-label:has-text('N° Radicado PQR') + td.ng-binding",
                "estado_solicitud": "td.text-td-label:has-text('Estado Solicitud') + td.ng-binding",
                "finalizar": "td.text-td-label:has-text('Finalizar') + td",
                "adjuntar_archivo": "td.text-td-label:has-text('Adjuntar archivo') + td",
                "numero_reclamo_sgc": "input[name='NumeroReclamoSGC']",
                "comentarios": "td.text-td-label:has-text('Comentarios') + td"
            }
        else:
            # Estamos en la página de lista, extraer datos de la tabla md-data-table
            logger.info("📋 Extrayendo datos de tabla de lista (md-data-table)")
            # Los datos se extraerán por posición de columna más adelante
            data_selectors = {}
        
        # Extraer datos
        pqr_data = {}
        
        if is_detail_page and data_selectors:
            # Extraer datos usando selectores para página de detalle
            for field_name, selector in data_selectors.items():
                try:
                    if field_name == "numero_reclamo_sgc":
                        # Campo especial que es un input
                        element = page.locator(selector).first
                        if element.is_visible():
                            value = element.get_attribute('value') or element.input_value()
                            pqr_data[field_name] = value.strip() if value else ""
                        else:
                            pqr_data[field_name] = ""
                    else:
                        # Campos normales de texto
                        element = page.locator(selector).first
                        if element.is_visible():
                            text = element.inner_text()
                            pqr_data[field_name] = text.strip() if text else ""
                        else:
                            pqr_data[field_name] = ""
                            
                    logger.info(f"✅ {field_name}: {pqr_data[field_name][:50]}...")
                    
                except Exception as field_error:
                    logger.warning(f"⚠️ Error extrayendo {field_name}: {field_error}")
                    pqr_data[field_name] = ""
        else:
            # Estamos en la página de lista, extraer datos de la tabla md-data-table
            try:
                # Buscar todas las filas de la tabla
                rows = page.locator('tbody.md-body tr.md-row')
                row_count = rows.count()
                logger.info(f"Encontradas {row_count} filas en la tabla")
                
                if row_count > 0:
                    # Tomar la primera fila (asumiendo que es la que se clickeó)
                    target_row = rows.first
                    
                    # Extraer datos por posición de columna (basado en la estructura observada)
                    cells = target_row.locator('td.md-cell')
                    cell_count = cells.count()
                    logger.info(f"Encontradas {cell_count} celdas en la fila")
                    
                    if cell_count >= 10:  # Verificar que hay suficientes columnas
                        # Mapeo basado en la estructura observada en el HTML:
                        # 0: Número radicado, 1: Fecha, 2: Estado, 3: Tipo PQR, 4: NIC, 
                        # 5: Nombres, 6: Teléfono, 7: Celular, 8: Correo, 9: Documento, 10: Canal
                        pqr_data = {
                            'numero_radicado': cells.nth(0).inner_text().strip(),
                            'fecha': cells.nth(1).inner_text().strip(),
                            'estado_solicitud': cells.nth(2).inner_text().strip(),
                            'tipo_pqr': cells.nth(3).inner_text().strip(),
                            'nic': cells.nth(4).inner_text().strip(),
                            'nombres_apellidos': cells.nth(5).inner_text().strip(),
                            'telefono': cells.nth(6).inner_text().strip(),
                            'celular': cells.nth(7).inner_text().strip(),
                            'correo_electronico': cells.nth(8).inner_text().strip(),
                            'documento_identidad': cells.nth(9).inner_text().strip(),
                            'canal_respuesta': cells.nth(10).inner_text().strip() if cell_count > 10 else '',
                            # Campos que no están en la tabla de lista
                            'lectura': '',
                            'documento_prueba': '',
                            'cuerpo_reclamacion': '',
                            'finalizar': '',
                            'adjuntar_archivo': '',
                            'numero_reclamo_sgc': '',
                            'comentarios': ''
                        }
                        
                        # Log de datos extraídos
                        for key, value in pqr_data.items():
                            logger.info(f"✅ {key}: {value}")
                            
                    else:
                        logger.warning(f"Número insuficiente de columnas: {cell_count}")
                        # Inicializar con valores vacíos
                        pqr_data = {key: '' for key in [
                            'nic', 'fecha', 'documento_identidad', 'nombres_apellidos', 'lectura',
                            'correo_electronico', 'telefono', 'celular', 'tipo_pqr', 'canal_respuesta',
                            'documento_prueba', 'cuerpo_reclamacion', 'numero_radicado', 'estado_solicitud',
                            'finalizar', 'adjuntar_archivo', 'numero_reclamo_sgc', 'comentarios'
                        ]}
                else:
                    logger.warning("No se encontraron filas en la tabla")
                    # Inicializar con valores vacíos
                    pqr_data = {key: '' for key in [
                        'nic', 'fecha', 'documento_identidad', 'nombres_apellidos', 'lectura',
                        'correo_electronico', 'telefono', 'celular', 'tipo_pqr', 'canal_respuesta',
                        'documento_prueba', 'cuerpo_reclamacion', 'numero_radicado', 'estado_solicitud',
                        'finalizar', 'adjuntar_archivo', 'numero_reclamo_sgc', 'comentarios'
                    ]}
                    
            except Exception as table_error:
                logger.error(f"Error extrayendo datos de tabla: {table_error}")
                # Inicializar con valores vacíos
                pqr_data = {key: '' for key in [
                    'nic', 'fecha', 'documento_identidad', 'nombres_apellidos', 'lectura',
                    'correo_electronico', 'telefono', 'celular', 'tipo_pqr', 'canal_respuesta',
                    'documento_prueba', 'cuerpo_reclamacion', 'numero_radicado', 'estado_solicitud',
                    'finalizar', 'adjuntar_archivo', 'numero_reclamo_sgc', 'comentarios'
                ]}
        
        # Guardar datos en JSON
        json_filename = f"downloads/afinia/new_version/pqr_{record_number}_data_{timestamp}.json"
        import json
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(pqr_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Datos JSON guardados en: {json_filename}")
        
        # Manejar adjuntos si existen
        sgc_number = pqr_data.get('numero_reclamo_sgc', f'PQR_{record_number}')
        handle_attachments(page, sgc_number, record_number)
        
        # Generar PDF de la página completa
        generate_pdf_report(page, sgc_number, record_number)
        
        return pqr_data
        
    except Exception as e:
        logger.error(f"❌ Error extrayendo datos de PQR #{record_number}: {str(e)}")
        # Tomar screenshot del error
        try:
            page.screenshot(path=f"downloads/afinia/new_version/pqr_{record_number}_error_{timestamp}.png")
        except:
            pass
        return {}

@performance_monitor
def handle_attachments(page, sgc_number, record_number):
    """Maneja la descarga de adjuntos si existen"""
    try:
        logger.info(f"=== Verificando adjuntos para PQR #{record_number} ===")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Buscar enlaces de documentos/pruebas
        attachment_selectors = [
            "a[href*='download']",
            "a[href*='archivo']",
            "a[href*='documento']",
            "td.text-td-label:has-text('Documento/prueba') + td a",
            "td.text-td-label:has-text('Adjuntar archivo') + td a"
        ]
        
        attachments_found = False
        
        for selector in attachment_selectors:
            try:
                attachments = page.locator(selector)
                count = attachments.count()
                
                if count > 0:
                    logger.info(f"✅ Encontrados {count} adjuntos con selector: {selector}")
                    
                    for i in range(count):
                        try:
                            attachment = attachments.nth(i)
                            href = attachment.get_attribute('href')
                            text = attachment.inner_text()
                            
                            if href and text:
                                logger.info(f"📎 Adjunto encontrado: {text} -> {href}")
                                
                                # Marcar el adjunto con el número SGC
                                attachment_name = f"{sgc_number}_{text.strip()}_adjunto"
                                logger.info(f"✅ Adjunto marcado como: {attachment_name}")
                                
                                attachments_found = True
                                
                        except Exception as att_error:
                            logger.warning(f"Error procesando adjunto {i}: {att_error}")
                            continue
                            
                    if attachments_found:
                        break
                        
            except Exception as selector_error:
                logger.warning(f"Error con selector de adjuntos {selector}: {selector_error}")
                continue
        
        if not attachments_found:
            logger.info("ℹ️ No se encontraron adjuntos en esta PQR")
            
        return attachments_found
        
    except Exception as e:
        logger.error(f"❌ Error manejando adjuntos: {str(e)}")
        return False

@performance_monitor
def generate_pdf_report(page, sgc_number, record_number):
    """Genera un PDF de la página completa usando Ctrl+P"""
    try:
        logger.info(f"=== Generando PDF para PQR #{record_number} ===")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Usar la funcionalidad de PDF nativa de Playwright
        pdf_filename = f"downloads/afinia/new_version/{sgc_number}_PQR_{record_number}_{timestamp}.pdf"
        
        # Generar PDF
        page.pdf(
            path=pdf_filename,
            format='A4',
            print_background=True,
            margin={
                'top': '1cm',
                'right': '1cm',
                'bottom': '1cm',
                'left': '1cm'
            }
        )
        
        logger.info(f"✅ PDF generado: {pdf_filename}")
        return pdf_filename
        
    except Exception as e:
        logger.error(f"❌ Error generando PDF: {str(e)}")
        # Fallback: screenshot de página completa
        try:
            screenshot_filename = f"downloads/afinia/new_version/{sgc_number}_PQR_{record_number}_{timestamp}_screenshot.png"
            page.screenshot(path=screenshot_filename, full_page=True)
            logger.info(f"✅ Screenshot completo generado como fallback: {screenshot_filename}")
            return screenshot_filename
        except Exception as screenshot_error:
            logger.error(f"❌ Error generando screenshot fallback: {screenshot_error}")
            return None

@performance_monitor
def analyze_post_login_structure(page):
    """Analiza la estructura de la página después del login y ejecuta el flujo completo"""
    try:
        logger.info("🚀 Iniciando analyze_post_login_structure")
        logger.info("=== PASO 4: Analizando estructura post-login ===")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Esperar a que la página cargue completamente
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        
        # Tomar screenshot inicial
        page.screenshot(path=f"downloads/afinia/new_version/step4_post_login_{timestamp}.png")
        
        # Guardar HTML para análisis
        html_content = page.content()
        with open(f"downloads/afinia/new_version/step4_post_login_{timestamp}.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info("✅ Screenshot y HTML guardados para análisis")
        
        # Ejecutar flujo completo de filtros
        logger.info("🔄 Iniciando flujo completo de filtros...")
        
        # Paso 5: Configurar estado
        configure_status_filter(page)
        
        # Paso 6: Configurar fechas
        configure_date_filters(page)
        
        # Paso 7: Ejecutar búsqueda
        execute_search_with_filters(page)
        
        # Paso 7.5: Colapsar panel de filtros
        collapse_filters_panel(page)
        
        # Paso 8: Procesar registros de PQR
        logger.info("")
        logger.info("============================================================")
        logger.info("INICIANDO PROCESAMIENTO DE PQR - MODO PRUEBA (2 registros)")
        logger.info("============================================================")
        
        processed_records = process_pqr_records(page, max_records=2)
        
        if processed_records > 0:
            logger.info(f"✅ Procesamiento de PQR completado: {processed_records} registros procesados")
        else:
            logger.warning("⚠️ No se pudieron procesar registros de PQR")
        
        logger.info("✅ Flujo completo de filtros ejecutado exitosamente")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en analyze_post_login_structure: {str(e)}")
        page.screenshot(path=f"downloads/afinia/new_version/step4_error_{timestamp}.png")
        return False
        pqr_data["extraction_timestamp"] = timestamp
        pqr_data["page_url"] = page.url
        
        # Guardar datos en JSON
        import json
        json_filename = f"downloads/afinia/new_version/pqr_{record_number}_data_{timestamp}.json"
        os.makedirs(os.path.dirname(json_filename), exist_ok=True)
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(pqr_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Datos extraídos y guardados en: {json_filename}")
        
        # Manejar documentos adjuntos si existen
        sgc_number = pqr_data.get('numero_reclamo_sgc', f'PQR_{record_number}')
        handle_attachments(page, sgc_number, record_number)
        
        # Generar PDF de la página
        generate_pdf_report(page, sgc_number, record_number)
        
        return pqr_data
        
    except Exception as e:
        logger.error(f"❌ Error extrayendo datos de PQR #{record_number}: {str(e)}")
        page.screenshot(path=f"downloads/afinia/new_version/pqr_{record_number}_error_{timestamp}.png")
        return {}

@performance_monitor
def analyze_post_login_structure(page):
    """Analiza la estructura después del login y ejecuta el flujo completo"""
    try:
        logger.info("🚀 Iniciando analyze_post_login_structure")
        logger.info("=== ANÁLISIS POST-LOGIN: Estructura de la nueva Oficina Virtual ===")
        
        # Paso 1: Expandir panel de filtros
        logger.info("=== PASO 1: Expandiendo panel de filtros ===")
        try:
            expand_filters_panel(page)
            logger.info("✅ Panel de filtros expandido exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error expandiendo filtros: {e}")
            # Continuar con el flujo aunque falle la expansión
        
        # Paso 2: Configurar filtro de estado
        logger.info("=== PASO 2: Configurando filtro de estado ===")
        try:
            configure_status_filter(page)
            logger.info("✅ Filtro de estado configurado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error configurando estado: {e}")
            # Continuar con el flujo aunque falle el estado
        
        # Paso 3: Configurar filtros de fecha
        logger.info("=== PASO 3: Configurando filtros de fecha ===")
        try:
            configure_date_filters(page)
            logger.info("✅ Filtros de fecha configurados exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error configurando fechas: {e}")
            # Continuar con el flujo aunque fallen las fechas
        
        # Paso 4: Ejecutar búsqueda con filtros
        logger.info("=== PASO 4: Ejecutando búsqueda con filtros ===")
        try:
            execute_search_with_filters(page)
            logger.info("✅ Búsqueda ejecutada exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error ejecutando búsqueda: {e}")
            # Intentar búsqueda básica como fallback
            try:
                search_button = page.locator("button:has-text('Buscar'), input[type='submit'][value*='Buscar']").first
                search_button.click()
                logger.info("✅ Búsqueda básica ejecutada como fallback")
                page.wait_for_timeout(3000)
            except Exception as fallback_error:
                logger.error(f"❌ Error en búsqueda fallback: {fallback_error}")
        
        # Paso 5: Colapsar panel de filtros
        logger.info("=== PASO 5: Colapsando panel de filtros ===")
        try:
            collapse_filters_panel(page)
            logger.info("✅ Panel de filtros colapsado exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error colapsando filtros: {e}")
            # No es crítico, continuar
        
        # Tomar screenshot de resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(os.getcwd(), "downloads", "afinia", "new_version", f"post_search_results_{timestamp}.png")
        page.screenshot(path=screenshot_path)
        logger.info(f"✅ Screenshot de resultados guardado en: {screenshot_path}")
        
        # Paso 6: Procesar PQRs (modo prueba - solo 2 registros)
        logger.info("=== PASO 6: Procesando PQRs (modo prueba: 2 registros) ===")
        
        try:
            # Usar la función ya implementada para procesar PQRs
            process_pqr_records(page, max_records=2)
            logger.info("✅ PQRs procesados exitosamente")
        except Exception as e:
            logger.warning(f"⚠️ Error procesando PQRs: {e}")
            # Continuar con procesamiento manual como fallback
            logger.info("Intentando procesamiento manual como fallback...")
            
            # Buscar botones del ojo con selectores más específicos
            eye_selectors = [
                'a.md-primary[tooltip="Ver PQR"]',
                'td.md-actions a[tooltip="Ver PQR"]',
                'a[href*="#Detail/"]',
                'td.md-cell.md-actions a.md-primary',
                "button.btn-eye",
                "a.btn-eye", 
                "button[title*='Ver']",
                "a[title*='Ver']",
                "button:has(i.fa-eye)",
                "a:has(i.fa-eye)",
                ".btn:has(.fa-eye)",
                "button.view-btn",
                "a.view-btn"
            ]
            
            found_buttons = []
            for selector in eye_selectors:
                try:
                    buttons = page.locator(selector)
                    count = buttons.count()
                    if count > 0:
                        logger.info(f"✅ Encontrados {count} botones con selector: {selector}")
                        for i in range(min(count, 2)):  # Solo procesar 2 en modo prueba
                            found_buttons.append((selector, i))
                        break
                except Exception as e:
                    logger.warning(f"Error con selector {selector}: {e}")
                    continue
            
            if not found_buttons:
                logger.error("❌ No se encontraron botones del ojo")
                return
            
            logger.info(f"✅ Total de botones encontrados para procesar: {len(found_buttons)}")
            
            # Procesar cada PQR
            successful_records = 0
            for idx, (selector, button_idx) in enumerate(found_buttons, 1):
                try:
                    logger.info(f"=== Procesando PQR #{idx} ===")
                    
                    # Obtener el botón específico
                    button = page.locator(selector).nth(button_idx)
                    
                    # Hacer clic derecho para abrir menú contextual
                    try:
                        button.click(button='right')
                        page.wait_for_timeout(1000)
                        
                        # Buscar opciones del menú contextual
                        context_menu_options = [
                            "text='Abrir en pestaña nueva'",
                            "text='Open in new tab'",
                            "text='Abrir enlace en pestaña nueva'",
                            "[data-action='open-new-tab']"
                        ]
                        
                        new_tab_opened = False
                        for option in context_menu_options:
                            try:
                                menu_item = page.locator(option).first
                                if menu_item.is_visible():
                                    menu_item.click()
                                    new_tab_opened = True
                                    logger.info(f"✅ Clic en menú contextual: {option}")
                                    break
                            except:
                                continue
                        
                        if not new_tab_opened:
                            # Fallback: usar JavaScript para abrir en nueva pestaña
                            href = button.get_attribute('href') or button.get_attribute('data-href')
                            if href:
                                page.evaluate(f"window.open('{href}', '_blank')")
                                logger.info("✅ Nueva pestaña abierta con JavaScript")
                            else:
                                logger.warning("⚠️ No se pudo obtener href para abrir nueva pestaña")
                                continue
                                
                    except Exception as click_error:
                        logger.warning(f"⚠️ Error con clic derecho: {click_error}")
                        # Fallback: clic normal
                        try:
                            button.click()
                            logger.info("✅ Clic normal ejecutado como fallback")
                        except Exception as fallback_error:
                            logger.error(f"❌ Error en fallback de clic: {fallback_error}")
                            continue
                    
                    # Esperar por nueva pestaña
                    page.wait_for_timeout(3000)
                    
                    # Verificar si se abrió nueva pestaña
                    context = page.context
                    pages = context.pages
                    
                    if len(pages) > 1:
                        # Cambiar a la nueva pestaña
                        new_page = pages[-1]
                        new_page.wait_for_load_state('networkidle', timeout=15000)
                        
                        # Extraer datos de la PQR
                        pqr_data = extract_pqr_data(new_page, idx)
                        
                        if pqr_data:
                            successful_records += 1
                            logger.info(f"✅ PQR #{idx} procesada exitosamente")
                        
                        # Cerrar la pestaña
                        new_page.close()
                        logger.info("✅ Pestaña cerrada después del procesamiento")
                        
                    else:
                        logger.warning(f"⚠️ No se detectó nueva pestaña para PQR #{idx}")
                    
                    # Pausa entre procesamiento
                    page.wait_for_timeout(2000)
                    
                except Exception as record_error:
                    logger.error(f"❌ Error procesando PQR #{idx}: {record_error}")
                    continue
            
            logger.info(f"✅ Procesados {successful_records} registros de PQR exitosamente")
        
        # Pausa para revisión manual
        logger.info("⏸️ Pausa de 30 segundos para revisión manual...")
        page.wait_for_timeout(30000)
        
    except Exception as e:
        logger.error(f"❌ Error en analyze_post_login_structure: {str(e)}")
        page.screenshot(path="downloads/afinia/new_version/error_post_login.png")

# Función principal
def main():
    """Función principal que ejecuta todo el flujo"""
    try:
        logger.info("🚀 Iniciando desarrollo paso a paso del nuevo extractor de Afinia")
        
        # Configurar navegador
        playwright, browser, context, page = setup_browser()
        
        try:
            # Paso 1: Navegar al portal
            navigate_to_new_afinia_portal(page)
            
            # Paso 2: Realizar login
            perform_login(page)
            
            # Paso 3: Analizar estructura post-login y procesar PQRs
            analyze_post_login_structure(page)
            
        finally:
             # Cerrar navegador
             browser.close()
             playwright.stop()
             logger.info("✅ Navegador cerrado correctamente")
            
    except Exception as e:
        logger.error(f"❌ Error en función principal: {str(e)}")
        raise

if __name__ == "__main__":
    main()