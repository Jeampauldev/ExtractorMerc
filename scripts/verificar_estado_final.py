#!/usr/bin/env python3
"""
Script para verificar el estado final después del procesamiento
"""
import os
import sys
import boto3
import json
from pathlib import Path
from sqlalchemy import text

# Añadir el directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar configuraciones
from src.config.rds_config import get_rds_engine
from src.config.env_loader import get_s3_config

def contar_archivos_s3():
    """Cuenta archivos en S3 por empresa"""
    try:
        s3_config = get_s3_config()
        s3_client = boto3.client(
            's3',
            region_name=s3_config['region'],
            aws_access_key_id=s3_config['access_key_id'],
            aws_secret_access_key=s3_config['secret_access_key']
        )
        bucket_name = s3_config['bucket_name']
        
        # Prefijos para cada empresa
        prefijos = {
            'afinia': 'Central_De_Escritos/Afinia/01_raw_data/oficina_virtual/',
            'aire': 'Central_De_Escritos/Aire/01_raw_data/oficina_virtual/'
        }
        
        conteos = {}
        total_s3 = 0
        
        for empresa, prefijo in prefijos.items():
            paginator = s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=bucket_name,
                Prefix=prefijo
            )
            
            contador = 0
            for page in page_iterator:
                if 'Contents' in page:
                    contador += len(page['Contents'])
            
            conteos[empresa] = contador
            total_s3 += contador
            print(f"Archivos en S3 para {empresa.upper()}: {contador}")
        
        print(f"Total archivos en S3: {total_s3}")
        return conteos, total_s3
        
    except Exception as e:
        print(f"Error contando archivos S3: {e}")
        return {}, 0

def contar_registros_bd():
    """Cuenta registros en la base de datos por empresa"""
    try:
        engine = get_rds_engine()
        
        with engine.connect() as conn:
            # Contar por empresa
            query = text("""
                SELECT empresa, COUNT(*) as total
                FROM data_general.registros_ov_s3 
                WHERE origen_carga = 'migracion'
                GROUP BY empresa
                ORDER BY empresa
            """)
            
            result = conn.execute(query)
            conteos = {}
            total_bd = 0
            
            for row in result:
                empresa = row.empresa
                total = row.total
                conteos[empresa] = total
                total_bd += total
                print(f"Registros en BD para {empresa.upper()}: {total}")
            
            print(f"Total registros en BD: {total_bd}")
            
            # Obtener estadísticas adicionales
            query_estado = text("""
                SELECT estado_carga, COUNT(*) as total
                FROM data_general.registros_ov_s3 
                WHERE origen_carga = 'migracion'
                GROUP BY estado_carga
            """)
            
            result_estado = conn.execute(query_estado)
            print("\nEstadísticas por estado de carga:")
            for row in result_estado:
                print(f"  {row.estado_carga}: {row.total}")
            
            return conteos, total_bd
            
    except Exception as e:
        print(f"Error contando registros BD: {e}")
        return {}, 0

def contar_archivos_locales():
    """Cuenta archivos locales disponibles para procesar"""
    try:
        # Directorios base
        dirs_base = [
            Path("data/downloads/afinia/oficina_virtual/processed"),
            Path("data/downloads/aire/oficina_virtual/processed")
        ]
        
        conteos = {}
        total_local = 0
        
        for dir_path in dirs_base:
            if dir_path.exists():
                archivos = list(dir_path.glob("*"))
                empresa = dir_path.parts[-3]  # afinia o aire
                conteos[empresa] = len(archivos)
                total_local += len(archivos)
                print(f"Archivos locales para {empresa.upper()}: {len(archivos)}")
            else:
                print(f"Directorio no encontrado: {dir_path}")
        
        print(f"Total archivos locales: {total_local}")
        return conteos, total_local
        
    except Exception as e:
        print(f"Error contando archivos locales: {e}")
        return {}, 0

def main():
    print("=== VERIFICACIÓN ESTADO FINAL ===\n")
    
    # Contar archivos locales
    print("1. Archivos locales disponibles:")
    conteos_local, total_local = contar_archivos_locales()
    
    print("\n2. Archivos subidos a S3:")
    conteos_s3, total_s3 = contar_archivos_s3()
    
    print("\n3. Registros en base de datos:")
    conteos_bd, total_bd = contar_registros_bd()
    
    print("\n=== RESUMEN COMPARATIVO ===")
    print(f"Archivos locales: {total_local}")
    print(f"Archivos en S3: {total_s3}")
    print(f"Registros en BD: {total_bd}")
    
    print("\nDiferencias:")
    if total_s3 > total_local:
        print(f"S3 tiene {total_s3 - total_local} archivos más que local (puede incluir archivos de procesamiento anterior)")
    elif total_local > total_s3:
        print(f"Local tiene {total_local - total_s3} archivos más que S3")
    else:
        print("S3 y local tienen la misma cantidad de archivos")
    
    if total_s3 > total_bd:
        print(f"S3 tiene {total_s3 - total_bd} archivos más que registros en BD")
    elif total_bd > total_s3:
        print(f"BD tiene {total_bd - total_s3} registros más que archivos en S3")
    else:
        print("S3 y BD están sincronizados")
    
    # Análisis por empresa
    print("\n=== ANÁLISIS POR EMPRESA ===")
    for empresa in ['afinia', 'aire']:
        local = conteos_local.get(empresa, 0)
        s3 = conteos_s3.get(empresa, 0)
        bd = conteos_bd.get(empresa, 0)
        
        print(f"\n{empresa.upper()}:")
        print(f"  Local: {local}")
        print(f"  S3: {s3}")
        print(f"  BD: {bd}")
        
        if s3 != bd:
            print(f"  [ADVERTENCIA]  Diferencia S3-BD: {s3 - bd}")

if __name__ == "__main__":
    main()