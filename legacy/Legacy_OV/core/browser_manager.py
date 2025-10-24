#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Browser Manager - Gestión Centralizada de Navegadores
====================================================

Este módulo centraliza toda la lógica de configuración y gestión de navegadores
para ExtractorOV, eliminando duplicación de código entre extractors.

Características principales:
- Configuración estándar de Playwright
- Manejo de contextos y páginas optimizado
- Configuración de viewport y opciones consistente
- Gestión automática de recursos (cleanup)
- Screenshots automáticos para debugging
- Timeouts optimizados por defecto

Basado en la implementación exitosa de oficina_virtual_afinia_extractor_new.py
"""

import os
import time
import asyncio
import logging
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

# Configurar logger específico para BrowserManager
logger = logging.getLogger('BROWSER-MANAGER')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[BROWSER-MANAGER] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

class BrowserManager:
    """Gestor centralizado de navegadores para ExtractorOV."""

    # Configuraciones por defecto optimizadas para visualización completa
    DEFAULT_VIEWPORT = {'width': 1920, 'height': 1080}  # Viewport estándar para contenido completo
    DEFAULT_TIMEOUT = 15000  # 15 segundos - Optimizado para mejor rendimiento

    # Argumentos de Chrome optimizados para web scraping sin factores de escala conflictivos
    DEFAULT_CHROME_ARGS = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--disable-extensions',
        '--disable-plugins',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--start-maximized',  # Maximizar ventana para ver página completa
        '--window-size=1920,1080',  # Tamaño de ventana específico
        '--enable-automation',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--ignore-certificate-errors',
        '--ignore-ssl-errors',
        '--ignore-certificate-errors-spki-list',
        '--allow-running-insecure-content'
    ]

    # Argumentos de Chrome optimizados para Ubuntu Server (headless)
    UBUNTU_SERVER_CHROME_ARGS = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--disable-extensions',
        '--disable-plugins',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--disable-gpu',  # Importante para servidores sin GPU
        '--disable-software-rasterizer',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--disable-field-trial-config',
        '--disable-ipc-flooding-protection',
        '--enable-automation',
        '--window-size=1920,1080',
        '--virtual-time-budget=5000',  # Para mejor estabilidad en servidor
        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '--ignore-certificate-errors',
        '--ignore-ssl-errors',
        '--ignore-certificate-errors-spki-list',
        '--allow-running-insecure-content'
    ]

    def __init__(self, headless: bool = False, 
                 viewport: Optional[Dict[str, int]] = None,
                 timeout: int = None,
                 screenshots_dir: str = "downloads/screenshots",
                 server_mode: bool = False):
        """
        Inicializa el gestor de navegador.

        Args:
            headless: Si ejecutar el navegador en modo headless
            viewport: Configuración de viewport personalizada
            timeout: Timeout por defecto en milisegundos
            screenshots_dir: Directorio para screenshots de debugging
            server_mode: Modo servidor (Ubuntu) con configuraciones optimizadas
        """
        self.headless = headless
        self.viewport = viewport or self.DEFAULT_VIEWPORT
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.screenshots_dir = screenshots_dir
        self.server_mode = server_mode
        
        logger.info(f"BrowserManager inicializado con timeout: {self.timeout}ms")

        # Seleccionar argumentos de Chrome según el modo
        if server_mode:
            self.chrome_args = self.UBUNTU_SERVER_CHROME_ARGS.copy()
            logger.info("Modo servidor Ubuntu activado")
        else:
            self.chrome_args = self.DEFAULT_CHROME_ARGS.copy()
            logger.info("Modo desktop activado")

        # Estados internos
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Asegurar que el directorio de screenshots existe
        os.makedirs(self.screenshots_dir, exist_ok=True)

        logger.info(f"BrowserManager inicializado - Headless: {headless}, Viewport: {self.viewport}")
        if server_mode:
            logger.info("Configuraciones optimizadas para Ubuntu Server aplicadas")

    async def setup_browser(self) -> Tuple[Browser, Page]:
        """
        Configura y lanza el navegador con opciones optimizadas.

        Returns:
            Tuple[Browser, Page]: Instancias del navegador y página configuradas
        """
        try:
            logger.info("Configurando navegador Playwright...")

            # Inicializar Playwright
            self.playwright = await async_playwright().start()

            # Lanzar navegador con argumentos apropiados
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=self.chrome_args
            )

            # Crear contexto del navegador
            self.context = await self.browser.new_context(
                viewport=self.viewport,
                device_scale_factor=0.8,  # Factor de escala optimizado para ver más contenido
                accept_downloads=True,
                ignore_https_errors=True,
                java_script_enabled=True,  # Habilitar JavaScript para funcionalidad completa
                bypass_csp=True,  # Bypass Content Security Policy si es necesario
                extra_http_headers={
                    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
                }
            )

            # Crear nueva página
            self.page = await self.context.new_page()

            # Configurar timeout por defecto
            self.page.set_default_timeout(self.timeout)
            self.context.set_default_timeout(self.timeout)
            
            # Debug: Verificar timeout configurado
            logger.info(f"Timeout configurado en página y contexto: {self.timeout}ms")

            # Configurar viewport
            await self.page.set_viewport_size(self.viewport)

            # Aplicar script de inicialización para zoom
            await self.page.add_init_script("""
                // Aplicar zoom out CSS al documento
                document.addEventListener('DOMContentLoaded', function() {
                    document.body.style.zoom = '0.75';
                    document.documentElement.style.zoom = '0.75';
                });

                // Aplicar zoom inmediatamente si el DOM ya está cargado
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', function() {
                        document.body.style.zoom = '0.75';
                        document.documentElement.style.zoom = '0.75';
                    });
                } else {
                    document.body.style.zoom = '0.75';
                    document.documentElement.style.zoom = '0.75';
                }
            """)

            logger.info("Navegador configurado exitosamente")
            return self.browser, self.page

        except Exception as e:
            logger.error(f"Error configurando navegador: {e}")
            await self.cleanup()
            raise

    async def navigate_to_url(self, url: str, wait_until: str = 'networkidle', timeout: int = None) -> bool:
        """
        Navega a una URL específica con manejo de errores.

        Args:
            url: URL de destino
            wait_until: Condición de espera ('load', 'domcontentloaded', 'networkidle')
            timeout: Timeout específico para esta navegación (opcional)

        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            if not self.page:
                raise Exception("Página no inicializada. Ejecutar setup_browser() primero.")

            # Usar timeout específico o el timeout configurado
            nav_timeout = timeout if timeout is not None else self.timeout
            logger.info(f"Navegando a: {url} con timeout: {nav_timeout}ms, wait_until: {wait_until}")
            
            # Intentar navegación
            response = await self.page.goto(url, wait_until=wait_until, timeout=nav_timeout)
            logger.info(f"Respuesta recibida: {response.status if response else 'None'}")
            
            # Esperar un momento para que la página se estabilice
            await asyncio.sleep(2)
            logger.info("Navegación completada exitosamente")
            return True

        except Exception as e:
            logger.error(f"Error navegando a {url}: {e}")
            await self.take_screenshot("navigation_error")
            return False

    async def take_screenshot(self, name: str, step: str = None) -> str:
        """
        Toma una captura de pantalla para debugging.

        Args:
            name: Nombre base del archivo
            step: Paso opcional para incluir en el nombre

        Returns:
            str: Ruta del archivo de screenshot creado
        """
        try:
            if not self.page:
                logger.warning("No se puede tomar screenshot: página no inicializada")
                return ""

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            step_prefix = f"{step}_" if step else ""
            filename = f"{step_prefix}{name}_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)

            await self.page.screenshot(path=filepath, full_page=True)
            logger.info(f"Screenshot guardado: {filepath}")
            return filepath

        except Exception as e:
            logger.warning(f"Error tomando screenshot: {e}")
            return ""

    async def wait_for_element(self, selector: str, timeout: int = None) -> Optional[Any]:
        """
        Espera por un elemento específico.

        Args:
            selector: Selector CSS del elemento
            timeout: Timeout personalizado en milisegundos

        Returns:
            Element si se encuentra, None si no
        """
        try:
            if not self.page:
                logger.warning("Página no inicializada")
                return None

            timeout = timeout or self.timeout
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            
            if element and await element.is_visible():
                logger.debug(f"Elemento encontrado: {selector}")
                return element
            else:
                logger.warning(f"Elemento no visible: {selector}")
                return None

        except Exception as e:
            logger.debug(f"Elemento no encontrado {selector}: {e}")
            return None

    async def safe_click(self, selector: str, description: str = "elemento") -> bool:
        """
        Hace click de forma segura en un elemento.

        Args:
            selector: Selector CSS del elemento
            description: Descripción del elemento para logs

        Returns:
            bool: True si el click fue exitoso
        """
        try:
            element = await self.wait_for_element(selector)
            if not element:
                logger.warning(f"No se puede hacer click en {description}: elemento no encontrado")
                return False

            # Verificar que el elemento esté habilitado
            if not await element.is_enabled():
                logger.warning(f"Elemento {description} no está habilitado")
                return False

            # Scroll al elemento si es necesario
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(0.5)  # Pequeña pausa para estabilizar

            # Hacer click
            await element.click()
            logger.info(f"Click realizado en {description}")
            return True

        except Exception as e:
            logger.error(f"Error haciendo click en {description}: {e}")
            await self.take_screenshot(f"click_error_{description}")
            return False

    async def safe_fill(self, selector: str, value: str, description: str = "campo") -> bool:
        """
        Llena un campo de forma segura.

        Args:
            selector: Selector CSS del campo
            value: Valor a llenar
            description: Descripción del campo para logs

        Returns:
            bool: True si el llenado fue exitoso
        """
        try:
            element = await self.wait_for_element(selector)
            if not element or not value:
                logger.warning(f"No se puede llenar {description}: elemento o valor inválido")
                return False

            # Limpiar campo primero
            await element.click()
            await element.fill("")
            await asyncio.sleep(0.3)

            # Llenar con el nuevo valor
            await element.fill(value)
            logger.info(f"Campo {description} llenado correctamente")
            return True

        except Exception as e:
            logger.error(f"Error llenando {description}: {e}")
            await self.take_screenshot(f"fill_error_{description}")
            return False

    async def wait_for_download(self, timeout: int = 30000) -> Optional[str]:
        """
        Espera por una descarga y retorna la ruta del archivo.

        Args:
            timeout: Timeout en milisegundos

        Returns:
            str: Ruta del archivo descargado o None si falló
        """
        try:
            if not self.page:
                logger.warning("Página no inicializada")
                return None

            logger.info("Esperando descarga...")
            
            # Esperar por el evento de descarga
            async with self.page.expect_download(timeout=timeout) as download_info:
                download = await download_info.value
                
                # Guardar el archivo
                download_path = os.path.join(self.screenshots_dir, download.suggested_filename)
                await download.save_as(download_path)
                
                logger.info(f"Archivo descargado: {download_path}")
                return download_path

        except Exception as e:
            logger.error(f"Error esperando descarga: {e}")
            return None

    async def execute_script(self, script: str) -> Any:
        """
        Ejecuta JavaScript en la página.

        Args:
            script: Código JavaScript a ejecutar

        Returns:
            Resultado de la ejecución del script
        """
        try:
            if not self.page:
                logger.warning("Página no inicializada")
                return None

            result = await self.page.evaluate(script)
            logger.debug("Script ejecutado exitosamente")
            return result

        except Exception as e:
            logger.error(f"Error ejecutando script: {e}")
            return None

    async def get_page_title(self) -> str:
        """
        Obtiene el título de la página actual.

        Returns:
            str: Título de la página
        """
        try:
            if not self.page:
                return ""
            
            title = await self.page.title()
            return title

        except Exception as e:
            logger.error(f"Error obteniendo título: {e}")
            return ""

    async def cleanup(self):
        """Limpia todos los recursos del navegador."""
        try:
            logger.info("Limpiando recursos del navegador...")

            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            logger.info("Recursos del navegador liberados exitosamente")

        except Exception as e:
            logger.warning(f"Error limpiando recursos: {e}")

    async def __aenter__(self):
        """Soporte para context manager async."""
        await self.setup_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Soporte para context manager async."""
        await self.cleanup()

    def __del__(self):
        """Destructor para asegurar limpieza de recursos."""
        try:
            # Solo intentar cleanup si hay un loop de eventos activo
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.cleanup())
        except:
            pass  # Ignorar errores en el destructor
