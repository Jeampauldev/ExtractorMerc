#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PopupHandler específico para Afinia
Optimizado para cerrar solo el popup principal sin perder tiempo
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger('AFINIA-POPUP')

class AfiniaPopupHandler:
    """
    PopupHandler específico para Afinia
    Se enfoca únicamente en cerrar el popup principal #myModal
    """
    
    def __init__(self, page: Page):
        """
        Inicializa el manejador de popups específico de Afinia
        
        Args:
            page: Página de Playwright
        """
        self.page = page
        self.logger = logger
        
    async def handle_afinia_popup(self) -> bool:
        """
        Maneja específicamente el popup principal de Afinia
        Se detiene inmediatamente después de cerrarlo exitosamente
        
        Returns:
            bool: True si el popup se cerró exitosamente o no existe
        """
        try:
            self.logger.info("VERIFICANDO Verificando popup principal de Afinia...")
            
            # Verificar si el modal está visible
            modal_visible = await self.page.is_visible('#myModal')
            self.logger.info(f"Modal #myModal visible: {modal_visible}")
            
            if not modal_visible:
                self.logger.info("EXITOSO No hay popup visible, continuando...")
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
                    self.logger.info(f"OBJETIVO Probando selector {i}/{len(close_selectors)}: {selector}")
                    close_element = await self.page.wait_for_selector(selector, timeout=3000)
                    if close_element and await close_element.is_visible():
                        self.logger.info(f"EXITOSO Elemento de cierre encontrado con selector: {selector}")
                        
                        # Intentar clic normal
                        try:
                            await close_element.click()
                            await asyncio.sleep(1)
                            self.logger.info(f"EXITOSO Clic normal exitoso")
                            
                            # Verificar si el modal se cerró
                            modal_still_visible = await self.page.is_visible('#myModal')
                            if not modal_still_visible:
                                self.logger.info("EXITOSO Popup de Afinia cerrado exitosamente")
                                return True
                            else:
                                self.logger.warning("ADVERTENCIA Modal aún visible después del clic")
                                
                        except Exception as e:
                            self.logger.warning(f"ADVERTENCIA Clic normal falló: {e}")
                        
                        # Intentar clic forzado si el normal falló
                        try:
                            await close_element.click(force=True)
                            await asyncio.sleep(1)
                            self.logger.info(f"EXITOSO Clic forzado exitoso")
                            
                            # Verificar si el modal se cerró
                            modal_still_visible = await self.page.is_visible('#myModal')
                            if not modal_still_visible:
                                self.logger.info("EXITOSO Popup de Afinia cerrado exitosamente")
                                return True
                                
                        except Exception as e:
                            self.logger.warning(f"ADVERTENCIA Clic forzado falló: {e}")
                        
                        # Intentar dispatch event
                        try:
                            await close_element.dispatch_event('click')
                            await asyncio.sleep(1)
                            self.logger.info(f"EXITOSO Dispatch event exitoso")
                            
                            # Verificar si el modal se cerró
                            modal_still_visible = await self.page.is_visible('#myModal')
                            if not modal_still_visible:
                                self.logger.info("EXITOSO Popup de Afinia cerrado exitosamente")
                                return True
                                
                        except Exception as e:
                            self.logger.warning(f"ADVERTENCIA Dispatch event falló: {e}")
                            
                except Exception as e:
                    self.logger.info(f"ADVERTENCIA Selector {selector} no encontrado: {e}")
                    continue
            
            # Fallback con JavaScript como último recurso
            self.logger.info("CONFIGURANDO Usando fallback JavaScript")
            try:
                js_code = """
                // Buscar y cerrar el modal de Afinia
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
                    self.logger.info("EXITOSO Popup cerrado con JavaScript fallback")
                    return True
                    
            except Exception as e:
                self.logger.error(f"Error en JavaScript fallback: {e}")
            
            # Si llegamos aquí, no se pudo cerrar el popup
            self.logger.warning("ADVERTENCIA No se pudo cerrar el popup, continuando de todos modos...")
            return True  # Continuar aunque no se haya cerrado
            
        except Exception as e:
            self.logger.error(f"ERROR Error manejando popup de Afinia: {e}")
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
            self.logger.info(f"ESPERANDO Esperando popup de Afinia (máximo {max_wait_seconds}s)...")
            
            # Esperar a que aparezca el modal o timeout
            try:
                await self.page.wait_for_selector('#myModal', timeout=max_wait_seconds * 1000)
                self.logger.info("VERIFICANDO Popup detectado, procediendo a cerrarlo...")
                return await self.handle_afinia_popup()
            except PlaywrightTimeoutError:
                self.logger.info("EXITOSO No apareció popup en el tiempo esperado, continuando...")
                return True
                
        except Exception as e:
            self.logger.error(f"Error esperando popup: {e}")
            return True
