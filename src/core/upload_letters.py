# -*- coding: utf-8 -*-
"""
Módulo de Carga de Cartas - Mercurio ExtractorMerc
=======================================

🔄 MIGRADO DESDE IPO LEGACY
Fuente: legacy/backend-ipo-backup/services/mercurio/upload_letters.py
Fecha migración: 2024
Propósito: Automatización de carga de cartas de respuesta en Mercurio

Funcionalidades:
- Carga automática de cartas principales
- Carga de cartas de notificación
- Manejo de reintentos en caso de fallos
- Integración con base de datos para seguimiento
"""

import asyncio
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import pytz
from playwright.async_api import async_playwright, Browser, Page
from sqlalchemy import create_engine, text

from config.centralized_config import config
from src.core.logging import get_logger

logger = get_logger()
config = AppConfig()

# 🔄 MIGRADO DESDE IPO: Configuración de zona horaria
zona_horaria = pytz.timezone("America/Bogota")

# 🔄 MIGRADO DESDE IPO: Configuraciones de Mercurio
MERCURIO_CONFIG = {
    "base_url": "https://mercurio.creg.gov.co/",
    "login_url": "https://mercurio.creg.gov.co/Account/Login",
    "timeout": 30000,
    "retry_attempts": 3,
    "retry_delay": 5000
}

# 🔄 MIGRADO DESDE IPO: Selectores CSS
SELECTORS = {
    "login": {
        "username": "#UserName",
        "password": "#Password",
        "submit": "input[type='submit']"
    },
    "navigation": {
        "pqr_menu": "a[href*='PQR']",
        "search_button": "#btnBuscar",
        "radicado_input": "#NumeroRadicado",
        "actions_button": "button:has-text('Acciones')",
        "upload_response": "a:has-text('Cargar Respuesta')"
    },
    "upload": {
        "file_input": "input[type='file']",
        "document_type": "#TipoDocumento",
        "save_button": "button:has-text('Guardar')",
        "notification_checkbox": "#EsNotificacion"
    },
    "alerts": {
        "success": ".alert-success",
        "error": ".alert-danger",
        "warning": ".alert-warning"
    }
}


class MercurioLetterUploader:
    """🔄 MIGRADO DESDE IPO: Clase para automatizar carga de cartas en Mercurio"""
    
    def __init__(self, company: str):
        self.company = company.lower()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.credentials = self._get_credentials()
        
    def _get_credentials(self) -> Dict[str, str]:
        """Obtiene credenciales según la empresa"""
        if self.company == "aire":
            return {
                "username": config.mercurio.aire_username,
                "password": config.mercurio.aire_password
            }
        elif self.company == "afinia":
            return {
                "username": config.mercurio.afinia_username,
                "password": config.mercurio.afinia_password
            }
        else:
            raise ValueError(f"Empresa no soportada: {self.company}")
    
    async def initialize_browser(self) -> None:
        """Inicializa el navegador"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=config.app.headless_mode,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        
    async def close_browser(self) -> None:
        """Cierra el navegador"""
        if self.browser:
            await self.browser.close()
    
    async def login(self) -> bool:
        """🔄 MIGRADO DESDE IPO: Realiza login en Mercurio"""
        try:
            logger.info(f"Iniciando login para {self.company}")
            
            await self.page.goto(MERCURIO_CONFIG["login_url"])
            await self.page.wait_for_load_state("networkidle")
            
            # Llenar credenciales
            await self.page.fill(SELECTORS["login"]["username"], self.credentials["username"])
            await self.page.fill(SELECTORS["login"]["password"], self.credentials["password"])
            
            # Hacer clic en submit
            await self.page.click(SELECTORS["login"]["submit"])
            await self.page.wait_for_load_state("networkidle")
            
            # Verificar login exitoso
            current_url = self.page.url
            if "login" not in current_url.lower():
                logger.info("Login exitoso")
                return True
            else:
                logger.error("Login fallido")
                return False
                
        except Exception as e:
            logger.error(f"Error en login: {e}")
            return False
    
    async def navigate_to_pqr(self) -> bool:
        """Navega al módulo de PQR"""
        try:
            await self.page.click(SELECTORS["navigation"]["pqr_menu"])
            await self.page.wait_for_load_state("networkidle")
            return True
        except Exception as e:
            logger.error(f"Error navegando a PQR: {e}")
            return False
    
    async def search_radicado(self, radicado: str) -> bool:
        """🔄 MIGRADO DESDE IPO: Busca un radicado específico"""
        try:
            logger.info(f"Buscando radicado: {radicado}")
            
            # Limpiar campo y escribir radicado
            await self.page.fill(SELECTORS["navigation"]["radicado_input"], "")
            await self.page.fill(SELECTORS["navigation"]["radicado_input"], radicado)
            
            # Hacer clic en buscar
            await self.page.click(SELECTORS["navigation"]["search_button"])
            await self.page.wait_for_load_state("networkidle")
            
            # Verificar si se encontró el radicado
            await self.page.wait_for_timeout(2000)
            
            # Buscar el radicado en los resultados
            radicado_found = await self.page.locator(f"text={radicado}").count() > 0
            
            if radicado_found:
                logger.info(f"Radicado {radicado} encontrado")
                return True
            else:
                logger.warning(f"Radicado {radicado} no encontrado")
                return False
                
        except Exception as e:
            logger.error(f"Error buscando radicado {radicado}: {e}")
            return False
    
    async def upload_letter(self, radicado: str, file_path: str, is_notification: bool = False) -> bool:
        """🔄 MIGRADO DESDE IPO: Carga una carta de respuesta"""
        try:
            logger.info(f"Cargando carta para radicado {radicado}: {file_path}")
            
            # Buscar el radicado
            if not await self.search_radicado(radicado):
                return False
            
            # Hacer clic en acciones
            await self.page.click(SELECTORS["navigation"]["actions_button"])
            await self.page.wait_for_timeout(1000)
            
            # Hacer clic en cargar respuesta
            await self.page.click(SELECTORS["navigation"]["upload_response"])
            await self.page.wait_for_load_state("networkidle")
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                logger.error(f"Archivo no encontrado: {file_path}")
                return False
            
            # Cargar archivo
            await self.page.set_input_files(SELECTORS["upload"]["file_input"], file_path)
            
            # Seleccionar tipo de documento
            if is_notification:
                await self.page.check(SELECTORS["upload"]["notification_checkbox"])
                await self.page.select_option(SELECTORS["upload"]["document_type"], "Notificación")
            else:
                await self.page.select_option(SELECTORS["upload"]["document_type"], "Respuesta")
            
            # Guardar
            await self.page.click(SELECTORS["upload"]["save_button"])
            await self.page.wait_for_load_state("networkidle")
            
            # Verificar éxito
            success_alert = await self.page.locator(SELECTORS["alerts"]["success"]).count()
            error_alert = await self.page.locator(SELECTORS["alerts"]["error"]).count()
            
            if success_alert > 0:
                logger.info(f"Carta cargada exitosamente para {radicado}")
                return True
            elif error_alert > 0:
                error_text = await self.page.locator(SELECTORS["alerts"]["error"]).text_content()
                logger.error(f"Error cargando carta para {radicado}: {error_text}")
                return False
            else:
                logger.warning(f"Estado incierto para carga de {radicado}")
                return False
                
        except Exception as e:
            logger.error(f"Error cargando carta para {radicado}: {e}")
            return False
    
    async def upload_letters_batch(self, letters_data: List[Dict]) -> Dict[str, List[str]]:
        """🔄 MIGRADO DESDE IPO: Carga un lote de cartas"""
        results = {
            "success": [],
            "failed": [],
            "not_found": []
        }
        
        try:
            await self.initialize_browser()
            
            if not await self.login():
                logger.error("No se pudo hacer login")
                return results
            
            if not await self.navigate_to_pqr():
                logger.error("No se pudo navegar a PQR")
                return results
            
            for letter_info in letters_data:
                radicado = letter_info["radicado"]
                file_path = letter_info["file_path"]
                is_notification = letter_info.get("is_notification", False)
                
                # Intentar carga con reintentos
                success = False
                for attempt in range(MERCURIO_CONFIG["retry_attempts"]):
                    try:
                        success = await self.upload_letter(radicado, file_path, is_notification)
                        if success:
                            break
                        else:
                            if attempt < MERCURIO_CONFIG["retry_attempts"] - 1:
                                logger.info(f"Reintentando carga para {radicado} (intento {attempt + 2})")
                                await self.page.wait_for_timeout(MERCURIO_CONFIG["retry_delay"])
                    except Exception as e:
                        logger.error(f"Error en intento {attempt + 1} para {radicado}: {e}")
                        if attempt < MERCURIO_CONFIG["retry_attempts"] - 1:
                            await self.page.wait_for_timeout(MERCURIO_CONFIG["retry_delay"])
                
                # Clasificar resultado
                if success:
                    results["success"].append(radicado)
                else:
                    results["failed"].append(radicado)
                
                # Pausa entre cargas
                await self.page.wait_for_timeout(2000)
            
        except Exception as e:
            logger.error(f"Error en carga por lotes: {e}")
        finally:
            await self.close_browser()
        
        return results


# 🔄 MIGRADO DESDE IPO: Funciones de utilidad para base de datos
def get_pending_letters(company: str, limit: int = 50) -> pd.DataFrame:
    """Obtiene cartas pendientes de carga desde la base de datos"""
    try:
        engine = create_engine(config.database.get_connection_string())
        
        if company.lower() == "aire":
            query = """
            SELECT rad_mercurio, file_path, is_notification, created_at
            FROM public.aire_letters_pending
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT :limit
            """
        elif company.lower() == "afinia":
            query = """
            SELECT rad_mercurio, file_path, is_notification, created_at
            FROM public.afinia_letters_pending
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT :limit
            """
        else:
            raise ValueError(f"Empresa no soportada: {company}")
        
        return pd.read_sql(query, engine, params={"limit": limit})
        
    except Exception as e:
        logger.error(f"Error obteniendo cartas pendientes: {e}")
        return pd.DataFrame()


def update_letter_status(radicados: List[str], status: str, company: str) -> None:
    """Actualiza el estado de las cartas en la base de datos"""
    try:
        engine = create_engine(config.database.get_connection_string())
        
        if company.lower() == "aire":
            table = "public.aire_letters_pending"
        elif company.lower() == "afinia":
            table = "public.afinia_letters_pending"
        else:
            raise ValueError(f"Empresa no soportada: {company}")
        
        with engine.connect() as conn:
            for radicado in radicados:
                conn.execute(
                    text(f"UPDATE {table} SET status = :status, updated_at = :updated_at WHERE rad_mercurio = :radicado"),
                    {
                        "status": status,
                        "updated_at": datetime.now(zona_horaria),
                        "radicado": radicado
                    }
                )
        
        logger.info(f"Actualizado estado de {len(radicados)} cartas a '{status}'")
        
    except Exception as e:
        logger.error(f"Error actualizando estado de cartas: {e}")


# 🔄 MIGRADO DESDE IPO: Función principal de carga
async def upload_letters_for_company(company: str, limit: int = 50) -> Dict[str, List[str]]:
    """Función principal para cargar cartas de una empresa"""
    logger.info(f"Iniciando carga de cartas para {company}")
    
    try:
        # Obtener cartas pendientes
        pending_letters = get_pending_letters(company, limit)
        
        if pending_letters.empty:
            logger.info(f"No hay cartas pendientes para {company}")
            return {"success": [], "failed": [], "not_found": []}
        
        logger.info(f"Encontradas {len(pending_letters)} cartas pendientes")
        
        # Preparar datos para carga
        letters_data = []
        for _, row in pending_letters.iterrows():
            letters_data.append({
                "radicado": row["rad_mercurio"],
                "file_path": row["file_path"],
                "is_notification": row.get("is_notification", False)
            })
        
        # Realizar carga
        uploader = MercurioLetterUploader(company)
        results = await uploader.upload_letters_batch(letters_data)
        
        # Actualizar estados en base de datos
        if results["success"]:
            update_letter_status(results["success"], "uploaded", company)
        
        if results["failed"]:
            update_letter_status(results["failed"], "failed", company)
        
        logger.info(f"Carga completada para {company}: {len(results['success'])} exitosas, {len(results['failed'])} fallidas")
        
        return results
        
    except Exception as e:
        logger.error(f"Error en carga de cartas para {company}: {e}")
        return {"success": [], "failed": [], "not_found": []}


# 🔄 MIGRADO DESDE IPO: Función para ejecutar desde línea de comandos
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python upload_letters.py <company> [limit]")
        print("Ejemplo: python upload_letters.py aire 25")
        sys.exit(1)
    
    company = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    results = asyncio.run(upload_letters_for_company(company, limit))
    
    print(f"\nResultados para {company}:")
    print(f"Exitosas: {len(results['success'])}")
    print(f"Fallidas: {len(results['failed'])}")
    print(f"No encontradas: {len(results['not_found'])}")