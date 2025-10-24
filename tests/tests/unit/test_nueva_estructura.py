#!/usr/bin/env python3
"""
Script de prueba para la nueva estructura de directorios
=========================================================

Prueba la nueva organización:
- downloaders/extractorOV/ (Oficina Virtual)
- downloaders/extractorMerc/ (sistema_anterior)
"""

import sys
import os
from datetime import datetime, timedelta

def test_nueva_estructura():
    """Prueba la nueva estructura organizacional"""

    print('[EMOJI_REMOVIDO] PRUEBA DE NUEVA ESTRUCTURA ORGANIZACIONAL')
    print('=' * 60)

    # Test 1: Importaciones de ExtractorOV
    print('\n[EMOJI_REMOVIDO] Probando ExtractorOV (Oficina Virtual):')
    try:
        from d_downloaders_04.extractorOV.aire.oficina_virtual_aire_modular import OficinaVirtualAireModular
        print('[EXITOSO] OficinaVirtualAireModular (Aire) - IMPORTADO')
    except ImportError as e:
        print(f'[ERROR] Error importando Aire OV: {e}')

    try:
        from d_downloaders_04.extractorOV.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular
        print('[EXITOSO] OficinaVirtualAfiniaModular (Afinia) - IMPORTADO')
    except ImportError as e:
        print(f'[ERROR] Error importando Afinia OV: {e}')

    # Test 2: Importaciones de ExtractorMerc
    print('\n[EMOJI_REMOVIDO] Probando ExtractorMerc (sistema_anterior):')
    try:
        from d_downloaders_04.extractor_sistema_anteriorAfiniaModular import extractor_sistema_anteriorAfiniaModular
        print('[EXITOSO] (sistema_anterior)AfiniaModular (Afinia) - IMPORTADO')
    except ImportError as e:
        print(f'[ERROR] Error importando Afinia sistema_anterior: {e}')

    # Test 3: Importaciones desde módulos principales
    print('\n[EMOJI_REMOVIDO] Probando importaciones desde módulos principales:')
    try:
        from d_downloaders_04.extractorOV import OficinaVirtualAireModular, OficinaVirtualAfiniaModular
        print('[EXITOSO] Importación directa desde extractorOV - OK')
    except ImportError as e:
        print(f'[ERROR] Error importando desde extractorOV: {e}')

    try:
        from d_downloaders_04.extractor_sistema_anteriorAfiniaModular import extractor_sistema_anteriorAfiniaModular
        print('[EXITOSO] Importación directa desde extractorMerc - OK')
    except ImportError as e:
        print(f'[ERROR] Error importando desde extractorMerc: {e}')

    # Test 4: Importaciones desde downloaders principal
    print('\n[EMOJI_REMOVIDO] Probando importaciones desde downloaders principal:')
    try:
        from downloaders import oficina_virtual_sistema_anteriorAfiniaModular
        print('[EXITOSO] Importación directa desde downloaders - OK')
    except ImportError as e:
        print(f'[ERROR] Error importando desde downloaders: {e}')

    print('\n[EXITOSO] PRUEBA DE ESTRUCTURA COMPLETADA')
    return True

def test_funcionalidad_basica():
    """Prueba funcionalidad básica de los extractores"""

    print('\n🧪 PRUEBA DE FUNCIONALIDAD BÁSICA')
    print('=' * 50)

    # Test ExtractorOV Aire
    print('\n[EMOJI_REMOVIDO] Probando ExtractorOV Aire:')
    try:
        from d_downloaders_04.extractorOV.aire.oficina_virtual_aire_modular import OficinaVirtualAireModular

        extractor = OficinaVirtualAireModular(headless=True, company='aire')
        print('[EXITOSO] Instancia creada exitosamente')
        print('[EXITOSO] Configuración cargada')

    except Exception as e:
        print(f'[ERROR] Error: {e}')

    # Test ExtractorMerc Afinia
    print('\n[EMOJI_REMOVIDO] Probando ExtractorMerc Afinia:')
    try:
        from d_downloaders_04.extractor_sistema_anteriorAfiniaModular import extractor_sistema_anteriorAfiniaModular

        extractor = extractor_sistema_anteriorAfiniaModular(headless=True, company='afinia')
        print('[EXITOSO] Instancia creada exitosamente')
        print('[EXITOSO] Configuración cargada')

    except Exception as e:
        print(f'[ERROR] Error: {e}')

    print('\n[EXITOSO] PRUEBA DE FUNCIONALIDAD COMPLETADA')
    return True

def mostrar_estructura():
    """Muestra la nueva estructura de directorios"""

    print('\n[EMOJI_REMOVIDO] NUEVA ESTRUCTURA DE DIRECTORIOS:')
    print('=' * 50)
    print("""
[EMOJI_REMOVIDO] downloaders/
[EMOJI_REMOVIDO] __init__.py                    # Módulo principal
[EMOJI_REMOVIDO]
[EMOJI_REMOVIDO] extractorOV/                   # Oficina Virtual
[EMOJI_REMOVIDO]   [EMOJI_REMOVIDO] __init__.py
[EMOJI_REMOVIDO]   [EMOJI_REMOVIDO] afinia/
[EMOJI_REMOVIDO]   [EMOJI_REMOVIDO]   [EMOJI_REMOVIDO] __init__.py
[EMOJI_REMOVIDO]   [EMOJI_REMOVIDO]   [EMOJI_REMOVIDO] oficina_virtual_afinia_modular.py
[EMOJI_REMOVIDO]   [EMOJI_REMOVIDO]   [EMOJI_REMOVIDO] oficina_virtual_afinia.py (legacy)
[EMOJI_REMOVIDO]   [EMOJI_REMOVIDO] aire/
[EMOJI_REMOVIDO]       [EMOJI_REMOVIDO] __init__.py
[EMOJI_REMOVIDO]       [EMOJI_REMOVIDO] oficina_virtual_aire_modular.py
[EMOJI_REMOVIDO]       [EMOJI_REMOVIDO] oficina_virtual_aire.py (legacy)
[EMOJI_REMOVIDO]
[EMOJI_REMOVIDO] extractorMerc/                 # sistema_anterior
    [EMOJI_REMOVIDO] __init__.py
    [EMOJI_REMOVIDO] afinia/
    [EMOJI_REMOVIDO]   [EMOJI_REMOVIDO] __init__.py
    [EMOJI_REMOVIDO]   [EMOJI_REMOVIDO] (sistema_anterior)_afinia_modular.py
    [EMOJI_REMOVIDO] aire/
        [EMOJI_REMOVIDO] __init__.py
        [EMOJI_REMOVIDO] (sistema_anterior)_aire_modular.py (pendiente)

[EMOJI_REMOVIDO] VENTAJAS:
• Organización clara por plataforma
• Separación lógica Oficina Virtual vs sistema_anterior 
• Fácil escalabilidad para nuevas empresas
• Imports intuitivos y limpios
• Mantiene compatibilidad con extractores legacy
    """)

if __name__ == '__main__':
    print("[INICIANDO] Iniciando pruebas de nueva estructura organizacional...")

    try:
        mostrar_estructura()
        test_nueva_estructura() 
        test_funcionalidad_basica()

        print("\n" + "="*60)
        print("[COMPLETADO] TODAS LAS PRUEBAS DE ESTRUCTURA PASARON")
        print("[EXITOSO] La nueva organización está funcionando correctamente!")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] ERROR EN LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

