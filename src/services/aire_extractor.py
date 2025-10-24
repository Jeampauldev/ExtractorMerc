"""
Aire Extractor - Extractor de Mercurio para Aire
===============================================

Extractor específico para la plataforma de Mercurio de Aire
utilizando la nueva arquitectura modular.
Integra funcionalidades legacy de Mercurio para PQR verbales y oficina virtual.
"""

import logging
import time
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from ..core.base_extractor import BaseExtractor, ExtractorStatus
from ..core.browser_manager import BrowserManager
from ..core.authentication_manager import AuthenticationManager
from ..core.data_processor import DataProcessor
from ..core.mercurio_adapter import MercurioAdapter

logger = logging.getLogger(__name__)

class AireExtractor(BaseExtractor):
    """
    Extractor específico para Mercurio de Aire.
    
    Implementa la lógica específica para extraer datos de la plataforma
    de Mercurio de Aire siguiendo el flujo de negocio establecido.
    Integra funcionalidades legacy de Mercurio para PQR verbales y oficina virtual.
    """
    
    def __init__(self, headless: bool = True, download_dir: Optional[str] = None):
        super().__init__("aire", headless)
        self.download_dir = download_dir or f"downloads/aire/mercurio"
        self.browser_manager: Optional[BrowserManager] = None
        self.auth_manager: Optional[AuthenticationManager] = None
        self.data_processor: Optional[DataProcessor] = None
        self.mercurio_adapter: Optional[MercurioAdapter] = None
        
        # URLs específicas de Aire Mercurio (según flujos.yaml)
        self.urls = {
            "base": "https://caribesol.servisoft.com.co/mercurio/index.jsp?err=0",
            "login": "https://caribesol.servisoft.com.co/mercurio/index.jsp?err=0",
            "pqr_pendientes": "https://caribesol.servisoft.com.co/mercurio/servlet/ControllerMercurio?command=consultaEspecial&tipoOperacion=parametros&idCnslta=00000015",
            "oficina_virtual": "https://oficinavirtual.aire.com.co/",
            "oficina_virtual_login": "https://oficinavirtual.aire.com.co/login.aspx",
            "consulta_especial": "https://caribesol.servisoft.com.co/mercurio/consultaEspecial.aspx",
            "reportes": "https://caribesol.servisoft.com.co/mercurio/reportes.aspx"
        }
        
        # Configuración específica de filtros (según flujos.yaml)
        self.filter_config = {
            "tipo_documento": "Pérdidas Técnicas",
            "estado": "Terminado",  # Aire usa "Terminado" en lugar de "Todos"
            "fecha_desde": None,  # Se calculará dinámicamente (30 días antes)
            "fecha_hasta": None   # Se calculará dinámicamente (hoy)
        }
        
        # Configurar fechas automáticamente según flujos.yaml
        self._setup_date_filters()
        
        # Configuración de reportes Mercurio (legacy integration)
        self.mercurio_reports = {
            "pqr_verbales_pendientes": {
                "name": "PQR Verbales Pendientes",
                "url_suffix": "PQRs/PQRVerbales.aspx",
                "id_consulta": "00000066",
                "download_selector": "#btnGenerarExcel"
            },
            "oficina_virtual_pqr": {
                "name": "Oficina Virtual PQR",
                "url_suffix": "PQRs/ListaPQRs.aspx",
                "id_consulta": "00000001",
                "download_selector": "#btnDescargar"
            }
        }
        
        # Credenciales de Mercurio (según flujos.yaml)
        self.mercurio_credentials = {
            "username": os.getenv("MERCURIO_AIRE_USERNAME", "MHERNANDEZO"),
            "password": os.getenv("MERCURIO_AIRE_PASSWORD", "1234")
        }
        
        # Credenciales de Oficina Virtual
        self.oficina_virtual_credentials = {
            "username": os.getenv("OFICINA_VIRTUAL_AIRE_USERNAME", ""),
            "password": os.getenv("OFICINA_VIRTUAL_AIRE_PASSWORD", "")
        }
    
    def setup_browser(self) -> bool:
        """Configurar el navegador para Aire"""
        try:
            logger.info("[AIRE] Configurando navegador...")
            
            self.browser_manager = BrowserManager(company="aire")
            
            success = self.browser_manager.setup()
            if success:
                # Configurar adaptador de Mercurio
                self.mercurio_adapter = MercurioAdapter(
                    page=self.browser_manager.page,
                    company="aire",
                    config={
                        "url": self.urls["base"],
                        "username": self.mercurio_credentials["username"],
                        "password": self.mercurio_credentials["password"]
                    }
                )
                logger.info("[AIRE] Navegador y adaptador Mercurio configurados exitosamente")
            else:
                logger.error("[AIRE] Error configurando navegador")
            
            return success
            
        except Exception as e:
            error_msg = f"Error en setup_browser: {str(e)}"
            logger.error(f"[AIRE] {error_msg}")
            self.log_error(error_msg)
            return False
    
    def authenticate(self) -> bool:
        """Autenticar en la plataforma de Aire Mercurio"""
        try:
            logger.info("[AIRE] Iniciando autenticación en Mercurio...")
            
            if not self.browser_manager or not self.browser_manager.page:
                raise Exception("Navegador no configurado")
            
            if not self.mercurio_adapter:
                raise Exception("Adaptador Mercurio no configurado")
            
            # Navegar a la página de login
            self.browser_manager.page.goto(self.urls["login"], timeout=30000)
            
            # Usar el adaptador de Mercurio para login
            success = self.mercurio_adapter.perform_login(
                username=self.mercurio_credentials["username"],
                password=self.mercurio_credentials["password"]
            )
            
            if success:
                logger.info("[AIRE] Autenticación Mercurio exitosa")
            else:
                logger.error("[AIRE] Fallo en autenticación Mercurio")
            
            return success
            
        except Exception as e:
            error_msg = f"Error en authenticate: {str(e)}"
            logger.error(f"[AIRE] {error_msg}")
            self.log_error(error_msg)
            return False

    def extract_data(self) -> bool:
        """Extraer datos de Mercurio Aire"""
        try:
            logger.info("[AIRE] Iniciando extracción de datos Mercurio...")
            
            if not self.browser_manager or not self.browser_manager.page:
                raise Exception("Navegador no configurado")
            
            page = self.browser_manager.page
            
            # Extraer reportes de Mercurio
            extracted_files = []
            
            # 1. Extraer PQR Verbales Pendientes
            pqr_verbales_files = self._extract_pqr_verbales(page)
            extracted_files.extend(pqr_verbales_files)
            
            # 2. Extraer datos de Oficina Virtual
            oficina_virtual_files = self._extract_oficina_virtual(page)
            extracted_files.extend(oficina_virtual_files)
            
            # 3. Procesar archivos descargados
            if extracted_files:
                self._process_extracted_files(extracted_files)
                logger.info(f"[AIRE] Extracción completada. {len(extracted_files)} archivos procesados")
                return True
            else:
                logger.warning("[AIRE] No se extrajeron archivos")
                return False
            
        except Exception as e:
            error_msg = f"Error en extract_data: {str(e)}"
            logger.error(f"[AIRE] {error_msg}")
            self.log_error(error_msg)
            return False

    def _extract_pqr_verbales(self, page: Page) -> List[str]:
        """Extraer PQR Verbales Pendientes (legacy integration)"""
        try:
            logger.info("[AIRE] === EXTRAYENDO PQR VERBALES PENDIENTES ===")
            
            report_config = self.mercurio_reports["pqr_verbales_pendientes"]
            
            # Navegar a la sección de PQR Verbales
            success = self.mercurio_adapter.navigate_to_report_section(report_config)
            if not success:
                logger.error("[AIRE] Error navegando a PQR Verbales")
                return []
            
            # Configurar fechas (últimos 30 días)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            success = self._configure_date_range_pqr_verbales(
                page,
                start_date.strftime("%d/%m/%Y"),
                end_date.strftime("%d/%m/%Y")
            )
            
            if not success:
                logger.warning("[AIRE] Error configurando fechas verbales, continuando...")
            
            # Descargar reporte
            file_path = self.mercurio_adapter.download_report(report_config)
            
            if file_path:
                logger.info(f"[AIRE] ✅ PQR Verbales descargado: {file_path}")
                return [file_path]
            else:
                logger.warning("[AIRE] ⚠️ No se pudo descargar PQR Verbales")
                return []
                
        except Exception as e:
            logger.error(f"[AIRE] Error extrayendo PQR Verbales: {e}")
            return []

    def _extract_oficina_virtual(self, page: Page) -> List[str]:
        """Extraer datos de Oficina Virtual Aire (legacy integration)"""
        try:
            logger.info("[AIRE] === EXTRAYENDO OFICINA VIRTUAL ===")
            
            # Navegar a Oficina Virtual
            page.goto(self.urls["oficina_virtual_login"], timeout=30000)
            
            # Autenticar en Oficina Virtual
            success = self._authenticate_oficina_virtual(page)
            if not success:
                logger.error("[AIRE] Error autenticando en Oficina Virtual")
                return []
            
            # Navegar a la lista de PQRs
            success = self._navigate_to_pqr_list_oficina_virtual(page)
            if not success:
                logger.error("[AIRE] Error navegando a lista PQR Oficina Virtual")
                return []
            
            # Configurar filtros para Oficina Virtual
            success = self._configure_filters_oficina_virtual(page)
            if not success:
                logger.warning("[AIRE] Error configurando filtros Oficina Virtual, continuando...")
            
            # Descargar reporte de Oficina Virtual
            file_path = self._download_oficina_virtual_report(page)
            
            if file_path:
                logger.info(f"[AIRE] ✅ Oficina Virtual descargado: {file_path}")
                return [file_path]
            else:
                logger.warning("[AIRE] ⚠️ No se pudo descargar Oficina Virtual")
                return []
                
        except Exception as e:
            logger.error(f"[AIRE] Error extrayendo Oficina Virtual: {e}")
            return []

    def _authenticate_oficina_virtual(self, page: Page) -> bool:
        """Autenticar en Oficina Virtual Aire (legacy integration)"""
        try:
            logger.info("[AIRE] Autenticando en Oficina Virtual...")
            
            # Buscar campos de login
            username_selectors = [
                "#txtUsuario",
                "input[name*='usuario']",
                "input[type='text']"
            ]
            
            password_selectors = [
                "#txtPassword",
                "input[name*='password']",
                "input[type='password']"
            ]
            
            # Llenar usuario
            for selector in username_selectors:
                if page.locator(selector).count() > 0:
                    page.fill(selector, self.oficina_virtual_credentials["username"])
                    break
            
            # Llenar contraseña
            for selector in password_selectors:
                if page.locator(selector).count() > 0:
                    page.fill(selector, self.oficina_virtual_credentials["password"])
                    break
            
            # Hacer clic en login
            login_selectors = [
                "#btnLogin",
                "input[type='submit']",
                "button[type='submit']"
            ]
            
            for selector in login_selectors:
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    break
            
            # Esperar navegación
            page.wait_for_load_state("networkidle")
            
            # Verificar login exitoso
            if "login" not in page.url.lower():
                logger.info("[AIRE] ✅ Login Oficina Virtual exitoso")
                return True
            else:
                logger.error("[AIRE] ❌ Login Oficina Virtual falló")
                return False
                
        except Exception as e:
            logger.error(f"[AIRE] Error autenticando Oficina Virtual: {e}")
            return False

    def _navigate_to_pqr_list_oficina_virtual(self, page: Page) -> bool:
        """Navegar a la lista de PQRs en Oficina Virtual (legacy integration)"""
        try:
            logger.info("[AIRE] Navegando a lista PQR Oficina Virtual...")
            
            # Buscar enlaces o menús para PQRs
            pqr_selectors = [
                "a[href*='PQR']",
                "a[href*='pqr']",
                "a[title*='PQR']",
                "#menuPQR"
            ]
            
            for selector in pqr_selectors:
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    page.wait_for_load_state("networkidle")
                    break
            
            logger.info("[AIRE] ✅ Navegación a PQR Oficina Virtual exitosa")
            return True
            
        except Exception as e:
            logger.error(f"[AIRE] Error navegando a PQR Oficina Virtual: {e}")
            return False

    def _configure_filters_oficina_virtual(self, page: Page) -> bool:
        """Configurar filtros para Oficina Virtual (legacy integration)"""
        try:
            logger.info("[AIRE] Configurando filtros Oficina Virtual...")
            
            # Configurar estado: Terminado
            estado_selectors = [
                "select[name*='estado']",
                "#ddlEstado"
            ]
            
            for selector in estado_selectors:
                if page.locator(selector).count() > 0:
                    page.select_option(selector, label="Terminado")
                    break
            
            # Configurar fechas (ayer - hoy)
            yesterday = datetime.now() - timedelta(days=1)
            today = datetime.now()
            
            fecha_desde_selectors = [
                "input[name*='fechaDesde']",
                "#txtFechaDesde"
            ]
            
            fecha_hasta_selectors = [
                "input[name*='fechaHasta']",
                "#txtFechaHasta"
            ]
            
            # Fecha desde
            for selector in fecha_desde_selectors:
                if page.locator(selector).count() > 0:
                    page.fill(selector, yesterday.strftime("%d/%m/%Y"))
                    break
            
            # Fecha hasta
            for selector in fecha_hasta_selectors:
                if page.locator(selector).count() > 0:
                    page.fill(selector, today.strftime("%d/%m/%Y"))
                    break
            
            logger.info("[AIRE] ✅ Filtros Oficina Virtual configurados")
            return True
            
        except Exception as e:
            logger.error(f"[AIRE] Error configurando filtros Oficina Virtual: {e}")
            return False

    def _download_oficina_virtual_report(self, page: Page) -> Optional[str]:
        """Descargar reporte de Oficina Virtual (legacy integration)"""
        try:
            logger.info("[AIRE] Descargando reporte Oficina Virtual...")
            
            # Buscar botón de descarga
            download_selectors = [
                "#btnDescargar",
                "input[value*='Descargar']",
                "a[href*='excel']",
                "button[title*='Excel']"
            ]
            
            for selector in download_selectors:
                if page.locator(selector).count() > 0:
                    with page.expect_download() as download_info:
                        page.click(selector)
                    
                    download = download_info.value
                    file_path = download.path()
                    
                    if file_path:
                        logger.info(f"[AIRE] ✅ Reporte Oficina Virtual descargado: {file_path}")
                        return str(file_path)
                    break
            
            logger.warning("[AIRE] ⚠️ No se encontró botón de descarga Oficina Virtual")
            return None
            
        except Exception as e:
            logger.error(f"[AIRE] Error descargando Oficina Virtual: {e}")
            return None

    def _configure_date_range_pqr_verbales(self, page: Page, start_date: str, end_date: str) -> bool:
        """Configurar rango de fechas para PQR Verbales (legacy integration)"""
        try:
            logger.info(f"[AIRE] Configurando fechas PQR Verbales: {start_date} - {end_date}")
            
            # Buscar campos de fecha específicos para PQR Verbales
            date_inputs = page.query_selector_all("input[type='text']")
            
            if len(date_inputs) >= 2:
                # Llenar fecha desde
                date_inputs[0].click()
                date_inputs[0].fill("")
                page.wait_for_timeout(200)
                date_inputs[0].type(start_date, delay=100)
                
                # Llenar fecha hasta
                date_inputs[1].click()
                date_inputs[1].fill("")
                page.wait_for_timeout(200)
                date_inputs[1].type(end_date, delay=100)
                
                logger.info("[AIRE] ✅ Fechas PQR Verbales configuradas")
                return True
            else:
                logger.warning("[AIRE] ⚠️ No se encontraron campos de fecha suficientes")
                return False
                
        except Exception as e:
            logger.error(f"[AIRE] Error configurando fechas PQR Verbales: {e}")
            return False

    def _process_extracted_files(self, file_paths: List[str]) -> None:
        """Procesar archivos extraídos usando el data processor"""
        try:
            logger.info(f"[AIRE] Procesando {len(file_paths)} archivos extraídos...")
            
            if not self.data_processor:
                self.data_processor = DataProcessor("aire")
            
            for file_path in file_paths:
                try:
                    result = self.data_processor.process_file(file_path)
                    if result:
                        logger.info(f"[AIRE] ✅ Procesado: {file_path}")
                    else:
                        logger.warning(f"[AIRE] ⚠️ Error procesando: {file_path}")
                except Exception as e:
                    logger.error(f"[AIRE] Error procesando {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"[AIRE] Error en procesamiento de archivos: {e}")

    def cleanup(self) -> None:
        """Limpiar recursos"""
        try:
            logger.info("[AIRE] Limpiando recursos...")
            
            if self.browser_manager:
                self.browser_manager.cleanup()
                
            if self.mercurio_adapter:
                # Obtener estadísticas del adaptador
                stats = self.mercurio_adapter.get_adapter_stats()
                logger.info(f"[AIRE] Estadísticas Mercurio: {stats}")
                
            logger.info("[AIRE] Limpieza completada")
            
        except Exception as e:
            logger.error(f"[AIRE] Error en cleanup: {e}")

    def get_extraction_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la extracción"""
        summary = {
            "company": "AIRE",
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": None,
            "extracted_files_count": len(self.extracted_files),
            "extracted_files": self.extracted_files,
            "errors_count": len(self.errors),
            "errors": self.errors,
            "filter_config": self.filter_config
        }
        
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            summary["duration"] = str(duration)
        
        return summary

    def _setup_date_filters(self) -> None:
        """Configurar filtros de fecha según flujos.yaml: 30 días antes hasta hoy"""
        try:
            from datetime import datetime, timedelta
            
            # Fecha hasta: hoy
            fecha_hasta = datetime.now()
            # Fecha desde: 30 días antes de hoy
            fecha_desde = fecha_hasta - timedelta(days=30)
            
            self.filter_config["fecha_hasta"] = fecha_hasta.strftime("%d/%m/%Y")
            self.filter_config["fecha_desde"] = fecha_desde.strftime("%d/%m/%Y")
            
            logger.info(f"[AIRE] Filtros de fecha configurados: {self.filter_config['fecha_desde']} - {self.filter_config['fecha_hasta']}")
            
        except Exception as e:
            logger.error(f"[AIRE] Error configurando filtros de fecha: {e}")
    
    def _apply_data_filters(self, data: List[Dict]) -> List[Dict]:
        """Aplicar filtros de datos según flujos.yaml: asunto (PETICION, QUEJA, RECLAMO, TMP) y pasos (2,3,4)"""
        try:
            if not data:
                return data
            
            # Filtros según flujos.yaml
            valid_asuntos = ["PETICION", "QUEJA", "RECLAMO", "TMP"]
            valid_pasos = ["2", "3", "4"]
            
            filtered_data = []
            for record in data:
                # Filtrar por asunto
                asunto = record.get("asunto", "").upper()
                if any(valid_asunto in asunto for valid_asunto in valid_asuntos):
                    # Filtrar por pasos
                    paso = str(record.get("paso", ""))
                    if paso in valid_pasos:
                        filtered_data.append(record)
            
            logger.info(f"[AIRE] Datos filtrados: {len(data)} -> {len(filtered_data)} registros")
            return filtered_data
            
        except Exception as e:
            logger.error(f"[AIRE] Error aplicando filtros de datos: {e}")
            return data