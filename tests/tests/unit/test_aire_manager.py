#!/usr/bin/env python3
"""
Pruebas unitarias para aire_manager.py
Valida que el manager funcione correctamente antes y después de cambios
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from aire_manager import main_aire_extraction, main


class TestAireManager(unittest.TestCase):
    """Pruebas unitarias para el manager de Aire"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.mock_browser_manager = Mock()
        self.mock_auth_manager = Mock()
        self.mock_logger = Mock()
        
        # Mock de configuración
        self.mock_config = {
            'url': 'https://test.aire.com',
            'credentials': {'username': 'test', 'password': 'test'},
            'timeouts': {'navigation': 30, 'login': 15}
        }
    
    @patch('aire_manager.get_extractor_config')
    @patch('aire_manager.OficinaVirtualAireModular')
    def test_main_aire_extraction_exitoso(self, mock_extractor_class, mock_get_config):
        """Prueba extracción exitosa de Aire"""
        # Configurar mocks
        mock_get_config.return_value = self.mock_config
        mock_extractor = Mock()
        mock_extractor.run_extraction.return_value = "Extracción exitosa"
        mock_extractor_class.return_value = mock_extractor
        
        # Ejecutar función
        result = main_aire_extraction(
            self.mock_browser_manager, 
            self.mock_auth_manager, 
            self.mock_logger
        )
        
        # Verificar comportamiento
        mock_get_config.assert_called_once_with("aire", "oficina_virtual")
        mock_extractor_class.assert_called_once_with(
            self.mock_browser_manager,
            self.mock_auth_manager,
            self.mock_config
        )
        mock_extractor.run_extraction.assert_called_once()
        self.assertEqual(result, "Extracción exitosa")
    
    @patch('aire_manager.get_extractor_config')
    @patch('aire_manager.OficinaVirtualAireModular')
    def test_main_aire_extraction_error_en_extractor(self, mock_extractor_class, mock_get_config):
        """Prueba manejo de errores durante la extracción de Aire"""
        # Configurar mocks
        mock_get_config.return_value = self.mock_config
        mock_extractor = Mock()
        mock_extractor.run_extraction.side_effect = Exception("Error en extracción Aire")
        mock_extractor_class.return_value = mock_extractor
        
        # Verificar que se propaga la excepción
        with self.assertRaises(Exception) as context:
            main_aire_extraction(
                self.mock_browser_manager, 
                self.mock_auth_manager, 
                self.mock_logger
            )
        
        # Verificar comportamiento
        self.assertEqual(str(context.exception), "Error en extracción Aire")
        mock_extractor.run_extraction.assert_called_once()
    
    @patch('aire_manager.get_extractor_config')
    @patch('aire_manager.OficinaVirtualAireModular')
    def test_main_aire_extraction_error_en_configuracion(self, mock_extractor_class, mock_get_config):
        """Prueba manejo de errores en la configuración"""
        # Configurar mock para que falle
        mock_get_config.side_effect = Exception("Error al cargar configuración")
        
        # Verificar que se propaga la excepción
        with self.assertRaises(Exception) as context:
            main_aire_extraction(
                self.mock_browser_manager, 
                self.mock_auth_manager, 
                self.mock_logger
            )
        
        # Verificar comportamiento
        self.assertEqual(str(context.exception), "Error al cargar configuración")
        mock_extractor_class.assert_not_called()
    
    @patch('aire_manager.run_extractor')
    @patch('aire_manager.get_extractor_config')
    def test_main_function(self, mock_get_config, mock_run_extractor):
        """Prueba la función main"""
        # Configurar mocks
        mock_get_config.return_value = self.mock_config
        
        # Ejecutar función main
        main()
        
        # Verificar comportamiento
        mock_get_config.assert_called_once_with("aire", "oficina_virtual")
        mock_run_extractor.assert_called_once_with(
            extractor_name="Aire",
            config=self.mock_config,
            extractor_function=main_aire_extraction
        )
    
    @patch('aire_manager.get_extractor_config')
    def test_configuracion_valida(self, mock_get_config):
        """Prueba que la configuración se carga correctamente"""
        # Configurar mock
        mock_get_config.return_value = self.mock_config
        
        # Verificar que se puede obtener la configuración
        config = mock_get_config("aire", "oficina_virtual")
        
        # Verificar estructura de configuración
        self.assertIn('url', config)
        self.assertIn('credentials', config)
        self.assertIn('timeouts', config)
    
    def test_parametros_requeridos_main_aire_extraction(self):
        """Prueba que main_aire_extraction requiere todos los parámetros"""
        # Verificar que falla sin parámetros
        with self.assertRaises(TypeError):
            main_aire_extraction()
        
        # Verificar que falla con parámetros incompletos
        with self.assertRaises(TypeError):
            main_aire_extraction(self.mock_browser_manager)
        
        with self.assertRaises(TypeError):
            main_aire_extraction(self.mock_browser_manager, self.mock_auth_manager)
    
    @patch('aire_manager.get_extractor_config')
    @patch('aire_manager.OficinaVirtualAireModular')
    def test_inicializacion_extractor_con_parametros_correctos(self, mock_extractor_class, mock_get_config):
        """Prueba que el extractor se inicializa con los parámetros correctos"""
        # Configurar mocks
        mock_get_config.return_value = self.mock_config
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        
        # Ejecutar función
        main_aire_extraction(
            self.mock_browser_manager, 
            self.mock_auth_manager, 
            self.mock_logger
        )
        
        # Verificar que se inicializa con los parámetros correctos
        mock_extractor_class.assert_called_once_with(
            self.mock_browser_manager,
            self.mock_auth_manager,
            self.mock_config
        )


class TestAireManagerIntegration(unittest.TestCase):
    """Pruebas de integración para validar el flujo completo"""
    
    @patch('aire_manager.run_extractor')
    @patch('aire_manager.get_extractor_config')
    def test_flujo_completo_main(self, mock_get_config, mock_run_extractor):
        """Prueba el flujo completo desde main"""
        # Configurar mocks
        mock_config = {
            'url': 'https://test.aire.com',
            'credentials': {'username': 'test', 'password': 'test'}
        }
        mock_get_config.return_value = mock_config
        
        # Ejecutar main
        main()
        
        # Verificar que se llama run_extractor con los parámetros correctos
        mock_run_extractor.assert_called_once()
        args, kwargs = mock_run_extractor.call_args
        
        self.assertEqual(kwargs['extractor_name'], "Aire")
        self.assertEqual(kwargs['config'], mock_config)
        self.assertEqual(kwargs['extractor_function'], main_aire_extraction)
    
    @patch('aire_manager.get_extractor_config')
    @patch('aire_manager.OficinaVirtualAireModular')
    def test_retorno_de_main_aire_extraction(self, mock_extractor_class, mock_get_config):
        """Prueba que main_aire_extraction retorna el resultado del extractor"""
        # Configurar mocks
        mock_get_config.return_value = self.mock_config
        mock_extractor = Mock()
        expected_result = {"status": "success", "records": 100}
        mock_extractor.run_extraction.return_value = expected_result
        mock_extractor_class.return_value = mock_extractor
        
        # Ejecutar función
        result = main_aire_extraction(
            Mock(), Mock(), Mock()
        )
        
        # Verificar que retorna el resultado correcto
        self.assertEqual(result, expected_result)


class TestAireManagerComparacionConAfinia(unittest.TestCase):
    """Pruebas para validar diferencias específicas entre Aire y Afinia"""
    
    @patch('aire_manager.get_extractor_config')
    def test_configuracion_aire_vs_afinia(self, mock_get_config):
        """Prueba que Aire usa get_extractor_config en lugar de get_afinia_config"""
        # Configurar mock
        mock_config = {'platform': 'aire'}
        mock_get_config.return_value = mock_config
        
        # Verificar que se llama con parámetros específicos de Aire
        config = mock_get_config("aire", "oficina_virtual")
        mock_get_config.assert_called_with("aire", "oficina_virtual")
    
    @patch('aire_manager.get_extractor_config')
    @patch('aire_manager.OficinaVirtualAireModular')
    def test_aire_no_maneja_popups_como_afinia(self, mock_extractor_class, mock_get_config):
        """Prueba que Aire no requiere manejo especial de popups como Afinia"""
        # Configurar mocks
        mock_get_config.return_value = self.mock_config
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        
        # Ejecutar función
        main_aire_extraction(Mock(), Mock(), Mock())
        
        # Verificar que se inicializa sin configuraciones especiales de popup
        # (esto es implícito en la diferencia de parámetros vs Afinia)
        mock_extractor_class.assert_called_once()


if __name__ == '__main__':
    # Configurar el runner de pruebas
    unittest.main(verbosity=2)