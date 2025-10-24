#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Truncado seguro de tablas en CE-IA (PostgreSQL)
===============================================

Este script vacía las tablas `ov_afinia` y `ov_aire` en el esquema
`data_general` de la base de datos CE-IA usando TRUNCATE con
`RESTART IDENTITY CASCADE` para garantizar limpieza completa.

Uso:
  python scripts/truncate_data_general_tables.py --confirm yes

Opciones:
  --schema <nombre>         Esquema a usar (default: data_general)
  --tables <t1> <t2> ...    Tablas a truncar (default: ov_afinia ov_aire)
  --dry-run                 Muestra conteos sin truncar

Requiere que la configuración RDS esté disponible vía `src.config.rds_config`.
"""

import sys
from pathlib import Path
import argparse
import logging
from typing import List

from sqlalchemy import text

# Asegurar que el proyecto raíz esté en el PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from src.config.rds_config import get_rds_engine
except Exception as e:
    print(f"ERROR: No se pudo importar configuración RDS: {e}")
    sys.exit(1)


logger = logging.getLogger("truncate_data_general")


def get_counts(engine, schema: str, tables: List[str]) -> dict:
    """Obtiene conteos actuales por tabla."""
    counts = {}
    with engine.connect() as conn:
        for t in tables:
            try:
                res = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{t}"))
                counts[t] = res.scalar() or 0
            except Exception as e:
                counts[t] = f"ERROR: {e}"
    return counts


def truncate_tables(engine, schema: str, tables: List[str]) -> None:
    """Ejecuta TRUNCATE en las tablas dadas con RESTART IDENTITY CASCADE."""
    tables_qualified = ", ".join([f"{schema}.{t}" for t in tables])
    sql = text(f"TRUNCATE TABLE {tables_qualified} RESTART IDENTITY CASCADE")
    with engine.begin() as conn:
        conn.execute(sql)


def main():
    parser = argparse.ArgumentParser(description="Truncado seguro de tablas en CE-IA")
    parser.add_argument("--confirm", help="Debe ser 'yes' para ejecutar el truncado", default="no")
    parser.add_argument("--schema", help="Esquema a usar", default="data_general")
    parser.add_argument("--tables", nargs="*", help="Tablas a truncar", default=["ov_afinia", "ov_aire"])
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar conteos, no truncar")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Inicializando truncado de tablas")

    # Obtener engine
    try:
        engine = get_rds_engine()
    except Exception as e:
        logger.error(f"No se pudo obtener engine RDS: {e}")
        sys.exit(2)

    # Mostrar conteos antes
    before = get_counts(engine, args.schema, args.tables)
    logger.info(f"Conteos antes del truncado: {before}")

    if args.dry_run:
        logger.info("Dry-run habilitado. No se ejecutará truncado.")
        print("RESULTADO: Dry-run. No se modificaron las tablas.")
        sys.exit(0)

    if args.confirm.lower() != "yes":
        logger.error("Confirmación requerida. Ejecute con --confirm yes para proceder.")
        print("ABORTADO: Falta confirmación --confirm yes")
        sys.exit(3)

    # Ejecutar truncado
    try:
        truncate_tables(engine, args.schema, args.tables)
        logger.info(f"TRUNCATE ejecutado sobre {args.tables} en esquema {args.schema}")
    except Exception as e:
        logger.error(f"Error ejecutando TRUNCATE: {e}")
        print(f"ERROR: Falló el truncado: {e}")
        sys.exit(4)

    # Verificar conteos después
    after = get_counts(engine, args.schema, args.tables)
    logger.info(f"Conteos después del truncado: {after}")
    print("RESULTADO FINAL:")
    for t in args.tables:
        print(f"- {args.schema}.{t}: {after.get(t)} registros")

    # Salida con éxito si todos son 0
    if all(isinstance(after.get(t), int) and after.get(t) == 0 for t in args.tables):
        sys.exit(0)
    else:
        logger.warning("Alguna tabla no quedó en 0. Verifique dependencias o errores.")
        sys.exit(5)


if __name__ == "__main__":
    main()