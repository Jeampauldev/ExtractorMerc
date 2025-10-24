"""
Browser Manager - Gestor Centralizado de Navegador
=================================================

Gestor centralizado para manejo de navegador Playwright con configuraciones
optimizadas para extracción de datos de Mercurio.
"""

import os
import logging
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from pathlib import Path

# Importar el detector de plataforma
from ..utils.platform_detector import platform_detector

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Gestor centralizado de navegador para extractores de Mercurio.
    
    Maneja la configuración, inicialización y limpieza del navegador
    con configuraciones optimizadas para cada empresa.
    """
    
    def __init__(self, company: str = "afinia"):
        self.company = company.lower()
        
        # Detectar plataforma automáticamente
        self.platform_config = platform_detector.detect_platform()
        
        # Configurar headless basado en la plataforma detectada
        self.headless = self.platform_config.headless_required
        
        # Aplicar configuración de entorno
        platform_detector.apply_environment_config()
        
        # Log de configuración detectada
        logger.info(f"🖥️ Plataforma detectada: {self.platform_config.platform_type}")
        logger.info(f"🎭 Modo headless: {'Activado' if self.headless else 'Desactivado'}")
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Configurar directorio de descargas usando configuración de plataforma
        self.downloads_dir = self._get_downloads_dir()
        
    def _get_downloads_dir(self) -> str:
        """Obtener directorio de descargas específico por empresa usando configuración de plataforma"""
        # Usar configuración de rutas de la plataforma
        paths_config = self.platform_config.paths_config
        base_dir = Path(paths_config['downloads_base'])
        company_dir = base_dir / self.company / "mercurio"
        company_dir.mkdir(parents=True, exist_ok=True)
        return str(company_dir)
    
    def _get_browser_config(self) -> Dict[str, Any]:
        """Obtener configuración del navegador usando configuración de plataforma"""
        # Obtener configuración base de la plataforma
        platform_browser_config = self.platform_config.browser_config
        
        # Configuración base
        config = {
            "headless": self.headless,
            "args": platform_browser_config.get('args', []).copy(),
            "slow_mo": 100 if not self.headless else 0
        }
        
        # Agregar argumentos adicionales específicos para extracción
        additional_args = [
            "--start-maximized",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding"
        ]
        
        config["args"].extend(additional_args)
        
        # Configurar timeouts más conservadores (solo para el contexto, no para launch)
        config.update({
            "timeout": 15000  # 15 segundos timeout general
        })
        
        return config
    
    def _get_context_config(self) -> Dict[str, Any]:
        """Obtener configuración del contexto"""
        return {
            "viewport": {"width": 1920, "height": 1080},
            "accept_downloads": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    def setup(self) -> bool:
        """
        Configurar e inicializar el navegador.
        
        Returns:
            bool: True si la configuración fue exitosa
        """
        try:
            logger.info(f"[{self.company.upper()}] Inicializando navegador...")
            
            # Inicializar Playwright
            self.playwright = sync_playwright().start()
            
            # Configurar navegador
            browser_config = self._get_browser_config()
            self.browser = self.playwright.chromium.launch(**browser_config)
            
            # Configurar contexto
            context_config = self._get_context_config()
            self.context = self.browser.new_context(**context_config)
            
            # Configurar página
            self.page = self.context.new_page()
            
            # Configurar timeouts más conservadores
            self.page.set_default_timeout(15000)  # 15 segundos
            self.page.set_default_navigation_timeout(30000)  # 30 segundos
            
            # Configurar manejo de errores de página
            self.page.on("pageerror", lambda error: logger.warning(f"[{self.company.upper()}] Page error: {error}"))
            self.page.on("requestfailed", lambda request: logger.warning(f"[{self.company.upper()}] Request failed: {request.url}"))
            
            # Configurar manejo de descargas
            self._setup_download_handler()
            
            logger.info(f"[{self.company.upper()}] Navegador configurado exitosamente")
            logger.info(f"[{self.company.upper()}] Directorio de descargas: {self.downloads_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.company.upper()}] Error configurando navegador: {str(e)}")
            self.cleanup()
            return False
    
    def _setup_download_handler(self) -> None:
        """Configurar manejo de descargas"""
        def handle_download(download):
            try:
                # Generar nombre único para el archivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.company}_{timestamp}_{download.suggested_filename}"
                filepath = os.path.join(self.downloads_dir, filename)
                
                # Guardar archivo
                download.save_as(filepath)
                logger.info(f"[{self.company.upper()}] Archivo descargado: {filename}")
                
                return filepath
                
            except Exception as e:
                logger.error(f"[{self.company.upper()}] Error en descarga: {str(e)}")
                return None
        
        if self.page:
            self.page.on("download", handle_download)
    
    def navigate_to(self, url: str, wait_until: str = "networkidle") -> bool:
        """
        Navegar a una URL específica.
        
        Args:
            url: URL de destino
            wait_until: Condición de espera
            
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            if not self.page:
                raise Exception("Navegador no inicializado")
            
            logger.info(f"[{self.company.upper()}] Navegando a: {url}")
            
            response = self.page.goto(url, wait_until=wait_until)
            
            if response and response.status >= 400:
                raise Exception(f"Error HTTP {response.status}")
            
            logger.info(f"[{self.company.upper()}] Navegación exitosa")
            return True
            
        except Exception as e:
            logger.error(f"[{self.company.upper()}] Error en navegación: {str(e)}")
            return False
    
    def wait_for_element(self, selector: str, timeout: int = 10000) -> bool:
        """
        Esperar a que aparezca un elemento.
        
        Args:
            selector: Selector CSS del elemento
            timeout: Timeout en milisegundos
            
        Returns:
            bool: True si el elemento apareció
        """
        try:
            if not self.page:
                return False
            
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
            
        except Exception as e:
            logger.warning(f"[{self.company.upper()}] Elemento no encontrado: {selector}")
            return False
    
    def get_page(self) -> Optional[Page]:
        """Obtener la página actual"""
        return self.page
    
    def cleanup(self) -> None:
        """Limpiar recursos del navegador"""
        try:
            logger.info(f"[{self.company.upper()}] Limpiando recursos del navegador...")
            
            # Cerrar página con timeout
            if self.page:
                try:
                    self.page.close()
                except Exception as e:
                    logger.warning(f"[{self.company.upper()}] Error cerrando página: {str(e)}")
                finally:
                    self.page = None
            
            # Cerrar contexto con timeout
            if self.context:
                try:
                    self.context.close()
                except Exception as e:
                    logger.warning(f"[{self.company.upper()}] Error cerrando contexto: {str(e)}")
                finally:
                    self.context = None
            
            # Cerrar navegador con timeout
            if self.browser:
                try:
                    self.browser.close()
                except Exception as e:
                    logger.warning(f"[{self.company.upper()}] Error cerrando navegador: {str(e)}")
                finally:
                    self.browser = None
            
            # Detener Playwright con timeout
            if self.playwright:
                try:
                    self.playwright.stop()
                except Exception as e:
                    logger.warning(f"[{self.company.upper()}] Error deteniendo Playwright: {str(e)}")
                finally:
                    self.playwright = None
            
            logger.info(f"[{self.company.upper()}] Recursos limpiados exitosamente")
            
        except Exception as e:
            logger.error(f"[{self.company.upper()}] Error limpiando recursos: {str(e)}")

# Importar datetime para el handler de descargas
from datetime import datetime