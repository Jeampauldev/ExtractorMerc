"""
Servicio MCP (Model Context Protocol)
====================================

Este módulo implementa el protocolo MCP para mejorar el proceso de extracción
mediante comunicación estructurada entre modelos de IA y herramientas externas.

MCP permite:
- Comunicación estandarizada entre IA y herramientas
- Contexto compartido entre diferentes servicios
- Orquestación inteligente de tareas complejas
- Intercambio de datos estructurados
- Manejo de estado distribuido
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from pathlib import Path
from datetime import datetime
import uuid
from dataclasses import dataclass, asdict
from enum import Enum

from .config import MCPConfig, get_ai_config


class MCPMessageType(Enum):
    """Tipos de mensajes MCP"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPResourceType(Enum):
    """Tipos de recursos MCP"""
    DOCUMENT = "document"
    EXTRACTION = "extraction"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"
    CONTEXT = "context"


@dataclass
class MCPMessage:
    """Mensaje MCP estándar"""
    id: str
    type: MCPMessageType
    method: str
    params: Dict[str, Any]
    timestamp: datetime
    source: str
    target: Optional[str] = None
    context_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        data = asdict(self)
        data['type'] = self.type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Crear desde diccionario"""
        data['type'] = MCPMessageType(data['type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class MCPResource:
    """Recurso MCP"""
    id: str
    type: MCPResourceType
    name: str
    data: Any
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        data = asdict(self)
        data['type'] = self.type.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data


@dataclass
class MCPContext:
    """Contexto MCP para mantener estado"""
    id: str
    name: str
    resources: Dict[str, MCPResource]
    variables: Dict[str, Any]
    history: List[MCPMessage]
    created_at: datetime
    updated_at: datetime
    
    def add_resource(self, resource: MCPResource):
        """Agregar recurso al contexto"""
        self.resources[resource.id] = resource
        self.updated_at = datetime.now()
    
    def get_resource(self, resource_id: str) -> Optional[MCPResource]:
        """Obtener recurso por ID"""
        return self.resources.get(resource_id)
    
    def set_variable(self, key: str, value: Any):
        """Establecer variable de contexto"""
        self.variables[key] = value
        self.updated_at = datetime.now()
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Obtener variable de contexto"""
        return self.variables.get(key, default)


class MCPService:
    """Servicio MCP para coordinación de IA"""
    
    def __init__(self, config: Optional[MCPConfig] = None):
        self.config = config or get_ai_config().mcp
        self.logger = logging.getLogger(__name__)
        
        # Estado interno
        self.contexts: Dict[str, MCPContext] = {}
        self.handlers: Dict[str, Callable] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Registrar handlers por defecto
        self._register_default_handlers()
    
    def is_available(self) -> bool:
        """Verificar si MCP está disponible"""
        return True  # MCP es siempre disponible (protocolo interno)
    
    def _register_default_handlers(self):
        """Registrar handlers por defecto"""
        self.handlers.update({
            "create_context": self._handle_create_context,
            "get_context": self._handle_get_context,
            "update_context": self._handle_update_context,
            "delete_context": self._handle_delete_context,
            "add_resource": self._handle_add_resource,
            "get_resource": self._handle_get_resource,
            "list_resources": self._handle_list_resources,
            "set_variable": self._handle_set_variable,
            "get_variable": self._handle_get_variable,
            "execute_workflow": self._handle_execute_workflow,
            "analyze_document": self._handle_analyze_document,
            "coordinate_extraction": self._handle_coordinate_extraction
        })
    
    def register_handler(self, method: str, handler: Callable):
        """Registrar handler personalizado"""
        self.handlers[method] = handler
        self.logger.info(f"📝 Handler registrado: {method}")
    
    async def send_message(self, message: MCPMessage) -> MCPMessage:
        """Enviar mensaje MCP y obtener respuesta"""
        try:
            # Agregar mensaje al historial del contexto
            if message.context_id and message.context_id in self.contexts:
                self.contexts[message.context_id].history.append(message)
            
            # Buscar handler
            handler = self.handlers.get(message.method)
            if not handler:
                return self._create_error_response(
                    message, f"Handler no encontrado: {message.method}"
                )
            
            # Ejecutar handler
            result = await handler(message)
            
            # Crear respuesta
            response = MCPMessage(
                id=str(uuid.uuid4()),
                type=MCPMessageType.RESPONSE,
                method=f"{message.method}_response",
                params={"result": result, "original_id": message.id},
                timestamp=datetime.now(),
                source="mcp_service",
                target=message.source,
                context_id=message.context_id
            )
            
            # Agregar respuesta al historial
            if message.context_id and message.context_id in self.contexts:
                self.contexts[message.context_id].history.append(response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando mensaje MCP: {e}")
            return self._create_error_response(message, str(e))
    
    def _create_error_response(self, original_message: MCPMessage, error: str) -> MCPMessage:
        """Crear respuesta de error"""
        return MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.ERROR,
            method="error",
            params={"error": error, "original_id": original_message.id},
            timestamp=datetime.now(),
            source="mcp_service",
            target=original_message.source,
            context_id=original_message.context_id
        )
    
    # Handlers por defecto
    async def _handle_create_context(self, message: MCPMessage) -> Dict[str, Any]:
        """Crear nuevo contexto MCP"""
        params = message.params
        context_id = params.get("context_id", str(uuid.uuid4()))
        name = params.get("name", f"Context_{context_id[:8]}")
        
        context = MCPContext(
            id=context_id,
            name=name,
            resources={},
            variables={},
            history=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.contexts[context_id] = context
        self.logger.info(f"🆕 Contexto MCP creado: {context_id}")
        
        return {
            "context_id": context_id,
            "name": name,
            "created_at": context.created_at.isoformat()
        }
    
    async def _handle_get_context(self, message: MCPMessage) -> Dict[str, Any]:
        """Obtener información de contexto"""
        context_id = message.params.get("context_id")
        if not context_id or context_id not in self.contexts:
            raise ValueError(f"Contexto no encontrado: {context_id}")
        
        context = self.contexts[context_id]
        return {
            "id": context.id,
            "name": context.name,
            "resource_count": len(context.resources),
            "variable_count": len(context.variables),
            "message_count": len(context.history),
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat()
        }
    
    async def _handle_update_context(self, message: MCPMessage) -> Dict[str, Any]:
        """Actualizar contexto"""
        context_id = message.params.get("context_id")
        if not context_id or context_id not in self.contexts:
            raise ValueError(f"Contexto no encontrado: {context_id}")
        
        context = self.contexts[context_id]
        updates = message.params.get("updates", {})
        
        if "name" in updates:
            context.name = updates["name"]
        
        if "variables" in updates:
            context.variables.update(updates["variables"])
        
        context.updated_at = datetime.now()
        
        return {"updated": True, "context_id": context_id}
    
    async def _handle_delete_context(self, message: MCPMessage) -> Dict[str, Any]:
        """Eliminar contexto"""
        context_id = message.params.get("context_id")
        if context_id in self.contexts:
            del self.contexts[context_id]
            self.logger.info(f"🗑️ Contexto eliminado: {context_id}")
            return {"deleted": True, "context_id": context_id}
        
        return {"deleted": False, "error": "Contexto no encontrado"}
    
    async def _handle_add_resource(self, message: MCPMessage) -> Dict[str, Any]:
        """Agregar recurso a contexto"""
        context_id = message.context_id
        if not context_id or context_id not in self.contexts:
            raise ValueError(f"Contexto no encontrado: {context_id}")
        
        params = message.params
        resource = MCPResource(
            id=params.get("resource_id", str(uuid.uuid4())),
            type=MCPResourceType(params["type"]),
            name=params["name"],
            data=params["data"],
            metadata=params.get("metadata", {}),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.contexts[context_id].add_resource(resource)
        
        return {
            "resource_id": resource.id,
            "added": True,
            "context_id": context_id
        }
    
    async def _handle_get_resource(self, message: MCPMessage) -> Dict[str, Any]:
        """Obtener recurso de contexto"""
        context_id = message.context_id
        resource_id = message.params.get("resource_id")
        
        if not context_id or context_id not in self.contexts:
            raise ValueError(f"Contexto no encontrado: {context_id}")
        
        resource = self.contexts[context_id].get_resource(resource_id)
        if not resource:
            raise ValueError(f"Recurso no encontrado: {resource_id}")
        
        return resource.to_dict()
    
    async def _handle_list_resources(self, message: MCPMessage) -> Dict[str, Any]:
        """Listar recursos de contexto"""
        context_id = message.context_id
        if not context_id or context_id not in self.contexts:
            raise ValueError(f"Contexto no encontrado: {context_id}")
        
        context = self.contexts[context_id]
        resource_type = message.params.get("type")
        
        resources = []
        for resource in context.resources.values():
            if not resource_type or resource.type.value == resource_type:
                resources.append({
                    "id": resource.id,
                    "type": resource.type.value,
                    "name": resource.name,
                    "created_at": resource.created_at.isoformat()
                })
        
        return {"resources": resources, "count": len(resources)}
    
    async def _handle_set_variable(self, message: MCPMessage) -> Dict[str, Any]:
        """Establecer variable en contexto"""
        context_id = message.context_id
        if not context_id or context_id not in self.contexts:
            raise ValueError(f"Contexto no encontrado: {context_id}")
        
        key = message.params["key"]
        value = message.params["value"]
        
        self.contexts[context_id].set_variable(key, value)
        
        return {"set": True, "key": key, "context_id": context_id}
    
    async def _handle_get_variable(self, message: MCPMessage) -> Dict[str, Any]:
        """Obtener variable de contexto"""
        context_id = message.context_id
        if not context_id or context_id not in self.contexts:
            raise ValueError(f"Contexto no encontrado: {context_id}")
        
        key = message.params["key"]
        default = message.params.get("default")
        
        value = self.contexts[context_id].get_variable(key, default)
        
        return {"key": key, "value": value, "found": key in self.contexts[context_id].variables}
    
    async def _handle_execute_workflow(self, message: MCPMessage) -> Dict[str, Any]:
        """Ejecutar workflow coordinado"""
        workflow = message.params.get("workflow", [])
        context_id = message.context_id
        
        results = []
        
        for step in workflow:
            try:
                # Crear mensaje para el paso
                step_message = MCPMessage(
                    id=str(uuid.uuid4()),
                    type=MCPMessageType.REQUEST,
                    method=step["method"],
                    params=step.get("params", {}),
                    timestamp=datetime.now(),
                    source=message.source,
                    context_id=context_id
                )
                
                # Ejecutar paso
                response = await self.send_message(step_message)
                
                step_result = {
                    "step": step.get("name", step["method"]),
                    "success": response.type != MCPMessageType.ERROR,
                    "result": response.params
                }
                
                results.append(step_result)
                
                # Si el paso falla y es crítico, detener workflow
                if not step_result["success"] and step.get("critical", False):
                    break
                    
            except Exception as e:
                results.append({
                    "step": step.get("name", step["method"]),
                    "success": False,
                    "error": str(e)
                })
                
                if step.get("critical", False):
                    break
        
        return {
            "workflow_completed": True,
            "steps_executed": len(results),
            "results": results
        }
    
    async def _handle_analyze_document(self, message: MCPMessage) -> Dict[str, Any]:
        """Analizar documento usando IA coordinada"""
        params = message.params
        document_data = params.get("document")
        analysis_type = params.get("analysis_type", "general")
        
        # Simular análisis (en implementación real, coordinaría con Gemini)
        analysis = {
            "document_type": "PQR",
            "confidence": 0.95,
            "key_fields": {
                "numero_pqr": "RE4440202506962",
                "fecha": "2025-01-12",
                "tipo": "Reclamo",
                "estado": "En proceso"
            },
            "sentiment": "neutral",
            "priority": "medium",
            "requires_action": True
        }
        
        # Agregar como recurso al contexto
        if message.context_id:
            resource = MCPResource(
                id=str(uuid.uuid4()),
                type=MCPResourceType.ANALYSIS,
                name=f"Análisis_{analysis_type}",
                data=analysis,
                metadata={"analysis_type": analysis_type},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            if message.context_id in self.contexts:
                self.contexts[message.context_id].add_resource(resource)
        
        return analysis
    
    async def _handle_coordinate_extraction(self, message: MCPMessage) -> Dict[str, Any]:
        """Coordinar proceso de extracción completo"""
        params = message.params
        extraction_config = params.get("config", {})
        
        # Simular coordinación de extracción
        coordination_result = {
            "extraction_id": str(uuid.uuid4()),
            "status": "completed",
            "services_used": ["gemini", "stagehand"],
            "documents_processed": 5,
            "data_extracted": {
                "pqrs": 3,
                "attachments": 7,
                "metadata": {"total_size": "2.5MB"}
            },
            "quality_score": 0.92,
            "processing_time": "45.2s"
        }
        
        return coordination_result
    
    # Métodos de conveniencia
    async def create_context(self, name: str = None) -> str:
        """Crear contexto de forma conveniente"""
        message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.REQUEST,
            method="create_context",
            params={"name": name} if name else {},
            timestamp=datetime.now(),
            source="convenience_method"
        )
        
        response = await self.send_message(message)
        return response.params["result"]["context_id"]
    
    async def add_document_resource(self, context_id: str, document_data: Any, name: str) -> str:
        """Agregar documento como recurso"""
        message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.REQUEST,
            method="add_resource",
            params={
                "type": "document",
                "name": name,
                "data": document_data,
                "metadata": {"added_via": "convenience_method"}
            },
            timestamp=datetime.now(),
            source="convenience_method",
            context_id=context_id
        )
        
        response = await self.send_message(message)
        return response.params["result"]["resource_id"]
    
    async def coordinate_ai_workflow(self, context_id: str, workflow_steps: List[Dict]) -> Dict[str, Any]:
        """Coordinar workflow de IA"""
        message = MCPMessage(
            id=str(uuid.uuid4()),
            type=MCPMessageType.REQUEST,
            method="execute_workflow",
            params={"workflow": workflow_steps},
            timestamp=datetime.now(),
            source="convenience_method",
            context_id=context_id
        )
        
        response = await self.send_message(message)
        return response.params["result"]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servicio MCP"""
        total_resources = sum(len(ctx.resources) for ctx in self.contexts.values())
        total_messages = sum(len(ctx.history) for ctx in self.contexts.values())
        
        return {
            "available": self.is_available(),
            "active_contexts": len(self.contexts),
            "total_resources": total_resources,
            "total_messages": total_messages,
            "registered_handlers": len(self.handlers),
            "handler_methods": list(self.handlers.keys())
        }


# Funciones de conveniencia globales
_global_mcp_service = None

def get_mcp_service() -> MCPService:
    """Obtener instancia global del servicio MCP"""
    global _global_mcp_service
    if _global_mcp_service is None:
        _global_mcp_service = MCPService()
    return _global_mcp_service


async def quick_mcp_analysis(document_data: Any, analysis_type: str = "general") -> Dict[str, Any]:
    """Análisis rápido usando MCP"""
    service = get_mcp_service()
    
    # Crear contexto
    context_id = await service.create_context(f"QuickAnalysis_{datetime.now().strftime('%H%M%S')}")
    
    # Analizar documento
    message = MCPMessage(
        id=str(uuid.uuid4()),
        type=MCPMessageType.REQUEST,
        method="analyze_document",
        params={
            "document": document_data,
            "analysis_type": analysis_type
        },
        timestamp=datetime.now(),
        source="quick_analysis",
        context_id=context_id
    )
    
    response = await service.send_message(message)
    return response.params["result"]


if __name__ == "__main__":
    # Ejemplo de uso
    async def test_mcp():
        service = MCPService()
        
        print("🔗 Probando MCP Service...")
        
        # Crear contexto
        context_id = await service.create_context("TestContext")
        print(f"📝 Contexto creado: {context_id}")
        
        # Agregar recurso
        await service.add_document_resource(
            context_id, 
            {"content": "Documento de prueba"}, 
            "TestDocument"
        )
        
        # Ejecutar análisis
        analysis = await quick_mcp_analysis(
            {"content": "PQR de prueba"}, 
            "pqr_analysis"
        )
        print(f"📊 Análisis: {analysis}")
        
        # Mostrar estadísticas
        stats = service.get_stats()
        print(f"📈 Estadísticas: {stats}")
    
    # Ejecutar prueba
    asyncio.run(test_mcp())