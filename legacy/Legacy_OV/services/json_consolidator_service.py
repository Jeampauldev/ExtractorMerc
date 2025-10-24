#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio Consolidador de Archivos JSON
=====================================

Procesa y consolida archivos JSON de Afinia y Aire para crear datasets
unificados listos para carga a base de datos.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class ProcessingStats:
    """Estadísticas del procesamiento de archivos JSON"""
    total_files: int = 0
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    processing_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

@dataclass
class ValidationResult:
    """Resultado de validación de un registro"""
    is_valid: bool
    record: Dict
    errors: List[str]
    warnings: List[str]
    hash_record: str

class JSONConsolidatorService:
    """
    Servicio para consolidar archivos JSON de Afinia y Aire
    """
    
    def __init__(self, base_path: str = "data/downloads"):
        """
        Inicializar el servicio consolidador
        
        Args:
            base_path: Ruta base donde se encuentran los archivos JSON
        """
        self.base_path = Path(base_path)
        self.processed_path = Path("data/processed")
        self.processed_path.mkdir(parents=True, exist_ok=True)
        
        # Patrones de validación
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.phone_pattern = re.compile(r'^[\d\s\-\(\)\+]{7,15}$')
        self.nic_pattern = re.compile(r'^\d{6,10}$')
        self.document_pattern = re.compile(r'^\d{6,12}$')
        
        # Cache para deduplicación
        self.seen_hashes = set()
        self.seen_radicados = set()
        
    def scan_json_files(self, company: str) -> List[Path]:
        """
        Escanea archivos JSON de una empresa específica
        
        Args:
            company: 'afinia' o 'aire'
            
        Returns:
            Lista de rutas de archivos JSON encontrados
        """
        company_path = self.base_path / company / "oficina_virtual"
        
        if not company_path.exists():
            logger.warning(f"[2025-10-10_05:32:20][{company}][consolidator][scan_json_files][WARNING] - Directorio no encontrado: {company_path}")
            return []
        
        json_files = list(company_path.glob("*.json"))
        logger.info(f"[2025-10-10_05:32:20][{company}][consolidator][scan_json_files][INFO] - Encontrados {len(json_files)} archivos JSON")
        
        return json_files
    
    def load_json_file(self, file_path: Path) -> Tuple[List[Dict], List[str]]:
        """
        Carga y parsea un archivo JSON
        
        Args:
            file_path: Ruta del archivo JSON
            
        Returns:
            Tupla (registros, errores)
        """
        errors = []
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    records = [data]
                else:
                    errors.append(f"Formato JSON no reconocido en {file_path}")
                    
        except json.JSONDecodeError as e:
            errors.append(f"Error JSON en {file_path}: {e}")
        except Exception as e:
            errors.append(f"Error cargando {file_path}: {e}")
            
        return records, errors
    
    def normalize_data(self, record: Dict) -> Dict:
        """
        Normaliza los datos de un registro
        
        Args:
            record: Registro a normalizar
            
        Returns:
            Registro normalizado
        """
        normalized = record.copy()
        
        # Normalizar fecha
        if 'fecha' in normalized:
            normalized['fecha'] = self._normalize_date(normalized['fecha'])
        
        # Normalizar teléfonos
        for phone_field in ['telefono', 'celular']:
            if phone_field in normalized:
                normalized[phone_field] = self._normalize_phone(normalized[phone_field])
        
        # Normalizar email
        if 'correo_electronico' in normalized:
            normalized['correo_electronico'] = self._normalize_email(normalized['correo_electronico'])
        
        # Normalizar nombres
        if 'nombres_apellidos' in normalized:
            normalized['nombres_apellidos'] = self._normalize_name(normalized['nombres_apellidos'])
        
        # Normalizar NIC y documento
        for doc_field in ['nic', 'documento_identidad']:
            if doc_field in normalized:
                normalized[doc_field] = self._normalize_document(normalized[doc_field])
        
        return normalized
    
    def validate_record(self, record: Dict) -> ValidationResult:
        """
        Valida un registro individual
        
        Args:
            record: Registro a validar
            
        Returns:
            Resultado de validación
        """
        errors = []
        warnings = []
        
        # Campos obligatorios
        required_fields = ['numero_radicado', 'fecha', 'estado_solicitud']
        for field in required_fields:
            if not record.get(field):
                errors.append(f"Campo obligatorio faltante: {field}")
        
        # Validar fecha
        if record.get('fecha'):
            if not self._is_valid_date(record['fecha']):
                errors.append("Formato de fecha inválido")
        
        # Validar NIC
        if record.get('nic'):
            if not self.nic_pattern.match(str(record['nic'])):
                warnings.append("Formato NIC cuestionable")
        
        # Validar email
        if record.get('correo_electronico'):
            if not self.email_pattern.match(record['correo_electronico']):
                warnings.append("Formato email cuestionable")
        
        # Validar teléfonos
        for phone_field in ['telefono', 'celular']:
            if record.get(phone_field):
                if not self.phone_pattern.match(record[phone_field]):
                    warnings.append(f"Formato {phone_field} cuestionable")
        
        # Validar documento
        if record.get('documento_identidad'):
            if not self.document_pattern.match(str(record['documento_identidad'])):
                warnings.append("Formato documento cuestionable")
        
        # Generar hash del registro
        hash_record = self._generate_record_hash(record)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            record=record,
            errors=errors,
            warnings=warnings,
            hash_record=hash_record
        )
    
    def check_duplicates(self, record: Dict, hash_record: str) -> Tuple[bool, str]:
        """
        Verifica si un registro es duplicado
        
        Args:
            record: Registro a verificar
            hash_record: Hash del registro
            
        Returns:
            Tupla (es_duplicado, tipo_duplicado)
        """
        numero_radicado = record.get('numero_radicado', '')
        
        # Verificar duplicado por hash (exacto)
        if hash_record in self.seen_hashes:
            return True, "hash_exacto"
        
        # Verificar duplicado por numero_radicado
        if numero_radicado in self.seen_radicados:
            return True, "numero_radicado"
        
        # Agregar a cache
        self.seen_hashes.add(hash_record)
        self.seen_radicados.add(numero_radicado)
        
        return False, "ninguno"
    
    def process_company_files(self, company: str) -> Tuple[List[Dict], ProcessingStats]:
        """
        Procesa todos los archivos JSON de una empresa
        
        Args:
            company: 'afinia' o 'aire'
            
        Returns:
            Tupla (registros_válidos, estadísticas)
        """
        start_time = datetime.now()
        stats = ProcessingStats()
        valid_records = []
        
        logger.info(f"[2025-10-10_05:32:20][{company}][consolidator][process_company_files][INFO] - Iniciando procesamiento de archivos JSON")
        
        # Escanear archivos
        json_files = self.scan_json_files(company)
        stats.total_files = len(json_files)
        
        if not json_files:
            logger.warning(f"[2025-10-10_05:32:20][{company}][consolidator][process_company_files][WARNING] - No se encontraron archivos JSON")
            return valid_records, stats
        
        # Procesar cada archivo
        for file_path in json_files:
            logger.debug(f"[2025-10-10_05:32:20][{company}][consolidator][process_company_files][DEBUG] - Procesando: {file_path.name}")
            
            # Cargar archivo
            records, file_errors = self.load_json_file(file_path)
            stats.errors.extend(file_errors)
            
            if not records:
                continue
            
            # Procesar cada registro
            for record in records:
                stats.total_records += 1
                
                # Normalizar datos
                normalized_record = self.normalize_data(record)
                
                # Validar registro
                validation_result = self.validate_record(normalized_record)
                
                if not validation_result.is_valid:
                    stats.invalid_records += 1
                    stats.errors.extend([f"Registro {record.get('numero_radicado', 'sin_id')}: {error}" 
                                       for error in validation_result.errors])
                    continue
                
                # Verificar duplicados
                is_duplicate, dup_type = self.check_duplicates(
                    validation_result.record, 
                    validation_result.hash_record
                )
                
                if is_duplicate:
                    stats.duplicate_records += 1
                    logger.debug(f"[2025-10-10_05:32:20][{company}][consolidator][process_company_files][DEBUG] - Registro duplicado ({dup_type}): {record.get('numero_radicado')}")
                    continue
                
                # Agregar metadata
                final_record = validation_result.record.copy()
                final_record['hash_registro'] = validation_result.hash_record
                final_record['archivo_origen'] = file_path.name
                final_record['fecha_procesamiento'] = datetime.now().isoformat()
                final_record['warnings'] = validation_result.warnings
                
                valid_records.append(final_record)
                stats.valid_records += 1
        
        # Calcular tiempo de procesamiento
        stats.processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[2025-10-10_05:32:20][{company}][consolidator][process_company_files][INFO] - Procesamiento completado: {stats.valid_records} registros válidos de {stats.total_records} totales")
        
        return valid_records, stats
    
    def save_consolidated_dataset(self, company: str, records: List[Dict], stats: ProcessingStats) -> Dict[str, str]:
        """
        Guarda el dataset consolidado en múltiples formatos
        
        Args:
            company: 'afinia' o 'aire'
            records: Lista de registros válidos
            stats: Estadísticas del procesamiento
            
        Returns:
            Dict con las rutas de archivos generados
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_files = {}
        
        if not records:
            logger.warning(f"[2025-10-10_05:32:20][{company}][consolidator][save_consolidated_dataset][WARNING] - No hay registros para guardar")
            return output_files
        
        # Preparar DataFrame
        df = pd.DataFrame(records)
        
        # Archivo CSV para base de datos
        csv_path = self.processed_path / f"{company}_consolidated_{timestamp}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        output_files['csv'] = str(csv_path)
        
        # Archivo JSON maestro
        json_path = self.processed_path / f"{company}_master_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        output_files['json'] = str(json_path)
        
        # Reporte de estadísticas
        report_path = self.processed_path / f"{company}_processing_report_{timestamp}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(stats), f, indent=2, ensure_ascii=False)
        output_files['report'] = str(report_path)
        
        logger.info(f"[2025-10-10_05:32:20][{company}][consolidator][save_consolidated_dataset][INFO] - Dataset guardado: CSV={csv_path.name}, JSON={json_path.name}")
        
        return output_files
    
    def consolidate_company_data(self, company: str) -> Dict:
        """
        Consolida todos los datos de una empresa específica
        
        Args:
            company: 'afinia' o 'aire'
            
        Returns:
            Dict con resultados del consolidado
        """
        logger.info(f"[2025-10-10_05:32:20][{company}][consolidator][consolidate_company_data][INFO] - Iniciando consolidación de datos")
        
        # Limpiar cache para esta empresa
        self.seen_hashes.clear()
        self.seen_radicados.clear()
        
        # Procesar archivos
        valid_records, stats = self.process_company_files(company)
        
        # Guardar datasets
        output_files = self.save_consolidated_dataset(company, valid_records, stats)
        
        return {
            'company': company,
            'records_count': len(valid_records),
            'statistics': asdict(stats),
            'output_files': output_files,
            'success': len(valid_records) > 0
        }
    
    def consolidate_all_companies(self) -> Dict:
        """
        Consolida datos de todas las empresas (Afinia y Aire)
        
        Returns:
            Dict con resultados completos
        """
        logger.info("[2025-10-10_05:32:20][system][consolidator][consolidate_all_companies][INFO] - Iniciando consolidación completa")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'companies': {},
            'summary': {}
        }
        
        companies = ['afinia', 'aire']
        total_records = 0
        total_files = 0
        
        for company in companies:
            result = self.consolidate_company_data(company)
            results['companies'][company] = result
            total_records += result['records_count']
            total_files += result['statistics']['total_files']
        
        results['summary'] = {
            'total_companies': len(companies),
            'total_records': total_records,
            'total_files': total_files,
            'success': all(results['companies'][c]['success'] for c in companies)
        }
        
        logger.info(f"[2025-10-10_05:32:20][system][consolidator][consolidate_all_companies][INFO] - Consolidación completada: {total_records} registros de {total_files} archivos")
        
        return results
    
    # Métodos auxiliares privados
    
    def _normalize_date(self, date_str: str) -> str:
        """Normaliza formato de fecha"""
        if not date_str:
            return ""
        
        # Intentar múltiples formatos
        formats = [
            "%Y/%m/%d %H:%M",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y %H:%M"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(str(date_str).strip(), fmt)
                return dt.strftime("%Y/%m/%d %H:%M")
            except ValueError:
                continue
        
        return str(date_str)  # Retornar original si no se puede normalizar
    
    def _normalize_phone(self, phone: str) -> str:
        """Normaliza números de teléfono"""
        if not phone:
            return ""
        
        # Limpiar caracteres no numéricos excepto +
        cleaned = re.sub(r'[^\d+]', '', str(phone))
        return cleaned
    
    def _normalize_email(self, email: str) -> str:
        """Normaliza email"""
        if not email:
            return ""
        
        return str(email).lower().strip()
    
    def _normalize_name(self, name: str) -> str:
        """Normaliza nombres"""
        if not name:
            return ""
        
        return str(name).title().strip()
    
    def _normalize_document(self, document: str) -> str:
        """Normaliza documentos"""
        if not document:
            return ""
        
        return re.sub(r'\D', '', str(document))
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Valida formato de fecha"""
        if not date_str:
            return False
        
        formats = [
            "%Y/%m/%d %H:%M",
            "%Y-%m-%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                datetime.strptime(str(date_str).strip(), fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def _generate_record_hash(self, record: Dict) -> str:
        """Genera hash único para un registro"""
        # Campos clave para el hash
        key_fields = [
            'numero_radicado',
            'fecha',
            'tipo_pqr',
            'nic',
            'documento_identidad'
        ]
        
        hash_string = ""
        for field in key_fields:
            value = record.get(field, "")
            hash_string += f"{field}:{value}|"
        
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()


# Funciones de conveniencia para uso directo

def consolidate_afinia_data(base_path: str = "data/downloads") -> Dict:
    """
    Consolida datos de Afinia
    
    Args:
        base_path: Ruta base de archivos
        
    Returns:
        Resultado de consolidación
    """
    consolidator = JSONConsolidatorService(base_path)
    return consolidator.consolidate_company_data('afinia')


def consolidate_aire_data(base_path: str = "data/downloads") -> Dict:
    """
    Consolida datos de Aire
    
    Args:
        base_path: Ruta base de archivos
        
    Returns:
        Resultado de consolidación
    """
    consolidator = JSONConsolidatorService(base_path)
    return consolidator.consolidate_company_data('aire')


def consolidate_all_data(base_path: str = "data/downloads") -> Dict:
    """
    Consolida datos de todas las empresas
    
    Args:
        base_path: Ruta base de archivos
        
    Returns:
        Resultado completo de consolidación
    """
    consolidator = JSONConsolidatorService(base_path)
    return consolidator.consolidate_all_companies()


if __name__ == "__main__":
    # Test del servicio
    logger.info("[2025-10-10_05:32:20][system][consolidator][main][INFO] - Iniciando test del consolidador")
    
    result = consolidate_all_data()
    
    print("=" * 60)
    print("RESULTADO DEL CONSOLIDADOR DE JSON")
    print("=" * 60)
    print(f"Timestamp: {result['timestamp']}")
    print(f"Total de registros: {result['summary']['total_records']}")
    print(f"Total de archivos: {result['summary']['total_files']}")
    print(f"Éxito: {result['summary']['success']}")
    
    for company, data in result['companies'].items():
        print(f"\n{company.upper()}:")
        print(f"  - Registros: {data['records_count']}")
        print(f"  - Archivos: {data['statistics']['total_files']}")
        print(f"  - Duplicados: {data['statistics']['duplicate_records']}")
        print(f"  - Inválidos: {data['statistics']['invalid_records']}")
        print(f"  - Tiempo: {data['statistics']['processing_time']:.2f}s")
        
        if data['output_files']:
            print("  - Archivos generados:")
            for file_type, path in data['output_files'].items():
                print(f"    {file_type}: {Path(path).name}")