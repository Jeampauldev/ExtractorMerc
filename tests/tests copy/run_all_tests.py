#!/usr/bin/env python3
"""
Script para ejecutar todas las pruebas del proyecto ExtractorOV_Modular
Genera un reporte completo de cobertura y resultados
"""

import unittest
import sys
import os
from io import StringIO
import time

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestResult:
    """Clase para almacenar resultados de pruebas"""
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        self.failures = []
        self.errors = []
        self.execution_time = 0


def run_test_suite(test_module_name, description):
    """Ejecuta una suite de pruebas específica"""
    print(f"\n{'='*60}")
    print(f"EJECUTANDO: {description}")
    print(f"Módulo: {test_module_name}")
    print(f"{'='*60}")
    
    # Capturar salida
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    
    # Cargar y ejecutar pruebas
    start_time = time.time()
    try:
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(test_module_name)
        result = runner.run(suite)
        execution_time = time.time() - start_time
        
        # Crear objeto de resultado
        test_result = TestResult()
        test_result.total_tests = result.testsRun
        test_result.passed_tests = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        test_result.failed_tests = len(result.failures)
        test_result.error_tests = len(result.errors)
        test_result.skipped_tests = len(result.skipped)
        test_result.failures = result.failures
        test_result.errors = result.errors
        test_result.execution_time = execution_time
        
        # Mostrar resultados
        print(f"\nRESULTADOS DE {description}:")
        print(f"  Total de pruebas: {test_result.total_tests}")
        print(f"  Exitosas: {test_result.passed_tests}")
        print(f"  Fallidas: {test_result.failed_tests}")
        print(f"  Errores: {test_result.error_tests}")
        print(f"  Omitidas: {test_result.skipped_tests}")
        print(f"  Tiempo de ejecución: {test_result.execution_time:.2f}s")
        
        # Mostrar detalles de fallos si los hay
        if test_result.failures:
            print(f"\nFALLOS EN {description}:")
            for test, traceback in test_result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if test_result.errors:
            print(f"\nERRORES EN {description}:")
            for test, traceback in test_result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
        
        return test_result
        
    except Exception as e:
        print(f"ERROR al ejecutar {description}: {e}")
        test_result = TestResult()
        test_result.error_tests = 1
        test_result.execution_time = time.time() - start_time
        return test_result


def generate_summary_report(results):
    """Genera un reporte resumen de todas las pruebas"""
    print(f"\n{'='*80}")
    print("REPORTE RESUMEN DE TODAS LAS PRUEBAS")
    print(f"{'='*80}")
    
    total_tests = sum(r.total_tests for r in results.values())
    total_passed = sum(r.passed_tests for r in results.values())
    total_failed = sum(r.failed_tests for r in results.values())
    total_errors = sum(r.error_tests for r in results.values())
    total_skipped = sum(r.skipped_tests for r in results.values())
    total_time = sum(r.execution_time for r in results.values())
    
    print(f"TOTALES GENERALES:")
    print(f"  Total de pruebas ejecutadas: {total_tests}")
    print(f"  Pruebas exitosas: {total_passed}")
    print(f"  Pruebas fallidas: {total_failed}")
    print(f"  Errores: {total_errors}")
    print(f"  Pruebas omitidas: {total_skipped}")
    print(f"  Tiempo total de ejecución: {total_time:.2f}s")
    
    # Calcular porcentaje de éxito
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"  Tasa de éxito: {success_rate:.1f}%")
    
    print(f"\nDETALLE POR SUITE:")
    for suite_name, result in results.items():
        status = "[EXITOSO] EXITOSA" if (result.failed_tests + result.error_tests) == 0 else "[ERROR] CON FALLOS"
        print(f"  {suite_name}: {status}")
        print(f"    - Pruebas: {result.total_tests}, Exitosas: {result.passed_tests}, "
              f"Fallidas: {result.failed_tests}, Errores: {result.error_tests}")
    
    # Determinar estado general
    overall_status = "[EXITOSO] TODAS LAS PRUEBAS EXITOSAS" if (total_failed + total_errors) == 0 else "[ERROR] HAY PRUEBAS FALLIDAS"
    print(f"\nESTADO GENERAL: {overall_status}")
    
    return (total_failed + total_errors) == 0


def main():
    """Función principal para ejecutar todas las pruebas"""
    print("INICIANDO EJECUCIÓN COMPLETA DE PRUEBAS")
    print("ExtractorOV_Modular - Suite de Pruebas Completa")
    print(f"Fecha y hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Definir suites de pruebas
    test_suites = {
        "Pruebas Unitarias - Afinia Manager": "tests.unit.test_afinia_manager",
        "Pruebas Unitarias - Aire Manager": "tests.unit.test_aire_manager", 
        "Pruebas de Integración - Extractor Runner": "tests.unit.test_extractor_runner",
        "Pruebas de Regresión - Suite Completa": "tests.regression.test_regression_suite"
    }
    
    # Ejecutar cada suite
    results = {}
    start_time = time.time()
    
    for description, module_name in test_suites.items():
        results[description] = run_test_suite(module_name, description)
    
    total_execution_time = time.time() - start_time
    
    # Generar reporte resumen
    all_passed = generate_summary_report(results)
    
    print(f"\nTiempo total de ejecución: {total_execution_time:.2f}s")
    print(f"{'='*80}")
    
    # Retornar código de salida apropiado
    if all_passed:
        print("[COMPLETADO] TODAS LAS PRUEBAS HAN PASADO EXITOSAMENTE")
        print("El sistema está listo para implementar los cambios propuestos.")
        return 0
    else:
        print("[ADVERTENCIA]  ALGUNAS PRUEBAS HAN FALLADO")
        print("Revise los errores antes de implementar cambios.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)