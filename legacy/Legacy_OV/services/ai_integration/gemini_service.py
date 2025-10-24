"""
Servicio de Integración con Google Gemini
=========================================

Este módulo proporciona integración completa con Google Gemini Free API
para análisis inteligente de documentos y procesamiento de PQRs.

Funcionalidades:
- Análisis de contenido de documentos PDF
- Clasificación automática de PQRs
- Extracción de información estructurada
- Generación de resúmenes inteligentes
- Detección de anomalías en datos
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import hashlib

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai no está instalado. Instálalo con: pip install google-generativeai")

from .config import GeminiConfig, get_ai_config


class GeminiService:
    """Servicio para integración con Google Gemini"""
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or get_ai_config().gemini
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.cache = {}
        
        if GEMINI_AVAILABLE and self.config.api_key:
            self._initialize_gemini()
        else:
            self.logger.warning("Gemini no está disponible - verifica la instalación y configuración")
    
    def _initialize_gemini(self):
        """Inicializar el cliente de Gemini"""
        try:
            genai.configure(api_key=self.config.api_key)
            
            # Configurar el modelo con parámetros de seguridad
            generation_config = {
                "temperature": self.config.temperature,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": self.config.max_tokens,
            }
            
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            self.model = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            self.logger.info(f"✅ Gemini inicializado correctamente con modelo {self.config.model_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando Gemini: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Verificar si Gemini está disponible y configurado"""
        return GEMINI_AVAILABLE and self.model is not None
    
    def _get_cache_key(self, prompt: str, context: str = "") -> str:
        """Generar clave de caché para una consulta"""
        content = f"{prompt}:{context}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def analyze_document_content(self, content: str, document_type: str = "PQR") -> Dict[str, Any]:
        """
        Analizar el contenido de un documento usando Gemini
        
        Args:
            content: Contenido del documento a analizar
            document_type: Tipo de documento (PQR, Factura, etc.)
            
        Returns:
            Dict con análisis estructurado del documento
        """
        if not self.is_available():
            return {"error": "Gemini no está disponible"}
        
        cache_key = self._get_cache_key(content, document_type)
        if cache_key in self.cache:
            self.logger.info("📋 Usando resultado desde caché")
            return self.cache[cache_key]
        
        prompt = f"""
        Analiza el siguiente documento de tipo {document_type} y extrae información estructurada:

        CONTENIDO DEL DOCUMENTO:
        {content}

        Por favor, proporciona un análisis en formato JSON con la siguiente estructura:
        {{
            "tipo_documento": "{document_type}",
            "resumen": "Resumen breve del contenido",
            "entidades_principales": ["entidad1", "entidad2"],
            "fechas_importantes": ["fecha1", "fecha2"],
            "numeros_referencia": ["ref1", "ref2"],
            "clasificacion": "categoria_del_documento",
            "urgencia": "alta|media|baja",
            "temas_principales": ["tema1", "tema2"],
            "acciones_requeridas": ["accion1", "accion2"],
            "confianza": 0.95
        }}

        Responde ÚNICAMENTE con el JSON, sin texto adicional.
        """
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content, 
                prompt
            )
            
            # Procesar respuesta
            result_text = response.text.strip()
            
            # Intentar parsear como JSON
            try:
                result = json.loads(result_text)
                result["timestamp"] = datetime.now().isoformat()
                result["model_used"] = self.config.model_name
                
                # Guardar en caché
                self.cache[cache_key] = result
                
                self.logger.info(f"✅ Documento analizado exitosamente: {result.get('clasificacion', 'N/A')}")
                return result
                
            except json.JSONDecodeError:
                # Si no es JSON válido, devolver respuesta como texto
                return {
                    "error": "Respuesta no es JSON válido",
                    "raw_response": result_text,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error analizando documento: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def classify_pqr(self, pqr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clasificar un PQR usando IA
        
        Args:
            pqr_data: Datos del PQR a clasificar
            
        Returns:
            Dict con clasificación y análisis del PQR
        """
        if not self.is_available():
            return {"error": "Gemini no está disponible"}
        
        # Construir contexto del PQR
        context = f"""
        DATOS DEL PQR:
        - Número: {pqr_data.get('numero', 'N/A')}
        - Fecha: {pqr_data.get('fecha', 'N/A')}
        - Tipo: {pqr_data.get('tipo', 'N/A')}
        - Estado: {pqr_data.get('estado', 'N/A')}
        - Descripción: {pqr_data.get('descripcion', 'N/A')}
        - Cliente: {pqr_data.get('cliente', 'N/A')}
        """
        
        prompt = f"""
        Analiza el siguiente PQR y proporciona una clasificación detallada:

        {context}

        Proporciona un análisis en formato JSON:
        {{
            "categoria_principal": "queja|peticion|reclamo|sugerencia",
            "subcategoria": "categoria_especifica",
            "prioridad": "alta|media|baja",
            "complejidad": "simple|media|compleja",
            "tiempo_estimado_resolucion": "horas_estimadas",
            "departamento_responsable": "departamento",
            "requiere_atencion_inmediata": true/false,
            "palabras_clave": ["palabra1", "palabra2"],
            "sentimiento": "positivo|neutral|negativo",
            "confianza_clasificacion": 0.95,
            "recomendaciones": ["recomendacion1", "recomendacion2"]
        }}

        Responde ÚNICAMENTE con el JSON.
        """
        
        return await self.analyze_document_content(prompt, "PQR_CLASSIFICATION")
    
    async def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extraer datos estructurados de texto usando un esquema definido
        
        Args:
            text: Texto a procesar
            schema: Esquema de datos esperado
            
        Returns:
            Dict con datos extraídos según el esquema
        """
        if not self.is_available():
            return {"error": "Gemini no está disponible"}
        
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
        
        prompt = f"""
        Extrae información del siguiente texto según el esquema proporcionado:

        TEXTO:
        {text}

        ESQUEMA ESPERADO:
        {schema_str}

        Extrae la información y devuélvela en formato JSON siguiendo exactamente el esquema.
        Si algún campo no se encuentra, usa null.

        Responde ÚNICAMENTE con el JSON.
        """
        
        return await self.analyze_document_content(prompt, "DATA_EXTRACTION")
    
    async def generate_summary(self, content: str, max_words: int = 100) -> Dict[str, Any]:
        """
        Generar resumen inteligente de contenido
        
        Args:
            content: Contenido a resumir
            max_words: Máximo número de palabras en el resumen
            
        Returns:
            Dict con resumen y metadatos
        """
        if not self.is_available():
            return {"error": "Gemini no está disponible"}
        
        prompt = f"""
        Genera un resumen conciso del siguiente contenido en máximo {max_words} palabras:

        CONTENIDO:
        {content}

        Proporciona el resultado en formato JSON:
        {{
            "resumen": "resumen_conciso_aqui",
            "puntos_clave": ["punto1", "punto2", "punto3"],
            "palabras_totales": numero_de_palabras,
            "tono": "formal|informal|tecnico|comercial",
            "idioma_detectado": "español|ingles|otro"
        }}

        Responde ÚNICAMENTE con el JSON.
        """
        
        return await self.analyze_document_content(prompt, "SUMMARY")
    
    async def detect_anomalies(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detectar anomalías en un conjunto de datos
        
        Args:
            data_list: Lista de datos a analizar
            
        Returns:
            Dict con anomalías detectadas
        """
        if not self.is_available():
            return {"error": "Gemini no está disponible"}
        
        data_str = json.dumps(data_list[:10], indent=2, ensure_ascii=False)  # Limitar a 10 elementos
        
        prompt = f"""
        Analiza el siguiente conjunto de datos y detecta posibles anomalías:

        DATOS:
        {data_str}

        Busca patrones inusuales, valores atípicos, inconsistencias o datos que no siguen el patrón normal.

        Proporciona el resultado en formato JSON:
        {{
            "anomalias_detectadas": [
                {{
                    "tipo": "tipo_de_anomalia",
                    "descripcion": "descripcion_detallada",
                    "indice_elemento": numero_elemento,
                    "severidad": "alta|media|baja",
                    "confianza": 0.95
                }}
            ],
            "total_anomalias": numero_total,
            "porcentaje_anomalias": porcentaje,
            "recomendaciones": ["recomendacion1", "recomendacion2"]
        }}

        Responde ÚNICAMENTE con el JSON.
        """
        
        return await self.analyze_document_content(prompt, "ANOMALY_DETECTION")
    
    async def batch_analyze(self, items: List[str], analysis_type: str = "general") -> List[Dict[str, Any]]:
        """
        Analizar múltiples elementos en lote
        
        Args:
            items: Lista de elementos a analizar
            analysis_type: Tipo de análisis a realizar
            
        Returns:
            Lista con resultados de análisis
        """
        if not self.is_available():
            return [{"error": "Gemini no está disponible"} for _ in items]
        
        results = []
        
        # Procesar en lotes para evitar límites de API
        batch_size = 5
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_tasks = []
            
            for item in batch:
                if analysis_type == "pqr":
                    task = self.classify_pqr(item)
                else:
                    task = self.analyze_document_content(item, analysis_type)
                batch_tasks.append(task)
            
            # Ejecutar lote con delay para respetar límites de API
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Delay entre lotes
            if i + batch_size < len(items):
                await asyncio.sleep(1)
        
        return results
    
    def clear_cache(self):
        """Limpiar caché de resultados"""
        self.cache.clear()
        self.logger.info("🗑️ Caché de Gemini limpiado")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servicio"""
        return {
            "available": self.is_available(),
            "model": self.config.model_name if self.is_available() else None,
            "cache_size": len(self.cache),
            "api_key_configured": bool(self.config.api_key),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }


# Función de conveniencia para uso rápido
async def quick_analyze(content: str, analysis_type: str = "general") -> Dict[str, Any]:
    """
    Función de conveniencia para análisis rápido
    
    Args:
        content: Contenido a analizar
        analysis_type: Tipo de análisis
        
    Returns:
        Resultado del análisis
    """
    service = GeminiService()
    return await service.analyze_document_content(content, analysis_type)


if __name__ == "__main__":
    # Ejemplo de uso
    async def test_gemini():
        service = GeminiService()
        
        if service.is_available():
            print("🤖 Probando Gemini Service...")
            
            # Prueba de análisis de documento
            test_content = """
            PQR #12345 - Fecha: 2024-01-15
            Cliente: Juan Pérez
            Tipo: Reclamo
            Descripción: Factura incorrecta por servicios no prestados
            Estado: Pendiente
            """
            
            result = await service.analyze_document_content(test_content, "PQR")
            print("📄 Resultado del análisis:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        else:
            print("❌ Gemini no está disponible")
            print("Configura GEMINI_API_KEY en tu archivo .env")
    
    # Ejecutar prueba
    asyncio.run(test_gemini())