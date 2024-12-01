import os
import shutil
import logging
from xml.etree import ElementTree as ET
from libs.vasprun_optimized import vasprun

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/Users/artyombetekhtin/PycharmProjects/NiO_vasp/output_analysis/surfaces/1_0_0/graphs/processing_log.txt", mode='w'),
        logging.StreamHandler()
    ]
)


def prepare_output_directory(output_dir: str):
    """
    Creates or clears the directory for saving plots.
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

        gga = root.find(".//i[@name='GGA']")
        gga_suffix = f"_{gga.text}" if gga is not None and gga.text else ""

        ldau = root.find(".//i[@name='LDAU']")
        ldau_suffix = "_U" if ldau is not None and ldau.text.strip() == "T" else "_no_U"

        metagga = root.find(".//i[@name='METAGGA']")
        metagga_suffix = f"_{metagga.text}" if metagga is not None and metagga.text else ""

        return gga_suffix + ldau_suffix + metagga_suffix
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

    # Generate plots
    try:
        dos_path = os.path.join(output_dir, f"DOS_graph{suffix}.png")
        band_path = os.path.join(output_dir, f"BAND_graph{suffix}.png")
        band_dos_path = os.path.join(output_dir, f"BAND_dos_graph{suffix}.png")

        vasp.plot_dos(filename=dos_path)
        vasp.plot_band(filename=band_path)
        vasp.plot_band_dos(filename=band_dos_path)
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
    input_directory = '/Users/artyombetekhtin/PycharmProjects/NiO_vasp/output_analysis/surfaces/1_0_0/xmls'
    output_directory = '/Users/artyombetekhtin/PycharmProjects/NiO_vasp/output_analysis/surfaces/1_0_0/graphs'

    # Prepare the output directory and start processing
    prepare_output_directory(output_directory)
    process_xml_files(input_directory, output_directory)
