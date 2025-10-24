#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Programación de Tareas para Extractor OV Modular
==========================================================

Sistema de programación que implementa:
- Ejecución programada multi-plataforma
- Horarios específicos: L-S 4am-10pm, masivo 4am, verificación cada hora
- Integración con el orquestador completo

Implementa el Paso 22 del FLUJO_VERIFICACION.md:
- Programación automática de tareas
- Manejo de horarios y frecuencias
- Logging y monitoreo de ejecuciones

Autor: ISES | Analyst Data Jeam Paul Arcon Solano
Fecha: Octubre 2025
"""

import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import sys

# Agregar path para imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.orchestrators.complete_flow_orchestrator import CompleteFlowOrchestrator, CompleteFlowResult

logger = logging.getLogger(__name__)

@dataclass
class ScheduledTask:
    """Definición de una tarea programada"""
    name: str
    description: str
    schedule_type: str  # 'daily', 'hourly', 'weekly', 'interval'
    schedule_config: Dict[str, Any]  # Configuración específica del horario
    function: Callable
    args: tuple = ()
    kwargs: Dict[str, Any] = None
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}

@dataclass
class TaskExecutionResult:
    """Resultado de ejecución de una tarea"""
    task_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    success: bool = False
    result_data: Any = None
    error_message: Optional[str] = None
    execution_id: Optional[str] = None

class TaskScheduler:
    """
    Programador de tareas para el sistema de extracción
    """
    
    def __init__(self, simulated_mode: bool = False):
        """
        Inicializar programador de tareas
        
        Args:
            simulated_mode: Si True, ejecuta en modo simulado
        """
        self.simulated_mode = simulated_mode
        self.tasks: Dict[str, ScheduledTask] = {}
        self.execution_history: List[TaskExecutionResult] = []
        self.running = False
        self.scheduler_thread = None
        
        # Inicializar orquestador
        self.orchestrator = CompleteFlowOrchestrator(simulated_mode=simulated_mode)
        
        # Configurar tareas por defecto
        self._setup_default_tasks()
        
        logger.info(f"[task_scheduler][init] Programador inicializado (modo simulado: {simulated_mode})")
    
    def _setup_default_tasks(self):
        """Configurar tareas por defecto según FLUJO_VERIFICACION.md"""
        
        # Tarea 1: Ejecución masiva diaria a las 4:00 AM
        self.add_task(
            name="daily_massive_extraction",
            description="Ejecución masiva diaria completa para todas las empresas",
            schedule_type="daily",
            schedule_config={"time": "04:00"},
            function=self._execute_massive_daily_flow,
            kwargs={"include_web_download": True, "force_reprocess": True}
        )
        
        # Tarea 2: Ejecución regular cada 2 horas (L-S, 4am-10pm)
        self.add_task(
            name="regular_extraction",
            description="Ejecución regular cada 2 horas en horario laboral",
            schedule_type="interval",
            schedule_config={
                "hours": 2,
                "start_time": "04:00",
                "end_time": "22:00",
                "weekdays": [0, 1, 2, 3, 4, 5]  # L-S (Monday=0)
            },
            function=self._execute_regular_flow,
            kwargs={"include_web_download": True, "force_reprocess": False}
        )
        
        # Tarea 3: Verificación S3 cada hora
        self.add_task(
            name="hourly_s3_verification",
            description="Verificación S3 y subida de archivos pendientes cada hora",
            schedule_type="hourly",
            schedule_config={"minutes": 0},
            function=self._execute_s3_verification_flow,
            kwargs={}
        )
        
        # Tarea 4: Limpieza de logs semanal
        self.add_task(
            name="weekly_cleanup",
            description="Limpieza semanal de logs y archivos temporales",
            schedule_type="weekly",
            schedule_config={"day": "sunday", "time": "02:00"},
            function=self._execute_cleanup,
            kwargs={}
        )
    
    def add_task(self, name: str, description: str, schedule_type: str,
                 schedule_config: Dict[str, Any], function: Callable,
                 args: tuple = (), kwargs: Dict[str, Any] = None,
                 enabled: bool = True) -> bool:
        """
        Agregar una tarea programada
        
        Args:
            name: Nombre único de la tarea
            description: Descripción de la tarea
            schedule_type: Tipo de programación
            schedule_config: Configuración del horario
            function: Función a ejecutar
            args: Argumentos posicionales
            kwargs: Argumentos con nombre
            enabled: Si la tarea está habilitada
            
        Returns:
            True si se agregó exitosamente
        """
        if name in self.tasks:
            logger.warning(f"[task_scheduler][add_task] Tarea '{name}' ya existe, reemplazando")
        
        task = ScheduledTask(
            name=name,
            description=description,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            function=function,
            args=args,
            kwargs=kwargs or {},
            enabled=enabled
        )
        
        self.tasks[name] = task
        
        # Programar en schedule
        self._schedule_task(task)
        
        logger.info(f"[task_scheduler][add_task] Tarea '{name}' agregada y programada")
        return True
    
    def _schedule_task(self, task: ScheduledTask):
        """Programar una tarea en el sistema schedule"""
        if not task.enabled:
            return
        
        config = task.schedule_config
        
        if task.schedule_type == "daily":
            schedule.every().day.at(config["time"]).do(
                self._execute_task_wrapper, task
            ).tag(task.name)
            
        elif task.schedule_type == "hourly":
            minutes = config.get("minutes", 0)
            schedule.every().hour.at(f":{minutes:02d}").do(
                self._execute_task_wrapper, task
            ).tag(task.name)
            
        elif task.schedule_type == "weekly":
            day = config["day"]
            time_str = config["time"]
            getattr(schedule.every(), day).at(time_str).do(
                self._execute_task_wrapper, task
            ).tag(task.name)
            
        elif task.schedule_type == "interval":
            # Para intervalos complejos, usar un wrapper personalizado
            schedule.every(10).minutes.do(
                self._check_interval_task, task
            ).tag(f"{task.name}_checker")
    
    def _check_interval_task(self, task: ScheduledTask):
        """Verificar si una tarea de intervalo debe ejecutarse"""
        now = datetime.now()
        config = task.schedule_config
        
        # Verificar día de la semana
        if "weekdays" in config:
            if now.weekday() not in config["weekdays"]:
                return
        
        # Verificar horario
        start_time = datetime.strptime(config["start_time"], "%H:%M").time()
        end_time = datetime.strptime(config["end_time"], "%H:%M").time()
        
        if not (start_time <= now.time() <= end_time):
            return
        
        # Verificar intervalo desde última ejecución
        if task.last_run:
            hours_since_last = config.get("hours", 1)
            if now - task.last_run < timedelta(hours=hours_since_last):
                return
        
        # Ejecutar tarea
        self._execute_task_wrapper(task)
    
    def _execute_task_wrapper(self, task: ScheduledTask):
        """Wrapper para ejecutar una tarea con manejo de errores y logging"""
        execution_id = f"{task.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        result = TaskExecutionResult(
            task_name=task.name,
            start_time=start_time,
            execution_id=execution_id
        )
        
        logger.info(f"[task_scheduler][execute] Iniciando tarea '{task.name}' (ID: {execution_id})")
        
        try:
            # Ejecutar función de la tarea
            task_result = task.function(*task.args, **task.kwargs)
            
            result.success = True
            result.result_data = task_result
            
            # Actualizar estadísticas de la tarea
            task.last_run = start_time
            task.run_count += 1
            task.last_error = None
            
            logger.info(f"[task_scheduler][execute] Tarea '{task.name}' completada exitosamente")
            
        except Exception as e:
            error_msg = f"Error ejecutando tarea '{task.name}': {e}"
            logger.error(f"[task_scheduler][execute] {error_msg}")
            
            result.success = False
            result.error_message = error_msg
            
            # Actualizar estadísticas de error
            task.error_count += 1
            task.last_error = error_msg
        
        finally:
            result.end_time = datetime.now()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()
            
            # Guardar en historial
            self.execution_history.append(result)
            
            # Mantener solo los últimos 100 registros
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
    
    def _execute_massive_daily_flow(self, **kwargs) -> Dict[str, Any]:
        """Ejecutar flujo masivo diario"""
        logger.info("[task_scheduler][massive_daily] Iniciando flujo masivo diario")
        
        results = self.orchestrator.execute_flow_for_all_companies(**kwargs)
        report = self.orchestrator.generate_execution_report(results)
        
        # Guardar reporte
        self._save_execution_report(report, "massive_daily")
        
        return report
    
    def _execute_regular_flow(self, **kwargs) -> Dict[str, Any]:
        """Ejecutar flujo regular"""
        logger.info("[task_scheduler][regular] Iniciando flujo regular")
        
        results = self.orchestrator.execute_flow_for_all_companies(**kwargs)
        report = self.orchestrator.generate_execution_report(results)
        
        # Guardar reporte
        self._save_execution_report(report, "regular")
        
        return report
    
    def _execute_s3_verification_flow(self, **kwargs) -> Dict[str, Any]:
        """Ejecutar solo verificación y subida S3"""
        logger.info("[task_scheduler][s3_verification] Iniciando verificación S3")
        
        results = {}
        
        for empresa in ['afinia', 'aire']:
            try:
                # Solo ejecutar verificación y subida S3
                result = CompleteFlowResult(
                    empresa=empresa,
                    execution_id=f"{empresa}_s3_verify_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    start_time=datetime.now()
                )
                
                # Verificación S3
                verification_stats = self.orchestrator.s3_verifier.verify_s3_status_after_rds_load(empresa, {})
                
                # Subida S3 filtrada
                upload_stats = self.orchestrator.s3_uploader.upload_pending_files_for_company(empresa)
                
                result.end_time = datetime.now()
                result.total_duration = (result.end_time - result.start_time).total_seconds()
                result.total_files_uploaded = upload_stats.archivos_subidos
                result.overall_success = upload_stats.registros_fallidos == 0
                
                results[empresa] = result
                
            except Exception as e:
                logger.error(f"[task_scheduler][s3_verification] Error en {empresa}: {e}")
        
        report = self.orchestrator.generate_execution_report(results)
        self._save_execution_report(report, "s3_verification")
        
        return report
    
    def _execute_cleanup(self, **kwargs) -> Dict[str, Any]:
        """Ejecutar limpieza semanal"""
        logger.info("[task_scheduler][cleanup] Iniciando limpieza semanal")
        
        cleanup_result = {
            "timestamp": datetime.now().isoformat(),
            "files_cleaned": 0,
            "space_freed_mb": 0,
            "errors": []
        }
        
        try:
            # Limpiar logs antiguos (más de 30 días)
            log_dir = Path("logs")
            if log_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=30)
                
                for log_file in log_dir.glob("*.log"):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        size_mb = log_file.stat().st_size / (1024 * 1024)
                        log_file.unlink()
                        cleanup_result["files_cleaned"] += 1
                        cleanup_result["space_freed_mb"] += size_mb
            
            # Limpiar archivos temporales
            temp_dirs = ["temp", "tmp", "cache"]
            for temp_dir in temp_dirs:
                temp_path = Path(temp_dir)
                if temp_path.exists():
                    for temp_file in temp_path.glob("*"):
                        if temp_file.is_file():
                            size_mb = temp_file.stat().st_size / (1024 * 1024)
                            temp_file.unlink()
                            cleanup_result["files_cleaned"] += 1
                            cleanup_result["space_freed_mb"] += size_mb
            
        except Exception as e:
            error_msg = f"Error en limpieza: {e}"
            cleanup_result["errors"].append(error_msg)
            logger.error(f"[task_scheduler][cleanup] {error_msg}")
        
        return cleanup_result
    
    def _save_execution_report(self, report: Dict[str, Any], report_type: str):
        """Guardar reporte de ejecución"""
        try:
            reports_dir = Path("reports/scheduled_executions")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_type}_{timestamp}.json"
            
            report_path = reports_dir / filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"[task_scheduler][save_report] Reporte guardado: {report_path}")
            
        except Exception as e:
            logger.error(f"[task_scheduler][save_report] Error guardando reporte: {e}")
    
    def start_scheduler(self):
        """Iniciar el programador de tareas"""
        if self.running:
            logger.warning("[task_scheduler][start] El programador ya está ejecutándose")
            return
        
        self.running = True
        
        def run_scheduler():
            logger.info("[task_scheduler][start] Programador de tareas iniciado")
            
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Verificar cada minuto
                except Exception as e:
                    logger.error(f"[task_scheduler][run] Error en programador: {e}")
                    time.sleep(60)
            
            logger.info("[task_scheduler][stop] Programador de tareas detenido")
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("[task_scheduler][start] Hilo del programador iniciado")
    
    def stop_scheduler(self):
        """Detener el programador de tareas"""
        self.running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        logger.info("[task_scheduler][stop] Programador detenido y tareas limpiadas")
    
    def get_task_status(self) -> Dict[str, Any]:
        """Obtener estado de todas las tareas"""
        status = {
            "scheduler_running": self.running,
            "total_tasks": len(self.tasks),
            "enabled_tasks": sum(1 for task in self.tasks.values() if task.enabled),
            "tasks": {},
            "recent_executions": []
        }
        
        # Estado de tareas
        for name, task in self.tasks.items():
            status["tasks"][name] = {
                "description": task.description,
                "schedule_type": task.schedule_type,
                "enabled": task.enabled,
                "run_count": task.run_count,
                "error_count": task.error_count,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "last_error": task.last_error
            }
        
        # Ejecuciones recientes (últimas 10)
        recent_executions = sorted(self.execution_history, key=lambda x: x.start_time, reverse=True)[:10]
        
        for execution in recent_executions:
            status["recent_executions"].append({
                "task_name": execution.task_name,
                "execution_id": execution.execution_id,
                "start_time": execution.start_time.isoformat(),
                "duration_seconds": execution.duration_seconds,
                "success": execution.success,
                "error_message": execution.error_message
            })
        
        return status
    
    def enable_task(self, task_name: str) -> bool:
        """Habilitar una tarea"""
        if task_name not in self.tasks:
            return False
        
        self.tasks[task_name].enabled = True
        self._schedule_task(self.tasks[task_name])
        
        logger.info(f"[task_scheduler][enable] Tarea '{task_name}' habilitada")
        return True
    
    def disable_task(self, task_name: str) -> bool:
        """Deshabilitar una tarea"""
        if task_name not in self.tasks:
            return False
        
        self.tasks[task_name].enabled = False
        schedule.clear(task_name)
        
        logger.info(f"[task_scheduler][disable] Tarea '{task_name}' deshabilitada")
        return True


# Funciones de conveniencia

def start_production_scheduler(simulated_mode: bool = False) -> TaskScheduler:
    """
    Iniciar programador en modo producción
    
    Args:
        simulated_mode: Modo simulado
        
    Returns:
        Instancia del programador
    """
    scheduler = TaskScheduler(simulated_mode=simulated_mode)
    scheduler.start_scheduler()
    return scheduler

def run_scheduler_daemon(simulated_mode: bool = False):
    """
    Ejecutar programador como daemon
    
    Args:
        simulated_mode: Modo simulado
    """
    scheduler = start_production_scheduler(simulated_mode)
    
    try:
        logger.info("[task_scheduler][daemon] Programador ejecutándose como daemon")
        print("Programador de tareas iniciado. Presiona Ctrl+C para detener.")
        
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("[task_scheduler][daemon] Señal de interrupción recibida")
        print("\nDeteniendo programador...")
        
    finally:
        scheduler.stop_scheduler()
        print("Programador detenido.")


if __name__ == "__main__":
    # Test del programador de tareas
    logger.info("[task_scheduler][main] Iniciando test del programador")
    
    print("=" * 80)
    print("TEST DEL PROGRAMADOR DE TAREAS (MODO SIMULADO)")
    print("=" * 80)
    
    # Crear programador en modo simulado
    scheduler = TaskScheduler(simulated_mode=True)
    
    # Mostrar estado inicial
    status = scheduler.get_task_status()
    
    print(f"\nESTADO DEL PROGRAMADOR:")
    print(f"  - Ejecutándose: {status['scheduler_running']}")
    print(f"  - Total tareas: {status['total_tasks']}")
    print(f"  - Tareas habilitadas: {status['enabled_tasks']}")
    
    print(f"\nTAREAS CONFIGURADAS:")
    for name, task_info in status["tasks"].items():
        print(f"  - {name}:")
        print(f"    * Descripción: {task_info['description']}")
        print(f"    * Tipo: {task_info['schedule_type']}")
        print(f"    * Habilitada: {task_info['enabled']}")
        print(f"    * Ejecuciones: {task_info['run_count']}")
        print(f"    * Errores: {task_info['error_count']}")
    
    # Ejecutar una tarea manualmente para test
    print(f"\nEJECUTANDO TAREA DE VERIFICACIÓN S3 MANUALMENTE:")
    test_result = scheduler._execute_s3_verification_flow()
    
    print(f"  - Timestamp: {test_result['timestamp']}")
    print(f"  - Modo simulado: {test_result['modo_simulado']}")
    print(f"  - Empresas procesadas: {test_result['resumen_global']['empresas_procesadas']}")
    print(f"  - Empresas exitosas: {test_result['resumen_global']['empresas_exitosas']}")
    
    print("\n" + "=" * 80)
    print("NOTA: Para ejecutar en producción, usar:")
    print("  python -c \"from src.schedulers.task_scheduler import run_scheduler_daemon; run_scheduler_daemon()\"")
    print("=" * 80)