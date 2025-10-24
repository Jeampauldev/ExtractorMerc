"""
Script de pruebas para el procesador de datos de Aire.

Este script verifica que todos los componentes del procesador funcionen
correctamente antes de usar en producción.
"""

import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Importar componentes del procesador
from .config import AIRE_CONFIG
from .database_manager import DatabaseManager
from .validators import JSONValidator, validate_single_json
from .models import AirePQRData, TipoPQR, EstadoSolicitud, CanalRespuesta
from .data_processor import AireDataProcessor
from .logger import setup_logging, get_logger


class TestProcessor:
    """Clase para ejecutar pruebas del procesador de Aire."""

    def __init__(self):
        self.logger = setup_logging(log_level=20)  # INFO level
        self.test_results = []

    def log_test(self, test_name, success, message=""):
        """Registra el resultado de una prueba."""
        status = "[EXITOSO] PASS" if success else "[ERROR] FAIL"
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")

    def test_database_connection(self):
        """Prueba la conexión a la base de datos."""
        print("\n=== PRUEBA: Conexión a Base de Datos ===")

        try:
            db_manager = DatabaseManager()
            connection_ok = db_manager.connect()

            if connection_ok:
                self.log_test("Conexión BD", True, "Conexión exitosa")

                # Probar creación de tabla
                table_ok = db_manager.create_tables()
                self.log_test("Creación tabla", table_ok, 
                             "Tabla creada/verificada" if table_ok else "Error creando tabla")

                # Probar estadísticas
                stats = db_manager.get_table_stats()
                self.log_test("Estadísticas BD", stats is not None,
                             f"Registros: {stats.get('total_records', 'N/A')}" if stats else "Error obteniendo stats")
            else:
                self.log_test("Conexión BD", False, "No se pudo conectar")

            db_manager.disconnect()

        except Exception as e:
            self.log_test("Conexión BD", False, f"Error: {e}")

    def test_json_validation(self):
        """Prueba la validación de archivos JSON."""
        print("\n=== PRUEBA: Validación JSON ===")

        # Crear JSON de prueba válido
        json_valido = {
            "nic": "12345678901",
            "fecha": "2024-01-15",
            "documento_identidad": "12345678",
            "nombres_apellidos": "Juan Pérez",
            "numero_radicado": "RAD-2024-001",
            "estado_solicitud": "PENDIENTE",
            "tipo_pqr": "PETICION",
            "canal_respuesta": "EMAIL",
            "email": "juan@example.com",
            "telefono": "3001234567",
            "direccion": "Calle 123 #45-67",
            "descripcion": "Solicitud de información"
        }

        # Crear JSON de prueba inválido
        json_invalido = {
            "nic": "123",  # Muy corto
            "fecha": "fecha-invalida",
            "documento_identidad": "",
            "nombres_apellidos": "",
            "numero_radicado": "",
            "estado_solicitud": "ESTADO_INEXISTENTE"
        }

        try:
            # Crear archivos temporales
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(json_valido, f, ensure_ascii=False, indent=2)
                archivo_valido = f.name

            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(json_invalido, f, ensure_ascii=False, indent=2)
                archivo_invalido = f.name

            # Probar validación con archivo válido
            resultado_valido = validate_single_json(archivo_valido)
            self.log_test("JSON válido", resultado_valido['valid'], 
                         "Archivo válido reconocido correctamente")

            # Probar validación con archivo inválido
            resultado_invalido = validate_single_json(archivo_invalido)
            self.log_test("JSON inválido", not resultado_invalido['valid'], 
                         f"Errores detectados: {len(resultado_invalido.get('errors', []))}")

            # Probar validador de clase
            validator = JSONValidator()
            
            # Validar datos directamente
            is_valid, errors = validator.validate_data(json_valido)
            self.log_test("Validador clase - válido", is_valid, 
                         "Datos válidos procesados correctamente")

            is_valid, errors = validator.validate_data(json_invalido)
            self.log_test("Validador clase - inválido", not is_valid, 
                         f"Errores encontrados: {len(errors)}")

            # Limpiar archivos temporales
            os.unlink(archivo_valido)
            os.unlink(archivo_invalido)

        except Exception as e:
            self.log_test("Validación JSON", False, f"Error: {e}")

    def test_data_models(self):
        """Prueba los modelos de datos."""
        print("\n=== PRUEBA: Modelos de Datos ===")

        try:
            # Probar creación de modelo válido
            datos_validos = {
                "nic": "12345678901",
                "fecha": "2024-01-15",
                "documento_identidad": "12345678",
                "nombres_apellidos": "Juan Pérez",
                "numero_radicado": "RAD-2024-001",
                "estado_solicitud": "PENDIENTE",
                "tipo_pqr": "PETICION",
                "canal_respuesta": "EMAIL",
                "email": "juan@example.com",
                "telefono": "3001234567",
                "direccion": "Calle 123 #45-67",
                "descripcion": "Solicitud de información"
            }

            # Crear instancia del modelo
            pqr_data = AirePQRData.from_json(datos_validos)
            self.log_test("Creación modelo", pqr_data is not None, 
                         "Modelo creado desde JSON correctamente")

            # Probar validación del modelo
            is_valid, errors = pqr_data.validate()
            self.log_test("Validación modelo", is_valid, 
                         "Modelo válido" if is_valid else f"Errores: {errors}")

            # Probar conversión a diccionario
            dict_data = pqr_data.to_dict()
            self.log_test("Conversión a dict", isinstance(dict_data, dict), 
                         f"Diccionario con {len(dict_data)} campos")

            # Probar enums
            self.log_test("Enum TipoPQR", hasattr(TipoPQR, 'PETICION'), 
                         "Enum TipoPQR disponible")
            self.log_test("Enum EstadoSolicitud", hasattr(EstadoSolicitud, 'PENDIENTE'), 
                         "Enum EstadoSolicitud disponible")
            self.log_test("Enum CanalRespuesta", hasattr(CanalRespuesta, 'EMAIL'), 
                         "Enum CanalRespuesta disponible")

        except Exception as e:
            self.log_test("Modelos de datos", False, f"Error: {e}")

    def test_data_processor(self):
        """Prueba el procesador de datos."""
        print("\n=== PRUEBA: Procesador de Datos ===")

        try:
            # Crear procesador
            processor = AireDataProcessor()
            self.log_test("Creación procesador", processor is not None, 
                         "Procesador inicializado correctamente")

            # Crear directorio temporal con archivos de prueba
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Crear archivo JSON de prueba
                json_data = {
                    "nic": "12345678901",
                    "fecha": "2024-01-15",
                    "documento_identidad": "12345678",
                    "nombres_apellidos": "Juan Pérez",
                    "numero_radicado": "RAD-2024-001",
                    "estado_solicitud": "PENDIENTE",
                    "tipo_pqr": "PETICION",
                    "canal_respuesta": "EMAIL",
                    "email": "juan@example.com"
                }

                json_file = temp_path / "test_pqr.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                # Probar procesamiento
                results = processor.process_directory(str(temp_path))
                self.log_test("Procesamiento directorio", results is not None, 
                             f"Procesados: {results.get('processed', 0)} archivos")

                # Probar estadísticas
                stats = processor.get_processing_stats()
                self.log_test("Estadísticas procesador", stats is not None, 
                             f"Total procesados: {stats.get('total_processed', 0)}")

        except Exception as e:
            self.log_test("Procesador de datos", False, f"Error: {e}")

    def test_configuration(self):
        """Prueba la configuración del sistema."""
        print("\n=== PRUEBA: Configuración ===")

        try:
            # Verificar que la configuración existe
            self.log_test("Config disponible", AIRE_CONFIG is not None, 
                         "Configuración cargada correctamente")

            # Verificar campos requeridos
            required_fields = ['database', 'processing', 'logging']
            for field in required_fields:
                has_field = hasattr(AIRE_CONFIG, field) or field in AIRE_CONFIG
                self.log_test(f"Config.{field}", has_field, 
                             f"Campo {field} presente en configuración")

        except Exception as e:
            self.log_test("Configuración", False, f"Error: {e}")

    def test_logging_system(self):
        """Prueba el sistema de logging."""
        print("\n=== PRUEBA: Sistema de Logging ===")

        try:
            # Probar configuración de logging
            logger = setup_logging()
            self.log_test("Setup logging", logger is not None, 
                         "Logger configurado correctamente")

            # Probar obtención de logger
            test_logger = get_logger("test")
            self.log_test("Get logger", test_logger is not None, 
                         "Logger específico obtenido")

            # Probar escritura de log
            test_logger.info("Mensaje de prueba del sistema de logging")
            self.log_test("Escritura log", True, 
                         "Mensaje de prueba escrito correctamente")

        except Exception as e:
            self.log_test("Sistema de logging", False, f"Error: {e}")

    def run_all_tests(self):
        """Ejecuta todas las pruebas disponibles."""
        print("🧪 INICIANDO SUITE DE PRUEBAS AIRE")
        print("=" * 50)

        # Lista de pruebas a ejecutar
        test_methods = [
            ("Configuración", self.test_configuration),
            ("Sistema de Logging", self.test_logging_system),
            ("Conexión BD", self.test_database_connection),
            ("Validación JSON", self.test_json_validation),
            ("Modelos de Datos", self.test_data_models),
            ("Procesador de Datos", self.test_data_processor)
        ]

        # Ejecutar cada prueba
        for test_name, test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(f"Error en {test_name}", False, f"Excepción: {e}")

        # Generar resumen
        self.generate_test_report()

        # Retornar resultados
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        return {
            'success': passed_tests == total_tests,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'results': self.test_results
        }

    def generate_test_report(self):
        """Genera un reporte detallado de las pruebas."""
        print("\n" + "=" * 50)
        print("[DATOS] RESUMEN DE PRUEBAS")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests

        print(f"Total de pruebas: {total_tests}")
        print(f"Pruebas exitosas: {passed_tests}")
        print(f"Pruebas fallidas: {failed_tests}")
        print(f"Tasa de éxito: {(passed_tests/total_tests*100):.1f}%")

        if failed_tests > 0:
            print("\n[ERROR] PRUEBAS FALLIDAS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")

        # Guardar reporte en archivo
        try:
            report_file = Path(__file__).parent / "test_report.json"
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0
                },
                'results': self.test_results
            }

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            print(f"\n[ARCHIVO] Reporte guardado en: {report_file}")

        except Exception as e:
            print(f"\n[ADVERTENCIA] Error guardando reporte: {e}")


def main():
    """Función principal para ejecutar las pruebas."""
    tester = TestProcessor()
    results = tester.run_all_tests()
    
    # Salir con código de error si hay pruebas fallidas
    exit_code = 0 if results['success'] else 1
    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())
