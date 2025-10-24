"""
Validadores para el procesador de datos de Afinia.

Este módulo contiene las clases y funciones necesarias para validar
la integridad y formato de los datos JSON extraídos de Afinia.
"""

import json
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging

from .models import AfiniaPQRData, TipoPQR, EstadoSolicitud, CanalRespuesta


class JSONValidator:
    """Validador principal para archivos JSON de Afinia."""

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

    def validate_json_file(self, file_path: str) -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
        """
        Valida un archivo JSON completo.

        Args:
            file_path: Ruta al archivo JSON

        Returns:
            Tupla con (es_válido, lista_errores, datos_json)
        """
        errors = []
        json_data = None

        try:
            # Verificar que el archivo existe
            if not Path(file_path).exists():
                errors.append(f"El archivo {file_path} no existe")
                return False, errors, None

            # Cargar y parsear JSON
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)

            # Validar estructura JSON
            structure_valid, structure_errors = self._validate_json_structure(json_data)
            if not structure_valid:
                errors.extend(structure_errors)

            # Validar contenido de datos
            content_valid, content_errors = self._validate_json_content(json_data)
            if not content_valid:
                errors.extend(content_errors)

        except json.JSONDecodeError as e:
            errors.append(f"Error al parsear JSON: {str(e)}")
        except Exception as e:
            errors.append(f"Error inesperado al validar archivo: {str(e)}")

        is_valid = len(errors) == 0
        return is_valid, errors, json_data

    def validate_json_data(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida datos JSON directamente (sin archivo).

        Args:
            json_data: Diccionario con los datos JSON

        Returns:
            Diccionario con resultado de validación
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

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'data': json_data
        }

    def _validate_json_structure(self, json_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida la estructura básica del JSON.

        Args:
            json_data: Datos JSON a validar

        Returns:
            Tupla con (es_válido, lista_errores)
        """
        errors = []

        # Campos requeridos básicos
        required_fields = [
            'nic', 'fecha', 'documento_identidad', 'nombres_apellidos',
            'numero_radicado', 'estado_solicitud', 'tipo_pqr', 'canal_respuesta'
        ]

        # Verificar campos requeridos
        for field in required_fields:
            if field not in json_data:
                errors.append(f"Campo requerido faltante: {field}")
            elif not json_data[field] or str(json_data[field]).strip() == "":
                errors.append(f"Campo requerido vacío: {field}")

        # Verificar tipos de datos básicos
        if 'fecha' in json_data and json_data['fecha']:
            if not isinstance(json_data['fecha'], str):
                errors.append("El campo 'fecha' debe ser una cadena de texto")

        if 'nic' in json_data and json_data['nic']:
            if not isinstance(json_data['nic'], str):
                errors.append("El campo 'nic' debe ser una cadena de texto")

        return len(errors) == 0, errors

    def _validate_json_content(self, json_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida el contenido específico de los campos.

        Args:
            json_data: Datos JSON a validar

        Returns:
            Tupla con (es_válido, lista_errores)
        """
        errors = []

        # Validar NIC
        if 'nic' in json_data and json_data['nic']:
            if not self.patterns['nic'].match(str(json_data['nic'])):
                errors.append(f"Formato de NIC inválido: {json_data['nic']}")

        # Validar documento de identidad
        if 'documento_identidad' in json_data and json_data['documento_identidad']:
            if not self.patterns['documento'].match(str(json_data['documento_identidad'])):
                errors.append(f"Formato de documento inválido: {json_data['documento_identidad']}")

        # Validar correo electrónico
        if 'correo_electronico' in json_data and json_data['correo_electronico']:
            if not self.patterns['email'].match(str(json_data['correo_electronico'])):
                errors.append(f"Formato de email inválido: {json_data['correo_electronico']}")

        # Validar teléfonos
        for phone_field in ['telefono', 'celular']:
            if phone_field in json_data and json_data[phone_field]:
                if not self.patterns['phone'].match(str(json_data[phone_field])):
                    errors.append(f"Formato de {phone_field} inválido: {json_data[phone_field]}")

        # Validar fecha
        if 'fecha' in json_data and json_data['fecha']:
            if not self.patterns['fecha'].match(str(json_data['fecha'])):
                errors.append(f"Formato de fecha inválido: {json_data['fecha']}")

        # Validar número de radicado
        if 'numero_radicado' in json_data and json_data['numero_radicado']:
            if not self.patterns['radicado'].match(str(json_data['numero_radicado'])):
                errors.append(f"Formato de radicado inválido: {json_data['numero_radicado']}")

        # Validar enums
        if 'tipo_pqr' in json_data and json_data['tipo_pqr']:
            if not TipoPQR.is_valid_value(json_data['tipo_pqr']):
                errors.append(f"Tipo PQR inválido: {json_data['tipo_pqr']}")

        if 'estado_solicitud' in json_data and json_data['estado_solicitud']:
            if not EstadoSolicitud.is_valid_value(json_data['estado_solicitud']):
                errors.append(f"Estado solicitud inválido: {json_data['estado_solicitud']}")

        if 'canal_respuesta' in json_data and json_data['canal_respuesta']:
            if not CanalRespuesta.is_valid_value(json_data['canal_respuesta']):
                errors.append(f"Canal respuesta inválido: {json_data['canal_respuesta']}")

        return len(errors) == 0, errors

    def validate_batch(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Valida múltiples archivos JSON.

        Args:
            file_paths: Lista de rutas de archivos

        Returns:
            Diccionario con resultados de validación por lotes
        """
        results = {
            'total_files': len(file_paths),
            'valid_files': 0,
            'invalid_files': 0,
            'file_results': {},
            'summary_errors': []
        }

        for file_path in file_paths:
            try:
                is_valid, errors, data = self.validate_json_file(file_path)
                
                results['file_results'][file_path] = {
                    'is_valid': is_valid,
                    'errors': errors,
                    'has_data': data is not None
                }

                if is_valid:
                    results['valid_files'] += 1
                else:
                    results['invalid_files'] += 1
                    results['summary_errors'].extend(errors)

            except Exception as e:
                results['file_results'][file_path] = {
                    'is_valid': False,
                    'errors': [f"Error procesando archivo: {str(e)}"],
                    'has_data': False
                }
                results['invalid_files'] += 1

        # Calcular estadísticas
        results['success_rate'] = (results['valid_files'] / results['total_files'] * 100) if results['total_files'] > 0 else 0
        results['validation_timestamp'] = datetime.now().isoformat()

        return results

    def generate_validation_report(self, validation_results: Dict[str, Any], output_path: str = None) -> str:
        """
        Genera un reporte detallado de validación.

        Args:
            validation_results: Resultados de validación
            output_path: Ruta donde guardar el reporte

        Returns:
            Contenido del reporte como string
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("REPORTE DE VALIDACIÓN - PROCESADOR AFINIA")
        report_lines.append("=" * 60)
        report_lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Resumen general
        report_lines.append("RESUMEN GENERAL:")
        report_lines.append(f"  Total archivos: {validation_results['total_files']}")
        report_lines.append(f"  Archivos válidos: {validation_results['valid_files']}")
        report_lines.append(f"  Archivos inválidos: {validation_results['invalid_files']}")
        report_lines.append(f"  Tasa de éxito: {validation_results['success_rate']:.1f}%")
        report_lines.append("")

        # Detalles por archivo
        if validation_results['file_results']:
            report_lines.append("DETALLES POR ARCHIVO:")
            for file_path, result in validation_results['file_results'].items():
                status = "[EXITOSO] VÁLIDO" if result['is_valid'] else "[ERROR] INVÁLIDO"
                report_lines.append(f"  {status}: {Path(file_path).name}")
                
                if not result['is_valid'] and result['errors']:
                    for error in result['errors']:
                        report_lines.append(f"    - {error}")
                report_lines.append("")

        # Errores más comunes
        if validation_results['summary_errors']:
            error_counts = {}
            for error in validation_results['summary_errors']:
                error_type = error.split(':')[0] if ':' in error else error
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

            report_lines.append("ERRORES MÁS COMUNES:")
            for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"  {error_type}: {count} ocurrencias")
            report_lines.append("")

        report_content = "\n".join(report_lines)

        # Guardar reporte si se especifica ruta
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                self.logger.info(f"Reporte guardado en: {output_path}")
            except Exception as e:
                self.logger.error(f"Error guardando reporte: {e}")

        return report_content


class DataIntegrityValidator:
    """Validador de integridad de datos para detectar duplicados y inconsistencias."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processed_hashes = set()
        self.duplicate_records = []

    def generate_record_hash(self, json_data: Dict[str, Any]) -> str:
        """
        Genera un hash único para un registro basado en campos clave.

        Args:
            json_data: Datos del registro

        Returns:
            Hash MD5 del registro
        """
        # Campos clave para generar hash
        key_fields = ['nic', 'documento_identidad', 'numero_radicado', 'fecha']
        
        hash_string = ""
        for field in key_fields:
            value = str(json_data.get(field, "")).strip().lower()
            hash_string += f"{field}:{value}|"

        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    def check_duplicate(self, json_data: Dict[str, Any], file_path: str = None) -> bool:
        """
        Verifica si un registro es duplicado.

        Args:
            json_data: Datos del registro
            file_path: Ruta del archivo (opcional)

        Returns:
            True si es duplicado, False si no
        """
        record_hash = self.generate_record_hash(json_data)
        
        if record_hash in self.processed_hashes:
            duplicate_info = {
                'hash': record_hash,
                'file_path': file_path,
                'nic': json_data.get('nic', 'N/A'),
                'radicado': json_data.get('numero_radicado', 'N/A'),
                'timestamp': datetime.now().isoformat()
            }
            self.duplicate_records.append(duplicate_info)
            return True
        
        self.processed_hashes.add(record_hash)
        return False

    def validate_data_consistency(self, json_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida la consistencia interna de los datos.

        Args:
            json_data: Datos a validar

        Returns:
            Tupla con (es_consistente, lista_inconsistencias)
        """
        inconsistencies = []

        # Validar consistencia entre nombres y documento
        if 'nombres_apellidos' in json_data and 'documento_identidad' in json_data:
            nombres = str(json_data['nombres_apellidos']).strip()
            documento = str(json_data['documento_identidad']).strip()
            
            if len(nombres) < 3 and len(documento) > 0:
                inconsistencies.append("Nombre muy corto para documento válido")

        # Validar consistencia entre teléfono y celular
        if 'telefono' in json_data and 'celular' in json_data:
            telefono = str(json_data['telefono']).strip()
            celular = str(json_data['celular']).strip()
            
            if telefono == celular and len(telefono) > 0:
                # Esto podría ser normal, pero lo registramos
                pass

        # Validar consistencia entre estado y fecha
        if 'estado_solicitud' in json_data and 'fecha' in json_data:
            estado = str(json_data['estado_solicitud']).lower()
            fecha_str = str(json_data['fecha'])
            
            try:
                # Intentar parsear fecha para validaciones temporales
                if '-' in fecha_str:
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                elif '/' in fecha_str:
                    fecha = datetime.strptime(fecha_str, '%d/%m/%Y')
                else:
                    fecha = None

                if fecha:
                    # Validar fechas futuras para estados cerrados
                    if 'resuelto' in estado or 'cerrado' in estado:
                        if fecha > datetime.now():
                            inconsistencies.append("Estado resuelto con fecha futura")

            except ValueError:
                inconsistencies.append("Formato de fecha no reconocido para validación de consistencia")

        return len(inconsistencies) == 0, inconsistencies

    def get_duplicate_report(self) -> Dict[str, Any]:
        """
        Genera un reporte de registros duplicados.

        Returns:
            Diccionario con información de duplicados
        """
        return {
            'total_duplicates': len(self.duplicate_records),
            'duplicate_records': self.duplicate_records,
            'unique_hashes': len(self.processed_hashes),
            'report_timestamp': datetime.now().isoformat()
        }


def validate_single_json(file_path: str) -> Tuple[bool, List[str], Optional[AfiniaPQRData]]:
    """
    Función de conveniencia para validar un solo archivo JSON.

    Args:
        file_path: Ruta al archivo JSON

    Returns:
        Tupla con (es_válido, errores, objeto_datos)
    """
    validator = JSONValidator()
    is_valid, errors, json_data = validator.validate_json_file(file_path)
    
    pqr_data = None
    if is_valid and json_data:
        try:
            pqr_data = AfiniaPQRData.from_json(json_data)
        except Exception as e:
            errors.append(f"Error creando objeto de datos: {str(e)}")
            is_valid = False

    return is_valid, errors, pqr_data


def validate_json_batch(file_paths: List[str], check_duplicates: bool = True) -> Dict[str, Any]:
    """
    Función de conveniencia para validar múltiples archivos JSON.

    Args:
        file_paths: Lista de rutas de archivos
        check_duplicates: Si verificar duplicados

    Returns:
        Diccionario con resultados de validación
    """
    validator = JSONValidator()
    integrity_validator = DataIntegrityValidator() if check_duplicates else None
    
    # Validación básica
    results = validator.validate_batch(file_paths)
    
    # Verificación de duplicados si se solicita
    if check_duplicates and integrity_validator:
        duplicate_info = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                is_duplicate = integrity_validator.check_duplicate(json_data, file_path)
                if is_duplicate:
                    duplicate_info.append(file_path)
                    
            except Exception as e:
                # Error ya capturado en validación básica
                pass
        
        results['duplicate_check'] = {
            'duplicates_found': len(duplicate_info),
            'duplicate_files': duplicate_info,
            'duplicate_report': integrity_validator.get_duplicate_report()
        }
    
    return results


def main():
    """Función principal para pruebas del validador."""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python validators.py <archivo_json> [archivo2] [archivo3] ...")
        return
    
    file_paths = sys.argv[1:]
    
    print("[EMOJI_REMOVIDO] VALIDANDO ARCHIVOS JSON DE AFINIA")
    print("=" * 50)
    
    # Validar archivos
    results = validate_json_batch(file_paths, check_duplicates=True)
    
    # Mostrar resultados
    print(f"Total archivos: {results['total_files']}")
    print(f"Válidos: {results['valid_files']}")
    print(f"Inválidos: {results['invalid_files']}")
    print(f"Tasa de éxito: {results['success_rate']:.1f}%")
    
    if 'duplicate_check' in results:
        print(f"Duplicados encontrados: {results['duplicate_check']['duplicates_found']}")
    
    # Generar reporte
    validator = JSONValidator()
    report = validator.generate_validation_report(results)
    print("\n" + report)


if __name__ == "__main__":
    main()
