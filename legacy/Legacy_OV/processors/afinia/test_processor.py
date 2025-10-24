"""
Script de pruebas para el procesador de datos de Afinia.

Este script verifica que todos los componentes del procesador funcionen
correctamente antes de usar en producción.
"""

import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Importar componentes del procesador
from config import AFINIA_CONFIG
from database_manager import AfiniaDatabaseManager
from validators import JSONValidator, validate_single_json
from models import AfiniaPQRData, TipoPQR, EstadoSolicitud, CanalRespuesta
from data_processor import AfiniaDataProcessor
from logger import setup_logging, get_logger


class TestProcessor:
    """Clase para ejecutar pruebas del procesador de Afinia."""

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
            print(f"  [EMOJI_REMOVIDO] {message}")

    def test_database_connection(self):
        """Prueba la conexión a la base de datos."""
        print("\n=== PRUEBA: Conexión a Base de Datos ===")

        try:
            db_manager = AfiniaDatabaseManager()
            connection_ok = db_manager.test_connection()

            if connection_ok:
                self.log_test("Conexión BD", True, "Conexión exitosa")

                # Probar creación de tabla
                table_ok = db_manager.create_pqr_table()
                self.log_test("Creación tabla", table_ok, 
                             "Tabla creada/verificada" if table_ok else "Error creando tabla")

                # Probar estadísticas
                stats = db_manager.get_table_stats()
                self.log_test("Estadísticas BD", stats is not None,
                             f"Registros: {stats.get('total_records', 'N/A')}" if stats else "Error obteniendo stats")
            else:
                self.log_test("Conexión BD", False, "No se pudo conectar")

            db_manager.close()

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
            "estado_solicitud": "En proceso",
            "tipo_pqr": "Petición",
            "canal_respuesta": "Correo electrónico",
            "telefono": "3001234567",
            "celular": "3001234567",
            "correo_electronico": "juan.perez@email.com",
            "direccion": "Calle 123 #45-67",
            "barrio": "Centro",
            "municipio": "Barranquilla",
            "departamento": "Atlántico",
            "descripcion": "Solicitud de información",
            "observaciones": "Ninguna"
        }

        # Crear JSON de prueba inválido
        json_invalido = {
            "nic": "",  # Campo requerido vacío
            "fecha": "fecha-invalida",  # Formato de fecha incorrecto
            "documento_identidad": "123",  # Muy corto
            # Faltan campos requeridos
        }

        try:
            # Probar validación exitosa
            validator = JSONValidator()
            resultado_valido = validator.validate_json_data(json_valido)
            self.log_test("Validación JSON válido", resultado_valido['is_valid'],
                         f"Errores: {len(resultado_valido.get('errors', []))}")

            # Probar validación fallida
            resultado_invalido = validator.validate_json_data(json_invalido)
            self.log_test("Validación JSON inválido", not resultado_invalido['is_valid'],
                         f"Errores detectados: {len(resultado_invalido.get('errors', []))}")

            # Probar función de validación individual
            resultado_individual = validate_single_json(json_valido)
            self.log_test("Validación individual", resultado_individual is not None,
                         "Función de validación individual funciona")

        except Exception as e:
            self.log_test("Validación JSON", False, f"Error: {e}")

    def test_data_models(self):
        """Prueba los modelos de datos."""
        print("\n=== PRUEBA: Modelos de Datos ===")

        try:
            # Probar creación de modelo desde JSON
            json_data = {
                "nic": "12345678901",
                "fecha": "2024-01-15",
                "documento_identidad": "12345678",
                "nombres_apellidos": "María García",
                "numero_radicado": "RAD-2024-002",
                "estado_solicitud": "Resuelto",
                "tipo_pqr": "Queja",
                "canal_respuesta": "Teléfono",
                "telefono": "3009876543",
                "celular": "3009876543",
                "correo_electronico": "maria.garcia@email.com",
                "direccion": "Carrera 50 #30-20",
                "barrio": "El Prado",
                "municipio": "Barranquilla",
                "departamento": "Atlántico",
                "descripcion": "Queja por servicio",
                "observaciones": "Resuelta satisfactoriamente"
            }

            # Crear modelo desde JSON
            pqr_data = AfiniaPQRData.from_json(json_data)
            self.log_test("Creación modelo desde JSON", pqr_data is not None,
                         f"NIC: {pqr_data.nic if pqr_data else 'N/A'}")

            # Probar conversión a diccionario
            if pqr_data:
                dict_data = pqr_data.to_dict()
                self.log_test("Conversión a diccionario", isinstance(dict_data, dict),
                             f"Campos: {len(dict_data)}")

                # Probar enums
                self.log_test("Enum TipoPQR", hasattr(TipoPQR, 'PETICION'),
                             "Enums definidos correctamente")
                self.log_test("Enum EstadoSolicitud", hasattr(EstadoSolicitud, 'EN_PROCESO'),
                             "Estados definidos correctamente")
                self.log_test("Enum CanalRespuesta", hasattr(CanalRespuesta, 'CORREO_ELECTRONICO'),
                             "Canales definidos correctamente")

        except Exception as e:
            self.log_test("Modelos de datos", False, f"Error: {e}")

    def test_data_processor(self):
        """Prueba el procesador de datos."""
        print("\n=== PRUEBA: Procesador de Datos ===")

        try:
            # Crear archivo temporal de prueba
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json_data = {
                    "nic": "98765432101",
                    "fecha": "2024-01-20",
                    "documento_identidad": "98765432",
                    "nombres_apellidos": "Carlos Rodríguez",
                    "numero_radicado": "RAD-2024-003",
                    "estado_solicitud": "En proceso",
                    "tipo_pqr": "Reclamo",
                    "canal_respuesta": "Presencial",
                    "telefono": "3005555555",
                    "celular": "3005555555",
                    "correo_electronico": "carlos.rodriguez@email.com",
                    "direccion": "Avenida 40 #80-15",
                    "barrio": "Villa Country",
                    "municipio": "Barranquilla",
                    "departamento": "Atlántico",
                    "descripcion": "Reclamo por facturación",
                    "observaciones": "Pendiente revisión"
                }
                json.dump(json_data, temp_file, ensure_ascii=False, indent=2)
                temp_file_path = temp_file.name

            # Crear procesador
            processor = AfiniaDataProcessor()
            self.log_test("Creación procesador", processor is not None,
                         "Procesador inicializado correctamente")

            # Probar procesamiento de archivo
            if processor:
                resultado = processor.process_file(temp_file_path)
                self.log_test("Procesamiento archivo", resultado is not None,
                             f"Resultado: {type(resultado).__name__}")

                # Probar procesamiento por lotes
                batch_resultado = processor.process_batch([temp_file_path])
                self.log_test("Procesamiento lote", batch_resultado is not None,
                             f"Archivos procesados: {len(batch_resultado) if batch_resultado else 0}")

            # Limpiar archivo temporal
            os.unlink(temp_file_path)

        except Exception as e:
            self.log_test("Procesador de datos", False, f"Error: {e}")

    def test_configuration(self):
        """Prueba la configuración del sistema."""
        print("\n=== PRUEBA: Configuración ===")

        try:
            # Verificar que la configuración existe
            self.log_test("Configuración existe", AFINIA_CONFIG is not None,
                         "Configuración cargada")

            # Verificar secciones principales
            if AFINIA_CONFIG:
                required_sections = ['database', 'paths', 'validation', 'processing']
                for section in required_sections:
                    has_section = section in AFINIA_CONFIG
                    self.log_test(f"Sección {section}", has_section,
                                 f"Configuración de {section} {'presente' if has_section else 'faltante'}")

                # Verificar configuración de base de datos
                if 'database' in AFINIA_CONFIG:
                    db_config = AFINIA_CONFIG['database']
                    required_db_fields = ['host', 'database', 'user', 'password']
                    for field in required_db_fields:
                        has_field = field in db_config
                        self.log_test(f"Campo DB {field}", has_field,
                                     f"Campo {field} {'configurado' if has_field else 'faltante'}")

        except Exception as e:
            self.log_test("Configuración", False, f"Error: {e}")

    def test_logging_system(self):
        """Prueba el sistema de logging."""
        print("\n=== PRUEBA: Sistema de Logging ===")

        try:
            # Probar configuración de logging
            logger = get_logger("test_logger")
            self.log_test("Creación logger", logger is not None,
                         "Logger creado correctamente")

            # Probar diferentes niveles de log
            if logger:
                logger.info("Mensaje de prueba INFO")
                logger.warning("Mensaje de prueba WARNING")
                logger.error("Mensaje de prueba ERROR")
                self.log_test("Mensajes de log", True,
                             "Mensajes enviados a diferentes niveles")

        except Exception as e:
            self.log_test("Sistema de logging", False, f"Error: {e}")

    def test_file_operations(self):
        """Prueba operaciones con archivos."""
        print("\n=== PRUEBA: Operaciones con Archivos ===")

        try:
            # Crear directorio temporal
            temp_dir = Path(tempfile.mkdtemp())
            self.log_test("Creación directorio temporal", temp_dir.exists(),
                         f"Directorio: {temp_dir}")

            # Crear archivo de prueba
            test_file = temp_dir / "test_data.json"
            test_data = {
                "test": "data",
                "timestamp": datetime.now().isoformat()
            }

            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)

            self.log_test("Creación archivo", test_file.exists(),
                         f"Archivo: {test_file.name}")

            # Leer archivo
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            self.log_test("Lectura archivo", loaded_data == test_data,
                         "Datos leídos correctamente")

            # Limpiar
            test_file.unlink()
            temp_dir.rmdir()

        except Exception as e:
            self.log_test("Operaciones con archivos", False, f"Error: {e}")

    def run_all_tests(self):
        """Ejecuta todas las pruebas."""
        print("🧪 INICIANDO SUITE DE PRUEBAS AFINIA")
        print("=" * 50)

        # Lista de pruebas a ejecutar
        tests = [
            ("Configuración", self.test_configuration),
            ("Sistema de Logging", self.test_logging_system),
            ("Operaciones con Archivos", self.test_file_operations),
            ("Modelos de Datos", self.test_data_models),
            ("Validación JSON", self.test_json_validation),
            ("Procesador de Datos", self.test_data_processor),
            ("Conexión Base de Datos", self.test_database_connection)
        ]

        # Ejecutar pruebas
        for test_name, test_function in tests:
            try:
                test_function()
            except Exception as e:
                self.log_test(f"Error en {test_name}", False, f"Excepción: {e}")

        # Generar reporte final
        self.generate_test_report()

    def generate_test_report(self):
        """Genera un reporte de las pruebas ejecutadas."""
        print("\n" + "=" * 50)
        print("[DATOS] REPORTE FINAL DE PRUEBAS")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests

        print(f"Total de pruebas: {total_tests}")
        print(f"[EXITOSO] Exitosas: {passed_tests}")
        print(f"[ERROR] Fallidas: {failed_tests}")
        print(f"[METRICAS] Tasa de éxito: {(passed_tests/total_tests*100):.1f}%")

        if failed_tests > 0:
            print("\n[ERROR] PRUEBAS FALLIDAS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")

        # Guardar reporte en archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(__file__).parent / f"test_report_{timestamp}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'summary': {
                        'total': total_tests,
                        'passed': passed_tests,
                        'failed': failed_tests,
                        'success_rate': passed_tests/total_tests*100,
                        'timestamp': datetime.now().isoformat()
                    },
                    'results': self.test_results
                }, f, ensure_ascii=False, indent=2)

            print(f"\n[ARCHIVO] Reporte guardado en: {report_file}")

        except Exception as e:
            print(f"[ADVERTENCIA] Error guardando reporte: {e}")

        return passed_tests == total_tests


def main():
    """Función principal para ejecutar las pruebas."""
    tester = TestProcessor()
    success = tester.run_all_tests()
    
    if success:
        print("\n[COMPLETADO] ¡Todas las pruebas pasaron exitosamente!")
        return 0
    else:
        print("\n[ADVERTENCIA] Algunas pruebas fallaron. Revisar el reporte.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
