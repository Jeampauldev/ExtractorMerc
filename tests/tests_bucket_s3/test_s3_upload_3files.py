#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de Carga S3 - 3 Archivos
=============================

Script para probar la carga de solo 3 archivos JSON a S3
usando la estructura adaptada al bucket existente.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.services.aws_s3_service import AWSS3Service, S3UploadResult
except ImportError as e:
    print(f"[ERROR] Error importando módulos: {e}")
    sys.exit(1)

def print_banner():
    """Imprimir banner del test"""
    print("=" * 70)
    print("🧪 TEST DE CARGA S3 - 3 ARCHIVOS")
    print("=" * 70)
    print("Probando carga de archivos JSON con estructura adaptada...")
    print()

def find_sample_json_files(max_files: int = 3) -> List[Path]:
    """
    Buscar archivos JSON de muestra para el test
    
    Args:
        max_files: Máximo número de archivos a encontrar
        
    Returns:
        Lista de rutas de archivos JSON
    """
    print("[EMOJI_REMOVIDO] Buscando archivos JSON de muestra...")
    
    json_files = []
    
    # Buscar en directorio de archivos procesados
    search_paths = [
        Path("data/downloads/afinia/oficina_virtual/processed"),
        Path("data/downloads/aire/oficina_virtual/processed")
    ]
    
    for search_path in search_paths:
        if search_path.exists():
            # Buscar archivos JSON
            for json_file in search_path.glob("*_data_*.json"):
                if len(json_files) >= max_files:
                    break
                json_files.append(json_file)
                print(f"  [EMOJI_REMOVIDO] Encontrado: {json_file.name}")
            
            if len(json_files) >= max_files:
                break
    
    if not json_files:
        print("[ERROR] No se encontraron archivos JSON para el test")
        return []
    
    print(f"[EMOJI_REMOVIDO] Total archivos para test: {len(json_files)}")
    return json_files[:max_files]

def extract_pqr_info(json_file: Path) -> Dict[str, str]:
    """
    Extraer información del PQR desde el nombre del archivo
    
    Args:
        json_file: Archivo JSON
        
    Returns:
        Dict con empresa y numero_reclamo_sgc
    """
    filename = json_file.name
    
    # Extraer número de reclamo del formato: RE123456789_data_20251008_093221.json
    parts = filename.split('_')
    numero_reclamo_sgc = parts[0] if parts else filename.replace('.json', '')
    
    # Determinar empresa por el path
    if 'afinia' in str(json_file).lower():
        empresa = 'afinia'
    elif 'aire' in str(json_file).lower():
        empresa = 'aire'
    else:
        # Intentar determinar por el número de reclamo
        if numero_reclamo_sgc.startswith('RE221'):
            empresa = 'afinia'
        elif numero_reclamo_sgc.startswith('RE222'):
            empresa = 'aire'
        else:
            empresa = 'afinia'  # Default
    
    return {
        'empresa': empresa,
        'numero_reclamo_sgc': numero_reclamo_sgc
    }

def test_s3_upload(json_files: List[Path]) -> Dict[str, any]:
    """
    Probar la carga de archivos a S3
    
    Args:
        json_files: Lista de archivos para cargar
        
    Returns:
        Resultados del test
    """
    print("\n[INICIANDO] INICIANDO TEST DE CARGA A S3")
    print("-" * 50)
    
    s3_service = AWSS3Service()
    results = {
        'total_files': len(json_files),
        'successful_uploads': 0,
        'failed_uploads': 0,
        'pre_existing_files': 0,
        'details': [],
        'errors': []
    }
    
    for i, json_file in enumerate(json_files, 1):
        print(f"\n[ARCHIVO] [{i}/{len(json_files)}] Procesando: {json_file.name}")
        
        try:
            # Extraer información del PQR
            pqr_info = extract_pqr_info(json_file)
            print(f"  [EMOJI_REMOVIDO] Empresa: {pqr_info['empresa']}")
            print(f"  [EMOJI_REMOVIDO] PQR: {pqr_info['numero_reclamo_sgc']}")
            
            # Generar la key S3 esperada
            expected_key = s3_service._generate_s3_key(
                pqr_info['empresa'], 
                json_file.name, 
                pqr_info['numero_reclamo_sgc']
            )
            print(f"  [EMOJI_REMOVIDO] S3 Key: {expected_key}")
            
            # Intentar subir el archivo
            result = s3_service.upload_file_with_registry(
                file_path=json_file,
                empresa=pqr_info['empresa'],
                numero_reclamo_sgc=pqr_info['numero_reclamo_sgc']
            )
            
            # Procesar resultado
            if result.success:
                print(f"  [EXITOSO] Éxito: {result.upload_source}")
                
                if result.upload_source == "bot":
                    results['successful_uploads'] += 1
                else:
                    results['pre_existing_files'] += 1
                
                results['details'].append({
                    'file': json_file.name,
                    'status': 'success',
                    'upload_source': result.upload_source,
                    's3_key': result.s3_key,
                    's3_url': result.s3_url,
                    'registry_id': result.registry_id
                })
            else:
                print(f"  [ERROR] Error: {result.error_message}")
                results['failed_uploads'] += 1
                results['errors'].append(f"{json_file.name}: {result.error_message}")
                
                results['details'].append({
                    'file': json_file.name,
                    'status': 'failed',
                    'error': result.error_message
                })
        
        except Exception as e:
            print(f"  [ERROR] Error inesperado: {e}")
            results['failed_uploads'] += 1
            results['errors'].append(f"{json_file.name}: {str(e)}")
    
    return results

def print_test_summary(results: Dict[str, any]):
    """Imprimir resumen del test"""
    print("\n" + "=" * 70)
    print("[DATOS] RESUMEN DEL TEST")
    print("=" * 70)
    
    print(f"Total archivos procesados: {results['total_files']}")
    print(f"[EXITOSO] Subidas exitosas (nuevos): {results['successful_uploads']}")
    print(f"[EMOJI_REMOVIDO] Archivos pre-existentes: {results['pre_existing_files']}")
    print(f"[ERROR] Errores: {results['failed_uploads']}")
    
    if results['errors']:
        print(f"\n[ADVERTENCIA] ERRORES ENCONTRADOS:")
        for error in results['errors']:
            print(f"  - {error}")
    
    # Mostrar detalles de archivos exitosos
    successful_files = [d for d in results['details'] if d['status'] == 'success']
    if successful_files:
        print(f"\n[EXITOSO] ARCHIVOS PROCESADOS EXITOSAMENTE:")
        for detail in successful_files:
            print(f"  [ARCHIVO] {detail['file']}")
            print(f"      Status: {detail['upload_source']}")
            print(f"      S3 Key: {detail['s3_key']}")
            if detail.get('registry_id'):
                print(f"      Registry ID: {detail['registry_id']}")

def verify_s3_structure():
    """Verificar la estructura en S3 después de la carga"""
    print(f"\n[EMOJI_REMOVIDO] VERIFICANDO ESTRUCTURA S3...")
    print("-" * 50)
    
    # Ejecutar el revisor de estructura
    try:
        from config.review_s3_structure import get_s3_client, list_bucket_structure, analyze_extractorov_structure
        
        s3_client, bucket_name = get_s3_client()
        structure = list_bucket_structure(s3_client, bucket_name, max_objects=50)
        
        print(f"[DATOS] Objetos totales en bucket: {structure['total_objects']}")
        
        # Buscar archivos JSON recién subidos
        json_count = structure['file_types'].get('.json', 0)
        print(f"[ARCHIVO] Archivos JSON en bucket: {json_count}")
        
        # Mostrar estructura de Central_De_Escritos
        if 'Central_De_Escritos' in structure['folders']:
            central_folder = structure['folders']['Central_De_Escritos']
            print(f"[EMOJI_REMOVIDO] Central_De_Escritos: {central_folder['files']} archivos")
            print(f"   Subcarpetas: {len(central_folder['subfolders'])}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Error verificando estructura: {e}")
        return False

def main():
    """Función principal del test"""
    print_banner()
    
    try:
        # 1. Buscar archivos de muestra
        json_files = find_sample_json_files(max_files=3)
        if not json_files:
            print("[ERROR] No se pueden realizar tests sin archivos JSON")
            return False
        
        # 2. Probar carga a S3
        results = test_s3_upload(json_files)
        
        # 3. Mostrar resumen
        print_test_summary(results)
        
        # 4. Verificar estructura S3
        if results['successful_uploads'] > 0 or results['pre_existing_files'] > 0:
            verify_s3_structure()
        
        # 5. Resultado final
        if results['failed_uploads'] == 0:
            print(f"\n[COMPLETADO] TEST COMPLETADO EXITOSAMENTE")
            print("[EXITOSO] Todos los archivos se procesaron correctamente")
            print("[EXITOSO] Estructura S3 adaptada funciona correctamente")
            return True
        else:
            print(f"\n[ADVERTENCIA] TEST COMPLETADO CON ERRORES")
            print(f"[ERROR] {results['failed_uploads']} archivos fallaron")
            return False
    
    except Exception as e:
        print(f"\n[ERROR] Error durante el test: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)