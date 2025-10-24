# Configuración AWS S3 para Producción

## Resumen

Esta guía describe los pasos necesarios para configurar AWS S3 en el sistema de post-procesamiento, incluyendo la creación de bucket, configuración de permisos, y activación del servicio en producción.

## Estado Actual

- ✅ **Servicio AWS S3 implementado** con modo simulado
- ✅ **Tabla de registro `s3_files_registry` creada**
- ✅ **Estructura organizacional definida**
- 🔄 **Pendiente:** Configuración de credenciales para producción

## Estructura de Archivos en S3

```
Bucket: extractorov-data (configurable)
│
└── raw_data/
    ├── RE2210202542239/
    │   ├── RE2210202542239_data_20251008_093221.json
    │   └── RE2210202542239_data_20251008_093023.json
    │
    ├── 63643842/
    │   └── 63643842_data_20251008_124510.json
    │
    ├── PQR_1_20251008_122537/
    │   └── PQR_1_20251008_122537_data_20251008_122538.json
    │
    └── misc_afinia/
        └── archivos_sin_numero_reclamo.json
```

## Configuración Paso a Paso

### 1. Crear Bucket S3

```bash
# AWS CLI
aws s3 mb s3://extractorov-data --region us-east-1

# O usar la consola de AWS
# https://s3.console.aws.amazon.com/s3/buckets
```

### 2. Crear Usuario IAM

**Nombre recomendado:** `extractorov-s3-uploader`

**Política JSON requerida:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ExtractorOVS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:HeadObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::extractorov-data",
        "arn:aws:s3:::extractorov-data/*"
      ]
    },
    {
      "Sid": "ExtractorOVS3List", 
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Obtener Credenciales

Después de crear el usuario IAM:

1. Ir a **IAM Console** → **Users** → `extractorov-s3-uploader`
2. Pestaña **Security credentials** 
3. **Create access key** → **Application running outside AWS**
4. Guardar `Access Key ID` y `Secret Access Key`

### 4. Configurar Variables de Entorno

#### Opción A: Archivo .env
```bash
# config/env/.env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=abc123...
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=extractorov-data
S3_BASE_PATH=oficina-virtual
```

#### Opción B: Variables de Sistema
```bash
# Windows
set AWS_ACCESS_KEY_ID=AKIA...
set AWS_SECRET_ACCESS_KEY=abc123...
set AWS_REGION=us-east-1
set AWS_S3_BUCKET_NAME=extractorov-data
set S3_BASE_PATH=oficina-virtual

# Linux/Mac
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=abc123...
export AWS_REGION=us-east-1
export AWS_S3_BUCKET_NAME=extractorov-data
export S3_BASE_PATH=oficina-virtual
```

### 5. Verificar Configuración

```python
# Verificar configuración
from src.services.aws_s3_service import AWSS3Service

s3_service = AWSS3Service()
print(f"Bucket: {s3_service.bucket_name}")
print(f"Región: {s3_service.aws_region}")
print(f"Modo simulado: {s3_service.is_simulated_mode}")

# Debería mostrar:
# Bucket: extractorov-data
# Región: us-east-1  
# Modo simulado: False
```

### 6. Probar Conexión

```python
# Probar conectividad básica
from src.services.aws_s3_service import AWSS3Service

s3_service = AWSS3Service()

# Verificar acceso al bucket
exists, metadata = s3_service.check_file_exists_in_s3("test-connectivity")
print(f"Conexión S3 exitosa: {not s3_service.is_simulated_mode}")

# Probar subida de archivo de prueba
from pathlib import Path
import json
import tempfile

# Crear archivo temporal de prueba
test_data = {"test": "connectivity", "timestamp": "2025-10-10"}
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(test_data, f)
    test_file = Path(f.name)

# Subir archivo de prueba
result = s3_service.upload_file_with_registry(
    file_path=test_file,
    empresa="test",
    numero_reclamo_sgc="CONNECTIVITY_TEST"
)

print(f"Resultado de prueba:")
print(f"  - Éxito: {result.success}")
print(f"  - S3 Key: {result.s3_key}")
print(f"  - S3 URL: {result.s3_url}")
print(f"  - Upload Source: {result.upload_source}")

# Limpiar archivo temporal
test_file.unlink()
```

## Activar AWS S3 en Producción

### 1. Actualizar Managers

```python
# En afinia_manager.py y aire_manager.py

# CAMBIAR:
post_result = run_post_processing_for_company('afinia', database_only=True)

# POR:
post_result = run_post_processing_for_company('afinia', database_only=False)
```

### 2. Probar Post-Procesamiento Completo

```python
# Probar con una empresa
from src.services.post_processing_service import run_post_processing_for_company

result = run_post_processing_for_company('afinia', database_only=False)

print(f"Resultado completo:")
print(f"  BD - Insertados: {result.db_inserted}, Duplicados: {result.db_duplicates}")
print(f"  S3 - Subidos: {result.s3_uploaded}, Pre-existentes: {result.s3_pre_existing}")
print(f"  Errores: {len(result.error_messages)}")
```

### 3. Verificar Registro S3

```python
# Verificar tabla de registro S3
from src.services.aws_s3_service import AWSS3Service

s3_service = AWSS3Service()
stats = s3_service.get_s3_registry_stats()

print("Estadísticas de S3 Registry:")
print(f"  Total archivos registrados: {stats['totals']['total_files']}")
print(f"  Total tamaño: {stats['totals']['total_size_bytes'] / 1024 / 1024:.2f} MB")

for company, company_stats in stats.get('by_company_status', {}).items():
    print(f"\n  {company.upper()}:")
    for status_key, status_data in company_stats.items():
        print(f"    - {status_key}: {status_data['count']} archivos")
```

## Configuración de Bucket Avanzada

### 1. Versioning (Recomendado)
```bash
# Habilitar versioning
aws s3api put-bucket-versioning \
  --bucket extractorov-data \
  --versioning-configuration Status=Enabled
```

### 2. Lifecycle Policy (Opcional)
```json
{
  "Rules": [
    {
      "ID": "ExtractorOVArchive", 
      "Status": "Enabled",
      "Filter": {
        "Prefix": "oficina-virtual/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90, 
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

### 3. Bucket Policy (Opcional - Acceso Restringido)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RestrictToExtractorOVUser",
      "Effect": "Deny",
      "NotPrincipal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/extractorov-s3-uploader"
      },
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::extractorov-data",
        "arn:aws:s3:::extractorov-data/*"
      ]
    }
  ]
}
```

## Monitoreo y Alertas

### 1. CloudWatch Métricas
- `NumberOfObjects`
- `BucketSizeBytes`
- `AllRequests`
- `4xxErrors`
- `5xxErrors`

### 2. Alertas Recomendadas
```json
{
  "AlarmName": "ExtractorOV-S3-HighErrorRate",
  "MetricName": "4xxErrors",
  "Namespace": "AWS/S3",
  "Statistic": "Sum",
  "Period": 300,
  "EvaluationPeriods": 2,
  "Threshold": 10,
  "ComparisonOperator": "GreaterThanThreshold"
}
```

## Troubleshooting

### Error: NoCredentialsError
```
[s3_service][client] Credenciales AWS no encontradas - habilitando modo simulado
```
**Solución:** Verificar variables de entorno `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY`

### Error: AccessDenied
```
User is not authorized to perform: s3:PutObject on resource
```
**Solución:** Verificar política IAM del usuario, debe incluir permisos `s3:PutObject`

### Error: NoSuchBucket
```
The specified bucket does not exist
```
**Solución:** Crear el bucket o verificar variable `AWS_S3_BUCKET_NAME`

### Error: InvalidRegion
```
The specified region does not exist
```
**Solución:** Verificar variable `AWS_REGION`, usar región válida como `us-east-1`

## Comandos de Diagnóstico

### Verificar Conectividad AWS CLI
```bash
# Listar buckets
aws s3 ls

# Verificar acceso al bucket específico
aws s3 ls s3://extractorov-data/

# Probar subida
echo "test" > test.txt
aws s3 cp test.txt s3://extractorov-data/test.txt
rm test.txt
```

### Verificar Desde Python
```python
import boto3
from botocore.exceptions import ClientError

try:
    s3 = boto3.client('s3')
    response = s3.list_buckets()
    print("Buckets disponibles:")
    for bucket in response['Buckets']:
        print(f"  - {bucket['Name']}")
        
    # Verificar bucket específico
    s3.head_bucket(Bucket='extractorov-data')
    print("\nBucket 'extractorov-data' accesible ✅")
    
except ClientError as e:
    print(f"Error de AWS: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## Costos Estimados

### Almacenamiento (us-east-1)
- **Standard:** $0.023 por GB/mes
- **Standard-IA:** $0.0125 por GB/mes  
- **Glacier:** $0.004 por GB/mes

### Requests
- **PUT/COPY/POST:** $0.0005 por 1,000 requests
- **GET/SELECT:** $0.0004 por 1,000 requests

### Estimación Mensual (1000 PQRs/día)
- **Archivos:** ~30,000 archivos/mes
- **Tamaño:** ~3 GB/mes (100 KB promedio por archivo)
- **Costo Storage Standard:** ~$0.07/mes
- **Costo Requests:** ~$0.02/mes
- **Total estimado:** ~$0.10/mes

---

**Autor:** ISES | Analyst Data Jeam Paul Arcon Solano  
**Fecha:** Octubre 2025  
**Estado:** Documentación Completa ✅