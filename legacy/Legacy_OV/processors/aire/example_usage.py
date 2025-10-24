"""
Ejemplos de uso del procesador de datos de Aire.

Este archivo contiene ejemplos prácticos de cómo utilizar las diferentes
funcionalidades del procesador de datos de Aire.
"""

import json
from pathlib import Path
from datetime import datetime

# Importar componentes del procesador
from .data_processor import AireDataProcessor, process_aire_data, validate_aire_data
from .validators import validate_single_json, validate_json_files
from .logger import get_logger, setup_logging, timer
from .config import AIRE_CONFIG


def ejemplo_procesamiento_basico():
    """Ejemplo básico de procesamiento de archivos JSON."""
    print("=== EJEMPLO: Procesamiento Básico ===")

    # Ruta donde están los archivos JSON del extractor
    json_directory = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\aire\new_version"

    # Usar función de conveniencia para procesamiento completo
    resultado = process_aire_data(json_directory)

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

    json_directory = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\aire\new_version"

    # Validar archivos sin procesarlos
    resultados = validate_aire_data(json_directory)

    print(f"Total archivos encontrados: {resultados['total_files']}")
    print(f"Archivos válidos: {resultados['valid_files']}")
    print(f"Archivos inválidos: {resultados['invalid_files']}")

    if resultados['total_files'] > 0:
        tasa_validez = (resultados['valid_files'] / resultados['total_files']) * 100
        print(f"Tasa de validez: {tasa_validez:.2f}%")

    # Mostrar detalles de archivos inválidos
    archivos_invalidos = [f for f in resultados['files_details'] if not f['is_valid']]
    if archivos_invalidos:
        print(f"\nPrimeros archivos inválidos:")
        for archivo in archivos_invalidos[:2]:
            print(f" - {archivo['file_name']}:")
            for error in archivo['errors'][:2]:
                print(f"   * {error}")


def ejemplo_procesamiento_avanzado():
    """Ejemplo de procesamiento avanzado con configuración personalizada."""
    print("\n=== EJEMPLO: Procesamiento Avanzado ===")

    # Configuración personalizada
    config_personalizada = AIRE_CONFIG.copy()
    config_personalizada['processing']['batch_size'] = 10
    config_personalizada['processing']['max_retries'] = 3

    # Crear procesador con configuración personalizada
    processor = AireDataProcessor(config_personalizada)

    try:
        # Configurar logging
        setup_logging(level='DEBUG')
        logger = get_logger(__name__)

        # Directorio de archivos JSON
        json_directory = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\aire\new_version"

        # Procesar con métricas de tiempo
        with timer("Procesamiento completo"):
            resultado = processor.process_directory(json_directory)

        logger.info(f"Procesamiento completado: {resultado.total_insertados} registros")

        # Mostrar estadísticas detalladas
        print(f"\nEstadísticas detalladas:")
        print(f"- Tiempo total: {resultado.tiempo_procesamiento:.2f}s")
        print(f"- Archivos procesados: {resultado.total_archivos}")
        print(f"- Registros válidos: {resultado.total_insertados}")
        print(f"- Errores encontrados: {len([f for f in resultado.archivos_procesados if f.errores])}")

    except Exception as e:
        print(f"Error en procesamiento avanzado: {e}")


def ejemplo_validacion_individual():
    """Ejemplo de validación de archivos individuales."""
    print("\n=== EJEMPLO: Validación Individual ===")

    # Archivo específico para validar
    archivo_json = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\aire\new_version\pqr_001.json"

    try:
        # Validar archivo individual
        es_valido, errores, datos_pqr = validate_single_json(archivo_json)

        print(f"Archivo: {Path(archivo_json).name}")
        print(f"Válido: {'[EXITOSO] Sí' if es_valido else '[ERROR] No'}")

        if not es_valido:
            print("Errores encontrados:")
            for error in errores:
                print(f"  - {error}")
        else:
            print("Datos extraídos correctamente:")
            print(f"  - NIC: {datos_pqr.nic}")
            print(f"  - Documento: {datos_pqr.documento_identidad}")
            print(f"  - Radicado: {datos_pqr.numero_radicado}")
            print(f"  - Estado: {datos_pqr.estado_solicitud}")

    except FileNotFoundError:
        print(f"Archivo no encontrado: {archivo_json}")
    except Exception as e:
        print(f"Error validando archivo: {e}")


def ejemplo_monitoreo_metricas():
    """Ejemplo de monitoreo de métricas durante el procesamiento."""
    print("\n=== EJEMPLO: Monitoreo de Métricas ===")

    # Configurar logging con nivel DEBUG para ver métricas
    setup_logging(level='DEBUG')
    logger = get_logger(__name__)

    # Crear procesador
    processor = AireDataProcessor()

    # Directorio de prueba
    json_directory = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\aire\new_version"

    try:
        # Procesar con monitoreo
        logger.info("Iniciando procesamiento con monitoreo de métricas")
        
        resultado = processor.process_directory(json_directory)

        # Obtener métricas del procesador
        metricas = processor.get_processing_metrics()

        print(f"\nMétricas de procesamiento:")
        print(f"- Archivos procesados: {metricas.get('files_processed', 0)}")
        print(f"- Registros insertados: {metricas.get('records_inserted', 0)}")
        print(f"- Errores de validación: {metricas.get('validation_errors', 0)}")
        print(f"- Errores de base de datos: {metricas.get('database_errors', 0)}")
        print(f"- Tiempo promedio por archivo: {metricas.get('avg_time_per_file', 0):.3f}s")

    except Exception as e:
        logger.error(f"Error en monitoreo: {e}")
        print(f"Error: {e}")


def ejemplo_procesamiento_con_filtros():
    """Ejemplo de procesamiento con filtros específicos."""
    print("\n=== EJEMPLO: Procesamiento con Filtros ===")

    # Crear procesador
    processor = AireDataProcessor()

    # Directorio de archivos
    json_directory = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\aire\new_version"

    try:
        # Procesar solo archivos que cumplan ciertos criterios
        def filtro_archivos(archivo_path):
            """Filtro personalizado para archivos."""
            # Solo procesar archivos que contengan 'pqr' en el nombre
            return 'pqr' in Path(archivo_path).name.lower()

        # Aplicar filtro durante el procesamiento
        archivos_json = list(Path(json_directory).glob("*.json"))
        archivos_filtrados = [str(f) for f in archivos_json if filtro_archivos(str(f))]

        print(f"Archivos encontrados: {len(archivos_json)}")
        print(f"Archivos filtrados: {len(archivos_filtrados)}")

        if archivos_filtrados:
            resultado = processor.process_files(archivos_filtrados)
            print(f"Procesados: {resultado.total_archivos}")
            print(f"Insertados: {resultado.total_insertados}")
        else:
            print("No se encontraron archivos que cumplan el filtro")

    except Exception as e:
        print(f"Error en procesamiento con filtros: {e}")


def ejemplo_recuperacion_errores():
    """Ejemplo de manejo y recuperación de errores."""
    print("\n=== EJEMPLO: Recuperación de Errores ===")

    # Configuración con reintentos
    config_con_reintentos = AIRE_CONFIG.copy()
    config_con_reintentos['processing']['max_retries'] = 3
    config_con_reintentos['processing']['retry_delay'] = 1

    processor = AireDataProcessor(config_con_reintentos)
    logger = get_logger(__name__)

    # Directorio de prueba
    json_directory = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\aire\new_version"

    try:
        # Procesar con manejo de errores
        resultado = processor.process_directory(json_directory)

        # Analizar errores
        archivos_con_errores = [f for f in resultado.archivos_procesados if f.errores]
        
        if archivos_con_errores:
            print(f"\nArchivos con errores: {len(archivos_con_errores)}")
            
            # Categorizar errores
            errores_validacion = []
            errores_bd = []
            errores_otros = []

            for archivo in archivos_con_errores:
                for error in archivo.errores:
                    if 'validación' in error.lower() or 'formato' in error.lower():
                        errores_validacion.append((archivo.archivo, error))
                    elif 'base de datos' in error.lower() or 'sql' in error.lower():
                        errores_bd.append((archivo.archivo, error))
                    else:
                        errores_otros.append((archivo.archivo, error))

            print(f"- Errores de validación: {len(errores_validacion)}")
            print(f"- Errores de base de datos: {len(errores_bd)}")
            print(f"- Otros errores: {len(errores_otros)}")

            # Mostrar algunos ejemplos
            if errores_validacion:
                print(f"\nEjemplos de errores de validación:")
                for archivo, error in errores_validacion[:2]:
                    print(f"  {Path(archivo).name}: {error}")

        else:
            print("[EXITOSO] No se encontraron errores en el procesamiento")

    except Exception as e:
        logger.error(f"Error crítico: {e}")
        print(f"Error crítico en recuperación: {e}")


def ejemplo_exportacion_resultados():
    """Ejemplo de exportación de resultados a diferentes formatos."""
    print("\n=== EJEMPLO: Exportación de Resultados ===")

    processor = AireDataProcessor()
    
    # Directorio de archivos
    json_directory = r"c:\00_Project_Dev\10_ExtractorOV\ExtractorOV\downloads\aire\new_version"

    try:
        # Procesar archivos
        resultado = processor.process_directory(json_directory)

        # Crear reporte de resultados
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'total_archivos': resultado.total_archivos,
            'total_insertados': resultado.total_insertados,
            'tasa_exito': resultado.tasa_exito_global,
            'tiempo_procesamiento': resultado.tiempo_procesamiento,
            'archivos_procesados': []
        }

        # Agregar detalles de cada archivo
        for archivo_info in resultado.archivos_procesados:
            reporte['archivos_procesados'].append({
                'archivo': Path(archivo_info.archivo).name,
                'registros_insertados': archivo_info.registros_insertados,
                'tiene_errores': len(archivo_info.errores) > 0,
                'errores': archivo_info.errores
            })

        # Exportar a JSON
        reporte_path = Path("reporte_procesamiento_aire.json")
        with open(reporte_path, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)

        print(f"Reporte exportado a: {reporte_path}")
        print(f"Tamaño del reporte: {reporte_path.stat().st_size} bytes")

        # Crear resumen en texto
        resumen_path = Path("resumen_procesamiento_aire.txt")
        with open(resumen_path, 'w', encoding='utf-8') as f:
            f.write("RESUMEN DE PROCESAMIENTO - AIRE\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total archivos: {resultado.total_archivos}\n")
            f.write(f"Registros insertados: {resultado.total_insertados}\n")
            f.write(f"Tasa de éxito: {resultado.tasa_exito_global:.2f}%\n")
            f.write(f"Tiempo total: {resultado.tiempo_procesamiento:.2f}s\n\n")

            if archivos_con_errores := [f for f in resultado.archivos_procesados if f.errores]:
                f.write("ARCHIVOS CON ERRORES:\n")
                for archivo in archivos_con_errores:
                    f.write(f"- {Path(archivo.archivo).name}\n")
                    for error in archivo.errores:
                        f.write(f"  * {error}\n")

        print(f"Resumen exportado a: {resumen_path}")

    except Exception as e:
        print(f"Error en exportación: {e}")


def main():
    """Función principal que ejecuta todos los ejemplos."""
    print("[EMOJI_REMOVIDO] EJEMPLOS DE USO - PROCESADOR AIRE")
    print("=" * 50)

    try:
        # Ejecutar ejemplos en secuencia
        ejemplo_procesamiento_basico()
        ejemplo_validacion_previa()
        ejemplo_procesamiento_avanzado()
        ejemplo_validacion_individual()
        ejemplo_monitoreo_metricas()
        ejemplo_procesamiento_con_filtros()
        ejemplo_recuperacion_errores()
        ejemplo_exportacion_resultados()

        print("\n[EXITOSO] Todos los ejemplos ejecutados correctamente")

    except KeyboardInterrupt:
        print("\n[ADVERTENCIA] Ejecución interrumpida por el usuario")
    except Exception as e:
        print(f"\n[ERROR] Error ejecutando ejemplos: {e}")


if __name__ == "__main__":
    main()
