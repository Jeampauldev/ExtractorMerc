#!/usr/bin/env python3
"""
Monitor de Progreso Visual Multiplataforma
Proporciona visualización en tiempo real del progreso de carga de archivos
Compatible con Windows 11 y Ubuntu 24.04.3 LTS
"""

import os
import sys
import time
import threading
import platform
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ProgressMonitor:
    """Monitor de progreso visual multiplataforma optimizado"""
    
    def __init__(self, total_records: int = 0):
        self.total_records = total_records
        self.processed_records = 0
        self.successful_records = 0
        self.failed_records = 0
        self.s3_failures = 0
        self.db_failures = 0
        self.current_record = ""
        self.start_time = None
        self.is_running = False
        self.display_thread = None
        self.lock = threading.Lock()
        
        # Información del sistema
        self.system_info = self._detect_system()
        
        # Detectar capacidades del terminal
        self.supports_colors = self._check_color_support()
        self.terminal_width = self._get_terminal_width()
        self.refresh_rate = 0.5 if self.system_info['is_windows'] else 0.3
        
        # Configurar colores
        self._setup_colors()
        
    def _detect_system(self) -> Dict[str, Any]:
        """Detectar información del sistema"""
        return {
            'os': platform.system(),
            'is_windows': platform.system() == "Windows",
            'is_linux': platform.system() == "Linux",
            'python_version': platform.python_version(),
            'encoding': sys.stdout.encoding or 'utf-8'
        }
        
    def _setup_colors(self):
        """Configurar colores según el sistema"""
        if self.supports_colors:
            if self.system_info['is_windows']:
                try:
                    import colorama
                    colorama.init()
                except ImportError:
                    pass
            
            # Definir colores ANSI
            self.colors = {
                'reset': '\033[0m',
                'bold': '\033[1m',
                'green': '\033[92m',
                'red': '\033[91m',
                'yellow': '\033[93m',
                'blue': '\033[94m',
                'cyan': '\033[96m',
                'white': '\033[97m',
                'gray': '\033[90m'
            }
        else:
            # Sin colores
            self.colors = {key: '' for key in ['reset', 'bold', 'green', 'red', 'yellow', 'blue', 'cyan', 'white', 'gray']}
        
    def _check_color_support(self) -> bool:
        """Verificar si el terminal soporta colores ANSI"""
        if self.system_info['is_windows']:
            try:
                import colorama
                return True
            except ImportError:
                # Windows 10+ soporta ANSI nativamente
                return sys.version_info >= (3, 6)
        else:  # Unix/Linux
            return (sys.stdout.isatty() and 
                   os.environ.get('TERM', '') not in ['', 'dumb'] and
                   'color' in os.environ.get('TERM', '').lower())
        
    def _get_terminal_width(self) -> int:
        """Obtener ancho del terminal"""
        try:
            if self.system_info['is_windows']:
                import shutil
                return shutil.get_terminal_size().columns
            else:
                return os.get_terminal_size().columns
        except (OSError, AttributeError):
            return 80  # Valor por defecto
    
    def _clear_screen(self):
        """Limpiar pantalla de manera multiplataforma"""
        if self.system_info['is_windows']:
            os.system('cls')
        else:
            os.system('clear')
    
    def _move_cursor_up(self, lines: int):
        """Mover cursor hacia arriba"""
        if self.supports_colors:
            print(f'\033[{lines}A', end='', flush=True)
    
    def _clear_line(self):
        """Limpiar línea actual"""
        if self.supports_colors:
            print('\033[K', end='', flush=True)
        else:
            print(' ' * self.terminal_width, end='\r', flush=True)
    
    def start(self):
        """Iniciar el monitor de progreso"""
        with self.lock:
            if self.is_running:
                return
            
            self.is_running = True
            self.start_time = datetime.now()
            
            # Limpiar pantalla inicial
            self._clear_screen()
            
            # Iniciar hilo de actualización
            self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
            self.display_thread.start()
    
    def stop(self):
        """Detener el monitor de progreso"""
        with self.lock:
            self.is_running = False
        
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
    
    def update_progress(self, processed: int, successful: int, failed: int, 
                       s3_failures: int = 0, db_failures: int = 0, 
                       current_record: str = ""):
        """Actualizar estadísticas de progreso"""
        with self.lock:
            self.processed_records = processed
            self.successful_records = successful
            self.failed_records = failed
            self.s3_failures = s3_failures
            self.db_failures = db_failures
            self.current_record = current_record
    
    def _display_loop(self):
        """Bucle principal de visualización"""
        lines_printed = 0
        
        while self.is_running:
            try:
                # Mover cursor al inicio si ya hemos impreso líneas
                if lines_printed > 0:
                    self._move_cursor_up(lines_printed)
                
                # Generar y mostrar el display
                display_lines = self._generate_display()
                
                for line in display_lines:
                    self._clear_line()
                    print(line, flush=True)
                
                lines_printed = len(display_lines)
                
                # Esperar antes de la siguiente actualización
                time.sleep(self.refresh_rate)
                
            except Exception as e:
                # En caso de error, continuar sin mostrar
                time.sleep(1.0)
    
    def _generate_display(self) -> list:
        """Generar las líneas del display"""
        lines = []
        c = self.colors  # Shortcut para colores
        
        # Título
        lines.append(f"{c['bold']}{c['cyan']}{'='*self.terminal_width}{c['reset']}")
        lines.append(f"{c['bold']}{c['white']}[INICIANDO] MONITOR DE PROGRESO - CARGADOR DE ARCHIVOS{c['reset']}")
        lines.append(f"{c['bold']}{c['cyan']}{'='*self.terminal_width}{c['reset']}")
        lines.append("")
        
        # Información del sistema
        lines.append(f"{c['gray']}Sistema: {self.system_info['os']} | Python: {self.system_info['python_version']}{c['reset']}")
        lines.append("")
        
        # Estadísticas principales
        with self.lock:
            total = self.total_records
            processed = self.processed_records
            successful = self.successful_records
            failed = self.failed_records
            s3_fail = self.s3_failures
            db_fail = self.db_failures
            current = self.current_record
        
        # Progreso general
        if total > 0:
            progress_pct = (processed / total) * 100
            success_rate = (successful / max(processed, 1)) * 100
            
            # Barra de progreso
            bar_width = min(50, self.terminal_width - 30)
            filled = int((processed / total) * bar_width)
            bar = '[EMOJI_REMOVIDO]' * filled + '[EMOJI_REMOVIDO]' * (bar_width - filled)
            
            lines.append(f"{c['bold']}[DATOS] PROGRESO GENERAL:{c['reset']}")
            lines.append(f"   {c['cyan']}{bar}{c['reset']} {progress_pct:.1f}%")
            lines.append(f"   {processed}/{total} registros procesados")
            lines.append("")
        
        # Estadísticas detalladas
        lines.append(f"{c['bold']}[METRICAS] ESTADÍSTICAS:{c['reset']}")
        lines.append(f"   {c['green']}[EXITOSO] Exitosos:{c['reset']} {successful}")
        lines.append(f"   {c['red']}[ERROR] Fallidos:{c['reset']} {failed}")
        
        if s3_fail > 0:
            lines.append(f"   {c['yellow']}[S3]  Fallos S3:{c['reset']} {s3_fail}")
        
        if db_fail > 0:
            lines.append(f"   {c['yellow']}[BASE_DATOS]  Fallos DB:{c['reset']} {db_fail}")
        
        # Tasa de éxito
        if processed > 0:
            success_rate = (successful / processed) * 100
            color = c['green'] if success_rate >= 90 else c['yellow'] if success_rate >= 70 else c['red']
            lines.append(f"   {color}[DATOS] Tasa de éxito:{c['reset']} {success_rate:.1f}%")
        
        lines.append("")
        
        # Velocidad y tiempo
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            elapsed_str = str(elapsed).split('.')[0]  # Sin microsegundos
            
            lines.append(f"{c['bold']}[TIEMPO]  TIEMPO:{c['reset']}")
            lines.append(f"   Transcurrido: {elapsed_str}")
            
            if processed > 0:
                rate = processed / elapsed.total_seconds() * 60  # registros por minuto
                lines.append(f"   Velocidad: {rate:.1f} registros/min")
                
                # Estimación de tiempo restante
                if total > processed and rate > 0:
                    remaining_records = total - processed
                    eta_minutes = remaining_records / rate
                    eta = timedelta(minutes=eta_minutes)
                    eta_str = str(eta).split('.')[0]
                    lines.append(f"   ETA: {eta_str}")
            
            lines.append("")
        
        # Registro actual
        if current:
            lines.append(f"{c['bold']}[ARCHIVO] PROCESANDO:{c['reset']}")
            # Truncar si es muy largo
            max_len = self.terminal_width - 15
            display_current = current[:max_len] + "..." if len(current) > max_len else current
            lines.append(f"   {display_current}")
            lines.append("")
        
        # Línea de estado
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_line = f"{c['gray']}Actualizado: {timestamp} | Refresco: {self.refresh_rate}s{c['reset']}"
        lines.append(status_line)
        
        return lines
    
    def update_stats(self, stats: Dict[str, Any]):
        """Actualizar estadísticas"""
        self.processed_records = stats.get('processed_records', 0)
        self.successful_records = stats.get('successful_records', 0)
        self.failed_records = stats.get('failed_records', 0)
        self.files_uploaded = stats.get('files_uploaded', 0)
        self.s3_failures = stats.get('s3_failures', 0)
        self.total_size_mb = stats.get('total_size_mb', 0.0)
        
    def set_current_record(self, record_name: str, status: str = "Procesando..."):
        """Establecer registro actual"""
        self.current_record = record_name
        self.current_status = status
        
    def start_monitoring(self):
        """Iniciar monitoreo en hilo separado"""
        self.start()
        
    def stop_monitoring(self):
        """Detener monitoreo"""
        self.stop()
            
    def _render_display(self):
        """Renderizar pantalla de progreso"""
        # Mover cursor al inicio (sin limpiar para evitar parpadeo)
        if self.system_info['is_windows']:
            os.system('cls')
        else:
            print('\033[H\033[J', end='')
            
        # Calcular métricas
        elapsed = datetime.now() - self.start_time
        progress_pct = (self.processed_records / max(self.total_records, 1)) * 100
        
        # Estimar tiempo restante
        if self.processed_records > 0:
            avg_time_per_record = elapsed.total_seconds() / self.processed_records
            remaining_records = self.total_records - self.processed_records
            eta = timedelta(seconds=avg_time_per_record * remaining_records)
        else:
            eta = timedelta(0)
            
        # Colores ANSI
        GREEN = '\033[92m'
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        # Header
        print(f"{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD}{WHITE}[INICIANDO] CARGADOR DE ARCHIVOS DIRECTO - MONITOR DE PROGRESO{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}")
        print()
        
        # Información del sistema
        system_info = f"Sistema: {platform.system()} {platform.release()}"
        if self.system_info['is_linux']:
            try:
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            system_info = line.split('=')[1].strip().strip('"')
                            break
            except:
                pass
                
        print(f"{BLUE}[DATOS] Sistema: {system_info}{RESET}")
        print(f"{BLUE}⏰ Iniciado: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{BLUE}[TIEMPO]  Tiempo transcurrido: {str(elapsed).split('.')[0]}{RESET}")
        print()
        
        # Progreso principal
        bar_width = 50
        filled = int(bar_width * progress_pct / 100)
        bar = '[EMOJI_REMOVIDO]' * filled + '[EMOJI_REMOVIDO]' * (bar_width - filled)
        
        print(f"{BOLD}[METRICAS] PROGRESO GENERAL:{RESET}")
        print(f"[{GREEN}{bar}{RESET}] {progress_pct:.1f}%")
        print(f"Registros: {self.processed_records}/{self.total_records}")
        
        if eta.total_seconds() > 0:
            print(f"⏳ Tiempo estimado restante: {str(eta).split('.')[0]}")
        print()
        
        # Estadísticas detalladas
        print(f"{BOLD}[DATOS] ESTADÍSTICAS DETALLADAS:{RESET}")
        print(f"[EXITOSO] Exitosos:      {GREEN}{self.successful_records:>6}{RESET}")
        print(f"[ERROR] Fallidos:      {RED}{self.failed_records:>6}{RESET}")
        print(f"[EMOJI_REMOVIDO] Archivos subidos: {BLUE}{self.files_uploaded:>6}{RESET}")
        print(f"[EMOJI_REMOVIDO] Fallos S3:     {YELLOW}{self.s3_failures:>6}{RESET}")
        print(f"[EMOJI_REMOVIDO] Tamaño total:  {CYAN}{self.total_size_mb:>6.2f} MB{RESET}")
        print()
        
        # Estado actual
        print(f"{BOLD}[EMOJI_REMOVIDO] ESTADO ACTUAL:{RESET}")
        print(f"[EMOJI_REMOVIDO] Registro: {WHITE}{self.current_record}{RESET}")
        print(f"[EMOJI_REMOVIDO] Estado: {YELLOW}{self.current_status}{RESET}")
        print()
        
        # Velocidad de procesamiento
        if elapsed.total_seconds() > 0:
            records_per_sec = self.processed_records / elapsed.total_seconds()
            files_per_sec = self.files_uploaded / elapsed.total_seconds()
            mb_per_sec = self.total_size_mb / elapsed.total_seconds()
            
            print(f"{BOLD}[EMOJI_REMOVIDO] VELOCIDAD:{RESET}")
            print(f"[DATOS] Registros/seg: {records_per_sec:.2f}")
            print(f"[EMOJI_REMOVIDO] Archivos/seg:  {files_per_sec:.2f}")
            print(f"[EMOJI_REMOVIDO] MB/seg:        {mb_per_sec:.2f}")
            print()
        
        # Footer
        print(f"{CYAN}{'='*80}{RESET}")
        print(f"{WHITE}Presiona Ctrl+C para detener{RESET}")
        
        # Flush para asegurar que se muestre inmediatamente
        sys.stdout.flush()
        
    def show_final_report(self, stats: Dict[str, Any]):
        """Mostrar reporte final"""
        self.stop()
        
        c = self.colors
        
        print(f"\n{c['bold']}{c['green']}{'='*self.terminal_width}{c['reset']}")
        print(f"{c['bold']}{c['white']}[COMPLETADO] PROCESO COMPLETADO{c['reset']}")
        print(f"{c['bold']}{c['green']}{'='*self.terminal_width}{c['reset']}")
        print()
        
        # Estadísticas finales
        total = stats.get('processed_records', 0)
        successful = stats.get('successful_records', 0)
        failed = stats.get('failed_records', 0)
        s3_failures = stats.get('s3_failures', 0)
        db_failures = stats.get('db_failures', 0)
        
        print(f"{c['bold']}[DATOS] RESUMEN FINAL:{c['reset']}")
        print(f"   Total procesados: {total}")
        print(f"   {c['green']}[EXITOSO] Exitosos: {successful}{c['reset']}")
        print(f"   {c['red']}[ERROR] Fallidos: {failed}{c['reset']}")
        
        if s3_failures > 0:
            print(f"   {c['yellow']}[S3]  Fallos S3: {s3_failures}{c['reset']}")
        
        if db_failures > 0:
            print(f"   {c['yellow']}[BASE_DATOS]  Fallos DB: {db_failures}{c['reset']}")
        
        # Tasa de éxito
        if total > 0:
            success_rate = (successful / total) * 100
            color = c['green'] if success_rate >= 90 else c['yellow'] if success_rate >= 70 else c['red']
            print(f"   {color}[METRICAS] Tasa de éxito: {success_rate:.1f}%{c['reset']}")
        
        # Tiempo total
        if self.start_time:
            total_time = datetime.now() - self.start_time
            total_time_str = str(total_time).split('.')[0]
            print(f"   [TIEMPO]  Tiempo total: {total_time_str}")
            
            if total > 0:
                rate = total / total_time.total_seconds() * 60
                print(f"   [INICIANDO] Velocidad promedio: {rate:.1f} registros/min")
        
        print()
        print(f"{c['bold']}{c['green']}{'='*self.terminal_width}{c['reset']}")


def create_progress_monitor(total_records: int = 0) -> ProgressMonitor:
    """Factory function para crear monitor de progreso"""
    return ProgressMonitor(total_records)


if __name__ == "__main__":
    # Prueba del monitor
    monitor = create_progress_monitor(100)
    monitor.start_monitoring()
    
    try:
        # Simular progreso
        for i in range(100):
            time.sleep(0.1)
            stats = {
                'processed_records': i + 1,
                'successful_records': i,
                'failed_records': 1 if i > 50 else 0,
                'files_uploaded': (i + 1) * 3,
                's3_failures': 2 if i > 75 else 0,
                'total_size_mb': (i + 1) * 0.5
            }
            monitor.update_stats(stats)
            monitor.set_current_record(f"RAD{i+1:03d}", "Procesando archivos...")
            
    except KeyboardInterrupt:
        print("\n\nProceso interrumpido por el usuario")
    finally:
        final_stats = {
            'processed_records': 100,
            'successful_records': 99,
            'failed_records': 1,
            'files_uploaded': 300,
            's3_failures': 2,
            'total_size_mb': 50.0
        }
        monitor.show_final_report(final_stats)