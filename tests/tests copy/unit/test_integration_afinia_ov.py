#!/usr/bin/env python3
"""
Test de Integración Completa - Extractor Afinia Oficina Virtual
==============================================================

Este test verifica el flujo completo integrado:
1. Extracción de datos desde Oficina Virtual
2. Procesamiento automático con validación
3. Carga automática en RDS AWS
4. Verificación de datos en base de datos

Incluye:
- Test de conectividad RDS
- Test de creación de tablas
- Test de extracción + procesamiento
- Test de consultas y validación de datos
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Agregar ruta del proyecto
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Imports del sistema
from src.extractors.afinia.oficina_virtual_afinia_modular import OficinaVirtualAfiniaModular
from src.processors.afinia.database_manager import AfiniaDatabaseManager
from src.processors.afinia.data_processor import AfiniaDataProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[INTEGRATION-TEST] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class IntegrationTestAfiniaOV:
    """
    Suite de tests de integración para el sistema completo de Afinia OV
    """

    def __init__(self):
        """Inicializa el test de integración"""
        self.db_manager = AfiniaDatabaseManager()
        self.data_processor = AfiniaDataProcessor()
        self.extractor = None
        self.test_results = {
            'database_connectivity': False,
            'table_creation': False,
            'extraction_success': False,
            'processing_success': False,
            'data_verification': False,
            'total_records_processed': 0,
            'errors': []
        }

        logger.info("[INICIANDO] Inicializando test de integración completa")

    def test_database_connectivity(self) -> bool:
        """
        Test 1: Verificar conectividad con RDS AWS

        Returns:
            bool: True si la conexión es exitosa
        """
        logger.info("[EMOJI_REMOVIDO] TEST 1: Verificando conectividad RDS...")

        try:
            success = self.db_manager.test_connection()
            self.test_results['database_connectivity'] = success

            if success:
                logger.info("[EXITOSO] TEST 1 PASSED: Conectividad RDS exitosa")
            else:
                logger.error("[ERROR] TEST 1 FAILED: No se pudo conectar a RDS")

            return success

        except Exception as e:
            error_msg = f"TEST 1 ERROR: {str(e)}"
            self.test_results['errors'].append(error_msg)
            logger.error(f"[EMOJI_REMOVIDO] {error_msg}")
            return False

    def test_table_creation(self) -> bool:
        """
        Test 2: Verificar creación de tablas e índices

        Returns:
            bool: True si las tablas se crean correctamente
        """
        logger.info("[EMOJI_REMOVIDO] TEST 2: Verificando creación de tablas...")

        try:
            success = self.db_manager.create_table_if_not_exists()
            self.test_results['table_creation'] = success

            if success:
                logger.info("[EXITOSO] TEST 2 PASSED: Tablas e índices creados exitosamente")
            else:
                logger.error("[ERROR] TEST 2 FAILED: Error creando tablas")

            return success

        except Exception as e:
            error_msg = f"TEST 2 ERROR: {str(e)}"
            self.test_results['errors'].append(error_msg)
            logger.error(f"[EMOJI_REMOVIDO] {error_msg}")
            return False

    def test_extraction_with_processing(self, headless: bool = True) -> bool:
        """
        Test 3: Verificar extracción completa con procesamiento automático

        Args:
            headless: Si ejecutar en modo headless

        Returns:
            bool: True si la extracción y procesamiento son exitosos
        """
        logger.info("[EMOJI_REMOVIDO] TEST 3: Verificando extracción + procesamiento...")

        try:
            # Crear extractor
            self.extractor = OficinaVirtualAfiniaModular(headless=headless)

            # Ejecutar extracción con procesamiento automático
            logger.info("[EMOJI_REMOVIDO] Iniciando extracción completa...")
            results = self.extractor.run_extraction(
                report_types=["pqr_pendientes"],
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now()
            )

            # Verificar resultados de extracción
            extraction_success = results.get('success', False)
            self.test_results['extraction_success'] = extraction_success

            # Verificar resultados de procesamiento
            processing_results = results.get('processing', {})
            processing_success = processing_results.get('processed_files', 0) > 0
            self.test_results['processing_success'] = processing_success
            self.test_results['total_records_processed'] = processing_results.get('processed_records', 0)

            # Log detallado de resultados
            logger.info("[DATOS] RESULTADOS DE EXTRACCIÓN Y PROCESAMIENTO:")
            logger.info(f"  - Extracción exitosa: {extraction_success}")
            logger.info(f"  - Archivos extraídos: {len(results.get('extracted_files', {}))}")
            logger.info(f"  - Procesamiento exitoso: {processing_success}")
            logger.info(f"  - Archivos procesados: {processing_results.get('processed_files', 0)}")
            logger.info(f"  - Registros cargados en RDS: {processing_results.get('processed_records', 0)}")
            logger.info(f"  - Archivos fallidos: {processing_results.get('failed_files', 0)}")

            # Mostrar estadísticas detalladas
            if processing_results.get('stats'):
                logger.info("[METRICAS] Estadísticas detalladas:")
                for file_type, stats in processing_results['stats'].items():
                    logger.info(f"  {file_type}:")
                    logger.info(f"    - Procesados: {stats.get('processed_count', 0)}")
                    logger.info(f"    - Duplicados: {stats.get('duplicates_found', 0)}")
                    logger.info(f"    - Errores validación: {stats.get('validation_errors', 0)}")

            # Mostrar errores si los hay
            if results.get('errors'):
                logger.warning("[ADVERTENCIA] Errores encontrados:")
                for error in results['errors']:
                    logger.warning(f"  - {error}")
                    self.test_results['errors'].append(f"Extraction: {error}")

            if processing_results.get('errors'):
                logger.warning("[ADVERTENCIA] Errores de procesamiento:")
                for error in processing_results['errors']:
                    logger.warning(f"  - {error}")
                    self.test_results['errors'].append(f"Processing: {error}")

            # Determinar éxito del test
            test_success = extraction_success and processing_success

            if test_success:
                logger.info("[EXITOSO] TEST 3 PASSED: Extracción y procesamiento exitosos")
            else:
                logger.error("[ERROR] TEST 3 FAILED: Fallo en extracción o procesamiento")

            return test_success

        except Exception as e:
            error_msg = f"TEST 3 ERROR: {str(e)}"
            self.test_results['errors'].append(error_msg)
            logger.error(f"[EMOJI_REMOVIDO] {error_msg}")
            return False

        finally:
            # Cleanup
            if self.extractor:
                self.extractor.cleanup()

    def test_data_verification(self) -> bool:
        """
        Test 4: Verificar que los datos se cargaron correctamente en RDS

        Returns:
            bool: True si los datos están correctamente en la base de datos
        """
        logger.info("[EMOJI_REMOVIDO] TEST 4: Verificando datos en RDS...")

        try:
            # Obtener estadísticas de la base de datos
            stats = self.db_manager.get_processing_stats()

            if not stats:
                logger.warning("[ADVERTENCIA] No se pudieron obtener estadísticas de la base de datos")
                return False

            # Log estadísticas
            logger.info("[DATOS] ESTADÍSTICAS DE LA BASE DE DATOS:")
            logger.info(f"  - Total registros: {stats.get('total_records', 0)}")
            logger.info(f"  - Radicados únicos: {stats.get('unique_radicados', 0)}")
            logger.info(f"  - SGCs únicos: {stats.get('unique_sgc', 0)}")
            logger.info(f"  - Primer procesamiento: {stats.get('first_processed', 'N/A')}")
            logger.info(f"  - Último procesamiento: {stats.get('last_processed', 'N/A')}")
            logger.info(f"  - Procesados últimas 24h: {stats.get('processed_last_24h', 0)}")

            # Verificar que hay datos
            total_records = stats.get('total_records', 0)
            recent_records = stats.get('processed_last_24h', 0)

            # Consideramos exitoso si hay registros en general
            # o si se procesaron registros recientemente
            verification_success = total_records > 0 or recent_records > 0
            self.test_results['data_verification'] = verification_success

            if verification_success:
                logger.info("[EXITOSO] TEST 4 PASSED: Datos verificados en RDS")
            else:
                logger.error("[ERROR] TEST 4 FAILED: No se encontraron datos en RDS")

            return verification_success

        except Exception as e:
            error_msg = f"TEST 4 ERROR: {str(e)}"
            self.test_results['errors'].append(error_msg)
            logger.error(f"[EMOJI_REMOVIDO] {error_msg}")
            return False

    def run_full_integration_test(self, headless: bool = True) -> bool:
        """
        Ejecuta la suite completa de tests de integración

        Args:
            headless: Si ejecutar extracción en modo headless

        Returns:
            bool: True si todos los tests pasan
        """
        logger.info("[INICIANDO] INICIANDO SUITE COMPLETA DE TESTS DE INTEGRACIÓN")
        logger.info("=" * 60)

        start_time = time.time()

        # Ejecutar tests en secuencia
        tests_passed = 0
        total_tests = 4

        # Test 1: Conectividad
        if self.test_database_connectivity():
            tests_passed += 1
        else:
            logger.error("[EMOJI_REMOVIDO] Test de conectividad falló, cancelando suite")
            return False

        logger.info("-" * 40)

        # Test 2: Creación de tablas
        if self.test_table_creation():
            tests_passed += 1
        else:
            logger.error("[EMOJI_REMOVIDO] Test de creación de tablas falló, cancelando suite")
            return False

        logger.info("-" * 40)

        # Test 3: Extracción y procesamiento
        if self.test_extraction_with_processing(headless=headless):
            tests_passed += 1

        logger.info("-" * 40)

        # Test 4: Verificación de datos
        if self.test_data_verification():
            tests_passed += 1

        # Calcular tiempo total
        end_time = time.time()
        duration = end_time - start_time

        # Resumen final
        logger.info("=" * 60)
        logger.info("[EMOJI_REMOVIDO] RESUMEN DE TESTS DE INTEGRACIÓN")
        logger.info(f"  Tests ejecutados: {total_tests}")
        logger.info(f"  Tests exitosos: {tests_passed}")
        logger.info(f"  Tests fallidos: {total_tests - tests_passed}")
        logger.info(f"  Tiempo total: {duration:.2f} segundos")
        logger.info(f"  Registros procesados: {self.test_results['total_records_processed']}")

        # Mostrar detalles de cada test
        logger.info("\n[EMOJI_REMOVIDO] DETALLES POR TEST:")
        logger.info(f"  1. Conectividad RDS: {'[EXITOSO] PASS' if self.test_results['database_connectivity'] else '[ERROR] FAIL'}")
        logger.info(f"  2. Creación tablas: {'[EXITOSO] PASS' if self.test_results['table_creation'] else '[ERROR] FAIL'}")
        logger.info(f"  3. Extracción: {'[EXITOSO] PASS' if self.test_results['extraction_success'] else '[ERROR] FAIL'}")
        logger.info(f"  4. Procesamiento: {'[EXITOSO] PASS' if self.test_results['processing_success'] else '[ERROR] FAIL'}")
        logger.info(f"  5. Verificación datos: {'[EXITOSO] PASS' if self.test_results['data_verification'] else '[ERROR] FAIL'}")

        # Mostrar errores si los hay
        if self.test_results['errors']:
            logger.info("\n[ADVERTENCIA] ERRORES ENCONTRADOS:")
            for i, error in enumerate(self.test_results['errors'], 1):
                logger.info(f"  {i}. {error}")

        # Determinar éxito general
        all_tests_passed = tests_passed == total_tests

        if all_tests_passed:
            logger.info("\n[COMPLETADO] SUITE DE INTEGRACIÓN COMPLETADA EXITOSAMENTE")
            logger.info("[EXITOSO] El sistema completo está funcionando correctamente:")
            logger.info("  [EXITOSO] Extracción de datos")
            logger.info("  [EXITOSO] Validación y procesamiento")
            logger.info("  [EXITOSO] Carga en RDS AWS")
            logger.info("  [EXITOSO] Integridad de datos")
        else:
            logger.error("\n[EMOJI_REMOVIDO] SUITE DE INTEGRACIÓN FALLÓ")
            logger.error(f"[ERROR] {total_tests - tests_passed} test(s) no pasaron")
            logger.error("[EMOJI_REMOVIDO] Revisar logs para más detalles")

        return all_tests_passed


def main():
    """Función principal para ejecutar los tests"""
    logger.info("[INICIANDO] Iniciando tests de integración completa para Afinia OV")

    # Crear suite de tests
    test_suite = IntegrationTestAfiniaOV()

    # Ejecutar tests
    # Cambiar headless=False si quieres ver el navegador durante el test
    success = test_suite.run_full_integration_test(headless=True)

    # Salir con código apropiado
    if success:
        logger.info("[COMPLETADO] Todos los tests de integración pasaron exitosamente")
        sys.exit(0)
    else:
        logger.error("[EMOJI_REMOVIDO] Algunos tests de integración fallaron")
        sys.exit(1)


if __name__ == "__main__":
    main()
