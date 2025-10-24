"""
Afinia Extractor - Extractor de Mercurio para Afinia
===================================================

Extractor específico para la plataforma de Mercurio de Afinia
utilizando la nueva arquitectura modular.
Integra funcionalidades legacy de Mercurio para PQR escritas y verbales.
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

class AfiniaExtractor(BaseExtractor):
    """
    Extractor específico para Mercurio de Afinia.
    
    Implementa la lógica específica para extraer datos de la plataforma
    de Mercurio de Afinia siguiendo el flujo de negocio establecido.
    Integra funcionalidades legacy de Mercurio para PQR escritas y verbales.
    """
    
    def __init__(self, download_dir: Optional[str] = None):
        # Detectar plataforma automáticamente
        from ..utils.platform_detector import detect_platform
        platform_config = detect_platform()
        
        super().__init__("afinia", platform_config.headless_required)
        self.download_dir = download_dir or f"downloads/afinia/mercurio"
        self.browser_manager: Optional[BrowserManager] = None
        self.auth_manager: Optional[AuthenticationManager] = None
        self.data_processor: Optional[DataProcessor] = None
        self.mercurio_adapter: Optional[MercurioAdapter] = None
        
        # Log de configuración detectada
        logger.info(f"Plataforma detectada: {platform_config.platform_type}")
        logger.info(f"Modo headless: {platform_config.headless_required}")
        
        # URLs específicas de Afinia Mercurio (según flujos.yaml)
        self.urls = {
            "base": "https://serviciospqrs.afinia.com.co/mercurio/index.jsp?err=",
            "login": "https://serviciospqrs.afinia.com.co/mercurio/index.jsp?err=",
            "pqr_pendientes": "https://serviciospqrs.afinia.com.co/mercurio/servlet/ControllerMercurio?command=consultaEspecial&tipoOperacion=parametros&idCnslta=00000015",
            "pqr_verbales_pendientes": "https://serviciospqrs.afinia.com.co/mercurio/servlet/ControllerMercurio?command=consultaEspecial&tipoOperacion=parametros&idCnslta=00000066",
            "consulta_especial": "https://serviciospqrs.afinia.com.co/mercurio/consultaEspecial.aspx",
            "reportes": "https://serviciospqrs.afinia.com.co/mercurio/reportes.aspx"
        }
        
        # Configuración específica de filtros (según flujos.yaml)
        self.filter_config = {
            "tipo_documento": "Pérdidas Técnicas",
            "estado": "Todos",
            "fecha_desde": None,  # Se calculará dinámicamente (30 días antes)
            "fecha_hasta": None   # Se calculará dinámicamente (hoy)
        }
        
        # Configurar fechas automáticamente según flujos.yaml
        self._setup_date_filters()
        
        # Configuración de reportes Mercurio (legacy integration)
        self.mercurio_reports = {
            "pqr_escritas_pendientes": {
                "name": "PQR Escritas Pendientes",
                "url_suffix": "PQRs/PQREscritas.aspx",
                "id_consulta": "00000015",
                "download_selector": "#btnGenerarExcel"
            },
            "verbales_pendientes": {
                "name": "PQR Verbales Pendientes", 
                "url_suffix": "PQRs/PQRVerbales.aspx",
                "id_consulta": "00000066",
                "download_selector": "#btnGenerarExcel"
            }
        }
        
        # Credenciales de Mercurio (según flujos.yaml)
        self.mercurio_credentials = {
            "username": os.getenv("MERCURIO_AFINIA_USERNAME", "281005131"),
            "password": os.getenv("MERCURIO_AFINIA_PASSWORD", "123")
        }
    
    def setup_browser(self) -> bool:
        """Configurar el navegador para Afinia"""
        try:
            logger.info("[AFINIA] Configurando navegador...")
            
            # Crear browser manager (ya no necesita parámetros, detecta automáticamente)
            self.browser_manager = BrowserManager(company="afinia")
            
            success = self.browser_manager.setup()
            if success:
                # Configurar adaptador de Mercurio
                self.mercurio_adapter = MercurioAdapter(
                    page=self.browser_manager.page,
                    company="afinia",
                    config={
                        "url": self.urls["base"],
                        "username": self.mercurio_credentials["username"],
                        "password": self.mercurio_credentials["password"]
                    }
                )
                logger.info("[AFINIA] Navegador y adaptador Mercurio configurados exitosamente")
            else:
                logger.error("[AFINIA] Error configurando navegador")
            
            return success
            
        except Exception as e:
            error_msg = f"Error en setup_browser: {str(e)}"
            logger.error(f"[AFINIA] {error_msg}")
            self.log_error(error_msg)
            return False
    
    def authenticate(self) -> bool:
        """Autenticar en la plataforma de Afinia Mercurio"""
        try:
            logger.info("[AFINIA] Iniciando autenticación en Mercurio...")
            
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
                logger.info("[AFINIA] Autenticación Mercurio exitosa")
            else:
                logger.error("[AFINIA] Fallo en autenticación Mercurio")
            
            return success
            
        except Exception as e:
            error_msg = f"Error en authenticate: {str(e)}"
            logger.error(f"[AFINIA] {error_msg}")
            self.log_error(error_msg)
            return False

    def extract_data(self) -> bool:
        """Extraer datos de Mercurio Afinia"""
        try:
            logger.info("[AFINIA] Iniciando extracción de datos Mercurio...")
            
            if not self.browser_manager or not self.browser_manager.page:
                raise Exception("Navegador no configurado")
            
            page = self.browser_manager.page
            
            # Extraer reportes de Mercurio
            extracted_files = []
            
            # 1. Extraer PQR Escritas Pendientes
            pqr_escritas_files = self._extract_pqr_escritas(page)
            extracted_files.extend(pqr_escritas_files)
            
            # 2. Extraer PQR Verbales Pendientes
            pqr_verbales_files = self._extract_pqr_verbales(page)
            extracted_files.extend(pqr_verbales_files)
            
            # 3. Procesar archivos descargados
            if extracted_files:
                self._process_extracted_files(extracted_files)
                logger.info(f"[AFINIA] Extracción completada. {len(extracted_files)} archivos procesados")
                return True
            else:
                logger.warning("[AFINIA] No se extrajeron archivos")
                return False
            
        except Exception as e:
            error_msg = f"Error en extract_data: {str(e)}"
            logger.error(f"[AFINIA] {error_msg}")
            self.log_error(error_msg)
            return False

    def _extract_pqr_escritas(self, page: Page) -> List[str]:
        """Extraer PQR Escritas Pendientes (legacy integration)"""
        try:
            logger.info("[AFINIA] === EXTRAYENDO PQR ESCRITAS PENDIENTES ===")
            
            report_config = self.mercurio_reports["pqr_escritas_pendientes"]
            
            # Navegar a la sección de PQR Escritas
            success = self.mercurio_adapter.navigate_to_report_section(report_config)
            if not success:
                logger.error("[AFINIA] Error navegando a PQR Escritas")
                return []
            
            # Configurar fechas (últimos 30 días)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            success = self._configure_date_range_pqr_escritas(
                page, 
                start_date.strftime("%d/%m/%Y"),
                end_date.strftime("%d/%m/%Y")
            )
            
            if not success:
                logger.warning("[AFINIA] Error configurando fechas, continuando...")
            
            # Descargar reporte con nombre personalizado
            file_path = self.mercurio_adapter.download_report(report_config, custom_filename="afinia_pqr_pend")
            
            if file_path:
                logger.info(f"[AFINIA] ✅ PQR Escritas descargado: {file_path}")
                return [file_path]
            else:
                logger.warning("[AFINIA] ⚠️ No se pudo descargar PQR Escritas")
                return []
                
        except Exception as e:
            logger.error(f"[AFINIA] Error extrayendo PQR Escritas: {e}")
            return []

    def _extract_pqr_verbales(self, page: Page) -> List[str]:
        """Extraer PQR Verbales Pendientes (legacy integration)"""
        try:
            logger.info("[AFINIA] === EXTRAYENDO PQR VERBALES PENDIENTES ===")
            
            report_config = self.mercurio_reports["verbales_pendientes"]
            
            # Navegar a la sección de PQR Verbales
            success = self.mercurio_adapter.navigate_to_report_section(report_config)
            if not success:
                logger.error("[AFINIA] Error navegando a PQR Verbales")
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
                logger.warning("[AFINIA] Error configurando fechas verbales, continuando...")
            
            # Descargar reporte con nombre personalizado
            file_path = self.mercurio_adapter.download_report(report_config, custom_filename="afinia_pqr_verb_pend")
            
            if file_path:
                logger.info(f"[AFINIA] ✅ PQR Verbales descargado: {file_path}")
                return [file_path]
            else:
                logger.warning("[AFINIA] ⚠️ No se pudo descargar PQR Verbales")
                return []
                
        except Exception as e:
            logger.error(f"[AFINIA] Error extrayendo PQR Verbales: {e}")
            return []

    def _configure_date_range_pqr_escritas(self, page: Page, start_date: str, end_date: str) -> bool:
        """Configurar rango de fechas para PQR Escritas usando selectores específicos del HTML"""
        try:
            logger.info(f"[AFINIA] Configurando fechas PQR Escritas: {start_date} - {end_date}")
            
            # Selectores específicos basados en el HTML real
            fecha_desde_selector = 'input[name="param0"]'
            fecha_hasta_selector = 'input[name="param1"]'
            
            # Buscar y configurar fecha desde
            fecha_desde_field = page.query_selector(fecha_desde_selector)
            if fecha_desde_field:
                logger.info(f"[AFINIA] Campo fecha desde encontrado: {fecha_desde_selector}")
                fecha_desde_field.click()
                fecha_desde_field.fill("")
                page.wait_for_timeout(200)
                fecha_desde_field.type(start_date, delay=100)
                logger.info(f"[AFINIA] ✅ Fecha desde configurada: {start_date}")
            else:
                logger.warning(f"[AFINIA] ⚠️ Campo fecha desde no encontrado: {fecha_desde_selector}")
                return False
            
            # Buscar y configurar fecha hasta
            fecha_hasta_field = page.query_selector(fecha_hasta_selector)
            if fecha_hasta_field:
                logger.info(f"[AFINIA] Campo fecha hasta encontrado: {fecha_hasta_selector}")
                fecha_hasta_field.click()
                fecha_hasta_field.fill("")
                page.wait_for_timeout(200)
                fecha_hasta_field.type(end_date, delay=100)
                logger.info(f"[AFINIA] ✅ Fecha hasta configurada: {end_date}")
            else:
                logger.warning(f"[AFINIA] ⚠️ Campo fecha hasta no encontrado: {fecha_hasta_selector}")
                return False
                
            logger.info("[AFINIA] ✅ Ambas fechas PQR Escritas configuradas exitosamente")
            return True
                
        except Exception as e:
            logger.error(f"[AFINIA] Error configurando fechas PQR Escritas: {e}")
            return False

    def _configure_date_range_pqr_verbales(self, page: Page, start_date: str, end_date: str) -> bool:
        """Configurar rango de fechas para PQR Verbales usando selectores específicos del HTML"""
        try:
            logger.info(f"[AFINIA] Configurando fechas PQR Verbales: {start_date} - {end_date}")
            
            # Selectores específicos basados en el HTML real
            fecha_desde_selector = 'input[name="param0"]'
            fecha_hasta_selector = 'input[name="param1"]'
            
            # Buscar y configurar fecha desde
            fecha_desde_field = page.query_selector(fecha_desde_selector)
            if fecha_desde_field:
                logger.info(f"[AFINIA] Campo fecha desde encontrado: {fecha_desde_selector}")
                fecha_desde_field.click()
                fecha_desde_field.fill("")
                page.wait_for_timeout(200)
                fecha_desde_field.type(start_date, delay=100)
                logger.info(f"[AFINIA] ✅ Fecha desde configurada: {start_date}")
            else:
                logger.warning(f"[AFINIA] ⚠️ Campo fecha desde no encontrado: {fecha_desde_selector}")
                return False
            
            # Buscar y configurar fecha hasta
            fecha_hasta_field = page.query_selector(fecha_hasta_selector)
            if fecha_hasta_field:
                logger.info(f"[AFINIA] Campo fecha hasta encontrado: {fecha_hasta_selector}")
                fecha_hasta_field.click()
                fecha_hasta_field.fill("")
                page.wait_for_timeout(200)
                fecha_hasta_field.type(end_date, delay=100)
                logger.info(f"[AFINIA] ✅ Fecha hasta configurada: {end_date}")
            else:
                logger.warning(f"[AFINIA] ⚠️ Campo fecha hasta no encontrado: {fecha_hasta_selector}")
                return False
                
            logger.info("[AFINIA] ✅ Ambas fechas PQR Verbales configuradas exitosamente")
            return True
                
        except Exception as e:
            logger.error(f"[AFINIA] Error configurando fechas PQR Verbales: {e}")
            return False

    def _process_extracted_files(self, file_paths: List[str]) -> None:
        """Procesar archivos extraídos usando el data processor"""
        try:
            logger.info(f"[AFINIA] Procesando {len(file_paths)} archivos extraídos...")
            
            if not self.data_processor:
                self.data_processor = DataProcessor("afinia")
            
            for file_path in file_paths:
                try:
                    result = self.data_processor.process_file(file_path)
                    if result:
                        logger.info(f"[AFINIA] ✅ Procesado: {file_path}")
                    else:
                        logger.warning(f"[AFINIA] ⚠️ Error procesando: {file_path}")
                except Exception as e:
                    logger.error(f"[AFINIA] Error procesando {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"[AFINIA] Error en procesamiento de archivos: {e}")

    def cleanup(self) -> None:
        """Limpiar recursos"""
        try:
            logger.info("[AFINIA] Limpiando recursos...")
            
            if self.browser_manager:
                self.browser_manager.cleanup()
                
            if self.mercurio_adapter:
                # Obtener estadísticas del adaptador
                stats = self.mercurio_adapter.get_adapter_stats()
                logger.info(f"[AFINIA] Estadísticas Mercurio: {stats}")
                
            logger.info("[AFINIA] Limpieza completada")
            
        except Exception as e:
            logger.error(f"[AFINIA] Error en cleanup: {e}")

    def get_extraction_summary(self) -> Dict[str, Any]:
        """Obtener resumen de la extracción"""
        summary = {
            "company": "AFINIA",
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
            
            logger.info(f"[AFINIA] Filtros de fecha configurados: {self.filter_config['fecha_desde']} - {self.filter_config['fecha_hasta']}")
            
        except Exception as e:
            logger.error(f"[AFINIA] Error configurando filtros de fecha: {e}")
    
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
            
            logger.info(f"[AFINIA] Datos filtrados: {len(data)} -> {len(filtered_data)} registros")
            return filtered_data
            
        except Exception as e:
            logger.error(f"[AFINIA] Error aplicando filtros de datos: {e}")
            return data