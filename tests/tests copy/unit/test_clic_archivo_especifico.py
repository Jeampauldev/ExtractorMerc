#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para probar el clic específico en el texto del archivo documento_prueba
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

logger = logging.getLogger('test_clic_archivo')

async def test_clic_archivo_especifico():
    """Prueba el clic específico en archivos documento_prueba"""
    try:
        logger.info("=== PROBANDO CLIC EN ARCHIVO ESPECÍFICO ===")
        
        # Configurar variables de entorno
        os.environ['ENABLE_PQR_PROCESSING'] = 'true'
        os.environ['MAX_PQR_RECORDS'] = '2'  # 2 registros para tener oportunidades
        
        # Verificar credenciales
        username = os.getenv('OV_AFINIA_USERNAME')
        password = os.getenv('OV_AFINIA_PASSWORD')
        
        if not username or not password:
            logger.error("[ERROR] Credenciales no encontradas")
            return False
        
        logger.info(f"[EXITOSO] Credenciales disponibles: {username[:3]}***")
        
        # Importar y crear extractor
        from src.extractors.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular
        
        logger.info("[CONFIGURANDO] Creando extractor para probar clic en archivos específicos...")
        extractor = OficinaVirtualAfiniaModular(
            headless=False,  # Modo visual para observar el clic
            visual_mode=True,
            enable_pqr_processing=True,
            max_pqr_records=2
        )
        
        # Ejecutar extracción
        logger.info("[INICIANDO] Ejecutando extracción con clic en archivos específicos...")
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
            
            # Verificar archivos específicos descargados
            await verificar_archivos_especificos_descargados()
            
            return True
        else:
            logger.error(f"[ERROR] Error: {result.get('error', 'Error desconocido')}")
            return False
            
    except Exception as e:
        logger.error(f"[ERROR] Error en prueba: {e}")
        return False

async def verificar_archivos_especificos_descargados():
    """Verifica que se descargaron archivos específicos con extensiones originales"""
    logger.info("=== VERIFICANDO ARCHIVOS ESPECÍFICOS DESCARGADOS ===")
    
    # Ruta donde deben estar los archivos
    project_root = Path(__file__).parent
    processed_path = project_root / "m_downloads_13" / "afinia" / "oficina_virtual" / "processed"
    
    logger.info(f"[EMOJI_REMOVIDO] Verificando en: {processed_path.absolute()}")
    
    if processed_path.exists():
        # Buscar archivos de hoy
        today = datetime.now().strftime("%Y%m%d")
        
        # Buscar todos los archivos de hoy
        all_files = list(processed_path.glob(f"*{today}*"))
        
        # Categorizar archivos
        pdf_principales = []
        json_files = []
        adjuntos_especificos = []
        adjuntos_pagina = []
        
        for file in all_files:
            if file.suffix.lower() == '.json':
                json_files.append(file)
            elif '_adjunto_' in file.name:
                if '_adjunto_pagina_' in file.name:
                    adjuntos_pagina.append(file)
                else:
                    adjuntos_especificos.append(file)
            elif file.suffix.lower() == '.pdf':
                pdf_principales.append(file)
        
        logger.info(f"[ARCHIVO] PDFs principales: {len(pdf_principales)}")
        logger.info(f"[EMOJI_REMOVIDO] JSONs: {len(json_files)}")
        logger.info(f"[EMOJI_REMOVIDO] Adjuntos específicos: {len(adjuntos_especificos)}")
        logger.info(f"[ARCHIVO] Adjuntos de página (conversiones): {len(adjuntos_pagina)}")
        
        # Analizar adjuntos específicos
        if adjuntos_especificos:
            logger.info("\n[RESULTADO] ADJUNTOS ESPECÍFICOS ENCONTRADOS:")
            for adjunto in adjuntos_especificos:
                logger.info(f"   [EXITOSO] {adjunto.name} ({adjunto.stat().st_size} bytes)")
                
                # Verificar que tiene extensión original (no PDF)
                if adjunto.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx', '.txt', '.zip', '.rar']:
                    logger.info(f"      [EXITOSO] Extensión original mantenida: {adjunto.suffix}")
                elif adjunto.suffix.lower() == '.pdf':
                    logger.info(f"      [INFO] PDF - verificar si es original o conversión")
        else:
            logger.warning("[ADVERTENCIA] No se encontraron adjuntos específicos")
        
        # Analizar JSONs para ver correspondencia
        logger.info("\n[EMOJI_REMOVIDO] ANÁLISIS DE CORRESPONDENCIA:")
        archivos_esperados = []
        archivos_encontrados = []
        
        for json_file in json_files:
            try:
                import json
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                documento_prueba = data.get('documento_prueba', '').strip()
                sgc = data.get('sgc_number', 'UNKNOWN')
                
                if documento_prueba:
                    archivos_esperados.append((sgc, documento_prueba))
                    logger.info(f"   [EMOJI_REMOVIDO] {sgc}: Esperado '{documento_prueba}'")
                    
                    # Buscar si se descargó
                    expected_extension = documento_prueba.split('.')[-1] if '.' in documento_prueba else 'bin'
                    found_adjunto = None
                    
                    for adjunto in adjuntos_especificos:
                        if sgc in adjunto.name and adjunto.suffix.lower() == f'.{expected_extension.lower()}':
                            found_adjunto = adjunto
                            break
                    
                    if found_adjunto:
                        logger.info(f"      [EXITOSO] ENCONTRADO: {found_adjunto.name}")
                        archivos_encontrados.append((sgc, found_adjunto.name))
                    else:
                        logger.warning(f"      [ERROR] NO ENCONTRADO: Adjunto específico para '{documento_prueba}'")
                else:
                    logger.info(f"   [EMOJI_REMOVIDO] {sgc}: Sin archivo documento_prueba")
                    
            except Exception as json_error:
                logger.warning(f"   [ADVERTENCIA] Error leyendo {json_file.name}: {json_error}")
        
        # Resumen final
        logger.info(f"\n[DATOS] RESUMEN FINAL:")
        logger.info(f"   [EMOJI_REMOVIDO] Archivos esperados: {len(archivos_esperados)}")
        logger.info(f"   [EXITOSO] Archivos encontrados: {len(archivos_encontrados)}")
        logger.info(f"   [EMOJI_REMOVIDO] Adjuntos específicos: {len(adjuntos_especificos)}")
        logger.info(f"   [ARCHIVO] Conversiones de página: {len(adjuntos_pagina)}")
        
        success_rate = (len(archivos_encontrados) / len(archivos_esperados) * 100) if archivos_esperados else 0
        logger.info(f"   [METRICAS] Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate > 0:
            logger.info("[COMPLETADO] ¡ÉXITO! Se descargaron archivos específicos correctamente")
        elif adjuntos_especificos:
            logger.info("[ADVERTENCIA] Se descargaron algunos adjuntos pero no coinciden exactamente")
        else:
            logger.info("[INFO] No se descargaron adjuntos específicos")
            
    else:
        logger.error("[ERROR] El directorio de archivos procesados no existe")

async def main():
    """Función principal"""
    logger.info("🧪 INICIANDO PRUEBA DE CLIC EN ARCHIVO ESPECÍFICO")
    logger.info("=" * 60)
    
    success = await test_clic_archivo_especifico()
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("[COMPLETADO] PRUEBA EXITOSA - Funcionalidad de clic en archivo específico probada")
    else:
        logger.error("[ERROR] PRUEBA FALLIDA - Revisar funcionalidad de clic")
    
    return success

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
