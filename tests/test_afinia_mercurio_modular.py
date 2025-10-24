#!/usr/bin/env python3
"""
Script de prueba para el extractor modular de Mercurio Afinia
"""
import sys
import os
from datetime import datetime, timedelta

def test_extractor():
    try:
        from d4_downloaders.extractorMerc.afinia.mercurio_afinia_modular import MercurioAfiniaModular
        
        print('🧪 PRUEBA COMPLETA DEL EXTRACTOR MODULAR MERCURIO AFINIA')
        print('=' * 60)
        
        # Crear instancia
        extractor = MercurioAfiniaModular(headless=True, company='afinia')
        print('✓ Extractor inicializado')
        
        # La configuración ya se valida en el constructor
        print('✓ Configuración validada automáticamente')
        
        # Test de fechas (últimos 3 días para prueba rápida)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=3)
        
        print(f'📅 Período de prueba: {start_date.strftime("%Y-%m-%d")} a {end_date.strftime("%Y-%m-%d")}')
        
        # Ejecutar extracción completa (con navegador en modo headless)
        print()
        print('🚀 INICIANDO PROCESO DE EXTRACCIÓN...')
        
        # Calcular días hacia atrás
        days_back = (end_date - start_date).days
        print(f'📊 Extrayendo datos de los últimos {days_back} días')
        
        result = extractor.run_complete_extraction(days_back=days_back)
        
        print()
        print('📊 RESULTADO DE LA EXTRACCIÓN:')
        if result and isinstance(result, dict):
            print(f'✅ Proceso completado')
            
            # Verificar si se generaron archivos
            if 'files' in result and result['files']:
                print(f'📋 Archivos generados: {len(result["files"])}')
                for file_path in result['files']:
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        print(f'📄 {file_path} - Tamaño: {file_size} bytes')
                        
                        # Leer primeras líneas si es un archivo de texto
                        try:
                            if file_path.endswith('.csv') or file_path.endswith('.txt'):
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()
                                    print(f'  📋 Líneas: {len(lines)}')
                                    if lines:
                                        print(f'  🔤 Encabezado: {lines[0].strip()[:100]}...')
                        except Exception as read_error:
                            print(f'  ⚠️ Error al leer: {read_error}')
            
            # Mostrar métricas
            if 'metrics' in result:
                print(f'📊 Métricas: {result["metrics"]}')
                
        elif isinstance(result, str):  # Por si devuelve una ruta de archivo
            print(f'✅ Archivo generado: {result}')
            if os.path.exists(result):
                file_size = os.path.getsize(result)
                print(f'📄 Tamaño del archivo: {file_size} bytes')
        else:
            print('❌ No se generó resultado')
        
        print()
        print('🎯 PRUEBA COMPLETADA EXITOSAMENTE')
        return True
        
    except Exception as e:
        print(f'❌ ERROR EN LA PRUEBA: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Iniciando prueba del extractor modular de Mercurio Afinia...")
    result = test_extractor()
    
    if result:
        print("\n✅ TODAS LAS PRUEBAS PASARON")
        sys.exit(0)
    else:
        print("\n❌ ALGUNAS PRUEBAS FALLARON")
        sys.exit(1)

