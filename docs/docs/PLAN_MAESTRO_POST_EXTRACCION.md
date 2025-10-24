# Plan Maestro: Sistema de Procesamiento Post-Extracción
## ExtractorOV_Modular - Versión Empresarial

---

### 📋 **RESUMEN EJECUTIVO**

Este plan detalla la implementación de un sistema robusto para el procesamiento post-extracción de datos de Afinia y Aire, incluyendo:

1. **Procesamiento masivo de JSON** → datasets consolidados
2. **Carga controlada a RDS** → base de datos ce-ia (esquema data_general)
3. **Carga organizada a S3** → bucket con estructura empresarial
4. **Sistema de monitoreo incremental** → detección de registros nuevos
5. **Automatización programada** → operación Lunes-Sábado (5AM-10PM)
6. **Validación y testing** → control de calidad integral
7. **Operación y mantenimiento** → documentación y troubleshooting

---

## 🎯 **FASE 1: PROCESAMIENTO MASIVO DE JSON**

### **Objetivo**
Procesar todos los archivos JSON de Afinia/Aire y crear datasets consolidados listos para carga a base de datos.

### **Componentes a Desarrollar**

#### **1.1 Consolidador de Archivos JSON**
```python
# src/services/json_consolidator_service.py
```

**Funcionalidades:**
- ✅ Escaneo automático de directorios `data/downloads/{afinia|aire}/oficina_virtual/`
- ✅ Lectura y validación de esquema de archivos JSON
- ✅ Deduplicación inteligente por `numero_radicado` + fecha
- ✅ Normalización de datos (fechas, teléfonos, emails)
- ✅ Generación de hash único para cada registro
- ✅ Consolidación en datasets únicos por empresa
- ✅ Generación de reportes de procesamiento

#### **1.2 Validador de Datos**
```python
# src/services/data_validator_service.py
```

**Validaciones:**
- ✅ Campos obligatorios: `numero_radicado`, `fecha`, `estado_solicitud`
- ✅ Formato de fechas: YYYY/MM/DD HH:MM
- ✅ Validación de NIC (solo números, longitud)
- ✅ Validación de correos electrónicos
- ✅ Validación de números de teléfono colombianos
- ✅ Detección de registros duplicados
- ✅ Identificación de registros incompletos

#### **1.3 Generador de Datasets**
```python
# src/services/dataset_generator_service.py
```

**Salidas:**
- ✅ **CSV para BD**: `data/processed/afinia_consolidated_YYYYMMDD.csv`
- ✅ **CSV para BD**: `data/processed/aire_consolidated_YYYYMMDD.csv`
- ✅ **JSON maestro**: archivos JSON limpios y validados
- ✅ **Reportes**: estadísticas de procesamiento y calidad
- ✅ **Logs detallados**: trazabilidad completa del procesamiento

### **Testing de Fase 1**
- ✅ Test unitarios para cada validación
- ✅ Test de integración con archivos reales
- ✅ Test de performance con volúmenes grandes
- ✅ Validación de calidad de datos

---

## 🗄️ **FASE 2: CONFIGURACIÓN Y CONEXIÓN RDS**

### **Objetivo**
Establecer conexión robusta con la base de datos `ce-ia` en el esquema `data_general` con las tablas `ov_afinia` y `ov_aire`.

### **Componentes a Desarrollar**

#### **2.1 Configuración RDS Enterprise**
```python
# src/config/rds_config.py
```

**Características:**
- ✅ Pool de conexiones con `SQLAlchemy`
- ✅ Configuración de SSL/TLS
- ✅ Gestión de timeouts y reintentos
- ✅ Monitoreo de salud de conexión
- ✅ Rotación automática de credenciales (opcional)

#### **2.2 Modelos de Datos**
```python
# src/models/ov_models.py
```

**Esquemas de BD:**
```sql
-- Tabla ov_afinia (esquema data_general)
CREATE TABLE data_general.ov_afinia (
    id SERIAL PRIMARY KEY,
    numero_radicado VARCHAR(50) UNIQUE NOT NULL,
    fecha TIMESTAMP NOT NULL,
    estado_solicitud VARCHAR(100),
    tipo_pqr VARCHAR(200),
    nic VARCHAR(20),
    nombres_apellidos VARCHAR(200),
    telefono VARCHAR(20),
    celular VARCHAR(20),
    correo_electronico VARCHAR(100),
    documento_identidad VARCHAR(20),
    canal_respuesta VARCHAR(100),
    hash_registro VARCHAR(64) UNIQUE,
    fecha_extraccion TIMESTAMP DEFAULT NOW(),
    archivos_s3_urls JSONB,
    procesado_flag BOOLEAN DEFAULT FALSE,
    INDEX idx_numero_radicado (numero_radicado),
    INDEX idx_fecha (fecha),
    INDEX idx_hash (hash_registro)
);

-- Tabla ov_aire (esquema data_general)
CREATE TABLE data_general.ov_aire (
    -- Misma estructura que ov_afinia
);
```

#### **2.3 Gestor de Conexión Empresarial**
```python
# src/services/rds_connection_service.py
```

**Funcionalidades:**
- ✅ Pool de conexiones configurables
- ✅ Manejo de reconexión automática
- ✅ Monitoring de performance
- ✅ Logging detallado de operaciones
- ✅ Validación de esquemas y tablas
- ✅ Backup automático antes de operaciones masivas

### **Testing de Fase 2**
- ✅ Test de conectividad a RDS
- ✅ Validación de esquemas y tablas
- ✅ Test de inserción y consulta
- ✅ Test de performance con volúmenes grandes
- ✅ Test de recuperación ante fallos

---

## 📊 **FASE 3: SERVICIO DE CARGA MASIVA A BD**

### **Objetivo**
Implementar carga robusta y controlada de datos a las tablas RDS con detección de duplicados y manejo de errores.

### **Componentes a Desarrollar**

#### **3.1 Motor de Carga Masiva**
```python
# src/services/bulk_loader_service.py
```

**Funcionalidades:**
- ✅ Carga por lotes optimizada (batch size configurable)
- ✅ Control de duplicados por hash y numero_radicado
- ✅ Modo UPSERT (INSERT + UPDATE inteligente)
- ✅ Rollback automático en caso de errores
- ✅ Progress tracking con estimaciones de tiempo
- ✅ Logging detallado de cada operación

#### **3.2 Control de Duplicados**
```python
# src/services/duplicate_control_service.py
```

**Estrategias:**
- ✅ **Nivel 1**: Por hash de registro (cambios menores)
- ✅ **Nivel 2**: Por numero_radicado + fecha (duplicados exactos)
- ✅ **Nivel 3**: Por similitud de contenido (fuzzy matching)
- ✅ Marcado de registros como actualizados vs nuevos
- ✅ Historial de cambios y actualizaciones

#### **3.3 Monitor de Carga**
```python
# src/services/load_monitor_service.py
```

**Monitoreo:**
- ✅ Métricas en tiempo real: registros/segundo
- ✅ Detección de errores y alertas
- ✅ Estimación de tiempo restante
- ✅ Generación de reportes de carga
- ✅ Dashboard web opcional para monitoreo

### **Testing de Fase 3**
- ✅ Test de carga masiva con datasets reales
- ✅ Test de detección de duplicados
- ✅ Test de recuperación ante fallos
- ✅ Test de performance con 10K+ registros
- ✅ Validación de integridad de datos

---

## ☁️ **FASE 4: CONFIGURACIÓN Y SERVICIOS AWS S3**

### **Objetivo**
Configurar servicios S3 para carga organizada de archivos (PDFs, JSONs, adjuntos) con estructura empresarial.

### **Componentes a Desarrollar**

#### **4.1 Configuración S3 Enterprise**
```python
# src/config/s3_config.py
```

**Configuración:**
- ✅ SDK boto3 con configuración optimizada
- ✅ Políticas de retry y timeout
- ✅ Encriptación en tránsito y reposo
- ✅ Configuración de regiones y endpoints
- ✅ Gestión de credenciales IAM

#### **4.2 Estructura de Carpetas**

**Para Afinia:**
```
Central_De_Escritos/
└── Afinia/
    └── 01_raw_data/
        └── oficina_virtual/
            └── {numero_reclamo_cgs}/
                ├── pqr_detail.pdf
                ├── pqr_data.json
                └── adjunto_{timestamp}.{ext}
```

**Para Aire:**
```
Central_De_Escritos/
└── Air-e/
    └── 01_raw_data/
        └── oficina_virtual/
            └── {numero_reclamo_cgs}/
                ├── pqr_detail.pdf
                ├── pqr_data.json
                └── adjunto_{timestamp}.{ext}
```

#### **4.3 Gestor de Carga S3**
```python
# src/services/s3_upload_manager.py
```

**Funcionalidades:**
- ✅ Upload paralelo con pool de workers
- ✅ Verificación de integridad (MD5/SHA256)
- ✅ Manejo de archivos grandes (multipart upload)
- ✅ Metadata personalizada por archivo
- ✅ Logging detallado de cada upload
- ✅ Retry automático con backoff exponencial

### **Testing de Fase 4**
- ✅ Test de conectividad S3
- ✅ Test de upload de archivos individuales
- ✅ Test de upload masivo
- ✅ Validación de estructura de carpetas
- ✅ Test de integridad de archivos

---

## 📁 **FASE 5: SERVICIO DE CARGA DE ARCHIVOS**

### **Objetivo**
Implementar carga organizada y verificada de todos los archivos asociados a cada registro PQR.

### **Componentes a Desarrollar**

#### **5.1 Organizador de Archivos**
```python
# src/services/file_organizer_service.py
```

**Funcionalidades:**
- ✅ Asociación automática: JSON ↔ PDF ↔ adjuntos
- ✅ Verificación de integridad de archivos
- ✅ Generación de estructura de carpetas por numero_radicado
- ✅ Renombrado consistente de archivos
- ✅ Metadata extraction de PDFs y adjuntos

#### **5.2 Motor de Upload Empresarial**
```python
# src/services/enterprise_upload_service.py
```

**Proceso de Carga:**
1. ✅ **Pre-validación**: Verificar archivos existentes en local
2. ✅ **Organización**: Crear estructura de carpetas
3. ✅ **Upload secuencial**: JSON → PDF → adjuntos
4. ✅ **Verificación**: Confirmar integridad en S3
5. ✅ **Update BD**: Actualizar URLs S3 en registro de BD
6. ✅ **Cleanup**: Limpiar archivos locales (opcional)

#### **5.3 Verificador de Integridad**
```python
# src/services/integrity_checker_service.py
```

**Verificaciones:**
- ✅ Hash comparison local vs S3
- ✅ Tamaño de archivos
- ✅ Metadata consistency
- ✅ Accesibilidad de URLs
- ✅ Reportes de inconsistencias

### **Testing de Fase 5**
- ✅ Test de organización de archivos
- ✅ Test de upload completo por registro
- ✅ Test de verificación de integridad
- ✅ Test con registros que tienen/no tienen adjuntos
- ✅ Validación de URLs generadas

---

## 🔄 **FASE 6: SISTEMA DE MONITOREO INCREMENTAL**

### **Objetivo**
Implementar detección y procesamiento de registros nuevos, evitando duplicados y optimizando recursos.

### **Componentes a Desarrollar**

#### **6.1 Detector de Cambios**
```python
# src/services/change_detector_service.py
```

**Funcionalidades:**
- ✅ Comparación de timestamps de archivos
- ✅ Detección de nuevos archivos JSON
- ✅ Identificación de registros modificados
- ✅ Cache inteligente de estados anteriores
- ✅ Algoritmos de diferencias eficientes

#### **6.2 Procesador Incremental**
```python
# src/services/incremental_processor.py
```

**Proceso Incremental:**
1. ✅ **Escaneo**: Detectar archivos nuevos/modificados
2. ✅ **Extracción**: Procesar solo registros nuevos
3. ✅ **Verificación**: Comparar con BD para evitar duplicados
4. ✅ **Carga**: Procesar solo registros únicos
5. ✅ **Sincronización**: Actualizar cache y estados

#### **6.3 Optimizador de Recursos**
```python
# src/services/resource_optimizer.py
```

**Optimizaciones:**
- ✅ Procesamiento paralelo de registros independientes
- ✅ Cache de conexiones BD y S3
- ✅ Compresión de archivos antes de upload
- ✅ Limpieza automática de archivos procesados
- ✅ Gestión inteligente de memoria

### **Testing de Fase 6**
- ✅ Test de detección de cambios
- ✅ Test de procesamiento incremental
- ✅ Test de evitar duplicados
- ✅ Test de performance con actualizaciones menores
- ✅ Validación de optimizaciones

---

## ⏰ **FASE 7: AUTOMATIZACIÓN Y SCHEDULING**

### **Objetivo**
Implementar sistema de tareas programadas para operación automática Lunes-Sábado (5AM-10PM).

### **Componentes a Desarrollar**

#### **7.1 Scheduler Empresarial**
```python
# src/services/enterprise_scheduler.py
```

**Configuración de Horarios:**
- ✅ **Carga Masiva**: Lunes-Sábado 5:00 AM
- ✅ **Monitoreo Incremental**: Cada 2 horas (5AM-10PM)
- ✅ **Verificación de Integridad**: Diaria 11:30 PM
- ✅ **Limpieza y Mantenimiento**: Domingos 2:00 AM
- ✅ **Respaldo y Logs**: Diario 11:45 PM

#### **7.2 Motor de Tareas**
```python
# src/services/task_engine.py
```

**Funcionalidades:**
- ✅ Queue de tareas con prioridades
- ✅ Ejecución paralela controlada
- ✅ Monitoreo de recursos del sistema
- ✅ Alertas automáticas por email/Slack
- ✅ Recovery automático ante fallos

#### **7.3 Dashboard de Monitoreo**
```python
# src/dashboard/monitoring_dashboard.py
```

**Dashboard Web:**
- ✅ Estado en tiempo real de procesos
- ✅ Métricas de performance
- ✅ Logs de ejecución
- ✅ Configuración de alertas
- ✅ Reportes históricos

### **Testing de Fase 7**
- ✅ Test de scheduling y ejecución automática
- ✅ Test de recovery ante fallos
- ✅ Test de alertas y notificaciones
- ✅ Test de dashboard y monitoreo
- ✅ Test de carga completa end-to-end

---

## 🧪 **PLAN DE TESTING INTEGRAL**

### **Testing por Componente**
- ✅ **Tests Unitarios**: Cada servicio individualmente
- ✅ **Tests de Integración**: Conexiones BD/S3
- ✅ **Tests de Performance**: Volúmenes grandes
- ✅ **Tests de Stress**: Cargas extremas
- ✅ **Tests de Recovery**: Fallos y recuperación

### **Testing End-to-End**
- ✅ **Escenario 1**: Carga masiva inicial completa
- ✅ **Escenario 2**: Procesamiento incremental diario
- ✅ **Escenario 3**: Recovery ante fallos críticos
- ✅ **Escenario 4**: Verificación de integridad
- ✅ **Escenario 5**: Operación programada completa

### **Validación de Calidad**
- ✅ **Auditoría de Datos**: Consistencia BD vs archivos
- ✅ **Verificación S3**: Integridad de archivos
- ✅ **Performance Benchmarks**: Tiempos de respuesta
- ✅ **Monitoreo Continuo**: Alertas y métricas

---

## 📚 **DOCUMENTACIÓN Y OPERACIÓN**

### **Documentación Técnica**
- ✅ **API Documentation**: Servicios y métodos
- ✅ **Database Schema**: Estructura y relaciones
- ✅ **S3 Structure**: Organización de archivos
- ✅ **Configuration Guide**: Variables y parámetros
- ✅ **Troubleshooting Guide**: Problemas comunes

### **Guías Operacionales**
- ✅ **Manual de Operación**: Procedures diarias
- ✅ **Emergency Procedures**: Recovery ante fallos
- ✅ **Maintenance Guide**: Tareas de mantenimiento
- ✅ **Monitoring Guide**: Interpretación de métricas
- ✅ **Scaling Guide**: Aumentar capacidad

### **Training y Handover**
- ✅ **Training Sessions**: Para equipo técnico
- ✅ **Demo Environment**: Para pruebas seguras
- ✅ **Checklists**: Para operación diaria
- ✅ **Contact Information**: Soporte y escalamiento

---

## 🚀 **CRONOGRAMA DE IMPLEMENTACIÓN**

| Fase | Duración | Dependencias | Entregables |
|------|----------|-------------|-------------|
| **Fase 1**: Procesamiento JSON | 3 días | Análisis actual | Consolidador + Tests |
| **Fase 2**: Configuración RDS | 2 días | Credenciales BD | Conexión + Modelos |
| **Fase 3**: Carga Masiva BD | 3 días | Fase 1+2 | Loader + Control Duplicados |
| **Fase 4**: Configuración S3 | 2 días | Credenciales AWS | Config + Tests |
| **Fase 5**: Carga Archivos | 3 días | Fase 4 | Upload Manager + Verificador |
| **Fase 6**: Monitoreo Incremental | 2 días | Fase 1-5 | Detector + Procesador |
| **Fase 7**: Automatización | 2 días | Todas las fases | Scheduler + Dashboard |
| **Testing Integral** | 2 días | Fase 7 | Tests E2E + Validación |
| **Documentación** | 1 día | Testing | Docs + Training |

**Total: ~18 días de desarrollo** + testing + documentación

---

## 🎯 **CRITERIOS DE ÉXITO**

### **Funcionales**
- ✅ Procesamiento de 100% de archivos JSON sin errores
- ✅ 0% de duplicados en base de datos
- ✅ 100% de archivos cargados a S3 con integridad verificada
- ✅ Detección y procesamiento de registros nuevos <15 minutos
- ✅ Operación automática sin intervención manual

### **No Funcionales**
- ✅ **Performance**: >1000 registros/minuto
- ✅ **Disponibilidad**: 99.5% uptime durante horarios operacionales
- ✅ **Recovery**: <5 minutos para recuperación automática
- ✅ **Escalabilidad**: Soportar 10x volumen actual
- ✅ **Monitoreo**: Alertas automáticas ante cualquier fallo

### **Empresariales**
- ✅ **Auditoría**: Log completo de todas las operaciones
- ✅ **Compliance**: Cumplimiento de políticas de datos
- ✅ **Seguridad**: Encriptación y acceso controlado
- ✅ **Mantenibilidad**: Documentación y código limpio
- ✅ **Escalabilidad**: Arquitectura preparada para crecimiento

---

**Desarrollado por**: ISES | Analyst Data Jeam Paul Arcon Solano  
**Fecha**: Octubre 2025  
**Versión**: 1.0 - Plan Maestro