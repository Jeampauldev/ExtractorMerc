#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extractor modular mejorado para Oficina Virtual de Afinia
Incorpora las mejores prácticas del código original funcional
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.core.browser_manager import BrowserManager
from src.core.authentication import AuthenticationManager
from src.core.download_manager import DownloadManager
from src.components.popup_handler import PopupHandler
from src.components.afinia_popup_handler import AfiniaPopupHandler
from src.components.report_processor import ReportProcessor
from src.components.pqr_detail_extractor import PQRDetailExtractor
from src.components.afinia_date_configurator import AfiniaDateConfigurator
from src.components.afinia_download_manager import AfiniaDownloadManager
from src.components.afinia_filter_manager import AfiniaFilterManager
from src.components.afinia_pqr_processor import AfiniaPQRProcessor
from src.components.filter_manager import FilterManager, FilterConfig, FilterType
from src.processors.afinia.logger import MetricsCollector
from src.config.config import OficinaVirtualConfig
from src.config.afinia_config import setup_afinia_components
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Configuración de logging
import logging
logger = logging.getLogger('AFINIA-OV')


class OficinaVirtualAfiniaModular:
    """
    Extractor modular mejorado para Oficina Virtual de Afinia
    Incorpora las mejores prácticas del código original funcional
    """

    def __init__(self, headless: bool = True, visual_mode: bool = False, 
                 enable_pqr_processing: bool = False, max_pqr_records: int = 5):
        """
        Inicializa el extractor modular de Afinia

        Args:
            headless: Ejecutar en modo headless
            visual_mode: Ejecutar en modo visual para debugging
            enable_pqr_processing: Habilitar procesamiento específico de PQR
            max_pqr_records: Número máximo de registros PQR a procesar
        """
        self.headless = headless if not visual_mode else False
        self.visual_mode = visual_mode
        self.enable_pqr_processing = enable_pqr_processing
        self.max_pqr_records = max_pqr_records
        self.config = self._load_config()

        # Componentes principales
        self.browser_manager = None
        self.browser = None
        self.page = None
        self.metrics = MetricsCollector()

        # Componentes modulares
        self.auth_manager = None
        self.download_manager = None
        self.popup_handler = None
        self.afinia_popup_handler = None
        self.report_processor = None
        self.pqr_extractor = None
        self.afinia_date_configurator = None
        self.afinia_download_manager = None
        self.afinia_filter_manager = None
        self.afinia_pqr_processor = None  # Nuevo procesador específico de PQR
        self.filter_manager = None

        logger.info(f"OficinaVirtualAfiniaModular inicializado - Modo: {'Visual' if visual_mode else 'Headless'}")

    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración específica para Afinia"""
        project_root = Path(__file__).parent.parent.parent.parent

        default_config = {
            'url': os.getenv('OV_AFINIA_URL', 'https://caribemar.facture.co/'),
            'pqr_url': os.getenv('OV_AFINIA_PQR_URL', 'https://caribemar.facture.co/Listado-Radicaci%C3%B3n-PQR#/Detail'),
            'username': os.getenv('OV_AFINIA_USERNAME', ''),
            'password': os.getenv('OV_AFINIA_PASSWORD', ''),
            'timeout': int(os.getenv('BROWSER_TIMEOUT', '90000')),  # Aumentado a 90 segundos
            'download_path': str(project_root / 'data' / 'downloads' / 'afinia' / 'oficina_virtual'),
            'screenshots_dir': str(project_root / 'data' / 'downloads' / 'afinia' / 'oficina_virtual' / 'screenshots'),
            'max_records': int(os.getenv('MAX_RECORDS_PER_SESSION', '50')),
            'retry_attempts': int(os.getenv('RETRY_ATTEMPTS', '3')),
            'popup_selectors': [
                "#myModal",
                "#myModal .close",
                "#myModal .modal-header .close",
                "div.modal",
                ".modal .close",
                ".modal-backdrop",
                "button[id='closePopUp']",
                "button.close",
                "[data-dismiss='modal']",
                ".modal-header .close",
                "button:has-text('Cerrar')",
                "button:has-text('×')",
                "button:has-text('OK')",
                "button:has-text('Aceptar')"
            ],
            'login_selectors': {
                'username': [
                    "input[name='dnn$ctr$Login$Login_DotNetNuke.Membership.GatewayMembershipProvider$txtUsername']",
                    "#dnn_ctr_Login_Login_DotNetNuke_Membership_GatewayMembershipProvider_txtUsername",
                    "input[type='text'][name*='Username']"
                ],
                'password': [
                    "input[name='dnn$ctr$Login$Login_DotNetNuke.Membership.GatewayMembershipProvider$txtPassword']",
                    "#dnn_ctr_Login_Login_DotNetNuke_Membership_GatewayMembershipProvider_txtPassword",
                    "input[type='password'][name*='Password']"
                ],
                'submit': [
                    "a[id='dnn_ctr_Login_Login_DotNetNuke_Membership_GatewayMembershipProvider_cmdLogin']",
                    "#dnn_ctr_Login_Login_DotNetNuke_Membership_GatewayMembershipProvider_cmdLogin",
                    "a:has-text('Ingresar')",
                    "button:has-text('Ingresar')"
                ]
            },
            'filter_selectors': {
                'status': [
                    "md-select[name='Estado']",
                    "#select_3",
                    "md-select[aria-label*='Estado']"
                ],
                'status_option': [
                    "md-option:has-text('Finalizado')",
                    "md-option[value='Finalizado']",
                    "[role='option']:has-text('Finalizado')",
                    "md-select-menu md-option:has-text('Finalizado')"
                ],
                'date_initial': [
                    "md-datepicker[ng-model='filtros.fechaInicial'] input",
                    "input.md-datepicker-input[placeholder='YYYY-MM-DD']",
                    "md-datepicker[name='Fecha inicial'] input",
                    ".campo-fecha input[placeholder*='YYYY-MM-DD']"
                ],
                'date_final': [
                    "md-datepicker[ng-model='filtros.fechaFinal'] input",
                    "md-datepicker[name='Fecha inicial']:nth-of-type(2) input",
                    ".campo-fecha:nth-of-type(2) input[placeholder*='YYYY-MM-DD']"
                ],
                'search_button': [
                    "button:has-text('Buscar')",
                    "button[class*='btn-primary']",
                    "button[ng-click*='buscar']",
                    "md-button:has-text('Buscar')"
                ]
            }
        }

        # Aplicar configuración del sistema
        system_config = OficinaVirtualConfig.AFINIA
        for key, value in system_config.items():
            if key in default_config:
                default_config[key] = value

        return default_config

    async def _setup_components(self):
        """Inicializa y configura todos los componentes necesarios"""
        try:
            logger.info("CONFIGURANDO Inicializando componentes modulares...")

            # Inicializar BrowserManager
            logger.info(f"CONFIGURANDO Configurando BrowserManager con timeout: {self.config['timeout']}ms")
            self.browser_manager = BrowserManager(
                headless=self.headless,
                timeout=self.config['timeout'],
                screenshots_dir=self.config['screenshots_dir']
            )

            # Configurar browser y page
            await self.browser_manager.__aenter__()
            self.page = self.browser_manager.page
            self.context = self.browser_manager.context

            # Verificar que page y context se inicializaron correctamente
            if not self.page:
                raise Exception("Error: self.page es None después de inicializar BrowserManager")
            if not self.context:
                raise Exception("Error: self.context es None después de inicializar BrowserManager")

            # Configurar timeout por defecto
            self.context.set_default_timeout(self.config['timeout'])
            self.page.set_default_timeout(self.config['timeout'])

            # Configurar componentes modulares
            self.auth_manager = AuthenticationManager(
                self.page,
                self.config['login_selectors']
            )

            self.download_manager = DownloadManager(
                self.page,
                self.config['download_path']
            )

            # Inicializar PopupHandler específico de Afinia (optimizado)
            self.afinia_popup_handler = AfiniaPopupHandler(self.page)

            self.report_processor = ReportProcessor()

            self.pqr_extractor = PQRDetailExtractor(
                self.page,
                self.config['download_path'],
                self.config['screenshots_dir']
            )

            # Componentes específicos de Afinia
            self.afinia_date_configurator = AfiniaDateConfigurator(self.page)
            self.afinia_download_manager = AfiniaDownloadManager(self.page, self.config['download_path'])
            self.afinia_filter_manager = AfiniaFilterManager(self.page)

            self.filter_manager = FilterManager(self.page)
            
            # Inicializar procesador específico de PQR si está habilitado
            if self.enable_pqr_processing:
                logger.info("CONFIGURANDO Inicializando procesador específico de PQR...")
                self.afinia_pqr_processor = AfiniaPQRProcessor(
                    self.page,
                    self.config['download_path'],
                    self.config['screenshots_dir']
                )
                logger.info("EXITOSO Procesador de PQR inicializado")

            logger.info("EXITOSO Componentes inicializados correctamente")
            return True

        except Exception as e:
            logger.error(f"ERROR Error inicializando componentes: {e}")
            return False

    async def run_full_extraction(self, username: str = None, password: str = None,
                                start_date: datetime = None, end_date: datetime = None) -> Dict:
        """
        Ejecuta el proceso completo de extracción

        Args:
            username: Usuario para login (opcional, usa config si no se provee)
            password: Contraseña para login (opcional, usa config si no se provee)
            start_date: Fecha inicial para filtrado (opcional)
            end_date: Fecha final para filtrado (opcional)

        Returns:
            Dict con resultados de la extracción
        """
        start_time = time.time()
        
        try:
            # Usar credenciales de config si no se proveen
            username = username or self.config['username']
            password = password or self.config['password']

            if not username or not password:
                raise ValueError("Credenciales no proporcionadas")

            # Inicializar componentes
            if not await self._setup_components():
                raise Exception("Error en inicialización de componentes")

            # Proceso de login
            logger.info(" Iniciando proceso de login...")
            
            # Navegar directamente a la URL configurada sin agregar '/login'
            base_url = self.config['url']
            logger.info(f" Navegando a URL base: {base_url}")
            
            try:
                # Usar 'load' en lugar de 'networkidle' para navegación más rápida
                await self.browser_manager.navigate_to_url(base_url, wait_until='load', timeout=self.config['timeout'])
                logger.info("EXITOSO Navegación exitosa a URL base")
            except PlaywrightTimeoutError as e:
                logger.warning(f"ADVERTENCIA Timeout en navegación inicial: {e}")
                logger.info("REANUDANDO Intentando con URL alternativa sin /login...")
                
                # Intentar con URL base sin /login
                base_url_alt = base_url.replace('/login', '/')
                try:
                    await self.browser_manager.navigate_to_url(base_url_alt, timeout=self.config['timeout'])
                    logger.info("EXITOSO Navegación exitosa a URL alternativa")
                except Exception as e2:
                    logger.error(f"ERROR Error también con URL alternativa: {e2}")
                    # Tomar screenshot para diagnóstico
                    try:
                        await self.page.screenshot(path=f"{self.config['screenshots_dir']}/timeout_navigation.png")
                        logger.info(" Screenshot de timeout guardado")
                    except:
                        pass
                    raise Exception(f"No se pudo acceder a la página de Afinia: {e}")
            except Exception as e:
                logger.error(f"ERROR Error de navegación: {e}")
                raise
            
            # Manejar popup específico de Afinia (optimizado)
            logger.info("VERIFICANDO Verificando popup específico de Afinia...")
            try:
                # Esperar un momento para que la página se estabilice
                await asyncio.sleep(2)
                
                # Usar el PopupHandler optimizado específico de Afinia
                popup_handled = await self.afinia_popup_handler.handle_afinia_popup()
                
                if popup_handled:
                    logger.info("EXITOSO Popup de Afinia manejado exitosamente, continuando...")
                else:
                    logger.warning("ADVERTENCIA Problema manejando popup, continuando de todos modos...")
                    
            except Exception as e:
                logger.error(f"ERROR Error en manejo de popup: {e}")
            
            # Login con selectores específicos de Afinia
            login_selectors = self.config.get('login_selectors', {})
            await self.auth_manager.login(
                username, 
                password,
                username_selectors=login_selectors.get('username'),
                password_selectors=login_selectors.get('password'),
                login_button_selectors=login_selectors.get('submit'),
                take_screenshots=False  # Solo screenshots en errores
            )

            # Navegar a sección PQR
            logger.info("REANUDANDO Navegando a sección PQR...")
            await self.browser_manager.navigate_to_url(self.config['pqr_url'], timeout=self.config['timeout'])

            # Proceso completo de filtrado específico de Afinia
            logger.info("CONFIGURANDO Iniciando proceso de filtrado específico de Afinia...")
            filter_success = await self.afinia_filter_manager.configure_filters_and_search(days_back=1)
            
            processed_data = []
            files_downloaded = 0
            pqr_processed = 0
            
            if filter_success:
                # Procesar resultados usando componente específico de Afinia
                logger.info("VERIFICANDO Procesando resultados...")
                process_success = await self.afinia_download_manager._process_search_results()
                
                if process_success:
                    processed_data.append({"status": "success", "method": "afinia_specific"})
                    files_downloaded += 1
                
                # Procesar PQR con secuencia específica si está habilitado
                if self.enable_pqr_processing and self.afinia_pqr_processor:
                    logger.info("LISTA INICIANDO PROCESAMIENTO ESPECÍFICO DE PQR...")
                    try:
                        #  ACTIVAR PAGINACIÓN AUTOMÁTICA PARA PRUEBA
                        pqr_processed = await self.afinia_pqr_processor.process_all_pqr_records(
                            max_records=self.max_pqr_records,
                            enable_pagination=True  # ¡ACTIVAR PAGINACIÓN!
                        )
                        logger.info(f"EXITOSO Procesamiento PQR completado: {pqr_processed} registros")
                        processed_data.append({
                            "status": "success", 
                            "method": "pqr_specific_sequence",
                            "records_processed": pqr_processed
                        })
                    except Exception as pqr_error:
                        logger.error(f"ERROR Error en procesamiento PQR: {pqr_error}")
                        processed_data.append({
                            "status": "error", 
                            "method": "pqr_specific_sequence",
                            "error": str(pqr_error)
                        })
            else:
                logger.warning("ADVERTENCIA Error en filtrado, intentando procesamiento directo...")
                
                # Si el filtrado falla pero el procesamiento PQR está habilitado, intentar solo PQR
                if self.enable_pqr_processing and self.afinia_pqr_processor:
                    logger.info("LISTA Intentando procesamiento PQR directo...")
                    try:
                        #  ACTIVAR PAGINACIÓN AUTOMÁTICA PARA PRUEBA (DIRECTO)
                        pqr_processed = await self.afinia_pqr_processor.process_all_pqr_records(
                            max_records=self.max_pqr_records,
                            enable_pagination=True  # ¡ACTIVAR PAGINACIÓN!
                        )
                        logger.info(f"EXITOSO Procesamiento PQR directo completado: {pqr_processed} registros")
                        processed_data.append({
                            "status": "success", 
                            "method": "pqr_direct_processing",
                            "records_processed": pqr_processed
                        })
                    except Exception as pqr_error:
                        logger.error(f"ERROR Error en procesamiento PQR directo: {pqr_error}")
                        processed_data.append({
                            "status": "error", 
                            "method": "pqr_direct_processing",
                            "error": str(pqr_error)
                        })

            # Recolectar métricas
            metrics = self.metrics.get_metrics_summary()

            logger.info("EXITOSO Extracción completada exitosamente")
            result = {
                'success': True,
                'processed_files': len(processed_data),
                'files_downloaded': files_downloaded,
                'metrics': metrics,
                'execution_time': time.time() - start_time,
                'processed_data': processed_data
            }
            
            # Agregar información específica de PQR si se procesaron
            if pqr_processed > 0:
                result['pqr_processed'] = pqr_processed
                logger.info(f"PROCESADOS Total PQR procesados: {pqr_processed}")
            
            return result

        except Exception as e:
            logger.error(f"Error en extracción: {e}")
            return {
                'success': False,
                'error': str(e)
            }

        finally:
            # Limpiar recursos
            if self.browser_manager:
                await self.browser_manager.cleanup()
                logger.info("LIMPIEZA Recursos limpiados")


# Código de prueba
if __name__ == "__main__":
    import asyncio

    async def main_demo():
        print("=== Oficina Virtual Afinia Modular Mejorado ===")
        print("Ejecutando extracción de prueba...")

        # Crear instancia del extractor
        extractor = OficinaVirtualAfiniaModular(visual_mode=True)

        # Ejecutar extracción completa
        result = await extractor.run_full_extraction()

        print(f"Resultado: {result}")

    asyncio.run(main_demo())
