# Integración del Post-Procesamiento con Managers

## Resumen

Este documento describe la implementación completa del sistema de post-procesamiento integrado que coordina automáticamente la carga de datos a base de datos y AWS S3 después de la extracción de PQRs.

## Arquitectura del Sistema

```
FLUJO COMPLETO DEL SISTEMA
==========================

1. EXTRACCIÓN
   afinia_manager.py / aire_manager.py
   ↓
   Descarga PQRs → data/downloads/{empresa}/oficina_virtual/processed/
   
2. POST-PROCESAMIENTO AUTOMÁTICO  
   src/services/post_processing_service.py
   ↓
   ├── CARGA A BASE DE DATOS
   │   └── src/services/bulk_database_loader.py
   │       ├── Escanea archivos JSON procesados
   │       ├── Genera hash SHA-256 por registro
   │       ├── Detecta duplicados (hash + numero_radicado)
   │       ├── Inserta/actualiza en PostgreSQL RDS
   │       └── Reporta estadísticas
   │
   └── CARGA A AWS S3 (opcional)
       └── src/services/aws_s3_service.py
           ├── Sube archivos JSON organizados por fecha
           ├── Detecta archivos pre-existentes
           ├── Registra en tabla s3_files_registry
           └── Reporta estadísticas

3. RESULTADO CONSOLIDADO
   └── Métricas completas en respuesta del manager
```

## Componentes Implementados

### 1. Servicio de Post-Procesamiento (`post_processing_service.py`)

**Funcionalidades:**
- Coordina carga a BD y S3
- Manejo de errores transversales
- Reportes consolidados por empresa
- Modo `database_only` para omitir S3

**Métodos principales:**
```python
# Procesar una empresa específica
result = run_post_processing_for_company('afinia', database_only=True)

# Procesar todas las empresas
stats = run_complete_post_processing()

# Generar reporte completo
report = generate_post_processing_report()
```

### 2. Carga Masiva a Base de Datos (`bulk_database_loader.py`)

**Funcionalidades:**
- Escanea archivos JSON en `data/downloads/{empresa}/oficina_virtual/processed/`
- Mapea campos JSON a estructura de BD
- Genera hash SHA-256 basado en campos clave
- Detecta duplicados con prioridades:
  1. **Hash exacto** (mismo contenido)
  2. **Número de radicado** (actualizar si hash cambió)
- Manejo transaccional con rollback
- Estadísticas detalladas de carga

**Tablas de destino:**
- `data_general.ov_afinia`
- `data_general.ov_aire`

**Hash SHA-256 basado en:**
- `numero_radicado`
- `fecha` 
- `tipo_pqr`
- `nic`
- `documento_identidad`

### 3. Servicio AWS S3 (`aws_s3_service.py`)

**Funcionalidades:**
- Estructura organizada: `oficina-virtual/{empresa}/año/mes/día/{numero_reclamo_sgc}/{archivo}.json`
- Detección automática de archivos pre-existentes
- Modo simulado cuando no hay credenciales AWS
- Registro completo en tabla `s3_files_registry`

**Tabla de registro S3:**
```sql
data_general.s3_files_registry
├── filename, s3_bucket, s3_key, s3_url
├── numero_reclamo_sgc (enlace con ov_afinia/ov_aire)  
├── empresa, file_size, file_type, content_type
├── upload_status: pending, uploaded, error, pre_existing
├── upload_source: bot, manual, pre_existing
├── file_hash (SHA-256 para integridad)
└── timestamps y metadata JSON
```

## Integración con Managers

### Antes (Solo Extracción)
```python
# afinia_manager.py
result = await self.extractor.run_full_extraction(...)
return result
```

### Después (Extracción + Post-Procesamiento)
```python
# afinia_manager.py
result = await self.extractor.run_full_extraction(...)

# POST-PROCESAMIENTO AUTOMÁTICO
from src.services.post_processing_service import run_post_processing_for_company
post_result = run_post_processing_for_company('afinia', database_only=True)

# MÉTRICAS INTEGRADAS EN RESPUESTA
result['post_processing'] = {
    'success': post_result.success,
    'db_inserted': post_result.db_inserted,
    'db_updated': post_result.db_updated, 
    'db_duplicates': post_result.db_duplicates,
    's3_uploaded': post_result.s3_uploaded,
    'processing_time': post_result.total_processing_time
}

return result
```

## Estado Actual

### ✅ **IMPLEMENTADO Y PROBADO**

1. **Carga a Base de Datos**
   - 181 archivos JSON procesados para Afinia
   - 10 archivos JSON procesados para Aire  
   - Sistema de hash y detección de duplicados funcionando
   - 115 registros insertados inicialmente, 76 duplicados manejados
   - Integración completa con managers

2. **Estructura de Base de Datos**
   - Tablas `ov_afinia` y `ov_aire` operativas
   - Columna `hash_registro` implementada con índices
   - Tabla `s3_files_registry` creada y lista

3. **Post-Procesamiento Integrado**
   - Modo `database_only` implementado y probado
   - Managers actualizados para ejecutar post-procesamiento automáticamente
   - Métricas consolidadas en respuesta de managers

### 🔄 **EN CONFIGURACIÓN**

4. **AWS S3**
   - Servicio implementado con modo simulado
   - Estructura organizacional definida
   - Registro en BD implementado
   - **Pendiente:** Configuración de credenciales AWS para producción

## Configuración Requerida para AWS S3

### Variables de Entorno Necesarias
```bash
# Credenciales AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Configuración S3
AWS_S3_BUCKET_NAME=extractorov-data
S3_BASE_PATH=oficina-virtual
```

### Permisos IAM Requeridos
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject", 
        "s3:HeadObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name/*",
        "arn:aws:s3:::your-bucket-name"
      ]
    }
  ]
}
```

## Activar AWS S3 en Producción

### Paso 1: Configurar Credenciales
```python
# Verificar configuración
from src.services.aws_s3_service import AWSS3Service

s3_service = AWSS3Service()
print(f"Bucket: {s3_service.bucket_name}")
print(f"Región: {s3_service.aws_region}")
print(f"Modo simulado: {s3_service.is_simulated_mode}")
```

### Paso 2: Actualizar Managers para AWS S3
```python
# En afinia_manager.py y aire_manager.py, cambiar:
post_result = run_post_processing_for_company('afinia', database_only=True)

# Por:
post_result = run_post_processing_for_company('afinia', database_only=False)
```

### Paso 3: Verificar Carga Completa
```python
# Probar carga completa
from src.services.post_processing_service import run_complete_post_processing
stats = run_complete_post_processing()
```

## Comandos de Verificación

### Verificar Estado de BD
```python
from src.services.bulk_database_loader import BulkDatabaseLoader
loader = BulkDatabaseLoader()
stats = loader.get_database_stats()
print(stats)
```

### Verificar Registro S3
```python
from src.services.aws_s3_service import AWSS3Service
s3_service = AWSS3Service()
stats = s3_service.get_s3_registry_stats()
print(stats)
```

### Ejecutar Post-Procesamiento Manual
```python
from src.services.post_processing_service import run_post_processing_for_company

# Solo BD
result_bd = run_post_processing_for_company('afinia', database_only=True)

# BD + S3 (cuando esté configurado)
result_full = run_post_processing_for_company('afinia', database_only=False)
```

## Métricas y Monitoreo

### Estructura de Respuesta del Manager
```python
{
  'success': True,
  'duration': 245.3,
  'service': 'afinia',
  'files_downloaded': 181,
  'pqr_processed': 181,
  
  'post_processing': {
    'success': True,
    'db_inserted': 15,
    'db_updated': 3,
    'db_duplicates': 163,
    's3_uploaded': 181,
    's3_pre_existing': 0,
    'processing_time': 45.2
  }
}
```

### Logs Estructurados
```
[2025-10-10_01:15:20][afinia][manager][POST-PROCESAMIENTO] Iniciando carga a base de datos y S3...
[2025-10-10_01:15:25][afinia][bulk_loader][load_processed_json_to_database] Cargando datos a BD para afinia...
[2025-10-10_01:15:30][afinia][bulk_loader][load_processed_json_to_database] BD completado: 15 insertados, 3 actualizados
[2025-10-10_01:15:30][afinia][manager][POST-PROCESAMIENTO] Completado exitosamente
```

## Próximos Pasos

1. **Configurar AWS S3** con credenciales correctas
2. **Implementar monitoreo incremental** para detectar solo cambios
3. **Crear scheduler automático** para ejecución programada
4. **Desarrollar panel de métricas** en tiempo real
5. **Implementar sistema de alertas** para errores o anomalías

---

**Autor:** ISES | Analyst Data Jeam Paul Arcon Solano  
**Fecha:** Octubre 2025  
**Estado:** Post-Procesamiento BD ✅ | AWS S3 🔄 | Integración ✅