#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para probar las correcciones de rutas y descarga de adjuntos
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Cargar variables de entorno
env_path = project_root / 'p16_env' / '.env'
load_dotenv(env_path)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('test_correcciones')

async def test_correcciones():
    """Prueba las correcciones implementadas"""
    try:
        logger.info("=== PROBANDO CORRECCIONES PQR ===")
        
        # Configurar variables de entorno
        os.environ['ENABLE_PQR_PROCESSING'] = 'true'
        os.environ['MAX_PQR_RECORDS'] = '2'  # Solo 2 para prueba rápida
        
        # Verificar credenciales
        username = os.getenv('OV_AFINIA_USERNAME')
        password = os.getenv('OV_AFINIA_PASSWORD')
        
        if not username or not password:
            logger.error("[ERROR] Credenciales no encontradas")
            return False
        
        logger.info(f"[EXITOSO] Credenciales disponibles: {username[:3]}***")
        
        # Importar y crear extractor
        from src.extractors.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular
        
        logger.info("[CONFIGURANDO] Creando extractor con correcciones...")
        extractor = OficinaVirtualAfiniaModular(
            headless=False,  # Modo visual para observar
            visual_mode=True,
            enable_pqr_processing=True,
            max_pqr_records=2
        )
        
        # Ejecutar extracción
        logger.info("[INICIANDO] Ejecutando extracción con correcciones...")
        start_time = datetime.now()
        
        result = await extractor.run_full_extraction(
            username=username,
            password=password
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Verificar resultados
        logger.info("[DATOS] RESULTADOS:")
        logger.info(f"   [TIEMPO] Tiempo: {execution_time:.2f} segundos")
        logger.info(f"   [EXITOSO] Éxito: {result.get('success', False)}")
        
        if result.get('success'):
            logger.info(f"   [EMOJI_REMOVIDO] Archivos descargados: {result.get('files_downloaded', 0)}")
            logger.info(f"   [EMOJI_REMOVIDO] PQR procesados: {result.get('pqr_processed', 0)}")
            
            # Verificar archivos en la ruta correcta
            await verificar_archivos_en_ruta_correcta()
            
            return True
        else:
            logger.error(f"[ERROR] Error: {result.get('error', 'Error desconocido')}")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Error en prueba: {e}")
        return False

async def verificar_archivos_en_ruta_correcta():
    """Verifica que los archivos se generen en la ruta correcta del proyecto"""
    logger.info("=== VERIFICANDO ARCHIVOS EN RUTA CORRECTA ===")
    
    # Ruta correcta dentro del proyecto
    project_root = Path(__file__).parent
    correct_path = project_root / "m_downloads_13" / "afinia" / "oficina_virtual" / "processed"
    
    logger.info(f"[EMOJI_REMOVIDO] Ruta correcta esperada: {correct_path.absolute()}")
    logger.info(f"[EMOJI_REMOVIDO] Ruta existe: {correct_path.exists()}")
    
    if correct_path.exists():
        # Buscar archivos de hoy
        today = datetime.now().strftime("%Y%m%d")
        
        pdf_files = list(correct_path.glob(f"*{today}*.pdf"))
        json_files = list(correct_path.glob(f"*{today}*.json"))
        adjunto_files = list(correct_path.glob(f"*adjunto*{today}*"))
        
        logger.info(f"[ARCHIVO] PDFs de hoy: {len(pdf_files)}")
        for pdf in pdf_files[-3:]:  # Mostrar últimos 3
            logger.info(f"   - {pdf.name} ({pdf.stat().st_size} bytes)")
        
        logger.info(f"[EMOJI_REMOVIDO] JSONs de hoy: {len(json_files)}")
        for json_file in json_files[-3:]:  # Mostrar últimos 3
            logger.info(f"   - {json_file.name} ({json_file.stat().st_size} bytes)")
        
        logger.info(f"[EMOJI_REMOVIDO] Adjuntos de hoy: {len(adjunto_files)}")
        for adjunto in adjunto_files:
            logger.info(f"   - {adjunto.name} ({adjunto.stat().st_size} bytes)")
        
        if pdf_files or json_files:
            logger.info("[EXITOSO] CORRECCIÓN DE RUTA: FUNCIONANDO")
        else:
            logger.warning("[ADVERTENCIA] No se encontraron archivos de hoy en la ruta correcta")
            
        if adjunto_files:
            logger.info("[EXITOSO] DESCARGA DE ADJUNTOS: FUNCIONANDO")
        else:
            logger.info("[INFO] No se encontraron adjuntos (puede ser normal si no hay adjuntos en los PQR)")
    else:
        logger.error("[ERROR] La ruta correcta no existe")
    
    # Verificar si hay archivos en la ruta incorrecta (fuera del proyecto)
    incorrect_path = Path("C:/00_Project_Dev/m_downloads_13/afinia/oficina_virtual/processed")
    if incorrect_path.exists():
        incorrect_files = list(incorrect_path.glob("*"))
        if incorrect_files:
            logger.warning(f"[ADVERTENCIA] Se encontraron {len(incorrect_files)} archivos en ruta incorrecta: {incorrect_path}")
            logger.info("[INFO] Esto indica que la corrección de ruta puede necesitar ajustes")
        else:
            logger.info("[EXITOSO] No hay archivos en la ruta incorrecta")

async def main():
    """Función principal"""
    logger.info("🧪 INICIANDO PRUEBA DE CORRECCIONES")
    logger.info("=" * 50)
    
    success = await test_correcciones()
    
    logger.info("\n" + "=" * 50)
    if success:
        logger.info("[COMPLETADO] PRUEBA EXITOSA - Correcciones funcionando")
    else:
        logger.error("[ERROR] PRUEBA FALLIDA - Revisar correcciones")
    
    return success

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
