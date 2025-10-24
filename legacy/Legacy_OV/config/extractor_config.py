#!/usr/bin/env python3
"""
Sistema de Configuración Centralizada Avanzado - ExtractorOV
==========================================================

Sistema avanzado de configuración centralizada que proporciona:
- Configuración por ambiente (dev, test, prod)
- Validación automática de configuraciones
- Carga dinámica desde múltiples fuentes
- Configuración específica por empresa y plataforma
- Sistema de overrides y fallbacks
- Configuración de secretos y credenciales
- Validación de esquemas
- Cache de configuraciones

Autor: ExtractorOV Team
Fecha: 2025-09-26
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class Environment(Enum):
    """Ambientes soportados"""
    DEVELOPMENT = "dev"
    TESTING = "test"
    PRODUCTION = "prod"

class Platform(Enum):
    """Plataformas soportadas"""
    OFICINA_VIRTUAL = "oficina_virtual"

class Company(Enum):
    """Empresas soportadas"""
    AFINIA = "afinia"
    AIRE = "aire"

@dataclass
class TimeoutConfig:
    """Configuración de timeouts"""
    navigation: int = 30000
    login: int = 45000
    download: int = 60000
    element_wait: int = 15000
    page_load: int = 45000

@dataclass
class BrowserConfig:
    """Configuración del navegador optimizada para mejor visualización"""
    headless: bool = True
    viewport_width: int = 1920  # Viewport más grande para ver contenido completo
    viewport_height: int = 1080
    device_scale_factor: float = 0.8  # Factor de escala optimizado
    args: List[str] = None

    def __post_init__(self):
        if self.args is None:
            self.args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--start-maximized",
                "--window-size=1920,1080",  # Tamaño de ventana específico
                "--force-device-scale-factor=0.8",  # Zoom optimizado para ver más contenido
                "--disable-features=TranslateUI",
                "--enable-automation",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ]

@dataclass
class ReportConfig:
    """Configuración de un reporte específico"""
    name: str
    url_suffix: str
    download_selector: str
    enabled: bool = True
    timeout: int = 60000

@dataclass
class ExtractorConfig:
    """Configuración completa de un extractor"""
    # Información básica
    company: str
    platform: str
    url: str
    username: str
    password: str

    # Configuraciones específicas
    timeouts: TimeoutConfig
    browser: BrowserConfig
    reports: Dict[str, ReportConfig]

    # Configuraciones opcionales
    selectors: Dict[str, Any] = None
    options: Dict[str, Any] = None
    enabled: bool = True

class ConfigurationManager:
    """
    Gestor centralizado de configuraciones para ExtractorOV

    Proporciona configuración centralizada con soporte para:
    - Múltiples ambientes
    - Validación automática
    - Carga desde archivos y variables de entorno
    - Sistema de cache
    """

    def __init__(self, environment: str = None):
        """
        Inicializa el gestor de configuración

        Args:
            environment: Ambiente a usar (dev, test, prod)
        """
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.env_dir = self.project_root / "config" / "env"

        # Determinar ambiente
        self.environment = self._determine_environment(environment)

        # Cache de configuraciones
        self._config_cache: Dict[str, ExtractorConfig] = {}

        # Cargar variables de entorno
        self._load_environment_variables()

        logger.info(f"ConfigurationManager inicializado - Ambiente: {self.environment.value}")

    def _determine_environment(self, env: str = None) -> Environment:
        """Determina el ambiente a usar"""
        if env:
            try:
                return Environment(env.lower())
            except ValueError:
                pass

        # Desde variable de entorno
        env_var = os.getenv('EXTRACTOR_ENV', 'dev').lower()
        try:
            return Environment(env_var)
        except ValueError:
            logger.warning(f"Ambiente desconocido '{env_var}', usando 'dev'")
            return Environment.DEVELOPMENT

    def _load_environment_variables(self):
        """Carga variables de entorno según el ambiente"""
        env_files = [
            self.env_dir / ".env",
            self.env_dir / f".env.{self.environment.value}",
        ]

        for env_file in env_files:
            if env_file.exists():
                load_dotenv(dotenv_path=str(env_file), override=True)
                logger.info(f"Variables de entorno cargadas desde: {env_file}")

    def get_extractor_config(self, company: str, platform: str) -> Optional[ExtractorConfig]:
        """
        Obtiene la configuración para un extractor específico

        Args:
            company: Nombre de la empresa
            platform: Nombre de la plataforma

        Returns:
            Configuración del extractor o None si no se encuentra
        """
        cache_key = f"{company}_{platform}"

        # Verificar cache
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]

        # Cargar configuración
        config = self._load_extractor_config(company, platform)

        if config:
            # Validar configuración
            if self._validate_config(config):
                # Guardar en cache
                self._config_cache[cache_key] = config
                return config
            else:
                logger.error(f"Configuración inválida para {company}/{platform}")
                return None

        logger.warning(f"No se encontró configuración para {company}/{platform}")
        return None

    def _load_extractor_config(self, company: str, platform: str) -> Optional[ExtractorConfig]:
        """Carga la configuración desde múltiples fuentes"""

        # 1. Intentar cargar desde archivo YAML específico
        config_file = self.config_dir / "companies" / f"{company}_{platform}.yaml"
        if config_file.exists():
            config = self._load_from_yaml(config_file)
            if config:
                return config

        # 2. Cargar desde configuración legacy (config.py)
        return self._load_from_legacy_config(company, platform)

    def _load_from_yaml(self, config_file: Path) -> Optional[ExtractorConfig]:
        """Carga configuración desde archivo YAML"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            return self._dict_to_extractor_config(data)

        except Exception as e:
            logger.error(f"Error cargando {config_file}: {e}")
            return None

    def _load_from_legacy_config(self, company: str, platform: str) -> Optional[ExtractorConfig]:
        """Carga configuración desde el sistema legacy"""
        try:
            # Importar el sistema legacy
from src.config.config import get_extractor_config

            legacy_config = get_extractor_config(company, platform)
            if legacy_config:
                return self._dict_to_extractor_config(legacy_config)

        except Exception as e:
            logger.error(f"Error cargando configuración legacy: {e}")

        return None

    def _dict_to_extractor_config(self, data: Dict[str, Any]) -> ExtractorConfig:
        """Convierte un diccionario a ExtractorConfig"""

        # Procesar timeouts
        timeouts_data = data.get('timeouts', {})
        timeouts = TimeoutConfig(**timeouts_data)

        # Procesar configuración de navegador
        browser_data = data.get('browser', {})
        browser = BrowserConfig(**browser_data)

        # Procesar reportes
        reports_data = data.get('reports', {})
        reports = {}
        for key, report_data in reports_data.items():
            reports[key] = ReportConfig(**report_data)

        # Crear configuración completa
        config = ExtractorConfig(
            company=data.get('company_name', data.get('company', '')),
            platform=data.get('platform', ''),
            url=data.get('url', ''),
            username=data.get('username', ''),
            password=data.get('password', ''),
            timeouts=timeouts,
            browser=browser,
            reports=reports,
            selectors=data.get('selectors'),
            options=data.get('options'),
            enabled=data.get('enabled', True)
        )

        return config

    def _validate_config(self, config: ExtractorConfig) -> bool:
        """Valida una configuración"""
        required_fields = ['company', 'platform', 'url', 'username', 'password']

        for field in required_fields:
            if not getattr(config, field):
                logger.error(f"Campo requerido faltante: {field}")
                return False

        # Validar que hay al menos un reporte configurado
        if not config.reports:
            logger.error("No hay reportes configurados")
            return False

        logger.info(f"Configuración válida para {config.company}/{config.platform}")
        return True

    def save_config(self, company: str, platform: str, config: ExtractorConfig):
        """
        Guarda una configuración en archivo YAML

        Args:
            company: Nombre de la empresa
            platform: Nombre de la plataforma 
            config: Configuración a guardar
        """
        companies_dir = self.config_dir / "companies"
        companies_dir.mkdir(exist_ok=True)

        config_file = companies_dir / f"{company}_{platform}.yaml"

        # Convertir a diccionario
        config_dict = asdict(config)

        # Guardar en YAML
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Configuración guardada en {config_file}")

        # Actualizar cache
        cache_key = f"{company}_{platform}"
        self._config_cache[cache_key] = config

    def list_available_configs(self) -> List[Dict[str, str]]:
        """Lista todas las configuraciones disponibles"""
        configs = []

        # Desde archivos YAML
        companies_dir = self.config_dir / "companies"
        if companies_dir.exists():
            for yaml_file in companies_dir.glob("*.yaml"):
                parts = yaml_file.stem.split("_", 1)
                if len(parts) == 2:
                    company, platform = parts
                    configs.append({
                        'company': company,
                        'platform': platform,
                        'source': 'yaml',
                        'file': str(yaml_file)
                    })

        # Desde configuración legacy
        legacy_combinations = [
            ('afinia', 'oficina_virtual'),
            ('aire', 'oficina_virtual')
        ]

        for company, platform in legacy_combinations:
            # Solo agregar si no existe ya desde YAML
            if not any(c['company'] == company and c['platform'] == platform 
                      for c in configs):
                configs.append({
                    'company': company,
                    'platform': platform,
                    'source': 'legacy',
                    'file': 'config/config.py'
                })

        return configs

    def get_global_config(self) -> Dict[str, Any]:
        """Obtiene configuración global del sistema"""
        return {
            'environment': self.environment.value,
            'project_root': str(self.project_root),
            'config_dir': str(self.config_dir),
            'env_dir': str(self.env_dir),
            'available_configs': len(self.list_available_configs()),
            'cache_size': len(self._config_cache)
        }

# Instancia global del gestor de configuración
_config_manager: Optional[ConfigurationManager] = None

def get_config_manager(environment: str = None) -> ConfigurationManager:
    """
    Obtiene la instancia global del gestor de configuración

    Args:
        environment: Ambiente a usar (solo en la primera llamada)

    Returns:
        ConfigurationManager: Instancia del gestor
    """
    global _config_manager

    if _config_manager is None:
        _config_manager = ConfigurationManager(environment)

    return _config_manager

def get_extractor_config(company: str, platform: str) -> Optional[ExtractorConfig]:
    """
    Función de conveniencia para obtener configuración de extractor

    Args:
        company: Nombre de la empresa
        platform: Nombre de la plataforma

    Returns:
        Configuración del extractor o None
    """
    manager = get_config_manager()
    return manager.get_extractor_config(company, platform)

if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Sistema de Configuración Centralizada ===")

    manager = get_config_manager()
    print(f"Configuración global: {manager.get_global_config()}")

    print("\nConfiguraciones disponibles:")
    for config in manager.list_available_configs():
        print(f" - {config['company']}/{config['platform']} ({config['source']})")

    print("\nProbando carga de configuraciones:")
    test_cases = [
        ('aire', 'oficina_virtual'),
        ('afinia', 'oficina_virtual')
    ]

    for company, platform in test_cases:
        config = manager.get_extractor_config(company, platform)
        if config:
            print(f" [EMOJI_REMOVIDO] {company}/{platform}: {len(config.reports)} reportes configurados")
        else:
            print(f" [ERROR] {company}/{platform}: No disponible")
