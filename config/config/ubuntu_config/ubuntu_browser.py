#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configurador de Navegador para Ubuntu Server
============================================

Configura automáticamente el navegador según el entorno detectado,
optimizando para Ubuntu Server con modo headless.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from .environment_detector import is_ubuntu_server, is_headless_required

logger = logging.getLogger(__name__)

class UbuntuBrowserConfig:
    """Configurador de navegador adaptivo para diferentes entornos"""
    
    def __init__(self, force_headless: bool = None):
        """
        Inicializa el configurador de navegador
        
        Args:
            force_headless: Forzar modo headless (None = automático)
        """
        self.is_ubuntu = is_ubuntu_server()
        self.force_headless = force_headless
        self.auto_headless = is_headless_required()
        
        # Determinar si usar headless
        if force_headless is not None:
            self.headless = force_headless
        else:
            self.headless = self.auto_headless
        
        logger.info(f"[EMOJI_REMOVIDO] BrowserConfig - Ubuntu: {self.is_ubuntu}, Headless: {self.headless}")
    
    def get_chrome_args(self) -> List[str]:
        """
        Obtiene los argumentos de Chrome optimizados para el entorno
        
        Returns:
            List[str]: Lista de argumentos para Chrome
        """
        if self.is_ubuntu or self.headless:
            return self._get_ubuntu_chrome_args()
        else:
            return self._get_windows_chrome_args()
    
    def _get_ubuntu_chrome_args(self) -> List[str]:
        """Argumentos de Chrome optimizados para Ubuntu Server"""
        args = [
            # Argumentos básicos de headless
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            
            # Optimizaciones de memoria para servidor
            "--memory-pressure-off",
            "--max_old_space_size=4096",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            
            # Desactivar funciones innecesarias en servidor
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",
            "--disable-javascript",  # Se puede remover si se necesita JS
            "--disable-default-apps",
            "--disable-sync",
            
            # Configuración de red
            "--aggressive-cache-discard",
            "--disable-background-networking",
            
            # Configuración de display para entorno servidor
            "--display=:99" if os.getenv('DISPLAY') else "",
            
            # Argumentos específicos para headless
            "--window-size=1366,768",
            "--start-maximized",
            "--disable-infobars",
            "--disable-notifications",
        ]
        
        # Filtrar argumentos vacíos
        return [arg for arg in args if arg]
    
    def _get_windows_chrome_args(self) -> List[str]:
        """Argumentos de Chrome optimizados para Windows"""
        args = [
            # Argumentos básicos para Windows
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--start-maximized",
            "--disable-infobars",
            
            # Configuraciones específicas de Windows
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]
        
        return args
    
    def get_playwright_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración completa para Playwright
        
        Returns:
            Dict: Configuración de Playwright
        """
        config = {
            "headless": self.headless,
            "args": self.get_chrome_args(),
            "viewport": {"width": 1366, "height": 768},
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "accept_downloads": True,
        }
        
        # Configuraciones específicas según entorno
        if self.is_ubuntu:
            config.update(self._get_ubuntu_playwright_config())
        else:
            config.update(self._get_windows_playwright_config())
        
        return config
    
    def _get_ubuntu_playwright_config(self) -> Dict[str, Any]:
        """Configuraciones específicas de Playwright para Ubuntu"""
        return {
            "slow_mo": 100,  # Ralentizar para servidor
            "timeout": 60000,  # Mayor timeout para servidor
            "navigation_timeout": 60000,
            "expect_timeout": 30000,
            
            # Configuración de downloads para Ubuntu
            "download_path": os.path.expanduser("~/ExtractorOV_Modular/downloads"),
            
            # Variables de entorno específicas
            "env": {
                "DISPLAY": ":99",
                "UBUNTU_SERVER": "true",
                "HEADLESS": "true",
            }
        }
    
    def _get_windows_playwright_config(self) -> Dict[str, Any]:
        """Configuraciones específicas de Playwright para Windows"""
        return {
            "slow_mo": 50,  # Velocidad normal para desktop
            "timeout": 30000,  # Timeout normal
            "navigation_timeout": 30000,
            "expect_timeout": 15000,
        }
    
    def get_browser_executable_path(self) -> Optional[str]:
        """
        Obtiene la ruta del ejecutable del navegador según el entorno
        
        Returns:
            Optional[str]: Ruta del ejecutable o None para usar default
        """
        if self.is_ubuntu:
            # Rutas comunes de Chrome en Ubuntu
            chrome_paths = [
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium",
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    logger.info(f"[EMOJI_REMOVIDO] Chrome encontrado en: {path}")
                    return path
            
            logger.warning("[ADVERTENCIA] No se encontró Chrome instalado en Ubuntu")
            return None
        
        # En Windows, usar el path por defecto de Playwright
        return None
    
    def setup_xvfb_environment(self) -> Dict[str, str]:
        """
        Configura el entorno XVFB para Ubuntu Server
        
        Returns:
            Dict: Variables de entorno para XVFB
        """
        if not self.is_ubuntu:
            return {}
        
        env_vars = {
            "DISPLAY": ":99",
            "XVFB_WHD": "1366x768x24",
            "UBUNTU_SERVER": "true",
        }
        
        logger.info("[EMOJI_REMOVIDO] Configuración XVFB activada")
        return env_vars
    
    def validate_browser_setup(self) -> bool:
        """
        Valida que la configuración del navegador sea correcta
        
        Returns:
            bool: True si la configuración es válida
        """
        try:
            config = self.get_playwright_config()
            
            # Validaciones básicas
            if not isinstance(config.get("headless"), bool):
                logger.error("[ERROR] Configuración headless inválida")
                return False
            
            if not isinstance(config.get("args"), list):
                logger.error("[ERROR] Argumentos de Chrome inválidos")
                return False
            
            # Validaciones específicas para Ubuntu
            if self.is_ubuntu:
                if not self._validate_ubuntu_setup():
                    return False
            
            logger.info("[EXITOSO] Configuración del navegador validada")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error validando configuración: {e}")
            return False
    
    def _validate_ubuntu_setup(self) -> bool:
        """Valida la configuración específica de Ubuntu"""
        try:
            # Verificar XVFB si está en headless
            if self.headless:
                if not os.getenv('DISPLAY'):
                    logger.warning("[ADVERTENCIA] DISPLAY no configurado - recomendado para headless")
            
            # Verificar si Chrome está instalado
            chrome_path = self.get_browser_executable_path()
            if not chrome_path:
                logger.warning("[ADVERTENCIA] Chrome no encontrado - Playwright instalará automáticamente")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error validando setup Ubuntu: {e}")
            return False
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de toda la configuración
        
        Returns:
            Dict: Resumen de configuración
        """
        config = self.get_playwright_config()
        
        return {
            "environment": "ubuntu_server" if self.is_ubuntu else "windows",
            "headless": self.headless,
            "auto_headless": self.auto_headless,
            "chrome_args_count": len(config["args"]),
            "viewport": config["viewport"],
            "timeout": config.get("timeout", 30000),
            "chrome_executable": self.get_browser_executable_path(),
            "xvfb_enabled": bool(self.is_ubuntu and self.headless),
            "download_path": config.get("download_path", "default"),
        }
    
    def print_configuration_summary(self):
        """Imprime un resumen de la configuración del navegador"""
        summary = self.get_configuration_summary()
        config = self.get_playwright_config()
        
        print("=" * 60)
        print("[EMOJI_REMOVIDO] CONFIGURACIÓN DEL NAVEGADOR - ExtractorOV")
        print("=" * 60)
        print(f"Entorno: {summary['environment'].upper()}")
        print(f"Modo headless: {'[EXITOSO] ACTIVADO' if summary['headless'] else '[ERROR] DESACTIVADO'}")
        print(f"Auto-detección headless: {'[EXITOSO]' if summary['auto_headless'] else '[ERROR]'}")
        print(f"Viewport: {summary['viewport']['width']}x{summary['viewport']['height']}")
        print(f"Timeout: {summary['timeout']}ms")
        print(f"Chrome ejecutable: {summary['chrome_executable'] or 'Por defecto (Playwright)'}")
        
        if summary['xvfb_enabled']:
            print("[EMOJI_REMOVIDO] XVFB: [EXITOSO] HABILITADO")
            xvfb_env = self.setup_xvfb_environment()
            for key, value in xvfb_env.items():
                print(f"   {key}={value}")
        else:
            print("[EMOJI_REMOVIDO] XVFB: [ERROR] NO REQUERIDO")
        
        print(f"\n[CONFIGURANDO] ARGUMENTOS DE CHROME ({len(config['args'])} total):")
        for i, arg in enumerate(config['args'][:10], 1):  # Mostrar solo primeros 10
            print(f"   {i}. {arg}")
        
        if len(config['args']) > 10:
            print(f"   ... y {len(config['args']) - 10} argumentos más")
        
        print("=" * 60)


# Funciones de conveniencia
def get_browser_config(force_headless: bool = None) -> Dict[str, Any]:
    """
    Función de conveniencia para obtener configuración del navegador
    
    Args:
        force_headless: Forzar modo headless
    
    Returns:
        Dict: Configuración de Playwright
    """
    browser_config = UbuntuBrowserConfig(force_headless=force_headless)
    return browser_config.get_playwright_config()

def get_chrome_args(force_headless: bool = None) -> List[str]:
    """
    Función de conveniencia para obtener argumentos de Chrome
    
    Args:
        force_headless: Forzar modo headless
    
    Returns:
        List[str]: Argumentos de Chrome
    """
    browser_config = UbuntuBrowserConfig(force_headless=force_headless)
    return browser_config.get_chrome_args()

def setup_xvfb_env() -> Dict[str, str]:
    """
    Función de conveniencia para configurar entorno XVFB
    
    Returns:
        Dict[str, str]: Variables de entorno para XVFB
    """
    browser_config = UbuntuBrowserConfig()
    return browser_config.setup_xvfb_environment()

def print_browser_info():
    """Función de conveniencia para mostrar información del navegador"""
    browser_config = UbuntuBrowserConfig()
    browser_config.print_configuration_summary()

# Instancia global para uso directo
browser_config = UbuntuBrowserConfig()

if __name__ == "__main__":
    print_browser_info()