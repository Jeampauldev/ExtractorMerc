"""
AIRE PAGINATION MANAGER
Sistema de paginación automática para procesamiento masivo de PQR
Optimizado para servidor Linux con controles de pausa/parada
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger('AIRE-PAGINATION')

@dataclass
class PaginationState:
    """Estado de la paginación"""
    current_page: int = 1
    total_records: int = 0
    processed_records: int = 0
    records_per_page: int = 10
    total_pages: int = 0
    session_start: str = ""
    last_checkpoint: str = ""
    is_paused: bool = False
    is_stopped: bool = False

class AirePaginationManager:
    """Gestor de paginación automática para Aire"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.control_dir = self.base_dir / "pagination_control"
        self.checkpoint_dir = self.base_dir / "checkpoints"
        self.control_dir.mkdir(exist_ok=True)
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        # Archivos de control
        self.pause_file = self.control_dir / "PAUSE"
        self.stop_file = self.control_dir / "STOP"
        self.resume_file = self.control_dir / "RESUME"
        self.status_file = self.control_dir / "STATUS.json"
        
        # Estado
        self.state = PaginationState()
        
        # Configuración para servidor
        self.max_records_per_session = int(os.getenv('MAX_RECORDS_PER_SESSION', '50'))
        self.checkpoint_frequency = int(os.getenv('CHECKPOINT_FREQUENCY', '10'))  # Cada 10 registros
        self.pause_between_pages = float(os.getenv('PAUSE_BETWEEN_PAGES', '3.0'))  # 3 segundos
        
        logger.info(f"PaginationManager inicializado")
        logger.info(f"Control dir: {self.control_dir}")
        logger.info(f"Checkpoint dir: {self.checkpoint_dir}")
        logger.info(f"Max records per session: {self.max_records_per_session}")

    def _check_control_signals(self) -> str:
        """Verificar archivos de control para pausar/detener"""
        if self.stop_file.exists():
            logger.warning("SEÑAL DE PARADA DETECTADA")
            self.state.is_stopped = True
            return "STOP"
            
        if self.pause_file.exists() and not self.resume_file.exists():
            if not self.state.is_paused:
                logger.warning("SEÑAL DE PAUSA DETECTADA")
                self.state.is_paused = True
            return "PAUSE"
            
        if self.resume_file.exists():
            if self.state.is_paused:
                logger.info("SEÑAL DE REANUDACIÓN DETECTADA")
                self.state.is_paused = False
                # Limpiar archivo de pausa y reanudación
                self.pause_file.unlink(missing_ok=True)
                self.resume_file.unlink(missing_ok=True)
            return "RESUME"
            
        return "CONTINUE"

    async def extract_pagination_info(self, page) -> Tuple[int, int, int]:
        """Extraer información de paginación de la página"""
        try:
            # Buscar el elemento con información de paginación
            pagination_selectors = [
                "div.label.ng-binding",  # Selector específico del HTML proporcionado
                ".md-table-pagination .label",
                "[class*='pagination'] .label",
                ".pagination-info"
            ]
            
            for selector in pagination_selectors:
                try:
                    elements = page.locator(selector)
                    count = await elements.count()
                    
                    for i in range(count):
                        element = elements.nth(i)
                        text = await element.inner_text()
                        
                        # Buscar patrón "1 - 10 de 333529"
                        if " de " in text and "-" in text:
                            parts = text.split(" de ")
                            if len(parts) == 2:
                                range_part = parts[0].strip()  # "1 - 10"
                                total_str = parts[1].strip()   # "333529"
                                
                                # Extraer números del rango
                                range_numbers = range_part.split(" - ")
                                if len(range_numbers) == 2:
                                    start_num = int(range_numbers[0])
                                    end_num = int(range_numbers[1])
                                    total_records = int(total_str)
                                    
                                    logger.info(f"Paginación detectada: {text}")
                                    logger.info(f"Rango actual: {start_num} - {end_num}")
                                    logger.info(f"Total registros: {total_records}")
                                    
                                    return start_num, end_num, total_records
                                    
                except Exception as e:
                    logger.debug(f"Error con selector {selector}: {e}")
                    continue
                    
            logger.warning("No se pudo extraer información de paginación")
            return 1, 10, 0
            
        except Exception as e:
            logger.error(f"Error extrayendo paginación: {e}")
            return 1, 10, 0

    async def has_next_page(self, page) -> bool:
        """Verificar si hay página siguiente disponible"""
        try:
            # Buscar botón "Next" - puede estar habilitado o deshabilitado
            next_button_selectors = [
                "button[ng-click*='next()']:not([disabled])",  # Botón next no deshabilitado
                "button[aria-label='Next']:not([disabled])",
                ".md-icon-button[ng-click*='next()']:not([disabled])",
                "button:has(md-icon[md-svg-icon*='navigate-next']):not([disabled])"
            ]
            
            for selector in next_button_selectors:
                try:
                    button = page.locator(selector).first
                    if await button.count() > 0:
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        
                        logger.debug(f"Botón Next - Visible: {is_visible}, Habilitado: {is_enabled}")
                        
                        if is_visible and is_enabled:
                            return True
                            
                except Exception as e:
                    logger.debug(f"Error verificando selector {selector}: {e}")
                    continue
                    
            logger.info("No hay página siguiente disponible")
            return False
            
        except Exception as e:
            logger.error(f"Error verificando página siguiente: {e}")
            return False

    async def click_next_page(self, page) -> bool:
        """Hacer clic en el botón de página siguiente"""
        try:
            logger.info("Intentando ir a página siguiente...")
            
            next_button_selectors = [
                "button[ng-click*='next()']:not([disabled])",
                "button[aria-label='Next']:not([disabled])",
                ".md-icon-button[ng-click*='next()']:not([disabled])",
                "button:has(md-icon[md-svg-icon*='navigate-next']):not([disabled])"
            ]
            
            for selector in next_button_selectors:
                try:
                    button = page.locator(selector).first
                    
                    if await button.count() > 0:
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                        
                        if is_visible and is_enabled:
                            # Scroll al botón y hacer clic
                            await button.scroll_into_view_if_needed()
                            await asyncio.sleep(1)
                            
                            await button.click()
                            
                            # Esperar a que la página se actualice
                            await asyncio.sleep(self.pause_between_pages)
                            
                            # Esperar a que el contenido se cargue
                            await page.wait_for_load_state('networkidle')
                            
                            logger.info("Clic en página siguiente exitoso")
                            return True
                            
                except Exception as e:
                    logger.debug(f"Error con selector {selector}: {e}")
                    continue
                    
            logger.error("No se pudo hacer clic en página siguiente")
            return False
            
        except Exception as e:
            logger.error(f"Error haciendo clic en página siguiente: {e}")
            return False

    async def process_all_pages(self, page, pqr_processor, max_pages: Optional[int] = None) -> Dict[str, Any]:
        """
        Procesar todas las páginas de PQR con paginación automática
        
        Args:
            page: Página de Playwright
            pqr_processor: Instancia del procesador de PQR
            max_pages: Límite máximo de páginas (None = sin límite)
        """
        try:
            # Inicializar sesión
            self.state.session_start = datetime.now().isoformat()
            
            # Extraer información inicial de paginación
            start_num, end_num, total_records = await self.extract_pagination_info(page)
            self.state.total_records = total_records
            self.state.records_per_page = end_num - start_num + 1
            self.state.total_pages = (total_records + self.state.records_per_page - 1) // self.state.records_per_page
            
            logger.info(f"INICIO DE PROCESAMIENTO MASIVO")
            logger.info(f"Total registros: {self.state.total_records:,}")
            logger.info(f"Páginas estimadas: {self.state.total_pages:,}")
            logger.info(f"Registros por página: {self.state.records_per_page}")

            results = {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'pages_processed': 0,
                'start_time': self.state.session_start,
                'checkpoints_created': 0
            }
            
            current_page = self.state.current_page
            
            while True:
                # Verificar señales de control
                signal = self._check_control_signals()
                
                if signal == "STOP":
                    logger.warning("PARADA SOLICITADA - Guardando progreso...")
                    break
                
                # Verificar límites
                if max_pages and current_page > max_pages:
                    logger.info(f"Límite de páginas alcanzado: {max_pages}")
                    break
                
                logger.info(f"=== PROCESANDO PÁGINA {current_page} ===")
                
                # Procesar registros de la página actual
                try:
                    # Aquí llamamos al procesador de PQR existente
                    page_results = await pqr_processor.process_current_page_records(page, max_records=self.max_records_per_session)
                    
                    # Actualizar estadísticas
                    results['total_processed'] += page_results.get('total_processed', 0)
                    results['successful'] += page_results.get('successful', 0)
                    results['failed'] += page_results.get('failed', 0)
                    results['pages_processed'] += 1
                    
                    # Actualizar estado
                    self.state.processed_records += page_results.get('total_processed', 0)
                    self.state.current_page = current_page
                    
                    logger.info(f"Página {current_page} completada")
                    logger.info(f"Procesados en página: {page_results.get('total_processed', 0)}")
                    logger.info(f"Total procesados: {self.state.processed_records:,}/{self.state.total_records:,}")
                    
                except Exception as page_error:
                    logger.error(f"Error procesando página {current_page}: {page_error}")
                    results['failed'] += self.state.records_per_page  # Asumir que toda la página falló
                
                # Verificar si hay página siguiente
                if not await self.has_next_page(page):
                    logger.info("No hay más páginas. Procesamiento completado")
                    break
                
                # Ir a página siguiente
                if not await self.click_next_page(page):
                    logger.error("No se pudo navegar a página siguiente")
                    break
                
                current_page += 1
                
                # Pausa entre páginas para no sobrecargar el servidor
                await asyncio.sleep(self.pause_between_pages)
            
            results['end_time'] = datetime.now().isoformat()
            
            logger.info(f"PROCESAMIENTO COMPLETADO")
            logger.info(f"Total procesados: {results['total_processed']:,}")
            logger.info(f"Exitosos: {results['successful']:,}")
            logger.info(f"Fallidos: {results['failed']:,}")
            logger.info(f"Páginas procesadas: {results['pages_processed']:,}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error en procesamiento masivo: {e}")
            return results