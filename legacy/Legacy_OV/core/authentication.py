#!/usr/bin/env python3
"""
Authentication Manager - Sistema de Autenticación Centralizado
============================================================

Este módulo centraliza toda la lógica de autenticación para ExtractorOV,
eliminando duplicación de código entre extractors y proporcionando
estrategias robustas de login.

Características principales:
- Login genérico con múltiples estrategias
- Manejo de credenciales desde configuración
- Verificación automática de login exitoso
- Screenshots automáticos para debugging
- Manejo de popups y diálogos
- Múltiples estrategias de fallback

Basado en las implementaciones exitosas de los extractores legacy.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

# Configurar logger específico para AuthenticationManager
logger = logging.getLogger('AUTH-MANAGER')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[AUTH-MANAGER] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

class AuthenticationManager:
    """Gestor centralizado de autenticación para ExtractorOV."""

    # Selectores comunes para campos de usuario
    COMMON_USERNAME_SELECTORS = [
        'input[name="usuario"]',
        'input[name="username"]',
        'input[name="email"]',
        'input[name="user"]',
        'input[type="text"]:first-of-type',
        'input[type="email"]',
        '.form-control:first-of-type',
        '#username',
        '#usuario',
        '#email'
    ]

    # Selectores comunes para campos de contraseña
    COMMON_PASSWORD_SELECTORS = [
        'input[name="clave"]',
        'input[name="contrasena"]',
        'input[name="password"]',
        'input[name="pass"]',
        'input[type="password"]',
        '.form-control[type="password"]',
        '#password',
        '#clave',
        '#contrasena'
    ]

    # Selectores comunes para botones de login
    COMMON_LOGIN_BUTTON_SELECTORS = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Ingresar")',
        'button:has-text("INGRESAR")',
        'button:has-text("Login")',
        'button:has-text("Entrar")',
        'input[value="Ingresar"]',
        'input[value="Login"]',
        '.btn-login',
        '.login-button',
        '#login-button',
        '#submit'
    ]

    # Selectores para verificación de login exitoso
    COMMON_SUCCESS_INDICATORS = [
        'a:has-text("Consultas")',
        '*:has-text("Consultas")',
        'a:has-text("CONSULTAS")',
        '*:has-text("CONSULTAS")',
        'a[href*="consulta"]',
        '.menu',
        '.navbar',
        '.sidebar',
        'iframe',
        'frame',
        'table'
    ]

    def __init__(self, page: Page, screenshots_dir: str = "downloads/screenshots"):
        """
        Inicializa el gestor de autenticación.

        Args:
            page: Página de Playwright para interactuar
            screenshots_dir: Directorio para screenshots de debugging
        """
        self.page = page
        self.screenshots_dir = screenshots_dir

        # Configurar manejador de diálogos por defecto
        self.page.on("dialog", lambda dialog: dialog.accept())

        logger.info(f"AuthenticationManager inicializado para página: {self.page.url}")

    async def login(self, username: str, password: str,
              username_selectors: Optional[List[str]] = None,
              password_selectors: Optional[List[str]] = None,
              login_button_selectors: Optional[List[str]] = None,
              success_indicators: Optional[List[str]] = None,
              take_screenshots: bool = True) -> bool:
        """
        Realiza login con múltiples estrategias de fallback.

        Args:
            username: Nombre de usuario
            password: Contraseña
            username_selectors: Selectores personalizados para campo usuario (opcional)
            password_selectors: Selectores personalizados para campo contraseña (opcional)
            login_button_selectors: Selectores personalizados para botón login (opcional)
            success_indicators: Selectores personalizados para verificación (opcional)
            take_screenshots: Si tomar screenshots para debugging

        Returns:
            True si el login fue exitoso, False en caso contrario
        """
        logger.info(f"Iniciando proceso de login para usuario: {username}")

        # Usar selectores personalizados o por defecto
        username_sels = username_selectors or self.COMMON_USERNAME_SELECTORS
        password_sels = password_selectors or self.COMMON_PASSWORD_SELECTORS
        button_sels = login_button_selectors or self.COMMON_LOGIN_BUTTON_SELECTORS
        success_sels = success_indicators or self.COMMON_SUCCESS_INDICATORS

        try:
            # Screenshot inicial solo en caso de error
            # (Removido screenshot rutinario inicial)

            # Paso 1: Llenar campo de usuario
            if not await self._fill_username_field(username, username_sels):
                logger.error("No se pudo llenar el campo de usuario")
                return False

            # Paso 2: Llenar campo de contraseña
            if not await self._fill_password_field(password, password_sels):
                logger.error("No se pudo llenar el campo de contraseña")
                return False

            # Screenshot después de llenar credenciales solo en caso de error
            # (Removido screenshot rutinario después de credenciales)

            # Paso 3: Hacer clic en botón de login
            if not await self._click_login_button(button_sels):
                logger.error("No se pudo hacer clic en el botón de login")
                return False

            # Paso 4: Esperar a que se procese el login
            await self._wait_for_login_processing()

            # Screenshot después del login solo en caso de error
            # (Removido screenshot rutinario después del login)

            # Paso 5: Verificar que el login fue exitoso
            if await self._verify_login_success(success_sels):
                logger.info("Login exitoso verificado")

                # Configuraciones post-login
                await self._post_login_setup()

                return True
            else:
                logger.error("Login falló - no se pudo verificar éxito")
                if take_screenshots:
                    await self._take_screenshot("login_verification_failed")
                return False

        except Exception as e:
            logger.error(f"Error durante el proceso de login: {str(e)}")
            if take_screenshots:
                await self._take_screenshot("login_exception")
            return False

    async def _fill_username_field(self, username: str, selectors: List[str]) -> bool:
        """
        Llena el campo de usuario usando múltiples estrategias.

        Args:
            username: Nombre de usuario
            selectors: Lista de selectores a probar

        Returns:
            True si se llenó exitosamente, False si falló
        """
        logger.info("Intentando llenar campo de usuario...")

        # Análisis de campos disponibles
        all_inputs = await self.page.query_selector_all("input")
        logger.info(f"Encontrados {len(all_inputs)} campos de entrada en la página")

        for i, input_elem in enumerate(all_inputs[:5]):  # Limitar análisis
            try:
                input_type = await input_elem.get_attribute("type") or "text"
                input_name = await input_elem.get_attribute("name") or "sin_nombre"
                input_id = await input_elem.get_attribute("id") or "sin_id"
                logger.info(f"Campo {i+1}: tipo='{input_type}', nombre='{input_name}', id='{input_id}'")
            except Exception as e:
                logger.warning(f"Error analizando campo {i+1}: {e}")

        # Intentar con cada selector
        for selector in selectors:
            try:
                logger.info(f"Probando selector de usuario: {selector}")
                username_field = await self.page.wait_for_selector(selector, timeout=3000)

                if username_field and await username_field.is_visible():
                    # Llenar el campo
                    await username_field.click()
                    await username_field.fill("")  # Limpiar primero
                    time.sleep(0.1)
                    await username_field.type(username, delay=50)

                    # Verificar que se llenó correctamente
                    filled_value = await username_field.input_value()
                    if filled_value == username:
                        logger.info(f"Campo de usuario llenado correctamente con selector: {selector}")
                        return True
                    else:
                        logger.warning(f"Campo llenado incorrectamente: esperado '{username}', obtenido '{filled_value}'")

            except PlaywrightTimeoutError:
                logger.debug(f"Selector {selector} no encontrado (timeout)")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue

        # Fallback con JavaScript
        logger.info("Intentando llenar usuario con JavaScript fallback...")
        try:
            js_result = await self.page.evaluate(f"""
                () => {{
                    const inputs = document.querySelectorAll('input[type="text"], input:not([type]), input[type="email"]');
                    for (let input of inputs) {{
                        if (input.offsetParent !== null) {{ // visible
                            input.value = '{username}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                    }}
                    return false;
                }}
            """)

            if js_result:
                logger.info("Campo de usuario llenado con JavaScript fallback")
                return True

        except Exception as e:
            logger.warning(f"Error en JavaScript fallback para usuario: {e}")

        logger.error("No se pudo llenar el campo de usuario con ninguna estrategia")
        return False

    async def _fill_password_field(self, password: str, selectors: List[str]) -> bool:
        """
        Llena el campo de contraseña usando múltiples estrategias.

        Args:
            password: Contraseña
            selectors: Lista de selectores a probar

        Returns:
            True si se llenó exitosamente, False si falló
        """
        logger.info("Intentando llenar campo de contraseña...")

        # Intentar con cada selector
        for selector in selectors:
            try:
                logger.info(f"Probando selector de contraseña: {selector}")
                password_field = await self.page.wait_for_selector(selector, timeout=3000)

                if password_field and await password_field.is_visible():
                    # Llenar el campo
                    await password_field.click()
                    await password_field.fill("")  # Limpiar primero
                    time.sleep(0.1)
                    await password_field.type(password, delay=50)

                    # Verificar que se llenó (sin mostrar la contraseña en logs)
                    filled_value = await password_field.input_value()
                    if filled_value == password:
                        logger.info(f"Campo de contraseña llenado correctamente con selector: {selector}")
                        return True
                    else:
                        logger.warning("Campo de contraseña no se llenó correctamente")

            except PlaywrightTimeoutError:
                logger.debug(f"Selector {selector} no encontrado (timeout)")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue

        # Fallback con JavaScript
        logger.info("Intentando llenar contraseña con JavaScript fallback...")
        try:
            js_result = await self.page.evaluate(f"""
                () => {{
                    const inputs = document.querySelectorAll('input[type="password"]');
                    for (let input of inputs) {{
                        if (input.offsetParent !== null) {{ // visible
                            input.value = '{password}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                    }}
                    return false;
                }}
            """)

            if js_result:
                logger.info("Campo de contraseña llenado con JavaScript fallback")
                return True

        except Exception as e:
            logger.warning(f"Error en JavaScript fallback para contraseña: {e}")

        logger.error("No se pudo llenar el campo de contraseña con ninguna estrategia")
        return False

    async def _click_login_button(self, selectors: List[str]) -> bool:
        """
        Hace clic en el botón de login usando múltiples estrategias.

        Args:
            selectors: Lista de selectores a probar

        Returns:
            True si se hizo clic exitosamente, False si falló
        """
        logger.info("Intentando hacer clic en botón de login...")

        # Intentar con cada selector
        for selector in selectors:
            try:
                logger.info(f"Probando selector de botón: {selector}")
                login_button = await self.page.wait_for_selector(selector, timeout=3000)

                if login_button and await login_button.is_visible():
                    # Hacer clic en el botón
                    await login_button.click()
                    logger.info(f"Clic exitoso en botón con selector: {selector}")
                    return True

            except PlaywrightTimeoutError:
                logger.debug(f"Selector {selector} no encontrado (timeout)")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue

        # Fallback con JavaScript
        logger.info("Intentando hacer clic con JavaScript fallback...")
        try:
            js_result = await self.page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button[type="submit"], input[type="submit"], button');
                    for (let button of buttons) {
                        if (button.offsetParent !== null) { // visible
                            const text = button.textContent || button.value || '';
                            if (text.toLowerCase().includes('ingresar') || 
                                text.toLowerCase().includes('login') || 
                                text.toLowerCase().includes('entrar')) {
                                button.click();
                                return true;
                            }
                        }
                    }
                    return false;
                }
            """)

            if js_result:
                logger.info("Clic en botón realizado con JavaScript fallback")
                return True

        except Exception as e:
            logger.warning(f"Error en JavaScript fallback para botón: {e}")

        logger.error("No se pudo hacer clic en el botón de login con ninguna estrategia")
        return False

    async def _wait_for_login_processing(self):
        """Espera a que se procese el login."""
        logger.info("Esperando procesamiento del login...")
        time.sleep(2)  # Espera básica

        # Esperar a que desaparezcan posibles indicadores de carga
        try:
            await self.page.wait_for_selector('.loading, .spinner, .progress', state='detached', timeout=5000)
        except PlaywrightTimeoutError:
            pass  # No hay problema si no hay indicadores de carga

    async def _verify_login_success(self, selectors: List[str]) -> bool:
        """
        Verifica que el login fue exitoso buscando indicadores de éxito.

        Args:
            selectors: Lista de selectores que indican login exitoso

        Returns:
            True si se verificó el éxito, False si falló
        """
        logger.info("Verificando éxito del login...")

        # OPTIMIZACIÓN AFINIA: Verificar cambio de URL PRIMERO (más rápido)
        try:
            current_url = self.page.url
            if 'login' not in current_url.lower() and 'signin' not in current_url.lower():
                logger.info("Login exitoso verificado por cambio de URL")
                return True
        except Exception as e:
            logger.debug(f"Error verificando URL: {e}")

        # Esperar un poco para que cargue la página
        time.sleep(0.5)  # Reducido de 1s a 0.5s

        # Intentar con cada selector (con timeout reducido)
        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=2000)  # Reducido de 5000ms a 2000ms
                if element and await element.is_visible():
                    logger.info(f"Login exitoso verificado con selector: {selector}")
                    return True
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Error verificando con selector {selector}: {e}")
                continue

        # Para Afinia: verificar elementos específicos con timeout reducido
        try:
            afinia_elements = ['iframe', 'table']
            for element_selector in afinia_elements:
                try:
                    element = await self.page.wait_for_selector(element_selector, timeout=1000)  # Reducido de 2000ms a 1000ms
                    if element:
                        logger.info(f"Login exitoso verificado por presencia de: {element_selector}")
                        return True
                except PlaywrightTimeoutError:
                    continue
        except Exception as e:
            logger.debug(f"Error en verificaciones adicionales: {e}")

        logger.warning("No se pudo verificar el éxito del login")
        return False

    async def _post_login_setup(self):
        """Configuraciones adicionales después del login exitoso."""
        logger.info("Ejecutando configuraciones post-login...")

        # Verificar si se encuentra en la página de inicio
        try:
            await self.page.wait_for_selector('#main', timeout=2000)
            logger.info("Página de inicio encontrada")
        except PlaywrightTimeoutError:
            logger.debug("Página de inicio no encontrada")
            # Manejar posibles popups post-login
            await self._handle_post_login_popups()

            # Esperar a que se estabilice la página
            time.sleep(1)

        except Exception as e:
            logger.warning(f"Error en configuraciones post-login: {e}")

    async def _handle_post_login_popups(self):
        """Maneja popups que pueden aparecer después del login."""
        try:
            # Buscar y cerrar popups comunes
            popup_selectors = [
                'button:has-text("Cerrar")',
                'button:has-text("OK")',
                'button:has-text("Aceptar")',
                '.close',
                '.modal-close',
                '[aria-label="Close"]'
            ]

            for selector in popup_selectors:
                try:
                    popup_button = await self.page.wait_for_selector(selector, timeout=1000)
                    if popup_button and await popup_button.is_visible():
                        await popup_button.click()
                        logger.info(f"Popup cerrado con selector: {selector}")
                        time.sleep(0.5)
                except PlaywrightTimeoutError:
                    continue

        except Exception as e:
            logger.debug(f"Error manejando popups post-login: {e}")

    async def _take_screenshot(self, name: str):
        """
        Toma un screenshot para debugging.

        Args:
            name: Nombre del screenshot
        """
        try:
            import os
            os.makedirs(self.screenshots_dir, exist_ok=True)
            screenshot_path = f"{self.screenshots_dir}/{name}_{int(time.time())}.png"
            await self.page.screenshot(path=screenshot_path)
            logger.debug(f"Screenshot guardado: {screenshot_path}")
        except Exception as e:
            logger.error(f"Error tomando screenshot {name}: {e}")

    async def is_logged_in(self, success_indicators: Optional[List[str]] = None) -> bool:
        """
        Verifica si ya está logueado.

        Args:
            success_indicators: Selectores personalizados para verificación

        Returns:
            True si está logueado, False si no
        """
        selectors = success_indicators or self.COMMON_SUCCESS_INDICATORS
        return await self._verify_login_success(selectors)

    async def logout(self, logout_selectors: Optional[List[str]] = None) -> bool:
        """
        Realiza logout si es posible.

        Args:
            logout_selectors: Selectores para botones de logout

        Returns:
            True si se realizó logout, False si no
        """
        default_logout_selectors = [
            'a:has-text("Salir")',
            'a:has-text("Logout")',
            'a:has-text("Cerrar Sesión")',
            'button:has-text("Salir")',
            'button:has-text("Logout")',
            '.logout',
            '#logout'
        ]

        selectors = logout_selectors or default_logout_selectors

        for selector in selectors:
            try:
                logout_element = await self.page.wait_for_selector(selector, timeout=2000)
                if logout_element and await logout_element.is_visible():
                    await logout_element.click()
                    logger.info(f"Logout realizado con selector: {selector}")
                    time.sleep(1)
                    return True
            except PlaywrightTimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Error con selector de logout {selector}: {e}")
                continue

        logger.info("No se encontró opción de logout")
        return False
