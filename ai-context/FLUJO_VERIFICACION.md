Plan de Verificación del Flujo – Oficina Virtual (Afinia y Air-e)

Fuente de requerimiento: ai-context/flujos.yaml
Objetivo: crear un checklist operativo para verificar el flujo “Descarga → CSV → Carga RDS → Filtrar no duplicados → Subida S3”, identificando lo implementado y lo pendiente, con referencia a componentes (src/components) y núcleo (src/core).

Convenciones de estado
- [x] Implementado: funcional y presente en código
- [ ] Pendiente/Parcial: requiere ajuste, alineación o desarrollo adicional

Resumen de arquitectura por etapa (común)
- Descarga y navegación web: managers y extractores coordinan autenticación, filtros y paginación
- Consolidación CSV: JSONConsolidatorService genera `*_consolidated_<timestamp>.csv` y reportes
- Carga RDS: BulkDatabaseLoader ingiere CSV con deduplicación por hash y numero_radicado
- Selección de no duplicados: derivado del resultado RDS (insertados/actualizados)
- Subida S3: S3UploaderService organiza por empresa/tipo; registrar en `data_general.s3_files_registry`

Afinia – Checklist detallado por pasos
- [x] Paso 1: abrir la página de Afinia
  - Componentes: `src/components/afinia_download_manager.py`, `src/components/afinia_filter_manager.py`
  - Core: `src/core/browser_manager.py`, `src/core/base_extractor.py`
- [x] Paso 2: quitar el popup (solo Afinia)
  - Componentes: `src/components/afinia_popup_handler.py`
  - Core: `src/core/base_extractor.py` (hooks de flujo)
- [x] Paso 3: agregar usuario y contraseña
  - Componentes: `src/components/afinia_download_manager.py`
  - Core: `src/core/authentication.py`
- [x] Paso 4: click en ingresar
  - Componentes: `src/components/afinia_download_manager.py`
  - Core: `src/core/base_extractor.py`
- [x] Paso 5: ir a listados de PQR
  - Componentes: `src/components/afinia_pqr_processor.py`
  - Core: `src/core/base_extractor.py`
- [x] Paso 6: clic en el botón filtrar
  - Componentes: `src/components/afinia_filter_manager.py`, `src/components/filter_manager.py`
  - Core: `src/core/base_extractor.py`
- [x] Paso 7: estado = finalizado
  - Componentes: `src/components/afinia_filter_manager.py`, `src/components/filter_manager.py`
- [x] Paso 8: ingresar fecha inicial = ayer
  - Componentes: `src/components/date_configurator.py`
- [x] Paso 9: ingresar fecha final = hoy
  - Componentes: `src/components/date_configurator.py`
- [x] Paso 10: click en consultar
  - Componentes: `src/components/afinia_filter_manager.py`
- [x] Paso 11: presionar nuevamente el botón filtrar
  - Componentes: `src/components/afinia_filter_manager.py`
- [x] Paso 12: seleccionar el ojo inicial y abrir en nueva pestaña
  - Componentes: `src/components/pqr_detail_extractor.py`
- [x] Paso 13: imprimir ventana con Ctrl+P y guardar PDF (nombre = numero SGC + fecha)
  - Componentes: `src/components/report_processor.py`, `src/components/pqr_detail_extractor.py`
  - Observación: estandarizar convención de nombres con `numero_radicado` + fecha
- [x] Paso 14: guardar JSON completo (metadata)
  - Componentes: `src/components/afinia_pqr_processor.py`
  - Salidas: `data/downloads/afinia/oficina_virtual/processed/<radicado>/pqr_data.json`
- [x] Paso 15: descargar documento_prueba y adjuntos (.pdf/.jpg/.docx)
  - Componentes: `src/components/pqr_detail_extractor.py`, `src/core/download_manager.py`
- [x] Paso 16: cerrar la página y repetir en lote
  - Componentes: `src/components/afinia_download_manager.py`
  - Core: `src/utils/extractor_runner.py`
- [x] Paso 17: paginación a siguientes 10 registros
  - Componentes: `src/components/afinia_filter_manager.py`
  - Evidencia: `data/downloads/afinia/oficina_virtual/pagination_control/`
- [x] Paso 18: crear CSV de todos los JSON descargados
  - Servicios: `src/services/json_consolidator_service.py` → `afinia_consolidated_<timestamp>.csv`
- [x] Paso 19: cargar CSV a RDS (data_general.ov_afinia) solo nuevos
  - Servicios: `src/services/bulk_database_loader.py` (dedupe por hash y `numero_radicado`)
- [ ] Paso 20: verificar salida (nuevos/duplicados) contra `data_general.s3_files_registry`
  - Servicios: `src/services/aws_s3_service.py` (registro S3); `config/check_s3_status.py`
  - Acción: automatizar cruce post-carga CSV→RDS con tabla S3 para confirmar pendientes de subida
- [ ] Paso 21: cargar a bucket S3 en carpeta `afinia/01_raw_data/oficina_virtual/<numero_sgc>`
  - Servicios: `src/services/s3_uploader_service.py` (estructura actual: `afinia/oficina_virtual/{pdfs|data|screenshots}`)
  - Acción: alinear estructura S3 con requerimiento (`01_raw_data/...`) o documentar la diferencia y crear mapeo
- [ ] Paso 22: ejecución programada (L–S 4am–10pm; masivo 4am; verificación cada hora)
  - Ubuntu: `config/ubuntu_config/extractorov-afinia.service` (parcial)
  - Windows: pendiente (Task Scheduler)
  - Acción: crear orquestación multi-plataforma y ventanas horarias
- [ ] Paso 23: intercalar proceso de Air-e con Afinia (o paralelizar)
  - Managers: `afinia_manager.py`, `aire_manager.py`
  - Acción: orquestador que alterna o paraleliza con control de recursos

Air-e – Checklist paralelo por pasos
- [x] Paso 1: abrir la página de Air-e
  - Componentes: `src/components/aire_download_manager.py`, `src/components/aire_filter_manager.py`
  - Core: `src/core/browser_manager.py`, `src/core/base_extractor.py`
- [x] Paso 2: (no aplica popup Air-e)
- [x] Paso 3: agregar usuario y contraseña
  - Componentes: `src/components/aire_download_manager.py`
  - Core: `src/core/authentication.py`
- [x] Paso 4–11: navegación, filtros y consulta
  - Componentes: `src/components/aire_filter_manager.py`, `src/components/filter_manager.py`, `src/components/date_configurator.py`
- [x] Paso 12–16: abrir detalle, imprimir/guardar PDF, guardar JSON, iteración
  - Componentes: `src/components/aire_pqr_processor.py`, `src/components/pqr_detail_extractor.py`, `src/components/report_processor.py`
- [x] Paso 17: paginación
  - Componentes: `src/components/aire_filter_manager.py`
- [x] Paso 18: crear CSV
  - Servicios: `src/services/json_consolidator_service.py` → `aire_consolidated_<timestamp>.csv` (disponible si se habilita compañía)
- [x] Paso 19: cargar CSV a RDS (data_general.ov_aire) solo nuevos
  - Servicios: `src/services/bulk_database_loader.py` (soporte para Aire; revisar flag)
- [ ] Paso 20: verificación contra `data_general.s3_files_registry`
  - Servicios: `src/services/aws_s3_service.py`; `config/check_s3_status.py`
  - Acción: automatizar cruce post-carga
- [ ] Paso 21: cargar a S3 en carpeta `aire/01_raw_data/oficina_virtual/<numero_sgc>`
  - Servicios: `src/services/s3_uploader_service.py` (estructura actual: `aire/oficina_virtual/{pdfs|data|screenshots}`)
  - Acción: alinear estructura o documentar mapeo
- [ ] Paso 22: ejecución programada (L–S 4am–10pm)
  - Ubuntu: crear `.service` para Air-e (pendiente)
  - Windows: pendiente (Task Scheduler)
- [ ] Paso 23: intercalar con Afinia (orquestación)

Verificaciones adicionales y acciones concretas
- CSV consolidado
  - Comando: `python -c "from src.services.json_consolidator_service import consolidate_afinia_data; print(consolidate_afinia_data())"`
  - Salidas: `data/processed/afinia_consolidated_*.csv`, `*_processing_report_*.json`
- Carga RDS (Afinia)
  - Comando: `python -c "from src.services.bulk_database_loader import load_latest_consolidated_files; print(load_latest_consolidated_files())"`
  - Validaciones: contar insertados/actualizados y duplicados; consulta en BD por ventana temporal
- Selección de “no duplicados” para S3
  - Acción: derivar lista de `numero_radicado` a partir de insertados/actualizados en el último run
- Subida S3 (filtrada)
  - API: `S3UploaderService().upload_file(file_path, service_type='afinia', file_type='pdfs', custom_filename='radicado_hash_timestamp.pdf')`
  - Registro: validar `data_general.s3_files_registry` (estado `uploaded/pre_existing/error`)

Riesgos y notas
- Alineación de estructura S3: el requerimiento usa `01_raw_data/...`, el servicio actual usa `afinia/oficina_virtual/{pdfs|data|screenshots}`; decidir mapeo definitivo
- Bug conocido (nombres S3): `scripts/direct_json_to_rds_loader_with_files.py` usa `record_dir` no definido al crear `custom_filename`; corregir con `numero_radicado`
- Orquestación y programación: Ubuntu parcialmente implementado para Afinia; faltan tareas programadas Windows y coordinación con Air-e

Seguimiento y actualización
- Este archivo sirve como checklist para control operativo. Actualizar marcadores [x]/[ ] al completar acciones pendientes.
- Proponer PRs vinculando commits a pasos específicos (ej.: “Paso 21 – Alinear ruta S3”).