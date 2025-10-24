"""
Script de Prueba - Sistema de Carga S3
======================================

Crea archivos PDF de prueba y verifica la funcionalidad del sistema.
"""

import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
import pytest

# Agregar el directorio del módulo al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.s3_uploader_service import S3UploaderService
from src.config.env_loader import get_s3_config


def create_test_pdf(file_path: Path, content: str):
    """Crea un PDF de prueba simple"""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        c = canvas.Canvas(str(file_path), pagesize=letter)
        width, height = letter
        
        # Título
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "Documento de Prueba")
        
        # Contenido
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 150, content)
        c.drawString(100, height - 180, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        c.save()
        return True
    except Exception as e:
        print(f"Error creando PDF: {e}")
        return False


def test_create_sample_files():
    """Crea archivos de prueba para testing"""
    print("\n" + "="*60)
    print("CREANDO: Archivos de prueba")
    print("="*60 + "\n")
    
    # Crear directorio de pruebas
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)
    
    # Crear archivos de prueba
    files = [
        ("factura_001_afinia.pdf", "Factura de prueba para Afinia"),
        ("pqr_002_aire.pdf", "PQR de prueba para Aire"),
        ("reporte_003_general.pdf", "Reporte general de prueba")
    ]
    
    created_files = []
    for filename, content in files:
        file_path = test_dir / filename
        if create_test_pdf(file_path, content):
            created_files.append(file_path)
            print(f"[EMOJI_REMOVIDO] Creado: {filename}")
        else:
            print(f"[EMOJI_REMOVIDO] Error creando: {filename}")
    
    return created_files


def test_s3_uploader_service():
    """Prueba el servicio de carga S3"""
    print("\n" + "="*60)
    print("PROBANDO: Servicio S3UploaderService")
    print("="*60 + "\n")
    
    try:
        # Obtener configuración
        config = get_s3_config()
        print(f"[EMOJI_REMOVIDO] Configuración S3 cargada")
        print(f"  Bucket: {config.get('bucket_name', 'No configurado')}")
        print(f"  Región: {config.get('region', 'No configurado')}")
        
        # Crear instancia del servicio
        uploader = S3UploaderService(config)
        print(f"[EMOJI_REMOVIDO] Servicio S3UploaderService inicializado")
        
        return True
    except Exception as e:
        print(f"[EMOJI_REMOVIDO] Error inicializando servicio: {e}")
        return False


def test_upload_single_file():
    """Prueba cargar un archivo individual"""
    print("\n" + "="*60)
    print("PROBANDO: Carga de archivo individual")
    print("="*60 + "\n")
    
    try:
        # Crear archivo de prueba
        test_file = Path("test_data/test_upload.pdf")
        if not create_test_pdf(test_file, "Archivo de prueba para carga S3"):
            print("[EMOJI_REMOVIDO] No se pudo crear archivo de prueba")
            return False
        
        # Obtener configuración y crear servicio
        config = get_s3_config()
        uploader = S3UploaderService(config)
        
        # Intentar carga (esto puede fallar si no hay credenciales válidas)
        print(f"Intentando cargar: {test_file.name}")
        result = uploader.upload_file(
            file_path=str(test_file),
            service_type="afinia",
            file_type="pdfs"
        )
        
        if result.success:
            print(f"[EMOJI_REMOVIDO] Archivo cargado exitosamente")
            print(f"  URL S3: {result.s3_url}")
            print(f"  Tamaño: {result.file_size_bytes} bytes")
            print(f"  Duración: {result.upload_duration_seconds}s")
            return True
        else:
            print(f"[EMOJI_REMOVIDO] Error en carga: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"[EMOJI_REMOVIDO] Error durante prueba: {e}")
        return False
    finally:
        # Limpiar archivo de prueba
        if test_file.exists():
            test_file.unlink()


def test_batch_upload():
    """Prueba carga masiva de archivos"""
    print("\n" + "="*60)
    print("PROBANDO: Carga masiva de archivos")
    print("="*60 + "\n")
    
    try:
        # Crear archivos de prueba
        created_files = test_create_sample_files()
        
        if not created_files:
            print("[EMOJI_REMOVIDO] No se pudieron crear archivos de prueba")
            return False
        
        # Obtener configuración y crear servicio
        config = get_s3_config()
        uploader = S3UploaderService(config)
        
        # Intentar carga masiva
        print(f"Intentando carga masiva de {len(created_files)} archivos")
        result = uploader.upload_directory(
            directory_path="test_data",
            service_type="general",
            file_type="reports"
        )
        
        print(f"Resultado de carga masiva:")
        print(f"  Total archivos: {result.total_files}")
        print(f"  Exitosos: {result.successful_uploads}")
        print(f"  Fallidos: {result.failed_uploads}")
        print(f"  Tamaño total: {result.total_size_bytes} bytes")
        
        return result.successful_uploads > 0
        
    except Exception as e:
        print(f"[EMOJI_REMOVIDO] Error durante carga masiva: {e}")
        return False
    finally:
        # Limpiar archivos de prueba
        test_dir = Path("test_data")
        if test_dir.exists():
            for file in test_dir.glob("*.pdf"):
                file.unlink()
            test_dir.rmdir()


def main():
    """Ejecuta todas las pruebas"""
    print("INICIANDO PRUEBAS DEL SISTEMA S3")
    print("="*80)
    
    tests = [
        ("Crear archivos de prueba", test_create_sample_files),
        ("Inicializar servicio S3", test_s3_uploader_service),
        ("Carga individual", test_upload_single_file),
        ("Carga masiva", test_batch_upload)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[EMOJI_REMOVIDO] Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE PRUEBAS")
    print("="*80)
    
    passed = 0
    for test_name, result in results:
        status = "[EMOJI_REMOVIDO] PASS" if result else "[EMOJI_REMOVIDO] FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{len(results)} pruebas exitosas")
    
    if passed == len(results):
        print("[COMPLETADO] Todas las pruebas pasaron!")
    else:
        print("[ADVERTENCIA]  Algunas pruebas fallaron. Revisar configuración S3.")


if __name__ == "__main__":
    main()
