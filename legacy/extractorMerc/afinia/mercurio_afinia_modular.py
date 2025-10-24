#!/usr/bin/env python3
"""
Mercurio AFINIA Extractor - Versión Modular Completa
====================================================

Extractor completamente modular para Mercurio de AFINIA, utilizando todos los
componentes modulares implementados y el adaptador específico de Mercurio.

Este extractor replica las funcionalidades de los extractores legacy pero
con una arquitectura completamente modular, reutilizable y mantenible.

Características principales:
- Arquitectura completamente modular
- Reutilización del adaptador de Mercurio
- Configuración específica para AFINIA
- Manejo robusto de errores y popups
- Métricas y monitoring integrados
- Procesamiento automático de archivos descargados
- Soporte para múltiples tipos de reportes PQR

Basado en los patrones exitosos de los extractores legacy de Mercurio.
Autor: ExtractorOV Team  
Fecha: 2025-09-26
"""

import sys
import os
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configurar paths para importaciones
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Importar componentes modulares
from a1_core.browser_manager import BrowserManager
from a1_core.authentication import AuthenticationManager
from a1_core.download_manager import DownloadManager
from c3_components.date_configurator import DateConfigurator
from c3_components.popup_handler import PopupHandler
from g7_utils.performance_monitor import PerformanceMonitor, TimingContext
from f6_config.config import get_extractor_config

# Cargar variables de entorno
from dotenv import load_dotenv
env_file = Path(__file__).parent.parent.parent.parent / "env" / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=str(env_file), override=True)
    print(f"✅ Variables de entorno cargadas desde: {env_file}")

class MercurioAfiniaModular:
    """
    Extractor modular para Mercurio de AFINIA
    
    Utiliza todos los componentes modulares implementados y el adaptador
    específico de Mercurio para proporcionar funcionalidad completa
    de extracción de reportes PQR.
    """
    
    def __init__(self, headless: bool = False, company: str = "afinia"):
        """
        Inicializa el extractor modular de AFINIA
        
        Args:
            headless: Si ejecutar en modo headless
            company: Nombre de la empresa (por defecto 'afinia')
        """
        self.company = company.lower()
        self.headless = headless
        self.logger = logging.getLogger(f"{__name__}.{company.upper()}")
        
        # Configurar logging específico
        logging.basicConfig(
            level=logging.INFO,
            format=f'[MODULAR-MERCURIO-{company.upper()} %(levelname)s] %(message)s'
        )
        
        # Inicializar componentes
        self.browser_manager = None
        self.browser = None
        self.page = None
        self.perf_monitor = PerformanceMonitor(include_args=True)

        # Componentes modulares
        self.auth_manager = None
        self.download_manager = None
        self.date_configurator = None
        self.popup_handler = None
        
        # Cargar configuración específica de AFINIA
        self.config = self._load_afinia_config()
        
        # Validar configuración
        self._validate_config()
        
        self.logger.info(f"✅ {self.__class__.__name__} inicializado")
    
    def _load_afinia_config(self) -> Dict[str, Any]:
        """Carga la configuración específica para AFINIA"""
        try:
            # Intentar cargar desde el sistema de configuración centralizada
            config = get_extractor_config("afinia", "mercurio")
            
            if config:
                self.logger.info("✅ Configuración AFINIA cargada desde sistema centralizado")
                return config
            
        except Exception as e:
            self.logger.warning(f"No se pudo cargar config centralizada: {e}")
        
        # Configuración de fallback específica para AFINIA
        fallback_config = {
            # URLs específicas de AFINIA
            'url': 'https://mercurio.afinia.com.co/Mercurio/',
            'base_url': 'https://mercurio.afinia.com.co/',
            
            # Credenciales desde variables de entorno
            'username': os.getenv('MERCURIO_AFINIA_USERNAME', ''),
            'password': os.getenv('MERCURIO_AFINIA_PASSWORD', ''),
            
            # Configuraciones específicas de AFINIA
            'company_name': 'AFINIA',
            'platform': 'mercurio',
            'timeouts': {
                'navigation': 30000,
                'login': 45000,
                'download': 60000
            },
            'reports': {
                'pqr_escritas': {
                    'name': 'PQR Escritas Pendientes',
                    'url_suffix': 'PQRs/PQRsEscritas',
                    'download_selector': '#btnGenerarExcel'
                },
                'verbales': {
                    'name': 'PQR Verbales Pendientes', 
                    'url_suffix': 'PQRs/PQRsVerbales',
                    'download_selector': '#btnGenerarExcel'
                }
            }
        }
        
        self.logger.info("✅ Usando configuración de fallback para AFINIA")
        return fallback_config
    
    def _validate_config(self):
        """Valida que la configuración esté completa"""
        required_fields = ['url', 'username', 'password']
        missing_fields = []
        
        for field in required_fields:
            if not self.config.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Configuración incompleta para AFINIA - Faltan: {missing_fields}")
        
        self.logger.info("✅ Configuración AFINIA Mercurio válida")
    
    @PerformanceMonitor(include_args=True)
    def setup_browser(self) -> bool:
        """
        Configura el navegador usando el BrowserManager modular
        
        Returns:
            bool: True si se configuró exitosamente
        """
        try:
            self.logger.info("=== CONFIGURANDO NAVEGADOR Y COMPONENTES ===")
            
            # Usar BrowserManager modular
            self.browser_manager = BrowserManager(
                headless=self.headless,
                viewport={'width': 1366, 'height': 768}
            )
            
            # Configurar browser y página
            self.browser, self.page = self.browser_manager.setup_browser()
            
            # Configurar timeouts específicos para AFINIA
            self.page.set_default_timeout(self.config['timeouts']['navigation'])
            
            # Inicializar componentes con la página ya creada
            self.auth_manager = AuthenticationManager(self.page, f"downloads/{self.company}/mercurio/screenshots")
            self.download_manager = DownloadManager(self.page, f"downloads/{self.company}/mercurio")
            self.date_configurator = DateConfigurator(self.page)
            self.popup_handler = PopupHandler(self.page)

            self.logger.info("✅ Navegador y componentes configurados exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando navegador: {e}")
            return False
    
    @PerformanceMonitor()
    def navigate_to_site(self) -> bool:
        """
        Navega al sitio de Mercurio de AFINIA
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            self.logger.info("=== NAVEGANDO A MERCURIO AFINIA ===")
            
            url = self.config['url']
            self.logger.info(f"Navegando a: {url}")
            
            # Crear directorio para screenshots
            screenshot_dir = Path("downloads") / self.company / "mercurio" / "screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            # Navegar con manejo robusto
            self.page.goto(url, timeout=self.config['timeouts']['navigation'], wait_until="domcontentloaded")
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # Tomar screenshot inicial
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.page.screenshot(path=screenshot_dir / f"step1_initial_{timestamp}.png")
            
            # Verificar que llegamos correctamente
            current_url = self.page.url
            title = self.page.title()
            
            self.logger.info(f"✅ Navegación exitosa - URL: {current_url}")
            self.logger.info(f"✅ Título de página: {title}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error navegando al sitio: {e}")
            return False
    
    @PerformanceMonitor()
    def perform_login(self) -> bool:
        """
        Realiza login usando el adaptador modular de Mercurio
        
        Returns:
            bool: True si fue exitoso
        """
        try:
            with TimingContext("mercurio_login_process"):
                self.logger.info("=== INICIANDO LOGIN EN MERCURIO ===")
                
                # Usar adaptador para realizar login
                username = self.config['username']
                password = self.config['password']
                
                self.logger.info(f"Iniciando login para: {username[:10]}...")
                
                login_success = self.mercurio_adapter.perform_login(username, password)
                
                if login_success:
                    self.logger.info("✅ Login exitoso en Mercurio AFINIA")
                    
                    # Tomar screenshot de éxito
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_dir = Path("downloads") / self.company / "mercurio" / "screenshots"
                    self.page.screenshot(path=screenshot_dir / f"step2_login_success_{timestamp}.png")
                    
                    return True
                else:
                    self.logger.error("❌ Login falló")
                    return False
                
        except Exception as e:
            self.logger.error(f"❌ Error en proceso de login: {e}")
            return False
    
    @PerformanceMonitor()
    def download_all_reports(self, days_back: int = 30) -> List[str]:
        """
        Descarga todos los reportes configurados usando el adaptador
        
        Args:
            days_back: Días hacia atrás para los reportes
            
        Returns:
            List[str]: Lista de archivos descargados
        """
        try:
            self.logger.info("=== INICIANDO DESCARGA DE REPORTES ===")
            
            downloaded_files = []
            report_configs = self.config.get('reports', {})
            
            for report_key, report_config in report_configs.items():
                try:
                    self.logger.info(f"Procesando reporte: {report_config['name']}")
                    
                    # Navegar a la sección del reporte
                    navigation_success = self.mercurio_adapter.navigate_to_report_section(report_config)
                    
                    if not navigation_success:
                        self.logger.warning(f"⚠️ No se pudo navegar a {report_config['name']}")
                        continue
                    
                    # Configurar fechas
                    date_success = self.mercurio_adapter.configure_date_range(days_back)
                    if not date_success:
                        self.logger.warning(f"⚠️ No se pudieron configurar fechas para {report_config['name']}")
                    
                    # Descargar el reporte
                    file_path = self.mercurio_adapter.download_report(report_config)
                    
                    if file_path:
                        downloaded_files.append(file_path)
                        self.logger.info(f"✅ {report_config['name']}: archivo descargado - {file_path}")
                    else:
                        self.logger.warning(f"⚠️ {report_config['name']}: No se descargó archivo")
                    
                    time.sleep(2)  # Pausa entre reportes
                    
                except Exception as e:
                    self.logger.error(f"Error procesando reporte {report_key}: {e}")
                    continue
            
            self.logger.info(f"✅ Descarga completada: {len(downloaded_files)} archivos en total")
            return downloaded_files
            
        except Exception as e:
            self.logger.error(f"❌ Error en descarga de reportes: {e}")
            return []
    
    @PerformanceMonitor()
    def run_complete_extraction(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Ejecuta el proceso completo de extracción
        
        Args:
            days_back: Días hacia atrás para los reportes
            
        Returns:
            Dict: Resultado del proceso con archivos y métricas
        """
        try:
            self.logger.info("🚀 INICIANDO EXTRACCIÓN COMPLETA DE AFINIA MERCURIO")
            
            # Paso 1: Configurar navegador
            if not self.setup_browser():
                return {'success': False, 'error': 'Error configurando navegador'}
            
            # Paso 2: Navegar al sitio
            if not self.navigate_to_site():
                return {'success': False, 'error': 'Error navegando al sitio'}
            
            # Paso 3: Realizar login
            if not self.perform_login():
                return {'success': False, 'error': 'Error en login'}
            
            # Paso 4: Descargar reportes
            downloaded_files = self.download_all_reports(days_back)
            
            # Generar resultado
            result = {
                'success': True,
                'files': downloaded_files,
                'metrics': {
                    'total_files': len(downloaded_files),
                    'extraction_date': datetime.now().isoformat(),
                    'days_back': days_back,
                    'company': self.company,
                    'platform': 'mercurio'
                }
            }
            
            self.logger.info("🎉 EXTRACCIÓN COMPLETA EXITOSA")
            self.logger.info(f"   - Duración: {self.perf_monitor.get_total_time():.2f} segundos")
            self.logger.info(f"   - Archivos descargados: {len(downloaded_files)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error en extracción completa: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            # Cleanup de recursos
            self._cleanup()
    
    def _cleanup(self):
        """Limpia recursos del navegador"""
        try:
            self.logger.info("🧹 Iniciando cleanup de recursos del navegador...")
            
            if self.browser_manager:
                self.browser_manager.cleanup()
                self.logger.info("✅ Cleanup completado")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Error durante cleanup: {e}")

# Función de conveniencia para uso directo
def extract_afinia_mercurio(days_back: int = 30, headless: bool = True) -> Dict[str, Any]:
    """
    Función de conveniencia para extraer datos de Mercurio Afinia
    
    Args:
        days_back: Días hacia atrás para los reportes
        headless: Si ejecutar en modo headless
        
    Returns:
        Dict: Resultado de la extracción
    """
    extractor = MercurioAfiniaModular(headless=headless)
    return extractor.run_complete_extraction(days_back=days_back)

if __name__ == "__main__":
    # Ejecutar extractor directamente si se llama como script
    import argparse
    
    parser = argparse.ArgumentParser(description='Extractor Modular Mercurio AFINIA')
    parser.add_argument('--days', type=int, default=30, help='Días hacia atrás para extraer')
    parser.add_argument('--headless', action='store_true', help='Ejecutar en modo headless')
    parser.add_argument('--verbose', action='store_true', help='Logging detallado')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    print("🚀 Iniciando Extractor Modular Mercurio AFINIA")
    print(f"📅 Extrayendo últimos {args.days} días")
    print(f"👁️ Modo headless: {args.headless}")
    
    result = extract_afinia_mercurio(days_back=args.days, headless=args.headless)
    
    if result['success']:
        print("✅ EXTRACCIÓN EXITOSA")
        print(f"📁 Archivos descargados: {result['metrics']['total_files']}")
        for file_path in result['files']:
            print(f"   - {file_path}")
    else:
        print("❌ EXTRACCIÓN FALLÓ")
        print(f"   Error: {result.get('error', 'Error desconocido')}")
        sys.exit(1)
