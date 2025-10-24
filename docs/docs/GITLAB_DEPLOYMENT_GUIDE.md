# 🚀 GUÍA DE DEPLOYMENT PARA GITLAB EMPRESARIAL
## ExtractorOV_Modular v2.0

**Fecha:** 9 de Octubre 2025  
**Sistema:** ExtractorOV_Modular  
**Servicios:** Afinia y Aire

---

## 📁 **CARPETAS ESENCIALES PARA GITLAB**

### ✅ **INCLUIR EN GITLAB (Carpetas principales)**

```
ExtractorOV_Modular/
├── 📂 src/                          # ⭐ CORE DEL SISTEMA
│   ├── components/                  # Componentes modulares
│   ├── config/                      # Configuraciones (sin .env)
│   ├── core/                        # Funcionalidades base
│   ├── extractors/                  # Extractores Afinia/Aire
│   ├── processors/                  # Procesadores de datos
│   ├── services/                    # Servicios externos
│   └── utils/                       # Utilidades comunes
│
├── 📂 config/                       # ⭐ CONFIGURACIONES
│   ├── ubuntu_config/               # Configuración Ubuntu Server
│   └── README.md                    # Documentación
│
├── 📂 examples/                     # ⭐ EJEMPLOS Y TUTORIALES
│   ├── data_processing/             # Procesamiento de datos
│   ├── massive_processing/          # Procesamiento masivo
│   ├── specialized_sequences/       # Secuencias específicas
│   ├── tutorials/                   # Tutoriales paso a paso
│   └── web_dashboards/              # Dashboards web
│
├── 📂 tests/                        # ⭐ PRUEBAS UNITARIAS
│   └── unit/                        # Pruebas específicas
│
├── 📂 scripts/                      # ⭐ SCRIPTS DE MANTENIMIENTO
│   ├── fix_logging_paths.py         # Scripts de logging
│   ├── validate_functionality.py    # Validación funcional
│   └── ubuntu_setup.sh              # Setup Ubuntu
│
├── 📂 docs/                         # ⭐ DOCUMENTACIÓN TÉCNICA
│   ├── analysis/                    # Análisis técnicos
│   ├── planning/                    # Planificación
│   ├── reports/                     # Reportes
│   └── setup/                       # Documentación setup
│
├── 📂 data/                         # 📁 ESTRUCTURA DATOS
│   └── README.md                    # Solo documentación
│
├── 📄 README.md                     # ⭐ DOCUMENTACIÓN PRINCIPAL
├── 📄 requirements.txt              # ⭐ DEPENDENCIAS PYTHON
├── 📄 afinia_manager.py             # ⭐ MANAGER AFINIA
├── 📄 aire_manager.py               # ⭐ MANAGER AIRE  
├── 📄 .gitignore                    # ⭐ CONTROL DE ARCHIVOS
└── 📄 GITLAB_DEPLOYMENT_GUIDE.md    # ⭐ ESTA GUÍA
```

### ❌ **NO INCLUIR EN GITLAB (Carpetas que excluir)**

```
ExtractorOV_Modular/
├── 🚫 legacy/                       # Archivos deprecated
│   ├── deprecated_docs/             # Documentación obsoleta  
│   ├── old_components/              # Componentes antiguos
│   └── old_runners/                 # Runners obsoletos
│
├── 🚫 ai-context/                   # Contexto específico de AI
│   ├── analyze_performance.py       # Análisis específico
│   ├── REPORTE_MEJORAS_*.md         # Reportes internos
│   └── PROJECT_STANDARDS.md         # Estándares internos
│
├── 🚫 logs/                         # Logs del sistema
├── 🚫 downloads/                    # Archivos descargados
├── 🚫 screenshots/                  # Screenshots de debugging
├── 🚫 .venv/                        # Entorno virtual
├── 🚫 __pycache__/                  # Cache de Python
├── 🚫 *.env                         # Variables de entorno
└── 🚫 *.log                         # Archivos de log
```

---

## 🔒 **INFORMACIÓN SENSIBLE - NUNCA INCLUIR**

### ⚠️ **Archivos de credenciales:**
- ❌ `.env`, `.env.local`, `*.env`
- ❌ `credentials.json`, `secrets.json`
- ❌ `config.local.py`
- ❌ Cualquier archivo con passwords, tokens, API keys

### ⚠️ **Datos operacionales:**
- ❌ `logs/`, `*.log` (contienen información de sesiones)
- ❌ `downloads/`, `test_downloads/` (PDFs descargados)
- ❌ `screenshots/` (capturas pueden contener datos sensibles)
- ❌ Base de datos local: `*.db`, `*.sqlite`

### ⚠️ **Configuraciones específicas:**
- ❌ Archivos con URLs específicas de producción
- ❌ Configuraciones de bases de datos reales
- ❌ Tokens de servicios AWS/S3

---

## 📋 **CHECKLIST DE PREPARACIÓN PARA GITLAB**

### ✅ **Antes de subir al repositorio:**

1. **Verificar .gitignore actualizado:**
   ```bash
   # Verificar que el .gitignore incluye:
   *.env
   logs/
   downloads/
   screenshots/
   .venv/
   __pycache__/
   ```

2. **Limpiar archivos sensibles:**
   ```bash
   # Buscar y eliminar archivos .env
   find . -name "*.env" -not -path "./.env.example" -delete
   
   # Limpiar logs
   rm -rf logs/ *.log
   
   # Limpiar downloads
   rm -rf downloads/ test_downloads/
   
   # Limpiar screenshots
   rm -rf screenshots/ *.png *.jpg
   ```

3. **Verificar archivos .env.example:**
   ```bash
   # Asegurar que existen los archivos ejemplo:
   src/processors/afinia/.env.example
   src/processors/aire/.env.example
   legacy/old_components/q_uploader_17/.env.example
   ```

4. **Validar estructura:**
   ```bash
   # Ejecutar script de validación
   python scripts/validate_functionality.py
   ```

---

## 🛠️ **CONFIGURACIÓN DE .GITIGNORE EMPRESARIAL**

### **Versión recomendada para GitLab:**

```gitignore
# ============================================================================
# EXTRACTOR OV MODULAR - GITIGNORE EMPRESARIAL
# ============================================================================

# Variables de entorno y credenciales (CRÍTICO)
.env
.env.*
*.env
!*.env.example
config.local.py
credentials.json
secrets.json

# Datos operacionales sensibles (CRÍTICO)
logs/
*.log
downloads/
test_downloads/
integration_test_downloads/
screenshots/
*.png
*.jpg
*.jpeg

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Base de datos local
*.db
*.sqlite
*.sqlite3

# Archivos temporales
~$*
Thumbs.db
desktop.ini

# Testing y coverage
.pytest_cache/
.coverage
htmlcov/
.tox/

# Jupyter Notebook
.ipynb_checkpoints

# Playwright
.playwright/

# Específicos del proyecto
legacy/deprecated_docs/
ai-context/
r_env_*/
14_logs/
13_downloads/
```

---

## 🚀 **ESTRUCTURA RECOMENDADA EN GITLAB**

### **Organización de ramas:**

```
main                    # Rama principal (producción)
├── develop            # Rama de desarrollo
├── feature/logging    # Mejoras de logging
├── feature/afinia     # Mejoras Afinia
├── feature/aire       # Mejoras Aire
├── hotfix/security    # Parches críticos
└── release/v2.1       # Versiones específicas
```

### **Tags de versiones:**
```
v2.0.0    # Versión actual con logging profesional
v2.0.1    # Parches menores
v2.1.0    # Próxima versión mayor
```

---

## 📖 **DOCUMENTACIÓN A INCLUIR**

### ✅ **Documentación esencial:**

1. **README.md principal** - Descripción general del proyecto
2. **docs/setup/README_REQUISITOS_MINIMOS.md** - Requisitos mínimos
3. **config/README.md** - Documentación de configuración  
4. **examples/README.md** - Guías de uso
5. **src/processors/afinia/README.md** - Documentación Afinia
6. **src/processors/aire/README.md** - Documentación Aire

### ✅ **Documentación de setup:**

- **Instalación en Ubuntu:** `config/ubuntu_config/README.md`
- **Configuración de entorno:** `docs/setup/README_REQUISITOS_MINIMOS.md`
- **Guías de uso:** `examples/tutorials/`

---

## ⚡ **COMANDOS DE PREPARACIÓN RÁPIDA**

### **Script de limpieza pre-GitLab:**

```bash
# 1. Limpiar archivos sensibles
rm -rf logs/ downloads/ screenshots/
find . -name "*.env" -not -name "*.env.example" -delete
find . -name "*.log" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 2. Validar .gitignore
git check-ignore .env
git check-ignore logs/
git check-ignore downloads/

# 3. Verificar estructura
ls -la src/
ls -la config/
ls -la examples/

# 4. Test rápido de funcionalidad
python -m pytest tests/unit/ -v --tb=short

# 5. Validar requirements
pip freeze > requirements_current.txt
diff requirements.txt requirements_current.txt
```

---

## 🎯 **RECOMENDACIONES FINALES**

### **1. Seguridad:**
- ✅ **Nunca subir credenciales reales**
- ✅ **Usar archivos .env.example como plantillas**
- ✅ **Revisar cada commit antes de push**
- ✅ **Configurar branch protection en main**

### **2. Organización:**
- ✅ **Usar semantic versioning (v2.0.0)**
- ✅ **Tags descriptivos para releases**
- ✅ **Issues y MRs bien documentados**
- ✅ **CI/CD pipeline para testing automático**

### **3. Colaboración:**
- ✅ **README claro y actualizado**
- ✅ **Documentación de APIs internas**
- ✅ **Guías de contribución**
- ✅ **Changelog mantenido**

### **4. Mantenimiento:**
- ✅ **Scripts de validación automática**
- ✅ **Tests unitarios funcionando**
- ✅ **Logging profesional implementado**
- ✅ **Monitoreo de performance**

---

## 📊 **RESUMEN ESTADÍSTICO**

### **Carpetas a incluir:** 8 principales
- `src/`, `config/`, `examples/`, `tests/`, `scripts/`, `docs/`, `data/`, archivos raíz

### **Carpetas a excluir:** 3 principales  
- `legacy/`, `ai-context/`, archivos temporales/sensibles

### **Tamaño estimado del repo:** ~15-20 MB
- Sin archivos binarios, logs o descargas
- Con documentación completa
- Con ejemplos y tutoriales

### **Archivos críticos protegidos:** 100%
- Variables de entorno: ✅ Protegidas
- Credenciales: ✅ Protegidas  
- Logs operacionales: ✅ Protegidas
- Screenshots: ✅ Protegidas

---

*Guía generada automáticamente el 9 de Octubre 2025 para deployment empresarial de ExtractorOV_Modular v2.0*