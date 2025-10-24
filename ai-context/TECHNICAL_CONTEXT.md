# Contexto Técnico - ExtractorOV_Modular

## Para Agentes IA: Información Técnica Detallada

Este documento proporciona contexto técnico profundo sobre la arquitectura y funcionamiento del sistema para facilitar el trabajo de agentes IA.

---

## Estado Actual del Sistema

### ✅ Completado y Funcional
- **Sistema de logging unificado** con formato profesional
- **Limpieza de emojis** en archivos críticos, componentes y servicios
- **Managers principales** (afinia_manager.py, aire_manager.py) funcionando
- **Servicios de datos** (database_service.py, s3_uploader_service.py) operativos
- **Componentes modulares** (pagination, filters, downloads) activos

### 🔄 En Desarrollo/Pendiente
- **Carga masiva a RDS** para tablas `ov_afinia` y `ov_aire` en esquema `data`
- **Integración completa S3** con metadatos y compresión
- **Scripts de mantenimiento** automatizados
- **Dashboard web** de monitoreo

---

## Arquitectura de Datos

### Base de Datos RDS (PostgreSQL)
```sql
-- Esquema principal para datos de producción
CREATE SCHEMA IF NOT EXISTS data;

-- Tabla para datos de Afinia
CREATE TABLE data.ov_afinia (
    id SERIAL PRIMARY KEY,
    pqr_number VARCHAR(50) UNIQUE NOT NULL,
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pqr_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'processed',
    file_paths TEXT[],
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para datos de Aire
CREATE TABLE data.ov_aire (
    id SERIAL PRIMARY KEY,
    pqr_number VARCHAR(50) UNIQUE NOT NULL,
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pqr_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'processed',
    file_paths TEXT[],
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Estructura S3
```
s3://tu-bucket-name/
├── afinia/
│   ├── raw-data/          # Datos JSON sin procesar
│   ├── processed/         # Datos procesados y validados
│   ├── attachments/       # Adjuntos descargados
│   └── backups/           # Respaldos automáticos
└── aire/
    ├── raw-data/
    ├── processed/
    ├── attachments/
    └── backups/
```

---

## Flujo de Datos Detallado

### 1. Inicialización
```python
# afinia_manager.py - Punto de entrada principal
manager = AfiniaManager(headless=True, test_mode=False)
result = await manager.run_extraction()
```

### 2. Autenticación y Navegación
```python
# src/extractors/afinia/oficina_virtual_afinia_modular.py
extractor = OficinaVirtualAfiniaModular()
await extractor.authenticate(username, password)
await extractor.navigate_to_pqr_section()
```

### 3. Aplicación de Filtros
```python
# src/components/afinia_filter_manager.py
filter_manager = AfiniaFilterManager()
await filter_manager.apply_date_filters(start_date, end_date)
await filter_manager.apply_status_filter("Finalizado")
```

### 4. Extracción de Datos
```python
# src/components/afinia_pagination_manager.py
pagination_manager = AfiniaPaginationManager()
results = await pagination_manager.process_all_pages()
```

### 5. Procesamiento y Almacenamiento
```python
# src/services/data_loader_service.py
loader = DataLoaderService()
await loader.load_to_rds(results, table='ov_afinia')

# src/services/s3_uploader_service.py
s3_service = S3UploaderService()
await s3_service.upload_batch(files, prefix='afinia/processed/')
```

---

## Componentes Críticos

### 1. Sistema de Logging Unificado
**Archivo:** `src/config/unified_logging_config.py`

```python
# Formato profesional implementado
class ProfessionalFormatter(logging.Formatter):
    def format(self, record):
        # [YYYY-MM-DD_HH:MM:SS][servicio][core][componente][LEVEL] - mensaje
        timestamp = self.formatTime(record, '%Y-%m-%d_%H:%M:%S')
        return f"[{timestamp}][{service}][{core}][{component}][{record.levelname}] - {clean_msg}"
```

### 2. Manager de Paginación
**Archivo:** `src/components/afinia_pagination_manager.py`

**Funcionalidades clave:**
- Control de estado de paginación
- Checkpoint/resume functionality
- Manejo de errores y reintentos
- Límites configurables de registros

### 3. Procesador de PQRs
**Archivo:** `src/components/afinia_pqr_processor.py`

**Responsabilidades:**
- Extracción de metadatos de PQRs
- Descarga de adjuntos
- Validación de datos
- Estructura de datos consistente

---

## Patrones de Diseño Utilizados

### 1. Factory Pattern
```python
# src/core/browser/browser_factory.py
class BrowserFactory:
    @staticmethod
    def create_browser(browser_type: str, headless: bool = True):
        if browser_type == "playwright":
            return PlaywrightBrowser(headless=headless)
        # Otros navegadores...
```

### 2. Strategy Pattern
```python
# src/processors/data/data_processor.py
class DataProcessor:
    def __init__(self, strategy: ProcessingStrategy):
        self.strategy = strategy
    
    def process(self, data):
        return self.strategy.process(data)
```

### 3. Observer Pattern
```python
# src/utils/performance_monitor.py
class PerformanceMonitor:
    def notify_observers(self, event_type: str, data: dict):
        for observer in self.observers:
            observer.update(event_type, data)
```

---

## Configuración del Sistema

### Variables de Entorno Críticas
```bash
# Credenciales de servicios
OV_AFINIA_USERNAME=usuario_oficial
OV_AFINIA_PASSWORD=password_seguro

# Configuración de base de datos
RDS_HOST=tu-instancia.region.rds.amazonaws.com
RDS_PORT=5432
RDS_DATABASE=extractorov
RDS_USERNAME=db_user
RDS_PASSWORD=db_password

# Configuración de S3
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
S3_BUCKET_NAME=tu-bucket-extractorov
S3_REGION=us-east-1

# Configuración de logging
LOG_LEVEL=INFO
LOG_MAX_FILES=10
LOG_MAX_SIZE_MB=50
```

### Timeouts y Límites
```bash
# Navegador
PAGE_TIMEOUT=30000
NAVIGATION_TIMEOUT=60000
DOWNLOAD_TIMEOUT=120000

# Procesamiento
MAX_CONCURRENT_DOWNLOADS=3
MAX_RETRY_ATTEMPTS=3
BATCH_SIZE=50

# Base de datos
DB_CONNECTION_TIMEOUT=30
DB_QUERY_TIMEOUT=300
```

---

## Testing y Validación

### Scripts de Verificación
```bash
# Verificación completa del sistema
python scripts/validate_functionality.py

# Test de conectividad
python scripts/test_connectivity.py

# Verificación de estándares
python scripts/verify_logging_standards.py

# Test de integración con servicios
python scripts/test_service_integration.py
```

### Tests Unitarios Clave
```python
# tests/unit/test_afinia_manager.py
def test_afinia_manager_initialization():
    manager = AfiniaManager(headless=True)
    assert manager.headless == True
    assert manager.extractor is None

# tests/unit/test_database_service.py
def test_database_connection():
    service = DatabaseService()
    assert service.test_connection() == True
```

---

## Debugging y Troubleshooting

### Logs Importantes
1. **Manager logs**: `data/logs/afinia_manager.log`
2. **Unified logs**: `data/logs/current/afinia_ov.log`
3. **Component logs**: `data/logs/current/` (por componente)

### Señales de Problemas
```python
# Indicadores en logs de problemas comunes
ERROR_PATTERNS = {
    "credential_error": ["authentication failed", "login error"],
    "timeout_error": ["timeout", "navigation timeout"],
    "page_error": ["page not found", "element not found"],
    "database_error": ["connection refused", "query timeout"],
    "s3_error": ["access denied", "bucket not found"]
}
```

### Comandos de Diagnóstico
```bash
# Verificar estado de servicios
python -c "
from src.services.database_service import DatabaseService
from src.services.s3_uploader_service import S3UploaderService

db = DatabaseService()
print('DB Status:', db.test_connection())

s3 = S3UploaderService()
print('S3 Status:', s3.test_connection())
"

# Verificar importaciones críticas
python -c "
import sys
sys.path.append('C:/00_Project_Dev/ExtractorOV_Modular')
from afinia_manager import AfiniaManager
from src.services.database_service import DatabaseService
print('All imports successful')
"
```

---

## Mejores Prácticas para IAs

### 1. Antes de Modificar Código
```python
# Hacer backup
import shutil
import datetime

backup_name = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy("archivo_original.py", f"archivo_original_{backup_name}.py")
```

### 2. Verificación Post-Cambios
```python
# Template de verificación
def verify_changes():
    try:
        # Import test
        from afinia_manager import AfiniaManager
        
        # Initialization test
        manager = AfiniaManager(headless=True, test_mode=True)
        
        # Logging format test
        import logging
        logger = logging.getLogger('test')
        logger.info("VERIFICANDO formato de log profesional")
        
        print("VERIFICACION EXITOSA")
        return True
    except Exception as e:
        print(f"ERROR EN VERIFICACION: {e}")
        return False

verify_changes()
```

### 3. Limpieza Automática
```python
# Siempre aplicar después de cambios
import subprocess
subprocess.run([
    "python", 
    "scripts/clean_emojis_professional.py", 
    "--apply-all"
])
```

---

## Roadmap Técnico

### Próximas Mejoras Técnicas
1. **Containerización**: Docker para deployment
2. **CI/CD**: GitHub Actions para testing automático
3. **Monitoring**: Prometheus/Grafana para métricas
4. **Alertas**: Sistema de notificaciones automáticas
5. **API REST**: Endpoint para consultas externas

### Optimizaciones Planificadas
1. **Paralelización**: Procesamiento concurrente de PQRs
2. **Caching**: Redis para datos temporales
3. **Compression**: Optimización de almacenamiento S3
4. **Load Balancing**: Distribución de carga en múltiples instancias

---

## Contacto y Soporte

**Desarrollador Original:** ISES | Analyst Data Jeam Paul Arcon Solano

Para dudas técnicas específicas, consultar:
1. Este directorio `ai-context/`
2. Documentación en `docs/`
3. Logs del sistema en `data/logs/`
4. Scripts de diagnóstico en `scripts/`

---

*Documento técnico actualizado: 2025-10-08*
*Versión del sistema: 2.0 Professional*