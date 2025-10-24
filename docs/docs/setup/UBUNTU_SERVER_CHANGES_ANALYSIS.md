# Análisis Completo - Adaptación para Ubuntu Server

## 📋 **RESUMEN EJECUTIVO**
Este documento detalla todos los cambios necesarios para ejecutar los extractores de Aire y Afinia en Ubuntu Server, sin hacer modificaciones aún al código actual.

---

## 🔍 **ÁREAS QUE REQUIEREN ADAPTACIÓN**

### 1. **RUTAS DE ARCHIVOS Y DIRECTORIOS**

#### **Problemas identificados:**
- Rutas hardcodeadas de Windows (`C:\`, `D:\`)
- Separadores de ruta específicos de Windows (`\`)
- Referencias a `m_downloads_13` y estructura de directorios

#### **Archivos que necesitan ajuste:**
```
f_config_06/config.py          # Rutas de descarga y screenshots
a_core_01/browser_manager.py   # Directorio de screenshots 
c_components_03/afinia_pqr_processor.py  # Rutas de descarga
c_components_03/aire_pqr_processor.py    # Rutas de descarga
```

#### **Cambios necesarios:**
- Usar `pathlib.Path` para compatibilidad multiplataforma
- Detectar automáticamente el sistema operativo
- Rutas base dinámicas: `/home/user/ExtractorOV_Modular/`

---

### 2. **CONFIGURACIÓN DE NAVEGADOR (HEADLESS)**

#### **Problemas identificados:**
- Modo visual por defecto (requiere interfaz gráfica)
- Argumentos de Chrome específicos para Windows
- Falta detección automática de entorno servidor

#### **Archivos que necesitan ajuste:**
```
a_core_01/browser_manager.py   # Configuración principal del navegador
f_config_06/config.py          # Configuración headless
run_afinia_ov_visual.py        # Script principal Afinia
run_aire_ov_visual.py          # Script principal Aire
```

#### **Cambios necesarios:**
- Detectar automáticamente si está en Ubuntu Server
- Activar modo headless automáticamente en servidor
- Argumentos de Chrome optimizados para Linux sin GUI
- Usar `xvfb-run` cuando sea necesario

---

### 3. **VARIABLES DE ENTORNO**

#### **Problemas identificados:**
- Archivo `.env` en `p16_env/.env` (ruta específica)
- Variables de entorno Windows-specific
- Falta configuración para modo servidor

#### **Archivos que necesitan ajuste:**
```
f_config_06/config.py               # Carga de variables de entorno
f_config_06/environment_loader.py   # Loader de entorno
p16_env/.env                        # Archivo de variables
```

#### **Cambios necesarios:**
- Variables de entorno para Ubuntu: `UBUNTU_SERVER=true`, `DISPLAY=:99`
- Rutas de descarga dinámicas
- Configuración automática de modo headless

---

### 4. **PERMISOS Y PROPIETARIOS DE ARCHIVOS**

#### **Problemas identificados:**
- Descargas y screenshots sin permisos apropiados
- Directorios sin permisos de escritura

#### **Cambios necesarios:**
- Establecer permisos `755` para directorios
- Establecer permisos `644` para archivos descargados
- Manejar usuarios no-root apropiadamente

---

### 5. **DEPENDENCIAS DEL SISTEMA**

#### **Dependencias requeridas en Ubuntu:**
```bash
# Dependencias del sistema
python3 python3-pip python3-venv
curl wget git unzip

# Dependencias para navegador headless
xvfb libnss3-dev libatk-bridge2.0-dev
libdrm-dev libxkbcommon-dev libgbm-dev
libasound2-dev libxrandr2 libxss1
libgconf-2-4 libxcomposite1 libxcursor1
libxdamage1 libxi6 libxtst6 libnss3
libcups2 libpangocairo-1.0-0 libatk1.0-0
libcairo-gobject2 libgtk-3-0 libgdk-pixbuf2.0-0

# Playwright y navegadores
playwright
```

---

## 🔧 **ESTRATEGIA DE IMPLEMENTACIÓN**

### **Fase 1: Detección Automática de Entorno**
```python
import os
import platform

def is_ubuntu_server():
    """Detecta si está ejecutándose en Ubuntu Server"""
    if platform.system() != 'Linux':
        return False
    
    # Verificar si es Ubuntu
    try:
        with open('/etc/os-release', 'r') as f:
            content = f.read()
            if 'Ubuntu' not in content:
                return False
    except FileNotFoundError:
        return False
    
    # Verificar si no hay DISPLAY (modo servidor)
    return os.getenv('DISPLAY') is None or os.getenv('UBUNTU_SERVER') == 'true'
```

### **Fase 2: Configuración Adaptiva de Rutas**
```python
from pathlib import Path
import os

class PathManager:
    def __init__(self):
        if is_ubuntu_server():
            self.base_dir = Path.home() / "ExtractorOV_Modular"
        else:
            self.base_dir = Path("C:/00_Project_Dev/ExtractorOV_Modular")
        
        self.downloads_dir = self.base_dir / "downloads"
        self.screenshots_dir = self.base_dir / "screenshots"
```

### **Fase 3: Configuración de Navegador Adaptiva**
```python
class AdaptiveBrowserManager:
    def __init__(self):
        self.is_server = is_ubuntu_server()
        self.headless = self.is_server  # Automático en servidor
        
        if self.is_server:
            self.chrome_args = self.get_server_chrome_args()
        else:
            self.chrome_args = self.get_desktop_chrome_args()
```

---

## 📁 **ESTRUCTURA DE ARCHIVOS NUEVA REQUERIDA**

```
ExtractorOV_Modular/
├── ubuntu_setup.sh              # ✅ Ya creado
├── ubuntu_config/
│   ├── ubuntu_paths.py          # 🔄 Nuevo - Gestión de rutas Linux
│   ├── ubuntu_browser.py        # 🔄 Nuevo - Config navegador servidor
│   └── environment_detector.py  # 🔄 Nuevo - Detección de entorno
├── scripts/
│   ├── run_afinia_ubuntu.sh     # 🔄 Nuevo - Script ejecución Afinia
│   ├── run_aire_ubuntu.sh       # 🔄 Nuevo - Script ejecución Aire
│   └── setup_permissions.sh     # 🔄 Nuevo - Configurar permisos
└── systemd/
    ├── extractor-afinia.service # 🔄 Nuevo - Servicio systemd
    └── extractor-aire.service   # 🔄 Nuevo - Servicio systemd
```

---

## 🚀 **SCRIPTS DE EJECUCIÓN REQUERIDOS**

### **run_afinia_ubuntu.sh**
```bash
#!/bin/bash
cd /home/$USER/ExtractorOV_Modular
source venv/bin/activate
export HEADLESS=true
export UBUNTU_SERVER=true
export DISPLAY=:99
xvfb-run -a python run_afinia_ov_visual.py
```

### **run_aire_ubuntu.sh**
```bash
#!/bin/bash
cd /home/$USER/ExtractorOV_Modular
source venv/bin/activate
export HEADLESS=true
export UBUNTU_SERVER=true
export DISPLAY=:99
xvfb-run -a python run_aire_ov_visual.py
```

---

## ⚙️ **MODIFICACIONES DE CÓDIGO NECESARIAS**

### **1. BrowserManager Adaptivo** (`a_core_01/browser_manager.py`)
- Detectar entorno automáticamente
- Configurar argumentos Chrome según SO
- Activar headless en servidor automáticamente

### **2. Config Multiplataforma** (`f_config_06/config.py`)
- Rutas dinámicas según SO
- Variables de entorno adaptivas
- Configuración de descarga multiplataforma

### **3. Procesadores PQR** (`c_components_03/`)
- Rutas de descarga dinámicas
- Manejo de permisos en Linux
- Screenshots con rutas correctas

### **4. Scripts Principales**
- `run_afinia_ov_visual.py`: Detección de entorno
- `run_aire_ov_visual.py`: Detección de entorno

---

## 🔒 **SEGURIDAD Y PERMISOS**

### **Permisos de archivos Linux:**
```bash
# Directorios
chmod 755 /home/user/ExtractorOV_Modular/
chmod 755 /home/user/ExtractorOV_Modular/downloads/
chmod 755 /home/user/ExtractorOV_Modular/screenshots/

# Archivos de configuración
chmod 600 /home/user/ExtractorOV_Modular/.env

# Scripts ejecutables
chmod +x /home/user/ExtractorOV_Modular/scripts/*.sh
```

---

## 📊 **ORDEN DE IMPLEMENTACIÓN RECOMENDADO**

1. ✅ **Script de instalación** (ubuntu_setup.sh) - COMPLETADO
2. 🔄 **Detector de entorno** - Crear función de detección
3. 🔄 **PathManager adaptivo** - Gestión de rutas multiplataforma
4. 🔄 **BrowserManager adaptivo** - Configuración navegador servidor
5. 🔄 **Config multiplataforma** - Configuración adaptiva
6. 🔄 **Scripts de ejecución** - Scripts bash para Ubuntu
7. 🔄 **Servicios systemd** - Auto-inicio en servidor
8. 🔄 **Testing completo** - Verificación funcionamiento

---

## 🎯 **RESULTADO ESPERADO**

Al completar todos estos cambios:

✅ **Detección automática**: El sistema detectará si está en Ubuntu Server  
✅ **Configuración adaptiva**: Rutas, navegador y entorno se configuran automáticamente  
✅ **Modo headless**: Se activa automáticamente en servidor  
✅ **Scripts de ejecución**: Comandos simples para ejecutar extractores  
✅ **Servicios systemd**: Auto-inicio y gestión de servicios  
✅ **Compatibilidad**: Funciona tanto en Windows como en Ubuntu Server  

**Comando final esperado:**
```bash
# Instalación
bash ubuntu_setup.sh

# Ejecución
bash scripts/run_afinia_ubuntu.sh
bash scripts/run_aire_ubuntu.sh

# O como servicio
sudo systemctl start extractor-afinia
sudo systemctl start extractor-aire
```