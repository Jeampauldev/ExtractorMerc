#!/usr/bin/env python3
"""
Script de Prueba para Cargador de Archivos
Genera datos de prueba y ejecuta el cargador con archivos

Autor: Sistema de Extracción OV
Fecha: 2025-10-12
"""

import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

def create_test_data():
    """Crear estructura de datos de prueba"""
    
    # Directorio base para pruebas
    test_dir = Path("test_file_loader_data")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir()
    
    # Datos de prueba
    test_records = [
        {
            "numero_radicado": "RAD001",
            "numero_reclamo_sgc": "SGC001",
            "fecha": "2024/10/12 10:30",
            "estado_solicitud": "En proceso",
            "tipo_pqr": "Queja",
            "nombre_completo": "Juan Pérez García",
            "numero_documento": "12345678",
            "telefono": "3001234567",
            "email": "juan.perez@email.com",
            "direccion": "Calle 123 #45-67",
            "barrio": "Centro",
            "municipio": "Barranquilla",
            "departamento": "Atlántico",
            "nic": "NIC001",
            "descripcion_solicitud": "Solicitud de revisión de facturación",
            "respuesta_empresa": "Se procederá con la revisión",
            "observaciones": "Cliente solicita urgencia"
        },
        {
            "numero_radicado": "RAD002",
            "numero_reclamo_sgc": "SGC002",
            "fecha": "2024/10/12 11:45",
            "estado_solicitud": "Resuelto",
            "tipo_pqr": "Petición",
            "nombre_completo": "María López Rodríguez",
            "numero_documento": "87654321",
            "telefono": "3009876543",
            "email": "maria.lopez@email.com",
            "direccion": "Carrera 50 #30-20",
            "barrio": "El Prado",
            "municipio": "Barranquilla",
            "departamento": "Atlántico",
            "nic": "NIC002",
            "descripcion_solicitud": "Solicitud de reconexión del servicio",
            "respuesta_empresa": "Servicio reconectado exitosamente",
            "observaciones": "Pago realizado"
        },
        {
            "numero_radicado": "RAD003",
            "numero_reclamo_sgc": "SGC003",
            "fecha": "2024/10/12 14:20",
            "estado_solicitud": "Pendiente",
            "tipo_pqr": "Reclamo",
            "nombre_completo": "Carlos Martínez Silva",
            "numero_documento": "11223344",
            "telefono": "3005566778",
            "email": "carlos.martinez@email.com",
            "direccion": "Avenida 40 #25-15",
            "barrio": "Boston",
            "municipio": "Barranquilla",
            "departamento": "Atlántico",
            "nic": "NIC003",
            "descripcion_solicitud": "Reclamo por corte no programado",
            "respuesta_empresa": "En investigación",
            "observaciones": "Afectación múltiples usuarios"
        }
    ]
    
    # Crear estructura para cada registro
    for i, record in enumerate(test_records):
        numero_radicado = record["numero_radicado"]
        record_dir = test_dir / numero_radicado
        record_dir.mkdir()
        
        # 1. Crear archivo JSON
        json_file = record_dir / "pqr_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        
        # 2. Crear PDF simulado (archivo de texto)
        pdf_file = record_dir / "pqr_detail.pdf"
        pdf_content = f"""DETALLE DE PQR - {numero_radicado}
        
Número de Radicado: {record['numero_radicado']}
SGC: {record['numero_reclamo_sgc']}
Fecha: {record['fecha']}
Estado: {record['estado_solicitud']}
Tipo: {record['tipo_pqr']}

DATOS DEL SOLICITANTE:
Nombre: {record['nombre_completo']}
Documento: {record['numero_documento']}
Teléfono: {record['telefono']}
Email: {record['email']}

UBICACIÓN:
Dirección: {record['direccion']}
Barrio: {record['barrio']}
Municipio: {record['municipio']}
Departamento: {record['departamento']}
NIC: {record['nic']}

DESCRIPCIÓN:
{record['descripcion_solicitud']}

RESPUESTA:
{record['respuesta_empresa']}

OBSERVACIONES:
{record['observaciones']}

--- FIN DEL DOCUMENTO ---
"""
        with open(pdf_file, 'w', encoding='utf-8') as f:
            f.write(pdf_content)
        
        # 3. Crear adjuntos simulados (solo para algunos registros)
        if i < 2:  # Solo primeros 2 registros tendrán adjuntos
            adjuntos_dir = record_dir / "adjuntos"
            adjuntos_dir.mkdir()
            
            # Adjunto 1: Documento de identidad
            adjunto1 = adjuntos_dir / f"cedula_{record['numero_documento']}.pdf"
            with open(adjunto1, 'w', encoding='utf-8') as f:
                f.write(f"DOCUMENTO DE IDENTIDAD\nNúmero: {record['numero_documento']}\nNombre: {record['nombre_completo']}")
            
            # Adjunto 2: Factura (solo primer registro)
            if i == 0:
                adjunto2 = adjuntos_dir / f"factura_{record['nic']}.pdf"
                with open(adjunto2, 'w', encoding='utf-8') as f:
                    f.write(f"FACTURA DE SERVICIOS\nNIC: {record['nic']}\nCliente: {record['nombre_completo']}")
    
    print(f"Datos de prueba creados en: {test_dir.absolute()}")
    print(f"Registros creados: {len(test_records)}")
    
    # Mostrar estructura creada
    print("\nEstructura creada:")
    for record_dir in test_dir.iterdir():
        if record_dir.is_dir():
            print(f"\n{record_dir.name}/")
            for file_path in record_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(record_dir)
                    size_kb = file_path.stat().st_size / 1024
                    print(f"  {rel_path} ({size_kb:.1f} KB)")
    
    return test_dir

def run_file_loader_test(test_dir: Path, service_type: str = "afinia"):
    """Ejecutar prueba del cargador de archivos"""
    
    print(f"\n=== EJECUTANDO PRUEBA DE CARGADOR DE ARCHIVOS ===")
    print(f"Servicio: {service_type}")
    print(f"Directorio: {test_dir}")
    print("\n[INICIANDO] Iniciando cargador con monitor visual...")
    
    try:
        # Importar y ejecutar el cargador
        from direct_json_to_rds_loader_with_files import DirectLoaderWithFiles
        
        # Crear instancia del cargador con monitor visual habilitado
        loader = DirectLoaderWithFiles(
            service_type=service_type,
            input_directory=str(test_dir),
            enable_visual_monitor=True  # Habilitar visualización
        )
        
        # Ejecutar el proceso
        report = loader.run()
        
        print(f"\n[EXITOSO] Proceso completado")
        
        # Mostrar resultados
        print(f"\n=== RESULTADOS DE LA PRUEBA ===")
        print(f"Total de registros: {report['summary']['total_records']}")
        print(f"Procesados: {report['summary']['processed_records']}")
        print(f"Fallidos: {report['summary']['failed_records']}")
        print(f"Duplicados: {report['summary']['duplicate_records']}")
        print(f"Archivos subidos: {report['summary']['files_uploaded']}")
        print(f"Tamaño total: {report['summary']['total_size_mb']} MB")
        print(f"Tasa de éxito: {report['summary']['success_rate_percent']}%")
        print(f"Fallos S3: {report['summary']['s3_upload_failures']}")
        
        if report['errors']:
            print(f"\nErrores encontrados ({len(report['errors'])}):")
            for i, error in enumerate(report['errors'][:10], 1):
                print(f"  {i}. {error}")
            if len(report['errors']) > 10:
                print(f"  ... y {len(report['errors']) - 10} errores más")
        
        return report
        
    except Exception as e:
        print(f"[ERROR] Error ejecutando prueba: {e}")
        import traceback
        traceback.print_exc()
        return None

def cleanup_test_data(test_dir: Path):
    """Limpiar datos de prueba"""
    try:
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print(f"\nDatos de prueba eliminados: {test_dir}")
    except Exception as e:
        print(f"Error limpiando datos de prueba: {e}")

def main():
    """Función principal"""
    print("=== PRUEBA DE CARGADOR DE ARCHIVOS ===")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Crear datos de prueba
        print("\n1. Creando datos de prueba...")
        test_dir = create_test_data()
        
        # 2. Ejecutar prueba
        print("\n2. Ejecutando cargador de archivos...")
        report = run_file_loader_test(test_dir, "afinia")
        
        # 3. Guardar reporte de prueba
        if report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_report_file = f"test_file_loader_report_{timestamp}.json"
            
            with open(test_report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\nReporte de prueba guardado en: {test_report_file}")
        
        # 4. Preguntar si limpiar datos
        response = input("\n¿Desea eliminar los datos de prueba? (s/N): ").strip().lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            cleanup_test_data(test_dir)
        else:
            print(f"Datos de prueba conservados en: {test_dir.absolute()}")
        
        print("\n=== PRUEBA COMPLETADA ===")
        
    except KeyboardInterrupt:
        print("\nPrueba interrumpida por el usuario")
    except Exception as e:
        print(f"Error en prueba principal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()