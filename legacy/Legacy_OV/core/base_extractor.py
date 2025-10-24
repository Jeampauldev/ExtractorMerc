#!/usr/bin/env python3
"""
Base Extractor - ExtractorOV Modular
===================================

Clase base abstracta para todos los extractores. Implementa funcionalidades
comunes y define la interfaz que deben seguir todos los extractores específicos.
"""

import time
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from functools import wraps

from src_OV.config.config import ExtractorConfig
# Sistema de métricas opcional
try:
    from data.metrics.metrics_logger import create_metrics_logger
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    def create_metrics_logger(name):
        return None

class BaseExtractor(ABC):
    """Clase base para todos los extractores"""

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el extractor base con configuración específica

        Args:
            config: Diccionario de configuración específico del extractor
        """
        self.config = config
        self.company = config.get('company_name', 'unknown')
        self.platform = config.get('platform', 'unknown')

        # Configurar logging
        self.logger = logging.getLogger(f"{self.platform.upper()}-{self.company.upper()}")
        self.logger.setLevel(logging.INFO)

        # Crear handler si no existe
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(f'[{self.platform.upper()}-{self.company.upper()} %(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Inicializar sistema de métricas (opcional)
        metrics_name = f"{self.platform}_{self.company}"
        self.metrics = create_metrics_logger(metrics_name) if METRICS_AVAILABLE else None

        # Variables de instancia para browser
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self.logger.info(f"Extractor inicializado: {self.company.upper()} {self.platform.upper()}")

    def performance_monitor(self, func):
        """Decorator para monitorear rendimiento de funciones"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = func.__name__
            self.logger.info(f"Iniciando {function_name}")

            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time

                self.logger.info(f"{function_name} completado en {execution_time:.2f} segundos")

                # Registrar métricas (si está disponible)
                if self.metrics:
                    self.metrics.log_step_completion(
                        step_name=function_name,
                        duration=execution_time,
                        status="success"
                    )

                return result

            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time

                self.logger.error(f"{function_name} falló después de {execution_time:.2f} segundos: {str(e)}")

                # Registrar métricas de error (si está disponible)
                if self.metrics:
                    self.metrics.log_step_completion(
                        step_name=function_name,
                        duration=execution_time,
                        status="error",
                        error_message=str(e)
                    )

                raise

        return wrapper

    def setup_browser(self) -> Tuple[Page, Browser, BrowserContext]:
        """Configura y inicializa el navegador Playwright"""
        try:
            self.logger.info("Configurando navegador...")

            self.playwright = sync_playwright().start()

            browser_config = ExtractorConfig.BROWSER_CONFIG

            self.browser = self.playwright.chromium.launch(
                headless=browser_config["headless"],
                args=browser_config["args"]
            )

            self.context = self.browser.new_context(
                viewport=browser_config["viewport"],
                device_scale_factor=browser_config["device_scale_factor"],
                accept_downloads=True,
                ignore_https_errors=True
            )

            self.page = self.context.new_page()

            # Configurar timeouts
            timeouts = ExtractorConfig.TIMEOUTS
            self.page.set_default_timeout(timeouts["element_wait"])
            self.page.set_default_navigation_timeout(timeouts["navigation"])

            self.logger.info("Navegador configurado correctamente")
            return self.page, self.browser, self.context

        except Exception as e:
            self.logger.error(f"Error configurando navegador: {e}")
            raise

    def cleanup_browser(self):
        """Limpia y cierra todos los recursos del navegador"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            self.logger.info("Recursos del navegador liberados")

        except Exception as e:
            self.logger.warning(f"Error limpiando navegador: {e}")

    def take_screenshot(self, name: str, step: str = None) -> str:
        """Toma una captura de pantalla para debugging"""
        try:
            if not self.page:
                return ""

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            step_prefix = f"{step}_" if step else ""
            filename = f"{step_prefix}{name}_{self.company}_{timestamp}.png"

            # Crear directorio de screenshots
            screenshots_dir = ExtractorConfig.DOWNLOADS_DIR / self.company / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)

            filepath = screenshots_dir / filename
            self.page.screenshot(path=str(filepath))

            self.logger.info(f"Screenshot guardado: {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.warning(f"Error tomando screenshot: {e}")
            return ""

    async def find_element(self, selectors: List[str], timeout: Optional[int] = None):
        """
        Busca un elemento usando múltiples selectores.
        
        Args:
            selectors: Lista de selectores CSS a probar
            timeout: Timeout total en milisegundos
            
        Returns:
            ElementHandle si encuentra el elemento, None si no
        """
        if timeout is None:
            timeout = ExtractorConfig.TIMEOUTS["element_wait"]

        for i, selector in enumerate(selectors):
            try:
                self.logger.debug(f"Buscando elemento con selector {i+1}/{len(selectors)}: {selector}")
                element = await self.page.wait_for_selector(selector, timeout=timeout // len(selectors))

                if element and await element.is_visible():
                    self.logger.info(f"Elemento encontrado con selector: {selector}")
                    return element

            except Exception as e:
                self.logger.debug(f"Selector {selector} no funcionó: {e}")
                continue

        self.logger.warning(f"Ningún selector funcionó: {selectors}")
        return None

    async def safe_click(self, element, description: str = "elemento") -> bool:
        """Hace click de forma segura en un elemento"""
        try:
            if not element:
                self.logger.warning(f"No se puede hacer click en {description}: elemento es None")
                return False

            # Verificar que el elemento sea visible y esté habilitado
            if not await element.is_visible():
                self.logger.warning(f"Elemento {description} no es visible")
                return False

            if not await element.is_enabled():
                self.logger.warning(f"Elemento {description} no está habilitado")
                return False

            # Scroll al elemento si es necesario
            await element.scroll_into_view_if_needed()
            time.sleep(0.5)  # Pequeña pausa para estabilizar

            # Hacer click
            await element.click()
            self.logger.info(f"Click realizado en {description}")
            return True

        except Exception as e:
            self.logger.error(f"Error haciendo click en {description}: {e}")
            return False

    async def safe_fill(self, element, value: str, description: str = "campo") -> bool:
        """Llena un campo de forma segura"""
        try:
            if not element or not value:
                self.logger.warning(f"No se puede llenar {description}: elemento o valor inválido")
                return False

            # Limpiar campo primero
            await element.click()
            await element.fill("")
            time.sleep(0.3)

            # Llenar con el nuevo valor
            await element.fill(value)
            self.logger.info(f"Campo {description} llenado correctamente")
            return True

        except Exception as e:
            self.logger.error(f"Error llenando {description}: {e}")
            return False

    def configure_date_range(self, start_date: datetime, end_date: datetime) -> bool:
        """
        Configura el rango de fechas para la extracción
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            True si se configuró correctamente
        """
        self.logger.info(f"Configurando rango de fechas: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
        # Implementación específica en cada extractor
        return True

    # Métodos abstractos que deben implementar las clases hijas
    @abstractmethod
    def login(self) -> bool:
        """Realiza el proceso de login específico de cada plataforma"""
        pass

    @abstractmethod
    def navigate_to_reports_section(self) -> bool:
        """Navega a la sección de reportes específica de cada plataforma"""
        pass

    @abstractmethod
    def extract_report(self, report_type: str, start_date: datetime, end_date: datetime) -> Optional[str]:
        """
        Extrae un reporte específico
        
        Args:
            report_type: Tipo de reporte a extraer
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Ruta del archivo extraído o None si falló
        """
        pass

    def run_extraction(self, report_types: List[str], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Ejecuta el proceso completo de extracción
        
        Args:
            report_types: Lista de tipos de reportes a extraer
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Diccionario con resultados de la extracción
        """
        results = {
            "success": False,
            "extracted_files": [],
            "errors": [],
            "execution_time": 0,
            "company": self.company,
            "platform": self.platform
        }

        start_time = time.time()

        try:
            self.logger.info(f"Iniciando extracción para {self.company.upper()} {self.platform.upper()}")
            self.logger.info(f"Reportes solicitados: {report_types}")
            self.logger.info(f"Rango: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")

            # Configurar navegador
            self.setup_browser()

            # Realizar login
            if not self.login():
                raise Exception("Error en el proceso de login")

            # Navegar a reportes
            if not self.navigate_to_reports_section():
                raise Exception("Error navegando a la sección de reportes")

            # Extraer cada reporte
            for report_type in report_types:
                try:
                    self.logger.info(f"Extrayendo reporte: {report_type}")
                    file_path = self.extract_report(report_type, start_date, end_date)

                    if file_path:
                        results["extracted_files"].append({
                            "report_type": report_type,
                            "file_path": file_path,
                            "success": True
                        })
                        self.logger.info(f"Reporte {report_type} extraído: {file_path}")
                    else:
                        results["errors"].append(f"No se pudo extraer el reporte: {report_type}")
                        self.logger.error(f"Falló extracción de reporte: {report_type}")

                except Exception as e:
                    error_msg = f"Error extrayendo {report_type}: {str(e)}"
                    results["errors"].append(error_msg)
                    self.logger.error(error_msg)

            # Marcar como exitoso si se extrajo al menos un archivo
            results["success"] = len(results["extracted_files"]) > 0

        except Exception as e:
            error_msg = f"Error general en extracción: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)

        finally:
            # Limpiar recursos
            self.cleanup_browser()

            # Calcular tiempo total
            results["execution_time"] = time.time() - start_time

            # Log final
            if results["success"]:
                self.logger.info(f"Extracción completada exitosamente en {results['execution_time']:.2f}s")
                self.logger.info(f"Archivos extraídos: {len(results['extracted_files'])}")
            else:
                self.logger.error(f"Extracción falló después de {results['execution_time']:.2f}s")
                self.logger.error(f"Errores: {len(results['errors'])}")

            # Registrar métricas finales
            self.metrics.log_extraction_completion(
                total_time=results['execution_time'],
                success=results['success'],
                files_extracted=len(results['extracted_files']),
                errors=results['errors']
            )

        return results
