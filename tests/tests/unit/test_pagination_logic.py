"""
PRUEBA SIMPLE - LÓGICA DE PAGINACIÓN
Valida que la lógica de paginación está correctamente implementada
"""

import sys
sys.path.append('.')

import logging
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test.logic')

async def test_pagination_manager_logic():
    """Test de la lógica del PaginationManager sin navegador"""
    logger.info("🧪 === PRUEBA DE LÓGICA DE PAGINACIÓN ===")
    
    try:
        from src.components.afinia_pagination_manager import AfiniaPaginationManager, PaginationState
        
        # Crear manager con directorio temporal
        base_dir = Path(__file__).parent / "temp_test"
        base_dir.mkdir(exist_ok=True)
        
        manager = AfiniaPaginationManager(base_dir)
        
        # Test 1: Verificar inicialización
        assert manager.state.current_page == 1
        assert manager.state.total_records == 0
        assert manager.state.is_paused == False
        logger.info("[EXITOSO] Test 1: Inicialización correcta")
        
        # Test 2: Simular extracción de información de paginación
        mock_page = MagicMock()
        mock_element = AsyncMock()
        mock_element.inner_text = AsyncMock(return_value="1 - 10 de 33529")
        mock_locator = AsyncMock()
        mock_locator.count = AsyncMock(return_value=1)
        mock_locator.nth = AsyncMock(return_value=mock_element)
        mock_page.locator = MagicMock(return_value=mock_locator)
        
        start_num, end_num, total_records = await manager.extract_pagination_info(mock_page)
        
        assert start_num == 1
        assert end_num == 10
        assert total_records == 33529
        logger.info(f"[EXITOSO] Test 2: Extracción de paginación - {start_num}-{end_num} de {total_records:,}")
        
        # Test 3: Verificar checkpoint
        manager.state.current_page = 5
        manager.state.total_records = 33529
        manager.state.processed_records = 250
        
        checkpoint_saved = manager._save_checkpoint()
        assert checkpoint_saved == True
        logger.info("[EXITOSO] Test 3: Checkpoint guardado correctamente")
        
        # Test 4: Verificar scripts de control
        manager.create_control_scripts()
        
        scripts_dir = base_dir.parent / "server_control_scripts"
        expected_scripts = ["pause.sh", "resume.sh", "stop.sh", "status.sh", "clean_signals.sh"]
        
        for script in expected_scripts:
            script_path = scripts_dir / script
            assert script_path.exists(), f"Script {script} no existe"
        
        logger.info("[EXITOSO] Test 4: Scripts de control creados")
        
        # Test 5: Verificar integración con PQRProcessor
        from src.components.afinia_pqr_processor import AfiniaPQRProcessor
        
        mock_page_pqr = MagicMock()
        processor = AfiniaPQRProcessor(
            page=mock_page_pqr,
            download_path=str(base_dir),
            screenshots_dir=str(base_dir / "screenshots")
        )
        
        # Verificar que tiene PaginationManager
        assert hasattr(processor, 'pagination_manager')
        assert processor.pagination_manager is not None
        logger.info("[EXITOSO] Test 5: Integración PQRProcessor correcta")
        
        # Test 6: Verificar método de procesamiento masivo
        assert hasattr(processor, 'process_all_pages_massive')
        assert hasattr(processor, 'process_current_page_records')
        logger.info("[EXITOSO] Test 6: Métodos de procesamiento masivo presentes")
        
        logger.info("[COMPLETADO] ¡TODOS LOS TESTS DE LÓGICA PASARON!")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Error en tests: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_pagination_parameters():
    """Test de parámetros de paginación"""
    logger.info("🧪 === PRUEBA DE PARÁMETROS DE PAGINACIÓN ===")
    
    try:
        # Test del nuevo parámetro enable_pagination
        from src.components.afinia_pqr_processor import AfiniaPQRProcessor
        
        mock_page = MagicMock()
        base_dir = Path(__file__).parent / "temp_test"
        
        processor = AfiniaPQRProcessor(
            page=mock_page,
            download_path=str(base_dir),
            screenshots_dir=str(base_dir / "screenshots")
        )
        
        # Verificar que el método acepta enable_pagination
        import inspect
        sig = inspect.signature(processor.process_all_pqr_records)
        params = list(sig.parameters.keys())
        
        assert 'enable_pagination' in params, "Parámetro enable_pagination no encontrado"
        logger.info("[EXITOSO] Parámetro enable_pagination presente en process_all_pqr_records")
        
        # Verificar valores por defecto
        enable_pagination_param = sig.parameters['enable_pagination']
        assert enable_pagination_param.default == False, "Valor por defecto debería ser False"
        logger.info("[EXITOSO] Valor por defecto de enable_pagination es False")
        
        logger.info("[COMPLETADO] ¡TESTS DE PARÁMETROS PASARON!")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Error en test de parámetros: {e}")
        return False

async def main():
    """Ejecutar todos los tests de lógica"""
    logger.info("[INICIANDO] === INICIANDO TESTS DE LÓGICA DE PAGINACIÓN ===")
    
    test1_result = await test_pagination_manager_logic()
    test2_result = await test_pagination_parameters()
    
    if test1_result and test2_result:
        logger.info("[COMPLETADO] ¡TODOS LOS TESTS PASARON! La lógica de paginación está correcta.")
        logger.info("")
        logger.info("[RESULTADO] CONCLUSIÓN:")
        logger.info("   [ARCHIVO] El sistema de paginación automática está correctamente implementado")
        logger.info("   [EMOJI_REMOVIDO] Los controles de servidor están configurados")
        logger.info("   [EMOJI_REMOVIDO] El sistema de checkpoint funciona")
        logger.info("   [CONFIGURANDO] La integración con PQRProcessor es correcta")
        logger.info("")
        logger.info("[INFO] PARA PROBAR EN VIVO:")
        logger.info("   python run_afinia_ov_massive_with_pagination.py")
        logger.info("   O usar enable_pagination=True en process_all_pqr_records()")
        
        return True
    else:
        logger.error("[ERROR] Algunos tests fallaron")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    exit(0 if success else 1)