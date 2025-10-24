"""
AFINIA PAGINATION MANAGER
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

logger = logging.getLogger('AFINIA-PAGINATION')

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

class AfiniaPaginationManager:
    """Gestor de paginación automática para Afinia"""
    
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
        
        logger.info(f"EXITOSO PaginationManager inicializado")
        logger.info(f"ARCHIVOS Control dir: {self.control_dir}")
        logger.info(f"GUARDANDO Checkpoint dir: {self.checkpoint_dir}")
        logger.info(f"CONFIGURACION Max records per session: {self.max_records_per_session}")

    def _load_checkpoint(self) -> bool:
        """Cargar último checkpoint si existe"""
        try:
            checkpoint_files = list(self.checkpoint_dir.glob("checkpoint_*.json"))
            if not checkpoint_files:
                logger.info("LISTA No se encontraron checkpoints previos")
                return False
                
            # Obtener el checkpoint más reciente
            latest_checkpoint = max(checkpoint_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_checkpoint, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
                
            # Restaurar estado
            self.state.current_page = checkpoint_data.get('current_page', 1)
            self.state.total_records = checkpoint_data.get('total_records', 0)
            self.state.processed_records = checkpoint_data.get('processed_records', 0)
            self.state.records_per_page = checkpoint_data.get('records_per_page', 10)
            self.state.total_pages = checkpoint_data.get('total_pages', 0)
            
            logger.info(f"EXITOSO Checkpoint cargado: {latest_checkpoint.name}")
            logger.info(f"PAGINA Página actual: {self.state.current_page}")
            logger.info(f"PROCESADOS Procesados: {self.state.processed_records}/{self.state.total_records}")
            return True
            
        except Exception as e:
            logger.error(f"ERROR Error cargando checkpoint: {e}")
            return False

    def _save_checkpoint(self) -> bool:
        """Guardar checkpoint actual"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_file = self.checkpoint_dir / f"checkpoint_{timestamp}.json"
            
            checkpoint_data = {
                'timestamp': timestamp,
                'current_page': self.state.current_page,
                'total_records': self.state.total_records,
                'processed_records': self.state.processed_records,
                'records_per_page': self.state.records_per_page,
                'total_pages': self.state.total_pages,
                'session_start': self.state.session_start,
                'last_checkpoint': timestamp
            }
            
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"GUARDANDO Checkpoint guardado: {checkpoint_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"ERROR Error guardando checkpoint: {e}")
            return False

    def _update_status(self):
        """Actualizar archivo de estado para monitoreo externo"""
        try:
            status_data = {
                'timestamp': datetime.now().isoformat(),
                'current_page': self.state.current_page,
                'total_pages': self.state.total_pages,
                'processed_records': self.state.processed_records,
                'total_records': self.state.total_records,
                'progress_percentage': (self.state.processed_records / self.state.total_records * 100) if self.state.total_records > 0 else 0,
                'is_paused': self.state.is_paused,
                'is_stopped': self.state.is_stopped,
                'session_start': self.state.session_start,
                'estimated_remaining': self._estimate_remaining_time()
            }
            
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"ADVERTENCIA Error actualizando estado: {e}")

    def _estimate_remaining_time(self) -> str:
        """Estimar tiempo restante basado en progreso actual"""
        try:
            if self.state.processed_records == 0:
                return "Calculando..."
                
            # Tiempo transcurrido desde inicio de sesión
            if not self.state.session_start:
                return "No disponible"
                
            session_start = datetime.fromisoformat(self.state.session_start)
            elapsed_time = (datetime.now() - session_start).total_seconds()
            
            # Velocidad promedio (registros por segundo)
            avg_speed = self.state.processed_records / elapsed_time if elapsed_time > 0 else 0
            
            if avg_speed > 0:
                remaining_records = self.state.total_records - self.state.processed_records
                remaining_seconds = remaining_records / avg_speed
                
                hours = int(remaining_seconds // 3600)
                minutes = int((remaining_seconds % 3600) // 60)
                return f"{hours}h {minutes}m"
            else:
                return "Calculando..."
                
        except Exception as e:
            logger.warning(f"ADVERTENCIA Error calculando tiempo: {e}")
            return "Error"

    def _check_control_signals(self) -> str:
        """Verificar archivos de control para pausar/detener"""
        if self.stop_file.exists():
            logger.warning(" SEÑAL DE PARADA DETECTADA")
            self.state.is_stopped = True
            return "STOP"
            
        if self.pause_file.exists() and not self.resume_file.exists():
            if not self.state.is_paused:
                logger.warning("⏸ SEÑAL DE PAUSA DETECTADA")
                self.state.is_paused = True
            return "PAUSE"
            
        if self.resume_file.exists():
            if self.state.is_paused:
                logger.info(" SEÑAL DE REANUDACIÓN DETECTADA")
                self.state.is_paused = False
                # Limpiar archivo de pausa y reanudación
                self.pause_file.unlink(missing_ok=True)
                self.resume_file.unlink(missing_ok=True)
            return "RESUME"
            
        return "CONTINUE"

    async def _wait_for_resume(self):
        """Esperar hasta que se reanude el procesamiento"""
        logger.info("⏸ Procesamiento pausado. Esperando señal de reanudación...")
        
        while self.state.is_paused and not self.state.is_stopped:
            await asyncio.sleep(5)  # Verificar cada 5 segundos
            signal = self._check_control_signals()
            self._update_status()
            
            if signal == "STOP":
                break
            elif signal == "RESUME":
                break
                
        if not self.state.is_stopped:
            logger.info(" Procesamiento reanudado")

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
                                    
                                    logger.info(f"PROCESADOS Paginación detectada: {text}")
                                    logger.info(f"METRICAS Rango actual: {start_num} - {end_num}")
                                    logger.info(f"LISTA Total registros: {total_records}")
                                    
                                    return start_num, end_num, total_records
                                    
                except Exception as e:
                    logger.debug(f"Error con selector {selector}: {e}")
                    continue
                    
            logger.warning("ADVERTENCIA No se pudo extraer información de paginación")
            return 1, 10, 0
            
        except Exception as e:
            logger.error(f"ERROR Error extrayendo paginación: {e}")
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
                        
                        logger.debug(f"VERIFICANDO Botón Next - Visible: {is_visible}, Habilitado: {is_enabled}")
                        
                        if is_visible and is_enabled:
                            return True
                            
                except Exception as e:
                    logger.debug(f"Error verificando selector {selector}: {e}")
                    continue
                    
            logger.info("PAGINA No hay página siguiente disponible")
            return False
            
        except Exception as e:
            logger.error(f"ERROR Error verificando página siguiente: {e}")
            return False

    async def click_next_page(self, page) -> bool:
        """Hacer clic en el botón de página siguiente"""
        try:
            logger.info(" Intentando ir a página siguiente...")
            
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
                            
                            logger.info("EXITOSO Clic en página siguiente exitoso")
                            return True
                            
                except Exception as e:
                    logger.debug(f"Error con selector {selector}: {e}")
                    continue
                    
            logger.error("ERROR No se pudo hacer clic en página siguiente")
            return False
            
        except Exception as e:
            logger.error(f"ERROR Error haciendo clic en página siguiente: {e}")
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
            
            # Cargar checkpoint si existe
            checkpoint_loaded = self._load_checkpoint()
            
            # Extraer información inicial de paginación
            if not checkpoint_loaded:
                start_num, end_num, total_records = await self.extract_pagination_info(page)
                self.state.total_records = total_records
                self.state.records_per_page = end_num - start_num + 1
                self.state.total_pages = (total_records + self.state.records_per_page - 1) // self.state.records_per_page
                
                logger.info(f"OBJETIVO INICIO DE PROCESAMIENTO MASIVO")
                logger.info(f"PROCESADOS Total registros: {self.state.total_records:,}")
                logger.info(f"PAGINA Páginas estimadas: {self.state.total_pages:,}")
                logger.info(f"CONFIGURACION Registros por página: {self.state.records_per_page}")
            else:
                logger.info(f"REANUDANDO REANUDANDO DESDE CHECKPOINT")
                logger.info(f"PAGINA Página actual: {self.state.current_page}")
                logger.info(f"PROCESADOS Progreso: {self.state.processed_records}/{self.state.total_records}")

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
                    logger.warning(" PARADA SOLICITADA - Guardando progreso...")
                    self._save_checkpoint()
                    break
                elif signal == "PAUSE":
                    await self._wait_for_resume()
                    if self.state.is_stopped:
                        break
                
                # Verificar límites
                if max_pages and current_page > max_pages:
                    logger.info(f"PAGINA Límite de páginas alcanzado: {max_pages}")
                    break
                
                logger.info(f"PAGINA === PROCESANDO PÁGINA {current_page} ===")
                
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
                    
                    logger.info(f"EXITOSO Página {current_page} completada")
                    logger.info(f"PROCESADOS Procesados en página: {page_results.get('total_processed', 0)}")
                    logger.info(f"METRICAS Total procesados: {self.state.processed_records:,}/{self.state.total_records:,}")
                    
                except Exception as page_error:
                    logger.error(f"ERROR Error procesando página {current_page}: {page_error}")
                    results['failed'] += self.state.records_per_page  # Asumir que toda la página falló
                
                # Guardar checkpoint periódicamente
                if current_page % self.checkpoint_frequency == 0:
                    self._save_checkpoint()
                    results['checkpoints_created'] += 1
                
                # Actualizar estado
                self._update_status()
                
                # Verificar si hay página siguiente
                if not await self.has_next_page(page):
                    logger.info("COMPLETADO No hay más páginas. Procesamiento completado")
                    break
                
                # Ir a página siguiente
                if not await self.click_next_page(page):
                    logger.error("ERROR No se pudo navegar a página siguiente")
                    break
                
                current_page += 1
                
                # Pausa entre páginas para no sobrecargar el servidor
                await asyncio.sleep(self.pause_between_pages)
            
            # Guardar checkpoint final
            self._save_checkpoint()
            results['end_time'] = datetime.now().isoformat()
            
            logger.info(f"PROCESO_COMPLETADO PROCESAMIENTO COMPLETADO")
            logger.info(f"PROCESADOS Total procesados: {results['total_processed']:,}")
            logger.info(f"EXITOSO Exitosos: {results['successful']:,}")
            logger.info(f"ERROR Fallidos: {results['failed']:,}")
            logger.info(f"PAGINA Páginas procesadas: {results['pages_processed']:,}")
            
            return results
            
        except Exception as e:
            logger.error(f"ERROR Error en procesamiento masivo: {e}")
            self._save_checkpoint()  # Guardar progreso antes de salir
            return results

    def create_control_scripts(self):
        """Crear scripts de control para servidor Linux"""
        scripts_dir = self.base_dir / "server_control_scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        # Script de pausa
        pause_script = scripts_dir / "pause.sh"
        pause_script.write_text(f"""#!/bin/bash
# Script para pausar el procesamiento
echo "⏸  Pausando procesamiento..."
touch "{self.pause_file}"
echo "EXITOSO Señal de pausa enviada"
echo " Para reanudar, ejecuta: ./resume.sh"
""")
        pause_script.chmod(0o755)
        
        # Script de reanudación
        resume_script = scripts_dir / "resume.sh"
        resume_script.write_text(f"""#!/bin/bash
# Script para reanudar el procesamiento
echo "  Reanudando procesamiento..."
touch "{self.resume_file}"
echo "EXITOSO Señal de reanudación enviada"
""")
        resume_script.chmod(0o755)
        
        # Script de parada
        stop_script = scripts_dir / "stop.sh"
        stop_script.write_text(f"""#!/bin/bash
# Script para detener el procesamiento
echo " Deteniendo procesamiento..."
touch "{self.stop_file}"
echo "EXITOSO Señal de parada enviada"
echo "ADVERTENCIA  El sistema guardará el progreso antes de detenerse"
""")
        stop_script.chmod(0o755)
        
        # Script de estado
        status_script = scripts_dir / "status.sh"
        status_script.write_text(f"""#!/bin/bash
# Script para ver estado del procesamiento
if [ -f "{self.status_file}" ]; then
    echo "PROCESADOS ESTADO ACTUAL:"
    cat "{self.status_file}" | jq '.'
else
    echo "ERROR No hay información de estado disponible"
fi
""")
        status_script.chmod(0o755)
        
        # Script de limpieza
        clean_script = scripts_dir / "clean_signals.sh"
        clean_script.write_text(f"""#!/bin/bash
# Script para limpiar señales de control
echo "LIMPIEZA Limpiando señales de control..."
rm -f "{self.pause_file}" "{self.resume_file}" "{self.stop_file}"
echo "EXITOSO Señales de control limpiadas"
""")
        clean_script.chmod(0o755)
        
        logger.info(f" Scripts de control creados en: {scripts_dir}")
        logger.info(" Comandos disponibles:")
        logger.info(f"   ./pause.sh   - Pausar procesamiento")
        logger.info(f"   ./resume.sh  - Reanudar procesamiento")
        logger.info(f"   ./stop.sh    - Detener procesamiento")
        logger.info(f"   ./status.sh  - Ver estado actual")
        logger.info(f"   ./clean_signals.sh - Limpiar señales")