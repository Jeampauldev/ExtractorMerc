# ExtractorOV Modular - Proyecto Reorganizado

## Descripción General

ExtractorOV Modular es un sistema de extracción automatizada de datos de oficinas virtuales para las empresas Afinia y Aire. El proyecto ha sido completamente reorganizado siguiendo mejores prácticas de desarrollo.

## Estructura del Proyecto

### Estructura Nueva Organizada

```
ExtractorOV_Modular/
├── src/                           # Código fuente principal
│   ├── __init__.py               # Paquete Python principal
│   ├── core/                     # Componentes centrales
│   │   └── a_core_01/            # Browser manager, autenticación, etc.
│   ├── extractors/               # Extractores específicos
│   │   └── d_downloaders_04/     
│   │       ├── afinia/           # Extractor de Afinia
│   │       └── aire/             # Extractor de Aire
│   ├── components/               # Componentes modulares
│   │   └── c_components_03/      # Filtros, popup handlers, procesadores
│   ├── processors/               # Procesadores de datos
│   │   └── e_processors_05/
│   │       ├── afinia/           # Procesamiento específico Afinia
│   │       └── aire/             # Procesamiento específico Aire
│   ├── config/                   # Configuraciones
│   │   ├── f_config_06/          # Configuraciones principales
│   │   └── ubuntu_config/        # Configuración Ubuntu
│   └── utils/                    # Utilidades
│       └── g_utils_07/           # Funciones de utilidad
│
├── config/                       # Configuraciones de entorno
│   ├── env/                      # Variables de entorno
│   └── ubuntu_config/            # Configuración específica Ubuntu
│
├── data/                         # Datos del proyecto
│   ├── downloads/                # Archivos descargados
│   ├── logs/                     # Archivos de log
│   ├── metrics/                  # Métricas y análisis
│   └── backup/                   # Respaldos
│
├── examples/                     # Ejemplos y casos de uso
│   ├── massive_processing/       # Procesamiento masivo
│   ├── specialized_sequences/    # Secuencias especializadas
│   ├── dashboard/                # Dashboard y visualización
│   └── tutorials/                # Tutoriales y scripts de ayuda
│
├── legacy/                       # Archivos obsoletos/de referencia
│   ├── old_runners/              # Scripts run_* antiguos
│   ├── old_components/           # Componentes obsoletos
│   ├── archive/                  # Archivos archivados
│   └── deprecated_docs/          # Documentación obsoleta
│
├── tests/                        # Pruebas unitarias
│   └── unit/                     # Pruebas unitarias específicas
│
├── docs/                         # Documentación organizada
│   ├── analysis/                 # Análisis del proyecto
│   ├── planning/                 # Planificación y diseño
│   ├── setup/                    # Guías de instalación
│   └── reports/                  # Reportes y análisis
│
├── scripts/                      # Scripts de utilidad
├── aire_manager.py               # Manager principal para Aire
├── afinia_manager.py             # Manager principal para Afinia
└── README.md                     # Este archivo
```

## Managers Principales

### Afinia Manager
- **Archivo**: `afinia_manager.py`
- **Uso**: `python afinia_manager.py [opciones]`
- **Opciones**:
  - `--headless`: Modo sin interfaz gráfica
  - `--visual`: Modo visual (para debugging)
  - `--test`: Modo de prueba
  - `--max-records N`: Procesar máximo N registros

### Aire Manager
- **Archivo**: `aire_manager.py`
- **Uso**: `python aire_manager.py [opciones]`
- **Opciones**: Mismas que Afinia Manager

## Configuración

### Variables de Entorno
Las credenciales se configuran mediante variables de entorno:

```bash
# Afinia
export OV_AFINIA_USERNAME="tu_usuario"
export OV_AFINIA_PASSWORD="tu_password"

# Aire
export OV_AIRE_USERNAME="tu_usuario"
export OV_AIRE_PASSWORD="tu_password"
```

### Archivo .env
Alternativamente, crear archivo `.env` en `config/env/`:

```
OV_AFINIA_USERNAME=tu_usuario
OV_AFINIA_PASSWORD=tu_password
OV_AIRE_USERNAME=tu_usuario
OV_AIRE_PASSWORD=tu_password
```

## Ejemplos de Uso

### Extracción Básica
```bash
# Afinia en modo visual para debugging
python afinia_manager.py --visual --test

# Aire en modo producción (headless)
python aire_manager.py --headless --max-records 50
```

### Procesamiento Masivo
```bash
# Ver ejemplos en examples/massive_processing/
python examples/massive_processing/run_afinia_ov_massive_with_pagination.py
python examples/massive_processing/run_aire_ov_massive_with_pagination.py
```

### Secuencias Especializadas
```bash
# Ver ejemplos en examples/specialized_sequences/
python examples/specialized_sequences/run_afinia_ov_specific_sequence.py
python examples/specialized_sequences/run_aire_ov_specific_sequence.py
```

## Características Principales

### Modularidad
- Componentes independientes y reutilizables
- Separación clara de responsabilidades
- Fácil extensión y mantenimiento

### Robustez
- Manejo avanzado de errores
- Reintentos automáticos
- Logging detallado

### Configurabilidad
- Configuración por empresa
- Múltiples ambientes (dev, test, prod)
- Personalización flexible

## Migración desde Versión Anterior

### Scripts Obsoletos
Los siguientes archivos han sido movidos a `legacy/old_runners/`:
- `run_afinia_ov_headless.py`
- `run_afinia_ov_visual.py`
- `run_aire_ov_headless.py`
- `run_aire_ov_visual.py`
- `run_aire_ov_simple.py`

### Nuevos Managers
Usar en su lugar:
- `afinia_manager.py` (reemplaza todos los run_afinia_*)
- `aire_manager.py` (reemplaza todos los run_aire_*)

## Desarrollo

### Estructura de Imports
Los imports siguen la nueva estructura:

```python
# Extractores
from src.extractors.d_downloaders_04.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular
from src.extractors.d_downloaders_04.aire.oficina_virtual_aire_modular import OficinaVirtualAireModular

# Configuración
from src.config.f_config_06.config import OficinaVirtualConfig

# Componentes core
from src.core.a_core_01.browser_manager import BrowserManager
from src.core.a_core_01.authentication import AuthenticationManager
```

### Extensión del Sistema
1. Nuevos extractores: agregar en `src/extractors/`
2. Nuevos componentes: agregar en `src/components/`
3. Nuevas configuraciones: agregar en `src/config/`

## Logging

El sistema genera logs en:
- `data/logs/`: Logs de ejecución
- `data/metrics/`: Métricas de rendimiento

## Pruebas

Ejecutar pruebas unitarias:
```bash
python -m pytest tests/
```

## Soporte

Para problemas o consultas:
1. Revisar logs en `data/logs/`
2. Consultar documentación en `docs/`
3. Revisar ejemplos en `examples/`

## Changelog

### Versión 2.0 (Reorganización Completa)
- ✅ Reorganización completa de la estructura del proyecto
- ✅ Separación clara de responsabilidades
- ✅ Managers unificados para cada empresa
- ✅ Documentación reorganizada
- ✅ Ejemplos y tutoriales organizados
- ✅ Sistema de configuración mejorado
- ✅ Imports actualizados a nueva estructura

### Versión 1.x (Legacy)
- Scripts individuales para cada modo
- Estructura de carpetas con prefijos numericos
- Documentación dispersa