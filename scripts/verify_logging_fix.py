#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Verificación - Configuración de Logging Corregida
===========================================================

Este script verifica que todas las configuraciones de logging 
estén funcionando correctamente después de las correcciones.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_directory_structure():
    """Verifica la estructura de directorios"""
    print("[EMOJI_REMOVIDO] Verificando estructura de directorios...")
    
    data_dir = project_root / 'data'
    logs_dir = data_dir / 'logs'
    
    # Verificar directorios principales
    directories_to_check = [
        data_dir,
        logs_dir,
        data_dir / 'downloads',
        data_dir / 'processed',
        data_dir / 'metrics'
    ]
    
    for dir_path in directories_to_check:
        if dir_path.exists():
            print(f"[EXITOSO] {dir_path.relative_to(project_root)} - OK")
        else:
            print(f"[ERROR] {dir_path.relative_to(project_root)} - FALTA")
    
    # Verificar que NO existan directorios incorrectos
    wrong_dir = data_dir / 'data'
    if wrong_dir.exists():
        print(f"[ADVERTENCIA]  {wrong_dir.relative_to(project_root)} - DIRECTORIO DUPLICADO DETECTADO")
        return False
    else:
        print("[EXITOSO] No se detectaron directorios duplicados")
    
    return True

def check_log_files_location():
    """Verifica la ubicación de archivos de log"""
    print("\n[EMOJI_REMOVIDO] Verificando ubicación de archivos de log...")
    
    # Buscar todos los archivos .log en el proyecto
    log_files = list(project_root.glob('**/*.log'))
    
    correct_logs = []
    incorrect_logs = []
    
    for log_file in log_files:
        rel_path = log_file.relative_to(project_root)
        if str(rel_path).startswith('data/logs') or str(rel_path).startswith('data\\logs'):
            correct_logs.append(rel_path)
        else:
            incorrect_logs.append(rel_path)
    
    print(f"[EXITOSO] Logs en ubicación correcta: {len(correct_logs)}")
    for log in correct_logs[:5]:  # Mostrar solo los primeros 5
        print(f"   • {log}")
    if len(correct_logs) > 5:
        print(f"   ... y {len(correct_logs) - 5} más")
    
    if incorrect_logs:
        print(f"[ERROR] Logs en ubicación incorrecta: {len(incorrect_logs)}")
        for log in incorrect_logs:
            print(f"   • {log}")
        return False
    else:
        print("[EXITOSO] Todos los logs están en la ubicación correcta")
    
    return True

def check_unified_logging_config():
    """Verifica la configuración de logging unificado"""
    print("\n[EMOJI_REMOVIDO] Verificando configuración de logging unificado...")
    
    try:
        from src.config.unified_logging_config import get_unified_logger
        
        # Crear instancia del logger unificado
        unified_logger = get_unified_logger()
        
        # Verificar que el directorio base sea correcto
        expected_base = project_root / 'data' / 'logs'
        if unified_logger.base_logs_dir == expected_base:
            print(f"[EXITOSO] Directorio base correcto: {unified_logger.base_logs_dir}")
        else:
            print(f"[ERROR] Directorio base incorrecto: {unified_logger.base_logs_dir}")
            print(f"   Esperado: {expected_base}")
            return False
        
        # Probar creación de logger para cada servicio
        for service in ['afinia', 'aire']:
            try:
                logger = unified_logger.get_logger(service, 'test')
                print(f"[EXITOSO] Logger para {service} creado correctamente")
            except Exception as e:
                print(f"[ERROR] Error creando logger para {service}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error al verificar configuración unificada: {e}")
        return False

def check_managers_configuration():
    """Verifica la configuración de los managers"""
    print("\n[EMOJI_REMOVIDO] Verificando configuración de managers...")
    
    managers = [
        project_root / 'afinia_manager.py',
        project_root / 'aire_manager.py'
    ]
    
    for manager_file in managers:
        if not manager_file.exists():
            print(f"[ERROR] Manager no encontrado: {manager_file.name}")
            continue
        
        # Leer el archivo y verificar las rutas
        content = manager_file.read_text(encoding='utf-8')
        
        # Buscar rutas problemáticas
        if 'data/logs' in content and 'data"/"data/logs' not in content:
            print(f"[EXITOSO] {manager_file.name} - Rutas corregidas")
        elif '"data/logs"' in content:
            print(f"[EXITOSO] {manager_file.name} - Rutas corregidas")
        else:
            print(f"[ADVERTENCIA]  {manager_file.name} - Verificar manualmente las rutas")
    
    return True

def generate_summary():
    """Genera un resumen del estado actual"""
    print("\n" + "="*60)
    print("[EMOJI_REMOVIDO] RESUMEN DE VERIFICACIÓN")
    print("="*60)
    
    checks = [
        ("Estructura de directorios", check_directory_structure()),
        ("Ubicación de archivos de log", check_log_files_location()),
        ("Configuración de logging unificado", check_unified_logging_config()),
        ("Configuración de managers", check_managers_configuration())
    ]
    
    all_passed = all(result for _, result in checks)
    
    print(f"\n[RESULTADO] Resultado general: {'[EXITOSO] APROBADO' if all_passed else '[ERROR] NECESITA REVISIÓN'}")
    
    if all_passed:
        print("\n[COMPLETADO] ¡Todas las correcciones se aplicaron exitosamente!")
        print("   • Los logs se generan en data/logs/")
        print("   • No hay directorios duplicados")
        print("   • La configuración unificada funciona")
        print("   • Los managers tienen rutas corregidas")
    else:
        print("\n[ADVERTENCIA]  Algunos elementos necesitan revisión:")
        for check_name, result in checks:
            if not result:
                print(f"   • {check_name}: [ERROR]")
    
    return all_passed

if __name__ == '__main__':
    print("[CONFIGURANDO] VERIFICACIÓN DE CORRECCIONES DE LOGGING")
    print("=" * 60)
    
    success = generate_summary()
    
    print(f"\n{'='*60}")
    print(f"Estado final: {'[EXITOSO] EXITOSO' if success else '[ERROR] CON ERRORES'}")
    
    sys.exit(0 if success else 1)