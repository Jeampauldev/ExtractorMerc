"""
Base Extractor - Clase Base Abstracta para Extractores
=====================================================

Clase base que define la interfaz común para todos los extractores
de Mercurio (Afinia y Aire).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ExtractorStatus(Enum):
    """Estados del extractor"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    AUTHENTICATING = "authenticating"
    EXTRACTING = "extracting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class BaseExtractor(ABC):
    """
    Clase base abstracta para todos los extractores de Mercurio.
    
    Define la interfaz común y funcionalidades compartidas entre
    los extractores de Afinia y Aire.
    """
    
    def __init__(self, company: str, headless: bool = True):
        self.company = company
        self.headless = headless
        self.status = ExtractorStatus.IDLE
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.extracted_files: List[str] = []
        self.errors: List[str] = []
        
        # Configurar logger específico
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{company}")
    
    @abstractmethod
    def setup_browser(self) -> bool:
        """Configurar e inicializar el navegador"""
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Realizar autenticación en la plataforma"""
        pass
    
    @abstractmethod
    def extract_data(self, **kwargs) -> Dict[str, Any]:
        """Extraer datos de la plataforma"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Limpiar recursos y cerrar conexiones"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del extractor"""
        return {
            "company": self.company,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "extracted_files": len(self.extracted_files),
            "errors": len(self.errors)
        }
    
    def log_error(self, error: str) -> None:
        """Registrar un error"""
        self.errors.append(f"{datetime.now().isoformat()}: {error}")
        self.logger.error(error)
    
    def log_info(self, message: str) -> None:
        """Registrar información"""
        self.logger.info(f"[{self.company.upper()}] {message}")
    
    def run_extraction(self, **kwargs) -> Dict[str, Any]:
        """
        Ejecutar el proceso completo de extracción.
        
        Template method que define el flujo general:
        1. Setup browser
        2. Authenticate
        3. Extract data
        4. Cleanup
        """
        self.start_time = datetime.now()
        self.status = ExtractorStatus.INITIALIZING
        
        try:
            # 1. Setup browser
            self.log_info("Inicializando navegador...")
            if not self.setup_browser():
                raise Exception("Error al configurar navegador")
            
            # 2. Authenticate
            self.status = ExtractorStatus.AUTHENTICATING
            self.log_info("Autenticando...")
            if not self.authenticate():
                raise Exception("Error en autenticación")
            
            # 3. Extract data
            self.status = ExtractorStatus.EXTRACTING
            self.log_info("Extrayendo datos...")
            result = self.extract_data(**kwargs)
            
            self.status = ExtractorStatus.COMPLETED
            self.end_time = datetime.now()
            
            return {
                "success": True,
                "company": self.company,
                "extracted_files": self.extracted_files,
                "duration": (self.end_time - self.start_time).total_seconds(),
                "result": result
            }
            
        except Exception as e:
            self.status = ExtractorStatus.ERROR
            self.end_time = datetime.now()
            error_msg = f"Error en extracción: {str(e)}"
            self.log_error(error_msg)
            
            return {
                "success": False,
                "company": self.company,
                "error": error_msg,
                "extracted_files": self.extracted_files,
                "duration": (self.end_time - self.start_time).total_seconds() if self.end_time else 0
            }
        
        finally:
            # Siempre limpiar recursos
            try:
                self.cleanup()
            except Exception as e:
                self.log_error(f"Error en cleanup: {str(e)}")