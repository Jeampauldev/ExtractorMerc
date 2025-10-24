#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis de duplicados por Número de Reclamo SGC
================================================

Escanea archivos CSV en `data/processed` y detecta duplicados
ignorando el timestamp, usando como clave el "número de reclamo SGC".

Intenta identificar la columna de reclamo entre candidatos comunes
(p.ej., `numero_radicado`, `numero_reclamo_sgc`, `radicado`).

Salida:
- Reporte Markdown en `data/reports/duplicates_sgc_report_<timestamp>.md`
- Detalle CSV en `data/reports/duplicates_sgc_detail_<timestamp>.csv`

Uso:
  python scripts/analyze_duplicates_sgc.py --input-dir data/processed

Opciones:
  --input-dir <path>       Directorio con CSVs a analizar (default: data/processed)
  --claim-column <name>    Nombre exacto de la columna del reclamo (opcional)
  --limit <n>              Límite de ejemplos por grupo en el reporte (default: 5)
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import csv
import datetime as dt

logger = logging.getLogger("analyze_duplicates_sgc")

# Candidatos de columna para número de reclamo
CLAIM_COLUMN_CANDIDATES = [
    "numero_reclamo_sgc",
    "numero_radicado",
    "radicado",
    "nro_reclamo_sgc",
    "nro_radicado",
    "numero_reclamo",
]

# Candidatos de fecha/timestamp
DATE_COLUMN_CANDIDATES = [
    "fecha",
    "fecha_extraccion",
    "created_at",
    "updated_at",
    "timestamp",
]


def normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def find_column(header: List[str], candidates: List[str]) -> str:
    norm_header = [normalize(h) for h in header]
    for cand in candidates:
        if cand in norm_header:
            return header[norm_header.index(cand)]
    return ""


def read_csv_rows(file_path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = [r for r in reader]
    return header, rows


def detect_dataset(file_name: str) -> str:
    name_lower = file_name.lower()
    if "afinia" in name_lower:
        return "afinia"
    if "aire" in name_lower:
        return "aire"
    return "desconocido"


def main():
    parser = argparse.ArgumentParser(description="Analizar duplicados por número de reclamo SGC")
    parser.add_argument("--input-dir", default="data/processed", help="Directorio con CSVs a analizar")
    parser.add_argument("--claim-column", default="", help="Nombre exacto de columna del reclamo (opcional)")
    parser.add_argument("--limit", type=int, default=5, help="Límite de ejemplos por grupo en el reporte")
    parser.add_argument("--scope", choices=["global", "dataset"], default="dataset", help="Ámbito de clave de reclamo")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info(f"Iniciando análisis en {args.input_dir}")

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Directorio no existe: {input_dir}")
        print("ABORTADO: El directorio de entrada no existe")
        sys.exit(2)

    csv_files = sorted([p for p in input_dir.glob("*.csv")])
    if not csv_files:
        logger.warning("No se encontraron archivos CSV en el directorio")
        print("SIN DATOS: No hay CSVs para analizar")
        sys.exit(0)

    all_records = []
    problems = []
    for csv_file in csv_files:
        try:
            header, rows = read_csv_rows(csv_file)
            if not header:
                problems.append((csv_file.name, "CSV sin encabezados"))
                continue

            claim_col = args.claim_column or find_column(header, CLAIM_COLUMN_CANDIDATES)
            date_col = find_column(header, DATE_COLUMN_CANDIDATES)

            if not claim_col:
                problems.append((csv_file.name, f"No se detectó columna de reclamo. Encabezados: {header}"))
                continue

            dataset = detect_dataset(csv_file.name)
            for r in rows:
                claim_val = (r.get(claim_col) or "").strip()
                date_val = (r.get(date_col) or "").strip() if date_col else ""
                if not claim_val:
                    continue
                all_records.append({
                    "dataset": dataset,
                    "source_file": csv_file.name,
                    "claim_col": claim_col,
                    "date_col": date_col,
                    "claim": claim_val,
                    "date": date_val,
                })
        except Exception as e:
            problems.append((csv_file.name, f"Error leyendo CSV: {e}"))

    if not all_records:
        logger.warning("No se recolectaron registros con columna de reclamo válida")
        print("SIN DATOS: No se encontraron registros válidos")
        sys.exit(0)

    # Agrupar por dataset y claim
    from collections import defaultdict
    groups = defaultdict(list)
    for rec in all_records:
        if args.scope == "global":
            key = ("global", rec["claim"])  # ignoramos dataset y timestamp
        else:
            key = (rec["dataset"], rec["claim"])  # ignoramos timestamp
        groups[key].append(rec)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    uniques = {k: v for k, v in groups.items() if len(v) == 1}

    # Contadores por dataset
    counts_by_dataset = defaultdict(lambda: {"total": 0, "duplicates": 0, "uniques": 0})
    for (dataset, _claim), rows in groups.items():
        counts_by_dataset[dataset]["total"] += len(rows)
        if len(rows) > 1:
            counts_by_dataset[dataset]["duplicates"] += 1
        else:
            counts_by_dataset[dataset]["uniques"] += 1

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    md_path = reports_dir / f"duplicates_sgc_report_{ts}.md"
    csv_path = reports_dir / f"duplicates_sgc_detail_{ts}.csv"

    # Escribir detalle CSV solo de duplicados
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["dataset", "claim", "source_file", "date_col", "date"])
        for (dataset, claim), rows in duplicates.items():
            for r in rows:
                writer.writerow([dataset, claim, r["source_file"], r.get("date_col") or "", r.get("date") or ""])

    # Escribir reporte Markdown
    with md_path.open("w", encoding="utf-8") as f:
        f.write(f"# Reporte de Duplicados por Número de Reclamo SGC\n\n")
        f.write(f"Fecha: {dt.datetime.now().isoformat()}\n\n")
        f.write("## Resumen por Dataset\n\n")
        for ds, cnt in counts_by_dataset.items():
            f.write(f"- {ds}: claves únicas={cnt['uniques']}, duplicadas={cnt['duplicates']}, registros totales={cnt['total']}\n")
        f.write("\n")

        if problems:
            f.write("## Archivos con Problemas\n\n")
            for name, msg in problems:
                f.write(f"- {name}: {msg}\n")
            f.write("\n")

        scope_label = "GLOBAL" if args.scope == "global" else "POR DATASET"
        f.write(f"## Duplicados Detectados (ámbito: {scope_label}, ignorando timestamp)\n\n")
        if not duplicates:
            f.write("No se detectaron duplicados.\n")
        else:
            # Mostrar ejemplos limitados
            for (dataset, claim), rows in sorted(duplicates.items(), key=lambda x: (x[0][0], x[0][1])):
                f.write(f"- Dataset={dataset}, Reclamo={claim}, ocurrencias={len(rows)}\n")
                for r in rows[:args.limit]:
                    f.write(f"  - Archivo={r['source_file']} FechaCol={r.get('date_col') or ''} Fecha={r.get('date') or ''}\n")
                if len(rows) > args.limit:
                    f.write(f"  ... (+{len(rows) - args.limit} más)\n")
            f.write("\n")

        f.write("## Ubicaciones de salida\n\n")
        f.write(f"- Detalle CSV: {csv_path}\n")
        f.write(f"- Reporte MD: {md_path}\n")

    print("ANÁLISIS COMPLETADO")
    print(f"Duplicados: {len(duplicates)} claves; Únicos: {len(uniques)} claves")
    print(f"Reporte: {md_path}")
    print(f"Detalle: {csv_path}")


if __name__ == "__main__":
    main()