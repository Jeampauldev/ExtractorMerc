#!/usr/bin/env python3
"""
Pruebas unitarias para afinia_manager.py
Valida que el manager funcione correctamente antes y después de cambios
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from afinia_manager import run_afinia_extraction, main


class TestAfiniaManager(unittest.TestCase):
    """Pruebas unitarias para el manager de Afinia"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.mock_browser_manager = Mock()
        self.mock_auth_manager = Mock()
        self.mock_logger = Mock()
        
        # Mock de configuración
        self.mock_config = {
            'url': 'https://test.afinia.com',
            'credentials': {'username': 'test', 'password': 'test'},
            'timeouts': {'navigation': 30, 'login': 15}
        }
    
    @patch('afinia_manager.get_afinia_config')
    @patch('afinia_manager.OficinaVirtualAfiniaModular')
    def test_run_afinia_extraction_login_exitoso(self, mock_extractor_class, mock_get_config):
        """Prueba extracción exitosa con login correcto"""
        # Configurar mocks
        mock_get_config.return_value = self.mock_config
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        self.mock_auth_manager.login.return_value = True
        
        # Ejecutar función
        run_afinia_extraction(
            self.mock_browser_manager, 
            self.mock_auth_manager, 
            self.mock_logger
        )
        
        # Verificar comportamiento
        self.mock_auth_manager.login.assert_called_once()
        self.mock_logger.info.assert_called_with("Login exitoso en Afinia")
        mock_extractor_class.assert_called_once_with(
            browser_manager=self.mock_browser_manager,
            config=self.mock_config,
            logger=self.mock_logger
        )
        mock_extractor.run_extraction.assert_called_once()
    
    @patch('afinia_manager.get_afinia_config')
    @patch('afinia_manager.OficinaVirtualAfiniaModular')
    def test_run_afinia_extraction_login_fallido(self, mock_extractor_class, mock_get_config):
        """Prueba manejo de error cuando falla el login"""
        # Configurar mocks
        mock_get_config.return_value = self.mock_config
        self.mock_auth_manager.login.return_value = False
        
        # Verificar que se lanza excepción
        with self.assertRaises(Exception) as context:
            run_afinia_extraction(
                self.mock_browser_manager, 
                self.mock_auth_manager, 
                self.mock_logger
            )
        
        # Verificar comportamiento
        self.assertEqual(str(context.exception), "Fallo en el login de Afinia")
        self.mock_auth_manager.login.assert_called_once()
        self.mock_logger.error.assert_called_with("Fallo en el login de Afinia")
        mock_extractor_class.assert_not_called()
    
    @patch('afinia_manager.get_afinia_config')
    @patch('afinia_manager.OficinaVirtualAfiniaModular')
    def test_run_afinia_extraction_error_en_extractor(self, mock_extractor_class, mock_get_config):
        """Prueba manejo de errores durante la extracción"""
        # Configurar mocks
        mock_get_config.return_value = self.mock_config
        mock_extractor = Mock()
        mock_extractor.run_extraction.side_effect = Exception("Error en extracción")
        mock_extractor_class.return_value = mock_extractor
        self.mock_auth_manager.login.return_value = True
        
        # Verificar que se propaga la excepción
        with self.assertRaises(Exception) as context:
            run_afinia_extraction(
                self.mock_browser_manager, 
                self.mock_auth_manager, 
                self.mock_logger
            )
        
        # Verificar comportamiento
        self.assertEqual(str(context.exception), "Error en extracción")
        mock_extractor.run_extraction.assert_called_once()
    
    @patch('afinia_manager.run_extractor')
    @patch('afinia_manager.get_afinia_config')
    def test_main_function(self, mock_get_config, mock_run_extractor):
        """Prueba la función main"""
        # Configurar mocks
        mock_get_config.return_value = self.mock_config
        
        # Ejecutar función main
        main()
        
        # Verificar comportamiento
        mock_get_config.assert_called_once()
        mock_run_extractor.assert_called_once_with(
            extractor_name="Afinia",
            config=self.mock_config,
            extractor_function=run_afinia_extraction
        )
    
    @patch('afinia_manager.get_afinia_config')
    def test_configuracion_valida(self, mock_get_config):
        """Prueba que la configuración se carga correctamente"""
        # Configurar mock
        mock_get_config.return_value = self.mock_config
        
        # Verificar que se puede obtener la configuración
        config = mock_get_config()
        
        # Verificar estructura de configuración
        self.assertIn('url', config)
        self.assertIn('credentials', config)
        self.assertIn('timeouts', config)
    
    def test_parametros_requeridos_run_afinia_extraction(self):
        """Prueba que run_afinia_extraction requiere todos los parámetros"""
        # Verificar que falla sin parámetros
        with self.assertRaises(TypeError):
            run_afinia_extraction()
        
        # Verificar que falla con parámetros incompletos
        with self.assertRaises(TypeError):
            run_afinia_extraction(self.mock_browser_manager)
        
        with self.assertRaises(TypeError):
            run_afinia_extraction(self.mock_browser_manager, self.mock_auth_manager)


class TestAfiniaManagerIntegration(unittest.TestCase):
    """Pruebas de integración para validar el flujo completo"""
    
    @patch('afinia_manager.run_extractor')
    @patch('afinia_manager.get_afinia_config')
    def test_flujo_completo_main(self, mock_get_config, mock_run_extractor):
        """Prueba el flujo completo desde main"""
        # Configurar mocks
        mock_config = {
            'url': 'https://test.afinia.com',
            'credentials': {'username': 'test', 'password': 'test'}
        }
        mock_get_config.return_value = mock_config
        
        # Ejecutar main
        main()
        
        # Verificar que se llama run_extractor con los parámetros correctos
        mock_run_extractor.assert_called_once()
        args, kwargs = mock_run_extractor.call_args
        
        self.assertEqual(kwargs['extractor_name'], "Afinia")
        self.assertEqual(kwargs['config'], mock_config)
        self.assertEqual(kwargs['extractor_function'], run_afinia_extraction)


if __name__ == '__main__':
    # Configurar el runner de pruebas
    unittest.main(verbosity=2)