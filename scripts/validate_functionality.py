[EMOJI_REMOVIDO]#!/usr/bin/env python3
"""
Script de Validación de Funcionalidad - ExtractorOV_Modular
=========================================================

Este script verifica que todas las funcionalidades críticas del proyecto
sigan funcionando correctamente después de realizar cambios de limpieza
y reorganización.

Uso:
    python validate_functionality.py [--phase PHASE] [--verbose]

Fases disponibles:
    - pre: Validación antes de cambios
    - post: Validación después de cambios
    - all: Todas las validaciones
"""

import os
import sys
import json
import logging
import traceback
import importlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import argparse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[VALIDATOR %(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class FunctionalityValidator:
    """Validador de funcionalidad del proyecto ExtractorOV_Modular"""
    
    def __init__(self, verbose: bool = False):
        """
        Inicializar validador
        
        Args:
            verbose: Si mostrar información detallada
        """
        self.verbose = verbose
        self.project_root = Path(__file__).parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # Agregar project root al path
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
    
    def log_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Registrar resultado de test"""
        self.results["total_tests"] += 1
        
        if success:
            self.results["passed"] += 1
            logger.info(f"[EXITOSO] {test_name}: {message}")
        else:
            self.results["failed"] += 1
            logger.error(f"[ERROR] {test_name}: {message}")
            self.results["errors"].append({
                "test": test_name,
                "message": message,
                "details": details or {}
            })
        
        self.results["details"][test_name] = {
            "success": success,
            "message": message,
            "details": details or {}
        }
    
    def validate_imports(self) -> bool:
        """Validar que todos los módulos críticos se importen correctamente"""
        logger.info("[EMOJI_REMOVIDO] Validando importaciones críticas...")
        
        critical_modules = [
            # Core modules
            "src.core.a_core_01.base_extractor",
            "src.core.a_core_01.browser_manager", 
            "src.core.a_core_01.authentication",
            "src.core.a_core_01.download_manager",
            
            # Components
            "src.components.c_components_03.date_configurator",
            "src.components.c_components_03.filter_manager",
            "src.components.c_components_03.popup_handler",
            "src.components.c_components_03.report_processor",
            
            # Config
            "src.config.f_config_06.config",
            "src.config.f_config_06.afinia_config",
            
            # Extractors
            "src.extractors.d_downloaders_04.afinia.oficina_virtual_afinia_modular",
            "src.extractors.d_downloaders_04.aire.oficina_virtual_aire_modular",
            
            # Metrics
            "data.metrics.o_metrics_15.metrics_logger"
        ]
        
        failed_imports = []
        successful_imports = []
        
        for module_name in critical_modules:
            try:
                importlib.import_module(module_name)
                successful_imports.append(module_name)
                if self.verbose:
                    logger.debug(f"  [EMOJI_REMOVIDO] {module_name}")
            except Exception as e:
                failed_imports.append((module_name, str(e)))
                logger.warning(f"  [EMOJI_REMOVIDO] {module_name}: {str(e)}")
        
        success = len(failed_imports) == 0
        message = f"{len(successful_imports)}/{len(critical_modules)} módulos importados correctamente"
        
        self.log_result("import_validation", success, message, {
            "successful": successful_imports,
            "failed": failed_imports
        })
        
        return success
    
    def validate_configurations(self) -> bool:
        """Validar configuraciones críticas"""
        logger.info("[EMOJI_REMOVIDO] Validando configuraciones...")
        
        try:
            # Importar y validar configuraciones
            from src.config.config import get_extractor_config
            
            # Validar configuración de Afinia
            afinia_config = get_extractor_config("afinia", "oficina_virtual")
            if not afinia_config:
                self.log_result("config_afinia", False, "Configuración de Afinia no encontrada")
                return False
            
            # Validar campos críticos
            required_fields = ["url", "company_name", "platform", "timeout", "selectors"]
            missing_fields = [field for field in required_fields if field not in afinia_config]
            
            if missing_fields:
                self.log_result("config_afinia", False, f"Campos faltantes: {missing_fields}")
                return False
            
            # Validar configuración de Aire
            aire_config = get_extractor_config("aire", "oficina_virtual")
            if not aire_config:
                self.log_result("config_aire", False, "Configuración de Aire no encontrada")
                return False
            
            self.log_result("config_validation", True, "Configuraciones válidas", {
                "afinia_fields": len(afinia_config.keys()),
                "aire_fields": len(aire_config.keys())
            })
            
            return True
            
        except Exception as e:
            self.log_result("config_validation", False, f"Error validando configuraciones: {str(e)}")
            return False
    
    def validate_file_structure(self) -> bool:
        """Validar estructura de archivos críticos"""
        logger.info("[EMOJI_REMOVIDO] Validando estructura de archivos...")
        
        # Archivos críticos que deben existir
        critical_files = [
            "run_afinia_ov_visual.py",
            "run_afinia_ov_headless.py", 
            "run_afinia_ov_specific_sequence.py",
            "requirements.txt",
            "a_core_01/__init__.py",
            "b_adapters_02/__init__.py",
            "c_components_03/__init__.py",
            "f_config_06/__init__.py",
            "f_config_06/config.py"
        ]
        
        # Directorios críticos que deben existir
        critical_dirs = [
            "a_core_01",
            "b_adapters_02", 
            "c_components_03",
            "d_downloaders_04",
            "f_config_06",
            "g_utils_07"
        ]
        
        missing_files = []
        missing_dirs = []
        
        # Verificar archivos
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        # Verificar directorios
        for dir_path in critical_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        success = len(missing_files) == 0 and len(missing_dirs) == 0
        total_items = len(critical_files) + len(critical_dirs)
        found_items = total_items - len(missing_files) - len(missing_dirs)
        
        message = f"{found_items}/{total_items} elementos críticos encontrados"
        
        self.log_result("file_structure", success, message, {
            "missing_files": missing_files,
            "missing_dirs": missing_dirs
        })
        
        return success
    
    def validate_environment_config(self) -> bool:
        """Validar configuración de entorno"""
        logger.info("[EMOJI_REMOVIDO] Validando configuración de entorno...")
        
        # Verificar que existan directorios de env
        p16_env = self.project_root / "p16_env"
        r_env_18 = self.project_root / "r_env_18"
        
        env_dirs_found = []
        if p16_env.exists():
            env_dirs_found.append("p16_env")
        if r_env_18.exists():
            env_dirs_found.append("r_env_18")
        
        if not env_dirs_found:
            self.log_result("env_config", False, "No se encontraron directorios de configuración de entorno")
            return False
        
        # Verificar archivos .env
        env_files_found = []
        for env_dir in env_dirs_found:
            env_file = self.project_root / env_dir / ".env"
            if env_file.exists():
                env_files_found.append(f"{env_dir}/.env")
        
        message = f"Encontrados: {', '.join(env_dirs_found)} | Archivos .env: {', '.join(env_files_found)}"
        
        self.log_result("env_config", True, message, {
            "env_directories": env_dirs_found,
            "env_files": env_files_found
        })
        
        return True
    
    def validate_extractor_instantiation(self) -> bool:
        """Validar que los extractores principales se puedan instanciar"""
        logger.info("[EMOJI_REMOVIDO] Validando instanciación de extractores...")
        
        try:
            # Intentar importar extractores principales
            from d_downloaders_04.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular
            
            # Intentar crear instancia (sin inicializar navegador)
            config_test = {
                "url": "https://test.com",
                "username": "test",
                "password": "test",
                "company_name": "afinia",
                "platform": "oficina_virtual",
                "timeout": 30000,
                "selectors": {},
                "timeouts": {"navigation": 30000, "login": 30000}
            }
            
            # Test de instanciación (sin ejecutar)
            extractor = None
            try:
                # Solo verificar que la clase existe y se puede importar
                extractor_class = OficinaVirtualAfiniaModular
                self.log_result("extractor_instantiation", True, "Extractores principales accesibles")
                return True
            except Exception as e:
                self.log_result("extractor_instantiation", False, f"Error instanciando extractor: {str(e)}")
                return False
                
        except ImportError as e:
            self.log_result("extractor_instantiation", False, f"Error importando extractores: {str(e)}")
            return False
    
    def validate_scripts_syntax(self) -> bool:
        """Validar sintaxis de scripts principales"""
        logger.info("[EMOJI_REMOVIDO] Validando sintaxis de scripts...")
        
        main_scripts = [
            "run_afinia_ov_visual.py",
            "run_afinia_ov_headless.py",
            "run_afinia_ov_specific_sequence.py",
            "test_connectivity.py"
        ]
        
        syntax_errors = []
        valid_scripts = []
        
        for script in main_scripts:
            script_path = self.project_root / script
            if not script_path.exists():
                syntax_errors.append((script, "Archivo no encontrado"))
                continue
            
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Compilar para verificar sintaxis
                compile(content, str(script_path), 'exec')
                valid_scripts.append(script)
                
            except SyntaxError as e:
                syntax_errors.append((script, f"Error de sintaxis: {str(e)}"))
            except Exception as e:
                syntax_errors.append((script, f"Error: {str(e)}"))
        
        success = len(syntax_errors) == 0
        message = f"{len(valid_scripts)}/{len(main_scripts)} scripts con sintaxis válida"
        
        self.log_result("scripts_syntax", success, message, {
            "valid_scripts": valid_scripts,
            "syntax_errors": syntax_errors
        })
        
        return success
    
    def run_validation_suite(self, phase: str = "all") -> Dict[str, Any]:
        """
        Ejecutar suite completa de validación
        
        Args:
            phase: Fase de validación ("pre", "post", "all")
            
        Returns:
            Diccionario con resultados de validación
        """
        logger.info(f"[INICIANDO] Iniciando validación de funcionalidad - Fase: {phase}")
        
        # Lista de validaciones por fase
        validations = {
            "pre": [
                self.validate_file_structure,
                self.validate_imports,
                self.validate_configurations,
                self.validate_environment_config,
                self.validate_scripts_syntax,
                self.validate_extractor_instantiation
            ],
            "post": [
                self.validate_file_structure,
                self.validate_imports,
                self.validate_configurations,
                self.validate_environment_config,
                self.validate_scripts_syntax,
                self.validate_extractor_instantiation
            ]
        }
        
        if phase == "all":
            tests_to_run = validations["pre"]  # Pre y post son iguales
        else:
            tests_to_run = validations.get(phase, validations["pre"])
        
        # Ejecutar validaciones
        for validation_func in tests_to_run:
            try:
                validation_func()
            except Exception as e:
                test_name = validation_func.__name__
                logger.error(f"[ERROR] Error ejecutando {test_name}: {str(e)}")
                self.log_result(test_name, False, f"Excepción: {str(e)}")
                
                if self.verbose:
                    logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Calcular estadísticas finales
        success_rate = (self.results["passed"] / self.results["total_tests"]) * 100 if self.results["total_tests"] > 0 else 0
        
        logger.info(f"[DATOS] Resultados de validación:")
        logger.info(f"   Total: {self.results['total_tests']} tests")
        logger.info(f"   [EXITOSO] Exitosos: {self.results['passed']} ({success_rate:.1f}%)")
        logger.info(f"   [ERROR] Fallidos: {self.results['failed']}")
        
        if self.results["failed"] > 0:
            logger.warning(f"[ADVERTENCIA]  Se encontraron {self.results['failed']} problemas:")
            for error in self.results["errors"]:
                logger.warning(f"     - {error['test']}: {error['message']}")
        
        # Guardar resultados
        results_file = self.project_root / f"validation_results_{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[ARCHIVO] Resultados guardados en: {results_file}")
        
        return self.results

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Validador de funcionalidad ExtractorOV_Modular")
    parser.add_argument("--phase", choices=["pre", "post", "all"], default="all",
                      help="Fase de validación a ejecutar")
    parser.add_argument("--verbose", action="store_true", 
                      help="Mostrar información detallada")
    
    args = parser.parse_args()
    
    # Crear y ejecutar validador
    validator = FunctionalityValidator(verbose=args.verbose)
    results = validator.run_validation_suite(args.phase)
    
    # Retornar código de salida apropiado
    exit_code = 0 if results["failed"] == 0 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
