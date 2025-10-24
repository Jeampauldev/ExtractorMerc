"""
Módulo de Integración de IA para ExtractorOV
===========================================

Este módulo proporciona integración completa con servicios de IA:
- Google Gemini Free API
- Stagehand para automatización web inteligente
- MCP (Model Context Protocol) para mejorar el procesamiento

Características principales:
- Análisis inteligente de documentos extraídos
- Automatización web mejorada con IA
- Procesamiento contextual de PQRs
- Optimización de flujos de extracción

Uso:
    from src.services.ai_integration import AIOrchestrator
    
    orchestrator = AIOrchestrator()
    result = await orchestrator.process_extraction_data(data)
"""

from .ai_orchestrator import AIOrchestrator
from .gemini_service import GeminiService
from .stagehand_service import StagehandService
from .mcp_service import MCPService
from .config import AIConfig

__version__ = "1.0.0"
__author__ = "ExtractorOV Team"

__all__ = [
    "AIOrchestrator",
    "GeminiService", 
    "StagehandService",
    "MCPService",
    "AIConfig"
]