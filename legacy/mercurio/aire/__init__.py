"""IPO Air-e - Implementación del Sistema IPO para Air-e
===================================================

Implementación específica del sistema IPO para extraer datos
desde la plataforma Mercurio para la empresa Air-e.
Incluye adaptadores de datos y lógica de negocio específica.
"""

from typing import Dict, List, Any
import pandas as pd
# Importación condicional de boto3 para modo local
import os
try:
    if os.getenv('MERCURIO_LOCAL_MODE') != 'true':
        import boto3
    else:
        boto3 = None
except ImportError:
    boto3 = None
from datetime import datetime

from src.core.adapters import DataAdapter, AdapterType, register_adapter
from src.mercurio.base import BaseMercurioService, IPODocument, IPOReport, IPODataProcessor
from config.centralized_config import Company
from src.core.logging import get_logger

logger = get_logger(__name__)

@register_adapter(AdapterType.MERCURIO_DATA, Company.AIRE)
class AireDataAdapter(DataAdapter):
    """
    Adaptador específico para estructura de datos IPO de Air-e
    """
    
    def _load_company_config(self) -> Dict[str, Any]:
        """Carga configuración específica de Air-e"""
        return {
            'required_columns': [
                'fecha_evento', 'codigo_circuito', 'tipo_perdida',
                'energia_perdida_kwh', 'duracion_minutos', 'causa'
            ],
            'date_format': '%d/%m/%Y',
            'decimal_separator': ',',
            'encoding': 'utf-8'
        }
    
    async def get_credentials(self) -> Dict[str, str]:
        """Air-e no requiere credenciales específicas para datos"""
        return {}
    
    def validate_configuration(self) -> bool:
        """Valida configuración del adaptador de datos Air-e"""
        required_keys = ['required_columns', 'date_format']
        return all(key in self._config for key in required_keys)
    
    def get_field_mapping(self) -> Dict[str, str]:
        """Mapeo de campos Air-e a formato estándar"""
        return {
            'fecha_evento': 'event_date',
            'codigo_circuito': 'circuit_code',
            'tipo_perdida': 'loss_type',
            'energia_perdida_kwh': 'energy_lost_kwh',
            'duracion_minutos': 'duration_minutes',
            'causa': 'cause',
            'valor_economico': 'economic_value',
            'observaciones': 'observations'
        }
    
    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma datos de Air-e al formato estándar"""
        field_mapping = self.get_field_mapping()
        transformed = {}
        
        for air_e_field, standard_field in field_mapping.items():
            if air_e_field in raw_data:
                value = raw_data[air_e_field]
                
                # Transformaciones específicas para Air-e
                if standard_field == 'event_date' and isinstance(value, str):
                    try:
                        transformed[standard_field] = datetime.strptime(
                            value, self._config['date_format']
                        ).date()
                    except ValueError:
                        transformed[standard_field] = None
                elif standard_field in ['energy_lost_kwh', 'economic_value'] and isinstance(value, str):
                    # Air-e usa coma como separador decimal
                    try:
                        transformed[standard_field] = float(value.replace(',', '.'))
                    except ValueError:
                        transformed[standard_field] = 0.0
                else:
                    transformed[standard_field] = value
        
        return transformed
    
    def validate_data_format(self, data: Dict[str, Any]) -> bool:
        """Valida formato de datos específico de Air-e"""
        required_columns = self._config['required_columns']
        
        # Verificar que existan las columnas requeridas
        missing_columns = set(required_columns) - set(data.keys())
        if missing_columns:
            logger.warning(f"Columnas faltantes en datos Air-e: {missing_columns}")
            return False
        
        # Validaciones específicas de Air-e
        if 'fecha_evento' in data and data['fecha_evento']:
            try:
                datetime.strptime(str(data['fecha_evento']), self._config['date_format'])
            except ValueError:
                logger.warning("Formato de fecha inválido en datos Air-e")
                return False
        
        return True

class AireMercurioService(BaseMercurioService):
    """
    Servicio de procesamiento IPO específico para Air-e
    """
    
    def __init__(self):
        from src.core.adapters import AdapterFactory
        adapter = AdapterFactory.create_adapter(AdapterType.MERCURIO_DATA, Company.AIRE)
        super().__init__(adapter)
        self.data_processor = IPODataProcessor("aire")
    
    async def validate_ipo_data(self, ipo: IPODocument) -> Dict[str, Any]:
        """Valida datos IPO específicos de Air-e"""
        try:
            # Cargar archivo Excel
            df = self.data_processor.load_excel_file(ipo.file_path)
            
            # Validar columnas requeridas para Air-e
            required_columns = self.adapter._config['required_columns']
            validation_result = self.data_processor.validate_required_columns(df, required_columns)
            
            if not validation_result['is_valid']:
                return validation_result
            
            # Validaciones específicas de Air-e
            air_e_validations = []
            
            # Validar formato de fechas
            date_column = 'fecha_evento'
            if date_column in df.columns:
                invalid_dates = df[df[date_column].isna()].index.tolist()
                if invalid_dates:
                    air_e_validations.append(f"Fechas inválidas en filas: {invalid_dates[:10]}")
            
            # Validar valores de energía
            energy_column = 'energia_perdida_kwh'
            if energy_column in df.columns:
                negative_energy = df[df[energy_column] < 0].index.tolist()
                if negative_energy:
                    air_e_validations.append(f"Valores de energía negativos en filas: {negative_energy[:10]}")
            
            # Generar estadísticas
            stats = self.data_processor.generate_summary_stats(df)
            
            return {
                'is_valid': len(air_e_validations) == 0,
                'error_message': '; '.join(air_e_validations) if air_e_validations else None,
                'air_e_validations': air_e_validations,
                'statistics': stats,
                'total_records': len(df)
            }
            
        except Exception as e:
            self.logger.error(f"Error validando datos IPO Air-e: {e}")
            return {
                'is_valid': False,
                'error_message': str(e)
            }
    
    async def process_ipo_file(self, ipo: IPODocument) -> bool:
        """Procesa archivo IPO específico de Air-e"""
        try:
            # Cargar y limpiar datos
            df = self.data_processor.load_excel_file(ipo.file_path)
            df_clean = self.data_processor.clean_data(df)
            
            # Transformar datos usando el adaptador
            transformed_rows = []
            for _, row in df_clean.iterrows():
                row_dict = row.to_dict()
                transformed_row = self.adapter.transform_data(row_dict)
                transformed_rows.append(transformed_row)
            
            # Crear DataFrame transformado
            df_transformed = pd.DataFrame(transformed_rows)
            
            # Procesamiento específico de Air-e
            df_processed = self._apply_aire_business_rules(df_transformed)
            
            # Guardar datos procesados
            output_path = ipo.file_path.replace('.xlsx', '_processed.xlsx')
            df_processed.to_excel(output_path, index=False)
            
            self.logger.info(f"Archivo IPO Air-e procesado: {len(df_processed)} registros")
            return True
            
        except Exception as e:
            self.logger.error(f"Error procesando archivo IPO Air-e: {e}")
            return False
    
    def _apply_aire_business_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica reglas de negocio específicas de Air-e"""
        try:
            # Regla 1: Categorizar pérdidas por magnitud
            df['loss_category'] = df['energy_lost_kwh'].apply(
                lambda x: 'HIGH' if x > 1000 else 'MEDIUM' if x > 100 else 'LOW'
            )
            
            # Regla 2: Calcular prioridad basada en duración y energía
            df['priority_score'] = (
                df['energy_lost_kwh'] * 0.7 + 
                df['duration_minutes'] * 0.3
            )
            
            # Regla 3: Clasificar por tipo de circuito Air-e
            df['circuit_type'] = df['circuit_code'].apply(
                lambda x: 'PRIMARY' if str(x).startswith('P') else 'SECONDARY'
            )
            
            # Regla 4: Agregar timestamp de procesamiento
            df['processed_date'] = datetime.now()
            df['company'] = 'aire'
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error aplicando reglas de negocio Air-e: {e}")
            return df
    
    async def generate_reports(self, ipo: IPODocument) -> List[IPOReport]:
        """Genera reportes específicos para Air-e"""
        try:
            reports = []
            
            # Reporte 1: Resumen de pérdidas por tipo
            report1 = await self._generate_loss_summary_report(ipo)
            if report1:
                reports.append(report1)
            
            # Reporte 2: Análisis de circuitos críticos
            report2 = await self._generate_critical_circuits_report(ipo)
            if report2:
                reports.append(report2)
            
            # Reporte 3: Tendencias mensuales (específico Air-e)
            report3 = await self._generate_monthly_trends_report(ipo)
            if report3:
                reports.append(report3)
            
            self.logger.info(f"Se generaron {len(reports)} reportes para Air-e")
            return reports
            
        except Exception as e:
            self.logger.error(f"Error generando reportes Air-e: {e}")
            return []
    
    async def _generate_loss_summary_report(self, ipo: IPODocument) -> IPOReport:
        """Genera reporte resumen de pérdidas para Air-e"""
        # TODO: Implementar generación real de PDF
        report_id = f"aire_loss_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path = f"/tmp/reports/aire/{ipo.period}/loss_summary_{report_id}.pdf"
        
        return IPOReport(
            id=report_id,
            ipo_document_id=ipo.id,
            report_type="loss_summary",
            file_path=file_path,
            generation_date=datetime.now(),
            parameters={"company": "aire", "period": ipo.period}
        )
    
    async def _generate_critical_circuits_report(self, ipo: IPODocument) -> IPOReport:
        """Genera reporte de circuitos críticos para Air-e"""
        # TODO: Implementar generación real de PDF
        report_id = f"aire_critical_circuits_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path = f"/tmp/reports/aire/{ipo.period}/critical_circuits_{report_id}.pdf"
        
        return IPOReport(
            id=report_id,
            ipo_document_id=ipo.id,
            report_type="critical_circuits",
            file_path=file_path,
            generation_date=datetime.now(),
            parameters={"company": "aire", "period": ipo.period}
        )
    
    async def _generate_monthly_trends_report(self, ipo: IPODocument) -> IPOReport:
        """Genera reporte de tendencias mensuales específico para Air-e"""
        # TODO: Implementar generación real de PDF
        report_id = f"aire_monthly_trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path = f"/tmp/reports/aire/{ipo.period}/monthly_trends_{report_id}.pdf"
        
        return IPOReport(
            id=report_id,
            ipo_document_id=ipo.id,
            report_type="monthly_trends",
            file_path=file_path,
            generation_date=datetime.now(),
            parameters={"company": "aire", "period": ipo.period, "aire_specific": True}
        )
    
    # Método upload_to_s3 heredado de BaseMercurioService
    # Usa el servicio S3 centralizado en src.core.s3_service