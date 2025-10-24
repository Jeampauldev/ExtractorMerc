# Visión General del Sistema - ExtractorOV Modular

## Descripción del Sistema

ExtractorOV Modular es un sistema profesional de extracción automatizada de datos de PQRs (Peticiones, Quejas y Reclamos) desde las plataformas de Oficina Virtual de Afinia y Aire en Barranquilla, Colombia.

## Arquitectura General

### Principios Arquitectónicos

1. **Separación de Responsabilidades**: Cada componente tiene una responsabilidad específica y bien definida
2. **Modularidad**: Los componentes son intercambiables y reutilizables
3. **Escalabilidad**: El sistema puede manejar incrementos en la carga de trabajo
4. **Mantenibilidad**: El código es limpio, documentado y fácil de modificar
5. **Confiabilidad**: Manejo robusto de errores y recuperación automática

### Vista de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                    ExtractorOV Modular                         │
├─────────────────────────────────────────────────────────────────┤
│  Capa de Presentación                                          │
│  ┌─────────────────┐  ┌─────────────────┐                    │
│  │ CLI Managers    │  │ Web Dashboard   │                    │
│  │ (afinia_manager │  │ (Futuro)        │                    │
│  │  aire_manager)  │  │                 │                    │
│  └─────────────────┘  └─────────────────┘                    │
├─────────────────────────────────────────────────────────────────┤
│  Capa de Lógica de Negocio                                     │
│  ┌─────────────────┐  ┌─────────────────┐                    │
│  │ Afinia Extractor│  │ Aire Extractor  │                    │
│  └─────────────────┘  └─────────────────┘                    │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │ PQR Processor   │  │ Filter Manager  │  │ Pagination    │ │
│  └─────────────────┘  └─────────────────┘  │ Manager       │ │
│                                           └───────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Capa de Servicios                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │ Database        │  │ S3 Uploader     │  │ Download      │ │
│  │ Service         │  │ Service         │  │ Manager       │ │
│  └─────────────────┘  └─────────────────┘  └───────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Capa de Infraestructura                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │ Browser         │  │ Authentication  │  │ Logging       │ │
│  │ Manager         │  │ Handler         │  │ System        │ │
│  └─────────────────┘  └─────────────────┘  └───────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Capa de Datos                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │ PostgreSQL RDS  │  │ Amazon S3       │  │ Local Files   │ │
│  │ (Structured)    │  │ (Documents)     │  │ (Logs/Cache)  │ │
│  └─────────────────┘  └─────────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes Principales

### 1. Gestores de Extracción (Managers)

**Ubicación**: Raíz del proyecto
- `afinia_manager.py`: Coordina extracción de datos de Afinia
- `aire_manager.py`: Coordina extracción de datos de Aire

**Responsabilidades**:
- Inicialización del sistema
- Coordinación de componentes
- Manejo de flujo principal de extracción
- Reporte de resultados

### 2. Extractores Principales

**Ubicación**: `src/extractors/`
- `afinia/oficina_virtual_afinia_modular.py`
- `aire/oficina_virtual_aire_modular.py`

**Responsabilidades**:
- Automatización del navegador
- Autenticación en plataformas
- Navegación a secciones específicas
- Extracción de datos estructurados

### 3. Componentes Modulares

**Ubicación**: `src/components/`

#### Gestores de Filtros
- `afinia_filter_manager.py`
- `aire_filter_manager.py`

Funciones:
- Aplicación de filtros de fecha
- Filtros por estado de PQR
- Validación de criterios de búsqueda

#### Gestores de Paginación
- `afinia_pagination_manager.py`
- `aire_pagination_manager.py`

Funciones:
- Control de navegación entre páginas
- Checkpoint y recuperación
- Manejo de límites de extracción

#### Procesadores de PQRs
- `afinia_pqr_processor.py`
- `aire_pqr_processor.py`

Funciones:
- Extracción de metadatos
- Descarga de adjuntos
- Validación de datos
- Estructura de salida consistente

### 4. Servicios de Datos

**Ubicación**: `src/services/`

#### Database Service
- Conexión a PostgreSQL RDS
- Operaciones CRUD optimizadas
- Gestión de transacciones
- Pool de conexiones

#### S3 Uploader Service
- Carga de archivos a Amazon S3
- Gestión de metadatos
- Compresión automática
- Control de versiones

#### Data Loader Service
- Procesamiento de datos masivos
- Validación y limpieza
- Transformaciones ETL
- Carga a base de datos

### 5. Núcleo del Sistema

**Ubicación**: `src/core/`

#### Browser Manager
- Inicialización de navegadores
- Configuración de opciones
- Manejo de contextos
- Limpieza de recursos

#### Authentication Handler
- Gestión de credenciales
- Procesos de login automático
- Manejo de sesiones
- Renovación de tokens

## Patrones de Diseño Implementados

### 1. Factory Pattern
Utilizado para la creación de navegadores y extractores específicos según la plataforma.

```python
class ExtractorFactory:
    @staticmethod
    def create_extractor(platform: str):
        if platform == "afinia":
            return AfiniaExtractor()
        elif platform == "aire":
            return AireExtractor()
```

### 2. Strategy Pattern
Implementado en procesadores de datos para diferentes algoritmos de extracción.

```python
class DataProcessor:
    def __init__(self, strategy: ProcessingStrategy):
        self.strategy = strategy
    
    def process(self, data):
        return self.strategy.execute(data)
```

### 3. Observer Pattern
Usado en el sistema de monitoring para notificaciones de eventos.

```python
class ExtractionMonitor:
    def __init__(self):
        self.observers = []
    
    def notify(self, event_type, data):
        for observer in self.observers:
            observer.update(event_type, data)
```

### 4. Command Pattern
Implementado para operaciones de extracción con capacidad de deshacer y repetir.

```python
class ExtractionCommand:
    def execute(self):
        # Lógica de extracción
        pass
    
    def undo(self):
        # Lógica de rollback
        pass
```

## Flujo de Datos

### 1. Inicialización
1. Carga de configuración desde variables de entorno
2. Inicialización de servicios (DB, S3, Logging)
3. Verificación de conectividad
4. Preparación de contexto de navegador

### 2. Autenticación
1. Navegación a página de login
2. Introducción de credenciales
3. Manejo de CAPTCHA si es necesario
4. Verificación de login exitoso

### 3. Configuración de Filtros
1. Navegación a sección de PQRs
2. Aplicación de filtros de fecha
3. Aplicación de filtros de estado
4. Confirmación de criterios aplicados

### 4. Extracción de Datos
1. Inicialización del procesador de paginación
2. Extracción de datos de página actual
3. Navegación a página siguiente
4. Repetición hasta completar todas las páginas

### 5. Procesamiento y Almacenamiento
1. Validación de datos extraídos
2. Descarga de adjuntos asociados
3. Almacenamiento en base de datos
4. Carga de archivos a S3
5. Generación de reportes

## Configuración del Sistema

### Variables de Entorno Críticas

```bash
# Credenciales de servicios
OV_AFINIA_USERNAME=usuario_afinia
OV_AFINIA_PASSWORD=password_afinia
OV_AIRE_USERNAME=usuario_aire  
OV_AIRE_PASSWORD=password_aire

# Base de datos
RDS_HOST=instancia.region.rds.amazonaws.com
RDS_PORT=5432
RDS_DATABASE=extractorov
RDS_USERNAME=db_user
RDS_PASSWORD=db_password

# Amazon S3
AWS_ACCESS_KEY_ID=access_key
AWS_SECRET_ACCESS_KEY=secret_key
S3_BUCKET_NAME=bucket-extractorov
S3_REGION=us-east-1

# Configuración de navegador
HEADLESS_MODE=true
PAGE_TIMEOUT=30000
NAVIGATION_TIMEOUT=60000
DOWNLOAD_TIMEOUT=120000

# Logging
LOG_LEVEL=INFO
LOG_MAX_FILES=10
LOG_MAX_SIZE_MB=50
```

## Métricas y Monitoreo

### Métricas de Rendimiento
- Registros procesados por minuto
- Tiempo promedio de extracción por PQR
- Tasa de éxito de descargas
- Uso de memoria y CPU
- Latencia de red

### Métricas de Calidad
- Tasa de errores por componente
- Precisión de datos extraídos
- Integridad de adjuntos descargados
- Consistencia de formatos de datos

### Alertas Configuradas
- Fallos de autenticación
- Timeouts de navegación
- Errores de base de datos
- Problemas de conectividad S3
- Límites de memoria excedidos

## Seguridad

### Gestión de Credenciales
- Variables de entorno para credenciales sensibles
- No almacenamiento en código fuente
- Cifrado de credenciales en tránsito
- Rotación periódica de credenciales

### Validación de Datos
- Sanitización de entradas
- Validación de tipos de datos
- Verificación de integridad de archivos
- Logs sanitizados sin información sensible

### Comunicaciones
- HTTPS obligatorio para todas las conexiones
- Verificación de certificados SSL
- Retry con backoff exponencial
- Rate limiting para evitar bloqueos

## Escalabilidad

### Escalabilidad Horizontal
- Múltiples instancias del sistema
- Balanceador de carga
- Queue system para distribuir trabajo
- Coordinación mediante base de datos

### Escalabilidad Vertical
- Configuración de recursos ajustable
- Pool de conexiones dimensionable
- Cache configurable
- Límites de memoria ajustables

### Optimizaciones
- Procesamiento paralelo de PQRs
- Cache de datos frecuentes
- Compresión de archivos
- Índices optimizados en base de datos

## Mantenimiento

### Monitoreo Continuo
- Health checks automatizados
- Alertas por métricas críticas
- Dashboards de estado en tiempo real
- Reportes de rendimiento diarios

### Backup y Recuperación
- Backup automático de base de datos
- Versionado de archivos en S3
- Procedimientos de recuperación documentados
- Testing periódico de backups

### Actualizaciones
- Versionado semántico del sistema
- Proceso de deployment automatizado
- Rollback automático ante fallos
- Testing previo en ambiente staging

---

**Documento de Arquitectura del Sistema ExtractorOV Modular**
*Versión: 2.0*
*Última actualización: Octubre 2025*