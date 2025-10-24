# ExtractorMERC - Sistema de Extracción Modular

Sistema modular profesional para la extracción automatizada de datos desde diversas plataformas web. Actualmente implementado para las plataformas de Afinia y Aire en Barranquilla, Colombia.

## Características Principales

- **Extracción Automatizada**: Procesamiento inteligente de datos desde cualquier plataforma web configurable.
- **Arquitectura Modular**: Diseño escalable y mantenible con separación clara de responsabilidades
- **Modo Dual**: Ejecución en modo visual (con interfaz) o headless (sin interfaz) para diferentes entornos
- **Filtrado Avanzado**: Sistema de filtros por fechas, estado y criterios personalizados
- **Gestión de Adjuntos**: Descarga automática y organizada de documentos de prueba
- **Reportería Completa**: Generación de reportes PDF, Excel y CSV con datos consolidados
- **Sistema de Logs**: Logging robusto con niveles configurables y archivado automático
- **Multiplataforma**: Compatibilidad nativa con Windows y Ubuntu Server
- **Métricas Integradas**: Sistema de monitoreo y métricas de rendimiento

## Arquitectura del Sistema
 
```
ExtractorOV_Modular/
├── src/                    # Código fuente principal
│   ├── components/         # Componentes base y reutilizables
│   │   ├── browser/        # Gestión de navegadores (Playwright)
│   │   ├── filters/        # Managers de filtros por plataforma
│   │   ├── pagination/     # Gestión de paginación automática
│   │   └── validation/     # Validadores de datos y configuración
│   ├── config/             # Configuración centralizada
│   │   ├── config.py       # Configuración principal del sistema
│   │   └── extractor_config.py # Configuración específica de extractores
│   ├── core/               # Núcleo del sistema
│   │   ├── base/           # Clases base abstractas
│   │   ├── exceptions/     # Excepciones personalizadas
│   │   └── interfaces/     # Interfaces y contratos
│   ├── extractors/         # Extractores específicos por plataforma
│   │   ├── afinia/         # Extractor para plataforma Afinia
│   │   └── aire/           # Extractor para plataforma Aire
│   ├── processors/         # Procesadores de datos
│   │   ├── data/           # Procesamiento de datos extraídos
│   │   └── report/         # Generación de reportes
│   └── utils/              # Utilidades generales
│       ├── file_utils.py   # Manejo de archivos
│       ├── date_utils.py   # Utilidades de fechas
│       └── logger.py       # Configuración de logging
├── data/                   # Datos generados y temporales
│   ├── downloads/          # Archivos descargados organizados por servicio
│   ├── logs/              # Sistema de logs con archivado automático
│   │   ├── current/        # Logs activos
│   │   └── archived/       # Logs archivados por fecha
│   └── metrics/           # Métricas y estadísticas del sistema
├── config/                 # Configuración externa
│   ├── env/               # Variables de entorno y credenciales
│   └── ubuntu_config/     # Configuración específica para Ubuntu Server
├── docs/                  # Documentación del proyecto
│   ├── analysis/          # Análisis técnicos
│   ├── planning/          # Planificación y roadmaps
│   ├── setup/             # Guías de instalación
│   └── reports/           # Reportes de estado
├── examples/              # Ejemplos de uso y tutoriales
│   ├── basic/             # Ejemplos básicos
│   ├── advanced/          # Casos de uso avanzados
│   └── scripts/           # Scripts de ejemplo
├── tests/                 # Suite de pruebas
│   ├── unit/              # Pruebas unitarias
│   ├── integration/       # Pruebas de integración
│   └── fixtures/          # Datos de prueba
└── scripts/               # Scripts de utilidad y automatización
    ├── deployment/        # Scripts de despliegue
    ├── maintenance/       # Scripts de mantenimiento
    └── ubuntu_setup.sh    # Instalación automática para Ubuntu
```

## Instalación

### Requisitos del Sistema

- **Python**: 3.8 o superior
- **Navegador**: Chrome/Chromium instalado y actualizado
- **Sistema Operativo**: Windows 10/11 o Ubuntu Server 18.04+
- **RAM**: Mínimo 4GB (recomendado 8GB)
- **Espacio en Disco**: 2GB libres para datos temporales

### Instalación en Windows

1. **Preparación del entorno**:
```powershell
git clone https://github.com/tu-usuario/ExtractorOV_Modular.git
cd ExtractorOV_Modular

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate
```

2. **Instalación de dependencias**:
```powershell
pip install -r requirements.txt
playwright install chromium
```

3. **Configuración de credenciales**:
```powershell
copy config\env\.env.example config\env\.env
# Editar config\env\.env con tus credenciales
```

### Instalación en Ubuntu Server

1. **Instalación automatizada**:
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/ExtractorOV_Modular.git
cd ExtractorOV_Modular

# Ejecutar script de instalación
sudo chmod +x scripts/ubuntu_setup.sh
./scripts/ubuntu_setup.sh
```

2. **Configuración manual** (alternativa):
```bash
# Instalar dependencias del sistema
sudo apt update && sudo apt install -y python3 python3-pip python3-venv

# Instalar Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
sudo apt update && sudo apt install -y google-chrome-stable

# Configurar entorno Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Configuración de Variables de Entorno

Configura el archivo `config/env/.env` con las siguientes variables:

```bash
# === CREDENCIALES AFINIA ===
OV_AFINIA_USERNAME=tu_usuario_afinia
OV_AFINIA_PASSWORD=tu_password_afinia
OV_AFINIA_URL=https://oficinavirtual.afinia.com.co

# === CREDENCIALES AIRE ===
OV_AIRE_USERNAME=tu_usuario_aire
OV_AIRE_PASSWORD=tu_password_aire
OV_AIRE_URL=https://oficinavirtual.aire.com.co

# === CONFIGURACIÓN DE FILTROS ===
FILTER_DAYS_BACK=1
FILTER_STATE=Finalizado
DATE_FORMAT=%d/%m/%Y

# === CONFIGURACIÓN DE TIMEOUTS ===
PAGE_TIMEOUT=30000
DOWNLOAD_TIMEOUT=60000
NAVIGATION_TIMEOUT=30000

# === CONFIGURACIÓN DE LOGS ===
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
LOG_MAX_SIZE_MB=100

# === CONFIGURACIÓN DE NAVEGADOR ===
HEADLESS_MODE=true
BROWSER_VIEWPORT_WIDTH=1920
BROWSER_VIEWPORT_HEIGHT=1080
```

## Uso del Sistema

### Gestores Principales

El sistema proporciona gestores dedicados para cada plataforma con interfaz de línea de comandos:

#### Extractor Afinia
```bash
# Ejecución básica en modo visual
python afinia_manager.py --visual

# Ejecución en modo headless (ideal para servidores)
python afinia_manager.py --headless

# Ejecución con parámetros personalizados
python afinia_manager.py --headless --days-back 7 --state "En Proceso"

# Ver todas las opciones disponibles
python afinia_manager.py --help
```

#### Extractor Aire
```bash
# Ejecución básica en modo visual
python aire_manager.py --visual

# Ejecución en modo headless
python aire_manager.py --headless

# Con configuración específica
python aire_manager.py --headless --config config/custom_config.json

# Ver ayuda completa
python aire_manager.py --help
```

### Uso Programático

Para integración en aplicaciones o scripts personalizados:

```python
from src.extractors.afinia.afinia_manager import AfiniaManager
from src.extractors.aire.aire_manager import AireManager
from src.config.config import Config

# Configuración personalizada
config = Config()
config.FILTER_DAYS_BACK = 3
config.HEADLESS_MODE = True

# Extractor Afinia
afinia = AfiniaManager(config=config)
result = afinia.extract_pqrs()
print(f"Extraídos {result.total_records} registros de Afinia")

# Extractor Aire
aire = AireManager(config=config)
result = aire.extract_pqrs()
print(f"Extraídos {result.total_records} registros de Aire")

# Acceso a métricas
print(f"Tiempo total: {result.execution_time}s")
print(f"Errores: {result.error_count}")
```

## Funcionalidades Avanzadas

### Sistema de Filtros Inteligente

- **Filtros por Fecha**: Rangos personalizables con validación automática
- **Filtros por Estado**: Estados predefinidos y personalizados
- **Filtros Compuestos**: Combinación de múltiples criterios
- **Validación Automática**: Verificación de filtros antes de aplicar

### Gestión de Adjuntos

- **Detección Automática**: Identificación de documentos de prueba en PQRs
- **Descarga Inteligente**: Retry automático y validación de integridad
- **Organización**: Estructura de carpetas por servicio y fecha
- **Nomenclatura**: Nombres únicos con timestamp y metadatos

### Sistema de Reportería

#### Formatos de Salida
- **PDF**: Reportes ejecutivos con gráficos y estadísticas
- **Excel**: Datos tabulares con múltiples hojas
- **CSV**: Datos en formato estándar para análisis
- **JSON**: Datos estructurados para integración

#### Tipos de Reportes
- **Reporte Ejecutivo**: Resumen con métricas clave
- **Reporte Detallado**: Todos los datos extraídos
- **Reporte de Errores**: Análisis de fallos y problemas
- **Reporte de Métricas**: Estadísticas de rendimiento

### Monitoreo y Métricas

```python
# Acceso a métricas en tiempo real
from src.utils.metrics import MetricsCollector

metrics = MetricsCollector()
stats = metrics.get_extraction_stats()

print(f"Registros procesados: {stats.total_processed}")
print(f"Tasa de éxito: {stats.success_rate}%")
print(f"Tiempo promedio por registro: {stats.avg_time_per_record}s")
```

## Configuración para Producción

### Ubuntu Server (Recomendado)

```bash
# Configuración de servicio systemd
sudo cp scripts/deployment/extractor-ov.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable extractor-ov
sudo systemctl start extractor-ov

# Configuración de cron para ejecución programada
crontab -e
# Agregar: 0 6 * * * /path/to/ExtractorOV_Modular/scripts/daily_extraction.sh
```

### Configuración de Logs para Producción

```bash
# Rotación automática de logs
sudo cp scripts/deployment/extractor-ov-logrotate /etc/logrotate.d/extractor-ov

# Verificar configuración
sudo logrotate -d /etc/logrotate.d/extractor-ov
```

### Optimización de Rendimiento

```bash
# Variables de entorno para producción
export PYTHONUNBUFFERED=1
export CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage --disable-gpu"
export MAX_CONCURRENT_EXTRACTIONS=2
export MEMORY_LIMIT_MB=2048
```

## Troubleshooting

### Problemas Comunes

| Problema | Causa Probable | Solución |
|----------|----------------|----------|
| Error de credenciales | Configuración incorrecta en .env | Verificar credenciales en `config/env/.env` |
| Timeout del navegador | Red lenta o configuración timeout | Aumentar `PAGE_TIMEOUT` en .env |
| Fallos de descarga | Permisos o espacio en disco | Verificar permisos en `data/downloads/` |
| Chrome no encontrado | Instalación incompleta | Ejecutar `playwright install chromium` |
| Import errors | Entorno virtual no activado | Activar venv y reinstalar dependencias |

### Herramientas de Diagnóstico

```bash
# Verificar configuración del sistema
python scripts/diagnostic/system_check.py

# Validar credenciales
python scripts/diagnostic/credentials_test.py

# Test de conectividad
python scripts/diagnostic/connectivity_test.py

# Análisis de logs
python scripts/diagnostic/log_analyzer.py --days 7
```

### Logs de Debug

```bash
# Activar logging detallado
export LOG_LEVEL=DEBUG
python afinia_manager.py --visual --debug

# Logs en tiempo real
tail -f data/logs/current/extractor_$(date +%Y%m%d).log
```

## Testing

### Ejecución de Pruebas

```bash
# Todas las pruebas
python -m pytest tests/ -v

# Pruebas con cobertura
python -m pytest tests/ --cov=src/ --cov-report=html

# Pruebas específicas
python -m pytest tests/unit/test_extractors.py -v
python -m pytest tests/integration/ -v

# Pruebas de rendimiento
python -m pytest tests/performance/ --benchmark-only
```

### Pruebas Manuales

```bash
# Test de extractores individualmente
python examples/basic/test_afinia_extraction.py
python examples/basic/test_aire_extraction.py

# Validación end-to-end
python examples/advanced/full_pipeline_test.py
```

## Mantenimiento

### Limpieza Automática

```bash
# Script de limpieza semanal
./scripts/maintenance/weekly_cleanup.sh

# Limpieza de logs antiguos
./scripts/maintenance/cleanup_logs.sh --older-than 30

# Optimización de base de datos
./scripts/maintenance/optimize_data.sh
```

### Actualización del Sistema

```bash
# Actualizar dependencias
pip install -r requirements.txt --upgrade
playwright install --with-deps

# Migración de datos
python scripts/migration/migrate_data.py --version 2.0
```

## Desarrollo y Extensión

### Agregar Nuevo Extractor

1. **Crear estructura base**:
```bash
mkdir -p src/extractors/nueva_plataforma
cp -r src/extractors/afinia/* src/extractors/nueva_plataforma/
```

2. **Implementar clases requeridas**:
```python
class NuevaPlataformaExtractor(BaseExtractor):
    def extract_data(self) -> ExtractionResult:
        # Implementar lógica específica
        pass
```

3. **Configurar variables de entorno**:
```bash
# En config/env/.env
OV_NUEVA_USERNAME=usuario
OV_NUEVA_PASSWORD=password
OV_NUEVA_URL=https://nueva-plataforma.com
```

### Contribución

```bash
# Setup desarrollo
git clone https://github.com/tu-usuario/ExtractorOV_Modular.git
cd ExtractorOV_Modular
pre-commit install

# Ejecutar tests antes de commit
python -m pytest tests/
python -m flake8 src/
python -m black src/ tests/
```

## Seguridad

- **Credenciales**: Almacenamiento seguro en variables de entorno
- **Logs**: Sanitización automática de información sensible
- **Archivos Temporales**: Limpieza automática después de procesamiento
- **Comunicaciones**: HTTPS obligatorio para todas las conexiones
- **Validación**: Sanitización de entradas y validación de datos

## Soporte y Documentación

### Recursos Disponibles

- **Documentación Técnica**: `docs/` - Documentación completa del sistema
- **Ejemplos**: `examples/` - Casos de uso y tutoriales
- **Scripts**: `scripts/` - Herramientas de mantenimiento y utilidad
- **Tests**: `tests/` - Suite completa de pruebas

### Contacto

Para soporte técnico, reportes de bugs o solicitudes de funcionalidades:

1. **GitHub Issues**: Crear issue con template correspondiente
2. **Documentación**: Revisar `docs/` para guías detalladas
3. **Logs**: Incluir logs relevantes en reportes de problemas
4. **Reproducción**: Proporcionar pasos claros para reproducir issues

---

**ExtractorOV Modular** - Sistema profesional de extracción de datos PQR para las plataformas de Oficina Virtual de Afinia y Aire en Barranquilla, Colombia. Desarrollado con arquitectura modular, escalable y preparado para entornos de producción.