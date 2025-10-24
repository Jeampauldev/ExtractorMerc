# Procesador de Datos Afinia

Sistema de validación y carga de datos JSON extraídos del sistema de oficina virtual de Afinia hacia una base de datos RDS de AWS.

## Descripción

Este módulo procesa los archivos JSON generados por el extractor `oficina_virtual_afinia_extractor_new.py`, valida su integridad y los carga en una base de datos MySQL en AWS RDS. El sistema está diseñado para ser robusto, escalable y proporcionar métricas detalladas del procesamiento.

## Estructura del Proyecto

```
processors/afinia/
├── __init__.py              # Inicialización del módulo
├── config.py                # Configuración de BD y procesamiento
├── database_manager.py      # Gestión de conexiones y operaciones BD
├── models.py                # Modelos de datos y estructuras
├── validators.py            # Validadores de JSON e integridad
├── data_processor.py        # Procesador principal de datos
├── logger.py                # Sistema de logging y métricas
├── main.py                  # Script principal CLI
├── requirements.txt         # Dependencias Python
└── README.md               # Esta documentación
```

## Instalación

1. **Instalar dependencias:**
   ```bash
   pip install -r processors/afinia/requirements.txt
   ```

2. **Verificar configuración:**
   - Revisar credenciales RDS en `config.py`
   - Ajustar rutas de archivos según necesidad

## Uso

### Línea de Comandos

El procesador incluye una interfaz CLI completa:

```bash
# Procesar todos los archivos JSON en un directorio
python -m processors.afinia.main process -d "C:\path\to\json\files"

# Procesar un archivo específico
python -m processors.afinia.main process -f "C:\path\to\file.json"

# Validar archivos sin procesarlos
python -m processors.afinia.main validate -d "C:\path\to\json\files"

# Obtener estadísticas del procesador
python -m processors.afinia.main stats

# Probar conexión a base de datos
python -m processors.afinia.main test-connection

# Limpiar registros duplicados
python -m processors.afinia.main cleanup-duplicates

# Procesar solo archivos nuevos
python -m processors.afinia.main process -d "C:\path\to\json\files" --new-only
```

### Uso Programático

```python
from processors.afinia import AfiniaDataProcessor, validate_afinia_data

# Crear procesador
processor = AfiniaDataProcessor()

# Procesar directorio completo
result = processor.process_directory("C:/path/to/json/files")
print(f"Procesados: {result.total_archivos} archivos")
print(f"Tasa de éxito: {result.tasa_exito_global:.2f}%")

# Procesar archivo individual
file_result = processor.process_json_file("C:/path/to/file.json")

# Solo validar archivos
validation_results = validate_afinia_data("C:/path/to/json/files")

# Cerrar conexiones
processor.close()
```

## Configuración

### Base de Datos RDS

La configuración de la base de datos se encuentra en `config.py`:

```python
'database': {
    'host': os.getenv('DB_HOST', 'your-rds-endpoint.rds.amazonaws.com'),
    'database': os.getenv('DB_NAME', 'your-database'),
    'user': os.getenv('DB_USER', 'your-username'),
    'password': os.getenv('DB_PASSWORD'),  # ⚠️ USAR VARIABLES DE ENTORNO
    'port': int(os.getenv('DB_PORT', '3306')),
    'charset': 'utf8mb4'
}
```

**⚠️ IMPORTANTE:** Las credenciales deben configurarse en variables de entorno:
```bash
# En .env o variables de sistema
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_NAME=your-database
DB_USER=your-username
DB_PASSWORD=your-secure-password
DB_PORT=3306
```

### Esquema de Tabla

El sistema crea automáticamente la tabla `afinia_pqr` con la siguiente estructura:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INT AUTO_INCREMENT | Clave primaria |
| nic | VARCHAR(50) | Número de identificación del cliente |
| fecha | VARCHAR(20) | Fecha de la PQR |
| documento_identidad | VARCHAR(20) | Documento de identidad |
| nombres_apellidos | VARCHAR(200) | Nombres y apellidos |
| correo_electronico | VARCHAR(100) | Email del cliente |
| telefono | VARCHAR(20) | Teléfono |
| celular | VARCHAR(20) | Celular |
| tipo_pqr | VARCHAR(50) | Tipo de PQR |
| canal_respuesta | VARCHAR(50) | Canal de respuesta |
| numero_radicado | VARCHAR(50) | Número de radicado |
| estado_solicitud | VARCHAR(50) | Estado de la solicitud |
| lectura | TEXT | Lectura del medidor |
| documento_prueba | TEXT | Documento de prueba |
| cuerpo_reclamacion | TEXT | Cuerpo de la reclamación |
| finalizar | VARCHAR(10) | Campo finalizar |
| adjuntar_archivo | TEXT | Archivos adjuntos |
| numero_reclamo_sgc | VARCHAR(50) | Número de reclamo SGC |
| comentarios | TEXT | Comentarios adicionales |
| fecha_procesamiento | DATETIME | Fecha de procesamiento |
| archivo_origen | VARCHAR(255) | Archivo de origen |
| hash_registro | VARCHAR(32) | Hash único del registro |

## Validaciones

El sistema implementa múltiples niveles de validación:

### Validación de Estructura JSON
- Verificación de campos requeridos
- Validación de tipos de datos
- Estructura JSON válida

### Validación de Contenido
- **NIC**: Formato alfanumérico 5-20 caracteres
- **Email**: Formato de email válido
- **Teléfonos**: Formato numérico con separadores
- **Documento**: Solo números, 6-15 dígitos
- **Fecha**: Formatos DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
- **Tipos PQR**: Valores válidos (Petición, Queja, Reclamo, etc.)

### Validación de Duplicados
- Hash MD5 basado en campos clave (NIC, documento, radicado, fecha)
- Detección automática de registros duplicados
- Funcionalidad de limpieza de duplicados

## Logging y Métricas

### Sistema de Logging
- Logs estructurados con timestamps
- Múltiples niveles: DEBUG, INFO, WARNING, ERROR
- Archivos de log rotativos por día
- Logging tanto a consola como archivo

### Métricas Recolectadas
- **Contadores**: Archivos procesados, validaciones exitosas/fallidas
- **Timers**: Tiempo de procesamiento, operaciones BD
- **Gauges**: Tasas de éxito, rendimiento

### Reportes de Rendimiento
```python
# Generar reporte de las últimas 24 horas
processor = AfiniaDataProcessor()
report = processor.logger.get_performance_report(hours=24)

# Exportar reporte a archivo
processor.logger.export_performance_report("reporte_rendimiento.json")
```

## Manejo de Errores

### Errores de Validación
- Campos faltantes o inválidos
- Formatos incorrectos
- Tipos de datos incorrectos

### Errores de Base de Datos
- Conexión fallida
- Errores de inserción
- Problemas de esquema

### Recuperación de Errores
- Reintentos automáticos para operaciones BD
- Continuación del procesamiento ante errores individuales
- Logging detallado de todos los errores

## Monitoreo

### Estadísticas en Tiempo Real
```python
processor = AfiniaDataProcessor()
stats = processor.get_processing_stats()
print(f"Tasa de éxito: {stats['success_rate']:.2f}%")
```

### Verificación de Salud del Sistema
```bash
# Probar conexión BD
python -m processors.afinia.main test-connection

# Obtener estadísticas generales
python -m processors.afinia.main stats --output stats_report.json
```

## Ejemplos de Uso Avanzado

### Procesamiento con Configuración Personalizada
```python
custom_config = {
    'processing': {
        'batch_size': 50,
        'max_retries': 5
    },
    'database': {
        'host': 'mi-servidor-personalizado.com'
    }
}

processor = AfiniaDataProcessor(custom_config)
```

### Validación Masiva con Reporte
```python
from processors.afinia.validators import BatchValidator

validator = BatchValidator()
results = validator.validate_directory("C:/json/files")
summary = validator.get_validation_summary(results)
print(summary)
```

### Procesamiento con Métricas Personalizadas
```python
from processors.afinia.logger import get_logger, timer

logger = get_logger()

@timer('custom_processing')
def mi_procesamiento_personalizado():
    # Tu código aquí
    logger.info("Procesamiento personalizado completado")
```

## Solución de Problemas

### Problemas Comunes

1. **Error de conexión a BD**
   - Verificar credenciales en `config.py`
   - Comprobar conectividad de red
   - Validar permisos de usuario BD

2. **Archivos JSON inválidos**
   - Usar comando `validate` para identificar problemas
   - Revisar formato y estructura JSON
   - Verificar encoding de archivos (UTF-8)

3. **Rendimiento lento**
   - Ajustar `batch_size` en configuración
   - Verificar índices de BD
   - Monitorear métricas de rendimiento

### Logs de Depuración
```bash
# Ejecutar con logging detallado
python -m processors.afinia.main process -d "C:/path" --log-level DEBUG
```

## Contribución

Para contribuir al desarrollo:

1. Seguir las convenciones de código existentes
2. Agregar tests para nuevas funcionalidades
3. Actualizar documentación según cambios
4. Usar el sistema de logging para nuevas funciones

## Licencia

Este proyecto es parte del sistema de extracción de datos de oficinas virtuales.