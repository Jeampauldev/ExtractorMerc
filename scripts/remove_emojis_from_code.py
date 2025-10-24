#!/usr/bin/env python3
"""
Script para eliminar emojis de archivos de código y mantener un desarrollo profesional.
Reemplaza emojis con texto descriptivo apropiado.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Mapeo de emojis a texto profesional
EMOJI_REPLACEMENTS = {
    # Proceso y estado
    '[INICIANDO]': '[INICIANDO]',
    '[CONFIGURANDO]': '[CONFIGURANDO]',
    '[CONFIGURACION]': '[CONFIGURACION]',
    '[EXITOSO]': '[EXITOSO]',
    '[ERROR]': '[ERROR]',
    '[ADVERTENCIA]': '[ADVERTENCIA]',
    '[COMPLETADO]': '[COMPLETADO]',
    '[INFO]': '[INFO]',
    
    # Datos y archivos
    '[ARCHIVO]': '[ARCHIVO]',
    '[DATOS]': '[DATOS]',
    '[METRICAS]': '[METRICAS]',
    '[BASE_DATOS]': '[BASE_DATOS]',
    '[S3]': '[S3]',
    
    # Tiempo
    '[TIEMPO]': '[TIEMPO]',
    
    # Otros símbolos comunes
    '[INFO]': '[INFO]',
    '[RESULTADO]': '[RESULTADO]',
}

class EmojiRemover:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.processed_files = []
        self.changes_made = 0
        
    def find_files_with_emojis(self) -> List[Path]:
        """Encuentra archivos que contienen emojis."""
        files_with_emojis = []
        
        # Patrones de archivos a procesar
        patterns = ['*.py', '*.ps1']
        
        for pattern in patterns:
            for file_path in self.project_root.rglob(pattern):
                # Excluir ciertos directorios
                if any(part in str(file_path) for part in ['.git', '__pycache__', '.venv', 'node_modules']):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Buscar emojis usando regex
                    emoji_pattern = re.compile(
                        "["
                        "\U0001F600-\U0001F64F"  # emoticons
                        "\U0001F300-\U0001F5FF"  # symbols & pictographs
                        "\U0001F680-\U0001F6FF"  # transport & map
                        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                        "\U00002702-\U000027B0"
                        "\U000024C2-\U0001F251"
                        "]+", flags=re.UNICODE
                    )
                    
                    if emoji_pattern.search(content):
                        files_with_emojis.append(file_path)
                        
                except Exception as e:
                    print(f"Error leyendo {file_path}: {e}")
                    
        return files_with_emojis
    
    def remove_emojis_from_file(self, file_path: Path) -> bool:
        """Remueve emojis de un archivo específico."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            modified_content = original_content
            changes_in_file = 0
            
            # Reemplazar emojis específicos
            for emoji, replacement in EMOJI_REPLACEMENTS.items():
                if emoji in modified_content:
                    count = modified_content.count(emoji)
                    modified_content = modified_content.replace(emoji, replacement)
                    changes_in_file += count
            
            # Remover cualquier emoji restante con regex
            emoji_pattern = re.compile(
                "["
                "\U0001F600-\U0001F64F"  # emoticons
                "\U0001F300-\U0001F5FF"  # symbols & pictographs
                "\U0001F680-\U0001F6FF"  # transport & map
                "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                "\U00002702-\U000027B0"
                "\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE
            )
            
            remaining_emojis = emoji_pattern.findall(modified_content)
            if remaining_emojis:
                modified_content = emoji_pattern.sub('[EMOJI_REMOVIDO]', modified_content)
                changes_in_file += len(remaining_emojis)
            
            # Escribir archivo solo si hubo cambios
            if changes_in_file > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                self.processed_files.append(file_path)
                self.changes_made += changes_in_file
                
                print(f"[PROCESADO] {file_path.relative_to(self.project_root)} - {changes_in_file} emojis removidos")
                return True
            else:
                print(f"[SIN_CAMBIOS] {file_path.relative_to(self.project_root)}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error procesando {file_path}: {e}")
            return False
    
    def process_all_files(self):
        """Procesa todos los archivos con emojis."""
        print("[INICIANDO] Búsqueda de archivos con emojis...")
        
        files_with_emojis = self.find_files_with_emojis()
        
        if not files_with_emojis:
            print("[INFO] No se encontraron archivos con emojis.")
            return
        
        print(f"[INFO] Encontrados {len(files_with_emojis)} archivos con emojis")
        print("\n[PROCESANDO] Removiendo emojis...")
        
        for file_path in files_with_emojis:
            self.remove_emojis_from_file(file_path)
        
        print(f"\n[COMPLETADO] Proceso terminado")
        print(f"[RESUMEN] Archivos procesados: {len(self.processed_files)}")
        print(f"[RESUMEN] Total de emojis removidos: {self.changes_made}")
        
        if self.processed_files:
            print("\n[ARCHIVOS_MODIFICADOS]")
            for file_path in self.processed_files:
                print(f"  - {file_path.relative_to(self.project_root)}")

def main():
    """Función principal."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    print(f"[INFO] Directorio del proyecto: {project_root}")
    
    remover = EmojiRemover(project_root)
    remover.process_all_files()

if __name__ == "__main__":
    main()