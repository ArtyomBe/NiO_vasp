#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate INCAR files for NiO SCF HSE06+HF scans over AEXX = 0..1.00 (0..100%).

- Creates subfolders 0_percent ... 100_percent in the destination directory.
- Writes an INCAR into each subfolder with AEXX = i/100 (formatted to 2 decimals).
- Uses pathlib, logging, and atomic writes.
- CLI flags let you change destination directory and overwrite behavior.

Usage:
    python generate_incar_aexx_scan.py -v
    python generate_incar_aexx_scan.py --no-overwrite
    python generate_incar_aexx_scan.py --dest /some/other/path
"""

from __future__ import annotations

import argparse
import logging
import tempfile
from pathlib import Path
from typing import Final

# ========= Defaults =========

DEFAULT_BASE_DIR: Final[Path] = Path(
    "/Users/artyombetekhtin/PycharmProjects/nio_vasp/src/inputs/NiO/scf"
)

INCAR_TEMPLATE: Final[str] = """System   = NiO (AFM-II, SCF HSE06+HF)
ISPIN    = 2
ISYM     = 0
ENCUT    = 600
PREC     = Accurate
ADDGRID  = .TRUE.
LASPH    = .TRUE.
LREAL    = .FALSE.

LDAU     = .TRUE.
LDAUTYPE = 2
LDAUL    = 2  -1      # Ni  O
LDAUU    = 6.0 0.0
LDAUJ    = 0   0

LHFCALC  = .TRUE.
AEXX     = {aexx:.2f}
HFSCREEN = 0.2
ALGO     = All
PRECFOCK = Fast
EDIFF    = 1e-06
NELM     = 120

ISMEAR   = -5
SIGMA    = 0.05
IBRION   = -1

ISTART   = 1
ICHARG   = 11

NWRITE   = 1
LCHARG   = .TRUE.
LWAVE    = .FALSE.
"""


# ========= Helpers =========

def setup_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    ensure_dir(path.parent)
    with tempfile.NamedTemporaryFile("w", encoding=encoding, dir=path.parent, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(content)
        tmp.flush()
    tmp_path.replace(path)  # atomic on POSIX
    logging.debug("Wrote file: %s", path)


def write_incar(dest_dir: Path, aexx_value: float, overwrite: bool = True) -> Path:
    """Render INCAR for a given aexx_value into dest_dir/INCAR."""
    ensure_dir(dest_dir)
    incar_path = dest_dir / "INCAR"

    if incar_path.exists() and not overwrite:
        logging.info("Skip existing (overwrite disabled): %s", incar_path)
        return incar_path

    content = INCAR_TEMPLATE.format(aexx=aexx_value)
    atomic_write_text(incar_path, content)
    logging.info("INCAR created: %s (AEXX=%.2f)", incar_path, aexx_value)
    return incar_path


def generate_scan(base_dir: Path, overwrite: bool = True) -> None:
    """
    Create 101 folders [0..100]_percent and write INCAR with AEXX=i/100.
    """
    ensure_dir(base_dir)
    for i in range(0, 101):
        aexx = i / 100.0
        subdir = base_dir / f"{i}_percent"
        logging.debug("Preparing folder: %s (AEXX=%.2f)", subdir, aexx)
        write_incar(subdir, aexx, overwrite=overwrite)
    logging.info("All INCAR files generated in: %s", base_dir)


# ========= CLI =========

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate NiO HSE06+HF SCF INCARs for AEXX scan (0..100%)."
    )
    parser.add_argument(
        "-d", "--dest", type=Path, default=DEFAULT_BASE_DIR,
        help=f"Destination base directory (default: {DEFAULT_BASE_DIR})"
    )
    parser.add_argument(
        "--no-overwrite", action="store_true",
        help="Do not overwrite existing INCAR files."
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="Increase log verbosity (-v=INFO, -vv=DEBUG)."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)
    generate_scan(args.dest, overwrite=not args.no_overwrite)


if __name__ == "__main__":
    main()
