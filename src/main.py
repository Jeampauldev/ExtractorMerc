#!/usr/bin/env python3
"""
ExtractorMERC - Sistema Modular de Extracción de Datos Mercurio
===============================================================

Sistema refactorizado para la extracción automatizada de datos desde
las plataformas Mercurio de Afinia y Aire, con arquitectura modular
y mantenible.

Características principales:
- Arquitectura modular y escalable
- Manejo robusto de errores
- Logging centralizado
- Configuración flexible
- Procesamiento de datos optimizado

Autor: ExtractorOV Team
Fecha: 2025-01-27
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/extractor_merc.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Importaciones locales
from core.base_extractor import BaseExtractor, ExtractorStatus
from services.afinia_extractor import AfiniaExtractor
from services.aire_extractor import AireExtractor
from utils.aire_logger import setup_logging
from config.afinia_config import get_afinia_config


class ExtractorMercOrchestrator:
    """
    Orquestador principal del sistema ExtractorMERC
    
    Coordina la ejecución de extractores para diferentes empresas
    y maneja el flujo de trabajo completo.
    """
    
    def __init__(self):
        self.extractors: Dict[str, BaseExtractor] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        
    def register_extractor(self, company: str, extractor: BaseExtractor):
        """Registra un extractor para una empresa específica"""
        self.extractors[company] = extractor
        logger.info(f"Extractor registrado para {company}")
        
    async def run_extraction(self, company: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta la extracción para una empresa específica
        
        Args:
            company: Nombre de la empresa (afinia, aire)
            **kwargs: Parámetros adicionales para la extracción
            
        Returns:
            Diccionario con los resultados de la extracción
        """
        if company not in self.extractors:
            raise ValueError(f"No hay extractor registrado para {company}")
            
        extractor = self.extractors[company]
        
        try:
            logger.info(f"Iniciando extracción para {company}")
            start_time = datetime.now()
            
            # Ejecutar extracción
            result = await extractor.run_extraction(**kwargs)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Almacenar resultados
            self.results[company] = {
                'status': result.get('status', 'unknown'),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'extracted_files': result.get('extracted_files', []),
                'errors': result.get('errors', []),
                'statistics': result.get('statistics', {})
            }
            
            logger.info(f"Extracción completada para {company} en {duration:.2f}s")
            return self.results[company]
            
        except Exception as e:
            logger.error(f"Error en extracción para {company}: {str(e)}")
            self.results[company] = {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            raise
            
    async def run_all_extractions(self, **kwargs) -> Dict[str, Dict[str, Any]]:
        """
        Ejecuta extracciones para todas las empresas registradas
        
        Returns:
            Diccionario con resultados de todas las extracciones
        """
        tasks = []
        for company in self.extractors.keys():
            task = asyncio.create_task(
                self.run_extraction(company, **kwargs),
                name=f"extraction_{company}"
            )
            tasks.append((company, task))
            
        # Ejecutar todas las extracciones en paralelo
        results = {}
        for company, task in tasks:
            try:
                results[company] = await task
            except Exception as e:
                logger.error(f"Fallo en extracción para {company}: {str(e)}")
                results[company] = {
                    'status': 'error',
                    'error': str(e)
                }
                
        return results
        
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de todas las extracciones ejecutadas"""
        summary = {
            'total_extractors': len(self.extractors),
            'completed_extractions': len(self.results),
            'successful_extractions': 0,
            'failed_extractions': 0,
            'companies': list(self.extractors.keys()),
            'results': self.results
        }
        
        for result in self.results.values():
            if result.get('status') == 'completed':
                summary['successful_extractions'] += 1
            else:
                summary['failed_extractions'] += 1
                
        return summary


async def main():
    """Función principal del sistema ExtractorMERC"""
    
    # Crear directorio de logs si no existe
    Path('logs').mkdir(exist_ok=True)
    
    logger.info("=== Iniciando ExtractorMERC ===")
    
    try:
        # Inicializar orquestador
        orchestrator = ExtractorMercOrchestrator()
        
        # Registrar extractores
        afinia_extractor = AfiniaExtractor(
            company="afinia",
            headless=True
        )
        orchestrator.register_extractor("afinia", afinia_extractor)
        
        aire_extractor = AireExtractor(
            company="aire", 
            headless=True
        )
        orchestrator.register_extractor("aire", aire_extractor)
        
        # Ejecutar extracciones
        logger.info("Ejecutando extracciones para todas las empresas...")
        results = await orchestrator.run_all_extractions()
        
        # Mostrar resumen
        summary = orchestrator.get_summary()
        logger.info("=== Resumen de Extracciones ===")
        logger.info(f"Total de extractores: {summary['total_extractors']}")
        logger.info(f"Extracciones exitosas: {summary['successful_extractions']}")
        logger.info(f"Extracciones fallidas: {summary['failed_extractions']}")
        
        # Mostrar detalles por empresa
        for company, result in results.items():
            status = result.get('status', 'unknown')
            logger.info(f"{company.upper()}: {status}")
            
            if 'duration_seconds' in result:
                logger.info(f"  Duración: {result['duration_seconds']:.2f}s")
            if 'extracted_files' in result:
                logger.info(f"  Archivos extraídos: {len(result['extracted_files'])}")
            if 'errors' in result and result['errors']:
                logger.warning(f"  Errores: {len(result['errors'])}")
                
        logger.info("=== ExtractorMERC Finalizado ===")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error crítico en ExtractorMERC: {str(e)}")
        raise


if __name__ == "__main__":
    # Ejecutar el sistema
    try:
        summary = asyncio.run(main())
        
        # Código de salida basado en resultados
        if summary['failed_extractions'] > 0:
            sys.exit(1)  # Salir con error si hubo fallos
        else:
            sys.exit(0)  # Salir exitosamente
            
    except KeyboardInterrupt:
        logger.info("Extracción interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        sys.exit(1)