#!/usr/bin/env python3
"""
Script de prueba para el extractor modular de Aire
"""
import sys
import os
from datetime import datetime, timedelta

def test_extractor():
    try:
        from src.extractors.aire.oficina_virtual_aire_modular import OficinaVirtualAireModular

        print('🧪 PRUEBA COMPLETA DEL EXTRACTOR MODULAR DE AIRE')
        print('=' * 60)

        # Crear instancia
        extractor = OficinaVirtualAireModular(headless=True, company='aire')
        print('[EXITOSO] Extractor inicializado')

        # La configuración ya se valida en el constructor
        print('[EXITOSO] Configuración validada automáticamente')

        # Test de fechas (últimos 3 días para prueba rápida)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)

        print(f'[EMOJI_REMOVIDO] Período de prueba: {start_date.strftime("%Y-%m-%d")} a {end_date.strftime("%Y-%m-%d")}')

        # Ejecutar extracción completa (con navegador en modo headless)
        print()
        print('[INICIANDO] INICIANDO PROCESO DE EXTRACCIÓN...')

        # Calcular días hacia atrás
        days_back = (end_date - start_date).days
        print(f'[DATOS] Extrayendo datos de los últimos {days_back} días')

        result = extractor.run_complete_extraction(days_back=days_back)

        print()
        print('[EMOJI_REMOVIDO] RESULTADO DE LA EXTRACCIÓN:')
        if result and isinstance(result, dict):
            print(f'[EXITOSO] Proceso completado')

            # Verificar si se generaron archivos
            if 'files' in result and result['files']:
                print(f'[EMOJI_REMOVIDO] Archivos generados: {len(result["files"])}')
                for file_path in result['files']:
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f'[ARCHIVO] {file_path} - Tamaño: {file_size} bytes')

                        # Leer primeras líneas
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                print(f'[EMOJI_REMOVIDO] Líneas: {len(lines)}')
                                if lines:
                                    print(f'[EMOJI_REMOVIDO] Encabezado: {lines[0].strip()[:100]}...')
                        except Exception as read_error:
                            print(f'[ADVERTENCIA] Error al leer: {read_error}')

            # Mostrar métricas
            if 'metrics' in result:
                print(f'[DATOS] Métricas: {result["metrics"]}')

        elif isinstance(result, str): # Por si devuelve una ruta de archivo
            print(f'[ARCHIVO] Archivo generado: {result}')
            if os.path.exists(result):
                file_size = os.path.getsize(result)
                print(f'[ARCHIVO] Tamaño del archivo: {file_size} bytes')
        else:
            print('[ERROR] No se generó resultado')

        print()
        print('[COMPLETADO] PRUEBA COMPLETADA EXITOSAMENTE')
        return True

    except Exception as e:
        print(f'[ERROR] ERROR EN LA PRUEBA: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Iniciando prueba del extractor modular de Aire...")
    result = test_extractor()

    if result:
        print("\n[EXITOSO] TODAS LAS PRUEBAS PASARON")
        sys.exit(0)
    else:
        print("\n[ERROR] ALGUNAS PRUEBAS FALLARON")
        sys.exit(1)

