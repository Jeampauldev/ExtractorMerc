#!/usr/bin/env python3
"""
Performance Monitor - Decoradores y Utilidades de Performance
===========================================================

Este módulo centraliza todas las utilidades para monitoreo de performance
en ExtractorOV, eliminando duplicación de código entre extractors.

Características principales:
- Decorador de performance monitoring
- Métricas de tiempo de ejecución
- Logging estructurado de performance
- Manejo de errores con timing
- Compatibilidad con métricas legacy

Basado en las implementaciones exitosas de los extractores legacy.
"""

import time
import logging
import functools
from datetime import datetime
from typing import Callable, Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor de performance para funciones y métodos."""

    def __init__(self, include_args: bool = False, include_return: bool = False):
        """
        Inicializa el monitor de performance.

        Args:
            include_args: Si incluir argumentos en los logs
            include_return: Si incluir valores de retorno en los logs
        """
        self.include_args = include_args
        self.include_return = include_return
        self.metrics_data: Dict[str, list] = {}

    def __call__(self, func: Callable) -> Callable:
        """
        Decorador que monitorea la performance de una función.

        Args:
            func: Función a decorar

        Returns:
            Función decorada con monitoreo de performance
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            # Log inicial
            logger.info(f"DURACION Iniciando {func_name}")

            # Incluir argumentos en log si se requiere
            if self.include_args:
                args_str = ", ".join([str(arg)[:50] for arg in args[:3]]) # Limitar longitud
                kwargs_str = ", ".join([f"{k}={str(v)[:50]}" for k, v in list(kwargs.items())[:3]])
                if args_str or kwargs_str:
                    logger.debug(f" Argumentos: {args_str} {kwargs_str}")

            try:
                # Ejecutar función
                result = func(*args, **kwargs)

                # Calcular tiempo
                end_time = time.time()
                execution_time = end_time - start_time

                # Log exitoso
                logger.info(f"EXITOSO {func_name} completado en {execution_time:.2f} segundos")

                # Registrar métricas
                self._record_metric(func_name, execution_time, True)

                # Incluir retorno si se requiere
                if self.include_return and result is not None:
                    result_str = str(result)[:100] if not isinstance(result, (dict, list)) else str(type(result))
                    logger.debug(f" Retorno: {result_str}")

                return result

            except Exception as e:
                # Calcular tiempo aún en caso de error
                end_time = time.time()
                execution_time = end_time - start_time

                # Log de error
                logger.error(f"ERROR {func_name} falló después de {execution_time:.2f} segundos: {str(e)}")

                # Registrar métrica de fallo
                self._record_metric(func_name, execution_time, False, str(e))

                # Re-lanzar excepción
                raise

        return wrapper

    def _record_metric(self, func_name: str, execution_time: float, 
                      success: bool, error_msg: Optional[str] = None):
        """
        Registra una métrica de performance.

        Args:
            func_name: Nombre de la función
            execution_time: Tiempo de ejecución
            success: Si fue exitosa
            error_msg: Mensaje de error (opcional)
        """
        if func_name not in self.metrics_data:
            self.metrics_data[func_name] = []

        metric_entry = {
            'timestamp': datetime.now().isoformat(),
            'execution_time': execution_time,
            'success': success,
            'error_msg': error_msg
        }

        self.metrics_data[func_name].append(metric_entry)

    def get_metrics(self, func_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene métricas de performance registradas.

        Args:
            func_name: Función específica (None para todas)

        Returns:
            Diccionario con métricas
        """
        if func_name:
            return self.metrics_data.get(func_name, [])
        return self.metrics_data.copy()

    def get_summary(self, func_name: str) -> Dict[str, Any]:
        """
        Obtiene resumen de métricas para una función.

        Args:
            func_name: Nombre de la función

        Returns:
            Diccionario con resumen estadístico
        """
        metrics = self.metrics_data.get(func_name, [])
        if not metrics:
            return {}

        execution_times = [m['execution_time'] for m in metrics]
        success_count = sum(1 for m in metrics if m['success'])

        return {
            'total_calls': len(metrics),
            'successful_calls': success_count,
            'failed_calls': len(metrics) - success_count,
            'success_rate': success_count / len(metrics) * 100,
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times),
            'total_execution_time': sum(execution_times)
        }


# Instancia global del monitor para compatibilidad con código legacy
_global_monitor = PerformanceMonitor()

def performance_monitor(func: Callable) -> Callable:
    """
    Decorador de performance monitor (compatibilidad legacy).

    Args:
        func: Función a decorar

    Returns:
        Función decorada
    """
    return _global_monitor(func)

def performance_monitor_with_args(include_args: bool = False, 
                                 include_return: bool = False) -> Callable:
    """
    Decorador configurable de performance monitor.

    Args:
        include_args: Si incluir argumentos en logs
        include_return: Si incluir valores de retorno

    Returns:
        Decorador configurado
    """
    monitor = PerformanceMonitor(include_args, include_return)
    return monitor

def time_function(func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """
    Ejecuta una función y retorna resultado + tiempo de ejecución.

    Args:
        func: Función a ejecutar
        *args: Argumentos posicionales
        **kwargs: Argumentos con nombre

    Returns:
        Tupla (resultado, tiempo_ejecución)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    execution_time = time.time() - start_time

    return result, execution_time

def log_execution_time(func_name: str, execution_time: float, success: bool = True):
    """
    Registra tiempo de ejecución en logs.

    Args:
        func_name: Nombre de la función
        execution_time: Tiempo de ejecución
        success: Si fue exitosa
    """
    status_icon = "EXITOSO" if success else "ERROR"
    status_text = "completado" if success else "falló"

    logger.info(f"{status_icon} {func_name} {status_text} en {execution_time:.2f} segundos")

class TimingContext:
    """Context manager para medir tiempo de ejecución."""

    def __init__(self, operation_name: str, log_result: bool = True):
        """
        Inicializa el context manager.

        Args:
            operation_name: Nombre de la operación
            log_result: Si logear el resultado automáticamente
        """
        self.operation_name = operation_name
        self.log_result = log_result
        self.start_time = None
        self.execution_time = None

    def __enter__(self):
        """Inicia el cronómetro."""
        self.start_time = time.time()
        logger.info(f"DURACION Iniciando {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza el cronómetro y logea el resultado."""
        self.execution_time = time.time() - self.start_time

        if self.log_result:
            success = exc_type is None
            status_icon = "EXITOSO" if success else "ERROR"
            status_text = "completado" if success else "falló"

            logger.info(f"{status_icon} {self.operation_name} {status_text} en {self.execution_time:.2f} segundos")

        return False # No suprimir excepciones

def benchmark_function(func: Callable, iterations: int = 1, *args, **kwargs) -> Dict[str, float]:
    """
    Ejecuta benchmarking de una función.

    Args:
        func: Función a benchmarker
        iterations: Número de iteraciones
        *args: Argumentos para la función
        **kwargs: Argumentos con nombre

    Returns:
        Diccionario con estadísticas de benchmark
    """
    execution_times = []

    for i in range(iterations):
        start_time = time.time()
        try:
            func(*args, **kwargs)
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
        except Exception as e:
            logger.warning(f"Error en iteración {i+1}: {e}")

    if not execution_times:
        return {}

    return {
        'iterations': len(execution_times),
        'avg_time': sum(execution_times) / len(execution_times),
        'min_time': min(execution_times),
        'max_time': max(execution_times),
        'total_time': sum(execution_times),
        'times': execution_times
    }

# Funciones de conveniencia para compatibilidad con código legacy
def get_performance_metrics(func_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene métricas de performance del monitor global.

    Args:
        func_name: Función específica (None para todas)

    Returns:
        Métricas de performance
    """
    return _global_monitor.get_metrics(func_name)

def get_performance_summary(func_name: str) -> Dict[str, Any]:
    """
    Obtiene resumen de performance del monitor global.

    Args:
        func_name: Nombre de la función

    Returns:
        Resumen estadístico
    """
    return _global_monitor.get_summary(func_name)

def reset_performance_metrics():
    """Reinicia las métricas de performance del monitor global."""
    global _global_monitor
    _global_monitor = PerformanceMonitor()
    logger.info("LIMPIEZA Métricas de performance reiniciadas")

# Alias para compatibilidad con código legacy
monitor = performance_monitor
timing = TimingContext
