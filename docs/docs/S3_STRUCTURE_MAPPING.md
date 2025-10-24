# Mapeo de Estructura S3 - Extractor OV Modular

## Objetivo

Documentar la estructura actual de S3 y su alineación con los requerimientos del sistema de Oficina Virtual para Afinia y Air-e.

**Fecha:** Octubre 2025  
**Autor:** ISES | Analyst Data Jeam Paul Arcon Solano  
**Referencia:** Paso 21 del FLUJO_VERIFICACION.md

---

## Estructura S3 Requerida vs Actual

### Estructura Requerida (Según Especificaciones)

```
bucket-name/
├── afinia/
│   ├── 01_raw_data/
│   │   └── oficina_virtual/
│   │       ├── json/
│   │       │   ├── YYYY/MM/DD/
│   │       │   │   ├── archivo_001.json
│   │       │   │   ├── archivo_002.json
│   │       │   │   └── ...
│   │       └── csv/
│   │           ├── YYYY/MM/DD/
│   │           │   ├── archivo_001.csv
│   │           │   ├── archivo_002.csv
│   │           │   └── ...
│   ├── 02_processed_data/
│   └── 03_reports/
└── aire/
    ├── 01_raw_data/
    │   └── oficina_virtual/
    │       ├── json/
    │       └── csv/
    ├── 02_processed_data/
    └── 03_reports/
```

### Estructura Actual (Implementada en aws_s3_service.py)

Según el análisis del código en `src/services/aws_s3_service.py`:

```python
def generate_s3_key(self, empresa: str, numero_reclamo: str, extension: str = "json") -> str:
    """
    Generar clave S3 basada en empresa y número de reclamo
    Formato: {empresa}/oficina_virtual/{numero_reclamo}.{extension}
    """
    return f"{empresa}/oficina_virtual/{numero_reclamo}.{extension}"
```

**Estructura Actual:**
```
bucket-name/
├── afinia/
│   └── oficina_virtual/
│       ├── 12345678.json
│       ├── 12345679.json
│       └── ...
└── aire/
    └── oficina_virtual/
        ├── 87654321.json
        ├── 87654322.json
        └── ...
```

---

## Análisis de Diferencias

### ❌ Diferencias Identificadas

1. **Falta estructura de carpetas por fecha**
   - **Requerido:** `01_raw_data/oficina_virtual/json/YYYY/MM/DD/`
   - **Actual:** `oficina_virtual/`

2. **Falta separación por tipo de archivo**
   - **Requerido:** Carpetas separadas para `json/` y `csv/`
   - **Actual:** Todo en la misma carpeta

3. **Falta estructura de procesamiento**
   - **Requerido:** Carpetas `02_processed_data/` y `03_reports/`
   - **Actual:** Solo datos raw

4. **Nomenclatura de archivos**
   - **Requerido:** Nombres descriptivos con fecha/hora
   - **Actual:** Solo número de reclamo

### ✅ Aspectos Correctos

1. **Separación por empresa**
   - ✅ Correcta separación entre `afinia/` y `aire/`

2. **Identificación por número de reclamo**
   - ✅ Uso del número de reclamo como identificador único

3. **Extensión de archivos**
   - ✅ Soporte para diferentes extensiones (json, csv)

---

## Opciones de Alineación

### Opción 1: Migración Completa (Recomendada)

**Ventajas:**
- Cumple completamente con especificaciones
- Mejor organización y escalabilidad
- Facilita búsquedas y mantenimiento

**Desventajas:**
- Requiere migración de archivos existentes
- Cambios en código de múltiples servicios

**Implementación:**
```python
def generate_s3_key_v2(self, empresa: str, numero_reclamo: str, 
                      extension: str = "json", fecha: datetime = None) -> str:
    """
    Generar clave S3 con estructura completa
    Formato: {empresa}/01_raw_data/oficina_virtual/{tipo}/{YYYY}/{MM}/{DD}/{numero_reclamo}_{timestamp}.{extension}
    """
    if fecha is None:
        fecha = datetime.now()
    
    tipo = "json" if extension == "json" else "csv"
    timestamp = fecha.strftime("%H%M%S")
    
    return (f"{empresa}/01_raw_data/oficina_virtual/{tipo}/"
            f"{fecha.year:04d}/{fecha.month:02d}/{fecha.day:02d}/"
            f"{numero_reclamo}_{timestamp}.{extension}")
```

### Opción 2: Estructura Híbrida (Intermedia)

**Implementación:**
```python
def generate_s3_key_hybrid(self, empresa: str, numero_reclamo: str, 
                          extension: str = "json") -> str:
    """
    Estructura híbrida que mantiene compatibilidad
    Formato: {empresa}/01_raw_data/oficina_virtual/{numero_reclamo}.{extension}
    """
    return f"{empresa}/01_raw_data/oficina_virtual/{numero_reclamo}.{extension}"
```

### Opción 3: Mantener Actual + Documentar (Mínima)

**Ventajas:**
- Sin cambios de código
- Sin migración necesaria

**Desventajas:**
- No cumple especificaciones
- Limitaciones futuras de escalabilidad

---

## Impacto en Servicios

### Servicios Afectados por Cambio de Estructura

1. **`aws_s3_service.py`**
   - Método `generate_s3_key()`
   - Método `check_file_exists_in_s3()`
   - Método `upload_file()`

2. **`s3_verification_service.py`**
   - Lógica de verificación de archivos
   - Comparación con registros RDS

3. **`filtered_s3_uploader.py`**
   - Generación de rutas de subida
   - Verificación de duplicados

4. **Base de datos `data_general.registros_ov_s3`**
   - Campo `ruta_s3` necesitará actualización
   - Posible migración de datos existentes

### Archivos de Configuración

```python
# config/s3_structure.py
S3_STRUCTURE_CONFIG = {
    "version": "2.0",
    "base_structure": {
        "raw_data": "01_raw_data",
        "processed_data": "02_processed_data", 
        "reports": "03_reports"
    },
    "oficina_virtual": {
        "json_path": "oficina_virtual/json",
        "csv_path": "oficina_virtual/csv"
    },
    "date_format": {
        "year": "%Y",
        "month": "%m", 
        "day": "%d"
    },
    "filename_format": "{numero_reclamo}_{timestamp}.{extension}"
}
```

---

## Plan de Migración Recomendado

### Fase 1: Preparación (1-2 días)
1. ✅ Documentar estructura actual (este documento)
2. 🔄 Crear configuración de nueva estructura
3. 🔄 Desarrollar utilidades de migración
4. 🔄 Crear tests para nueva estructura

### Fase 2: Implementación (2-3 días)
1. 🔄 Actualizar `aws_s3_service.py` con nueva estructura
2. 🔄 Modificar servicios dependientes
3. 🔄 Actualizar base de datos y registros
4. 🔄 Ejecutar tests de integración

### Fase 3: Migración de Datos (1-2 días)
1. 🔄 Script de migración de archivos existentes
2. 🔄 Actualización de registros en RDS
3. 🔄 Verificación de integridad post-migración
4. 🔄 Backup de estructura anterior

### Fase 4: Validación (1 día)
1. 🔄 Tests end-to-end con nueva estructura
2. 🔄 Verificación de todos los flujos
3. 🔄 Documentación actualizada
4. 🔄 Capacitación del equipo

---

## Recomendación Final

**Se recomienda implementar la Opción 1 (Migración Completa)** por las siguientes razones:

1. **Cumplimiento de especificaciones:** Alinea completamente con los requerimientos
2. **Escalabilidad:** Facilita el crecimiento futuro del sistema
3. **Mantenibilidad:** Estructura más clara y organizada
4. **Búsquedas eficientes:** Permite filtros por fecha y tipo
5. **Separación de responsabilidades:** Clara distinción entre raw, processed y reports

### Cronograma Estimado
- **Tiempo total:** 6-8 días
- **Esfuerzo:** 1 desarrollador senior
- **Riesgo:** Medio (requiere coordinación con otros sistemas)

### Criterios de Éxito
- ✅ Todos los archivos migrados correctamente
- ✅ Servicios funcionando con nueva estructura
- ✅ Tests pasando al 100%
- ✅ Documentación actualizada
- ✅ Sin pérdida de datos

---

## Próximos Pasos

1. **Inmediato:** Revisar y aprobar este documento
2. **Esta semana:** Implementar Opción 1 según plan de migración
3. **Siguiente semana:** Ejecutar migración y validación
4. **Seguimiento:** Monitoreo post-migración durante 1 semana

---

**Estado:** 📋 Documentado - Pendiente de implementación  
**Prioridad:** 🔴 Alta  
**Dependencias:** Aprobación del plan de migración