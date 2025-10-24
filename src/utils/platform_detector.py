#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Platform Detector - Detector de Plataforma Centralizado
======================================================

Módulo centralizado para detectar la plataforma de ejecución (Windows/Ubuntu)
y configurar automáticamente el entorno apropiado.

Este módulo unifica toda la lógica de detección de plataforma y elimina
la duplicación de código entre diferentes managers.
"""

import os
import platform
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PlatformConfig:
    """Configuración específica de la plataforma detectada"""
    platform_type: str  # 'windows', 'ubuntu_server', 'ubuntu_desktop', 'other_linux'
    is_windows: bool
    is_ubuntu: bool
    is_server: bool
    headless_required: bool
    browser_config: Dict[str, Any]
    paths_config: Dict[str, str]
    environment_vars: Dict[str, str]

class PlatformDetector:
    """Detector centralizado de plataforma y configuración automática"""
    
    def __init__(self):
        self._platform_config: Optional[PlatformConfig] = None
        self._detection_cache = {}
        
    @property
    def platform_type(self) -> str:
        """Retorna el tipo de plataforma detectada"""
        return self.detect_platform().platform_type
    
    @property
    def platform_config(self) -> PlatformConfig:
        """Retorna la configuración completa de la plataforma"""
        return self.detect_platform()
    
    def is_windows(self) -> bool:
        """Verifica si la plataforma es Windows"""
        return self.detect_platform().is_windows
    
    def is_ubuntu(self) -> bool:
        """Verifica si la plataforma es Ubuntu"""
        return self.detect_platform().is_ubuntu
    
    def is_ubuntu_server(self) -> bool:
        """Verifica si la plataforma es Ubuntu Server"""
        return self.detect_platform().is_server
    
    def is_headless_required(self) -> bool:
        """Verifica si se requiere modo headless"""
        return self.detect_platform().headless_required
    
    def get_browser_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del navegador"""
        return self.detect_platform().browser_config
    
    def get_paths_config(self) -> Dict[str, str]:
        """Obtiene la configuración de rutas"""
        return self.detect_platform().paths_config
    
    def get_platform_config(self) -> Dict[str, Any]:
        """Obtiene la configuración completa como diccionario"""
        config = self.detect_platform()
        return {
            'platform_type': config.platform_type,
            'is_windows': config.is_windows,
            'is_ubuntu': config.is_ubuntu,
            'is_server': config.is_server,
            'headless_required': config.headless_required,
            'browser_config': config.browser_config,
            'paths': config.paths_config,
            'environment_vars': config.environment_vars
        }
        
    def detect_platform(self) -> PlatformConfig:
        """
        Detecta la plataforma y retorna la configuración completa
        
        Returns:
            PlatformConfig: Configuración completa de la plataforma
        """
        if self._platform_config:
            return self._platform_config
            
        logger.info("🔍 Detectando plataforma del sistema...")
        
        # Detectar tipo de sistema
        platform_type = self._detect_system_type()
        
        # Configurar según la plataforma detectada
        config = self._create_platform_config(platform_type)
        
        self._platform_config = config
        logger.info(f"✅ Plataforma detectada: {platform_type}")
        
        return config
    
    def _detect_system_type(self) -> str:
        """Detecta el tipo específico de sistema"""
        system = platform.system().lower()
        
        if system == 'windows':
            return 'windows'
        elif system == 'linux':
            return self._detect_linux_variant()
        else:
            logger.warning(f"Sistema no soportado: {system}")
            return 'unknown'
    
    def _detect_linux_variant(self) -> str:
        """Detecta la variante específica de Linux"""
        try:
            # Verificar si es Ubuntu
            if not self._is_ubuntu():
                return 'other_linux'
            
            # Verificar si es servidor (sin GUI)
            if self._is_server_environment():
                return 'ubuntu_server'
            else:
                return 'ubuntu_desktop'
                
        except Exception as e:
            logger.warning(f"Error detectando variante Linux: {e}")
            return 'other_linux'
    
    def _is_ubuntu(self) -> bool:
        """Verifica si el sistema es Ubuntu"""
        try:
            # Método 1: /etc/os-release
            if Path('/etc/os-release').exists():
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'ubuntu' in content:
                        return True
            
            # Método 2: lsb_release
            try:
                import subprocess
                result = subprocess.run(['lsb_release', '-i'], capture_output=True, text=True)
                if 'ubuntu' in result.stdout.lower():
                    return True
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
            
            return False
            
        except Exception as e:
            logger.warning(f"Error verificando Ubuntu: {e}")
            return False
    
    def _is_server_environment(self) -> bool:
        """Detecta si está ejecutándose en un entorno servidor (sin GUI)"""
        indicators = [
            # Variable de entorno forzada
            os.getenv('UBUNTU_SERVER', '').lower() == 'true',
            
            # No hay DISPLAY configurado
            os.getenv('DISPLAY') is None,
            
            # Variable HEADLESS activada
            os.getenv('HEADLESS', '').lower() == 'true',
            
            # Verificar si hay sesión X11 activa
            not self._has_x11_session(),
            
            # Verificar si hay gestores de ventanas corriendo
            not self._has_window_manager(),
        ]
        
        # Si al menos 2 indicadores son positivos, es servidor
        server_indicators = sum(indicators)
        is_server = server_indicators >= 2
        
        logger.debug(f"Indicadores de servidor: {server_indicators}/5 - Es servidor: {is_server}")
        return is_server
    
    def _has_x11_session(self) -> bool:
        """Verifica si hay una sesión X11 activa"""
        try:
            import subprocess
            result = subprocess.run(['xset', 'q'], capture_output=True, stderr=subprocess.DEVNULL)
            return result.returncode == 0
        except Exception:
            return False
    
    def _has_window_manager(self) -> bool:
        """Verifica si hay un gestor de ventanas corriendo"""
        try:
            import subprocess
            
            # Gestores de ventanas comunes
            window_managers = ['gnome-session', 'kde-session', 'xfce4-session', 'lxsession']
            
            for wm in window_managers:
                result = subprocess.run(['pgrep', '-x', wm], capture_output=True)
                if result.returncode == 0:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _create_platform_config(self, platform_type: str) -> PlatformConfig:
        """Crea la configuración específica para la plataforma detectada"""
        
        is_windows = platform_type == 'windows'
        is_ubuntu = platform_type.startswith('ubuntu')
        is_server = platform_type == 'ubuntu_server'
        headless_required = is_server or os.getenv('HEADLESS', '').lower() == 'true'
        
        # Configuración del navegador
        browser_config = self._get_browser_config(platform_type, headless_required)
        
        # Configuración de rutas
        paths_config = self._get_paths_config(platform_type)
        
        # Variables de entorno
        environment_vars = self._get_environment_vars(platform_type, headless_required)
        
        return PlatformConfig(
            platform_type=platform_type,
            is_windows=is_windows,
            is_ubuntu=is_ubuntu,
            is_server=is_server,
            headless_required=headless_required,
            browser_config=browser_config,
            paths_config=paths_config,
            environment_vars=environment_vars
        )
    
    def _get_browser_config(self, platform_type: str, headless_required: bool) -> Dict[str, Any]:
        """Obtiene la configuración del navegador según la plataforma"""
        
        base_config = {
            'headless': headless_required,
            'args': []
        }
        
        if platform_type == 'ubuntu_server':
            # Configuración específica para Ubuntu Server
            base_config['args'].extend([
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-field-trial-config',
                '--disable-ipc-flooding-protection'
            ])
            
            # Variables de entorno para Xvfb
            base_config['env_vars'] = {
                'DISPLAY': ':99',
                'XVFB_WHD': '1920x1080x24'
            }
            
        elif platform_type == 'windows':
            # Configuración específica para Windows
            base_config['args'].extend([
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ])
        
        return base_config
    
    def _get_paths_config(self, platform_type: str) -> Dict[str, str]:
        """Obtiene la configuración de rutas según la plataforma"""
        
        if platform_type == 'ubuntu_server':
            return {
                'downloads_base': '/home/ubuntu/ExtractorOV_Downloads',
                'logs_base': '/home/ubuntu/ExtractorOV_Logs',
                'screenshots_base': '/home/ubuntu/ExtractorOV_Screenshots',
                'browsers_base': '/home/ubuntu/.cache/ms-playwright'
            }
        else:
            # Windows y otros sistemas
            home = Path.home()
            return {
                'downloads_base': str(home / 'ExtractorOV_Downloads'),
                'logs_base': str(home / 'ExtractorOV_Logs'),
                'screenshots_base': str(home / 'ExtractorOV_Screenshots'),
                'browsers_base': str(home / '.cache' / 'ms-playwright')
            }
    
    def _get_environment_vars(self, platform_type: str, headless_required: bool) -> Dict[str, str]:
        """Obtiene las variables de entorno según la plataforma"""
        
        env_vars = {
            'PLATFORM_TYPE': platform_type,
            'HEADLESS': 'true' if headless_required else 'false'
        }
        
        if platform_type == 'ubuntu_server':
            env_vars.update({
                'UBUNTU_SERVER': 'true',
                'DISPLAY': ':99',
                'XVFB_WHD': '1920x1080x24',
                'PLAYWRIGHT_BROWSERS_PATH': '/home/ubuntu/.cache/ms-playwright'
            })
        
        return env_vars
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información completa del sistema"""
        config = self.detect_platform()
        
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'platform_type': config.platform_type,
            'is_windows': config.is_windows,
            'is_ubuntu': config.is_ubuntu,
            'is_server': config.is_server,
            'headless_required': config.headless_required,
            'user': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
            'home': str(Path.home()),
            'cwd': str(Path.cwd()),
        }
    
    def apply_environment_config(self):
        """Aplica la configuración de entorno detectada"""
        config = self.detect_platform()
        
        # Aplicar variables de entorno
        for key, value in config.environment_vars.items():
            if not os.getenv(key):
                os.environ[key] = value
                logger.debug(f"Variable de entorno configurada: {key}={value}")
        
        # Crear directorios necesarios
        self._ensure_directories_exist(config.paths_config)
    
    def _ensure_directories_exist(self, paths_config: Dict[str, str]):
        """Asegura que los directorios necesarios existan"""
        for path_type, path_str in paths_config.items():
            try:
                path = Path(path_str)
                path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Directorio asegurado: {path}")
            except Exception as e:
                logger.warning(f"Error creando directorio {path_str}: {e}")
    
    def print_platform_info(self):
        """Imprime información de la plataforma detectada"""
        config = self.detect_platform()
        system_info = self.get_system_info()
        
        print("=" * 80)
        print("🖥️  INFORMACIÓN DE PLATAFORMA DETECTADA")
        print("=" * 80)
        print(f"Sistema: {system_info['system']} ({system_info['platform']})")
        print(f"Tipo de plataforma: {config.platform_type}")
        print(f"Es Windows: {'✅' if config.is_windows else '❌'}")
        print(f"Es Ubuntu: {'✅' if config.is_ubuntu else '❌'}")
        print(f"Es servidor: {'✅' if config.is_server else '❌'}")
        print(f"Requiere headless: {'✅' if config.headless_required else '❌'}")
        print(f"Usuario: {system_info['user']}")
        print(f"Directorio actual: {system_info['cwd']}")
        print("=" * 80)

# Instancia global del detector
platform_detector = PlatformDetector()

# Funciones de conveniencia
def detect_platform() -> PlatformConfig:
    """Función de conveniencia para detectar la plataforma"""
    return platform_detector.detect_platform()

def is_windows() -> bool:
    """Función de conveniencia para verificar si es Windows"""
    return platform_detector.detect_platform().is_windows

def is_ubuntu() -> bool:
    """Función de conveniencia para verificar si es Ubuntu"""
    return platform_detector.detect_platform().is_ubuntu

def is_ubuntu_server() -> bool:
    """Función de conveniencia para verificar si es Ubuntu Server"""
    return platform_detector.detect_platform().is_server

def is_headless_required() -> bool:
    """Función de conveniencia para verificar si se requiere headless"""
    return platform_detector.detect_platform().headless_required

def get_browser_config() -> Dict[str, Any]:
    """Función de conveniencia para obtener configuración del navegador"""
    return platform_detector.detect_platform().browser_config

def get_paths_config() -> Dict[str, str]:
    """Función de conveniencia para obtener configuración de rutas"""
    return platform_detector.detect_platform().paths_config

def apply_platform_config():
    """Función de conveniencia para aplicar configuración de plataforma"""
    platform_detector.apply_environment_config()

def print_platform_info():
    """Función de conveniencia para mostrar información de plataforma"""
    platform_detector.print_platform_info()

# Configuración automática al importar
if __name__ == "__main__":
    print_platform_info()