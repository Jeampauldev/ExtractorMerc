# -*- coding: utf-8 -*-
"""
Módulo de Limpieza y Transformación de Datos - Mercurio ExtractorMerc
=======================================================================

🔄 MIGRADO DESDE IPO LEGACY
Fuente: legacy/backend-ipo-backup/services/mercurio/clean_and_transform.py
Fecha migración: 2024
Propósito: Procesamiento y transformación de datos de reportes Mercurio

Procesos soportados:
- RRA Pendientes (Air-e)
- RRA Recibidas (Air-e) 
- Verbales Pendientes (Afinia)
- Auditoría Pendientes (Air-e)
"""

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import pytz
from sqlalchemy import create_engine, text

from config.centralized_config import config
from src.core.logging import get_logger

logger = get_logger()

# 🔄 MIGRADO DESDE IPO: Configuración de zona horaria
zona_horaria = pytz.timezone("America/Bogota")


def actualizar_pendientes(data: pd.DataFrame, tabla: str, key: str = "rad_mercurio") -> None:
    """🔄 MIGRADO DESDE IPO: Actualiza tabla de pendientes en BD"""
    logger.info(f"Actualizando tabla {tabla} con {len(data)} registros")
    
    try:
        # Crear conexión a la base de datos
        engine = create_engine(config.database.get_connection_string())
        
        # Leer datos existentes
        xdata = pd.read_sql(f"SELECT * FROM {tabla}", engine)
        logger.info(f"Tabla {tabla} tiene {len(xdata)} registros")
        
        # Identificar registros
        new_records = data[~data[key].isin(xdata[key])]
        logger.info(f"Nuevos registros: {len(new_records)}")
        
        records_to_delete = xdata[~xdata[key].isin(data[key])]
        logger.info(f"Registros a borrar: {len(records_to_delete)}")
        
        records_to_update = data[data[key].isin(xdata[key])]
        logger.info(f"Registros a actualizar: {len(records_to_update)}")
        
        # Insertar nuevos registros
        if not new_records.empty:
            new_records.to_sql(tabla, engine, if_exists="append", index=False)
            logger.info("Nuevos registros insertados")
        
        # Borrar registros obsoletos y a actualizar
        if (not records_to_delete.empty) or (not records_to_update.empty):
            ids_to_delete = tuple(
                records_to_delete[key].tolist() + records_to_update[key].tolist()
            )
            with engine.connect() as conn:
                conn.execute(text(f"DELETE FROM {tabla} WHERE {key} IN {ids_to_delete}"))
            logger.info("Registros borrados")
        
        # Actualizar registros
        if not records_to_update.empty:
            records_to_update.to_sql(tabla, engine, if_exists="append", index=False)
            logger.info("Registros actualizados insertados")
            
    except Exception as e:
        logger.error(f"Error actualizando tabla {tabla}: {e}")
        raise


def rra_pendientes(data: pd.DataFrame) -> None:
    """🔄 MIGRADO DESDE IPO: Procesa datos de RRA pendientes (Air-e)"""
    logger.info("Iniciando procesamiento de RRA pendientes")
    
    if len(data) == 0:
        logger.warning("No hay datos para procesar")
        return
    
    try:
        current_date = datetime.now(tz=zona_horaria)
        
        # Limpiar nombres de columnas
        data.columns = [col.lower().strip().replace(" ", "_") for col in data.columns]
        data = data.drop(columns=["#"], errors="ignore")
        
        # Filtrar datos por documento respuesta
        filtro = (
            data["documento_respuesta"] == "Recurso Reposicion Apelacion Improcedente"
        )
        data = data.loc[filtro, :]
        logger.info(f"Registros después del filtro: {len(data)}")
        
        # Convertir columnas de fecha
        dates_columns = data.filter(regex=r"fecha_").columns
        data[dates_columns] = data[dates_columns].apply(
            lambda x: pd.to_datetime(x, errors="coerce", format="%Y-%m-%d %H.%M.%S.%f")
        )
        
        # Calcular fecha de vencimiento
        data["dias_venc"] = data["correo_electronico"].apply(
            lambda x: 3 if "@" in str(x) else 20
        )
        data["fec_vencimiento"] = data.apply(
            lambda row: row["fecha_firma"] + pd.DateOffset(days=row["dias_venc"]),
            axis=1,
        )
        
        # Calcular días hábiles
        data["dias_habiles"] = data.apply(
            lambda row: np.busday_count(
                row["fecha_firma"].date(), datetime.now().date()
            ),
            axis=1,
        )
        
        # Limpiar columnas de texto
        string_columns = data.select_dtypes(include="object").columns
        data[string_columns] = data[string_columns].apply(lambda x: x.str.strip())
        
        # Limpiar y preparar datos finales
        data.drop(columns=["dias_venc"], errors="ignore", inplace=True)
        data["last_update"] = current_date
        
        # Ordenar y eliminar duplicados
        data.sort_values(
            by=["rad_mercurio", "fecha_firma"], ascending=[True, False], inplace=True
        )
        data.drop_duplicates(subset=["rad_mercurio"], inplace=True)
        
        logger.info("Procesamiento de datos completado")
        
        # Guardar en base de datos usando transacción
        engine = create_engine(config.database.get_connection_string())
        with engine.connect() as connection:
            with connection.begin():
                logger.info("Guardando datos en base de datos")
                
                # Truncar tabla temporal
                connection.execute(text("TRUNCATE TABLE public.rra_pendientes_temp;"))
                
                # Insertar datos
                data.to_sql(
                    "rra_pendientes_temp",
                    con=connection,
                    if_exists="append",
                    index=False,
                )
                
                # Actualizar tabla principal
                connection.execute(text(
                    "INSERT INTO public.rra_pendientes SELECT * FROM public.rra_pendientes_temp;"
                ))
                
                logger.info("Datos guardados exitosamente")
                
    except Exception as e:
        logger.error(f"Error procesando RRA pendientes: {e}")
        raise


def rra_recibidas(data: pd.DataFrame) -> None:
    """🔄 MIGRADO DESDE IPO: Procesa datos de RRA recibidas (Air-e)"""
    logger.info("Iniciando procesamiento de RRA recibidas")
    
    if len(data) == 0:
        logger.warning("No hay datos para procesar")
        return
    
    try:
        current_date = datetime.now(tz=zona_horaria)
        
        # Limpiar nombres de columnas
        data.columns = [col.lower().strip().replace(" ", "_") for col in data.columns]
        data = data.drop(columns=["#"], errors="ignore")
        
        # Convertir columnas de fecha
        dates_columns = data.filter(regex=r"fecha_").columns
        data[dates_columns] = data[dates_columns].apply(
            lambda x: pd.to_datetime(x, errors="coerce", format="%Y-%m-%d %H.%M.%S.%f")
        )
        
        # Limpiar columnas de texto
        string_columns = data.select_dtypes(include="object").columns
        data[string_columns] = data[string_columns].apply(lambda x: x.str.strip())
        
        data["last_update"] = current_date
        
        # Eliminar duplicados
        data.sort_values(
            by=["rad_mercurio", "fecha_recepcion"], ascending=[True, False], inplace=True
        )
        data.drop_duplicates(subset=["rad_mercurio"], inplace=True)
        
        logger.info(f"Procesamiento completado: {len(data)} registros")
        
        # Actualizar tabla
        actualizar_pendientes(data, "public.rra_recibidas")
        
    except Exception as e:
        logger.error(f"Error procesando RRA recibidas: {e}")
        raise


def verbales_pendientes(data: pd.DataFrame) -> None:
    """🔄 MIGRADO DESDE IPO: Procesa datos de verbales pendientes (Afinia)"""
    logger.info("Iniciando procesamiento de verbales pendientes")
    
    if len(data) == 0:
        logger.warning("No hay datos para procesar")
        return
    
    try:
        current_date = datetime.now(tz=zona_horaria)
        
        # Limpiar nombres de columnas
        data.columns = [col.lower().strip().replace(" ", "_") for col in data.columns]
        data = data.drop(columns=["#"], errors="ignore")
        
        # Filtrar por tipo de documento
        filtro = data["tipo_documento"] == "Acta de Visita de Verificación"
        data = data.loc[filtro, :]
        logger.info(f"Registros después del filtro: {len(data)}")
        
        # Convertir columnas de fecha
        dates_columns = data.filter(regex=r"fecha_").columns
        data[dates_columns] = data[dates_columns].apply(
            lambda x: pd.to_datetime(x, errors="coerce", format="%Y-%m-%d %H.%M.%S.%f")
        )
        
        # Calcular días de vencimiento
        data["dias_venc"] = data["correo_electronico"].apply(
            lambda x: 3 if "@" in str(x) else 20
        )
        data["fec_vencimiento"] = data.apply(
            lambda row: row["fecha_firma"] + pd.DateOffset(days=row["dias_venc"]),
            axis=1,
        )
        
        # Calcular días hábiles
        data["dias_habiles"] = data.apply(
            lambda row: np.busday_count(
                row["fecha_firma"].date(), datetime.now().date()
            ),
            axis=1,
        )
        
        # Limpiar columnas de texto
        string_columns = data.select_dtypes(include="object").columns
        data[string_columns] = data[string_columns].apply(lambda x: x.str.strip())
        
        # Preparar datos finales
        data.drop(columns=["dias_venc"], errors="ignore", inplace=True)
        data["last_update"] = current_date
        
        # Ordenar y eliminar duplicados
        data.sort_values(
            by=["rad_mercurio", "fecha_firma"], ascending=[True, False], inplace=True
        )
        data.drop_duplicates(subset=["rad_mercurio"], inplace=True)
        
        logger.info(f"Procesamiento completado: {len(data)} registros")
        
        # Actualizar tabla
        actualizar_pendientes(data, "public.afinia_verbales_pendientes")
        
    except Exception as e:
        logger.error(f"Error procesando verbales pendientes: {e}")
        raise


def auditoria_pendientes(data: pd.DataFrame) -> None:
    """🔄 MIGRADO DESDE IPO: Procesa datos de auditoría pendientes (Air-e)"""
    logger.info("Iniciando procesamiento de auditoría pendientes")
    
    if len(data) == 0:
        logger.warning("No hay datos para procesar")
        return
    
    try:
        current_date = datetime.now(tz=zona_horaria)
        
        # Limpiar nombres de columnas
        data.columns = [col.lower().strip().replace(" ", "_") for col in data.columns]
        data = data.drop(columns=["#"], errors="ignore")
        
        # Convertir columnas de fecha
        dates_columns = data.filter(regex=r"fecha_").columns
        data[dates_columns] = data[dates_columns].apply(
            lambda x: pd.to_datetime(x, errors="coerce", format="%Y-%m-%d %H.%M.%S.%f")
        )
        
        # Limpiar columnas de texto
        string_columns = data.select_dtypes(include="object").columns
        data[string_columns] = data[string_columns].apply(lambda x: x.str.strip())
        
        data["last_update"] = current_date
        
        # Eliminar duplicados
        data.sort_values(
            by=["rad_mercurio", "fecha_recepcion"], ascending=[True, False], inplace=True
        )
        data.drop_duplicates(subset=["rad_mercurio"], inplace=True)
        
        logger.info(f"Procesamiento completado: {len(data)} registros")
        
        # Actualizar tabla
        actualizar_pendientes(data, "public.auditoria_pendientes")
        
    except Exception as e:
        logger.error(f"Error procesando auditoría pendientes: {e}")
        raise


# 🔄 MIGRADO DESDE IPO: Funciones de utilidad adicionales
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia un DataFrame aplicando transformaciones comunes"""
    # Limpiar nombres de columnas
    df.columns = [col.lower().strip().replace(" ", "_") for col in df.columns]
    
    # Eliminar columnas innecesarias
    df = df.drop(columns=["#"], errors="ignore")
    
    # Limpiar strings
    string_columns = df.select_dtypes(include="object").columns
    df[string_columns] = df[string_columns].apply(lambda x: x.str.strip())
    
    return df


def convert_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas de fecha al formato correcto"""
    dates_columns = df.filter(regex=r"fecha_").columns
    df[dates_columns] = df[dates_columns].apply(
        lambda x: pd.to_datetime(x, errors="coerce", format="%Y-%m-%d %H.%M.%S.%f")
    )
    return df