#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create a fixed INCAR file for NiO relaxation.

- Writes exactly the required INCAR content (no AEXX, no templating).
- Uses pathlib for paths, logging for diagnostics, and atomic write to avoid
  partial files.
- CLI allows overriding the destination directory if needed.
"""

from __future__ import annotations

import argparse
import logging
import tempfile
from pathlib import Path
from typing import Final

# ======== Configuration ========

# Default destination directory
DEFAULT_DEST_DIR: Final[Path] = Path(
    "/Users/artyombetekhtin/PycharmProjects/nio_vasp/src/inputs/NiO/BandStructure"
)

# Exact INCAR content to write (keeps your spacing and blank lines verbatim)
INCAR_CONTENT: Final[str] = """SYSTEM   = NiO (AFM-II, Bands PBE+U)

ENCUT    = 600
PREC     = Accurate
ADDGRID  = .TRUE.
LREAL    = .FALSE.
EDIFF    = 1E-08

ISPIN    = 2
ISYM     = 0
LASPH    = .TRUE.
LDAU     = .TRUE.
LDAUTYPE = 2
LDAUL    = 2  -1
LDAUU    = 6.0 0.0
LDAUJ    = 0   0

ISTART   = 1
ICHARG   = 11
ALGO     = Normal
NELM     = 1
IBRION   = -1
NSW      = 0

ISMEAR   = 0
SIGMA    = 0.01

LORBIT   = 11

NWRITE   = 1
LCHARG   = .FALSE.
LWAVE    = .FALSE.

NCORE    = 8
#KPAR    = 8
"""


# ======== Helpers ========

def setup_logging(verbosity: int) -> None:
    """Configure logging level and format."""
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def ensure_directory(path: Path) -> None:
    """Create the directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    logging.debug("Ensured directory exists: %s", path)


def atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """
    Write text atomically:
    1) write to a NamedTemporaryFile in the same directory
    2) rename to the final path
    This avoids partial files on interruption.
    """
    ensure_directory(path.parent)
    with tempfile.NamedTemporaryFile("w", encoding=encoding, dir=path.parent, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(content)
        tmp.flush()
    tmp_path.replace(path)  # atomic on POSIX
    logging.debug("Atomically wrote file: %s", path)


def write_incar(dest_dir: Path, overwrite: bool = True) -> Path:
    """Create INCAR in dest_dir with fixed content."""
    ensure_directory(dest_dir)
    incar_path = dest_dir / "INCAR"

    if incar_path.exists() and not overwrite:
        logging.info("INCAR already exists and overwrite=False, skipping: %s", incar_path)
        return incar_path

    atomic_write_text(incar_path, INCAR_CONTENT)
    logging.info("INCAR created: %s", incar_path)
    return incar_path


# ======== CLI ========

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a fixed INCAR for NiO relaxation."
    )
    parser.add_argument(
        "-d", "--dest",
        type=Path,
        default=DEFAULT_DEST_DIR,
        help=f"Destination directory (default: {DEFAULT_DEST_DIR})"
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not overwrite existing INCAR if present."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (-v for INFO, -vv for DEBUG)."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)
    write_incar(args.dest, overwrite=not args.no_overwrite)


if __name__ == "__main__":
    main()
