#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de Subida S3 Filtrada para Extractor OV Modular
========================================================

Servicio para subir archivos a S3 de manera filtrada, procesando solo
registros no duplicados identificados por el S3VerificationService.

Implementa el Paso 21 del FLUJO_VERIFICACION.md:
- Subida S3 filtrada solo para registros no duplicados
- Integración con S3UploaderService existente
- Control de duplicados y manejo de errores

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import time

from src.services.s3_verification_service import S3VerificationService, S3VerificationResult
from src.services.unified_s3_service import UnifiedS3Service, S3PathStructure

logger = logging.getLogger(__name__)

@dataclass
class FilteredUploadResult:
    """Resultado de subida filtrada"""
    numero_radicado: str
    empresa: str
    archivos_procesados: int = 0
    archivos_subidos: int = 0
    archivos_fallidos: int = 0
    bytes_subidos: int = 0
    tiempo_procesamiento: float = 0.0
    s3_registry_id: Optional[int] = None
    estado: str = 'pendiente'  # 'completado', 'parcial', 'fallido', 'omitido'
    errores: List[str] = None
    
    def __post_init__(self):
        if self.errores is None:
            self.errores = []

@dataclass
class FilteredUploadStats:
    """Estadísticas de subida filtrada"""
    total_candidatos: int = 0
    registros_procesados: int = 0
    registros_omitidos: int = 0
    registros_completados: int = 0
    registros_parciales: int = 0
    registros_fallidos: int = 0
    archivos_subidos: int = 0
    bytes_totales: int = 0
    tiempo_total: float = 0.0
    errores_globales: List[str] = None
    
    def __post_init__(self):
        if self.errores_globales is None:
            self.errores_globales = []

class FilteredS3Uploader:
    """
    Servicio para subida filtrada de archivos a S3
    """
    
    def __init__(self, simulated_mode: bool = False):
        """
        Inicializar servicio de subida filtrada
        
        Args:
            simulated_mode: Si True, simula las subidas sin ejecutarlas
        """
        self.verification_service = S3VerificationService()
        self.s3_uploader = UnifiedS3Service(path_structure=S3PathStructure.CENTRAL)
        self.simulated_mode = simulated_mode
        
        logger.info(f"[filtered_s3_uploader][init] Servicio inicializado "
                   f"(modo simulado: {simulated_mode})")
    
    def upload_pending_files_for_company(self, empresa: str,
                                       limite_archivos: Optional[int] = None,
                                       limite_registros: Optional[int] = None) -> FilteredUploadStats:
        """
        Subir archivos pendientes para una empresa específica
        
        Args:
            empresa: 'afinia' o 'aire'
            limite_archivos: Límite de archivos por registro (opcional)
            limite_registros: Límite de registros a procesar (opcional)
            
        Returns:
            Estadísticas de la subida filtrada
        """
        start_time = datetime.now()
        stats = FilteredUploadStats()
        
        try:
            logger.info(f"[filtered_s3_uploader][upload_company] Iniciando subida filtrada para {empresa}")
            
            # Obtener archivos pendientes de subida
            files_to_upload = self.verification_service.get_files_to_upload(
                empresa, limite=limite_registros
            )
            
            stats.total_candidatos = len(files_to_upload)
            
            if not files_to_upload:
                logger.info(f"[filtered_s3_uploader][upload_company] No hay archivos pendientes para {empresa}")
                stats.tiempo_total = (datetime.now() - start_time).total_seconds()
                return stats
            
            logger.info(f"[filtered_s3_uploader][upload_company] Procesando {len(files_to_upload)} "
                       f"registros para {empresa}")
            
            # Procesar cada registro
            for file_info in files_to_upload:
                try:
                    result = self._upload_single_record(file_info, limite_archivos)
                    
                    stats.registros_procesados += 1
                    stats.archivos_subidos += result.archivos_subidos
                    stats.bytes_totales += result.bytes_subidos
                    
                    if result.estado == 'completado':
                        stats.registros_completados += 1
                    elif result.estado == 'parcial':
                        stats.registros_parciales += 1
                    elif result.estado == 'fallido':
                        stats.registros_fallidos += 1
                    elif result.estado == 'omitido':
                        stats.registros_omitidos += 1
                    
                    # Agregar errores específicos del registro
                    if result.errores:
                        stats.errores_globales.extend(result.errores)
                    
                    # Log de progreso cada 10 registros
                    if stats.registros_procesados % 10 == 0:
                        logger.info(f"[filtered_s3_uploader][upload_company] Progreso: "
                                   f"{stats.registros_procesados}/{stats.total_candidatos} registros")
                
                except Exception as e:
                    error_msg = f"Error procesando registro {file_info.get('numero_radicado', 'unknown')}: {e}"
                    logger.error(f"[filtered_s3_uploader][upload_company] {error_msg}")
                    stats.errores_globales.append(error_msg)
                    stats.registros_fallidos += 1
            
            stats.tiempo_total = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"[filtered_s3_uploader][upload_company] Completado para {empresa}: "
                       f"{stats.registros_completados} completados, "
                       f"{stats.registros_parciales} parciales, "
                       f"{stats.registros_fallidos} fallidos, "
                       f"{stats.archivos_subidos} archivos subidos")
            
            return stats
            
        except Exception as e:
            error_msg = f"Error en subida filtrada para {empresa}: {e}"
            logger.error(f"[filtered_s3_uploader][upload_company] {error_msg}")
            stats.errores_globales.append(error_msg)
            stats.tiempo_total = (datetime.now() - start_time).total_seconds()
            return stats
    
    def _upload_single_record(self, file_info: Dict[str, Any], 
                            limite_archivos: Optional[int] = None) -> FilteredUploadResult:
        """
        Subir archivos de un solo registro
        
        Args:
            file_info: Información del registro y archivos
            limite_archivos: Límite de archivos a subir
            
        Returns:
            Resultado de la subida del registro
        """
        start_time = datetime.now()
        numero_radicado = file_info['numero_radicado']
        empresa = file_info['empresa']
        
        # Manejar tanto el formato nuevo (file_path) como el antiguo (archivos)
        if 'file_path' in file_info:
            # Formato nuevo: un archivo por registro
            archivos = [file_info['file_path']]
        elif 'archivos' in file_info:
            # Formato antiguo: lista de archivos
            archivos = file_info['archivos']
        else:
            # Sin archivos
            archivos = []
        
        result = FilteredUploadResult(
            numero_radicado=numero_radicado,
            empresa=empresa,
            s3_registry_id=file_info.get('s3_registry_id')
        )
        
        try:
            # Aplicar límite de archivos si se especifica
            if limite_archivos and len(archivos) > limite_archivos:
                archivos = archivos[:limite_archivos]
                logger.info(f"[filtered_s3_uploader][upload_single] Limitando a {limite_archivos} "
                           f"archivos para {numero_radicado}")
            
            result.archivos_procesados = len(archivos)
            
            # Verificar que no esté ya subido (doble verificación)
            if self._is_already_uploaded(empresa, numero_radicado):
                result.estado = 'omitido'
                result.errores.append("Registro ya subido a S3")
                logger.info(f"[filtered_s3_uploader][upload_single] Omitiendo {numero_radicado} "
                           f"(ya subido)")
                return result
            
            # Subir archivos usando el S3UploaderService
            upload_results = []
            
            for archivo_path in archivos:
                try:
                    archivo = Path(archivo_path)
                    
                    if not archivo.exists():
                        result.errores.append(f"Archivo no encontrado: {archivo_path}")
                        result.archivos_fallidos += 1
                        continue
                    
                    # Usar el método upload_file_with_registry del AWSS3Service
                    upload_result = self.s3_uploader.upload_file_with_registry(
                        file_path=archivo,
                        empresa=empresa,
                        numero_reclamo_sgc=numero_radicado
                    )
                    
                    if upload_result and upload_result.success:
                        result.archivos_subidos += 1
                        result.bytes_subidos += archivo.stat().st_size
                        upload_results.append(upload_result)
                        
                        logger.debug(f"[filtered_s3_uploader][upload_single] Subido: {archivo.name} "
                                    f"para {numero_radicado}")
                    else:
                        result.archivos_fallidos += 1
                        error_msg = f"Fallo subiendo {archivo.name}"
                        if upload_result and upload_result.error_message:
                            error_msg += f": {upload_result.error_message}"
                        result.errores.append(error_msg)
                
                except Exception as e:
                    result.archivos_fallidos += 1
                    result.errores.append(f"Error subiendo {archivo_path}: {e}")
                    logger.error(f"[filtered_s3_uploader][upload_single] Error subiendo {archivo_path}: {e}")
            
            # Determinar estado final
            if result.archivos_subidos == result.archivos_procesados:
                result.estado = 'completado'
            elif result.archivos_subidos > 0:
                result.estado = 'parcial'
            else:
                result.estado = 'fallido'
            
            result.tiempo_procesamiento = (datetime.now() - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            result.estado = 'fallido'
            result.errores.append(f"Error general: {e}")
            result.tiempo_procesamiento = (datetime.now() - start_time).total_seconds()
            logger.error(f"[filtered_s3_uploader][upload_single] Error procesando {numero_radicado}: {e}")
            return result
    
    def _is_already_uploaded(self, empresa: str, numero_radicado: str) -> bool:
        """
        Verificar si un registro ya está subido a S3
        
        Args:
            empresa: Empresa
            numero_radicado: Número de radicado
            
        Returns:
            True si ya está subido
        """
        try:
            # Usar el verification service para verificar estado
            pending_uploads = self.verification_service.get_pending_uploads_for_company(empresa)
            
            for upload in pending_uploads:
                if (upload.numero_radicado == numero_radicado and 
                    not upload.necesita_subida):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"[filtered_s3_uploader][is_already_uploaded] Error verificando {numero_radicado}: {e}")
            return False
    
    def upload_all_pending_files(self, limite_por_empresa: Optional[int] = None) -> Dict[str, FilteredUploadStats]:
        """
        Subir archivos pendientes para todas las empresas
        
        Args:
            limite_por_empresa: Límite de registros por empresa
            
        Returns:
            Estadísticas por empresa
        """
        results = {}
        
        for empresa in ['afinia', 'aire']:
            logger.info(f"[filtered_s3_uploader][upload_all] Procesando {empresa}")
            
            try:
                stats = self.upload_pending_files_for_company(
                    empresa, limite_registros=limite_por_empresa
                )
                results[empresa] = stats
                
            except Exception as e:
                logger.error(f"[filtered_s3_uploader][upload_all] Error procesando {empresa}: {e}")
                stats = FilteredUploadStats()
                stats.errores_globales.append(f"Error procesando {empresa}: {e}")
                results[empresa] = stats
        
        return results
    
    def generate_upload_report(self, stats_by_company: Dict[str, FilteredUploadStats]) -> Dict[str, Any]:
        """
        Generar reporte de subida filtrada
        
        Args:
            stats_by_company: Estadísticas por empresa
            
        Returns:
            Reporte completo
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'modo_simulado': self.simulated_mode,
            'empresas': {},
            'resumen_total': {
                'total_candidatos': 0,
                'registros_procesados': 0,
                'registros_completados': 0,
                'registros_parciales': 0,
                'registros_fallidos': 0,
                'registros_omitidos': 0,
                'archivos_subidos': 0,
                'bytes_totales': 0,
                'tiempo_total': 0.0,
                'errores_totales': 0
            }
        }
        
        for empresa, stats in stats_by_company.items():
            report['empresas'][empresa] = asdict(stats)
            
            # Actualizar totales
            totales = report['resumen_total']
            totales['total_candidatos'] += stats.total_candidatos
            totales['registros_procesados'] += stats.registros_procesados
            totales['registros_completados'] += stats.registros_completados
            totales['registros_parciales'] += stats.registros_parciales
            totales['registros_fallidos'] += stats.registros_fallidos
            totales['registros_omitidos'] += stats.registros_omitidos
            totales['archivos_subidos'] += stats.archivos_subidos
            totales['bytes_totales'] += stats.bytes_totales
            totales['tiempo_total'] += stats.tiempo_total
            totales['errores_totales'] += len(stats.errores_globales)
        
        return report


# Funciones de conveniencia

def upload_pending_files(empresa: str = None, 
                        limite_registros: int = None,
                        simulated_mode: bool = False) -> Dict[str, Any]:
    """
    Subir archivos pendientes de manera filtrada
    
    Args:
        empresa: Empresa específica o None para todas
        limite_registros: Límite de registros por empresa
        simulated_mode: Modo simulado
        
    Returns:
        Reporte de subida
    """
    uploader = FilteredS3Uploader(simulated_mode=simulated_mode)
    
    if empresa:
        stats = uploader.upload_pending_files_for_company(empresa, limite_registros=limite_registros)
        stats_by_company = {empresa: stats}
    else:
        stats_by_company = uploader.upload_all_pending_files(limite_por_empresa=limite_registros)
    
    return uploader.generate_upload_report(stats_by_company)

def test_filtered_upload(empresa: str = 'afinia', limite: int = 5) -> Dict[str, Any]:
    """
    Probar subida filtrada en modo simulado
    
    Args:
        empresa: Empresa a probar
        limite: Límite de registros
        
    Returns:
        Reporte de prueba
    """
    return upload_pending_files(empresa=empresa, limite_registros=limite, simulated_mode=True)


if __name__ == "__main__":
    # Test del servicio de subida filtrada
    logger.info("[filtered_s3_uploader][main] Iniciando test de subida filtrada")
    
    # Ejecutar en modo simulado
    print("=" * 70)
    print("TEST DE SUBIDA S3 FILTRADA (MODO SIMULADO)")
    print("=" * 70)
    
    report = test_filtered_upload(empresa='afinia', limite=3)
    
    print(f"\nTimestamp: {report['timestamp']}")
    print(f"Modo simulado: {report['modo_simulado']}")
    
    # Resumen total
    resumen = report['resumen_total']
    print(f"\nRESUMEN TOTAL:")
    print(f"  - Candidatos encontrados: {resumen['total_candidatos']}")
    print(f"  - Registros procesados: {resumen['registros_procesados']}")
    print(f"  - Completados: {resumen['registros_completados']}")
    print(f"  - Parciales: {resumen['registros_parciales']}")
    print(f"  - Fallidos: {resumen['registros_fallidos']}")
    print(f"  - Omitidos: {resumen['registros_omitidos']}")
    print(f"  - Archivos subidos: {resumen['archivos_subidos']}")
    print(f"  - Bytes totales: {resumen['bytes_totales']:,}")
    print(f"  - Tiempo total: {resumen['tiempo_total']:.2f}s")
    print(f"  - Errores totales: {resumen['errores_totales']}")
    
    # Detalles por empresa
    for empresa, stats in report['empresas'].items():
        print(f"\n{empresa.upper()}:")
        print(f"  - Candidatos: {stats['total_candidatos']}")
        print(f"  - Procesados: {stats['registros_procesados']}")
        print(f"  - Completados: {stats['registros_completados']}")
        print(f"  - Archivos subidos: {stats['archivos_subidos']}")
        print(f"  - Tiempo: {stats['tiempo_total']:.2f}s")
        
        if stats['errores_globales']:
            print(f"  - Errores: {len(stats['errores_globales'])}")
            for error in stats['errores_globales'][:3]:
                print(f"    * {error}")
    
    print("\n" + "=" * 70)