#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALIZADOR DE RENDIMIENTO DEL SISTEMA DE EXTRACCIÓN
===================================================

Analiza logs, estadísticas y rendimiento del sistema de extracción de Afinia/Aire.
Genera reportes detallados y proyecciones de escalabilidad.

Features:
- Análisis de tiempos de ejecución por componente
- Detección de cuellos de botella
- Proyecciones para diferentes volúmenes de datos
- Estadísticas de éxito/fallo
- Análisis de formato de logs
- Generación de reportes en JSON y texto
"""

import os
import re
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import statistics

@dataclass
class ComponentMetrics:
    """Métricas de un componente específico"""
    name: str
    total_executions: int = 0
    success_count: int = 0
    failed_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    bottleneck_score: float = 0.0

@dataclass
class ExtrationSession:
    """Sesión de extracción completa"""
    start_time: str
    end_time: str
    duration: float
    success: bool
    records_processed: int = 0
    files_downloaded: int = 0
    pqrs_processed: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class PerformanceAnalyzer:
    """Analizador de rendimiento del sistema"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.logs_dir = self.data_dir / "logs"
        self.results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'format_analysis': {},
            'performance_metrics': {},
            'component_analysis': {},
            'session_analysis': {},
            'projections': {},
            'recommendations': []
        }
        
    def analyze_log_format(self) -> Dict[str, Any]:
        """Analiza el formato de los logs para verificar profesionalización"""
        print("[EMOJI_REMOVIDO] Analizando formato de logs...")
        
        format_stats = {
            'professional_format_count': 0,
            'legacy_format_count': 0,
            'total_lines': 0,
            'format_compliance': 0.0,
            'professional_pattern': r'\[\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}\]\[[\w]+\]\[[\w]+\]\[[\w]+\]\[[\w]+\] - .*',
            'legacy_patterns': [
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+ - [\w\.]+ - [\w]+ - .*',
                r'\[[\w-]+\] [\w]+: .*'
            ],
            'samples': {
                'professional': [],
                'legacy': []
            }
        }
        
        log_files = list(self.logs_dir.glob("*.log"))
        professional_pattern = re.compile(format_stats['professional_pattern'])
        legacy_patterns = [re.compile(pattern) for pattern in format_stats['legacy_patterns']]
        
        for log_file in log_files:
            print(f"  [EMOJI_REMOVIDO] Analizando: {log_file.name}")
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                            
                        format_stats['total_lines'] += 1
                        
                        # Verificar formato profesional
                        if professional_pattern.match(line):
                            format_stats['professional_format_count'] += 1
                            if len(format_stats['samples']['professional']) < 3:
                                format_stats['samples']['professional'].append(line)
                        else:
                            # Verificar formatos legacy
                            is_legacy = False
                            for legacy_pattern in legacy_patterns:
                                if legacy_pattern.match(line):
                                    format_stats['legacy_format_count'] += 1
                                    is_legacy = True
                                    if len(format_stats['samples']['legacy']) < 3:
                                        format_stats['samples']['legacy'].append(line)
                                    break
                            
                            if not is_legacy:
                                # Línea que no coincide con ningún formato conocido
                                if len(format_stats['samples']['legacy']) < 5:
                                    format_stats['samples']['legacy'].append(f"UNKNOWN: {line}")
                                    
            except Exception as e:
                print(f"  [ERROR] Error leyendo {log_file.name}: {e}")
        
        # Calcular compliance
        if format_stats['total_lines'] > 0:
            format_stats['format_compliance'] = (
                format_stats['professional_format_count'] / format_stats['total_lines'] * 100
            )
        
        print(f"  [EXITOSO] Formato profesional: {format_stats['professional_format_count']} líneas")
        print(f"  [DATOS] Compliance: {format_stats['format_compliance']:.1f}%")
        
        return format_stats

    def extract_component_metrics(self) -> Dict[str, ComponentMetrics]:
        """Extrae métricas por componente de los logs"""
        print("[CONFIGURACION] Analizando métricas por componente...")
        
        components = {}
        timestamp_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2})\]')
        component_pattern = re.compile(r'\[[\w]+\]\[([\w]+)\]\[([\w]+)\]\[[\w]+\]')
        
        log_files = list(self.logs_dir.glob("*.log"))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Extraer componente
                    component_match = component_pattern.search(line)
                    if not component_match:
                        continue
                        
                    core = component_match.group(1)
                    component = component_match.group(2)
                    comp_name = f"{core}.{component}"
                    
                    if comp_name not in components:
                        components[comp_name] = ComponentMetrics(name=comp_name)
                    
                    comp = components[comp_name]
                    comp.total_executions += 1
                    
                    # Detectar éxito/fallo
                    if 'EXITOSO' in line or 'SUCCESS' in line:
                        comp.success_count += 1
                    elif 'ERROR' in line or 'FAILED' in line:
                        comp.failed_count += 1
                        
            except Exception as e:
                print(f"  [ERROR] Error procesando {log_file.name}: {e}")
        
        # Calcular métricas derivadas
        for comp in components.values():
            if comp.total_executions > 0:
                comp.avg_time = comp.total_time / comp.total_executions
            comp.bottleneck_score = comp.total_executions * comp.avg_time
            
        print(f"  [DATOS] Componentes analizados: {len(components)}")
        return components

    def analyze_extraction_sessions(self) -> List[ExtrationSession]:
        """Analiza sesiones completas de extracción"""
        print("[EMOJI_REMOVIDO] Analizando sesiones de extracción...")
        
        sessions = []
        session_pattern = re.compile(r'INICIANDO EXTRACCIÓN DE (AFINIA|AIRE)')
        duration_pattern = re.compile(r'DURACION.*?(\d+\.?\d*)\s+segundos')
        files_pattern = re.compile(r'ARCHIVOS.*?(\d+)')
        pqr_pattern = re.compile(r'PQRs procesados.*?(\d+)')
        
        log_files = list(self.logs_dir.glob("*.log"))
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                current_session = None
                
                for line in lines:
                    line = line.strip()
                    
                    # Detectar inicio de sesión
                    if session_pattern.search(line):
                        if current_session:
                            sessions.append(current_session)
                            
                        current_session = ExtrationSession(
                            start_time="",
                            end_time="",
                            duration=0.0,
                            success=False
                        )
                        
                        # Extraer timestamp de inicio
                        timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2})\]', line)
                        if timestamp_match:
                            current_session.start_time = timestamp_match.group(1)
                    
                    # Procesar línea de sesión actual
                    if current_session:
                        # Duración
                        duration_match = duration_pattern.search(line)
                        if duration_match:
                            current_session.duration = float(duration_match.group(1))
                        
                        # Archivos descargados
                        files_match = files_pattern.search(line)
                        if files_match and 'ARCHIVOS' in line:
                            current_session.files_downloaded = int(files_match.group(1))
                        
                        # PQRs procesados
                        pqr_match = pqr_pattern.search(line)
                        if pqr_match:
                            current_session.pqrs_processed = int(pqr_match.group(1))
                        
                        # Éxito/Fallo
                        if 'EXTRACCIÓN COMPLETADA EXITOSAMENTE' in line:
                            current_session.success = True
                            timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2})\]', line)
                            if timestamp_match:
                                current_session.end_time = timestamp_match.group(1)
                        
                        # Errores
                        if 'ERROR' in line and 'Error' in line:
                            current_session.errors.append(line)
                
                # Agregar última sesión
                if current_session:
                    sessions.append(current_session)
                    
            except Exception as e:
                print(f"  [ERROR] Error procesando {log_file.name}: {e}")
        
        print(f"  [DATOS] Sesiones encontradas: {len(sessions)}")
        return sessions

    def calculate_projections(self, sessions: List[ExtrationSession]) -> Dict[str, Any]:
        """Calcula proyecciones para diferentes escenarios"""
        print("[RESULTADO] Calculando proyecciones...")
        
        if not sessions:
            return {"error": "No hay sesiones para analizar"}
        
        # Filtrar sesiones exitosas
        successful_sessions = [s for s in sessions if s.success and s.duration > 0]
        
        if not successful_sessions:
            return {"error": "No hay sesiones exitosas para analizar"}
        
        # Métricas básicas
        durations = [s.duration for s in successful_sessions]
        pqrs_per_session = [s.pqrs_processed for s in successful_sessions if s.pqrs_processed > 0]
        
        if not pqrs_per_session:
            pqrs_per_session = [10]  # Default fallback
        
        avg_duration = statistics.mean(durations)
        avg_pqrs = statistics.mean(pqrs_per_session)
        time_per_pqr = avg_duration / avg_pqrs if avg_pqrs > 0 else avg_duration
        
        # Proyecciones para diferentes escenarios
        projections = {
            'current_performance': {
                'avg_session_duration_seconds': round(avg_duration, 1),
                'avg_pqrs_per_session': round(avg_pqrs, 1),
                'avg_time_per_pqr_seconds': round(time_per_pqr, 1),
                'sessions_analyzed': len(successful_sessions)
            },
            'scenario_200_records_15_pagination': {
                'total_records': 200,
                'records_per_page': 15,
                'total_pages': 14,  # ceil(200/15)
                'estimated_total_duration_minutes': 0,
                'estimated_sessions_needed': 0,
                'breakdown': {}
            },
            'optimization_targets': {
                'current_bottlenecks': [],
                'time_reduction_opportunities': {},
                'scalability_recommendations': []
            }
        }
        
        # Calcular escenario específico: 200 registros con 15 por página
        scenario = projections['scenario_200_records_15_pagination']
        
        # Estimar sesiones necesarias (asumiendo 10 registros por sesión promedio)
        sessions_needed = max(1, round(scenario['total_records'] / avg_pqrs))
        scenario['estimated_sessions_needed'] = sessions_needed
        
        # Tiempo total estimado
        total_time_seconds = sessions_needed * avg_duration
        scenario['estimated_total_duration_minutes'] = round(total_time_seconds / 60, 1)
        
        # Desglose detallado
        scenario['breakdown'] = {
            'login_and_setup_per_session': round(avg_duration * 0.3, 1),  # 30% setup
            'pqr_processing_per_session': round(avg_duration * 0.7, 1),   # 70% processing
            'parallel_optimization_potential': round(total_time_seconds * 0.4, 1),  # 40% reducible
            'estimated_with_optimization_minutes': round((total_time_seconds * 0.6) / 60, 1)
        }
        
        # Recomendaciones de optimización
        projections['optimization_targets']['scalability_recommendations'] = [
            f"Para procesar 200 registros eficientemente, considerar:",
            f"1. Paralelización: 2-3 sesiones concurrentes",
            f"2. Optimización de timeouts y esperas",
            f"3. Mejora del cache de autenticación",
            f"4. Reducción de screenshots innecesarios"
        ]
        
        print(f"  [METRICAS] Proyección 200 registros: ~{scenario['estimated_total_duration_minutes']} minutos")
        print(f"  [RESULTADO] Con optimización: ~{scenario['breakdown']['estimated_with_optimization_minutes']} minutos")
        
        return projections

    def generate_recommendations(self, format_stats: Dict, components: Dict, sessions: List) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        # Recomendaciones de formato
        if format_stats.get('format_compliance', 0) < 90:
            recommendations.append(
                f"[EMOJI_REMOVIDO] CRÍTICO: Formato de logging al {format_stats['format_compliance']:.1f}%. "
                f"Migrar {format_stats['legacy_format_count']} líneas restantes al formato profesional."
            )
        else:
            recommendations.append("[EXITOSO] EXCELENTE: Formato de logging profesional implementado correctamente.")
        
        # Recomendaciones de rendimiento
        successful_sessions = [s for s in sessions if s.success]
        if successful_sessions:
            avg_duration = statistics.mean([s.duration for s in successful_sessions])
            if avg_duration > 180:  # > 3 minutos
                recommendations.append(
                    f"[EMOJI_REMOVIDO] OPTIMIZACIÓN: Sesiones promedio de {avg_duration:.1f}s. "
                    f"Considerar optimización de timeouts y paralelización."
                )
        
        # Recomendaciones de componentes
        bottleneck_components = sorted(
            components.values(), 
            key=lambda x: x.bottleneck_score, 
            reverse=True
        )[:3]
        
        for comp in bottleneck_components:
            if comp.bottleneck_score > 100:
                recommendations.append(
                    f"[EMOJI_REMOVIDO] CUELLO DE BOTELLA: {comp.name} con {comp.total_executions} ejecuciones. "
                    f"Revisar optimización."
                )
        
        return recommendations

    def run_analysis(self) -> Dict[str, Any]:
        """Ejecuta el análisis completo"""
        print("=" * 60)
        print("[DATOS] ANÁLISIS DE RENDIMIENTO DEL SISTEMA DE EXTRACCIÓN")
        print("=" * 60)
        
        # 1. Análisis de formato de logs
        format_stats = self.analyze_log_format()
        self.results['format_analysis'] = format_stats
        
        # 2. Análisis de componentes
        components = self.extract_component_metrics()
        self.results['component_analysis'] = {
            name: {
                'total_executions': comp.total_executions,
                'success_count': comp.success_count,
                'failed_count': comp.failed_count,
                'success_rate': comp.success_count / max(1, comp.total_executions) * 100,
                'bottleneck_score': comp.bottleneck_score
            }
            for name, comp in components.items()
        }
        
        # 3. Análisis de sesiones
        sessions = self.analyze_extraction_sessions()
        self.results['session_analysis'] = {
            'total_sessions': len(sessions),
            'successful_sessions': len([s for s in sessions if s.success]),
            'average_duration': statistics.mean([s.duration for s in sessions if s.duration > 0]) if sessions else 0,
            'total_pqrs_processed': sum([s.pqrs_processed for s in sessions]),
            'sessions': [
                {
                    'start_time': s.start_time,
                    'duration': s.duration,
                    'success': s.success,
                    'pqrs_processed': s.pqrs_processed,
                    'files_downloaded': s.files_downloaded
                }
                for s in sessions
            ]
        }
        
        # 4. Proyecciones
        projections = self.calculate_projections(sessions)
        self.results['projections'] = projections
        
        # 5. Recomendaciones
        recommendations = self.generate_recommendations(format_stats, components, sessions)
        self.results['recommendations'] = recommendations
        
        return self.results

    def save_report(self, output_file: str = None) -> str:
        """Guarda el reporte de análisis"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"performance_analysis_{timestamp}.json"
        
        output_path = Path(output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        return str(output_path)

    def print_summary(self):
        """Imprime resumen del análisis"""
        print("\n" + "=" * 60)
        print("[EMOJI_REMOVIDO] RESUMEN DEL ANÁLISIS")
        print("=" * 60)
        
        # Formato de logs
        format_analysis = self.results.get('format_analysis', {})
        print(f"[EMOJI_REMOVIDO] FORMATO DE LOGS:")
        print(f"   • Compliance: {format_analysis.get('format_compliance', 0):.1f}%")
        print(f"   • Profesional: {format_analysis.get('professional_format_count', 0)} líneas")
        print(f"   • Legacy: {format_analysis.get('legacy_format_count', 0)} líneas")
        
        # Sesiones
        session_analysis = self.results.get('session_analysis', {})
        print(f"\n[EMOJI_REMOVIDO] SESIONES DE EXTRACCIÓN:")
        print(f"   • Total: {session_analysis.get('total_sessions', 0)}")
        print(f"   • Exitosas: {session_analysis.get('successful_sessions', 0)}")
        print(f"   • Duración promedio: {session_analysis.get('average_duration', 0):.1f}s")
        print(f"   • PQRs procesados: {session_analysis.get('total_pqrs_processed', 0)}")
        
        # Proyecciones
        projections = self.results.get('projections', {})
        scenario = projections.get('scenario_200_records_15_pagination', {})
        if scenario:
            print(f"\n[RESULTADO] PROYECCIÓN (200 REGISTROS):")
            print(f"   • Tiempo estimado: {scenario.get('estimated_total_duration_minutes', 0)} minutos")
            print(f"   • Sesiones necesarias: {scenario.get('estimated_sessions_needed', 0)}")
            breakdown = scenario.get('breakdown', {})
            if breakdown:
                print(f"   • Con optimización: {breakdown.get('estimated_with_optimization_minutes', 0)} minutos")
        
        # Recomendaciones
        print(f"\n[INFO] RECOMENDACIONES:")
        for rec in self.results.get('recommendations', []):
            print(f"   {rec}")
        
        print("\n" + "=" * 60)

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Analizador de rendimiento del sistema de extracción')
    parser.add_argument('--data-dir', default='data', 
                       help='Directorio de datos (default: data)')
    parser.add_argument('--output', '-o', 
                       help='Archivo de salida del reporte JSON')
    parser.add_argument('--summary-only', action='store_true',
                       help='Solo mostrar resumen sin generar reporte completo')
    
    args = parser.parse_args()
    
    # Crear analizador
    analyzer = PerformanceAnalyzer(args.data_dir)
    
    # Ejecutar análisis
    results = analyzer.run_analysis()
    
    # Mostrar resumen
    analyzer.print_summary()
    
    # Guardar reporte si se solicita
    if not args.summary_only:
        report_file = analyzer.save_report(args.output)
        print(f"\n[EMOJI_REMOVIDO] Reporte completo guardado en: {report_file}")
    
    return results

if __name__ == '__main__':
    main()