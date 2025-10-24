#!/usr/bin/env python3
"""
Sistema de Logging Avanzado para Dashboard
Captura métricas detalladas de cada paso de los extractores
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import threading
from contextlib import contextmanager
import functools
import traceback

class DashboardLogger:
    """Logger avanzado que envía métricas al dashboard en tiempo real"""

    def __init__(self, extractor_name: str, dashboard_url: str = "http://localhost:8000"):
        self.extractor_name = extractor_name
        self.dashboard_url = dashboard_url
        self.session = None
        self.metrics = {
            'extractor_name': extractor_name,
            'status': 'idle',
            'start_time': None,
            'end_time': None,
            'current_step': '',
            'steps_completed': [],
            'files_downloaded': 0,
            'files_processed': 0,
            'records_inserted': 0,
            'duplicates_found': 0,
            'errors': [],
            'module_connections': {},
            'file_locations': {},
            'performance_stats': {
                'step_times': {},
                'connection_times': {},
                'download_sizes': {},
                'processing_times': {}
            }
        }
        self._current_step_start = None
        self._lock = threading.Lock()

    async def _send_update(self, updates: dict):
        """Enviar actualización al dashboard"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Preparar datos para serialización JSON
            serializable_updates = self._make_serializable(updates)

            async with self.session.post(
                f"{self.dashboard_url}/api/extractor/{self.extractor_name}/update",
                json=serializable_updates,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status != 200:
                    print(f"Error enviando métricas: {response.status}")

        except Exception as e:
            # No bloquear el extractor si hay problemas con el dashboard
            print(f"Warning: No se pudieron enviar métricas: {e}")

    def _make_serializable(self, data: Any) -> Any:
        """Convertir datos a formato serializable JSON"""
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, Path):
            return str(data)
        elif isinstance(data, dict):
            return {k: self._make_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        else:
            return data

    def start_extraction(self):
        """Iniciar proceso de extracción"""
        with self._lock:
            self.metrics['status'] = 'running'
            self.metrics['start_time'] = datetime.now()
            self.metrics['steps_completed'] = []
            self.metrics['errors'] = []

        asyncio.create_task(self._send_update({
            'status': 'running',
            'start_time': self.metrics['start_time'],
            'current_step': 'Iniciando extractor...'
        }))

        self.log_step('Extractor iniciado')

    def complete_extraction(self, success: bool = True):
        """Completar proceso de extracción"""
        with self._lock:
            self.metrics['status'] = 'completed' if success else 'error'
            self.metrics['end_time'] = datetime.now()

            if self.metrics['start_time']:
                duration = self.metrics['end_time'] - self.metrics['start_time']
                self.metrics['performance_stats']['total_duration'] = duration.total_seconds()

        asyncio.create_task(self._send_update({
            'status': self.metrics['status'],
            'end_time': self.metrics['end_time'],
            'current_step': 'Proceso completado' if success else 'Proceso terminado con errores'
        }))

        self.log_step(f'Extractor {"completado" if success else "terminado con errores"}')

    def log_step(self, step_name: str, details: Optional[Dict] = None):
        """Registrar un paso del proceso"""
        now = datetime.now()

        with self._lock:
            # Finalizar paso anterior si existe
            if self._current_step_start and self.metrics['current_step']:
                duration = (now - self._current_step_start).total_seconds()
                self.metrics['performance_stats']['step_times'][self.metrics['current_step']] = duration

            # Completar paso anterior
            if self.metrics['current_step'] not in self.metrics['steps_completed']:
                self.metrics['steps_completed'].append(self.metrics['current_step'])

            # Iniciar nuevo paso
            self.metrics['current_step'] = step_name
            self._current_step_start = now

            # Agregar detalles adicionales
            if details:
                self.metrics.update(details)

        # Enviar actualización
        update_data = {
            'current_step': step_name,
            'steps_completed': self.metrics['steps_completed']
        }

        if details:
            update_data.update(details)

        asyncio.create_task(self._send_update(update_data))

        print(f"[{now.strftime('%H:%M:%S')}] {self.extractor_name}: {step_name}")

    def log_module_connection(self, module_name: str, connection_time: float, success: bool = True):
        """Registrar conexión a módulo"""
        with self._lock:
            self.metrics['module_connections'][module_name] = {
                'connection_time': connection_time,
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
            self.metrics['performance_stats']['connection_times'][module_name] = connection_time

        status = "exitosa" if success else "fallida"
        self.log_step(f"Conexión {status} a {module_name}", {
            'module_connections': {module_name: self.metrics['module_connections'][module_name]}
        })

    def log_file_download(self, filename: str, file_path: str, size_bytes: int):
        """Registrar descarga de archivo"""
        with self._lock:
            self.metrics['files_downloaded'] += 1
            self.metrics['file_locations'][filename] = {
                'path': file_path,
                'size': size_bytes,
                'downloaded_at': datetime.now().isoformat()
            }
            self.metrics['performance_stats']['download_sizes'][filename] = size_bytes

        size_mb = size_bytes / (1024 * 1024)
        self.log_step(f"Descargado: {filename}", {
            'files_downloaded': self.metrics['files_downloaded'],
            'file_locations': {filename: self.metrics['file_locations'][filename]}
        })

        print(f" → Archivo: {filename} ({size_mb:.2f} MB)")

    def log_file_processed(self, filename: str, records_count: int, processing_time: float):
        """Registrar procesamiento de archivo"""
        with self._lock:
            self.metrics['files_processed'] += 1
            self.metrics['performance_stats']['processing_times'][filename] = processing_time

        self.log_step(f"Procesado: {filename}", {
            'files_processed': self.metrics['files_processed'],
            'processing_time': processing_time
        })

        print(f" → Procesados {records_count} registros en {processing_time:.2f}s")

    def log_database_operation(self, operation: str, records_count: int, duplicates: int = 0):
        """Registrar operación de base de datos"""
        with self._lock:
            if operation == 'insert':
                self.metrics['records_inserted'] += records_count
                self.metrics['duplicates_found'] += duplicates

        self.log_step(f"BD {operation}: {records_count} registros", {
            'records_inserted': self.metrics['records_inserted'],
            'duplicates_found': self.metrics['duplicates_found']
        })

        if duplicates > 0:
            print(f" → {duplicates} duplicados omitidos")

    def log_error(self, error_message: str, exception: Optional[Exception] = None):
        """Registrar error"""
        error_info = {
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }

        if exception:
            error_info['exception'] = str(exception)
            error_info['traceback'] = traceback.format_exc()

        with self._lock:
            self.metrics['errors'].append(error_info)

        asyncio.create_task(self._send_update({
            'errors': self.metrics['errors']
        }))

        print(f" ERROR {self.extractor_name}: {error_message}")
        if exception:
            print(f" Excepción: {exception}")

    def log_warning(self, warning_message: str):
        """Registrar advertencia"""
        print(f" WARNING {self.extractor_name}: {warning_message}")

    def log_success(self, success_message: str):
        """Registrar éxito"""
        print(f" SUCCESS {self.extractor_name}: {success_message}")

    @contextmanager
    def step_timer(self, step_name: str):
        """Context manager para medir tiempo de paso"""
        start_time = time.time()
        self.log_step(step_name)

        try:
            yield
        except Exception as e:
            self.log_error(f"Error en paso '{step_name}'", e)
            raise
        finally:
            duration = time.time() - start_time
            with self._lock:
                self.metrics['performance_stats']['step_times'][step_name] = duration
            print(f" [TIEMPO] Duración: {duration:.2f}s")

    @contextmanager
    def module_connection_timer(self, module_name: str):
        """Context manager para medir tiempo de conexión a módulo"""
        start_time = time.time()
        success = False

        try:
            yield
            success = True
        except Exception as e:
            self.log_error(f"Error conectando a {module_name}", e)
            raise
        finally:
            connection_time = time.time() - start_time
            self.log_module_connection(module_name, connection_time, success)

    def get_summary(self) -> Dict:
        """Obtener resumen de métricas"""
        with self._lock:
            summary = {
                'extractor_name': self.extractor_name,
                'status': self.metrics['status'],
                'files_downloaded': self.metrics['files_downloaded'],
                'files_processed': self.metrics['files_processed'],
                'records_inserted': self.metrics['records_inserted'],
                'duplicates_found': self.metrics['duplicates_found'],
                'errors_count': len(self.metrics['errors']),
                'steps_completed': len(self.metrics['steps_completed']),
                'performance_stats': self.metrics['performance_stats'].copy()
            }

            if self.metrics['start_time']:
                end_time = self.metrics['end_time'] or datetime.now()
                duration = end_time - self.metrics['start_time']
                summary['total_duration'] = duration.total_seconds()

            return summary

    async def cleanup(self):
        """Limpiar recursos"""
        if self.session:
            await self.session.close()

# Decorator para métricas automáticas
def track_performance(step_name: str = None):
    """Decorator para trackear automáticamente el performance de funciones"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Buscar logger en argumentos
            logger = None
            for arg in args:
                if hasattr(arg, 'dashboard_logger'):
                    logger = arg.dashboard_logger
                    break

            if not logger:
                return await func(*args, **kwargs)

            name = step_name or f"{func.__name__}"
            with logger.step_timer(name):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Buscar logger en argumentos
            logger = None
            for arg in args:
                if hasattr(arg, 'dashboard_logger'):
                    logger = arg.dashboard_logger
                    break

            if not logger:
                return func(*args, **kwargs)

            name = step_name or f"{func.__name__}"
            with logger.step_timer(name):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

# Instancia global para casos donde no se puede inyectar el logger
_global_loggers: Dict[str, DashboardLogger] = {}

def get_logger(extractor_name: str) -> DashboardLogger:
    """Obtener o crear logger global"""
    if extractor_name not in _global_loggers:
        _global_loggers[extractor_name] = DashboardLogger(extractor_name)
    return _global_loggers[extractor_name]
