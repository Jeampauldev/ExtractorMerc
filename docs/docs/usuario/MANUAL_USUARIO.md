# Manual del Usuario - ExtractorOV Modular

## Introducción

Este manual está dirigido a usuarios finales que operan el sistema ExtractorOV Modular para extraer datos de PQRs (Peticiones, Quejas y Reclamos) desde las plataformas de Oficina Virtual de Afinia y Aire.

## Descripción del Sistema

ExtractorOV Modular es una herramienta automatizada que permite:

- **Extraer datos de PQRs** desde las plataformas oficiales de Afinia y Aire
- **Descargar adjuntos** de documentos de prueba automáticamente
- **Aplicar filtros** por fecha, estado y otros criterios
- **Generar reportes** en múltiples formatos (Excel, CSV, PDF)
- **Almacenar datos** de forma segura y organizada

## Requisitos Previos

### Credenciales Necesarias
- **Usuario y contraseña** para Oficina Virtual de Afinia
- **Usuario y contraseña** para Oficina Virtual de Aire
- **Permisos de acceso** a las secciones de PQRs en ambas plataformas

### Acceso al Sistema
- **Conexión a internet** estable
- **Acceso al servidor** donde está instalado el sistema
- **Permisos de ejecución** para los scripts del sistema

## Primeros Pasos

### Verificar Instalación

Antes de usar el sistema, verificar que esté correctamente instalado:

```bash
# En Windows (PowerShell)
python afinia_manager.py --help

# En Linux/Ubuntu
./venv/bin/python afinia_manager.py --help
```

### Verificar Configuración

Comprobar que las credenciales estén configuradas:

```bash
# Ejecutar verificación de configuración
python scripts/validate_environment.py

# Debe mostrar:
# ✓ Credenciales de Afinia configuradas
# ✓ Credenciales de Aire configuradas
# ✓ Configuración del sistema válida
```

## Uso Básico del Sistema

### Extracción de Datos de Afinia

#### Ejecución Estándar

```bash
# Extracción con configuración por defecto
python afinia_manager.py --headless

# El sistema extraerá:
# - PQRs del último día
# - Solo PQRs en estado "Finalizado"
# - Descargará adjuntos automáticamente
```

#### Ejecución con Parámetros Personalizados

```bash
# Extraer PQRs de los últimos 7 días
python afinia_manager.py --headless --days-back 7

# Extraer PQRs con estado específico
python afinia_manager.py --headless --state "En Proceso"

# Extraer con límite de registros
python afinia_manager.py --headless --max-records 100

# Extraer con rango de fechas específico
python afinia_manager.py --headless --start-date "01/10/2025" --end-date "07/10/2025"
```

#### Ejecución en Modo Visual (Para Depuración)

```bash
# Ver el proceso en navegador visible
python afinia_manager.py --visual

# Útil para:
# - Verificar problemas de login
# - Observar el proceso de extracción
# - Depurar filtros o navegación
```

### Extracción de Datos de Aire

#### Comandos Básicos

```bash
# Extracción estándar de Aire
python aire_manager.py --headless

# Extracción con parámetros personalizados
python aire_manager.py --headless --days-back 3 --max-records 50

# Extracción en modo visual
python aire_manager.py --visual
```

### Parámetros Disponibles

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--headless` | Ejecutar sin mostrar navegador | `--headless` |
| `--visual` | Mostrar navegador durante ejecución | `--visual` |
| `--days-back N` | Extraer PQRs de los últimos N días | `--days-back 7` |
| `--start-date` | Fecha de inicio (formato DD/MM/YYYY) | `--start-date "01/10/2025"` |
| `--end-date` | Fecha de fin (formato DD/MM/YYYY) | `--end-date "07/10/2025"` |
| `--state` | Estado de PQRs a filtrar | `--state "Finalizado"` |
| `--max-records N` | Límite máximo de registros | `--max-records 100` |
| `--test-mode` | Ejecutar en modo de prueba | `--test-mode` |
| `--help` | Mostrar ayuda completa | `--help` |

## Interpretación de Resultados

### Estructura de Salida

Al finalizar la extracción, el sistema genera:

```
data/
├── downloads/
│   ├── afinia/
│   │   ├── 2025-10-10/          # Datos por fecha
│   │   │   ├── pqrs_data.xlsx   # Datos principales
│   │   │   ├── pqrs_data.csv    # Datos en CSV
│   │   │   └── attachments/     # Adjuntos descargados
│   │   └── reports/             # Reportes generados
│   └── aire/
│       └── [estructura similar]
└── logs/
    └── current/                 # Logs de ejecución
```

### Archivos Generados

#### Archivo Principal de Datos
- **Nombre**: `pqrs_data.xlsx` o `pqrs_data.csv`
- **Contenido**: Todos los datos extraídos de PQRs
- **Columnas típicas**:
  - Número de PQR
  - Fecha de creación
  - Estado actual
  - Tipo de solicitud
  - Descripción
  - Cliente
  - Adjuntos disponibles

#### Carpeta de Adjuntos
- **Ubicación**: `attachments/` dentro de cada carpeta de fecha
- **Contenido**: Documentos PDF, imágenes y otros archivos
- **Nomenclatura**: `{numero_pqr}_{tipo_documento}_{timestamp}.{extension}`

#### Reporte de Ejecución
- **Nombre**: `extraction_report.pdf`
- **Contenido**:
  - Resumen de extracción
  - Estadísticas de registros procesados
  - Errores encontrados
  - Tiempo total de ejecución

### Mensajes de Salida del Sistema

#### Mensajes de Éxito
```
[2025-10-10_06:00:00][afinia][manager][main][INFO] - Iniciando extractor Afinia
[2025-10-10_06:00:15][afinia][manager][auth][INFO] - Autenticación exitosa
[2025-10-10_06:00:30][afinia][manager][filter][INFO] - Filtros aplicados: últimos 1 días
[2025-10-10_06:02:00][afinia][manager][pagination][INFO] - Procesando página 1 de 3
[2025-10-10_06:03:45][afinia][manager][download][INFO] - Descargados 25 adjuntos
[2025-10-10_06:04:00][afinia][manager][main][INFO] - Extracción completada: 45 registros procesados
```

#### Mensajes de Advertencia
```
[2025-10-10_06:01:30][afinia][manager][download][WARNING] - Adjunto no disponible para PQR 12345
[2025-10-10_06:02:15][afinia][manager][filter][WARNING] - No se encontraron PQRs en la fecha especificada
```

#### Mensajes de Error
```
[2025-10-10_06:00:05][afinia][manager][auth][ERROR] - Fallo en autenticación: credenciales inválidas
[2025-10-10_06:01:00][afinia][manager][network][ERROR] - Timeout de página: servidor no responde
[2025-10-10_06:02:30][afinia][manager][database][ERROR] - Error al guardar datos: conexión perdida
```

## Casos de Uso Comunes

### Extracción Diaria de Rutina

```bash
# Crear script de extracción diaria
#!/bin/bash
# daily_extraction.sh

echo "Iniciando extracción diaria $(date)"

# Extraer PQRs de Afinia del día anterior
python afinia_manager.py --headless --days-back 1

# Extraer PQRs de Aire del día anterior
python aire_manager.py --headless --days-back 1

echo "Extracción diaria completada $(date)"
```

### Extracción de Rango de Fechas Específico

```bash
# Para extraer datos de una semana específica
python afinia_manager.py --headless \
  --start-date "01/10/2025" \
  --end-date "07/10/2025" \
  --state "Finalizado"
```

### Extracción de Recuperación (Datos Faltantes)

```bash
# Extraer datos con límite alto para recuperar información perdida
python afinia_manager.py --headless \
  --days-back 30 \
  --max-records 5000 \
  --state "Finalizado"
```

### Verificación de Sistema

```bash
# Test rápido con pocos registros para verificar funcionamiento
python afinia_manager.py --visual \
  --test-mode \
  --max-records 5
```

## Solución de Problemas Comunes

### Problema: Error de Autenticación

**Síntomas:**
```
[ERROR] Fallo en autenticación: credenciales inválidas
```

**Soluciones:**
1. Verificar credenciales en el archivo de configuración
2. Confirmar que las credenciales son correctas en la plataforma web
3. Verificar que la cuenta no esté bloqueada
4. Ejecutar en modo visual para observar el proceso de login

**Comandos de verificación:**
```bash
# Verificar configuración
python scripts/validate_environment.py

# Test en modo visual
python afinia_manager.py --visual --test-mode
```

### Problema: Timeout de Navegación

**Síntomas:**
```
[ERROR] Timeout de página: servidor no responde
```

**Soluciones:**
1. Verificar conexión a internet
2. Aumentar timeouts en configuración
3. Reintentar la extracción
4. Verificar estado de la plataforma web

**Comandos de solución:**
```bash
# Ejecutar con timeouts extendidos
# Editar config/env/.env:
# PAGE_TIMEOUT=60000
# NAVIGATION_TIMEOUT=120000

# Reintentar extracción
python afinia_manager.py --headless --max-records 10
```

### Problema: No Se Encuentran PQRs

**Síntomas:**
```
[WARNING] No se encontraron PQRs en la fecha especificada
```

**Soluciones:**
1. Verificar rango de fechas
2. Cambiar filtros de estado
3. Ampliar período de búsqueda
4. Verificar que existan PQRs en la plataforma

**Comandos de solución:**
```bash
# Ampliar búsqueda
python afinia_manager.py --headless --days-back 7

# Cambiar filtro de estado
python afinia_manager.py --headless --state "Todos"

# Verificar en modo visual
python afinia_manager.py --visual --days-back 3
```

### Problema: Errores de Descarga de Adjuntos

**Síntomas:**
```
[WARNING] Adjunto no disponible para PQR 12345
```

**Soluciones:**
1. Verificar espacio en disco
2. Comprobar permisos de escritura
3. Verificar conectividad de red
4. Reintentar solo la descarga de adjuntos

### Problema: Sistema Lento

**Síntomas:**
- Ejecución muy lenta
- Timeouts frecuentes
- Alto uso de memoria

**Soluciones:**
```bash
# Reducir carga concurrente
# Editar config/env/.env:
# MAX_CONCURRENT_DOWNLOADS=1
# MAX_CONCURRENT_EXTRACTIONS=1

# Ejecutar con límites
python afinia_manager.py --headless --max-records 50

# Verificar recursos del sistema
htop  # En Linux
taskmgr  # En Windows
```

## Mantenimiento y Monitoreo

### Limpieza de Archivos

```bash
# Limpiar logs antiguos (ejecutar semanalmente)
python scripts/cleanup_logs.py --older-than 30

# Limpiar archivos temporales
python scripts/cleanup_temp.py

# Limpiar descargas antiguas (opcional)
python scripts/cleanup_downloads.py --older-than 90
```

### Verificación de Estado

```bash
# Verificar estado general del sistema
python scripts/system_health_check.py

# Verificar conectividad de servicios
python scripts/connectivity_check.py

# Verificar integridad de datos
python scripts/data_integrity_check.py
```

### Monitoreo de Logs

```bash
# Ver logs en tiempo real (Linux)
tail -f data/logs/current/afinia_manager.log

# Ver logs en tiempo real (Windows)
Get-Content -Path "data\logs\current\afinia_manager.log" -Wait

# Buscar errores en logs
grep -i error data/logs/current/*.log

# Contar registros procesados hoy
grep -c "registros procesados" data/logs/current/*.log
```

## Programación de Extracciones Automáticas

### Usando Cron (Linux)

```bash
# Editar crontab
crontab -e

# Agregar extracciones automáticas
# Afinia todos los días a las 6:00 AM
0 6 * * * cd /ruta/al/proyecto && ./venv/bin/python afinia_manager.py --headless >> /var/log/extractorov/cron.log 2>&1

# Aire todos los días a las 6:30 AM
30 6 * * * cd /ruta/al/proyecto && ./venv/bin/python aire_manager.py --headless >> /var/log/extractorov/cron.log 2>&1

# Limpieza semanal los domingos a las 2:00 AM
0 2 * * 0 cd /ruta/al/proyecto && ./scripts/cleanup_logs.sh >> /var/log/extractorov/maintenance.log 2>&1
```

### Usando Task Scheduler (Windows)

1. Abrir **Task Scheduler**
2. Crear **Basic Task**
3. Configurar:
   - **Name**: "Extracción Diaria Afinia"
   - **Trigger**: Daily
   - **Time**: 06:00
   - **Action**: Start a program
   - **Program**: `python`
   - **Arguments**: `afinia_manager.py --headless`
   - **Start in**: `C:\ruta\al\proyecto`

## Mejores Prácticas

### Para Uso Diario

1. **Ejecutar extracciones** en horarios de bajo tráfico (madrugada)
2. **Verificar logs** diariamente para identificar problemas
3. **Realizar backup** de datos importantes periódicamente
4. **Monitorear espacio** en disco para descargas

### Para Uso Seguro

1. **No compartir credenciales** del sistema
2. **Usar modo headless** en producción
3. **Verificar resultados** antes de procesar datos
4. **Mantener logs** para auditoría

### Para Rendimiento Óptimo

1. **Ejecutar en servidor dedicado** cuando sea posible
2. **Limitar registros** en extracciones de prueba
3. **Usar filtros específicos** para reducir carga
4. **Programar mantenimiento** regular del sistema

## Soporte y Contacto

### Recursos de Autoayuda

1. **Logs del sistema**: `data/logs/current/`
2. **Documentación técnica**: `docs/`
3. **Scripts de diagnóstico**: `scripts/`

### Información para Soporte Técnico

Al contactar soporte, proporcionar:

1. **Comando ejecutado** exacto
2. **Mensajes de error** completos de los logs
3. **Fecha y hora** del problema
4. **Configuración del sistema** (sin credenciales)
5. **Pasos para reproducir** el problema

### Comandos para Recolectar Información de Diagnóstico

```bash
# Generar reporte completo de estado
python scripts/generate_support_report.py

# El reporte incluirá:
# - Versión del sistema
# - Configuración sanitizada
# - Logs recientes
# - Estado de servicios
# - Métricas de rendimiento
```

---

**Manual del Usuario - ExtractorOV Modular**
*Versión: 2.0*
*Última actualización: Octubre 2025*