#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revisor de Estructura S3 - ExtractorOV
=====================================

Script para revisar la estructura actual del bucket S3
sin intentar cargar archivos nuevos.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    from src.config.env_loader import get_s3_config
except ImportError as e:
    print(f"[ERROR] Error importando módulos: {e}")
    sys.exit(1)

def print_banner():
    """Imprimir banner del revisor"""
    print("=" * 70)
    print("[EMOJI_REMOVIDO] REVISOR DE ESTRUCTURA S3 - EXTRACTOR OV")
    print("=" * 70)
    print("Revisando estructura actual del bucket sin cargar archivos...")
    print()

def get_s3_client():
    """Obtener cliente S3 configurado"""
    s3_config = get_s3_config()
    
    return boto3.client(
        's3',
        aws_access_key_id=s3_config['access_key_id'],
        aws_secret_access_key=s3_config['secret_access_key'],
        region_name=s3_config['region']
    ), s3_config['bucket_name']

def list_bucket_structure(s3_client, bucket_name: str, max_objects: int = 100) -> Dict[str, Any]:
    """
    Listar estructura del bucket S3
    
    Args:
        s3_client: Cliente boto3 S3
        bucket_name: Nombre del bucket
        max_objects: Máximo número de objetos a listar
        
    Returns:
        Dict con información de la estructura
    """
    structure = {
        'bucket_name': bucket_name,
        'total_objects': 0,
        'total_size_bytes': 0,
        'folders': {},
        'recent_files': [],
        'file_types': {},
        'errors': []
    }
    
    try:
        print(f"[EMOJI_REMOVIDO] Analizando bucket: {bucket_name}")
        print("-" * 50)
        
        # Usar paginator para manejar buckets grandes
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=bucket_name,
            PaginationConfig={'MaxItems': max_objects}
        )
        
        objects_processed = 0
        
        for page in page_iterator:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                objects_processed += 1
                key = obj['Key']
                size = obj['Size']
                last_modified = obj['LastModified']
                
                structure['total_objects'] += 1
                structure['total_size_bytes'] += size
                
                # Analizar estructura de carpetas
                path_parts = key.split('/')
                if len(path_parts) > 1:
                    folder = path_parts[0]
                    if folder not in structure['folders']:
                        structure['folders'][folder] = {
                            'files': 0,
                            'size_bytes': 0,
                            'subfolders': set(),
                            'file_types': {}
                        }
                    
                    structure['folders'][folder]['files'] += 1
                    structure['folders'][folder]['size_bytes'] += size
                    
                    # Subfolder
                    if len(path_parts) > 2:
                        subfolder = path_parts[1]
                        structure['folders'][folder]['subfolders'].add(subfolder)
                
                # Tipo de archivo
                file_ext = Path(key).suffix.lower()
                if file_ext:
                    if file_ext not in structure['file_types']:
                        structure['file_types'][file_ext] = 0
                    structure['file_types'][file_ext] += 1
                    
                    if folder in structure['folders'] and file_ext not in structure['folders'][folder]['file_types']:
                        structure['folders'][folder]['file_types'][file_ext] = 0
                    if folder in structure['folders']:
                        structure['folders'][folder]['file_types'][file_ext] += 1
                
                # Archivos recientes (últimos 10)
                if len(structure['recent_files']) < 10:
                    structure['recent_files'].append({
                        'key': key,
                        'size': size,
                        'last_modified': last_modified.isoformat(),
                        'size_mb': round(size / 1024 / 1024, 2)
                    })
                
                # Progress cada 50 archivos
                if objects_processed % 50 == 0:
                    print(f"  Procesados: {objects_processed} objetos...")
        
        # Convertir sets a lists para JSON serialization
        for folder_info in structure['folders'].values():
            folder_info['subfolders'] = list(folder_info['subfolders'])
        
        print(f"[EXITOSO] Análisis completado: {structure['total_objects']} objetos")
        
    except ClientError as e:
        error_msg = f"Error AWS: {e.response['Error']['Code']} - {e.response['Error']['Message']}"
        structure['errors'].append(error_msg)
        print(f"[ERROR] {error_msg}")
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        structure['errors'].append(error_msg)
        print(f"[ERROR] {error_msg}")
    
    return structure

def analyze_extractorov_structure(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analizar la estructura específica para ExtractorOV
    
    Args:
        structure: Estructura del bucket
        
    Returns:
        Análisis específico para ExtractorOV
    """
    analysis = {
        'has_raw_data_folder': False,
        'pqr_folders': [],
        'company_distribution': {},
        'data_completeness': {},
        'recommendations': []
    }
    
    # Verificar carpeta raw_data
    if 'raw_data' in structure['folders']:
        analysis['has_raw_data_folder'] = True
        raw_data = structure['folders']['raw_data']
        
        # Analizar subfolders (números de reclamo)
        for subfolder in raw_data['subfolders']:
            if subfolder.startswith('RE'):
                analysis['pqr_folders'].append(subfolder)
                
                # Intentar determinar empresa por prefijo
                if subfolder.startswith('RE221'):  # Patrón típico Afinia
                    company = 'afinia'
                elif subfolder.startswith('RE222'):  # Patrón típico Aire  
                    company = 'aire'
                else:
                    company = 'unknown'
                
                if company not in analysis['company_distribution']:
                    analysis['company_distribution'][company] = 0
                analysis['company_distribution'][company] += 1
    
    # Verificar completeness de datos
    total_pqr = len(analysis['pqr_folders'])
    json_files = structure['file_types'].get('.json', 0)
    
    analysis['data_completeness'] = {
        'total_pqr_folders': total_pqr,
        'json_files': json_files,
        'avg_files_per_pqr': round(json_files / total_pqr, 2) if total_pqr > 0 else 0
    }
    
    # Generar recomendaciones
    if not analysis['has_raw_data_folder']:
        analysis['recommendations'].append("[ERROR] Falta la carpeta 'raw_data' - estructura no conforme")
    
    if total_pqr == 0:
        analysis['recommendations'].append("[ADVERTENCIA] No se encontraron carpetas de PQR (RExxxxxx)")
    elif total_pqr < 10:
        analysis['recommendations'].append(f"[ADVERTENCIA] Pocos PQRs encontrados ({total_pqr}) - posible problema de carga")
    else:
        analysis['recommendations'].append(f"[EXITOSO] Estructura correcta con {total_pqr} PQRs")
    
    if json_files == 0:
        analysis['recommendations'].append("[ERROR] No se encontraron archivos JSON")
    else:
        analysis['recommendations'].append(f"[EXITOSO] {json_files} archivos JSON encontrados")
    
    return analysis

def print_structure_report(structure: Dict[str, Any], analysis: Dict[str, Any]):
    """Imprimir reporte de estructura"""
    print("\n[DATOS] REPORTE DE ESTRUCTURA DEL BUCKET")
    print("=" * 70)
    
    # Información general
    print(f"\n[EMOJI_REMOVIDO] INFORMACIÓN GENERAL")
    print(f"Bucket: {structure['bucket_name']}")
    print(f"Total objetos: {structure['total_objects']:,}")
    print(f"Tamaño total: {structure['total_size_bytes'] / 1024 / 1024:.2f} MB")
    print(f"Carpetas principales: {len(structure['folders'])}")
    
    # Carpetas principales
    if structure['folders']:
        print(f"\n[EMOJI_REMOVIDO] CARPETAS PRINCIPALES")
        for folder, info in structure['folders'].items():
            size_mb = info['size_bytes'] / 1024 / 1024
            print(f"  [EMOJI_REMOVIDO] {folder}/")
            print(f"     - Archivos: {info['files']:,}")
            print(f"     - Tamaño: {size_mb:.2f} MB")
            print(f"     - Subcarpetas: {len(info['subfolders'])}")
            
            # Tipos de archivos en esta carpeta
            if info['file_types']:
                print(f"     - Tipos: {dict(info['file_types'])}")
    
    # Análisis específico ExtractorOV
    print(f"\n[RESULTADO] ANÁLISIS EXTRACTOROV")
    print(f"Carpeta raw_data: {'[EXITOSO] Existe' if analysis['has_raw_data_folder'] else '[ERROR] No existe'}")
    print(f"PQRs encontrados: {len(analysis['pqr_folders'])}")
    
    if analysis['company_distribution']:
        print("Distribución por empresa:")
        for company, count in analysis['company_distribution'].items():
            print(f"  - {company.upper()}: {count}")
    
    # Data completeness
    completeness = analysis['data_completeness']
    print(f"Archivos JSON: {completeness['json_files']}")
    print(f"Promedio archivos por PQR: {completeness['avg_files_per_pqr']}")
    
    # Tipos de archivos
    if structure['file_types']:
        print(f"\n[ARCHIVO] TIPOS DE ARCHIVOS")
        for ext, count in sorted(structure['file_types'].items()):
            print(f"  {ext}: {count} archivos")
    
    # Archivos recientes
    if structure['recent_files']:
        print(f"\n⏰ ARCHIVOS RECIENTES (MUESTRA)")
        for i, file_info in enumerate(structure['recent_files'][:5], 1):
            print(f"  {i}. {file_info['key']}")
            print(f"     Tamaño: {file_info['size_mb']} MB | Modificado: {file_info['last_modified']}")
    
    # Recomendaciones
    print(f"\n[INFO] RECOMENDACIONES")
    for rec in analysis['recommendations']:
        print(f"  {rec}")
    
    # Errores
    if structure['errors']:
        print(f"\n[ADVERTENCIA] ERRORES ENCONTRADOS")
        for error in structure['errors']:
            print(f"  [ERROR] {error}")

def save_structure_report(structure: Dict[str, Any], analysis: Dict[str, Any]):
    """Guardar reporte en archivo JSON"""
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'bucket_structure': structure,
        'extractorov_analysis': analysis,
        'summary': {
            'total_objects': structure['total_objects'],
            'total_size_mb': round(structure['total_size_bytes'] / 1024 / 1024, 2),
            'main_folders': len(structure['folders']),
            'pqr_count': len(analysis['pqr_folders']),
            'json_files': structure['file_types'].get('.json', 0),
            'has_raw_data': analysis['has_raw_data_folder']
        }
    }
    
    # Guardar en archivo
    report_file = Path('data/reports') / f"s3_structure_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n[EMOJI_REMOVIDO] Reporte guardado en: {report_file}")

def main():
    """Función principal"""
    print_banner()
    
    try:
        # Obtener cliente S3
        s3_client, bucket_name = get_s3_client()
        
        # Analizar estructura del bucket
        print("[EMOJI_REMOVIDO] Analizando estructura del bucket...")
        structure = list_bucket_structure(s3_client, bucket_name, max_objects=1000)
        
        # Análisis específico para ExtractorOV
        print("\n[RESULTADO] Analizando estructura para ExtractorOV...")
        analysis = analyze_extractorov_structure(structure)
        
        # Mostrar reporte
        print_structure_report(structure, analysis)
        
        # Guardar reporte
        save_structure_report(structure, analysis)
        
        print("\n[EXITOSO] Análisis completado exitosamente")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error durante el análisis: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)