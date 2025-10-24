#!/usr/bin/env python3
"""
Pruebas de integración para extractor_runner.py
Valida que el runner común funcione correctamente para ambos extractores
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import argparse

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.utils.extractor_runner import (
    setup_argument_parser, 
    initialize_logger, 
    run_extractor
)


class TestExtractorRunnerComponents(unittest.TestCase):
    """Pruebas unitarias para componentes individuales del extractor runner"""
    
    def test_setup_argument_parser(self):
        """Prueba la configuración del parser de argumentos"""
        parser = setup_argument_parser("TestExtractor")
        
        # Verificar que es un ArgumentParser
        self.assertIsInstance(parser, argparse.ArgumentParser)
        
        # Verificar que tiene los argumentos esperados
        # Parsear argumentos de prueba
        args = parser.parse_args(['--headless', '--debug'])
        self.assertTrue(args.headless)
        self.assertTrue(args.debug)
        
        # Parsear sin argumentos
        args_empty = parser.parse_args([])
        self.assertFalse(args_empty.headless)
        self.assertFalse(args_empty.debug)
    
    @patch('src.utils.extractor_runner.UnifiedLogger')
    def test_initialize_logger(self, mock_logger_class):
        """Prueba la inicialización del logger"""
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        
        # Probar sin debug
        logger = initialize_logger("TestExtractor", debug=False)
        
        mock_logger_class.assert_called_once_with(
            service_name="testextractor",
            enable_console=True,
            enable_file=True,
            log_level='INFO'
        )
        self.assertEqual(logger, mock_logger)
        
        # Resetear mock y probar con debug
        mock_logger_class.reset_mock()
        logger_debug = initialize_logger("TestExtractor", debug=True)
        
        mock_logger_class.assert_called_once_with(
            service_name="testextractor",
            enable_console=True,
            enable_file=True,
            log_level='DEBUG'
        )


class TestExtractorRunnerIntegration(unittest.TestCase):
    """Pruebas de integración para el runner completo"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.mock_config = {
            'url': 'https://test.com',
            'credentials': {'username': 'test', 'password': 'test'},
            'timeouts': {'navigation': 30}
        }
        
        self.mock_extractor_function = Mock()
    
    @patch('src.utils.extractor_runner.BrowserManager')
    @patch('src.utils.extractor_runner.AuthenticationManager')
    @patch('src.utils.extractor_runner.initialize_logger')
    @patch('sys.argv', ['test_script.py', '--headless'])
    def test_run_extractor_exitoso(self, mock_init_logger, mock_auth_class, mock_browser_class):
        """Prueba ejecución exitosa del extractor"""
        # Configurar mocks
        mock_logger = Mock()
        mock_init_logger.return_value = mock_logger
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        
        # Ejecutar función
        run_extractor(
            extractor_name="TestExtractor",
            config=self.mock_config,
            extractor_function=self.mock_extractor_function
        )
        
        # Verificar inicialización de componentes
        mock_browser_class.assert_called_once_with(
            headless=True,
            config=self.mock_config
        )
        mock_auth_class.assert_called_once_with(
            browser_manager=mock_browser,
            config=self.mock_config,
            logger=mock_logger
        )
        
        # Verificar que se ejecuta la función del extractor
        self.mock_extractor_function.assert_called_once_with(
            mock_browser, mock_auth, mock_logger
        )
        
        # Verificar logs
        mock_logger.info.assert_any_call("=== Iniciando Extractor TestExtractor ===")
        mock_logger.info.assert_any_call("Modo headless: True")
        mock_logger.info.assert_any_call("=== Extractor TestExtractor completado exitosamente ===")
        
        # Verificar cierre del navegador
        mock_browser.close.assert_called_once()
    
    @patch('src.utils.extractor_runner.BrowserManager')
    @patch('src.utils.extractor_runner.AuthenticationManager')
    @patch('src.utils.extractor_runner.initialize_logger')
    @patch('sys.argv', ['test_script.py'])
    def test_run_extractor_error_en_funcion(self, mock_init_logger, mock_auth_class, mock_browser_class):
        """Prueba manejo de errores en la función del extractor"""
        # Configurar mocks
        mock_logger = Mock()
        mock_init_logger.return_value = mock_logger
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        
        # Configurar función para que falle
        self.mock_extractor_function.side_effect = Exception("Error en extractor")
        
        # Verificar que se maneja la excepción
        with patch('sys.exit') as mock_exit:
            run_extractor(
                extractor_name="TestExtractor",
                config=self.mock_config,
                extractor_function=self.mock_extractor_function
            )
            
            # Verificar que se registra el error y se sale
            mock_logger.error.assert_called_with("Error en extractor TestExtractor: Error en extractor")
            mock_logger.exception.assert_called_with("Detalles del error:")
            mock_exit.assert_called_with(1)
        
        # Verificar que se cierra el navegador incluso con error
        mock_browser.close.assert_called_once()
    
    @patch('src.utils.extractor_runner.BrowserManager')
    @patch('src.utils.extractor_runner.AuthenticationManager')
    @patch('src.utils.extractor_runner.initialize_logger')
    @patch('sys.argv', ['test_script.py'])
    def test_run_extractor_keyboard_interrupt(self, mock_init_logger, mock_auth_class, mock_browser_class):
        """Prueba manejo de interrupción por teclado"""
        # Configurar mocks
        mock_logger = Mock()
        mock_init_logger.return_value = mock_logger
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        
        # Configurar función para simular interrupción
        self.mock_extractor_function.side_effect = KeyboardInterrupt()
        
        # Verificar que se maneja la interrupción
        with patch('sys.exit') as mock_exit:
            run_extractor(
                extractor_name="TestExtractor",
                config=self.mock_config,
                extractor_function=self.mock_extractor_function
            )
            
            # Verificar que se registra la interrupción y se sale
            mock_logger.warning.assert_called_with("Extractor TestExtractor interrumpido por el usuario")
            mock_exit.assert_called_with(1)
        
        # Verificar que se cierra el navegador
        mock_browser.close.assert_called_once()
    
    @patch('src.utils.extractor_runner.BrowserManager')
    @patch('src.utils.extractor_runner.AuthenticationManager')
    @patch('src.utils.extractor_runner.initialize_logger')
    @patch('sys.argv', ['test_script.py', '--debug'])
    def test_run_extractor_modo_debug(self, mock_init_logger, mock_auth_class, mock_browser_class):
        """Prueba ejecución en modo debug"""
        # Configurar mocks
        mock_logger = Mock()
        mock_init_logger.return_value = mock_logger
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        
        # Ejecutar función
        run_extractor(
            extractor_name="TestExtractor",
            config=self.mock_config,
            extractor_function=self.mock_extractor_function
        )
        
        # Verificar que se inicializa el logger con debug
        mock_init_logger.assert_called_once_with("TestExtractor", True)
        
        # Verificar logs de debug
        mock_logger.info.assert_any_call("Modo debug: True")
    
    @patch('src.utils.extractor_runner.BrowserManager')
    @patch('src.utils.extractor_runner.AuthenticationManager')
    @patch('src.utils.extractor_runner.initialize_logger')
    @patch('sys.argv', ['test_script.py'])
    def test_run_extractor_error_cierre_navegador(self, mock_init_logger, mock_auth_class, mock_browser_class):
        """Prueba manejo de errores al cerrar el navegador"""
        # Configurar mocks
        mock_logger = Mock()
        mock_init_logger.return_value = mock_logger
        mock_browser = Mock()
        mock_browser.close.side_effect = Exception("Error al cerrar")
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        
        # Ejecutar función
        run_extractor(
            extractor_name="TestExtractor",
            config=self.mock_config,
            extractor_function=self.mock_extractor_function
        )
        
        # Verificar que se registra el error de cierre
        mock_logger.error.assert_any_call("Error al cerrar navegador: Error al cerrar")
    
    @patch('src.utils.extractor_runner.BrowserManager')
    @patch('src.utils.extractor_runner.AuthenticationManager')
    @patch('src.utils.extractor_runner.initialize_logger')
    @patch('sys.argv', ['test_script.py'])
    def test_run_extractor_con_custom_args_handler(self, mock_init_logger, mock_auth_class, mock_browser_class):
        """Prueba ejecución con manejador de argumentos personalizado"""
        # Configurar mocks
        mock_logger = Mock()
        mock_init_logger.return_value = mock_logger
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        
        # Mock del manejador personalizado
        custom_handler = Mock()
        
        # Ejecutar función
        run_extractor(
            extractor_name="TestExtractor",
            config=self.mock_config,
            extractor_function=self.mock_extractor_function,
            custom_args_handler=custom_handler
        )
        
        # Verificar que se llama el manejador personalizado
        custom_handler.assert_called_once()


class TestExtractorRunnerCompatibility(unittest.TestCase):
    """Pruebas de compatibilidad con los managers existentes"""
    
    @patch('src.utils.extractor_runner.BrowserManager')
    @patch('src.utils.extractor_runner.AuthenticationManager')
    @patch('src.utils.extractor_runner.initialize_logger')
    @patch('sys.argv', ['test_script.py'])
    def test_compatibilidad_con_afinia_manager(self, mock_init_logger, mock_auth_class, mock_browser_class):
        """Prueba compatibilidad con el patrón de afinia_manager"""
        # Configurar mocks
        mock_logger = Mock()
        mock_init_logger.return_value = mock_logger
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        
        # Simular función de extracción como en afinia_manager
        def mock_afinia_extraction(browser_manager, auth_manager, logger):
            # Simular el patrón de afinia_manager
            if auth_manager.login():
                logger.info("Login exitoso en Afinia")
                # Simular creación de extractor
                return True
            else:
                logger.error("Fallo en el login de Afinia")
                raise Exception("Fallo en el login de Afinia")
        
        # Configurar auth_manager para login exitoso
        mock_auth.login.return_value = True
        
        # Ejecutar función
        run_extractor(
            extractor_name="Afinia",
            config={'url': 'test'},
            extractor_function=mock_afinia_extraction
        )
        
        # Verificar que se ejecuta correctamente
        mock_auth.login.assert_called_once()
        mock_logger.info.assert_any_call("Login exitoso en Afinia")
    
    @patch('src.utils.extractor_runner.BrowserManager')
    @patch('src.utils.extractor_runner.AuthenticationManager')
    @patch('src.utils.extractor_runner.initialize_logger')
    @patch('sys.argv', ['test_script.py'])
    def test_compatibilidad_con_aire_manager(self, mock_init_logger, mock_auth_class, mock_browser_class):
        """Prueba compatibilidad con el patrón de aire_manager"""
        # Configurar mocks
        mock_logger = Mock()
        mock_init_logger.return_value = mock_logger
        mock_browser = Mock()
        mock_browser_class.return_value = mock_browser
        mock_auth = Mock()
        mock_auth_class.return_value = mock_auth
        
        # Simular función de extracción como en aire_manager
        def mock_aire_extraction(browser_manager, auth_manager, logger):
            # Simular el patrón de aire_manager
            from unittest.mock import Mock
            extractor = Mock()
            extractor.run_extraction.return_value = "Extracción exitosa"
            return extractor.run_extraction()
        
        # Ejecutar función
        run_extractor(
            extractor_name="Aire",
            config={'url': 'test'},
            extractor_function=mock_aire_extraction
        )
        
        # Verificar que se ejecuta correctamente
        mock_logger.info.assert_any_call("=== Extractor Aire completado exitosamente ===")


if __name__ == '__main__':
    # Configurar el runner de pruebas
    unittest.main(verbosity=2)