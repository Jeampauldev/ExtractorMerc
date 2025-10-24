"""
Data Processor - Procesador de Datos
===================================

Procesador centralizado de datos para archivos CSV y JSON
extraídos de las plataformas de Mercurio.
"""

import os
import json
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Procesador centralizado de datos para Mercurio.
    
    Maneja la limpieza, transformación y validación de datos
    extraídos de las plataformas de Afinia y Aire.
    """
    
    def __init__(self, company: str):
        self.company = company.lower()
        self.processed_files = []
        self.errors = []
        
        # Configuraciones específicas por empresa
        self.processing_configs = {
            "afinia": {
                "csv_columns": {
                    "required": ["RADICADO", "FECHA", "TIPO_DOCUMENTO", "ESTADO"],
                    "optional": ["OBSERVACIONES", "USUARIO", "AREA"]
                },
                "date_formats": ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"],
                "encoding": "utf-8"
            },
            "aire": {
                "csv_columns": {
                    "required": ["RADICADO", "FECHA", "TIPO_DOCUMENTO", "ESTADO"],
                    "optional": ["OBSERVACIONES", "USUARIO", "AREA"]
                },
                "date_formats": ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"],
                "encoding": "utf-8"
            }
        }
    
    def process_csv_files(self, csv_files: List[str], output_dir: str) -> List[Dict[str, Any]]:
        """
        Procesar archivos CSV extraídos.
        
        Args:
            csv_files: Lista de rutas de archivos CSV
            output_dir: Directorio de salida para archivos procesados
            
        Returns:
            List[Dict]: Lista de resultados de procesamiento
        """
        results = []
        
        for csv_file in csv_files:
            try:
                logger.info(f"[{self.company.upper()}] Procesando CSV: {csv_file}")
                
                # Leer archivo CSV
                df = self._read_csv_file(csv_file)
                if df is None:
                    continue
                
                # Limpiar y validar datos
                df_cleaned = self._clean_dataframe(df)
                
                # Transformar datos
                df_transformed = self._transform_dataframe(df_cleaned)
                
                # Generar archivo de salida
                output_file = self._generate_output_file(df_transformed, csv_file, output_dir)
                
                # Generar estadísticas
                stats = self._generate_statistics(df_transformed)
                
                result = {
                    "input_file": csv_file,
                    "output_file": output_file,
                    "records_processed": len(df_transformed),
                    "statistics": stats,
                    "status": "success"
                }
                
                results.append(result)
                self.processed_files.append(output_file)
                
                logger.info(f"[{self.company.upper()}] CSV procesado exitosamente: {len(df_transformed)} registros")
                
            except Exception as e:
                error_msg = f"Error procesando {csv_file}: {str(e)}"
                logger.error(f"[{self.company.upper()}] {error_msg}")
                self.errors.append(error_msg)
                
                results.append({
                    "input_file": csv_file,
                    "output_file": None,
                    "records_processed": 0,
                    "statistics": {},
                    "status": "error",
                    "error": error_msg
                })
        
        return results
    
    def process_json_data(self, json_data: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
        """
        Procesar datos JSON extraídos.
        
        Args:
            json_data: Datos JSON a procesar
            output_dir: Directorio de salida
            
        Returns:
            Dict: Resultado del procesamiento
        """
        try:
            logger.info(f"[{self.company.upper()}] Procesando datos JSON")
            
            # Validar estructura JSON
            validated_data = self._validate_json_structure(json_data)
            
            # Transformar datos JSON
            transformed_data = self._transform_json_data(validated_data)
            
            # Guardar JSON procesado
            output_file = os.path.join(output_dir, f"processed_data_{self.company}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(transformed_data, f, indent=2, ensure_ascii=False)
            
            self.processed_files.append(output_file)
            
            result = {
                "output_file": output_file,
                "records_processed": len(transformed_data.get("records", [])),
                "status": "success"
            }
            
            logger.info(f"[{self.company.upper()}] JSON procesado exitosamente")
            return result
            
        except Exception as e:
            error_msg = f"Error procesando JSON: {str(e)}"
            logger.error(f"[{self.company.upper()}] {error_msg}")
            self.errors.append(error_msg)
            
            return {
                "output_file": None,
                "records_processed": 0,
                "status": "error",
                "error": error_msg
            }
    
    def _read_csv_file(self, csv_file: str) -> Optional[pd.DataFrame]:
        """Leer archivo CSV con manejo de encoding"""
        config = self.processing_configs.get(self.company, {})
        encoding = config.get("encoding", "utf-8")
        
        # Intentar diferentes encodings
        encodings = [encoding, "utf-8", "latin-1", "cp1252"]
        
        for enc in encodings:
            try:
                df = pd.read_csv(csv_file, encoding=enc)
                logger.debug(f"[{self.company.upper()}] CSV leído con encoding: {enc}")
                return df
            except Exception as e:
                logger.debug(f"[{self.company.upper()}] Falló encoding {enc}: {str(e)}")
                continue
        
        logger.error(f"[{self.company.upper()}] No se pudo leer el archivo CSV con ningún encoding")
        return None
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpiar y validar DataFrame"""
        # Crear copia para no modificar original
        df_clean = df.copy()
        
        # Eliminar filas completamente vacías
        df_clean = df_clean.dropna(how='all')
        
        # Limpiar espacios en blanco
        for col in df_clean.select_dtypes(include=['object']).columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
        
        # Reemplazar valores vacíos
        df_clean = df_clean.replace(['', 'nan', 'NaN', 'null'], pd.NA)
        
        # Validar columnas requeridas
        config = self.processing_configs.get(self.company, {})
        required_cols = config.get("csv_columns", {}).get("required", [])
        
        missing_cols = [col for col in required_cols if col not in df_clean.columns]
        if missing_cols:
            logger.warning(f"[{self.company.upper()}] Columnas faltantes: {missing_cols}")
        
        return df_clean
    
    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transformar DataFrame según reglas de negocio"""
        df_transformed = df.copy()
        
        # Transformar fechas
        df_transformed = self._transform_dates(df_transformed)
        
        # Normalizar estados
        df_transformed = self._normalize_status(df_transformed)
        
        # Agregar metadatos
        df_transformed['processed_at'] = datetime.now().isoformat()
        df_transformed['company'] = self.company.upper()
        
        return df_transformed
    
    def _transform_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transformar columnas de fecha"""
        date_columns = ['FECHA', 'fecha', 'Date', 'date']
        config = self.processing_configs.get(self.company, {})
        date_formats = config.get("date_formats", ["%d/%m/%Y"])
        
        for col in date_columns:
            if col in df.columns:
                for date_format in date_formats:
                    try:
                        df[col] = pd.to_datetime(df[col], format=date_format, errors='coerce')
                        logger.debug(f"[{self.company.upper()}] Fechas transformadas en columna {col}")
                        break
                    except Exception:
                        continue
        
        return df
    
    def _normalize_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizar valores de estado"""
        status_columns = ['ESTADO', 'estado', 'Status', 'status']
        
        # Mapeo de estados
        status_mapping = {
            'pendiente': 'PENDIENTE',
            'en proceso': 'EN_PROCESO',
            'completado': 'COMPLETADO',
            'cerrado': 'CERRADO',
            'cancelado': 'CANCELADO'
        }
        
        for col in status_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.lower().map(status_mapping).fillna(df[col])
        
        return df
    
    def _generate_output_file(self, df: pd.DataFrame, input_file: str, output_dir: str) -> str:
        """Generar archivo de salida procesado"""
        # Crear directorio si no existe
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generar nombre de archivo
        input_name = Path(input_file).stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"{input_name}_processed_{self.company}_{timestamp}.csv")
        
        # Guardar archivo
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        return output_file
    
    def _generate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generar estadísticas del DataFrame"""
        stats = {
            "total_records": len(df),
            "columns": list(df.columns),
            "null_counts": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.astype(str).to_dict()
        }
        
        # Estadísticas por estado si existe la columna
        status_cols = ['ESTADO', 'estado', 'Status', 'status']
        for col in status_cols:
            if col in df.columns:
                stats["status_distribution"] = df[col].value_counts().to_dict()
                break
        
        return stats
    
    def _validate_json_structure(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar estructura de datos JSON"""
        # Validaciones básicas
        if not isinstance(json_data, dict):
            raise ValueError("Los datos JSON deben ser un diccionario")
        
        # Asegurar estructura mínima
        validated_data = {
            "company": self.company.upper(),
            "extraction_date": datetime.now().isoformat(),
            "records": json_data.get("records", []),
            "metadata": json_data.get("metadata", {})
        }
        
        return validated_data
    
    def _transform_json_data(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transformar datos JSON"""
        transformed_data = json_data.copy()
        
        # Procesar registros si existen
        if "records" in transformed_data:
            records = transformed_data["records"]
            if isinstance(records, list):
                for record in records:
                    if isinstance(record, dict):
                        # Agregar timestamp de procesamiento
                        record["processed_at"] = datetime.now().isoformat()
        
        return transformed_data
    
    def get_processed_files(self) -> List[str]:
        """Obtener lista de archivos procesados"""
        return self.processed_files.copy()
    
    def get_errors(self) -> List[str]:
        """Obtener lista de errores"""
        return self.errors.copy()
    
    def clear_errors(self) -> None:
        """Limpiar lista de errores"""
        self.errors.clear()
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Obtener resumen del procesamiento"""
        return {
            "company": self.company.upper(),
            "processed_files_count": len(self.processed_files),
            "processed_files": self.processed_files,
            "errors_count": len(self.errors),
            "errors": self.errors,
            "last_processing": datetime.now().isoformat()
        }