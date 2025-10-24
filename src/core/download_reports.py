# -*- coding: utf-8 -*-
"""
Módulo de Descarga de Reportes - Mercurio ExtractorMerc
=======================================================

🔄 MIGRADO DESDE IPO LEGACY
Fuente: legacy/backend-ipo-backup/services/mercurio/download_reports.py
Fecha migración: 2024
Propósito: Automatización de descarga de reportes desde portales Mercurio

Empresas soportadas:
- Afinia: https://serviciospqrs.afinia.com.co/mercurio/
- Air-e: https://caribesol.servisoft.com.co/mercurio/
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import pandas as pd
from playwright.async_api import TimeoutError, async_playwright, Page, BrowserContext

from config.centralized_config import config
from src.core.logging import get_logger
from .clean_and_transform import (
    rra_pendientes,
    rra_recibidas,
    verbales_pendientes,
    auditoria_pendientes
)

logger = get_logger()

# 🔄 MIGRADO DESDE IPO: Configuraciones originales
PATH_PLAYWRIGHT = os.getenv("PLAYWRIGHT_BROWSERS_PATH")
TIMEOUT_MERCURIO = 5 * 60 * 1000  # 5 minutos en milisegundos
MERCURIO_SLEEP = 3  # segundos
REPORTS_DAYS_FROM = 30  # días hacia atrás


class MercurioReportDownloader:
    """🔄 MIGRADO DESDE IPO: Descargador de reportes Mercurio"""
    
    def __init__(self, empresa: str):
        self.empresa = empresa.lower()
        self.config = self._get_empresa_config()
        
    def _get_empresa_config(self) -> Dict[str, Any]:
        """🔄 MIGRADO DESDE IPO: Configuración por empresa"""
        configs = {
            "afinia": {
                "url": "https://serviciospqrs.afinia.com.co/mercurio/",
                "user": "281005131",
                "password": "123",
                "reports": {
                    "verbales_pendientes": {"id_consulta": "00000066"}
                }
            },
            "air-e": {
                "url": "https://caribesol.servisoft.com.co/mercurio/",
                "user": "81001380", 
                "password": "1234",
                "reports": {
                    "rra_pendientes": {"id_consulta": "00000014"},
                    "rra_recibidas": {"id_consulta": "00000013"},
                    "auditoria_pendientes": {"id_consulta": "00000015"}
                }
            }
        }
        return configs.get(self.empresa, {})
    
    async def handle_login(self, page: Page, parameters: Dict[str, str]) -> None:
        """🔄 MIGRADO DESDE IPO: Manejo de login en Mercurio"""
        await page.fill("input#usuario", parameters["user"])
        await page.fill("input#contrasena", parameters["password"])
        await page.click("input#ingresar")
        logger.info(f"Login realizado para {self.empresa}")
    
    async def get_report(self, report_type: str, date_from: str, date_to: str) -> Optional[str]:
        """🔄 MIGRADO DESDE IPO: Descarga un reporte específico"""
        if report_type not in self.config.get("reports", {}):
            logger.error(f"Tipo de reporte {report_type} no disponible para {self.empresa}")
            return None
            
        parameters = {
            "url": self.config["url"],
            "user": self.config["user"],
            "password": self.config["password"],
            "id_consulta": self.config["reports"][report_type]["id_consulta"],
            "date_from": date_from,
            "date_to": date_to,
            "consulta": report_type
        }
        
        async with async_playwright() as p:
            text_popup = "Ya existe una sesión abierta en Mercurio con este usuario, si ingresa, cerrara la sesión activa, desea ingresar?."
            
            browser = await p.chromium.launch(
                executable_path=PATH_PLAYWRIGHT,
                headless=True,
                args=["--ignore-certificate-errors"]
            )
            logger.info("Navegador configurado")
            
            context = await browser.new_context(
                accept_downloads=True,
                locale="es-CO",
                geolocation={"latitude": 4.7110, "longitude": -74.0721},
                permissions=["geolocation"]
            )
            
            context.set_default_timeout(TIMEOUT_MERCURIO)
            context.set_default_navigation_timeout(TIMEOUT_MERCURIO)
            
            page = await context.new_page()
            page.set_default_timeout(TIMEOUT_MERCURIO)
            page.set_default_navigation_timeout(TIMEOUT_MERCURIO)
            
            page.on(
                "dialog",
                lambda dialog: dialog.accept() if text_popup in dialog.message else None
            )
            
            try:
                await page.goto(parameters["url"], timeout=TIMEOUT_MERCURIO)
                logger.info("Entrando a la página de Mercurio")
                
                await self.handle_login(page, parameters)
                
                # Intentos de login
                max_attempts = 3
                n_attempt = 1
                
                while n_attempt <= max_attempts:
                    try:
                        await page.wait_for_selector("#Bar4", timeout=TIMEOUT_MERCURIO)
                        break
                    except Exception:
                        await self.handle_login(page, parameters)
                        await page.wait_for_selector("#Bar4", timeout=TIMEOUT_MERCURIO)
                        n_attempt += 1
                
                logger.info("Login exitoso")
                
                # Navegar a reportes
                doc_btn = page.locator("#Bar4")
                await doc_btn.hover(timeout=TIMEOUT_MERCURIO)
                
                download_path = await self.handle_popup(page, parameters)
                return download_path
                
            except Exception as e:
                logger.error(f"Error descargando reporte {report_type}: {e}")
                return None
            finally:
                await browser.close()
    
    async def handle_popup(self, page: Page, parameters: Dict[str, str]) -> Optional[str]:
        """🔄 MIGRADO DESDE IPO: Manejo del popup de reportes"""
        async with page.expect_popup() as popup_info:
            await page.wait_for_selector("#menuItem4_7")
            await page.click("a#menuItem4_7")
            popup = await popup_info.value
            await popup.set_viewport_size({"width": 720, "height": 1280})
            await popup.wait_for_load_state()
            await popup.get_by_text(parameters["id_consulta"]).click()
            logger.info(f"id_consulta seleccionado: {parameters['id_consulta']}")
            
            return await self.download_file(popup, parameters)
    
    async def download_file(self, page: Page, parameters: Dict[str, str]) -> Optional[str]:
        """🔄 MIGRADO DESDE IPO: Descarga el archivo del reporte"""
        try:
            date1 = page.locator('[name="param0"]')
            date2 = page.locator('[name="param1"]')
            await date1.fill(parameters["date_from"])
            await date2.fill(parameters["date_to"])
            
            logger.info(f"Fechas definidas: {parameters['date_from']} - {parameters['date_to']}")
            
            save_excel = page.locator("#cmd_ejecuta_excel")
            
            async with page.expect_download() as download_info:
                await page.wait_for_selector("input#cmd_ejecuta_excel")
                await save_excel.click()
                
            download = await download_info.value
            download_path = f"tmp/downloads/{download.suggested_filename}"
            await download.save_as(download_path)
            
            logger.info(f"Descarga exitosa: {parameters['consulta']} -> {download_path}")
            return download_path
            
        except Exception as e:
            logger.error(f"Error en descarga de archivo: {e}")
            return None


async def run_pipeline(empresa: str) -> Dict[str, Any]:
    """🔄 MIGRADO DESDE IPO: Pipeline principal de descarga de reportes"""
    logger.info(f"Iniciando pipeline de descarga para {empresa}")
    
    downloader = MercurioReportDownloader(empresa)
    
    # Calcular fechas
    date_to = datetime.now()
    date_from = date_to - timedelta(days=REPORTS_DAYS_FROM)
    
    date_from_str = date_from.strftime("%d/%m/%Y")
    date_to_str = date_to.strftime("%d/%m/%Y")
    
    results = {}
    
    if empresa.lower() == "afinia":
        reports = ["verbales_pendientes"]
    elif empresa.lower() == "air-e":
        reports = ["rra_pendientes", "rra_recibidas", "auditoria_pendientes"]
    else:
        logger.error(f"Empresa {empresa} no soportada")
        return {"error": f"Empresa {empresa} no soportada"}
    
    for report_type in reports:
        try:
            download_path = await downloader.get_report(report_type, date_from_str, date_to_str)
            if download_path:
                # Procesar y guardar en BD
                await save_report_to_db(download_path, {
                    "empresa": empresa,
                    "report_type": report_type,
                    "date_from": date_from_str,
                    "date_to": date_to_str
                })
                results[report_type] = "success"
            else:
                results[report_type] = "failed"
                
        except Exception as e:
            logger.error(f"Error procesando {report_type}: {e}")
            results[report_type] = f"error: {str(e)}"
    
    return results


async def save_report_to_db(download_path: str, parameters: Dict[str, str]) -> None:
    """🔄 MIGRADO DESDE IPO: Guarda reporte en base de datos"""
    try:
        if not os.path.exists(download_path):
            logger.error(f"Archivo no encontrado: {download_path}")
            return
            
        # Leer archivo Excel
        data = pd.read_excel(download_path)
        logger.info(f"Datos leídos: {len(data)} registros")
        
        # Procesar según tipo de reporte
        report_type = parameters["report_type"]
        empresa = parameters["empresa"]
        
        if report_type == "rra_pendientes":
            rra_pendientes(data)
        elif report_type == "rra_recibidas":
            rra_recibidas(data)
        elif report_type == "verbales_pendientes":
            verbales_pendientes(data)
        elif report_type == "auditoria_pendientes":
            auditoria_pendientes(data)
        else:
            logger.warning(f"Tipo de reporte no reconocido: {report_type}")
            
        logger.info(f"Reporte {report_type} procesado y guardado en BD")
        
    except Exception as e:
        logger.error(f"Error guardando reporte en BD: {e}")


async def run_main(empresa: str) -> Dict[str, Any]:
    """🔄 MIGRADO DESDE IPO: Función principal de ejecución"""
    try:
        if empresa.lower() == "all":
            results = {}
            for emp in ["afinia", "air-e"]:
                results[emp] = await run_pipeline(emp)
            return results
        else:
            return await run_pipeline(empresa)
            
    except Exception as e:
        logger.error(f"Error en run_main: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    asyncio.run(run_main("all"))