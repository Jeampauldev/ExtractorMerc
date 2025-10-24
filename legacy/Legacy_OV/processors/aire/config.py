"""
Configuración del Procesador de Afinia
======================================

Configuración específica para el procesamiento de datos de Afinia,
incluyendo conexión a RDS AWS y parámetros de procesamiento.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / "env" / ".env"
if env_file.exists():
 load_dotenv(dotenv_path=str(env_file), override=True)

# Configuración de Base de Datos RDS AWS
# [ADVERTENCIA] IMPORTANTE: Usar variables de entorno para credenciales
RDS_CONFIG = {
 "host": os.getenv("DB_HOST", "your-rds-endpoint.rds.amazonaws.com"),
 "database": os.getenv("DB_NAME", "your-database"),
 "username": os.getenv("DB_USER", "your-username"),
 "password": os.getenv("DB_PASSWORD"),  # [ADVERTENCIA] REQUERIDO en variables de entorno
 "port": int(os.getenv("DB_PORT", "3306")),
 "charset": "utf8mb4",
 "connect_timeout": 30,
 "read_timeout": 30,
 "write_timeout": 30
}

# Configuración de procesamiento
PROCESSING_CONFIG = {
 "batch_size": 100, # Número de registros a procesar por lote
 "max_retries": 3, # Número máximo de reintentos en caso de error
 "retry_delay": 5, # Segundos de espera entre reintentos
 "validation_strict": True, # Validación estricta de datos
 "backup_failed_records": True, # Respaldar registros que fallan
 "log_level": "INFO"
}

# Configuración de archivos y directorios
PATHS_CONFIG = {
 "input_directory": "downloads/afinia/new_version",
 "processed_directory": "downloads/afinia/processed",
 "failed_directory": "downloads/afinia/failed",
 "backup_directory": "downloads/afinia/backup",
 "logs_directory": "logs/processors/afinia"
}

# Esquema de tabla para PQR de Afinia
AFINIA_PQR_SCHEMA = {
 "table_name": "afinia_pqr",
 "fields": {
 "id": {"type": "INT", "primary_key": True, "auto_increment": True},
 "nic": {"type": "VARCHAR(50)", "nullable": True},
 "fecha": {"type": "DATETIME", "nullable": True},
 "documento_identidad": {"type": "VARCHAR(20)", "nullable": True},
 "nombres_apellidos": {"type": "VARCHAR(200)", "nullable": True},
 "lectura": {"type": "VARCHAR(50)", "nullable": True},
 "correo_electronico": {"type": "VARCHAR(100)", "nullable": True},
 "telefono": {"type": "VARCHAR(20)", "nullable": True},
 "celular": {"type": "VARCHAR(20)", "nullable": True},
 "tipo_pqr": {"type": "VARCHAR(100)", "nullable": True},
 "canal_respuesta": {"type": "VARCHAR(50)", "nullable": True},
 "documento_prueba": {"type": "VARCHAR(255)", "nullable": True},
 "cuerpo_reclamacion": {"type": "TEXT", "nullable": True},
 "numero_radicado": {"type": "VARCHAR(50)", "nullable": True, "unique": True},
 "estado_solicitud": {"type": "VARCHAR(50)", "nullable": True},
 "finalizar": {"type": "VARCHAR(50)", "nullable": True},
 "adjuntar_archivo": {"type": "VARCHAR(255)", "nullable": True},
 "numero_reclamo_sgc": {"type": "VARCHAR(50)", "nullable": True},
 "comentarios": {"type": "TEXT", "nullable": True},
 "extraction_timestamp": {"type": "DATETIME", "nullable": True},
 "page_url": {"type": "VARCHAR(500)", "nullable": True},
 "processed_at": {"type": "DATETIME", "default": "CURRENT_TIMESTAMP"},
 "created_at": {"type": "DATETIME", "default": "CURRENT_TIMESTAMP"},
 "updated_at": {"type": "DATETIME", "default": "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"}
 },
 "indexes": [
 {"name": "idx_numero_radicado", "columns": ["numero_radicado"]},
 {"name": "idx_numero_reclamo_sgc", "columns": ["numero_reclamo_sgc"]},
 {"name": "idx_fecha", "columns": ["fecha"]},
 {"name": "idx_estado_solicitud", "columns": ["estado_solicitud"]},
 {"name": "idx_processed_at", "columns": ["processed_at"]}
 ]
}

# Mapeo de campos JSON a campos de BD
FIELD_MAPPING = {
 "nic": "nic",
 "fecha": "fecha",
 "documento_identidad": "documento_identidad",
 "nombres_apellidos": "nombres_apellidos",
 "lectura": "lectura",
 "correo_electronico": "correo_electronico",
 "telefono": "telefono",
 "celular": "celular",
 "tipo_pqr": "tipo_pqr",
 "canal_respuesta": "canal_respuesta",
 "documento_prueba": "documento_prueba",
 "cuerpo_reclamacion": "cuerpo_reclamacion",
 "numero_radicado": "numero_radicado",
 "estado_solicitud": "estado_solicitud",
 "finalizar": "finalizar",
 "adjuntar_archivo": "adjuntar_archivo",
 "numero_reclamo_sgc": "numero_reclamo_sgc",
 "comentarios": "comentarios"
}

# Validaciones de campos
FIELD_VALIDATIONS = {
 "numero_radicado": {
 "required": False,
 "max_length": 50,
 "pattern": r"^\d*$" # Solo números
 },
 "numero_reclamo_sgc": {
 "required": False,
 "max_length": 50,
 "pattern": r"^[A-Z0-9]*$" # Letras mayúsculas y números
 },
 "correo_electronico": {
 "required": False,
 "max_length": 100,
 "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
 },
 "telefono": {
 "required": False,
 "max_length": 20,
 "pattern": r"^\d*$"
 },
 "celular": {
 "required": False,
 "max_length": 20,
 "pattern": r"^\d*$"
 },
 "documento_identidad": {
 "required": False,
 "max_length": 20,
 "pattern": r"^\d*$"
 }
}

# Configuración consolidada para Afinia
AFINIA_CONFIG = {
 "rds": RDS_CONFIG,
 "processing": PROCESSING_CONFIG,
 "paths": PATHS_CONFIG,
 "schema": AFINIA_PQR_SCHEMA,
 "field_mapping": FIELD_MAPPING,
 "field_validations": FIELD_VALIDATIONS
}
