#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para probar la descarga de adjuntos específicos del campo documento_prueba
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

logger = logging.getLogger('test_adjuntos_especificos')

async def test_adjuntos_especificos():
    """Prueba la descarga de adjuntos específicos"""
    try:
        logger.info("=== PROBANDO DESCARGA DE ADJUNTOS ESPECÍFICOS ===")
        
        # Configurar variables de entorno
        os.environ['ENABLE_PQR_PROCESSING'] = 'true'
        os.environ['MAX_PQR_RECORDS'] = '3'  # 3 registros para tener más oportunidades de encontrar adjuntos
        
        # Verificar credenciales
        username = os.getenv('OV_AFINIA_USERNAME')
        password = os.getenv('OV_AFINIA_PASSWORD')
        
        if not username or not password:
            logger.error("[ERROR] Credenciales no encontradas")
            return False
        
        logger.info(f"[EXITOSO] Credenciales disponibles: {username[:3]}***")
        
        # Importar y crear extractor
        from src.extractors.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular
        
        logger.info("[CONFIGURANDO] Creando extractor para probar adjuntos específicos...")
        extractor = OficinaVirtualAfiniaModular(
            headless=False,  # Modo visual para observar
            visual_mode=True,
            enable_pqr_processing=True,
            max_pqr_records=3
        )
        
        # Ejecutar extracción
        logger.info("[INICIANDO] Ejecutando extracción con foco en adjuntos...")
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
            
            # Verificar adjuntos específicos
            await verificar_adjuntos_especificos()
            
            return True
        else:
            logger.error(f"[ERROR] Error: {result.get('error', 'Error desconocido')}")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Error en prueba: {e}")
        return False

async def verificar_adjuntos_especificos():
    """Verifica que se descargaron adjuntos específicos con el formato correcto"""
    logger.info("=== VERIFICANDO ADJUNTOS ESPECÍFICOS ===")
    
    # Ruta donde deben estar los archivos
    project_root = Path(__file__).parent
    processed_path = project_root / "m_downloads_13" / "afinia" / "oficina_virtual" / "processed"
    
    logger.info(f"[EMOJI_REMOVIDO] Verificando en: {processed_path.absolute()}")
    
    if processed_path.exists():
        # Buscar archivos de hoy
        today = datetime.now().strftime("%Y%m%d")
        
        # Buscar archivos con patrón de adjuntos específicos
        all_files = list(processed_path.glob(f"*{today}*"))
        pdf_files = [f for f in all_files if f.suffix.lower() == '.pdf' and '_adjunto_' not in f.name]
        json_files = [f for f in all_files if f.suffix.lower() == '.json']
        adjunto_files = [f for f in all_files if '_adjunto_' in f.name]
        
        logger.info(f"[ARCHIVO] PDFs principales de hoy: {len(pdf_files)}")
        for pdf in pdf_files[-3:]:
            logger.info(f"   - {pdf.name} ({pdf.stat().st_size} bytes)")
        
        logger.info(f"[EMOJI_REMOVIDO] JSONs de hoy: {len(json_files)}")
        for json_file in json_files[-3:]:
            logger.info(f"   - {json_file.name} ({json_file.stat().st_size} bytes)")
        
        logger.info(f"[EMOJI_REMOVIDO] ADJUNTOS ESPECÍFICOS de hoy: {len(adjunto_files)}")
        
        adjuntos_correctos = 0
        adjuntos_incorrectos = 0
        
        for adjunto in adjunto_files:
            logger.info(f"   [EMOJI_REMOVIDO] {adjunto.name} ({adjunto.stat().st_size} bytes)")
            
            # Verificar formato del nombre
            if '_adjunto_' in adjunto.name and not '_adjunto_pagina_' in adjunto.name:
                # Formato correcto: SGC_adjunto_timestamp.extension_original
                adjuntos_correctos += 1
                logger.info(f"      [EXITOSO] Formato correcto - Adjunto específico")
                
                # Verificar que no sea PDF (a menos que el original sea PDF)
                if adjunto.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx', '.txt', '.zip', '.rar']:
                    logger.info(f"      [EXITOSO] Extensión original mantenida: {adjunto.suffix}")
                elif adjunto.suffix.lower() == '.pdf':
                    logger.info(f"      [INFO] PDF - puede ser original o conversión")
            else:
                # Formato incorrecto (probablemente conversión a PDF de página)
                adjuntos_incorrectos += 1
                logger.info(f"      [ADVERTENCIA] Formato incorrecto - Conversión de página")
        
        # Analizar JSONs para ver qué archivos se esperaban
        logger.info("\n[EMOJI_REMOVIDO] ANÁLISIS DE ARCHIVOS ESPERADOS:")
        archivos_esperados = []
        
        for json_file in json_files[-3:]:
            try:
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                documento_prueba = data.get('documento_prueba', '')
                sgc = data.get('sgc_number', 'UNKNOWN')
                
                if documento_prueba and documento_prueba.strip():
                    archivos_esperados.append((sgc, documento_prueba))
                    logger.info(f"   [ARCHIVO] {sgc}: Esperado '{documento_prueba}'")
                else:
                    logger.info(f"   [ARCHIVO] {sgc}: Sin archivo documento_prueba")
                    
            except Exception as json_error:
                logger.warning(f"   [ADVERTENCIA] Error leyendo {json_file.name}: {json_error}")
        
        # Resumen
        logger.info(f"\n[DATOS] RESUMEN DE ADJUNTOS:")
        logger.info(f"   [EXITOSO] Adjuntos específicos correctos: {adjuntos_correctos}")
        logger.info(f"   [ADVERTENCIA] Adjuntos incorrectos (conversiones): {adjuntos_incorrectos}")
        logger.info(f"   [EMOJI_REMOVIDO] Archivos esperados según JSON: {len(archivos_esperados)}")
        
        if adjuntos_correctos > 0:
            logger.info("[COMPLETADO] ¡ÉXITO! Se descargaron adjuntos específicos con formato correcto")
        elif adjunto_files:
            logger.warning("[ADVERTENCIA] Se descargaron adjuntos pero con formato incorrecto (conversiones)")
        else:
            logger.info("[INFO] No se descargaron adjuntos (puede ser normal si no hay adjuntos en los PQR)")
            
        # Verificar correspondencia
        if archivos_esperados:
            logger.info("\n[EMOJI_REMOVIDO] VERIFICANDO CORRESPONDENCIA:")
            for sgc, expected_file in archivos_esperados:
                found_adjunto = None
                for adjunto in adjunto_files:
                    if sgc in adjunto.name and '_adjunto_' in adjunto.name:
                        found_adjunto = adjunto
                        break
                
                if found_adjunto:
                    logger.info(f"   [EXITOSO] {sgc}: Encontrado {found_adjunto.name}")
                else:
                    logger.warning(f"   [ERROR] {sgc}: No encontrado adjunto para '{expected_file}'")
    else:
        logger.error("[ERROR] El directorio de archivos procesados no existe")

async def main():
    """Función principal"""
    logger.info("🧪 INICIANDO PRUEBA DE ADJUNTOS ESPECÍFICOS")
    logger.info("=" * 60)
    
    success = await test_adjuntos_especificos()
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("[COMPLETADO] PRUEBA EXITOSA - Funcionalidad de adjuntos específicos probada")
    else:
        logger.error("[ERROR] PRUEBA FALLIDA - Revisar funcionalidad de adjuntos")
    
    return success

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
