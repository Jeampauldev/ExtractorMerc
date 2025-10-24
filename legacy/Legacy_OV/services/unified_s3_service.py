#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio S3 Unificado - ExtractorOV
===================================

Servicio consolidado que unifica todas las funcionalidades de S3:
- Carga de archivos con múltiples estructuras de rutas
- Registro en base de datos
- Verificación de archivos existentes
- Carga masiva e incremental
- Metadatos detallados y trazabilidad completa

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Diciembre 2024
"""

import os
import json
import hashlib
import logging
import mimetypes
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum

import boto3
from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError
from boto3.s3.transfer import TransferConfig
from sqlalchemy import text
from sqlalchemy.orm import Session

# Importar configuraciones
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config.env_loader import get_s3_config
from config.rds_config import RDSConnectionManager

logger = logging.getLogger(__name__)

class S3PathStructure(Enum):
    """Tipos de estructura de rutas S3"""
    LEGACY = "legacy"  # {empresa}/oficina_virtual/{tipo}/{fecha}/{archivo}
    CENTRAL = "central"  # Central_De_Escritos/{empresa}/01_raw_data/oficina_virtual/{numero_reclamo_sgc}/{archivo}
    SIMPLE = "simple"  # {empresa}/{tipo}/{archivo}

@dataclass
class S3UploadResult:
    """Resultado unificado de carga a S3"""
    success: bool
    s3_key: str = ""
    s3_url: str = ""
    file_hash: str = ""
    file_size: int = 0
    error_message: str = ""
    upload_source: str = "bot"  # bot, pre_existing
    registry_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0

@dataclass
class S3BatchResult:
    """Resultado de carga masiva"""
    total_files: int = 0
    successful_uploads: int = 0
    failed_uploads: int = 0
    skipped_files: int = 0
    total_size: int = 0
    processing_time: float = 0.0
    results: List[S3UploadResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

@dataclass
class S3Stats:
    """Estadísticas del bucket S3"""
    total_objects: int = 0
    total_size: int = 0
    total_size_bytes: int = 0  # Agregado para compatibilidad con post_processing_service
    uploaded_files: int = 0  # Agregado para compatibilidad con post_processing_service
    pre_existing_files: int = 0  # Agregado para compatibilidad
    error_files: int = 0  # Agregado para compatibilidad
    processing_time: float = 0.0  # Agregado para compatibilidad con post_processing_service
    errors: List[str] = None  # Agregado para compatibilidad con post_processing_service
    by_company: Dict[str, int] = field(default_factory=dict)
    by_type: Dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class UnifiedS3Service:
    """
    Servicio S3 unificado que consolida todas las funcionalidades
    """
    
    # Extensiones permitidas
    ALLOWED_EXTENSIONS = {
        '.pdf', '.json', '.jpg', '.jpeg', '.png', '.gif', 
        '.txt', '.csv', '.xlsx', '.docx', '.zip', '.log'
    }
    
    # Mapeo de empresas
    COMPANY_MAPPING = {
        'afinia': 'afinia',
        'aire': 'aire',
        'general': 'general'
    }
    
    # Tipos de archivo soportados
    FILE_TYPES = {
        'pdfs', 'data', 'screenshots', 'reports', 'logs', 
        'attachments', 'json', 'images', 'documents'
    }
    
    def __init__(self, bucket_name: str = None, path_structure: S3PathStructure = S3PathStructure.CENTRAL):
        """
        Inicializar servicio S3 unificado
        
        Args:
            bucket_name: Nombre del bucket S3
            path_structure: Estructura de rutas a usar
        """
        # Configuración desde variables de entorno
        self.config = get_s3_config() if get_s3_config() else {}
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = bucket_name or os.getenv('AWS_S3_BUCKET_NAME', 'extractorov-data')
        
        # Estructura de rutas
        self.path_structure = path_structure
        
        # Cliente S3
        self._s3_client = None
        
        # Manager de BD
        self.rds_manager = RDSConnectionManager()
        
        # Configuración de transferencia
        self.transfer_config = TransferConfig(
            multipart_threshold=1024 * 25,  # 25MB
            max_concurrency=10,
            multipart_chunksize=1024 * 25,
            use_threads=True
        )
        
        logger.info(f"[unified_s3][init] Inicializado - Bucket: {self.bucket_name}, Estructura: {path_structure.value}")
    
    @property
    def s3_client(self):
        """Cliente S3 lazy-loaded"""
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key,
                    region_name=self.aws_region
                )
                logger.info(f"[unified_s3][client] Cliente S3 inicializado para región {self.aws_region}")
            except Exception as e:
                logger.error(f"[unified_s3][client] Error inicializando cliente S3: {e}")
                raise
        return self._s3_client
    
    def test_connection(self) -> bool:
        """Probar conexión a S3"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"[unified_s3][test] Conexión exitosa al bucket {self.bucket_name}")
            return True
        except Exception as e:
            logger.error(f"[unified_s3][test] Error conectando a S3: {e}")
            return False
    
    def generate_s3_key(self, empresa: str, file_type: str = 'data', 
                       filename: str = '', numero_reclamo_sgc: str = None,
                       date_prefix: bool = True) -> str:
        """
        Generar clave S3 según la estructura configurada
        
        Args:
            empresa: 'afinia', 'aire' o 'general'
            file_type: Tipo de archivo
            filename: Nombre del archivo
            numero_reclamo_sgc: Número de reclamo (para estructura CENTRAL)
            date_prefix: Agregar prefijo de fecha (para estructura LEGACY)
            
        Returns:
            Clave S3 generada
        """
        # Normalizar empresa
        empresa = self.COMPANY_MAPPING.get(empresa.lower(), 'general')
        
        if self.path_structure == S3PathStructure.CENTRAL:
            # Estructura: Central_De_Escritos/{empresa}/01_raw_data/oficina_virtual/{numero_reclamo_sgc}/{archivo}
            empresa_folder = self._get_company_folder(empresa)
            if numero_reclamo_sgc:
                return f"Central_De_Escritos/{empresa_folder}/01_raw_data/oficina_virtual/{numero_reclamo_sgc}/{filename}"
            else:
                return f"Central_De_Escritos/{empresa_folder}/01_raw_data/oficina_virtual/misc/{filename}"
        
        elif self.path_structure == S3PathStructure.LEGACY:
            # Estructura: {empresa}/oficina_virtual/{tipo}/{fecha}/{archivo}
            base_path = f"{empresa}/oficina_virtual/{file_type}"
            if date_prefix:
                date_str = datetime.now().strftime('%Y/%m/%d')
                return f"{base_path}/{date_str}/{filename}"
            else:
                return f"{base_path}/{filename}"
        
        else:  # SIMPLE
            # Estructura: {empresa}/{tipo}/{archivo}
            return f"{empresa}/{file_type}/{filename}"
    
    def _get_company_folder(self, empresa: str) -> str:
        """Obtener carpeta de empresa para estructura CENTRAL"""
        mapping = {
            'afinia': 'afinia',
            'aire': 'aire_sas'
        }
        return mapping.get(empresa, empresa)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcular hash SHA256 del archivo"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"[unified_s3][hash] Error calculando hash para {file_path}: {e}")
            return ""
    
    def _prepare_metadata(self, file_path: Path, empresa: str, 
                         custom_metadata: Dict = None) -> Dict[str, str]:
        """Preparar metadatos para el archivo"""
        metadata = {
            'uploaded_by': 'extractorov-unified',
            'uploaded_at': datetime.now().isoformat(),
            'original_filename': file_path.name,
            'empresa': empresa,
            'file_size': str(file_path.stat().st_size),
            'path_structure': self.path_structure.value
        }
        
        if custom_metadata:
            metadata.update({k: str(v) for k, v in custom_metadata.items()})
        
        return metadata
    
    def file_exists_in_s3(self, s3_key: str) -> Tuple[bool, Dict]:
        """Verificar si archivo existe en S3"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True, response.get('Metadata', {})
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False, {}
            else:
                logger.error(f"[unified_s3][exists] Error verificando {s3_key}: {e}")
                return False, {}
    
    def upload_file(self, file_path: Union[str, Path], empresa: str, 
                   file_type: str = 'data', numero_reclamo_sgc: str = None,
                   custom_filename: str = None, custom_metadata: Dict = None,
                   compress: bool = False, max_retries: int = 3) -> S3UploadResult:
        """
        Cargar archivo individual a S3
        
        Args:
            file_path: Ruta del archivo
            empresa: Empresa ('afinia', 'aire', 'general')
            file_type: Tipo de archivo
            numero_reclamo_sgc: Número de reclamo
            custom_filename: Nombre personalizado
            custom_metadata: Metadatos adicionales
            compress: Comprimir archivo antes de subir
            max_retries: Número máximo de reintentos
            
        Returns:
            S3UploadResult con el resultado de la carga
        """
        start_time = datetime.now()
        file_path = Path(file_path)
        
        try:
            # Validaciones
            if not file_path.exists():
                return S3UploadResult(
                    success=False,
                    error_message=f"Archivo no encontrado: {file_path}"
                )
            
            if file_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
                return S3UploadResult(
                    success=False,
                    error_message=f"Extensión no permitida: {file_path.suffix}"
                )
            
            # Generar clave S3
            filename = custom_filename or file_path.name
            s3_key = self.generate_s3_key(empresa, file_type, filename, numero_reclamo_sgc)
            
            # Calcular hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Verificar si existe
            exists_in_s3, s3_metadata = self.file_exists_in_s3(s3_key)
            upload_source = "pre_existing" if exists_in_s3 else "bot"
            
            # Preparar archivo para carga
            upload_file_path = str(file_path)
            if compress and file_path.suffix.lower() in ['.json', '.txt', '.csv', '.log']:
                # Comprimir archivo
                compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                upload_file_path = str(compressed_path)
                s3_key += '.gz'
            
            # Preparar metadatos
            metadata = self._prepare_metadata(file_path, empresa, custom_metadata)
            
            # Realizar carga si no existe
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            
            if not exists_in_s3:
                # Preparar argumentos de carga
                content_type, _ = mimetypes.guess_type(upload_file_path)
                extra_args = {
                    'Metadata': metadata,
                    'ContentType': content_type or 'application/octet-stream',
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
                
                # Realizar carga con reintentos
                logger.info(f"[unified_s3][upload] Cargando: {filename} -> {s3_key}")
                
                for attempt in range(max_retries):
                    try:
                        self.s3_client.upload_file(
                            upload_file_path,
                            self.bucket_name,
                            s3_key,
                            ExtraArgs=extra_args,
                            Config=self.transfer_config
                        )
                        logger.info(f"[unified_s3][upload] Carga exitosa: {s3_key}")
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise e
                        logger.warning(f"[unified_s3][upload] Intento {attempt + 1} falló: {e}")
            
            # Limpiar archivo comprimido temporal
            if compress and upload_file_path != str(file_path):
                Path(upload_file_path).unlink(missing_ok=True)
            
            # Registrar en base de datos
            registry_id = None
            try:
                with self.rds_manager.get_session() as session:
                    registry_id = self._register_file_in_db(
                        session, file_path, s3_key, s3_url, empresa, 
                        file_hash, upload_source, numero_reclamo_sgc
                    )
            except Exception as e:
                logger.warning(f"[unified_s3][upload] Error registrando en BD: {e}")
            
            # Calcular tiempo de procesamiento
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return S3UploadResult(
                success=True,
                s3_key=s3_key,
                s3_url=s3_url,
                file_hash=file_hash,
                file_size=file_path.stat().st_size,
                upload_source=upload_source,
                registry_id=registry_id,
                metadata=metadata,
                processing_time=processing_time
            )
            
        except Exception as e:
            error_msg = f"Error cargando {file_path}: {e}"
            logger.error(f"[unified_s3][upload] {error_msg}")
            return S3UploadResult(
                success=False,
                error_message=error_msg,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _register_file_in_db(self, session: Session, file_path: Path, 
                           s3_key: str, s3_url: str, empresa: str,
                           file_hash: str, upload_source: str,
                           numero_reclamo_sgc: str = None) -> Optional[int]:
        """Registrar archivo en base de datos"""
        try:
            file_info = {
                'bucket_s3': self.bucket_name,
                'clave_s3': s3_key,
                'url_s3': s3_url,
                'numero_reclamo_sgc': numero_reclamo_sgc,
                'empresa': empresa,
                'tamano_archivo': file_path.stat().st_size,
                'tipo_archivo': file_path.suffix.lower(),
                'tipo_contenido': mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream',
                'estado_carga': 'subido' if upload_source == 'bot' else 'pre_existente',
                'origen_carga': upload_source,
                'hash_archivo': file_hash,
                'fecha_carga': datetime.now(),
                'metadatos': json.dumps({
                    'ruta_original': str(file_path),
                    'estructura_ruta': self.path_structure.value
                }),
                'procesado': True,
                'sincronizado_bd': False
            }
            
            # Insertar registro
            insert_query = text("""
                INSERT INTO data.ov_s3_registry 
                (bucket_s3, clave_s3, url_s3, numero_reclamo_sgc, empresa, 
                 tamano_archivo, tipo_archivo, tipo_contenido, estado_carga, 
                 origen_carga, hash_archivo, fecha_carga, metadatos, procesado, sincronizado_bd)
                VALUES 
                (:bucket_s3, :clave_s3, :url_s3, :numero_reclamo_sgc, :empresa,
                 :tamano_archivo, :tipo_archivo, :tipo_contenido, :estado_carga,
                 :origen_carga, :hash_archivo, :fecha_carga, :metadatos, :procesado, :sincronizado_bd)
            """)
            
            result = session.execute(insert_query, file_info)
            session.commit()
            
            return result.lastrowid
            
        except Exception as e:
            session.rollback()
            logger.error(f"[unified_s3][register] Error registrando archivo: {e}")
            return None
    
    def upload_directory(self, directory_path: Union[str, Path], empresa: str,
                        file_type: str = 'data', pattern: str = '*',
                        max_workers: int = 5) -> S3BatchResult:
        """
        Cargar directorio completo a S3
        
        Args:
            directory_path: Ruta del directorio
            empresa: Empresa
            file_type: Tipo de archivo
            pattern: Patrón de archivos a procesar
            max_workers: Número de workers paralelos
            
        Returns:
            S3BatchResult con estadísticas de la carga
        """
        start_time = datetime.now()
        directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            return S3BatchResult(
                errors=[f"Directorio no encontrado: {directory_path}"]
            )
        
        # Encontrar archivos
        files = list(directory_path.glob(pattern))
        files = [f for f in files if f.is_file() and f.suffix.lower() in self.ALLOWED_EXTENSIONS]
        
        logger.info(f"[unified_s3][batch] Procesando {len(files)} archivos de {directory_path}")
        
        results = []
        total_size = 0
        
        for file_path in files:
            result = self.upload_file(file_path, empresa, file_type)
            results.append(result)
            if result.success:
                total_size += result.file_size
        
        # Calcular estadísticas
        successful = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return S3BatchResult(
            total_files=len(files),
            successful_uploads=successful,
            failed_uploads=failed,
            total_size=total_size,
            processing_time=processing_time,
            results=results,
            errors=[r.error_message for r in results if not r.success]
        )
    
    def get_bucket_stats(self) -> S3Stats:
        """Obtener estadísticas del bucket"""
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name)
            
            stats = S3Stats()
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        stats.total_objects += 1
                        stats.total_size += obj['Size']
                        
                        # Analizar por empresa
                        key_parts = obj['Key'].split('/')
                        if len(key_parts) > 0:
                            company = key_parts[0].lower()
                            if company in ['afinia', 'aire', 'central_de_escritos']:
                                stats.by_company[company] = stats.by_company.get(company, 0) + 1
                        
                        # Analizar por tipo
                        file_ext = Path(obj['Key']).suffix.lower()
                        if file_ext:
                            stats.by_type[file_ext] = stats.by_type.get(file_ext, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"[unified_s3][stats] Error obteniendo estadísticas: {e}")
            return S3Stats()

    def upload_company_files(self, company: str) -> S3Stats:
        """
        Subir archivos JSON procesados de una empresa específica
        
        Args:
            company: Nombre de la empresa ('afinia' o 'aire')
            
        Returns:
            S3Stats: Estadísticas de la carga
        """
        start_time = datetime.now()
        logger.info(f"[unified_s3][upload_company_files] Iniciando carga para empresa: {company}")
        
        # Determinar directorio de datos procesados
        base_path = Path("data/processed")
        company_path = base_path / company
        
        if not company_path.exists():
            logger.warning(f"[unified_s3][upload_company_files] No existe directorio: {company_path}")
            stats = S3Stats()
            stats.processing_time = (datetime.now() - start_time).total_seconds()
            return stats
        
        # Buscar archivos JSON procesados
        json_files = list(company_path.glob("**/*.json"))
        
        if not json_files:
            logger.warning(f"[unified_s3][upload_company_files] No se encontraron archivos JSON en: {company_path}")
            stats = S3Stats()
            stats.processing_time = (datetime.now() - start_time).total_seconds()
            return stats
        
        logger.info(f"[unified_s3][upload_company_files] Encontrados {len(json_files)} archivos JSON para {company}")
        
        # Cargar archivos usando upload_directory
        result = self.upload_directory(
            directory_path=company_path,
            empresa=company,
            file_type="oficina_virtual",
            pattern="**/*.json"
        )
        
        # Convertir resultado a S3Stats
        stats = S3Stats()
        stats.total_objects = result.successful_uploads
        stats.total_size = result.total_size
        stats.total_size_bytes = result.total_size  # Mapear para compatibilidad
        stats.uploaded_files = result.successful_uploads  # Mapear para compatibilidad
        stats.pre_existing_files = result.skipped_files  # Archivos que ya existían
        stats.error_files = result.failed_uploads  # Archivos con errores
        stats.processing_time = (datetime.now() - start_time).total_seconds()  # Calcular tiempo de procesamiento
        stats.by_company[company] = result.successful_uploads
        stats.by_type['.json'] = result.successful_uploads
        stats.last_updated = datetime.now()
        
        logger.info(f"[unified_s3][upload_company_files] Completado para {company}: {result.successful_uploads} archivos subidos")
        
        return stats

    def upload_processed_json_files(self, company: str) -> S3Stats:
        """
        Método de compatibilidad - alias para upload_company_files
        
        Args:
            company: Nombre de la empresa
            
        Returns:
            S3Stats: Estadísticas de la carga
        """
        return self.upload_company_files(company)

# Funciones de conveniencia

def create_unified_s3_service(path_structure: str = "central") -> UnifiedS3Service:
    """
    Crear servicio S3 unificado con estructura específica
    
    Args:
        path_structure: 'central', 'legacy' o 'simple'
        
    Returns:
        UnifiedS3Service configurado
    """
    structure_map = {
        'central': S3PathStructure.CENTRAL,
        'legacy': S3PathStructure.LEGACY,
        'simple': S3PathStructure.SIMPLE
    }
    
    structure = structure_map.get(path_structure.lower(), S3PathStructure.CENTRAL)
    return UnifiedS3Service(path_structure=structure)

def upload_file_unified(file_path: str, empresa: str, file_type: str = 'data',
                       path_structure: str = "central") -> S3UploadResult:
    """
    Función de utilidad para carga rápida de archivo
    
    Args:
        file_path: Ruta del archivo
        empresa: Empresa
        file_type: Tipo de archivo
        path_structure: Estructura de rutas
        
    Returns:
        S3UploadResult
    """
    service = create_unified_s3_service(path_structure)
    return service.upload_file(file_path, empresa, file_type)

if __name__ == "__main__":
    # CLI para el servicio unificado
    import argparse
    
    parser = argparse.ArgumentParser(description='Servicio S3 Unificado - ExtractorOV')
    parser.add_argument('--test-connection', action='store_true', help='Probar conexión a S3')
    parser.add_argument('--upload-file', help='Cargar archivo específico')
    parser.add_argument('--upload-directory', help='Cargar directorio completo')
    parser.add_argument('--empresa', '-e', choices=['afinia', 'aire', 'general'], 
                       default='general', help='Empresa')
    parser.add_argument('--file-type', '-t', default='data', help='Tipo de archivo')
    parser.add_argument('--path-structure', '-p', choices=['central', 'legacy', 'simple'],
                       default='central', help='Estructura de rutas')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas del bucket')
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear servicio
    try:
        service = create_unified_s3_service(args.path_structure)
    except Exception as e:
        print(f"ERROR: Error inicializando servicio S3: {e}")
        exit(1)
    
    if args.test_connection:
        print("Probando conexión a S3...")
        success = service.test_connection()
        print(f"Resultado: {'EXITOSO' if success else 'ERROR'}")
    
    elif args.upload_file:
        print(f"Cargando archivo: {args.upload_file}")
        result = service.upload_file(args.upload_file, args.empresa, args.file_type)
        if result.success:
            print(f"EXITOSO: {result.s3_url}")
        else:
            print(f"ERROR: {result.error_message}")
    
    elif args.upload_directory:
        print(f"Cargando directorio: {args.upload_directory}")
        result = service.upload_directory(args.upload_directory, args.empresa, args.file_type)
        print(f"Procesados: {result.total_files}, Exitosos: {result.successful_uploads}, Errores: {result.failed_uploads}")
    
    elif args.stats:
        print("Obteniendo estadísticas del bucket...")
        stats = service.get_bucket_stats()
        print(f"Total objetos: {stats.total_objects}")
        print(f"Tamaño total: {stats.total_size / (1024*1024):.2f} MB")
        print(f"Por empresa: {stats.by_company}")
        print(f"Por tipo: {stats.by_type}")