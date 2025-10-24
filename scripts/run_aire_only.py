#!/usr/bin/env python3
"""
Ejecutor Específico de Air-e - Mercurio
=======================================

Script para ejecutar únicamente el extractor de Air-e con parámetros personalizables.

Funcionalidades:
- Configuración de registros máximos
- Modo headless o visual
- Configuración de fechas (días hacia atrás o rango específico)
- Logging detallado
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta

# Agregar el directorio raíz al path (mismo patrón que run_afinia_only.py)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importaciones
from Merc.services.aire_extractor import AireExtractor

# Configurar logging (mismo patrón que run_afinia_only.py)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/aire_execution.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def run_aire_extraction(max_records=None, headless=True, days_back=30, start_date=None, end_date=None):
    """
    Ejecutar extracción completa de Air-e
    
    Args:
        max_records: Número máximo de registros a procesar
        headless: Si ejecutar en modo headless
        days_back: Días hacia atrás para filtrar (si no se especifican fechas)
        start_date: Fecha de inicio (formato YYYY-MM-DD)
        end_date: Fecha de fin (formato YYYY-MM-DD)
    """
    try:
        logger.info("=== INICIANDO EXTRACCIÓN AIR-E ===")
        logger.info(f"🎭 Modo headless: {'Activado' if headless else 'Desactivado'}")
        logger.info(f"📊 Registros máximos: {max_records if max_records else 'Sin límite'}")
        
        # Crear extractor
        extractor = AireExtractor(headless=headless)
        
        # Mostrar configuración
        logger.info("CONFIGURACIÓN ACTUAL:")
        logger.info(f"  - URL Base: {extractor.urls['base']}")
        logger.info(f"  - URL Login: {extractor.urls['login']}")
        logger.info(f"  - Usuario: {extractor.mercurio_credentials['username']}")
        
        # Configurar fechas si se especifican
        if start_date and end_date:
            logger.info(f"  - Fechas: {start_date} - {end_date}")
        else:
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(days=days_back)
            logger.info(f"  - Fechas (últimos {days_back} días): {start_date_obj.strftime('%Y-%m-%d')} - {end_date_obj.strftime('%Y-%m-%d')}")
        
        # Paso 1: Configurar navegador
        logger.info("\n[PASO 1/5] Configurando navegador...")
        if not extractor.setup_browser():
            raise Exception("Error configurando navegador")
        logger.info("✅ Navegador configurado exitosamente")
        
        # Paso 2: Autenticación
        logger.info("\n[PASO 2/5] Realizando login...")
        if not extractor.authenticate():
            raise Exception("Error en autenticación")
        logger.info("✅ Login exitoso")
        
        # Paso 3: Extraer datos PQR Verbales
        logger.info("\n[PASO 3/5] Extrayendo datos PQR Verbales...")
        pqr_result = extractor.extract_pqr_verbales(max_records=max_records)
        if pqr_result:
            logger.info("✅ Extracción PQR Verbales completada")
        else:
            logger.warning("⚠️ Extracción PQR Verbales falló")
        
        # Paso 4: Extraer datos Oficina Virtual
        logger.info("\n[PASO 4/5] Extrayendo datos Oficina Virtual...")
        ov_result = extractor.extract_oficina_virtual(max_records=max_records)
        if ov_result:
            logger.info("✅ Extracción Oficina Virtual completada")
        else:
            logger.warning("⚠️ Extracción Oficina Virtual falló")
        
        # Paso 5: Procesar archivos descargados
        logger.info("\n[PASO 5/5] Procesando archivos descargados...")
        processed_files = extractor.process_downloaded_files()
        logger.info(f"✅ Archivos procesados: {len(processed_files)}")
        
        # Resumen final
        logger.info("\n=== RESUMEN DE EXTRACCIÓN ===")
        logger.info(f"PQR Verbales: {'✅ Exitoso' if pqr_result else '❌ Falló'}")
        logger.info(f"Oficina Virtual: {'✅ Exitoso' if ov_result else '❌ Falló'}")
        logger.info(f"Archivos procesados: {len(processed_files)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en extracción Air-e: {str(e)}")
        return False
    finally:
        # Limpiar recursos
        try:
            extractor.cleanup()
            logger.info("🧹 Recursos liberados")
        except:
            pass


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Extractor Air-e con parámetros específicos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run_aire_only.py --max-records 2 --headless
  python run_aire_only.py --max-records 5 --visual --days-back 30
  python run_aire_only.py --max-records 10 --start-date "01/01/2025" --end-date "31/01/2025"
        """
    )
    
    parser.add_argument(
        '--max-records', 
        type=int, 
        default=2,
        help='Número máximo de registros a procesar (default: 2)'
    )
    
    parser.add_argument(
        '--headless', 
        action='store_true',
        help='Ejecutar en modo headless (sin mostrar navegador)'
    )
    
    parser.add_argument(
        '--visual', 
        action='store_true',
        help='Ejecutar en modo visual (mostrar navegador)'
    )
    
    parser.add_argument(
        '--days-back', 
        type=int, 
        default=30,
        help='Días hacia atrás para extraer (default: 30)'
    )
    
    parser.add_argument(
        '--start-date', 
        type=str,
        help='Fecha de inicio en formato DD/MM/YYYY'
    )
    
    parser.add_argument(
        '--end-date', 
        type=str,
        help='Fecha de fin en formato DD/MM/YYYY'
    )
    
    args = parser.parse_args()
    
    # Determinar modo headless
    headless = args.headless or not args.visual
    
    try:
        # Ejecutar extracción
        success = run_aire_extraction(
            max_records=args.max_records,
            headless=headless,
            days_back=args.days_back,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        if success:
            logger.info("🎉 Extracción Air-e completada exitosamente")
            sys.exit(0)
        else:
            logger.error("💥 Extracción Air-e falló")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Extracción interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Error inesperado: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()