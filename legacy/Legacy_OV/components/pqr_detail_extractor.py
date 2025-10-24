"""
Extractor de detalles de PQR - Versión Modular
Maneja apertura de pestañas, extracción de datos, generación de PDFs y manejo de adjuntos
"""

import asyncio
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

# Configurar logger específico para este módulo
logger = logging.getLogger('pqr_detail_extractor')

# Configurar el logger solo si no tiene handlers
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[PQR-EXTRACTOR] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

class PQRDetailExtractor:
    """
    Extractor de detalles de PQR - Versión Modular
    Maneja apertura de pestañas, extracción de datos, generación de PDFs y manejo de adjuntos
    """

    def __init__(self, page, download_path: str, screenshots_dir: str):
        """
        Inicializa el extractor de detalles PQR

        Args:
            page: Página de Playwright
            download_path: Directorio base para descargas
            screenshots_dir: Directorio para screenshots
        """
        self.page = page
        self.download_path = Path(download_path) / "processed"  # Guardar PDFs en subcarpeta processed
        self.screenshots_dir = Path(screenshots_dir)
        self.data_dir = Path(download_path) / "processed"  # Guardar JSONs en subcarpeta processed

        # Crear directorios si no existen
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Configurar selectores para extracción de datos
        self.data_selectors = {
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

        # Configurar selectores para adjuntos
        self.attachment_selectors = [
            "a[href*='download']",
            "a[href*='archivo']",
            "a[href*='documento']",
            "td.text-td-label:has-text('Documento/prueba') + td a",
            "td.text-td-label:has-text('Adjuntar archivo') + td a"
        ]

        logger.info("PQRDetailExtractor inicializado correctamente")

    async def process_pqr_records(self, max_records: Optional[int] = None) -> int:
        """
        Procesa registros PQR usando la lógica original
        
        Args:
            max_records: Número máximo de registros a procesar
            
        Returns:
            int: Número de registros procesados exitosamente
        """
        try:
            logger.info("=== INICIANDO PROCESAMIENTO DE PQR (LÓGICA ORIGINAL) ===")

            # Buscar botones del ojo usando múltiples selectores
            eye_selectors = [
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
                ".btn:has(.fa-eye)",
                "button.view-btn",
                "a.view-btn"
            ]

            found_buttons = []
            for selector in eye_selectors:
                try:
                    buttons = self.page.locator(selector)
                    count = await buttons.count()
                    if count > 0:
                        logger.info(f"Encontrados {count} botones con selector: {selector}")
                        max_to_process = min(count, max_records) if max_records else count
                        for i in range(max_to_process):
                            found_buttons.append((selector, i))
                        break
                except Exception as e:
                    logger.warning(f"Error con selector {selector}: {e}")
                    continue

            if not found_buttons:
                logger.error("No se encontraron botones del ojo")
                return 0

            logger.info(f"Total de botones encontrados para procesar: {len(found_buttons)}")

            # Procesar cada botón encontrado
            successful_records = 0
            for idx, (selector, button_idx) in enumerate(found_buttons, 1):
                try:
                    logger.info(f"=== Procesando PQR #{idx} ===")

                    # Obtener el botón específico
                    button = self.page.locator(selector).nth(button_idx)

                    # Procesar la PQR
                    pqr_data = await self._process_single_pqr(button, idx)

                    if pqr_data:
                        successful_records += 1
                        logger.info(f"PQR #{idx} procesada exitosamente")
                    else:
                        logger.warning(f"No se pudo procesar PQR #{idx}")

                    # Pausa entre procesamiento
                    await self.page.wait_for_timeout(2000)

                except Exception as record_error:
                    logger.error(f"Error procesando PQR #{idx}: {record_error}")
                    continue

            logger.info(f"Procesados {successful_records} registros de PQR exitosamente")
            return successful_records

        except Exception as e:
            logger.error(f"Error en process_pqr_records: {e}")
            return 0

    async def _process_single_pqr(self, eye_button, record_number: int) -> Optional[Dict[str, Any]]:
        """
        Procesa una sola PQR abriendo nueva pestaña y extrayendo datos
        
        Args:
            eye_button: Elemento del botón del ojo
            record_number: Número del registro
            
        Returns:
            Dict con datos extraídos o None si hay error
        """
        try:
            logger.info(f"Abriendo detalle de PQR #{record_number}")

            # Abrir en nueva pestaña
            new_page = await self._open_in_new_tab(eye_button)

            if new_page:
                try:
                    # Extraer datos de la PQR
                    pqr_data = await self._extract_pqr_data(new_page, record_number)

                    # Obtener número SGC para nombrar archivos
                    sgc_number = pqr_data.get('numero_reclamo_sgc', f'PQR_{record_number}')
                    attachments_found = await self._handle_attachments(new_page, sgc_number, record_number)

                    # Generar PDF
                    pdf_path = await self._generate_pdf_report(new_page, sgc_number, record_number)

                    return pqr_data

                finally:
                    # Cerrar la pestaña
                    new_page.close()
                    logger.info("Pestaña cerrada después del procesamiento")
            else:
                logger.warning(f"No se pudo abrir nueva pestaña para PQR {record_number}")
                return None

        except Exception as e:
            logger.error(f"Error procesando PQR {record_number}: {e}")
            return None

    async def _open_in_new_tab(self, eye_button) -> Optional[Any]:
        """
        Abre el enlace del botón del ojo en una nueva pestaña
        Implementa la lógica original de apertura de pestañas
        
        Args:
            eye_button: Elemento del botón del ojo
            
        Returns:
            Nueva página o None si hay error
        """
        try:
            logger.info("=== Iniciando apertura de nueva pestaña (lógica original) ===")

            # Intentar clic derecho para menú contextual
            try:
                logger.info("Ejecutando clic derecho en botón de ojo...")
                await eye_button.click(button='right')
                await self.page.wait_for_timeout(1000)  # Usar wait_for_timeout como en original
                logger.info("Clic derecho ejecutado exitosamente")

                # Buscar opciones del menú contextual
                context_menu_options = [
                    "text='Abrir en pestaña nueva'",
                    "text='Open in new tab'",
                    "text='Abrir enlace en pestaña nueva'",
                    "[data-action='open-new-tab']"
                ]

                new_tab_opened = False
                for option in context_menu_options:
                    try:
                        logger.info(f"Buscando opción de menú: {option}")
                        menu_item = self.page.locator(option).first
                        if await menu_item.is_visible():
                            await menu_item.click()
                            new_tab_opened = True
                            logger.info(f"Clic en menú contextual: {option}")
                            break
                    except Exception as menu_error:
                        logger.warning(f"Error con opción {option}: {menu_error}")
                        continue

                if not new_tab_opened:
                    logger.warning("No se pudo hacer clic en menú contextual, usando fallback...")
                    # Fallback: usar JavaScript para abrir nueva pestaña
                    href = await eye_button.get_attribute('href') or await eye_button.get_attribute('data-href')
                    if href:
                        logger.info(f"Usando JavaScript para abrir: {href}")
                        await self.page.evaluate(f"window.open('{href}', '_blank')")
                        logger.info("Nueva pestaña abierta con JavaScript")
                    else:
                        logger.warning("No se pudo obtener href para abrir nueva pestaña")
                        return None

            except Exception as click_error:
                logger.warning(f"Error con clic derecho: {click_error}")
                # Fallback: clic normal
                try:
                    await eye_button.click()
                    logger.info("Clic normal ejecutado como fallback")
                except Exception as fallback_error:
                    logger.error(f"Error en fallback de clic: {fallback_error}")
                    return None

            # Esperar a que se abra la nueva pestaña
            await self.page.wait_for_timeout(3000)

            # Obtener la nueva pestaña
            context = self.page.context
            pages = context.pages

            if len(pages) > 1:
                # Tomar la última pestaña (la más reciente)
                new_page = pages[-1]
                logger.info("Nueva pestaña detectada, cambiando a ella...")

                # Esperar a que la página cargue
                try:
                    await new_page.wait_for_load_state('networkidle', timeout=15000)
                    logger.info("Nueva página cargada completamente")
                except Exception as load_error:
                    logger.warning(f"Error esperando carga: {load_error}")

                return new_page
            else:
                logger.warning("No se detectó nueva pestaña")
                return None

        except Exception as e:
            logger.error(f"Error crítico abriendo nueva pestaña: {e}")
            return None

    def _build_full_url(self, href: str) -> Optional[str]:
        """
        Construye URL completa a partir de href relativo
        
        Args:
            href: URL relativa o completa
            
        Returns:
            URL completa o None si hay error
        """
        try:
            if not href:
                return None

            # Si ya es URL completa, devolverla
            if href.startswith('http'):
                return href

            # Obtener URL base de la página actual
            current_url = self.page.url
            base_url = '/'.join(current_url.split('/')[:3])  # protocolo + dominio

            # Construir URL completa
            if href.startswith('/'):
                full_url = base_url + href
            else:
                full_url = base_url + '/' + href

            logger.info(f"URL construida: {full_url}")
            return full_url

        except Exception as e:
            logger.error(f"Error construyendo URL: {e}")
            return None

    def _validate_detail_url(self, url: str) -> bool:
        """
        Valida si la URL es de una página de detalle válida
        
        Args:
            url: URL a validar
            
        Returns:
            bool: True si es válida
        """
        try:
            if not url:
                return False

            # Patrones que indican páginas de detalle válidas
            valid_patterns = [
                '#Detail/',
                '/Detail/',
                'detail',
                'pqr',
                'reclamo'
            ]

            # Patrones que indican páginas de error
            invalid_patterns = [
                '404',
                'error',
                'not-found',
                'azure',
                'custom domain'
            ]

            url_lower = url.lower()

            # Verificar patrones inválidos
            for pattern in invalid_patterns:
                if pattern in url_lower:
                    logger.warning(f"URL inválida detectada (patrón: {pattern}): {url}")
                    return False

            # Verificar patrones válidos
            for pattern in valid_patterns:
                if pattern.lower() in url_lower:
                    logger.info(f"URL válida confirmada (patrón: {pattern}): {url}")
                    return True

            # Si no coincide con ningún patrón, asumir válida
            logger.info(f"URL sin patrón específico, asumiendo válida: {url}")
            return True

        except Exception as e:
            logger.warning(f"Error validando URL: {e}")
            return True  # Asumir válida si hay error

    async def _verify_navigation_success(self) -> bool:
        """
        Verifica si la navegación fue exitosa
        
        Returns:
            bool: True si la navegación fue exitosa
        """
        try:
            # Esperar un poco para que la página cargue
            await self.page.wait_for_timeout(2000)

            # Obtener información de la página
            current_url = self.page.url
            page_title = await self.page.title()
            
            logger.info(f"URL actual: {current_url}")
            logger.info(f"Título de página: {page_title}")

            # Verificar si es página de error
            page_content = await self.page.content()
            error_indicators = [
                "404 web site not found",
                "404 not found",
                "page not found",
                "site not found",
                "custom domain has not been configured",
                "azure"
            ]

            content_lower = page_content.lower()
            title_lower = page_title.lower()

            for indicator in error_indicators:
                if indicator in content_lower or indicator in title_lower:
                    logger.error(f"Página de error detectada: {indicator}")
                    return False

            # Verificar si hay contenido de PQR
            pqr_indicators = [
                "nic",
                "reclamo",
                "pqr",
                "documento de identidad",
                "nombres y apellidos"
            ]

            has_pqr_content = False
            for indicator in pqr_indicators:
                if indicator in content_lower:
                    has_pqr_content = True
                    break

            if has_pqr_content:
                logger.info("Contenido de PQR detectado en la página")
                return True
            else:
                logger.warning("No se detectó contenido de PQR en la página")
                return False

        except Exception as e:
            logger.error(f"Error verificando navegación: {e}")
            return False

    async def _extract_pqr_data(self, page, record_number: int) -> Dict[str, Any]:
        """
        Extrae datos de la PQR de la página
        
        Args:
            page: Página de Playwright
            record_number: Número del registro
            
        Returns:
            Dict con datos extraídos
        """
        try:
            logger.info(f"Extrayendo datos de PQR #{record_number}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Datos base
            pqr_data = {
                'record_number': record_number,
                'extraction_timestamp': timestamp,
                'page_url': page.url,
                'page_title': await page.title()
            }

            # Verificar si es página de detalle válida
            if not await self._is_detail_page(page):
                logger.warning("La página no parece ser una página de detalle de PQR")
                # Intentar extraer datos de tabla si existe
                table_data = await self._extract_table_data(page)
                pqr_data.update(table_data)
                return pqr_data

            # Extraer datos usando selectores específicos
            for field_name, selector in self.data_selectors.items():
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
                        logger.info(f"{field_name}: {pqr_data[field_name]}")
                    else:
                        pqr_data[field_name] = ""
                        logger.warning(f"No se encontró elemento para {field_name}")
                except Exception as field_error:
                    logger.warning(f"Error extrayendo {field_name}: {field_error}")
                    pqr_data[field_name] = ""

            # Guardar datos en archivo JSON
            await self._save_pqr_data(pqr_data, record_number)

            return pqr_data

        except Exception as e:
            logger.error(f"Error extrayendo datos: {e}")
            return {
                'record_number': record_number,
                'extraction_timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'error': str(e)
            }

    async def _is_detail_page(self, page) -> bool:
        """
        Verifica si la página actual es una página de detalle de PQR
        
        Args:
            page: Página a verificar
            
        Returns:
            bool: True si es página de detalle
        """
        try:
            # Verificar URL
            url = page.url.lower()
            if 'detail' in url or '#detail' in url:
                return True

            # Verificar contenido específico de PQR
            content_indicators = [
                "td.text-td-label:has-text('NIC')",
                "td.text-td-label:has-text('Documento de identidad')",
                "td.text-td-label:has-text('Nombres y Apellidos')",
                "input[name='NumeroReclamoSGC']"
            ]

            for indicator in content_indicators:
                element = page.locator(indicator).first
                if await element.count() > 0:
                    logger.info(f"Página de detalle confirmada por: {indicator}")
                    return True

            return False

        except Exception as e:
            logger.warning(f"Error verificando página de detalle: {e}")
            return False

    async def _extract_table_data(self, page) -> Dict[str, str]:
        """
        Extrae datos de tablas genéricas cuando no se encuentra estructura específica
        
        Args:
            page: Página de Playwright
            
        Returns:
            Dict con datos extraídos de tablas
        """
        try:
            logger.info("Extrayendo datos de tablas genéricas")
            table_data = {}

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

                    for i in range(table_count):
                        table = tables.nth(i)
                        
                        # Extraer filas de la tabla
                        rows = table.locator("tr")
                        row_count = await rows.count()

                        for j in range(row_count):
                            row = rows.nth(j)
                            cells = row.locator("td, th")
                            cell_count = await cells.count()

                            if cell_count >= 2:
                                # Asumir que la primera celda es etiqueta y la segunda es valor
                                label_cell = cells.nth(0)
                                value_cell = cells.nth(1)

                                label = await label_cell.inner_text()
                                value = await value_cell.inner_text()

                                if label and value:
                                    # Limpiar y normalizar la etiqueta
                                    clean_label = label.strip().lower().replace(' ', '_').replace(':', '')
                                    table_data[clean_label] = value.strip()

                except Exception as table_error:
                    logger.warning(f"Error procesando tabla con selector {selector}: {table_error}")
                    continue

            logger.info(f"Datos extraídos de tablas: {len(table_data)} campos")
            return table_data

        except Exception as e:
            logger.error(f"Error extrayendo datos de tablas: {e}")
            return {}

    async def _handle_attachments(self, page, sgc_number: str, record_number: int) -> bool:
        """
        Maneja la descarga de adjuntos de la PQR
        
        Args:
            page: Página de Playwright
            sgc_number: Número SGC de la PQR
            record_number: Número del registro
            
        Returns:
            bool: True si se encontraron adjuntos
        """
        try:
            logger.info(f"Verificando adjuntos para PQR #{record_number}")
            attachments_found = False
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for selector in self.attachment_selectors:
                try:
                    attachments = page.locator(selector)
                    count = await attachments.count()

                    if count > 0:
                        logger.info(f"Encontrados {count} adjuntos con selector: {selector}")

                        for i in range(count):
                            try:
                                attachment = attachments.nth(i)
                                href = await attachment.get_attribute('href')
                                text = await attachment.inner_text()

                                if href and text:
                                    logger.info(f"Adjunto encontrado: {text} -> {href}")

                                    # Intentar descargar el adjunto
                                    try:
                                        # Configurar descarga
                                        async with page.expect_download() as download_info:
                                            await attachment.click()

                                        download = await download_info.value
                                        
                                        # Generar nombre de archivo
                                        original_name = download.suggested_filename or f"adjunto_{i+1}"
                                        file_extension = original_name.split('.')[-1] if '.' in original_name else 'pdf'
                                        attachment_filename = f"{sgc_number}_{text.replace(' ', '_')}_{timestamp}.{file_extension}"
                                        attachment_path = self.download_path / attachment_filename

                                        # Guardar archivo
                                        await download.save_as(attachment_path)
                                        logger.info(f"Adjunto descargado: {attachment_path}")
                                        attachments_found = True

                                    except Exception as download_error:
                                        logger.warning(f"Error descargando adjunto: {download_error}")
                                        # Marcar como encontrado aunque no se haya descargado
                                        attachments_found = True

                            except Exception as att_error:
                                logger.warning(f"Error procesando adjunto {i}: {att_error}")
                                continue

                        # Si encontramos adjuntos con este selector, no probar otros
                        if attachments_found:
                            break

                except Exception as selector_error:
                    logger.warning(f"Error con selector de adjuntos {selector}: {selector_error}")
                    continue

            if not attachments_found:
                logger.info("No se encontraron adjuntos para descargar")

            return attachments_found

        except Exception as e:
            logger.error(f"Error manejando adjuntos: {e}")
            return False

    async def _generate_pdf_report(self, page, sgc_number: str, record_number: int) -> Optional[str]:
        """
        Genera un reporte PDF de la página de PQR
        
        Args:
            page: Página de Playwright
            sgc_number: Número SGC de la PQR
            record_number: Número del registro
            
        Returns:
            str: Ruta del PDF generado o None si hay error
        """
        try:
            logger.info(f"Generando PDF para PQR #{record_number}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Generar nombre de archivo
            pdf_filename = self.download_path / f"{sgc_number}_PQR_{record_number}_{timestamp}.pdf"

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

            logger.info(f"PDF generado exitosamente: {pdf_filename}")
            return str(pdf_filename)

        except Exception as e:
            logger.error(f"Error generando PDF: {e}")
            
            # Fallback: generar screenshot
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_filename = self.screenshots_dir / f"{sgc_number}_PQR_{record_number}_{timestamp}.png"
                await page.screenshot(path=str(screenshot_filename), full_page=True)
                logger.info(f"Screenshot de respaldo generado: {screenshot_filename}")
                return str(screenshot_filename)
            except Exception as screenshot_error:
                logger.error(f"Error generando screenshot de respaldo: {screenshot_error}")
                return None

    async def _save_pqr_data(self, pqr_data: Dict[str, Any], record_number: int) -> bool:
        """
        Guarda los datos de PQR en archivo JSON
        
        Args:
            pqr_data: Datos de la PQR
            record_number: Número del registro
            
        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sgc_number = pqr_data.get('numero_reclamo_sgc', f'PQR_{record_number}')
            
            # Generar nombre de archivo
            json_filename = f"pqr_data_{sgc_number}_{timestamp}.json"
            json_path = self.data_dir / json_filename

            # Guardar datos
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(pqr_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Datos de PQR guardados en: {json_path}")
            return True

        except Exception as e:
            logger.error(f"Error guardando datos de PQR: {e}")
            return False