#!/usr/bin/env python3
"""
Logger y Métricas para Mercurio Aire
====================================

Sistema de logging y recolección de métricas específico para Mercurio Aire.
"""

import logging
from typing import Dict, Any
from e5_processors.aire.logger import MetricsCollector as AireMetricsCollector

logger = logging.getLogger(__name__)

class MetricsCollector(AireMetricsCollector):
    """
    Recolector de métricas específico para Mercurio Aire
    Hereda de AireMetricsCollector y añade métricas específicas
    """
    
    def __init__(self):
        """Inicializa el recolector de métricas para Mercurio Aire"""
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("📊 MetricsCollector para Mercurio Aire inicializado")
        
        # Métricas específicas de Mercurio
        self.mercurio_metrics = {
            'login_attempts': 0,
            'login_failures': 0,
            'session_duration': 0,
            'captcha_solved': 0,
            'navigation_errors': 0
        }
    
    def record_login_attempt(self, success: bool = True):
        """
        Registra un intento de login
        
        Args:
            success: Si el login fue exitoso
        """
        self.mercurio_metrics['login_attempts'] += 1
        if not success:
            self.mercurio_metrics['login_failures'] += 1
        
        self.logger.info(f"🔐 Login attempt: {'✅ Success' if success else '❌ Failed'}")
    
    def record_captcha_solved(self):
        """Registra que se resolvió un captcha"""
        self.mercurio_metrics['captcha_solved'] += 1
        self.logger.info("🧩 Captcha resuelto")
    
    def record_navigation_error(self, error_type: str):
        """
        Registra un error de navegación
        
        Args:
            error_type: Tipo de error de navegación
        """
        self.mercurio_metrics['navigation_errors'] += 1
        self.logger.warning(f"🚫 Error de navegación: {error_type}")
    
    def get_mercurio_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen de métricas específicas de Mercurio
        
        Returns:
            Dict con métricas de Mercurio
        """
        summary = self.get_summary()
        summary['mercurio_specific'] = self.mercurio_metrics.copy()
        
        # Calcular tasa de éxito de login
        if self.mercurio_metrics['login_attempts'] > 0:
            success_rate = ((self.mercurio_metrics['login_attempts'] - 
                           self.mercurio_metrics['login_failures']) / 
                          self.mercurio_metrics['login_attempts']) * 100
            summary['mercurio_specific']['login_success_rate'] = round(success_rate, 2)
        
        return summary