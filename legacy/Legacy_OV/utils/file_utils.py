#!/usr/bin/env python3
"""
Utilidades de Archivos
======================

Utilidades para manejo de archivos y directorios.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class FileUtils:
    """Utilidades para manejo de archivos"""

    @staticmethod
    def ensure_directory(directory_path: Union[str, Path]) -> bool:
        """
        Asegura que un directorio existe, creándolo si es necesario

        Args:
            directory_path: Ruta del directorio

        Returns:
            bool: True si el directorio existe o fue creado exitosamente
        """
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creando directorio {directory_path}: {e}")
            return False

    @staticmethod
    def read_json_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Lee un archivo JSON

        Args:
            file_path: Ruta del archivo JSON

        Returns:
            Dict con el contenido del JSON o None si hay error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo archivo JSON {file_path}: {e}")
            return None

    @staticmethod
    def write_json_file(file_path: Union[str, Path], data: Dict[str, Any], 
                       indent: int = 2) -> bool:
        """
        Escribe datos a un archivo JSON

        Args:
            file_path: Ruta del archivo JSON
            data: Datos a escribir
            indent: Indentación para el JSON

        Returns:
            bool: True si se escribió exitosamente
        """
        try:
            # Asegurar que el directorio padre existe
            FileUtils.ensure_directory(Path(file_path).parent)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error escribiendo archivo JSON {file_path}: {e}")
            return False

    @staticmethod
    def move_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Mueve un archivo de origen a destino

        Args:
            source: Ruta del archivo origen
            destination: Ruta del archivo destino

        Returns:
            bool: True si se movió exitosamente
        """
        try:
            # Asegurar que el directorio destino existe
            FileUtils.ensure_directory(Path(destination).parent)

            shutil.move(str(source), str(destination))
            return True
        except Exception as e:
            logger.error(f"Error moviendo archivo {source} a {destination}: {e}")
            return False

    @staticmethod
    def copy_file(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Copia un archivo de origen a destino

        Args:
            source: Ruta del archivo origen
            destination: Ruta del archivo destino

        Returns:
            bool: True si se copió exitosamente
        """
        try:
            # Asegurar que el directorio destino existe
            FileUtils.ensure_directory(Path(destination).parent)

            shutil.copy2(str(source), str(destination))
            return True
        except Exception as e:
            logger.error(f"Error copiando archivo {source} a {destination}: {e}")
            return False

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> Optional[int]:
        """
        Obtiene el tamaño de un archivo en bytes

        Args:
            file_path: Ruta del archivo

        Returns:
            int: Tamaño en bytes o None si hay error
        """
        try:
            return Path(file_path).stat().st_size
        except Exception as e:
            logger.error(f"Error obteniendo tamaño de archivo {file_path}: {e}")
            return None

    @staticmethod
    def list_files_in_directory(directory_path: Union[str, Path], 
                               pattern: str = "*") -> List[Path]:
        """
        Lista archivos en un directorio con un patrón opcional

        Args:
            directory_path: Ruta del directorio
            pattern: Patrón de archivos (ej: "*.json")

        Returns:
            Lista de rutas de archivos
        """
        try:
            directory = Path(directory_path)
            if not directory.exists():
                return []

            return list(directory.glob(pattern))
        except Exception as e:
            logger.error(f"Error listando archivos en {directory_path}: {e}")
            return []

    @staticmethod
    def backup_file(file_path: Union[str, Path], 
                   backup_suffix: str = None) -> Optional[Path]:
        """
        Crea una copia de respaldo de un archivo

        Args:
            file_path: Ruta del archivo original
            backup_suffix: Sufijo para el archivo de respaldo

        Returns:
            Path del archivo de respaldo o None si hay error
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return None

            if backup_suffix is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_suffix = f"_backup_{timestamp}"

            backup_path = source_path.with_suffix(f"{backup_suffix}{source_path.suffix}")

            if FileUtils.copy_file(source_path, backup_path):
                return backup_path
            return None

        except Exception as e:
            logger.error(f"Error creando respaldo de {file_path}: {e}")
            return None