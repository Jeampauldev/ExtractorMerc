"""
Script principal para el procesador de datos de Aire.

Este script proporciona una interfaz de línea de comandos para ejecutar
las diferentes funcionalidades del procesador de datos de Aire.
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

from .data_processor import AireDataProcessor, process_aire_data, validate_aire_data
from .logger import setup_logging, get_logger
from .config import AIRE_CONFIG


def setup_arguments():
    """Configura los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Procesador de datos JSON de Aire para RDS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
    python -m processors.aire.main process -d "C:/path/to/json/files"
    python -m processors.aire.main validate -d "C:/path/to/json/files"
    python -m processors.aire.main process -f "C:/path/to/file.json"
    python -m processors.aire.main stats
    python -m processors.aire.main cleanup-duplicates
    """
    )

    parser.add_argument(
        'command',
        choices=['process', 'validate', 'stats', 'cleanup-duplicates', 'test-connection'],
        help='Comando a ejecutar'
    )

    parser.add_argument(
        '-d', '--directory',
        type=str,
        help='Directorio con archivos JSON a procesar'
    )

    parser.add_argument(
        '-f', '--file',
        type=str,
        help='Archivo JSON específico a procesar'
    )

    parser.add_argument(
        '-p', '--pattern',
        type=str,
        default='pqr_*.json',
        help='Patrón de archivos a procesar (default: pqr_*.json)'
    )

    parser.add_argument(
        '--new-only',
        action='store_true',
        help='Procesar solo archivos nuevos (no procesados anteriormente)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Archivo de salida para reportes (JSON)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Nivel de logging (default: INFO)'
    )

    parser.add_argument(
        '--no-log-file',
        action='store_true',
        help='No crear archivo de log'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Archivo de configuración personalizada (JSON)'
    )

    return parser


def load_custom_config(config_path: str) -> dict:
    """Carga configuración personalizada desde archivo."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            custom_config = json.load(f)

        # Merge con configuración por defecto
        config = AIRE_CONFIG.copy()
        config.update(custom_config)

        return config

    except Exception as e:
        print(f"Error cargando configuración personalizada: {e}")
        return AIRE_CONFIG


def command_process(args, logger):
    """Ejecuta el comando de procesamiento."""
    config = AIRE_CONFIG
    if args.config:
        config = load_custom_config(args.config)

    processor = AireDataProcessor(config)

    try:
        if args.file:
            # Procesar archivo individual
            logger.info(f"Procesando archivo: {args.file}")
            result = processor.process_file(args.file)
            
            if result['success']:
                logger.info(f"Archivo procesado exitosamente: {result['records_inserted']} registros")
            else:
                logger.error(f"Error procesando archivo: {result['error']}")
                return False

        elif args.directory:
            # Procesar directorio
            logger.info(f"Procesando directorio: {args.directory}")
            results = processor.process_directory(
                args.directory,
                pattern=args.pattern,
                new_only=args.new_only
            )
            
            # Mostrar resumen
            total_files = len(results)
            successful = sum(1 for r in results if r['success'])
            failed = total_files - successful
            
            logger.info(f"Procesamiento completado: {successful}/{total_files} archivos exitosos")
            
            if failed > 0:
                logger.warning(f"{failed} archivos fallaron")
                for result in results:
                    if not result['success']:
                        logger.error(f"  - {result['file']}: {result['error']}")

        else:
            logger.error("Debe especificar --file o --directory")
            return False

        return True

    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}")
        return False


def command_validate(args, logger):
    """Ejecuta el comando de validación."""
    config = AIRE_CONFIG
    if args.config:
        config = load_custom_config(args.config)

    try:
        if args.file:
            # Validar archivo individual
            logger.info(f"Validando archivo: {args.file}")
            is_valid, errors = validate_aire_data(args.file, config)
            
            if is_valid:
                logger.info("Archivo válido")
            else:
                logger.warning(f"Archivo inválido: {len(errors)} errores encontrados")
                for error in errors:
                    logger.error(f"  - {error}")

        elif args.directory:
            # Validar directorio
            logger.info(f"Validando archivos en: {args.directory}")
            directory = Path(args.directory)
            
            if not directory.exists():
                logger.error(f"Directorio no existe: {args.directory}")
                return False

            json_files = list(directory.glob(args.pattern))
            if not json_files:
                logger.warning(f"No se encontraron archivos con patrón: {args.pattern}")
                return True

            total_files = len(json_files)
            valid_files = 0
            
            for json_file in json_files:
                is_valid, errors = validate_aire_data(str(json_file), config)
                
                if is_valid:
                    valid_files += 1
                    logger.info(f"[EMOJI_REMOVIDO] {json_file.name}")
                else:
                    logger.warning(f"[EMOJI_REMOVIDO] {json_file.name}: {len(errors)} errores")
                    for error in errors:
                        logger.debug(f"    - {error}")

            logger.info(f"Validación completada: {valid_files}/{total_files} archivos válidos")

        else:
            logger.error("Debe especificar --file o --directory")
            return False

        return True

    except Exception as e:
        logger.error(f"Error durante la validación: {e}")
        return False


def command_stats(args, logger):
    """Ejecuta el comando de estadísticas."""
    config = AIRE_CONFIG
    if args.config:
        config = load_custom_config(args.config)

    processor = AireDataProcessor(config)

    try:
        stats = processor.get_processing_stats()
        
        logger.info("=== Estadísticas de Procesamiento ===")
        logger.info(f"Archivos procesados: {stats.get('files_processed', 0)}")
        logger.info(f"Registros insertados: {stats.get('records_inserted', 0)}")
        logger.info(f"Errores de validación: {stats.get('validation_errors', 0)}")
        logger.info(f"Errores de base de datos: {stats.get('database_errors', 0)}")
        logger.info(f"Tiempo total de procesamiento: {stats.get('processing_time', 0):.2f}s")
        
        if stats.get('files_processed', 0) > 0:
            logger.info(f"Promedio registros por archivo: {stats.get('avg_records_per_file', 0):.1f}")
            logger.info(f"Promedio tiempo por archivo: {stats.get('avg_time_per_file', 0):.2f}s")
            logger.info(f"Tasa de éxito: {stats.get('success_rate', 0):.1f}%")

        # Exportar estadísticas si se especifica archivo de salida
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Estadísticas exportadas a: {args.output}")

        return True

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return False


def command_cleanup_duplicates(args, logger):
    """Ejecuta el comando de limpieza de duplicados."""
    config = AIRE_CONFIG
    if args.config:
        config = load_custom_config(args.config)

    processor = AireDataProcessor(config)

    try:
        logger.info("Iniciando limpieza de registros duplicados...")
        
        # Implementar lógica de limpieza de duplicados
        # Por ahora, solo mostrar mensaje
        logger.info("Funcionalidad de limpieza de duplicados en desarrollo")
        
        return True

    except Exception as e:
        logger.error(f"Error durante limpieza de duplicados: {e}")
        return False


def command_test_connection(args, logger):
    """Ejecuta el comando de prueba de conexión."""
    config = AIRE_CONFIG
    if args.config:
        config = load_custom_config(args.config)

    processor = AireDataProcessor(config)

    try:
        logger.info("Probando conexión a base de datos...")
        
        if processor.test_database_connection():
            logger.info("[EMOJI_REMOVIDO] Conexión a base de datos exitosa")
            return True
        else:
            logger.error("[EMOJI_REMOVIDO] Error de conexión a base de datos")
            return False

    except Exception as e:
        logger.error(f"Error probando conexión: {e}")
        return False


def main():
    """Función principal."""
    parser = setup_arguments()
    args = parser.parse_args()

    # Configurar logging
    log_level_map = {
        'DEBUG': 'DEBUG',
        'INFO': 'INFO',
        'WARNING': 'WARNING',
        'ERROR': 'ERROR'
    }
    
    logger = setup_logging(
        level=log_level_map.get(args.log_level, 'INFO'),
        log_file=None if args.no_log_file else f"aire_processor_{datetime.now().strftime('%Y%m%d')}.log"
    )

    logger.info(f"Iniciando procesador de Aire - Comando: {args.command}")

    # Ejecutar comando
    success = False
    
    try:
        if args.command == 'process':
            success = command_process(args, logger)
        elif args.command == 'validate':
            success = command_validate(args, logger)
        elif args.command == 'stats':
            success = command_stats(args, logger)
        elif args.command == 'cleanup-duplicates':
            success = command_cleanup_duplicates(args, logger)
        elif args.command == 'test-connection':
            success = command_test_connection(args, logger)
        else:
            logger.error(f"Comando no reconocido: {args.command}")
            parser.print_help()
            success = False

    except KeyboardInterrupt:
        logger.info("Procesamiento interrumpido por el usuario")
        success = False
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        success = False

    # Mostrar estadísticas finales si hay logger con métricas
    if hasattr(logger, 'get_processing_stats'):
        final_stats = logger.get_processing_stats()
        if final_stats.get('files_processed', 0) > 0:
            logger.info("=== Resumen de Sesión ===")
            logger.info(f"Archivos procesados: {final_stats['files_processed']}")
            logger.info(f"Registros insertados: {final_stats['records_inserted']}")
            logger.info(f"Tiempo total: {final_stats['processing_time']:.2f}s")

    if success:
        logger.info("Procesamiento completado exitosamente")
        sys.exit(0)
    else:
        logger.error("Procesamiento terminó con errores")
        sys.exit(1)


if __name__ == "__main__":
    main()
