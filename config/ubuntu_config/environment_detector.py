#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Detector de Entorno para Ubuntu Server
======================================

Detecta automáticamente si el sistema está ejecutándose en Ubuntu Server
y configura las variables apropiadas.
"""

import os
import platform
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EnvironmentDetector:
    """Detecta y configura el entorno de ejecución apropiado"""
    
    def __init__(self):
        self._system_info = None
        self._environment_type = None
        self._detection_cache = {}
    
    def detect_system_type(self) -> str:
        """
        Detecta el tipo de sistema donde se está ejecutando
        
        Returns:
            str: 'ubuntu_server', 'ubuntu_desktop', 'windows', 'other_linux', 'unknown'
        """
        if self._environment_type:
            return self._environment_type
        
        system = platform.system().lower()
        
        if system == 'windows':
            self._environment_type = 'windows'
        elif system == 'linux':
            self._environment_type = self._detect_linux_variant()
        else:
            self._environment_type = 'unknown'
        
        logger.info(f"Sistema detectado: {self._environment_type}")
        return self._environment_type
    
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
        
        logger.info(f"Indicadores de servidor: {server_indicators}/5 - Es servidor: {is_server}")
        return is_server
    
    def _has_x11_session(self) -> bool:
        """Verifica si hay una sesión X11 activa"""
        try:
            # Verificar DISPLAY
            if os.getenv('DISPLAY'):
                return True
            
            # Verificar procesos X11
            import subprocess
            result = subprocess.run(['pgrep', '-x', 'Xorg'], capture_output=True)
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
    
    def is_ubuntu_server(self) -> bool:
        """Método de conveniencia para verificar si es Ubuntu Server"""
        return self.detect_system_type() == 'ubuntu_server'
    
    def is_headless_required(self) -> bool:
        """Determina si se requiere modo headless"""
        system_type = self.detect_system_type()
        return system_type in ['ubuntu_server', 'other_linux'] or os.getenv('HEADLESS', '').lower() == 'true'
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtiene información completa del sistema"""
        if self._system_info:
            return self._system_info
        
        try:
            info = {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'environment_type': self.detect_system_type(),
                'headless_required': self.is_headless_required(),
                'display': os.getenv('DISPLAY'),
                'user': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
                'home': str(Path.home()),
                'cwd': str(Path.cwd()),
            }
            
            # Información específica de Ubuntu
            if self.detect_system_type().startswith('ubuntu'):
                info.update(self._get_ubuntu_info())
            
            self._system_info = info
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo información del sistema: {e}")
            return {'environment_type': 'unknown', 'error': str(e)}
    
    def _get_ubuntu_info(self) -> Dict[str, str]:
        """Obtiene información específica de Ubuntu"""
        info = {}
        
        try:
            import subprocess
            
            # Versión de Ubuntu
            result = subprocess.run(['lsb_release', '-rs'], capture_output=True, text=True)
            if result.returncode == 0:
                info['ubuntu_version'] = result.stdout.strip()
            
            # Codename de Ubuntu
            result = subprocess.run(['lsb_release', '-cs'], capture_output=True, text=True)
            if result.returncode == 0:
                info['ubuntu_codename'] = result.stdout.strip()
                
        except Exception as e:
            logger.warning(f"Error obteniendo información de Ubuntu: {e}")
        
        return info
    
    def configure_environment(self) -> Dict[str, str]:
        """
        Configura las variables de entorno apropiadas para el sistema detectado
        
        Returns:
            Dict con las variables de entorno recomendadas
        """
        env_vars = {}
        system_type = self.detect_system_type()
        
        if system_type == 'ubuntu_server':
            env_vars.update({
                'HEADLESS': 'true',
                'UBUNTU_SERVER': 'true',
                'DISPLAY': ':99',
                'PLAYWRIGHT_BROWSERS_PATH': str(Path.home() / 'ExtractorOV_Modular' / 'browsers'),
                'PYTHONPATH': str(Path.cwd()),
            })
        elif system_type == 'ubuntu_desktop':
            env_vars.update({
                'HEADLESS': 'false',
                'UBUNTU_SERVER': 'false',
                'PYTHONPATH': str(Path.cwd()),
            })
        elif system_type == 'windows':
            env_vars.update({
                'HEADLESS': 'false',
                'WINDOWS': 'true',
                'PYTHONPATH': str(Path.cwd()),
            })
        
        logger.info(f"Variables de entorno configuradas: {list(env_vars.keys())}")
        return env_vars
    
    def print_system_summary(self):
        """Imprime un resumen del sistema detectado"""
        info = self.get_system_info()
        env_vars = self.configure_environment()
        
        print("=" * 60)
        print("[EMOJI_REMOVIDO]  DETECCIÓN DE ENTORNO - ExtractorOV")
        print("=" * 60)
        print(f"Sistema operativo: {info.get('system', 'Unknown')}")
        print(f"Plataforma: {info.get('platform', 'Unknown')}")
        print(f"Tipo de entorno: {info.get('environment_type', 'Unknown')}")
        print(f"Usuario: {info.get('user', 'Unknown')}")
        print(f"Directorio home: {info.get('home', 'Unknown')}")
        
        if 'ubuntu_version' in info:
            print(f"Versión Ubuntu: {info['ubuntu_version']} ({info.get('ubuntu_codename', 'Unknown')})")
        
        print(f"Modo headless requerido: {'[EXITOSO] SÍ' if info.get('headless_required') else '[ERROR] NO'}")
        print(f"Variable DISPLAY: {info.get('display', 'No configurada')}")
        
        print("\n[CONFIGURANDO] VARIABLES DE ENTORNO RECOMENDADAS:")
        for key, value in env_vars.items():
            print(f"   {key}={value}")
        
        print("=" * 60)

# Instancia global para usar en otros módulos
environment_detector = EnvironmentDetector()

# Funciones de conveniencia
def is_ubuntu_server() -> bool:
    """Función de conveniencia para verificar si es Ubuntu Server"""
    return environment_detector.is_ubuntu_server()

def is_headless_required() -> bool:
    """Función de conveniencia para verificar si se requiere modo headless"""
    return environment_detector.is_headless_required()

def get_recommended_environment_vars() -> Dict[str, str]:
    """Función de conveniencia para obtener variables de entorno recomendadas"""
    return environment_detector.configure_environment()

def get_system_info() -> Dict[str, Any]:
    """Función de conveniencia para obtener información del sistema"""
    return environment_detector.get_system_info()

def print_system_info():
    """Función de conveniencia para mostrar información del entorno"""
    environment_detector.print_system_summary()

# Ejecutar detección automática al importar
if __name__ == "__main__":
    print_environment_info()