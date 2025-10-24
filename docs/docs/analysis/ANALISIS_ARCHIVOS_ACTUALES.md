# Análisis de Archivos Actuales - ExtractorOV

## 📊 **ESTADO ACTUAL DEL PROYECTO**

### **🔍 ARCHIVOS PRINCIPALES (Raíz)**

#### ✅ **FUNCIONALES - MANTENER**
```
aire_manager.py              ⭐ CRÍTICO - Manager principal Aire
afinia_manager.py            ⭐ CRÍTICO - Manager principal Afinia  
requirements.txt             📋 Dependencias Python
PLAN_REORGANIZACION.md       📖 Este análisis
ARCHIVOS_RUN_ANALISIS.md     📖 Análisis previo
```

#### 🔄 **OBSOLETOS - MOVER A LEGACY**
```
run_aire_ov_headless.py      ❌ Redundante (reemplazado por aire_manager.py)
run_aire_ov_visual.py        ❌ Redundante (reemplazado por aire_manager.py)  
run_aire_ov_simple.py        ❌ Redundante (funcionalidad básica)
run_afinia_ov_headless.py    ❌ Redundante (reemplazado por afinia_manager.py)
run_afinia_ov_visual.py      ❌ Redundante (reemplazado por afinia_manager.py)
```

#### 📚 **ESPECIALIZADOS - MOVER A EXAMPLES**
```
run_aire_ov_massive_with_pagination.py     💡 Casos especiales - paginación masiva
run_aire_ov_specific_sequence.py           💡 Casos especiales - secuencias específicas  
run_afinia_ov_massive_with_pagination.py   💡 Casos especiales - paginación masiva
run_afinia_ov_specific_sequence.py         💡 Casos especiales - secuencias específicas
```

### **📁 DIRECTORIOS PRINCIPALES**

#### 🔥 **CRÍTICOS - REORGANIZAR** (contienen lógica funcional)
```
a_core_01/              → src/core/           [BrowserManager, AuthenticationManager]
c_components_03/        → src/components/     [PQR processors, filtros, componentes específicos]  
d_downloaders_04/       → src/extractors/     [⚡ CRÍTICO: Extractores principales Aire/Afinia]
e_processors_05/        → src/processors/     [Procesadores de datos]
f_config_06/            → src/config/         [Configuraciones del sistema]
g_utils_07/             → src/utils/          [Utilidades generales]
ubuntu_config/          → config/ubuntu/      [⚡ CRÍTICO: Config Ubuntu Server]
```

#### 💾 **DATOS - CONSOLIDAR**
```
m_downloads_13/         → data/downloads/     [Descargas principales]
n_logs_14/              → data/logs/          [Logs principales] 
o_metrics_15/           → data/metrics/       [Métricas del sistema]
downloads/              → data/downloads/general/  [Consolidar con m_downloads_13]
logs/                   → data/logs/general/  [Consolidar con n_logs_14]
data/                   → data/general/       [Mantener y organizar]
```

#### 🧪 **TESTS Y EJEMPLOS - REORGANIZAR**
```
i_tests_09/             → tests/unit/         [Tests existentes]
h_dashboard_08/         → examples/dashboard/ [Demo dashboard]
l_scripts_12/           → examples/tutorials/ [Scripts varios]
```

#### 📦 **LEGACY Y DEPRECADOS - CONSOLIDAR**
```
j_docs_10/              → legacy/deprecated_docs/  [Docs obsoletos]
t_legacy_19/            → legacy/archive/          [Legacy existente]
b_adapters_02/          → legacy/old_components/   [Adaptadores obsoletos?]
p_validator_16/         → src/utils/validators/    [O legacy si obsoleto]
q_uploader_17/          → legacy/old_components/   [Si no se usa]
```

#### 🗑️ **ELIMINAR**
```
temp_test/              ❌ ELIMINAR - Directorio temporal
__pycache__/            ⚪ MANTENER - Cache Python (normal)
.venv/                  ⚪ MANTENER - Entorno virtual
```

## 🔗 **ANÁLISIS DE DEPENDENCIAS**

### **Imports Críticos que deben actualizarse:**

#### En `aire_manager.py`:
```python
# ACTUAL:
from d_downloaders_04.aire.oficina_virtual_aire_modular import OficinaVirtualAireModular

# NUEVO:  
from src.extractors.aire.oficina_virtual_aire_modular import OficinaVirtualAireModular
```

#### En `afinia_manager.py`:
```python  
# ACTUAL:
from d_downloaders_04.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular

# NUEVO:
from src.extractors.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular
```

#### En archivos de componentes:
```python
# ACTUAL:
from a_core_01.browser_manager import BrowserManager
from c_components_03.aire_pqr_processor import AirePQRProcessor

# NUEVO:
from src.core.browser_manager import BrowserManager  
from src.components.aire_pqr_processor import AirePQRProcessor
```

## ⚠️ **RIESGOS Y MITIGACIONES**

### **🚨 ALTO RIESGO:**
- `d_downloaders_04/` - Contiene extractores principales
- `ubuntu_config/` - Configuración Ubuntu Server  
- `aire_manager.py` / `afinia_manager.py` - Managers principales

**MITIGACIÓN:** 
- Backup completo antes de mover
- Actualizar imports inmediatamente después de mover
- Probar funcionalidad después de cada cambio mayor

### **⚠️ MEDIO RIESGO:**
- Archivos de configuración en `f_config_06/`
- Componentes específicos en `c_components_03/`
- Core components en `a_core_01/`

**MITIGACIÓN:**
- Actualizar rutas en configuraciones
- Verificar que todos los imports se actualicen
- Mantener estructura interna de directorios

### **✅ BAJO RIESGO:**
- Archivos run_* obsoletos (ya reemplazados)
- Directorios de datos (solo cambio de ubicación)
- Documentación y ejemplos

## 📋 **CHECKLIST PRE-REORGANIZACIÓN**

### **Antes de empezar:**
- [ ] ✅ Crear backup completo del proyecto
- [ ] ✅ Confirmar que aire_manager.py funciona  
- [ ] ✅ Confirmar que afinia_manager.py funciona
- [ ] ✅ Documentar imports actuales críticos
- [ ] ✅ Preparar plan de rollback

### **Durante la reorganización:**
- [ ] 📁 Crear nueva estructura de directorios
- [ ] 🔄 Mover directorios uno por uno
- [ ] 📝 Actualizar imports inmediatamente  
- [ ] 🧪 Probar funcionalidad después de cada fase
- [ ] 📋 Verificar que no se rompa nada crítico

### **Post-reorganización:**
- [ ] ✅ Probar aire_manager.py --test --visual
- [ ] ✅ Probar afinia_manager.py --test --visual  
- [ ] ✅ Verificar imports principales
- [ ] ✅ Probar configuración Ubuntu
- [ ] 📖 Actualizar documentación

## 🎯 **RESULTADO ESPERADO**

### **Estructura Final:**
```
ExtractorOV_Modular/
├── aire_manager.py              # 🚀 FUNCIONAL
├── afinia_manager.py            # 🚀 FUNCIONAL
├── requirements.txt             # 📋 DEPENDENCIAS  
├── src/                         # 🏗️ CÓDIGO FUENTE ORGANIZADO
├── config/                      # ⚙️ CONFIGURACIONES CENTRALIZADAS
├── data/                        # 💾 DATOS CONSOLIDADOS
├── examples/                    # 📚 CASOS ESPECIALES
├── legacy/                      # 📦 ARCHIVOS OBSOLETOS
├── docs/                        # 📖 DOCUMENTACIÓN
└── tests/                       # 🧪 PRUEBAS ORGANIZADAS
```

### **Beneficios:**
✅ Código fuente en `src/` (convención Python)  
✅ Configuraciones centralizadas en `config/`
✅ Datos consolidados en `data/`  
✅ Ejemplos organizados en `examples/`
✅ Legacy aislado en `legacy/`
✅ Solo managers funcionales en raíz
✅ Fácil navegación y mantenimiento
✅ Preparado para crecer y escalar