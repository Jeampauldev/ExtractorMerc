"""
Script de configuración e instalación del procesador de datos Aire.

Este script automatiza la configuración inicial del procesador, incluyendo:
- Instalación de dependencias
- Configuración de variables de entorno
- Creación de directorios necesarios
- Verificación de conexión a base de datos
- Configuración inicial de la tabla
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
from datetime import datetime


class AireSetup:
    """Clase para configurar el procesador de Aire."""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.project_root = self.base_dir.parent.parent
        self.setup_log = []

    def log(self, message, success=True):
        """Registra un mensaje del setup."""
        status = "[EXITOSO]" if success else "[ERROR]"
        log_entry = f"{status} {message}"
        print(log_entry)
        self.setup_log.append({
            'message': message,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })

    def check_python_version(self):
        """Verifica la versión de Python."""
        print("[EMOJI_REMOVIDO] Verificando versión de Python...")

        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self.log(f"Python {version.major}.{version.minor}.{version.micro} - Compatible")
            return True
        else:
            self.log(f"Python {version.major}.{version.minor}.{version.micro} - Requiere Python 3.8+", False)
            return False

    def install_dependencies(self):
        """Instala las dependencias necesarias."""
        print("\n[EMOJI_REMOVIDO] Instalando dependencias...")

        requirements_file = self.base_dir / "requirements.txt"

        if not requirements_file.exists():
            self.log("Archivo requirements.txt no encontrado", False)
            return False

        try:
            # Instalar dependencias
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True, check=True)

            self.log("Dependencias instaladas correctamente")
            return True

        except subprocess.CalledProcessError as e:
            self.log(f"Error instalando dependencias: {e.stderr}", False)
            return False

    def create_directories(self):
        """Crea los directorios necesarios."""
        print("\n[EMOJI_REMOVIDO] Creando directorios...")

        directories = [
            self.base_dir / "data/logs",
            self.base_dir / "output",
            self.base_dir / "errors",
            self.base_dir / "backups",
            self.base_dir / "reports"
        ]

        for directory in directories:
            try:
                directory.mkdir(exist_ok=True)
                self.log(f"Directorio creado: {directory.name}")
            except Exception as e:
                self.log(f"Error creando directorio {directory.name}: {e}", False)
                return False

        return True

    def setup_environment_file(self):
        """Configura el archivo de variables de entorno."""
        print("\n[CONFIGURANDO] Configurando variables de entorno...")

        env_example = self.base_dir / ".env.example"
        env_file = self.base_dir / ".env"

        if not env_example.exists():
            self.log("Archivo .env.example no encontrado", False)
            return False

        if env_file.exists():
            self.log("Archivo .env ya existe - no se sobrescribe")
            return True

        try:
            # Copiar archivo de ejemplo
            shutil.copy2(env_example, env_file)
            self.log("Archivo .env creado desde plantilla")

            print("\n[ADVERTENCIA] IMPORTANTE: Edita el archivo .env con tus credenciales reales")
            print(f"[EMOJI_REMOVIDO] Ubicación: {env_file}")

            return True

        except Exception as e:
            self.log(f"Error configurando archivo .env: {e}", False)
            return False

    def verify_database_connection(self):
        """Verifica la conexión a la base de datos."""
        print("\n[BASE_DATOS] Verificando conexión a base de datos...")

        try:
            # Importar el manager de base de datos
            from database_manager import DatabaseManager

            # Crear instancia del manager
            db_manager = DatabaseManager()

            # Intentar conectar
            if db_manager.connect():
                self.log("Conexión a base de datos exitosa")
                db_manager.disconnect()
                return True
            else:
                self.log("Error conectando a la base de datos", False)
                return False

        except ImportError:
            self.log("Módulo database_manager no encontrado", False)
            return False
        except Exception as e:
            self.log(f"Error verificando conexión: {e}", False)
            return False

    def setup_database_tables(self):
        """Configura las tablas necesarias en la base de datos."""
        print("\n[EMOJI_REMOVIDO] Configurando tablas de base de datos...")

        try:
            from database_manager import DatabaseManager

            db_manager = DatabaseManager()
            
            if not db_manager.connect():
                self.log("No se pudo conectar a la base de datos", False)
                return False

            # Crear tabla principal si no existe
            success = db_manager.create_tables()
            
            if success:
                self.log("Tablas de base de datos configuradas correctamente")
            else:
                self.log("Error configurando tablas de base de datos", False)

            db_manager.disconnect()
            return success

        except Exception as e:
            self.log(f"Error configurando tablas: {e}", False)
            return False

    def create_sample_config(self):
        """Crea un archivo de configuración de ejemplo."""
        print("\n[EMOJI_REMOVIDO] Creando configuración de ejemplo...")

        config_file = self.base_dir / "config_sample.json"

        sample_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "aire_pqr",
                "user": "usuario",
                "password": "contraseña"
            },
            "processing": {
                "batch_size": 1000,
                "max_workers": 4,
                "timeout_seconds": 300,
                "retry_attempts": 3
            },
            "logging": {
                "level": "INFO",
                "max_file_size_mb": 10,
                "backup_count": 5
            },
            "validation": {
                "strict_mode": True,
                "required_fields": [
                    "nic",
                    "fecha",
                    "documento_identidad",
                    "nombres_apellidos",
                    "numero_radicado",
                    "estado_solicitud"
                ]
            }
        }

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2, ensure_ascii=False)

            self.log(f"Configuración de ejemplo creada: {config_file.name}")
            return True

        except Exception as e:
            self.log(f"Error creando configuración de ejemplo: {e}", False)
            return False

    def run_tests(self):
        """Ejecuta las pruebas básicas del sistema."""
        print("\n🧪 Ejecutando pruebas básicas...")

        try:
            from test_processor import TestProcessor

            test_processor = TestProcessor()
            results = test_processor.run_all_tests()

            if results['success']:
                self.log("Todas las pruebas pasaron correctamente")
                return True
            else:
                self.log(f"Algunas pruebas fallaron: {results['failed_tests']}", False)
                return False

        except ImportError:
            self.log("Módulo test_processor no encontrado - omitiendo pruebas")
            return True
        except Exception as e:
            self.log(f"Error ejecutando pruebas: {e}", False)
            return False

    def generate_setup_report(self):
        """Genera un reporte del proceso de setup."""
        print("\n[DATOS] Generando reporte de configuración...")

        report_file = self.base_dir / "setup_report.json"

        report = {
            "setup_date": datetime.now().isoformat(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "setup_steps": self.setup_log,
            "success_count": len([log for log in self.setup_log if log['success']]),
            "error_count": len([log for log in self.setup_log if not log['success']]),
            "overall_success": all(log['success'] for log in self.setup_log)
        }

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            self.log(f"Reporte de configuración guardado: {report_file.name}")
            return True

        except Exception as e:
            self.log(f"Error generando reporte: {e}", False)
            return False

    def run_setup(self):
        """Ejecuta el proceso completo de configuración."""
        print("[INICIANDO] Iniciando configuración del procesador Aire")
        print("=" * 50)

        setup_steps = [
            ("Verificar versión de Python", self.check_python_version),
            ("Instalar dependencias", self.install_dependencies),
            ("Crear directorios", self.create_directories),
            ("Configurar variables de entorno", self.setup_environment_file),
            ("Verificar conexión a BD", self.verify_database_connection),
            ("Configurar tablas de BD", self.setup_database_tables),
            ("Crear configuración de ejemplo", self.create_sample_config),
            ("Ejecutar pruebas básicas", self.run_tests),
            ("Generar reporte", self.generate_setup_report)
        ]

        success_count = 0
        total_steps = len(setup_steps)

        for step_name, step_function in setup_steps:
            try:
                if step_function():
                    success_count += 1
                else:
                    print(f"\n[ADVERTENCIA] Paso fallido: {step_name}")
            except Exception as e:
                self.log(f"Error en paso '{step_name}': {e}", False)
                print(f"\n[ERROR] Error crítico en: {step_name}")

        print("\n" + "=" * 50)
        print(f"[METRICAS] Configuración completada: {success_count}/{total_steps} pasos exitosos")

        if success_count == total_steps:
            print("[COMPLETADO] ¡Configuración completada exitosamente!")
            print("\n[EMOJI_REMOVIDO] Próximos pasos:")
            print("1. Edita el archivo .env con tus credenciales")
            print("2. Revisa la configuración en config_sample.json")
            print("3. Ejecuta: python main.py --help para ver opciones")
        else:
            print("[ADVERTENCIA] Configuración completada con errores")
            print("[EMOJI_REMOVIDO] Revisa el archivo setup_report.json para más detalles")

        return success_count == total_steps


def main():
    """Función principal del script de setup."""
    setup = AireSetup()
    return setup.run_setup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
