"""ExtractorMerc Base - Funcionalidades Base del Sistema ExtractorMerc
==============================================

Clases base y funciones compartidas entre las implementaciones
de Air-e y Afinia para el módulo ExtractorMerc que extrae datos desde
la plataforma externa Mercurio (Informes de Pérdidas Operacionales).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
import pandas as pd

from src.core.adapters import DataAdapter
from src.core.logging import get_logger

logger = get_logger(__name__)

class ExtractorMercType(Enum):
    """Tipos de ExtractorMerc"""
    PERDIDAS_TECNICAS = "perdidas_tecnicas"
    PERDIDAS_COMERCIALES = "perdidas_comerciales"
    VERBALES = "verbales"
    AUDITORIA = "auditoria"

class ExtractorMercStatus(Enum):
    """Estados de procesamiento ExtractorMerc"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    VALIDATED = "validated"

@dataclass
class ExtractorMercDocument:
    """Modelo de datos para documentos ExtractorMerc"""
    id: str
    type: ExtractorMercType
    company: str
    period: str  # YYYY-MM format
    file_path: str
    upload_date: datetime
    processing_date: Optional[datetime] = None
    status: ExtractorMercStatus = ExtractorMercStatus.PENDING
    error_message: Optional[str] = None
    validation_results: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'type': self.type.value,
            'company': self.company,
            'period': self.period,
            'file_path': self.file_path,
            'upload_date': self.upload_date.isoformat(),
            'processing_date': self.processing_date.isoformat() if self.processing_date else None,
            'status': self.status.value,
            'error_message': self.error_message,
            'validation_results': self.validation_results
        }

@dataclass
class ExtractorMercReport:
    """Modelo de datos para reportes generados"""
    id: str
    extractor_merc_document_id: str
    report_type: str
    file_path: str
    generation_date: datetime
    parameters: Dict[str, Any]

class BaseMercurioService(ABC):
    """
    Servicio base para procesamiento de ExtractorMerc.
    Define la interfaz común para implementaciones específicas.
    """
    
    def __init__(self, adapter: DataAdapter):
        self.adapter = adapter
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def validate_extractor_merc_data(self, extractor_merc: ExtractorMercDocument) -> Dict[str, Any]:
        """Valida la estructura y contenido de datos ExtractorMerc"""
        pass
    
    @abstractmethod
    async def process_extractor_merc_file(self, extractor_merc: ExtractorMercDocument) -> bool:
        """Procesa un archivo ExtractorMerc específico"""
        pass
    
    @abstractmethod
    async def generate_reports(self, extractor_merc: ExtractorMercDocument) -> List[ExtractorMercReport]:
        """Genera reportes basados en datos ExtractorMerc procesados"""
        pass
    
    async def upload_to_s3(self, file_path: str, s3_key: str) -> bool:
        """Sube archivos procesados a S3 usando servicio centralizado"""
        from src.core.s3_service import s3_service
        return await s3_service.upload_file(file_path, s3_key)
    
    async def run_extractor_merc_processing(self, extractor_merc: ExtractorMercDocument) -> Dict[str, Any]:
        """
        Ejecuta el proceso completo de ExtractorMerc:
        1. Validación de datos
        2. Procesamiento del archivo
        3. Generación de reportes
        4. Subida a S3
        """
        self.logger.info(f"Iniciando procesamiento ExtractorMerc {extractor_merc.id}")
        
        try:
            extractor_merc.status = ExtractorMercStatus.PROCESSING
            extractor_merc.processing_date = datetime.now()
            
            # Validación de datos
            validation_result = await self.validate_extractor_merc_data(extractor_merc)
            extractor_merc.validation_results = validation_result
            
            if not validation_result.get('is_valid', False):
                extractor_merc.status = ExtractorMercStatus.ERROR
                extractor_merc.error_message = validation_result.get('error_message', 'Validación fallida')
                return extractor_merc.to_dict()
            
            # Procesamiento del archivo
            if not await self.process_extractor_merc_file(extractor_merc):
                extractor_merc.status = ExtractorMercStatus.ERROR
                extractor_merc.error_message = "Error en procesamiento de archivo"
                return extractor_merc.to_dict()
            
            # Generación de reportes
            reports = await self.generate_reports(extractor_merc)
            
            # Subida a S3
            s3_uploads = []
            for report in reports:
                s3_key = f"extractor_merc/{extractor_merc.company}/{extractor_merc.period}/{report.report_type}/{report.id}.pdf"
                if await self.upload_to_s3(report.file_path, s3_key):
                    s3_uploads.append(s3_key)
            
            extractor_merc.status = ExtractorMercStatus.COMPLETED
            
            result = extractor_merc.to_dict()
            result.update({
                'reports_generated': len(reports),
                's3_uploads': s3_uploads,
                'execution_time': datetime.now().isoformat()
            })
            
            self.logger.info(f"Procesamiento ExtractorMerc {extractor_merc.id} completado exitosamente")
            return result
            
        except Exception as e:
            self.logger.error(f"Error en procesamiento ExtractorMerc {extractor_merc.id}: {e}")
            extractor_merc.status = ExtractorMercStatus.ERROR
            extractor_merc.error_message = str(e)
            return extractor_merc.to_dict()

class ExtractorMercDataProcessor:
    """
    Procesador de datos ExtractorMerc con funcionalidades comunes
    """
    
    def __init__(self, company: str):
        self.company = company
        self.logger = get_logger(f"{__name__}.ExtractorMercDataProcessor")
    
    def load_excel_file(self, file_path: str) -> pd.DataFrame:
        """Carga archivo Excel con datos ExtractorMerc"""
        try:
            df = pd.read_excel(file_path)
            self.logger.info(f"Archivo Excel cargado: {len(df)} filas")
            return df
        except Exception as e:
            self.logger.error(f"Error cargando archivo Excel {file_path}: {e}")
            raise
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza datos"""
        try:
            # Eliminar filas vacías
            df = df.dropna(how='all')
            
            # Normalizar nombres de columnas
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Convertir tipos de datos
            for col in df.columns:
                if 'fecha' in col or 'date' in col:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                elif 'valor' in col or 'amount' in col or 'monto' in col:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            self.logger.info(f"Datos limpiados: {len(df)} filas válidas")
            return df
            
        except Exception as e:
            self.logger.error(f"Error limpiando datos: {e}")
            raise
    
    def validate_required_columns(self, df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
        """Valida que existan las columnas requeridas"""
        missing_columns = set(required_columns) - set(df.columns)
        
        if missing_columns:
            return {
                'is_valid': False,
                'error_message': f"Columnas faltantes: {', '.join(missing_columns)}",
                'missing_columns': list(missing_columns)
            }
        
        return {
            'is_valid': True,
            'validated_columns': required_columns,
            'total_columns': len(df.columns)
        }
    
    def generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Genera estadísticas resumen de los datos"""
        return {
            'total_records': len(df),
            'columns_count': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'null_counts': df.isnull().sum().to_dict(),
            'numeric_summary': df.describe().to_dict() if len(df.select_dtypes(include=['number']).columns) > 0 else {}
        }

class MercurioTaskScheduler:
    """
    Programador de tareas para procesamiento de Mercurio ExtractorMerc
    """
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.MercurioTaskScheduler")
        self.scheduled_tasks = {}
    
    def schedule_monthly_processing(self, company: str, day: int = 1, hour: int = 9):
        """Programa procesamiento mensual de ExtractorMerc"""
        self.logger.info(f"Programando procesamiento mensual para {company} el día {day} a las {hour}:00")
        # TODO: Implementar programación con Celery
    
    def schedule_immediate_processing(self, extractor_merc: ExtractorMercDocument) -> str:
        """Programa procesamiento inmediato de ExtractorMerc"""
        task_id = f"extractor_merc_processing_{extractor_merc.id}_{datetime.now().timestamp()}"
        self.logger.info(f"Programando procesamiento inmediato para ExtractorMerc {extractor_merc.id}, task_id: {task_id}")
        # TODO: Implementar ejecución inmediata con Celery
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Obtiene el estado de una tarea de procesamiento"""
        # TODO: Implementar consulta de estado con Celery
        return {
            'task_id': task_id,
            'status': 'pending',
            'progress': 0
        }