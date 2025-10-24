"""
Módulo para manejo inteligente de popups en aplicaciones web.
Proporciona detección automática, clasificación y manejo de diferentes tipos de popups.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Callable, Any, Set
from playwright.async_api import Page, ElementHandle, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class PopupType(Enum):
    """Tipos de popup identificados"""
    COOKIE_CONSENT = "cookie_consent"
    NEWSLETTER = "newsletter"
    NOTIFICATION = "notification"
    MODAL_DIALOG = "modal_dialog"
    ADVERTISEMENT = "advertisement"
    SURVEY = "survey"
    LOGIN_PROMPT = "login_prompt"
    TERMS_CONDITIONS = "terms_conditions"
    AGE_VERIFICATION = "age_verification"
    LOCATION_REQUEST = "location_request"
    PUSH_NOTIFICATION = "push_notification"
    CHAT_WIDGET = "chat_widget"
    FEEDBACK = "feedback"
    PROMOTION = "promotion"
    SECURITY_WARNING = "security_warning"
    UPDATE_NOTICE = "update_notice"
    MAINTENANCE = "maintenance"
    ERROR_DIALOG = "error_dialog"
    CONFIRMATION = "confirmation"
    LOADING = "loading"
    CAPTCHA = "captcha"
    UNKNOWN = "unknown"

class PopupAction(Enum):
    """Acciones disponibles para popups"""
    ACCEPT = "accept"  # Aceptar/Confirmar
    REJECT = "reject"  # Rechazar/Cancelar
    CLOSE = "close"    # Cerrar (X)
    DISMISS = "dismiss"  # Descartar
    IGNORE = "ignore"  # Ignorar el popup
    CUSTOM = "custom"  # Acción personalizada
    WAIT = "wait"      # Esperar a que desaparezca

@dataclass
class PopupConfig:
    """Configuración para manejo de un tipo de popup específico"""
    name: str
    popup_type: PopupType
    selectors: List[str]
    action: PopupAction
    priority: int = 5  # 1=alta, 10=baja
    timeout: float = 10.0
    custom_handler: Optional[Callable] = None
    text_patterns: List[str] = None  # Patrones de texto para identificar
    required_elements: List[str] = None  # Elementos que deben estar presentes

    def __post_init__(self):
        if self.text_patterns is None:
            self.text_patterns = []
        if self.required_elements is None:
            self.required_elements = []

@dataclass
class PopupEvent:
    """Registro de evento de popup"""
    timestamp: float
    popup_type: PopupType
    popup_name: str
    action_taken: PopupAction
    success: bool
    error_message: Optional[str] = None
    element_selector: Optional[str] = None
    page_url: Optional[str] = None

@dataclass
class PopupStats:
    """Estadísticas de manejo de popups"""
    total_detected: int = 0
    total_handled: int = 0
    total_failed: int = 0
    by_type: Dict[PopupType, int] = field(default_factory=dict)
    by_action: Dict[PopupAction, int] = field(default_factory=dict)
    average_response_time: float = 0.0

class PopupHandler:
    """
    Manejador inteligente de popups para aplicaciones web.
    
    Características:
    - Detección automática de popups comunes
    - Configuración personalizable por tipo
    - Manejo asíncrono y no bloqueante
    - Estadísticas y logging detallado
    - Soporte para acciones personalizadas
    """

    def __init__(self, page: Page, config_file: Optional[str] = None, popup_selectors: Optional[List[str]] = None):
        """
        Inicializa el manejador de popups.
        
        Args:
            page: Instancia de página de Playwright
            config_file: Archivo de configuración opcional
            popup_selectors: Lista de selectores personalizados para popups
        """
        self.page = page
        self.configs: Dict[str, PopupConfig] = {}
        self.events: List[PopupEvent] = []
        self.stats = PopupStats()
        self.active_handlers: Set[str] = set()
        self.is_monitoring = False
        self.custom_selectors = popup_selectors or []
        self._setup_default_configs()
        
        if config_file:
            self._load_config_file(config_file)

    def _setup_default_configs(self):
        """Configura los manejadores por defecto para popups comunes"""
        
        # Configuraciones por defecto
        default_configs = [
            PopupConfig(
                name="cookie_consent",
                popup_type=PopupType.COOKIE_CONSENT,
                selectors=[
                    "[id*='cookie']", "[class*='cookie']",
                    "[id*='consent']", "[class*='consent']",
                    ".cookie-banner", ".cookie-notice",
                    "#cookieConsent", ".gdpr-banner"
                ],
                action=PopupAction.ACCEPT,
                priority=1,
                text_patterns=["cookies", "consent", "privacy", "gdpr"]
            ),
            
            PopupConfig(
                name="newsletter_signup",
                popup_type=PopupType.NEWSLETTER,
                selectors=[
                    "[id*='newsletter']", "[class*='newsletter']",
                    "[id*='subscribe']", "[class*='subscribe']",
                    ".modal-newsletter", ".popup-newsletter"
                ],
                action=PopupAction.CLOSE,
                priority=2,
                text_patterns=["newsletter", "subscribe", "email", "signup"]
            ),
            
            PopupConfig(
                name="notification_request",
                popup_type=PopupType.PUSH_NOTIFICATION,
                selectors=[
                    "[id*='notification']", "[class*='notification']",
                    ".notification-popup", ".push-notification"
                ],
                action=PopupAction.REJECT,
                priority=1,
                text_patterns=["notifications", "allow", "block", "push"]
            ),
            
            PopupConfig(
                name="modal_dialog",
                popup_type=PopupType.MODAL_DIALOG,
                selectors=[
                    ".modal", ".dialog", ".popup",
                    "[role='dialog']", "[role='alertdialog']",
                    ".overlay", ".lightbox"
                ],
                action=PopupAction.CLOSE,
                priority=3
            ),
            
            PopupConfig(
                name="advertisement",
                popup_type=PopupType.ADVERTISEMENT,
                selectors=[
                    "[id*='ad']", "[class*='ad']",
                    "[id*='advertisement']", "[class*='advertisement']",
                    ".ad-popup", ".promo-popup"
                ],
                action=PopupAction.CLOSE,
                priority=4,
                text_patterns=["advertisement", "promo", "offer", "deal"]
            )
        ]
        
        for config in default_configs:
            self.configs[config.name] = config
            
        # Agregar configuración personalizada si se proporcionaron selectores
        if self.custom_selectors:
            custom_config = PopupConfig(
                name="custom_modal",
                popup_type=PopupType.MODAL_DIALOG,
                selectors=self.custom_selectors,
                action=PopupAction.CLOSE,
                priority=1,  # Alta prioridad para selectores específicos
                timeout=5.0
            )
            self.configs[custom_config.name] = custom_config
            logger.info(f"Configuración personalizada agregada con {len(self.custom_selectors)} selectores")

    async def start_monitoring(self, interval: float = 1.0):
        """
        Inicia el monitoreo automático de popups.
        
        Args:
            interval: Intervalo en segundos entre verificaciones
        """
        if self.is_monitoring:
            logger.warning("El monitoreo ya está activo")
            return
            
        self.is_monitoring = True
        logger.info("Iniciando monitoreo automático de popups")
        
        try:
            while self.is_monitoring:
                await self.scan_and_handle()
                await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"Error en monitoreo de popups: {e}")
        finally:
            self.is_monitoring = False

    def stop_monitoring(self):
        """Detiene el monitoreo automático"""
        self.is_monitoring = False
        logger.info("Monitoreo de popups detenido")

    async def scan_and_handle(self) -> Dict[str, Any]:
        """
        Escanea la página en busca de popups y los maneja según su configuración
        
        Returns:
            Dict con información sobre los popups encontrados y manejados
        """
        print(f"[POPUP-DEBUG] [EMOJI_REMOVIDO] Iniciando escaneo de popups. Configuraciones registradas: {len(self.configs)}")
        
        results = {
            'popups_found': [],
            'popups_handled': [],
            'errors': [],
            'total_events': 0
        }
        
        # Ordenar configuraciones por prioridad (menor número = mayor prioridad)
        sorted_configs = sorted(self.configs.values(), key=lambda x: x.priority)
        print(f"[POPUP-DEBUG] Configuraciones ordenadas por prioridad: {[config.name for config in sorted_configs]}")
        
        for config in sorted_configs:
            try:
                print(f"[POPUP-DEBUG] [EMOJI_REMOVIDO] Procesando configuración: {config.name} (prioridad: {config.priority})")
                
                # Buscar elemento del popup
                element = await self._find_popup_element(config)
                
                if element:
                    print(f"[POPUP-DEBUG] [EXITOSO] Popup encontrado: {config.name}")
                    results['popups_found'].append(config.name)
                    results['total_events'] += 1
                    
                    # Manejar el popup
                    event = await self._handle_popup_config(config)
                    
                    if event and event.success:
                        print(f"[POPUP-DEBUG] [EXITOSO] Popup manejado exitosamente: {config.name}")
                        results['popups_handled'].append(config.name)
                        self.events.append(event)
                        self._update_stats(event)
                        
                        # Esperar un poco después de manejar el popup
                        await asyncio.sleep(1)
                    else:
                        print(f"[POPUP-DEBUG] [ERROR] Error manejando popup: {config.name}")
                        results['errors'].append(f"Error manejando {config.name}")
                else:
                    print(f"[POPUP-DEBUG] [INFO] No se encontró popup: {config.name}")
                    
            except Exception as e:
                error_msg = f"Error procesando popup {config.name}: {str(e)}"
                print(f"[POPUP-DEBUG] [ERROR] {error_msg}")
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        print(f"[POPUP-DEBUG] [DATOS] Resumen del escaneo:")
        print(f"[POPUP-DEBUG]   - Popups encontrados: {len(results['popups_found'])}")
        print(f"[POPUP-DEBUG]   - Popups manejados: {len(results['popups_handled'])}")
        print(f"[POPUP-DEBUG]   - Errores: {len(results['errors'])}")
        print(f"[POPUP-DEBUG]   - Total eventos: {results['total_events']}")
        
        return results

    async def _handle_popup_config(self, config: PopupConfig) -> Optional[PopupEvent]:
        """
        Maneja un popup específico basado en su configuración.
        
        Args:
            config: Configuración del popup
            
        Returns:
            Evento de popup si se procesó, None si no se encontró
        """
        start_time = time.time()
        
        try:
            # Buscar elementos del popup
            element = await self._find_popup_element(config)
            if not element:
                return None
                
            # Verificar patrones de texto si están definidos
            if config.text_patterns and not await self._check_text_patterns(element, config.text_patterns):
                return None
                
            # Verificar elementos requeridos
            if config.required_elements and not await self._check_required_elements(config.required_elements):
                return None
                
            logger.info(f"Popup detectado: {config.name} ({config.popup_type.value})")
            
            # Marcar como activo para evitar procesamiento múltiple
            self.active_handlers.add(config.name)
            
            try:
                # Ejecutar acción
                success = await self._execute_action(element, config)
                
                # Crear evento
                event = PopupEvent(
                    timestamp=time.time(),
                    popup_type=config.popup_type,
                    popup_name=config.name,
                    action_taken=config.action,
                    success=success,
                    page_url=self.page.url
                )
                
                if success:
                    logger.info(f"Popup {config.name} manejado exitosamente con acción {config.action.value}")
                else:
                    logger.warning(f"Falló el manejo del popup {config.name}")
                    
                return event
                
            finally:
                # Remover de activos después de un delay
                await asyncio.sleep(1.0)
                self.active_handlers.discard(config.name)
                
        except Exception as e:
            logger.error(f"Error procesando popup {config.name}: {e}")
            return PopupEvent(
                timestamp=time.time(),
                popup_type=config.popup_type,
                popup_name=config.name,
                action_taken=config.action,
                success=False,
                error_message=str(e),
                page_url=self.page.url
            )

    async def _find_popup_element(self, config: PopupConfig) -> Optional[ElementHandle]:
        """
        Busca elementos de popup usando los selectores configurados.
        
        Args:
            config: Configuración del popup
            
        Returns:
            ElementHandle si se encuentra, None si no
        """
        print(f"[POPUP-DEBUG] Buscando popup '{config.name}' con {len(config.selectors)} selectores")
        
        for i, selector in enumerate(config.selectors):
            try:
                print(f"[POPUP-DEBUG] Probando selector {i+1}/{len(config.selectors)}: {selector}")
                
                # Esperar por el elemento con timeout corto
                element = await self.page.wait_for_selector(selector, timeout=2000)
                
                if element:
                    is_visible = await element.is_visible()
                    print(f"[POPUP-DEBUG] Elemento encontrado con selector '{selector}', visible: {is_visible}")
                    
                    if is_visible:
                        print(f"[POPUP-DEBUG] [EXITOSO] Elemento visible encontrado para popup '{config.name}'")
                        return element
                    else:
                        print(f"[POPUP-DEBUG] [ADVERTENCIA] Elemento encontrado pero no visible para selector '{selector}'")
                        
            except Exception as e:
                print(f"[POPUP-DEBUG] Selector '{selector}' no encontrado: {str(e)[:100]}")
                continue
                
        print(f"[POPUP-DEBUG] [ERROR] No se encontró elemento visible para popup '{config.name}'")
        return None

    async def _check_text_patterns(self, element: ElementHandle, patterns: List[str]) -> bool:
        """
        Verifica si el elemento contiene alguno de los patrones de texto.
        
        Args:
            element: Elemento a verificar
            patterns: Lista de patrones de texto
            
        Returns:
            True si se encuentra algún patrón, False si no
        """
        try:
            text_content = await element.text_content()
            if not text_content:
                return False
                
            text_lower = text_content.lower()
            return any(pattern.lower() in text_lower for pattern in patterns)
            
        except Exception as e:
            logger.debug(f"Error verificando patrones de texto: {e}")
            return False

    async def _check_required_elements(self, required_selectors: List[str]) -> bool:
        """
        Verifica que todos los elementos requeridos estén presentes.
        
        Args:
            required_selectors: Lista de selectores requeridos
            
        Returns:
            True si todos están presentes, False si no
        """
        for selector in required_selectors:
            try:
                element = await self.page.query_selector(selector)
                if not element or not await element.is_visible():
                    return False
            except Exception:
                return False
                
        return True

    async def _execute_action(self, element: ElementHandle, config: PopupConfig) -> bool:
        """
        Ejecuta la acción configurada en el popup.
        
        Args:
            element: Elemento del popup
            config: Configuración del popup
            
        Returns:
            True si la acción fue exitosa, False si no
        """
        try:
            print(f"[POPUP-DEBUG] [RESULTADO] Ejecutando acción {config.action.value} en popup {config.name}")
            
            if config.action == PopupAction.CUSTOM and config.custom_handler:
                result = await config.custom_handler(element, self.page)
                print(f"[POPUP-DEBUG] [EXITOSO] Acción personalizada ejecutada: {result}")
                return result
                
            elif config.action == PopupAction.IGNORE:
                print(f"[POPUP-DEBUG] ⏭[EMOJI_REMOVIDO] Popup ignorado según configuración")
                return True
                
            elif config.action == PopupAction.WAIT:
                print(f"[POPUP-DEBUG] ⏳ Esperando {config.timeout}s según configuración")
                await asyncio.sleep(config.timeout)
                return True
                
            else:
                # Para el popup de Afinia, usar los selectores específicos del legacy
                if config.name == "afinia_initial_modal":
                     print(f"[POPUP-DEBUG] [RESULTADO] Usando método específico para popup de Afinia")
                     return await self._handle_afinia_modal(element)
                
                # Buscar botón de acción específico
                action_element = await self._find_action_element(element, config.action)
                if action_element:
                    print(f"[POPUP-DEBUG] [RESULTADO] Elemento de acción encontrado, haciendo clic")
                    await action_element.click()
                    await asyncio.sleep(0.5)  # Esperar a que se procese
                    print(f"[POPUP-DEBUG] [EXITOSO] Clic en elemento de acción completado")
                    return True
                else:
                    print(f"[POPUP-DEBUG] [ADVERTENCIA] No se encontró elemento de acción específico, usando elemento principal")
                    # Fallback: hacer clic en el elemento principal
                    await element.click()
                    await asyncio.sleep(0.5)
                    print(f"[POPUP-DEBUG] [EXITOSO] Clic en elemento principal completado")
                    return True
                    
        except Exception as e:
            error_msg = f"Error ejecutando acción {config.action.value}: {e}"
            print(f"[POPUP-DEBUG] [ERROR] {error_msg}")
            logger.error(error_msg)
            return False

    async def _handle_afinia_modal(self, modal_element: ElementHandle) -> bool:
        """
        Maneja específicamente el modal de Afinia usando los métodos del código legacy.
        """
        try:
            print(f"[POPUP-DEBUG] [CONFIGURANDO] Iniciando manejo específico del modal de Afinia")
            
            # Selectores específicos del código legacy
            close_selectors = [
                "#myModal a.closePopUp i[ng-click=\"closeDialog()\"]",
                "#myModal .closePopUp i[ng-click=\"closeDialog()\"]", 
                "#myModal a.closePopUp",
                "#myModal .closePopUp",
                "#myModal .close",
                "#myModal button.close",
                "#myModal [aria-label='Close']"
            ]
            
            # Intentar con cada selector
            for i, selector in enumerate(close_selectors, 1):
                try:
                    print(f"[POPUP-DEBUG] [RESULTADO] Probando selector {i}/{len(close_selectors)}: {selector}")
                    close_element = await self.page.wait_for_selector(selector, timeout=2000)
                    if close_element and await close_element.is_visible():
                        print(f"[POPUP-DEBUG] [EXITOSO] Elemento de cierre encontrado con selector: {selector}")
                        
                        # Intentar clic normal
                        try:
                            await close_element.click()
                            await asyncio.sleep(1)
                            print(f"[POPUP-DEBUG] [EXITOSO] Clic normal exitoso")
                            return True
                        except Exception as e:
                            print(f"[POPUP-DEBUG] [ADVERTENCIA] Clic normal falló: {e}")
                        
                        # Intentar clic forzado
                        try:
                            await close_element.click(force=True)
                            await asyncio.sleep(1)
                            print(f"[POPUP-DEBUG] [EXITOSO] Clic forzado exitoso")
                            return True
                        except Exception as e:
                            print(f"[POPUP-DEBUG] [ADVERTENCIA] Clic forzado falló: {e}")
                        
                        # Intentar dispatch event
                        try:
                            await close_element.dispatch_event('click')
                            await asyncio.sleep(1)
                            print(f"[POPUP-DEBUG] [EXITOSO] Dispatch event exitoso")
                            return True
                        except Exception as e:
                            print(f"[POPUP-DEBUG] [ADVERTENCIA] Dispatch event falló: {e}")
                            
                except Exception as e:
                    print(f"[POPUP-DEBUG] [ADVERTENCIA] Selector {selector} no encontrado: {e}")
                    continue
            
            # Fallback con JavaScript como en el código legacy
            print(f"[POPUP-DEBUG] [CONFIGURANDO] Usando fallback JavaScript")
            js_code = """
                try {
                    var modal = document.getElementById('myModal');
                    if (modal) {
                        modal.style.display = 'none';
                        modal.remove();
                        console.log('Modal cerrado con JavaScript');
                        return true;
                    }
                    return false;
                } catch (e) {
                    console.error('Error cerrando modal:', e);
                    return false;
                }
            """
            
            result = await self.page.evaluate(js_code)
            if result:
                print(f"[POPUP-DEBUG] [EXITOSO] Modal cerrado exitosamente con JavaScript")
                return True
            else:
                print(f"[POPUP-DEBUG] [ERROR] Fallback JavaScript falló")
                return False
                
        except Exception as e:
            print(f"[POPUP-DEBUG] [ERROR] Error en manejo específico de Afinia: {e}")
            return False

    async def _find_action_element(self, popup_element: ElementHandle, action: PopupAction) -> Optional[ElementHandle]:
        """
        Busca el elemento específico para ejecutar la acción.
        
        Args:
            popup_element: Elemento del popup
            action: Acción a ejecutar
            
        Returns:
            ElementHandle del botón de acción si se encuentra
        """
        # Mapeo de acciones a selectores comunes
        action_selectors = {
            PopupAction.ACCEPT: [
                "button[id*='accept']", "button[class*='accept']",
                "button[id*='allow']", "button[class*='allow']",
                "button[id*='agree']", "button[class*='agree']",
                ".btn-accept", ".btn-allow", ".btn-agree",
                "[data-action='accept']", "[data-action='allow']"
            ],
            PopupAction.REJECT: [
                "button[id*='reject']", "button[class*='reject']",
                "button[id*='deny']", "button[class*='deny']",
                "button[id*='decline']", "button[class*='decline']",
                ".btn-reject", ".btn-deny", ".btn-decline",
                "[data-action='reject']", "[data-action='deny']"
            ],
            PopupAction.CLOSE: [
                "button[id*='close']", "button[class*='close']",
                ".close", ".btn-close", ".close-button",
                "[aria-label*='close']", "[title*='close']",
                ".modal-close", ".popup-close", "button.close"
            ],
            PopupAction.DISMISS: [
                "button[id*='dismiss']", "button[class*='dismiss']",
                ".btn-dismiss", ".dismiss-button",
                "[data-action='dismiss']"
            ]
        }
        
        selectors = action_selectors.get(action, [])
        
        for selector in selectors:
            try:
                element = await popup_element.query_selector(selector)
                if element and await element.is_visible():
                    return element
            except Exception:
                continue
                
        return None

    def _update_stats(self, event: PopupEvent):
        """
        Actualiza las estadísticas de manejo de popups.
        
        Args:
            event: Evento de popup procesado
        """
        self.stats.total_detected += 1
        
        if event.success:
            self.stats.total_handled += 1
        else:
            self.stats.total_failed += 1
            
        # Actualizar estadísticas por tipo
        if event.popup_type not in self.stats.by_type:
            self.stats.by_type[event.popup_type] = 0
        self.stats.by_type[event.popup_type] += 1
        
        # Actualizar estadísticas por acción
        if event.action_taken not in self.stats.by_action:
            self.stats.by_action[event.action_taken] = 0
        self.stats.by_action[event.action_taken] += 1

    def add_config(self, config: PopupConfig):
        """
        Añade una nueva configuración de popup.
        
        Args:
            config: Configuración del popup
        """
        self.configs[config.name] = config
        logger.info(f"Configuración añadida: {config.name}")

    def remove_config(self, name: str):
        """
        Elimina una configuración de popup.
        
        Args:
            name: Nombre de la configuración
        """
        if name in self.configs:
            del self.configs[name]
            logger.info(f"Configuración eliminada: {name}")

    def get_stats(self) -> PopupStats:
        """
        Obtiene las estadísticas actuales.
        
        Returns:
            Estadísticas de manejo de popups
        """
        return self.stats

    def get_events(self, popup_type: Optional[PopupType] = None) -> List[PopupEvent]:
        """
        Obtiene los eventos de popup registrados.
        
        Args:
            popup_type: Filtrar por tipo de popup (opcional)
            
        Returns:
            Lista de eventos de popup
        """
        if popup_type:
            return [event for event in self.events if event.popup_type == popup_type]
        return self.events.copy()

    def clear_events(self):
        """Limpia el historial de eventos"""
        self.events.clear()
        logger.info("Historial de eventos limpiado")

    def _load_config_file(self, config_file: str):
        """
        Carga configuraciones desde un archivo.
        
        Args:
            config_file: Ruta al archivo de configuración
        """
        # TODO: Implementar carga desde archivo JSON/YAML
        logger.info(f"Cargando configuración desde: {config_file}")
        pass

    async def handle_specific_popup(self, name: str) -> Optional[PopupEvent]:
        """
        Maneja un popup específico por nombre.
        
        Args:
            name: Nombre de la configuración del popup
            
        Returns:
            Evento de popup si se procesó
        """
        if name not in self.configs:
            logger.error(f"Configuración no encontrada: {name}")
            return None
            
        config = self.configs[name]
        return await self._handle_popup_config(config)

    async def wait_for_popup(self, popup_type: PopupType, timeout: float = 30.0) -> Optional[PopupEvent]:
        """
        Espera a que aparezca un tipo específico de popup.
        
        Args:
            popup_type: Tipo de popup a esperar
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Evento de popup cuando aparezca
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Buscar configuraciones del tipo especificado
            matching_configs = [
                config for config in self.configs.values()
                if config.popup_type == popup_type
            ]
            
            for config in matching_configs:
                element = await self._find_popup_element(config)
                if element:
                    return await self._handle_popup_config(config)
                    
            await asyncio.sleep(0.5)
            
        logger.warning(f"Timeout esperando popup tipo {popup_type.value}")
        return None

    def __str__(self) -> str:
        """Representación en string del manejador"""
        return f"PopupHandler(configs={len(self.configs)}, events={len(self.events)})"

    def __repr__(self) -> str:
        """Representación detallada del manejador"""
        return (f"PopupHandler(page={self.page.url}, "
                f"configs={len(self.configs)}, "
                f"events={len(self.events)}, "
                f"monitoring={self.is_monitoring})")
