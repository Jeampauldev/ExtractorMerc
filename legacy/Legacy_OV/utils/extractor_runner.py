#!/usr/bin/env python3
"""
Extractor Runner - Utilidad común para ejecutar extractores
===========================================================

Proporciona funcionalidad común para ejecutar extractores con manejo
de argumentos, logging y gestión de errores unificada.
"""

import argparse
import sys
import logging
import asyncio
from typing import Dict, Any, Callable, Optional

from src.core.browser_manager import BrowserManager
from src.core.authentication import AuthenticationManager


def setup_argument_parser(extractor_name: str) -> argparse.ArgumentParser:
    """
    Configura el parser de argumentos de línea de comandos.
    
    Args:
        extractor_name: Nombre del extractor para mostrar en la ayuda
        
    Returns:
        Parser configurado
    """
    parser = argparse.ArgumentParser(
        description=f'Extractor {extractor_name} - Oficina Virtual',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--headless', action='store_true', 
                       help='Ejecutar en modo headless (sin interfaz gráfica)')
    parser.add_argument('--debug', action='store_true',
                       help='Activar modo debug con logging detallado')
    
    return parser


def initialize_logger(extractor_name: str, debug: bool = False) -> logging.Logger:
    """
    Inicializa el logger unificado para el extractor.
    
    Args:
        extractor_name: Nombre del extractor
        debug: Si activar el modo debug
    
    Returns:
        Instancia del logger
    """
    from src.config.unified_logging_config import setup_service_logging
    logger = setup_service_logging(extractor_name.lower())
    
    # Configurar nivel de debug si es necesario
    if debug:
        logger.setLevel(logging.DEBUG)
    
    return logger


async def run_extractor_async(
    extractor_name: str,
    config: Dict[str, Any],
    extractor_function: Callable[[BrowserManager, AuthenticationManager, logging.Logger], Any],
    headless: bool = False,
    debug: bool = False
) -> None:
    """
    Ejecuta un extractor de forma asíncrona con la lógica común de inicialización.
    
    Args:
        extractor_name: Nombre del extractor (ej: 'Afinia', 'Aire')
        config: Configuración específica del extractor
        extractor_function: Función que ejecuta la lógica específica del extractor
        headless: Si ejecutar en modo headless
        debug: Si activar el modo debug
    """
    # Inicializar logger
    logger = initialize_logger(extractor_name, debug)
    browser_manager = None
    
    try:
        logger.info(f"=== Iniciando Extractor {extractor_name} ===")
        logger.info(f"Modo headless: {headless}")
        logger.info(f"Modo debug: {debug}")
        
        # Inicializar BrowserManager
        browser_manager = BrowserManager(headless=headless)
        
        # Configurar el navegador
        browser, page = await browser_manager.setup_browser()
        
        # Inicializar AuthenticationManager con la página
        auth_manager = AuthenticationManager(page=page)
        
        # Ejecutar la función específica del extractor
        result = await extractor_function(browser_manager, auth_manager, logger)
        
        logger.info(f"=== Extractor {extractor_name} completado exitosamente ===")
        return result
        
    except KeyboardInterrupt:
        logger.warning(f"Extractor {extractor_name} interrumpido por el usuario")
        raise
    except Exception as e:
        logger.error(f"Error en extractor {extractor_name}: {str(e)}")
        logger.exception("Detalles del error:")
        raise
    finally:
        # Limpiar recursos
        if browser_manager:
            try:
                await browser_manager.cleanup()
                logger.info("Navegador cerrado correctamente")
            except Exception as e:
                logger.error(f"Error al cerrar navegador: {str(e)}")


def run_extractor(
    extractor_name: str,
    config: Dict[str, Any],
    extractor_function: Callable[[BrowserManager, AuthenticationManager, logging.Logger], Any],
    custom_args_handler: Optional[Callable[[argparse.Namespace], None]] = None
) -> None:
    """
    Ejecuta un extractor con la lógica común de inicialización y manejo de errores.
    
    Args:
        extractor_name: Nombre del extractor (ej: 'Afinia', 'Aire')
        config: Configuración específica del extractor
        extractor_function: Función que ejecuta la lógica específica del extractor
        custom_args_handler: Función opcional para manejar argumentos personalizados
    """
    # Configurar argumentos de línea de comandos
    parser = setup_argument_parser(extractor_name)
    args = parser.parse_args()
    
    # Manejar argumentos personalizados si se proporciona
    if custom_args_handler:
        custom_args_handler(args)
    
    try:
        # Ejecutar de forma asíncrona
        asyncio.run(run_extractor_async(
            extractor_name=extractor_name,
            config=config,
            extractor_function=extractor_function,
            headless=args.headless,
            debug=args.debug
        ))
        
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception:
        sys.exit(1)