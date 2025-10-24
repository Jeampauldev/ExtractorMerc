#!/usr/bin/env python3
"""
Cargador Directo de JSON a RDS con Archivos
Versión mejorada con soporte para PDFs y adjuntos, integración S3 y monitoreo visual
Compatible con Windows 11 y Ubuntu 24.04.3 LTS
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import traceback

# Importaciones del proyecto
from src.config.rds_config import RDSConnectionManager
from src.config.unified_logging_config import setup_service_logging
from src.services.s3_uploader_service import S3UploaderService

# Importar monitor de progreso visual
try:
    from visual_progress_monitor import create_progress_monitor
    VISUAL_MONITOR_AVAILABLE = True
except ImportError:
    VISUAL_MONITOR_AVAILABLE = False
    print("[ADVERTENCIA]  Monitor visual no disponible - continuando sin visualización")

class DirectLoaderWithFiles:
    """Cargador directo que maneja JSON + archivos asociados"""
    
    def __init__(self, service_type: str, input_directory: str, enable_visual_monitor: bool = True):
        """
        Inicializar el cargador
        
        Args:
            service_type: 'afinia' o 'aire'
            input_directory: Directorio con archivos organizados por numero_radicado
            enable_visual_monitor: Habilitar monitor visual de progreso
        """
        self.service_type = service_type.lower()
        self.input_directory = Path(input_directory)
        self.enable_visual_monitor = enable_visual_monitor and VISUAL_MONITOR_AVAILABLE
        self.rds_manager = RDSConnectionManager()
        self.s3_service = S3UploaderService()
        
        # Configurar logging
        self.logger = setup_service_logging(self.service_type, "direct_loader")
        
        # Monitor de progreso visual
        self.progress_monitor = None
        
        # Estadísticas
        self.stats = {
            'total_records': 0,
            'processed_records': 0,
            'failed_records': 0,
            'duplicate_records': 0,
            'files_uploaded': 0,
            'total_size_mb': 0.0,
            's3_upload_failures': 0,
            'errors': []
        }
        
        # Configuración de archivos
        self.required_files = ['pqr_data.json']
        self.optional_files = ['pqr_detail.pdf']
        self.allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.docx', '.xlsx', '.txt'}
        self.max_file_size_mb = 50
        
        # Mapeo de campos JSON a RDS
        self.field_mapping = {
            'numero_radicado': 'numero_radicado',
            'fecha': 'fecha',
            'estado_solicitud': 'estado_solicitud',
            'tipo_pqr': 'tipo_pqr',
            'numero_reclamo_sgc': 'numero_reclamo_sgc',
            'nombre_completo': 'nombre_completo',
            'numero_documento': 'numero_documento',
            'telefono': 'telefono',
            'email': 'email',
            'direccion': 'direccion',
            'barrio': 'barrio',
            'municipio': 'municipio',
            'departamento': 'departamento',
            'nic': 'nic',
            'descripcion_solicitud': 'descripcion_solicitud',
            'respuesta_empresa': 'respuesta_empresa',
            'observaciones': 'observaciones'
        }

    def load_existing_sgcs(self) -> set:
        """Cargar SGCs existentes para detectar duplicados"""
        try:
            self.logger.info(f"Cargando SGCs existentes para {self.service_type}...")
            
            query = "SELECT numero_radicado FROM pqr_data WHERE servicio = %s"
            
            with self.rds_manager.get_session() as session:
                result = session.execute(query, (self.service_type,))
                results = result.fetchall()
                    
            existing_sgcs = {row[0] for row in results if row[0]}
            self.logger.info(f"Cargados {len(existing_sgcs)} SGCs existentes")
            return existing_sgcs
            
        except Exception as e:
            self.logger.error(f"Error cargando SGCs existentes: {e}")
            return set()

    def discover_record_directories(self) -> List[Path]:
        """Descubrir directorios de registros organizados por numero_radicado"""
        try:
            record_dirs = []
            
            if not self.input_directory.exists():
                self.logger.error(f"Directorio de entrada no existe: {self.input_directory}")
                return record_dirs
            
            # Buscar directorios que contengan al menos pqr_data.json
            for item in self.input_directory.iterdir():
                if item.is_dir():
                    json_file = item / 'pqr_data.json'
                    if json_file.exists():
                        record_dirs.append(item)
                        self.logger.debug(f"Directorio de registro encontrado: {item.name}")
            
            self.logger.info(f"Encontrados {len(record_dirs)} directorios de registros")
            return record_dirs
            
        except Exception as e:
            self.logger.error(f"Error descubriendo directorios: {e}")
            return []

    def validate_record_files(self, record_dir: Path) -> Tuple[bool, List[str], Dict[str, Path]]:
        """
        Validar archivos de un registro
        
        Returns:
            Tuple[bool, List[str], Dict[str, Path]]: (es_válido, errores, archivos_encontrados)
        """
        errors = []
        files_found = {}
        
        try:
            # Verificar archivos requeridos
            for required_file in self.required_files:
                file_path = record_dir / required_file
                if not file_path.exists():
                    errors.append(f"Archivo requerido faltante: {required_file}")
                else:
                    files_found[required_file] = file_path
            
            # Verificar archivos opcionales
            for optional_file in self.optional_files:
                file_path = record_dir / optional_file
                if file_path.exists():
                    files_found[optional_file] = file_path
            
            # Buscar adjuntos en subdirectorio
            attachments_dir = record_dir / 'adjuntos'
            if attachments_dir.exists() and attachments_dir.is_dir():
                for attachment in attachments_dir.iterdir():
                    if attachment.is_file():
                        # Validar extensión
                        if attachment.suffix.lower() not in self.allowed_extensions:
                            errors.append(f"Extensión no permitida: {attachment.name}")
                            continue
                        
                        # Validar tamaño
                        size_mb = attachment.stat().st_size / (1024 * 1024)
                        if size_mb > self.max_file_size_mb:
                            errors.append(f"Archivo muy grande ({size_mb:.1f}MB): {attachment.name}")
                            continue
                        
                        files_found[f"adjunto_{attachment.name}"] = attachment
            
            is_valid = len(errors) == 0
            return is_valid, errors, files_found
            
        except Exception as e:
            errors.append(f"Error validando archivos: {e}")
            return False, errors, {}

    def validate_json_data(self, data: Dict[str, Any]) -> List[str]:
        """Validar datos del JSON"""
        errors = []
        
        try:
            # Validaciones básicas
            if not data.get('numero_radicado'):
                errors.append("numero_radicado es obligatorio")
            
            if not data.get('numero_reclamo_sgc'):
                errors.append("numero_reclamo_sgc es obligatorio")
            
            # Validar fecha
            fecha = data.get('fecha')
            if fecha:
                # Intentar parsear diferentes formatos
                date_formats = [
                    '%Y/%m/%d %H:%M',
                    '%Y-%m-%d %H:%M:%S',
                    '%d/%m/%Y %H:%M',
                    '%Y-%m-%d'
                ]
                
                fecha_valida = False
                for fmt in date_formats:
                    try:
                        datetime.strptime(str(fecha), fmt)
                        fecha_valida = True
                        break
                    except ValueError:
                        continue
                
                if not fecha_valida:
                    errors.append("formato de fecha inválido")
            
            # Validar longitudes de campos
            field_limits = {
                'numero_radicado': 50,
                'estado_solicitud': 100,
                'tipo_pqr': 50,
                'numero_reclamo_sgc': 50,
                'nombre_completo': 200,
                'numero_documento': 20,
                'telefono': 20,
                'email': 100,
                'nic': 20
            }
            
            for field, max_length in field_limits.items():
                value = data.get(field)
                if value and len(str(value)) > max_length:
                    errors.append(f"{field} excede {max_length} caracteres")
            
            return errors
            
        except Exception as e:
            errors.append(f"Error validando JSON: {e}")
            return errors

    def upload_files_to_s3(self, files_found: Dict[str, Path], numero_radicado: str) -> Tuple[bool, Dict[str, str]]:
        """
        Subir archivos a S3
        
        Returns:
            Tuple[bool, Dict[str, str]]: (éxito, urls_s3)
        """
        s3_urls = {}
        
        try:
            for file_key, file_path in files_found.items():
                try:
                    # Determinar tipo de archivo para S3
                    if file_key == 'pqr_data.json':
                        file_type = 'data'
                    elif file_key == 'pqr_detail.pdf':
                        file_type = 'pdfs'
                    elif file_key.startswith('adjunto_'):
                        file_type = 'pdfs'  # Los adjuntos van en la carpeta de PDFs
                    else:
                        file_type = 'data'
                    
                    # Generar nombre único para S3
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    s3_filename = f"{record_dir.name}_{file_key}_{timestamp}{file_path.suffix}"
                    
                    # Subir archivo
                    result = self.s3_service.upload_file(
                        file_path=str(file_path),
                        service_type=self.service_type,
                        file_type=file_type,
                        custom_filename=s3_filename
                    )
                    
                    if result.success:
                        s3_urls[file_key] = result.s3_url
                        self.stats['files_uploaded'] += 1
                        self.stats['total_size_mb'] += result.file_size_bytes / (1024 * 1024)
                        self.logger.debug(f"Archivo subido: {file_key} -> {result.s3_url}")
                    else:
                        self.logger.error(f"Error subiendo {file_key}: {result.error_message}")
                        self.stats['s3_failures'] += 1
                        return False, {}  # Si falla algún archivo, no procesar el registro
                        
                except Exception as file_error:
                    self.logger.error(f"Error subiendo {file_key}: {file_error}")
                    self.stats['s3_failures'] += 1
                    return False, {}
            
            return True, s3_urls
            
        except Exception as e:
            self.logger.error(f"Error general subiendo archivos: {e}")
            return False, {}

    def insert_record_to_rds(self, data: Dict[str, Any], s3_urls: Dict[str, str]) -> bool:
        """Insertar registro en RDS con URLs de S3"""
        try:
            # Preparar datos para inserción
            record_data = {}
            for json_field, db_field in self.field_mapping.items():
                if json_field in data:
                    record_data[db_field] = data[json_field]
            
            # Agregar metadatos
            record_data['servicio'] = self.service_type
            record_data['fecha_extraccion'] = datetime.now()
            record_data['hash_contenido'] = hashlib.md5(f"{data.get('numero_reclamo_sgc', '')}{data.get('numero_radicado', '')}".encode()).hexdigest()
            
            # Mapear campos a nombres de columna correctos
            values = (
                record_data.get('numero_radicado'),
                record_data.get('fecha'),
                record_data.get('estado_solicitud'),
                record_data.get('tipo_pqr'),
                record_data.get('nombre_completo'),  # nombre_cliente
                record_data.get('telefono'),         # telefono_cliente
                record_data.get('email'),            # email_cliente
                record_data.get('direccion'),        # direccion_cliente
                record_data.get('barrio'),           # barrio_cliente
                record_data.get('municipio'),        # ciudad_cliente
                record_data.get('descripcion_solicitud'),  # descripcion_solicitud
                record_data.get('respuesta_empresa'),       # respuesta_solicitud
                record_data.get('observaciones'),
                record_data.get('servicio'),
                record_data.get('hash_contenido'),
                record_data.get('fecha_extraccion'),
                s3_urls.get('pqr_detail.pdf'),
                s3_urls.get('pqr_data.json'),
                json.dumps([url for key, url in s3_urls.items() if key.startswith('adjunto_')])
            )
            
            # Query para insertar en pqr_data
            query = """
            INSERT INTO pqr_data (
                numero_radicado, fecha, estado_solicitud, tipo_pqr, 
                nombre_cliente, telefono_cliente, email_cliente, 
                direccion_cliente, barrio_cliente, ciudad_cliente,
                descripcion_solicitud, respuesta_solicitud, observaciones,
                servicio, hash_contenido, fecha_extraccion,
                url_pdf_pqr, url_json_data, urls_adjuntos
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            with self.rds_manager.get_session() as session:
                session.execute(query, values)
                session.commit()
            
            self.logger.debug(f"Registro insertado: {data.get('numero_radicado')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error insertando registro: {e}")
            return False

    def process_record_directory(self, record_dir: Path, existing_sgcs: set) -> bool:
        """Procesar un directorio de registro completo"""
        try:
            numero_radicado = record_dir.name
            self.logger.info(f"Procesando registro: {numero_radicado}")
            
            # 1. Validar archivos
            is_valid, file_errors, files_found = self.validate_record_files(record_dir)
            if not is_valid:
                self.logger.error(f"Archivos inválidos para {numero_radicado}: {file_errors}")
                self.stats['errors'].extend(file_errors)
                return False
            
            # 2. Cargar y validar JSON
            json_file = files_found['pqr_data.json']
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            json_errors = self.validate_json_data(data)
            if json_errors:
                self.logger.error(f"Datos JSON inválidos para {numero_radicado}: {json_errors}")
                self.stats['errors'].extend(json_errors)
                return False
            
            # 3. Verificar duplicados
            sgc_number = data.get('numero_reclamo_sgc')
            if sgc_number in existing_sgcs:
                self.logger.info(f"Registro duplicado omitido: {sgc_number}")
                self.stats['duplicate_records'] += 1
                return True  # No es error, solo duplicado
            
            # 4. Subir archivos a S3
            upload_success, s3_urls = self.upload_files_to_s3(files_found, numero_radicado)
            if not upload_success:
                self.logger.error(f"Error subiendo archivos para {numero_radicado}")
                return False
            
            # 5. Insertar en RDS
            insert_success = self.insert_record_to_rds(data, s3_urls)
            if not insert_success:
                self.logger.error(f"Error insertando registro {numero_radicado}")
                return False
            
            # 6. Actualizar conjunto de SGCs existentes
            existing_sgcs.add(sgc_number)
            
            self.logger.info(f"Registro procesado exitosamente: {numero_radicado}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error procesando directorio {record_dir.name}: {e}")
            self.stats['errors'].append(f"Error procesando {record_dir.name}: {e}")
            return False

    def generate_report(self) -> Dict[str, Any]:
        """Generar reporte final"""
        success_rate = (self.stats['processed_records'] / max(self.stats['total_records'], 1)) * 100
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'service_type': self.service_type,
            'input_directory': str(self.input_directory),
            'summary': {
                'total_records': self.stats['total_records'],
                'processed_records': self.stats['processed_records'],
                'failed_records': self.stats['failed_records'],
                'duplicate_records': self.stats['duplicate_records'],
                'success_rate_percent': round(success_rate, 2),
                'files_uploaded': self.stats['files_uploaded'],
                'total_size_mb': round(self.stats['total_size_mb'], 2),
                's3_upload_failures': self.stats['s3_upload_failures']
            },
            'errors': self.stats['errors'][:50]  # Limitar errores en reporte
        }
        
        return report

    def run(self) -> Dict[str, Any]:
        """Ejecutar proceso completo de carga"""
        try:
            self.logger.info(f"=== INICIANDO CARGA DIRECTA CON ARCHIVOS ===")
            self.logger.info(f"Servicio: {self.service_type}")
            self.logger.info(f"Directorio de entrada: {self.input_directory}")
            
            # 1. Cargar SGCs existentes
            existing_sgcs = self.load_existing_sgcs()
            
            # 2. Descubrir directorios de registros
            record_directories = self.discover_record_directories()
            self.stats['total_records'] = len(record_directories)
            
            if not record_directories:
                self.logger.warning("No se encontraron directorios de registros para procesar")
                return self.generate_report()
            
            # 3. Inicializar monitor visual si está habilitado
            if self.enable_visual_monitor:
                self.progress_monitor = create_progress_monitor(len(record_directories))
                self.progress_monitor.start_monitoring()
                self.logger.info("Monitor visual iniciado")
            
            # 4. Procesar cada directorio
            for record_dir in record_directories:
                try:
                    if self.progress_monitor:
                        self.progress_monitor.set_current_record(record_dir.name, "Iniciando procesamiento...")
                        self.progress_monitor.update_stats(self.stats)
                    
                    success = self.process_record_directory(record_dir, existing_sgcs)
                    
                    if success:
                        self.stats['processed_records'] += 1
                        if self.progress_monitor:
                            self.progress_monitor.set_current_record(record_dir.name, "[EXITOSO] Completado exitosamente")
                    else:
                        self.stats['failed_records'] += 1
                        if self.progress_monitor:
                            self.progress_monitor.set_current_record(record_dir.name, "[ERROR] Error en procesamiento")
                    
                    # Actualizar monitor
                    if self.progress_monitor:
                        self.progress_monitor.update_stats(self.stats)
                        
                except Exception as e:
                    self.logger.error(f"Error procesando {record_dir.name}: {e}")
                    self.stats['failed_records'] += 1
                    
                    if self.progress_monitor:
                        self.progress_monitor.set_current_record(record_dir.name, f"[ERROR] Error: {str(e)[:50]}...")
                        self.progress_monitor.update_stats(self.stats)
            
            # 5. Generar reporte
            report = self.generate_report()
            
            # 6. Guardar reporte
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"file_loader_report_{self.service_type}_{timestamp}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Reporte guardado en: {report_file}")
            self.logger.info(f"Procesamiento completado: {self.stats['processed_records']}/{self.stats['total_records']} registros")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error en proceso principal: {e}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(f"Error principal: {e}")
            return self.generate_report()
        finally:
            # Detener monitor visual
            if self.progress_monitor:
                self.progress_monitor.show_final_report(self.stats)


def main():
    """Función principal"""
    if len(sys.argv) != 3:
        print("Uso: python direct_json_to_rds_loader_with_files.py <service_type> <input_directory>")
        print("Ejemplo: python direct_json_to_rds_loader_with_files.py afinia /path/to/records")
        sys.exit(1)
    
    service_type = sys.argv[1]
    input_directory = sys.argv[2]
    
    if service_type not in ['afinia', 'aire']:
        print("Error: service_type debe ser 'afinia' o 'aire'")
        sys.exit(1)
    
    # Ejecutar carga
    loader = DirectLoaderWithFiles(service_type, input_directory)
    report = loader.run()
    
    # Mostrar resumen
    print(f"\n=== RESUMEN DE CARGA ===")
    print(f"Servicio: {service_type}")
    print(f"Total de registros: {report['summary']['total_records']}")
    print(f"Procesados: {report['summary']['processed_records']}")
    print(f"Fallidos: {report['summary']['failed_records']}")
    print(f"Duplicados: {report['summary']['duplicate_records']}")
    print(f"Archivos subidos: {report['summary']['files_uploaded']}")
    print(f"Tamaño total: {report['summary']['total_size_mb']} MB")
    print(f"Tasa de éxito: {report['summary']['success_rate_percent']}%")


if __name__ == "__main__":
    main()