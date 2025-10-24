#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio AWS S3 para Extractor OV Modular
=========================================

Servicio robusto para carga, gestión y registro de archivos en AWS S3.
Incluye detección de archivos pre-existentes, registro en base de datos
y trazabilidad completa.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config.rds_config import RDSConnectionManager

logger = logging.getLogger(__name__)

@dataclass
class S3UploadResult:
    """Resultado de carga a S3"""
    success: bool
    s3_key: str = ""
    s3_url: str = ""
    file_hash: str = ""
    file_size: int = 0
    error_message: str = ""
    upload_source: str = "bot"  # bot, pre_existing
    registry_id: Optional[int] = None

@dataclass
class S3Stats:
    """Estadísticas de operaciones S3"""
    total_files: int = 0
    uploaded_files: int = 0
    pre_existing_files: int = 0
    error_files: int = 0
    total_size_bytes: int = 0
    processing_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class AWSS3Service:
    """
    Servicio para gestión de archivos en AWS S3 con registro en base de datos
    """
    
    def __init__(self, bucket_name: str = None):
        """
        Inicializar servicio S3
        
        Args:
            bucket_name: Nombre del bucket S3 (si no se especifica, se lee de variables de entorno)
        """
        # Configuración desde variables de entorno
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = bucket_name or os.getenv('AWS_S3_BUCKET_NAME', 'extractorov-data')
        
        # Configuración de rutas S3
        self.s3_base_path = os.getenv('S3_BASE_PATH', 'raw_data')
        
        # Cliente S3
        self._s3_client = None
        
        # Manager de BD
        self.rds_manager = RDSConnectionManager()
        
        logger.info(f"[s3_service][init] Inicializado - Bucket: {self.bucket_name}, Región: {self.aws_region}")
    
    @property
    def s3_client(self):
        """Lazy loading del cliente S3"""
        if self._s3_client is None:
            try:
                if self.aws_access_key and self.aws_secret_key:
                    self._s3_client = boto3.client(
                        's3',
                        aws_access_key_id=self.aws_access_key,
                        aws_secret_access_key=self.aws_secret_key,
                        region_name=self.aws_region
                    )
                else:
                    # Intentar usar credenciales por defecto (IAM role, etc.)
                    self._s3_client = boto3.client('s3', region_name=self.aws_region)
                
                logger.info("[s3_service][client] Cliente S3 inicializado exitosamente")
                
            except NoCredentialsError:
                logger.warning("[s3_service][client] Credenciales AWS no encontradas - habilitando modo simulado")
                self._s3_client = 'SIMULATED'  # Marcador para modo simulado
            except Exception as e:
                logger.warning(f"[s3_service][client] Error inicializando cliente S3: {e} - habilitando modo simulado")
                self._s3_client = 'SIMULATED'
        
        return self._s3_client
    
    @property 
    def is_simulated_mode(self) -> bool:
        """Verificar si está en modo simulado"""
        return self.s3_client == 'SIMULATED'
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calcular hash SHA-256 de un archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Hash SHA-256 del archivo
        """
        hash_sha256 = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"[s3_service][hash] Error calculando hash de {file_path}: {e}")
            return ""
    
    def _get_company_folder(self, empresa: str) -> str:
        """
        Obtener el nombre de carpeta de la empresa en S3.

        Permite personalizar el nombre mediante variables de entorno para
        ajustarse a estructuras existentes (por ejemplo, 'Air-e').

        Env vars soportadas:
        - S3_COMPANY_FOLDER_AFINIA (por defecto 'Afinia')
        - S3_COMPANY_FOLDER_AIRE (por defecto 'Air-e')
        """
        empresa_l = (empresa or '').strip().lower()
        if empresa_l == 'afinia':
            return os.getenv('S3_COMPANY_FOLDER_AFINIA', 'Afinia')
        if empresa_l == 'aire':
            return os.getenv('S3_COMPANY_FOLDER_AIRE', 'Air-e')
        # Fallback genérico
        return (empresa or 'Empresa').strip().title()

    def _generate_s3_key(self, empresa: str, filename: str, numero_reclamo_sgc: str = None) -> str:
        """
        Generar key S3 usando estructura existente del bucket
        
        Args:
            empresa: 'afinia' o 'aire'
            filename: Nombre del archivo
            numero_reclamo_sgc: Número de reclamo (opcional)
            
        Returns:
            Key S3 estructurada
        """
        # Adaptado a estructura existente: Central_De_Escritos/{empresa}/01_raw_data/oficina_virtual/{numero_reclamo_sgc}/{filename}
        empresa_folder = self._get_company_folder(empresa)
        
        if numero_reclamo_sgc:
            return f"Central_De_Escritos/{empresa_folder}/01_raw_data/oficina_virtual/{numero_reclamo_sgc}/{filename}"
        else:
            return f"Central_De_Escritos/{empresa_folder}/01_raw_data/oficina_virtual/misc/{filename}"
    
    def check_file_exists_in_s3(self, s3_key: str) -> Tuple[bool, Dict]:
        """
        Verificar si un archivo existe en S3
        
        Args:
            s3_key: Key del archivo en S3
            
        Returns:
            Tupla (existe, metadatos)
        """
        if self.is_simulated_mode:
            logger.debug(f"[s3_service][check_exists] Modo simulado - archivo {s3_key} no existe")
            return False, {}
            
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            metadata = {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag', '').strip('"')
            }
            
            return True, metadata
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False, {}
            else:
                logger.error(f"[s3_service][check_exists] Error verificando {s3_key}: {e}")
                return False, {}
        except Exception as e:
            logger.error(f"[s3_service][check_exists] Error inesperado verificando {s3_key}: {e}")
            return False, {}
    
    def upload_file_to_s3(self, file_path: Path, s3_key: str) -> Tuple[bool, str, str]:
        """
        Subir archivo a S3
        
        Args:
            file_path: Ruta local del archivo
            s3_key: Key destino en S3
            
        Returns:
            Tupla (éxito, url_s3, mensaje_error)
        """
        if self.is_simulated_mode:
            # Generar URL simulada
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            logger.info(f"[s3_service][upload] Modo simulado - archivo {s3_key} marcado como subido")
            return True, s3_url, ""
            
        try:
            # Determinar content type
            file_extension = file_path.suffix.lower()
            content_type_map = {
                '.json': 'application/json',
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.txt': 'text/plain',
                '.csv': 'text/csv',
                '.zip': 'application/zip'
            }
            content_type = content_type_map.get(file_extension, 'binary/octet-stream')
            
            # Subir archivo
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': {
                        'uploaded_by': 'extractorov-bot',
                        'uploaded_at': datetime.now().isoformat(),
                        'original_filename': file_path.name
                    }
                }
            )
            
            # Generar URL
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            
            logger.info(f"[s3_service][upload] Archivo subido exitosamente: {s3_key}")
            return True, s3_url, ""
            
        except ClientError as e:
            error_msg = f"Error AWS subiendo {s3_key}: {e}"
            logger.error(f"[s3_service][upload] {error_msg}")
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Error inesperado subiendo {s3_key}: {e}"
            logger.error(f"[s3_service][upload] {error_msg}")
            return False, "", error_msg
    
    def register_file_in_db(self, session: Session, file_info: Dict) -> Optional[int]:
        """
        Registrar archivo en base de datos usando tabla en español
        
        Args:
            session: Sesión de base de datos
            file_info: Información del archivo
            
        Returns:
            ID del registro creado o None si falló
        """
        try:
            insert_query = text("""
                INSERT INTO data_general.registros_ov_s3 (
                    nombre_archivo, bucket_s3, clave_s3, url_s3, numero_reclamo_sgc,
                    empresa, tamano_archivo, tipo_archivo, tipo_contenido, estado_carga,
                    origen_carga, hash_archivo, fecha_carga, metadatos, procesado,
                    sincronizado_bd
                ) VALUES (
                    :nombre_archivo, :bucket_s3, :clave_s3, :url_s3, :numero_reclamo_sgc,
                    :empresa, :tamano_archivo, :tipo_archivo, :tipo_contenido, :estado_carga,
                    :origen_carga, :hash_archivo, :fecha_carga, :metadatos, :procesado,
                    :sincronizado_bd
                )
                RETURNING id
            """)
            
            result = session.execute(insert_query, file_info)
            registry_id = result.scalar()
            session.commit()
            
            logger.debug(f"[s3_service][register_db] Archivo registrado con ID: {registry_id}")
            return registry_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"[s3_service][register_db] Error registrando archivo: {e}")
            return None
    
    def check_file_in_registry(self, session: Session, file_hash: str, s3_key: str) -> Optional[Dict]:
        """
        Verificar si un archivo ya está registrado en BD usando tabla en español
        
        Args:
            session: Sesión de BD
            file_hash: Hash del archivo
            s3_key: Key S3 del archivo
            
        Returns:
            Información del registro existente o None
        """
        try:
            query = text("""
                SELECT id, nombre_archivo, clave_s3, estado_carga, origen_carga, fecha_creacion
                FROM data_general.registros_ov_s3
                WHERE hash_archivo = :file_hash OR clave_s3 = :s3_key
                ORDER BY fecha_creacion DESC
                LIMIT 1
            """)
            
            result = session.execute(query, {
                'file_hash': file_hash,
                's3_key': s3_key
            }).fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'filename': result[1],
                    's3_key': result[2],
                    'upload_status': result[3],
                    'upload_source': result[4],
                    'created_at': result[5]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"[s3_service][check_registry] Error verificando registro: {e}")
            return None
    
    def upload_file_with_registry(self, file_path: Path, empresa: str, 
                                numero_reclamo_sgc: str = None) -> S3UploadResult:
        """
        Subir archivo a S3 con registro completo en BD
        
        Args:
            file_path: Ruta del archivo local
            empresa: 'afinia' o 'aire'
            numero_reclamo_sgc: Número de reclamo SGC (opcional)
            
        Returns:
            Resultado de la carga
        """
        start_time = datetime.now()
        
        if not file_path.exists():
            return S3UploadResult(
                success=False,
                error_message=f"Archivo no encontrado: {file_path}"
            )
        
        # Calcular hash del archivo
        file_hash = self._calculate_file_hash(file_path)
        if not file_hash:
            return S3UploadResult(
                success=False,
                error_message=f"No se pudo calcular hash del archivo: {file_path}"
            )
        
        # Generar key S3
        s3_key = self._generate_s3_key(empresa, file_path.name, numero_reclamo_sgc)
        
        session = self.rds_manager.get_session()
        
        try:
            # Verificar si ya está registrado
            existing_registry = self.check_file_in_registry(session, file_hash, s3_key)
            
            if existing_registry:
                logger.info(f"[s3_service][upload_with_registry] Archivo ya registrado: {existing_registry['s3_key']}")
                return S3UploadResult(
                    success=True,
                    s3_key=existing_registry['s3_key'],
                    s3_url=f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{existing_registry['s3_key']}",
                    file_hash=file_hash,
                    file_size=file_path.stat().st_size,
                    upload_source="pre_existing",
                    registry_id=existing_registry['id']
                )
            
            # Verificar si existe en S3 pero no está registrado
            exists_in_s3, s3_metadata = self.check_file_exists_in_s3(s3_key)
            upload_source = "pre_existing" if exists_in_s3 else "bot"
            
            # Si no existe en S3, subirlo
            s3_url = ""
            if not exists_in_s3:
                success, s3_url, error_msg = self.upload_file_to_s3(file_path, s3_key)
                if not success:
                    return S3UploadResult(
                        success=False,
                        error_message=error_msg
                    )
            else:
                s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
                logger.info(f"[s3_service][upload_with_registry] Archivo pre-existente en S3: {s3_key}")
            
            # Registrar en BD con campos en español
            file_info = {
                'nombre_archivo': file_path.name,
                'bucket_s3': self.bucket_name,
                'clave_s3': s3_key,
                'url_s3': s3_url,
                'numero_reclamo_sgc': numero_reclamo_sgc,
                'empresa': empresa,
                'tamano_archivo': file_path.stat().st_size,
                'tipo_archivo': file_path.suffix.lower(),
                'tipo_contenido': 'application/json' if file_path.suffix.lower() == '.json' else 'application/octet-stream',
                'estado_carga': 'subido' if not exists_in_s3 else 'pre_existente',
                'origen_carga': upload_source,
                'hash_archivo': file_hash,
                'fecha_carga': datetime.now(),
                'metadatos': json.dumps({
                    'ruta_original': str(file_path),
                    'tiempo_procesamiento': (datetime.now() - start_time).total_seconds(),
                    'metadatos_s3': s3_metadata if exists_in_s3 else None
                }),
                'procesado': True,
                'sincronizado_bd': False
            }
            
            registry_id = self.register_file_in_db(session, file_info)
            
            return S3UploadResult(
                success=True,
                s3_key=s3_key,
                s3_url=s3_url,
                file_hash=file_hash,
                file_size=file_info['tamano_archivo'],
                upload_source=upload_source,
                registry_id=registry_id
            )
            
        except Exception as e:
            error_msg = f"Error en upload_file_with_registry: {e}"
            logger.error(f"[s3_service][upload_with_registry] {error_msg}")
            return S3UploadResult(
                success=False,
                error_message=error_msg
            )
        finally:
            session.close()
    
    def upload_processed_json_files(self, company: str) -> S3Stats:
        """
        Subir archivos JSON procesados de una empresa a S3
        
        Args:
            company: 'afinia' o 'aire'
            
        Returns:
            Estadísticas de la carga
        """
        start_time = datetime.now()
        stats = S3Stats()
        
        # Ruta de archivos procesados
        processed_path = Path(f"data/downloads/{company}/oficina_virtual/processed")
        
        if not processed_path.exists():
            logger.warning(f"[s3_service][upload_processed] Directorio no encontrado: {processed_path}")
            return stats
        
        # Buscar archivos JSON procesados
        json_files = list(processed_path.glob("*_data_*.json"))
        stats.total_files = len(json_files)
        
        logger.info(f"[s3_service][upload_processed] Procesando {stats.total_files} archivos JSON de {company}")
        
        for json_file in json_files:
            try:
                # Extraer numero_reclamo_sgc del nombre del archivo
                # Formato esperado: RE123456789_data_20251008_123456.json
                filename_parts = json_file.stem.split('_')
                numero_reclamo_sgc = filename_parts[0] if filename_parts else None
                
                # Si el número no es válido, usar el nombre completo del archivo
                if not numero_reclamo_sgc or len(numero_reclamo_sgc) < 5:
                    numero_reclamo_sgc = json_file.stem
                
                # Subir archivo
                result = self.upload_file_with_registry(
                    file_path=json_file,
                    empresa=company,
                    numero_reclamo_sgc=numero_reclamo_sgc
                )
                
                if result.success:
                    stats.total_size_bytes += result.file_size
                    
                    if result.upload_source == "bot":
                        stats.uploaded_files += 1
                        logger.debug(f"[s3_service][upload_processed] Subido: {json_file.name}")
                    else:
                        stats.pre_existing_files += 1
                        logger.debug(f"[s3_service][upload_processed] Pre-existente: {json_file.name}")
                else:
                    stats.error_files += 1
                    stats.errors.append(f"Error en {json_file.name}: {result.error_message}")
                    logger.error(f"[s3_service][upload_processed] Error en {json_file.name}: {result.error_message}")
                    
            except Exception as e:
                stats.error_files += 1
                error_msg = f"Error procesando {json_file.name}: {e}"
                stats.errors.append(error_msg)
                logger.error(f"[s3_service][upload_processed] {error_msg}")
        
        stats.processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[s3_service][upload_processed] Completado {company}: {stats.uploaded_files} subidos, {stats.pre_existing_files} pre-existentes, {stats.error_files} errores")
        
        return stats
    
    def get_s3_registry_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del registro S3
        
        Returns:
            Estadísticas del registro
        """
        session = self.rds_manager.get_session()
        
        try:
            # Estadísticas generales usando tabla en español
            stats_query = text("""
                SELECT 
                    empresa,
                    estado_carga,
                    origen_carga,
                    COUNT(*) as count,
                    SUM(tamano_archivo) as total_size,
                    MAX(fecha_creacion) as latest_upload
                FROM data_general.registros_ov_s3
                GROUP BY empresa, estado_carga, origen_carga
                ORDER BY empresa, estado_carga, origen_carga
            """)
            
            results = session.execute(stats_query).fetchall()
            
            stats = {
                'timestamp': datetime.now().isoformat(),
                'by_company_status': {},
                'totals': {
                    'total_files': 0,
                    'total_size_bytes': 0,
                    'by_status': {},
                    'by_source': {}
                }
            }
            
            for row in results:
                empresa, status, source, count, size, latest = row
                
                # Por empresa y estado
                if empresa not in stats['by_company_status']:
                    stats['by_company_status'][empresa] = {}
                
                key = f"{status}_{source}"
                stats['by_company_status'][empresa][key] = {
                    'count': count,
                    'total_size_bytes': size or 0,
                    'latest_upload': latest.isoformat() if latest else None
                }
                
                # Totales
                stats['totals']['total_files'] += count
                stats['totals']['total_size_bytes'] += (size or 0)
                
                # Por estado
                if status not in stats['totals']['by_status']:
                    stats['totals']['by_status'][status] = 0
                stats['totals']['by_status'][status] += count
                
                # Por origen
                if source not in stats['totals']['by_source']:
                    stats['totals']['by_source'][source] = 0
                stats['totals']['by_source'][source] += count
            
            return stats
            
        except Exception as e:
            logger.error(f"[s3_service][get_stats] Error obteniendo estadísticas: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
        finally:
            session.close()


# Funciones de conveniencia

def upload_company_files(company: str) -> S3Stats:
    """
    Subir archivos JSON procesados de una empresa
    
    Args:
        company: 'afinia' o 'aire'
        
    Returns:
        Estadísticas de carga
    """
    s3_service = AWSS3Service()
    return s3_service.upload_processed_json_files(company)

def upload_all_processed_files() -> Dict[str, S3Stats]:
    """
    Subir archivos JSON procesados de todas las empresas
    
    Returns:
        Estadísticas por empresa
    """
    s3_service = AWSS3Service()
    results = {}
    
    for company in ['afinia', 'aire']:
        logger.info(f"[s3_service][upload_all] Procesando archivos de {company}")
        results[company] = s3_service.upload_processed_json_files(company)
    
    return results

if __name__ == "__main__":
    # Test del servicio S3
    logger.info("[s3_service][main] Iniciando test de servicio S3")
    
    # Subir archivos procesados
    results = upload_all_processed_files()
    
    print("=" * 70)
    print("RESULTADO DE CARGA A AWS S3")
    print("=" * 70)
    
    if results:
        total_uploaded = 0
        total_pre_existing = 0
        total_errors = 0
        total_size = 0
        
        for company, stats in results.items():
            print(f"\n{company.upper()}:")
            print(f"  - Total archivos: {stats.total_files}")
            print(f"  - Subidos (nuevos): {stats.uploaded_files}")
            print(f"  - Pre-existentes: {stats.pre_existing_files}")
            print(f"  - Errores: {stats.error_files}")
            print(f"  - Tamaño total: {stats.total_size_bytes / 1024 / 1024:.2f} MB")
            print(f"  - Tiempo: {stats.processing_time:.2f}s")
            
            total_uploaded += stats.uploaded_files
            total_pre_existing += stats.pre_existing_files
            total_errors += stats.error_files
            total_size += stats.total_size_bytes
            
            if stats.errors and len(stats.errors) > 0:
                print(f"  - Errores encontrados: {len(stats.errors)}")
                for error in stats.errors[:2]:  # Mostrar solo los primeros 2
                    print(f"    * {error}")
        
        print(f"\nRESUMEN TOTAL:")
        print(f"  - Total subidos: {total_uploaded}")
        print(f"  - Total pre-existentes: {total_pre_existing}")
        print(f"  - Total errores: {total_errors}")
        print(f"  - Tamaño total: {total_size / 1024 / 1024:.2f} MB")
    else:
        print("No se procesaron archivos")
    
    # Mostrar estadísticas del registro
    s3_service = AWSS3Service()
    registry_stats = s3_service.get_s3_registry_stats()
    
    print(f"\nESTADÍSTICAS DEL REGISTRO S3:")
    if 'error' not in registry_stats:
        print(f"  - Total archivos registrados: {registry_stats['totals']['total_files']}")
        print(f"  - Tamaño total registrado: {registry_stats['totals']['total_size_bytes'] / 1024 / 1024:.2f} MB")
        
        for company, company_stats in registry_stats.get('by_company_status', {}).items():
            print(f"\n  {company.upper()}:")
            for status_key, status_data in company_stats.items():
                print(f"    - {status_key}: {status_data['count']} archivos")
    else:
        print(f"  Error: {registry_stats['error']}")
    
    print("\n" + "=" * 70)