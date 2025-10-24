#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PopupHandler específico para Aire
Optimizado para cerrar solo el popup principal sin perder tiempo
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class AirePopupHandler:
    """
    PopupHandler específico para Aire
    Se enfoca únicamente en cerrar el popup principal #myModal
    """
    
    def __init__(self, page: Page):
        """
        Inicializa el manejador de popups específico de Aire
        
        Args:
            page: Página de Playwright
        """
        self.page = page
        self.logger = logger
        
    async def handle_aire_popup(self) -> bool:
        """
        Maneja específicamente el popup principal de Aire
        Se detiene inmediatamente después de cerrarlo exitosamente
        
        Returns:
            bool: True si el popup se cerró exitosamente o no existe
        """
        try:
            self.logger.info("Verificando popup principal de Aire...")
            
            # Verificar si el modal está visible
            modal_visible = await self.page.is_visible('#myModal')
            self.logger.info(f"Modal #myModal visible: {modal_visible}")
            
            if not modal_visible:
                self.logger.info("No hay popup visible, continuando...")
                return True
            
            # Selectores específicos del código legacy en orden de prioridad
            close_selectors = [
                "#myModal a.closePopUp i[ng-click=\"closeDialog()\"]",
                "#myModal i.material-icons[ng-click=\"closeDialog()\"]",
                "a.closePopUp i.material-icons",
                "#myModal .closePopUp",
                "i[ng-click=\"closeDialog()\"]",
                "#myModal a.closePopUp"
            ]
            
            # Intentar con cada selector
            for i, selector in enumerate(close_selectors, 1):
                try:
                    self.logger.info(f"Probando selector {i}/{len(close_selectors)}: {selector}")
                    close_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if close_element and await close_element.is_visible():
                        self.logger.info(f"Elemento de cierre encontrado con selector: {selector}")
                        
                        # Intentar clic normal
                        try:
                            await close_element.click()
                            await asyncio.sleep(1)
                            self.logger.info(f"Clic normal exitoso")
                            
                            # Verificar si el modal se cerró
                            modal_still_visible = await self.page.is_visible('#myModal')
                            if not modal_still_visible:
                                self.logger.info("Popup de Aire cerrado exitosamente")
                                return True
                            else:
                                self.logger.warning("Modal aún visible después del clic")
                                
                        except Exception as e:
                            self.logger.warning(f"Clic normal falló: {e}")
                        
                        # Intentar clic forzado si el normal falló
                        try:
                            await close_element.click(force=True)
                            await asyncio.sleep(1)
                            self.logger.info(f"Clic forzado exitoso")
                            
                            # Verificar si el modal se cerró
                            modal_still_visible = await self.page.is_visible('#myModal')
                            if not modal_still_visible:
                                self.logger.info("Popup de Aire cerrado exitosamente")
                                return True
                                
                        except Exception as e:
                            self.logger.warning(f"Clic forzado falló: {e}")
                        
                        # Intentar dispatch event
                        try:
                            await close_element.dispatch_event('click')
                            await asyncio.sleep(1)
                            self.logger.info(f"Dispatch event exitoso")
                            
                            # Verificar si el modal se cerró
                            modal_still_visible = await self.page.is_visible('#myModal')
                            if not modal_still_visible:
                                self.logger.info("Popup de Aire cerrado exitosamente")
                                return True
                                
                        except Exception as e:
                            self.logger.warning(f"Dispatch event falló: {e}")
                            
                except Exception as e:
                    self.logger.info(f"Selector {selector} no encontrado: {e}")
                    continue
            
            # Fallback con JavaScript como último recurso
            self.logger.info("Usando fallback JavaScript")
            try:
                js_code = """
                // Buscar y cerrar el modal de Aire
                const modal = document.querySelector('#myModal');
                if (modal && modal.style.display !== 'none') {
                    // Intentar con el botón de cierre específico
                    const closeBtn = modal.querySelector('a.closePopUp i[ng-click="closeDialog()"]');
                    if (closeBtn) {
                        closeBtn.click();
                        return 'closed_with_button';
                    }
                    
                    // Fallback: ocultar directamente
                    modal.style.display = 'none';
                    return 'closed_with_js';
                }
                return 'not_found';
                """
                
                result = await self.page.evaluate(js_code)
                self.logger.info(f"Resultado JavaScript: {result}")
                
                if result in ['closed_with_button', 'closed_with_js']:
                    self.logger.info("Popup cerrado con JavaScript fallback")
                    return True
                    
            except Exception as e:
                self.logger.error(f"Error en JavaScript fallback: {e}")
            
            # Si llegamos aquí, no se pudo cerrar el popup
            self.logger.warning("No se pudo cerrar el popup, continuando de todos modos...")
            return True  # Continuar aunque no se haya cerrado
            
        except Exception as e:
            self.logger.error(f"Error manejando popup de Aire: {e}")
            return True  # Continuar aunque haya error
            
    async def wait_and_handle_popup(self, max_wait_seconds: int = 10) -> bool:
        """
        Espera a que aparezca el popup y lo maneja
        
        Args:
            max_wait_seconds: Máximo tiempo de espera en segundos
            
        Returns:
            bool: True si se manejó exitosamente o no apareció popup
        """
        try:
            self.logger.info(f"Esperando popup de Aire (máximo {max_wait_seconds}s)...")
            
            # Esperar a que aparezca el modal o timeout
            try:
                await self.page.wait_for_selector('#myModal', timeout=max_wait_seconds * 1000)
                self.logger.info("Popup detectado, procediendo a cerrarlo...")
                return await self.handle_aire_popup()
            except PlaywrightTimeoutError:
                self.logger.info("No apareció popup en el tiempo esperado, continuando...")
                return True
                
        except Exception as e:
            self.logger.error(f"Error esperando popup: {e}")
            return True