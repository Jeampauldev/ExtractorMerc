"""
Validadores para el procesador de datos de Aire.

Este módulo contiene las clases y funciones necesarias para validar
la integridad y formato de los datos JSON extraídos de Aire.
"""

import json
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging

from .models import AirePQRData, TipoPQR, EstadoSolicitud, CanalRespuesta


class JSONValidator:
    """Validador principal para archivos JSON de Aire."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_validation_patterns()

    def _setup_validation_patterns(self):
        """Configura los patrones de validación regex."""
        self.patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'phone': re.compile(r'^[\d\s\-\(\)\+]{7,15}$'),
            'nic': re.compile(r'^[\w\d\-]{5,20}$'),
            'documento': re.compile(r'^[\d]{6,15}$'),
            'radicado': re.compile(r'^[\w\d\-]{5,30}$'),
            'fecha': re.compile(r'^\d{2}/\d{2}/\d{4}$|^\d{4}-\d{2}-\d{2}$|^\d{2}-\d{2}-\d{4}$')
        }

    def validate_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Valida un archivo JSON completo.

        Args:
            file_path: Ruta al archivo JSON

        Returns:
            Diccionario con resultado de validación
        """
        result = {
            'valid': False,
            'errors': [],
            'data': None,
            'file_path': file_path
        }

        try:
            # Verificar que el archivo existe
            if not Path(file_path).exists():
                result['errors'].append(f"El archivo {file_path} no existe")
                return result

            # Cargar y parsear JSON
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)

            result['data'] = json_data

            # Validar estructura JSON
            structure_valid, structure_errors = self._validate_json_structure(json_data)
            if not structure_valid:
                result['errors'].extend(structure_errors)

            # Validar contenido de datos
            content_valid, content_errors = self._validate_json_content(json_data)
            if not content_valid:
                result['errors'].extend(content_errors)

            result['valid'] = len(result['errors']) == 0

        except json.JSONDecodeError as e:
            result['errors'].append(f"Error al parsear JSON: {str(e)}")
        except Exception as e:
            result['errors'].append(f"Error inesperado al validar archivo: {str(e)}")

        return result

    def validate_data(self, json_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida datos JSON directamente.

        Args:
            json_data: Datos JSON a validar

        Returns:
            Tupla con (es_válido, lista_errores)
        """
        errors = []

        # Validar estructura
        structure_valid, structure_errors = self._validate_json_structure(json_data)
        if not structure_valid:
            errors.extend(structure_errors)

        # Validar contenido
        content_valid, content_errors = self._validate_json_content(json_data)
        if not content_valid:
            errors.extend(content_errors)

        return len(errors) == 0, errors

    def _validate_json_structure(self, json_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida la estructura básica del JSON.

        Args:
            json_data: Datos JSON a validar

        Returns:
            Tupla con (es_válido, lista_errores)
        """
        errors = []
        required_fields = [
            'nic', 'fecha', 'documento_identidad', 'nombres_apellidos',
            'numero_radicado', 'estado_solicitud'
        ]

        # Verificar campos requeridos
        for field in required_fields:
            if field not in json_data:
                errors.append(f"Campo requerido faltante: {field}")

        # Verificar tipos de datos
        string_fields = [
            'nic', 'fecha', 'documento_identidad', 'nombres_apellidos',
            'email', 'telefono', 'direccion', 'tipo_pqr',
            'canal_respuesta', 'numero_radicado', 'estado_solicitud',
            'descripcion'
        ]

        for field in string_fields:
            if field in json_data and not isinstance(json_data[field], str):
                errors.append(f"Campo {field} debe ser string, recibido: {type(json_data[field])}")

        return len(errors) == 0, errors

    def _validate_json_content(self, json_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida el contenido específico de los campos JSON.

        Args:
            json_data: Datos JSON a validar

        Returns:
            Tupla con (es_válido, lista_errores)
        """
        errors = []

        # Validar NIC
        if 'nic' in json_data:
            nic = json_data['nic']
            if not self.patterns['nic'].match(str(nic)):
                errors.append(f"NIC inválido: {nic}")

        # Validar documento de identidad
        if 'documento_identidad' in json_data:
            doc = json_data['documento_identidad']
            if doc and not self.patterns['documento'].match(str(doc)):
                errors.append(f"Documento de identidad inválido: {doc}")

        # Validar email
        if 'email' in json_data and json_data['email']:
            email = json_data['email']
            if not self.patterns['email'].match(email):
                errors.append(f"Email inválido: {email}")

        # Validar teléfono
        if 'telefono' in json_data and json_data['telefono']:
            telefono = json_data['telefono']
            if not self.patterns['phone'].match(str(telefono)):
                errors.append(f"Teléfono inválido: {telefono}")

        # Validar fecha
        if 'fecha' in json_data:
            fecha = json_data['fecha']
            if not self.patterns['fecha'].match(str(fecha)):
                errors.append(f"Fecha inválida: {fecha}")

        # Validar número de radicado
        if 'numero_radicado' in json_data:
            radicado = json_data['numero_radicado']
            if not self.patterns['radicado'].match(str(radicado)):
                errors.append(f"Número de radicado inválido: {radicado}")

        # Validar enums
        if 'tipo_pqr' in json_data and json_data['tipo_pqr']:
            try:
                TipoPQR(json_data['tipo_pqr'])
            except ValueError:
                errors.append(f"Tipo PQR inválido: {json_data['tipo_pqr']}")

        if 'estado_solicitud' in json_data and json_data['estado_solicitud']:
            try:
                EstadoSolicitud(json_data['estado_solicitud'])
            except ValueError:
                errors.append(f"Estado solicitud inválido: {json_data['estado_solicitud']}")

        if 'canal_respuesta' in json_data and json_data['canal_respuesta']:
            try:
                CanalRespuesta(json_data['canal_respuesta'])
            except ValueError:
                errors.append(f"Canal respuesta inválido: {json_data['canal_respuesta']}")

        return len(errors) == 0, errors

    def validate_batch(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Valida múltiples archivos JSON.

        Args:
            file_paths: Lista de rutas de archivos

        Returns:
            Diccionario con resultados de validación
        """
        results = {
            'total_files': len(file_paths),
            'valid_files': 0,
            'invalid_files': 0,
            'files': []
        }

        for file_path in file_paths:
            file_result = self.validate_json_file(file_path)
            results['files'].append(file_result)

            if file_result['valid']:
                results['valid_files'] += 1
            else:
                results['invalid_files'] += 1

        results['success_rate'] = (results['valid_files'] / results['total_files'] * 100) if results['total_files'] > 0 else 0

        return results


class DuplicateDetector:
    """Detector de archivos JSON duplicados."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.seen_hashes = set()
        self.seen_records = {}

    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calcula el hash MD5 de un archivo.

        Args:
            file_path: Ruta del archivo

        Returns:
            Hash MD5 del archivo o None si hay error
        """
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculando hash de {file_path}: {e}")
            return None

    def calculate_content_hash(self, json_data: Dict[str, Any]) -> str:
        """
        Calcula un hash basado en el contenido relevante del JSON.

        Args:
            json_data: Datos JSON

        Returns:
            Hash del contenido
        """
        # Campos clave para identificar duplicados
        key_fields = ['nic', 'numero_radicado', 'fecha', 'documento_identidad']
        
        content_string = ""
        for field in key_fields:
            if field in json_data:
                content_string += str(json_data[field])

        return hashlib.md5(content_string.encode('utf-8')).hexdigest()

    def is_duplicate_file(self, file_path: str) -> bool:
        """
        Verifica si un archivo es duplicado basado en su hash.

        Args:
            file_path: Ruta del archivo

        Returns:
            True si es duplicado, False en caso contrario
        """
        file_hash = self.calculate_file_hash(file_path)
        if file_hash is None:
            return False

        if file_hash in self.seen_hashes:
            return True

        self.seen_hashes.add(file_hash)
        return False

    def is_duplicate_content(self, json_data: Dict[str, Any], file_path: str = "") -> bool:
        """
        Verifica si el contenido JSON es duplicado.

        Args:
            json_data: Datos JSON
            file_path: Ruta del archivo (opcional)

        Returns:
            True si es duplicado, False en caso contrario
        """
        content_hash = self.calculate_content_hash(json_data)

        if content_hash in self.seen_records:
            self.logger.warning(f"Contenido duplicado detectado: {file_path}")
            return True

        self.seen_records[content_hash] = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        }
        return False

    def get_duplicate_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de duplicados detectados.

        Returns:
            Diccionario con estadísticas
        """
        return {
            'total_unique_files': len(self.seen_hashes),
            'total_unique_records': len(self.seen_records),
            'duplicate_files_detected': 0,  # Se incrementaría en uso real
            'duplicate_records_detected': 0  # Se incrementaría en uso real
        }


def validate_single_json(file_path: str) -> Dict[str, Any]:
    """
    Función de conveniencia para validar un solo archivo JSON.

    Args:
        file_path: Ruta del archivo JSON

    Returns:
        Diccionario con resultado de validación
    """
    validator = JSONValidator()
    return validator.validate_json_file(file_path)


def validate_directory(directory_path: str, pattern: str = "*.json") -> Dict[str, Any]:
    """
    Valida todos los archivos JSON en un directorio.

    Args:
        directory_path: Ruta del directorio
        pattern: Patrón de archivos a buscar

    Returns:
        Diccionario con resultados de validación
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        return {
            'error': f"El directorio {directory_path} no existe",
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'files': []
        }

    json_files = list(directory.glob(pattern))
    file_paths = [str(f) for f in json_files]

    validator = JSONValidator()
    return validator.validate_batch(file_paths)


def detect_duplicates_in_directory(directory_path: str, pattern: str = "*.json") -> Dict[str, Any]:
    """
    Detecta archivos duplicados en un directorio.

    Args:
        directory_path: Ruta del directorio
        pattern: Patrón de archivos a buscar

    Returns:
        Diccionario con resultados de detección
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        return {
            'error': f"El directorio {directory_path} no existe",
            'duplicates': []
        }

    json_files = list(directory.glob(pattern))
    detector = DuplicateDetector()
    
    duplicates = []
    for json_file in json_files:
        if detector.is_duplicate_file(str(json_file)):
            duplicates.append(str(json_file))

    return {
        'total_files': len(json_files),
        'duplicate_files': len(duplicates),
        'duplicates': duplicates,
        'stats': detector.get_duplicate_stats()
    }


def create_validation_report(results: Dict[str, Any], output_file: str = None) -> str:
    """
    Crea un reporte detallado de validación.

    Args:
        results: Resultados de validación
        output_file: Archivo de salida (opcional)

    Returns:
        Contenido del reporte como string
    """
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("REPORTE DE VALIDACIÓN DE ARCHIVOS JSON")
    report_lines.append("=" * 60)
    report_lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # Resumen general
    report_lines.append("RESUMEN GENERAL:")
    report_lines.append(f"  Total de archivos: {results.get('total_files', 0)}")
    report_lines.append(f"  Archivos válidos: {results.get('valid_files', 0)}")
    report_lines.append(f"  Archivos inválidos: {results.get('invalid_files', 0)}")
    report_lines.append(f"  Tasa de éxito: {results.get('success_rate', 0):.1f}%")
    report_lines.append("")

    # Detalles de archivos inválidos
    invalid_files = [f for f in results.get('files', []) if not f.get('valid', True)]
    if invalid_files:
        report_lines.append("ARCHIVOS CON ERRORES:")
        for file_info in invalid_files:
            report_lines.append(f"  [ARCHIVO] {Path(file_info['file_path']).name}")
            for error in file_info.get('errors', []):
                report_lines.append(f"    [ERROR] {error}")
            report_lines.append("")

    report_content = "\n".join(report_lines)

    # Guardar en archivo si se especifica
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
        except Exception as e:
            logging.error(f"Error guardando reporte en {output_file}: {e}")

    return report_content
