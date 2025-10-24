# Servicios ExtractorOV - RDS y S3

Este directorio contiene los servicios desarrollados para manejar la carga de datos extraídos por los sistemas de Afinia y Aire tanto a la base de datos RDS como a AWS S3.

## 📋 Índice

- [Servicios Disponibles](#servicios-disponibles)
- [Configuración](#configuración)
- [Uso Básico](#uso-básico)
- [Ejemplos Avanzados](#ejemplos-avanzados)
- [Estructura de Base de Datos](#estructura-de-base-de-datos)
- [Estructura S3](#estructura-s3)
- [Troubleshooting](#troubleshooting)

## 🚀 Servicios Disponibles

### 1. DatabaseService
**Archivo:** `database_service.py`

Servicio unificado para operaciones de base de datos que maneja la conexión y carga de datos a las tablas `ov_afinia` y `ov_aire` en el esquema `data` de RDS.

**Características:**
- Conexión segura a RDS usando configuración de entorno
- Carga de datos JSON con validación automática
- Control de duplicados por hash y número de radicado
- Transacciones seguras con rollback automático en caso de error
- Estadísticas detalladas de tablas y procesamiento

### 2. DataLoaderService
**Archivo:** `data_loader_service.py`

Servicio para carga masiva de archivos JSON que automatiza el procesamiento de múltiples archivos con detección automática del tipo de servicio.

**Características:**
- Procesamiento por lotes con soporte paralelo
- Detección automática de tipo de servicio (Afinia/Aire)
- Validación de archivos JSON antes del procesamiento
- Estadísticas detalladas con reportes automáticos
- Manejo robusto de errores con reintentos

### 3. S3UploaderService
**Archivo:** `s3_uploader_service.py`

Servicio para carga de archivos (PDFs, imágenes, JSON) a AWS S3 con organización automática por empresa y tipo de archivo.

**Características:**
- Carga organizada por servicio y tipo de archivo
- Metadatos detallados para cada archivo
- Compresión automática para archivos de texto (opcional)
- Encriptación AES256 por defecto
- Reintentos automáticos con backoff exponencial

## ⚙️ Configuración

### Variables de Entorno Requeridas

#### Para RDS:
```bash
# RDS Configuration
RDS_HOST=your-rds-endpoint.rds.amazonaws.com
RDS_DATABASE=your-database-name
RDS_USERNAME=your-username
RDS_PASSWORD=your-password
RDS_PORT=3306
RDS_CHARSET=utf8mb4
```

#### Para S3:
```bash
# S3 Configuration
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2
```

### Archivo de Configuración
Las variables pueden configurarse en:
- `config/env/.env`
- `.env` en la raíz del proyecto
- Variables de entorno del sistema

## 🔧 Uso Básico

### Carga Individual de Archivo JSON a RDS

```python
from services import DatabaseService

# Crear servicio
db_service = DatabaseService()

# Cargar archivo JSON de Afinia
result = db_service.load_data_from_json(
    service_type='afinia',
    json_file_path='data/downloads/afinia/data.json',
    check_duplicates=True
)

print(f"Insertados: {result.records_inserted}")
print(f"Saltados: {result.records_skipped}")
```

### Carga Masiva de Archivos

```python
from services import DataLoaderService

# Crear servicio
loader = DataLoaderService(max_workers=4)

# Procesar directorio completo
stats = loader.process_directory(
    directory='data/downloads/afinia',
    service_type='afinia',
    check_duplicates=True,
    recursive=True,
    parallel=True
)

# Generar reporte
report = loader.generate_processing_report(stats, 'processing_report.txt')
print(report)
```

### Carga de Archivos a S3

```python
from services import S3UploaderService

# Crear servicio
s3_service = S3UploaderService()

# Cargar archivo individual
result = s3_service.upload_file(
    file_path='data/downloads/afinia/document.pdf',
    service_type='afinia',
    file_type='pdfs'
)

# Cargar directorio completo
batch_result = s3_service.upload_directory(
    directory_path='data/downloads/afinia/screenshots',
    service_type='afinia',
    file_type='screenshots',
    file_patterns=['*.png', '*.jpg']
)
```

## 📊 Ejemplos Avanzados

### Procesamiento Completo con Validación

```python
from services import DatabaseService, S3UploaderService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Validar entorno
db_service = DatabaseService()
s3_service = S3UploaderService()

# Validar conexiones
db_ready = db_service.test_connection()
s3_ready = s3_service.test_connection()

if db_ready and s3_ready:
    # Procesar datos JSON a RDS
    json_result = db_service.load_data_from_json('afinia', 'data.json')
    
    # Cargar archivos a S3
    s3_result = s3_service.upload_file('document.pdf', 'afinia', 'pdfs')
    
    print("Procesamiento completado exitosamente")
else:
    print("Error en configuración del entorno")
```

### Uso de CLI Integrado

```bash
# Probar conexión RDS
python -m services.database_service --test-connection

# Validar entorno completo
python -m services.database_service --validate-env

# Obtener estadísticas de tabla
python -m services.database_service --table-stats ov_afinia

# Cargar archivo JSON
python -m services.data_loader_service \
    --files data/afinia_data.json \
    --service-type afinia

# Cargar directorio completo
python -m services.data_loader_service \
    --directory data/downloads/afinia \
    --service-type afinia \
    --report-file report.txt

# Probar conexión S3
python -m services.s3_uploader_service --test-connection

# Cargar archivo a S3
python -m services.s3_uploader_service \
    --upload-file document.pdf \
    --service-type afinia \
    --file-type pdfs

# Obtener estadísticas S3
python -m services.s3_uploader_service --stats
```

## 🗄️ Estructura de Base de Datos

### Esquema: `data`

#### Tabla: `ov_afinia`
```sql
CREATE TABLE data.ov_afinia (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nic VARCHAR(50),
    fecha DATE,
    documento_identidad VARCHAR(20),
    nombres_apellidos VARCHAR(200),
    correo_electronico VARCHAR(100),
    telefono VARCHAR(20),
    celular VARCHAR(20),
    tipo_pqr VARCHAR(100),
    canal_respuesta VARCHAR(50),
    numero_radicado VARCHAR(50),
    estado_solicitud VARCHAR(50),
    lectura VARCHAR(50),
    documento_prueba VARCHAR(255),
    cuerpo_reclamacion TEXT,
    finalizar VARCHAR(50),
    adjuntar_archivo VARCHAR(255),
    numero_reclamo_sgc VARCHAR(50),
    comentarios TEXT,
    extraction_timestamp DATETIME,
    page_url VARCHAR(500),
    data_hash VARCHAR(32),
    file_source VARCHAR(255),
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_numero_radicado (numero_radicado),
    INDEX idx_estado_solicitud (estado_solicitud),
    INDEX idx_data_hash (data_hash),
    INDEX idx_processed_at (processed_at)
);
```

#### Tabla: `ov_aire`
Estructura idéntica a `ov_afinia` pero para datos de Aire.

## ☁️ Estructura S3

### Organización de Carpetas

```
bucket-name/
├── afinia/
│   ├── oficina_virtual/
│   │   ├── pdfs/2024/10/08/documento.pdf
│   │   ├── data/2024/10/08/datos.json
│   │   └── screenshots/2024/10/08/captura.png
│   ├── reports/
│   └── logs/
├── aire/
│   ├── oficina_virtual/
│   │   ├── pdfs/2024/10/08/documento.pdf
│   │   ├── data/2024/10/08/datos.json
│   │   └── screenshots/2024/10/08/captura.png
│   ├── reports/
│   └── logs/
└── general/
    ├── reports/
    ├── logs/
    └── backups/
```

### Metadatos Automáticos

Cada archivo cargado incluye metadatos:
- `original-filename`: Nombre original del archivo
- `file-size`: Tamaño en bytes
- `upload-timestamp`: Timestamp de carga
- `service-type`: Tipo de servicio (afinia/aire/general)
- `file-extension`: Extensión del archivo
- `uploader`: Identificador del sistema (extractorov-modular)
- `file-hash`: Hash MD5 del archivo

## 🔍 Troubleshooting

### Errores Comunes

#### Error de Conexión RDS
```
Error conectando a RDS: (2003, "Can't connect to MySQL server")
```
**Solución:**
- Verificar que `RDS_HOST`, `RDS_USERNAME`, `RDS_PASSWORD` estén configurados
- Comprobar reglas de seguridad del grupo de seguridad RDS
- Validar que la instancia RDS esté activa

#### Error de Conexión S3
```
Error conectando a S3: NoSuchBucket
```
**Solución:**
- Verificar que `AWS_S3_BUCKET_NAME` existe y es accesible
- Comprobar permisos del usuario IAM
- Validar `AWS_REGION` correcta

#### Error de Permisos S3
```
Error S3: AccessDenied
```
**Solución:**
- Verificar permisos IAM del usuario:
  - `s3:GetObject`
  - `s3:PutObject`
  - `s3:ListBucket`

#### Duplicados en RDS
Los duplicados se manejan automáticamente usando:
- Hash MD5 de datos clave
- Número de radicado único

#### Archivos Grandes en S3
Para archivos >25MB se usa carga multipart automática.

### Logs y Monitoreo

Los servicios generan logs detallados en:
- Consola (nivel INFO)
- Archivo de log específico (si se configura)
- Sistema de logging unificado (`data/logs/`)

### Validación de Entorno

Usar los comandos de validación antes de procesar:

```bash
# Validar RDS
python -m services.database_service --validate-env

# Validar S3
python -m services.s3_uploader_service --test-connection
```

## 📚 Recursos Adicionales

- **Ejemplo Completo:** `examples/data_processing/load_data_to_rds_and_s3.py`
- **Configuración de Entorno:** `config/env/.env.example`
- **Documentación de API:** Docstrings en cada servicio
- **Tests:** `tests/unit/test_services.py` (pendiente)

## 🤝 Contribución

Para contribuir a estos servicios:

1. Seguir las convenciones de código existentes
2. Agregar docstrings detallados
3. Incluir manejo de errores robusto
4. Agregar logging apropiado
5. Actualizar esta documentación

---

**Nota:** Estos servicios están diseñados para funcionar sin ejecutar carga real hasta que el entorno esté completamente configurado y validado.