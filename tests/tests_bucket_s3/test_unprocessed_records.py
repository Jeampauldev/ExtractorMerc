#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.s3_massive_loader import S3MassiveLoader

def main():
    print("[EMOJI_REMOVIDO] Verificando registros no procesados...")
    
    loader = S3MassiveLoader()
    
    # Verificar Afinia
    records_afinia = loader.get_unprocessed_records('afinia')
    print(f"[DATOS] Afinia: {len(records_afinia)} registros no procesados")
    
    if records_afinia:
        print("  Primer registro:")
        print(f"    - Número: {records_afinia[0]['numero_radicado']}")
        print(f"    - Fecha: {records_afinia[0]['fecha']}")
        print(f"    - Empresa: {records_afinia[0]['empresa']}")
    
    # Verificar Aire
    records_aire = loader.get_unprocessed_records('aire') 
    print(f"[DATOS] Aire: {len(records_aire)} registros no procesados")
    
    if records_aire:
        print("  Primer registro:")
        print(f"    - Número: {records_aire[0]['numero_radicado']}")
        print(f"    - Fecha: {records_aire[0]['fecha']}")
        print(f"    - Empresa: {records_aire[0]['empresa']}")

if __name__ == "__main__":
    main()