#!/usr/bin/env python3
"""
Mercurio Adapter - Adaptador especializado para plataforma Mercurio
===================================================================

Este módulo encapsula toda la lógica específica de la plataforma Mercurio
que es común entre diferentes empresas (Afinia, Aire, etc.), permitiendo
reutilizar código y mantener consistencia.

Características principales:
- Manejo específico de autenticación en Mercurio
- Navegación estándar entre módulos (PQRs, RRAs, etc.)
- Configuración de filtros y fechas específica del sistema
- Gestión de descargas de reportes Excel
- Adaptación a diferentes empresas usando la misma plataforma

Basado en los patrones exitosos de los extractores legacy de Mercurio.

Autor: ExtractorOV Team
Fecha: 2025-09-26
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importaciones absolutas
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .browser_manager import BrowserManager
from .authentication_manager import AuthenticationManager
from src_OV.core.download_manager import DownloadManager
from src_OV.components.date_configurator import DateConfigurator, DateFormat
from src_OV.components.filter_manager import FilterManager
from src_OV.components.popup_handler import PopupHandler
from src_OV.components.report_processor import ReportProcessor

logger = logging.getLogger(__name__)

class MercurioAdapter:
    """
    Adaptador especializado para la plataforma Mercurio
    
    Encapsula toda la lógica común de navegación, autenticación y descarga
    que es específica de la plataforma Mercurio, independientemente
    de la empresa (Afinia, Aire, etc.)
    """
    
    def __init__(self, page: Page, company: str, config: Dict[str, Any]):
        """
        Inicializa el adaptador de Mercurio
        
        Args:
            page: Página de Playwright
            company: Nombre de la empresa (afinia, aire, etc.)
            config: Configuración específica de la empresa
        """
        self.page = page
        self.company = company.lower()
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{company.upper()}")
        
        # Configurar componentes modulares
        self.auth_manager = AuthenticationManager(self.company)
        self.download_manager = DownloadManager(page, f"downloads/{company}/mercurio")
        self.date_config = DateConfigurator(page)
        self.filter_manager = FilterManager(page) 
        self.popup_handler = PopupHandler(page)
        self.report_processor = ReportProcessor(f"downloads/{company}/mercurio")
        
        # Configurar selectores específicos de Mercurio
        self._setup_selectors()
        
        # Configurar manejo de popups específicos
        self._setup_popup_handlers()
    
    def _setup_selectors(self):
        """Configura los selectores específicos de la plataforma Mercurio"""
        # Selectores base de Mercurio (comunes para todas las empresas)
        self.base_selectors = {
            # Elementos de login estándar de Mercurio
            'username': [
                "input[name='txtUsuario']",
                "input[id='txtUsuario']",
                "input[type='text'][placeholder*='usuario']",
                "input[class*='form-control']:first-of-type"
            ],
            'password': [
                "input[name='txtClave']",
                "input[id='txtClave']",
                "input[type='password']",
                "input[class*='form-control'][type='password']"
            ],
            'login_button': [
                "input[name='btnIniciarSesion']",
                "input[id='btnIniciarSesion']",
                "input[type='submit'][value*='Ingresar']",
                "input[type='submit'][value*='Iniciar']",
                "button[type='submit']",
                "#btnIniciarSesion"
            ],
            
            # Navegación específica de Mercurio
            'menu_pqrs': [
                "a[href*='PQRs']",
                "a:has-text('PQRs')",
                "a:has-text('PQR')",
                ".menu-item:has-text('PQR')",
                "li:has-text('PQR')"
            ],
            'menu_rras': [
                "a[href*='RRAs']",
                "a:has-text('RRAs')",
                "a:has-text('RRA')",
                ".menu-item:has-text('RRA')",
                "li:has-text('RRA')"
            ],
            
            # Elementos de descarga de reportes
            'download_button': [
                "#btnGenerarExcel",
                "input[id='btnGenerarExcel']",
                "input[value*='Excel']",
                "button:has-text('Generar Excel')",
                "button:has-text('Exportar')",
                "a:has-text('Descargar')"
            ],
            
            # Filtros de fecha específicos de Mercurio
            'date_from': [
                "input[name*='fechaInicio']",
                "input[id*='fechaInicio']",
                "#txtFechaInicio",
                "input[type='date']:first-of-type"
            ],
            'date_to': [
                "input[name*='fechaFin']", 
                "input[id*='fechaFin']",
                "#txtFechaFin",
                "input[type='date']:last-of-type"
            ],
            
            # Indicadores de éxito específicos
            'success_indicators': [
                ".menu-principal",
                ".navbar",
                "iframe[name='contenido']",
                "frame[name='contenido']",
                "table[class*='grid']",
                ".panel-heading"
            ]
        }
        
        # Fusionar con selectores específicos de la empresa si existen
        if 'selectors' in self.config:
            self.selectors = {**self.base_selectors, **self.config['selectors']}
        else:
            self.selectors = self.base_selectors
    
    def _setup_popup_handlers(self):
        """Configura el manejo específico de popups de Mercurio"""
        try:
            from src_OV.components.popup_handler import PopupConfig, PopupType, PopupAction
            from dataclasses import dataclass
        except ImportError:
            # Fallback si no están disponibles los componentes avanzados
            self.logger.warning("Componentes de popup no disponibles, usando manejo básico")
            return
        
        # Crear configuración de popup usando dataclass
        @dataclass
        class MercurioPopupConfig:
            name: str = "mercurio_alert"
            popup_type: PopupType = PopupType.ERROR_DIALOG
            selectors: list = None
            action: PopupAction = PopupAction.ACCEPT
            priority: int = 1
            timeout: float = 5.0
            text_patterns: list = None
            
            def __post_init__(self):
                if self.selectors is None:
                    self.selectors = ["dialog", "alert"]
                if self.text_patterns is None:
                    self.text_patterns = ['Error', 'Aviso', 'Información']
        
        # Crear configuración de popup
        mercurio_alert_config = MercurioPopupConfig()
        
        self.popup_handler.add_config(mercurio_alert_config)
    
    def perform_login(self, username: str, password: str) -> bool:
        """
        Realiza el login usando los componentes modulares
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            bool: True si el login fue exitoso
        """
        try:
            self.logger.info("=== INICIANDO LOGIN EN MERCURIO ===")
            
            # Realizar login usando el authentication manager con credenciales
            success = self.auth_manager.authenticate(
                page=self.page,
                username=username,
                password=password
            )
            
            if success:
                self.logger.info("✅ Login exitoso en Mercurio")
                
                # Configuraciones post-login específicas de Mercurio
                self._post_login_setup()
                
                # Verificar indicadores específicos de Mercurio
                success = self._verify_mercurio_login_success()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error durante login: {e}")
            return False
    
    def _post_login_setup(self):
        """Configuraciones específicas post-login para Mercurio"""
        try:
            # Esperar a que se cargue el frame principal de Mercurio
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Verificar si hay frames y cambiar al frame principal si es necesario
            frames = self.page.frames
            if len(frames) > 1:
                self.logger.info(f"Detectados {len(frames)} frames, verificando frame principal...")
                for frame in frames:
                    if 'contenido' in frame.name.lower():
                        self.logger.info("✅ Frame principal detectado")
                        break
            
        except Exception as e:
            self.logger.warning(f"Error en configuración post-login: {e}")
    
    def _verify_mercurio_login_success(self) -> bool:
        """Verifica el login exitoso con indicadores específicos de Mercurio"""
        try:
            # Indicadores específicos de Mercurio
            mercurio_success_indicators = [
                ".menu-principal",
                ".navbar",
                "iframe[name='contenido']",
                "frame[name='contenido']", 
                "table[class*='grid']",
                ".panel-heading",
                "a:has-text('PQR')",
                "a:has-text('RRA')"
            ]
            
            for indicator in mercurio_success_indicators:
                try:
                    element = self.page.wait_for_selector(indicator, timeout=5000)
                    if element and element.is_visible():
                        self.logger.info(f"✅ Indicador de login exitoso: {indicator}")
                        return True
                except:
                    continue
            
            # Verificar URL - debe contener 'mercurio' y no 'login'
            current_url = self.page.url.lower()
            if "mercurio" in current_url and "login" not in current_url:
                self.logger.info("✅ Login exitoso - URL cambió correctamente")
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Error verificando login: {e}")
            return False
    
    def navigate_to_module(self, module_type: str) -> bool:
        """
        Navega a un módulo específico de Mercurio (PQRs, RRAs, etc.)
        
        Args:
            module_type: Tipo de módulo ('pqrs', 'rras', etc.)
            
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            self.logger.info(f"=== NAVEGANDO A MÓDULO {module_type.upper()} ===")
            
            # Seleccionar selectores según el módulo
            if module_type.lower() in ['pqr', 'pqrs']:
                selectors = self.selectors['menu_pqrs']
            elif module_type.lower() in ['rra', 'rras']:
                selectors = self.selectors['menu_rras']
            else:
                self.logger.error(f"Módulo desconocido: {module_type}")
                return False
            
            # Intentar navegación con cada selector
            for selector in selectors:
                try:
                    element = self.page.wait_for_selector(selector, timeout=5000)
                    if element and element.is_visible():
                        element.click()
                        
                        # Esperar navegación
                        self.page.wait_for_load_state("networkidle")
                        time.sleep(3)
                        
                        self.logger.info(f"✅ Navegación exitosa a {module_type} usando: {selector}")
                        return True
                        
                except:
                    continue
            
            self.logger.warning(f"⚠️ No se pudo navegar a módulo {module_type}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error navegando a módulo {module_type}: {e}")
            return False
    
    def navigate_to_report_section(self, report_config: Dict[str, Any]) -> bool:
        """
        Navega a una sección específica de reporte dentro de un módulo
        
        Args:
            report_config: Configuración del reporte con url_suffix
            
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            if 'url_suffix' not in report_config:
                self.logger.error("Configuración de reporte sin url_suffix")
                return False
            
            # Construir URL completa
            base_url = self.config['url'].rstrip('/')
            report_url = f"{base_url}/{report_config['url_suffix']}"
            
            self.logger.info(f"Navegando a: {report_url}")
            
            # Navegar directamente a la sección del reporte
            self.page.goto(report_url, timeout=30000, wait_until="domcontentloaded")
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # Verificar que estamos en la página correcta
            current_url = self.page.url
            if report_config['url_suffix'] in current_url:
                self.logger.info("✅ Navegación exitosa a sección de reporte")
                return True
            else:
                self.logger.warning(f"⚠️ URL actual no coincide: {current_url}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error navegando a sección de reporte: {e}")
            return False
    
    def configure_date_range(self, days_back: int = 30) -> bool:
        """
        Configura el rango de fechas usando el date configurator
        
        Args:
            days_back: Días hacia atrás para el reporte
            
        Returns:
            bool: True si se configuró exitosamente
        """
        try:
            self.logger.info(f"=== CONFIGURANDO FECHAS ({days_back} días) ===")
            
            # Crear rango de fechas
            date_range = self.date_config.create_date_range(days_back=days_back)
            
            # Configurar selectores específicos de Mercurio
            date_selectors = {
                'start_date': self.selectors['date_from'][0] if self.selectors['date_from'] else None,
                'end_date': self.selectors['date_to'][0] if self.selectors['date_to'] else None
            }
            
            # Aplicar configuración de fechas
            success = self.date_config.configure_date_range(
                date_range=date_range,
                selectors=date_selectors
            )
            
            if success:
                self.logger.info("✅ Fechas configuradas exitosamente")
            else:
                self.logger.warning("⚠️ No se pudieron configurar las fechas automáticamente")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error configurando fechas: {e}")
            return False
    
    def download_report(self, report_config: Dict[str, Any], custom_filename: Optional[str] = None) -> Optional[str]:
        """
        Descarga un reporte específico usando el download manager
        
        Args:
            report_config: Configuración del reporte con download_selector
            custom_filename: Nombre personalizado para el archivo (sin extensión)
            
        Returns:
            str: Ruta del archivo descargado o None si falló
        """
        try:
            self.logger.info(f"=== DESCARGANDO REPORTE: {report_config.get('name', 'Desconocido')} ===")
            
            # Configurar selector de descarga
            download_selector = report_config.get('download_selector', self.selectors['download_button'][0])
            
            # Descargar usando el download manager
            file_path = self.download_manager.download_report(
                company=self.company,
                report_type=report_config.get('name', 'reporte'),
                button_selectors=[download_selector],
                timeout=60000,
                custom_filename=custom_filename
            )
            
            if file_path:
                self.logger.info(f"✅ Reporte descargado: {file_path}")
                
                # Procesar archivo descargado
                self._process_downloaded_file(file_path, report_config)
                
                return file_path
            else:
                self.logger.warning(f"⚠️ No se pudo descargar el reporte")
                return None
                
        except Exception as e:
            self.logger.error(f"Error descargando reporte: {e}")
            return None
    
    def _process_downloaded_file(self, file_path: str, report_config: Dict[str, Any]):
        """Procesa un archivo descargado usando el report processor"""
        try:
            self.logger.info(f"=== PROCESANDO ARCHIVO: {file_path} ===")
            
            metadata = self.report_processor.process_file(
                file_path=file_path,
                company=self.company,
                report_type="mercurio_report"
            )
            
            if metadata.is_valid:
                self.logger.info(f"✅ Procesado: {metadata.final_path}")
            else:
                self.logger.warning(f"⚠️ Error procesando: {metadata.error_message}")
                
        except Exception as e:
            self.logger.error(f"Error procesando archivo {file_path}: {e}")
    
    def get_company_specific_config(self) -> Dict[str, Any]:
        """
        Obtiene configuración específica de la empresa
        
        Returns:
            Dict: Configuración adaptada a la empresa
        """
        base_config = {
            'login_timeout': 30.0,
            'download_timeout': 60.0,
            'navigation_timeout': 15.0,
            'default_date_range': 30
        }
        
        # Configuraciones específicas por empresa
        company_configs = {
            'afinia': {
                'base_url': 'https://mercurio.afinia.com.co/',
                'main_modules': ['PQRs'],
                'default_reports': ['pqr_escritas', 'verbales']
            },
            'aire': {
                'base_url': 'https://mercurio.aire.com.co/',
                'main_modules': ['PQRs', 'RRAs'],
                'default_reports': ['pqr_pendientes', 'rra_pendientes', 'rra_recibidas']
            }
        }
        
        company_config = company_configs.get(self.company, {})
        return {**base_config, **company_config}
    
    def get_adapter_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del adaptador
        
        Returns:
            Dict: Estadísticas de uso
        """
        return {
            'company': self.company,
            'platform': 'mercurio',
            'popup_stats': self.popup_handler.get_stats() if hasattr(self.popup_handler, 'get_stats') else {},
            'download_stats': self.download_manager.get_download_stats() if hasattr(self.download_manager, 'get_download_stats') else {},
            'processing_stats': self.report_processor.get_processing_stats() if hasattr(self.report_processor, 'get_processing_stats') else {},
            'config_loaded': bool(self.config)
        }

# Funciones de utilidad para facilitar el uso del adaptador
def create_mercurio_adapter(page: Page, company: str, config: Dict[str, Any]) -> MercurioAdapter:
    """
    Factory function para crear adaptador de Mercurio
    
    Args:
        page: Página de Playwright
        company: Nombre de la empresa
        config: Configuración de la empresa
        
    Returns:
        MercurioAdapter: Adaptador configurado
    """
    return MercurioAdapter(page, company, config)

if __name__ == "__main__":
    # Ejemplo de uso del adaptador
    print("=== Mercurio Adapter - Información ===")
    print("Este módulo proporciona adaptación específica para la plataforma Mercurio")
    print("Empresas soportadas: Afinia, Aire")
    print("Funcionalidades: Login, Navegación módulos, Descarga de reportes, Procesamiento")

