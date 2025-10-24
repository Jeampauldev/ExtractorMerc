"""
Authentication Manager - Gestor de Autenticación
===============================================

Gestor centralizado de autenticación para las plataformas de Mercurio
de Afinia y Aire con manejo de credenciales y estrategias específicas.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from playwright.sync_api import Page
from dotenv import load_dotenv
from src.config.f_config_06.config import get_extractor_config

logger = logging.getLogger(__name__)

class AuthenticationManager:
    """
    Gestor centralizado de autenticación para Mercurio.
    
    Maneja las credenciales y estrategias de login específicas
    para cada empresa (Afinia y Aire).
    """
    
    def __init__(self, company: str):
        self.company = company.lower()
        self.credentials = self._load_credentials()
        self.config = get_extractor_config(self.company)

        if not self.config:
            raise ValueError(f"No se encontró configuración para la empresa: {self.company}")
    
    def _load_credentials(self) -> Dict[str, str]:
        """Cargar credenciales desde variables de entorno"""
        # Cargar archivo .env si existe
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_file):
            load_dotenv(env_file)
        
        # Obtener credenciales específicas por empresa
        username_key = f"{self.company.upper()}_USERNAME"
        password_key = f"{self.company.upper()}_PASSWORD"
        
        username = os.getenv(username_key)
        password = os.getenv(password_key)
        
        if not username or not password:
            logger.warning(f"[{self.company.upper()}] Credenciales no encontradas en variables de entorno")
            logger.warning(f"[{self.company.upper()}] Buscando: {username_key}, {password_key}")
        
        return {
            "username": username or "",
            "password": password or ""
        }
    
    def get_login_url(self) -> str:
        """Obtener URL de login para la empresa"""
        return self.config.get("login_url", "")
    
    def authenticate(self, page: Page, username: str = None, password: str = None) -> bool:
        """
        Realizar autenticación en la plataforma.
        
        Args:
            page: Página de Playwright
            username: Usuario opcional (si no se proporciona, usa las credenciales cargadas)
            password: Contraseña opcional (si no se proporciona, usa las credenciales cargadas)
            
        Returns:
            bool: True si la autenticación fue exitosa
        """
        try:
            # Usar credenciales proporcionadas o las cargadas por defecto
            auth_username = username or self.credentials["username"]
            auth_password = password or self.credentials["password"]
            
            if not auth_username or not auth_password:
                raise Exception("Credenciales no configuradas")
            
            logger.info(f"[{self.company.upper()}] Iniciando autenticación...")
            
            # Navegar a página de login
            login_url = self.get_login_url()
            logger.info(f"[{self.company.upper()}] Navegando a: {login_url}")
            
            try:
                page.goto(login_url, wait_until="networkidle", timeout=30000)  # 30 segundos máximo
            except Exception as e:
                logger.warning(f"[{self.company.upper()}] Timeout en goto, intentando con domcontentloaded: {str(e)}")
                try:
                    page.goto(login_url, wait_until="domcontentloaded", timeout=15000)
                except Exception as e2:
                    logger.error(f"[{self.company.upper()}] Error navegando: {str(e2)}")
                    raise Exception(f"No se pudo navegar a la página de login: {str(e2)}")
            
            # Esperar a que cargue la página con timeout controlado
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception as e:
                logger.warning(f"[{self.company.upper()}] Timeout en networkidle inicial, continuando: {str(e)}")
                page.wait_for_timeout(3000)
            
            # Llenar campo de usuario
            if not self._fill_field(page, self.config["selectors"]["username"], auth_username):
                raise Exception("No se pudo llenar el campo de usuario")
            
            # Llenar campo de contraseña
            if not self._fill_field(page, self.config["selectors"]["password"], auth_password):
                raise Exception("No se pudo llenar el campo de contraseña")
            
            # Hacer clic en botón de login
            if not self._click_element(page, self.config["selectors"]["login_button"]):
                raise Exception("No se pudo hacer clic en el botón de login")
            
            # Esperar a que complete el login con timeout más corto
            try:
                page.wait_for_load_state("networkidle", timeout=10000)  # 10 segundos máximo
            except Exception as e:
                logger.warning(f"[{self.company.upper()}] Timeout en networkidle, continuando: {str(e)}")
                # Esperar un poco y continuar
                page.wait_for_timeout(3000)
            
            # Verificar éxito del login
            if self._verify_login_success(page, self.config["success_indicators"]):
                logger.info(f"[{self.company.upper()}] Autenticación exitosa")
                return True
            else:
                raise Exception("Login fallido - no se encontraron indicadores de éxito")
            
        except Exception as e:
            logger.error(f"[{self.company.upper()}] Error en autenticación: {str(e)}")
            return False
    
    def _fill_field(self, page: Page, selectors: List[str], value: str) -> bool:
        """Llenar un campo usando múltiples selectores"""
        for selector in selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.fill(selector, value)
                    logger.debug(f"[{self.company.upper()}] Campo llenado con selector: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"[{self.company.upper()}] Selector falló: {selector} - {str(e)}")
                continue
        
        logger.error(f"[{self.company.upper()}] No se pudo llenar campo con ningún selector")
        return False
    
    def _click_element(self, page: Page, selectors: List[str]) -> bool:
        """Hacer clic en un elemento usando múltiples selectores"""
        for selector in selectors:
            try:
                # Verificar si el elemento existe
                if page.locator(selector).count() > 0:
                    # Esperar a que el elemento sea visible y esté habilitado
                    page.wait_for_selector(selector, state="visible", timeout=5000)
                    
                    # Hacer scroll al elemento si es necesario
                    page.locator(selector).scroll_into_view_if_needed()
                    
                    # Hacer clic
                    page.click(selector, timeout=5000)
                    logger.info(f"[{self.company.upper()}] Clic exitoso con selector: {selector}")
                    
                    # Esperar un poco después del clic con timeout controlado
                    try:
                        page.wait_for_timeout(1000)
                    except Exception as e:
                        logger.warning(f"[{self.company.upper()}] Timeout después del clic: {str(e)}")
                    return True
            except Exception as e:
                logger.debug(f"[{self.company.upper()}] Clic falló: {selector} - {str(e)}")
                continue
        
        logger.error(f"[{self.company.upper()}] No se pudo hacer clic con ningún selector")
        return False
    
    def _verify_login_success(self, page: Page, indicators: List[str]) -> bool:
        """Verificar éxito del login usando indicadores"""
        for indicator in indicators:
            try:
                # Esperar un poco para que cargue la página
                page.wait_for_timeout(2000)
                
                if page.locator(indicator).count() > 0:
                    logger.debug(f"[{self.company.upper()}] Indicador de éxito encontrado: {indicator}")
                    return True
            except Exception as e:
                logger.debug(f"[{self.company.upper()}] Indicador no encontrado: {indicator}")
                continue
        
        # Verificar también por URL o título
        current_url = page.url
        if "login" not in current_url.lower() and "error" not in current_url.lower():
            logger.debug(f"[{self.company.upper()}] Login exitoso por URL: {current_url}")
            return True
        
        return False
    
    def get_credentials(self) -> Dict[str, str]:
        """Obtener credenciales actuales"""
        return self.credentials.copy()
    
    def update_credentials(self, username: str, password: str) -> None:
        """Actualizar credenciales"""
        self.credentials["username"] = username
        self.credentials["password"] = password
        logger.info(f"[{self.company.upper()}] Credenciales actualizadas")