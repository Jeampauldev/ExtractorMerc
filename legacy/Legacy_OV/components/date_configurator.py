"""
Configurador de fechas para automatización web
Maneja diferentes tipos de calendarios y formatos de fecha
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum
import re
from playwright.async_api import Page, ElementHandle

logger = logging.getLogger(__name__)

class DateFormat(Enum):
    """Formatos de fecha soportados"""
    DD_MM_YYYY = "dd/mm/yyyy"
    MM_DD_YYYY = "mm/dd/yyyy"
    YYYY_MM_DD = "yyyy-mm-dd"
    DD_MM_YY = "dd/mm/yy"
    YYYY_DD_MM = "yyyy-dd-mm"
    ISO_FORMAT = "iso"
    TIMESTAMP = "timestamp"

class CalendarType(Enum):
    """Tipos de calendario detectados"""
    INPUT_DATE = "input_date"
    DROPDOWN = "dropdown"
    CALENDAR_PICKER = "calendar_picker"
    CUSTOM_WIDGET = "custom_widget"
    DUAL_INPUT = "dual_input"

@dataclass
class DateRange:
    """Clase para representar un rango de fechas"""
    start_date: date
    end_date: date
    format: DateFormat = DateFormat.DD_MM_YYYY

    def __post_init__(self):
        """Validar el rango de fechas"""
        if self.start_date > self.end_date:
            raise ValueError(f"Fecha inicial ({self.start_date}) no puede ser posterior a fecha final ({self.end_date})")

    def to_string(self, format_type: DateFormat = None) -> Tuple[str, str]:
        """Convierte el rango a strings en el formato especificado"""
        fmt = format_type or self.format

        format_map = {
            DateFormat.DD_MM_YYYY: "%d/%m/%Y",
            DateFormat.MM_DD_YYYY: "%m/%d/%Y",
            DateFormat.YYYY_MM_DD: "%Y-%m-%d",
            DateFormat.DD_MM_YY: "%d/%m/%y",
            DateFormat.YYYY_DD_MM: "%Y-%d-%m",
            DateFormat.ISO_FORMAT: "%Y-%m-%d",
            DateFormat.TIMESTAMP: "%s"
        }

        format_str = format_map.get(fmt, "%d/%m/%Y")

        if fmt == DateFormat.TIMESTAMP:
            start_str = str(int(datetime.combine(self.start_date, datetime.min.time()).timestamp()))
            end_str = str(int(datetime.combine(self.end_date, datetime.min.time()).timestamp()))
        else:
            start_str = self.start_date.strftime(format_str)
            end_str = self.end_date.strftime(format_str)

        return start_str, end_str

    def get_days_count(self) -> int:
        """Obtiene el número de días en el rango"""
        return (self.end_date - self.start_date).days + 1

class DateConfigurator:
    """
    Configurador principal para manejo de fechas en páginas web
    Detecta automáticamente el tipo de calendario y aplica las fechas correspondientes
    """
    
    def __init__(self, page: Page = None, default_format: DateFormat = DateFormat.DD_MM_YYYY):
        """
        Inicializa el configurador de fechas
        
        Args:
            page: Página de Playwright para interactuar
            default_format: Formato de fecha por defecto
        """
        self.page = page
        self.default_format = default_format
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Selectores comunes para diferentes tipos de campos de fecha
        self.date_selectors = {
            'input_date': [
                'input[type="date"]',
                'input[id*="date"]',
                'input[name*="date"]',
                'input[class*="date"]'
            ],
            'start_date': [
                'input[id*="start"]',
                'input[id*="inicio"]',
                'input[id*="desde"]',
                'input[name*="start"]',
                'input[name*="from"]',
                '.date-start input',
                '.fecha-inicio input'
            ],
            'end_date': [
                'input[id*="end"]',
                'input[id*="fin"]',
                'input[id*="hasta"]',
                'input[name*="end"]',
                'input[name*="to"]',
                '.date-end input',
                '.fecha-fin input'
            ],
            'calendar_trigger': [
                'button[class*="calendar"]',
                '.calendar-trigger',
                '.date-picker-trigger',
                'i[class*="calendar"]'
            ]
        }

    def create_date_range(self, 
                         start_date: Union[str, date, datetime] = None,
                         end_date: Union[str, date, datetime] = None,
                         days_back: int = None,
                         format_type: DateFormat = None) -> DateRange:
        """
        Crea un rango de fechas basado en los parámetros proporcionados
        
        Args:
            start_date: Fecha de inicio (string, date o datetime)
            end_date: Fecha de fin (string, date o datetime)
            days_back: Número de días hacia atrás desde hoy
            format_type: Formato de fecha a usar
            
        Returns:
            DateRange: Objeto con el rango de fechas configurado
        """
        fmt = format_type or self.default_format

        try:
            # Opción 1: Usar days_back para crear rango desde X días atrás hasta hoy
            if days_back is not None:
                end_dt = date.today()
                start_dt = end_dt - timedelta(days=days_back)

                self.logger.info(f"Creando rango de {days_back} días: {start_dt} a {end_dt}")
                return DateRange(start_dt, end_dt, fmt)

            # Opción 2: Usar fechas específicas de inicio y fin
            if start_date and end_date:
                start_dt = self._parse_date(start_date)
                end_dt = self._parse_date(end_date)

                self.logger.info(f"Creando rango específico: {start_dt} a {end_dt}")
                return DateRange(start_dt, end_dt, fmt)

            # Opción 3: Solo fecha de inicio, fin será hoy
            if start_date:
                start_dt = self._parse_date(start_date)
                end_dt = date.today()

                self.logger.info(f"Creando rango desde {start_dt} hasta hoy")
                return DateRange(start_dt, end_dt, fmt)

            # Opción 4: Rango por defecto (últimos 30 días)
            end_dt = date.today()
            start_dt = end_dt - timedelta(days=30)

            self.logger.info(f"Creando rango por defecto (30 días): {start_dt} a {end_dt}")
            return DateRange(start_dt, end_dt, fmt)

        except Exception as e:
            self.logger.error(f"Error creando rango de fechas: {e}")
            raise ValueError(f"No se pudo crear el rango de fechas: {e}")

    def _parse_date(self, date_input: Union[str, date, datetime]) -> date:
        """
        Parsea diferentes tipos de entrada de fecha a objeto date
        
        Args:
            date_input: Entrada de fecha en varios formatos
            
        Returns:
            date: Objeto date parseado
        """
        if isinstance(date_input, date):
            return date_input
        elif isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, str):
            # Intentar varios formatos comunes
            formats = [
                "%Y-%m-%d",  # 2025-01-15
                "%d/%m/%Y",  # 15/01/2025
                "%m/%d/%Y",  # 01/15/2025
                "%d-%m-%Y",  # 15-01-2025
                "%Y%m%d",    # 20250115
                "%d/%m/%y",  # 15/01/25
                "%m/%d/%y",  # 01/15/25
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_input.strip(), fmt).date()
                except ValueError:
                    continue

            raise ValueError(f"No se pudo parsear la fecha: {date_input}")
        else:
            raise ValueError(f"Tipo de fecha no soportado: {type(date_input)}")

    async def detect_calendar_type(self) -> CalendarType:
        """
        Detecta automáticamente el tipo de calendario en la página
        
        Returns:
            CalendarType: Tipo de calendario detectado
        """
        if not self.page:
            raise ValueError("No hay página disponible para detección")

        try:
            # Detectar inputs de tipo date (HTML5)
            date_inputs = await self.page.query_selector_all('input[type="date"]')
            if date_inputs:
                self.logger.info("Detectado: INPUT_DATE")
                return CalendarType.INPUT_DATE

            # Detectar dropdowns de fecha (selects para día/mes/año)
            selects = await self.page.query_selector_all('select[id*="date"], select[id*="month"], select[id*="year"]')
            if len(selects) >= 2:
                self.logger.info("Detectado: DROPDOWN")
                return CalendarType.DROPDOWN

            # Detectar widgets de calendario
            calendar_widgets = await self.page.query_selector_all('.calendar, .datepicker, .date-picker, [class*="calendar"]')
            if calendar_widgets:
                self.logger.info("Detectado: CALENDAR_PICKER")
                return CalendarType.CALENDAR_PICKER

            # Detectar inputs duales (inicio y fin separados)
            start_inputs = []
            end_inputs = []
            for selector in self.date_selectors['start_date']:
                elements = await self.page.query_selector_all(selector)
                start_inputs.extend(elements)

            for selector in self.date_selectors['end_date']:
                elements = await self.page.query_selector_all(selector)
                end_inputs.extend(elements)

            if start_inputs and end_inputs:
                self.logger.info("Detectado: DUAL_INPUT")
                return CalendarType.DUAL_INPUT

            # Por defecto, asumir widget personalizado
            self.logger.info("Detectado: CUSTOM_WIDGET (por defecto)")
            return CalendarType.CUSTOM_WIDGET

        except Exception as e:
            self.logger.error(f"Error detectando tipo de calendario: {e}")
            return CalendarType.CUSTOM_WIDGET

    async def configure_date_range(self, 
                                 date_range: DateRange,
                                 selectors: Dict[str, str] = None,
                                 calendar_type: CalendarType = None) -> bool:
        """
        Configura el rango de fechas en la página web
        
        Args:
            date_range: Rango de fechas a configurar
            selectors: Selectores personalizados para los campos
            calendar_type: Tipo de calendario (se detecta automáticamente si no se especifica)
            
        Returns:
            bool: True si la configuración fue exitosa
        """
        if not self.page:
            raise ValueError("No hay página disponible para configuración")

        try:
            # Detectar tipo de calendario si no se especifica
            if calendar_type is None:
                calendar_type = await self.detect_calendar_type()

            self.logger.info(f"Configurando fechas con tipo: {calendar_type}")

            # Obtener strings de fecha en el formato apropiado
            start_str, end_str = date_range.to_string()

            # Aplicar configuración según el tipo detectado
            if calendar_type == CalendarType.INPUT_DATE:
                return await self._configure_input_date(date_range, selectors)
            elif calendar_type == CalendarType.DROPDOWN:
                return await self._configure_dropdown_date(date_range, selectors)
            elif calendar_type == CalendarType.DUAL_INPUT:
                return await self._configure_dual_input_date(date_range, selectors)
            elif calendar_type == CalendarType.CALENDAR_PICKER:
                return await self._configure_calendar_picker(date_range, selectors)
            else:  # CUSTOM_WIDGET
                return await self._configure_custom_widget(date_range, selectors)
                
        except Exception as e:
            self.logger.error(f"Error configurando rango de fechas: {e}")
            return False

    async def _configure_input_date(self, date_range: DateRange, selectors: Dict[str, str] = None) -> bool:
        """Configura fechas en inputs HTML5 de tipo date"""
        try:
            # Para inputs HTML5, usar formato ISO
            iso_range = DateRange(date_range.start_date, date_range.end_date, DateFormat.ISO_FORMAT)
            start_str, end_str = iso_range.to_string()

            # Buscar campos de fecha
            if selectors and 'start_date' in selectors:
                start_input = await self.page.query_selector(selectors['start_date'])
            else:
                start_input = await self._find_start_date_input()

            if selectors and 'end_date' in selectors:
                end_input = await self.page.query_selector(selectors['end_date'])
            else:
                end_input = await self._find_end_date_input()

            # Llenar campos
            if start_input:
                await start_input.fill(start_str)
                await self.page.wait_for_timeout(500)
                self.logger.info(f"Fecha de inicio configurada: {start_str}")

            # Llenar campo de fin
            if end_input:
                await end_input.fill(end_str)
                await self.page.wait_for_timeout(500)
                self.logger.info(f"Fecha de fin configurada: {end_str}")

            return start_input is not None and end_input is not None

        except Exception as e:
            self.logger.error(f"Error en configuración INPUT_DATE: {e}")
            return False

    async def _configure_dual_input_date(self, date_range: DateRange, selectors: Dict[str, str] = None) -> bool:
        """Configura fechas en campos de entrada duales (inicio y fin separados)"""
        try:
            start_str, end_str = date_range.to_string()

            # Buscar campos específicos
            start_input = None
            end_input = None

            if selectors:
                if 'start_date' in selectors:
                    start_input = await self.page.query_selector(selectors['start_date'])
                if 'end_date' in selectors:
                    end_input = await self.page.query_selector(selectors['end_date'])

            if not start_input:
                start_input = await self._find_start_date_input()
            if not end_input:
                end_input = await self._find_end_date_input()

            # Llenar campos
            success = True

            if start_input:
                await start_input.click()
                await start_input.fill(start_str)
                await self.page.keyboard.press("Tab")
                self.logger.info(f"Campo inicio llenado: {start_str}")
            else:
                success = False

            if end_input:
                await end_input.click()
                await end_input.fill(end_str)
                await self.page.keyboard.press("Tab")
                self.logger.info(f"Campo fin llenado: {end_str}")
            else:
                success = False

            return success

        except Exception as e:
            self.logger.error(f"Error en configuración DUAL_INPUT: {e}")
            return False

    async def _configure_dropdown_date(self, date_range: DateRange, selectors: Dict[str, str] = None) -> bool:
        """Configura fechas en dropdowns (selects)"""
        try:
            # TODO: Implementar lógica para dropdowns de fecha
            # Esto requiere detectar y llenar selects de día, mes y año
            self.logger.warning("Configuración de DROPDOWN no implementada completamente")
            return False

        except Exception as e:
            self.logger.error(f"Error en configuración DROPDOWN: {e}")
            return False

    async def _configure_calendar_picker(self, date_range: DateRange, selectors: Dict[str, str] = None) -> bool:
        """Configura fechas en widgets de calendario (date pickers)"""
        try:
            # TODO: Implementar lógica para widgets de calendario
            # Esto requiere hacer clic en el calendario y navegar por las fechas
            self.logger.warning("Configuración de CALENDAR_PICKER no implementada completamente")
            return False

        except Exception as e:
            self.logger.error(f"Error en configuración CALENDAR_PICKER: {e}")
            return False

    async def _configure_custom_widget(self, date_range: DateRange, selectors: Dict[str, str] = None) -> bool:
        """Configuración genérica para widgets personalizados"""
        try:
            # Estrategia genérica: buscar cualquier input que parezca de fecha
            start_str, end_str = date_range.to_string()

            # Buscar inputs genéricos de fecha
            date_inputs = await self.page.query_selector_all('input[id*="date"], input[name*="date"], input[placeholder*="date"]')

            if len(date_inputs) >= 2:
                await date_inputs[0].fill(start_str)
                await date_inputs[1].fill(end_str)
                self.logger.info(f"Configuración genérica aplicada: {start_str} - {end_str}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error en configuración CUSTOM_WIDGET: {e}")
            return False

    async def _find_start_date_input(self) -> Optional[ElementHandle]:
        """Busca el campo de fecha de inicio"""
        for selector in self.date_selectors['start_date']:
            element = await self.page.query_selector(selector)
            if element:
                return element
        return None

    async def _find_end_date_input(self) -> Optional[ElementHandle]:
        """Busca el campo de fecha de fin"""
        for selector in self.date_selectors['end_date']:
            element = await self.page.query_selector(selector)
            if element:
                return element
        return None

    def validate_date_range(self, 
                           start_date: Union[str, date], 
                           end_date: Union[str, date],
                           max_days: int = None,
                           allow_future: bool = False) -> bool:
        """
        Valida un rango de fechas
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            max_days: Máximo número de días permitidos en el rango
            allow_future: Si se permiten fechas futuras
            
        Returns:
            bool: True si el rango es válido
        """
        try:
            start_dt = self._parse_date(start_date)
            end_dt = self._parse_date(end_date)

            # Validar orden de fechas
            if start_dt > end_dt:
                self.logger.error(f"Fecha de inicio ({start_dt}) posterior a fecha de fin ({end_dt})")
                return False

            # Validar fechas futuras si no están permitidas
            today = date.today()
            if start_dt > today or end_dt > today:
                self.logger.error(f"No se permiten fechas futuras")
                return False

            # Validar máximo de días
            if max_days:
                days_diff = (end_dt - start_dt).days + 1
                if days_diff > max_days:
                    self.logger.error(f"Rango de {days_diff} días excede el máximo permitido ({max_days})")
                    return False

            self.logger.info(f"Rango de fechas válido: {start_dt} a {end_dt}")
            return True

        except Exception as e:
            self.logger.error(f"Error validando rango de fechas: {e}")
            return False

    def get_preset_ranges(self) -> Dict[str, DateRange]:
        """
        Obtiene rangos de fechas predefinidos comunes
        
        Returns:
            Dict[str, DateRange]: Diccionario con rangos predefinidos
        """
        today = date.today()

        presets = {
            'hoy': DateRange(today, today, self.default_format),
            'ayer': DateRange(today - timedelta(days=1), today - timedelta(days=1), self.default_format),
            'ultima_semana': DateRange(today - timedelta(days=7), today, self.default_format),
            'ultimo_mes': DateRange(today - timedelta(days=30), today, self.default_format),
            'ultimos_3_meses': DateRange(today - timedelta(days=90), today, self.default_format),
            'mes_actual': DateRange(today.replace(day=1), today, self.default_format),
            'mes_anterior': self._get_previous_month_range()
        }

        return presets

    def _get_previous_month_range(self) -> DateRange:
        """Obtiene el rango del mes anterior completo"""
        today = date.today()
        
        # Primer día del mes actual
        first_current = today.replace(day=1)
        
        # Último día del mes anterior
        last_previous = first_current - timedelta(days=1)
        
        # Primer día del mes anterior
        first_previous = last_previous.replace(day=1)

        return DateRange(first_previous, last_previous, self.default_format)

    def set_page(self, page: Page):
        """Configura la página de Playwright"""
        self.page = page
        self.logger.info("Página de Playwright configurada")

# Funciones de utilidad
def create_quick_range(days_back: int, format_type: DateFormat = DateFormat.DD_MM_YYYY) -> DateRange:
    """
    Función de utilidad para crear rápidamente un rango de días hacia atrás
    
    Args:
        days_back: Número de días hacia atrás desde hoy
        format_type: Formato de fecha
        
    Returns:
        DateRange: Rango de fechas creado
    """
    configurator = DateConfigurator()
    return configurator.create_date_range(days_back=days_back, format_type=format_type)

def get_last_month() -> DateRange:
    """Obtiene el rango del mes anterior"""
    configurator = DateConfigurator()
    return configurator._get_previous_month_range()

def validate_date_string(date_str: str) -> bool:
    """
    Valida si una cadena puede ser parseada como fecha
    
    Args:
        date_str: Cadena de fecha a validar
        
    Returns:
        bool: True si es válida
    """
    configurator = DateConfigurator()
    try:
        configurator._parse_date(date_str)
        return True
    except ValueError:
        return False

# Ejemplo de uso
if __name__ == "__main__":
    # Crear configurador
    print("=== DateConfigurator - Pruebas ===")
    
    configurator = DateConfigurator()
    
    # Crear diferentes tipos de rangos
    range_7days = configurator.create_date_range(days_back=7)
    print(f"Últimos 7 días: {range_7days.start_date} a {range_7days.end_date}")
    
    # Rango específico
    range_specific = configurator.create_date_range("2025-01-01", "2025-01-15")
    print(f"Rango específico: {range_specific.start_date} a {range_specific.end_date}")
    
    # Rangos predefinidos
    presets = configurator.get_preset_ranges()
    print(f"Último mes: {presets['ultimo_mes'].start_date} a {presets['ultimo_mes'].end_date}")
    
    # Validación
    is_valid = configurator.validate_date_range("2025-01-01", "2025-01-15", max_days=30)
    print(f"Rango válido: {is_valid}")
