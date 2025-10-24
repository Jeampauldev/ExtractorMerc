"""
Script principal para el procesador de datos de Afinia.

Este script proporciona una interfaz de línea de comandos para ejecutar
las diferentes funcionalidades del procesador de datos de Afinia.
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

from .data_processor import AfiniaDataProcessor, process_afinia_data, validate_afinia_data
from .logger import setup_logging, get_logger
from .config import AFINIA_CONFIG


def setup_arguments():
    """Configura los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Procesador de datos JSON de Afinia para RDS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
    python -m processors.afinia.main process -d "C:/path/to/json/files"
    python -m processors.afinia.main validate -d "C:/path/to/json/files"
    python -m processors.afinia.main process -f "C:/path/to/file.json"
    python -m processors.afinia.main stats
    python -m processors.afinia.main cleanup-duplicates
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
        config = AFINIA_CONFIG.copy()
        config.update(custom_config)

        return config

    except Exception as e:
        print(f"Error cargando configuración personalizada: {e}")
        return AFINIA_CONFIG


def command_process(args, logger):
    """Ejecuta el comando de procesamiento."""
    config = AFINIA_CONFIG
    if args.config:
        config = load_custom_config(args.config)

    processor = AfiniaDataProcessor(config)

    try:
        if args.file:
            # Procesar archivo individual
            logger.info(f"Procesando archivo: {args.file}")
            resultado = processor.process_single_file(args.file)
            
            if resultado.exito:
                print(f"[EXITOSO] Archivo procesado exitosamente")
                print(f"   Registros insertados: {resultado.registros_insertados}")
            else:
                print(f"[ERROR] Error procesando archivo: {resultado.errores[0] if resultado.errores else 'Error desconocido'}")
                return False

        elif args.directory:
            # Procesar directorio
            logger.info(f"Procesando directorio: {args.directory}")
            
            if args.new_only:
                resultado = processor.process_new_files_only(args.directory, pattern=args.pattern)
            else:
                resultado = processor.process_directory(args.directory, pattern=args.pattern)

            print(f"[DATOS] Resumen del procesamiento:")
            print(f"   Total archivos: {resultado.total_archivos}")
            print(f"   Registros insertados: {resultado.total_insertados}")
            print(f"   Tasa de éxito: {resultado.tasa_exito_global:.2f}%")
            print(f"   Tiempo total: {resultado.tiempo_total:.2f}s")

            # Mostrar archivos con errores
            archivos_con_errores = [f for f in resultado.archivos_procesados if f.errores]
            if archivos_con_errores:
                print(f"\n[ADVERTENCIA]  Archivos con errores ({len(archivos_con_errores)}):")
                for archivo in archivos_con_errores[:5]:  # Mostrar solo los primeros 5
                    print(f"   - {Path(archivo.archivo).name}: {archivo.errores[0]}")

        else:
            print("[ERROR] Debe especificar un directorio (-d) o archivo (-f) para procesar")
            return False

        # Exportar resultado si se especifica
        if args.output:
            export_result(resultado, args.output, logger)

        return True

    except Exception as e:
        logger.error(f"Error en procesamiento: {e}")
        print(f"[ERROR] Error: {e}")
        return False

    finally:
        processor.close()


def command_validate(args, logger):
    """Ejecuta el comando de validación."""
    if not args.directory:
        print("[ERROR] Debe especificar un directorio (-d) para validar")
        return False

    try:
        logger.info(f"Validando archivos en: {args.directory}")
        resultado = validate_afinia_data(args.directory, pattern=args.pattern)

        print(f"[EMOJI_REMOVIDO] Resumen de validación:")
        print(f"   Total archivos: {resultado['total_files']}")
        print(f"   Archivos válidos: {resultado['valid_files']}")
        print(f"   Archivos inválidos: {resultado['invalid_files']}")
        
        if resultado['total_files'] > 0:
            tasa_validez = (resultado['valid_files'] / resultado['total_files']) * 100
            print(f"   Tasa de validez: {tasa_validez:.2f}%")

        # Mostrar errores de validación
        if resultado['validation_errors']:
            print(f"\n[ADVERTENCIA]  Errores de validación:")
            for archivo, errores in list(resultado['validation_errors'].items())[:5]:
                print(f"   - {Path(archivo).name}:")
                for error in errores[:2]:  # Mostrar solo los primeros 2 errores por archivo
                    print(f"     * {error}")

        # Exportar resultado si se especifica
        if args.output:
            export_result(resultado, args.output, logger)

        return resultado['invalid_files'] == 0

    except Exception as e:
        logger.error(f"Error en validación: {e}")
        print(f"[ERROR] Error: {e}")
        return False


def command_stats(args, logger):
    """Ejecuta el comando de estadísticas."""
    config = AFINIA_CONFIG
    if args.config:
        config = load_custom_config(args.config)

    processor = AfiniaDataProcessor(config)

    try:
        # Probar conexión
        if not processor.db_manager.test_connection():
            print("[ERROR] No se pudo conectar a la base de datos")
            return False

        print("[DATOS] Estadísticas del sistema:")
        
        # Estadísticas de la base de datos
        db_stats = processor.db_manager.get_table_stats()
        if db_stats:
            print(f"\n[BASE_DATOS]  Base de datos:")
            print(f"   Total registros: {db_stats.get('total_records', 'N/A')}")
            print(f"   Registros únicos: {db_stats.get('unique_records', 'N/A')}")
            print(f"   Último procesamiento: {db_stats.get('last_processed', 'N/A')}")

        # Estadísticas del procesador
        proc_stats = processor.get_processing_stats()
        print(f"\n[CONFIGURACION]  Procesador:")
        print(f"   Archivos procesados: {proc_stats['files_processed']}")
        print(f"   Tasa de éxito: {proc_stats['success_rate']:.2f}%")
        print(f"   Errores de validación: {proc_stats['validation_errors']}")
        print(f"   Errores de BD: {proc_stats['database_errors']}")

        # Estadísticas de rendimiento
        performance_report = logger.get_performance_report(hours=24)
        if performance_report:
            print(f"\n[METRICAS] Rendimiento (últimas 24h):")
            proc_perf = performance_report.get('processing_performance', {})
            if proc_perf.get('count', 0) > 0:
                print(f"   Operaciones: {proc_perf['count']}")
                print(f"   Tiempo promedio: {proc_perf['avg']:.3f}s")
                print(f"   Tiempo total: {proc_perf['total']:.2f}s")

        # Exportar estadísticas si se especifica
        if args.output:
            stats_data = {
                'database_stats': db_stats,
                'processor_stats': proc_stats,
                'performance_report': performance_report,
                'timestamp': datetime.now().isoformat()
            }
            export_result(stats_data, args.output, logger)

        return True

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        print(f"[ERROR] Error: {e}")
        return False

    finally:
        processor.close()


def command_cleanup_duplicates(args, logger):
    """Ejecuta el comando de limpieza de duplicados."""
    config = AFINIA_CONFIG
    if args.config:
        config = load_custom_config(args.config)

    processor = AfiniaDataProcessor(config)

    try:
        print("🧹 Iniciando limpieza de duplicados...")
        
        # Obtener estadísticas antes
        stats_antes = processor.db_manager.get_table_stats()
        registros_antes = stats_antes.get('total_records', 0) if stats_antes else 0

        # Ejecutar limpieza
        resultado = processor.cleanup_duplicates()

        if 'error' in resultado:
            print(f"[ERROR] Error en limpieza: {resultado['error']}")
            return False

        # Obtener estadísticas después
        stats_despues = processor.db_manager.get_table_stats()
        registros_despues = stats_despues.get('total_records', 0) if stats_despues else 0

        print(f"[EXITOSO] Limpieza completada:")
        print(f"   Registros antes: {registros_antes}")
        print(f"   Registros después: {registros_despues}")
        print(f"   Grupos de duplicados: {resultado['duplicates_found']}")
        print(f"   Registros eliminados: {resultado['records_deleted']}")

        # Exportar resultado si se especifica
        if args.output:
            cleanup_data = {
                'records_before': registros_antes,
                'records_after': registros_despues,
                'duplicates_found': resultado['duplicates_found'],
                'records_deleted': resultado['records_deleted'],
                'timestamp': datetime.now().isoformat()
            }
            export_result(cleanup_data, args.output, logger)

        return True

    except Exception as e:
        logger.error(f"Error en limpieza de duplicados: {e}")
        print(f"[ERROR] Error: {e}")
        return False

    finally:
        processor.close()


def command_test_connection(args, logger):
    """Ejecuta el comando de prueba de conexión."""
    config = AFINIA_CONFIG
    if args.config:
        config = load_custom_config(args.config)

    processor = AfiniaDataProcessor(config)

    try:
        print("[EMOJI_REMOVIDO] Probando conexión a la base de datos...")
        
        if processor.db_manager.test_connection():
            print("[EXITOSO] Conexión exitosa")
            
            # Verificar tabla
            if processor.db_manager.create_pqr_table():
                print("[EXITOSO] Tabla PQR verificada/creada")
            else:
                print("[ADVERTENCIA]  Problema con la tabla PQR")
                
            return True
        else:
            print("[ERROR] Error de conexión")
            return False

    except Exception as e:
        logger.error(f"Error probando conexión: {e}")
        print(f"[ERROR] Error: {e}")
        return False

    finally:
        processor.close()


def export_result(data, output_file: str, logger):
    """Exporta resultado a archivo JSON."""
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if hasattr(data, 'to_dict'):
                json.dump(data.to_dict(), f, indent=2, ensure_ascii=False, default=str)
            else:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"[ARCHIVO] Resultado exportado: {output_path}")
        logger.info(f"Resultado exportado a: {output_path}")

    except Exception as e:
        logger.error(f"Error exportando resultado: {e}")
        print(f"[ADVERTENCIA]  Error exportando resultado: {e}")


def main():
    """Función principal."""
    parser = setup_arguments()
    args = parser.parse_args()

    # Configurar logging
    log_level = getattr(args, 'log_level', 'INFO')
    log_file = not getattr(args, 'no_log_file', False)
    
    logger = setup_logging(
        log_level=log_level,
        log_file=log_file
    )

    # Mostrar información inicial
    print("[INICIANDO] PROCESADOR DE DATOS AFINIA")
    print("=" * 40)
    
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
            print(f"[ERROR] Comando no reconocido: {args.command}")
            parser.print_help()
            success = False

    except KeyboardInterrupt:
        print("\n[ADVERTENCIA]  Operación interrumpida por el usuario")
        logger.warning("Operación interrumpida por el usuario")
        success = False

    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        logger.error(f"Error inesperado: {e}")
        success = False

    # Resultado final
    if success:
        print("\n[EXITOSO] Operación completada exitosamente")
        sys.exit(0)
    else:
        print("\n[ERROR] Operación falló")
        sys.exit(1)


if __name__ == "__main__":
    main()
