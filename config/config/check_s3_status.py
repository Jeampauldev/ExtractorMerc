#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador de Estado AWS S3 - ExtractorOV
==========================================

Script para verificar el estado actual de la configuración AWS S3
y mostrar información sobre el bucket y archivos.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.services.aws_s3_service import AWSS3Service, S3Stats
    from src.config.env_loader import get_s3_config, validate_credentials
except ImportError as e:
    print(f"[ERROR] Error importando módulos: {e}")
    print("Asegúrate de estar en el directorio raíz del proyecto")
    sys.exit(1)

def print_banner():
    """Imprimir banner del verificador"""
    print("=" * 70)
    print("[EMOJI_REMOVIDO] VERIFICADOR DE ESTADO AWS S3 - EXTRACTOR OV")
    print("=" * 70)
    print("Verificando configuración y conectividad de AWS S3...")
    print()

def check_environment_variables() -> Dict:
    """
    Verificar variables de entorno AWS
    
    Returns:
        Dict con el estado de las variables
    """
    print("[EMOJI_REMOVIDO] VERIFICANDO VARIABLES DE ENTORNO")
    print("-" * 50)
    
    s3_config = get_s3_config()
    validation = validate_credentials()
    
    status = {
        'has_credentials': validation.get('s3', False),
        'config': s3_config,
        'missing_vars': []
    }
    
    # Verificar cada variable requerida
    required_vars = ['access_key_id', 'secret_access_key', 'bucket_name']
    for var in required_vars:
        if not s3_config.get(var):
            status['missing_vars'].append(var)
    
    # Mostrar estado
    print(f"[EMOJI_REMOVIDO] Access Key ID: {'Configurado' if s3_config.get('access_key_id') else '[ERROR] Faltante'}")
    print(f"[EMOJI_REMOVIDO] Secret Key: {'Configurado' if s3_config.get('secret_access_key') else '[ERROR] Faltante'}")
    print(f"[EMOJI_REMOVIDO] Bucket Name: {s3_config.get('bucket_name') or '[ERROR] No configurado'}")
    print(f"[EMOJI_REMOVIDO] Región: {s3_config.get('region') or 'us-east-1 (default)'}")
    print(f"[EMOJI_REMOVIDO] Base Path: {s3_config.get('S3_BASE_PATH') or 'raw_data (default)'}")
    
    return status

def check_s3_service() -> Dict:
    """
    Verificar servicio S3 y conectividad
    
    Returns:
        Dict con el estado del servicio
    """
    print("\n[EMOJI_REMOVIDO] VERIFICANDO SERVICIO AWS S3")
    print("-" * 50)
    
    status = {
        'service_initialized': False,
        'simulated_mode': False,
        'connectivity_test': False,
        'error_message': None
    }
    
    try:
        # Inicializar servicio S3
        s3_service = AWSS3Service()
        status['service_initialized'] = True
        status['simulated_mode'] = s3_service.is_simulated_mode
        
        print(f"[EMOJI_REMOVIDO] Servicio S3: {'Inicializado' if status['service_initialized'] else '[ERROR] Error'}")
        print(f"[EMOJI_REMOVIDO] Modo: {'Simulado' if status['simulated_mode'] else 'Real (AWS)'}")
        
        # Test de conectividad si no está en modo simulado
        if not status['simulated_mode']:
            # Intentar test básico
            try:
                # Verificar si podemos acceder al bucket
                exists, metadata = s3_service.check_file_exists_in_s3("test/connectivity_check.txt")
                status['connectivity_test'] = True
                print("[EMOJI_REMOVIDO] Conectividad: AWS S3 accesible")
            except Exception as e:
                status['error_message'] = str(e)
                print(f"[ADVERTENCIA]  Conectividad: Error - {e}")
        else:
            print("[ADVERTENCIA]  En modo simulado - No se puede verificar conectividad real")
        
        return status
        
    except Exception as e:
        status['error_message'] = str(e)
        print(f"[ERROR] Error inicializando servicio S3: {e}")
        return status

def check_bucket_contents() -> Dict:
    """
    Verificar contenido del bucket S3
    
    Returns:
        Dict con información del bucket
    """
    print("\n[EMOJI_REMOVIDO] VERIFICANDO CONTENIDO DEL BUCKET")
    print("-" * 50)
    
    status = {
        'accessible': False,
        'file_count': 0,
        'total_size': 0,
        'structure': {},
        'recent_files': [],
        'error_message': None
    }
    
    try:
        s3_service = AWSS3Service()
        
        if s3_service.is_simulated_mode:
            print("[ADVERTENCIA]  Modo simulado - No se puede verificar contenido real del bucket")
            return status
        
        # Obtener estadísticas del registro S3
        registry_stats = s3_service.get_s3_registry_stats()
        
        if 'error' in registry_stats:
            status['error_message'] = registry_stats['error']
            print(f"[ERROR] Error obteniendo estadísticas: {registry_stats['error']}")
        else:
            status['accessible'] = True
            totals = registry_stats.get('totals', {})
            status['file_count'] = totals.get('total_files', 0)
            status['total_size'] = totals.get('total_size_bytes', 0)
            
            print(f"[EMOJI_REMOVIDO] Archivos registrados: {status['file_count']}")
            print(f"[EMOJI_REMOVIDO] Tamaño total: {status['total_size'] / 1024 / 1024:.2f} MB")
            
            # Mostrar estadísticas por empresa
            by_company = registry_stats.get('by_company_status', {})
            for company, company_stats in by_company.items():
                print(f"  [DATOS] {company.upper()}:")
                for status_key, data in company_stats.items():
                    print(f"    - {status_key}: {data.get('count', 0)} archivos")
        
        return status
        
    except Exception as e:
        status['error_message'] = str(e)
        print(f"[ERROR] Error verificando bucket: {e}")
        return status

def show_configuration_instructions():
    """Mostrar instrucciones de configuración"""
    print("\n[EMOJI_REMOVIDO]  INSTRUCCIONES DE CONFIGURACIÓN")
    print("=" * 70)
    print()
    print("Para configurar AWS S3 correctamente:")
    print()
    print("1[EMOJI_REMOVIDO]⃣  Ejecutar el script de configuración:")
    print("   python config/setup_aws_s3.py")
    print()
    print("2[EMOJI_REMOVIDO]⃣  O configurar manualmente las variables de entorno:")
    print("   - AWS_ACCESS_KEY_ID=tu_access_key")
    print("   - AWS_SECRET_ACCESS_KEY=tu_secret_key")
    print("   - AWS_REGION=us-east-1")
    print("   - AWS_S3_BUCKET_NAME=extractorov-data")
    print()
    print("3[EMOJI_REMOVIDO]⃣  Verificar permisos IAM:")
    print("   - s3:GetObject, s3:PutObject, s3:DeleteObject")
    print("   - s3:ListBucket, s3:GetBucketLocation")
    print()
    print("4[EMOJI_REMOVIDO]⃣  Probar la configuración:")
    print("   python config/check_s3_status.py")

def main():
    """Función principal"""
    print_banner()
    
    # Verificar variables de entorno
    env_status = check_environment_variables()
    
    # Verificar servicio S3
    service_status = check_s3_service()
    
    # Verificar contenido del bucket (si es posible)
    bucket_status = check_bucket_contents()
    
    # Resumen final
    print("\n[DATOS] RESUMEN DE ESTADO")
    print("=" * 70)
    
    all_good = True
    
    if env_status['has_credentials']:
        print("[EXITOSO] Variables de entorno configuradas")
    else:
        print("[ERROR] Variables de entorno faltantes")
        all_good = False
    
    if service_status['service_initialized']:
        if service_status['simulated_mode']:
            print("[ADVERTENCIA]  Servicio S3 en modo simulado")
            all_good = False
        else:
            print("[EXITOSO] Servicio S3 inicializado (modo real)")
    else:
        print("[ERROR] Servicio S3 no inicializado")
        all_good = False
    
    if bucket_status['accessible']:
        print(f"[EXITOSO] Bucket accesible con {bucket_status['file_count']} archivos")
    elif service_status['simulated_mode']:
        print("[ADVERTENCIA]  Bucket no verificado (modo simulado)")
    else:
        print("[ERROR] Bucket no accesible")
        all_good = False
    
    print()
    if all_good:
        print("[COMPLETADO] ¡TODO CONFIGURADO CORRECTAMENTE!")
        print("AWS S3 está listo para usar.")
    else:
        print("[ADVERTENCIA]  CONFIGURACIÓN INCOMPLETA")
        show_configuration_instructions()
    
    print("=" * 70)

if __name__ == "__main__":
    main()