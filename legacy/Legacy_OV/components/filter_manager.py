#!/usr/bin/env python3
"""
FilterManager - Componente especializado para gestión de filtros
================================================================

Este módulo proporciona herramientas avanzadas para manejar filtros complejos
en extractores de diferentes plataformas, permitiendo configurar filtros de
reportes de manera centralizada y reutilizable.

Características principales:
- Gestión centralizada de filtros de reportes
- Soporte para múltiples tipos de filtros (dropdown, checkbox, texto, etc.)
- Detección automática de elementos de filtro
- Configuración dinámica de opciones
- Validación de selecciones
- Manejo de dependencias entre filtros

Autor: ExtractorOV Team
Fecha: 2025-09-26
"""

import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import re
import time
import os
from datetime import datetime
from playwright.async_api import Page, ElementHandle
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class FilterType(Enum):
    """Tipos de filtros soportados"""
    DROPDOWN = "dropdown"
    MULTI_SELECT = "multi_select" 
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    TEXT_INPUT = "text_input"
    DATE_RANGE = "date_range"
    CUSTOM = "custom"

class FilterOperator(Enum):
    """Operadores para filtros de texto"""
    EQUALS = "equals"
    CONTAINS = "contains" 
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"

@dataclass
class FilterOption:
    """Opción individual de un filtro"""
    value: str
    text: str
    selected: bool = False
    disabled: bool = False

    def __str__(self):
        status = "[EMOJI_REMOVIDO]" if self.selected else "[EMOJI_REMOVIDO]"
        return f"{status} {self.text} ({self.value})"

@dataclass 
class FilterConfig:
    """Configuración de un filtro específico"""
    name: str
    filter_type: FilterType
    selector: str
    label: str = ""
    options: List[FilterOption] = None
    value: Any = None
    required: bool = False
    depends_on: List[str] = None # Otros filtros de los que depende

    def __post_init__(self):
        if self.options is None:
            self.options = []
        if self.depends_on is None:
            self.depends_on = []

class FilterManager:
    """
    Gestor centralizado de filtros para extractores web
    
    Proporciona funcionalidades para descubrir, configurar y aplicar
    filtros de manera automática en páginas web complejas.
    
    Args:
        page: Instancia de página de Playwright
    """
    
    def __init__(self, page: Page):
        self.page = page
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.filters = {} # Diccionario de filtros configurados
        self.applied_filters = {} # Filtros actualmente aplicados
        
        # Selectores comunes para diferentes tipos de filtros
        self.filter_selectors = {
            'dropdown': [
                'select',
                '.dropdown',
                '[role="combobox"]',
                '.select-wrapper select',
                '.form-control select'
            ],
            'multi_select': [
                'select[multiple]',
                '.multi-select',
                '[role="listbox"]'
            ],
            'checkbox': [
                'input[type="checkbox"]',
                '.checkbox',
                '.form-check-input'
            ],
            'radio': [
                'input[type="radio"]',
                '.radio',
                '.form-radio'
            ],
            'text_input': [
                'input[type="text"]',
                'input[type="search"]',
                '.form-control',
                '.filter-input'
            ]
        }
        
        # Filtros comunes por nombre/id
        self.common_filters = {
            'empresa': ['#empresa', '#company', '[name="empresa"]', '.empresa-select'],
            'tipo_documento': ['#tipoDocumento', '#documentType', '[name="tipo_documento"]'],
            'estado': ['#estado', '#status', '[name="estado"]', '.estado-select'],
            'fecha_desde': ['#fechaDesde', '#dateFrom', '[name="fecha_desde"]'],
            'fecha_hasta': ['#fechaHasta', '#dateTo', '[name="fecha_hasta"]'],
            'categoria': ['#categoria', '#category', '[name="categoria"]'],
            'departamento': ['#departamento', '#department', '[name="departamento"]'],
            'municipio': ['#municipio', '#municipality', '[name="municipio"]'],
            'buscar': ['#buscar', '#search', '[name="buscar"]', '.search-input']
        }

    def register_filter(self, filter_config: FilterConfig) -> bool:
        """
        Registra un nuevo filtro en el gestor
        
        Args:
            filter_config: Configuración del filtro
            
        Returns:
            bool: True si se registró exitosamente
        """
        try:
            self.filters[filter_config.name] = filter_config
            self.logger.info(f"Filtro registrado: {filter_config.name} ({filter_config.filter_type.value})")
            return True
        except Exception as e:
            self.logger.error(f"Error registrando filtro {filter_config.name}: {e}")
            return False

    async def discover_filters(self, container_selector: str = "body") -> List[FilterConfig]:
        """
        Descubre automáticamente filtros en la página
        
        Args:
            container_selector: Selector del contenedor donde buscar filtros
            
        Returns:
            List[FilterConfig]: Lista de filtros descubiertos
        """
        if not self.page:
            raise ValueError("No hay página disponible para descubrir filtros")
            
        discovered_filters = []
        
        try:
            # Buscar elementos select (dropdowns)
            selects = await self.page.query_selector_all(f"{container_selector} select")
            for select in selects:
                filter_config = await self._analyze_select_element(select)
                if filter_config:
                    discovered_filters.append(filter_config)
            
            # Buscar grupos de checkboxes
            checkbox_groups = await self._find_checkbox_groups(container_selector)
            for group_config in checkbox_groups:
                discovered_filters.append(group_config)
            
            # Buscar inputs de texto que parezcan filtros
            text_inputs = await self.page.query_selector_all(f"{container_selector} input[type='text'], {container_selector} input[type='search']")
            for input_elem in text_inputs:
                filter_config = await self._analyze_text_input(input_elem)
                if filter_config:
                    discovered_filters.append(filter_config)
                    
            self.logger.info(f"Descubiertos {len(discovered_filters)} filtros automáticamente")
            
            # Registrar filtros descubiertos
            for filter_config in discovered_filters:
                self.register_filter(filter_config)
                
            return discovered_filters
            
        except Exception as e:
            self.logger.error(f"Error descubriendo filtros: {e}")
            return []

    async def _analyze_select_element(self, select_element: ElementHandle) -> Optional[FilterConfig]:
        """Analiza un elemento select para crear configuración de filtro"""
        try:
            # Obtener atributos del elemento
            id_attr = await select_element.get_attribute('id') or ''
            name_attr = await select_element.get_attribute('name') or ''
            class_attr = await select_element.get_attribute('class') or ''
            multiple = await select_element.get_attribute('multiple') is not None
            
            # Determinar nombre del filtro
            filter_name = id_attr or name_attr or f"select_{hash(class_attr) % 1000}"
            
            # Obtener label
            label = await self._get_element_label(select_element)
            
            # Obtener opciones
            options = await self._get_select_options(select_element)
            
            # Determinar tipo de filtro
            filter_type = FilterType.MULTI_SELECT if multiple else FilterType.DROPDOWN
            
            # Construir selector
            if id_attr:
                selector = f"#{id_attr}"
            elif name_attr:
                selector = f"[name='{name_attr}']"
            else:
                selector = f"select.{class_attr.split()[0]}" if class_attr else "select"
                
            return FilterConfig(
                name=filter_name,
                filter_type=filter_type,
                selector=selector,
                label=label or filter_name,
                options=options
            )
            
        except Exception as e:
            self.logger.error(f"Error analizando elemento select: {e}")
            return None

    async def _get_select_options(self, select_element: ElementHandle) -> List[FilterOption]:
        """Obtiene las opciones de un elemento select"""
        options = []
        try:
            option_elements = await select_element.query_selector_all('option')
            
            for option_elem in option_elements:
                value = await option_elem.get_attribute('value') or ''
                text = await option_elem.inner_text()
                selected = await option_elem.get_attribute('selected') is not None
                disabled = await option_elem.get_attribute('disabled') is not None
                
                # Filtrar opciones vacías o de placeholder
                if value and text.strip() and not text.lower().startswith(('seleccione', 'choose', 'select')):
                    options.append(FilterOption(
                        value=value,
                        text=text.strip(),
                        selected=selected,
                        disabled=disabled
                    ))
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo opciones de select: {e}")
            
        return options

    async def _find_checkbox_groups(self, container_selector: str) -> List[FilterConfig]:
        """Encuentra grupos de checkboxes relacionados"""
        groups = []
        
        try:
            checkboxes = await self.page.query_selector_all(f"{container_selector} input[type='checkbox']")
            
            # Agrupar checkboxes por nombre
            checkbox_groups = {}
            
            for checkbox in checkboxes:
                name = await checkbox.get_attribute('name')
                if name:
                    if name not in checkbox_groups:
                        checkbox_groups[name] = []
                    checkbox_groups[name].append(checkbox)
            
            # Crear configuraciones para grupos con múltiples opciones
            for group_name, group_checkboxes in checkbox_groups.items():
                if len(group_checkboxes) > 1: # Solo grupos con múltiples opciones
                    options = []
                    
                    for checkbox in group_checkboxes:
                        value = await checkbox.get_attribute('value') or ''
                        label = await self._get_checkbox_label(checkbox)
                        checked = await checkbox.is_checked()
                        
                        if value and label:
                            options.append(FilterOption(
                                value=value,
                                text=label,
                                selected=checked
                            ))
                    
                    if options:
                        filter_config = FilterConfig(
                            name=group_name,
                            filter_type=FilterType.CHECKBOX,
                            selector=f"input[name='{group_name}']",
                            label=group_name.replace('_', ' ').title(),
                            options=options
                        )
                        groups.append(filter_config)
                        
        except Exception as e:
            self.logger.error(f"Error encontrando grupos de checkboxes: {e}")
            
        return groups

    async def _get_checkbox_label(self, checkbox_element: ElementHandle) -> str:
        """Obtiene el label de un checkbox"""
        try:
            # Método 1: Label con 'for' attribute
            checkbox_id = await checkbox_element.get_attribute('id')
            if checkbox_id:
                label_elem = await self.page.query_selector(f"label[for='{checkbox_id}']")
                if label_elem:
                    return await label_elem.inner_text()
            
            # Método 2: Label padre
            parent = await checkbox_element.query_selector('xpath=..')
            if parent:
                parent_tag = await parent.evaluate('el => el.tagName.toLowerCase()')
                if parent_tag == 'label':
                    text = await parent.inner_text()
                    return text.strip()
            
            # Método 3: Texto siguiente
            following_text = await checkbox_element.evaluate('''
                el => {
                    let next = el.nextSibling;
                    while (next && next.nodeType !== 3) {
                        next = next.nextSibling;
                    }
                    return next ? next.textContent.trim() : '';
                }
            ''')
            
            if following_text:
                return following_text
                
            return ""
            
        except Exception as e:
            self.logger.error(f"Error obteniendo label de checkbox: {e}")
            return ""

    async def _analyze_text_input(self, input_element: ElementHandle) -> Optional[FilterConfig]:
        """Analiza un input de texto para determinar si es un filtro"""
        try:
            id_attr = await input_element.get_attribute('id') or ''
            name_attr = await input_element.get_attribute('name') or ''
            placeholder = await input_element.get_attribute('placeholder') or ''
            class_attr = await input_element.get_attribute('class') or ''
            
            # Determinar si parece ser un filtro basándose en atributos
            filter_keywords = ['filter', 'search', 'buscar', 'filtro', 'find', 'lookup']
            
            is_filter = any(keyword in attr.lower() for attr in [id_attr, name_attr, placeholder, class_attr] for keyword in filter_keywords)
            
            if is_filter:
                filter_name = id_attr or name_attr or f"text_filter_{hash(placeholder) % 1000}"
                label = await self._get_element_label(input_element) or placeholder or filter_name
                
                selector = f"#{id_attr}" if id_attr else f"[name='{name_attr}']" if name_attr else f"input[placeholder='{placeholder}']"
                
                return FilterConfig(
                    name=filter_name,
                    filter_type=FilterType.TEXT_INPUT,
                    selector=selector,
                    label=label
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error analizando input de texto: {e}")
            return None

    async def _get_element_label(self, element: ElementHandle) -> str:
        """Obtiene el label asociado a cualquier elemento"""
        try:
            # Método 1: Label con 'for' attribute
            elem_id = await element.get_attribute('id')
            if elem_id:
                label_elem = await self.page.query_selector(f"label[for='{elem_id}']")
                if label_elem:
                    return await label_elem.inner_text()
            
            # Método 2: Label padre
            parent = await element.query_selector('xpath=..')
            if parent:
                parent_tag = await parent.evaluate('el => el.tagName.toLowerCase()')
                if parent_tag == 'label':
                    return await parent.inner_text()
            
            # Método 3: Buscar label previo
            prev_label = await element.evaluate('''
                el => {
                    let prev = el.previousElementSibling;
                    while (prev) {
                        if (prev.tagName.toLowerCase() === 'label') {
                            return prev.textContent.trim();
                        }
                        prev = prev.previousElementSibling;
                    }
                    return '';
                }
            ''')
            
            if prev_label:
                return prev_label
                
            return ""
            
        except Exception as e:
            self.logger.error(f"Error obteniendo label de elemento: {e}")
            return ""

    async def apply_filter(self, filter_name: str, value: Any, operator: FilterOperator = FilterOperator.EQUALS) -> bool:
        """
        Aplica un filtro específico

        Args:
            filter_name: Nombre del filtro a aplicar
            value: Valor a aplicar
            operator: Operador para filtros de texto

        Returns:
            bool: True si se aplicó exitosamente
        """
        if filter_name not in self.filters:
            self.logger.error(f"Filtro no registrado: {filter_name}")
            return False
            
        filter_config = self.filters[filter_name]
        
        try:
            success = False
            
            if filter_config.filter_type == FilterType.DROPDOWN:
                success = await self._apply_dropdown_filter(filter_config, value)
            elif filter_config.filter_type == FilterType.MULTI_SELECT:
                success = await self._apply_multiselect_filter(filter_config, value)
            elif filter_config.filter_type == FilterType.CHECKBOX:
                success = await self._apply_checkbox_filter(filter_config, value)
            elif filter_config.filter_type == FilterType.TEXT_INPUT:
                success = await self._apply_text_filter(filter_config, value, operator)
            else:
                self.logger.warning(f"Tipo de filtro no implementado: {filter_config.filter_type}")
                return False
                
            if success:
                self.applied_filters[filter_name] = {
                    'value': value,
                    'operator': operator,
                    'timestamp': asyncio.get_event_loop().time()
                }
                self.logger.info(f"Filtro aplicado exitosamente: {filter_name} = {value}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error aplicando filtro {filter_name}: {e}")
            return False

    async def _apply_dropdown_filter(self, filter_config: FilterConfig, value: str) -> bool:
        """Aplica un filtro de tipo dropdown/select"""
        try:
            select_element = await self.page.query_selector(filter_config.selector)
            if not select_element:
                self.logger.error(f"No se encontró elemento select: {filter_config.selector}")
                return False
                
            # Intentar seleccionar por valor
            try:
                await select_element.select_option(value=value)
                await self.page.wait_for_timeout(500) # Esperar a que se procese
                return True
            except:
                pass
                
            # Intentar seleccionar por texto
            try:
                await select_element.select_option(label=value)
                await self.page.wait_for_timeout(500)
                return True
            except:
                pass
                
            # Buscar opción que contenga el valor
            options = await select_element.query_selector_all('option')
            for option in options:
                option_text = await option.inner_text()
                option_value = await option.get_attribute('value')
                
                if value.lower() in option_text.lower() or value.lower() in (option_value or '').lower():
                    await select_element.select_option(value=option_value)
                    await self.page.wait_for_timeout(500)
                    return True
                    
            self.logger.error(f"No se encontró opción '{value}' en dropdown {filter_config.name}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error aplicando filtro dropdown: {e}")
            return False

    async def _apply_multiselect_filter(self, filter_config: FilterConfig, values: List[str]) -> bool:
        """Aplica un filtro de tipo multi-select"""
        try:
            if not isinstance(values, list):
                values = [values]
                
            select_element = await self.page.query_selector(filter_config.selector)
            if not select_element:
                return False
                
            # Limpiar selecciones previas
            await select_element.select_option([])
            
            # Seleccionar múltiples valores
            selected_values = []
            options = await select_element.query_selector_all('option')
            
            for option in options:
                option_text = await option.inner_text()
                option_value = await option.get_attribute('value')
                
                for target_value in values:
                    if (target_value.lower() in option_text.lower() or 
                        target_value.lower() in (option_value or '').lower()):
                        selected_values.append(option_value)
                        break
                        
            if selected_values:
                await select_element.select_option(selected_values)
                await self.page.wait_for_timeout(500)
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error aplicando filtro multiselect: {e}")
            return False

    async def _apply_checkbox_filter(self, filter_config: FilterConfig, values: Union[str, List[str]]) -> bool:
        """Aplica un filtro de tipo checkbox"""
        try:
            if not isinstance(values, list):
                values = [values]
                
            checkboxes = await self.page.query_selector_all(filter_config.selector)
            success_count = 0
            
            for checkbox in checkboxes:
                checkbox_value = await checkbox.get_attribute('value')
                should_check = checkbox_value in values
                is_checked = await checkbox.is_checked()
                
                if should_check != is_checked:
                    await checkbox.click()
                    success_count += 1
                    
            await self.page.wait_for_timeout(300)
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error aplicando filtro checkbox: {e}")
            return False

    async def _apply_text_filter(self, filter_config: FilterConfig, value: str, operator: FilterOperator) -> bool:
        """Aplica un filtro de tipo texto"""
        try:
            input_element = await self.page.query_selector(filter_config.selector)
            if not input_element:
                return False
                
            # Limpiar campo y escribir nuevo valor
            await input_element.click()
            await input_element.fill('')
            await input_element.type(value)
            
            # Presionar Enter para aplicar filtro
            await input_element.press('Enter')
            await self.page.wait_for_timeout(500)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error aplicando filtro de texto: {e}")
            return False

    async def clear_filter(self, filter_name: str) -> bool:
        """
        Limpia un filtro específico
        
        Args:
            filter_name: Nombre del filtro a limpiar
            
        Returns:
            bool: True si se limpió exitosamente
        """
        if filter_name not in self.filters:
            return False
            
        filter_config = self.filters[filter_name]
        
        try:
            if filter_config.filter_type == FilterType.DROPDOWN:
                select_element = await self.page.query_selector(filter_config.selector)
                if select_element:
                    await select_element.select_option('')
                    
            elif filter_config.filter_type == FilterType.MULTI_SELECT:
                select_element = await self.page.query_selector(filter_config.selector)
                if select_element:
                    await select_element.select_option([])
                    
            elif filter_config.filter_type == FilterType.CHECKBOX:
                checkboxes = await self.page.query_selector_all(filter_config.selector)
                for checkbox in checkboxes:
                    if await checkbox.is_checked():
                        await checkbox.click()
                        
            elif filter_config.filter_type == FilterType.TEXT_INPUT:
                input_element = await self.page.query_selector(filter_config.selector)
                if input_element:
                    await input_element.fill('')
                    
            # Remover de filtros aplicados
            if filter_name in self.applied_filters:
                del self.applied_filters[filter_name]
                
            self.logger.info(f"Filtro limpiado: {filter_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error limpiando filtro {filter_name}: {e}")
            return False

    async def clear_all_filters(self) -> bool:
        """
        Limpia todos los filtros aplicados
        
        Returns:
            bool: True si se limpiaron todos exitosamente
        """
        try:
            success_count = 0
            for filter_name in list(self.applied_filters.keys()):
                if await self.clear_filter(filter_name):
                    success_count += 1
                    
            self.logger.info(f"Limpiados {success_count} filtros")
            return success_count == len(self.applied_filters)
            
        except Exception as e:
            self.logger.error(f"Error limpiando todos los filtros: {e}")
            return False

    def get_applied_filters(self) -> Dict[str, Any]:
        """
        Obtiene información de filtros actualmente aplicados
        
        Returns:
            Dict: Diccionario con filtros aplicados y sus valores
        """
        return self.applied_filters.copy()

    def get_filter_config(self, filter_name: str) -> Optional[FilterConfig]:
        """
        Obtiene la configuración de un filtro específico
        
        Args:
            filter_name: Nombre del filtro
            
        Returns:
            FilterConfig: Configuración del filtro o None si no existe
        """
        return self.filters.get(filter_name)

    def list_available_filters(self) -> List[str]:
        """
        Lista todos los filtros disponibles
        
        Returns:
            List[str]: Lista de nombres de filtros disponibles
        """
        return list(self.filters.keys())

    async def wait_for_filter_results(self, timeout: int = 10000) -> bool:
        """
        Espera a que se carguen los resultados después de aplicar filtros
        
        Args:
            timeout: Tiempo máximo de espera en milisegundos
            
        Returns:
            bool: True si se detectaron cambios en la página
        """
        try:
            # Esperar a que desaparezcan indicadores de carga
            loading_selectors = [
                '.loading',
                '.spinner',
                '[data-loading="true"]',
                '.fa-spinner',
                '.loader'
            ]
            
            for selector in loading_selectors:
                try:
                    await self.page.wait_for_selector(selector, state='hidden', timeout=timeout)
                except:
                    continue
                    
            # Esperar un poco más para asegurar que se carguen los datos
            await self.page.wait_for_timeout(1000)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error esperando resultados de filtros: {e}")
            return False

    async def validate_filter_application(self, filter_name: str, expected_value: Any) -> bool:
        """
        Valida que un filtro se haya aplicado correctamente
        
        Args:
            filter_name: Nombre del filtro a validar
            expected_value: Valor esperado
            
        Returns:
            bool: True si el filtro está aplicado correctamente
        """
        if filter_name not in self.filters:
            return False
            
        filter_config = self.filters[filter_name]
        
        try:
            if filter_config.filter_type == FilterType.DROPDOWN:
                select_element = await self.page.query_selector(filter_config.selector)
                if select_element:
                    current_value = await select_element.input_value()
                    return current_value == expected_value
                    
            elif filter_config.filter_type == FilterType.TEXT_INPUT:
                input_element = await self.page.query_selector(filter_config.selector)
                if input_element:
                    current_value = await input_element.input_value()
                    return current_value == expected_value
                    
            # Para otros tipos de filtros, verificar en applied_filters
            return (filter_name in self.applied_filters and 
                    self.applied_filters[filter_name]['value'] == expected_value)
                    
        except Exception as e:
            self.logger.error(f"Error validando filtro {filter_name}: {e}")
            return False

    def __str__(self) -> str:
        """Representación en string del FilterManager"""
        return f"FilterManager(filters={len(self.filters)}, applied={len(self.applied_filters)})"
