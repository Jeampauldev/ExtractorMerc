#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detección de archivos duplicados por Número de Reclamo SGC
===========================================================

Recorre `data/` y busca archivos (CSV, XLSX, TXT, JSON) que contengan
o incluyan en el nombre el número de reclamo SGC. Agrupa por número y
reporta duplicados ignorando variaciones de timestamp o carpeta.

Estrategias:
- Extraer número SGC del nombre del archivo con regex.
- Intentar leer primeros registros/lineas para detectar columna o campo
  que contenga el número SGC (CSV/JSON/TXT simples).

Salida:
- Reporte Markdown en `data/reports/file_duplicates_sgc_<timestamp>.md`

Uso:
  python scripts/analyze_file_duplicates_sgc.py --root-dir data
"""

import argparse
import logging
import sys
from pathlib import Path
import re
import datetime as dt
import csv
import json

logger = logging.getLogger("analyze_file_duplicates_sgc")

# Regex relativamente flexible para número SGC (radicado alfanumérico)
SGC_REGEX = re.compile(r"(?i)(sgc|reclamo|radicado|num|nro|numero)[-_\s]*([a-z0-9]{6,})")

CLAIM_KEYS = [
    "numero_reclamo_sgc", "numero_radicado", "radicado", "nro_reclamo_sgc",
    "nro_radicado", "numero_reclamo", "reclamo", "sgc"
]

EXT_SUPPORTED = {".csv", ".json", ".txt", ".xlsx"}


def extract_sgc_from_name(name: str):
    m = SGC_REGEX.search(name)
    if m:
        return m.group(2)
    return ""


def extract_sgc_from_csv(path: Path):
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            norm = [h.strip().lower().replace(" ", "_") for h in header]
            for key in CLAIM_KEYS:
                if key in norm:
                    col = header[norm.index(key)]
                    for i, row in enumerate(reader):
                        val = (row.get(col) or "").strip()
                        if val:
                            return val
                        if i > 20:
                            break
    except Exception:
        return ""
    return ""


def extract_sgc_from_json(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Soporta lista de objetos o dict plano
        def scan_obj(obj):
            for k, v in (obj.items() if isinstance(obj, dict) else []):
                k_norm = k.strip().lower().replace(" ", "_")
                if k_norm in CLAIM_KEYS and isinstance(v, (str, int)):
                    return str(v)
            return ""

        if isinstance(data, list):
            for item in data[:50]:
                val = scan_obj(item)
                if val:
                    return val
        elif isinstance(data, dict):
            val = scan_obj(data)
            if val:
                return val
    except Exception:
        return ""
    return ""


def extract_sgc_from_txt(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = SGC_REGEX.search(text)
        if m:
            return m.group(2)
    except Exception:
        return ""
    return ""


def main():
    parser = argparse.ArgumentParser(description="Detectar archivos duplicados por número SGC")
    parser.add_argument("--root-dir", default="data", help="Directorio raíz a escanear")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    root_dir = Path(args.root_dir)
    if not root_dir.exists():
        logger.error(f"No existe el directorio: {root_dir}")
        print("ABORTADO: Directorio no existe")
        sys.exit(2)

    files = []
    for p in root_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in EXT_SUPPORTED:
            files.append(p)

    if not files:
        print("SIN DATOS: No se encontraron archivos soportados")
        sys.exit(0)

    from collections import defaultdict
    groups = defaultdict(list)

    for fpath in files:
        sgc = extract_sgc_from_name(fpath.name)
        if not sgc:
            if fpath.suffix.lower() == ".csv":
                sgc = extract_sgc_from_csv(fpath)
            elif fpath.suffix.lower() == ".json":
                sgc = extract_sgc_from_json(fpath)
            elif fpath.suffix.lower() == ".txt":
                sgc = extract_sgc_from_txt(fpath)
        if sgc:
            groups[sgc].append(str(fpath))

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    md_path = reports_dir / f"file_duplicates_sgc_{ts}.md"

    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Duplicados de Archivos por Número SGC\n\n")
        f.write(f"Fecha: {dt.datetime.now().isoformat()}\n\n")
        dup_keys = [k for k, v in groups.items() if len(v) > 1]
        f.write(f"Total claves con duplicados: {len(dup_keys)}\n\n")
        for key in sorted(dup_keys):
            f.write(f"- SGC={key}, archivos={len(groups[key])}\n")
            for path in groups[key]:
                f.write(f"  - {path}\n")
        f.write("\n")
        f.write("## Observaciones\n\n")
        f.write("- La detección usa nombre y contenido básico; timestamps y rutas son ignorados.\n")
        f.write("- Verifique manualmente casos límite con nombres poco informativos o archivos binarios.\n")

    print("ANÁLISIS ARCHIVOS COMPLETADO")
    print(f"Reporte: {md_path}")


if __name__ == "__main__":
    main()