#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Simple de Limpieza S3
============================

Script para eliminar archivos de prueba del bucket S3.
"""

import os
import sys
import boto3
from pathlib import Path
from botocore.exceptions import ClientError

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

def get_s3_credentials():
    """Obtener credenciales S3 desde variables de entorno"""
    return {
        'access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
        'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
        'bucket_name': os.getenv('S3_BUCKET_NAME')
    }

def clean_s3_test_files():
    """Limpiar archivos de prueba del bucket S3"""
    print("🧹 INICIANDO LIMPIEZA DE ARCHIVOS DE PRUEBA S3")
    print("=" * 60)
    
    # Obtener credenciales
    s3_config = get_s3_credentials()
    
    if not all([s3_config['access_key_id'], s3_config['secret_access_key'], s3_config['bucket_name']]):
        print("❌ ERROR: Faltan credenciales S3 en variables de entorno")
        return False
    
    try:
        # Crear cliente S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=s3_config['access_key_id'],
            aws_secret_access_key=s3_config['secret_access_key'],
            region_name=s3_config['region']
        )
        
        bucket_name = s3_config['bucket_name']
        print(f"📦 Bucket: {bucket_name}")
        
        # Prefijos a limpiar (archivos de prueba recientes)
        prefixes_to_clean = [
            'Central_De_Escritos/Afinia/01_raw_data/oficina_virtual/',
            'Central_De_Escritos/Air-e/01_raw_data/oficina_virtual/'
        ]
        
        total_deleted = 0
        
        for prefix in prefixes_to_clean:
            print(f"\n🔍 Buscando archivos en: {prefix}")
            
            # Listar objetos con el prefijo
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                print(f"   ✅ No hay archivos en {prefix}")
                continue
            
            objects_to_delete = []
            for obj in response['Contents']:
                key = obj['Key']
                # Solo eliminar archivos de prueba (con timestamp reciente)
                if any(test_pattern in key for test_pattern in ['test_', '20251013', 'prueba']):
                    objects_to_delete.append({'Key': key})
                    print(f"   🗑️  Marcado para eliminar: {key}")
            
            # Eliminar objetos
            if objects_to_delete:
                delete_response = s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': objects_to_delete}
                )
                
                deleted_count = len(delete_response.get('Deleted', []))
                total_deleted += deleted_count
                print(f"   ✅ Eliminados {deleted_count} archivos de {prefix}")
                
                if 'Errors' in delete_response:
                    for error in delete_response['Errors']:
                        print(f"   ❌ Error eliminando {error['Key']}: {error['Message']}")
        
        print(f"\n🎉 LIMPIEZA COMPLETADA")
        print(f"📊 Total archivos eliminados: {total_deleted}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Error AWS: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    success = clean_s3_test_files()
    sys.exit(0 if success else 1)