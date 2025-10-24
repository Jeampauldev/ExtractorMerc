#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestor de filtros específico para Aire
Basado en el código legacy funcional
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class AireFilterManager:
    """
    Gestor de filtros específico para Aire
    Implementa la lógica exacta del código legacy funcional
    """
    
    def __init__(self, page: Page):
        """
        Inicializa el gestor de filtros
        
        Args:
            page: Página de Playwright
        """
        self.page = page
        self.logger = logger
        
    async def configure_filters_and_search(self, days_back: int = 1) -> bool:
        """
        Proceso completo de configuración de filtros y búsqueda
        Basado exactamente en el código legacy funcional
        
        Args:
            days_back: Días hacia atrás desde hoy para fecha inicial
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("=== INICIANDO CONFIGURACIÓN DE FILTROS (PROCESO LEGACY) ===")
            
            # PASO 1: Expandir panel de filtros (clic en "Filtrar")
            expand_success = await self._expand_filters_panel()
            if not expand_success:
                self.logger.warning("Error expandiendo panel de filtros, continuando...")
                
            # PASO 2: Configurar estado "Finalizado" (después de expandir)
            status_success = await self._configure_status_filter()
            if not status_success:
                self.logger.warning("Error configurando estado, continuando...")
                
            # PASO 3: Configurar fechas
            dates_success = await self._configure_date_filters(days_back)
            if not dates_success:
                self.logger.warning("Error configurando fechas, continuando...")
                
            # PASO 4: Ejecutar búsqueda
            search_success = await self._execute_search()
            if not search_success:
                self.logger.error("Error ejecutando búsqueda")
                return False
                
            # PASO 5: Colapsar panel de filtros (opcional)
            await self._collapse_filters_panel()
            
            self.logger.info("Configuración de filtros y búsqueda completada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en configuración de filtros: {str(e)}")
            return False
            
    async def _expand_filters_panel(self) -> bool:
        """
        Expande el panel de filtros haciendo clic en el botón 'Filtrar'
        Basado en los selectores del código legacy
        
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("=== PASO 1: Expandiendo panel de filtros ===")
            
            # Selectores exactos del código legacy funcional
            filter_button_selectors = [
                "a.accordion-toggle[ng-click='toggleOpen()']",
                "a[accordion-transclude='heading']",
                "a:has-text('Filtrar')",
                ".accordion-toggle:has-text('Filtrar')",
                "accordion .panel-heading a"
            ]
            
            filter_button = None
            
            for i, selector in enumerate(filter_button_selectors):
                try:
                    self.logger.info(f"Probando selector de filtrar {i+1}: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        filter_button = element
                        self.logger.info(f"Botón de filtrar encontrado con selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    self.logger.info(f"Selector {selector} no encontrado")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error con selector {selector}: {e}")
                    continue
            
            if not filter_button:
                raise Exception("Botón de filtrar no encontrado")
            
            # Hacer clic en el botón de filtrar
            self.logger.info("Haciendo clic en botón 'Filtrar'...")
            await filter_button.click()
            
            # Esperar a que se expanda el panel
            self.logger.info("Esperando expansión del panel...")
            await asyncio.sleep(2)
            
            self.logger.info("Panel de filtros expandido exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error expandiendo panel de filtros: {e}")
            return False
            
    async def _configure_status_filter(self) -> bool:
        """
        Configura el filtro de estado a "Finalizado" directamente
        Busca el campo Estado sin necesidad de expandir panel
        
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("=== PASO 2: Configurando estado 'Finalizado' ===")
            
            # Selectores exactos del código legacy funcional
            status_selectors = [
                "md-select[ng-model='filtros.Estado']",  # Nota: 'Estado' con mayúscula
                "md-select[name='Estado']",
                "#select_3",
                "md-select[aria-label*='Estado']"
            ]
            
            status_field = None
            
            for i, selector in enumerate(status_selectors):
                try:
                    self.logger.info(f"Probando selector de estado {i+1}: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        status_field = element
                        self.logger.info(f"Campo de estado encontrado con selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    self.logger.info(f"Selector {selector} no encontrado")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error con selector {selector}: {e}")
                    continue
            
            if not status_field:
                self.logger.warning("Campo de estado no encontrado")
                return False
            
            # Hacer clic en el campo de estado para abrirlo
            self.logger.info("Abriendo selector de estado...")
            await status_field.click()
            await asyncio.sleep(2)
            
            # Buscar y seleccionar la opción 'Finalizado' (selectores exactos del legacy)
            finalizado_selectors = [
                "md-option:has-text('Finalizado')",
                "md-option[value='Finalizado']",
                "[role='option']:has-text('Finalizado')",
                "md-select-menu md-option:has-text('Finalizado')"
            ]
            
            finalizado_option = None
            
            for i, selector in enumerate(finalizado_selectors):
                try:
                    self.logger.info(f"Probando selector de 'Finalizado' {i+1}: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        finalizado_option = element
                        self.logger.info(f"Opción 'Finalizado' encontrada con selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    self.logger.info(f"Selector {selector} no encontrado")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error con selector {selector}: {e}")
                    continue
            
            if not finalizado_option:
                self.logger.warning("Opción 'Finalizado' no encontrada")
                return False
            
            # Seleccionar 'Finalizado'
            self.logger.info("Seleccionando 'Finalizado'...")
            await finalizado_option.click()
            await asyncio.sleep(2)
            
            self.logger.info("Estado 'Finalizado' configurado exitosamente")
            return True
                
        except Exception as e:
            self.logger.error(f"Error configurando estado: {e}")
            return False
            
    async def _configure_date_filters(self, days_back: int = 1) -> bool:
        """
        Configura los filtros de fecha inicial y final
        Basado exactamente en el código legacy funcional
        
        Args:
            days_back: Días hacia atrás desde hoy para fecha inicial
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("=== PASO 3: Configurando filtros de fecha ===")
            
            # Calcular fechas (igual que en el legacy)
            today = datetime.now()
            start_date = today - timedelta(days=days_back)
            
            fecha_inicial = start_date.strftime("%Y-%m-%d")
            fecha_final = today.strftime("%Y-%m-%d")
            
            self.logger.info(f"Configurando fechas: Inicial={fecha_inicial}, Final={fecha_final}")
            
            # Configurar fecha inicial
            initial_success = await self._configure_initial_date(fecha_inicial)
            
            # Configurar fecha final
            final_success = await self._configure_final_date(fecha_final)
            
            if initial_success or final_success:
                self.logger.info("Filtros de fecha configurados exitosamente")
                return True
            else:
                self.logger.warning("No se pudieron configurar las fechas completamente")
                return False
                
        except Exception as e:
            self.logger.error(f"Error configurando fechas: {str(e)}")
            return False
            
    async def _configure_initial_date(self, fecha_inicial: str) -> bool:
        """
        Configura la fecha inicial usando los selectores del código legacy
        
        Args:
            fecha_inicial: Fecha en formato YYYY-MM-DD
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("Configurando fecha inicial...")
            
            # Selectores amplios para fecha inicial
            fecha_inicial_selectors = [
                "md-datepicker[ng-model='filtros.fechaInicial'] input",
                "input.md-datepicker-input[placeholder*='YYYY']",
                "input[placeholder*='Fecha inicial']",
                "input[placeholder*='fecha inicial']",
                "input[name*='fechaInicial']",
                "input[id*='fechaInicial']",
                ".campo-fecha input",
                "md-datepicker input",
                "input[type='date']",
                "input[placeholder*='YYYY-MM-DD']"
            ]
            
            fecha_inicial_field = None
            
            for i, selector in enumerate(fecha_inicial_selectors):
                try:
                    self.logger.info(f"Probando selector de fecha inicial {i+1}: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        fecha_inicial_field = element
                        self.logger.info(f"Campo de fecha inicial encontrado con selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    self.logger.info(f"Selector {selector} no encontrado")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error con selector {selector}: {e}")
                    continue
            
            if fecha_inicial_field:
                # Limpiar y llenar fecha inicial (igual que en legacy)
                await fecha_inicial_field.click()
                await fecha_inicial_field.fill("")
                await fecha_inicial_field.type(fecha_inicial)
                self.logger.info(f"Fecha inicial configurada: {fecha_inicial}")
                await asyncio.sleep(1)
                return True
            else:
                self.logger.warning("Campo de fecha inicial no encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"Error configurando fecha inicial: {e}")
            return False
            
    async def _configure_final_date(self, fecha_final: str) -> bool:
        """
        Configura la fecha final usando los selectores del código legacy
        
        Args:
            fecha_final: Fecha en formato YYYY-MM-DD
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("Configurando fecha final...")
            
            # Selectores amplios para fecha final
            fecha_final_selectors = [
                "md-datepicker[ng-model='filtros.fechaFinal'] input",
                "input[placeholder*='Fecha final']",
                "input[placeholder*='fecha final']",
                "input[name*='fechaFinal']",
                "input[id*='fechaFinal']",
                "md-datepicker:nth-of-type(2) input",  # Segundo datepicker
                ".campo-fecha:nth-of-type(2) input",
                "input[type='date']:nth-of-type(2)",
                "input[placeholder*='YYYY-MM-DD']:nth-of-type(2)"
            ]
            
            fecha_final_field = None
            
            for i, selector in enumerate(fecha_final_selectors):
                try:
                    self.logger.info(f"Probando selector de fecha final {i+1}: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        fecha_final_field = element
                        self.logger.info(f"Campo de fecha final encontrado con selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    self.logger.info(f"Selector {selector} no encontrado")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error con selector {selector}: {e}")
                    continue
            
            if fecha_final_field:
                # Limpiar y llenar fecha final (igual que en legacy)
                await fecha_final_field.click()
                await fecha_final_field.fill("")
                await fecha_final_field.type(fecha_final)
                self.logger.info(f"Fecha final configurada: {fecha_final}")
                await asyncio.sleep(1)
                return True
            else:
                self.logger.warning("Campo de fecha final no encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"Error configurando fecha final: {e}")
            return False
            
    async def _execute_search(self) -> bool:
        """
        Ejecuta la búsqueda usando el botón de buscar
        Basado en los selectores del código legacy
        
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("=== PASO 4: Ejecutando búsqueda ===")
            
            # Selectores exactos del código legacy funcional
            search_button_selectors = [
                "button[ng-click='Search()'][aria-label='Buscar']",
                "button.md-raised.md-primary:has-text('Buscar')",
                "button[aria-label='Buscar']",
                "button:has-text('Buscar')",
                "input[type='submit'][value*='Buscar']"
            ]
            
            search_button = None
            
            for i, selector in enumerate(search_button_selectors):
                try:
                    self.logger.info(f"Probando selector de búsqueda {i+1}: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        search_button = element
                        self.logger.info(f"Botón de búsqueda encontrado con selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    self.logger.info(f"Selector {selector} no encontrado")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error con selector {selector}: {e}")
                    continue
            
            if search_button:
                # Hacer clic en el botón de búsqueda
                await search_button.click()
                self.logger.info("Clic en botón de búsqueda ejecutado")
                
                # Esperar resultados (igual que en legacy)
                self.logger.info("Esperando resultados...")
                await self.page.wait_for_load_state('networkidle', timeout=30000)
                await asyncio.sleep(3)
                
                return True
            else:
                self.logger.error("No se encontró botón de búsqueda")
                return False
                
        except Exception as e:
            self.logger.error(f"Error ejecutando búsqueda: {e}")
            return False
            
    async def _collapse_filters_panel(self) -> bool:
        """
        Colapsa el panel de filtros (opcional)
        
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("=== PASO 5: Colapsando panel de filtros ===")
            
            # Selectores para colapsar
            filter_toggle_selectors = [
                "a.accordion-toggle[ng-click='toggleOpen()']",
                ".accordion-toggle:has-text('Filtrar')",
                ".panel-title a.accordion-toggle",
                "a[accordion-transclude='heading']:has-text('Filtrar')"
            ]
            
            for selector in filter_toggle_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element and await element.is_visible():
                        await element.click()
                        self.logger.info("Panel de filtros colapsado")
                        await asyncio.sleep(1)
                        return True
                except:
                    continue
                    
            self.logger.info("No se pudo colapsar el panel (no crítico)")
            return True
            
        except Exception as e:
            self.logger.warning(f"Error colapsando panel: {e}")
            return True  # No es crítico