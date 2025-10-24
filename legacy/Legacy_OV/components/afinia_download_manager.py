#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestor de descargas específico para Afinia
Basado en el código legacy funcional
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional, List
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger('AFINIA-DOWNLOAD')

class AfiniaDownloadManager:
    """
    Gestor de descargas específico para Afinia
    Implementa la lógica exacta del código legacy funcional
    """
    
    def __init__(self, page: Page, download_path: str):
        """
        Inicializa el gestor de descargas
        
        Args:
            page: Página de Playwright
            download_path: Ruta base para descargas
        """
        self.page = page
        self.download_path = download_path
        self.logger = logger
        
        # Crear directorio de descargas si no existe
        os.makedirs(download_path, exist_ok=True)
        
    async def execute_search_and_process(self) -> bool:
        """
        Ejecuta la búsqueda y procesa los resultados
        Basado en el código legacy funcional
        
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("=== EJECUTANDO BÚSQUEDA Y PROCESAMIENTO ===")
            
            # Paso 1: Ejecutar búsqueda
            search_success = await self._execute_search()
            if not search_success:
                self.logger.error("Error ejecutando búsqueda")
                return False
                
            # Paso 2: Procesar resultados
            process_success = await self._process_search_results()
            if not process_success:
                self.logger.error("Error procesando resultados")
                return False
                
            self.logger.info("EXITOSO Búsqueda y procesamiento completados exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR Error en búsqueda y procesamiento: {str(e)}")
            return False
            
    async def _execute_search(self) -> bool:
        """
        Ejecuta la búsqueda usando el botón de buscar
        Basado en los selectores del código legacy
        
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("Ejecutando búsqueda...")
            
            # Selectores exactos del código legacy funcional
            search_button_selectors = [
                "button[ng-click='Search()'][aria-label='Buscar']",
                "button.md-raised.md-primary:has-text('Buscar')",
                "button[aria-label='Buscar']",
                "button:has-text('Buscar')",
                "input[type='submit'][value*='Buscar']"
            ]
            
            search_button = None
            
            for i, selector in enumerate(search_button_selectors):
                try:
                    self.logger.info(f"Probando selector de búsqueda {i+1}: {selector}")
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        search_button = element
                        self.logger.info(f"EXITOSO Botón de búsqueda encontrado con selector: {selector}")
                        break
                except PlaywrightTimeoutError:
                    self.logger.info(f"Selector {selector} no encontrado")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error con selector {selector}: {e}")
                    continue
            
            if search_button:
                # Hacer clic en el botón de búsqueda
                await search_button.click()
                self.logger.info("EXITOSO Clic en botón de búsqueda ejecutado")
                
                # Esperar resultados (igual que en legacy)
                self.logger.info("ESPERANDO Esperando resultados...")
                await self.page.wait_for_load_state('networkidle', timeout=30000)
                await asyncio.sleep(3)
                
                return True
            else:
                self.logger.error("ERROR No se encontró botón de búsqueda")
                return False
                
        except Exception as e:
            self.logger.error(f"Error ejecutando búsqueda: {e}")
            return False
            
    async def _process_search_results(self) -> bool:
        """
        Procesa los resultados de la búsqueda
        Extrae datos de PQR de la tabla de resultados
        
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.logger.info("Procesando resultados de búsqueda...")
            
            # Verificar si hay resultados
            results_found = await self._check_for_results()
            if not results_found:
                self.logger.warning("No se encontraron resultados")
                return True  # No es un error, simplemente no hay datos
                
            # Extraer datos de la tabla
            extracted_data = await self._extract_table_data()
            
            if extracted_data:
                self.logger.info(f"EXITOSO Extraídos {len(extracted_data)} registros")
                
                # Guardar datos extraídos
                await self._save_extracted_data(extracted_data)
                return True
            else:
                self.logger.warning("No se pudieron extraer datos de la tabla")
                return False
                
        except Exception as e:
            self.logger.error(f"Error procesando resultados: {e}")
            return False
            
    async def _check_for_results(self) -> bool:
        """
        Verifica si hay resultados en la tabla
        
        Returns:
            bool: True si hay resultados
        """
        try:
            # Buscar tabla de resultados
            table_selectors = [
                "table",
                ".table",
                "[role='table']",
                "md-table",
                ".data-table"
            ]
            
            for selector in table_selectors:
                try:
                    table = await self.page.wait_for_selector(selector, timeout=5000)
                    if table:
                        # Verificar si hay filas de datos
                        rows = await table.query_selector_all("tr")
                        if len(rows) > 1:  # Más de 1 fila (header + datos)
                            self.logger.info(f"EXITOSO Tabla encontrada con {len(rows)} filas")
                            return True
                except:
                    continue
                    
            # Verificar mensajes de "sin resultados"
            no_results_selectors = [
                ":has-text('No se encontraron')",
                ":has-text('Sin resultados')",
                ":has-text('No hay datos')",
                ".no-data",
                ".empty-results"
            ]
            
            for selector in no_results_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element and await element.is_visible():
                        self.logger.info("Mensaje de 'sin resultados' encontrado")
                        return False
                except:
                    continue
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error verificando resultados: {e}")
            return False
            
    async def _extract_table_data(self) -> List[dict]:
        """
        Extrae datos de la tabla de resultados
        Basado en la estructura del código legacy
        
        Returns:
            List[dict]: Lista de registros extraídos
        """
        try:
            extracted_data = []
            
            # Buscar tabla
            table = await self.page.query_selector("table")
            if not table:
                self.logger.warning("No se encontró tabla de resultados")
                return []
                
            # Obtener filas de datos (excluyendo header)
            rows = await table.query_selector_all("tr")
            if len(rows) <= 1:
                self.logger.warning("No hay filas de datos en la tabla")
                return []
                
            # Procesar cada fila (empezar desde índice 1 para saltar header)
            for i, row in enumerate(rows[1:], 1):
                try:
                    cells = await row.query_selector_all("td")
                    cell_count = len(cells)
                    
                    if cell_count >= 10:  # Verificar estructura según legacy
                        # Mapeo basado en la estructura del código legacy:
                        # 0: Número radicado, 1: Fecha, 2: Estado, 3: Tipo PQR, 4: NIC, 
                        # 5: Nombres, 6: Teléfono, 7: Celular, 8: Correo, 9: Documento, 10: Canal
                        pqr_data = {
                            'numero_radicado': await cells[0].inner_text() if len(cells) > 0 else '',
                            'fecha': await cells[1].inner_text() if len(cells) > 1 else '',
                            'estado_solicitud': await cells[2].inner_text() if len(cells) > 2 else '',
                            'tipo_pqr': await cells[3].inner_text() if len(cells) > 3 else '',
                            'nic': await cells[4].inner_text() if len(cells) > 4 else '',
                            'nombres_apellidos': await cells[5].inner_text() if len(cells) > 5 else '',
                            'telefono': await cells[6].inner_text() if len(cells) > 6 else '',
                            'celular': await cells[7].inner_text() if len(cells) > 7 else '',
                            'correo_electronico': await cells[8].inner_text() if len(cells) > 8 else '',
                            'documento_identidad': await cells[9].inner_text() if len(cells) > 9 else '',
                            'canal_respuesta': await cells[10].inner_text() if len(cells) > 10 else ''
                        }
                        
                        # Limpiar datos
                        for key, value in pqr_data.items():
                            pqr_data[key] = value.strip() if value else ''
                            
                        extracted_data.append(pqr_data)
                        self.logger.info(f"Registro {i} extraído: {pqr_data['numero_radicado']}")
                        
                    else:
                        self.logger.warning(f"Fila {i} tiene {cell_count} columnas, esperadas >= 10")
                        
                except Exception as row_error:
                    self.logger.error(f"Error procesando fila {i}: {row_error}")
                    continue
                    
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Error extrayendo datos de tabla: {e}")
            return []
            
    async def _save_extracted_data(self, data: List[dict]) -> bool:
        """
        Guarda los datos extraídos en archivo JSON
        
        Args:
            data: Lista de registros extraídos
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            import json
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"afinia_pqr_data_{timestamp}.json"
            filepath = os.path.join(self.download_path, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"EXITOSO Datos guardados en: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando datos: {e}")
            return False
