#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir todas las rutas de logging en el proyecto ExtractorOV_Modular
====================================================================================

Este script busca y corrige automáticamente las referencias a rutas de logging
antiguos para que todos los logs vayan a la estructura data/logs/.

Cambios que realiza:
- "logs/" -> "data/logs/"
- "./data/logs/" -> "./data/logs/"
- "data/logs" -> "data/logs"
- Actualizar configuraciones de logging
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

class LoggingPathFixer:
    """Clase para corregir las rutas de logging en el proyecto"""
    
    def __init__(self, project_root: str):
        """
        Inicializa el fixer
        
        Args:
            project_root: Directorio raíz del proyecto
        """
        self.project_root = Path(project_root)
        self.changes_made = []
        
        # Patrones a buscar y sus reemplazos
        self.patterns = [
            # Rutas básicas
            (r'["\']logs["\']', r'"data/logs"'),
            (r'["\']\.\/logs["\']', r'"./data/logs"'),
            (r'["\']\.\/logs\/["\']', r'"./data/logs/"'),
            
            # Rutas legacy
            (r'["\']n_logs_14["\']', r'"data/logs"'),
            (r'["\']\.\/n_logs_14["\']', r'"./data/logs"'),
            
            # Paths objects
            (r'Path\(["\']logs["\']\)', r'Path("data/logs")'),
            (r'Path\(["\']\.\/logs["\']\)', r'Path("./data/logs")'),
            (r'project_root\s*\/\s*["\']logs["\']', r'project_root / "data/logs"'),
            
            # Configuraciones específicas
            (r'base_logs_dir:\s*str\s*=\s*["\']logs["\']', r'base_logs_dir: str = "data/logs"'),
            (r'LOG_PATH\s*=\s*["\']\.\/n_logs_14["\']', r'LOG_PATH = "./data/logs"'),
            (r'LOG_PATH\s*=\s*["\']\.\/logs["\']', r'LOG_PATH = "./data/logs"'),
        ]
        
        # Archivos a excluir del procesamiento
        self.exclude_patterns = [
            r'__pycache__',
            r'\.git',
            r'\.venv',
            r'node_modules',
            r'\.log$',
            r'\.pyc$',
            r'\.json$',
            r'legacy/',
            r'deprecated_docs/',
        ]
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Determina si un archivo debe excluirse del procesamiento"""
        file_str = str(file_path)
        return any(re.search(pattern, file_str) for pattern in self.exclude_patterns)
    
    def get_python_files(self) -> List[Path]:
        """Obtiene todos los archivos Python del proyecto"""
        python_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Excluir directorios
            dirs[:] = [d for d in dirs if not any(re.search(pattern, d) for pattern in self.exclude_patterns)]
            
            for file in files:
                if file.endswith(('.py', '.sh', '.md')):
                    file_path = Path(root) / file
                    if not self.should_exclude_file(file_path):
                        python_files.append(file_path)
        
        return python_files
    
    def fix_file(self, file_path: Path) -> List[str]:
        """
        Corrige las rutas de logging en un archivo
        
        Returns:
            Lista de cambios realizados
        """
        changes = []
        
        try:
            # Leer archivo original
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            modified_content = original_content
            
            # Aplicar cada patrón
            for pattern, replacement in self.patterns:
                matches = re.findall(pattern, modified_content)
                if matches:
                    modified_content = re.sub(pattern, replacement, modified_content)
                    changes.append(f"  {pattern} -> {replacement} ({len(matches)} occurrence(s))")
            
            # Si hubo cambios, escribir el archivo
            if changes and modified_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                self.changes_made.append({
                    'file': str(file_path),
                    'changes': changes
                })
                
                return changes
                
        except Exception as e:
            print(f"Error procesando {file_path}: {e}")
        
        return []
    
    def run(self) -> None:
        """Ejecuta la corrección en todo el proyecto"""
        print("[CONFIGURANDO] Iniciando corrección de rutas de logging...")
        print(f"[EMOJI_REMOVIDO] Directorio raíz: {self.project_root}")
        print()
        
        # Obtener archivos Python
        files = self.get_python_files()
        print(f"[ARCHIVO] Archivos a procesar: {len(files)}")
        print()
        
        # Procesar cada archivo
        total_files_changed = 0
        
        for file_path in files:
            changes = self.fix_file(file_path)
            if changes:
                total_files_changed += 1
                print(f"[EXITOSO] {file_path.relative_to(self.project_root)}:")
                for change in changes:
                    print(change)
                print()
        
        # Resumen
        print("=" * 60)
        print("[DATOS] RESUMEN DE CORRECCIONES")
        print("=" * 60)
        print(f"Archivos procesados: {len(files)}")
        print(f"Archivos modificados: {total_files_changed}")
        print(f"Total de correcciones: {len(self.changes_made)}")
        print()
        
        if self.changes_made:
            print("[EXITOSO] Correcciones completadas exitosamente!")
            print()
            print("[EMOJI_REMOVIDO] Próximos pasos recomendados:")
            print("1. Revisar los cambios realizados")
            print("2. Ejecutar tests para validar funcionalidad")
            print("3. Probar los extractores para confirmar que los logs van a data/logs/")
        else:
            print("[INFO]  No se encontraron rutas de logging que corregir.")


def main():
    """Función principal"""
    # Determinar directorio del proyecto
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Crear y ejecutar el fixer
    fixer = LoggingPathFixer(str(project_root))
    fixer.run()


if __name__ == "__main__":
    main()