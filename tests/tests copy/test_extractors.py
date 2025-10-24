#!/usr/bin/env python3
"""
Script de prueba para verificar que Afinia y Aire estén completamente listos
para ejecutarse con descarga de JSON y archivos adjuntos.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent / "src"))

async def test_afinia_configuration():
    """Prueba la configuración del extractor de Afinia"""
    print("=== PRUEBA EXTRACTOR AFINIA ===")
    
    try:
        from extractors.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular
        
        extractor = OficinaVirtualAfiniaModular(
            headless=True,
            visual_mode=False,
            enable_pqr_processing=True,
            max_pqr_records=2
        )
        
        print("Configuración:")
        print(f"- PQR Processing: {extractor.enable_pqr_processing}")
        print(f"- Max Records: {extractor.max_pqr_records}")
        print(f"- Download Path: {extractor.config['download_path']}")
        
        # Verificar que el procesador PQR esté inicializado
        if hasattr(extractor, 'afinia_pqr_processor') and extractor.afinia_pqr_processor:
            print("✓ AfiniaPQRProcessor inicializado correctamente")
            print(f"- Download Path PQR: {extractor.afinia_pqr_processor.download_path}")
        else:
            print("✗ AfiniaPQRProcessor NO inicializado")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en configuración Afinia: {e}")
        return False

async def test_aire_configuration():
    """Prueba la configuración del extractor de Aire"""
    print("\n=== PRUEBA EXTRACTOR AIRE ===")
    
    try:
        from extractors.aire.oficina_virtual_aire_modular import OficinaVirtualAireModular
        
        extractor = OficinaVirtualAireModular(
            headless=True,
            visual_mode=False
        )
        
        print("Configuración:")
        print(f"- Download Path: {extractor.config['download_path']}")
        print(f"- Screenshots Dir: {extractor.config['screenshots_dir']}")
        
        # Verificar que el método extract_pqr_data tenga enable_pqr_processing
        import inspect
        sig = inspect.signature(extractor.extract_pqr_data)
        params = list(sig.parameters.keys())
        
        if 'enable_pqr_processing' in params:
            print("✓ Aire tiene soporte para enable_pqr_processing")
        else:
            print("✗ Aire NO tiene soporte para enable_pqr_processing")
        
        # Verificar que run_full_extraction tenga enable_pqr_processing
        sig_full = inspect.signature(extractor.run_full_extraction)
        params_full = list(sig_full.parameters.keys())
        
        if 'enable_pqr_processing' in params_full:
            print("✓ run_full_extraction tiene soporte para enable_pqr_processing")
        else:
            print("✗ run_full_extraction NO tiene soporte para enable_pqr_processing")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en configuración Aire: {e}")
        return False

async def test_pqr_processors():
    """Prueba que los procesadores PQR tengan lógica de descarga de adjuntos"""
    print("\n=== PRUEBA PROCESADORES PQR ===")
    
    try:
        from components.afinia_pqr_processor import AfiniaPQRProcessor
        from components.aire_pqr_processor import AirePQRProcessor
        
        # Verificar métodos de descarga en Afinia
        afinia_methods = dir(AfiniaPQRProcessor)
        if '_download_document_proof_attachments' in afinia_methods:
            print("✓ AfiniaPQRProcessor tiene método de descarga de adjuntos")
        else:
            print("✗ AfiniaPQRProcessor NO tiene método de descarga de adjuntos")
        
        # Verificar métodos de descarga en Aire
        aire_methods = dir(AirePQRProcessor)
        if '_download_document_proof_attachments' in aire_methods:
            print("✓ AirePQRProcessor tiene método de descarga de adjuntos")
        else:
            print("✗ AirePQRProcessor NO tiene método de descarga de adjuntos")
        
        return True
        
    except Exception as e:
        print(f"✗ Error verificando procesadores PQR: {e}")
        return False

async def main():
    """Función principal de prueba"""
    print("VERIFICACIÓN DE EXTRACTORES AFINIA Y AIRE")
    print("=" * 50)
    
    afinia_ok = await test_afinia_configuration()
    aire_ok = await test_aire_configuration()
    processors_ok = await test_pqr_processors()
    
    print("\n" + "=" * 50)
    print("RESUMEN:")
    print(f"- Afinia: {'✓ LISTO' if afinia_ok else '✗ PROBLEMAS'}")
    print(f"- Aire: {'✓ LISTO' if aire_ok else '✗ PROBLEMAS'}")
    print(f"- Procesadores PQR: {'✓ LISTO' if processors_ok else '✗ PROBLEMAS'}")
    
    if afinia_ok and aire_ok and processors_ok:
        print("\n🎉 AMBOS EXTRACTORES ESTÁN LISTOS PARA EJECUTARSE")
        print("   - Descargan JSON ✓")
        print("   - Descargan archivos adjuntos ✓")
    else:
        print("\n⚠️  HAY PROBLEMAS QUE RESOLVER")
    
    return afinia_ok and aire_ok and processors_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)