#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Limpiar Emojis y Aplicar Formato Profesional
=======================================================

Este script limpia emojis de archivos específicos y los reemplaza con
texto profesional, manteniendo la funcionalidad del sistema.

Desarrollado por: ISES | Analyst Data Jeam Paul Arcon Solano
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

class EmojiCleaner:
    """Clase para limpiar emojis y aplicar formato profesional"""
    
    # Mapeo de emojis específicos a texto profesional
    EMOJI_REPLACEMENTS = {
        # Inicio/Configuración
        '[INICIANDO]': 'INICIANDO',
        '[CONFIGURANDO]': 'CONFIGURANDO',
        '[CONFIGURACION]': 'CONFIGURACION',
        
        # Estado/Validación  
        '[EXITOSO]': 'EXITOSO',
        '[ERROR]': 'ERROR',
        '[ADVERTENCIA]': 'ADVERTENCIA',
        '[EMOJI_REMOVIDO]': 'VERIFICANDO',
        
        # Información/Datos
        '[EMOJI_REMOVIDO]': 'FECHA',
        '[EMOJI_REMOVIDO]': 'ARCHIVOS',
        '[ARCHIVO]': 'PAGINA',
        '[DATOS]': 'PROCESADOS',
        '[METRICAS]': 'METRICAS',
        '[EMOJI_REMOVIDO]': 'DESCARGANDO',
        '[EMOJI_REMOVIDO]': 'GUARDANDO',
        
        # Tiempo/Proceso
        '[TIEMPO]': 'DURACION',
        '⏳': 'ESPERANDO',
        
        # Finalización
        '[EMOJI_REMOVIDO]': 'COMPLETADO',
        '[COMPLETADO]': 'PROCESO_COMPLETADO',
        '🧹': 'LIMPIEZA',
        '🧪': 'MODO_TEST',
        
        # Otros
        '[RESULTADO]': 'OBJETIVO',
        '[EMOJI_REMOVIDO]': 'REANUDANDO',
        '[EMOJI_REMOVIDO]': 'LISTA'
    }
    
    def __init__(self, dry_run: bool = True):
        """
        Inicializa el limpiador de emojis
        
        Args:
            dry_run: Si True, solo muestra lo que se cambiaría sin hacer cambios
        """
        self.dry_run = dry_run
        self.changes_made = []
    
    def clean_file(self, file_path: str) -> bool:
        """
        Limpia emojis de un archivo específico
        
        Args:
            file_path: Ruta del archivo a limpiar
            
        Returns:
            bool: True si se hicieron cambios
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            changes_in_file = []
            
            # Aplicar reemplazos específicos
            for emoji, replacement in self.EMOJI_REPLACEMENTS.items():
                if emoji in content:
                    content = content.replace(emoji, replacement)
                    changes_in_file.append(f"  {emoji} -> {replacement}")
            
            # Remover cualquier emoji restante con patrón general
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs  
                u"\U0001F680-\U0001F6FF"  # transport & map
                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                u"\U00002500-\U00002BEF"  # chinese char
                u"\U00002702-\U000027B0"
                u"\U000024C2-\U0001F251"
                u"\U0001f926-\U0001f937"
                u"\U00010000-\U0010ffff"
                u"\u2640-\u2642" 
                u"\u2600-\u2B55"
                u"\u200d"
                u"\u23cf"
                u"\u23e9"
                u"\u231a"
                u"\ufe0f"  # dingbats
                u"\u3030"
                "]+", flags=re.UNICODE)
            
            # Verificar si hay emojis restantes
            remaining_emojis = emoji_pattern.findall(content)
            if remaining_emojis:
                content = emoji_pattern.sub('', content)
                changes_in_file.append(f"  Emojis restantes removidos: {set(remaining_emojis)}")
            
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                self.changes_made.append({
                    'file': file_path,
                    'changes': changes_in_file
                })
                return True
                
        except Exception as e:
            print(f"ERROR procesando {file_path}: {e}")
            return False
            
        return False
    
    def clean_critical_files(self) -> None:
        """Limpia archivos críticos del sistema"""
        
        critical_files = [
            'afinia_manager.py',
            'aire_manager.py'
        ]
        
        self._process_file_list(critical_files, "CRITICOS")
    
    def clean_component_files(self) -> None:
        """Limpia archivos de componentes menos críticos"""
        
        component_files = [
            'src/components/afinia_popup_handler.py',
            'src/components/afinia_filter_manager.py',
            'src/components/afinia_pagination_manager.py',
            'src/components/afinia_download_manager.py',
            'src/components/afinia_pqr_processor.py',
            'src/components/aire_pqr_processor.py',
            'src/components/popup_handler.py'
        ]
        
        self._process_file_list(component_files, "COMPONENTES")
    
    def clean_service_files(self) -> None:
        """Limpia archivos de servicios"""
        
        service_files = [
            'src/services/s3_uploader_service.py',
            'src/services/data_loader_service.py',
            'src/services/database_service.py'
        ]
        
        self._process_file_list(service_files, "SERVICIOS")
        
    def clean_extractor_files(self) -> None:
        """Limpia archivos de extractores principales"""
        
        extractor_files = [
            'src/extractors/afinia/oficina_virtual_afinia_modular.py',
            'src/extractors/aire/oficina_virtual_aire_modular.py',
            'src/core/download_manager.py',
            'src/utils/performance_monitor.py'
        ]
        
        self._process_file_list(extractor_files, "EXTRACTORES")
        
    def _process_file_list(self, files: list, category: str) -> None:
        """Procesa una lista de archivos de una categoria específica"""
        project_root = Path('C:/00_Project_Dev/ExtractorOV_Modular')
        
        print(f"LIMPIEZA DE EMOJIS - ARCHIVOS {category}")
        print("=" * 50)
        
        if self.dry_run:
            print("MODO: DRY RUN (Sin hacer cambios)")
        else:
            print("MODO: APLICAR CAMBIOS")
            
        print()
        
        for file_name in files:
            file_path = project_root / file_name
            
            if file_path.exists():
                print(f"Procesando: {file_name}")
                if self.clean_file(str(file_path)):
                    print(f"  CAMBIOS DETECTADOS en {Path(file_name).name}")
                else:
                    print(f"  Sin cambios necesarios en {Path(file_name).name}")
                print()
            else:
                print(f"ARCHIVO NO ENCONTRADO: {file_name}")
                print()
        
        project_root = Path('C:/00_Project_Dev/ExtractorOV_Modular')
        
        print("LIMPIEZA DE EMOJIS - ARCHIVOS CRITICOS")
        print("=" * 50)
        
        if self.dry_run:
            print("MODO: DRY RUN (Sin hacer cambios)")
        else:
            print("MODO: APLICAR CAMBIOS")
            
        print()
        
        for file_name in files:
            file_path = project_root / file_name
            
            if file_path.exists():
                print(f"Procesando: {file_name}")
                if self.clean_file(str(file_path)):
                    print(f"  CAMBIOS DETECTADOS en {Path(file_name).name}")
                else:
                    print(f"  Sin cambios necesarios en {Path(file_name).name}")
                print()
            else:
                print(f"ARCHIVO NO ENCONTRADO: {file_name}")
                print()
    
    def show_summary(self) -> None:
        """Muestra resumen de cambios realizados"""
        print("\nRESUMEN DE CAMBIOS:")
        print("=" * 30)
        
        if not self.changes_made:
            print("No se detectaron cambios necesarios")
            return
            
        for change in self.changes_made:
            print(f"\nArchivo: {Path(change['file']).name}")
            for change_detail in change['changes']:
                print(change_detail)

def main():
    """Función principal"""
    print("Script de Limpieza de Emojis - Formato Profesional")
    print("Desarrollado por: ISES | Analyst Data Jeam Paul Arcon Solano")
    print()
    
    # Primero ejecutar en modo dry-run para archivos críticos
    cleaner = EmojiCleaner(dry_run=True)
    cleaner.clean_critical_files()
    cleaner.show_summary()
    
    if cleaner.changes_made:
        print("\n" + "="*50)
        print("ATENCION: Se detectaron cambios necesarios")
        print("Opciones disponibles:")
        print("  --apply-critical    : Aplicar solo a archivos críticos")
        print("  --apply-components  : Aplicar a archivos de componentes")
        print("  --apply-services    : Aplicar a archivos de servicios")
        print("  --apply-extractors  : Aplicar a archivos de extractores")
        print("  --apply-all         : Aplicar a todos los archivos")
        print("="*50)

if __name__ == "__main__":
    import sys
    
    if '--apply-critical' in sys.argv:
        print("APLICANDO CAMBIOS A ARCHIVOS CRITICOS...")
        cleaner = EmojiCleaner(dry_run=False)
        cleaner.clean_critical_files() 
        cleaner.show_summary()
        
    elif '--apply-components' in sys.argv:
        print("APLICANDO CAMBIOS A COMPONENTES...")
        cleaner = EmojiCleaner(dry_run=False)
        cleaner.clean_component_files()
        cleaner.show_summary()
        
    elif '--apply-services' in sys.argv:
        print("APLICANDO CAMBIOS A SERVICIOS...")
        cleaner = EmojiCleaner(dry_run=False)
        cleaner.clean_service_files()
        cleaner.show_summary()
        
    elif '--apply-extractors' in sys.argv:
        print("APLICANDO CAMBIOS A EXTRACTORES...")
        cleaner = EmojiCleaner(dry_run=False)
        cleaner.clean_extractor_files()
        cleaner.show_summary()
        
    elif '--apply-all' in sys.argv:
        print("APLICANDO CAMBIOS A TODOS LOS ARCHIVOS...")
        cleaner = EmojiCleaner(dry_run=False)
        cleaner.clean_critical_files()
        cleaner.clean_component_files() 
        cleaner.clean_service_files()
        cleaner.clean_extractor_files()
        cleaner.show_summary()
        
    elif '--test-components' in sys.argv:
        print("PROBANDO COMPONENTES (DRY RUN)...")
        cleaner = EmojiCleaner(dry_run=True)
        cleaner.clean_component_files()
        cleaner.show_summary()
        
    elif '--test-services' in sys.argv:
        print("PROBANDO SERVICIOS (DRY RUN)...")
        cleaner = EmojiCleaner(dry_run=True)
        cleaner.clean_service_files()
        cleaner.show_summary()
        
    else:
        main()
