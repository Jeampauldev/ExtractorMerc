#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Configuración AWS S3 para ExtractorOV
==============================================

Script interactivo para configurar las credenciales AWS S3
y validar la conectividad con el bucket.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Tuple, Optional

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("[ERROR] boto3 no está instalado. Instalando...")
    os.system("pip install boto3")
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

def print_banner():
    """Imprimir banner del script"""
    print("=" * 70)
    print("[CONFIGURANDO] CONFIGURACIÓN AWS S3 - EXTRACTOR OV")
    print("=" * 70)
    print("Este script te ayudará a configurar AWS S3 paso a paso.")
    print("Necesitarás tener:")
    print("[EMOJI_REMOVIDO] Access Key ID de AWS")
    print("[EMOJI_REMOVIDO] Secret Access Key de AWS") 
    print("[EMOJI_REMOVIDO] Nombre del bucket S3")
    print("[EMOJI_REMOVIDO] Región de AWS")
    print("-" * 70)

def get_user_input(prompt: str, default: str = None, required: bool = True) -> str:
    """
    Obtener input del usuario con validación
    
    Args:
        prompt: Mensaje para mostrar al usuario
        default: Valor por defecto
        required: Si el campo es requerido
        
    Returns:
        Valor ingresado por el usuario
    """
    while True:
        if default:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "
            
        value = input(full_prompt).strip()
        
        if not value and default:
            return default
        elif not value and required:
            print("[ERROR] Este campo es requerido. Por favor ingresa un valor.")
            continue
        elif not value and not required:
            return ""
        else:
            return value

def collect_aws_credentials() -> Dict[str, str]:
    """
    Recopilar credenciales AWS del usuario
    
    Returns:
        Dict con las credenciales AWS
    """
    print("\n[EMOJI_REMOVIDO] PASO 1: CREDENCIALES AWS")
    print("-" * 40)
    
    credentials = {}
    
    # Access Key ID
    while True:
        access_key = get_user_input("AWS Access Key ID")
        if access_key.startswith("AKIA") and len(access_key) >= 16:
            credentials['AWS_ACCESS_KEY_ID'] = access_key
            break
        else:
            print("[ERROR] El Access Key ID debe comenzar con 'AKIA' y tener al menos 16 caracteres.")
    
    # Secret Access Key
    while True:
        secret_key = get_user_input("AWS Secret Access Key")
        if len(secret_key) >= 20:
            credentials['AWS_SECRET_ACCESS_KEY'] = secret_key
            break
        else:
            print("[ERROR] El Secret Access Key debe tener al menos 20 caracteres.")
    
    # Región
    region = get_user_input("AWS Region", default="us-east-1")
    credentials['AWS_REGION'] = region
    
    # Bucket name
    bucket_name = get_user_input("Nombre del bucket S3", default="extractorov-data")
    credentials['AWS_S3_BUCKET_NAME'] = bucket_name
    
    # Configuración adicional
    credentials['S3_BASE_PATH'] = get_user_input("Ruta base en S3", default="raw_data", required=False)
    credentials['AWS_S3_IAM_USER'] = get_user_input("Usuario IAM", default="extractorov-bot", required=False)
    
    return credentials

def test_aws_connection(credentials: Dict[str, str]) -> Tuple[bool, str]:
    """
    Probar la conexión a AWS S3
    
    Args:
        credentials: Credenciales AWS
        
    Returns:
        Tupla (éxito, mensaje)
    """
    try:
        # Crear cliente S3 con las credenciales
        s3_client = boto3.client(
            's3',
            aws_access_key_id=credentials['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=credentials['AWS_SECRET_ACCESS_KEY'],
            region_name=credentials['AWS_REGION']
        )
        
        bucket_name = credentials['AWS_S3_BUCKET_NAME']
        
        # Test 1: Listar buckets
        print("  [EMOJI_REMOVIDO] Verificando acceso a AWS...")
        response = s3_client.list_buckets()
        bucket_names = [bucket['Name'] for bucket in response['Buckets']]
        
        # Test 2: Verificar si el bucket existe
        print(f"  [EMOJI_REMOVIDO]  Verificando bucket '{bucket_name}'...")
        if bucket_name not in bucket_names:
            return False, f"[ERROR] El bucket '{bucket_name}' no existe o no tienes acceso."
        
        # Test 3: Verificar permisos de escritura
        print("  [EMOJI_REMOVIDO]  Verificando permisos de escritura...")
        test_key = "test/connectivity_test.txt"
        test_content = f"Test de conectividad - {os.getenv('USER', 'ExtractorOV')} - {Path(__file__).name}"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content,
            ContentType='text/plain'
        )
        
        # Test 4: Verificar permisos de lectura
        print("  [EMOJI_REMOVIDO] Verificando permisos de lectura...")
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
        content = response['Body'].read().decode('utf-8')
        
        # Test 5: Limpiar archivo de prueba
        print("  🧹 Limpiando archivo de prueba...")
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        
        return True, "[EXITOSO] Conexión a AWS S3 exitosa. Todos los permisos verificados."
        
    except NoCredentialsError:
        return False, "[ERROR] Credenciales AWS no válidas o no encontradas."
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            return False, f"[ERROR] El bucket '{credentials['AWS_S3_BUCKET_NAME']}' no existe."
        elif error_code == 'AccessDenied':
            return False, "[ERROR] Acceso denegado. Verifica los permisos IAM."
        else:
            return False, f"[ERROR] Error AWS: {error_code} - {e.response['Error']['Message']}"
    except Exception as e:
        return False, f"[ERROR] Error inesperado: {str(e)}"

def save_credentials_to_env(credentials: Dict[str, str]) -> bool:
    """
    Guardar credenciales en archivo .env
    
    Args:
        credentials: Credenciales a guardar
        
    Returns:
        True si se guardó exitosamente
    """
    try:
        env_dir = Path(__file__).parent / "env"
        env_dir.mkdir(exist_ok=True)
        env_file = env_dir / ".env"
        
        # Leer archivo existente si existe
        existing_vars = {}
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_vars[key] = value
        
        # Actualizar con nuevas credenciales
        existing_vars.update(credentials)
        
        # Escribir archivo actualizado
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# ===============================================\n")
            f.write("# EXTRACTOROV - CONFIGURACIÓN DE ENTORNO\n")
            f.write("# ===============================================\n")
            f.write("# Generado automáticamente - No editar a mano\n")
            f.write(f"# Fecha: {os.environ.get('DATE', 'N/A')}\n")
            f.write("# ===============================================\n\n")
            
            f.write("# AWS S3 Configuration\n")
            aws_keys = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION', 
                       'AWS_S3_BUCKET_NAME', 'S3_BASE_PATH', 'AWS_S3_IAM_USER']
            for key in aws_keys:
                if key in existing_vars:
                    f.write(f"{key}={existing_vars[key]}\n")
            
            f.write("\n# Database Configuration\n")
            db_keys = ['RDS_HOST', 'RDS_DATABASE', 'RDS_USERNAME', 'RDS_PASSWORD', 'RDS_PORT']
            for key in db_keys:
                if key in existing_vars:
                    f.write(f"{key}={existing_vars[key]}\n")
            
            f.write("\n# Oficinas Virtuales\n")
            ov_keys = ['OV_AFINIA_USERNAME', 'OV_AFINIA_PASSWORD', 'OV_AIRE_USERNAME', 'OV_AIRE_PASSWORD']
            for key in ov_keys:
                if key in existing_vars:
                    f.write(f"{key}={existing_vars[key]}\n")
            
            f.write("\n# App Configuration\n")
            app_keys = ['APP_ENV', 'DEBUG', 'LOG_LEVEL']
            for key in app_keys:
                if key in existing_vars:
                    f.write(f"{key}={existing_vars[key]}\n")
                else:
                    # Valores por defecto
                    defaults = {'APP_ENV': 'production', 'DEBUG': 'false', 'LOG_LEVEL': 'INFO'}
                    if key in defaults:
                        f.write(f"{key}={defaults[key]}\n")
        
        print(f"[EXITOSO] Credenciales guardadas en: {env_file}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error guardando credenciales: {e}")
        return False

def main():
    """Función principal del script"""
    print_banner()
    
    try:
        # Paso 1: Recopilar credenciales
        credentials = collect_aws_credentials()
        
        # Paso 2: Probar conexión
        print(f"\n🧪 PASO 2: PROBANDO CONEXIÓN AWS S3")
        print("-" * 40)
        success, message = test_aws_connection(credentials)
        print(message)
        
        if not success:
            print("\n[ERROR] La configuración falló. Por favor revisa tus credenciales y permisos.")
            return False
        
        # Paso 3: Guardar configuración
        print(f"\n[EMOJI_REMOVIDO] PASO 3: GUARDANDO CONFIGURACIÓN")
        print("-" * 40)
        if save_credentials_to_env(credentials):
            print("[EXITOSO] Configuración guardada exitosamente.")
        else:
            print("[ERROR] Error guardando la configuración.")
            return False
        
        # Paso 4: Resumen final
        print(f"\n[COMPLETADO] CONFIGURACIÓN COMPLETADA")
        print("=" * 70)
        print("[EXITOSO] AWS S3 configurado correctamente")
        print("[EXITOSO] Credenciales guardadas")
        print("[EXITOSO] Conectividad verificada")
        print()
        print("Próximos pasos:")
        print("1. Ejecutar tests de carga: python -m src.services.aws_s3_service")
        print("2. Configurar scheduler automático")
        print("3. Implementar monitoreo")
        print("=" * 70)
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n[ADVERTENCIA]  Configuración cancelada por el usuario.")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)