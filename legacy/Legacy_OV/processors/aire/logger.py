"""
Sistema de logging y métricas para el procesador de Aire.

Este módulo proporciona funcionalidades avanzadas de logging,
métricas y monitoreo para el procesamiento de datos de Aire.
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
            return {'count': 0, 'avg': 0.0, 'min': 0.0, 'max': 0.0, 'total': 0.0}
        
        return {
            'count': len(times),
            'avg': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
            'total': sum(times)
        }

    def get_recent_metrics(self, hours: int = 1) -> List[ProcessingMetric]:
        """Obtiene métricas recientes."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics if m.timestamp >= cutoff]

    def export_metrics(self, filepath: str, hours: int = 24):
        """Exporta métricas a archivo JSON."""
        recent_metrics = self.get_recent_metrics(hours)
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'hours_covered': hours,
            'total_metrics': len(recent_metrics),
            'counters': dict(self.counters),
            'timer_stats': {name: self.get_timer_stats(name) for name in self.timers},
            'metrics': [asdict(m) for m in recent_metrics]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)


class AireLogger:
    """Logger especializado para el procesador de Aire."""

    def __init__(self, name: str = "aire_processor", log_level: int = logging.INFO):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Evitar duplicar handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Métricas
        self.metrics = MetricsCollector()
        
        # Contadores específicos
        self.processing_stats = {
            'files_processed': 0,
            'records_inserted': 0,
            'validation_errors': 0,
            'database_errors': 0,
            'processing_time': 0.0
        }

    def _setup_handlers(self):
        """Configura los handlers del logger."""
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Handler para archivo
        log_dir = Path("data/logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def info(self, message: str, **kwargs):
        """Log info con métricas."""
        self.logger.info(message)
        self.metrics.record_counter('info_messages', metadata=kwargs)

    def error(self, message: str, **kwargs):
        """Log error con métricas."""
        self.logger.error(message)
        self.metrics.record_counter('error_messages', metadata=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning con métricas."""
        self.logger.warning(message)
        self.metrics.record_counter('warning_messages', metadata=kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug con métricas."""
        self.logger.debug(message)
        self.metrics.record_counter('debug_messages', metadata=kwargs)

    def log_processing_start(self, file_path: str):
        """Registra inicio de procesamiento de archivo."""
        self.info(f"Iniciando procesamiento: {Path(file_path).name}")
        self.metrics.record_counter('processing_started', metadata={'file': file_path})

    def log_processing_success(self, file_path: str, records_count: int, duration: float):
        """Registra procesamiento exitoso."""
        self.info(f"Procesamiento exitoso: {Path(file_path).name} - {records_count} registros en {duration:.2f}s")
        self.metrics.record_counter('processing_success')
        self.metrics.record_timer('processing_duration', duration, {'file': file_path})
        self.metrics.record_gauge('records_processed', records_count, {'file': file_path})
        
        # Actualizar estadísticas
        self.processing_stats['files_processed'] += 1
        self.processing_stats['records_inserted'] += records_count
        self.processing_stats['processing_time'] += duration

    def log_processing_error(self, file_path: str, error: str, duration: float = 0):
        """Registra error en procesamiento."""
        self.error(f"Error procesando {Path(file_path).name}: {error}")
        self.metrics.record_counter('processing_errors', metadata={'file': file_path, 'error': error})
        if duration > 0:
            self.metrics.record_timer('failed_processing_duration', duration, {'file': file_path})

    def log_validation_error(self, file_path: str, errors: List[str]):
        """Registra errores de validación."""
        self.warning(f"Errores de validación en {Path(file_path).name}: {len(errors)} errores")
        for error in errors:
            self.debug(f"  - {error}")
        
        self.metrics.record_counter('validation_errors', len(errors), 
                                  metadata={'file': file_path, 'error_count': len(errors)})
        self.processing_stats['validation_errors'] += len(errors)

    def log_database_error(self, operation: str, error: str):
        """Registra errores de base de datos."""
        self.error(f"Error de BD en {operation}: {error}")
        self.metrics.record_counter('database_errors', metadata={'operation': operation, 'error': error})
        self.processing_stats['database_errors'] += 1

    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de procesamiento."""
        stats = self.processing_stats.copy()
        
        # Agregar métricas calculadas
        if stats['files_processed'] > 0:
            stats['avg_records_per_file'] = stats['records_inserted'] / stats['files_processed']
            stats['avg_time_per_file'] = stats['processing_time'] / stats['files_processed']
            stats['success_rate'] = ((stats['files_processed'] - stats['validation_errors'] - stats['database_errors']) 
                                   / stats['files_processed']) * 100
        else:
            stats['avg_records_per_file'] = 0
            stats['avg_time_per_file'] = 0
            stats['success_rate'] = 0
        
        return stats

    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Genera reporte de rendimiento."""
        recent_metrics = self.metrics.get_recent_metrics(hours)
        
        # Agrupar métricas por tipo
        counters = {}
        timers = {}
        gauges = {}
        
        for metric in recent_metrics:
            if metric.metric_type == 'counter':
                name = metric.metadata.get('counter_name', 'unknown')
                counters[name] = counters.get(name, 0) + metric.value
            elif metric.metric_type == 'timer':
                name = metric.metadata.get('timer_name', 'processing_duration')
                if name not in timers:
                    timers[name] = []
                timers[name].append(metric.value)
            elif metric.metric_type == 'gauge':
                name = metric.metadata.get('gauge_name', 'unknown')
                gauges[name] = metric.value
        
        # Calcular estadísticas de timers
        timer_stats = {}
        for name, times in timers.items():
            if times:
                timer_stats[name] = {
                    'count': len(times),
                    'avg': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'total': sum(times)
                }
        
        return {
            'report_timestamp': datetime.now().isoformat(),
            'hours_covered': hours,
            'total_metrics': len(recent_metrics),
            'counters': counters,
            'timer_stats': timer_stats,
            'gauges': gauges,
            'processing_stats': self.get_processing_stats()
        }

    def export_performance_report(self, filepath: str, hours: int = 24):
        """Exporta reporte de rendimiento a archivo."""
        report = self.get_performance_report(hours)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        self.info(f"Reporte de rendimiento exportado: {filepath}")

    def reset_stats(self):
        """Reinicia las estadísticas de procesamiento."""
        self.processing_stats = {
            'files_processed': 0,
            'records_inserted': 0,
            'validation_errors': 0,
            'database_errors': 0,
            'processing_time': 0.0
        }
        self.info("Estadísticas de procesamiento reiniciadas")


# Instancia global del logger
_global_logger = None


def get_logger(name: str = "aire_processor") -> AireLogger:
    """Obtiene una instancia del logger."""
    global _global_logger
    if _global_logger is None:
        _global_logger = AireLogger(name)
    return _global_logger


def setup_logging(level: str = 'INFO', log_file: str = None) -> AireLogger:
    """Configura el sistema de logging."""
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    log_level = level_map.get(level.upper(), logging.INFO)
    logger = AireLogger("aire_processor", log_level)
    
    if log_file:
        # Agregar handler adicional para archivo específico
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.logger.addHandler(file_handler)
    
    return logger


class timer:
    """Context manager para medir tiempo de ejecución."""
    
    def __init__(self, name: str, logger: AireLogger = None):
        self.name = name
        self.logger = logger or get_logger()
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Iniciando timer: {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if exc_type is None:
            self.logger.info(f"Timer {self.name}: {duration:.3f}s")
        else:
            self.logger.error(f"Timer {self.name} terminó con error: {duration:.3f}s")
        
        self.logger.metrics.record_timer(self.name, duration)

    @property
    def duration(self) -> float:
        """Obtiene la duración medida."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0


def log_function_call(func):
    """Decorador para loggear llamadas a funciones."""
    def wrapper(*args, **kwargs):
        logger = get_logger()
        func_name = func.__name__
        
        logger.debug(f"Llamando función: {func_name}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"Función {func_name} completada en {duration:.3f}s")
            logger.metrics.record_timer(f"function_{func_name}", duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error en función {func_name}: {e} (duración: {duration:.3f}s)")
            logger.metrics.record_counter('function_errors', metadata={'function': func_name, 'error': str(e)})
            raise
    
    return wrapper
