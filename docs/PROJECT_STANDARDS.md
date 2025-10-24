# Estándares del Proyecto Merc

## 1. Introducción

Este documento define la arquitectura, los estándares y las mejores prácticas a seguir en el desarrollo del proyecto `Merc`. El objetivo es asegurar un código consistente, mantenible y escalable.

## 2. Arquitectura de Carpetas

La estructura del proyecto se organiza de la siguiente manera, centrada completamente dentro de la carpeta `Merc`:

```
Merc/
├── .env                  # Archivo de variables de entorno. NO versionar.
├── .env.template         # Plantilla del archivo .env.
├── main.py               # Punto de entrada principal de la aplicación.
├── requirements.txt      # Dependencias de Python.
|
├── config/               # Módulos de configuración de la aplicación.
│   ├── __init__.py
│   └── env_loader.py     # Cargador centralizado de variables de entorno.
|
├── core/                 # Lógica de negocio central y clases base.
│   ├── __init__.py
│   ├── browser_manager.py  # Gestión del navegador web.
│   └── base_extractor.py   # Clase base para todos los extractores.
|
├── components/           # Componentes reutilizables para los flujos.
│   ├── __init__.py
│   ├── filter_manager.py   # Lógica para aplicar filtros.
│   └── popup_handler.py    # Lógica para manejar pop-ups.
|
├── services/             # Orquestadores de los flujos de extracción.
│   ├── __init__.py
│   ├── afinia_extractor.py # Orquesta el flujo completo para Afinia.
│   └── aire_extractor.py   # Orquesta el flujo completo para Aire.
|
├── utils/                # Utilidades generales (helpers, validadores, etc.).
│   └── __init__.py
|
├── tests/                # Pruebas unitarias y de integración.
│   └── __init__.py
|
└── docs/                 # Documentación del proyecto.
    └── PROJECT_STANDARDS.md
```

## 3. Gestión de la Configuración

- **Única Fuente de Verdad:** Toda la configuración que depende del entorno (credenciales, hosts, etc.) debe estar en el archivo `Merc/.env`.
- **Carga Centralizada:** El módulo `Merc/config/env_loader.py` es el único responsable de cargar y proveer acceso a estas variables.
- **No Credenciales en el Código:** Nunca se deben escribir credenciales o datos sensibles directamente en el código fuente.

## 4. Logging

- Se utilizará el módulo `logging` nativo de Python.
- La configuración del nivel de log (`LOG_LEVEL`), y si se escribe a fichero o consola, se gestionará a través de las variables en el archivo `.env`.
- Se debe crear un logger por módulo: `logger = logging.getLogger(__name__)`.

## 5. Convenciones de Nomenclatura

- **Archivos:** `snake_case.py` (ej. `browser_manager.py`).
- **Clases:** `PascalCase` (ej. `BrowserManager`).
- **Funciones y Métodos:** `snake_case()` (ej. `get_rds_config()`).
- **Variables y Constantes:** `snake_case` para variables, `UPPER_SNAKE_CASE` para constantes a nivel de módulo.
- **Métodos Privados:** `_internal_method()`.
