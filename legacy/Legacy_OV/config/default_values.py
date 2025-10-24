#!/usr/bin/env python3
"""
Default Configurations - Configuraciones por defecto para componentes modulares
===============================================================================

Este módulo centraliza las configuraciones por defecto que pueden ser utilizadas
por los componentes PopupHandler y ReportProcessor cuando no se especifican
configuraciones personalizadas.

Características principales:
- Configuraciones genéricas reutilizables
- Separación de configuraciones específicas por empresa
- Fácil mantenimiento y actualización
- Compatibilidad con múltiples extractores

Autor: ExtractorOV Team
Fecha: 2025-09-26
"""

from typing import List
from src.components.popup_handler import PopupConfig, PopupType, PopupAction
from src.components.report_processor import ProcessingRule

def get_default_popup_configs() -> List[PopupConfig]:
    """
    Retorna configuraciones por defecto para PopupHandler

    Returns:
        Lista de configuraciones de popup genéricas
    """
    configs = []

    # Diálogos JavaScript estándar
    configs.append(PopupConfig(
        name="js_alert",
        popup_type=PopupType.ALERT,
        selectors=[],  # Se maneja via dialog listener
        action=PopupAction.ACCEPT,
        priority=1
    ))

    configs.append(PopupConfig(
        name="js_confirm",
        popup_type=PopupType.CONFIRM,
        selectors=[],
        action=PopupAction.ACCEPT,
        priority=1
    ))

    # Modales comunes
    configs.append(PopupConfig(
        name="generic_modal",
        popup_type=PopupType.MODAL,
        selectors=[
            '.modal',
            '.modal-dialog',
            '[role="dialog"]',
            '.ui-dialog',
            '.popup-modal'
        ],
        action=PopupAction.CLOSE,
        priority=3
    ))

    # Banners de cookies
    configs.append(PopupConfig(
        name="cookie_banner",
        popup_type=PopupType.COOKIE_BANNER,
        selectors=[
            '#cookie-banner',
            '.cookie-banner',
            '.cookie-consent',
            '[class*="cookie"]',
            '[id*="cookie"]'
        ],
        action=PopupAction.ACCEPT,
        priority=8,
        text_patterns=['cookie', 'cookies', 'aceptar cookies']
    ))

    # Notificaciones
    configs.append(PopupConfig(
        name="notification",
        popup_type=PopupType.NOTIFICATION,
        selectors=[
            '.notification',
            '.alert',
            '.toast',
            '.snackbar',
            '[role="alert"]'
        ],
        action=PopupAction.CLOSE,
        priority=5
    ))

    # Diálogos de error
    configs.append(PopupConfig(
        name="error_dialog",
        popup_type=PopupType.ERROR_DIALOG,
        selectors=[
            '.error-dialog',
            '.error-modal',
            '[class*="error"]'
        ],
        action=PopupAction.CLOSE,
        priority=2,
        text_patterns=['error', 'problema', 'fallo']
    ))

    return configs

def get_default_processing_rules() -> List[ProcessingRule]:
    """
    Retorna reglas de procesamiento por defecto para ReportProcessor

    Returns:
        Lista de reglas de procesamiento genéricas
    """
    rules = []

    # Regla para reportes de Afinia
    rules.append(ProcessingRule(
        name="afinia_reports",
        pattern=r".*afinia.*\.(xlsx?|csv|pdf)$",
        company="afinia",
        report_type="general",
        target_directory="afinia/reports",
        rename_template="{company}_{type}_{date}_{timestamp}.{ext}",
        validation_rules=["min_size:1024", "max_age_days:30"]
    ))

    # Regla para reportes de Aire
    rules.append(ProcessingRule(
        name="aire_reports", 
        pattern=r".*aire.*\.(xlsx?|csv|pdf)$",
        company="aire",
        report_type="general",
        target_directory="aire/reports",
        rename_template="{company}_{type}_{date}_{timestamp}.{ext}",
        validation_rules=["min_size:1024", "max_age_days:30"]
    ))

    # Regla para reportes PQR
    rules.append(ProcessingRule(
        name="pqr_reports",
        pattern=r".*(pqr|peticion|queja|reclamo).*\.(xlsx?|csv)$",
        company="general",
        report_type="pqr",
        target_directory="{company}/pqr",
        rename_template="{company}_pqr_{date}_{timestamp}.{ext}",
        validation_rules=["min_size:512", "required_columns:fecha,tipo,estado"]
    ))

    # Regla para reportes financieros
    rules.append(ProcessingRule(
        name="financial_reports",
        pattern=r".*(factura|pago|cobro|financiero).*\.(xlsx?|csv|pdf)$",
        company="general", 
        report_type="financial",
        target_directory="{company}/financial",
        rename_template="{company}_financial_{date}_{timestamp}.{ext}",
        validation_rules=["min_size:1024"]
    ))

    return rules

def setup_default_components(popup_handler, report_processor):
    """
    Configura componentes con configuraciones por defecto

    Args:
        popup_handler: Instancia de PopupHandler
        report_processor: Instancia de ReportProcessor
    """
    # Registrar configuraciones de popup por defecto
    for config in get_default_popup_configs():
        popup_handler.register_popup_config(config)

    # Registrar reglas de procesamiento por defecto
    for rule in get_default_processing_rules():
        report_processor.add_processing_rule(rule)

if __name__ == "__main__":
    print("=== Default Configurations - Pruebas ===")

    # Mostrar configuraciones disponibles
    popup_configs = get_default_popup_configs()
    processing_rules = get_default_processing_rules()

    print(f"Configuraciones de popup por defecto: {len(popup_configs)}")
    for config in popup_configs:
        print(f" - {config.name}: {config.popup_type.value} -> {config.action.value}")

    print(f"\nReglas de procesamiento por defecto: {len(processing_rules)}")
    for rule in processing_rules:
        print(f" - {rule.name}: {rule.company} -> {rule.report_type}")