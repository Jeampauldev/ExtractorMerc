#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de Post-Procesamiento Integral
=======================================

Servicio que coordina todas las actividades de post-procesamiento después 
de la extracción de datos: carga a base de datos, subida a S3, y generación
de reportes consolidados.

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

from src.services.bulk_database_loader import load_processed_json_files
from src.services.unified_s3_service import UnifiedS3Service, S3PathStructure

logger = logging.getLogger(__name__)

@dataclass
class PostProcessingResult:
    """Resultado del post-procesamiento"""
    success: bool
    company: str
    
    # Estadísticas de BD
    db_inserted: int = 0
    db_updated: int = 0
    db_duplicates: int = 0
    db_errors: int = 0
    db_time: float = 0.0
    
    # Estadísticas de S3
    s3_uploaded: int = 0
    s3_pre_existing: int = 0
    s3_errors: int = 0
    s3_total_size: int = 0
    s3_time: float = 0.0
    
    # Información general
    total_files_processed: int = 0
    total_processing_time: float = 0.0
    error_messages: List[str] = None
    
    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []

@dataclass
class IntegratedPostProcessingStats:
    """Estadísticas consolidadas de post-procesamiento"""
    success: bool
    companies_processed: List[str]
    results_by_company: Dict[str, PostProcessingResult]
    
    # Totales generales
    total_db_inserted: int = 0
    total_db_updated: int = 0
    total_db_duplicates: int = 0
    total_db_errors: int = 0
    
    total_s3_uploaded: int = 0
    total_s3_pre_existing: int = 0
    total_s3_errors: int = 0
    total_s3_size_mb: float = 0.0
    
    total_processing_time: float = 0.0
    timestamp: str = ""

class PostProcessingService:
    """
    Servicio integral de post-procesamiento para coordinar carga a BD y S3
    """
    
    def __init__(self):
        """Inicializar servicio de post-procesamiento"""
        self.start_time = None
        logger.info("[post_processing][init] Servicio de post-procesamiento inicializado")
    
    def process_company_data(self, company: str, database_only: bool = False) -> PostProcessingResult:
        """
        Procesar datos de una empresa específica
        
        Args:
            company: 'afinia' o 'aire'
            database_only: Si True, solo procesa base de datos (omite S3)
            
        Returns:
            Resultado del procesamiento
        """
        start_time = datetime.now()
        
        logger.info(f"[post_processing][process_company] Iniciando post-procesamiento para {company}")
        
        result = PostProcessingResult(
            success=False,
            company=company
        )
        
        try:
            # 1. Carga a base de datos
            logger.info(f"[post_processing][process_company] Cargando datos a BD para {company}...")
            
            from src.services.bulk_database_loader import BulkDatabaseLoader
            db_loader = BulkDatabaseLoader()
            db_stats = db_loader.load_processed_json_to_database(company)
            
            # Estadísticas de BD
            result.db_inserted = db_stats.inserted_records
            result.db_updated = db_stats.updated_records
            result.db_duplicates = db_stats.skipped_duplicates
            result.db_errors = db_stats.error_records
            result.db_time = db_stats.processing_time
            result.total_files_processed = db_stats.total_records
            
            if db_stats.errors:
                result.error_messages.extend(db_stats.errors)
            
            logger.info(f"[post_processing][process_company] BD completado para {company}: "
                       f"{result.db_inserted} insertados, {result.db_updated} actualizados")
            
            # 2. Subida a S3 (solo si no es modo database_only)
            if not database_only:
                logger.info(f"[post_processing][process_company] Subiendo archivos a S3 para {company}...")
                
                # Usar UnifiedS3Service en lugar de la función importada
                s3_service = UnifiedS3Service(path_structure=S3PathStructure.CENTRAL)
                s3_stats = s3_service.upload_company_files(company)
                
                # Estadísticas de S3
                result.s3_uploaded = s3_stats.uploaded_files
                result.s3_pre_existing = s3_stats.pre_existing_files
                result.s3_errors = s3_stats.error_files
                result.s3_total_size = s3_stats.total_size_bytes
                result.s3_time = s3_stats.processing_time
                
                if s3_stats.errors:
                    result.error_messages.extend(s3_stats.errors)
                
                logger.info(f"[post_processing][process_company] S3 completado para {company}: "
                           f"{result.s3_uploaded} subidos, {result.s3_pre_existing} pre-existentes")
            else:
                logger.info(f"[post_processing][process_company] Omitiendo S3 (modo database_only)")
            
            # 3. Determinar éxito general
            result.success = (result.db_errors == 0 and result.s3_errors == 0) or \
                           (result.db_inserted > 0 or result.s3_uploaded > 0)
            
            # Tiempo total
            end_time = datetime.now()
            result.total_processing_time = (end_time - start_time).total_seconds()
            
            logger.info(f"[post_processing][process_company] Post-procesamiento completado para {company}: "
                       f"{'EXITOSO' if result.success else 'CON ERRORES'} en {result.total_processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Error crítico en post-procesamiento de {company}: {e}"
            logger.error(f"[post_processing][process_company] {error_msg}")
            
            result.error_messages.append(error_msg)
            result.total_processing_time = (datetime.now() - start_time).total_seconds()
            
            return result
    
    def run_integrated_post_processing(self, companies: List[str] = None) -> IntegratedPostProcessingStats:
        """
        Ejecutar post-procesamiento integral para todas las empresas
        
        Args:
            companies: Lista de empresas a procesar (por defecto ['afinia', 'aire'])
            
        Returns:
            Estadísticas consolidadas
        """
        self.start_time = datetime.now()
        
        if companies is None:
            companies = ['afinia', 'aire']
        
        logger.info(f"[post_processing][run_integrated] Iniciando post-procesamiento integral para: {companies}")
        
        # Inicializar estadísticas
        stats = IntegratedPostProcessingStats(
            success=True,
            companies_processed=companies,
            results_by_company={},
            timestamp=self.start_time.isoformat()
        )
        
        # Procesar cada empresa
        for company in companies:
            try:
                result = self.process_company_data(company)
                stats.results_by_company[company] = result
                
                # Acumular totales
                stats.total_db_inserted += result.db_inserted
                stats.total_db_updated += result.db_updated
                stats.total_db_duplicates += result.db_duplicates
                stats.total_db_errors += result.db_errors
                
                stats.total_s3_uploaded += result.s3_uploaded
                stats.total_s3_pre_existing += result.s3_pre_existing
                stats.total_s3_errors += result.s3_errors
                stats.total_s3_size_mb += (result.s3_total_size / 1024 / 1024)
                
                # Si alguna empresa falló, marcar como fallido
                if not result.success:
                    stats.success = False
                
            except Exception as e:
                error_msg = f"Error crítico procesando {company}: {e}"
                logger.error(f"[post_processing][run_integrated] {error_msg}")
                
                # Crear resultado de error
                error_result = PostProcessingResult(
                    success=False,
                    company=company,
                    error_messages=[error_msg]
                )
                stats.results_by_company[company] = error_result
                stats.success = False
        
        # Tiempo total de procesamiento
        end_time = datetime.now()
        stats.total_processing_time = (end_time - self.start_time).total_seconds()
        
        logger.info(f"[post_processing][run_integrated] Post-procesamiento integral completado: "
                   f"{'EXITOSO' if stats.success else 'CON ERRORES'} en {stats.total_processing_time:.2f}s")
        
        return stats
    
    def generate_processing_report(self, stats: IntegratedPostProcessingStats) -> Dict[str, Any]:
        """
        Generar reporte consolidado de post-procesamiento
        
        Args:
            stats: Estadísticas del procesamiento
            
        Returns:
            Reporte estructurado
        """
        report = {
            'post_processing_report': {
                'timestamp': stats.timestamp,
                'success': stats.success,
                'total_processing_time': stats.total_processing_time,
                'companies_processed': stats.companies_processed,
                
                'database_summary': {
                    'total_inserted': stats.total_db_inserted,
                    'total_updated': stats.total_db_updated,
                    'total_duplicates': stats.total_db_duplicates,
                    'total_errors': stats.total_db_errors
                },
                
                's3_summary': {
                    'total_uploaded': stats.total_s3_uploaded,
                    'total_pre_existing': stats.total_s3_pre_existing,
                    'total_errors': stats.total_s3_errors,
                    'total_size_mb': round(stats.total_s3_size_mb, 2)
                },
                
                'by_company': {}
            }
        }
        
        # Detalles por empresa
        for company, result in stats.results_by_company.items():
            company_report = {
                'success': result.success,
                'total_files_processed': result.total_files_processed,
                'processing_time': result.total_processing_time,
                
                'database': {
                    'inserted': result.db_inserted,
                    'updated': result.db_updated,
                    'duplicates': result.db_duplicates,
                    'errors': result.db_errors,
                    'time_seconds': result.db_time
                },
                
                's3': {
                    'uploaded': result.s3_uploaded,
                    'pre_existing': result.s3_pre_existing,
                    'errors': result.s3_errors,
                    'size_mb': round(result.s3_total_size / 1024 / 1024, 2),
                    'time_seconds': result.s3_time
                }
            }
            
            if result.error_messages:
                company_report['error_messages'] = result.error_messages
            
            report['post_processing_report']['by_company'][company] = company_report
        
        return report


# Funciones de conveniencia

def run_post_processing_for_company(company: str, database_only: bool = False) -> PostProcessingResult:
    """
    Ejecutar post-procesamiento para una empresa específica
    
    Args:
        company: 'afinia' o 'aire'
        database_only: Si True, solo procesa base de datos (omite S3)
        
    Returns:
        Resultado del procesamiento
    """
    service = PostProcessingService()
    return service.process_company_data(company, database_only=database_only)

def run_complete_post_processing() -> IntegratedPostProcessingStats:
    """
    Ejecutar post-procesamiento completo para todas las empresas
    
    Returns:
        Estadísticas consolidadas
    """
    service = PostProcessingService()
    return service.run_integrated_post_processing()

def generate_post_processing_report() -> Dict[str, Any]:
    """
    Generar reporte completo de post-procesamiento
    
    Returns:
        Reporte estructurado
    """
    service = PostProcessingService()
    stats = service.run_integrated_post_processing()
    return service.generate_processing_report(stats)

if __name__ == "__main__":
    # Test del servicio de post-procesamiento
    logger.info("[post_processing][main] Iniciando test de post-procesamiento integral")
    
    # Ejecutar post-procesamiento completo
    stats = run_complete_post_processing()
    
    print("=" * 80)
    print("REPORTE DE POST-PROCESAMIENTO INTEGRAL")
    print("=" * 80)
    
    print(f"\nESTADO GENERAL: {'[EXITOSO] EXITOSO' if stats.success else '[ERROR] CON ERRORES'}")
    print(f"Tiempo total: {stats.total_processing_time:.2f} segundos")
    print(f"Empresas procesadas: {', '.join(stats.companies_processed)}")
    
    print(f"\nRESUMEN BASE DE DATOS:")
    print(f"  - Insertados: {stats.total_db_inserted}")
    print(f"  - Actualizados: {stats.total_db_updated}")
    print(f"  - Duplicados: {stats.total_db_duplicates}")
    print(f"  - Errores: {stats.total_db_errors}")
    
    print(f"\nRESUMEN AWS S3:")
    print(f"  - Subidos (nuevos): {stats.total_s3_uploaded}")
    print(f"  - Pre-existentes: {stats.total_s3_pre_existing}")
    print(f"  - Errores: {stats.total_s3_errors}")
    print(f"  - Tamaño total: {stats.total_s3_size_mb:.2f} MB")
    
    # Detalles por empresa
    for company, result in stats.results_by_company.items():
        print(f"\n{company.upper()} - {'[EXITOSO]' if result.success else '[ERROR]'}:")
        print(f"  - Archivos procesados: {result.total_files_processed}")
        print(f"  - Tiempo: {result.total_processing_time:.2f}s")
        
        print(f"  Base de Datos:")
        print(f"    * Insertados: {result.db_inserted}")
        print(f"    * Actualizados: {result.db_updated}")
        print(f"    * Duplicados: {result.db_duplicates}")
        print(f"    * Errores: {result.db_errors}")
        
        print(f"  AWS S3:")
        print(f"    * Subidos: {result.s3_uploaded}")
        print(f"    * Pre-existentes: {result.s3_pre_existing}")
        print(f"    * Errores: {result.s3_errors}")
        print(f"    * Tamaño: {result.s3_total_size / 1024 / 1024:.2f} MB")
        
        if result.error_messages:
            print(f"  Errores encontrados: {len(result.error_messages)}")
            for error in result.error_messages[:2]:  # Mostrar solo los primeros 2
                print(f"    - {error}")
    
    print("\n" + "=" * 80)