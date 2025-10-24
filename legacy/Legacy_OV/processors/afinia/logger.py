"""
Sistema de logging y métricas para el procesador de Afinia.

Este módulo proporciona funcionalidades avanzadas de logging,
métricas y monitoreo para el procesamiento de datos de Afinia.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading


@dataclass
class ProcessingMetric:
    """Métrica individual de procesamiento."""
    timestamp: datetime
    metric_type: str
    value: float
    metadata: Dict[str, Any]


class MetricsCollector:
    """Recolector de métricas de procesamiento."""

    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics = deque(maxlen=max_metrics)
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.lock = threading.Lock()

    def record_counter(self, name: str, value: int = 1, metadata: Dict[str, Any] = None):
        """Registra un contador."""
        with self.lock:
            self.counters[name] += value
            metric = ProcessingMetric(
                timestamp=datetime.now(),
                metric_type='counter',
                value=value,
                metadata=metadata or {}
            )
            self.metrics.append(metric)

    def record_timer(self, name: str, duration: float, metadata: Dict[str, Any] = None):
        """Registra una duración."""
        with self.lock:
            self.timers[name].append(duration)
            metric = ProcessingMetric(
                timestamp=datetime.now(),
                metric_type='timer',
                value=duration,
                metadata=metadata or {}
            )
            self.metrics.append(metric)

    def record_gauge(self, name: str, value: float, metadata: Dict[str, Any] = None):
        """Registra un valor gauge."""
        with self.lock:
            metric = ProcessingMetric(
                timestamp=datetime.now(),
                metric_type='gauge',
                value=value,
                metadata={**(metadata or {}), 'gauge_name': name}
            )
            self.metrics.append(metric)

    def get_counter(self, name: str) -> int:
        """Obtiene el valor de un contador."""
        return self.counters.get(name, 0)

    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Obtiene estadísticas de un timer."""
        times = self.timers.get(name, [])
        if not times:
            return {'count': 0, 'avg': 0, 'min': 0, 'max': 0, 'total': 0}

        return {
            'count': len(times),
            'avg': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
            'total': sum(times)
        }

    def get_metrics_summary(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Obtiene un resumen de métricas."""
        with self.lock:
            if since:
                filtered_metrics = [m for m in self.metrics if m.timestamp >= since]
            else:
                filtered_metrics = list(self.metrics)

            summary = {
                'total_metrics': len(filtered_metrics),
                'counters': dict(self.counters),
                'timers': {name: self.get_timer_stats(name) for name in self.timers},
                'time_range': {
                    'start': min(m.timestamp for m in filtered_metrics).isoformat() if filtered_metrics else None,
                    'end': max(m.timestamp for m in filtered_metrics).isoformat() if filtered_metrics else None
                }
            }

            return summary

    def export_metrics(self, file_path: str):
        """Exporta métricas a archivo JSON."""
        with self.lock:
            metrics_data = {
                'export_timestamp': datetime.now().isoformat(),
                'metrics': [asdict(m) for m in self.metrics],
                'summary': self.get_metrics_summary()
            }

            # Convertir datetime a string para JSON
            for metric in metrics_data['metrics']:
                metric['timestamp'] = metric['timestamp'].isoformat()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)

    def clear_metrics(self):
        """Limpia todas las métricas."""
        with self.lock:
            self.metrics.clear()
            self.counters.clear()
            self.timers.clear()


class AfiniaLogger:
    """Logger especializado para el procesador de Afinia."""

    def __init__(self, name: str = "afinia_processor", log_level: int = logging.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.metrics = MetricsCollector()
        self.log_file_path = None

        self._setup_logger(log_level)

    def _setup_logger(self, log_level: int):
        """Configura el logger."""
        if self.logger.handlers:
            return  # Ya configurado

        self.logger.setLevel(log_level)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (opcional)
        self._setup_file_handler(formatter)

    def _setup_file_handler(self, formatter):
        """Configura el handler de archivo."""
        try:
            # Usar estructura consolidada data/metrics/afinia
            logs_dir = Path("data/metrics/afinia")
            logs_dir.mkdir(parents=True, exist_ok=True)

            log_filename = f"afinia_processor_{datetime.now().strftime('%Y%m%d')}.log"
            self.log_file_path = logs_dir / log_filename

            file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        except Exception as e:
            self.logger.warning(f"No se pudo configurar logging a archivo: {e}")

    def info(self, message: str, **kwargs):
        """Log info con métricas."""
        self.logger.info(message)
        self.metrics.record_counter('log_info', metadata=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning con métricas."""
        self.logger.warning(message)
        self.metrics.record_counter('log_warning', metadata=kwargs)

    def error(self, message: str, **kwargs):
        """Log error con métricas."""
        self.logger.error(message)
        self.metrics.record_counter('log_error', metadata=kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug con métricas."""
        self.logger.debug(message)
        self.metrics.record_counter('log_debug', metadata=kwargs)

    def log_processing_start(self, file_path: str):
        """Registra inicio de procesamiento."""
        self.info(f"Iniciando procesamiento: {file_path}")
        self.metrics.record_counter('processing_started', metadata={'file': file_path})

    def log_processing_end(self, file_path: str, duration: float, success: bool):
        """Registra fin de procesamiento."""
        status = "exitoso" if success else "fallido"
        self.info(f"Procesamiento {status}: {file_path} ({duration:.2f}s)")

        self.metrics.record_timer('processing_duration', duration, {'file': file_path})
        self.metrics.record_counter('processing_completed', metadata={
            'file': file_path,
            'success': success,
            'duration': duration
        })

    def log_validation_result(self, file_path: str, is_valid: bool, errors: List[str]):
        """Registra resultado de validación."""
        if is_valid:
            self.info(f"Validación exitosa: {file_path}")
            self.metrics.record_counter('validation_success')
        else:
            self.warning(f"Validación fallida: {file_path} - Errores: {len(errors)}")
            self.metrics.record_counter('validation_failed')

        for error in errors:
            self.debug(f"Error validación {file_path}: {error}")

    def log_database_operation(self, operation: str, success: bool, duration: float = None):
        """Registra operación de base de datos."""
        status = "exitosa" if success else "fallida"
        message = f"Operación BD {operation} {status}"

        if duration:
            message += f" ({duration:.3f}s)"
            self.metrics.record_timer(f'db_{operation}_duration', duration)

        if success:
            self.info(message)
            self.metrics.record_counter(f'db_{operation}_success')
        else:
            self.error(message)
            self.metrics.record_counter(f'db_{operation}_failed')

    def log_batch_summary(self, total_files: int, successful: int, failed: int, duration: float):
        """Registra resumen de procesamiento en lote."""
        success_rate = (successful / total_files * 100) if total_files > 0 else 0

        self.info(f"Resumen lote: {total_files} archivos, {successful} exitosos, "
                  f"{failed} fallidos, tasa éxito: {success_rate:.1f}% ({duration:.2f}s)")

        self.metrics.record_gauge('batch_success_rate', success_rate)
        self.metrics.record_counter('batch_processed', total_files)
        self.metrics.record_timer('batch_duration', duration)

    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Genera reporte de rendimiento."""
        since = datetime.now() - timedelta(hours=hours)
        summary = self.metrics.get_metrics_summary(since)

        # Calcular métricas adicionales
        processing_stats = self.metrics.get_timer_stats('processing_duration')
        db_stats = {
            'insert_success': self.metrics.get_counter('db_insert_success'),
            'insert_failed': self.metrics.get_counter('db_insert_failed'),
            'connection_success': self.metrics.get_counter('db_connection_success'),
            'connection_failed': self.metrics.get_counter('db_connection_failed')
        }

        validation_stats = {
            'success': self.metrics.get_counter('validation_success'),
            'failed': self.metrics.get_counter('validation_failed')
        }

        report = {
            'report_period_hours': hours,
            'generated_at': datetime.now().isoformat(),
            'processing_performance': processing_stats,
            'database_operations': db_stats,
            'validation_results': validation_stats,
            'log_levels': {
                'info': self.metrics.get_counter('log_info'),
                'warning': self.metrics.get_counter('log_warning'),
                'error': self.metrics.get_counter('log_error'),
                'debug': self.metrics.get_counter('log_debug')
            },
            'full_metrics_summary': summary
        }

        return report

    def export_performance_report(self, file_path: str, hours: int = 24):
        """Exporta reporte de rendimiento a archivo."""
        report = self.get_performance_report(hours)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.info(f"Reporte de rendimiento exportado: {file_path}")

    def get_log_file_path(self) -> Optional[str]:
        """Obtiene la ruta del archivo de log."""
        return str(self.log_file_path) if self.log_file_path else None


class TimerContext:
    """Context manager para medir tiempos."""

    def __init__(self, logger: AfiniaLogger, timer_name: str, metadata: Dict[str, Any] = None):
        self.logger = logger
        self.timer_name = timer_name
        self.metadata = metadata or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.logger.metrics.record_timer(self.timer_name, duration, self.metadata)


# Instancia global del logger
_global_logger = None


def get_logger(name: str = "afinia_processor") -> AfiniaLogger:
    """Obtiene la instancia global del logger."""
    global _global_logger
    if _global_logger is None:
        _global_logger = AfiniaLogger(name)
    return _global_logger


def setup_logging(log_level: int = logging.INFO, log_file: bool = True) -> AfiniaLogger:
    """
    Configura el sistema de logging global.

    Args:
        log_level: Nivel de logging
        log_file: Si crear archivo de log

    Returns:
        Instancia del logger configurado
    """
    logger = get_logger()
    logger.logger.setLevel(log_level)

    if not log_file and logger.log_file_path:
        # Remover file handler si existe
        for handler in logger.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                logger.logger.removeHandler(handler)
                handler.close()
        logger.log_file_path = None

    return logger


def timer(timer_name: str, metadata: Dict[str, Any] = None):
    """
    Decorator para medir tiempo de ejecución.

    Args:
        timer_name: Nombre del timer
        metadata: Metadatos adicionales
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger()
            with TimerContext(logger, timer_name, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator
