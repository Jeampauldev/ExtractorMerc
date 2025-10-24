#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de Carga S3 - ExtractorOV
==================================

Este servicio maneja la carga de archivos (PDFs, JSON, imágenes) a AWS S3
desde los datos procesados por los extractores de Afinia y Aire.

Características:
- Carga automática a buckets organizados por empresa
- Metadatos detallados para cada archivo
- Reintentos automáticos en caso de errores
- Validación de archivos antes de carga
- Encriptación y compresión opcional
- Logging detallado de todas las operaciones
"""

import logging
import boto3
import mimetypes
import hashlib
import gzip
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from botocore.exceptions import ClientError, BotoCoreError
from boto3.s3.transfer import TransferConfig

# Importar configuración de entorno
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.env_loader import get_s3_config


@dataclass
class S3UploadResult:
    """Resultado de una carga a S3"""
    success: bool
    file_path: str = ""
    s3_bucket: str = ""
    s3_key: str = ""
    s3_url: str = ""
    file_size_bytes: int = 0
    upload_duration_seconds: float = 0.0
    error_message: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    upload_timestamp: str = ""


@dataclass
class S3BatchResult:
    """Resultado de carga masiva a S3"""
    total_files: int = 0
    successful_uploads: int = 0
    failed_uploads: int = 0
    total_size_bytes: int = 0
    total_duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    upload_details: List[S3UploadResult] = field(default_factory=list)


class S3UploaderService:
    """
    Servicio para carga de archivos a AWS S3
    
    Maneja la carga eficiente y organizada de archivos generados por
    los extractores a buckets S3 estructurados por empresa y tipo.
    """
    
    # Extensiones permitidas por defecto
    DEFAULT_ALLOWED_EXTENSIONS = {
        '.pdf', '.json', '.jpg', '.jpeg', '.png', '.gif', 
        '.txt', '.csv', '.xlsx', '.docx', '.zip'
    }
    
    # Estructura de carpetas en S3
    S3_FOLDER_STRUCTURE = {
        'afinia': {
            'pdfs': 'afinia/oficina_virtual/pdfs',
            'data': 'afinia/oficina_virtual/data',
            'screenshots': 'afinia/oficina_virtual/screenshots',
            'reports': 'afinia/reports',
            'logs': 'afinia/logs'
        },
        'aire': {
            'pdfs': 'aire/oficina_virtual/pdfs',
            'data': 'aire/oficina_virtual/data', 
            'screenshots': 'aire/oficina_virtual/screenshots',
            'reports': 'aire/reports',
            'logs': 'aire/logs'
        },
        'general': {
            'reports': 'general/reports',
            'logs': 'general/logs',
            'backups': 'general/backups'
        }
    }
    
    def __init__(self, config: Optional[Dict] = None, 
                 allowed_extensions: Optional[set] = None,
                 enable_compression: bool = False):
        """
        Inicializa el servicio de S3
        
        Args:
            config: Configuración personalizada de S3
            allowed_extensions: Extensiones de archivo permitidas
            enable_compression: Si habilitar compresión gzip para archivos de texto
        """
        self.config = config or get_s3_config()
        self.allowed_extensions = allowed_extensions or self.DEFAULT_ALLOWED_EXTENSIONS
        self.enable_compression = enable_compression
        self.logger = logging.getLogger(__name__)
        
        # Cliente S3 y configuración de transferencia
        self.s3_client = None
        self.transfer_config = None
        
        # Validar configuración
        self._validate_config()
        
        # Inicializar cliente S3
        self._initialize_s3_client()
        
        self.logger.info(f"S3UploaderService inicializado para bucket: {self.config.get('bucket_name')}")
    
    def _validate_config(self) -> None:
        """Valida la configuración de S3"""
        required_fields = ['bucket_name', 'access_key_id', 'secret_access_key', 'region']
        missing = [field for field in required_fields if not self.config.get(field)]
        
        if missing:
            raise ValueError(f"Configuración de S3 incompleta. Campos faltantes: {missing}")
    
    def _initialize_s3_client(self) -> None:
        """Inicializa el cliente S3 y configuración de transferencia"""
        try:
            # Crear cliente S3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config['access_key_id'],
                aws_secret_access_key=self.config['secret_access_key'],
                region_name=self.config['region']
            )
            
            # Configurar transferencia para archivos grandes
            self.transfer_config = TransferConfig(
                multipart_threshold=1024 * 25,  # 25 MB
                max_concurrency=10,
                multipart_chunksize=1024 * 25,
                use_threads=True
            )
            
            self.logger.info(f"Cliente S3 inicializado para región: {self.config['region']}")
            
        except Exception as e:
            self.logger.error(f"Error inicializando cliente S3: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión a S3 y permisos del bucket
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            self.logger.info("Probando conexión a S3...")
            
            # Intentar listar objetos en el bucket (solo para probar permisos)
            response = self.s3_client.list_objects_v2(
                Bucket=self.config['bucket_name'],
                MaxKeys=1
            )
            
            self.logger.info("EXITOSO Conexión a S3 exitosa")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                self.logger.error(f"ERROR Bucket no existe: {self.config['bucket_name']}")
            elif error_code == 'AccessDenied':
                self.logger.error(f"ERROR Acceso denegado al bucket: {self.config['bucket_name']}")
            else:
                self.logger.error(f"ERROR Error S3: {error_code}")
            return False
        except Exception as e:
            self.logger.error(f"ERROR Error conectando a S3: {e}")
            return False
    
    def generate_s3_key(self, service_type: str, file_type: str, 
                       filename: str, date_prefix: bool = True) -> str:
        """
        Genera la clave S3 (ruta) para un archivo
        
        Args:
            service_type: 'afinia', 'aire' o 'general'
            file_type: Tipo de archivo ('pdfs', 'data', 'screenshots', etc.)
            filename: Nombre del archivo
            date_prefix: Si agregar prefijo de fecha
            
        Returns:
            str: Clave S3 completa
        """
        # Obtener estructura base
        if service_type not in self.S3_FOLDER_STRUCTURE:
            service_type = 'general'
        
        folder_structure = self.S3_FOLDER_STRUCTURE[service_type]
        if file_type not in folder_structure:
            file_type = 'data'  # Por defecto
        
        base_path = folder_structure[file_type]
        
        # Agregar prefijo de fecha si se solicita
        if date_prefix:
            date_str = datetime.now().strftime('%Y/%m/%d')
            s3_key = f"{base_path}/{date_str}/{filename}"
        else:
            s3_key = f"{base_path}/{filename}"
        
        return s3_key
    
    def generate_file_hash(self, file_path: str) -> str:
        """
        Genera hash MD5 de un archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            str: Hash MD5 del archivo
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Error generando hash para {file_path}: {e}")
            return ""
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Valida que un archivo sea apto para carga
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_error)
        """
        try:
            path = Path(file_path)
            
            # Verificar que existe
            if not path.exists():
                return False, "Archivo no encontrado"
            
            # Verificar que es un archivo
            if not path.is_file():
                return False, "La ruta no es un archivo"
            
            # Verificar tamaño (máximo 5GB)
            size_gb = path.stat().st_size / (1024 ** 3)
            if size_gb > 5:
                return False, f"Archivo demasiado grande: {size_gb:.2f}GB (máximo 5GB)"
            
            # Verificar extensión
            if path.suffix.lower() not in self.allowed_extensions:
                return False, f"Extensión no permitida: {path.suffix}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Error validando archivo: {e}"
    
    def prepare_metadata(self, file_path: str, service_type: str,
                        custom_metadata: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Prepara metadatos para el archivo
        
        Args:
            file_path: Ruta del archivo
            service_type: Tipo de servicio
            custom_metadata: Metadatos personalizados adicionales
            
        Returns:
            Dict[str, str]: Metadatos preparados
        """
        try:
            path = Path(file_path)
            file_stats = path.stat()
            
            metadata = {
                'original-filename': path.name,
                'file-size': str(file_stats.st_size),
                'upload-timestamp': datetime.now().isoformat(),
                'service-type': service_type,
                'file-extension': path.suffix.lower(),
                'uploader': 'extractorov-modular',
                'file-hash': self.generate_file_hash(file_path)
            }
            
            # Agregar metadatos personalizados
            if custom_metadata:
                # AWS S3 requiere que las claves de metadata sean lowercase
                for key, value in custom_metadata.items():
                    metadata[key.lower()] = str(value)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error preparando metadatos para {file_path}: {e}")
            return {'error': str(e)}
    
    def compress_file(self, file_path: str) -> Optional[str]:
        """
        Comprime un archivo usando gzip (opcional para archivos de texto)
        
        Args:
            file_path: Ruta del archivo original
            
        Returns:
            str: Ruta del archivo comprimido o None si no se pudo comprimir
        """
        if not self.enable_compression:
            return None
        
        path = Path(file_path)
        
        # Solo comprimir archivos de texto
        text_extensions = {'.json', '.txt', '.csv', '.log'}
        if path.suffix.lower() not in text_extensions:
            return None
        
        try:
            compressed_path = str(path) + '.gz'
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Verificar que la compresión fue efectiva
            original_size = Path(file_path).stat().st_size
            compressed_size = Path(compressed_path).stat().st_size
            
            if compressed_size < original_size * 0.9:  # Al menos 10% de reducción
                self.logger.info(f"Archivo comprimido: {original_size} -> {compressed_size} bytes")
                return compressed_path
            else:
                # La compresión no fue efectiva, eliminar archivo comprimido
                Path(compressed_path).unlink()
                return None
                
        except Exception as e:
            self.logger.error(f"Error comprimiendo archivo {file_path}: {e}")
            return None
    
    def upload_file(self, file_path: str, service_type: str, file_type: str = 'data',
                   custom_filename: Optional[str] = None,
                   custom_metadata: Optional[Dict[str, str]] = None,
                   max_retries: int = 3) -> S3UploadResult:
        """
        Carga un archivo a S3
        
        Args:
            file_path: Ruta del archivo local
            service_type: Tipo de servicio ('afinia', 'aire', 'general')
            file_type: Tipo de archivo ('pdfs', 'data', 'screenshots', etc.)
            custom_filename: Nombre personalizado en S3 (opcional)
            custom_metadata: Metadatos adicionales
            max_retries: Número máximo de reintentos
            
        Returns:
            S3UploadResult: Resultado de la carga
        """
        start_time = datetime.now()
        result = S3UploadResult(success=False, file_path=file_path)
        
        try:
            # Validar archivo
            is_valid, error_msg = self.validate_file(file_path)
            if not is_valid:
                result.error_message = f"Validación fallida: {error_msg}"
                return result
            
            # Determinar archivo a cargar (original o comprimido)
            upload_file_path = file_path
            compressed_path = self.compress_file(file_path)
            if compressed_path:
                upload_file_path = compressed_path
            
            # Determinar nombre del archivo en S3
            path = Path(upload_file_path)
            s3_filename = custom_filename or path.name
            s3_key = self.generate_s3_key(service_type, file_type, s3_filename)
            
            # Preparar metadatos
            metadata = self.prepare_metadata(file_path, service_type, custom_metadata)
            
            # Preparar argumentos de carga
            content_type, _ = mimetypes.guess_type(upload_file_path)
            extra_args = {
                'Metadata': metadata,
                'ContentType': content_type or 'application/octet-stream',
                'ServerSideEncryption': 'AES256',  # Encriptación por defecto
                'StorageClass': 'STANDARD_IA'  # Acceso infrecuente por defecto
            }
            
            # Realizar carga con reintentos
            self.logger.info(f"Cargando: {path.name} -> s3://{self.config['bucket_name']}/{s3_key}")
            
            for attempt in range(max_retries):
                try:
                    self.s3_client.upload_file(
                        upload_file_path,
                        self.config['bucket_name'],
                        s3_key,
                        ExtraArgs=extra_args,
                        Config=self.transfer_config
                    )
                    
                    # Carga exitosa
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    file_size = Path(upload_file_path).stat().st_size
                    
                    result.success = True
                    result.s3_bucket = self.config['bucket_name']
                    result.s3_key = s3_key
                    result.s3_url = f"s3://{self.config['bucket_name']}/{s3_key}"
                    result.file_size_bytes = file_size
                    result.upload_duration_seconds = duration
                    result.metadata = metadata
                    result.upload_timestamp = end_time.isoformat()
                    
                    self.logger.info(
                        f"EXITOSO Archivo cargado: {s3_filename} "
                        f"({file_size/1024/1024:.2f} MB en {duration:.2f}s)"
                    )
                    
                    break
                    
                except (ClientError, BotoCoreError) as e:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Intento {attempt + 1} fallido, reintentando... Error: {e}")
                        import time
                        time.sleep(2 ** attempt)  # Backoff exponencial
                    else:
                        raise e
            
            # Limpiar archivo comprimido temporal si se creó
            if compressed_path and Path(compressed_path).exists():
                Path(compressed_path).unlink()
        
        except Exception as e:
            result.error_message = str(e)
            self.logger.error(f"ERROR Error cargando {file_path}: {e}")
        
        finally:
            result.upload_duration_seconds = (datetime.now() - start_time).total_seconds()
        
        return result
    
    def upload_directory(self, directory_path: str, service_type: str,
                        file_type: str = 'data', recursive: bool = True,
                        file_patterns: Optional[List[str]] = None) -> S3BatchResult:
        """
        Carga todos los archivos de un directorio a S3
        
        Args:
            directory_path: Ruta del directorio
            service_type: Tipo de servicio
            file_type: Tipo de archivo
            recursive: Si buscar recursivamente en subdirectorios
            file_patterns: Patrones de archivos a incluir (ej: ['*.pdf', '*.json'])
            
        Returns:
            S3BatchResult: Resultado de la carga masiva
        """
        start_time = datetime.now()
        result = S3BatchResult()
        
        try:
            # Encontrar archivos
            directory = Path(directory_path)
            if not directory.exists():
                result.errors.append(f"Directorio no encontrado: {directory_path}")
                return result
            
            files_to_upload = []
            
            if recursive:
                if file_patterns:
                    for pattern in file_patterns:
                        files_to_upload.extend(directory.glob(f"**/{pattern}"))
                else:
                    files_to_upload.extend(directory.glob("**/*"))
            else:
                if file_patterns:
                    for pattern in file_patterns:
                        files_to_upload.extend(directory.glob(pattern))
                else:
                    files_to_upload.extend(directory.glob("*"))
            
            # Filtrar solo archivos (no directorios)
            files_to_upload = [f for f in files_to_upload if f.is_file()]
            result.total_files = len(files_to_upload)
            
            self.logger.info(f"Iniciando carga de {result.total_files} archivos desde {directory_path}")
            
            # Cargar archivos uno por uno
            for file_path in files_to_upload:
                try:
                    upload_result = self.upload_file(
                        str(file_path), service_type, file_type
                    )
                    
                    result.upload_details.append(upload_result)
                    
                    if upload_result.success:
                        result.successful_uploads += 1
                        result.total_size_bytes += upload_result.file_size_bytes
                    else:
                        result.failed_uploads += 1
                        result.errors.append(f"{file_path.name}: {upload_result.error_message}")
                        
                except Exception as e:
                    result.failed_uploads += 1
                    result.errors.append(f"{file_path.name}: {e}")
                    self.logger.error(f"Error cargando {file_path}: {e}")
            
        except Exception as e:
            result.errors.append(f"Error procesando directorio: {e}")
            self.logger.error(f"Error en carga masiva: {e}")
        
        finally:
            result.total_duration_seconds = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(
            f"Carga masiva completada: {result.successful_uploads}/{result.total_files} exitosos "
            f"en {result.total_duration_seconds:.2f}s"
        )
        
        return result
    
    def get_s3_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del bucket S3
        
        Returns:
            Dict[str, Any]: Estadísticas del bucket
        """
        stats = {
            'bucket_name': self.config['bucket_name'],
            'total_objects': 0,
            'total_size_bytes': 0,
            'services': {},
            'error': None
        }
        
        try:
            # Contar objetos por servicio
            for service_type in self.S3_FOLDER_STRUCTURE.keys():
                service_stats = {
                    'object_count': 0,
                    'total_size': 0,
                    'file_types': {}
                }
                
                # Listar objetos con prefijo del servicio
                paginator = self.s3_client.get_paginator('list_objects_v2')
                page_iterator = paginator.paginate(
                    Bucket=self.config['bucket_name'],
                    Prefix=f"{service_type}/"
                )
                
                for page in page_iterator:
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            service_stats['object_count'] += 1
                            service_stats['total_size'] += obj['Size']
                            
                            # Clasificar por tipo de archivo
                            key_parts = obj['Key'].split('/')
                            if len(key_parts) > 2:
                                file_type = key_parts[2]  # Ej: afinia/oficina_virtual/pdfs
                                if file_type not in service_stats['file_types']:
                                    service_stats['file_types'][file_type] = {
                                        'count': 0, 'size': 0
                                    }
                                service_stats['file_types'][file_type]['count'] += 1
                                service_stats['file_types'][file_type]['size'] += obj['Size']
                
                stats['services'][service_type] = service_stats
                stats['total_objects'] += service_stats['object_count']
                stats['total_size_bytes'] += service_stats['total_size']
        
        except Exception as e:
            stats['error'] = str(e)
            self.logger.error(f"Error obteniendo estadísticas S3: {e}")
        
        return stats


# Funciones de utilidad

def upload_file_to_s3(file_path: str, service_type: str, file_type: str = 'data',
                     config: Optional[Dict] = None) -> S3UploadResult:
    """
    Función de utilidad para cargar un archivo a S3
    
    Args:
        file_path: Ruta del archivo
        service_type: Tipo de servicio
        file_type: Tipo de archivo
        config: Configuración S3 personalizada
        
    Returns:
        S3UploadResult: Resultado de la carga
    """
    uploader = S3UploaderService(config)
    return uploader.upload_file(file_path, service_type, file_type)


def upload_directory_to_s3(directory_path: str, service_type: str, file_type: str = 'data',
                          config: Optional[Dict] = None) -> S3BatchResult:
    """
    Función de utilidad para cargar un directorio completo a S3
    
    Args:
        directory_path: Ruta del directorio
        service_type: Tipo de servicio
        file_type: Tipo de archivo
        config: Configuración S3 personalizada
        
    Returns:
        S3BatchResult: Resultado de la carga masiva
    """
    uploader = S3UploaderService(config)
    return uploader.upload_directory(directory_path, service_type, file_type)


if __name__ == "__main__":
    # CLI para el servicio S3
    import argparse
    
    parser = argparse.ArgumentParser(description='Servicio de Carga S3 - ExtractorOV')
    parser.add_argument('--test-connection', action='store_true', help='Probar conexión a S3')
    parser.add_argument('--upload-file', help='Cargar archivo específico')
    parser.add_argument('--upload-directory', help='Cargar directorio completo')
    parser.add_argument('--service-type', '-s', choices=['afinia', 'aire', 'general'], 
                       default='general', help='Tipo de servicio')
    parser.add_argument('--file-type', '-t', default='data',
                       help='Tipo de archivo (pdfs, data, screenshots, etc.)')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas del bucket')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear servicio
    try:
        uploader = S3UploaderService()
    except Exception as e:
        print(f"ERROR Error inicializando servicio S3: {e}")
        exit(1)
    
    if args.test_connection:
        print("VERIFICANDO Probando conexión a S3...")
        success = uploader.test_connection()
        print(f"Resultado: {'EXITOSO Éxito' if success else 'ERROR Error'}")
    
    elif args.upload_file:
        print(f" Cargando archivo: {args.upload_file}")
        result = uploader.upload_file(
            args.upload_file, args.service_type, args.file_type
        )
        
        if result.success:
            print(f"EXITOSO Carga exitosa:")
            print(f"   S3 URL: {result.s3_url}")
            print(f"   Tamaño: {result.file_size_bytes/1024/1024:.2f} MB")
            print(f"   Duración: {result.upload_duration_seconds:.2f}s")
        else:
            print(f"ERROR Error: {result.error_message}")
    
    elif args.upload_directory:
        print(f"ARCHIVOS Cargando directorio: {args.upload_directory}")
        result = uploader.upload_directory(
            args.upload_directory, args.service_type, args.file_type
        )
        
        print(f"EXITOSO Carga masiva completada:")
        print(f"   Total archivos: {result.total_files}")
        print(f"   Exitosos: {result.successful_uploads}")
        print(f"   Fallidos: {result.failed_uploads}")
        print(f"   Tamaño total: {result.total_size_bytes/1024/1024:.2f} MB")
        print(f"   Duración: {result.total_duration_seconds:.2f}s")
        
        if result.errors:
            print("ERROR Errores:")
            for error in result.errors[:5]:
                print(f"   • {error}")
            if len(result.errors) > 5:
                print(f"   ... y {len(result.errors) - 5} más")
    
    elif args.stats:
        print("PROCESADOS Obteniendo estadísticas de S3...")
        stats = uploader.get_s3_stats()
        
        if stats['error']:
            print(f"ERROR Error: {stats['error']}")
        else:
            print(f"Bucket: {stats['bucket_name']}")
            print(f"Total objetos: {stats['total_objects']}")
            print(f"Tamaño total: {stats['total_size_bytes']/1024/1024/1024:.2f} GB")
            
            for service, service_stats in stats['services'].items():
                if service_stats['object_count'] > 0:
                    print(f"\n{service.upper()}:")
                    print(f"  Archivos: {service_stats['object_count']}")
                    print(f"  Tamaño: {service_stats['total_size']/1024/1024:.2f} MB")
                    for file_type, type_stats in service_stats['file_types'].items():
                        print(f"    {file_type}: {type_stats['count']} archivos")
    
    else:
        parser.print_help()