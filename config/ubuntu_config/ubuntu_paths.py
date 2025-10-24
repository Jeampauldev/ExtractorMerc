#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestor de Rutas Multiplataforma
===============================

Gestiona las rutas de archivos y directorios de manera compatible
entre Windows y Ubuntu Server.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, Union
from .environment_detector import is_ubuntu_server

logger = logging.getLogger(__name__)

class PathManager:
    """Gestor de rutas multiplataforma para ExtractorOV"""
    
    def __init__(self, force_ubuntu: bool = False):
        """
        Inicializa el gestor de rutas
        
        Args:
            force_ubuntu: Forzar el uso de rutas Ubuntu (para testing)
        """
        self.is_ubuntu = force_ubuntu or is_ubuntu_server()
        self._paths_cache = {}
        self._initialize_paths()
    
    def _initialize_paths(self):
        """Inicializa las rutas base según el sistema detectado"""
        if self.is_ubuntu:
            self._setup_ubuntu_paths()
        else:
            self._setup_windows_paths()
        
        # Crear directorios necesarios
        self._ensure_directories_exist()
    
    def _setup_ubuntu_paths(self):
        """Configura rutas para Ubuntu Server"""
        logger.info("[EMOJI_REMOVIDO] Configurando rutas para Ubuntu Server")
        
        # Directorio base del proyecto
        self.project_root = Path.home() / "ExtractorOV_Modular"
        
        # Directorios principales
        self.downloads_dir = self.project_root / "data" / "downloads"
        self.screenshots_dir = self.project_root / "data" / "downloads" / "screenshots"
        self.logs_dir = self.project_root / "data" / "data/logs"
        self.data_dir = self.project_root / "data"
        self.config_dir = self.project_root / "config" / "env"
        
        # Directorios específicos de empresas
        self.aire_downloads = self.downloads_dir / "aire" / "oficina_virtual"
        self.afinia_downloads = self.downloads_dir / "afinia" / "oficina_virtual"
        
        # Screenshots específicos
        self.aire_screenshots = self.aire_downloads / "screenshots"
        self.afinia_screenshots = self.afinia_downloads / "screenshots"
        
        # Procesados
        self.aire_processed = self.aire_downloads / "processed"
        self.afinia_processed = self.afinia_downloads / "processed"
        
        # Archivos de configuración
        self.env_file = self.project_root / ".env"
        self.log_file = self.logs_dir / "extractor.log"
        
        # Playwright
        self.browsers_dir = self.project_root / "browsers"
        
        logger.info(f"[EMOJI_REMOVIDO] Directorio base: {self.project_root}")
    
    def _setup_windows_paths(self):
        """Configura rutas para Windows"""
        logger.info("🪟 Configurando rutas para Windows")
        
        # Directorio base del proyecto (mantener estructura actual)
        self.project_root = Path("C:/00_Project_Dev/ExtractorOV_Modular")
        
        # Directorios principales
        self.downloads_dir = self.project_root / "data" / "downloads"
        self.screenshots_dir = self.project_root / "data" / "downloads" / "screenshots"
        self.logs_dir = self.project_root / "data" / "data/logs"
        self.data_dir = self.project_root / "data"
        self.config_dir = self.project_root / "config" / "env"
        
        # Directorios específicos de empresas
        self.aire_downloads = self.downloads_dir / "aire" / "oficina_virtual"
        self.afinia_downloads = self.downloads_dir / "afinia" / "oficina_virtual"
        
        # Screenshots específicos
        self.aire_screenshots = self.aire_downloads / "screenshots"
        self.afinia_screenshots = self.afinia_downloads / "screenshots"
        
        # Procesados
        self.aire_processed = self.aire_downloads / "processed"
        self.afinia_processed = self.afinia_downloads / "processed"
        
        # Archivos de configuración
        self.env_file = self.config_dir / ".env"
        self.log_file = self.logs_dir / "extractor.log"
        
        # Playwright (usar default de Windows)
        self.browsers_dir = None
        
        logger.info(f"[EMOJI_REMOVIDO] Directorio base: {self.project_root}")
    
    def _ensure_directories_exist(self):
        """Crea todos los directorios necesarios"""
        directories = [
            self.project_root,
            self.downloads_dir,
            self.screenshots_dir,
            self.logs_dir,
            self.data_dir,
            self.config_dir,
            self.aire_downloads,
            self.afinia_downloads,
            self.aire_screenshots,
            self.afinia_screenshots,
            self.aire_processed,
            self.afinia_processed,
        ]
        
        # Agregar browsers_dir si está definido (Ubuntu)
        if self.browsers_dir:
            directories.append(self.browsers_dir)
        
        created_count = 0
        for directory in directories:
            if not directory.exists():
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    if self.is_ubuntu:
                        # Configurar permisos apropiados en Ubuntu
                        os.chmod(str(directory), 0o755)
                    created_count += 1
                    logger.debug(f"[EMOJI_REMOVIDO] Directorio creado: {directory}")
                except Exception as e:
                    logger.error(f"[ERROR] Error creando directorio {directory}: {e}")
        
        if created_count > 0:
            logger.info(f"[EMOJI_REMOVIDO] {created_count} directorios creados/verificados")
    
    def get_download_path(self, empresa: str = "general") -> Path:
        """
        Obtiene la ruta de descarga para una empresa específica
        
        Args:
            empresa: 'aire', 'afinia', o 'general'
        
        Returns:
            Path: Ruta de descarga apropiada
        """
        empresa = empresa.lower()
        
        if empresa == "aire":
            return self.aire_downloads
        elif empresa == "afinia":
            return self.afinia_downloads
        else:
            return self.downloads_dir
    
    def get_processed_path(self, empresa: str) -> Path:
        """
        Obtiene la ruta de archivos procesados para una empresa
        
        Args:
            empresa: 'aire' o 'afinia'
        
        Returns:
            Path: Ruta de archivos procesados
        """
        empresa = empresa.lower()
        
        if empresa == "aire":
            return self.aire_processed
        elif empresa == "afinia":
            return self.afinia_processed
        else:
            return self.data_dir
    
    def get_screenshots_path(self, empresa: str = "general") -> Path:
        """
        Obtiene la ruta de screenshots para una empresa específica
        
        Args:
            empresa: 'aire', 'afinia', o 'general'
        
        Returns:
            Path: Ruta de screenshots apropiada
        """
        empresa = empresa.lower()
        
        if empresa == "aire":
            return self.aire_screenshots
        elif empresa == "afinia":
            return self.afinia_screenshots
        else:
            return self.screenshots_dir
    
    def get_env_file_path(self) -> Path:
        """Obtiene la ruta del archivo .env"""
        return self.env_file
    
    def get_log_file_path(self, empresa: Optional[str] = None) -> Path:
        """
        Obtiene la ruta del archivo de log
        
        Args:
            empresa: Empresa específica para log separado (opcional)
        
        Returns:
            Path: Ruta del archivo de log
        """
        if empresa:
            return self.logs_dir / f"{empresa.lower()}_extractor.log"
        return self.log_file
    
    def get_relative_path(self, absolute_path: Union[str, Path]) -> Path:
        """
        Convierte una ruta absoluta a relativa respecto al proyecto
        
        Args:
            absolute_path: Ruta absoluta
        
        Returns:
            Path: Ruta relativa al proyecto
        """
        abs_path = Path(absolute_path)
        try:
            return abs_path.relative_to(self.project_root)
        except ValueError:
            return abs_path
    
    def ensure_path_exists(self, path: Union[str, Path], is_file: bool = False) -> bool:
        """
        Asegura que una ruta existe, creándola si es necesario
        
        Args:
            path: Ruta a verificar/crear
            is_file: Si True, crea el directorio padre; si False, crea el directorio
        
        Returns:
            bool: True si la ruta existe o se creó exitosamente
        """
        path_obj = Path(path)
        
        try:
            if is_file:
                # Si es un archivo, crear el directorio padre
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                if self.is_ubuntu:
                    os.chmod(str(path_obj.parent), 0o755)
            else:
                # Si es un directorio, crearlo
                path_obj.mkdir(parents=True, exist_ok=True)
                if self.is_ubuntu:
                    os.chmod(str(path_obj), 0o755)
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error creando ruta {path}: {e}")
            return False
    
    def get_path_info(self) -> Dict[str, str]:
        """
        Obtiene un diccionario con información de todas las rutas configuradas
        
        Returns:
            Dict: Información de rutas
        """
        return {
            "system_type": "ubuntu_server" if self.is_ubuntu else "windows",
            "project_root": str(self.project_root),
            "downloads_dir": str(self.downloads_dir),
            "screenshots_dir": str(self.screenshots_dir),
            "logs_dir": str(self.logs_dir),
            "aire_downloads": str(self.aire_downloads),
            "afinia_downloads": str(self.afinia_downloads),
            "aire_processed": str(self.aire_processed),
            "afinia_processed": str(self.afinia_processed),
            "env_file": str(self.env_file),
            "log_file": str(self.log_file),
            "browsers_dir": str(self.browsers_dir) if self.browsers_dir else "default",
        }
    
    def print_paths_summary(self):
        """Imprime un resumen de todas las rutas configuradas"""
        info = self.get_path_info()
        
        print("=" * 60)
        print("[EMOJI_REMOVIDO] CONFIGURACIÓN DE RUTAS - ExtractorOV")
        print("=" * 60)
        print(f"Sistema: {info['system_type'].upper()}")
        print(f"Directorio del proyecto: {info['project_root']}")
        print()
        print("[EMOJI_REMOVIDO] DIRECTORIOS PRINCIPALES:")
        print(f"   Descargas: {info['downloads_dir']}")
        print(f"   Screenshots: {info['screenshots_dir']}")
        print(f"   Logs: {info['logs_dir']}")
        print()
        print("[EMOJI_REMOVIDO] DIRECTORIOS POR EMPRESA:")
        print(f"   Aire - Descargas: {info['aire_downloads']}")
        print(f"   Aire - Procesados: {info['aire_processed']}")
        print(f"   Afinia - Descargas: {info['afinia_downloads']}")
        print(f"   Afinia - Procesados: {info['afinia_processed']}")
        print()
        print("[CONFIGURACION] ARCHIVOS DE CONFIGURACIÓN:")
        print(f"   Variables entorno: {info['env_file']}")
        print(f"   Archivo de log: {info['log_file']}")
        print(f"   Navegadores: {info['browsers_dir']}")
        print("=" * 60)


# Instancia global del PathManager
path_manager = PathManager()

# Funciones de conveniencia para uso directo
def get_download_path(empresa: str = "general") -> Path:
    """Función de conveniencia para obtener ruta de descarga"""
    return path_manager.get_download_path(empresa)

def get_processed_path(empresa: str) -> Path:
    """Función de conveniencia para obtener ruta de procesados"""
    return path_manager.get_processed_path(empresa)

def get_screenshots_path(empresa: str = "general") -> Path:
    """Función de conveniencia para obtener ruta de screenshots"""
    return path_manager.get_screenshots_path(empresa)

def ensure_path_exists(path: Union[str, Path], is_file: bool = False) -> bool:
    """Función de conveniencia para asegurar que una ruta existe"""
    return path_manager.ensure_path_exists(path, is_file)

def get_ubuntu_paths() -> PathManager:
    """Función de conveniencia para obtener el gestor de rutas"""
    return path_manager

def create_project_directories() -> bool:
    """Función de conveniencia para crear todos los directorios del proyecto"""
    try:
        path_manager._ensure_directories_exist()
        return True
    except Exception as e:
        logger.error(f"Error creando directorios del proyecto: {e}")
        return False

def print_paths_info():
    """Función de conveniencia para mostrar información de rutas"""
    path_manager.print_paths_summary()

# Ejecutar configuración automática al importar
if __name__ == "__main__":
    print_paths_info()
