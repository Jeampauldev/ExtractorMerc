#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar y validar la estructura del directorio data/
==================================================================

Verifica que:
1. No haya directorios data/ duplicados
2. Todos los logs vayan a data/logs/
3. No haya carpetas logs/ fuera de data/
4. La estructura esté correctamente organizada
"""

import os
from pathlib import Path
from typing import List, Dict, Any

class DataStructureVerifier:
    """Clase para verificar la estructura del directorio data"""
    
    def __init__(self, project_root: str):
        """
        Args:
            project_root: Directorio raíz del proyecto
        """
        self.project_root = Path(project_root)
        self.issues = []
        self.stats = {
            'data_dirs_found': 0,
            'logs_dirs_found': 0,
            'log_files_found': 0,
            'data_files_found': 0,
        }
    
    def find_all_data_dirs(self) -> List[Path]:
        """Encuentra todos los directorios llamados 'data' en el proyecto"""
        data_dirs = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Excluir directorios de entornos virtuales y paquetes
            if any(exclude in root for exclude in ['.venv', 'site-packages', '.git', '__pycache__']):
                continue
                
            if 'data' in dirs:
                data_dir = Path(root) / 'data'
                data_dirs.append(data_dir)
                self.stats['data_dirs_found'] += 1
        
        return data_dirs
    
    def find_all_logs_dirs(self) -> List[Path]:
        """Encuentra todos los directorios llamados 'logs' en el proyecto"""
        logs_dirs = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Excluir directorios de entornos virtuales y paquetes
            if any(exclude in root for exclude in ['.venv', 'site-packages', '.git', '__pycache__']):
                continue
                
            if 'logs' in dirs:
                logs_dir = Path(root) / 'logs'
                logs_dirs.append(logs_dir)
                self.stats['logs_dirs_found'] += 1
        
        return logs_dirs
    
    def find_log_files(self) -> List[Path]:
        """Encuentra todos los archivos .log en el proyecto"""
        log_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Excluir directorios de entornos virtuales y paquetes
            if any(exclude in root for exclude in ['.venv', 'site-packages', '.git', '__pycache__']):
                continue
                
            for file in files:
                if file.endswith('.log'):
                    log_file = Path(root) / file
                    log_files.append(log_file)
                    self.stats['log_files_found'] += 1
        
        return log_files
    
    def count_data_files(self) -> int:
        """Cuenta archivos de datos en el directorio data principal"""
        data_dir = self.project_root / 'data'
        if not data_dir.exists():
            return 0
            
        count = 0
        for root, dirs, files in os.walk(data_dir):
            count += len(files)
            
        self.stats['data_files_found'] = count
        return count
    
    def check_expected_structure(self) -> List[str]:
        """Verifica que la estructura esperada esté presente"""
        expected_paths = [
            'data',
            'data/downloads',
            'data/downloads/afinia',
            'data/downloads/aire',
            'data/logs',
            'data/metrics',
        ]
        
        missing = []
        for path in expected_paths:
            full_path = self.project_root / path
            if not full_path.exists():
                missing.append(path)
        
        return missing
    
    def analyze_log_locations(self, log_files: List[Path]) -> Dict[str, List[Path]]:
        """Analiza la ubicación de los archivos de log"""
        locations = {
            'correct': [],      # En data/logs/
            'incorrect': [],    # Fuera de data/logs/
        }
        
        correct_path = self.project_root / 'data' / 'logs'
        
        for log_file in log_files:
            try:
                # Verificar si está dentro de data/logs/
                log_file.relative_to(correct_path)
                locations['correct'].append(log_file)
            except ValueError:
                locations['incorrect'].append(log_file)
        
        return locations
    
    def run_verification(self) -> Dict[str, Any]:
        """Ejecuta la verificación completa"""
        print("[EMOJI_REMOVIDO] Verificando estructura del directorio data/...")
        print(f"[EMOJI_REMOVIDO] Proyecto: {self.project_root}")
        print()
        
        # Buscar directorios data
        data_dirs = self.find_all_data_dirs()
        print(f"[EMOJI_REMOVIDO] Directorios 'data' encontrados: {len(data_dirs)}")
        for data_dir in data_dirs:
            rel_path = data_dir.relative_to(self.project_root)
            print(f"   - {rel_path}")
        print()
        
        # Verificar si hay duplicados
        if len(data_dirs) > 1:
            self.issues.append("[ADVERTENCIA]  Múltiples directorios 'data' encontrados")
            # Verificar si hay uno principal válido
            main_data = self.project_root / 'data'
            if main_data in data_dirs:
                print("[EXITOSO] Directorio principal 'data/' encontrado")
                duplicates = [d for d in data_dirs if d != main_data]
                for dup in duplicates:
                    rel_path = dup.relative_to(self.project_root)
                    print(f"[ERROR] Duplicado encontrado: {rel_path}")
            else:
                self.issues.append("[ERROR] No se encuentra el directorio principal 'data/'")
        
        # Buscar directorios logs
        logs_dirs = self.find_all_logs_dirs()
        print(f"[EMOJI_REMOVIDO] Directorios 'logs' encontrados: {len(logs_dirs)}")
        for logs_dir in logs_dirs:
            rel_path = logs_dir.relative_to(self.project_root)
            print(f"   - {rel_path}")
        print()
        
        # Verificar logs fuera de data/
        correct_logs_dir = self.project_root / 'data' / 'logs'
        incorrect_logs_dirs = [d for d in logs_dirs if d != correct_logs_dir]
        
        if incorrect_logs_dirs:
            self.issues.append("[ADVERTENCIA]  Directorios 'logs' encontrados fuera de data/")
            for incorrect in incorrect_logs_dirs:
                rel_path = incorrect.relative_to(self.project_root)
                print(f"[ERROR] Logs fuera de data/: {rel_path}")
        
        # Buscar archivos de log
        log_files = self.find_log_files()
        print(f"[ARCHIVO] Archivos .log encontrados: {len(log_files)}")
        
        # Analizar ubicaciones de logs
        log_locations = self.analyze_log_locations(log_files)
        print(f"   - En data/logs/: {len(log_locations['correct'])}")
        print(f"   - Fuera de data/logs/: {len(log_locations['incorrect'])}")
        
        if log_locations['incorrect']:
            print("\n[ERROR] Archivos de log en ubicaciones incorrectas:")
            for log_file in log_locations['incorrect']:
                rel_path = log_file.relative_to(self.project_root)
                print(f"     - {rel_path}")
        
        # Verificar estructura esperada
        missing = self.check_expected_structure()
        if missing:
            print(f"\n[ADVERTENCIA]  Estructura faltante: {missing}")
            self.issues.extend(missing)
        else:
            print("\n[EXITOSO] Estructura básica presente")
        
        # Contar archivos de datos
        data_files_count = self.count_data_files()
        print(f"\n[DATOS] Archivos en data/: {data_files_count}")
        
        # Resumen final
        print("\n" + "=" * 60)
        print("[DATOS] RESUMEN DE VERIFICACIÓN")
        print("=" * 60)
        
        for key, value in self.stats.items():
            print(f"{key}: {value}")
        
        print(f"\nProblemas encontrados: {len(self.issues)}")
        
        if self.issues:
            print("\n[ERROR] PROBLEMAS DETECTADOS:")
            for issue in self.issues:
                print(f"   {issue}")
            print("\n[EMOJI_REMOVIDO] Recomendaciones:")
            print("1. Eliminar directorios data/ duplicados")
            print("2. Mover logs a data/logs/")
            print("3. Eliminar directorios logs/ fuera de data/")
            print("4. Crear estructura faltante")
        else:
            print("\n[EXITOSO] ¡Estructura verificada correctamente!")
            print("   - Un solo directorio data/")
            print("   - Todos los logs en data/logs/")
            print("   - Estructura completa presente")
        
        return {
            'success': len(self.issues) == 0,
            'issues_count': len(self.issues),
            'issues': self.issues,
            'stats': self.stats,
            'data_dirs': [str(d.relative_to(self.project_root)) for d in data_dirs],
            'logs_dirs': [str(d.relative_to(self.project_root)) for d in logs_dirs],
            'log_files_correct': len(log_locations['correct']),
            'log_files_incorrect': len(log_locations['incorrect']),
        }


def main():
    """Función principal"""
    # Determinar directorio del proyecto
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Crear y ejecutar el verificador
    verifier = DataStructureVerifier(str(project_root))
    result = verifier.run_verification()
    
    # Salir con código apropiado
    exit_code = 0 if result['success'] else 1
    exit(exit_code)


if __name__ == "__main__":
    main()