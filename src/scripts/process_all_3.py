import os
import re
import gc
import logging
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from logging.handlers import RotatingFileHandler

# Use a non-interactive backend for faster plotting/headless runs
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from xml.etree import ElementTree as ET
from colorlog import ColoredFormatter

from libs.vasprun_optimized import vasprun
from utils.utils import get_project_path


# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------

def _build_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("process_all")
    logger.setLevel(logging.INFO)

    # Remove old handlers to avoid duplicates on re-runs
    for h in list(logger.handlers):
        logger.removeHandler(h)

    # Ensure parent directories exist
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Console (colored)
    console_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    ch = logging.StreamHandler()
    ch.setFormatter(console_formatter)
    ch.setLevel(logging.INFO)

    # File (rotating)
    fh = RotatingFileHandler(log_file, maxBytes=10 ** 6, backupCount=5)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    fh.setLevel(logging.INFO)

    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.info(f"Logging configured. Logs will be saved to {log_file}")
    return logger


# --------------------------------------------------------------------------------------
# Core domain classes
# --------------------------------------------------------------------------------------

class XMLSuffixParser:
    """Fast streaming parser for small set of VASP tags used in filenames."""

    PARAM_MAP = {
        "GGA": lambda x: f"GGA_{x.strip()}",
        "LDAU": lambda x: "U" if x.strip().upper() == "T" else "no_U",
        "AEXX": lambda x: f"AEXX_{round(float(x.strip()) * 100)}%",
    }

    @classmethod
    def parse_suffix(cls, xml_file: Path, logger: Optional[logging.Logger] = None) -> str:
        try:
            suffix_parts: List[str] = []
            # iterparse is streaming -> low memory
            for _event, element in ET.iterparse(str(xml_file), events=("start", "end")):
                if element.tag == "i" and (name := element.attrib.get("name")) in cls.PARAM_MAP:
                    text = element.text
                    if text is not None:
                        try:
                            suffix_parts.append(cls.PARAM_MAP[name](text))
                        except Exception as ve:
                            if logger:
                                logger.warning(f"Invalid value for {name} in {xml_file.name}: {ve}")
                # Free memory as we go
                element.clear()
            return f"_{'_'.join(suffix_parts)}" if suffix_parts else "_unknown"
        except ET.ParseError as pe:
            if logger:
                logger.error(f"XML parsing error for file {xml_file.name}: {pe}")
            return "_unknown"
        except Exception as e:
            if logger:
                logger.error(f"Unexpected error while processing {xml_file.name}: {e}")
            return "_unknown"


class VaspJob:
    """Encapsulates processing of a single vasprun.xml file."""

    __slots__ = ("xml_path", "out_dir")

    def __init__(self, xml_path: Path, out_dir: Path):
        self.xml_path = xml_path
        self.out_dir = out_dir

    def run(self) -> None:
        logger = logging.getLogger("process_all")
        logger.info(f"Processing file: {self.xml_path}")

        try:
            vasp = vasprun(str(self.xml_path), verbosity=1)
        except Exception as e:
            logger.error(f"Error creating vasprun instance for {self.xml_path.name}: {e}")
            return

        if getattr(vasp, "error", False):
            logger.error(f"Error parsing file {self.xml_path.name}: {getattr(vasp, 'errormsg', 'unknown error')}")
            return

        suffix = XMLSuffixParser.parse_suffix(self.xml_path, logger)

        try:
            values = vasp.values
            calc = values.get("calculation", {})
            logger.info(
                "\n".join(
                    [
                        f"File: {self.xml_path.name}{suffix}",
                        f"Energy: {calc.get('energy')}",
                        f"Energy per atom: {calc.get('energy_per_atom')}",
                        f"System elements: {values.get('elements')}",
                        f"System composition: {values.get('composition')}",
                        f"Band gap: {values.get('gap')}",
                        f"Valence Band Maximum (VBM): {values.get('vbm')}",
                        f"Conduction Band Minimum (CBM): {values.get('cbm')}",
                    ]
                )
            )
        except Exception as e:
            logger.warning(f"Logging values failed for {self.xml_path.name}: {e}")

        # Prepare output subfolders once per job
        dos_dir = self.out_dir / "DOS_graphs"
        band_dir = self.out_dir / "BAND_graphs"
        band_dos_dir = self.out_dir / "BAND_DOS_graphs"
        for d in (dos_dir, band_dir, band_dos_dir):
            d.mkdir(parents=True, exist_ok=True)

        try:
            vasp.plot_dos(filename=str(dos_dir / f"DOS_graph{suffix}.png"))
            plt.close("all")

            vasp.plot_band(filename=str(band_dir / f"BAND_graph{suffix}.png"))
            plt.close("all")

            vasp.plot_band_dos(filename=str(band_dos_dir / f"BAND_DOS_graph{suffix}.png"))
            plt.close("all")
        except Exception as e:
            logger.error(f"Error generating plots for {self.xml_path.name}: {e}")
        finally:
            # Free memory (crucial when running in parallel)
            del vasp
            gc.collect()


class VaspBatchRunner:
    """High-level orchestrator for scanning, sorting and parallel execution."""

    def __init__(self, input_dir: Path, output_dir: Path, use_processes: bool = True, max_workers: Optional[int] = None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.use_processes = use_processes
        # Sensible default: cap workers to CPU count, but avoid oversubscription
        self.max_workers = max_workers or max(1, min(os.cpu_count() or 4, 8))

    @staticmethod
    def _numeric_sort_key(path: Path) -> int:
        # Extract first integer from filename for numeric ordering; fallback 0
        m = re.search(r"(\d+)", path.name)
        return int(m.group(1)) if m else 0

    def _collect_xmls(self) -> List[Path]:
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")
        files = sorted(self.input_dir.glob("*.xml"), key=self._numeric_sort_key)
        return files

    def prepare_output_dir(self, logger: logging.Logger) -> None:
        # Safer and faster than shutil.rmtree + makedirs when the dir may be large:
        # Only (re)create leaf directories we use; avoid nuking the whole tree.
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "DOS_graphs").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "BAND_graphs").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "BAND_DOS_graphs").mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory prepared: {self.output_dir}")

    def run(self, logger: logging.Logger) -> None:
        xml_files = self._collect_xmls()
        if not xml_files:
            logger.warning("No XML files found in the directory for processing.")
            return

        self.prepare_output_dir(logger)

        executor_cls = ProcessPoolExecutor if self.use_processes else __import__("concurrent.futures").futures.ThreadPoolExecutor
        logger.info(
            f"Starting parallel processing with {executor_cls.__name__} (max_workers={self.max_workers}) on {len(xml_files)} files"
        )

        # Submit jobs; construct arguments per process to avoid pickling large objects
        with executor_cls(max_workers=self.max_workers) as ex:
            futures = {
                ex.submit(_run_single_job, str(p), str(self.output_dir)): p.name for p in xml_files
            }
            for fut in as_completed(futures):
                name = futures[fut]
                try:
                    fut.result()
                except Exception as e:
                    logger.error(f"Error processing file {name}: {e}")


# Helper function at module top-level so it is picklable by ProcessPoolExecutor

def _run_single_job(xml_path: str, out_dir: str) -> None:
    job = VaspJob(Path(xml_path), Path(out_dir))
    job.run()


# --------------------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    project = Path(get_project_path())

    input_directory = project / "output_analysis" / "HF_analysis" / "TiO2" / "Anatase" / "xmls"
    output_directory = project / "output_analysis" / "HF_analysis" / "TiO2" / "Anatase" / "graphs"
    log_file = project / "output_analysis" / "HF_analysis" / "TiO2" / "Anatase" / "logs" / "Processing_All_xml_log.txt"

    logger = _build_logger(log_file)

    # Switch to threads if IO-bound or if spawning processes is expensive on your system
    use_processes = True
    # Optionally override via env var, e.g., EXPORT VASP_USE_PROCESSES=0
    env_flag = os.getenv("VASP_USE_PROCESSES")
    if env_flag is not None:
        use_processes = env_flag not in ("0", "false", "False")

    max_workers_env = os.getenv("VASP_MAX_WORKERS")
    max_workers = int(max_workers_env) if max_workers_env and max_workers_env.isdigit() else None

    runner = VaspBatchRunner(input_directory, output_directory, use_processes=use_processes, max_workers=max_workers)
    runner.run(logger)