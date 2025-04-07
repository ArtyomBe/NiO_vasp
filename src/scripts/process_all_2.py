import logging
import os
import shutil
from xml.etree import ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

import matplotlib.pyplot as plt
from libs.vasprun_optimized import vasprun
from utils.utils import get_project_path
from colorlog import ColoredFormatter
import gc


def setup_logging(output_dir: str):
    """
    Configures logging to save logs in the specified output directory with colored console output.
    """
    log_file = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "NiO", "logs", "Processing_All_xml_log.txt")

    # Remove old handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Colored console formatting
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red"
        },
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Rotating file handler to limit file size
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(log_file, maxBytes=10 ** 6, backupCount=5)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )
    logging.info(f"Logging configured. Logs will be saved to {log_file}")


def prepare_output_directory(output_dir: str):
    """
    Creates or clears the directory for saving plots and logs.
    """
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    try:
        os.makedirs(output_dir)
        logging.info(f"Output directory prepared: {output_dir}")
    except PermissionError as e:
        logging.error(f"Permission error while creating output directory {output_dir}: {e}")
        raise


def parse_filename_suffix(xml_file: str) -> str:
    """
    Parses the XML file and returns a well-formatted suffix for filenames.
    """
    try:
        suffix_parts = []
        parameter_map = {
            "GGA": lambda x: f"GGA_{x.strip()}",
            "LDAU": lambda x: "U" if x.strip().upper() == "T" else "no_U",
            "AEXX": lambda x: f"AEXX_{round(float(x.strip()) * 100)}%",
        }

        for event, element in ET.iterparse(xml_file, events=("start", "end")):
            if element.tag == "i" and "name" in element.attrib:
                param = element.attrib["name"]
                if param in parameter_map and element.text:
                    try:
                        formatted_value = parameter_map[param](element.text)
                        suffix_parts.append(formatted_value)
                    except ValueError as ve:
                        logging.warning(f"Invalid value for {param} in {xml_file}: {ve}")
                element.clear()  # Free memory immediately
        return f"_{'_'.join(suffix_parts)}" if suffix_parts else "_unknown"

    except ET.ParseError as pe:
        logging.error(f"XML parsing error for file {xml_file}: {pe}")
        return "_unknown"
    except Exception as e:
        logging.error(f"Unexpected error while processing {xml_file}: {e}")
        return "_unknown"


def process_file(filepath: str, output_dir: str):
    """
    Processes a single vasprun.xml file and generates plots.
    """
    logging.info(f"Processing file: {filepath}")

    try:
        vasp = vasprun(filepath, verbosity=1)
    except Exception as e:
        logging.error(f"Error creating vasprun instance for file {filepath}: {e}")
        return

    if vasp.error:
        logging.error(f"Error parsing file {filepath}: {vasp.errormsg}")
        return

    # Generate file suffix
    suffix = parse_filename_suffix(filepath)

    # Log data
    logging.info(
        f"File: {os.path.basename(filepath)}{suffix}\n"
        f"Energy: {vasp.values['calculation']['energy']}\n"
        f"Energy per atom: {vasp.values['calculation']['energy_per_atom']}\n"
        f"System elements: {vasp.values['elements']}\n"
        f"System composition: {vasp.values['composition']}\n"
        f"Band gap: {vasp.values['gap']}\n"
        f"Valence Band Maximum (VBM): {vasp.values['vbm']}\n"
        f"Conduction Band Minimum (CBM): {vasp.values['cbm']}"
    )

    # Generate plots and ensure they are closed after saving
    try:
        os.makedirs(os.path.join(output_dir, "DOS_graphs"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "BAND_graphs"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "BAND_DOS_graphs"), exist_ok=True)

        dos_path = os.path.join(output_dir, "DOS_graphs", f"DOS_graph{suffix}.png")
        band_path = os.path.join(output_dir, "BAND_graphs", f"BAND_graph{suffix}.png")
        band_dos_path = os.path.join(output_dir, "BAND_DOS_graphs", f"BAND_DOS_graph{suffix}.png")

        vasp.plot_dos(filename=dos_path)
        plt.close('all')

        vasp.plot_band(filename=band_path)
        plt.close('all')

        vasp.plot_band_dos(filename=band_dos_path)
        plt.close('all')

        #logging.info(f"Plots saved: {dos_path}, {band_path}, {band_dos_path}")
    except Exception as e:
        logging.error(f"Error generating plots for file {filepath}: {e}")
    finally:
        del vasp  # Explicitly delete to free memory
        gc.collect()


def process_xml_files(input_dir: str, output_dir: str):
    """
    Processes all XML files in the directory in numerical order based on filenames using multithreading.
    """
    xml_files = [f for f in os.listdir(input_dir) if f.endswith('.xml')]
    xml_files = sorted(xml_files, key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))

    if not xml_files:
        logging.warning("No XML files found in the directory for processing.")
        return

    with ThreadPoolExecutor(max_workers=4) as executor:  # Limit threads to avoid memory exhaustion
        future_to_file = {
            executor.submit(process_file, os.path.join(input_dir, filename), output_dir): filename
            for filename in xml_files
        }

        for future in as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error processing file {filename}: {e}")


if __name__ == "__main__":
    input_directory = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "NiO", "xmls")
    output_directory = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "NiO", "graphs")

    prepare_output_directory(output_directory)
    setup_logging(output_directory)
    process_xml_files(input_directory, output_directory)