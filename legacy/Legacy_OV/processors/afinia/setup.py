"""
Script de configuración e instalación del procesador de datos Afinia.

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


class AfiniaSetup:
    """Clase para configurar el procesador de Afinia."""

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
        print("[EMOJI_REMOVIDO] Instalando dependencias...")

        requirements = [
            "pandas>=1.5.0",
            "openpyxl>=3.0.0",
            "psycopg2-binary>=2.9.0",
            "python-dotenv>=0.19.0",
            "requests>=2.28.0",
            "beautifulsoup4>=4.11.0",
            "selenium>=4.0.0",
            "webdriver-manager>=3.8.0",
            "sqlalchemy>=1.4.0",
            "pydantic>=1.10.0"
        ]

        for requirement in requirements:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", requirement],
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.log(f"Instalado: {requirement}")
            except subprocess.CalledProcessError as e:
                self.log(f"Error instalando {requirement}: {e}", False)
                return False

        return True

    def create_directories(self):
        """Crea los directorios necesarios."""
        print("[EMOJI_REMOVIDO] Creando directorios...")

        directories = [
            self.base_dir / "data" / "input",
            self.base_dir / "data" / "output",
            self.base_dir / "data" / "processed",
            self.base_dir / "data" / "backup",
            self.base_dir / "data/logs",
            self.base_dir / "temp",
            self.base_dir / "config"
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.log(f"Directorio creado: {directory}")
            except Exception as e:
                self.log(f"Error creando directorio {directory}: {e}", False)
                return False

        return True

    def create_env_file(self):
        """Crea el archivo .env con configuración por defecto."""
        print("[CONFIGURACION] Configurando variables de entorno...")

        env_file = self.base_dir / ".env"
        env_content = """# Configuración de Base de Datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=afinia_db
DB_USER=afinia_user
DB_PASSWORD=your_password_here

# Configuración de Selenium
SELENIUM_HEADLESS=true
SELENIUM_TIMEOUT=30
SELENIUM_IMPLICIT_WAIT=10

# Configuración de Logging
LOG_LEVEL=INFO
LOG_FILE=logs/afinia_processor.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Configuración de Procesamiento
BATCH_SIZE=100
MAX_RETRIES=3
RETRY_DELAY=5

# URLs de Afinia
AFINIA_BASE_URL=https://oficinavirtual.afinia.com.co
AFINIA_LOGIN_URL=https://oficinavirtual.afinia.com.co/login

# Configuración de Archivos
INPUT_DIR=data/input
OUTPUT_DIR=data/output
PROCESSED_DIR=data/processed
BACKUP_DIR=data/backup
"""

        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            self.log(f"Archivo .env creado: {env_file}")
            return True
        except Exception as e:
            self.log(f"Error creando archivo .env: {e}", False)
            return False

    def create_config_file(self):
        """Crea el archivo de configuración JSON."""
        print("[EMOJI_REMOVIDO] Creando archivo de configuración...")

        config_file = self.base_dir / "config" / "afinia_config.json"
        config_data = {
            "database": {
                "table_name": "afinia_pqr",
                "connection_pool_size": 5,
                "connection_timeout": 30,
                "query_timeout": 60
            },
            "selenium": {
                "browser": "chrome",
                "window_size": [1920, 1080],
                "page_load_timeout": 30,
                "element_timeout": 10,
                "download_timeout": 120
            },
            "processing": {
                "chunk_size": 1000,
                "parallel_workers": 4,
                "memory_limit_mb": 512,
                "temp_cleanup": True
            },
            "validation": {
                "required_fields": [
                    "nic",
                    "fecha",
                    "documento_identidad",
                    "nombres_apellidos",
                    "numero_radicado",
                    "estado_solicitud"
                ],
                "field_lengths": {
                    "nic": 50,
                    "documento_identidad": 20,
                    "nombres_apellidos": 200,
                    "numero_radicado": 50,
                    "telefono": 20,
                    "celular": 20,
                    "correo_electronico": 100
                }
            },
            "logging": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "date_format": "%Y-%m-%d %H:%M:%S",
                "console_output": True,
                "file_output": True
            }
        }

        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            self.log(f"Archivo de configuración creado: {config_file}")
            return True
        except Exception as e:
            self.log(f"Error creando archivo de configuración: {e}", False)
            return False

    def test_database_connection(self):
        """Prueba la conexión a la base de datos."""
        print("[BASE_DATOS] Probando conexión a base de datos...")

        try:
            # Importar aquí para evitar errores si no están instaladas las dependencias
            from database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            if db_manager.test_connection():
                self.log("Conexión a base de datos exitosa")
                return True
            else:
                self.log("Error en conexión a base de datos", False)
                return False
        except ImportError:
            self.log("Módulo de base de datos no disponible - Saltando prueba", False)
            return True
        except Exception as e:
            self.log(f"Error probando conexión: {e}", False)
            return False

    def create_database_table(self):
        """Crea la tabla en la base de datos si no existe."""
        print("[EMOJI_REMOVIDO] Configurando tabla de base de datos...")

        try:
            from database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            if db_manager.create_table():
                self.log("Tabla de base de datos configurada")
                return True
            else:
                self.log("Error configurando tabla de base de datos", False)
                return False
        except ImportError:
            self.log("Módulo de base de datos no disponible - Saltando configuración", False)
            return True
        except Exception as e:
            self.log(f"Error configurando tabla: {e}", False)
            return False

    def verify_selenium_setup(self):
        """Verifica que Selenium esté configurado correctamente."""
        print("[EMOJI_REMOVIDO] Verificando configuración de Selenium...")

        try:
            from selenium import webdriver
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options

            # Configurar opciones de Chrome
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Configurar el servicio
            service = Service(ChromeDriverManager().install())

            # Crear driver de prueba
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get("https://www.google.com")
            driver.quit()

            self.log("Selenium configurado correctamente")
            return True
        except Exception as e:
            self.log(f"Error en configuración de Selenium: {e}", False)
            return False

    def create_sample_files(self):
        """Crea archivos de ejemplo."""
        print("[ARCHIVO] Creando archivos de ejemplo...")

        # Crear script de ejemplo
        example_script = self.base_dir / "example_usage.py"
        if not example_script.exists():
            self.log("Archivo de ejemplo ya existe")
        else:
            self.log("Archivo de ejemplo creado")

        # Crear archivo README
        readme_file = self.base_dir / "README.md"
        readme_content = """# Procesador de Datos Afinia

## Descripción
Este módulo procesa datos de PQR extraídos del sistema de oficina virtual de Afinia.

## Instalación
1. Ejecutar `python setup.py` para configuración inicial
2. Configurar variables de entorno en `.env`
3. Ejecutar `python example_usage.py` para prueba

## Uso
```python
from main import AfiniaProcessor

processor = AfiniaProcessor()
result = processor.process_file("data/input/archivo.json")
```

## Configuración
- `.env`: Variables de entorno
- `config/afinia_config.json`: Configuración detallada
- `logs/`: Archivos de log
- `data/`: Directorios de datos

## Dependencias
- pandas
- openpyxl
- psycopg2-binary
- selenium
- webdriver-manager
"""

        try:
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            self.log(f"README creado: {readme_file}")
            return True
        except Exception as e:
            self.log(f"Error creando README: {e}", False)
            return False

    def run_setup(self):
        """Ejecuta el setup completo."""
        print("[INICIANDO] Iniciando configuración del procesador Afinia...")
        print("=" * 60)

        setup_steps = [
            ("Verificar Python", self.check_python_version),
            ("Instalar dependencias", self.install_dependencies),
            ("Crear directorios", self.create_directories),
            ("Configurar variables de entorno", self.create_env_file),
            ("Crear configuración", self.create_config_file),
            ("Verificar Selenium", self.verify_selenium_setup),
            ("Probar base de datos", self.test_database_connection),
            ("Configurar tabla", self.create_database_table),
            ("Crear archivos de ejemplo", self.create_sample_files)
        ]

        success_count = 0
        total_steps = len(setup_steps)

        for step_name, step_function in setup_steps:
            print(f"\n[EMOJI_REMOVIDO] {step_name}...")
            try:
                if step_function():
                    success_count += 1
                else:
                    print(f"[ADVERTENCIA] Paso '{step_name}' completado con advertencias")
            except Exception as e:
                self.log(f"Error en paso '{step_name}': {e}", False)

        print("\n" + "=" * 60)
        print(f"[RESULTADO] Setup completado: {success_count}/{total_steps} pasos exitosos")

        if success_count == total_steps:
            print("[EXITOSO] ¡Configuración completada exitosamente!")
            print("\n[EMOJI_REMOVIDO] Próximos pasos:")
            print("1. Revisar y actualizar el archivo .env con tus credenciales")
            print("2. Configurar la conexión a base de datos")
            print("3. Ejecutar python example_usage.py para probar")
        else:
            print("[ADVERTENCIA] Configuración completada con algunas advertencias")
            print("[EMOJI_REMOVIDO] Revisar los logs para más detalles")

        # Guardar log del setup
        log_file = self.base_dir / "data/logs" / "setup.log"
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.setup_log, f, indent=2, ensure_ascii=False)
            print(f"[ARCHIVO] Log guardado en: {log_file}")
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo guardar el log: {e}")

        return success_count == total_steps


def main():
    """Función principal del setup."""
    setup = AfiniaSetup()
    return setup.run_setup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
