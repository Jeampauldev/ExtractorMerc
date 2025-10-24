"""IPO Afinia - Implementación del Sistema IPO para Afinia
=====================================================

Implementación específica del sistema IPO para extraer datos
desde la plataforma Mercurio para la empresa Afinia.
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

@register_adapter(AdapterType.MERCURIO_DATA, Company.AFINIA)
class AfiniaDataAdapter(DataAdapter):
    """
    Adaptador específico para estructura de datos IPO de Afinia
    """
    
    def _load_company_config(self) -> Dict[str, Any]:
        """Carga configuración específica de Afinia"""
        return {
            'required_columns': [
                'fecha_incidente', 'circuito', 'tipo_falla',
                'kwh_perdidos', 'tiempo_duracion', 'descripcion'
            ],
            'date_format': '%Y-%m-%d',  # Afinia usa formato diferente
            'decimal_separator': '.',
            'encoding': 'latin-1'  # Afinia puede usar codificación diferente
        }
    
    async def get_credentials(self) -> Dict[str, str]:
        """Afinia no requiere credenciales específicas para datos"""
        return {}
    
    def validate_configuration(self) -> bool:
        """Valida configuración del adaptador de datos Afinia"""
        required_keys = ['required_columns', 'date_format']
        return all(key in self._config for key in required_keys)
    
    def get_field_mapping(self) -> Dict[str, str]:
        """Mapeo de campos Afinia a formato estándar"""
        return {
            'fecha_incidente': 'event_date',
            'circuito': 'circuit_code',
            'tipo_falla': 'loss_type',
            'kwh_perdidos': 'energy_lost_kwh',
            'tiempo_duracion': 'duration_minutes',
            'descripcion': 'cause',
            'impacto_economico': 'economic_value',
            'notas': 'observations',
            'zona': 'zone',  # Campo específico de Afinia
            'subestacion': 'substation'  # Campo específico de Afinia
        }
    
    def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma datos de Afinia al formato estándar"""
        field_mapping = self.get_field_mapping()
        transformed = {}
        
        for afinia_field, standard_field in field_mapping.items():
            if afinia_field in raw_data:
                value = raw_data[afinia_field]
                
                # Transformaciones específicas para Afinia
                if standard_field == 'event_date' and isinstance(value, str):
                    try:
                        transformed[standard_field] = datetime.strptime(
                            value, self._config['date_format']
                        ).date()
                    except ValueError:
                        transformed[standard_field] = None
                elif standard_field in ['energy_lost_kwh', 'economic_value']:
                    # Afinia ya usa punto como separador decimal
                    try:
                        transformed[standard_field] = float(value) if value else 0.0
                    except (ValueError, TypeError):
                        transformed[standard_field] = 0.0
                elif standard_field == 'duration_minutes' and isinstance(value, str):
                    # Afinia puede usar formato "HH:MM"
                    try:
                        if ':' in str(value):
                            hours, minutes = value.split(':')
                            transformed[standard_field] = int(hours) * 60 + int(minutes)
                        else:
                            transformed[standard_field] = int(float(value))
                    except (ValueError, TypeError):
                        transformed[standard_field] = 0
                else:
                    transformed[standard_field] = value
        
        return transformed
    
    def validate_data_format(self, data: Dict[str, Any]) -> bool:
        """Valida formato de datos específico de Afinia"""
        required_columns = self._config['required_columns']
        
        # Verificar que existan las columnas requeridas
        missing_columns = set(required_columns) - set(data.keys())
        if missing_columns:
            logger.warning(f"Columnas faltantes en datos Afinia: {missing_columns}")
            return False
        
        # Validaciones específicas de Afinia
        if 'fecha_incidente' in data and data['fecha_incidente']:
            try:
                datetime.strptime(str(data['fecha_incidente']), self._config['date_format'])
            except ValueError:
                logger.warning("Formato de fecha inválido en datos Afinia")
                return False
        
        return True

class AfiniaMercurioService(BaseMercurioService):
    """
    Servicio de procesamiento IPO específico para Afinia
    """
    
    def __init__(self):
        from src.core.adapters import AdapterFactory
        adapter = AdapterFactory.create_adapter(AdapterType.MERCURIO_DATA, Company.AFINIA)
        super().__init__(adapter)
        self.data_processor = IPODataProcessor("afinia")
    
    async def validate_ipo_data(self, ipo: IPODocument) -> Dict[str, Any]:
        """Valida datos IPO específicos de Afinia"""
        try:
            # Cargar archivo Excel (puede requerir encoding específico)
            df = pd.read_excel(ipo.file_path, encoding=self.adapter._config['encoding'])
            
            # Validar columnas requeridas para Afinia
            required_columns = self.adapter._config['required_columns']
            validation_result = self.data_processor.validate_required_columns(df, required_columns)
            
            if not validation_result['is_valid']:
                return validation_result
            
            # Validaciones específicas de Afinia
            afinia_validations = []
            
            # Validar formato de fechas (formato diferente a Air-e)
            date_column = 'fecha_incidente'
            if date_column in df.columns:
                invalid_dates = df[df[date_column].isna()].index.tolist()
                if invalid_dates:
                    afinia_validations.append(f"Fechas inválidas en filas: {invalid_dates[:10]}")
            
            # Validar códigos de subestación (específico de Afinia)
            if 'subestacion' in df.columns:
                empty_substations = df[df['subestacion'].isna()].index.tolist()
                if empty_substations:
                    afinia_validations.append(f"Subestaciones no especificadas en filas: {empty_substations[:10]}")
            
            # Validar zonas (específico de Afinia)
            if 'zona' in df.columns:
                valid_zones = ['ZONA1', 'ZONA2', 'ZONA3', 'ZONA4']  # Zonas válidas de Afinia
                invalid_zones = df[~df['zona'].isin(valid_zones)].index.tolist()
                if invalid_zones:
                    afinia_validations.append(f"Zonas inválidas en filas: {invalid_zones[:10]}")
            
            # Generar estadísticas
            stats = self.data_processor.generate_summary_stats(df)
            
            return {
                'is_valid': len(afinia_validations) == 0,
                'error_message': '; '.join(afinia_validations) if afinia_validations else None,
                'afinia_validations': afinia_validations,
                'statistics': stats,
                'total_records': len(df)
            }
            
        except Exception as e:
            self.logger.error(f"Error validando datos IPO Afinia: {e}")
            return {
                'is_valid': False,
                'error_message': str(e)
            }
    
    async def process_ipo_file(self, ipo: IPODocument) -> bool:
        """Procesa archivo IPO específico de Afinia"""
        try:
            # Cargar datos con encoding específico de Afinia
            df = pd.read_excel(ipo.file_path, encoding=self.adapter._config['encoding'])
            df_clean = self.data_processor.clean_data(df)
            
            # Transformar datos usando el adaptador
            transformed_rows = []
            for _, row in df_clean.iterrows():
                row_dict = row.to_dict()
                transformed_row = self.adapter.transform_data(row_dict)
                transformed_rows.append(transformed_row)
            
            # Crear DataFrame transformado
            df_transformed = pd.DataFrame(transformed_rows)
            
            # Procesamiento específico de Afinia
            df_processed = self._apply_afinia_business_rules(df_transformed)
            
            # Guardar datos procesados
            output_path = ipo.file_path.replace('.xlsx', '_processed.xlsx')
            df_processed.to_excel(output_path, index=False)
            
            self.logger.info(f"Archivo IPO Afinia procesado: {len(df_processed)} registros")
            return True
            
        except Exception as e:
            self.logger.error(f"Error procesando archivo IPO Afinia: {e}")
            return False
    
    def _apply_afinia_business_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica reglas de negocio específicas de Afinia"""
        try:
            # Regla 1: Clasificación por impacto (específico Afinia)
            df['impact_level'] = df['energy_lost_kwh'].apply(
                lambda x: 'CRITICO' if x > 2000 else 'ALTO' if x > 500 else 'MEDIO' if x > 50 else 'BAJO'
            )
            
            # Regla 2: Índice de criticidad por zona
            zone_weights = {'ZONA1': 1.5, 'ZONA2': 1.2, 'ZONA3': 1.0, 'ZONA4': 0.8}
            df['zone_weight'] = df.get('zone', 'ZONA3').map(zone_weights).fillna(1.0)
            df['criticality_index'] = df['energy_lost_kwh'] * df['zone_weight']
            
            # Regla 3: Categorización por tipo de falla Afinia
            afinia_fault_mapping = {
                'CORTO_CIRCUITO': 'SHORT_CIRCUIT',
                'SOBRECARGA': 'OVERLOAD',
                'FALLA_EQUIPO': 'EQUIPMENT_FAILURE',
                'MANTENIMIENTO': 'MAINTENANCE'
            }
            df['fault_category'] = df['loss_type'].map(afinia_fault_mapping).fillna('OTHER')
            
            # Regla 4: Cálculo de tiempo de respuesta esperado
            df['expected_response_time'] = df['impact_level'].apply(
                lambda x: 15 if x == 'CRITICO' else 30 if x == 'ALTO' else 60 if x == 'MEDIO' else 120
            )
            
            # Regla 5: Agregar metadatos de Afinia
            df['processed_date'] = datetime.now()
            df['company'] = 'afinia'
            df['processing_version'] = 'v2.0_afinia'
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error aplicando reglas de negocio Afinia: {e}")
            return df
    
    async def generate_reports(self, ipo: IPODocument) -> List[IPOReport]:
        """Genera reportes específicos para Afinia"""
        try:
            reports = []
            
            # Reporte 1: Análisis por zonas (específico Afinia)
            report1 = await self._generate_zone_analysis_report(ipo)
            if report1:
                reports.append(report1)
            
            # Reporte 2: Impacto por subestaciones
            report2 = await self._generate_substation_impact_report(ipo)
            if report2:
                reports.append(report2)
            
            # Reporte 3: Indicadores de calidad del servicio (específico Afinia)
            report3 = await self._generate_service_quality_report(ipo)
            if report3:
                reports.append(report3)
            
            # Reporte 4: Comparativo con meses anteriores
            report4 = await self._generate_comparative_report(ipo)
            if report4:
                reports.append(report4)
            
            self.logger.info(f"Se generaron {len(reports)} reportes para Afinia")
            return reports
            
        except Exception as e:
            self.logger.error(f"Error generando reportes Afinia: {e}")
            return []
    
    async def _generate_zone_analysis_report(self, ipo: IPODocument) -> IPOReport:
        """Genera reporte de análisis por zonas específico para Afinia"""
        # TODO: Implementar generación real de PDF
        report_id = f"afinia_zone_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path = f"/tmp/reports/afinia/{ipo.period}/zone_analysis_{report_id}.pdf"
        
        return IPOReport(
            id=report_id,
            ipo_document_id=ipo.id,
            report_type="zone_analysis",
            file_path=file_path,
            generation_date=datetime.now(),
            parameters={"company": "afinia", "period": ipo.period, "zones": ["ZONA1", "ZONA2", "ZONA3", "ZONA4"]}
        )
    
    async def _generate_substation_impact_report(self, ipo: IPODocument) -> IPOReport:
        """Genera reporte de impacto por subestaciones para Afinia"""
        # TODO: Implementar generación real de PDF
        report_id = f"afinia_substation_impact_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path = f"/tmp/reports/afinia/{ipo.period}/substation_impact_{report_id}.pdf"
        
        return IPOReport(
            id=report_id,
            ipo_document_id=ipo.id,
            report_type="substation_impact",
            file_path=file_path,
            generation_date=datetime.now(),
            parameters={"company": "afinia", "period": ipo.period}
        )
    
    async def _generate_service_quality_report(self, ipo: IPODocument) -> IPOReport:
        """Genera reporte de calidad del servicio específico para Afinia"""
        # TODO: Implementar generación real de PDF
        report_id = f"afinia_service_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path = f"/tmp/reports/afinia/{ipo.period}/service_quality_{report_id}.pdf"
        
        return IPOReport(
            id=report_id,
            ipo_document_id=ipo.id,
            report_type="service_quality",
            file_path=file_path,
            generation_date=datetime.now(),
            parameters={"company": "afinia", "period": ipo.period, "quality_indicators": True}
        )
    
    async def _generate_comparative_report(self, ipo: IPODocument) -> IPOReport:
        """Genera reporte comparativo para Afinia"""
        # TODO: Implementar generación real de PDF
        report_id = f"afinia_comparative_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_path = f"/tmp/reports/afinia/{ipo.period}/comparative_{report_id}.pdf"
        
        return IPOReport(
            id=report_id,
            ipo_document_id=ipo.id,
            report_type="comparative",
            file_path=file_path,
            generation_date=datetime.now(),
            parameters={"company": "afinia", "period": ipo.period, "compare_months": 3}
        )
    
    # Método upload_to_s3 heredado de BaseMercurioService
    # Usa el servicio S3 centralizado en src.core.s3_service