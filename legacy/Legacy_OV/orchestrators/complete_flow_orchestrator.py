#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquestador de Flujo Completo para Extractor OV Modular
======================================================

Orquestador que coordina el flujo completo:
Web → CSV → RDS → Verificación S3 → Subida S3

Implementa el Paso 23 del FLUJO_VERIFICACION.md:
- Coordinar flujo completo para Afinia y Air-e
- Integrar todos los servicios existentes
- Manejo de errores y logging detallado
- Reportes de ejecución

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time

# Servicios de extracción y carga
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.services.bulk_database_loader import BulkDatabaseLoader
from src.services.s3_verification_service import S3VerificationService, S3VerificationStats
from src.services.filtered_s3_uploader import FilteredS3Uploader, FilteredUploadStats
from src.services.json_consolidator_service import JSONConsolidatorService

# Servicios de descarga (si existen)
try:
    from src.services.web_downloader_service import WebDownloaderService
except ImportError:
    WebDownloaderService = None

logger = logging.getLogger(__name__)

@dataclass
class FlowStepResult:
    """Resultado de un paso del flujo"""
    step_name: str
    empresa: str
    success: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    records_processed: int = 0
    files_processed: int = 0
    errors: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CompleteFlowResult:
    """Resultado del flujo completo"""
    empresa: str
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration: float = 0.0
    steps_completed: List[FlowStepResult] = None
    overall_success: bool = False
    total_records_processed: int = 0
    total_files_uploaded: int = 0
    summary: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.steps_completed is None:
            self.steps_completed = []
        if self.summary is None:
            self.summary = {}

class CompleteFlowOrchestrator:
    """
    Orquestador del flujo completo de procesamiento
    """
    
    def __init__(self, simulated_mode: bool = False):
        """
        Inicializar orquestador
        
        Args:
            simulated_mode: Si True, ejecuta en modo simulado
        """
        self.simulated_mode = simulated_mode
        
        # Inicializar servicios
        self.db_loader = BulkDatabaseLoader()
        self.s3_verifier = S3VerificationService()
        self.s3_uploader = FilteredS3Uploader(simulated_mode=simulated_mode)
        self.json_consolidator = JSONConsolidatorService()
        
        # Web downloader (opcional)
        self.web_downloader = None
        if WebDownloaderService:
            try:
                self.web_downloader = WebDownloaderService()
            except Exception as e:
                logger.warning(f"[complete_flow][init] No se pudo inicializar WebDownloaderService: {e}")
        
        logger.info(f"[complete_flow][init] Orquestador inicializado (modo simulado: {simulated_mode})")
    
    def execute_complete_flow(self, empresa: str,
                            include_web_download: bool = False,
                            csv_directory: Optional[str] = None,
                            force_reprocess: bool = False) -> CompleteFlowResult:
        """
        Ejecutar el flujo completo para una empresa
        
        Args:
            empresa: 'afinia' o 'aire'
            include_web_download: Si incluir descarga web
            csv_directory: Directorio de archivos CSV (si no se descarga)
            force_reprocess: Forzar reprocesamiento
            
        Returns:
            Resultado del flujo completo
        """
        execution_id = f"{empresa}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        result = CompleteFlowResult(
            empresa=empresa,
            execution_id=execution_id,
            start_time=start_time
        )
        
        logger.info(f"[complete_flow][execute] Iniciando flujo completo para {empresa} "
                   f"(ID: {execution_id})")
        
        try:
            # Paso 1: Descarga Web (opcional)
            if include_web_download and self.web_downloader:
                step_result = self._execute_web_download(empresa)
                result.steps_completed.append(step_result)
                
                if not step_result.success:
                    logger.error(f"[complete_flow][execute] Fallo en descarga web para {empresa}")
                    result.overall_success = False
                    return self._finalize_result(result)
            
            # Paso 1.5: Consolidación JSON → CSV
            step_result = self._execute_json_consolidation(empresa)
            result.steps_completed.append(step_result)
            
            if not step_result.success:
                logger.warning(f"[complete_flow][execute] Advertencia en consolidación JSON para {empresa}")
                # No es crítico si no hay JSONs, continuar con CSVs existentes
            
            # Paso 2: Carga CSV → RDS
            csv_dir = csv_directory or self._get_default_csv_directory(empresa)
            step_result = self._execute_csv_to_rds(empresa, csv_dir, force_reprocess)
            result.steps_completed.append(step_result)
            
            if not step_result.success:
                logger.error(f"[complete_flow][execute] Fallo en carga CSV→RDS para {empresa}")
                result.overall_success = False
                return self._finalize_result(result)
            
            result.total_records_processed += step_result.records_processed
            
            # Paso 3: Verificación S3
            step_result = self._execute_s3_verification(empresa)
            result.steps_completed.append(step_result)
            
            if not step_result.success:
                logger.warning(f"[complete_flow][execute] Advertencia en verificación S3 para {empresa}")
                # No es crítico, continuar
            
            # Paso 4: Subida S3 Filtrada
            step_result = self._execute_filtered_s3_upload(empresa)
            result.steps_completed.append(step_result)
            
            if not step_result.success:
                logger.error(f"[complete_flow][execute] Fallo en subida S3 para {empresa}")
                result.overall_success = False
                return self._finalize_result(result)
            
            result.total_files_uploaded += step_result.files_processed
            
            # Flujo completado exitosamente
            result.overall_success = True
            logger.info(f"[complete_flow][execute] Flujo completado exitosamente para {empresa}")
            
        except Exception as e:
            error_msg = f"Error crítico en flujo completo para {empresa}: {e}"
            logger.error(f"[complete_flow][execute] {error_msg}")
            
            # Agregar error al último paso o crear uno nuevo
            if result.steps_completed:
                result.steps_completed[-1].errors.append(error_msg)
            else:
                error_step = FlowStepResult(
                    step_name="error_critico",
                    empresa=empresa,
                    success=False,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    errors=[error_msg]
                )
                result.steps_completed.append(error_step)
            
            result.overall_success = False
        
        return self._finalize_result(result)
    
    def _execute_web_download(self, empresa: str) -> FlowStepResult:
        """Ejecutar descarga web"""
        step_result = FlowStepResult(
            step_name="web_download",
            empresa=empresa,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"[complete_flow][web_download] Iniciando descarga web para {empresa}")
            
            if self.simulated_mode:
                # Simular descarga
                time.sleep(1)
                step_result.success = True
                step_result.files_processed = 10  # Simulado
                step_result.metadata = {"simulated": True, "files_downloaded": 10}
            else:
                # Ejecutar descarga real (implementar según servicio disponible)
                step_result.success = True
                step_result.files_processed = 0
                step_result.metadata = {"message": "Web download not implemented"}
            
        except Exception as e:
            step_result.errors.append(f"Error en descarga web: {e}")
            step_result.success = False
        
        step_result.end_time = datetime.now()
        step_result.duration_seconds = (step_result.end_time - step_result.start_time).total_seconds()
        
        return step_result
    
    def _execute_json_consolidation(self, empresa: str) -> FlowStepResult:
        """Ejecutar consolidación JSON → CSV"""
        step_result = FlowStepResult(
            step_name="json_consolidation",
            empresa=empresa,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"[complete_flow][json_consolidation] Iniciando consolidación JSON para {empresa}")
            
            if self.simulated_mode:
                # Simular consolidación
                time.sleep(1)
                step_result.success = True
                step_result.records_processed = 50  # Simulado
                step_result.files_processed = 5  # Simulado
                step_result.metadata = {
                    "simulated": True,
                    "csv_generated": f"data/processed/{empresa}_consolidated_simulated.csv"
                }
            else:
                # Ejecutar consolidación real
                consolidation_result = self.json_consolidator.consolidate_company_data(empresa)
                
                step_result.success = consolidation_result.get('success', False)
                step_result.records_processed = consolidation_result.get('records_count', 0)
                step_result.files_processed = consolidation_result.get('statistics', {}).get('total_files', 0)
                
                if consolidation_result.get('output_files'):
                    step_result.metadata = {
                        "output_files": consolidation_result['output_files'],
                        "statistics": consolidation_result['statistics']
                    }
                    logger.info(f"[complete_flow][json_consolidation] CSV generado: {consolidation_result['output_files'].get('csv', 'N/A')}")
                else:
                    step_result.errors.append("No se generaron archivos de salida")
                    
                if not step_result.success:
                    step_result.errors.append("Consolidación JSON falló o no encontró archivos")
            
        except Exception as e:
            step_result.errors.append(f"Error en consolidación JSON: {e}")
            step_result.success = False
        
        step_result.end_time = datetime.now()
        step_result.duration_seconds = (step_result.end_time - step_result.start_time).total_seconds()
        
        logger.info(f"[complete_flow][json_consolidation] Consolidación completada para {empresa}: "
                   f"éxito={step_result.success}, registros={step_result.records_processed}")
        
        return step_result
    
    def _execute_csv_to_rds(self, empresa: str, csv_directory: str, 
                          force_reprocess: bool = False) -> FlowStepResult:
        """Ejecutar carga CSV → RDS"""
        step_result = FlowStepResult(
            step_name="csv_to_rds",
            empresa=empresa,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"[complete_flow][csv_to_rds] Iniciando carga CSV→RDS para {empresa}")
            
            csv_path = Path(csv_directory)
            if not csv_path.exists():
                step_result.errors.append(f"Directorio CSV no encontrado: {csv_directory}")
                step_result.success = False
                return step_result
            
            # Buscar archivos CSV
            csv_files = list(csv_path.glob("*.csv"))
            if not csv_files:
                step_result.errors.append(f"No se encontraron archivos CSV en: {csv_directory}")
                step_result.success = False
                return step_result
            
            step_result.files_processed = len(csv_files)
            
            if self.simulated_mode:
                # Simular carga
                time.sleep(2)
                step_result.success = True
                step_result.records_processed = len(csv_files) * 100  # Simulado
                step_result.metadata = {
                    "simulated": True,
                    "csv_files": [str(f) for f in csv_files],
                    "records_loaded": step_result.records_processed
                }
            else:
                # Ejecutar carga real
                total_records = 0
                
                for csv_file in csv_files:
                    try:
                        # Usar BulkDatabaseLoader
                        load_result = self.db_loader.load_csv_to_database(
                            csv_file_path=str(csv_file),
                            company=empresa
                        )
                        
                        if load_result and hasattr(load_result, 'inserted_records'):
                            total_records += load_result.inserted_records
                        
                    except Exception as e:
                        step_result.errors.append(f"Error cargando {csv_file.name}: {e}")
                
                step_result.records_processed = total_records
                step_result.success = len(step_result.errors) == 0
                step_result.metadata = {
                    "csv_files_processed": len(csv_files),
                    "total_records_loaded": total_records
                }
            
        except Exception as e:
            step_result.errors.append(f"Error en carga CSV→RDS: {e}")
            step_result.success = False
        
        step_result.end_time = datetime.now()
        step_result.duration_seconds = (step_result.end_time - step_result.start_time).total_seconds()
        
        return step_result
    
    def _execute_s3_verification(self, empresa: str) -> FlowStepResult:
        """Ejecutar verificación S3"""
        step_result = FlowStepResult(
            step_name="s3_verification",
            empresa=empresa,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"[complete_flow][s3_verification] Iniciando verificación S3 para {empresa}")
            
            # Ejecutar verificación
            verification_stats = self.s3_verifier.verify_s3_status_after_rds_load(empresa, {})
            
            step_result.success = len(verification_stats.errores) == 0
            step_result.records_processed = verification_stats.total_registros_rds
            step_result.metadata = {
                "total_registros_rds": verification_stats.total_registros_rds,
                "pendientes_s3": verification_stats.registros_pendientes_s3,
                "ya_subidos": verification_stats.registros_ya_subidos,
                "con_error": verification_stats.registros_con_error,
                "archivos_encontrados": verification_stats.archivos_encontrados,
                "archivos_faltantes": verification_stats.archivos_faltantes,
                "tiempo_procesamiento": verification_stats.tiempo_procesamiento
            }
            
            if verification_stats.errores:
                step_result.errors.extend(verification_stats.errores)
            
        except Exception as e:
            step_result.errors.append(f"Error en verificación S3: {e}")
            step_result.success = False
        
        step_result.end_time = datetime.now()
        step_result.duration_seconds = (step_result.end_time - step_result.start_time).total_seconds()
        
        return step_result
    
    def _execute_filtered_s3_upload(self, empresa: str) -> FlowStepResult:
        """Ejecutar subida S3 filtrada"""
        step_result = FlowStepResult(
            step_name="filtered_s3_upload",
            empresa=empresa,
            start_time=datetime.now()
        )
        
        try:
            logger.info(f"[complete_flow][s3_upload] Iniciando subida S3 filtrada para {empresa}")
            
            # Ejecutar subida filtrada
            upload_stats = self.s3_uploader.upload_pending_files_for_company(empresa)
            
            step_result.success = upload_stats.registros_fallidos == 0
            step_result.records_processed = upload_stats.registros_procesados
            step_result.files_processed = upload_stats.archivos_subidos
            step_result.metadata = {
                "total_candidatos": upload_stats.total_candidatos,
                "registros_procesados": upload_stats.registros_procesados,
                "registros_completados": upload_stats.registros_completados,
                "registros_parciales": upload_stats.registros_parciales,
                "registros_fallidos": upload_stats.registros_fallidos,
                "registros_omitidos": upload_stats.registros_omitidos,
                "archivos_subidos": upload_stats.archivos_subidos,
                "bytes_totales": upload_stats.bytes_totales,
                "tiempo_total": upload_stats.tiempo_total
            }
            
            if upload_stats.errores_globales:
                step_result.errors.extend(upload_stats.errores_globales)
            
        except Exception as e:
            step_result.errors.append(f"Error en subida S3: {e}")
            step_result.success = False
        
        step_result.end_time = datetime.now()
        step_result.duration_seconds = (step_result.end_time - step_result.start_time).total_seconds()
        
        return step_result
    
    def _get_default_csv_directory(self, empresa: str) -> str:
        """Obtener directorio CSV por defecto - usar data/processed donde se generan los CSVs consolidados"""
        return "data/processed"
    
    def _finalize_result(self, result: CompleteFlowResult) -> CompleteFlowResult:
        """Finalizar resultado del flujo"""
        result.end_time = datetime.now()
        result.total_duration = (result.end_time - result.start_time).total_seconds()
        
        # Generar resumen
        result.summary = {
            "steps_total": len(result.steps_completed),
            "steps_successful": sum(1 for step in result.steps_completed if step.success),
            "steps_failed": sum(1 for step in result.steps_completed if not step.success),
            "total_errors": sum(len(step.errors) for step in result.steps_completed),
            "execution_time_minutes": result.total_duration / 60,
            "records_per_minute": result.total_records_processed / (result.total_duration / 60) if result.total_duration > 0 else 0
        }
        
        return result
    
    def execute_flow_for_all_companies(self, **kwargs) -> Dict[str, CompleteFlowResult]:
        """
        Ejecutar flujo completo para todas las empresas
        
        Args:
            **kwargs: Argumentos para execute_complete_flow
            
        Returns:
            Resultados por empresa
        """
        results = {}
        
        for empresa in ['afinia', 'aire']:
            logger.info(f"[complete_flow][execute_all] Procesando {empresa}")
            
            try:
                result = self.execute_complete_flow(empresa, **kwargs)
                results[empresa] = result
                
            except Exception as e:
                logger.error(f"[complete_flow][execute_all] Error procesando {empresa}: {e}")
                
                # Crear resultado de error
                error_result = CompleteFlowResult(
                    empresa=empresa,
                    execution_id=f"{empresa}_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    overall_success=False
                )
                
                error_step = FlowStepResult(
                    step_name="critical_error",
                    empresa=empresa,
                    success=False,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    errors=[f"Error crítico: {e}"]
                )
                
                error_result.steps_completed.append(error_step)
                results[empresa] = error_result
        
        return results
    
    def generate_execution_report(self, results: Dict[str, CompleteFlowResult]) -> Dict[str, Any]:
        """
        Generar reporte de ejecución
        
        Args:
            results: Resultados por empresa
            
        Returns:
            Reporte completo
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'modo_simulado': self.simulated_mode,
            'empresas': {},
            'resumen_global': {
                'empresas_procesadas': len(results),
                'empresas_exitosas': 0,
                'empresas_fallidas': 0,
                'total_registros': 0,
                'total_archivos_subidos': 0,
                'tiempo_total_minutos': 0.0,
                'errores_totales': 0
            }
        }
        
        for empresa, result in results.items():
            # Datos por empresa
            empresa_data = asdict(result)
            report['empresas'][empresa] = empresa_data
            
            # Actualizar totales
            if result.overall_success:
                report['resumen_global']['empresas_exitosas'] += 1
            else:
                report['resumen_global']['empresas_fallidas'] += 1
            
            report['resumen_global']['total_registros'] += result.total_records_processed
            report['resumen_global']['total_archivos_subidos'] += result.total_files_uploaded
            report['resumen_global']['tiempo_total_minutos'] += result.total_duration / 60
            report['resumen_global']['errores_totales'] += sum(len(step.errors) for step in result.steps_completed)
        
        return report


# Funciones de conveniencia

def execute_complete_flow_for_company(empresa: str, simulated_mode: bool = False, **kwargs) -> CompleteFlowResult:
    """
    Ejecutar flujo completo para una empresa
    
    Args:
        empresa: 'afinia' o 'aire'
        simulated_mode: Modo simulado
        **kwargs: Argumentos adicionales
        
    Returns:
        Resultado del flujo
    """
    orchestrator = CompleteFlowOrchestrator(simulated_mode=simulated_mode)
    return orchestrator.execute_complete_flow(empresa, **kwargs)

def execute_complete_flow_all_companies(simulated_mode: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Ejecutar flujo completo para todas las empresas
    
    Args:
        simulated_mode: Modo simulado
        **kwargs: Argumentos adicionales
        
    Returns:
        Reporte completo
    """
    orchestrator = CompleteFlowOrchestrator(simulated_mode=simulated_mode)
    results = orchestrator.execute_flow_for_all_companies(**kwargs)
    return orchestrator.generate_execution_report(results)


if __name__ == "__main__":
    # Test del orquestador completo
    logger.info("[complete_flow][main] Iniciando test del orquestador completo")
    
    print("=" * 80)
    print("TEST DEL ORQUESTADOR DE FLUJO COMPLETO (MODO SIMULADO)")
    print("=" * 80)
    
    # Ejecutar para todas las empresas en modo simulado
    report = execute_complete_flow_all_companies(simulated_mode=True)
    
    print(f"\nTimestamp: {report['timestamp']}")
    print(f"Modo simulado: {report['modo_simulado']}")
    
    # Resumen global
    resumen = report['resumen_global']
    print(f"\nRESUMEN GLOBAL:")
    print(f"  - Empresas procesadas: {resumen['empresas_procesadas']}")
    print(f"  - Empresas exitosas: {resumen['empresas_exitosas']}")
    print(f"  - Empresas fallidas: {resumen['empresas_fallidas']}")
    print(f"  - Total registros procesados: {resumen['total_registros']}")
    print(f"  - Total archivos subidos: {resumen['total_archivos_subidos']}")
    print(f"  - Tiempo total: {resumen['tiempo_total_minutos']:.2f} minutos")
    print(f"  - Errores totales: {resumen['errores_totales']}")
    
    # Detalles por empresa
    for empresa, empresa_data in report['empresas'].items():
        print(f"\n{empresa.upper()}:")
        print(f"  - Ejecución ID: {empresa_data['execution_id']}")
        print(f"  - Éxito general: {empresa_data['overall_success']}")
        print(f"  - Duración: {empresa_data['total_duration']:.2f}s")
        print(f"  - Registros procesados: {empresa_data['total_records_processed']}")
        print(f"  - Archivos subidos: {empresa_data['total_files_uploaded']}")
        print(f"  - Pasos completados: {len(empresa_data['steps_completed'])}")
        
        # Mostrar pasos
        for step in empresa_data['steps_completed']:
            status = "✓" if step['success'] else "✗"
            print(f"    {status} {step['step_name']}: {step['duration_seconds']:.2f}s")
            if step['errors']:
                for error in step['errors'][:2]:  # Mostrar solo los primeros 2
                    print(f"      - Error: {error}")
    
    print("\n" + "=" * 80)