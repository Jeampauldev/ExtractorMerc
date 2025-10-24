"""
Ejemplos de uso del procesador de datos de Afinia.

Este archivo contiene ejemplos prácticos de cómo utilizar las diferentes
funcionalidades del procesador de datos de Afinia.
"""

import json
from pathlib import Path
from datetime import datetime

# Importar componentes del procesador
from .data_processor import AfiniaDataProcessor, process_afinia_data, validate_afinia_data
from .validators import validate_single_json, validate_json_files
from .logger import get_logger, setup_logging, timer
from .config import AFINIA_CONFIG


def ejemplo_procesamiento_basico():
    """Ejemplo básico de procesamiento de archivos JSON."""
    print("=== EJEMPLO: Procesamiento Básico ===")

    # Ruta donde están los archivos JSON del extractor
    json_directory = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\afinia\new_version"

    # Usar función de conveniencia para procesamiento completo
    resultado = process_afinia_data(json_directory)

    print(f"Archivos procesados: {resultado.total_archivos}")
    print(f"Registros insertados: {resultado.total_insertados}")
    print(f"Tasa de éxito: {resultado.tasa_exito_global:.2f}%")

    # Mostrar archivos con errores
    archivos_con_errores = [f for f in resultado.archivos_procesados if f.errores]
    if archivos_con_errores:
        print(f"\nArchivos con errores: {len(archivos_con_errores)}")
        for archivo in archivos_con_errores[:3]:  # Mostrar solo los primeros 3
            print(f" - {archivo.archivo}: {archivo.errores[0]}")


def ejemplo_validacion_previa():
    """Ejemplo de validación de archivos antes del procesamiento."""
    print("\n=== EJEMPLO: Validación Previa ===")

    json_directory = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\afinia\new_version"

    # Validar archivos sin procesarlos
    resultados = validate_afinia_data(json_directory)

    print(f"Total archivos encontrados: {resultados['total_files']}")
    print(f"Archivos válidos: {resultados['valid_files']}")
    print(f"Archivos con errores: {resultados['invalid_files']}")

    # Mostrar algunos errores
    if resultados['validation_errors']:
        print("\nPrimeros errores encontrados:")
        for error in list(resultados['validation_errors'].items())[:3]:
            archivo, errores = error
            print(f" - {archivo}: {errores[0]}")


def ejemplo_procesamiento_avanzado():
    """Ejemplo de procesamiento con configuración personalizada."""
    print("\n=== EJEMPLO: Procesamiento Avanzado ===")

    # Configurar logging personalizado
    logger = setup_logging(log_file=True)

    # Crear procesador con configuración personalizada
    config_personalizada = AFINIA_CONFIG.copy()
    config_personalizada['batch_size'] = 50  # Procesar en lotes más pequeños
    config_personalizada['max_retries'] = 5  # Más reintentos

    processor = AfiniaDataProcessor(config=config_personalizada)

    json_directory = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\afinia\new_version"

    try:
        # Procesar con métricas detalladas
        resultado = processor.process_directory(json_directory)

        print(f"Procesamiento completado:")
        print(f" - Total archivos: {resultado.total_archivos}")
        print(f" - Registros insertados: {resultado.total_insertados}")
        print(f" - Tiempo total: {resultado.tiempo_total:.2f}s")
        print(f" - Tasa de éxito: {resultado.tasa_exito_global:.2f}%")

        # Obtener reporte de rendimiento
        reporte = logger.get_performance_report(hours=1)
        print(f"\nRendimiento última hora:")
        print(f" - Procesamiento promedio: {reporte['processing_performance']['avg']:.3f}s")
        print(f" - Operaciones BD exitosas: {reporte['database_operations']['insert_success']}")

    except Exception as e:
        logger.error(f"Error en procesamiento avanzado: {e}")
        print(f"Error: {e}")


def ejemplo_validacion_individual():
    """Ejemplo de validación de archivos individuales."""
    print("\n=== EJEMPLO: Validación Individual ===")

    json_directory = Path(r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\afinia\new_version")

    # Buscar archivos JSON
    json_files = list(json_directory.glob("*.json"))

    if not json_files:
        print("No se encontraron archivos JSON en el directorio")
        return

    print(f"Validando {len(json_files)} archivos...")

    archivos_validos = 0
    archivos_invalidos = 0

    for json_file in json_files[:5]:  # Validar solo los primeros 5
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validar estructura
            is_valid, errores = validate_single_json(data, str(json_file))

            if is_valid:
                archivos_validos += 1
                print(f"[EMOJI_REMOVIDO] {json_file.name}: Válido")
            else:
                archivos_invalidos += 1
                print(f"[EMOJI_REMOVIDO] {json_file.name}: {errores[0] if errores else 'Error desconocido'}")

        except Exception as e:
            archivos_invalidos += 1
            print(f"[EMOJI_REMOVIDO] {json_file.name}: Error al leer archivo - {e}")

    print(f"\nResumen validación:")
    print(f" - Archivos válidos: {archivos_validos}")
    print(f" - Archivos inválidos: {archivos_invalidos}")


@timer("ejemplo_con_metricas")
def ejemplo_con_metricas():
    """Ejemplo de función con medición automática de tiempo."""
    print("\n=== EJEMPLO: Función con Métricas ===")

    logger = get_logger()

    # Simular procesamiento
    import time
    time.sleep(0.1)

    logger.info("Procesamiento con métricas completado")

    # Obtener estadísticas del timer
    stats = logger.metrics.get_timer_stats("ejemplo_con_metricas")
    print(f"Tiempo de ejecución: {stats['avg']:.3f}s")


def ejemplo_manejo_errores():
    """Ejemplo de manejo de errores y recuperación."""
    print("\n=== EJEMPLO: Manejo de Errores ===")

    logger = get_logger()

    # Directorio que no existe
    directorio_inexistente = r"c:\directorio\que\no\existe"

    try:
        resultado = process_afinia_data(directorio_inexistente)
        print("Procesamiento exitoso (no debería llegar aquí)")

    except FileNotFoundError as e:
        logger.warning(f"Directorio no encontrado: {e}")
        print(f"Error esperado: Directorio no encontrado")

    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        print(f"Error inesperado: {e}")

    # Intentar con directorio válido pero archivos corruptos
    try:
        # Crear archivo JSON inválido temporalmente
        temp_dir = Path("temp_test")
        temp_dir.mkdir(exist_ok=True)

        archivo_corrupto = temp_dir / "corrupto.json"
        with open(archivo_corrupto, 'w') as f:
            f.write('{"datos": "incompleto"')  # JSON inválido

        resultado = process_afinia_data(str(temp_dir))
        print(f"Procesamiento con errores: {resultado.total_archivos} archivos")

        # Limpiar
        archivo_corrupto.unlink()
        temp_dir.rmdir()

    except Exception as e:
        logger.error(f"Error en prueba de archivos corruptos: {e}")


def ejemplo_exportar_metricas():
    """Ejemplo de exportación de métricas y reportes."""
    print("\n=== EJEMPLO: Exportar Métricas ===")

    logger = get_logger()

    # Generar algunas métricas
    logger.metrics.record_counter("test_counter", 10)
    logger.metrics.record_timer("test_timer", 1.5)
    logger.metrics.record_gauge("test_gauge", 75.5)

    # Exportar métricas
    try:
        metrics_dir = Path("o15_metrics/afinia")
        metrics_dir.mkdir(parents=True, exist_ok=True)

        # Exportar métricas detalladas
        metrics_file = metrics_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        logger.metrics.export_metrics(str(metrics_file))
        print(f"Métricas exportadas: {metrics_file}")

        # Exportar reporte de rendimiento
        report_file = metrics_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        logger.export_performance_report(str(report_file), hours=24)
        print(f"Reporte exportado: {report_file}")

    except Exception as e:
        logger.error(f"Error exportando métricas: {e}")
        print(f"Error: {e}")


def ejemplo_configuracion_personalizada():
    """Ejemplo de configuración personalizada del procesador."""
    print("\n=== EJEMPLO: Configuración Personalizada ===")

    # Configuración personalizada
    config_custom = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_afinia',
            'user': 'test_user',
            'password': 'test_pass'
        },
        'processing': {
            'batch_size': 25,
            'max_retries': 3,
            'retry_delay': 2.0,
            'timeout': 30
        },
        'validation': {
            'strict_mode': True,
            'required_fields': ['fecha', 'numero_factura', 'valor_total'],
            'validate_dates': True
        },
        'logging': {
            'level': 'DEBUG',
            'file_logging': True,
            'metrics_enabled': True
        }
    }

    try:
        # Crear procesador con configuración personalizada
        processor = AfiniaDataProcessor(config=config_custom)
        print("Procesador creado con configuración personalizada")

        # Mostrar configuración actual
        print(f"Batch size: {processor.config['processing']['batch_size']}")
        print(f"Modo estricto: {processor.config['validation']['strict_mode']}")
        print(f"Nivel de logging: {processor.config['logging']['level']}")

    except Exception as e:
        print(f"Error creando procesador personalizado: {e}")


def mostrar_estadisticas_directorio():
    """Muestra estadísticas de archivos en el directorio."""
    print("\n=== EJEMPLO: Estadísticas del Directorio ===")

    json_directory = Path(r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\afinia\new_version")

    if not json_directory.exists():
        print(f"Directorio no existe: {json_directory}")
        return

    # Contar archivos
    json_files = list(json_directory.glob("*.json"))
    total_size = sum(f.stat().st_size for f in json_files)

    print(f"Directorio: {json_directory}")
    print(f"Archivos JSON: {len(json_files)}")
    print(f"Tamaño total: {total_size / 1024 / 1024:.2f} MB")

    if json_files:
        sizes = [f.stat().st_size for f in json_files]
        print(f"Archivo más grande: {max(sizes) / 1024:.1f} KB")
        print(f"Archivo más pequeño: {min(sizes) / 1024:.1f} KB")
        print(f"Tamaño promedio: {sum(sizes) / len(sizes) / 1024:.1f} KB")


def main():
    """Función principal que ejecuta todos los ejemplos."""
    print("[INICIANDO] EJEMPLOS DE USO - PROCESADOR AFINIA")
    print("=" * 50)

    try:
        # Configurar logging global
        setup_logging()

        # Ejecutar ejemplos
        ejemplo_procesamiento_basico()
        ejemplo_validacion_previa()
        ejemplo_procesamiento_avanzado()
        ejemplo_validacion_individual()
        ejemplo_con_metricas()
        ejemplo_manejo_errores()
        ejemplo_exportar_metricas()
        ejemplo_configuracion_personalizada()
        mostrar_estadisticas_directorio()

        print("\n[EXITOSO] Todos los ejemplos ejecutados correctamente")

    except KeyboardInterrupt:
        print("\n[ADVERTENCIA] Ejecución interrumpida por el usuario")

    except Exception as e:
        print(f"\n[ERROR] Error general: {e}")

    finally:
        print("\n[EMOJI_REMOVIDO] Fin de ejemplos")


if __name__ == "__main__":
    main()
