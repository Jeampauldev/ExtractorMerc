#!/usr/bin/env python3
"""
Mercurio Aire Extractor - Generado Automáticamente
==========================================

Extractor modular para Mercurio de AIRE.
Utiliza adaptador específico de Mercurio y componentes modulares.

Generado: 2025-09-26
Tipo: full
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Configurar paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Imports de componentes modulares
from a1_core.browser_manager import BrowserManager
from b2_adapters.mercurio_adapter import MercurioAdapter
from g7_utils.performance_monitor import PerformanceMonitor, TimingContext
from f6_config.config import get_extractor_config

# Import del procesador de datos
from e5_processors.mercurio_aire.data_processor import AireMercurioDataProcessor

# Configurar logging específico para AIRE-MERCURIO
logger = logging.getLogger('aire_mercurio')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[AIRE-MERCURIO] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Evitar que interfiera con otros loggers

class MercurioAireModular:
    """
    Extractor modular para Mercurio de AIRE
    
    Generado automáticamente el 2025-09-26.
    """
    
    def __init__(self, headless: bool = False):
        """Inicializa el extractor"""
        self.headless = headless
        self.config = get_extractor_config("aire", "mercurio")
        
        if not self.config:
            self.config = self._get_default_config()
        
        # Componentes
        self.browser_manager = None
        self.mercurio_adapter = None
        self.data_processor = AireMercurioDataProcessor()
        self.page = None
        
        logger.info("✅ MercurioAireModular inicializado")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto"""
        return {
            "url": "https://mercurio.aire.com.co/Mercurio/",
            "username": os.getenv("MERCURIO_AIRE_USERNAME", ""),
            "password": os.getenv("MERCURIO_AIRE_PASSWORD", ""),
            "company_name": "AIRE",
            "platform": "mercurio",
            "timeouts": {
                "navigation": 30000,
                "login": 45000,
                "download": 60000
            }
        }
    
    def setup_browser(self) -> bool:
        """Configura navegador y adaptador"""
        try:
            logger.info("🔧 Configurando navegador...")
            
            self.browser_manager = BrowserManager(
                headless=self.headless,
                screenshots_dir="downloads/aire/mercurio/screenshots"
            )
            
            browser, page = self.browser_manager.setup_browser()
            self.page = page
            
            # Configurar adaptador de Mercurio
            self.mercurio_adapter = MercurioAdapter(
                page=self.page,
                company="aire",
                config=self.config
            )
            
            logger.info("✅ Navegador configurado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configurando navegador: {e}")
            return False
    
    def navigate_to_site(self) -> bool:
        """Navega al sitio de Mercurio"""
        try:
            url = self.config["url"]
            logger.info(f"🧭 Navegando a: {url}")
            
            self.page.goto(url, timeout=self.config["timeouts"]["navigation"])
            self.page.wait_for_load_state("networkidle")
            
            logger.info("✅ Navegación exitosa")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error navegando: {e}")
            return False
    
    def perform_login(self) -> bool:
        """Realiza login"""
        try:
            # Usar adaptador para login
            username = self.config["username"]
            password = self.config["password"]
            
            logger.info(f"🔑 Iniciando login: {username}")
            
            return self.mercurio_adapter.perform_login(username, password)
            
        except Exception as e:
            logger.error(f"❌ Error en login: {e}")
            return False
    
    def download_reports(self, report_types: List[str] = None) -> List[str]:
        """Descarga reportes"""
        if not report_types:
            report_types = ["pqr_escritas", "pqr_verbales"]
        
        downloaded_files = []
        
        for report_type in report_types:
            try:
                logger.info(f"📊 Descargando: {report_type}")
                
                # Usar adaptador para descarga
                file_path = self.mercurio_adapter.download_report({
                    "name": report_type,
                    "url_suffix": report_type.replace("_", "").title()
                })
                
                if file_path:
                    downloaded_files.append(file_path)
                    logger.info(f"✅ Descargado: {file_path}")
                
            except Exception as e:
                logger.error(f"❌ Error descargando {report_type}: {e}")
        
        return downloaded_files
    
    def process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Procesa archivos descargados"""
        results = {
            'processed_files': 0,
            'total_records': 0,
            'errors': []
        }
        
        for file_path in file_paths:
            try:
                result = self.data_processor.process_json_file(file_path)
                if result['success']:
                    results['processed_files'] += 1
                    results['total_records'] += result.get('processed_count', 0)
                else:
                    results['errors'].append(f"Error procesando {file_path}")
                    
            except Exception as e:
                results['errors'].append(f"Error procesando {file_path}: {str(e)}")
        
        return results
    
    def run_extraction(self, 
                      report_types: List[str] = None,
                      days_back: int = 30) -> Dict[str, Any]:
        """Ejecuta extracción completa"""
        
        logger.info("🚀 Iniciando extracción de AIRE Mercurio")
        
        results = {
            'success': False,
            'files': [],
            'errors': [],
            'metrics': {}
        }
        
        try:
            # 1. Configurar navegador
            if not self.setup_browser():
                results['errors'].append("Error configurando navegador")
                return results
            
            # 2. Navegar al sitio
            if not self.navigate_to_site():
                results['errors'].append("Error navegando al sitio")
                return results
            
            # 3. Realizar login
            if not self.perform_login():
                results['errors'].append("Error en login")
                return results
            
            # 4. Descargar reportes
            downloaded_files = self.download_reports(report_types)
            results['files'] = downloaded_files
            
            # 5. Procesar archivos
            if downloaded_files:
                processing_results = self.process_files(downloaded_files)
                results['processing'] = processing_results
                results['success'] = processing_results['processed_files'] > 0
            else:
                results['success'] = False
            
            logger.info(f"✅ Extracción completada: {len(downloaded_files)} archivos")
            
        except Exception as e:
            error_msg = f"Error en extracción: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(f"💥 {error_msg}")
        
        finally:
            self._cleanup()
        
        return results
    
    def _cleanup(self):
        """Limpia recursos"""
        try:
            if self.browser_manager:
                self.browser_manager.cleanup()
            logger.info("✅ Cleanup completado")
        except Exception as e:
            logger.warning(f"⚠️ Error en cleanup: {e}")


def main():
    """Función principal"""
    logger.info("🎬 DEMO: MercurioAireModular")
    
    extractor = MercurioAireModular(headless=True)
    results = extractor.run_extraction()
    
    logger.info("📊 RESULTADOS:")
    logger.info(f"   Éxito: {results['success']}")
    logger.info(f"   Archivos: {len(results.get('files', []))}")
    
    return results['success']


def extract_aire_mercurio(headless: bool = False, 
                         report_types: List[str] = None,
                         days_back: int = 30) -> Dict[str, Any]:
    """
    Función principal de extracción para Mercurio Aire
    
    Args:
        headless: Ejecutar en modo headless
        report_types: Tipos de reportes a descargar
        days_back: Días hacia atrás para la extracción
        
    Returns:
        Dict con resultados de la extracción
    """
    extractor = MercurioAireModular(headless=headless)
    return extractor.run_extraction(report_types=report_types, days_back=days_back)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

