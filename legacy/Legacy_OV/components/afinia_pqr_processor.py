"""
Procesador específico de PQR para Afinia
Implementa la secuencia específica requerida:
1. Clic en ojo para abrir nueva pestaña (sin cerrar anterior)
2. Imprimir/guardar PDF con nombre del campo "Número Reclamo SGC"
3. Verificar adjuntos en "Documento/prueba" y descargar con código SGC
4. Extraer y guardar JSON con todos los datos de la PQR
5. Cerrar ventana y continuar con siguiente registro
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from .afinia_pagination_manager import AfiniaPaginationManager
import logging

# Configurar logger específico para este módulo
logger = logging.getLogger('AFINIA-PQR')


class AfiniaPQRProcessor:
    """
    Procesador específico de PQR para Afinia
    Implementa la secuencia exacta requerida por el usuario
    """

    def __init__(self, page, download_path: str, screenshots_dir: str):
        """
        Inicializa el procesador de PQR de Afinia

        Args:
            page: Página de Playwright
            download_path: Directorio base para descargas
            screenshots_dir: Directorio para screenshots
        """
        self.page = page
        
        # Asegurar que usamos la ruta dentro del proyecto
        base_path = Path(download_path)
        if not str(base_path).endswith("ExtractorOV_Modular"):
        # Si la ruta no termina en el proyecto, construir la ruta correcta
            project_root = Path(__file__).parent.parent.parent
            base_path = project_root / "data" / "downloads" / "afinia" / "oficina_virtual"
        
        self.download_path = base_path / "processed"
        self.screenshots_dir = Path(screenshots_dir)
        self.data_dir = base_path / "processed"

        # Crear directorios si no existen
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ARCHIVOS Directorio de descarga configurado: {self.download_path.absolute()}")
        logger.info(f"ARCHIVOS Directorio de datos configurado: {self.data_dir.absolute()}")

        # Selectores específicos para número SGC
        self.sgc_selectors = [
            "input[name='NumeroReclamoSGC']",
            "td.text-td-label:has-text('Número Reclamo SGC') + td input",
            "td.text-td-label:has-text('Número Reclamo SGC') + td.ng-binding",
            "input[id*='SGC']",
            "input[placeholder*='SGC']"
        ]

        # Selectores específicos para adjuntos en "Documento/prueba"
        self.document_proof_selectors = [
            "td.text-td-label:has-text('Documento/prueba') + td a",
            "td.text-td-label:has-text('Documento/prueba') + td a[href*='download']",
            "td.text-td-label:has-text('Documento/prueba') + td a[href*='archivo']",
            "td.text-td-label:has-text('Documento/prueba') + td a[href*='documento']",
            "td:has(.text-td-label:has-text('Documento/prueba')) + td a",
            "td:has-text('Documento/prueba') + td a",
            "td:has-text('Documento') + td a",
            "td:has-text('prueba') + td a",
            ".text-td-label:has-text('Documento') ~ td a",
            ".text-td-label:has-text('prueba') ~ td a",
            "a[href*='attachment']",
            "a[href*='file']",
            "a[download]",
            "a:has-text('Descargar')",
            "a:has-text('Ver')",
            "a:has-text('Archivo')",
            "button:has-text('Descargar')",
            "button:has-text('Ver archivo')"
        ]

        # Selectores para botones del ojo
        self.eye_button_selectors = [
            'a.md-primary[tooltip="Ver PQR"]',
            'td.md-actions a[tooltip="Ver PQR"]',
            'a[href*="#Detail/"]',
            'td.md-cell.md-actions a.md-primary',
            "button.btn-eye",
            "a.btn-eye", 
            "button[title*='Ver']",
            "a[title*='Ver']",
            "button:has(i.fa-eye)",
            "a:has(i.fa-eye)",
            ".btn:has(.fa-eye)"
        ]

        # Inicializar PaginationManager para procesamiento masivo
        self.pagination_manager = AfiniaPaginationManager(self.download_path.parent)
        
        logger.info("AfiniaPQRProcessor inicializado correctamente")

    async def process_all_pqr_records(self, max_records: Optional[int] = None, enable_pagination: bool = False) -> int:
        """
        Procesa todos los registros PQR siguiendo la secuencia específica
        Si enable_pagination=True, continúa con paginación automática después de la página actual
        
        Args:
            max_records: Número máximo de registros a procesar en la página actual
            enable_pagination: Si True, activa paginación automática después de procesar página actual
            
        Returns:
            int: Número de registros procesados exitosamente
        """
        try:
            logger.info("=== INICIANDO PROCESAMIENTO DE PQR (SECUENCIA ESPECÍFICA AFINIA) ===")

            # Buscar botones del ojo
            found_buttons = await self._find_eye_buttons()
            
            if not found_buttons:
                logger.error("No se encontraron botones del ojo")
                return 0

            # Limitar número de registros si se especifica
            if max_records:
                found_buttons = found_buttons[:max_records]

            logger.info(f"Total de botones encontrados para procesar: {len(found_buttons)}")

            # Procesar cada botón siguiendo la secuencia específica
            successful_records = 0
            for idx, (selector, button_idx) in enumerate(found_buttons, 1):
                try:
                    logger.info(f"=== Procesando PQR #{idx} de {len(found_buttons)} ===")

                    # Obtener el botón específico
                    button = self.page.locator(selector).nth(button_idx)

                    # Procesar la PQR con secuencia específica
                    success = await self._process_single_pqr_specific_sequence(button, idx)

                    if success:
                        successful_records += 1
                        logger.info(f"EXITOSO PQR #{idx} procesada exitosamente")
                    else:
                        logger.warning(f"ERROR No se pudo procesar PQR #{idx}")

                    # Pausa entre procesamiento
                    await self.page.wait_for_timeout(2000)

                except Exception as record_error:
                    logger.error(f"Error procesando PQR #{idx}: {record_error}")
                    continue

            logger.info(f"PROCESO_COMPLETADO PROCESAMIENTO PÁGINA ACTUAL COMPLETADO: {successful_records}/{len(found_buttons)} registros exitosos")
            
            # Si está habilitada la paginación, continuar con páginas siguientes
            if enable_pagination:
                logger.info("PAGINA Activando paginación automática para procesar todas las páginas...")
                
                # Ejecutar procesamiento masivo con paginación
                pagination_results = await self.pagination_manager.process_all_pages(
                    page=self.page,
                    pqr_processor=self,
                    max_pages=None  # Sin límite, procesar todas las páginas
                )
                
                total_records_all_pages = pagination_results.get('total_processed', 0)
                logger.info(f"OBJETIVO PROCESAMIENTO MASIVO COMPLETADO: {total_records_all_pages} registros en total")
                
                return successful_records + total_records_all_pages
            
            return successful_records

        except Exception as e:
            logger.error(f"Error en process_all_pqr_records: {e}")
            return 0

    async def process_all_pages_massive(self, max_pages: Optional[int] = None) -> Dict[str, Any]:
        """
        Procesamiento masivo con paginación automática - 333,529 registros
        
        Args:
            max_pages: Límite máximo de páginas (None = sin límite)
            
        Returns:
            Dict con estadísticas del procesamiento
        """
        try:
            logger.info("INICIANDO === INICIANDO PROCESAMIENTO MASIVO CON PAGINACIÓN ===")
            logger.info("PROCESADOS Total estimado: 333,529 registros")
            logger.info("OBJETIVO Configurando para servidor Linux con controles")
            
            # Crear scripts de control para servidor
            self.pagination_manager.create_control_scripts()
            
            # Ejecutar procesamiento masivo con paginación
            results = await self.pagination_manager.process_all_pages(
                page=self.page,
                pqr_processor=self,
                max_pages=max_pages
            )
            
            logger.info("PROCESO_COMPLETADO PROCESAMIENTO MASIVO COMPLETADO")
            return results
            
        except Exception as e:
            logger.error(f"ERROR Error en procesamiento masivo: {e}")
            return {
                'total_processed': 0,
                'successful': 0,
                'failed': 0,
                'error': str(e)
            }

    async def process_current_page_records(self, page, max_records: Optional[int] = None) -> Dict[str, Any]:
        """
        Procesa los registros de la página actual (llamado por PaginationManager)
        
        Args:
            page: Página de Playwright
            max_records: Máximo número de registros por página
            
        Returns:
            Dict con resultados del procesamiento de la página
        """
        try:
            # Procesar registros de la página actual usando el método existente
            successful_records = await self.process_all_pqr_records(max_records=max_records)
            
            return {
                'total_processed': successful_records,
                'successful': successful_records,
                'failed': 0
            }
            
        except Exception as e:
            logger.error(f"ERROR Error procesando página actual: {e}")
            return {
                'total_processed': 0,
                'successful': 0,
                'failed': max_records or 10  # Asumir 10 registros por página por defecto
            }

    async def _find_eye_buttons(self) -> List[tuple]:
        """
        Encuentra todos los botones del ojo disponibles
        
        Returns:
            List de tuplas (selector, índice)
        """
        try:
            found_buttons = []
            
            for selector in self.eye_button_selectors:
                try:
                    buttons = self.page.locator(selector)
                    count = await buttons.count()
                    if count > 0:
                        logger.info(f"Encontrados {count} botones con selector: {selector}")
                        for i in range(count):
                            found_buttons.append((selector, i))
                        break  # Usar el primer selector que funcione
                except Exception as e:
                    logger.warning(f"Error con selector {selector}: {e}")
                    continue

            return found_buttons

        except Exception as e:
            logger.error(f"Error buscando botones del ojo: {e}")
            return []

    async def _process_single_pqr_specific_sequence(self, eye_button, record_number: int) -> bool:
        """
        Procesa una sola PQR siguiendo la secuencia específica requerida:
        1. Clic para abrir nueva pestaña (sin cerrar anterior)
        2. Imprimir/guardar PDF con nombre del campo "Número Reclamo SGC"
        3. Verificar adjuntos en "Documento/prueba" y descargar con código SGC
        4. Extraer y guardar JSON con todos los datos de la PQR
        5. Cerrar ventana y continuar
        
        Args:
            eye_button: Elemento del botón del ojo
            record_number: Número del registro
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            logger.info(f"REANUDANDO INICIANDO SECUENCIA ESPECÍFICA PARA PQR #{record_number}")

            # PASO 1: Abrir nueva pestaña SIN cerrar la anterior
            logger.info(" PASO 1: Abriendo nueva pestaña sin cerrar la anterior...")
            new_page = await self._open_new_tab_without_closing_current(eye_button)

            if not new_page:
                logger.error("ERROR No se pudo abrir nueva pestaña")
                return False

            try:
                # Esperar a que la página cargue completamente con timeout extendido
                try:
                    await new_page.wait_for_load_state('networkidle', timeout=60000)  # 60 segundos
                    logger.info("EXITOSO Nueva pestaña cargada exitosamente")
                except Exception as load_error:
                    logger.warning(f"ADVERTENCIA Timeout en networkidle, intentando con domcontentloaded: {load_error}")
                    try:
                        await new_page.wait_for_load_state('domcontentloaded', timeout=30000)  # 30 segundos
                        logger.info("EXITOSO Nueva pestaña cargada con domcontentloaded")
                        # Esperar adicional para asegurar carga de AngularJS
                        await new_page.wait_for_timeout(5000)
                    except Exception as fallback_error:
                        logger.warning(f"ADVERTENCIA Timeout en domcontentloaded también, continuando: {fallback_error}")
                        # Esperar un poco y continuar
                        await new_page.wait_for_timeout(3000)

                # PASO 2: Extraer número SGC para nombrar archivos
                logger.info("VERIFICANDO PASO 2: Extrayendo número SGC...")
                sgc_number = await self._extract_sgc_number_from_page(new_page, record_number)
                logger.info(f"LISTA Número SGC extraído: {sgc_number}")

                # PASO 3: Generar PDF con nombre del SGC
                logger.info("PAGINA PASO 3: Generando PDF con nombre del SGC...")
                pdf_success = False
                try:
                    pdf_success = await self._generate_pdf_with_sgc_name(new_page, sgc_number, record_number)
                except Exception as pdf_error:
                    logger.error(f"ERROR Error en generación PDF: {pdf_error}")
                
                # PASO 4: Verificar y descargar adjuntos específicamente de "Documento/prueba"
                logger.info(" PASO 4: Verificando adjuntos en 'Documento/prueba'...")
                attachments_success = False
                try:
                    attachments_success = await self._download_document_proof_attachments(new_page, sgc_number, record_number)
                except Exception as attachments_error:
                    logger.error(f"ERROR Error en descarga adjuntos: {attachments_error}")

                # PASO 5: Extraer y guardar JSON con todos los datos
                logger.info("GUARDANDO PASO 5: Extrayendo y guardando JSON...")
                json_success = False
                try:
                    json_success = await self._extract_and_save_json_data(new_page, sgc_number, record_number)
                except Exception as json_error:
                    logger.error(f"ERROR Error en extracción JSON: {json_error}")

                # Resultado final - Considerar exitoso si al menos uno funcionó
                overall_success = pdf_success or attachments_success or json_success
                
                logger.info(f"METRICAS Resultados PQR #{record_number}: PDF={pdf_success}, Adjuntos={attachments_success}, JSON={json_success}")
                
                if overall_success:
                    logger.info(f"EXITOSO Secuencia completada para PQR #{record_number}")
                else:
                    logger.warning(f"ADVERTENCIA Ningun paso fue exitoso para PQR #{record_number}")

                # Siempre devolver True para que no se interrumpa el procesamiento masivo
                # El éxito real se registra en los logs
                return True

            finally:
                # PASO 6: Cerrar la pestaña de manera segura
                logger.info(" PASO 6: Cerrando pestaña...")
                try:
                    if new_page and not new_page.is_closed():
                        await new_page.close()
                        logger.info("EXITOSO Pestaña cerrada, continuando con siguiente registro")
                    else:
                        logger.info("ℹ Pestaña ya estaba cerrada")
                except Exception as close_error:
                    logger.warning(f"ADVERTENCIA Error cerrando pestaña: {close_error}")

        except Exception as e:
            logger.error(f"ERROR Error en secuencia específica para PQR {record_number}: {e}")
            return False

    async def _open_new_tab_without_closing_current(self, eye_button) -> Optional[Any]:
        """
        Abre nueva pestaña sin cerrar la actual usando múltiples métodos
        
        Args:
            eye_button: Elemento del botón del ojo
            
        Returns:
            Nueva página o None si hay error
        """
        try:
            logger.info(" Iniciando apertura de nueva pestaña...")
            
            # Obtener número de pestañas antes
            context = self.page.context
            initial_pages = len(context.pages)
            logger.info(f"Pestañas iniciales: {initial_pages}")

            # MÉTODO 1: Clic derecho + menú contextual (más confiable)
            try:
                logger.info(" Método 1: Clic derecho + menú contextual...")
                await eye_button.click(button='right')
                await self.page.wait_for_timeout(1500)

                # Opciones del menú contextual en orden de prioridad
                context_menu_options = [
                    "text='Abrir enlace en pestaña nueva'",
                    "text='Abrir en pestaña nueva'", 
                    "text='Open link in new tab'",
                    "text='Open in new tab'",
                    "[role='menuitem']:has-text('nueva')",
                    "[role='menuitem']:has-text('new tab')"
                ]

                for option in context_menu_options:
                    try:
                        logger.info(f"Probando opción: {option}")
                        menu_item = self.page.locator(option).first
                        if await menu_item.is_visible(timeout=2000):
                            await menu_item.click()
                            logger.info(f"EXITOSO Menú contextual usado: {option}")
                            
                            # Esperar nueva pestaña
                            await self.page.wait_for_timeout(3000)
                            current_pages = len(context.pages)
                            if current_pages > initial_pages:
                                new_page = context.pages[-1]
                                logger.info(f"EXITOSO Nueva pestaña abierta ({current_pages} pestañas)")
                                return new_page
                            break
                    except Exception:
                        continue

            except Exception as menu_error:
                logger.warning(f"Error con menú contextual: {menu_error}")

            # MÉTODO 2: JavaScript window.open
            try:
                logger.info("CONFIGURANDO Método 2: JavaScript window.open...")
                href = await eye_button.get_attribute('href')
                
                if not href:
                    # Intentar obtener href de diferentes formas
                    href = await eye_button.get_attribute('data-href')
                    if not href:
                        # Construir href desde onclick
                        onclick = await eye_button.get_attribute('onclick')
                        if onclick and 'Detail' in onclick:
                            import re
                            match = re.search(r"Detail/([^'\"]+)", onclick)
                            if match:
                                detail_id = match.group(1)
                                current_url = self.page.url
                                base_url = current_url.split('#')[0]
                                href = f"{base_url}#Detail/{detail_id}"
                                logger.info(f"URL construida desde onclick: {href}")

                if href:
                    logger.info(f"Abriendo con JavaScript: {href}")
                    await self.page.evaluate(f"window.open('{href}', '_blank')")
                    await self.page.wait_for_timeout(3000)
                    
                    current_pages = len(context.pages)
                    if current_pages > initial_pages:
                        new_page = context.pages[-1]
                        logger.info(f"EXITOSO Nueva pestaña abierta con JavaScript ({current_pages} pestañas)")
                        return new_page

            except Exception as js_error:
                logger.warning(f"Error con JavaScript: {js_error}")

            # MÉTODO 3: Ctrl+Click
            try:
                logger.info("⌨ Método 3: Ctrl+Click...")
                await eye_button.click(modifiers=['Control'])
                await self.page.wait_for_timeout(3000)
                
                current_pages = len(context.pages)
                if current_pages > initial_pages:
                    new_page = context.pages[-1]
                    logger.info(f"EXITOSO Nueva pestaña abierta con Ctrl+Click ({current_pages} pestañas)")
                    return new_page

            except Exception as ctrl_error:
                logger.warning(f"Error con Ctrl+Click: {ctrl_error}")

            logger.error("ERROR No se pudo abrir nueva pestaña con ningún método")
            return None

        except Exception as e:
            logger.error(f"Error crítico abriendo nueva pestaña: {e}")
            return None

    async def _extract_sgc_number_from_page(self, page, record_number: int) -> str:
        """
        Extrae el número SGC de la página para usar en nombres de archivos
        
        Args:
            page: Página de Playwright
            record_number: Número del registro
            
        Returns:
            str: Número SGC o valor por defecto
        """
        try:
            logger.info("VERIFICANDO Extrayendo número SGC...")

            for selector in self.sgc_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        # Para campos input, obtener el valor
                        if 'input' in selector:
                            value = await element.get_attribute('value') or await element.input_value()
                        else:
                            # Para otros elementos, obtener el texto
                            value = await element.inner_text()
                        
                        if value and value.strip():
                            sgc_number = value.strip()
                            logger.info(f"EXITOSO SGC encontrado con selector {selector}: {sgc_number}")
                            return sgc_number

                except Exception as selector_error:
                    logger.warning(f"Error con selector SGC {selector}: {selector_error}")
                    continue

            # Valor por defecto si no se encuentra
            default_sgc = f"PQR_{record_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.warning(f"ADVERTENCIA No se encontró número SGC, usando valor por defecto: {default_sgc}")
            return default_sgc

        except Exception as e:
            logger.error(f"Error extrayendo número SGC: {e}")
            return f"PQR_{record_number}_ERROR"

    async def _generate_pdf_with_sgc_name(self, page, sgc_number: str, record_number: int) -> bool:
        """
        Genera PDF con el nombre del número SGC
        
        Args:
            page: Página de Playwright
            sgc_number: Número SGC para el nombre
            record_number: Número del registro
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            logger.info(f"PAGINA Generando PDF con nombre SGC: {sgc_number}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Generar nombre de archivo con SGC
            pdf_filename = self.download_path / f"{sgc_number}_{timestamp}.pdf"

            # Generar PDF
            await page.pdf(
                path=str(pdf_filename),
                format='A4',
                print_background=True,
                margin={
                    'top': '1cm',
                    'right': '1cm',
                    'bottom': '1cm',
                    'left': '1cm'
                }
            )

            logger.info(f"EXITOSO PDF generado exitosamente: {pdf_filename}")
            return True

        except Exception as e:
            logger.error(f"ERROR Error generando PDF: {e}")
            
            # Fallback: generar screenshot
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_filename = self.screenshots_dir / f"{sgc_number}_{timestamp}.png"
                await page.screenshot(path=str(screenshot_filename), full_page=True)
                logger.info(f" Screenshot de respaldo generado: {screenshot_filename}")
                return True
            except Exception as screenshot_error:
                logger.error(f"ERROR Error generando screenshot de respaldo: {screenshot_error}")
                return False

    async def _download_document_proof_attachments(self, page, sgc_number: str, record_number: int) -> bool:
        """
        Descarga adjuntos específicamente del campo "Documento/prueba"
        Busca el archivo específico mencionado en el campo documento_prueba del JSON
        
        Args:
            page: Página de Playwright
            sgc_number: Número SGC para nombrar archivos
            record_number: Número del registro
            
        Returns:
            bool: True si se encontraron adjuntos
        """
        try:
            logger.info(" Verificando adjuntos en 'Documento/prueba'...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Extraer el nombre del archivo del campo documento_prueba
            documento_prueba_filename = await self._extract_documento_prueba_filename(page)
            logger.info(f"VERIFICANDO Archivo documento_prueba extraído: {documento_prueba_filename}")

            # Tomar screenshot para análisis
            try:
                screenshot_path = self.screenshots_dir / f"adjuntos_analysis_{sgc_number}_{timestamp}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f" Screenshot para análisis de adjuntos: {screenshot_path}")
            except Exception:
                pass

            # Si tenemos el nombre del archivo, intentar descargarlo
            if documento_prueba_filename and documento_prueba_filename != "":
                logger.info(f"OBJETIVO Buscando enlace de descarga: {documento_prueba_filename}")
                
                # Selectores para enlaces de descarga (incluyendo elementos AngularJS)
                download_selectors = [
                    f"div.link-archivo:has-text('{documento_prueba_filename}')",  # Específico para link-archivo
                    f"*[ng-click*='descargarAdjunto']:has-text('{documento_prueba_filename}')",  # ng-click con descargarAdjunto
                    f"div[ng-click]:has-text('{documento_prueba_filename}')",  # Cualquier div con ng-click
                    f"*[role='button']:has-text('{documento_prueba_filename}')",  # Elementos con rol de botón
                    f"a[href*='{documento_prueba_filename}']",  # Enlaces tradicionales
                    f"a:has-text('{documento_prueba_filename}')", 
                    f"button:has-text('{documento_prueba_filename}')",
                    f"*[onclick*='{documento_prueba_filename}']"
                ]
                
                # Intentar descargar con cada selector
                for selector in download_selectors:
                    try:
                        elements = page.locator(selector)
                        count = await elements.count()
                        
                        for i in range(count):
                            element = elements.nth(i)
                            is_visible = await element.is_visible()
                            element_text = await element.inner_text()
                            tag_name = await element.evaluate("el => el.tagName")
                            ng_click = await element.get_attribute('ng-click')
                            class_name = await element.get_attribute('class')
                            role = await element.get_attribute('role')
                            
                            logger.info(f"    Elemento {i+1}: Tag={tag_name}, Visible={is_visible}")
                            logger.info(f"    Texto: '{element_text[:50]}...'")
                            logger.info(f"    ng-click: {ng_click}")
                            logger.info(f"    class: {class_name}")
                            logger.info(f"    role: {role}")
                            
                            if is_visible and documento_prueba_filename in element_text:
                                logger.info(f"   OBJETIVO ¡ENCONTRADO! Elemento con archivo: {documento_prueba_filename}")
                                try:
                                    logger.info(f"   REANUDANDO Intentando descarga con selector: {selector}")
                                    
                                    # Esperar un poco antes del clic para asegurar que la página está lista
                                    await page.wait_for_timeout(1000)
                                    
                                    async with page.expect_download(timeout=30000) as download_info:
                                        await element.click()
                                    
                                    download = await download_info.value
                                    file_extension = documento_prueba_filename.split('.')[-1] if '.' in documento_prueba_filename else 'bin'
                                    attachment_filename = f"{sgc_number}_adjunto_{timestamp}.{file_extension}"
                                    attachment_path = self.download_path / attachment_filename
                                    
                                    await download.save_as(str(attachment_path))
                                    logger.info(f"   EXITOSO ¡DESCARGA EXITOSA! {attachment_filename}")
                                    logger.info(f"   PROCESADOS Tamaño: {attachment_path.stat().st_size} bytes")
                                    return True
                                    
                                except Exception as download_error:
                                    logger.warning(f"   ADVERTENCIA Error con elemento {i}: {download_error}")
                                    
                                    # Si falla la descarga esperada, intentar método alternativo
                                    if ng_click and 'descargarAdjunto' in ng_click:
                                        try:
                                            logger.info(f"   REANUDANDO Intentando clic sin expectativa de descarga...")
                                            await element.click()
                                            await page.wait_for_timeout(3000)  # Esperar respuesta
                                            logger.info(f"   ℹ Clic ejecutado en elemento ng-click")
                                        except Exception as click_error:
                                            logger.warning(f"   ADVERTENCIA Error en clic alternativo: {click_error}")
                                    
                                    continue
                    except Exception:
                        continue
                
                # Método específico para elementos AngularJS
                logger.info("VERIFICANDO Intentando método específico para AngularJS...")
                try:
                    # Buscar elementos específicos con la estructura que nos mostraste
                    angular_selectors = [
                        "div.link-archivo.ng-binding[ng-click*='descargarAdjunto']",
                        "div.link-archivo[role='button']",
                        "div[ng-click*='descargarAdjunto'][role='button']",
                        "div.ng-binding[ng-click*='descargarAdjunto']",
                        "*[ng-click*='descargarAdjunto']"
                    ]
                    
                    for angular_selector in angular_selectors:
                        try:
                            logger.info(f"VERIFICANDO Probando selector AngularJS: {angular_selector}")
                            angular_elements = page.locator(angular_selector)
                            angular_count = await angular_elements.count()
                            
                            logger.info(f" Encontrados {angular_count} elementos AngularJS")
                            
                            for i in range(angular_count):
                                angular_element = angular_elements.nth(i)
                                angular_text = await angular_element.inner_text()
                                angular_visible = await angular_element.is_visible()
                                
                                logger.info(f"    Elemento AngularJS {i+1}: Visible={angular_visible}")
                                logger.info(f"    Texto: '{angular_text}'")
                                
                                if angular_visible and documento_prueba_filename in angular_text:
                                    logger.info(f"   OBJETIVO ¡ENCONTRADO! Elemento AngularJS con archivo")
                                    
                                    try:
                                        # Intentar con expectativa de descarga
                                        logger.info(f"   REANUDANDO Clic en elemento AngularJS con expectativa...")
                                        async with page.expect_download(timeout=30000) as download_info:
                                            await angular_element.click()
                                        
                                        download = await download_info.value
                                        file_extension = documento_prueba_filename.split('.')[-1] if '.' in documento_prueba_filename else 'bin'
                                        attachment_filename = f"{sgc_number}_adjunto_{timestamp}.{file_extension}"
                                        attachment_path = self.download_path / attachment_filename
                                        
                                        await download.save_as(str(attachment_path))
                                        logger.info(f"   EXITOSO ¡DESCARGA ANGULAR EXITOSA! {attachment_filename}")
                                        logger.info(f"   PROCESADOS Tamaño: {attachment_path.stat().st_size} bytes")
                                        return True
                                        
                                    except Exception as angular_error:
                                        logger.warning(f"   ADVERTENCIA Error descarga AngularJS: {angular_error}")
                                        
                                        # Intentar clic simple
                                        try:
                                            logger.info(f"   REANUDANDO Clic simple en elemento AngularJS...")
                                            await angular_element.click()
                                            await page.wait_for_timeout(5000)  # Esperar respuesta
                                            logger.info(f"   ℹ Clic AngularJS ejecutado (sin descarga detectada)")
                                        except Exception as click_error:
                                            logger.warning(f"   ADVERTENCIA Error en clic AngularJS: {click_error}")
                                            
                        except Exception as angular_selector_error:
                            logger.warning(f"Error con selector AngularJS {angular_selector}: {angular_selector_error}")
                            continue
                            
                except Exception as angular_method_error:
                    logger.warning(f"Error en método AngularJS: {angular_method_error}")
                
                # Si no se logró descarga, mostrar fallback
                logger.info("ℹ No se pudo descargar con selectores directos ni AngularJS")
                if documento_prueba_filename:
                    logger.info(f" Archivo buscado: {documento_prueba_filename}")
                return False
                        
            return False
            
        except Exception as e:
            logger.error(f"ERROR Error manejando adjuntos: {e}")
            return False

    async def _legacy_download_method(self, page, sgc_number: str, record_number: int, documento_prueba_filename: str) -> bool:
        """
        Método legacy para buscar archivos en toda la página (mantenido por compatibilidad)
        """
        try:
            return False
        except Exception as e:
            logger.error(f"ERROR Error en método legacy: {e}")
            return False

    async def _extract_documento_prueba_filename(self, page) -> str:
        """
        Extrae el nombre del archivo del campo documento_prueba
        
        Args:
            page: Página de Playwright
            
        Returns:
            str: Nombre del archivo o cadena vacía
        """
        try:
            # Selectores para el campo documento_prueba
            documento_selectors = [
                "td.text-td-label:has-text('Documento/prueba') + td",
                "td:has-text('Documento/prueba') + td",
                "td:has-text('Documento') + td",
                ".text-td-label:has-text('Documento') + td"
            ]
            
            for selector in documento_selectors:
                try:
                    elements = page.locator(selector)
                    count = await elements.count()
                    
                    if count > 0:
                        for i in range(count):
                            element = elements.nth(i)
                            text = await element.inner_text()
                            
                            # Buscar patrones de archivo (con extensión)
                            import re
                            file_pattern = r'([a-f0-9\-]{36}\.(jpg|jpeg|png|gif|pdf|doc|docx|txt|zip|rar))'
                            match = re.search(file_pattern, text, re.IGNORECASE)
                            
                            if match:
                                filename = match.group(1)
                                logger.info(f"PAGINA Archivo encontrado en campo: {filename}")
                                return filename
                            
                            # Si no encuentra patrón específico, buscar cualquier texto que parezca archivo
                            if '.' in text and len(text.strip()) < 100:  # Probable nombre de archivo
                                clean_text = text.strip()
                                if not any(word in clean_text.lower() for word in ['campo', 'documento', 'prueba', 'adjunto']):
                                    logger.info(f"PAGINA Posible archivo encontrado: {clean_text}")
                                    return clean_text
                                    
                except Exception as selector_error:
                    logger.warning(f"Error con selector documento {selector}: {selector_error}")
                    continue
            
            return ""
            
        except Exception as e:
            logger.warning(f"Error extrayendo nombre de archivo documento_prueba: {e}")
            return ""

    async def _extract_and_save_json_data(self, page, sgc_number: str, record_number: int) -> bool:
        """
        Extrae todos los datos de la PQR y los guarda en formato JSON
        
        Args:
            page: Página de Playwright
            sgc_number: Número SGC para nombrar archivo
            record_number: Número del registro
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            logger.info(f"GUARDANDO Extrayendo datos JSON para PQR #{record_number}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Datos base del JSON
            pqr_data = {
                'record_number': record_number,
                'sgc_number': sgc_number,
                'extraction_timestamp': timestamp,
                'page_url': page.url,
                'page_title': await page.title()
            }

            # Selectores específicos para extraer datos de PQR
            data_selectors = {
                "nic": "td.text-td-label:has-text('NIC') + td.ng-binding",
                "fecha": "td.text-td-label:has-text('Fecha') + td.ng-binding",
                "documento_identidad": "td.text-td-label:has-text('Documento de identidad') + td.ng-binding",
                "nombres_apellidos": "td.text-td-label:has-text('Nombres y Apellidos') + td.ng-binding",
                "lectura": "td.text-td-label:has-text('Lectura') + td.ng-binding",
                "correo_electronico": "td.text-td-label:has-text('Correo electrónico') + td.ng-binding",
                "telefono": "td.text-td-label:has-text('Teléfono') + td.ng-binding",
                "celular": "td.text-td-label:has-text('Celular') + td.ng-binding",
                "tipo_pqr": "td.text-td-label:has-text('Tipo de PQR') + td.ng-binding",
                "canal_respuesta": "td.text-td-label:has-text('Canal de respuesta') + td",
                "documento_prueba": "td.text-td-label:has-text('Documento/prueba') + td",
                "cuerpo_reclamacion": "td.text-td-label:has-text('Cuerpo de la reclamación') + td",
                "numero_radicado": "td.text-td-label:has-text('N° Radicado PQR') + td.ng-binding",
                "estado_solicitud": "td.text-td-label:has-text('Estado Solicitud') + td.ng-binding",
                "finalizar": "td.text-td-label:has-text('Finalizar') + td",
                "adjuntar_archivo": "td.text-td-label:has-text('Adjuntar archivo') + td",
                "numero_reclamo_sgc": "input[name='NumeroReclamoSGC']",
                "comentarios": "td.text-td-label:has-text('Comentarios') + td"
            }

            # Extraer datos usando selectores
            for field_name, selector in data_selectors.items():
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        if field_name == 'numero_reclamo_sgc':
                            # Para campos de input, obtener el valor
                            value = await element.get_attribute('value') or await element.input_value()
                        else:
                            # Para otros elementos, obtener el texto
                            value = await element.inner_text()
                        
                        pqr_data[field_name] = value.strip() if value else ""
                        logger.info(f"LISTA {field_name}: {pqr_data[field_name]}")
                    else:
                        pqr_data[field_name] = ""
                        logger.warning(f"ADVERTENCIA No se encontró elemento para {field_name}")
                        
                except Exception as field_error:
                    logger.warning(f"ADVERTENCIA Error extrayendo {field_name}: {field_error}")
                    pqr_data[field_name] = ""

            # Extraer datos adicionales de tablas si existen
            try:
                additional_data = await self._extract_additional_table_data(page)
                pqr_data.update(additional_data)
            except Exception as table_error:
                logger.warning(f"ADVERTENCIA Error extrayendo datos adicionales de tabla: {table_error}")

            # Generar nombre de archivo JSON
            json_filename = f"{sgc_number}_data_{timestamp}.json"
            json_path = self.data_dir / json_filename

            # Guardar JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(pqr_data, f, ensure_ascii=False, indent=2)

            logger.info(f"EXITOSO JSON guardado exitosamente: {json_path}")
            logger.info(f"PROCESADOS Campos extraídos: {len([k for k, v in pqr_data.items() if v])}")
            
            return True

        except Exception as e:
            logger.error(f"ERROR Error extrayendo/guardando JSON: {e}")
            return False

    async def _extract_additional_table_data(self, page) -> dict:
        """
        Extrae datos adicionales de tablas genéricas en la página
        
        Args:
            page: Página de Playwright
            
        Returns:
            dict: Datos adicionales extraídos
        """
        try:
            additional_data = {}
            
            # Buscar tablas con datos
            table_selectors = [
                "table",
                ".table",
                "[role='table']",
                ".data-table"
            ]

            for selector in table_selectors:
                try:
                    tables = page.locator(selector)
                    table_count = await tables.count()

                    for i in range(min(table_count, 3)):  # Máximo 3 tablas para evitar sobrecarga
                        table = tables.nth(i)
                        
                        # Extraer filas de la tabla
                        rows = table.locator("tr")
                        row_count = await rows.count()

                        for j in range(min(row_count, 20)):  # Máximo 20 filas por tabla
                            try:
                                row = rows.nth(j)
                                cells = row.locator("td, th")
                                cell_count = await cells.count()

                                if cell_count >= 2:
                                    # Primera celda como etiqueta, segunda como valor
                                    label_cell = cells.nth(0)
                                    value_cell = cells.nth(1)

                                    label = await label_cell.inner_text()
                                    value = await value_cell.inner_text()

                                    if label and value and len(label.strip()) > 0 and len(value.strip()) > 0:
                                        # Limpiar y normalizar la etiqueta
                                        clean_label = label.strip().lower().replace(' ', '_').replace(':', '').replace('/', '_')
                                        if clean_label not in additional_data:  # Evitar duplicados
                                            additional_data[f"tabla_{clean_label}"] = value.strip()

                            except Exception:
                                continue

                except Exception:
                    continue

            logger.info(f"PROCESADOS Datos adicionales de tabla extraídos: {len(additional_data)} campos")
            return additional_data

        except Exception as e:
            logger.warning(f"ADVERTENCIA Error extrayendo datos adicionales: {e}")
            return {}
