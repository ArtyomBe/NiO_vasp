import logging
import os
import shutil
from xml.etree import ElementTree as ET

import matplotlib.pyplot as plt
from libs.vasprun_optimized import vasprun
from utils.utils import get_project_path
from colorlog import ColoredFormatter

def setup_logging(output_dir: str):
    """
    Configures logging to save logs in the specified output directory with colored console output.
    """
    log_file = os.path.join(output_dir, "processing_log.txt")

    # Удаление старых обработчиков
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Настройка цветного форматирования для консоли
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

    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Обработчик для файла
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

    # Настройка логирования
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
    os.makedirs(output_dir)
    logging.info(f"Output directory prepared: {output_dir}")


def parse_filename_suffix(xml_file: str) -> str:
    """
    Parses the XML file and returns a suffix for the plot filenames.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        suffix_parts = []

        # Extract GGA
        gga = root.find(".//i[@name='GGA']")
        if gga is not None and gga.text:
            suffix_parts.append(f"GGA_{gga.text.strip()}")

        # Extract LDAU
        ldau = root.find(".//i[@name='LDAU']")
        if ldau is not None and ldau.text.strip() == "T":
            suffix_parts.append("U")
        elif ldau is not None:
            suffix_parts.append("no_U")

        # Extract METAGGA
        metagga = root.find(".//i[@name='METAGGA']")
        if metagga is not None and metagga.text:
            suffix_parts.append(f"METAGGA_{metagga.text.strip()}")

        # Extract AEXX and convert to percentage
        aexx = root.find(".//i[@name='AEXX']")
        if aexx is not None and aexx.text:
            try:
                aexx_value = float(aexx.text.strip())
                suffix_parts.append(f"AEXX_{int(aexx_value * 100)}%")
            except ValueError:
                logging.warning(f"Invalid value for AEXX in {xml_file}")

        # Join suffix parts
        return "_" + "_".join(suffix_parts) if suffix_parts else ""
    except Exception as e:
        logging.error(f"Error parsing XML file {xml_file}: {e}")
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
        #dos_path = os.path.join(output_dir, f"DOS_graph{suffix}.png")
        #band_path = os.path.join(output_dir, f"BAND_graph{suffix}.png")
        #band_dos_path = os.path.join(output_dir, f"BAND_DOS_graph{suffix}.png")
        #dos_path = os.makedirs(os.path.join(output_dir, "DOS_graphs"), exist_ok=True)
        #band_path = os.makedirs(os.path.join(output_dir, "BAND_graphs"), exist_ok=True)
        #band_dos_path = os.makedirs(os.path.join(output_dir, "BAND_DOS_graphs"), exist_ok=True)
        # Ensure the directories exist
        os.makedirs(os.path.join(output_dir, "DOS_graphs"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "BAND_graphs"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "BAND_DOS_graphs"), exist_ok=True)

        # Define paths
        dos_path = os.path.join(output_dir, "DOS_graphs", f"DOS_graph{suffix}.png")
        band_path = os.path.join(output_dir, "BAND_graphs", f"BAND_graph{suffix}.png")
        band_dos_path = os.path.join(output_dir, "BAND_DOS_graphs", f"BAND_DOS_graph{suffix}.png")


        vasp.plot_dos(filename=dos_path)
        plt.close()  # Close the DOS plot

        vasp.plot_band(filename=band_path)
        plt.close()  # Close the BAND plot

        vasp.plot_band_dos(filename=band_dos_path)
        plt.close()  # Close the BAND + DOS plot

        logging.info(f"Plots saved: {dos_path}, {band_path}, {band_dos_path}")
    except Exception as e:
        logging.error(f"Error generating plots for file {filepath}: {e}")


def process_xml_files(input_dir: str, output_dir: str):
    """
    Processes all XML files in the directory.
    """
    xml_files = [f for f in os.listdir(input_dir) if f.endswith('.xml')]
    if not xml_files:
        logging.warning("No XML files found in the directory for processing.")
        return

    for filename in xml_files:
        filepath = os.path.join(input_dir, filename)
        process_file(filepath, output_dir)


if __name__ == "__main__":
    # Path to the directory with XML files
    input_directory = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "xmls")
    output_directory = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "graphs")

    # Prepare the output directory and setup logging
    prepare_output_directory(output_directory)
    setup_logging(output_directory)
    process_xml_files(input_directory, output_directory)
