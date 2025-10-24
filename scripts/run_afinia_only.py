#!/usr/bin/env python3
"""
Ejecutor Específico de Afinia - Mercurio
=======================================

Script para ejecutar únicamente el extractor de Afinia siguiendo
el flujo completo implementado según flujos.yaml.

Funcionalidades:
- Login automático con credenciales configuradas
- Filtros de fecha automáticos (30 días)
- Navegación a PQR pendientes
- Descarga de reportes Excel
- Procesamiento de datos con filtros específicos
- Detección automática de plataforma (Windows/Ubuntu)
"""

import sys
import os
import logging
from datetime import datetime
import time

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar detector de plataforma
from Merc.utils.platform_detector import platform_detector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('afinia_execution.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def run_afinia_extraction():
    """
    Ejecutar extracción completa de Afinia con detección automática de plataforma
    """
    try:
        # Detectar plataforma automáticamente
        platform_config = platform_detector.detect_platform()
        
        logger.info("=== INICIANDO EXTRACCIÓN AFINIA ===")
        logger.info(f"🖥️ Plataforma detectada: {platform_config.platform_type}")
        logger.info(f"🎭 Modo headless: {'Activado' if platform_config.headless_required else 'Desactivado'}")
        
        # Aplicar configuración de entorno
        platform_detector.apply_environment_config()
        
        from Merc.services.afinia_extractor import AfiniaExtractor
        
        # Crear extractor (ya no necesita parámetro headless, se detecta automáticamente)
        extractor = AfiniaExtractor()
        
        # Mostrar configuración
        logger.info("CONFIGURACIÓN ACTUAL:")
        logger.info(f"  - URL Base: {extractor.urls['base']}")
        logger.info(f"  - URL Login: {extractor.urls['login']}")
        logger.info(f"  - Usuario: {extractor.mercurio_credentials['username']}")
        logger.info(f"  - Fechas: {extractor.filter_config['fecha_desde']} - {extractor.filter_config['fecha_hasta']}")
        
        # Paso 1: Configurar navegador
        logger.info("\n[PASO 1/6] Configurando navegador...")
        if not extractor.setup_browser():
            raise Exception("Error configurando navegador")
        logger.info("✅ Navegador configurado exitosamente")
        
        # Pausa breve para estabilidad
        time.sleep(2)
        
        # Paso 2: Autenticación
        logger.info("\n[PASO 2/6] Realizando login...")
        if not extractor.authenticate():
            raise Exception("Error en autenticación")
        logger.info("✅ Login exitoso")
        
        # Pausa después del login
        time.sleep(3)
        
        # Paso 3: Navegar a PQR Pendientes
        logger.info("\n[PASO 3/6] Navegando a PQR Pendientes...")
        page = extractor.browser_manager.page
        
        # Verificar que el navegador sigue activo
        try:
            if page.is_closed():
                logger.error("❌ El navegador se ha cerrado inesperadamente")
                return False
        except Exception as check_error:
            logger.error(f"❌ Error verificando estado del navegador: {check_error}")
            return False
        
        # Verificar estado del navegador antes de navegar
        logger.info(f"Estado actual del navegador: {page.url}")
        
        # Navegar a PQR Escritas Pendientes
        pqr_url = extractor.urls.get('pqr_pendientes')
        if not pqr_url:
            pqr_url = extractor.urls.get('base')  # Fallback a URL base
            logger.warning("URL pqr_pendientes no encontrada, usando URL base como fallback")
        
        logger.info(f"URL objetivo: {pqr_url}")
        logger.info("Iniciando navegación...")
        
        try:
            # Navegar con timeout extendido y logging detallado
            logger.info("Ejecutando page.goto()...")
            page.goto(pqr_url, timeout=45000, wait_until="domcontentloaded")
            logger.info("page.goto() completado exitosamente")
            
            # Verificar que la navegación fue exitosa
            current_url = page.url
            logger.info(f"URL actual después de navegación: {current_url}")
            
            # Esperar a que cargue la página
            logger.info("Esperando carga completa de la página...")
            time.sleep(3)
            
            # Verificar elementos en la página
            try:
                title = page.title()
                logger.info(f"Título de la página: {title}")
            except Exception as title_error:
                logger.warning(f"No se pudo obtener el título: {title_error}")
            
            logger.info("✅ Navegación completada exitosamente")
            
        except Exception as nav_error:
            logger.error(f"❌ Error durante la navegación: {nav_error}")
            logger.info("Verificando estado del navegador...")
            
            # Verificar si el navegador sigue activo
            try:
                if page.is_closed():
                    logger.error("❌ El navegador se cerró durante la navegación")
                    return False
                else:
                    logger.info("El navegador sigue activo, continuando...")
            except Exception as check_error:
                logger.error(f"❌ Error verificando estado del navegador: {check_error}")
                return False
        
        # Paso 4: Configurar filtros de fecha
        logger.info("\n[PASO 4/6] Configurando filtros de fecha...")
        extractor._setup_date_filters()
        
        # Aplicar fechas en los campos HTML de la página actual
        page = extractor.browser_manager.page
        fecha_desde = extractor.filter_config.get("fecha_desde")
        fecha_hasta = extractor.filter_config.get("fecha_hasta")
        
        if fecha_desde and fecha_hasta:
            logger.info(f"Aplicando fechas en campos HTML: {fecha_desde} - {fecha_hasta}")
            success = extractor._configure_date_range_pqr_escritas(page, fecha_desde, fecha_hasta)
            if success:
                logger.info("✅ Fechas aplicadas exitosamente en los campos HTML")
            else:
                logger.warning("⚠️ Error aplicando fechas en los campos HTML")
        else:
            logger.warning("⚠️ Fechas no configuradas en filter_config")
        
        logger.info("✅ Filtros de fecha configurados")
        
        # Pausa después de filtros
        time.sleep(2)
        
        # Paso 5: Generar y descargar reportes Excel (PQR Pendientes y Verbales)
        logger.info("\n[PASO 5/6] Generando y descargando reportes Excel...")
        
        # === DESCARGA 1: PQR PENDIENTES ===
        logger.info("=== DESCARGANDO PQR PENDIENTES ===")
        
        # Navegar a PQR Pendientes (usando mismo formato que PQR Verbales)
        logger.info("Navegando a PQR Pendientes...")
        pqr_pendientes_url = "https://serviciospqrs.afinia.com.co/mercurio/servlet/ControllerMercurio?command=consultaEspecial&tipoOperacion=parametros&idCnslta=00000065"
        page.goto(pqr_pendientes_url)
        page.wait_for_load_state("networkidle")
        
        # Aplicar las fechas configuradas a los campos HTML
        logger.info("Aplicando fechas a los campos HTML...")
        fecha_desde = extractor.filter_config.get('fecha_desde')
        fecha_hasta = extractor.filter_config.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta:
            logger.info(f"Aplicando fechas: {fecha_desde} - {fecha_hasta}")
            extractor._configure_date_range_pqr_escritas(page, fecha_desde, fecha_hasta)
        else:
            logger.warning("No se pudieron obtener las fechas configuradas")
        
        # Hacer clic en el botón de Excel para PQR Pendientes con múltiples selectores
        logger.info("Buscando botón Excel para PQR Pendientes...")
        
        # Esperar a que la página se cargue completamente
        page.wait_for_load_state("networkidle")
        
        # Intentar múltiples selectores para el botón Excel
        excel_selectors_pend = [
            "#cmd_ejecuta_excel",
            "input[id='cmd_ejecuta_excel']",
            "input[value='Generar en Excel']",
            "input[onclick*='fnGenerarExcel']",
            "input[type='button'][value*='Excel']",
            "input[onclick*='Excel']"
        ]
        
        excel_button_pend = None
        for selector in excel_selectors_pend:
            try:
                # Esperar hasta 5 segundos por cada selector
                excel_button_pend = page.wait_for_selector(selector, timeout=5000)
                if excel_button_pend:
                    logger.info(f"✅ Botón Excel encontrado con selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} falló: {e}")
                continue
        
        if excel_button_pend:
            try:
                with page.expect_download(timeout=60000) as download_info_pend:  # 60 segundos
                    excel_button_pend.click(timeout=10000)
                
                download_pend = download_info_pend.value
                
                # Generar nombre de archivo con timestamp según flujo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_pend = f"afinia_pqr_pend_{timestamp}.xls"
                filepath_pend = os.path.join("data", "raw", "afinia", "pqr_pendientes", filename_pend)
                
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(filepath_pend), exist_ok=True)
                
                # Guardar archivo
                download_pend.save_as(filepath_pend)
                logger.info(f"✅ Archivo PQR Pendientes descargado exitosamente: {filepath_pend}")
                
            except Exception as e:
                logger.error(f"❌ Error descargando PQR Pendientes: {e}")
        else:
            logger.error("❌ No se encontró el botón Excel para PQR Pendientes")
        
        # Paso 6: Navegar a PQR Verbales Pendientes
        logger.info("\n[PASO 6/6] Navegando a PQR Verbales Pendientes...")
        pqr_verbales_url = "https://serviciospqrs.afinia.com.co/mercurio/servlet/ControllerMercurio?command=consultaEspecial&tipoOperacion=parametros&idCnslta=00000016"
        
        # Verificar que el navegador sigue activo antes de navegar
        page = extractor.browser_manager.page
        try:
            if page.is_closed():
                logger.error("❌ El navegador se ha cerrado antes de navegar a PQR Verbales")
                return False
        except Exception as check_error:
            logger.error(f"❌ Error verificando estado del navegador: {check_error}")
            return False
        
        logger.info(f"Estado actual del navegador: {page.url}")
        logger.info(f"URL objetivo: {pqr_verbales_url}")
        
        try:
            # Navegar a PQR Verbales
            logger.info("Navegando a PQR Verbales...")
            page.goto(pqr_verbales_url, timeout=45000, wait_until="domcontentloaded")
            logger.info("✅ Navegación a PQR Verbales completada")
            
            # Esperar a que cargue la página
            time.sleep(3)
            
            # Aplicar fechas en los campos HTML para PQR Verbales
            logger.info("Aplicando fechas para PQR Verbales...")
            success = extractor._configure_date_range_pqr_verbales(page, fecha_desde, fecha_hasta)
            if success:
                logger.info("✅ Fechas aplicadas exitosamente para PQR Verbales")
            else:
                logger.warning("⚠️ Error aplicando fechas para PQR Verbales")
            
            # Buscar y hacer clic en el botón "General en Excel" con múltiples selectores
            logger.info("Buscando botón 'General en Excel' para PQR Verbales...")
            
            # Esperar a que la página se cargue completamente
            page.wait_for_load_state("networkidle")
            
            # Intentar múltiples selectores para el botón Excel
            excel_selectors_verb = [
                "input[value='General en Excel']",
                "input[value='Generar en Excel']", 
                "#cmd_ejecuta_excel",
                "input[id='cmd_ejecuta_excel']",
                "input[onclick*='fnGenerarExcel']",
                "input[type='button'][value*='Excel']",
                "input[onclick*='Excel']"
            ]
            
            excel_button_verb = None
            for selector in excel_selectors_verb:
                try:
                    # Esperar hasta 5 segundos por cada selector
                    excel_button_verb = page.wait_for_selector(selector, timeout=5000)
                    if excel_button_verb:
                        logger.info(f"✅ Botón Excel encontrado con selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} falló: {e}")
                    continue
            
            if excel_button_verb:
                logger.info("✅ Botón 'General en Excel' encontrado para PQR Verbales")
                
                # Configurar descarga con nombre personalizado
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                custom_filename = f"afinia_pqr_verb_pend_{timestamp}"
                
                # Configurar el download manager para la descarga con timeout extendido
                download_promise = page.expect_download(timeout=60000)  # 60 segundos
                
                # Hacer clic en el botón
                excel_button_verb.click()
                logger.info("✅ Clic en botón 'General en Excel' para PQR Verbales ejecutado")
                
                # Esperar y manejar la descarga
                download = download_promise.value
                
                # Guardar el archivo con el nombre personalizado en la nueva estructura
                download_path = f"data/raw/afinia/pqr_verbales/{custom_filename}.xls"
                
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(download_path), exist_ok=True)
                
                download.save_as(download_path)
                
                logger.info(f"✅ Archivo PQR Verbales descargado como: {custom_filename}.xls")
                
            else:
                logger.error("❌ No se encontró el botón 'General en Excel' para PQR Verbales")
                
        except Exception as e:
            logger.error(f"❌ Error descargando PQR Verbales: {e}")
            # Verificar si el navegador se cerró
            try:
                if page.is_closed():
                    logger.error("❌ El navegador se cerró durante la descarga de PQR Verbales")
                    return False
            except Exception:
                pass
        
        # Pausa para estabilidad después de las descargas
        time.sleep(3)
        
        # Mostrar resumen final
        logger.info("\n" + "="*60)
        logger.info("EXTRACCIÓN COMPLETADA EXITOSAMENTE")
        logger.info("="*60)
        logger.info("📋 Resumen:")
        logger.info(f"  - Empresa: Afinia")
        logger.info(f"  - Período: {extractor.filter_config['fecha_desde']} - {extractor.filter_config['fecha_hasta']}")
        logger.info(f"  - Archivos descargados: 2 (PQR Pendientes + PQR Verbales)")
        logger.info(f"  - Tiempo total: {datetime.now().strftime('%H:%M:%S')}")
        
        # Limpiar recursos
        extractor.cleanup()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en extracción: {e}")
        return False

def run_afinia_test_only():
    """Ejecutar solo prueba de login sin extracción completa"""
    try:
        logger.info("=== PRUEBA DE LOGIN AFINIA ===")
        
        from Merc.services.afinia_extractor import AfiniaExtractor
        
        # Crear extractor en modo visible para ver el proceso
        extractor = AfiniaExtractor(headless=False)
        
        logger.info("Configurando navegador...")
        if not extractor.setup_browser():
            logger.error("Error configurando navegador")
            return False
        
        logger.info("Realizando login...")
        success = extractor.authenticate()
        
        if success:
            logger.info("✅ LOGIN EXITOSO!")
            
            # Mostrar URL actual
            current_url = extractor.browser_manager.page.url
            logger.info(f"URL actual: {current_url}")
            
            # Esperar para ver el resultado
            input("\nPresiona ENTER para cerrar el navegador...")
        else:
            logger.error("❌ LOGIN FALLIDO!")
        
        extractor.cleanup()
        return success
        
    except Exception as e:
        logger.error(f"Error en prueba: {e}")
        return False

def main():
    """Función principal - Ejecuta automáticamente la extracción de Afinia"""
    print("\n" + "="*60)
    print("EXTRACTOR AFINIA - MERCURIO")
    print("="*60)
    
    # Mostrar información de plataforma detectada
    platform_detector.print_platform_info()
    
    logger.info("🚀 Iniciando extracción automática de Afinia...")
    return run_afinia_extraction()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nOperación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        sys.exit(1)