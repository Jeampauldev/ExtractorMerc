#!/usr/bin/env python3
"""
Test de Login Real - Mercurio
============================

Script para probar el login real en las plataformas de Mercurio
de Afinia y Aire con las credenciales especificadas en flujos.yaml.

IMPORTANTE: Este script requiere conexión a internet y las credenciales
deben ser válidas para funcionar correctamente.
"""

import sys
import os
import logging
import asyncio
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging sin emojis para evitar problemas de codificación
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_login_real.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_afinia_login():
    """Probar login real de Afinia"""
    try:
        logger.info("=== PROBANDO LOGIN REAL AFINIA ===")
        
        from Merc.services.afinia_extractor import AfiniaExtractor
        
        # Crear extractor con navegador visible para debugging
        extractor = AfiniaExtractor(headless=False)
        
        logger.info("[AFINIA] Configurando navegador...")
        if not extractor.setup_browser():
            logger.error("[AFINIA] Error configurando navegador")
            return False
        
        logger.info("[AFINIA] Intentando autenticación...")
        logger.info(f"[AFINIA] URL: {extractor.urls['login']}")
        logger.info(f"[AFINIA] Usuario: {extractor.mercurio_credentials['username']}")
        logger.info(f"[AFINIA] Password: {'*' * len(extractor.mercurio_credentials['password'])}")
        
        # Intentar login
        success = extractor.authenticate()
        
        if success:
            logger.info("[AFINIA] LOGIN EXITOSO!")
            
            # Esperar un poco para ver el resultado
            import time
            time.sleep(3)
            
            # Obtener URL actual para verificar
            if extractor.browser_manager and extractor.browser_manager.page:
                current_url = extractor.browser_manager.page.url
                logger.info(f"[AFINIA] URL después del login: {current_url}")
        else:
            logger.error("[AFINIA] LOGIN FALLIDO!")
        
        # Limpiar recursos
        extractor.cleanup()
        
        return success
        
    except Exception as e:
        logger.error(f"[AFINIA] Error en test de login: {e}")
        return False

def test_aire_login():
    """Probar login real de Aire"""
    try:
        logger.info("=== PROBANDO LOGIN REAL AIRE ===")
        
        from Merc.services.aire_extractor import AireExtractor
        
        # Crear extractor con navegador visible para debugging
        extractor = AireExtractor(headless=False)
        
        logger.info("[AIRE] Configurando navegador...")
        if not extractor.setup_browser():
            logger.error("[AIRE] Error configurando navegador")
            return False
        
        logger.info("[AIRE] Intentando autenticación...")
        logger.info(f"[AIRE] URL: {extractor.urls['login']}")
        logger.info(f"[AIRE] Usuario: {extractor.mercurio_credentials['username']}")
        logger.info(f"[AIRE] Password: {'*' * len(extractor.mercurio_credentials['password'])}")
        
        # Intentar login
        success = extractor.authenticate()
        
        if success:
            logger.info("[AIRE] LOGIN EXITOSO!")
            
            # Esperar un poco para ver el resultado
            import time
            time.sleep(3)
            
            # Obtener URL actual para verificar
            if extractor.browser_manager and extractor.browser_manager.page:
                current_url = extractor.browser_manager.page.url
                logger.info(f"[AIRE] URL después del login: {current_url}")
        else:
            logger.error("[AIRE] LOGIN FALLIDO!")
        
        # Limpiar recursos
        extractor.cleanup()
        
        return success
        
    except Exception as e:
        logger.error(f"[AIRE] Error en test de login: {e}")
        return False

def test_quick_validation():
    """Prueba rápida de validación sin navegador real"""
    try:
        logger.info("=== VALIDACIÓN RÁPIDA ===")
        
        from Merc.services.afinia_extractor import AfiniaExtractor
        from Merc.services.aire_extractor import AireExtractor
        
        # Verificar configuraciones
        afinia = AfiniaExtractor(headless=True)
        aire = AireExtractor(headless=True)
        
        # Verificar URLs
        logger.info(f"[AFINIA] URL base: {afinia.urls['base']}")
        logger.info(f"[AIRE] URL base: {aire.urls['base']}")
        
        # Verificar credenciales
        logger.info(f"[AFINIA] Credenciales: {afinia.mercurio_credentials['username']}")
        logger.info(f"[AIRE] Credenciales: {aire.mercurio_credentials['username']}")
        
        # Verificar filtros de fecha
        logger.info(f"[AFINIA] Fechas: {afinia.filter_config['fecha_desde']} - {afinia.filter_config['fecha_hasta']}")
        logger.info(f"[AIRE] Fechas: {aire.filter_config['fecha_desde']} - {aire.filter_config['fecha_hasta']}")
        
        logger.info("VALIDACIÓN RÁPIDA COMPLETADA")
        return True
        
    except Exception as e:
        logger.error(f"Error en validación rápida: {e}")
        return False

def main():
    """Función principal"""
    logger.info("INICIANDO PRUEBAS DE LOGIN REAL")
    logger.info("=" * 60)
    
    # Preguntar al usuario qué prueba ejecutar
    print("\nSeleccione la prueba a ejecutar:")
    print("1. Validación rápida (sin navegador)")
    print("2. Test login Afinia (con navegador)")
    print("3. Test login Aire (con navegador)")
    print("4. Test ambos logins")
    
    try:
        choice = input("\nIngrese su opción (1-4): ").strip()
    except KeyboardInterrupt:
        print("\nPrueba cancelada por el usuario")
        return False
    
    results = {}
    
    if choice == "1":
        results["validacion"] = test_quick_validation()
    elif choice == "2":
        results["afinia_login"] = test_afinia_login()
    elif choice == "3":
        results["aire_login"] = test_aire_login()
    elif choice == "4":
        results["afinia_login"] = test_afinia_login()
        results["aire_login"] = test_aire_login()
    else:
        logger.error("Opción inválida")
        return False
    
    # Resumen
    logger.info("=" * 60)
    logger.info("RESUMEN DE PRUEBAS")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "EXITOSO" if result else "FALLIDO"
        logger.info(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    logger.info(f"\nResultado: {passed_tests}/{total_tests} pruebas exitosas")
    
    if passed_tests == total_tests:
        logger.info("TODAS LAS PRUEBAS PASARON!")
        return True
    else:
        logger.error("ALGUNAS PRUEBAS FALLARON")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nPrueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        sys.exit(1)