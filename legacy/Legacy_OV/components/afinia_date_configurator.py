#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configurador de fechas específico para Afinia
Basado en el código legacy funcional
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class AfiniaDateConfigurator:
    """
    Configurador de fechas específico para Afinia
    Implementa la lógica exacta del código legacy funcional
    """
    
    def __init__(self, page: Page):
        """
        Inicializa el configurador de fechas
        
        Args:
            page: Página de Playwright
        """
        self.page = page
        self.logger = logger
        
    async def configure_date_filters(self, days_back: int = 1) -> bool:
        """
        Configura los filtros de fecha inicial y final
        Basado exactamente en el código legacy funcional
        
        Args:
            days_back: Días hacia atrás desde hoy para fecha inicial
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            self.logger.info("=== CONFIGURANDO FILTROS DE FECHA ===")
            
            # Calcular fechas (igual que en el legacy)
            today = datetime.now()
            start_date = today - timedelta(days=days_back)
            
            fecha_inicial = start_date.strftime("%Y-%m-%d")
            fecha_final = today.strftime("%Y-%m-%d")
            
            self.logger.info(f"Configurando fechas: Inicial={fecha_inicial}, Final={fecha_final}")
            
            # Configurar fecha inicial
            await self._configure_initial_date(fecha_inicial)
            
            # Configurar fecha final
            await self._configure_final_date(fecha_final)
            
            self.logger.info("[EXITOSO] Filtros de fecha configurados exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error configurando fechas: {str(e)}")
            raise
            
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
            
            # Selectores exactos del código legacy funcional
            fecha_inicial_selectors = [
                "md-datepicker[ng-model='filtros.fechaInicial'] input",
                "input.md-datepicker-input[placeholder='YYYY-MM-DD']",
                "md-datepicker[name='Fecha inicial'] input",
                ".campo-fecha input[placeholder*='YYYY-MM-DD']"
            ]
            
            fecha_inicial_field = None
            
            for i, selector in enumerate(fecha_inicial_selectors):
                try:
                    self.logger.info(f"Probando selector de fecha inicial {i+1}: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        fecha_inicial_field = element
                        self.logger.info(f"[EXITOSO] Campo de fecha inicial encontrado con selector: {selector}")
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
                self.logger.info(f"[EXITOSO] Fecha inicial configurada: {fecha_inicial}")
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
            
            # Selectores exactos del código legacy funcional
            fecha_final_selectors = [
                "md-datepicker[ng-model='filtros.fechaFinal'] input",
                "md-datepicker[name='Fecha inicial']:nth-of-type(2) input",  # Segundo datepicker
                ".campo-fecha:nth-of-type(2) input[placeholder*='YYYY-MM-DD']"
            ]
            
            fecha_final_field = None
            
            for i, selector in enumerate(fecha_final_selectors):
                try:
                    self.logger.info(f"Probando selector de fecha final {i+1}: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        fecha_final_field = element
                        self.logger.info(f"[EXITOSO] Campo de fecha final encontrado con selector: {selector}")
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
                self.logger.info(f"[EXITOSO] Fecha final configurada: {fecha_final}")
                await asyncio.sleep(1)
                return True
            else:
                self.logger.warning("Campo de fecha final no encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"Error configurando fecha final: {e}")
            return False
