# Configuración del Sistema - ExtractorOV Modular

## Descripción

Este directorio contiene toda la configuración del sistema ExtractorOV_Modular, organizada de manera modular y escalable para diferentes entornos de ejecución.

## Estructura de Configuración

```
config/
├── env/                    # Variables de entorno y credenciales
│   ├── .env                # Configuración principal (NO commitear)
│   ├── .env.example       # Plantilla de configuración
│   └── README.md          # Documentación de variables de entorno
├── ubuntu_config/         # Configuración específica para Ubuntu Server
│   ├── environment_detector.py  # Detector de entorno automático
│   ├── ubuntu_browser.py        # Configuración de navegador para Ubuntu
│   ├── ubuntu_paths.py          # Gestor de rutas multiplataforma
│   ├── install_ubuntu.sh        # Script de instalación automatizada
│   ├── run_ubuntu.sh            # Script de ejecución principal
│   ├── extractorov-*.service    # Servicios systemd
│   └── README.md               # Documentación Ubuntu Server
├── settings/              # Configuraciones adicionales (futuro)
└── README.md              # Esta documentación
```

## Componentes Principales

### 1. Variables de Entorno (`env/`)

Gestión centralizada de todas las variables de configuración del sistema:

#### Archivos Principales
- **`.env`**: Configuración de producción con credenciales reales
- **`.env.example`**: Plantilla profesional con documentación completa
- **`README.md`**: Guía detallada de configuración y uso

#### Variables Críticas
```bash
# Credenciales de acceso (OBLIGATORIO)
OV_AFINIA_USERNAME=tu_usuario_afinia
OV_AFINIA_PASSWORD=tu_password_afinia
OV_AIRE_USERNAME=tu_usuario_aire
OV_AIRE_PASSWORD=tu_password_aire

# Configuración del sistema
APP_ENV=production
DEBUG=false
HEADLESS_MODE=true

# Directorios (nueva estructura)
DOWNLOAD_PATH=./data/downloads
LOG_PATH=./data/logs
METRICS_PATH=./data/metrics
```

#### Características Avanzadas
- Configuraciones específicas por plataforma (Afinia/Aire)
- Sistema de logging configurable con rotación
- Optimizaciones de rendimiento y memoria
- Configuraciones de seguridad y limpieza automática
- Soporte para múltiples ambientes (desarrollo, producción)

### 2. Configuración Ubuntu (`ubuntu_config/`)

Configuración especializada para Ubuntu Server con soporte completo para producción:

#### Componentes Clave

**`environment_detector.py`**
- Detección automática del entorno de ejecución
- Identificación de Ubuntu Server vs Desktop
- Configuración automática de variables específicas

**`ubuntu_browser.py`**
- Configuración optimizada de Chrome para Ubuntu
- Soporte para modo headless con XVFB
- Argumentos específicos para entorno servidor

**`ubuntu_paths.py`**
- Gestor de rutas multiplataforma
- Creación automática de directorios
- Manejo correcto de permisos en Linux

**Scripts de Automatización**
- `install_ubuntu.sh`: Instalación completa automatizada
- `run_ubuntu.sh`: Gestión de ejecución y servicios

**Servicios Systemd**
- `extractorov-afinia.service`
- `extractorov-aire.service`
- Auto-reinicio, logging y monitoreo automático

## Configuración por Ambiente

### Desarrollo (Windows)

```bash
# Variables recomendadas para desarrollo
APP_ENV=development
DEBUG=true
HEADLESS_MODE=false
LOG_LEVEL=DEBUG
SCREENSHOT_ON_ERROR=true
```

Características:
- Navegador visible para debugging
- Logs detallados
- Screenshots automáticos en errores
- Timeouts extendidos para desarrollo

### Producción (Ubuntu Server)

```bash
# Variables optimizadas para producción
APP_ENV=production
DEBUG=false
HEADLESS_MODE=true
LOG_LEVEL=INFO
CLEAN_TEMP_ON_EXIT=true
```

Características:
- Modo headless con XVFB
- Servicios systemd para auto-reinicio
- Logs optimizados con rotación
- Limpieza automática de archivos temporales

### Testing

```bash
# Variables para entorno de pruebas
APP_ENV=testing
DEBUG=false
HEADLESS_MODE=true
LOG_LEVEL=WARNING
MAX_RECORDS_PER_SESSION=5
```

## Guías de Configuración

### Configuración Inicial

1. **Copiar plantilla de variables**:
```bash
cp config/env/.env.example config/env/.env
```

2. **Configurar credenciales obligatorias**:
```bash
# Editar config/env/.env con credenciales reales
OV_AFINIA_USERNAME=tu_usuario
OV_AFINIA_PASSWORD=tu_password
OV_AIRE_USERNAME=tu_usuario
OV_AIRE_PASSWORD=tu_password
```

3. **Ajustar configuración según ambiente**:
```bash
# Para desarrollo local
HEADLESS_MODE=false
DEBUG=true

# Para servidor de producción
HEADLESS_MODE=true
DEBUG=false
```

### Configuración para Ubuntu Server

1. **Ejecutar instalación automatizada**:
```bash
chmod +x scripts/ubuntu_setup.sh
./scripts/ubuntu_setup.sh
```

2. **Configurar servicios systemd** (automático):
```bash
sudo systemctl enable extractorov-afinia extractorov-aire
sudo systemctl start extractorov-afinia extractorov-aire
```

3. **Verificar estado**:
```bash
sudo systemctl status extractorov-afinia
journalctl -u extractorov-afinia -f
```

### Configuración Avanzada

#### Optimización de Rendimiento
```bash
# Variables de rendimiento en .env
MAX_MEMORY_MB=2048
MAX_CONCURRENT_PAGES=2
THREAD_POOL_SIZE=4
GARBAGE_COLLECTION_THRESHOLD=100
```

#### Configuración de Red
```bash
# Proxy (si es necesario)
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080

# Timeouts de red
PAGE_TIMEOUT=30000
DOWNLOAD_TIMEOUT=60000
NAVIGATION_TIMEOUT=30000
```

#### Configuración de Logging
```bash
# Sistema de logging avanzado
LOG_LEVEL=INFO
LOG_FORMAT=[%(levelname)s] %(asctime)s - %(name)s:%(lineno)d - %(message)s
LOG_MAX_SIZE_MB=10
LOG_RETENTION_DAYS=30
LOG_ROTATION=daily
```

## Seguridad

### Mejores Prácticas

1. **Variables Sensibles**:
   - Nunca commitear el archivo `.env`
   - Usar permisos restrictivos: `chmod 600 config/env/.env`
   - Rotar credenciales periódicamente

2. **Configuración Segura**:
   ```bash
   # Permisos recomendados
   chmod 600 config/env/.env
   chmod 700 config/ubuntu_config/
   chown -R usuario:usuario config/
   ```

3. **Gestión de Credenciales en Producción**:
   - Considerar AWS Secrets Manager
   - Usar HashiCorp Vault para secretos
   - Implementar rotación automática

### Variables Sensibles Identificadas

- `OV_AFINIA_USERNAME` / `OV_AFINIA_PASSWORD`
- `OV_AIRE_USERNAME` / `OV_AIRE_PASSWORD`
- `RDS_*` (credenciales de base de datos)
- `AWS_*` (credenciales de AWS)

## Validación de Configuración

### Verificación Automática

```bash
# Validar configuración completa
python -c "from src.config.config import Config; print('✓ Válida' if Config.validate() else '✗ Error')"

# Verificar variables críticas
python -c "
import os
from dotenv import load_dotenv
load_dotenv('config/env/.env')
required = ['OV_AFINIA_USERNAME', 'OV_AFINIA_PASSWORD', 'OV_AIRE_USERNAME', 'OV_AIRE_PASSWORD']
for var in required:
    status = '✓' if os.getenv(var) else '✗'
    print(f'{status} {var}')
"
```

### Verificación Manual

```bash
# Verificar estructura de directorios
ls -la config/env/
ls -la config/ubuntu_config/

# Verificar permisos
stat -c '%a %n' config/env/.env

# Verificar sintaxis de servicios (Ubuntu)
sudo systemd-analyze verify config/ubuntu_config/extractorov-*.service
```

## Troubleshooting

### Problemas Comunes

| Problema | Causa Probable | Solución |
|----------|----------------|----------|
| Variables no encontradas | Archivo .env faltante | Copiar desde .env.example |
| Error de permisos | Permisos incorrectos | `chmod 600 config/env/.env` |
| Servicios no inician | Configuración systemd | Verificar archivos .service |
| Chrome falla en Ubuntu | Dependencias faltantes | Ejecutar install_ubuntu.sh |

### Comandos de Diagnóstico

```bash
# Verificar configuración del entorno
env | grep -E "(OV_|APP_|DEBUG|HEADLESS)"

# Test de conectividad
curl -I https://www.google.com

# Verificar instalación Ubuntu
python3 -c "from config.ubuntu_config.environment_detector import get_system_info; print(get_system_info())"

# Verificar servicios (Ubuntu)
systemctl list-units extractorov-*
```

## Mantenimiento

### Actualización de Configuración

```bash
# Backup de configuración actual
cp config/env/.env config/env/.env.backup.$(date +%Y%m%d)

# Actualizar plantilla (conservar credenciales)
git pull origin main
# Revisar cambios en .env.example
# Actualizar .env manualmente si es necesario
```

### Limpieza de Configuración

```bash
# Limpiar archivos de cache
rm -rf config/ubuntu_config/__pycache__/

# Verificar archivos temporales
find config/ -name "*.tmp" -o -name "*.bak"

# Auditar permisos
find config/ -type f -exec stat -c '%a %n' {} \;
```

## Migración y Compatibilidad

### Migración desde Versión Anterior

Si viene de una estructura anterior del proyecto:

```bash
# Backup de configuración anterior
cp p16_env/.env config/env/.env.legacy

# Migrar configuraciones esenciales
grep -E "^(OV_|AFINIA_|AIRE_)" p16_env/.env >> config/env/.env

# Actualizar rutas en código (automático con scripts)
python scripts/migration/update_config_paths.py
```

### Compatibilidad

- **Windows 10/11**: Soporte completo
- **Ubuntu 18.04+**: Soporte completo con optimizaciones
- **Python 3.8+**: Requerido
- **Chrome/Chromium**: Instalación automática en Ubuntu

## Recursos Adicionales

### Documentación Relacionada

- [README Principal](../README.md) - Documentación general del proyecto
- [Variables de Entorno](env/README.md) - Guía detallada de variables
- [Ubuntu Server](ubuntu_config/README.md) - Configuración específica Ubuntu
- [Scripts de Instalación](../scripts/README.md) - Scripts de automatización

### Herramientas de Desarrollo

```bash
# Validador de configuración
python scripts/validate_config.py

# Generador de configuración
python scripts/generate_config.py --env production

# Test de configuración
python scripts/test_config.py --all
```

## Contribución

### Agregar Nueva Configuración

1. **Crear archivo de configuración** en el subdirectorio apropiado
2. **Documentar variables** en README correspondiente
3. **Agregar validación** en scripts de verificación
4. **Actualizar .env.example** con nuevas variables
5. **Crear tests** para nueva configuración

### Estructura de Nuevas Configuraciones

```bash
# Para nuevas plataformas o entornos
config/nueva_plataforma/
├── detector.py           # Detector de entorno
├── configurator.py       # Configurador específico
├── install_script.sh     # Script de instalación
└── README.md            # Documentación
```

---

**ExtractorOV Configuration** - Sistema de configuración modular, escalable y seguro para múltiples entornos de ejecución.