#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Logging Unificado - ExtractorOV_Modular
================================================================

Este módulo proporciona una configuración unificada de logging para todo el proyecto,
con logs específicos por servicio (Afinia/Aire) y carpetas visibles.

Características:
- Un solo archivo de log por servicio (Afinia y Aire)
- Carpetas visibles (no ocultas)
- Rotación automática de logs
- Configuración centralizada
- Compatibilidad con métricas existentes
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import json

class UnifiedLogger:
    """Clase para manejar el sistema de logging unificado"""
    
    # Configuración de servicios
    SERVICES = {
        'afinia': {
            'name': 'afinia',
            'log_file': 'afinia_ov.log',
            'description': 'Oficina Virtual Afinia - Extractor'
        },
        'aire': {
            'name': 'aire', 
            'log_file': 'aire_ov.log',
            'description': 'Oficina Virtual Aire - Extractor'
        }
    }
    
    def __init__(self, base_logs_dir: str = "data/logs"):
        """
        Inicializa el sistema de logging unificado
        
        Args:
            base_logs_dir: Directorio base para logs (visible, no oculto)
        """
        self.base_logs_dir = Path(base_logs_dir)
        self.loggers = {}
        self._setup_logging_structure()
    
    def _setup_logging_structure(self):
        """Crea la estructura de directorios de logging"""
        # Crear directorio base visible
        self.base_logs_dir.mkdir(exist_ok=True)
        
        # Crear subdirectorios para organización
        (self.base_logs_dir / "current").mkdir(exist_ok=True)
        (self.base_logs_dir / "archived").mkdir(exist_ok=True)
        
    def get_logger(self, service: str, component: Optional[str] = None) -> logging.Logger:
        """
        Obtiene o crea un logger para el servicio especificado
        
        Args:
            service: Nombre del servicio ('afinia' o 'aire')
            component: Componente específico (opcional)
            
        Returns:
            logging.Logger: Logger configurado
        """
        if service not in self.SERVICES:
            raise ValueError(f"Servicio '{service}' no válido. Servicios disponibles: {list(self.SERVICES.keys())}")
        
        # Crear nombre único del logger
        logger_name = f"{service}"
        if component:
            logger_name += f".{component}"
            
        # Si ya existe, retornarlo
        if logger_name in self.loggers:
            return self.loggers[logger_name]
            
        # Crear nuevo logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        # Evitar duplicar handlers
        if not logger.handlers:
            self._setup_handlers(logger, service)
            
        self.loggers[logger_name] = logger
        return logger
    
    def _setup_handlers(self, logger: logging.Logger, service: str):
        """Configura los handlers para un logger específico"""
        service_config = self.SERVICES[service]
        
        # Handler para archivo principal del servicio (con rotación)
        log_file_path = self.base_logs_dir / "current" / service_config['log_file']
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato profesional sin emojis
        # [YYYY-MM-DD_HH:MM:SS][servicio][core][componente][LEVEL] - mensaje
        def clean_message(record):
            # Remover emojis del mensaje
            import re
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                u"\U0001F680-\U0001F6FF"  # transport & map
                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                u"\U00002500-\U00002BEF"  # chinese char
                u"\U00002702-\U000027B0"
                u"\U00002702-\U000027B0"
                u"\U000024C2-\U0001F251"
                u"\U0001f926-\U0001f937"
                u"\U00010000-\U0010ffff"
                u"\u2640-\u2642" 
                u"\u2600-\u2B55"
                u"\u200d"
                u"\u23cf"
                u"\u23e9"
                u"\u231a"
                u"\ufe0f"  # dingbats
                u"\u3030"
                "]+", flags=re.UNICODE)
            return emoji_pattern.sub(r'', record.getMessage()).strip()
        
        class ProfessionalFormatter(logging.Formatter):
            def format(self, record):
                # Extraer información del servicio del nombre del logger
                logger_parts = record.name.split('.')
                service = 'general'
                core = 'system'
                component = 'main'
                
                # Identificar servicio
                if 'afinia' in record.name.lower():
                    service = 'afinia'
                elif 'aire' in record.name.lower():
                    service = 'aire'
                
                # Identificar core y componente
                if len(logger_parts) >= 2:
                    core = logger_parts[-2] if len(logger_parts) > 1 else 'main'
                    component = logger_parts[-1]
                
                # Limpiar mensaje de emojis
                clean_msg = clean_message(record)
                
                # Formato: [YYYY-MM-DD_HH:MM:SS][servicio][core][componente][LEVEL] - mensaje
                timestamp = self.formatTime(record, '%Y-%m-%d_%H:%M:%S')
                return f"[{timestamp}][{service}][{core}][{component}][{record.levelname}] - {clean_msg}"
        
        formatter = ProfessionalFormatter()
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    def log_session_start(self, service: str, session_data: Dict[str, Any]):
        """Registra el inicio de una sesión"""
        logger = self.get_logger(service, "session")
        
        session_info = {
            'event': 'session_start',
            'service': service,
            'timestamp': datetime.now().isoformat(),
            'data': session_data
        }
        
        logger.info(f"SESSION_START: {json.dumps(session_info, ensure_ascii=False)}")
        
    def log_session_end(self, service: str, session_data: Dict[str, Any]):
        """Registra el fin de una sesión"""
        logger = self.get_logger(service, "session")
        
        session_info = {
            'event': 'session_end',
            'service': service,
            'timestamp': datetime.now().isoformat(),
            'data': session_data
        }
        
        logger.info(f"SESSION_END: {json.dumps(session_info, ensure_ascii=False)}")
        
    def log_download(self, service: str, file_info: Dict[str, Any]):
        """Registra una descarga"""
        logger = self.get_logger(service, "download")
        
        download_info = {
            'event': 'file_download',
            'service': service,
            'timestamp': datetime.now().isoformat(),
            'file_info': file_info
        }
        
        logger.info(f"DOWNLOAD: {json.dumps(download_info, ensure_ascii=False)}")
        
    def log_error(self, service: str, error_info: Dict[str, Any]):
        """Registra un error"""
        logger = self.get_logger(service, "error")
        
        error_data = {
            'event': 'error',
            'service': service,
            'timestamp': datetime.now().isoformat(),
            'error_info': error_info
        }
        
        logger.error(f"ERROR: {json.dumps(error_data, ensure_ascii=False)}")
        
    def get_service_stats(self, service: str) -> Dict[str, Any]:
        """Obtiene estadísticas del servicio"""
        service_log_file = self.base_logs_dir / "current" / self.SERVICES[service]['log_file']
        
        if not service_log_file.exists():
            return {'total_lines': 0, 'file_size': 0, 'last_modified': None}
            
        stat = service_log_file.stat()
        
        # Contar líneas aproximadamente
        with open(service_log_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
            
        return {
            'total_lines': line_count,
            'file_size': stat.st_size,
            'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'log_file': str(service_log_file)
        }


# Instancia global del sistema de logging unificado
_unified_logger = None

def get_unified_logger() -> UnifiedLogger:
    """
    Obtiene la instancia global del sistema de logging unificado
    
    Returns:
        UnifiedLogger: Instancia del sistema unificado
    """
    global _unified_logger
    if _unified_logger is None:
        _unified_logger = UnifiedLogger()
    return _unified_logger

def setup_service_logging(service: str, component: Optional[str] = None) -> logging.Logger:
    """
    Función de conveniencia para configurar logging para un servicio
    
    Args:
        service: Nombre del servicio ('afinia' o 'aire')
        component: Componente específico (opcional)
        
    Returns:
        logging.Logger: Logger configurado
    """
    unified_logger = get_unified_logger()
    return unified_logger.get_logger(service, component)

def setup_professional_logging() -> None:
    """
    Configura el formato profesional para TODOS los loggers del sistema
    """
    # Obtener todos los loggers existentes
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    loggers.append(logging.getLogger())  # Root logger
    
    # Crear formatter profesional
    class GlobalProfessionalFormatter(logging.Formatter):
        def format(self, record):
            # Limpiar mensaje de emojis
            import re
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"  # emoticons
                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                u"\U0001F680-\U0001F6FF"  # transport & map
                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                u"\U00002500-\U00002BEF"  # chinese char
                u"\U00002702-\U000027B0"
                u"\U00002702-\U000027B0"
                u"\U000024C2-\U0001F251"
                u"\U0001f926-\U0001f937"
                u"\U00010000-\U0010ffff"
                u"\u2640-\u2642" 
                u"\u2600-\u2B55"
                u"\u200d"
                u"\u23cf"
                u"\u23e9"
                u"\u231a"
                u"\ufe0f"  # dingbats
                u"\u3030"
                "]+", flags=re.UNICODE)
            
            clean_msg = emoji_pattern.sub(r'', record.getMessage()).strip()
            
            # Detectar servicio del nombre del logger
            logger_parts = record.name.split('.')
            service = 'general'
            core = 'system'
            component = 'main'
            
            # Identificar servicio
            if 'afinia' in record.name.lower():
                service = 'afinia'
            elif 'aire' in record.name.lower():
                service = 'aire'
            elif any(keyword in record.name.lower() for keyword in ['browser', 'auth', 'download', 'report', 'pqr']):
                # Detectar servicio del contexto si es posible
                service = 'afinia'  # Default, se puede mejorar con contexto
            
            # Identificar core y componente
            if len(logger_parts) >= 2:
                core = logger_parts[-2] if len(logger_parts) > 1 else 'system'
                component = logger_parts[-1]
            elif len(logger_parts) == 1:
                component = logger_parts[0]
            
            # Mejorar detección basada en el contenido del mensaje
            message_text = clean_msg.lower()
            
            # Detectar por contexto del mensaje con más granularidad
            # Orden de prioridad: más específico primero
            
            # DETECTAR COMPONENTES ESPECÍFICOS PRIMERO (más específico -> menos específico)
            
            # Componentes de gestión del sistema
            if 'afiniamanager inicializado' in message_text or 'inicializando extractor' in message_text:
                core = 'system'
                component = 'main_coordinator'
            elif 'validando entorno' in message_text or 'credenciales configuradas' in message_text:
                core = 'system'
                component = 'environment_validator'
            elif 'directorios verificados' in message_text:
                core = 'filesystem'
                component = 'directory_validator'
            elif 'rango de fechas' in message_text:
                core = 'config'
                component = 'date_configurator'
            elif 'configuración:' in message_text and 'usuario:' in message_text:
                core = 'config'
                component = 'session_configurator'
            elif 'inicializando componentes modulares' in message_text:
                core = 'system'
                component = 'module_initializer'
            elif 'procesador de pqr inicializado' in message_text:
                core = 'pqr'
                component = 'pqr_initializer'
            elif 'componentes inicializados correctamente' in message_text:
                core = 'system'
                component = 'component_validator'
            
            # Componentes específicos de PQR
            elif 'secuencia específica' in message_text or ('paso' in message_text and any(x in message_text for x in ['1', '2', '3', '4', '5'])):
                core = 'pqr'
                component = 'sequence_processor'
            elif 'sgc' in message_text or ('pdf' in message_text and 'generar' in message_text):
                core = 'pqr'
                component = 'pdf_generator'
            elif 'adjunto' in message_text or ('descarga' in message_text and ('pdf' in message_text or 'archivo' in message_text)):
                core = 'pqr'
                component = 'attachment_downloader'
            elif 'json' in message_text and ('extrayendo' in message_text or 'guardando' in message_text):
                core = 'pqr'
                component = 'data_extractor'
            elif 'procesando pqr' in message_text or 'procesamiento de pqr' in message_text:
                core = 'pqr'
                component = 'main_processor'
            elif 'lista iniciando procesamiento' in message_text:
                core = 'pqr'
                component = 'batch_processor'
            elif 'encontrados' in message_text and 'botones' in message_text:
                core = 'ui'
                component = 'button_scanner'
            elif 'total de botones encontrados' in message_text:
                core = 'ui'
                component = 'element_counter'
            elif 'procesando pqr #' in message_text:
                core = 'pqr'
                component = 'item_processor'
            
            # Componentes de navegación y UI
            elif 'nueva pestaña' in message_text or 'javascript window.open' in message_text:
                core = 'browser'
                component = 'tab_manager'
            elif 'popup' in message_text or 'modal' in message_text:
                core = 'ui'
                component = 'popup_handler'
            elif 'filtro' in message_text or ('configuración' in message_text and 'fecha' in message_text):
                core = 'ui'
                component = 'filter_configurator'
            elif 'selector' in message_text or 'elemento' in message_text:
                core = 'ui'
                component = 'element_finder'
            
            # Componentes de autenticación
            elif 'login' in message_text or 'autenticación' in message_text or 'credenciales' in message_text:
                core = 'auth'
                component = 'authenticator'
            
            # Componentes de navegación y sección
            elif 'navegando a sección' in message_text:
                core = 'navigation'
                component = 'section_navigator'
            elif 'navegando a url' in message_text:
                core = 'navigation'
                component = 'url_navigator'
            elif 'navegando' in message_text or 'navegación' in message_text:
                core = 'browser'
                component = 'navigator'
            elif 'timeout' in message_text and 'navegador' in message_text:
                core = 'browser'
                component = 'config_manager'
            elif 'proceso de filtrado' in message_text:
                core = 'filter'
                component = 'filter_processor'
            elif 'configuración de filtros' in message_text:
                core = 'filter'
                component = 'filter_configurator'
            elif 'expandiendo panel' in message_text:
                core = 'ui'
                component = 'panel_expander'
            elif 'configurando estado' in message_text:
                core = 'form'
                component = 'state_configurator'
            elif 'ejecutando búsqueda' in message_text:
                core = 'search'
                component = 'search_executor'
            
            # Componentes de datos
            elif 'tabla' in message_text or ('registros' in message_text and 'extra' in message_text):
                core = 'data'
                component = 'table_extractor'
            elif 'procesando resultados' in message_text:
                core = 'data'
                component = 'results_processor'
            
            # Componentes de gestión
            elif 'paginación' in message_text or 'checkpoint' in message_text:
                core = 'pagination'
                component = 'checkpoint_manager'
            elif 'inicializando' in message_text and 'componente' in message_text:
                core = 'system'
                component = 'initializer'
            elif 'configurando' in message_text:
                core = 'config'
                component = 'configurator'
            elif 'limpieza' in message_text or 'cleanup' in message_text:
                core = 'system'
                component = 'cleanup_manager'
            
            # Patrones más específicos por palabras clave
            elif 'screenshot' in message_text or 'captura' in message_text:
                core = 'debug'
                component = 'screenshot_manager'
            elif 'esperando' in message_text or 'timeout' in message_text:
                core = 'browser'
                component = 'wait_manager'
            elif 'campo' in message_text and ('llenar' in message_text or 'encontrar' in message_text):
                core = 'form'
                component = 'field_manager'
            elif 'botón' in message_text and ('clic' in message_text or 'encontrado' in message_text):
                core = 'ui'
                component = 'button_handler'
            elif 'regla' in message_text and 'procesamiento' in message_text:
                core = 'config'
                component = 'rule_processor'
            elif 'archivo' in message_text and ('guardado' in message_text or 'generado' in message_text):
                core = 'file'
                component = 'file_manager'
            elif 'datos' in message_text and ('tabla' in message_text or 'extraídos' in message_text):
                core = 'data'
                component = 'field_extractor'
            elif 'validando' in message_text or 'verificando' in message_text:
                core = 'validation'
                component = 'validator'
            elif 'directorio' in message_text or 'carpeta' in message_text:
                core = 'filesystem'
                component = 'directory_manager'
            elif 'sesión' in message_text or 'checkpoint' in message_text:
                core = 'session'
                component = 'session_manager'
            
            # Fallbacks generales
            elif 'extractor' in message_text or 'extracción' in message_text:
                core = 'extractor'
                component = 'coordinator'
            elif 'manager' in message_text:
                core = 'system'
                component = 'manager'
            elif 'procesamiento' in message_text:
                core = 'processor'
                component = 'main'
            
            # Mapear nombres conocidos con más detalle
            name_mapping = {
                'BROWSER-MANAGER': {'core': 'browser', 'component': 'manager'},
                'AUTH-MANAGER': {'core': 'auth', 'component': 'manager'},
                'DOWNLOAD-MANAGER': {'core': 'download', 'component': 'manager'},
                'REPORT-PROCESSOR': {'core': 'report', 'component': 'processor'},
                'PQR-EXTRACTOR': {'core': 'pqr', 'component': 'extractor'},
                'AFINIA-OV': {'core': 'extractor', 'component': 'afinia_main'},
                'AFINIA-PQR': {'core': 'pqr', 'component': 'processor'},
                'AFINIA-PAGINATION': {'core': 'pagination', 'component': 'manager'},
                'AFINIA-MANAGER': {'core': 'manager', 'component': 'coordinator'},
                'AFINIA-DOWNLOAD': {'core': 'download', 'component': 'afinia_mgr'},
                'AFINIA-FILTER': {'core': 'filter', 'component': 'afinia_mgr'},
                'AFINIA-POPUP': {'core': 'popup', 'component': 'handler'},
                'AIRE-OV': {'core': 'extractor', 'component': 'aire_main'},
                'AIRE-PQR': {'core': 'pqr', 'component': 'aire_proc'},
                'AIRE-PAGINATION': {'core': 'pagination', 'component': 'aire_mgr'}
            }
            
            if record.name in name_mapping:
                core = name_mapping[record.name]['core']
                component = name_mapping[record.name]['component']
            
            # Formato: [YYYY-MM-DD_HH:MM:SS][servicio][core][componente][LEVEL] - mensaje
            timestamp = self.formatTime(record, '%Y-%m-%d_%H:%M:%S')
            return f"[{timestamp}][{service}][{core}][{component}][{record.levelname}] - {clean_msg}"
    
    # Aplicar formatter a todos los handlers
    professional_formatter = GlobalProfessionalFormatter()
    
    for logger in loggers:
        for handler in logger.handlers:
            handler.setFormatter(professional_formatter)

def initialize_professional_logging() -> None:
    """
    Inicializa el sistema de logging profesional para toda la aplicación
    """
    # Configurar el logger unificado principal
    unified_logger = get_unified_logger()
    
    # Aplicar formato profesional a todos los loggers existentes
    setup_professional_logging()
    
    print("[INIT][system][config][logging][INFO] - Sistema de logging profesional inicializado")

def log_system_event(service: str, event_type: str, data: Dict[str, Any]):
    """
    Función de conveniencia para registrar eventos del sistema
    
    Args:
        service: Servicio que genera el evento
        event_type: Tipo de evento
        data: Datos del evento
    """
    unified_logger = get_unified_logger()
    logger = unified_logger.get_logger(service, "system")
    
    event_info = {
        'event': event_type,
        'service': service,
        'timestamp': datetime.now().isoformat(),
        'data': data
    }
    
    logger.info(f"SYSTEM_EVENT: {json.dumps(event_info, ensure_ascii=False)}")

def get_all_services_stats() -> Dict[str, Dict[str, Any]]:
    """
    Obtiene estadísticas de todos los servicios
    
    Returns:
        Dict: Estadísticas de todos los servicios
    """
    unified_logger = get_unified_logger()
    stats = {}
    
    for service in UnifiedLogger.SERVICES.keys():
        stats[service] = unified_logger.get_service_stats(service)
        
    return stats

# Compatibilidad con sistema anterior
def setup_legacy_logging():
    """Configuración de compatibilidad con el sistema anterior"""
    # Redirigir logging básico al sistema unificado
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )