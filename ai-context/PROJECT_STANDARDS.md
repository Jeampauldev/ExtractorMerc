# Estándares del Proyecto ExtractorMERC

## 🤖 Información para Agentes IA y Desarrolladores

Este documento establece los estándares profesionales que deben seguirse al trabajar con este proyecto.

---

## Créditos y Autoría

**Desarrollado por: ISES | Analyst Data Jeam Paul Arcon Solano**

Este proyecto ha sido desarrollado con estándares profesionales empresariales, eliminando cualquier rastro de automatización o uso de herramientas de IA en el código final.

---

## Estándares de Código Profesional

### 1. Logging Sin Emojis

**FORMATO OBLIGATORIO:**
```log
[YYYY-MM-DD_HH:MM:SS][mercurio][flujo][componente][LEVEL] - mensaje
``` 

**EJEMPLOS CORRECTOS:**
```
[2025-10-08_14:30:15][afinia][pagination][manager][INFO] - Procesando página 5 de 12
[2025-10-08_14:30:16][afinia][download][handler][EXITOSO] - Archivo descargado correctamente
[2025-10-08_14:30:17][afinia][filter][validator][ADVERTENCIA] - Filtro de fecha no especificado
[2025-10-08_14:30:18][afinia][session][manager][ERROR] - Fallo en conexión con servidor
```

**ELEMENTOS PROHIBIDOS:**
- Emojis de cualquier tipo (🚀, ✅, ❌, ⚠️, etc.)
- Elementos visuales no profesionales
- Referencias a IA o automatización
- Comentarios casuales o informales

### 2. Reemplazos de Emojis Estándar

Cuando encuentres emojis, utilizar estos reemplazos profesionales:

| Emoji | Reemplazo Profesional |
|-------|----------------------|
| 🚀 | INICIANDO |
| ✅ | EXITOSO |
| ❌ | ERROR |
| ⚠️ | ADVERTENCIA |
| 🔍 | VERIFICANDO |
| 📅 | FECHA |
| 📁 | ARCHIVOS |
| 📊 | PROCESADOS |
| 📈 | METRICAS |
| 📥 | DESCARGANDO |
| 💾 | GUARDANDO |
| ⏱️ | DURACION |
| ⏳ | ESPERANDO |
| 🏁 | COMPLETADO |
| 🎉 | PROCESO_COMPLETADO |
| 🧹 | LIMPIEZA |
| 🧪 | MODO_TEST |
| 🎯 | OBJETIVO |
| 🔄 | REANUDANDO |
| 📋 | LISTA |

### 3. Documentación Profesional

**COMENTARIOS EN CÓDIGO:**
```python
# Correcto - Profesional
def process_pqr_data(self, data: dict) -> ProcessResult:
    """
    Procesa los datos de PQR extraídos del sistema.
    
    Args:
        data: Diccionario con datos de PQR validados
        
    Returns:
        ProcessResult: Resultado del procesamiento con métricas
    """
    pass

# Incorrecto - Casual/IA
def process_pqr_data(self, data: dict):
    # Esta función procesa los datos como me indicaste
    # Aquí va la lógica que generé automáticamente
    pass
```

### 4. Nombres de Variables y Funciones

**ESTILO PROFESIONAL:**
```python
# Correcto
def validate_extraction_parameters(self, params: dict) -> ValidationResult:
    extraction_start_time = datetime.now()
    processed_records_count = 0
    error_handling_strategy = "continue_on_error"

# Incorrecto  
def do_stuff(self, params):
    start = datetime.now()
    count = 0
    strategy = "keep_going"
```

---

## Arquitectura del Sistema

### Principios Fundamentales

1. **Modularidad**: Cada componente tiene una responsabilidad específica
2. **Separación de Concerns**: Lógica de negocio separada de presentación
3. **Configurabilidad**: Sistema adaptable a diferentes entornos
4. **Observabilidad**: Logging y métricas en todos los niveles

### Estructura de Directorios Críticos

```
ExtractorOV_Modular/
├── src/                    # Código fuente principal
│   ├── components/         # Componentes reutilizables
│   ├── extractors/         # Extractores específicos por plataforma
│   ├── services/           # Servicios de datos (RDS, S3)
│   └── config/             # Configuración centralizada
├── ai-context/             # ⭐ Esta carpeta - Info para IAs
├── scripts/                # Scripts de utilidad y limpieza
└── data/                   # Datos generados y logs
```

### Componentes Críticos NO Tocar Sin Aprobación

1. **afinia_manager.py** - Manager principal de Afinia
2. **aire_manager.py** - Manager principal de Aire  
3. **src/services/database_service.py** - Servicio de base de datos
4. **src/config/unified_logging_config.py** - Sistema de logging

---

## Flujo de Trabajo para IAs

### Antes de Hacer Cambios

1. **Revisar este documento** para entender estándares
2. **Ejecutar script de verificación**:
   ```bash
   python scripts/verify_functionality.py
   ```
3. **Hacer backup** de archivos que vas a modificar
4. **Aplicar cambios gradualmente** - nunca masivos

### Después de Hacer Cambios

1. **Ejecutar limpieza de emojis**:
   ```bash
   python scripts/clean_emojis_professional.py --test-all
   ```
2. **Verificar funcionalidad**:
   ```bash
   python -c "from afinia_manager import AfiniaManager; print('Funcionalidad OK')"
   ```
3. **Revisar logs** para asegurar formato correcto
4. **Documentar cambios** en este directorio

### Herramientas Disponibles

```bash
# Limpieza de emojis por categorías
python scripts/clean_emojis_professional.py --apply-critical     # Solo archivos críticos
python scripts/clean_emojis_professional.py --apply-components  # Solo componentes
python scripts/clean_emojis_professional.py --apply-services    # Solo servicios
python scripts/clean_emojis_professional.py --apply-all         # Todo el proyecto

# Verificación de funcionalidad
python scripts/validate_functionality.py

# Verificación de estándares
python scripts/verify_logging_standards.py
```

---

## Casos de Uso del Sistema

### Objetivo Principal
Extracción automatizada de PQRs (Peticiones, Quejas y Reclamos) desde:
- **Oficina Virtual Afinia**: Portal web de la empresa eléctrica
- **Oficina Virtual Aire**: Portal web de la empresa de gas

### Flujo de Datos
1. **Autenticación** en portales web oficiales
2. **Aplicación de filtros** por fecha y estado
3. **Extracción de metadatos** de PQRs
4. **Descarga de adjuntos** (documentos de prueba)
5. **Almacenamiento** en base de datos RDS
6. **Backup** en S3 de AWS
7. **Generación de reportes** en múltiples formatos

### Tecnologías Clave
- **Playwright**: Automatización de navegadores
- **PostgreSQL**: Base de datos (RDS)
- **AWS S3**: Almacenamiento de archivos
- **Python 3.8+**: Lenguaje principal

---

## Mantenimiento y Evolución

### Principios de Cambios

1. **Cambios Incrementales**: Nunca modificar múltiples archivos críticos simultáneamente
2. **Testing Continuo**: Verificar funcionalidad después de cada cambio
3. **Logging Consistente**: Mantener formato profesional en todos los componentes
4. **Documentación Actualizada**: Mantener este archivo actualizado con cambios

### Archivos de Configuración Importante

1. **config/env/.env** - Variables de entorno y credenciales
2. **src/config/unified_logging_config.py** - Configuración de logging
3. **requirements.txt** - Dependencias Python
4. **ai-context/** - Esta carpeta con información para IAs

---

## Preguntas Frecuentes para IAs

### ¿Puedo modificar archivos críticos?
Sí, pero con extrema precaución. Hacer backup primero y verificar funcionalidad después.

### ¿Cómo mantengo el formato de logging profesional?
Usa el script `clean_emojis_professional.py` y sigue el formato establecido en este documento.

### ¿Qué hacer si algo se rompe?
1. Restaurar desde backup
2. Ejecutar `python scripts/validate_functionality.py`
3. Revisar logs en `data/logs/current/`
4. Contactar al desarrollador original si es necesario

### ¿Puedo agregar nuevas funcionalidades?
Sí, siguiendo la arquitectura modular existente y los estándares de este documento.

---

## Historial de Cambios

**2025-10-08**: 
- Implementación de sistema de logging profesional sin emojis
- Creación de scripts de limpieza automatizada
- Establecimiento de estándares de desarrollo profesional
- Limpieza de archivos críticos: afinia_manager.py, aire_manager.py
- Limpieza de componentes: handlers, processors, managers
- Limpieza de servicios: database, s3_uploader, data_loader

---

*Este documento debe mantenerse actualizado con cualquier cambio en los estándares del proyecto.*