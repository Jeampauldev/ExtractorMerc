# Guía de Migración a UnifiedS3Service

## Resumen

Se ha creado un nuevo servicio unificado `UnifiedS3Service` que consolida las funcionalidades de los servicios S3 existentes:
- `S3UploaderService`
- `AWSS3Service`
- `S3MassiveLoader`

## Cambios Realizados

### 1. Nuevo Servicio Unificado

**Archivo:** `src/services/unified_s3_service.py`

El `UnifiedS3Service` proporciona:
- Múltiples estructuras de rutas (LEGACY, CENTRAL, SIMPLE)
- Interfaz consistente para todas las operaciones S3
- Compatibilidad con los servicios existentes
- Registro en base de datos integrado

### 2. Actualizaciones de Importaciones

Los siguientes archivos han sido actualizados para usar `UnifiedS3Service`:

#### `src/services/__init__.py`
```python
# Agregado
from .unified_s3_service import UnifiedS3Service, S3PathStructure

__all__ = [
    # ... otros servicios
    'UnifiedS3Service',
    'S3PathStructure',
]
```

#### `src/services/s3_massive_loader.py`
```python
# Antes
from src.services.aws_s3_service import AWSS3Service, S3UploadResult

# Después
from src.services.unified_s3_service import UnifiedS3Service, S3PathStructure

# Inicialización
self.s3_service = UnifiedS3Service(path_structure=S3PathStructure.LEGACY)
```

#### `src/services/filtered_s3_uploader.py`
```python
# Antes
from src.services.aws_s3_service import AWSS3Service, S3UploadResult, S3Stats

# Después
from src.services.unified_s3_service import UnifiedS3Service, S3PathStructure

# Inicialización
self.s3_uploader = UnifiedS3Service(path_structure=S3PathStructure.CENTRAL)
```

#### `src/services/post_processing_service.py`
```python
# Antes
from src.services.aws_s3_service import upload_all_processed_files

# Después
from src.services.unified_s3_service import UnifiedS3Service, S3PathStructure

# Uso
s3_service = UnifiedS3Service(path_structure=S3PathStructure.CENTRAL)
s3_stats = s3_service.upload_company_files(company)
```

## Estructuras de Rutas Disponibles

### S3PathStructure.LEGACY
Compatible con `AWSS3Service`
```
empresa/numero_reclamo_sgc/filename
```

### S3PathStructure.CENTRAL
Compatible con `S3UploaderService`
```
service_type/file_type/filename
```

### S3PathStructure.SIMPLE
Estructura simplificada
```
company/date/filename
```

## Compatibilidad

El `UnifiedS3Service` mantiene compatibilidad con:
- Métodos existentes de `S3UploaderService`
- Métodos existentes de `AWSS3Service`
- Estructuras de datos de retorno
- Configuraciones de bucket y credenciales

## Próximos Pasos

1. **Pruebas de Integración**: Ejecutar tests para verificar que todas las funcionalidades funcionan correctamente
2. **Migración Gradual**: Los servicios antiguos pueden coexistir durante el período de transición
3. **Documentación**: Actualizar documentación de API para reflejar el nuevo servicio

## Beneficios

- **Consistencia**: Una sola interfaz para todas las operaciones S3
- **Mantenibilidad**: Código centralizado y más fácil de mantener
- **Flexibilidad**: Soporte para múltiples estructuras de rutas
- **Escalabilidad**: Fácil agregar nuevas funcionalidades S3