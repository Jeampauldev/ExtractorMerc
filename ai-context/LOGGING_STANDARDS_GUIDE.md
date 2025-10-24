# 🤖 Instrucciones para la Mejora del Logging (para Agentes IA)

**Objetivo:** Asegurar que todo el sistema de logging del proyecto `ExtractorMERC` cumpla con los estándares profesionales definidos, eliminando cualquier formato no conforme y garantizando una integración del 100% con el formato unificado.

---

## 1. Formato de Logging Obligatorio

Todos los mensajes de log deben adherirse estrictamente al siguiente formato profesional:

```log
[YYYY-MM-DD_HH:MM:SS][servicio][flujo][componente][LEVEL] - mensaje
```

**Ejemplos Correctos:**
*   `[2025-10-08_14:30:15][afinia][pagination][manager][INFO] - Procesando página 5 de 12`
*   `[2025-10-08_14:30:16][afinia][download][handler][EXITOSO] - Archivo descargado correctamente`
*   `[2025-10-08_14:30:17][afinia][filter][validator][ADVERTENCIA] - Filtro de fecha no especificado`
*   `[2025-10-08_14:30:18][afinia][session][manager][ERROR] - Fallo en conexión con servidor`

---

## 2. Reemplazo de Emojis y Términos Informales

**Acción:** Identificar y reemplazar cualquier emoji o término informal en los mensajes de log con su equivalente profesional, según la tabla definida en `PROJECT_STANDARDS.md`.

| Emoji | Reemplazo Profesional |
| :---- | :-------------------- |
| 🚀    | INICIANDO             |
| ✅    | EXITOSO               |
| ❌    | ERROR                 |
| ⚠️    | ADVERTENCIA           |
| 🔍    | VERIFICANDO           |
| 📅    | FECHA                 |
| 📁    | ARCHIVOS              |
| 📊    | PROCESADOS            |
| 📈    | METRICAS              |
| 📥    | DESCARGANDO           |
| 💾    | GUARDANDO             |
| ⏱️    | DURACION              |
| ⏳    | ESPERANDO             |
| 🏁    | COMPLETADO            |
| 🎉    | PROCESO_COMPLETADO    |
| 🧹    | LIMPIEZA              |
| 🧪    | MODO_TEST             |
| 🎯    | OBJETIVO              |
| 🔄    | REANUDANDO            |
| 📋    | LISTA                 |

**Elementos Prohibidos:**
*   Emojis de cualquier tipo.
*   Referencias a IA o automatización en logs.
*   Comentarios casuales o informales en logs.

---

## 3. Tarea Principal: Integración Completa del Logging Unificado

**Contexto:** Actualmente, el 95% de los logs ya utilizan el formato profesional, pero aún existen componentes con formatos mixtos (ej. `[COMPONENT] INFO:`).

**Directiva:**
1.  **Identificar:** Recorrer todos los archivos de código fuente (`.py`) dentro de la carpeta `src/`.
2.  **Detectar:** Buscar cualquier instancia de logging que no cumpla con el formato `[YYYY-MM-DD_HH:MM:SS][servicio][flujo][componente][LEVEL] - mensaje` o que contenga emojis/términos informales.
3.  **Refactorizar:** Modificar las llamadas a `logger.info()`, `logger.warning()`, `logger.error()`, `logger.debug()` para que generen mensajes que se ajusten al formato obligatorio y utilicen los reemplazos profesionales.
4.  **Asegurar Contexto:** Para cada mensaje de log, inferir y proporcionar los valores correctos para `[servicio]`, `[flujo]`, y `[componente]` basándose en la ubicación del archivo y la lógica circundante.
5.  **Verificar:** Después de aplicar los cambios, ejecutar el script de limpieza de emojis (`scripts/clean_emojis_professional.py --apply-all`) y validar que no queden logs no conformes.

**Prioridad:** **ALTA** - Esta es una tarea crítica para la estandarización y observabilidad del proyecto.

---

## 4. Uso de `logging.getLogger(__name__)`

**Directiva:** Asegurarse de que cada módulo Python que realice logging inicialice su logger de la siguiente manera:

```python
import logging
logger = logging.getLogger(__name__)
```

Esto permite una configuración granular y un seguimiento adecuado del origen de los mensajes.

---

## 5. Referencia Adicional

Para cualquier duda sobre los estándares de código o logging, consultar el documento `ai-context/PROJECT_STANDARDS.md`.