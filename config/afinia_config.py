"""
Configuración del Procesador de Mercurio Afinia
===============================================

Configuración específica para el procesamiento de datos de Mercurio Afinia,
incluyendo esquemas de BD y mapeos de campos específicos para Mercurio.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / "env" / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=str(env_file), override=True)

# Configuración específica para Mercurio Afinia
MERCURIO_AFINIA_CONFIG = {
    "batch_size": 100,
    "max_retries": 3,
    "retry_delay": 5,
    "validation_strict": True,
    "backup_failed_records": True,
    "log_level": "INFO"
}

# Usar el mismo esquema base pero con tabla específica para Mercurio
MERCURIO_PQR_SCHEMA = {
    "table_name": "mercurio_afinia_pqr",
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
        "extraction_source": {"type": "VARCHAR(50)", "default": "mercurio"},
        "extraction_timestamp": {"type": "DATETIME", "nullable": True},
        "page_url": {"type": "VARCHAR(500)", "nullable": True},
        "processed_at": {"type": "DATETIME", "default": "CURRENT_TIMESTAMP"},
        "created_at": {"type": "DATETIME", "default": "CURRENT_TIMESTAMP"},
        "updated_at": {"type": "DATETIME", "default": "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"}
    },
    "indexes": [
        {"name": "idx_mercurio_numero_radicado", "columns": ["numero_radicado"]},
        {"name": "idx_mercurio_numero_reclamo_sgc", "columns": ["numero_reclamo_sgc"]},
        {"name": "idx_mercurio_fecha", "columns": ["fecha"]},
        {"name": "idx_mercurio_estado_solicitud", "columns": ["estado_solicitud"]},
        {"name": "idx_mercurio_extraction_source", "columns": ["extraction_source"]},
        {"name": "idx_mercurio_processed_at", "columns": ["processed_at"]}
    ]
}

# Mapeo de campos específico para Mercurio Afinia
# Estos pueden ser diferentes de Oficina Virtual
FIELD_MAPPING_MERCURIO = {
    "nic": "nic",
    "fecha": "fecha", 
    "fecha_solicitud": "fecha",  # Posible alternativa
    "documento_identidad": "documento_identidad",
    "cedula": "documento_identidad",  # Alternativa común en Mercurio
    "nombres_apellidos": "nombres_apellidos",
    "nombre_completo": "nombres_apellidos",  # Alternativa
    "lectura": "lectura",
    "correo_electronico": "correo_electronico",
    "email": "correo_electronico",  # Alternativa
    "telefono": "telefono",
    "celular": "celular",
    "tipo_pqr": "tipo_pqr",
    "tipo_solicitud": "tipo_pqr",  # Alternativa común en Mercurio
    "canal_respuesta": "canal_respuesta",
    "documento_prueba": "documento_prueba",
    "cuerpo_reclamacion": "cuerpo_reclamacion",
    "descripcion": "cuerpo_reclamacion",  # Alternativa
    "numero_radicado": "numero_radicado",
    "radicado": "numero_radicado",  # Alternativa
    "estado_solicitud": "estado_solicitud",
    "estado": "estado_solicitud",  # Alternativa
    "finalizar": "finalizar",
    "adjuntar_archivo": "adjuntar_archivo",
    "numero_reclamo_sgc": "numero_reclamo_sgc",
    "sgc": "numero_reclamo_sgc",  # Alternativa
    "comentarios": "comentarios",
    "observaciones": "comentarios"  # Alternativa
}
