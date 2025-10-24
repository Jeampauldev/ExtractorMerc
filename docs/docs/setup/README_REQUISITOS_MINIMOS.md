# REQUISITOS MÍNIMOS - ExtractorOV Modular

## GUÍA RÁPIDA PARA FUNCIONAMIENTO

Esta guía te dice **exactamente** lo que necesitas para que los extractores funcionen, sin archivos innecesarios.

## DEPENDENCIAS REQUERIDAS

### 1. Instalar Python y dependencias básicas
```powershell
# Instalar dependencias de Python
pip install playwright
pip install python-dotenv

# Instalar navegadores de Playwright
python -m playwright install
```

### 2. Verificar versión de Python
```powershell
python --version
# Necesitas Python 3.7 o superior
```

## ARCHIVOS MÍNIMOS REQUERIDOS

### NÚCLEO DEL SISTEMA (a_core_01/)
**Estos 3 archivos son ESENCIALES:**
```
a_core_01/
├── browser_manager.py        # Gestor de navegadores Playwright
├── authentication.py         # Sistema de login unificado
└── download_manager.py       # Gestor de descargas
```

### CONFIGURACIÓN (f_config_06/)
**Estos 2 archivos son ESENCIALES:**
```
f_config_06/
├── unified_logging_config.py # Sistema de logging
└── config.py                 # Configuraciones base
```

### EXTRACTORES PRINCIPALES (d_downloaders_04/)
**Estos 2 archivos son ESENCIALES:**
```
d_downloaders_04/
├── afinia/
│   └── oficina_virtual_afinia_modular.py  # Extractor de Afinia
└── aire/
    └── oficina_virtual_aire_modular.py    # Extractor de Aire
```

### SCRIPTS DE EJECUCIÓN
**Estos 2 archivos son ESENCIALES:**
```
run_afinia_ov_visual.py       # Script principal para Afinia
run_aire_ov_visual.py         # Script principal para Aire
```

### VARIABLES DE ENTORNO
**Este 1 archivo es ESENCIAL:**
```
p16_env/
└── .env                      # Credenciales y configuración
```

## CREDENCIALES CONFIGURADAS

El archivo `p16_env/.env` ya contiene todas las credenciales necesarias:

```env
# OFICINA VIRTUAL AIRE
OV_AIRE_USERNAME=Augusto Rafael Perez Ayala
OV_AIRE_PASSWORD=BDYEdOSNDUbpJJMRrc00

# OFICINA VIRTUAL AFINIA
OV_AFINIA_USERNAME=OFICINA VIRTUAL CE
OV_AFINIA_PASSWORD=Oficinavirtual*

# URLs (configuradas automáticamente)
OV_AIRE_URL=https://caribesol.facture.co/...
OV_AFINIA_URL=https://caribemar.facture.co/...
```

## EJECUCIÓN INMEDIATA

### Probar Extractor de Afinia (FUNCIONAL COMPLETO)
```powershell
cd C:\00_Project_Dev\ExtractorOV_Modular
python run_afinia_ov_visual.py
```

**Resultado esperado:**
```
=== INICIANDO EXTRACTOR DE AFINIA EN MODO VISUAL ===
[AUTH-MANAGER] INFO: Login exitoso verificado
[AFINIA-PQR] INFO: === INICIANDO PROCESAMIENTO DE PQR ===
[AFINIA-PQR] INFO: PDF generado exitosamente
Extractor completado exitosamente
PQR procesados: 1
```

### Probar Extractor de Aire (LOGIN EXITOSO)
```powershell
cd C:\00_Project_Dev\ExtractorOV_Modular
python run_aire_ov_visual.py
```

**Resultado esperado:**
```
=== INICIANDO EXTRACTOR DE AIRE EN MODO VISUAL ===
[AUTH-MANAGER] INFO: Login exitoso verificado con selector: body
Navegación a PQRs exitosa
Extractor completado exitosamente
Registros extraídos: 0
```

## ARCHIVOS QUE NO NECESITAS

**Estos archivos son complementarios (puedes ignorarlos para funcionalidad básica):**

- `c_components_03/` - Componentes modulares adicionales
- `e_processors_05/` - Procesadores específicos 
- `run_*_headless.py` - Versiones sin interfaz gráfica
- `run_*_specific_sequence.py` - Versiones con secuencia específica
- `n_logs_14/` - Se crea automáticamente
- `m13_downloads/` - Se crea automáticamente
- `o_metrics_15/` - Se crea automáticamente

## SOLUCIÓN DE PROBLEMAS RÁPIDA

### Error: "ModuleNotFoundError"
```powershell
# Asegúrate de estar en el directorio correcto
cd C:\00_Project_Dev\ExtractorOV_Modular
python run_afinia_ov_visual.py
```

### Error: "Playwright not found"
```powershell
pip install playwright
python -m playwright install
```

### Error: "Variables de entorno no encontradas"
```powershell
# Verificar que existe el archivo
dir p16_env\.env
# Debe existir y tener contenido
```

### Los extractores fallan en login
1. Verificar conectividad:
   - Afinia: https://caribemar.facture.co/login
   - Aire: https://caribesol.facture.co/login
2. Revisar screenshots en: `m13_downloads/servicio/oficina_virtual/screenshots/`

## VERIFICACIÓN RÁPIDA

**Para verificar que tienes todo lo necesario:**

```powershell
# Verificar archivos esenciales
dir a_core_01\browser_manager.py
dir a_core_01\authentication.py  
dir a_core_01\download_manager.py
dir f_config_06\unified_logging_config.py
dir f_config_06\config.py
dir d_downloaders_04\afinia\oficina_virtual_afinia_modular.py
dir d_downloaders_04\aire\oficina_virtual_aire_modular.py
dir run_afinia_ov_visual.py
dir run_aire_ov_visual.py
dir p16_env\.env

# Si todos estos archivos existen, tienes todo lo necesario
```

## RESUMEN EJECUTIVO

**TOTAL DE ARCHIVOS ESENCIALES: 10 archivos**

1. 3 archivos del núcleo (`a_core_01/`)
2. 2 archivos de configuración (`f_config_06/`) 
3. 2 extractores principales (`d_downloaders_04/`)
4. 2 scripts de ejecución (raíz)
5. 1 archivo de variables de entorno (`p16_env/`)

**CON ESTOS 10 ARCHIVOS + DEPENDENCIAS DE PYTHON = EXTRACTORES FUNCIONANDO**

---

## ESTADO FUNCIONAL ACTUAL

- **Afinia**: Login exitoso + Procesamiento de PQR completo + Descargas
- **Aire**: Login exitoso + Navegación a sección PQR + Base lista para procesamiento

**Ambos extractores están operativos para sus funciones principales.**