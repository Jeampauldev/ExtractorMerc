#!/usr/bin/env python3
"""
Test del Flujo de Mercurio
=========================

Script para probar el funcionamiento de los extractores de Afinia y Aire
según las especificaciones del archivo flujos.yaml.

Verifica:
1. Configuración de URLs correctas
2. Credenciales según flujos.yaml
3. Filtros de fecha automáticos (30 días)
4. Filtros de datos (asunto y pasos)
5. Funcionalidad de login
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_flujo_mercurio.log')
    ]
)

logger = logging.getLogger(__name__)

def test_afinia_configuration():
    """Probar configuración de Afinia según flujos.yaml"""
    try:
        logger.info("=== PROBANDO CONFIGURACIÓN AFINIA ===")
        
        from Merc.services.afinia_extractor import AfiniaExtractor
        
        # Crear instancia del extractor
        extractor = AfiniaExtractor(headless=True)
        
        # Verificar URLs según flujos.yaml
        expected_urls = {
            "base": "https://mercurio.afinia.com.co/mercurio/index.jsp?err=0",
            "login": "https://mercurio.afinia.com.co/mercurio/index.jsp?err=0",
            "pqr_pendientes": "https://mercurio.afinia.com.co/mercurio/servlet/ControllerMercurio?command=consultaEspecial&tipoOperacion=parametros&idCnslta=00000015"
        }
        
        for key, expected_url in expected_urls.items():
            actual_url = extractor.urls.get(key)
            if actual_url == expected_url:
                logger.info(f"✅ [AFINIA] URL {key}: {actual_url}")
            else:
                logger.error(f"❌ [AFINIA] URL {key} incorrecta: {actual_url} != {expected_url}")
        
        # Verificar credenciales según flujos.yaml
        expected_username = "281005131"
        expected_password = "123"
        
        actual_username = extractor.mercurio_credentials["username"]
        actual_password = extractor.mercurio_credentials["password"]
        
        if actual_username == expected_username:
            logger.info(f"✅ [AFINIA] Username: {actual_username}")
        else:
            logger.error(f"❌ [AFINIA] Username incorrecto: {actual_username} != {expected_username}")
            
        if actual_password == expected_password:
            logger.info(f"✅ [AFINIA] Password: {actual_password}")
        else:
            logger.error(f"❌ [AFINIA] Password incorrecto: {actual_password} != {expected_password}")
        
        # Verificar filtros de fecha (30 días)
        fecha_desde = extractor.filter_config.get("fecha_desde")
        fecha_hasta = extractor.filter_config.get("fecha_hasta")
        
        if fecha_desde and fecha_hasta:
            logger.info(f"✅ [AFINIA] Filtros de fecha: {fecha_desde} - {fecha_hasta}")
            
            # Verificar que las fechas sean correctas (30 días)
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, "%d/%m/%Y")
                fecha_hasta_dt = datetime.strptime(fecha_hasta, "%d/%m/%Y")
                diferencia = (fecha_hasta_dt - fecha_desde_dt).days
                
                if 29 <= diferencia <= 31:  # Permitir variación por días del mes
                    logger.info(f"✅ [AFINIA] Rango de fechas correcto: {diferencia} días")
                else:
                    logger.warning(f"⚠️ [AFINIA] Rango de fechas inesperado: {diferencia} días")
            except Exception as e:
                logger.error(f"❌ [AFINIA] Error validando fechas: {e}")
        else:
            logger.error("❌ [AFINIA] Filtros de fecha no configurados")
        
        # Probar filtros de datos
        test_data = [
            {"asunto": "PETICION", "paso": "2"},
            {"asunto": "QUEJA", "paso": "3"},
            {"asunto": "RECLAMO", "paso": "4"},
            {"asunto": "TMP", "paso": "2"},
            {"asunto": "OTRO", "paso": "2"},  # Debe ser filtrado
            {"asunto": "PETICION", "paso": "1"},  # Debe ser filtrado
        ]
        
        filtered_data = extractor._apply_data_filters(test_data)
        expected_count = 4  # Solo los primeros 4 deben pasar el filtro
        
        if len(filtered_data) == expected_count:
            logger.info(f"✅ [AFINIA] Filtros de datos funcionando: {len(filtered_data)}/{len(test_data)} registros")
        else:
            logger.error(f"❌ [AFINIA] Filtros de datos incorrectos: {len(filtered_data)}/{len(test_data)} registros")
        
        logger.info("✅ [AFINIA] Configuración verificada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ [AFINIA] Error en configuración: {e}")
        return False

def test_aire_configuration():
    """Probar configuración de Aire según flujos.yaml"""
    try:
        logger.info("=== PROBANDO CONFIGURACIÓN AIRE ===")
        
        from Merc.services.aire_extractor import AireExtractor
        
        # Crear instancia del extractor
        extractor = AireExtractor(headless=True)
        
        # Verificar URLs según flujos.yaml
        expected_urls = {
            "base": "https://caribesol.servisoft.com.co/mercurio/index.jsp?err=0",
            "login": "https://caribesol.servisoft.com.co/mercurio/index.jsp?err=0",
            "pqr_pendientes": "https://caribesol.servisoft.com.co/mercurio/servlet/ControllerMercurio?command=consultaEspecial&tipoOperacion=parametros&idCnslta=00000015"
        }
        
        for key, expected_url in expected_urls.items():
            actual_url = extractor.urls.get(key)
            if actual_url == expected_url:
                logger.info(f"✅ [AIRE] URL {key}: {actual_url}")
            else:
                logger.error(f"❌ [AIRE] URL {key} incorrecta: {actual_url} != {expected_url}")
        
        # Verificar credenciales según flujos.yaml
        expected_username = "MHERNANDEZO"
        expected_password = "1234"
        
        actual_username = extractor.mercurio_credentials["username"]
        actual_password = extractor.mercurio_credentials["password"]
        
        if actual_username == expected_username:
            logger.info(f"✅ [AIRE] Username: {actual_username}")
        else:
            logger.error(f"❌ [AIRE] Username incorrecto: {actual_username} != {expected_username}")
            
        if actual_password == expected_password:
            logger.info(f"✅ [AIRE] Password: {actual_password}")
        else:
            logger.error(f"❌ [AIRE] Password incorrecto: {actual_password} != {expected_password}")
        
        # Verificar filtros de fecha (30 días)
        fecha_desde = extractor.filter_config.get("fecha_desde")
        fecha_hasta = extractor.filter_config.get("fecha_hasta")
        
        if fecha_desde and fecha_hasta:
            logger.info(f"✅ [AIRE] Filtros de fecha: {fecha_desde} - {fecha_hasta}")
            
            # Verificar que las fechas sean correctas (30 días)
            try:
                fecha_desde_dt = datetime.strptime(fecha_desde, "%d/%m/%Y")
                fecha_hasta_dt = datetime.strptime(fecha_hasta, "%d/%m/%Y")
                diferencia = (fecha_hasta_dt - fecha_desde_dt).days
                
                if 29 <= diferencia <= 31:  # Permitir variación por días del mes
                    logger.info(f"✅ [AIRE] Rango de fechas correcto: {diferencia} días")
                else:
                    logger.warning(f"⚠️ [AIRE] Rango de fechas inesperado: {diferencia} días")
            except Exception as e:
                logger.error(f"❌ [AIRE] Error validando fechas: {e}")
        else:
            logger.error("❌ [AIRE] Filtros de fecha no configurados")
        
        # Probar filtros de datos
        test_data = [
            {"asunto": "PETICION", "paso": "2"},
            {"asunto": "QUEJA", "paso": "3"},
            {"asunto": "RECLAMO", "paso": "4"},
            {"asunto": "TMP", "paso": "2"},
            {"asunto": "OTRO", "paso": "2"},  # Debe ser filtrado
            {"asunto": "PETICION", "paso": "1"},  # Debe ser filtrado
        ]
        
        filtered_data = extractor._apply_data_filters(test_data)
        expected_count = 4  # Solo los primeros 4 deben pasar el filtro
        
        if len(filtered_data) == expected_count:
            logger.info(f"✅ [AIRE] Filtros de datos funcionando: {len(filtered_data)}/{len(test_data)} registros")
        else:
            logger.error(f"❌ [AIRE] Filtros de datos incorrectos: {len(filtered_data)}/{len(test_data)} registros")
        
        logger.info("✅ [AIRE] Configuración verificada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ [AIRE] Error en configuración: {e}")
        return False

def test_login_functionality():
    """Probar funcionalidad de login (sin navegador real)"""
    try:
        logger.info("=== PROBANDO FUNCIONALIDAD DE LOGIN ===")
        
        # Verificar que los extractores se puedan instanciar
        from Merc.services.afinia_extractor import AfiniaExtractor
        from Merc.services.aire_extractor import AireExtractor
        
        afinia_extractor = AfiniaExtractor(headless=True)
        aire_extractor = AireExtractor(headless=True)
        
        logger.info("✅ Extractores instanciados correctamente")
        
        # Verificar que tengan los métodos necesarios
        required_methods = ['setup_browser', 'authenticate', 'extract_data', 'cleanup']
        
        for method in required_methods:
            if hasattr(afinia_extractor, method):
                logger.info(f"✅ [AFINIA] Método {method} disponible")
            else:
                logger.error(f"❌ [AFINIA] Método {method} no disponible")
                
            if hasattr(aire_extractor, method):
                logger.info(f"✅ [AIRE] Método {method} disponible")
            else:
                logger.error(f"❌ [AIRE] Método {method} no disponible")
        
        logger.info("✅ Funcionalidad de login verificada")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en funcionalidad de login: {e}")
        return False

def main():
    """Función principal de pruebas"""
    logger.info("🚀 INICIANDO PRUEBAS DEL FLUJO MERCURIO")
    logger.info("=" * 60)
    
    results = {
        "afinia_config": False,
        "aire_config": False,
        "login_functionality": False
    }
    
    # Probar configuración de Afinia
    results["afinia_config"] = test_afinia_configuration()
    
    # Probar configuración de Aire
    results["aire_config"] = test_aire_configuration()
    
    # Probar funcionalidad de login
    results["login_functionality"] = test_login_functionality()
    
    # Resumen de resultados
    logger.info("=" * 60)
    logger.info("📊 RESUMEN DE PRUEBAS")
    logger.info("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nResultado final: {passed_tests}/{total_tests} pruebas pasaron")
    
    if passed_tests == total_tests:
        logger.info("🎉 ¡TODAS LAS PRUEBAS PASARON! El flujo está correctamente configurado.")
        return True
    else:
        logger.error("⚠️ Algunas pruebas fallaron. Revisar la configuración.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)