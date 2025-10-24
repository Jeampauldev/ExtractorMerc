"""
Servicio de Stagehand para automatización web inteligente con Gemini
Implementación usando bridge Node.js para acceso completo al SDK oficial
"""

import asyncio
import json
import logging
import subprocess
import time
import signal
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import aiohttp
import base64

from .config import StagehandConfig, get_ai_config


class StagehandService:
    """Servicio para automatización web usando Stagehand con Gemini"""
    
    def __init__(self, config: Optional[StagehandConfig] = None):
        self.config = config or StagehandConfig()
        self.logger = logging.getLogger(__name__)
        self.session_id = None
        self.bridge_process = None
        self.bridge_port = 3001
        self.bridge_url = f"http://localhost:{self.bridge_port}"
        
        # Configurar logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.start_bridge()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self._close_stagehand_session()
        await self.stop_bridge()
    
    def is_available(self) -> bool:
        """Verificar si Stagehand está disponible"""
        ai_config = get_ai_config()
        return bool(ai_config.gemini.api_key)
    
    async def start_bridge(self):
        """Iniciar el bridge Node.js de Stagehand"""
        if self.bridge_process:
            return
        
        try:
            bridge_path = Path(__file__).parent / "stagehand_bridge.js"
            
            # Configurar variables de entorno para Gemini
            env = os.environ.copy()
            ai_config = get_ai_config()
            env["GEMINI_API_KEY"] = ai_config.gemini.api_key
            env["GEMINI_PROJECT_ID"] = ai_config.gemini.project_id
            
            self.bridge_process = subprocess.Popen(
                ["node", str(bridge_path)],
                cwd=str(bridge_path.parent),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Esperar a que el bridge esté listo
            await asyncio.sleep(3)
            
            # Verificar que el bridge esté funcionando
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{self.bridge_url}/health") as response:
                        if response.status == 200:
                            self.logger.info("✅ Bridge Node.js iniciado correctamente")
                        else:
                            raise Exception("Bridge no responde correctamente")
                except Exception as e:
                    self.logger.error(f"❌ Error verificando bridge: {e}")
                    raise
                    
        except Exception as e:
            self.logger.error(f"❌ Error iniciando bridge: {e}")
            raise
    
    async def stop_bridge(self):
        """Detener el bridge Node.js"""
        if self.bridge_process:
            try:
                if os.name == 'nt':
                    # Windows
                    self.bridge_process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    # Unix/Linux
                    self.bridge_process.terminate()
                
                self.bridge_process.wait(timeout=5)
                self.logger.info("✅ Bridge Node.js detenido")
            except subprocess.TimeoutExpired:
                self.bridge_process.kill()
                self.logger.warning("⚠️ Bridge forzado a cerrar")
            except Exception as e:
                self.logger.error(f"❌ Error deteniendo bridge: {e}")
            finally:
                self.bridge_process = None
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
        """Realizar petición HTTP al bridge Node.js"""
        url = f"{self.bridge_url}/{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "POST":
                    async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        result = await response.json()
                elif method == "GET":
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        result = await response.json()
                elif method == "DELETE":
                    async with session.delete(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        result = await response.json()
                else:
                    raise ValueError(f"Método HTTP no soportado: {method}")
                
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Error en petición a {endpoint}: {e}")
            raise
    
    async def create_stagehand_session(self, headless: bool = True) -> str:
        """Crear nueva sesión de Stagehand con configuración Gemini"""
        if self.session_id:
            await self._close_stagehand_session()
        
        ai_config = get_ai_config()
        
        # Configuración para Stagehand con Gemini
        data = {
            "modelName": "gemini-1.5-flash",  # Modelo Gemini
            "apiKey": ai_config.gemini.api_key,
            "projectId": ai_config.gemini.project_id,
            "options": {
                "headless": headless,
                "viewport": {"width": 1280, "height": 720},
                "enableCaching": True,
                "debugDom": False
            }
        }
        
        try:
            response = await self._make_request("create", data)
            
            if response.get("success"):
                self.session_id = response.get("sessionId")
                self.logger.info(f"✅ Sesión Stagehand creada con Gemini: {self.session_id}")
                return self.session_id
            else:
                raise Exception(f"Error creando sesión: {response.get('error')}")
                
        except Exception as e:
            self.logger.error(f"❌ Error creando sesión Stagehand: {e}")
            raise
    
    async def navigate_to_page(self, url: str, wait_for: str = "networkidle") -> Dict[str, Any]:
        """Navegar a una página web usando Stagehand"""
        if not self.session_id:
            raise RuntimeError("Sesión no creada. Llama a create_stagehand_session() primero")
        
        try:
            data = {
                "sessionId": self.session_id,
                "url": url,
                "waitUntil": wait_for
            }
            
            response = await self._make_request("navigate", data)
            
            if response.get("success"):
                self.logger.info(f"✅ Navegación exitosa a: {url}")
                return response
            else:
                raise Exception(f"Error navegando: {response.get('error')}")
                
        except Exception as e:
            self.logger.error(f"❌ Error navegando a {url}: {e}")
            raise
    
    async def perform_action(self, instruction: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Realizar una acción usando instrucciones en lenguaje natural"""
        if not self.session_id:
            raise RuntimeError("Sesión no creada. Llama a create_stagehand_session() primero")
        
        try:
            data = {
                "sessionId": self.session_id,
                "instruction": instruction,
                "options": options or {}
            }
            
            response = await self._make_request("act", data)
            
            if response.get("success"):
                self.logger.info(f"✅ Acción realizada: {instruction}")
                return response
            else:
                raise Exception(f"Error realizando acción: {response.get('error')}")
                
        except Exception as e:
            self.logger.error(f"❌ Error realizando acción '{instruction}': {e}")
            raise
    
    async def extract_data(self, instruction: str, schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extraer datos de la página usando instrucciones en lenguaje natural"""
        if not self.session_id:
            raise RuntimeError("Sesión no creada. Llama a create_stagehand_session() primero")
        
        try:
            data = {
                "sessionId": self.session_id,
                "instruction": instruction,
                "schema": schema
            }
            
            response = await self._make_request("extract", data)
            
            if response.get("success"):
                self.logger.info(f"✅ Datos extraídos: {instruction}")
                return response
            else:
                raise Exception(f"Error extrayendo datos: {response.get('error')}")
                
        except Exception as e:
            self.logger.error(f"❌ Error extrayendo datos '{instruction}': {e}")
            raise
    
    async def fill_form(self, form_data: Dict[str, str], submit: bool = False) -> Dict[str, Any]:
        """
        Llenar formulario automáticamente usando IA
        
        Args:
            form_data: Diccionario con datos del formulario
            submit: Si enviar el formulario después de llenarlo
            
        Returns:
            Dict con resultado de la operación
        """
        if not self.session_id:
            raise RuntimeError("Sesión no creada. Llama a create_stagehand_session() primero")
        
        # Construir instrucción para llenar formulario
        form_instructions = []
        for field, value in form_data.items():
            form_instructions.append(f"Llenar el campo '{field}' con '{value}'")
        
        instruction = ". ".join(form_instructions)
        if submit:
            instruction += ". Luego enviar el formulario."
        
        return await self.perform_action(instruction)
    
    async def handle_popup(self, action: str = "close") -> Dict[str, Any]:
        """
        Manejar popups automáticamente
        
        Args:
            action: Acción a realizar (close, accept, dismiss)
            
        Returns:
            Dict con resultado de la operación
        """
        instruction = f"Si hay algún popup o modal abierto, {action} it"
        return await self.perform_action(instruction)
    
    async def wait_for_element(self, description: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Esperar a que aparezca un elemento específico
        
        Args:
            description: Descripción del elemento a esperar
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Dict con resultado de la espera
        """
        if not self.session_id:
            raise RuntimeError("Sesión no creada. Llama a create_stagehand_session() primero")
        
        try:
            data = {
                "sessionId": self.session_id,
                "description": description,
                "timeout": timeout
            }
            
            response = await self._make_request("wait", data)
            
            if response.get("success"):
                self.logger.info(f"⏳ Elemento encontrado: {description}")
                return response
            else:
                raise Exception(f"Error esperando elemento: {response.get('error')}")
                
        except Exception as e:
            self.logger.error(f"❌ Error esperando elemento '{description}': {e}")
            raise
    
    async def take_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Tomar captura de pantalla de la página actual
        
        Args:
            filename: Nombre del archivo (opcional)
            
        Returns:
            Dict con información de la captura
        """
        if not self.session_id:
            raise RuntimeError("Sesión no creada. Llama a create_stagehand_session() primero")
        
        try:
            data = {
                "sessionId": self.session_id,
                "filename": filename
            }
            
            response = await self._make_request("screenshot", data)
            
            if response.get("success"):
                self.logger.info("📸 Captura de pantalla tomada")
                return response
            else:
                raise Exception(f"Error tomando captura: {response.get('error')}")
                
        except Exception as e:
            self.logger.error(f"❌ Error tomando captura: {e}")
            raise
    
    async def execute_sequence(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ejecutar secuencia de acciones automatizadas
        
        Args:
            steps: Lista de pasos a ejecutar
            
        Returns:
            Lista con resultados de cada paso
        """
        results = []
        
        for i, step in enumerate(steps):
            self.logger.info(f"🔄 Ejecutando paso {i+1}/{len(steps)}: {step.get('description', 'Sin descripción')}")
            
            step_type = step.get("type")
            
            try:
                if step_type == "navigate":
                    result = await self.navigate_to_page(step["url"], step.get("wait_for", "networkidle"))
                
                elif step_type == "action":
                    result = await self.perform_action(step["instruction"], step.get("options", {}))
                
                elif step_type == "extract":
                    result = await self.extract_data(step["instruction"], step.get("schema"))
                
                elif step_type == "fill_form":
                    result = await self.fill_form(step["form_data"], step.get("submit", False))
                
                elif step_type == "wait":
                    result = await self.wait_for_element(step["description"], step.get("timeout", 30))
                
                elif step_type == "screenshot":
                    result = await self.take_screenshot(step.get("filename"))
                
                else:
                    result = {"error": f"Tipo de paso desconocido: {step_type}"}
                
                result["step_index"] = i
                result["step_description"] = step.get("description", "")
                results.append(result)
                
                # Delay entre pasos si se especifica
                if step.get("delay"):
                    await asyncio.sleep(step["delay"])
                    
            except Exception as e:
                error_result = {
                    "error": str(e),
                    "step_index": i,
                    "step_description": step.get("description", ""),
                    "step_type": step_type
                }
                results.append(error_result)
                
                # Si el paso es crítico, detener la secuencia
                if step.get("critical", False):
                    self.logger.error(f"❌ Paso crítico falló, deteniendo secuencia: {e}")
                    break
        
        return results
    
    async def _close_stagehand_session(self) -> Dict[str, Any]:
        """Cerrar sesión de Stagehand"""
        if not self.session_id:
            return {"message": "No hay sesión activa"}
        
        try:
            data = {"sessionId": self.session_id}
            response = await self._make_request("close", data, method="DELETE")
            
            if response.get("success"):
                self.logger.info("🔒 Sesión Stagehand cerrada")
                self.session_id = None
                return response
            else:
                raise Exception(f"Error cerrando sesión: {response.get('error')}")
                
        except Exception as e:
            self.logger.error(f"❌ Error cerrando sesión: {e}")
            return {"error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servicio"""
        ai_config = get_ai_config()
        return {
            "available": self.is_available(),
            "gemini_api_key_configured": bool(ai_config.gemini.api_key),
            "gemini_project_id": ai_config.gemini.project_id,
            "bridge_url": self.bridge_url,
            "bridge_running": bool(self.bridge_process),
            "active_session": self.session_id
        }


# Funciones de conveniencia
async def quick_extract(url: str, instruction: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Función de conveniencia para extracción rápida
    
    Args:
        url: URL a visitar
        instruction: Qué extraer
        schema: Esquema opcional
        
    Returns:
        Datos extraídos
    """
    async with StagehandService() as service:
        if not service.is_available():
            return {"error": "Stagehand no está disponible"}
        
        # Crear sesión y navegar
        await service.create_stagehand_session()
        await service.navigate_to_page(url)
        
        # Extraer datos
        result = await service.extract_data(instruction, schema)
        
        # Cerrar sesión
        await service._close_stagehand_session()
        
        return result


async def quick_automation(url: str, steps: List[str]) -> List[Dict[str, Any]]:
    """
    Función de conveniencia para automatización rápida
    
    Args:
        url: URL inicial
        steps: Lista de instrucciones a ejecutar
        
    Returns:
        Resultados de cada paso
    """
    async with StagehandService() as service:
        if not service.is_available():
            return [{"error": "Stagehand no está disponible"}]
        
        # Crear sesión y navegar
        await service.create_stagehand_session()
        await service.navigate_to_page(url)
        
        # Ejecutar pasos
        results = []
        for step in steps:
            result = await service.perform_action(step)
            results.append(result)
        
        # Cerrar sesión
        await service._close_stagehand_session()
        
        return results


if __name__ == "__main__":
    # Ejemplo de uso
    async def test_stagehand():
        async with StagehandService() as service:
            if service.is_available():
                print("🎭 Probando Stagehand Service...")
                
                # Crear sesión
                session_id = await service.create_stagehand_session()
                print(f"📱 Sesión creada: {session_id}")
                
                # Navegar a página de prueba
                nav_result = await service.navigate_to_page("https://example.com")
                print(f"🌐 Navegación: {nav_result}")
                
                # Extraer título
                extract_result = await service.extract_data("Extraer el título de la página")
                print(f"📊 Extracción: {extract_result}")
                
                # Cerrar sesión
                close_result = await service._close_stagehand_session()
                print(f"🔒 Sesión cerrada: {close_result}")
                
            else:
                print("❌ Stagehand no está disponible")
                print("Configura GEMINI_API_KEY y GEMINI_PROJECT_ID en tu archivo .env")
    
    # Ejecutar prueba
    asyncio.run(test_stagehand())