# Plan de Reorganización - ExtractorOV Modular

## 📊 **ANÁLISIS DE ESTRUCTURA ACTUAL**

### **Directorios Actuales:**
```
ExtractorOV_Modular/
├── a_core_01/              # Componentes core (MANTENER)
├── b_adapters_02/          # Adaptadores (REVISAR)
├── c_components_03/        # Componentes específicos (MANTENER)
├── d_downloaders_04/       # Extractores principales (MANTENER - CRÍTICO)
├── e_processors_05/        # Procesadores (MANTENER)
├── f_config_06/            # Configuraciones (MANTENER)
├── g_utils_07/             # Utilidades (MANTENER)
├── h_dashboard_08/         # Dashboard (MOVER A EXAMPLES)
├── i_tests_09/             # Tests (MANTENER - RENOMBRAR)
├── j_docs_10/              # Docs obsoletos (MOVER A LEGACY)
├── l_scripts_12/           # Scripts varios (REVISAR)
├── m_downloads_13/         # Descargas (MANTENER)
├── n_logs_14/              # Logs (MANTENER)
├── o_metrics_15/           # Métricas (MANTENER)
├── p16_env/                # Variables entorno (MANTENER)
├── p_validator_16/         # Validadores (MANTENER)
├── q_uploader_17/          # Uploaders (REVISAR)
├── t_legacy_19/            # Legacy existente (CONSOLIDAR)
├── ubuntu_config/          # Configuración Ubuntu (MANTENER)
├── scripts/                # Scripts generales (CONSOLIDAR)
├── data/                   # Datos (MANTENER)
├── downloads/              # Descargas adicionales (CONSOLIDAR)
├── logs/                   # Logs adicionales (CONSOLIDAR)
├── temp_test/              # Temporal (ELIMINAR)
└── __pycache__/            # Cache Python (MANTENER)
```

### **Archivos Principales en Raíz:**
```
FUNCIONALES (MANTENER EN RAÍZ):
├── aire_manager.py         ⭐ FUNCIONAL - MANTENER
├── afinia_manager.py       ⭐ FUNCIONAL - MANTENER
└── ubuntu_config/          ⭐ FUNCIONAL - MANTENER

OBSOLETOS (MOVER A LEGACY):
├── run_aire_ov_headless.py      🔄 REDUNDANTE
├── run_aire_ov_visual.py        🔄 REDUNDANTE  
├── run_aire_ov_simple.py        🔄 REDUNDANTE
├── run_afinia_ov_headless.py    🔄 REDUNDANTE
└── run_afinia_ov_visual.py      🔄 REDUNDANTE

ESPECIALIZADOS (MOVER A EXAMPLES):
├── run_aire_ov_massive_with_pagination.py     📚 ESPECIALIZADO
├── run_aire_ov_specific_sequence.py           📚 ESPECIALIZADO
├── run_afinia_ov_massive_with_pagination.py   📚 ESPECIALIZADO
└── run_afinia_ov_specific_sequence.py         📚 ESPECIALIZADO
```

## 🎯 **NUEVA ESTRUCTURA PROPUESTA**

### **Estructura Final Objetivo:**
```
ExtractorOV_Modular/
├── README.md                    # Documentación principal
├── requirements.txt             # Dependencias
├── .env.example                 # Ejemplo variables entorno
├── aire_manager.py              # 🚀 MANAGER PRINCIPAL AIRE
├── afinia_manager.py            # 🚀 MANAGER PRINCIPAL AFINIA
│
├── src/                         # 📁 CÓDIGO FUENTE PRINCIPAL
│   ├── core/                    # Componentes core (a_core_01 renombrado)
│   ├── components/              # Componentes específicos (c_components_03)
│   ├── extractors/              # Extractores (d_downloaders_04)
│   ├── processors/              # Procesadores (e_processors_05)
│   ├── config/                  # Configuraciones (f_config_06)
│   ├── utils/                   # Utilidades (g_utils_07)
│   └── __init__.py              # Módulo Python
│
├── config/                      # 🔧 CONFIGURACIONES
│   ├── ubuntu_config/           # Config Ubuntu Server
│   ├── env/                     # Variables entorno (p16_env)
│   └── settings/                # Configuraciones generales
│
├── data/                        # 📊 DATOS Y ALMACENAMIENTO
│   ├── downloads/               # Descargas consolidadas
│   ├── processed/               # Archivos procesados
│   ├── logs/                    # Logs consolidados
│   └── metrics/                 # Métricas (o_metrics_15)
│
├── scripts/                     # 📜 SCRIPTS AUXILIARES
│   ├── ubuntu/                  # Scripts Ubuntu (ubuntu_config/run_ubuntu.sh)
│   ├── maintenance/             # Scripts mantenimiento
│   └── deployment/              # Scripts despliegue
│
├── tests/                       # 🧪 PRUEBAS
│   ├── unit/                    # Tests unitarios (i_tests_09)
│   ├── integration/             # Tests integración
│   └── fixtures/                # Datos test
│
├── examples/                    # 📚 EJEMPLOS Y CASOS ESPECIALES
│   ├── specialized_sequences/   # Scripts específicos
│   ├── massive_processing/      # Procesamiento masivo
│   ├── dashboard/               # Dashboard demo (h_dashboard_08)
│   └── tutorials/               # Tutoriales
│
├── legacy/                      # 📦 ARCHIVOS OBSOLETOS
│   ├── old_runners/             # Scripts run_* obsoletos
│   ├── deprecated_docs/         # Docs obsoletos (j_docs_10)
│   ├── old_components/          # Componentes obsoletos
│   └── archive/                 # Archivo general (t_legacy_19)
│
├── docs/                        # 📖 DOCUMENTACIÓN
│   ├── api/                     # Documentación API
│   ├── installation/            # Guías instalación
│   ├── user_guide/              # Guías usuario
│   └── development/             # Guías desarrollo
│
└── .venv/                       # Entorno virtual Python
```

## 📋 **PLAN DE ACCIÓN DETALLADO**

### **FASE 1: Crear Nueva Estructura**
```bash
# Crear directorios principales
mkdir src, config, data, scripts, tests, examples, legacy, docs

# Crear subdirectorios
mkdir src/{core,components,extractors,processors,config,utils}
mkdir config/{ubuntu_config,env,settings}
mkdir data/{downloads,processed,logs,metrics}
mkdir scripts/{ubuntu,maintenance,deployment}
mkdir tests/{unit,integration,fixtures}
mkdir examples/{specialized_sequences,massive_processing,dashboard,tutorials}
mkdir legacy/{old_runners,deprecated_docs,old_components,archive}
mkdir docs/{api,installation,user_guide,development}
```

### **FASE 2: Mover y Renombrar Directorios**
```bash
# Mover directorios core
mv a_core_01/ → src/core/
mv c_components_03/ → src/components/
mv d_downloaders_04/ → src/extractors/
mv e_processors_05/ → src/processors/
mv f_config_06/ → src/config/
mv g_utils_07/ → src/utils/

# Mover configuraciones
mv ubuntu_config/ → config/ubuntu_config/
mv p16_env/ → config/env/
mv p_validator_16/ → src/utils/validators/

# Consolidar datos
mv m_downloads_13/ → data/downloads/
mv n_logs_14/ → data/logs/
mv o_metrics_15/ → data/metrics/

# Mover tests
mv i_tests_09/ → tests/unit/

# Mover ejemplos
mv h_dashboard_08/ → examples/dashboard/
mv l_scripts_12/ → examples/tutorials/

# Mover legacy
mv j_docs_10/ → legacy/deprecated_docs/
mv t_legacy_19/ → legacy/archive/
```

### **FASE 3: Organizar Archivos Principales**
```bash
# MANTENER EN RAÍZ (funcionales)
KEEP: aire_manager.py
KEEP: afinia_manager.py
KEEP: requirements.txt
KEEP: .env (si existe)

# MOVER A LEGACY (obsoletos)
mv run_aire_ov_headless.py → legacy/old_runners/
mv run_aire_ov_visual.py → legacy/old_runners/
mv run_aire_ov_simple.py → legacy/old_runners/
mv run_afinia_ov_headless.py → legacy/old_runners/
mv run_afinia_ov_visual.py → legacy/old_runners/

# MOVER A EXAMPLES (especializados)
mv run_aire_ov_massive_with_pagination.py → examples/massive_processing/
mv run_aire_ov_specific_sequence.py → examples/specialized_sequences/
mv run_afinia_ov_massive_with_pagination.py → examples/massive_processing/
mv run_afinia_ov_specific_sequence.py → examples/specialized_sequences/
```

### **FASE 4: Consolidar Directorios Duplicados**
```bash
# Consolidar downloads
merge downloads/ → data/downloads/general/

# Consolidar logs  
merge logs/ → data/logs/general/

# Consolidar scripts
merge scripts/ → scripts/general/

# Limpiar temporales
rm -rf temp_test/
```

### **FASE 5: Actualizar Imports**
```python
# Actualizar imports en archivos principales
# ANTES:
from d_downloaders_04.aire.oficina_virtual_aire_modular import OficinaVirtualAireModular
from c_components_03.aire_pqr_processor import AirePQRProcessor
from a_core_01.browser_manager import BrowserManager

# DESPUÉS:
from src.extractors.aire.oficina_virtual_aire_modular import OficinaVirtualAireModular  
from src.components.aire_pqr_processor import AirePQRProcessor
from src.core.browser_manager import BrowserManager
```

### **FASE 6: Crear Archivos de Configuración**
```python
# src/__init__.py - Hacer src/ un módulo Python
# config/settings.py - Configuraciones centralizadas
# docs/README.md - Documentación actualizada
# .env.example - Ejemplo variables entorno
```

## ⚠️ **CONSIDERACIONES IMPORTANTES**

### **Archivos CRÍTICOS que NO se deben mover:**
- ✅ `aire_manager.py` - MANTENER EN RAÍZ
- ✅ `afinia_manager.py` - MANTENER EN RAÍZ  
- ✅ `requirements.txt` - MANTENER EN RAÍZ
- ✅ `.venv/` - MANTENER EN RAÍZ

### **Directorios CRÍTICOS (contienen lógica funcional):**
- 🔥 `d_downloaders_04/` - Contiene extractores principales
- 🔥 `c_components_03/` - Contiene componentes específicos  
- 🔥 `a_core_01/` - Contiene componentes core
- 🔥 `ubuntu_config/` - Configuración Ubuntu Server

### **Impacto en Funcionalidad:**
- 📍 Todos los imports se actualizarán automáticamente
- 📍 Los managers principales seguirán funcionando
- 📍 La configuración Ubuntu se mantendrá intacta
- 📍 Se preservará toda la funcionalidad existente

## 🎯 **BENEFICIOS DE LA REORGANIZACIÓN**

### **Antes (Problemático):**
```
❌ Nombres con números (a_core_01, b_adapters_02)
❌ Archivos run_* redundantes en raíz  
❌ Directorios duplicados (downloads/, m_downloads_13/)
❌ Documentación dispersa
❌ No sigue convenciones Python
```

### **Después (Mejorado):**
```
✅ Nombres descriptivos (src/core/, src/components/)
✅ Solo managers funcionales en raíz
✅ Estructura consolidada y organizada  
✅ Documentación centralizada
✅ Sigue convenciones Python estándar
✅ Fácil navegación y mantenimiento
```

## 🔍 **VALIDACIÓN POST-REORGANIZACIÓN**

### **Tests a ejecutar:**
```bash
# 1. Verificar managers principales
python aire_manager.py --test --visual
python afinia_manager.py --test --visual

# 2. Verificar imports
python -c "from src.core.browser_manager import BrowserManager; print('✅ Core imports OK')"
python -c "from src.extractors.aire.oficina_virtual_aire_modular import OficinaVirtualAireModular; print('✅ Extractor imports OK')"

# 3. Verificar Ubuntu config
python -c "from config.ubuntu_config import is_ubuntu_server; print('✅ Ubuntu config OK')"
```

## ❓ **APROBACIÓN REQUERIDA**

¿Estás de acuerdo con este plan de reorganización?

### **Confirma si quieres proceder con:**
1. ✅ **Crear nueva estructura de directorios**
2. ✅ **Mover archivos obsoletos a legacy/**  
3. ✅ **Reorganizar componentes core en src/**
4. ✅ **Actualizar todos los imports**
5. ✅ **Consolidar directorios duplicados**
6. ✅ **Preservar funcionalidad de managers**

**🚨 IMPORTANTE:** Una vez iniciado, se hará un backup completo antes de cualquier cambio.