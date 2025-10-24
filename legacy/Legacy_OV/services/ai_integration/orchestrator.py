"""
Orquestador de Servicios de IA
==============================

Este módulo implementa el orquestador principal que coordina todos los servicios
de IA (Gemini, Stagehand, MCP) para proporcionar una experiencia unificada
y optimizada de extracción y análisis de documentos.

El orquestador:
- Coordina múltiples servicios de IA
- Optimiza el flujo de trabajo según el contexto
- Maneja errores y recuperación automática
- Proporciona análisis inteligente y automatización
- Mantiene contexto compartido entre servicios
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from datetime import datetime
import uuid
from dataclasses import dataclass
from enum import Enum

from .config import get_ai_config
from .gemini_service import GeminiService
from .stagehand_service import StagehandService
from .mcp_service import MCPService, MCPMessage, MCPMessageType, MCPResourceType


class WorkflowType(Enum):
    """Tipos de workflows disponibles"""
    DOCUMENT_ANALYSIS = "document_analysis"
    WEB_EXTRACTION = "web_extraction"
    INTELLIGENT_AUTOMATION = "intelligent_automation"
    HYBRID_PROCESSING = "hybrid_processing"
    QUALITY_ASSURANCE = "quality_assurance"


class TaskPriority(Enum):
    """Prioridades de tareas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WorkflowStep:
    """Paso de workflow"""
    id: str
    name: str
    service: str  # gemini, stagehand, mcp
    method: str
    params: Dict[str, Any]
    priority: TaskPriority
    depends_on: List[str]
    timeout: int
    retry_count: int
    critical: bool


@dataclass
class WorkflowResult:
    """Resultado de workflow"""
    workflow_id: str
    success: bool
    steps_completed: int
    total_steps: int
    results: Dict[str, Any]
    errors: List[str]
    execution_time: float
    quality_score: Optional[float]


class AIOrchestrator:
    """Orquestador principal de servicios de IA"""
    
    def __init__(self):
        self.config = get_ai_config()
        self.logger = logging.getLogger(__name__)
        
        # Servicios de IA
        self.gemini = GeminiService()
        self.stagehand = StagehandService()
        self.mcp = MCPService()
        
        # Estado del orquestador
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.service_stats: Dict[str, Dict[str, Any]] = {}
        
        # Workflows predefinidos
        self.predefined_workflows = self._initialize_workflows()
    
    def _initialize_workflows(self) -> Dict[str, List[WorkflowStep]]:
        """Inicializar workflows predefinidos"""
        return {
            "pqr_complete_analysis": [
                WorkflowStep(
                    id="extract_document",
                    name="Extraer documento de la web",
                    service="stagehand",
                    method="extract_data",
                    params={"instruction": "Extraer información del PQR"},
                    priority=TaskPriority.HIGH,
                    depends_on=[],
                    timeout=60,
                    retry_count=2,
                    critical=True
                ),
                WorkflowStep(
                    id="analyze_content",
                    name="Analizar contenido con IA",
                    service="gemini",
                    method="analyze_document",
                    params={"analysis_type": "comprehensive"},
                    priority=TaskPriority.HIGH,
                    depends_on=["extract_document"],
                    timeout=30,
                    retry_count=1,
                    critical=True
                ),
                WorkflowStep(
                    id="classify_pqr",
                    name="Clasificar PQR",
                    service="gemini",
                    method="classify_pqr",
                    params={},
                    priority=TaskPriority.MEDIUM,
                    depends_on=["analyze_content"],
                    timeout=20,
                    retry_count=1,
                    critical=False
                ),
                WorkflowStep(
                    id="extract_structured_data",
                    name="Extraer datos estructurados",
                    service="gemini",
                    method="extract_structured_info",
                    params={},
                    priority=TaskPriority.HIGH,
                    depends_on=["analyze_content"],
                    timeout=25,
                    retry_count=1,
                    critical=True
                ),
                WorkflowStep(
                    id="quality_check",
                    name="Verificación de calidad",
                    service="gemini",
                    method="detect_anomalies",
                    params={},
                    priority=TaskPriority.MEDIUM,
                    depends_on=["extract_structured_data"],
                    timeout=15,
                    retry_count=1,
                    critical=False
                )
            ],
            
            "intelligent_web_automation": [
                WorkflowStep(
                    id="create_browser_context",
                    name="Crear contexto de navegador",
                    service="stagehand",
                    method="create_browser_context",
                    params={"headless": True},
                    priority=TaskPriority.HIGH,
                    depends_on=[],
                    timeout=30,
                    retry_count=2,
                    critical=True
                ),
                WorkflowStep(
                    id="navigate_to_page",
                    name="Navegar a página objetivo",
                    service="stagehand",
                    method="navigate_to_page",
                    params={},  # URL se pasa en runtime
                    priority=TaskPriority.HIGH,
                    depends_on=["create_browser_context"],
                    timeout=45,
                    retry_count=2,
                    critical=True
                ),
                WorkflowStep(
                    id="analyze_page_structure",
                    name="Analizar estructura de página",
                    service="gemini",
                    method="analyze_document",
                    params={"analysis_type": "web_structure"},
                    priority=TaskPriority.MEDIUM,
                    depends_on=["navigate_to_page"],
                    timeout=20,
                    retry_count=1,
                    critical=False
                ),
                WorkflowStep(
                    id="perform_extraction",
                    name="Realizar extracción inteligente",
                    service="stagehand",
                    method="extract_data",
                    params={},  # Instrucciones se pasan en runtime
                    priority=TaskPriority.HIGH,
                    depends_on=["navigate_to_page"],
                    timeout=60,
                    retry_count=2,
                    critical=True
                )
            ],
            
            "document_quality_assurance": [
                WorkflowStep(
                    id="initial_analysis",
                    name="Análisis inicial del documento",
                    service="gemini",
                    method="analyze_document",
                    params={"analysis_type": "quality_check"},
                    priority=TaskPriority.HIGH,
                    depends_on=[],
                    timeout=30,
                    retry_count=1,
                    critical=True
                ),
                WorkflowStep(
                    id="detect_anomalies",
                    name="Detectar anomalías",
                    service="gemini",
                    method="detect_anomalies",
                    params={},
                    priority=TaskPriority.HIGH,
                    depends_on=["initial_analysis"],
                    timeout=25,
                    retry_count=1,
                    critical=True
                ),
                WorkflowStep(
                    id="validate_structure",
                    name="Validar estructura",
                    service="gemini",
                    method="extract_structured_info",
                    params={"validation_mode": True},
                    priority=TaskPriority.MEDIUM,
                    depends_on=["initial_analysis"],
                    timeout=20,
                    retry_count=1,
                    critical=False
                ),
                WorkflowStep(
                    id="generate_quality_report",
                    name="Generar reporte de calidad",
                    service="gemini",
                    method="generate_summary",
                    params={"summary_type": "quality_report"},
                    priority=TaskPriority.LOW,
                    depends_on=["detect_anomalies", "validate_structure"],
                    timeout=15,
                    retry_count=1,
                    critical=False
                )
            ]
        }
    
    async def __aenter__(self):
        """Inicializar servicios"""
        # Inicializar servicios que lo requieran
        if hasattr(self.stagehand, '__aenter__'):
            await self.stagehand.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cerrar servicios"""
        if hasattr(self.stagehand, '__aexit__'):
            await self.stagehand.__aexit__(exc_type, exc_val, exc_tb)
    
    def get_available_services(self) -> Dict[str, bool]:
        """Obtener servicios disponibles"""
        return {
            "gemini": self.gemini.is_available(),
            "stagehand": self.stagehand.is_available(),
            "mcp": self.mcp.is_available()
        }
    
    async def execute_workflow(
        self, 
        workflow_type: Union[WorkflowType, str], 
        params: Dict[str, Any] = None,
        context_id: str = None
    ) -> WorkflowResult:
        """
        Ejecutar workflow completo
        
        Args:
            workflow_type: Tipo de workflow o nombre personalizado
            params: Parámetros para el workflow
            context_id: ID de contexto MCP (opcional)
            
        Returns:
            Resultado del workflow
        """
        start_time = datetime.now()
        workflow_id = str(uuid.uuid4())
        params = params or {}
        
        # Obtener pasos del workflow
        if isinstance(workflow_type, WorkflowType):
            workflow_name = workflow_type.value
        else:
            workflow_name = workflow_type
        
        if workflow_name not in self.predefined_workflows:
            return WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                steps_completed=0,
                total_steps=0,
                results={},
                errors=[f"Workflow no encontrado: {workflow_name}"],
                execution_time=0.0,
                quality_score=None
            )
        
        steps = self.predefined_workflows[workflow_name]
        
        # Crear contexto MCP si no se proporciona
        if not context_id:
            context_id = await self.mcp.create_context(f"Workflow_{workflow_name}_{workflow_id[:8]}")
        
        # Registrar workflow activo
        self.active_workflows[workflow_id] = {
            "type": workflow_name,
            "context_id": context_id,
            "start_time": start_time,
            "params": params,
            "steps": steps
        }
        
        self.logger.info(f"🚀 Iniciando workflow: {workflow_name} (ID: {workflow_id[:8]})")
        
        # Ejecutar pasos
        results = {}
        errors = []
        completed_steps = 0
        
        try:
            # Resolver dependencias y ejecutar pasos
            executed_steps = set()
            
            while len(executed_steps) < len(steps):
                progress_made = False
                
                for step in steps:
                    if step.id in executed_steps:
                        continue
                    
                    # Verificar dependencias
                    if all(dep in executed_steps for dep in step.depends_on):
                        try:
                            self.logger.info(f"⚡ Ejecutando paso: {step.name}")
                            
                            # Preparar parámetros del paso
                            step_params = {**step.params, **params}
                            
                            # Ejecutar paso según el servicio
                            step_result = await self._execute_step(
                                step, step_params, context_id, results
                            )
                            
                            results[step.id] = step_result
                            executed_steps.add(step.id)
                            completed_steps += 1
                            progress_made = True
                            
                            self.logger.info(f"✅ Paso completado: {step.name}")
                            
                        except Exception as e:
                            error_msg = f"Error en paso {step.name}: {str(e)}"
                            self.logger.error(f"❌ {error_msg}")
                            errors.append(error_msg)
                            
                            if step.critical:
                                raise Exception(f"Paso crítico falló: {step.name}")
                            
                            # Marcar como ejecutado aunque haya fallado
                            executed_steps.add(step.id)
                            results[step.id] = {"error": str(e)}
                
                if not progress_made:
                    raise Exception("Dependencias circulares o no resueltas en el workflow")
            
            success = len(errors) == 0 or not any(
                step.critical and step.id not in [r for r in results if "error" not in results[r]]
                for step in steps
            )
            
        except Exception as e:
            self.logger.error(f"❌ Workflow falló: {e}")
            errors.append(str(e))
            success = False
        
        finally:
            # Limpiar workflow activo
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
        
        # Calcular tiempo de ejecución
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Calcular puntuación de calidad
        quality_score = self._calculate_quality_score(results, errors, completed_steps, len(steps))
        
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            success=success,
            steps_completed=completed_steps,
            total_steps=len(steps),
            results=results,
            errors=errors,
            execution_time=execution_time,
            quality_score=quality_score
        )
        
        self.logger.info(
            f"🏁 Workflow completado: {workflow_name} "
            f"({completed_steps}/{len(steps)} pasos, {execution_time:.1f}s, "
            f"calidad: {quality_score:.2f if quality_score else 'N/A'})"
        )
        
        return workflow_result
    
    async def _execute_step(
        self, 
        step: WorkflowStep, 
        params: Dict[str, Any], 
        context_id: str,
        previous_results: Dict[str, Any]
    ) -> Any:
        """Ejecutar un paso individual del workflow"""
        
        # Enriquecer parámetros con resultados previos si es necesario
        enriched_params = self._enrich_step_params(step, params, previous_results)
        
        if step.service == "gemini":
            return await self._execute_gemini_step(step, enriched_params)
        
        elif step.service == "stagehand":
            return await self._execute_stagehand_step(step, enriched_params)
        
        elif step.service == "mcp":
            return await self._execute_mcp_step(step, enriched_params, context_id)
        
        else:
            raise ValueError(f"Servicio desconocido: {step.service}")
    
    def _enrich_step_params(
        self, 
        step: WorkflowStep, 
        params: Dict[str, Any], 
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enriquecer parámetros del paso con resultados previos"""
        enriched = params.copy()
        
        # Agregar datos de pasos dependientes
        for dep_id in step.depends_on:
            if dep_id in previous_results:
                dep_result = previous_results[dep_id]
                enriched[f"{dep_id}_result"] = dep_result
                
                # Casos específicos de enriquecimiento
                if step.method == "analyze_document" and dep_id == "extract_document":
                    if "extracted_data" in dep_result:
                        enriched["document_content"] = dep_result["extracted_data"]
                
                elif step.method == "classify_pqr" and dep_id == "analyze_content":
                    if "analysis" in dep_result:
                        enriched["analysis_context"] = dep_result["analysis"]
        
        return enriched
    
    async def _execute_gemini_step(self, step: WorkflowStep, params: Dict[str, Any]) -> Any:
        """Ejecutar paso de Gemini"""
        if not self.gemini.is_available():
            raise Exception("Servicio Gemini no disponible")
        
        method = getattr(self.gemini, step.method, None)
        if not method:
            raise Exception(f"Método no encontrado en Gemini: {step.method}")
        
        # Ejecutar con timeout y reintentos
        for attempt in range(step.retry_count + 1):
            try:
                result = await asyncio.wait_for(
                    method(**params), 
                    timeout=step.timeout
                )
                return result
                
            except asyncio.TimeoutError:
                if attempt == step.retry_count:
                    raise Exception(f"Timeout en paso Gemini: {step.name}")
                await asyncio.sleep(2 ** attempt)  # Backoff exponencial
                
            except Exception as e:
                if attempt == step.retry_count:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def _execute_stagehand_step(self, step: WorkflowStep, params: Dict[str, Any]) -> Any:
        """Ejecutar paso de Stagehand"""
        if not self.stagehand.is_available():
            raise Exception("Servicio Stagehand no disponible")
        
        method = getattr(self.stagehand, step.method, None)
        if not method:
            raise Exception(f"Método no encontrado en Stagehand: {step.method}")
        
        # Ejecutar con timeout y reintentos
        for attempt in range(step.retry_count + 1):
            try:
                result = await asyncio.wait_for(
                    method(**params), 
                    timeout=step.timeout
                )
                return result
                
            except asyncio.TimeoutError:
                if attempt == step.retry_count:
                    raise Exception(f"Timeout en paso Stagehand: {step.name}")
                await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                if attempt == step.retry_count:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    async def _execute_mcp_step(self, step: WorkflowStep, params: Dict[str, Any], context_id: str) -> Any:
        """Ejecutar paso de MCP"""
        message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.REQUEST,
            method=step.method,
            params=params,
            timestamp=datetime.now(),
            source="orchestrator",
            context_id=context_id
        )
        
        # Ejecutar con timeout y reintentos
        for attempt in range(step.retry_count + 1):
            try:
                response = await asyncio.wait_for(
                    self.mcp.send_message(message), 
                    timeout=step.timeout
                )
                
                if response.type == MCPMessageType.ERROR:
                    raise Exception(response.params.get("error", "Error MCP desconocido"))
                
                return response.params.get("result")
                
            except asyncio.TimeoutError:
                if attempt == step.retry_count:
                    raise Exception(f"Timeout en paso MCP: {step.name}")
                await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                if attempt == step.retry_count:
                    raise
                await asyncio.sleep(2 ** attempt)
    
    def _calculate_quality_score(
        self, 
        results: Dict[str, Any], 
        errors: List[str], 
        completed_steps: int, 
        total_steps: int
    ) -> Optional[float]:
        """Calcular puntuación de calidad del workflow"""
        if total_steps == 0:
            return None
        
        # Puntuación base por completitud
        completion_score = completed_steps / total_steps
        
        # Penalización por errores
        error_penalty = len(errors) * 0.1
        
        # Bonificación por resultados exitosos
        success_bonus = 0.0
        for result in results.values():
            if isinstance(result, dict) and "error" not in result:
                success_bonus += 0.05
        
        # Calcular puntuación final
        quality_score = max(0.0, min(1.0, completion_score - error_penalty + success_bonus))
        
        return quality_score
    
    # Métodos de conveniencia para workflows comunes
    async def analyze_pqr_complete(
        self, 
        document_data: Any = None, 
        url: str = None
    ) -> WorkflowResult:
        """Análisis completo de PQR"""
        params = {}
        if document_data:
            params["document_content"] = document_data
        if url:
            params["url"] = url
        
        return await self.execute_workflow(
            WorkflowType.DOCUMENT_ANALYSIS, 
            params
        )
    
    async def intelligent_web_extraction(
        self, 
        url: str, 
        extraction_instructions: str
    ) -> WorkflowResult:
        """Extracción web inteligente"""
        params = {
            "url": url,
            "instruction": extraction_instructions
        }
        
        return await self.execute_workflow(
            WorkflowType.WEB_EXTRACTION, 
            params
        )
    
    async def quality_assurance_check(self, document_data: Any) -> WorkflowResult:
        """Verificación de calidad de documento"""
        params = {"document_content": document_data}
        
        return await self.execute_workflow(
            WorkflowType.QUALITY_ASSURANCE, 
            params
        )
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del orquestador"""
        services = self.get_available_services()
        
        return {
            "available_services": services,
            "active_workflows": len(self.active_workflows),
            "predefined_workflows": list(self.predefined_workflows.keys()),
            "service_stats": {
                "gemini": self.gemini.get_stats() if services["gemini"] else None,
                "stagehand": self.stagehand.get_stats() if services["stagehand"] else None,
                "mcp": self.mcp.get_stats() if services["mcp"] else None
            }
        }


# Instancia global del orquestador
_global_orchestrator = None

def get_orchestrator() -> AIOrchestrator:
    """Obtener instancia global del orquestador"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = AIOrchestrator()
    return _global_orchestrator


# Funciones de conveniencia
async def quick_pqr_analysis(document_data: Any) -> Dict[str, Any]:
    """Análisis rápido de PQR"""
    async with AIOrchestrator() as orchestrator:
        result = await orchestrator.analyze_pqr_complete(document_data)
        return {
            "success": result.success,
            "analysis": result.results,
            "quality_score": result.quality_score,
            "execution_time": result.execution_time
        }


async def quick_web_extraction(url: str, instructions: str) -> Dict[str, Any]:
    """Extracción web rápida"""
    async with AIOrchestrator() as orchestrator:
        result = await orchestrator.intelligent_web_extraction(url, instructions)
        return {
            "success": result.success,
            "extracted_data": result.results,
            "quality_score": result.quality_score,
            "execution_time": result.execution_time
        }


if __name__ == "__main__":
    # Ejemplo de uso
    async def test_orchestrator():
        async with AIOrchestrator() as orchestrator:
            print("🎼 Probando AI Orchestrator...")
            
            # Mostrar servicios disponibles
            services = orchestrator.get_available_services()
            print(f"🔧 Servicios disponibles: {services}")
            
            # Ejecutar análisis de documento de prueba
            test_doc = {"content": "PQR de prueba para análisis"}
            result = await orchestrator.analyze_pqr_complete(test_doc)
            
            print(f"📊 Resultado del análisis:")
            print(f"  - Éxito: {result.success}")
            print(f"  - Pasos completados: {result.steps_completed}/{result.total_steps}")
            print(f"  - Tiempo de ejecución: {result.execution_time:.2f}s")
            print(f"  - Puntuación de calidad: {result.quality_score:.2f if result.quality_score else 'N/A'}")
            
            if result.errors:
                print(f"  - Errores: {result.errors}")
            
            # Mostrar estadísticas
            stats = orchestrator.get_orchestrator_stats()
            print(f"📈 Estadísticas del orquestador: {stats}")
    
    # Ejecutar prueba
    asyncio.run(test_orchestrator())