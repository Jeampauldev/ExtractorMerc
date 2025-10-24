#!/usr/bin/env python3
"""
Suite de Pruebas de Regresión para ExtractorOV_Modular
Valida que la funcionalidad existente no se rompa con los cambios propuestos
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.config.config import get_extractor_config, OficinaVirtualConfig


class TestConfigurationRegression(unittest.TestCase):
    """Pruebas de regresión para el sistema de configuración"""
    
    def test_afinia_config_structure_unchanged(self):
        """Verifica que la estructura de configuración de Afinia no haya cambiado"""
        config = get_extractor_config('afinia', 'oficina_virtual')
        
        # Verificar que la configuración existe
        self.assertIsNotNone(config, "Configuración de Afinia no encontrada")
        
        # Verificar claves principales que deben existir
        required_keys = [
            'url', 'username', 'password', 'selectors', 'timeouts'
        ]
        
        for key in required_keys:
            self.assertIn(key, config, f"Clave requerida '{key}' faltante en configuración de Afinia")
        
        # Verificar estructura de selectors
        self.assertIn('username', config['selectors'])
        self.assertIn('password', config['selectors'])
        self.assertIn('submit', config['selectors'])
        
        # Verificar estructura de timeouts
        timeout_keys = ['navigation', 'login', 'download']
        for key in timeout_keys:
            self.assertIn(key, config['timeouts'])
    
    def test_aire_config_structure_unchanged(self):
        """Verifica que la estructura de configuración de Aire no haya cambiado"""
        config = get_extractor_config('aire', 'oficina_virtual')
        
        # Verificar que la configuración existe
        self.assertIsNotNone(config, "Configuración de Aire no encontrada")
        
        # Verificar claves principales que deben existir
        required_keys = [
            'url', 'username', 'password', 'selectors', 'timeouts'
        ]
        
        for key in required_keys:
            self.assertIn(key, config, f"Clave requerida '{key}' faltante en configuración de Aire")
        
        # Verificar estructura de selectors
        self.assertIn('username', config['selectors'])
        self.assertIn('password', config['selectors'])
        self.assertIn('submit', config['selectors'])
        
        # Verificar estructura de timeouts
        timeout_keys = ['navigation', 'login', 'download']
        for key in timeout_keys:
            self.assertIn(key, config['timeouts'])
    
    def test_default_configs_integrity(self):
        """Verifica que las configuraciones por defecto mantengan su integridad"""
        # Verificar que existen las configuraciones esperadas
        expected_configs = ['afinia', 'aire']
        
        for config_name in expected_configs:
            config = get_extractor_config(config_name, 'oficina_virtual')
            self.assertIsNotNone(config, f"Configuración '{config_name}' no encontrada")
            
            # Verificar estructura básica de cada configuración
            self.assertIsInstance(config, dict, 
                                f"Configuración '{config_name}' debe ser un diccionario")
            self.assertIn('url', config, 
                         f"URL faltante en configuración '{config_name}'")
            self.assertIn('username', config, 
                         f"Username faltante en configuración '{config_name}'")
            self.assertIn('password', config, 
                         f"Password faltante en configuración '{config_name}'")


class TestManagersRegression(unittest.TestCase):
    """Pruebas de regresión para los managers existentes"""
    
    @patch('afinia_manager.get_afinia_config')
    @patch('afinia_manager.run_extractor')
    def test_afinia_manager_main_function_unchanged(self, mock_run_extractor, mock_get_config):
        """Verifica que la función main de afinia_manager funcione como antes"""
        # Configurar mocks
        mock_config = {'url': 'test', 'username': 'test', 'password': 'test'}
        mock_get_config.return_value = mock_config
        
        # Importar y ejecutar
        import afinia_manager
        
        # Ejecutar main
        afinia_manager.main()
        
        # Verificar que se llaman las funciones esperadas
        mock_get_config.assert_called_once_with('afinia', 'oficina_virtual')
        mock_run_extractor.assert_called_once()
        
        # Verificar argumentos de run_extractor
        call_args = mock_run_extractor.call_args
        self.assertEqual(call_args[1]['extractor_name'], "Afinia")
        self.assertEqual(call_args[1]['config'], mock_config)
    
    @patch('afinia_manager.get_afinia_config')
    @patch('afinia_manager.run_extractor')
    def test_afinia_integration_flow_unchanged(self, mock_run_extractor, mock_get_config):
        """Verifica que el flujo completo de integración de Afinia funcione"""
        # Configurar mocks
        mock_config = {
            'url': 'test_url',
            'username': 'test_user',
            'password': 'test_pass',
            'selectors': {'username': '#user', 'password': '#pass'},
            'timeouts': {'navigation': 30}
        }
        mock_get_config.return_value = mock_config
        
        # Importar y ejecutar función principal
        import afinia_manager
        
        # Ejecutar función
        afinia_manager.main()
        
        # Verificar que se ejecuta sin errores
        mock_get_config.assert_called_once()
        mock_run_extractor.assert_called_once()
    
    @patch('src.config.config.get_extractor_config')
    @patch('aire_manager.run_extractor')
    def test_aire_manager_main_function_unchanged(self, mock_run_extractor, mock_get_config):
        """Verifica que la función main de aire_manager funcione como antes"""
        # Configurar mocks
        mock_config = {'url': 'test', 'username': 'test', 'password': 'test'}
        mock_get_config.return_value = mock_config
        
        # Importar y ejecutar
        import aire_manager
        aire_manager.main()
        
        # Verificar que se llamaron las funciones correctas
        mock_get_config.assert_called_once()
        mock_run_extractor.assert_called_once()
        
        # Verificar argumentos de run_extractor
        call_args = mock_run_extractor.call_args
        self.assertEqual(call_args[1]['extractor_name'], "Aire")
        self.assertEqual(call_args[1]['config'], mock_config)
    
    @patch('src.config.config.get_extractor_config')
    @patch('aire_manager.run_extractor')
    def test_aire_integration_flow_unchanged(self, mock_run_extractor, mock_get_config):
        """Verifica que el flujo completo de integración de Aire funcione"""
        # Configurar mocks
        mock_config = {
            'url': 'test_url',
            'username': 'test_user',
            'password': 'test_pass',
            'selectors': {'username': '#user', 'password': '#pass'},
            'timeouts': {'navigation': 30}
        }
        mock_get_config.return_value = mock_config
        
        # Verificar que se ejecuta sin errores
        mock_get_config.assert_called_once_with('aire', 'oficina_virtual')
        mock_run_extractor.assert_called_once()
    

class TestExtractorClassesRegression(unittest.TestCase):
    """Pruebas de regresión para las clases de extractores"""
    
    @patch('src.config.afinia_config.get_afinia_config')
    @patch('afinia_manager.OficinaVirtualAfiniaModular')
    @patch('afinia_manager.BrowserManager')
    @patch('afinia_manager.AuthenticationManager')
    def test_afinia_extractor_initialization_unchanged(self, mock_auth, mock_browser, mock_extractor, mock_get_config):
        """Verifica que la inicialización del extractor de Afinia no haya cambiado"""
        # Configurar mocks
        mock_config = {
            'url': 'test_url',
            'username': 'test_user',
            'password': 'test_pass',
            'selectors': {'username': '#user', 'password': '#pass'},
            'timeouts': {'navigation': 30}
        }
        mock_get_config.return_value = mock_config
        
        # Importar función
        from src.managers.afinia_manager import run_afinia_extraction
        
        # Ejecutar función
        mock_logger = MagicMock()
        run_afinia_extraction(mock_config, mock_logger)
        
        # Verificar inicialización de componentes
        mock_browser.assert_called_once()
        mock_auth.assert_called_once()
        mock_extractor.assert_called_once()
    
    @patch('src.config.config.get_extractor_config')
    @patch('aire_manager.OficinaVirtualAireModular')
    @patch('aire_manager.BrowserManager')
    @patch('aire_manager.AuthenticationManager')
    def test_aire_extractor_initialization_unchanged(self, mock_auth, mock_browser, mock_extractor, mock_get_config):
        """Verifica que la inicialización del extractor de Aire no haya cambiado"""
        # Configurar mocks
        mock_config = {
            'url': 'test_url',
            'username': 'test_user',
            'password': 'test_pass',
            'selectors': {'username': '#user', 'password': '#pass'},
            'timeouts': {'navigation': 30}
        }
        mock_get_config.return_value = mock_config
        
        # Importar función
        from aire_manager import main_aire_extraction
        
        # Ejecutar función
        mock_logger = MagicMock()
        main_aire_extraction(mock_config, mock_logger)
        
        # Verificar inicialización de componentes
        mock_browser.assert_called_once()
        mock_auth.assert_called_once()
        mock_extractor.assert_called_once()


class TestCoreComponentsRegression(unittest.TestCase):
    """Pruebas de regresión para componentes del core (sin modificar)"""
    
    def test_core_imports_still_work(self):
        """Verifica que las importaciones del core sigan funcionando"""
        try:
            from src.core.browser_manager import BrowserManager
            from src.core.auth_manager import AuthenticationManager
            from src.core.download_manager import DownloadManager
            from src.config.unified_logging_config import UnifiedLogger
        except ImportError as e:
            self.fail(f"Error al importar componentes del core: {e}")
    
    def test_browser_manager_interface_unchanged(self):
        """Verifica que la interfaz de BrowserManager no haya cambiado"""
        from src.core.browser_manager import BrowserManager
        
        # Verificar que la clase existe y tiene los métodos esperados
        expected_methods = ['__init__', 'get_driver', 'close', 'navigate_to']
        
        for method in expected_methods:
            self.assertTrue(hasattr(BrowserManager, method), 
                           f"Método '{method}' faltante en BrowserManager")
    
    def test_auth_manager_interface_unchanged(self):
        """Verifica que la interfaz de AuthenticationManager no haya cambiado"""
        from src.core.auth_manager import AuthenticationManager
        
        # Verificar que la clase existe y tiene los métodos esperados
        expected_methods = ['__init__', 'login']
        
        for method in expected_methods:
            self.assertTrue(hasattr(AuthenticationManager, method), 
                           f"Método '{method}' faltante en AuthenticationManager")


class TestUtilsRegression(unittest.TestCase):
    """Pruebas de regresión para utilidades"""
    
    def test_extractor_runner_interface_unchanged(self):
        """Verifica que la interfaz de extractor_runner no haya cambiado"""
        from src.utils.extractor_runner import run_extractor, setup_argument_parser, initialize_logger
        
        # Verificar que las funciones existen
        self.assertTrue(callable(run_extractor))
        self.assertTrue(callable(setup_argument_parser))
        self.assertTrue(callable(initialize_logger))
    
    @patch('src.utils.extractor_runner.BrowserManager')
    @patch('src.utils.extractor_runner.AuthenticationManager')
    @patch('src.utils.extractor_runner.initialize_logger')
    @patch('sys.argv', ['test_script.py'])
    def test_extractor_runner_backward_compatibility(self, mock_init_logger, mock_auth_class, mock_browser_class):
        """Verifica compatibilidad hacia atrás del extractor_runner"""
        from src.utils.extractor_runner import run_extractor
        
        # Configurar mocks
        mock_logger = Mock()
        mock_init_logger.return_value = mock_logger
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        
        # Función de extractor simple
        def simple_extractor(browser_manager, auth_manager, logger):
            return "success"
        
        # Ejecutar con parámetros mínimos (como se usaba antes)
        run_extractor(
            extractor_name="Test",
            config={'url': 'test'},
            extractor_function=simple_extractor
        )
        
        # Verificar que funciona sin errores
        mock_browser_class.assert_called_once()
        mock_auth_class.assert_called_once()


class TestFileStructureRegression(unittest.TestCase):
    """Pruebas de regresión para la estructura de archivos"""
    
    def test_required_files_exist(self):
        """Verifica que todos los archivos requeridos existan"""
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
        required_files = [
            'src/config/config.py',
            'src/config/default_configs.py',
            'src/managers/afinia_manager.py',
            'src/managers/aire_manager.py',
            'src/utils/extractor_runner.py',
            'src/extractors/afinia/oficina_virtual_afinia_modular.py',
            'src/extractors/aire/oficina_virtual_aire_modular.py',
            'requirements.txt'
        ]
        
        for file_path in required_files:
            full_path = os.path.join(base_path, file_path)
            self.assertTrue(os.path.exists(full_path), 
                           f"Archivo requerido no encontrado: {file_path}")
    
    def test_core_directory_unchanged(self):
        """Verifica que el directorio core no haya sido modificado"""
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        core_path = os.path.join(base_path, 'src', 'core')
        
        # Verificar que el directorio core existe
        self.assertTrue(os.path.exists(core_path), "Directorio src/core no encontrado")
        
        # Verificar archivos esperados en core
        expected_core_files = [
            'browser_manager.py',
            'auth_manager.py',
            'download_manager.py',
            'logger.py'
        ]
        
        for file_name in expected_core_files:
            file_path = os.path.join(core_path, file_name)
            self.assertTrue(os.path.exists(file_path), 
                           f"Archivo del core no encontrado: {file_name}")


class TestIntegrationRegression(unittest.TestCase):
    """Pruebas de regresión de integración end-to-end"""
    
    @patch('src.core.browser_manager.BrowserManager')
    @patch('src.core.auth_manager.AuthenticationManager')
    @patch('src.config.unified_logging_config.UnifiedLogger')
    def test_full_afinia_flow_regression(self, mock_logger_class, mock_auth_class, mock_browser_class):
        """Prueba de regresión del flujo completo de Afinia"""
        # Configurar mocks
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth.login.return_value = True
        mock_auth_class.return_value = mock_auth
        
        # Importar y ejecutar función de extracción
        from afinia_manager import run_afinia_extraction
        
        # Ejecutar función
        result = run_afinia_extraction(mock_browser, mock_auth, mock_logger)
        
        # Verificar que se ejecuta sin errores
        self.assertIsNotNone(result)
        mock_auth.login.assert_called_once()
    
    @patch('src.core.browser_manager.BrowserManager')
    @patch('src.core.auth_manager.AuthenticationManager')
    @patch('src.config.unified_logging_config.UnifiedLogger')
    def test_full_aire_flow_regression(self, mock_logger_class, mock_auth_class, mock_browser_class):
        """Prueba de regresión del flujo completo de Aire"""
        # Configurar mocks
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        
        # Importar y ejecutar función de extracción
        from src.managers.aire_manager import run_aire_extraction
        
        # Ejecutar función
        result = run_aire_extraction(mock_browser, mock_auth, mock_logger)
        
        # Verificar que se ejecuta sin errores
        self.assertIsNotNone(result)


if __name__ == '__main__':
    # Configurar el runner de pruebas con mayor verbosidad
    unittest.main(verbosity=2, buffer=True)