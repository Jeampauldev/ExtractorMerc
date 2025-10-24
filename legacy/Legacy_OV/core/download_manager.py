"""
Gestor de descargas para automatización de oficinas virtuales.

Este módulo proporciona funcionalidades para:
- Descargar reportes de diferentes empresas
- Gestionar timeouts y reintentos
- Detectar descargas automáticas
- Registrar métricas de descarga
- Tomar screenshots de debug

Autor: Sistema de Automatización
Fecha: 2024
"""

import asyncio
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from pathlib import Path
from playwright.async_api import Page, Download, TimeoutError as PlaywrightTimeoutError

# Configurar logger específico para este módulo
logger = logging.getLogger('DOWNLOAD-MANAGER')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[DOWNLOAD-MANAGER] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class DownloadManager:
    """Gestor de descargas para automatización de oficinas virtuales."""
    
    # Selectores comunes para botones de descarga
    COMMON_DOWNLOAD_BUTTON_SELECTORS = [
        'button:has-text("Descargar")',
        'button:has-text("Exportar")',
        'button:has-text("Excel")',
        'button:has-text("Generar Excel")',
        'button:has-text("Generar en Excel")',
        'a:has-text("Descargar")',
        'a:has-text("Exportar")',
        'input[value*="Generar Excel"]',
        'input[type="button"][value*="Generar Excel"]',
        'input[id="cmd_ejecuta_excel"]',
        'input[name="aceptar"][id="cmd_ejecuta_excel"]',
        '*[onclick*="fngenerarexcel"]',
        '*[onclick*="GenerarExcel"]',
        '.btn-download',
        '.btn-export',
        '#download-button',
        '#export-button',
        'button[title*="descargar"]',
        'button[title*="exportar"]'
    ]
    
    # Extensiones de archivo válidas
    VALID_EXTENSIONS = {
        '.xlsx', '.xls', '.csv', '.pdf', '.txt', '.json'
    }
    
    # Timeout por defecto para descargas (45 segundos)
    DEFAULT_DOWNLOAD_TIMEOUT = 45000

    def __init__(self, page: Page, base_download_dir: str = "downloads"):
        """
        Inicializa el gestor de descargas.

        Args:
            page: Página de Playwright para interactuar
            base_download_dir: Directorio base para descargas
        """
        self.page = page
        self.base_download_dir = Path(base_download_dir)
        
        # Asegurar que el directorio base existe
        self.base_download_dir.mkdir(parents=True, exist_ok=True)
        
        # Estado interno
        self.last_download: Optional[Download] = None
        self.download_metrics: List[Dict[str, Any]] = []
        
        logger.info(f"DownloadManager inicializado - Directorio base: {self.base_download_dir}")

    async def download_report(self, 
                       company: str,
                       report_type: str,
                       button_selectors: Optional[List[str]] = None,
                       timeout: int = None,
                       custom_filename: Optional[str] = None,
                       wait_before_click: int = 1000) -> Optional[str]:
        """
        Descarga un reporte usando múltiples estrategias.

        Args:
            company: Nombre de la empresa (afinia, aire, etc.)
            report_type: Tipo de reporte (pqr_pendientes, verbales, etc.)
            button_selectors: Selectores personalizados para botón de descarga
            timeout: Timeout personalizado en milisegundos
            custom_filename: Nombre de archivo personalizado (sin extensión)
            wait_before_click: Tiempo de espera antes del clic en ms

        Returns:
            Ruta del archivo descargado si fue exitoso, None si falló
        """
        logger.info(f"DESCARGANDO Iniciando descarga de reporte: {company}/{report_type}")
        
        # Configurar parámetros
        button_sels = button_selectors or self.COMMON_DOWNLOAD_BUTTON_SELECTORS
        download_timeout = timeout or self.DEFAULT_DOWNLOAD_TIMEOUT
        
        # Crear directorio específico para la empresa
        company_dir = self.base_download_dir / company
        company_dir.mkdir(exist_ok=True)

        try:
            # Buscar botón de descarga
            download_button = await self._find_download_button(button_sels)
            if not download_button:
                logger.error("ERROR No se encontró botón de descarga")
                return None

            # Esperar antes del clic si se especifica
            if wait_before_click > 0:
                logger.info(f"ESPERANDO Esperando {wait_before_click}ms antes del clic...")
                await asyncio.sleep(wait_before_click / 1000)

            # Ejecutar descarga
            download_path = await self._execute_download(
                download_button, 
                company_dir, 
                company, 
                report_type, 
                download_timeout,
                custom_filename
            )

            if download_path:
                # Descarga exitosa
                self._record_download_metrics(download_path, company, report_type, True)
                logger.info(f"EXITOSO Descarga exitosa: {download_path}")
                return str(download_path)
            else:
                # Intentar detectar descarga automática
                logger.info("VERIFICANDO Intentando detectar descarga automática...")
                detected_path = self._detect_recent_download(company_dir, report_type)

                if detected_path:
                    self._record_download_metrics(detected_path, company, report_type, True)
                    logger.info(f"EXITOSO Descarga detectada automáticamente: {detected_path}")
                    return str(detected_path)
                else:
                    self._record_download_metrics(None, company, report_type, False)
                    logger.error("ERROR No se pudo completar la descarga")
                    return None

        except Exception as e:
            logger.error(f"ERROR Error durante la descarga: {str(e)}")
            self._record_download_metrics(None, company, report_type, False, str(e))
            return None

    async def _find_download_button(self, selectors: List[str]):
        """
        Busca el botón de descarga usando múltiples selectores.

        Args:
            selectors: Lista de selectores CSS para buscar el botón

        Returns:
            Elemento del botón si se encuentra, None si no
        """
        logger.info("VERIFICANDO Buscando botón de descarga...")
        
        # Probar selectores específicos primero
        for selector in selectors:
            try:
                logger.info(f"Probando selector: {selector}")
                button = await self.page.wait_for_selector(selector, timeout=3000)
                
                if button and await button.is_visible():
                    button_text = await self._get_button_text(button)
                    logger.info(f"EXITOSO Botón encontrado: '{button_text}' con selector: {selector}")
                    return button
                    
            except PlaywrightTimeoutError:
                logger.debug(f"Selector {selector} no encontrado (timeout)")
                continue
            except Exception as e:
                logger.warning(f"Error con selector {selector}: {e}")
                continue
        
        # Fallback: buscar en todos los botones
        logger.info("VERIFICANDO Fallback: analizando todos los botones...")
        try:
            all_buttons = await self.page.query_selector_all("input[type='submit'], input[type='button'], button")
            logger.info(f"Encontrados {len(all_buttons)} botones para análisis")
            
            download_keywords = ["descargar", "exportar", "excel", "generar", "download", "export"]
            
            for button in all_buttons:
                if await button.is_visible():
                    button_text = (await self._get_button_text(button)).lower()
                    
                    if any(keyword in button_text for keyword in download_keywords):
                        logger.info(f"EXITOSO Botón candidato encontrado: '{button_text.strip()}'")
                        return button
                        
        except Exception as e:
            logger.error(f"Error en fallback de búsqueda: {e}")
        
        return None

    async def _get_button_text(self, button) -> str:
        """
        Obtiene el texto de un botón de manera segura.

        Args:
            button: Elemento del botón

        Returns:
            Texto del botón o 'sin_texto' si no se puede obtener
        """
        try:
            text = (await button.get_attribute("value") or 
                   await button.inner_text() or 
                   await button.get_attribute("title") or 
                   "sin_texto")
            return text.strip()
        except Exception:
            return "sin_texto"

    async def _execute_download(self, 
                         button,
                         target_dir: Path,
                         company: str,
                         report_type: str,
                         timeout: int,
                         custom_filename: Optional[str] = None) -> Optional[Path]:
        """
        Ejecuta la descarga haciendo clic en el botón.

        Args:
            button: Elemento del botón de descarga
            target_dir: Directorio de destino
            company: Nombre de la empresa
            report_type: Tipo de reporte
            timeout: Timeout en milisegundos
            custom_filename: Nombre personalizado del archivo

        Returns:
            Ruta del archivo descargado o None si falló
        """
        logger.info(" Ejecutando descarga...")

        try:
            # Configurar listener de descarga
            async with self.page.expect_download(timeout=timeout) as download_info:
                logger.info(" Haciendo clic en botón de descarga...")
                await button.click()
                
                # Screenshot de debug después del clic
                await self._take_debug_screenshot("after_download_click", target_dir)
                
                logger.info("ESPERANDO Esperando descarga...")
            
            # Obtener información de la descarga
            download = await download_info.value
            self.last_download = download
            
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = download.suggested_filename or f"{report_type}_{timestamp}.xlsx"
            
            # Aplicar nombre personalizado si se proporciona
            if custom_filename:
                file_extension = self._get_file_extension(original_filename)
                final_filename = f"{custom_filename}_{timestamp}{file_extension}"
            else:
                final_filename = f"{company}_{report_type}_{timestamp}{self._get_file_extension(original_filename)}"
            
            # Ruta completa del archivo
            file_path = target_dir / final_filename
            
            # Guardar archivo
            await download.save_as(str(file_path))
            
            logger.info(f"GUARDANDO Archivo guardado como: {final_filename}")
            logger.info(f"ARCHIVOS Ruta completa: {file_path}")
            
            return file_path

        except PlaywrightTimeoutError:
            logger.error(f"⏰ Timeout esperando descarga después de {timeout}ms")
            return None
        except Exception as e:
            logger.error(f"ERROR Error durante la ejecución de descarga: {e}")
            return None

    def _detect_recent_download(self, 
                               target_dir: Path, 
                               report_type: str,
                               max_age_seconds: int = 30) -> Optional[Path]:
        """
        Detecta archivos descargados recientemente en el directorio.

        Args:
            target_dir: Directorio donde buscar
            report_type: Tipo de reporte para filtrar
            max_age_seconds: Edad máxima del archivo en segundos

        Returns:
            Ruta del archivo más reciente encontrado o None
        """
        logger.info(f"VERIFICANDO Buscando archivos recientes en: {target_dir}")

        try:
            current_time = time.time()
            recent_files = []
            
            # Buscar archivos recientes
            for file_path in target_dir.glob("*"):
                if file_path.is_file():
                    # Verificar extensión válida
                    if file_path.suffix.lower() in self.VALID_EXTENSIONS:
                        file_time = file_path.stat().st_mtime
                        age_seconds = current_time - file_time
                        
                        if age_seconds <= max_age_seconds:
                            recent_files.append((file_path, age_seconds))
                            logger.info(f"PAGINA Archivo reciente encontrado: {file_path.name} (hace {age_seconds:.1f}s)")
            
            if recent_files:
                # Ordenar por tiempo (más reciente primero)
                recent_files.sort(key=lambda x: x[1])
                most_recent_file = recent_files[0][0]
                
                logger.info(f"EXITOSO Archivo más reciente: {most_recent_file.name}")
                return most_recent_file
            else:
                logger.info("ERROR No se encontraron archivos recientes")
                return None

        except Exception as e:
            logger.error(f"ERROR Error detectando descarga reciente: {e}")
            return None

    def _get_file_extension(self, filename: Optional[str]) -> str:
        """
        Obtiene la extensión de un archivo de manera segura.

        Args:
            filename: Nombre del archivo

        Returns:
            Extensión del archivo o '.xlsx' por defecto
        """
        if not filename:
            return ".xlsx"  # Extensión por defecto

        try:
            ext = Path(filename).suffix
            return ext if ext in self.VALID_EXTENSIONS else ".xlsx"
        except Exception:
            return ".xlsx"

    def _record_download_metrics(self, 
                                file_path: Optional[Path], 
                                company: str, 
                                report_type: str, 
                                success: bool,
                                error_message: Optional[str] = None):
        """
        Registra métricas de la descarga.

        Args:
            file_path: Ruta del archivo descargado
            company: Nombre de la empresa
            report_type: Tipo de reporte
            success: Si la descarga fue exitosa
            error_message: Mensaje de error si aplica
        """
        metrics_entry = {
            'timestamp': datetime.now().isoformat(),
            'company': company,
            'report_type': report_type,
            'success': success,
            'file_path': str(file_path) if file_path else None,
            'file_name': file_path.name if file_path else None,
            'file_size': file_path.stat().st_size if file_path and file_path.exists() else None,
            'error_message': error_message
        }

        self.download_metrics.append(metrics_entry)
        
        # Log del resultado
        if success:
            size_mb = metrics_entry['file_size'] / (1024 * 1024) if metrics_entry['file_size'] else 0
            logger.info(f"PROCESADOS Métrica registrada: {company}/{report_type} - {size_mb:.2f}MB")
        else:
            logger.warning(f"PROCESADOS Error registrado: {company}/{report_type} - {error_message}")

    def _take_debug_screenshot(self, step_name: str, target_dir: Path):
        """
        Toma un screenshot de debug.

        Args:
            step_name: Nombre del paso para el archivo
            target_dir: Directorio donde guardar el screenshot
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{step_name}_{timestamp}.png"
            filepath = target_dir / filename

            self.page.screenshot(path=str(filepath))
            logger.debug(f" Screenshot debug: {filename}")

        except Exception as e:
            logger.warning(f"ERROR Error tomando screenshot debug: {e}")

    def get_download_metrics(self) -> List[Dict[str, Any]]:
        """
        Obtiene las métricas de descarga registradas.

        Returns:
            Lista de métricas de descarga
        """
        return self.download_metrics.copy()

    def clear_metrics(self):
        """Limpia las métricas de descarga."""
        self.download_metrics.clear()
        logger.info("LIMPIEZA Métricas de descarga limpiadas")

    def get_last_download_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de la última descarga.

        Returns:
            Diccionario con información de la última descarga o None
        """
        if not self.last_download:
            return None

        try:
            return {
                'suggested_filename': self.last_download.suggested_filename,
                'url': self.last_download.url,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error obteniendo info de última descarga: {e}")
            return None


# Funciones de utilidad para compatibilidad con código existente
def download_file(page: Page, 
                 company: str, 
                 report_type: str,
                 button_selector: Optional[str] = None,
                 timeout: int = None) -> Optional[str]:
    """
    Función de utilidad para descargar un archivo.
    
    Args:
        page: Página de Playwright
        company: Nombre de la empresa
        report_type: Tipo de reporte
        button_selector: Selector del botón de descarga
        timeout: Timeout en milisegundos
        
    Returns:
        Ruta del archivo descargado o None
    """
    manager = DownloadManager(page)
    selectors = [button_selector] if button_selector else None
    return manager.download_report(company, report_type, selectors, timeout)


def setup_download_listener(page: Page, timeout: int = 45000) -> Callable:
    """
    Configura un listener de descarga básico.
    
    Args:
        page: Página de Playwright
        timeout: Timeout en milisegundos
        
    Returns:
        Función para manejar descargas
    """
    def handle_download(download: Download):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"download_{timestamp}_{download.suggested_filename or 'file.xlsx'}"
            download.save_as(filename)
            logger.info(f"Descarga guardada: {filename}")
        except Exception as e:
            logger.error(f"Error guardando descarga: {e}")
    
    page.on("download", handle_download)
    return handle_download
