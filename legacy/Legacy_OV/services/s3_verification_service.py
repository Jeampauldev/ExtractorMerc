#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servicio de Verificación S3 para Extractor OV Modular
====================================================

Servicio para verificar archivos pendientes de subida a S3 comparando
registros en las tablas ov_afinia/ov_aire con registros_ov_s3.

Implementa el Paso 20 del FLUJO_VERIFICACION.md:
- Verificar salida (nuevos/duplicados) contra data_general.registros_ov_s3
- Automatizar cruce post-carga CSV→RDS con tabla S3 para confirmar pendientes de subida

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config.rds_config import RDSConnectionManager

logger = logging.getLogger(__name__)

@dataclass
class S3VerificationResult:
    """Resultado de verificación S3"""
    numero_radicado: str
    empresa: str
    fecha_registro: datetime
    estado_rds: str  # 'nuevo', 'actualizado', 'existente'
    estado_s3: str   # 'pendiente', 'subido', 'error'
    ruta_archivos: Optional[str] = None
    s3_registry_id: Optional[int] = None
    necesita_subida: bool = True

@dataclass
class S3VerificationStats:
    """Estadísticas de verificación S3"""
    total_registros_rds: int = 0
    registros_pendientes_s3: int = 0
    registros_ya_subidos: int = 0
    registros_con_error: int = 0
    archivos_encontrados: int = 0
    archivos_faltantes: int = 0
    tiempo_procesamiento: float = 0.0
    errores: List[str] = None
    
    def __post_init__(self):
        if self.errores is None:
            self.errores = []

class S3VerificationService:
    """
    Servicio para verificar archivos pendientes de subida a S3
    """
    
    def __init__(self):
        """Inicializar servicio de verificación S3"""
        self.rds_manager = RDSConnectionManager()
        logger.info("[s3_verification][init] Servicio de verificación S3 inicializado")
    
    def get_pending_uploads_for_company(self, empresa: str, 
                                      fecha_desde: Optional[datetime] = None,
                                      fecha_hasta: Optional[datetime] = None) -> List[S3VerificationResult]:
        """
        Obtener registros pendientes de subida a S3 para una empresa
        
        Args:
            empresa: 'afinia' o 'aire'
            fecha_desde: Fecha inicial para filtrar (opcional)
            fecha_hasta: Fecha final para filtrar (opcional)
            
        Returns:
            Lista de registros pendientes de subida
        """
        session = self.rds_manager.get_session()
        pending_uploads = []
        
        try:
            # Tabla RDS correspondiente
            tabla_rds = f"ov_{empresa}"
            
            # Construir query base
            base_query = f"""
                SELECT 
                    rds.numero_radicado,
                    rds.fecha_creacion,
                    rds.fecha_actualizacion,
                    rds.hash_registro,
                    s3.id as s3_registry_id,
                    s3.estado_carga as s3_estado,
                    s3.fecha_creacion as s3_fecha_carga
                FROM data_general.{tabla_rds} rds
                LEFT JOIN data_general.registros_ov_s3 s3 
                    ON rds.numero_radicado = s3.numero_reclamo_sgc 
                    AND s3.empresa = :empresa
                WHERE 1=1
            """
            
            # Agregar filtros de fecha si se especifican
            params = {'empresa': empresa}
            
            if fecha_desde:
                base_query += " AND rds.fecha_creacion >= :fecha_desde"
                params['fecha_desde'] = fecha_desde
                
            if fecha_hasta:
                base_query += " AND rds.fecha_creacion <= :fecha_hasta"
                params['fecha_hasta'] = fecha_hasta
            
            # Ordenar por fecha de creación
            base_query += " ORDER BY rds.fecha_creacion DESC"
            
            query = text(base_query)
            results = session.execute(query, params).fetchall()
            
            logger.info(f"[s3_verification][get_pending] Encontrados {len(results)} registros para {empresa}")
            
            for row in results:
                numero_radicado, fecha_creacion, fecha_actualizacion, hash_registro, s3_id, s3_estado, s3_fecha = row
                
                # Determinar estado RDS
                if fecha_actualizacion and fecha_actualizacion > fecha_creacion:
                    estado_rds = 'actualizado'
                else:
                    estado_rds = 'nuevo'
                
                # Determinar estado S3 y necesidad de subida
                if s3_id is None:
                    estado_s3 = 'pendiente'
                    necesita_subida = True
                elif s3_estado == 'subido':
                    estado_s3 = 'subido'
                    necesita_subida = False
                elif s3_estado == 'error':
                    estado_s3 = 'error'
                    necesita_subida = True
                else:
                    estado_s3 = 'pendiente'
                    necesita_subida = True
                
                # Verificar si existen archivos locales
                ruta_archivos = self._get_local_files_path(empresa, numero_radicado)
                
                pending_uploads.append(S3VerificationResult(
                    numero_radicado=numero_radicado,
                    empresa=empresa,
                    fecha_registro=fecha_creacion,
                    estado_rds=estado_rds,
                    estado_s3=estado_s3,
                    ruta_archivos=ruta_archivos,
                    s3_registry_id=s3_id,
                    necesita_subida=necesita_subida
                ))
            
            return pending_uploads
            
        except Exception as e:
            logger.error(f"[s3_verification][get_pending] Error obteniendo registros pendientes para {empresa}: {e}")
            return []
        finally:
            session.close()
    
    def verify_s3_status_after_rds_load(self, empresa: str, 
                                       load_stats: Dict[str, Any]) -> S3VerificationStats:
        """
        Verificar estado S3 después de una carga RDS
        
        Args:
            empresa: 'afinia' o 'aire'
            load_stats: Estadísticas de la carga RDS (insertados, actualizados, etc.)
            
        Returns:
            Estadísticas de verificación S3
        """
        start_time = datetime.now()
        stats = S3VerificationStats()
        
        try:
            logger.info(f"[s3_verification][verify_after_load] Verificando estado S3 para {empresa}")
            
            # Obtener registros recientes (últimas 24 horas por defecto)
            fecha_desde = datetime.now() - timedelta(hours=24)
            pending_uploads = self.get_pending_uploads_for_company(empresa, fecha_desde=fecha_desde)
            
            stats.total_registros_rds = len(pending_uploads)
            
            for upload in pending_uploads:
                if upload.necesita_subida:
                    stats.registros_pendientes_s3 += 1
                    
                    # Verificar si existen archivos locales
                    if upload.ruta_archivos and Path(upload.ruta_archivos).exists():
                        stats.archivos_encontrados += 1
                    else:
                        stats.archivos_faltantes += 1
                        stats.errores.append(f"Archivos no encontrados para {upload.numero_radicado}")
                        
                elif upload.estado_s3 == 'subido':
                    stats.registros_ya_subidos += 1
                elif upload.estado_s3 == 'error':
                    stats.registros_con_error += 1
            
            stats.tiempo_procesamiento = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"[s3_verification][verify_after_load] Completado para {empresa}: "
                       f"{stats.registros_pendientes_s3} pendientes, "
                       f"{stats.registros_ya_subidos} ya subidos, "
                       f"{stats.registros_con_error} con error")
            
            return stats
            
        except Exception as e:
            error_msg = f"Error verificando estado S3 para {empresa}: {e}"
            logger.error(f"[s3_verification][verify_after_load] {error_msg}")
            stats.errores.append(error_msg)
            stats.tiempo_procesamiento = (datetime.now() - start_time).total_seconds()
            return stats
    
    def get_files_to_upload(self, empresa: str, 
                           limite: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtener lista de archivos listos para subir a S3
        
        Args:
            empresa: 'afinia' o 'aire'
            limite: Límite de archivos a retornar (opcional)
            
        Returns:
            Lista de archivos con información para subida
        """
        pending_uploads = self.get_pending_uploads_for_company(empresa)
        files_to_upload = []
        
        if not pending_uploads:
            logger.info(f"[s3_verification][get_files_to_upload] No hay registros pendientes para {empresa}")
            return files_to_upload
        
        # Directorio base donde están los archivos procesados
        base_path = Path(f"data/downloads/{empresa}/oficina_virtual/processed")
        
        if not base_path.exists():
            logger.error(f"[s3_verification][get_files_to_upload] Directorio no existe: {base_path}")
            return files_to_upload
        
        # Crear un mapeo de numero_radicado -> sgc_number leyendo archivos JSON
        radicado_to_sgc = {}
        json_files = list(base_path.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    
                    numero_radicado = data.get('numero_radicado')
                    sgc_number = data.get('sgc_number') or data.get('numero_reclamo_sgc')
                    
                    if numero_radicado and sgc_number:
                        radicado_to_sgc[numero_radicado] = sgc_number
                        
            except Exception as e:
                logger.debug(f"[s3_verification][get_files_to_upload] Error leyendo {json_file}: {e}")
                continue
        
        logger.debug(f"[s3_verification][get_files_to_upload] Mapeo radicado->SGC: {len(radicado_to_sgc)} registros")
        
        for upload in pending_uploads:
            if not upload.necesita_subida:
                continue
                
            numero_radicado = upload.numero_radicado
            
            # Obtener el SGC correspondiente
            sgc_number = radicado_to_sgc.get(numero_radicado)
            
            if not sgc_number:
                logger.warning(f"[s3_verification][get_files_to_upload] No se encontró SGC para radicado {numero_radicado}")
                continue
            
            # Verificar si existe la ruta de archivos
            if not upload.ruta_archivos:
                logger.warning(f"[s3_verification][get_files_to_upload] Sin ruta_archivos para {numero_radicado}")
                continue
            
            # Buscar archivos relacionados con este SGC
            archivos_encontrados = []
            
            # Buscar archivos con el patrón sgc_number_*
            # Extensiones comunes: json, pdf, jpg, jpeg, png, docx, doc
            extensiones = ['json', 'pdf', 'jpg', 'jpeg', 'png', 'docx', 'doc']
            
            for ext in extensiones:
                pattern = f"{sgc_number}_*.{ext}"
                matching_files = list(base_path.glob(pattern))
                archivos_encontrados.extend(matching_files)
            
            if archivos_encontrados:
                for archivo in archivos_encontrados:
                    files_to_upload.append({
                        'numero_radicado': numero_radicado,
                        'sgc_number': sgc_number,
                        'file_path': str(archivo),
                        'file_name': archivo.name,
                        'ruta_archivos': upload.ruta_archivos,
                        'empresa': empresa
                    })
                
                logger.debug(f"[s3_verification][get_files_to_upload] Encontrados {len(archivos_encontrados)} "
                           f"archivos para {numero_radicado} (SGC: {sgc_number}): {[f.name for f in archivos_encontrados]}")
            else:
                logger.warning(f"[s3_verification][get_files_to_upload] Archivos no encontrados para "
                             f"{numero_radicado} (SGC: {sgc_number})")
            
            # Aplicar límite si se especifica
            if limite and len(files_to_upload) >= limite:
                break
        
        logger.info(f"[s3_verification][get_files_to_upload] Total archivos para subir: {len(files_to_upload)}")
        return files_to_upload
    
    def _get_local_files_path(self, empresa: str, numero_radicado: str) -> Optional[str]:
        """
        Obtener ruta local de archivos para un número de radicado
        
        Args:
            empresa: 'afinia' o 'aire'
            numero_radicado: Número de radicado
            
        Returns:
            Ruta del directorio donde están los archivos o None si no existe
        """
        import glob
        
        # Directorio base donde están los archivos procesados
        base_dir = Path(f"data/downloads/{empresa}/oficina_virtual/processed")
        
        if not base_dir.exists():
            logger.warning(f"[s3_verification][_get_local_files_path] Directorio no existe: {base_dir}")
            return None
        
        # Buscar archivos JSON que contengan este numero_radicado
        json_files = list(base_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    
                    # Verificar si este archivo contiene el numero_radicado buscado
                    if data.get('numero_radicado') == numero_radicado:
                        # Extraer el sgc_number para buscar archivos relacionados
                        sgc_number = data.get('sgc_number') or data.get('numero_reclamo_sgc')
                        
                        if sgc_number:
                            logger.debug(f"[s3_verification][_get_local_files_path] Encontrado {numero_radicado} "
                                       f"en archivo {json_file.name}, SGC: {sgc_number}")
                            return str(base_dir)
                        
            except Exception as e:
                logger.debug(f"[s3_verification][_get_local_files_path] Error leyendo {json_file}: {e}")
                continue
        
        # Fallback: verificar estructuras de directorios originales
        possible_paths = [
            f"data/downloads/{empresa}/oficina_virtual/processed/{numero_radicado}",
            f"data/downloads/{empresa}/oficina_virtual/{numero_radicado}"
        ]
        
        for path_str in possible_paths:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                logger.debug(f"[s3_verification][_get_local_files_path] Encontrado directorio: {path}")
                return str(path)
        
        logger.warning(f"[s3_verification][_get_local_files_path] No se encontraron archivos "
                      f"para numero_radicado {numero_radicado} en {empresa}")
        return None
    
    def generate_verification_report(self, empresa: str = None) -> Dict[str, Any]:
        """
        Generar reporte completo de verificación S3
        
        Args:
            empresa: Empresa específica o None para todas
            
        Returns:
            Reporte de verificación
        """
        start_time = datetime.now()
        report = {
            'timestamp': start_time.isoformat(),
            'empresas': {},
            'resumen_total': {
                'total_registros': 0,
                'pendientes_subida': 0,
                'ya_subidos': 0,
                'con_error': 0,
                'archivos_encontrados': 0,
                'archivos_faltantes': 0
            }
        }
        
        empresas_a_verificar = [empresa] if empresa else ['afinia', 'aire']
        
        for emp in empresas_a_verificar:
            logger.info(f"[s3_verification][generate_report] Generando reporte para {emp}")
            
            stats = self.verify_s3_status_after_rds_load(emp, {})
            
            report['empresas'][emp] = {
                'total_registros': stats.total_registros_rds,
                'pendientes_subida': stats.registros_pendientes_s3,
                'ya_subidos': stats.registros_ya_subidos,
                'con_error': stats.registros_con_error,
                'archivos_encontrados': stats.archivos_encontrados,
                'archivos_faltantes': stats.archivos_faltantes,
                'tiempo_procesamiento': stats.tiempo_procesamiento,
                'errores': stats.errores
            }
            
            # Actualizar totales
            report['resumen_total']['total_registros'] += stats.total_registros_rds
            report['resumen_total']['pendientes_subida'] += stats.registros_pendientes_s3
            report['resumen_total']['ya_subidos'] += stats.registros_ya_subidos
            report['resumen_total']['con_error'] += stats.registros_con_error
            report['resumen_total']['archivos_encontrados'] += stats.archivos_encontrados
            report['resumen_total']['archivos_faltantes'] += stats.archivos_faltantes
        
        report['tiempo_total'] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"[s3_verification][generate_report] Reporte completado: "
                   f"{report['resumen_total']['pendientes_subida']} archivos pendientes de subida")
        
        return report


# Funciones de conveniencia

def verify_s3_status_for_company(empresa: str) -> S3VerificationStats:
    """
    Verificar estado S3 para una empresa específica
    
    Args:
        empresa: 'afinia' o 'aire'
        
    Returns:
        Estadísticas de verificación
    """
    service = S3VerificationService()
    return service.verify_s3_status_after_rds_load(empresa, {})

def get_pending_s3_uploads(empresa: str = None, limite: int = None) -> Dict[str, List[Dict]]:
    """
    Obtener archivos pendientes de subida a S3
    
    Args:
        empresa: Empresa específica o None para todas
        limite: Límite de archivos por empresa
        
    Returns:
        Diccionario con archivos pendientes por empresa
    """
    service = S3VerificationService()
    results = {}
    
    empresas_a_verificar = [empresa] if empresa else ['afinia', 'aire']
    
    for emp in empresas_a_verificar:
        results[emp] = service.get_files_to_upload(emp, limite)
    
    return results

def generate_s3_verification_report(empresa: str = None) -> Dict[str, Any]:
    """
    Generar reporte completo de verificación S3
    
    Args:
        empresa: Empresa específica o None para todas
        
    Returns:
        Reporte de verificación
    """
    service = S3VerificationService()
    return service.generate_verification_report(empresa)


if __name__ == "__main__":
    # Test del servicio de verificación S3
    logger.info("[s3_verification][main] Iniciando test de verificación S3")
    
    # Generar reporte completo
    report = generate_s3_verification_report()
    
    print("=" * 70)
    print("REPORTE DE VERIFICACIÓN S3")
    print("=" * 70)
    
    print(f"\nTimestamp: {report['timestamp']}")
    print(f"Tiempo total de procesamiento: {report['tiempo_total']:.2f}s")
    
    # Resumen total
    resumen = report['resumen_total']
    print(f"\nRESUMEN TOTAL:")
    print(f"  - Total registros en RDS: {resumen['total_registros']}")
    print(f"  - Pendientes de subida a S3: {resumen['pendientes_subida']}")
    print(f"  - Ya subidos a S3: {resumen['ya_subidos']}")
    print(f"  - Con errores: {resumen['con_error']}")
    print(f"  - Archivos encontrados localmente: {resumen['archivos_encontrados']}")
    print(f"  - Archivos faltantes: {resumen['archivos_faltantes']}")
    
    # Detalles por empresa
    for empresa, stats in report['empresas'].items():
        print(f"\n{empresa.upper()}:")
        print(f"  - Registros en RDS: {stats['total_registros']}")
        print(f"  - Pendientes S3: {stats['pendientes_subida']}")
        print(f"  - Ya subidos: {stats['ya_subidos']}")
        print(f"  - Con error: {stats['con_error']}")
        print(f"  - Archivos encontrados: {stats['archivos_encontrados']}")
        print(f"  - Archivos faltantes: {stats['archivos_faltantes']}")
        print(f"  - Tiempo procesamiento: {stats['tiempo_procesamiento']:.2f}s")
        
        if stats['errores']:
            print(f"  - Errores encontrados: {len(stats['errores'])}")
            for error in stats['errores'][:3]:  # Mostrar solo los primeros 3
                print(f"    * {error}")
    
    print("\n" + "=" * 70)