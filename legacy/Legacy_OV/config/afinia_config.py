"""
Configuraciones específicas para Afinia - Oficina Virtual
Módulo que centraliza todas las configuraciones hardcodeadas
"""

import os
from src.components.popup_handler import PopupConfig, PopupType, PopupAction
from src.components.report_processor import ProcessingRule
from typing import List, Dict, Any

# ============================================================================
# CONFIGURACIONES DE POPUPS ESPECÍFICAS PARA AFINIA
# ============================================================================

def get_afinia_popup_configs() -> List[PopupConfig]:
    """
    Retorna las configuraciones de popups específicas para Afinia

    Returns:
        List[PopupConfig]: Lista de configuraciones de popups
    """
    configs = []

    # Popup de notificación específico de Afinia
    notification_config = PopupConfig(
        name="notification",
        popup_type=PopupType.NOTIFICATION,
        selectors=[
            '.notification',
            '.alert',
            '.toast',
            '.snackbar',
            '[role="alert"]',
            '#myModal .notification'
        ],
        action=PopupAction.CLOSE,
        priority=5,
        timeout=10.0,
        text_patterns=['notificación', 'aviso', 'información']
    )
    configs.append(notification_config)

    # Diálogo de error específico de Afinia
    error_dialog_config = PopupConfig(
        name="error_dialog",
        popup_type=PopupType.ERROR_DIALOG,
        selectors=[
            '.error-dialog',
            '.error-modal',
            '[class*="error"]',
            '#myModal .error',
            '.modal-body .error'
        ],
        action=PopupAction.CLOSE,
        priority=2,
        timeout=15.0,
        text_patterns=['error', 'problema', 'fallo', 'excepción']
    )
    configs.append(error_dialog_config)

    # Modal inicial específico de Afinia - Selectores basados en código legacy funcional
    afinia_modal_config = PopupConfig(
        name="afinia_initial_modal",
        popup_type=PopupType.MODAL,
        selectors=[
            '#myModal a.closePopUp i[ng-click="closeDialog()"]',  # Selector más específico del botón de cierre
            '#myModal i.material-icons[ng-click="closeDialog()"]',  # Icono con ng-click
            'a.closePopUp i.material-icons',  # Contenedor del botón de cierre
            '#myModal .closePopUp',  # Enlace contenedor
            'i[ng-click="closeDialog()"]',  # Selector directo del ng-click
            '.modal-content i.material-icons:has-text("close")',  # Por el texto "close"
            '#myModal.modal[style*="display: block"] i.material-icons',  # Modal visible con icono
            'div[id="myModal"] a.closePopUp',  # Contenedor específico del modal
            '.closePopUp[style*="cursor: pointer"]',  # Por el estilo cursor pointer
            '#myModal',  # Fallback al modal completo
        ],
        action=PopupAction.CLOSE,
        priority=1,
        timeout=20.0,
        text_patterns=['myModal', 'closeDialog', 'cerrar', 'close']
    )
    configs.append(afinia_modal_config)

    # Popup de sesión expirada
    session_expired_config = PopupConfig(
        name="session_expired",
        popup_type=PopupType.MODAL,
        selectors=[
            '.session-expired',
            '#timeout-modal',
            '[class*="session"]'
        ],
        action=PopupAction.ACCEPT,
        priority=1,
        timeout=10.0,
        text_patterns=['sesión expirada', 'session expired', 'timeout']
    )
    configs.append(session_expired_config)

    return configs

# ============================================================================
# CONFIGURACIONES DE REPORTES ESPECÍFICAS PARA AFINIA
# ============================================================================

def get_afinia_report_rules() -> List[ProcessingRule]:
    """
    Retorna las reglas de procesamiento de reportes específicas para Afinia

    Returns:
        List[ProcessingRule]: Lista de reglas de procesamiento
    """
    rules = []

    # Regla para reportes PQR
    pqr_rule = ProcessingRule(
        name="afinia_pqr_processing",
        file_patterns=['*PQR*.xlsx', '*pqr*.xlsx', '*radicacion*.xlsx'],
        processing_steps=[
            'validate_headers',
            'clean_data',
            'standardize_dates',
            'extract_metadata',
            'generate_summary'
        ],
        output_format='json',
        validation_rules={
            'required_columns': [
                'numero_radicado',
                'fecha_radicacion',
                'tipo_solicitud',
                'estado'
            ],
            'date_columns': ['fecha_radicacion', 'fecha_vencimiento'],
            'numeric_columns': ['numero_radicado']
        }
    )
    rules.append(pqr_rule)

    # Regla para reportes financieros
    financial_rule = ProcessingRule(
        name="afinia_financial_processing",
        file_patterns=['*financiero*.xlsx', '*facturacion*.xlsx'],
        processing_steps=[
            'validate_financial_data',
            'calculate_totals',
            'generate_charts',
            'export_summary'
        ],
        output_format='pdf',
        validation_rules={
            'required_columns': [
                'periodo',
                'valor',
                'concepto'
            ],
            'numeric_columns': ['valor'],
            'date_columns': ['periodo']
        }
    )
    rules.append(financial_rule)

    # Regla para reportes de calidad
    quality_rule = ProcessingRule(
        name="afinia_quality_processing",
        file_patterns=['*calidad*.xlsx', '*indicadores*.xlsx'],
        processing_steps=[
            'validate_quality_metrics',
            'calculate_kpis',
            'generate_dashboard_data'
        ],
        output_format='json',
        validation_rules={
            'required_columns': [
                'indicador',
                'valor',
                'meta',
                'periodo'
            ],
            'numeric_columns': ['valor', 'meta'],
            'percentage_columns': ['cumplimiento']
        }
    )
    rules.append(quality_rule)

    return rules

# ============================================================================
# CONFIGURACIÓN PRINCIPAL DE AFINIA
# ============================================================================

AFINIA_SPECIFIC_CONFIG = {
    "company_name": "afinia",
    "base_url": "https://caribemar.facture.co/",
    "login_url": "https://caribemar.facture.co/login",
    "pqr_url": "https://caribemar.facture.co/Listado-Radicaci%C3%B3n-PQR#/List",
    
    # Configuraciones de tiempo de espera
    "timeouts": {
        "popup_timeout": 15.0,
        "login_timeout": 30.0,
        "download_timeout": 60.0,
        "page_load_timeout": 45.0
    },
    
    # Directorios específicos
    "directories": {
        "base_download": "downloads/afinia",
        "screenshots": "downloads/afinia/screenshots",
        "reports": "downloads/afinia/reports",
        "pqr": "downloads/afinia/pqr",
        "financial": "downloads/afinia/financial",
        "data/logs": "logs/afinia"
    },
    
    # Configuraciones de extracción
    "extraction": {
        "default_date_range_days": 7,
        "max_records_per_session": 50,
        "retry_attempts": 3,
        "screenshot_on_error": True,
        "generate_pdf_reports": True,
        "handle_attachments": True
    },
    
    # Configuraciones de logging
    "logging": {
        "level": "INFO",
        "format": "[AFINIA-OV] %(levelname)s: %(message)s",
        "file_logging": True,
        "console_logging": True
    }
}

def get_afinia_config() -> Dict[str, Any]:
    """
    Retorna la configuración completa de Afinia con credenciales desde variables de entorno

    Returns:
        Dict[str, Any]: Configuración completa
    """
    config = AFINIA_SPECIFIC_CONFIG.copy()
    
    # Agregar credenciales desde variables de entorno
    config['username'] = os.getenv('OV_AFINIA_USERNAME', '')
    config['password'] = os.getenv('OV_AFINIA_PASSWORD', '')
    config['url'] = os.getenv('OV_AFINIA_URL', config.get('base_url', 'https://caribemar.facture.co/'))
    config['pqr_url'] = os.getenv('OV_AFINIA_PQR_URL', config.get('pqr_url', 'https://caribemar.facture.co/Listado-Radicaci%C3%B3n-PQR#/List'))
    
    return config

def setup_afinia_components(popup_handler, report_processor):
    """
    Configura los componentes con las configuraciones específicas de Afinia

    Args:
        popup_handler: Instancia de PopupHandler
        report_processor: Instancia de ReportProcessor
    """
    # Registrar configuraciones de popups
    for popup_config in get_afinia_popup_configs():
        popup_handler.register_popup_config(popup_config)

    # Registrar reglas de procesamiento de reportes
    for report_rule in get_afinia_report_rules():
        report_processor.add_processing_rule(report_rule)