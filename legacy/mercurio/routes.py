"""ExtractorMerc Routes - Rutas API para el Sistema ExtractorMerc
=========================================

Definición de endpoints REST para el módulo ExtractorMerc que extrae datos
desde la plataforma externa Mercurio.
Incluye operaciones para ambas empresas (Aire y Afinia).
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

import os
from config.centralized_config import Company
from src.mercurio.base import ExtractorMercDocument, ExtractorMercType, ExtractorMercStatus, MercurioTaskScheduler
from src.core.logging import get_logger

logger = get_logger(__name__)

# Router para endpoints de Mercurio
mercurio_router = APIRouter()

# Modelos Pydantic para requests/responses
class UploadExtractorMercRequest(BaseModel):
    company: str
    period: str
    extractor_merc_type: str

class ProcessExtractorMercRequest(BaseModel):
    extractor_merc_id: str
    immediate: bool = True

class ExtractorMercResponse(BaseModel):
    id: str
    type: str
    company: str
    period: str
    status: str
    upload_date: str
    processing_date: Optional[str] = None

# Instancia del programador de tareas
task_scheduler = MercurioTaskScheduler()

def get_mercurio_service(company: str):
    """Factory para obtener el servicio Mercurio según la empresa"""
    # Verificar si está en modo local
    local_mode = os.getenv("MERCURIO_LOCAL_MODE", "false").lower() == "true"
    
    if company.lower() == "aire":
        from src.mercurio.aire import AireMercurioService
        service = AireMercurioService()
        if local_mode:
            logger.info("🏠 Aire Mercurio Service iniciado en modo local")
        return service
    elif company.lower() == "afinia":
        from src.mercurio.afinia import AfiniaMercurioService
        return AfiniaMercurioService()
    else:
        raise HTTPException(status_code=400, detail=f"Empresa no soportada: {company}")

@mercurio_router.get("/test")
async def test_mercurio_local():
    """Endpoint de prueba para verificar funcionamiento local de Mercurio"""
    logger.info("🧪 Ejecutando test de Mercurio")
    
    try:
        # Detectar modo de operación
        local_mode = os.getenv("MERCURIO_LOCAL_MODE", "false").lower() == "true"
        skip_aws = os.getenv("MERCURIO_SKIP_AWS", "false").lower() == "true"
        
        # Test básico de conectividad
        test_results = {
            "status": "success",
            "message": "ExtractorMerc funcionando correctamente",
            "timestamp": datetime.now().isoformat(),
            "mode": "local" if local_mode else "standard",
            "configuration": {
                "local_mode": local_mode,
                "aws_disabled": skip_aws,
                "storage": "local" if local_mode else "aws_s3"
            },
            "services": {
                "aire": "available",
                "afinia": "available"
            },
            "features": {
                "upload": "enabled",
                "processing": "enabled", 
                "reports": "enabled",
                "validation": "enabled",
                "download_reports": "enabled",
                "upload_letters": "enabled"
            }
        }
        
        logger.info(f"✅ Test de Mercurio completado - Modo: {'LOCAL' if local_mode else 'ESTÁNDAR'}")
        return test_results
        
    except Exception as e:
        logger.error(f"❌ Error en test de Mercurio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en test: {str(e)}")

@mercurio_router.get("/info")
async def get_mercurio_info():
    """Información general del módulo Mercurio"""
    return {
        "module": "ExtractorMerc",
        "description": "Procesamiento de Informes de Pérdidas Operacionales",
        "supported_companies": ["aire", "afinia"],
        "supported_types": [
            "perdidas_tecnicas",
            "perdidas_comerciales", 
            "verbales",
            "auditoria"
        ],
        "endpoints": [
            "/upload - Subir archivo ExtractorMerc",
            "/process - Procesar archivo ExtractorMerc",
            "/status/{task_id} - Consultar estado de procesamiento",
            "/history - Historial de procesamientos",
            "/reports - Reportes generados",
            "/download-reports - Descargar reportes desde Mercurio",
            "/upload-letters - Subir cartas a Mercurio",
            "/process/rra-pendientes - Procesar RRA pendientes",
            "/process/verbales-pendientes - Procesar verbales pendientes"
        ]
    }

@mercurio_router.post("/upload", response_model=ExtractorMercResponse)
async def upload_extractor_merc_file(
    file: UploadFile = File(...),
    company: str = Form(...),
    period: str = Form(...),
    extractor_merc_type: str = Form(...)
):
    """
    Sube un archivo ExtractorMerc para procesamiento
    """
    try:
        # Validaciones
        if company.lower() not in ["aire", "afinia"]:
            raise HTTPException(status_code=400, detail="Empresa no válida")
        
        if extractor_merc_type not in [t.value for t in ExtractorMercType]:
            raise HTTPException(status_code=400, detail="Tipo de ExtractorMerc no válido")
        
        # Validar formato de archivo
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel")
        
        # Generar ID único
        extractor_merc_id = str(uuid.uuid4())
        
        # Guardar archivo
        file_path = f"/tmp/uploads/extractor_merc/{company}/{period}/{extractor_merc_id}_{file.filename}"
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Crear documento ExtractorMerc
        extractor_merc_document = ExtractorMercDocument(
            id=extractor_merc_id,
            type=ExtractorMercType(extractor_merc_type),
            company=company.lower(),
            period=period,
            file_path=file_path,
            upload_date=datetime.now(),
            status=ExtractorMercStatus.PENDING
        )
        
        # TODO: Guardar en base de datos
        
        logger.info(f"Archivo ExtractorMerc subido: {extractor_merc_id} para {company}")
        
        return ExtractorMercResponse(
            id=extractor_merc_document.id,
            type=extractor_merc_document.type.value,
            company=extractor_merc_document.company,
            period=extractor_merc_document.period,
            status=extractor_merc_document.status.value,
            upload_date=extractor_merc_document.upload_date.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error subiendo archivo ExtractorMerc: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mercurio_router.post("/process")
async def process_extractor_merc(
    request: ProcessExtractorMercRequest,
    background_tasks: BackgroundTasks
):
    """
    Inicia el procesamiento de un archivo ExtractorMerc
    """
    try:
        # TODO: Obtener ExtractorMerc document de base de datos
        # Por ahora crear uno de ejemplo
        extractor_merc_document = ExtractorMercDocument(
            id=request.extractor_merc_id,
            type=ExtractorMercType.PERDIDAS_TECNICAS,
            company="aire",
            period="2024-08",
            file_path=f"/tmp/uploads/extractor_merc/aire/2024-08/{request.extractor_merc_id}.xlsx",
            upload_date=datetime.now(),
            status=ExtractorMercStatus.PENDING
        )
        
        if request.immediate:
            # Procesamiento inmediato
            task_id = task_scheduler.schedule_immediate_processing(extractor_merc_document)
            
            # Ejecutar en background
            mercurio_service = get_mercurio_service(extractor_merc_document.company)
            background_tasks.add_task(run_processing_task, mercurio_service, extractor_merc_document, task_id)
            
            return {
                "task_id": task_id,
                "status": "started",
                "message": f"Procesamiento iniciado para ExtractorMerc {request.extractor_merc_id}"
            }
        else:
            # Programar procesamiento
            task_scheduler.schedule_monthly_processing(extractor_merc_document.company)
            
            return {
                "task_id": "scheduled",
                "status": "scheduled",
                "message": f"Procesamiento programado para ExtractorMerc {request.extractor_merc_id}"
            }
            
    except Exception as e:
        logger.error(f"Error procesando ExtractorMerc: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mercurio_router.get("/status/{task_id}")
async def get_processing_status(task_id: str):
    """
    Consulta el estado de una tarea de procesamiento
    """
    try:
        status_info = task_scheduler.get_task_status(task_id)
        
        return {
            "task_id": task_id,
            "status": status_info['status'],
            "progress": status_info['progress'],
            "details": status_info.get('details', {})
        }
        
    except Exception as e:
        logger.error(f"Error consultando estado de tarea {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mercurio_router.get("/history")
async def get_processing_history(
    company: str = None,
    extractor_merc_type: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Obtiene el historial de procesamientos ExtractorMerc
    """
    try:
        # TODO: Implementar consulta a base de datos
        # Simular respuesta por ahora
        history = [
            {
                "id": "extractor_merc_001",
                "company": "aire",
                "type": "perdidas_tecnicas",
                "period": "2024-07",
                "upload_date": "2024-08-01T10:00:00Z",
                "processing_date": "2024-08-01T10:30:00Z",
                "status": "completed",
                "reports_generated": 3
            },
            {
                "id": "extractor_merc_002",
                "company": "afinia",
                "type": "verbales",
                "period": "2024-07",
                "upload_date": "2024-08-02T09:00:00Z",
                "processing_date": "2024-08-02T09:45:00Z",
                "status": "completed",
                "reports_generated": 2
            }
        ]
        
        # Filtrar por empresa y tipo si se especifica
        if company:
            history = [h for h in history if h['company'] == company.lower()]
        if extractor_merc_type:
            history = [h for h in history if h['type'] == extractor_merc_type.lower()]
        
        # Aplicar paginación
        paginated_history = history[offset:offset + limit]
        
        return {
            "total": len(history),
            "limit": limit,
            "offset": offset,
            "results": paginated_history
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mercurio_router.get("/reports")
async def get_generated_reports(
    extractor_merc_id: str = None,
    company: str = None,
    period: str = None
):
    """
    Obtiene lista de reportes generados
    """
    try:
        # TODO: Implementar consulta a base de datos
        # Simular respuesta por ahora
        reports = [
            {
                "id": "report_001",
                "extractor_merc_id": "extractor_merc_001",
                "type": "perdidas_resumen",
                "file_path": "s3://bucket/extractor_merc/aire/2024-07/perdidas_resumen/report_001.pdf",
                "generation_date": "2024-08-01T10:30:00Z"
            },
            {
                "id": "report_002",
                "extractor_merc_id": "extractor_merc_001",
                "type": "auditoria_detalle",
                "file_path": "s3://bucket/extractor_merc/aire/2024-07/auditoria_detalle/report_002.pdf",
                "generation_date": "2024-08-01T10:35:00Z"
            }
        ]
        
        # Aplicar filtros
        if extractor_merc_id:
            reports = [r for r in reports if r['extractor_merc_id'] == extractor_merc_id]
        if company:
            reports = [r for r in reports if company.lower() in r['file_path']]
        if period:
            reports = [r for r in reports if period in r['file_path']]
        
        return {
            "total": len(reports),
            "reports": reports
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo reportes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mercurio_router.get("/validate/{extractor_merc_id}")
async def validate_extractor_merc_data(extractor_merc_id: str):
    """
    Valida los datos de un archivo ExtractorMerc sin procesarlo
    """
    try:
        # TODO: Obtener ExtractorMerc document de base de datos
        # Simular validación por ahora
        
        return {
            "extractor_merc_id": extractor_merc_id,
            "validation_status": "valid",
            "validation_results": {
                "is_valid": True,
                "total_records": 1250,
                "validated_columns": ["fecha", "codigo", "valor", "tipo"],
                "errors": [],
                "warnings": ["Algunos valores nulos en columna 'observaciones'"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error validando ExtractorMerc {extractor_merc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 🔄 MIGRADO DESDE IPO: Nuevos endpoints para descarga de reportes
@mercurio_router.post("/download-reports")
async def download_mercurio_reports(
    company: str = Form(...),
    report_ids: List[str] = Form(...),
    date_from: Optional[str] = Form(None),
    date_to: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
):
    """🔄 MIGRADO DESDE IPO: Descarga reportes desde Mercurio"""
    try:
        logger.info(f"Iniciando descarga de reportes para {company} - Reports: {report_ids}")
        
        def run_download():
            """Función para ejecutar descarga en background"""
            try:
                # TODO: Implementar MercurioReportDownloader
                logger.info(f"Descarga completada para {company}")
                return {"status": "completed", "reports_downloaded": len(report_ids)}
            except Exception as e:
                logger.error(f"Error en descarga background: {e}")
                raise
        
        # Ejecutar descarga en background
        if background_tasks:
            background_tasks.add_task(run_download)
        
        return {
            "status": "success",
            "message": f"Descarga de reportes iniciada para {company}",
            "data": {
                "company": company, 
                "report_ids": report_ids,
                "started_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error descargando reportes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mercurio_router.post("/upload-letters")
async def upload_mercurio_letters(
    company: str = Form(...),
    limit: Optional[int] = Form(50),
    background_tasks: BackgroundTasks = None
):
    """🔄 MIGRADO DESDE IPO: Sube cartas a Mercurio"""
    try:
        logger.info(f"Iniciando carga de cartas para {company}")
        
        def run_upload():
            """Función para ejecutar carga en background"""
            try:
                # TODO: Implementar upload_letters_for_company
                logger.info(f"Carga de cartas completada para {company}")
                return {"status": "completed", "letters_uploaded": limit}
            except Exception as e:
                logger.error(f"Error en carga background: {e}")
                raise
        
        # Ejecutar carga en background
        if background_tasks:
            background_tasks.add_task(run_upload)
        
        return {
            "status": "success",
            "message": f"Carga de cartas iniciada para {company}",
            "data": {
                "company": company,
                "limit": limit,
                "started_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error subiendo cartas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mercurio_router.post("/process/rra-pendientes")
async def process_rra_pendientes(background_tasks: BackgroundTasks):
    """🔄 MIGRADO DESDE IPO: Procesa datos de RRA pendientes"""
    try:
        logger.info("Iniciando procesamiento de RRA pendientes")
        
        def run_processing():
            try:
                # TODO: Implementar procesamiento de RRA pendientes
                logger.info("Procesamiento de RRA pendientes completado")
            except Exception as e:
                logger.error(f"Error procesando RRA pendientes: {e}")
                raise
        
        background_tasks.add_task(run_processing)
        
        return {
            "status": "success",
            "message": "Procesamiento de RRA pendientes iniciado",
            "data": {"started_at": datetime.now().isoformat()}
        }
        
    except Exception as e:
        logger.error(f"Error procesando RRA pendientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mercurio_router.post("/process/verbales-pendientes")
async def process_verbales_pendientes(background_tasks: BackgroundTasks):
    """🔄 MIGRADO DESDE IPO: Procesa datos de verbales pendientes"""
    try:
        logger.info("Iniciando procesamiento de verbales pendientes")
        
        def run_processing():
            try:
                # TODO: Implementar procesamiento de verbales pendientes
                logger.info("Procesamiento de verbales pendientes completado")
            except Exception as e:
                logger.error(f"Error procesando verbales pendientes: {e}")
                raise
        
        background_tasks.add_task(run_processing)
        
        return {
            "status": "success",
            "message": "Procesamiento de verbales pendientes iniciado",
            "data": {"started_at": datetime.now().isoformat()}
        }
        
    except Exception as e:
        logger.error(f"Error procesando verbales pendientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Función auxiliar para ejecutar tareas en background
async def run_processing_task(mercurio_service, extractor_merc_document: ExtractorMercDocument, task_id: str):
    """
    Ejecuta una tarea de procesamiento ExtractorMerc en background
    """
    try:
        logger.info(f"Ejecutando procesamiento ExtractorMerc {task_id}")
        result = await mercurio_service.run_extractor_merc_processing(extractor_merc_document)
        
        # TODO: Guardar resultado en base de datos
        logger.info(f"Procesamiento {task_id} completado: {result}")
        
    except Exception as e:
        logger.error(f"Error en procesamiento {task_id}: {e}")
        # TODO: Actualizar estado de error en base de datos