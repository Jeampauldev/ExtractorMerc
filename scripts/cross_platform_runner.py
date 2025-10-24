#!/usr/bin/env python3
"""
Cross-Platform Runner para Cargador de Archivos
Detecta automáticamente el sistema operativo y ajusta la configuración
Compatible con Windows 11 y Ubuntu 24.04.3 LTS
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

def detect_system_info() -> Dict[str, Any]:
    """Detectar información del sistema operativo"""
    system_info = {
        'os': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'is_windows': platform.system() == "Windows",
        'is_linux': platform.system() == "Linux",
        'is_ubuntu': False,
        'ubuntu_version': None,
        'terminal_support': True,
        'color_support': True
    }
    
    # Detectar Ubuntu específicamente
    if system_info['is_linux']:
        try:
            with open('/etc/os-release', 'r') as f:
                os_release = f.read()
                if 'Ubuntu' in os_release:
                    system_info['is_ubuntu'] = True
                    # Extraer versión de Ubuntu
                    for line in os_release.split('\n'):
                        if line.startswith('VERSION_ID='):
                            system_info['ubuntu_version'] = line.split('=')[1].strip('"')
                            break
        except FileNotFoundError:
            pass
    
    # Verificar soporte de colores
    if system_info['is_windows']:
        # En Windows, verificar si está disponible colorama
        try:
            import colorama
            system_info['color_support'] = True
        except ImportError:
            system_info['color_support'] = False
    
    return system_info

def setup_environment(system_info: Dict[str, Any]) -> bool:
    """Configurar el entorno según el sistema operativo"""
    try:
        if system_info['is_windows']:
            # Configuración para Windows
            os.system('chcp 65001 > nul 2>&1')  # UTF-8
            os.system('color')  # Habilitar colores ANSI
            
            # Verificar dependencias
            try:
                import colorama
                colorama.init()
            except ImportError:
                print("[ADVERTENCIA]  Recomendación: Instalar colorama para mejor soporte de colores")
                print("   pip install colorama")
        
        elif system_info['is_linux']:
            # Configuración para Linux/Ubuntu
            os.environ['TERM'] = os.environ.get('TERM', 'xterm-256color')
            
            # Verificar que estamos en un terminal compatible
            if not sys.stdout.isatty():
                print("[ADVERTENCIA]  No se detectó un terminal interactivo")
                system_info['terminal_support'] = False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error configurando entorno: {e}")
        return False

def check_dependencies() -> Dict[str, bool]:
    """Verificar dependencias del proyecto"""
    dependencies = {
        'pathlib': True,  # Parte de stdlib
        'json': True,     # Parte de stdlib
        'logging': True,  # Parte de stdlib
        'datetime': True, # Parte de stdlib
        'threading': True, # Parte de stdlib
    }
    
    # Verificar dependencias del proyecto
    project_deps = {
        'src.config.rds_config': False,
        'src.config.unified_logging_config': False,
        'src.services.s3_uploader_service': False,
        'visual_progress_monitor': False
    }
    
    for dep in project_deps:
        try:
            __import__(dep)
            project_deps[dep] = True
        except ImportError:
            project_deps[dep] = False
    
    dependencies.update(project_deps)
    return dependencies

def print_system_banner(system_info: Dict[str, Any]):
    """Mostrar banner del sistema"""
    # Colores ANSI
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    if not system_info['color_support']:
        CYAN = WHITE = GREEN = YELLOW = BOLD = RESET = ''
    
    print(f"{BOLD}{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}{WHITE}[INICIANDO] CARGADOR DE ARCHIVOS MULTIPLATAFORMA{RESET}")
    print(f"{BOLD}{CYAN}{'='*80}{RESET}")
    print()
    
    # Información del sistema
    print(f"{GREEN}[DATOS] INFORMACIÓN DEL SISTEMA:{RESET}")
    print(f"   Sistema Operativo: {system_info['os']} {system_info['release']}")
    
    if system_info['is_ubuntu']:
        print(f"   Distribución: Ubuntu {system_info['ubuntu_version']}")
    
    print(f"   Arquitectura: {system_info['machine']}")
    print(f"   Python: {system_info['python_version']}")
    print(f"   Soporte de colores: {'[EXITOSO]' if system_info['color_support'] else '[ERROR]'}")
    print(f"   Terminal interactivo: {'[EXITOSO]' if system_info['terminal_support'] else '[ERROR]'}")
    print()

def run_file_loader(service_type: str, input_directory: str, enable_visual: bool = True) -> Optional[Dict[str, Any]]:
    """Ejecutar el cargador de archivos con configuración multiplataforma"""
    try:
        # Detectar sistema
        system_info = detect_system_info()
        
        # Mostrar banner
        print_system_banner(system_info)
        
        # Configurar entorno
        if not setup_environment(system_info):
            print("[ERROR] Error configurando el entorno")
            return None
        
        # Verificar dependencias
        deps = check_dependencies()
        missing_deps = [dep for dep, available in deps.items() if not available]
        
        if missing_deps:
            print(f"[ERROR] Dependencias faltantes: {missing_deps}")
            print("   Asegúrate de estar en el directorio correcto del proyecto")
            return None
        
        print(f"[EXITOSO] Todas las dependencias están disponibles")
        print()
        
        # Importar y ejecutar el cargador
        from direct_json_to_rds_loader_with_files import DirectLoaderWithFiles
        
        # Ajustar visualización según el sistema
        visual_enabled = enable_visual and system_info['terminal_support'] and system_info['color_support']
        
        if enable_visual and not visual_enabled:
            print("[ADVERTENCIA]  Monitor visual deshabilitado debido a limitaciones del terminal")
        
        print(f"[CONFIGURANDO] Configuración:")
        print(f"   Servicio: {service_type}")
        print(f"   Directorio: {input_directory}")
        print(f"   Monitor visual: {'[EXITOSO]' if visual_enabled else '[ERROR]'}")
        print()
        
        # Crear y ejecutar el cargador
        loader = DirectLoaderWithFiles(
            service_type=service_type,
            input_directory=input_directory,
            enable_visual_monitor=visual_enabled
        )
        
        results = loader.run()
        return results
        
    except KeyboardInterrupt:
        print("\n\n[ADVERTENCIA]  Proceso interrumpido por el usuario")
        return None
    except Exception as e:
        print(f"[ERROR] Error ejecutando cargador: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Cargador de Archivos Multiplataforma",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  Windows:
    python cross_platform_runner.py afinia C:\\datos\\afinia_records
    
  Ubuntu:
    python3 cross_platform_runner.py aire /home/user/aire_records
    
  Sin monitor visual:
    python cross_platform_runner.py afinia ./test_data --no-visual
        """
    )
    
    parser.add_argument('service_type', choices=['afinia', 'aire'], 
                       help='Tipo de servicio (afinia o aire)')
    parser.add_argument('input_directory', 
                       help='Directorio con los datos a procesar')
    parser.add_argument('--no-visual', action='store_true',
                       help='Deshabilitar monitor visual de progreso')
    
    args = parser.parse_args()
    
    # Verificar que el directorio existe
    if not Path(args.input_directory).exists():
        print(f"[ERROR] Error: El directorio '{args.input_directory}' no existe")
        sys.exit(1)
    
    # Ejecutar cargador
    results = run_file_loader(
        service_type=args.service_type,
        input_directory=args.input_directory,
        enable_visual=not args.no_visual
    )
    
    if results:
        print(f"\n[EXITOSO] Proceso completado exitosamente")
        success_rate = (results.get('successful_records', 0) / max(results.get('processed_records', 1), 1)) * 100
        print(f"[DATOS] Tasa de éxito: {success_rate:.1f}%")
    else:
        print(f"\n[ERROR] El proceso no se completó correctamente")
        sys.exit(1)

if __name__ == "__main__":
    main()