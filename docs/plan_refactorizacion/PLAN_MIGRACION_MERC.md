# Plan de Refactorización y Migración a `Merc`

## Objetivo Principal

El objetivo de este plan es transformar el proyecto `extractorMERC_modular` en una aplicación cohesiva y mantenible, centrada exclusivamente en la estructura de la carpeta `Merc`. Esto implica migrar la lógica funcional de `src_OV`, gestionar y limpiar el código heredado de `Merc/legacy`, y establecer una arquitectura clara y escalable para el futuro.

---

## Fases del Plan

### Fase 1: Análisis y Preparación (Corto Plazo)

**Meta:** Entender la estructura actual, identificar código reutilizable, y preparar el entorno para la migración.

**Acciones:**
1.  **Análisis de `src_OV`:**
    *   **Tarea:** Evaluar los componentes dentro de `src_OV` (especialmente en `components`, `config`, `core`, `processors`).
    *   **Resultado:** Documentar qué módulos son esenciales para los flujos de Afinia y Aire y cuáles pueden ser migrados directamente, adaptados o descartados.

2.  **Evaluación de `Merc/legacy`:**
    *   **Tarea:** Revisar el contenido de `Merc/legacy` (afinia, aire, extractorMerc, mercurio).
    *   **Resultado:** Clasificar cada subcarpeta como:
        *   **Migrar:** Contiene lógica útil que debe ser integrada en la nueva estructura de `Merc`.
        *   **Archivar:** Es obsoleto pero puede servir como referencia futura.
        *   **Eliminar:** No aporta valor y puede ser borrado.

3.  **Centralización de la Configuración:**
    *   **Tarea:** Unificar los diferentes archivos de configuración (`.env`, `config.py`, etc.) que se encuentran dispersos (`config/env`, `Merc/.env`, `src_OV/config`).
    *   **Resultado:** Crear un único punto de verdad para la configuración dentro de `Merc/config`, que gestione las variables de entorno y los parámetros de ejecución para todos los flujos.

4.  **Establecimiento de Estándares:**
    *   **Tarea:** Definir y documentar los estándares de codificación que se usarán en el proyecto `Merc`.
    *   **Resultado:** Crear un documento `PROJECT_STANDARDS.md` que incluya:
        *   Estructura de carpetas final.
        *   Normas de nombrado.
        *   Estrategia de logging unificada.
        *   Manejo de errores y excepciones.

---

### Fase 2: Construcción de la Base en `Merc`

**Meta:** Crear una estructura de aplicación sólida y centralizada dentro de la carpeta `Merc` que sirva como base para toda la funcionalidad.

**Acciones:**
1.  **Definir Arquitectura Final en `Merc`:**
    *   **Tarea:** Basado en el análisis, refinar la estructura de carpetas dentro de `Merc`. Se recomienda una estructura como:
        ```
        Merc/
        ├── core/         # Lógica de negocio central (auth, browser, db)
        ├── components/   # Componentes reutilizables (popups, filtros, paginación)
        ├── services/     # Orquestadores de flujos (afinia_extractor, aire_extractor)
        ├── utils/        # Utilidades generales (logging, validadores)
        ├── config/       # Configuración centralizada
        ├── tests/        # Pruebas unitarias e de integración
        └── main.py       # Punto de entrada principal
        ```
    *   **Resultado:** Crear las carpetas necesarias que falten en `Merc`.

2.  **Migrar Lógica Común y Central:**
    *   **Tarea:** Mover módulos base de `src_OV/core` y `src_OV/components` (ej. `BrowserManager`, `Authentication`, `PopupHandler`) a sus carpetas correspondientes en `Merc/core` y `Merc/components`.
    *   **Resultado:** Módulos centrales refactorizados y funcionando dentro de `Merc`, eliminando las dependencias de `src_OV`.

---

### Fase 3: Migración Incremental de Flujos

**Meta:** Migrar la funcionalidad de extracción de `src_OV` a la nueva estructura `Merc` de forma controlada, un flujo a la vez.

**Acciones:**
1.  **Migrar Flujo "Afinia":**
    *   **Tarea:** Mover y refactorizar toda la lógica específica de Afinia (`afinia_date_configurator`, `afinia_filter_manager`, etc.) de `src_OV` a la nueva estructura en `Merc`.
    *   **Resultado:** Un `afinia_extractor.py` en `Merc/services` que orquesta el flujo completo utilizando componentes y lógica de `Merc`. El script `run_afinia_only.py` deberá ser actualizado para usar este nuevo extractor.

2.  **Migrar Flujo "Aire":**
    *   **Tarea:** Repetir el proceso anterior para toda la lógica de Aire.
    *   **Resultado:** Un `aire_extractor.py` en `Merc/services` funcionando de manera análoga al de Afinia.

3.  **Actualizar Puntos de Entrada:**
    *   **Tarea:** Modificar `main.py` para que utilice exclusivamente los servicios y componentes de la estructura `Merc`.
    *   **Resultado:** El punto de entrada principal del proyecto ya no depende de `src_OV`.

---

### Fase 4: Desmantelamiento y Limpieza Final

**Meta:** Eliminar todo el código obsoleto para dejar una base de código limpia, moderna y fácil de mantener.

**Acciones:**
1.  **Archivar `Merc/legacy`:**
    *   **Tarea:** Comprimir la carpeta `Merc/legacy` en un archivo ZIP (`legacy_backup.zip`).
    *   **Resultado:** Eliminar la carpeta `Merc/legacy` del proyecto activo, manteniendo el archivo comprimido como referencia histórica.

2.  **Eliminar `src_OV`:**
    *   **Tarea:** Una vez que toda la funcionalidad haya sido migrada y verificada a través de pruebas, eliminar la carpeta `src_OV`.
    *   **Resultado:** El proyecto ahora solo contiene la estructura `Merc`.

---

### Fase 5: Verificación y Documentación

**Meta:** Asegurar la estabilidad del sistema refactorizado y documentar la nueva arquitectura para facilitar el mantenimiento futuro.

**Acciones:**
1.  **Pruebas Integrales:**
    *   **Tarea:** Ejecutar y/o crear una batería de pruebas `end-to-end` que validen los flujos completos de Afinia y Aire.
    *   **Resultado:** Confianza en que la refactorización no ha introducido regresiones.

2.  **Actualizar Documentación Principal:**
    *   **Tarea:** Modificar el `README.md` del proyecto para que refleje la nueva arquitectura, instrucciones de instalación y modo de uso.
    *   **Resultado:** Documentación actualizada que facilita la incorporación de nuevos desarrolladores al proyecto.
