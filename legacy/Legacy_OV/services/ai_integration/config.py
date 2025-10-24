"""
Configuración para el Módulo de Integración de IA
================================================

Este archivo maneja todas las configuraciones y credenciales necesarias
para los servicios de IA integrados.

IMPORTANTE: 
- Configura tus credenciales en las variables de entorno
- No hardcodees credenciales en este archivo
- Usa el archivo .env para desarrollo local
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GeminiConfig:
    """Configuración para Google Gemini Free API"""
    api_key: Optional[str] = None
    model_name: str = "gemini-1.5-flash"
    max_tokens: int = 8192
    temperature: float = 0.7
    timeout: int = 30
    project_name: str = "ExtractorOV"
    project_id: str = "980622586615"
    
    def __post_init__(self):
        # Cargar API key desde variables de entorno o usar la configurada
        self.api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCEuCHPoDtv3EFWLvfnbziCL-HqWDnhRAo")
        if not self.api_key:
            print("⚠️  GEMINI_API_KEY no configurada. Configúrala en tu archivo .env")
        else:
            print(f"✅ Gemini configurado correctamente para el proyecto: {self.project_name}")


@dataclass
class StagehandConfig:
    """Configuración para Stagehand"""
    api_key: Optional[str] = None
    base_url: str = "https://api.stagehand.dev"
    model_name: str = "gpt-4o-mini"
    headless: bool = True
    timeout: int = 60
    max_retries: int = 3
    
    def __post_init__(self):
        # Cargar configuración desde variables de entorno
        self.api_key = os.getenv("STAGEHAND_API_KEY")
        self.base_url = os.getenv("STAGEHAND_BASE_URL", self.base_url)
        if not self.api_key:
            print("⚠️  STAGEHAND_API_KEY no configurada. Configúrala en tu archivo .env")


@dataclass
class MCPConfig:
    """Configuración para MCP (Model Context Protocol)"""
    server_url: Optional[str] = None
    server_port: int = 8080
    protocol_version: str = "1.0"
    max_context_length: int = 32000
    enable_streaming: bool = True
    
    def __post_init__(self):
        # Cargar configuración desde variables de entorno
        self.server_url = os.getenv("MCP_SERVER_URL", f"http://localhost:{self.server_port}")
        self.server_port = int(os.getenv("MCP_SERVER_PORT", str(self.server_port)))


@dataclass
class AIConfig:
    """Configuración principal del módulo de IA"""
    
    # Configuraciones de servicios
    gemini: GeminiConfig
    stagehand: StagehandConfig
    mcp: MCPConfig
    
    # Configuraciones generales
    enable_gemini: bool = True
    enable_stagehand: bool = True
    enable_mcp: bool = True
    
    # Configuraciones de procesamiento
    max_concurrent_requests: int = 5
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hora
    
    # Directorios
    base_dir: Path = Path(__file__).parent.parent.parent.parent
    cache_dir: Path = None
    logs_dir: Path = None
    
    def __init__(self):
        self.gemini = GeminiConfig()
        self.stagehand = StagehandConfig()
        self.mcp = MCPConfig()
        
        # Configurar directorios
        self.cache_dir = self.base_dir / "data" / "ai_cache"
        self.logs_dir = self.base_dir / "data" / "logs" / "ai_integration"
        
        # Crear directorios si no existen
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar configuraciones desde variables de entorno
        self._load_from_env()
    
    def _load_from_env(self):
        """Cargar configuraciones desde variables de entorno"""
        self.enable_gemini = os.getenv("AI_ENABLE_GEMINI", "true").lower() == "true"
        self.enable_stagehand = os.getenv("AI_ENABLE_STAGEHAND", "true").lower() == "true"
        self.enable_mcp = os.getenv("AI_ENABLE_MCP", "true").lower() == "true"
        
        self.max_concurrent_requests = int(os.getenv("AI_MAX_CONCURRENT", "5"))
        self.cache_enabled = os.getenv("AI_CACHE_ENABLED", "true").lower() == "true"
        self.cache_ttl = int(os.getenv("AI_CACHE_TTL", "3600"))
    
    def is_configured(self) -> Dict[str, bool]:
        """Verificar qué servicios están configurados correctamente"""
        return {
            "gemini": self.enable_gemini and self.gemini.api_key is not None,
            "stagehand": self.enable_stagehand and self.stagehand.api_key is not None,
            "mcp": self.enable_mcp and self.mcp.server_url is not None
        }
    
    def get_status_report(self) -> str:
        """Generar reporte de estado de configuración"""
        status = self.is_configured()
        report = []
        report.append("🤖 Estado del Módulo de IA:")
        report.append("=" * 30)
        
        for service, configured in status.items():
            icon = "✅" if configured else "❌"
            status_text = "Configurado" if configured else "No configurado"
            report.append(f"{icon} {service.title()}: {status_text}")
        
        if not any(status.values()):
            report.append("\n⚠️  Ningún servicio de IA está configurado.")
            report.append("📝 Configura tus credenciales en el archivo .env:")
            report.append("   GEMINI_API_KEY=tu_api_key_aqui")
            report.append("   STAGEHAND_API_KEY=tu_api_key_aqui")
            report.append("   MCP_SERVER_URL=http://localhost:8080")
        
        return "\n".join(report)


# Instancia global de configuración
ai_config = AIConfig()


def get_ai_config() -> AIConfig:
    """Obtener la configuración global de IA"""
    return ai_config


def print_configuration_guide():
    """Imprimir guía de configuración para el usuario"""
    print("""
🚀 Guía de Configuración del Módulo de IA
=========================================

Para usar este módulo, necesitas configurar las siguientes credenciales:

1. 🔑 GEMINI API KEY (Google AI Studio):
   - Ve a: https://aistudio.google.com/app/apikey
   - Crea una nueva API key
   - Agrégala a tu .env: GEMINI_API_KEY=tu_api_key_aqui

2. 🎭 STAGEHAND API KEY:
   - Ve a: https://stagehand.dev
   - Obtén tu API key
   - Agrégala a tu .env: STAGEHAND_API_KEY=tu_api_key_aqui

3. 🔗 MCP SERVER (Opcional):
   - Configura tu servidor MCP
   - Agrégala a tu .env: MCP_SERVER_URL=http://localhost:8080

📁 Archivo .env de ejemplo:
--------------------------
# IA Integration
GEMINI_API_KEY=AIzaSyC...
STAGEHAND_API_KEY=sk-...
MCP_SERVER_URL=http://localhost:8080

# Configuraciones opcionales
AI_ENABLE_GEMINI=true
AI_ENABLE_STAGEHAND=true
AI_ENABLE_MCP=true
AI_MAX_CONCURRENT=5
AI_CACHE_ENABLED=true
AI_CACHE_TTL=3600

✨ Una vez configurado, podrás usar todas las funcionalidades de IA!
    """)


if __name__ == "__main__":
    # Mostrar estado actual y guía de configuración
    config = get_ai_config()
    print(config.get_status_report())
    print()
    print_configuration_guide()