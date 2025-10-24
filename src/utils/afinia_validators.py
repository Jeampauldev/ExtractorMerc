"""
Validadores para Mercurio Afinia
================================

Validadores específicos para datos extraídos de Mercurio Afinia.
Hereda funcionalidad base pero con adaptaciones específicas.
"""

import logging
import hashlib
from typing import Dict, List, Optional, Any

# Importar validador base
from e5_processors.afinia.validators import JSONValidator
from .config import FIELD_MAPPING_MERCURIO

logger = logging.getLogger(__name__)

class MercurioJSONValidator(JSONValidator):
    """
    Validador específico para datos JSON de Mercurio Afinia
    
    Hereda funcionalidad base pero adapta validaciones
    específicas para estructura de datos de Mercurio.
    """
    
    def __init__(self):
        """Inicializa el validador para Mercurio"""
        super().__init__()
        self.field_mapping = FIELD_MAPPING_MERCURIO
        logger.info("✅ MercurioJSONValidator inicializado")
    
    def validate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida un registro de Mercurio
        
        Args:
            record: Registro a validar
            
        Returns:
            Dict con resultado de validación
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validaciones básicas heredadas
            base_result = super().validate_record(record)
            result['errors'].extend(base_result.get('errors', []))
            result['warnings'].extend(base_result.get('warnings', []))
            
            # Validaciones específicas de Mercurio
            self._validate_mercurio_specific_fields(record, result)
            
            # Determinar validez final
            result['is_valid'] = len(result['errors']) == 0
            
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"Error validando registro: {str(e)}")
            logger.error(f"Error en validación: {str(e)}")
        
        return result
    
    def _validate_mercurio_specific_fields(self, record: Dict[str, Any], result: Dict[str, Any]):
        """
        Validaciones específicas para campos de Mercurio
        
        Args:
            record: Registro a validar
            result: Resultado de validación a actualizar
        """
        # Verificar que tengamos al menos uno de los identificadores principales
        numero_radicado = record.get('numero_radicado') or record.get('radicado')
        numero_sgc = record.get('numero_reclamo_sgc') or record.get('sgc')
        
        if not numero_radicado and not numero_sgc:
            result['errors'].append("Debe tener al menos número de radicado o SGC")
        
        # Validar formato de radicado si existe (Mercurio puede tener formato diferente)
        if numero_radicado:
            # Mercurio podría tener formatos específicos
            if not str(numero_radicado).strip():
                result['warnings'].append("Número de radicado está vacío")
        
        # Validar campos específicos de Mercurio
        tipo_solicitud = record.get('tipo_solicitud') or record.get('tipo_pqr')
        if tipo_solicitud and len(str(tipo_solicitud)) > 100:
            result['warnings'].append("Tipo de solicitud muy largo, se truncará")
        
        # Validar estado específico de Mercurio
        estado = record.get('estado') or record.get('estado_solicitud')
        if estado:
            # Estados comunes en Mercurio
            estados_validos = [
                'pendiente', 'en proceso', 'resuelto', 'cerrado',
                'abierto', 'tramite', 'solucionado', 'anulado'
            ]
            if str(estado).lower() not in estados_validos:
                result['warnings'].append(f"Estado no reconocido: {estado}")
    
    def generate_content_hash(self, record: Dict[str, Any]) -> str:
        """
        Genera hash de contenido específico para Mercurio
        
        Args:
            record: Registro para generar hash
            
        Returns:
            Hash MD5 del contenido
        """
        try:
            # Campos clave para identificar duplicados en Mercurio
            key_fields = [
                record.get('numero_radicado', ''),
                record.get('radicado', ''),
                record.get('numero_reclamo_sgc', ''),
                record.get('sgc', ''),
                record.get('cuerpo_reclamacion', ''),
                record.get('descripcion', ''),
                record.get('fecha', ''),
                record.get('fecha_solicitud', ''),
                record.get('documento_identidad', ''),
                record.get('cedula', '')
            ]
            
            # Concatenar campos no vacíos
            content = '|'.join([str(field) for field in key_fields if field])
            
            # Generar hash MD5
            return hashlib.md5(content.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"Error generando hash de contenido: {str(e)}")
            return ""
