# Módulo de Integración de IA

## 🎯 Descripción

Este módulo integra múltiples servicios de IA para mejorar significativamente el proceso de extracción y análisis de documentos PQR. Combina las capacidades de **Gemini Free API**, **Stagehand** y **Model Context Protocol (MCP)** para proporcionar:

- 🧠 **Análisis inteligente** de documentos con IA
- 🤖 **Automatización web** con lenguaje natural  
- 🔗 **Comunicación estructurada** entre servicios
- 🎼 **Orquestación** de workflows complejos

## 🏗️ Arquitectura

```
src/services/ai_integration/
├── __init__.py              # Punto de entrada del módulo
├── config.py                # Configuración y credenciales
├── gemini_service.py        # Servicio Google Gemini
├── stagehand_service.py     # Servicio Stagehand
├── mcp_service.py          # Model Context Protocol
├── orchestrator.py         # Orquestador principal
├── examples.py             # Ejemplos de uso
├── requirements.txt        # Dependencias específicas
└── README.md              # Esta documentación
```

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r src/services/ai_integration/requirements.txt
```

### 2. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Gemini API
GEMINI_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-1.5-flash
GEMINI_MAX_TOKENS=8192

# Stagehand
STAGEHAND_API_KEY=tu_stagehand_key_aqui
STAGEHAND_ENDPOINT=https://api.stagehand.dev
STAGEHAND_MODEL=gpt-4o

# MCP (Opcional)
MCP_ENABLED=true
MCP_SERVER_URL=localhost:8080
```

### 3. Verificar configuración

```python
from src.services.ai_integration.config import get_ai_config

config = get_ai_config()
print(f"Configuración válida: {config.is_configured()}")
```

## 📖 Uso Básico

### Análisis rápido de PQR

```python
from src.services.ai_integration import quick_pqr_analysis

# Documento de ejemplo
document = {
    "content": "Reclamo por facturación incorrecta..."
}

# Análisis automático
result = await quick_pqr_analysis(document)
print(f"Éxito: {result['success']}")
print(f"Análisis: {result['analysis']}")
```

### Extracción web inteligente

```python
from src.services.ai_integration import quick_web_extraction

# Extraer datos de una página
result = await quick_web_extraction(
    url="https://ejemplo.com/pqr/12345",
    instructions="Extraer número de PQR, fecha y descripción"
)

print(f"Datos extraídos: {result['extracted_data']}")
```

### Workflow completo con orquestador

```python
from src.services.ai_integration.orchestrator import AIOrchestrator, WorkflowType

async with AIOrchestrator() as orchestrator:
    result = await orchestrator.execute_workflow(
        WorkflowType.DOCUMENT_ANALYSIS,
        {"document_content": "contenido del PQR..."}
    )
    
    print(f"Pasos completados: {result.steps_completed}/{result.total_steps}")
    print(f"Calidad: {result.quality_score:.2f}")
```

## 🎼 Workflows Disponibles

### 1. Análisis Completo de PQR (`DOCUMENT_ANALYSIS`)

Workflow integral que incluye:
- ✅ Extracción de contenido
- 🧠 Análisis con IA
- 🏷️ Clasificación automática
- 📊 Extracción de datos estructurados
- 🔍 Verificación de calidad

### 2. Extracción Web Inteligente (`WEB_EXTRACTION`)

Para automatización web:
- 🌐 Creación de contexto de navegador
- 🔗 Navegación automática
- 📄 Análisis de estructura de página
- 📥 Extracción inteligente de datos

### 3. Aseguramiento de Calidad (`QUALITY_ASSURANCE`)

Para validación de documentos:
- 🔍 Análisis inicial
- ⚠️ Detección de anomalías
- ✅ Validación de estructura
- 📋 Reporte de calidad

## 🔧 Servicios Individuales

### Gemini Service

```python
from src.services.ai_integration.gemini_service import GeminiService

gemini = GeminiService()

# Análisis de documento
analysis = await gemini.analyze_document(
    document_content="contenido...",
    analysis_type="comprehensive"
)

# Clasificación de PQR
classification = await gemini.classify_pqr(
    document_content="contenido..."
)

# Extracción estructurada
structured = await gemini.extract_structured_info(
    document_content="contenido..."
)
```

### Stagehand Service

```python
from src.services.ai_integration.stagehand_service import StagehandService

stagehand = StagehandService()

# Crear contexto de navegador
context = await stagehand.create_browser_context(headless=True)

# Navegar y extraer
await stagehand.navigate_to_page("https://ejemplo.com")
data = await stagehand.extract_data(
    instruction="Extraer información de contacto"
)
```

### MCP Service

```python
from src.services.ai_integration.mcp_service import MCPService

mcp = MCPService()

# Crear contexto compartido
context_id = await mcp.create_context("PQR_Analysis_Session")

# Compartir recursos
await mcp.share_resource(
    context_id=context_id,
    resource_type="document",
    resource_data={"content": "..."}
)
```

## 🔗 Integración con Extractores Existentes

### Ejemplo con Extractor Afinia

```python
from src.services.ai_integration.orchestrator import AIOrchestrator

# Datos del extractor existente
extractor_data = {
    "sgc_number": "RE4440202506962",
    "raw_content": "contenido extraído...",
    "attachments": ["factura.pdf", "foto.jpg"]
}

# Enriquecer con IA
async with AIOrchestrator() as orchestrator:
    enhanced_result = await orchestrator.execute_workflow(
        "quality_assurance",
        {
            "document_content": extractor_data["raw_content"],
            "metadata": extractor_data
        }
    )
    
    # Combinar datos originales con análisis de IA
    enriched_data = {
        **extractor_data,
        "ai_analysis": enhanced_result.results,
        "quality_score": enhanced_result.quality_score
    }
```

## 📊 Monitoreo y Estadísticas

```python
# Obtener estadísticas del orquestador
stats = orchestrator.get_orchestrator_stats()

print(f"Servicios disponibles: {stats['available_services']}")
print(f"Workflows activos: {stats['active_workflows']}")
print(f"Estadísticas de servicios: {stats['service_stats']}")

# Estadísticas individuales
gemini_stats = gemini.get_stats()
stagehand_stats = stagehand.get_stats()
```

## 🛠️ Configuración Avanzada

### Personalizar Workflows

```python
from src.services.ai_integration.orchestrator import WorkflowStep, TaskPriority

# Crear workflow personalizado
custom_steps = [
    WorkflowStep(
        id="custom_analysis",
        name="Análisis personalizado",
        service="gemini",
        method="analyze_document",
        params={"analysis_type": "custom"},
        priority=TaskPriority.HIGH,
        depends_on=[],
        timeout=30,
        retry_count=2,
        critical=True
    )
]

# Registrar workflow
orchestrator.predefined_workflows["custom_workflow"] = custom_steps
```

### Configurar Timeouts y Reintentos

```python
# En config.py, ajustar configuraciones
config = AIConfig(
    gemini_timeout=60,
    stagehand_timeout=120,
    mcp_timeout=30,
    max_retries=3
)
```

## 🧪 Ejemplos y Pruebas

Ejecutar ejemplos completos:

```bash
cd src/services/ai_integration
python examples.py
```

Ejemplos específicos:

```python
from src.services.ai_integration.examples import AIIntegrationExamples

examples = AIIntegrationExamples()

# Ejecutar ejemplo específico
await examples.example_1_basic_document_analysis()
await examples.example_2_intelligent_web_extraction()
await examples.example_3_complete_workflow_orchestration()
```

## 🚨 Manejo de Errores

El módulo incluye manejo robusto de errores:

```python
try:
    result = await orchestrator.execute_workflow(...)
    
    if not result.success:
        print(f"Errores encontrados: {result.errors}")
        
    # Verificar pasos críticos
    critical_failed = any(
        step.critical and step.id not in result.results 
        for step in workflow_steps
    )
    
except Exception as e:
    logger.error(f"Error en workflow: {e}")
```

## 📈 Optimización de Rendimiento

### Caché de Consultas

```python
# Gemini incluye caché automático
gemini = GeminiService()
# Las consultas similares se cachean automáticamente
```

### Ejecución Paralela

```python
# Los workflows ejecutan pasos en paralelo cuando es posible
# basándose en las dependencias definidas
```

### Timeouts Adaptativos

```python
# Los timeouts se ajustan según la complejidad del documento
# y el historial de rendimiento
```

## 🔒 Seguridad

- 🔐 **API Keys** se cargan desde variables de entorno
- 🛡️ **Validación** de entrada en todos los servicios
- 🔍 **Logging** seguro sin exponer credenciales
- ⚡ **Timeouts** para prevenir bloqueos

## 🤝 Contribución

Para contribuir al módulo:

1. Seguir la estructura de servicios existente
2. Implementar manejo de errores robusto
3. Incluir tests y ejemplos
4. Documentar nuevas funcionalidades
5. Mantener compatibilidad con extractores existentes

## 📞 Soporte

Para problemas o preguntas:

1. Verificar configuración de API keys
2. Revisar logs en `data/logs/`
3. Ejecutar ejemplos de prueba
4. Consultar documentación de servicios individuales

---

**Nota**: Este módulo está diseñado para ser completamente independiente del desarrollo principal y puede integrarse gradualmente con los extractores existentes.