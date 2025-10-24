# 🚀 Sistema Mercurio - Despliegue en Producción

## 📋 Resumen Ejecutivo

El **Sistema Mercurio** es una solución completa y funcional para la extracción automatizada de datos PQR desde las plataformas Mercurio de **Afinia** y **Aire**. El sistema incluye:

✅ **Carga directa a RDS** con validación de duplicados  
✅ **Arquitectura modular** y escalable  
✅ **Validación robusta** de datos  
✅ **Manejo de errores** y logging centralizado  
✅ **Configuración flexible** por empresa  

---

## 📁 Archivos para Producción

### 🔧 **Archivos Core (Obligatorios)**

```
Merc/
├── main.py                          # Punto de entrada principal
├── requirements.txt                 # Dependencias del sistema
├── flujos.yaml                     # Configuración de flujos
├── .env.template                   # Plantilla de variables de entorno
└── run_afinia_only.py              # Script de ejecución específico
```

### 🏗️ **Módulos Core**

```
Merc/core/
├── __init__.py                     # Componentes base del sistema
├── base_extractor.py               # Extractor base
├── browser_manager.py              # Gestor de navegadores
├── authentication_manager.py       # Autenticación centralizada
├── mercurio_adapter.py             # Adaptador específico Mercurio
├── afinia_data_processor.py        # Procesador datos Afinia
├── aire_data_processor.py          # Procesador datos Aire
├── afinia_database_manager.py      # Gestor BD Afinia
└── aire_database_manager.py        # Gestor BD Aire
```

### ⚙️ **Configuración**

```
Merc/config/
├── __init__.py
└── afinia_config.py                # Configuración específica Mercurio
```

### 🔌 **Servicios**

```
Merc/services/
├── afinia_extractor.py             # Extractor Mercurio Afinia
└── aire_extractor.py               # Extractor Mercurio Aire
```

### 🛠️ **Utilidades**

```
Merc/utils/
├── __init__.py
├── afinia_validators.py            # Validadores específicos Mercurio
└── aire_logger.py                  # Sistema de logging
```

### 📊 **Scripts de Carga Directa**

```
Merc/scripts/
├── direct_json_to_rds_loader.py           # Carga directa básica
├── direct_json_to_rds_loader_with_files.py # Carga con archivos S3
└── validate_functionality.py              # Validación del sistema
```

## 🔧 Configuración de Producción

### 1. **Variables de Entorno (.env)**

```bash
# Credenciales Mercurio Afinia
MERCURIO_AFINIA_USERNAME=tu_usuario_afinia
MERCURIO_AFINIA_PASSWORD=tu_password_afinia

# Credenciales Mercurio Aire
MERCURIO_AIRE_USERNAME=tu_usuario_aire
MERCURIO_AIRE_PASSWORD=tu_password_aire

# Configuración RDS
RDS_HOST=tu-rds-endpoint.amazonaws.com
RDS_PORT=3306
RDS_DATABASE=data_general
RDS_USERNAME=tu_usuario_rds
RDS_PASSWORD=tu_password_rds

# Configuración AWS S3
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=tu-bucket-s3
```

### 2. **Instalación de Dependencias**

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno (Windows)
.venv\Scripts\activate

# Activar entorno (Linux/Mac)
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar navegadores Playwright
playwright install chromium
```

---

## 🚀 Ejecución en Producción

### **Opción 1: Ejecución Completa**
```bash
python main.py
```

### **Opción 2: Solo Afinia**
```bash
python run_afinia_only.py
```

### **Opción 3: Carga Directa de Datos**
```bash
python scripts/direct_json_to_rds_loader.py
```

---

## 📊 Características Técnicas Implementadas

### ✅ **Carga Directa a RDS**
- **Esquema específico**: `mercurio_afinia_pqr` y `mercurio_aire_pqr`
- **Validación de duplicados**: Por hash MD5 y número de radicado
- **Transacciones seguras**: Rollback automático en errores
- **Carga por lotes**: Optimizada para grandes volúmenes

### ✅ **Validación de Duplicados**
```python
# Algoritmo implementado en MercurioAfiniaDatabaseManager
def get_record_by_hash(self, hash_value: str) -> Optional[Dict]:
    """Verifica duplicados por hash MD5"""
    # Campos clave: numero_radicado + numero_reclamo_sgc + cuerpo_reclamacion
```

### ✅ **Arquitectura Modular**
- **Adaptador Mercurio**: Lógica común para ambas empresas
- **Extractores específicos**: Afinia y Aire independientes
- **Procesadores de datos**: Validación y transformación
- **Gestores de BD**: Operaciones específicas por empresa

### ✅ **Configuración Robusta**
- **Esquemas definidos**: `MERCURIO_PQR_SCHEMA` con índices optimizados
- **Mapeo de campos**: `FIELD_MAPPING_MERCURIO` para consistencia
- **URLs específicas**: Configuración por empresa en `flujos.yaml`

---

## 📈 Métricas y Monitoreo

### **Logging Centralizado**
- Logs detallados en `logs/extractor_merc.log`
- Niveles: INFO, WARNING, ERROR
- Formato estándar con timestamps

### **Estadísticas de Procesamiento**
```python
processing_stats = {
    'files_processed': 0,
    'records_processed': 0,
    'records_inserted': 0,
    'duplicates_found': 0,
    'validation_errors': 0,
    'database_errors': 0
}
```

---

## 🔒 Seguridad Implementada

✅ **Credenciales seguras** en variables de entorno  
✅ **Conexiones SSL** a RDS  
✅ **Validación de entrada** en todos los datos  
✅ **Manejo seguro de errores** sin exposición de datos  
✅ **Logs sin credenciales** sensibles  

---

## 📋 Comando de Empaquetado

```bash
# Crear paquete para producción
tar -czf mercurio_production.tar.gz \
  --exclude='.venv' \
  --exclude='legacy' \
  --exclude='tests' \
  --exclude='docs' \
  --exclude='ai-context' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  Merc/
```

---

## ✅ Estado del Sistema

**🟢 LISTO PARA PRODUCCIÓN**

- ✅ Extracción automatizada funcional
- ✅ Carga directa a RDS implementada
- ✅ Validación de duplicados operativa
- ✅ Arquitectura modular estable
- ✅ Configuración flexible
- ✅ Logging y monitoreo activo
- ✅ Manejo robusto de errores
- ✅ Documentación completa

---

##  Soporte

Para soporte técnico o consultas sobre el sistema:
- **Logs**: Revisar `logs/extractor_merc.log`
- **Validación**: Ejecutar `scripts/validate_functionality.py`
- **Estado**: Verificar conectividad RDS y credenciales

---

*Extractor para Mercurio - 2025*  
*Arquitectura modular con carga directa a RDS y validación de duplicados*