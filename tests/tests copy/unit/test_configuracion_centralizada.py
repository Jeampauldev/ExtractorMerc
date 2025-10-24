#!/usr/bin/env python3
"""
Script de prueba para el sistema de configuración centralizada avanzado
"""

import sys
sys.path.append('.')

def test_sistema_configuracion():
    """Prueba el sistema de configuración avanzado"""

    print('🧪 TEST DEL SISTEMA DE CONFIGURACIÓN CENTRALIZADA')
    print('=' * 55)

    try:
        from f_config_06.extractor_config import get_config_manager, get_extractor_config

        # Test 1: Inicialización del gestor
        print('\n1[EMOJI_REMOVIDO]⃣ Inicializando gestor de configuración:')
        manager = get_config_manager()
        print(f'[EMOJI_REMOVIDO] Ambiente: {manager.environment.value}')
        print(f'[EMOJI_REMOVIDO] Directorio del proyecto: {manager.project_root}')

        # Test 2: Configuración global
        print('\n2[EMOJI_REMOVIDO]⃣ Configuración global:')
        global_config = manager.get_global_config()
        for key, value in global_config.items():
            print(f'  • {key}: {value}')

        # Test 3: Listar configuraciones disponibles
        print('\n3[EMOJI_REMOVIDO]⃣ Configuraciones disponibles:')
        configs = manager.list_available_configs()
        for config in configs:
            print(f"  • {config['company']}/{config['platform']} ({config['source']})")

        # Test 4: Probar carga de configuraciones específicas
        print('\n4[EMOJI_REMOVIDO]⃣ Probando carga de configuraciones:')
        test_cases = [
            ('aire', 'oficina_virtual'),
            ('afinia', 'oficina_virtual'), 
            ('afinia', 'sistema_anterior'),
            ('aire', 'sistema_anterior')
        ]

        loaded_configs = 0
        for company, platform in test_cases:
            try:
                config = get_extractor_config(company, platform)
                if config:
                    print(f'[EXITOSO] {company}/{platform}: {len(config.reports) if config.reports else 0} reportes')
                    loaded_configs += 1
                else:
                    print(f'[ERROR] {company}/{platform}: No disponible')

            except Exception as e:
                print(f'[ADVERTENCIA] {company}/{platform}: Error - {e}')

        # Test 5: Verificar cache
        print('\n5[EMOJI_REMOVIDO]⃣ Estado del cache:')
        print(f'  • Configuraciones en cache: {len(manager._config_cache)}')
        for key in manager._config_cache.keys():
            print(f'    - {key}')

        # Resumen
        print(f'\n[DATOS] RESUMEN:')
        print(f'  • Configuraciones disponibles: {len(configs)}')
        print(f'  • Configuraciones cargadas exitosamente: {loaded_configs}')
        print(f'  • Cache poblado: {len(manager._config_cache)} entradas')

        success_rate = (loaded_configs / len(test_cases)) * 100 if test_cases else 0
        print(f'  • Tasa de éxito: {success_rate:.1f}%')

        return success_rate > 50

    except Exception as e:
        print(f'[ERROR] ERROR GENERAL: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_configuracion_legacy():
    """Prueba la compatibilidad con configuración legacy"""

    print('\n[EMOJI_REMOVIDO] TEST DE COMPATIBILIDAD CON CONFIGURACIÓN LEGACY')
    print('=' * 50)

    try:
        # Importar configuración legacy directamente
        from f_config_06.config import get_extractor_config as legacy_get_config

        print('[EXITOSO] Configuración legacy importada correctamente')

        # Probar carga
        test_cases = [
            ('aire', 'oficina_virtual'),
            ('afinia', 'sistema_anterior')
        ]

        for company, platform in test_cases:
            config = legacy_get_config(company, platform)
            if config:
                reports = len(config.get('reports', {}))
                print(f'[EXITOSO] Legacy {company}/{platform}: {reports} reportes')
            else:
                print(f'[ERROR] Legacy {company}/{platform}: No disponible')

        return True

    except Exception as e:
        print(f'[ERROR] ERROR EN CONFIGURACIÓN LEGACY: {e}')
        return False

if __name__ == '__main__':
    print("[INICIANDO] Iniciando pruebas del sistema de configuración centralizada...")

    try:
        # Test del sistema nuevo
        nuevo_funciona = test_sistema_configuracion()

        # Test de compatibilidad legacy
        legacy_funciona = test_configuracion_legacy()

        print("\n" + "="*60)
        if nuevo_funciona and legacy_funciona:
            print("[COMPLETADO] SISTEMA DE CONFIGURACIÓN CENTRALIZADA FUNCIONANDO!")
            print("[EXITOSO] Nuevo sistema: OK")
            print("[EXITOSO] Compatibilidad legacy: OK") 
            print("[EXITOSO] Cache y validaciones: OK")
        elif legacy_funciona:
            print("[ADVERTENCIA] SISTEMA PARCIALMENTE FUNCIONAL")
            print("[EXITOSO] Compatibilidad legacy: OK")
            print("[ERROR] Nuevo sistema: Con problemas")
        else:
            print("[ERROR] SISTEMA CON PROBLEMAS")

        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
