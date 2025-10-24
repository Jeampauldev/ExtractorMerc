#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de Carga Masiva S3
============================

Procesamiento masivo de todos los archivos existentes en los directorios processed
de Afinia y Aire para cargarlos al bucket S3 con registro en base de datos.

Características:
- Procesa grupos completos de archivos por número de reclamo SGC
- Sube PDFs principales, adjuntos (PDF, DOC, JPG) y JSONs de metadatos
- Registra cada archivo en la tabla registros_ov_s3
- Manejo de errores robusto y logging detallado
- Reporte de progreso en tiempo real

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import os
import json
import hashlib
import boto3
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import logging

from src.config.rds_config import get_rds_engine
from src.config.env_loader import get_s3_config
from sqlalchemy import text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BulkUploadService:
    """Servicio para carga masiva de archivos a S3"""
    
    def __init__(self):
        """Inicializar el servicio de carga masiva"""
        self.s3_config = get_s3_config()
        self.engine = get_rds_engine()
        
        # Cliente S3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.s3_config['access_key_id'],
            aws_secret_access_key=self.s3_config['secret_access_key'],
            region_name=self.s3_config['region']
        )
        
        self.bucket_name = self.s3_config['bucket_name']
        
        # Estadísticas
        self.stats = {
            'reclamos_procesados': 0,
            'archivos_subidos': 0,
            'archivos_error': 0,
            'bytes_totales': 0,
            'inicio': datetime.now()
        }
        
        # Extensiones válidas
        self.valid_extensions = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.json'}
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calcular hash SHA-256 de un archivo"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def get_reclamo_groups(self, processed_path: Path) -> Dict[str, List[Path]]:
        """Agrupar archivos por número de reclamo SGC"""
        reclamos = defaultdict(list)
        
        if not processed_path.exists():
            logger.warning(f"Directorio no encontrado: {processed_path}")
            return reclamos
        
        all_files = [f for f in processed_path.glob('*') if f.is_file()]
        
        for file in all_files:
            if file.suffix.lower() in self.valid_extensions:
                # Extraer número de reclamo del nombre del archivo
                filename = file.name
                if '_' in filename:
                    reclamo_sgc = filename.split('_')[0]
                    reclamos[reclamo_sgc].append(file)
        
        return reclamos
    
    def build_s3_key(self, empresa: str, archivo: str, reclamo_sgc: str) -> str:
        """Construir clave S3 para el archivo"""
        timestamp = datetime.now().strftime('%Y%m%d')

        # Determinar tipo de archivo
        if '_data_' in archivo and archivo.endswith('.json'):
            tipo_archivo = 'metadatos'
        elif '_adjunto_' in archivo:
            tipo_archivo = 'adjuntos'
        else:
            tipo_archivo = 'documentos_principales'

        # Normalizar carpeta de empresa en S3 (soporta 'Air-e' mediante ENV)
        empresa_l = (empresa or '').strip().lower()
        if empresa_l == 'afinia':
            empresa_folder = os.getenv('S3_COMPANY_FOLDER_AFINIA', 'Afinia')
        elif empresa_l == 'aire':
            empresa_folder = os.getenv('S3_COMPANY_FOLDER_AIRE', 'Air-e')
        else:
            empresa_folder = (empresa or 'Empresa').strip().title()

        # Construir clave S3
        s3_key = f"Central_De_Escritos/{empresa_folder}/01_raw_data/oficina_virtual/{reclamo_sgc}/{tipo_archivo}/{archivo}"

        return s3_key
    
    def upload_file_to_s3(self, file_path: Path, s3_key: str) -> Tuple[bool, Optional[str]]:
        """Subir archivo a S3"""
        try:
            # Determinar content type
            extension = file_path.suffix.lower()
            content_types = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.json': 'application/json',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png'
            }
            
            content_type = content_types.get(extension, 'application/octet-stream')
            
            # Subir archivo
            with open(file_path, 'rb') as file_data:
                self.s3_client.upload_fileobj(
                    file_data,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'Metadata': {
                            'source': 'bulk_upload',
                            'original_filename': file_path.name,
                            'upload_timestamp': datetime.now().isoformat()
                        }
                    }
                )
            
            logger.debug(f"Archivo subido exitosamente: {s3_key}")
            return True, None
            
        except Exception as e:
            error_msg = f"Error subiendo {file_path.name} a S3: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def register_file_in_db(self, file_info: Dict) -> bool:
        """Registrar archivo en la base de datos"""
        try:
            with self.engine.connect() as conn:
                insert_query = text("""
                    INSERT INTO data_general.registros_ov_s3 (
                        nombre_archivo,
                        tamano_archivo,
                        tipo_archivo,
                        hash_archivo,
                        clave_s3,
                        numero_reclamo_sgc,
                        empresa,
                        tipo_contenido,
                        estado_carga,
                        origen_carga,
                        procesado,
                        sincronizado_bd,
                        metadatos,
                        fecha_carga,
                        fecha_archivo,
                        fecha_creacion
                    ) VALUES (
                        :nombre_archivo,
                        :tamano_archivo,
                        :tipo_archivo,
                        :hash_archivo,
                        :clave_s3,
                        :numero_reclamo_sgc,
                        :empresa,
                        :tipo_contenido,
                        :estado_carga,
                        :origen_carga,
                        :procesado,
                        :sincronizado_bd,
                        :metadatos,
                        :fecha_carga,
                        :fecha_archivo,
                        :fecha_creacion
                    )
                """)
                
                conn.execute(insert_query, file_info)
                conn.commit()
                
            logger.debug(f"Archivo registrado en BD: {file_info['nombre_archivo']}")
            return True
            
        except Exception as e:
            logger.error(f"Error registrando en BD {file_info['nombre_archivo']}: {str(e)}")
            return False
    
    def process_reclamo_files(self, empresa: str, reclamo_sgc: str, files: List[Path]) -> Dict:
        """Procesar todos los archivos de un reclamo"""
        result = {
            'reclamo_sgc': reclamo_sgc,
            'total_archivos': len(files),
            'archivos_exitosos': 0,
            'archivos_error': 0,
            'errores': [],
            'archivos_procesados': []
        }
        
        logger.info(f"Procesando reclamo {reclamo_sgc} ({len(files)} archivos)")
        
        for file_path in files:
            try:
                # Calcular información del archivo
                file_size = file_path.stat().st_size
                file_hash = self.calculate_file_hash(file_path)
                
                # Construir clave S3
                s3_key = self.build_s3_key(empresa, file_path.name, reclamo_sgc)
                
                # Subir archivo a S3
                upload_success, upload_error = self.upload_file_to_s3(file_path, s3_key)
                
                if upload_success:
                    # Construir URL S3
                    s3_url = f"https://{self.bucket_name}.s3.{self.s3_config['region']}.amazonaws.com/{s3_key}"
                    
                    # Leer metadatos del JSON si existe
                    metadatos = {}
                    if file_path.suffix.lower() == '.json':
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                metadatos = json.load(f)
                        except:
                            pass
                    
                    # Preparar información para la base de datos
                    file_info = {
                        'nombre_archivo': file_path.name,
                        'tamano_archivo': file_size,
                        'tipo_archivo': file_path.suffix.lower(),
                        'hash_archivo': file_hash,
                        'clave_s3': s3_key,
                        'numero_reclamo_sgc': reclamo_sgc,
                        'empresa': empresa,
                        'tipo_contenido': self._get_content_type(file_path),
                        'estado_carga': 'subido',
                        'origen_carga': 'migracion',
                        'procesado': True,
                        'sincronizado_bd': True,
                        'metadatos': json.dumps(metadatos) if metadatos else None,
                        'fecha_carga': datetime.now(),
                        'fecha_archivo': datetime.fromtimestamp(file_path.stat().st_mtime),
                        'fecha_creacion': datetime.now()
                    }
                    
                    # Registrar en base de datos
                    db_success = self.register_file_in_db(file_info)
                    
                    if db_success:
                        result['archivos_exitosos'] += 1
                        result['archivos_procesados'].append(file_path.name)
                        self.stats['archivos_subidos'] += 1
                        self.stats['bytes_totales'] += file_size
                    else:
                        result['archivos_error'] += 1
                        result['errores'].append(f"Error BD: {file_path.name}")
                        self.stats['archivos_error'] += 1
                else:
                    result['archivos_error'] += 1
                    result['errores'].append(upload_error)
                    self.stats['archivos_error'] += 1
                    
            except Exception as e:
                error_msg = f"Error procesando {file_path.name}: {str(e)}"
                result['archivos_error'] += 1
                result['errores'].append(error_msg)
                self.stats['archivos_error'] += 1
                logger.error(error_msg)
        
        return result
    
    def _get_content_type(self, file_path: Path) -> str:
        """Determinar tipo de contenido del archivo"""
        extension = file_path.suffix.lower()
        if '_data_' in file_path.name and extension == '.json':
            return 'metadatos'
        elif '_adjunto_' in file_path.name:
            return 'adjunto'
        elif extension == '.pdf':
            return 'documento_principal'
        else:
            return 'archivo_adicional'
    
    def process_company_files(self, empresa: str, processed_path: Path) -> Dict:
        """Procesar todos los archivos de una empresa"""
        logger.info(f"Iniciando procesamiento de archivos para {empresa.upper()}")
        
        # Obtener grupos de reclamos
        reclamos = self.get_reclamo_groups(processed_path)
        
        if not reclamos:
            logger.warning(f"No se encontraron archivos para procesar en {empresa}")
            return {'empresa': empresa, 'reclamos_procesados': 0, 'resultados': []}
        
        logger.info(f"Encontrados {len(reclamos)} reclamos para procesar en {empresa}")
        
        resultados = []
        
        for i, (reclamo_sgc, files) in enumerate(reclamos.items(), 1):
            logger.info(f"[{i}/{len(reclamos)}] Procesando reclamo {reclamo_sgc}")
            
            result = self.process_reclamo_files(empresa, reclamo_sgc, files)
            resultados.append(result)
            
            self.stats['reclamos_procesados'] += 1
            
            # Mostrar progreso cada 10 reclamos
            if i % 10 == 0:
                self.print_progress(i, len(reclamos))
        
        return {
            'empresa': empresa,
            'reclamos_procesados': len(reclamos),
            'resultados': resultados
        }
    
    def print_progress(self, current: int, total: int):
        """Mostrar progreso de la carga"""
        porcentaje = (current / total) * 100
        tiempo_transcurrido = datetime.now() - self.stats['inicio']
        
        logger.info(f"Progreso: {current}/{total} ({porcentaje:.1f}%) | "
                   f"Archivos subidos: {self.stats['archivos_subidos']} | "
                   f"Errores: {self.stats['archivos_error']} | "
                   f"Tiempo: {tiempo_transcurrido}")
    
    def run_bulk_upload(self) -> Dict:
        """Ejecutar carga masiva completa"""
        logger.info("=== INICIANDO CARGA MASIVA S3 ===")
        
        base_path = Path('C:/00_Project_Dev/ExtractorOV_Modular/data/downloads')
        companies = ['afinia', 'aire']
        
        all_results = {}
        
        for empresa in companies:
            processed_path = base_path / empresa / 'oficina_virtual' / 'processed'
            company_result = self.process_company_files(empresa, processed_path)
            all_results[empresa] = company_result
        
        # Generar reporte final
        self.generate_final_report(all_results)
        
        return all_results
    
    def generate_final_report(self, results: Dict):
        """Generar reporte final de la carga masiva"""
        tiempo_total = datetime.now() - self.stats['inicio']
        
        logger.info("=== REPORTE FINAL DE CARGA MASIVA ===")
        logger.info(f"Tiempo total: {tiempo_total}")
        logger.info(f"Reclamos procesados: {self.stats['reclamos_procesados']}")
        logger.info(f"Archivos subidos exitosamente: {self.stats['archivos_subidos']}")
        logger.info(f"Archivos con error: {self.stats['archivos_error']}")
        logger.info(f"Bytes totales subidos: {self.stats['bytes_totales'] / (1024*1024):.2f} MB")
        
        for empresa, company_data in results.items():
            logger.info(f"\n{empresa.upper()}:")
            logger.info(f"  Reclamos: {company_data['reclamos_procesados']}")
            
            exitosos = sum(r['archivos_exitosos'] for r in company_data['resultados'])
            errores = sum(r['archivos_error'] for r in company_data['resultados'])
            
            logger.info(f"  Archivos exitosos: {exitosos}")
            logger.info(f"  Archivos con error: {errores}")
        
        logger.info("=== FIN DEL REPORTE ===")


def main():
    """Función principal para ejecutar la carga masiva"""
    try:
        service = BulkUploadService()
        results = service.run_bulk_upload()
        
        print("\n[EXITOSO] Carga masiva completada exitosamente")
        print(f"[DATOS] Estadísticas finales:")
        print(f"   - Reclamos procesados: {service.stats['reclamos_procesados']}")
        print(f"   - Archivos subidos: {service.stats['archivos_subidos']}")
        print(f"   - Archivos con error: {service.stats['archivos_error']}")
        print(f"   - Tiempo total: {datetime.now() - service.stats['inicio']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error crítico en carga masiva: {str(e)}")
        print(f"\n[ERROR] Error en carga masiva: {str(e)}")
        raise


if __name__ == "__main__":
    main()