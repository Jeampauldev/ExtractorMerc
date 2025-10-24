import argparse
import csv
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SGC_REGEXES = [
    re.compile(r"RE(\d{7,16})", re.IGNORECASE),
    re.compile(r"SGC[=:_\-\s]*(\d{7,16})", re.IGNORECASE),
    re.compile(r"(\d{7,16})")  # fallback for numeric sequences
]

TIMESTAMP_REGEXES = [
    # Matches *_YYYYMMDD_HHMMSS in filenames
    re.compile(r"_(\d{8})_(\d{6})")
]


@dataclass
class FileInfo:
    path: Path
    company: str
    sgc: str
    ext: str
    file_hash: Optional[str]
    timestamp: Optional[datetime]
    mtime: float


def compute_sha256(file_path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def extract_sgc_from_filename(name: str) -> Optional[str]:
    for rx in SGC_REGEXES:
        m = rx.search(name)
        if m:
            return m.group(1)
    return None


def extract_timestamp_from_filename(name: str) -> Optional[datetime]:
    for rx in TIMESTAMP_REGEXES:
        m = rx.search(name)
        if m:
            try:
                date_part, time_part = m.group(1), m.group(2)
                return datetime.strptime(f"{date_part}{time_part}", "%Y%m%d%H%M%S")
            except Exception:
                pass
    return None


def extract_sgc_from_json(file_path: Path) -> Optional[str]:
    try:
        with file_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        candidates = [
            data.get('sgc_number'),
            data.get('numero_radicado'),
            data.get('radicado'),
            data.get('numeroRadicado'),
        ]
        for c in candidates:
            if c and isinstance(c, (str, int)):
                cstr = str(c)
                sgc = extract_sgc_from_filename(cstr) or (cstr if cstr.isdigit() else None)
                if sgc:
                    return sgc
    except Exception:
        pass
    return None


def find_files(base_dir: Path, companies: Optional[List[str]], include_exts: List[str]) -> List[Path]:
    targets: List[Path] = []
    root = base_dir
    if companies:
        for company in companies:
            target = root / company / 'oficina_virtual' / 'processed'
            if target.exists():
                targets.append(target)
    else:
        for company_dir in (root).iterdir():
            if not company_dir.is_dir():
                continue
            target = company_dir / 'oficina_virtual' / 'processed'
            if target.exists():
                targets.append(target)

    files: List[Path] = []
    for t in targets:
        for p in t.rglob('*'):
            if p.is_file() and p.suffix.lower() in include_exts:
                files.append(p)
    return files


def build_file_info(file_path: Path, company: str, hash_enabled: bool) -> Optional[FileInfo]:
    name = file_path.name
    sgc = extract_sgc_from_filename(name)
    if not sgc and file_path.suffix.lower() == '.json':
        sgc = extract_sgc_from_json(file_path)
    if not sgc:
        return None
    ts = extract_timestamp_from_filename(name)
    fhash = compute_sha256(file_path) if hash_enabled else None
    try:
        mtime = file_path.stat().st_mtime
    except Exception:
        mtime = 0.0
    return FileInfo(path=file_path, company=company, sgc=sgc, ext=file_path.suffix.lower(), file_hash=fhash, timestamp=ts, mtime=mtime)


def group_by_sgc(files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
    groups: Dict[str, List[FileInfo]] = {}
    for fi in files:
        groups.setdefault(fi.sgc, []).append(fi)
    return groups


def choose_primary(files: List[FileInfo]) -> FileInfo:
    # Prefer explicit timestamp, fallback to mtime
    def sort_key(fi: FileInfo):
        return (fi.timestamp or datetime.fromtimestamp(fi.mtime))
    return sorted(files, key=sort_key)[-1]


def plan_cleanup(groups: Dict[str, List[FileInfo]], min_files_per_key: int) -> Dict[str, Dict[str, List[FileInfo]]]:
    plan: Dict[str, Dict[str, List[FileInfo]]] = {}
    for sgc, files in groups.items():
        if len(files) < min_files_per_key:
            continue
        primary = choose_primary(files)
        to_archive: List[FileInfo] = []
        to_keep: List[FileInfo] = [primary]
        for f in files:
            if f.path == primary.path:
                continue
            # If file_hash exists and differs, keep both (different states)
            if primary.file_hash and f.file_hash and primary.file_hash != f.file_hash:
                to_keep.append(f)
            else:
                to_archive.append(f)
        if len(to_archive) > 0:
            plan[sgc] = {'keep': to_keep, 'archive': to_archive}
    return plan


def write_report(plan: Dict[str, Dict[str, List[FileInfo]]], reports_dir: Path, dry_run: bool, base_dir: Path, archive_dir: Path) -> Tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    md_path = reports_dir / f'cleanup_duplicates_sgc_{ts}.md'
    csv_path = reports_dir / f'cleanup_duplicates_sgc_{ts}.csv'

    total_keys = len(plan)
    total_archive = sum(len(v['archive']) for v in plan.values())
    total_keep = sum(len(v['keep']) for v in plan.values())

    with md_path.open('w', encoding='utf-8') as md:
        md.write(f"# Limpieza de duplicados por SGC ({'DRY-RUN' if dry_run else 'EJECUCIÓN'})\n\n")
        md.write(f"Base: {base_dir}\n\n")
        md.write(f"Archivo destino: {archive_dir}\n\n")
        md.write(f"Claves con acción: {total_keys}\n\n")
        md.write(f"Archivos a archivar: {total_archive}\n\n")
        md.write(f"Archivos a conservar: {total_keep}\n\n")
        for sgc, actions in sorted(plan.items(), key=lambda x: x[0]):
            md.write(f"\n## SGC={sgc}\n\n")
            md.write("Conservar:\n")
            for fi in actions['keep']:
                md.write(f"- KEEP: {fi.path}\n")
            md.write("\nArchivar:\n")
            for fi in actions['archive']:
                md.write(f"- ARCHIVE: {fi.path}\n")

    with csv_path.open('w', newline='', encoding='utf-8') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(['sgc', 'action', 'company', 'path', 'timestamp', 'mtime', 'hash'])
        for sgc, actions in plan.items():
            for fi in actions['keep']:
                writer.writerow([sgc, 'keep', fi.company, str(fi.path), fi.timestamp.isoformat() if fi.timestamp else '', fi.mtime, fi.file_hash or ''])
            for fi in actions['archive']:
                writer.writerow([sgc, 'archive', fi.company, str(fi.path), fi.timestamp.isoformat() if fi.timestamp else '', fi.mtime, fi.file_hash or ''])

    return md_path, csv_path


def execute_cleanup(plan: Dict[str, Dict[str, List[FileInfo]]], archive_root: Path, base_dir: Path) -> None:
    for sgc, actions in plan.items():
        for fi in actions['archive']:
            # Preserve relative path structure under archive_root/<company>/oficina_virtual/processed/<SGC>/
            try:
                rel = fi.path.relative_to(base_dir)
            except ValueError:
                # If base_dir isn't a common parent, fallback to filename
                rel = Path(fi.path.name)
            target_dir = archive_root / fi.company / 'oficina_virtual' / 'processed' / sgc
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / rel.name
            # If file exists in archive, append counter
            if target_path.exists():
                stem = target_path.stem
                suffix = target_path.suffix
                counter = 1
                while True:
                    candidate = target_dir / f"{stem}__dup{counter}{suffix}"
                    if not candidate.exists():
                        target_path = candidate
                        break
                    counter += 1
            shutil.move(str(fi.path), str(target_path))


def main():
    parser = argparse.ArgumentParser(description='Limpiar/archivar duplicados por SGC en data/downloads/**/oficina_virtual/processed')
    parser.add_argument('--base-dir', default='data/downloads', help='Directorio base de downloads (por defecto data/downloads)')
    parser.add_argument('--company', dest='company', choices=['afinia', 'aire'], help='Empresa a filtrar (afinia, aire). Si no se provee, aplica a todas las encontradas.')
    parser.add_argument('--include-ext', default='.json,.pdf,.txt,.html,.csv', help='Extensiones a considerar, separadas por coma')
    parser.add_argument('--hash', dest='hash_enabled', action='store_true', help='Calcular hash de contenido para validar duplicados con distinto estado')
    parser.add_argument('--dry-run', dest='dry_run', action='store_true', help='Mostrar plan sin mover archivos')
    parser.add_argument('--confirm', dest='confirm', action='store_true', help='Confirmar ejecución (requiere no usar --dry-run)')
    parser.add_argument('--archive-dir', default='data/archive/duplicates', help='Directorio de destino para archivos duplicados')
    parser.add_argument('--min-files-per-key', type=int, default=2, help='Mínimo de archivos por SGC para considerar acción')

    args = parser.parse_args()
    base_dir = Path(args.base_dir)
    archive_dir = Path(args.archive_dir)
    include_exts = [s.strip().lower() for s in args.include_ext.split(',') if s.strip()]
    companies = [args.company] if args.company else None

    if args.confirm and args.dry_run:
        print('[ERROR] No puedes usar --confirm junto con --dry-run.')
        return

    files = find_files(base_dir, companies, include_exts)
    file_infos: List[FileInfo] = []
    for fp in files:
        # Derive company from path: data/downloads/<company>/oficina_virtual/processed/...
        try:
            rel = fp.relative_to(base_dir)
            company = rel.parts[0] if len(rel.parts) > 0 else 'unknown'
        except Exception:
            company = 'unknown'
        fi = build_file_info(fp, company=company, hash_enabled=args.hash_enabled)
        if fi:
            file_infos.append(fi)

    groups = group_by_sgc(file_infos)
    plan = plan_cleanup(groups, min_files_per_key=args.min_files_per_key)

    reports_dir = Path('data/reports')
    md_path, csv_path = write_report(plan, reports_dir, args.dry_run, base_dir, archive_dir)
    print(f"[REPORTE] {md_path}")
    print(f"[REPORTE_CSV] {csv_path}")
    print(f"[RESUMEN] Claves con acción: {len(plan)} | Archivar: {sum(len(v['archive']) for v in plan.values())} | Conservar: {sum(len(v['keep']) for v in plan.values())}")

    if not args.dry_run and args.confirm:
        execute_cleanup(plan, archive_root=archive_dir, base_dir=base_dir)
        print('[EJECUCIÓN] Limpieza completada. Archivos movidos al archivo de duplicados.')
    elif not args.dry_run and not args.confirm:
        print('[ADVERTENCIA] Ejecución sin confirmación no permitida. Usa --confirm para proceder o --dry-run para simular.')


if __name__ == '__main__':
    main()