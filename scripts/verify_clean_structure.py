#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación de Estructura Limpia - ExtractorOV
===============================================

Script para verificar que la limpieza de src/ se realizó correctamente
y que todos los servicios funcionan sin errores de importación.
"""

import sys
import os
from pathlib import Path

# Agregar src al path
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def check_structure():
    """Verifica la estructura de directorios"""
    print("[EMOJI_REMOVIDO] Verificando estructura de directorios...")
    
    expected_structure = {
        'src/config': ['env_loader.py', 'unified_logging_config.py', '__init__.py'],
        'src/services': ['database_service.py', 'data_loader_service.py', 's3_uploader_service.py', '__init__.py', 'README.md'],
        'src/utils': ['dashboard_logger.py', 'file_utils.py', 'performance_monitor.py', '__init__.py'],
        'src/processors/afinia': ['data_processor.py', 'validators.py', 'models.py', 'database_manager.py'],
        'src/processors/aire': ['data_processor.py', 'validators.py', 'models.py', 'database_manager.py'],
        'src/extractors/afinia': ['oficina_virtual_afinia_modular.py'],
        'src/extractors/aire': ['oficina_virtual_aire_modular.py']
    }
    
    issues = []
    
    for directory, expected_files in expected_structure.items():
        dir_path = project_root / directory
        
        if not dir_path.exists():
            issues.append(f"[ERROR] Directorio faltante: {directory}")
            continue
            
        print(f"[EXITOSO] {directory}")
        
        for file_name in expected_files:
            file_path = dir_path / file_name
            if not file_path.exists():
                issues.append(f"[ADVERTENCIA] Archivo faltante: {directory}/{file_name}")
            else:
                print(f"   [EXITOSO] {file_name}")
    
    # Verificar que directorios no deseados fueron eliminados
    unwanted_paths = [
        'src/utils/validators',
        'src/processors/afinia/ov_validator'
    ]
    
    for unwanted in unwanted_paths:
        unwanted_path = project_root / unwanted
        if unwanted_path.exists():
            issues.append(f"[ERROR] Directorio no eliminado: {unwanted}")
        else:
            print(f"[EXITOSO] Eliminado correctamente: {unwanted}")
    
    return issues

def check_imports():
    """Verifica que las importaciones funcionen correctamente"""
    print("\n[EMOJI_REMOVIDO] Verificando importaciones...")
    
    import_tests = [
        ('services', 'DatabaseService, DataLoaderService, S3UploaderService'),
        ('config.env_loader', 'get_rds_config, get_s3_config'),
        ('config.unified_logging_config', 'get_unified_logger'),
        ('utils.file_utils', '*'),
        ('processors.afinia.data_processor', 'AfiniaDataProcessor'),
        ('processors.aire.data_processor', '*')
    ]
    
    issues = []
    
    for module, imports in import_tests:
        try:
            if imports == '*':
                exec(f"import {module}")
            else:
                exec(f"from {module} import {imports}")
            print(f"[EXITOSO] {module}")
        except ImportError as e:
            issues.append(f"[ERROR] Error importando {module}: {e}")
        except Exception as e:
            issues.append(f"[ADVERTENCIA] Error en {module}: {e}")
    
    return issues

def check_services_functionality():
    """Verifica funcionalidad básica de servicios sin conexiones externas"""
    print("\n[EMOJI_REMOVIDO] Verificando funcionalidad de servicios...")
    
    issues = []
    
    try:
        # Test DatabaseService (sin conexión real)
        from services import DatabaseService
        
        # Crear servicio con configuración mock
        mock_config = {
            'host': 'localhost',
            'database': 'test',
            'username': 'test',
            'password': 'test'
        }
        
        try:
            db_service = DatabaseService(mock_config)
            print("[EXITOSO] DatabaseService - Inicialización correcta")
        except ValueError as e:
            if "Configuración de RDS incompleta" not in str(e):
                issues.append(f"[ERROR] DatabaseService error inesperado: {e}")
            else:
                print("[EXITOSO] DatabaseService - Validación de config funcionando")
        
        # Test DataLoaderService
        from services import DataLoaderService
        loader = DataLoaderService(db_config=mock_config, max_workers=2)
        print("[EXITOSO] DataLoaderService - Inicialización correcta")
        
        # Test S3UploaderService
        from services import S3UploaderService
        
        mock_s3_config = {
            'bucket_name': 'test-bucket',
            'access_key_id': 'test-key',
            'secret_access_key': 'test-secret',
            'region': 'us-west-2'
        }
        
        s3_service = S3UploaderService(mock_s3_config)
        print("[EXITOSO] S3UploaderService - Inicialización correcta")
        
    except Exception as e:
        issues.append(f"[ERROR] Error en servicios: {e}")
    
    return issues

def check_logging_structure():
    """Verifica que la estructura de logging esté correcta"""
    print("\n[EMOJI_REMOVIDO] Verificando estructura de logging...")
    
    issues = []
    
    # Verificar directorios de logs
    logs_dir = project_root / 'data' / 'logs'
    if not logs_dir.exists():
        issues.append("[ERROR] Directorio data/logs no existe")
        return issues
    
    print("[EXITOSO] Directorio data/logs existe")
    
    # Verificar subdirectorios
    required_subdirs = ['current', 'archived', 'general']
    for subdir in required_subdirs:
        subdir_path = logs_dir / subdir
        if subdir_path.exists():
            print(f"[EXITOSO] Subdirectorio logs/{subdir} existe")
        else:
            issues.append(f"[ADVERTENCIA] Subdirectorio logs/{subdir} faltante")
    
    # Verificar configuración de logging unificado
    try:
        from config.unified_logging_config import get_unified_logger
        unified_logger = get_unified_logger()
        print("[EXITOSO] Sistema de logging unificado funcional")
    except Exception as e:
        issues.append(f"[ERROR] Error en logging unificado: {e}")
    
    return issues

def generate_report(all_issues):
    """Genera reporte final"""
    print("\n" + "="*60)
    print("[EMOJI_REMOVIDO] REPORTE FINAL DE VERIFICACIÓN")
    print("="*60)
    
    if not all_issues:
        print("[COMPLETADO] ¡ESTRUCTURA COMPLETAMENTE LIMPIA Y FUNCIONAL!")
        print("\n[EXITOSO] Verificaciones exitosas:")
        print("   • Estructura de directorios correcta")
        print("   • Archivos obsoletos eliminados")
        print("   • Importaciones funcionando")
        print("   • Servicios RDS y S3 operativos")
        print("   • Sistema de logging unificado activo")
        print("\n[INICIANDO] El proyecto está listo para usar los nuevos servicios")
        return True
    else:
        print(f"[ADVERTENCIA] Se encontraron {len(all_issues)} problemas:")
        for issue in all_issues:
            print(f"   {issue}")
        print("\n[EMOJI_REMOVIDO] Recomendaciones:")
        print("   • Revisar los problemas listados arriba")
        print("   • Ejecutar nuevamente tras las correcciones")
        return False

def main():
    """Función principal"""
    print("🧹 VERIFICACIÓN DE ESTRUCTURA LIMPIA - ExtractorOV")
    print("="*60)
    
    all_issues = []
    
    # Ejecutar verificaciones
    all_issues.extend(check_structure())
    all_issues.extend(check_imports())
    all_issues.extend(check_services_functionality())
    all_issues.extend(check_logging_structure())
    
    # Generar reporte
    success = generate_report(all_issues)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())