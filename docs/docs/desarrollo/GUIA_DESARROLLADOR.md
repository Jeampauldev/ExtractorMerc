# Guía del Desarrollador - ExtractorOV Modular

## Introducción

Esta guía está dirigida a desarrolladores que trabajan en el sistema ExtractorOV Modular. Contiene información técnica detallada, estándares de código, y procedimientos de desarrollo.

## Estructura del Código

### Organización de Directorios

```
ExtractorOV_Modular/
├── src/                           # Código fuente principal
│   ├── components/                # Componentes modulares reutilizables
│   │   ├── afinia_*.py           # Componentes específicos de Afinia
│   │   └── aire_*.py             # Componentes específicos de Aire
│   ├── core/                     # Núcleo del sistema
│   │   ├── browser/              # Gestión de navegadores
│   │   ├── authentication/       # Manejo de autenticación
│   │   └── base/                 # Clases base abstractas
│   ├── services/                 # Servicios de infraestructura
│   │   ├── database_service.py   # Servicio de base de datos
│   │   ├── s3_uploader_service.py # Servicio de almacenamiento
│   │   └── data_loader_service.py # Cargador de datos
│   ├── extractors/               # Extractores por plataforma
│   │   ├── afinia/               # Extractor de Afinia
│   │   └── aire/                 # Extractor de Aire
│   ├── config/                   # Configuración del sistema
│   └── utils/                    # Utilidades generales
├── managers/                     # Gestores principales en raíz
│   ├── afinia_manager.py         # Gestor de Afinia
│   └── aire_manager.py           # Gestor de Aire
├── tests/                        # Suite de pruebas
├── docs/                         # Documentación
└── scripts/                      # Scripts de utilidad
```

### Convenciones de Nomenclatura

#### Archivos y Módulos
- **Formato**: `snake_case.py`
- **Prefijos por plataforma**: `afinia_*`, `aire_*`
- **Sufijos por tipo**: `*_manager.py`, `*_service.py`, `*_processor.py`

#### Clases
- **Formato**: `PascalCase`
- **Ejemplos**: `AfiniaManager`, `DatabaseService`, `PQRProcessor`
- **Sufijos**: `Manager`, `Service`, `Processor`, `Handler`

#### Funciones y Métodos
- **Formato**: `snake_case`
- **Ejemplos**: `extract_pqr_data()`, `apply_filters()`, `validate_credentials()`
- **Prefijos async**: `async def process_async()`

#### Variables y Constantes
- **Variables**: `snake_case`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Privadas**: `_variable_privada`
- **Muy privadas**: `__variable_muy_privada`

#### Configuración
- **Variables de entorno**: `UPPER_SNAKE_CASE`
- **Ejemplos**: `OV_AFINIA_USERNAME`, `DATABASE_URL`, `LOG_LEVEL`

## Arquitectura de Clases

### Clases Base

#### BaseExtractor
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseExtractor(ABC):
    """Clase base para todos los extractores de datos."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_authenticated = False
        self.browser = None
        
    @abstractmethod
    async def authenticate(self, username: str, password: str) -> bool:
        """Autentica en la plataforma correspondiente."""
        pass
        
    @abstractmethod
    async def extract_data(self) -> Dict[str, Any]:
        """Extrae datos de la plataforma."""
        pass
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Limpia recursos utilizados."""
        pass
```

#### BaseManager
```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseManager(ABC):
    """Clase base para gestores de extracción."""
    
    def __init__(self, headless: bool = True, test_mode: bool = False):
        self.headless = headless
        self.test_mode = test_mode
        self.extractor: Optional[BaseExtractor] = None
        
    @abstractmethod
    def setup_extractor(self) -> None:
        """Configura el extractor específico."""
        pass
        
    @abstractmethod
    async def run_extraction(self) -> Dict[str, Any]:
        """Ejecuta el proceso completo de extracción."""
        pass
```

#### BaseService
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseService(ABC):
    """Clase base para servicios del sistema."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_connected = False
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establece conexión con el servicio."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Cierra conexión con el servicio."""
        pass
        
    @abstractmethod
    def health_check(self) -> bool:
        """Verifica estado del servicio."""
        pass
```

### Interfaces Principales

#### ExtractionResult
```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class ExtractionResult:
    """Resultado de proceso de extracción."""
    success: bool
    total_records: int
    processed_records: int
    failed_records: int
    execution_time: float
    start_time: datetime
    end_time: datetime
    data: List[Dict[str, Any]]
    errors: List[str]
    metadata: Dict[str, Any]
    files_downloaded: List[str]
    
    @property
    def success_rate(self) -> float:
        """Calcula tasa de éxito."""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100
```

#### ConfigurationManager
```python
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SystemConfig:
    """Configuración del sistema."""
    # Credenciales
    afinia_username: str
    afinia_password: str
    aire_username: str
    aire_password: str
    
    # Base de datos
    database_url: str
    database_pool_size: int
    
    # S3
    s3_bucket: str
    s3_region: str
    aws_access_key: str
    aws_secret_key: str
    
    # Navegador
    headless_mode: bool
    page_timeout: int
    download_timeout: int
    
    # Logging
    log_level: str
    log_max_size_mb: int
    log_retention_days: int

class ConfigurationManager:
    """Gestor de configuración del sistema."""
    
    @classmethod
    def from_environment(cls) -> SystemConfig:
        """Crea configuración desde variables de entorno."""
        return SystemConfig(
            afinia_username=os.getenv('OV_AFINIA_USERNAME'),
            afinia_password=os.getenv('OV_AFINIA_PASSWORD'),
            aire_username=os.getenv('OV_AIRE_USERNAME'),
            aire_password=os.getenv('OV_AIRE_PASSWORD'),
            database_url=os.getenv('DATABASE_URL'),
            database_pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            s3_bucket=os.getenv('S3_BUCKET_NAME'),
            s3_region=os.getenv('S3_REGION', 'us-east-1'),
            aws_access_key=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            headless_mode=os.getenv('HEADLESS_MODE', 'true').lower() == 'true',
            page_timeout=int(os.getenv('PAGE_TIMEOUT', '30000')),
            download_timeout=int(os.getenv('DOWNLOAD_TIMEOUT', '120000')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_max_size_mb=int(os.getenv('LOG_MAX_SIZE_MB', '50')),
            log_retention_days=int(os.getenv('LOG_RETENTION_DAYS', '30'))
        )
```

## Sistema de Logging

### Configuración Unificada

El sistema utiliza un formato de logging profesional unificado:

```python
# src/config/unified_logging_config.py
import logging
import os
from datetime import datetime

class ProfessionalFormatter(logging.Formatter):
    """Formatter profesional para logs del sistema."""
    
    def format(self, record):
        # Formato: [YYYY-MM-DD_HH:MM:SS][servicio][core][componente][LEVEL] - mensaje
        timestamp = self.formatTime(record, '%Y-%m-%d_%H:%M:%S')
        service = getattr(record, 'service', 'sistema')
        core = getattr(record, 'core', 'principal')
        component = getattr(record, 'component', record.name)
        
        # Limpiar mensaje de caracteres no deseados
        clean_msg = record.getMessage().replace('🔍', '').replace('📁', '').strip()
        
        return f"[{timestamp}][{service}][{core}][{component}][{record.levelname}] - {clean_msg}"

def setup_logging(service_name: str, component_name: str, log_level: str = 'INFO'):
    """Configura logging unificado para componente."""
    logger = logging.getLogger(f"{service_name}.{component_name}")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Handler para archivo
    log_dir = "data/logs/current"
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"{service_name}_{component_name}.log"),
        encoding='utf-8'
    )
    file_handler.setFormatter(ProfessionalFormatter())
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ProfessionalFormatter())
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

### Uso del Sistema de Logging

```python
# En cualquier componente
from src.config.unified_logging_config import setup_logging

class AfiniaManager:
    def __init__(self):
        self.logger = setup_logging('afinia', 'manager', 'INFO')
        
    def process_data(self):
        self.logger.info("Iniciando procesamiento de datos")
        try:
            # Lógica de procesamiento
            self.logger.info("Procesamiento completado exitosamente")
        except Exception as e:
            self.logger.error(f"Error en procesamiento: {str(e)}")
```

## Manejo de Errores

### Excepciones Personalizadas

```python
# src/core/exceptions.py

class ExtractorOVError(Exception):
    """Excepción base del sistema."""
    pass

class AuthenticationError(ExtractorOVError):
    """Error de autenticación."""
    def __init__(self, platform: str, message: str = None):
        self.platform = platform
        default_msg = f"Fallo en autenticación para {platform}"
        super().__init__(message or default_msg)

class NavigationError(ExtractorOVError):
    """Error de navegación en páginas."""
    def __init__(self, url: str, message: str = None):
        self.url = url
        default_msg = f"Error navegando a {url}"
        super().__init__(message or default_msg)

class DataExtractionError(ExtractorOVError):
    """Error en extracción de datos."""
    def __init__(self, component: str, message: str = None):
        self.component = component
        default_msg = f"Error extrayendo datos en {component}"
        super().__init__(message or default_msg)

class DatabaseError(ExtractorOVError):
    """Error de base de datos."""
    def __init__(self, operation: str, message: str = None):
        self.operation = operation
        default_msg = f"Error en operación de base de datos: {operation}"
        super().__init__(message or default_msg)
```

### Manejo de Errores con Decoradores

```python
# src/utils/error_handling.py
import asyncio
import logging
from functools import wraps
from typing import Callable, Any

def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """Decorador para reintentar operaciones fallidas."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"Intento {attempt + 1} falló: {str(e)}. Reintentando en {delay}s...")
                        await asyncio.sleep(delay * (2 ** attempt))  # Backoff exponencial
                    else:
                        logging.error(f"Todos los intentos fallaron para {func.__name__}")
            
            raise last_exception
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"Intento {attempt + 1} falló: {str(e)}. Reintentando en {delay}s...")
                        import time
                        time.sleep(delay * (2 ** attempt))
                    else:
                        logging.error(f"Todos los intentos fallaron para {func.__name__}")
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def handle_extraction_errors(func: Callable) -> Callable:
    """Decorador para manejo específico de errores de extracción."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except AuthenticationError as e:
            logging.error(f"Error de autenticación en {e.platform}: {str(e)}")
            raise
        except NavigationError as e:
            logging.error(f"Error de navegación a {e.url}: {str(e)}")
            raise
        except DataExtractionError as e:
            logging.error(f"Error de extracción en {e.component}: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Error inesperado en {func.__name__}: {str(e)}")
            raise ExtractorOVError(f"Error inesperado: {str(e)}")
    
    return wrapper
```

## Testing

### Estructura de Pruebas

```
tests/
├── unit/                         # Pruebas unitarias
│   ├── test_managers.py         # Pruebas de managers
│   ├── test_services.py         # Pruebas de servicios
│   ├── test_components.py       # Pruebas de componentes
│   └── test_utils.py           # Pruebas de utilidades
├── integration/                 # Pruebas de integración
│   ├── test_afinia_flow.py     # Flujo completo Afinia
│   ├── test_aire_flow.py       # Flujo completo Aire
│   └── test_database.py        # Integración con DB
├── fixtures/                    # Datos de prueba
│   ├── sample_pqr_data.json    # Datos de ejemplo PQRs
│   └── config_test.py          # Configuración de pruebas
└── conftest.py                 # Configuración pytest
```

### Ejemplos de Pruebas Unitarias

```python
# tests/unit/test_managers.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.managers.afinia_manager import AfiniaManager
from src.core.exceptions import AuthenticationError

class TestAfiniaManager:
    
    @pytest.fixture
    def manager(self):
        """Fixture para AfiniaManager."""
        return AfiniaManager(headless=True, test_mode=True)
    
    def test_manager_initialization(self, manager):
        """Prueba inicialización correcta del manager."""
        assert manager.headless is True
        assert manager.test_mode is True
        assert manager.extractor is None
    
    @pytest.mark.asyncio
    async def test_successful_authentication(self, manager):
        """Prueba autenticación exitosa."""
        # Mock del extractor
        manager.extractor = AsyncMock()
        manager.extractor.authenticate.return_value = True
        
        result = await manager.authenticate("usuario", "password")
        
        assert result is True
        manager.extractor.authenticate.assert_called_once_with("usuario", "password")
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self, manager):
        """Prueba fallo en autenticación."""
        manager.extractor = AsyncMock()
        manager.extractor.authenticate.side_effect = AuthenticationError("afinia", "Credenciales inválidas")
        
        with pytest.raises(AuthenticationError):
            await manager.authenticate("usuario_malo", "password_malo")
```

### Pruebas de Integración

```python
# tests/integration/test_afinia_flow.py
import pytest
import os
from unittest.mock import patch
from src.managers.afinia_manager import AfiniaManager

@pytest.mark.integration
class TestAfiniaIntegrationFlow:
    
    @pytest.mark.skipif(not os.getenv('RUN_INTEGRATION_TESTS'), 
                       reason="Pruebas de integración deshabilitadas")
    @pytest.mark.asyncio
    async def test_complete_extraction_flow(self):
        """Prueba flujo completo de extracción de Afinia."""
        manager = AfiniaManager(headless=True, test_mode=True)
        
        # Configurar datos de prueba
        with patch.dict(os.environ, {
            'OV_AFINIA_USERNAME': 'usuario_test',
            'OV_AFINIA_PASSWORD': 'password_test'
        }):
            result = await manager.run_extraction()
            
            assert result.success is True
            assert result.total_records >= 0
            assert isinstance(result.data, list)
```

### Configuración de Pytest

```python
# conftest.py
import pytest
import asyncio
import os
from unittest.mock import Mock

@pytest.fixture(scope="session")
def event_loop():
    """Fixture para event loop de asyncio."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_config():
    """Fixture para configuración mock."""
    return {
        'headless_mode': True,
        'page_timeout': 5000,
        'download_timeout': 10000,
        'log_level': 'DEBUG'
    }

@pytest.fixture
def mock_database():
    """Fixture para base de datos mock."""
    return Mock()

# Markers personalizados
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marca pruebas como de integración"
    )
    config.addinivalue_line(
        "markers", "slow: marca pruebas lentas"
    )
```

## Desarrollo de Nuevas Funcionalidades

### Checklist para Nuevos Componentes

1. **Crear estructura base**:
   - [ ] Definir clase que herede de clase base apropiada
   - [ ] Implementar métodos abstractos requeridos
   - [ ] Agregar logging unificado
   - [ ] Implementar manejo de errores

2. **Documentar**:
   - [ ] Docstrings en español para todas las clases y métodos
   - [ ] Type hints completos
   - [ ] Ejemplos de uso en docstrings
   - [ ] Actualizar documentación técnica

3. **Testing**:
   - [ ] Pruebas unitarias con cobertura > 80%
   - [ ] Pruebas de integración si aplica
   - [ ] Pruebas de manejo de errores
   - [ ] Fixtures para datos de prueba

4. **Código limpio**:
   - [ ] Seguir convenciones de nomenclatura
   - [ ] Eliminar emojis del código
   - [ ] Aplicar formateo con Black
   - [ ] Verificar con Flake8

### Ejemplo de Nuevo Componente

```python
# src/components/nuevo_procesador.py
from typing import Dict, List, Any
from src.core.base import BaseProcessor
from src.config.unified_logging_config import setup_logging
from src.core.exceptions import DataExtractionError
from src.utils.error_handling import retry_on_error

class NuevoProcesador(BaseProcessor):
    """
    Procesador para nueva funcionalidad específica.
    
    Este componente maneja el procesamiento de datos específicos
    siguiendo los estándares del sistema.
    
    Attributes:
        config (Dict[str, Any]): Configuración del procesador
        logger: Logger configurado para el componente
        
    Example:
        ```python
        config = {'timeout': 30, 'max_items': 100}
        procesador = NuevoProcesador(config)
        resultado = await procesador.procesar_datos(datos)
        ```
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = setup_logging('sistema', 'nuevo_procesador')
        self.datos_procesados = []
        
    @retry_on_error(max_retries=3, delay=1.0)
    async def procesar_datos(self, datos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Procesa lista de datos según lógica específica.
        
        Args:
            datos: Lista de diccionarios con datos a procesar
            
        Returns:
            Dict con resultado del procesamiento incluyendo:
            - success: bool indicando éxito
            - processed_count: número de elementos procesados
            - errors: lista de errores encontrados
            
        Raises:
            DataExtractionError: Si falla el procesamiento
        """
        self.logger.info(f"Iniciando procesamiento de {len(datos)} elementos")
        
        resultado = {
            'success': False,
            'processed_count': 0,
            'errors': []
        }
        
        try:
            for i, item in enumerate(datos):
                try:
                    processed_item = await self._procesar_item_individual(item)
                    self.datos_procesados.append(processed_item)
                    resultado['processed_count'] += 1
                    
                except Exception as e:
                    error_msg = f"Error procesando item {i}: {str(e)}"
                    self.logger.warning(error_msg)
                    resultado['errors'].append(error_msg)
            
            resultado['success'] = resultado['processed_count'] > 0
            self.logger.info(f"Procesamiento completado: {resultado['processed_count']} elementos")
            
        except Exception as e:
            self.logger.error(f"Error crítico en procesamiento: {str(e)}")
            raise DataExtractionError('nuevo_procesador', str(e))
            
        return resultado
    
    async def _procesar_item_individual(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un elemento individual."""
        # Lógica específica de procesamiento
        return {
            'original': item,
            'processed_at': self._get_timestamp(),
            'status': 'processed'
        }
```

## Integración Continua

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.8
  
  - repo: https://github.com/PyCQA/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Pipeline de CI/CD

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        
    - name: Run linting
      run: |
        flake8 src/ tests/
        black --check src/ tests/
        
    - name: Run tests
      run: |
        pytest tests/unit/ -v --cov=src/
        
    - name: Run integration tests
      if: github.ref == 'refs/heads/main'
      run: |
        pytest tests/integration/ -v
      env:
        RUN_INTEGRATION_TESTS: true
```

## Herramientas de Desarrollo

### Configuración del IDE

#### VS Code Settings
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

### Scripts de Desarrollo

```bash
# scripts/dev-setup.sh
#!/bin/bash

echo "Configurando entorno de desarrollo..."

# Crear entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Instalar pre-commit hooks
pre-commit install

# Instalar navegadores para testing
playwright install

echo "Entorno configurado exitosamente!"
```

## Mejores Prácticas

### Código Limpio

1. **Funciones pequeñas**: Máximo 20 líneas por función
2. **Responsabilidad única**: Una función, una responsabilidad
3. **Nombres descriptivos**: Variables y funciones autoexplicativas
4. **Sin código duplicado**: Refactorizar código repetido
5. **Comentarios útiles**: Solo cuando el código no es autoexplicativo

### Performance

1. **Async/await**: Usar para operaciones I/O
2. **Lazy loading**: Cargar datos solo cuando se necesiten
3. **Connection pooling**: Para bases de datos
4. **Caching**: Para datos frecuentemente accedidos
5. **Profiling**: Medir antes de optimizar

### Seguridad

1. **Secrets management**: Nunca hardcodear credenciales
2. **Input validation**: Validar todas las entradas
3. **SQL injection**: Usar queries parametrizadas
4. **Logs sanitization**: No loguear información sensible
5. **Error handling**: No exponer información interna

---

**Guía del Desarrollador - ExtractorOV Modular**
*Versión: 2.0*
*Última actualización: Octubre 2025*