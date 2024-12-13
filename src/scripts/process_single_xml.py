import os
import logging
import pprint

from libs.vasprun_optimized import vasprun
from utils.utils import get_project_path

"""
This script processes VASP calculation results and generates plots for visualization.
It extracts key data from the VASP output (vasprun.xml) and handles errors gracefully.
"""


def setup_logging():
    """
    Configures logging for the script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("vasprun_analysis.log", mode='w')
        ]
    )


def validate_paths(vasprun_file, output_dir):
    """
    Validates the input file and output directory paths.
    """
    if not os.path.exists(vasprun_file):
        raise FileNotFoundError(f"Vasprun file '{vasprun_file}' not found.")
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
        logging.info(f"Created output directory: {output_dir}")


def extract_vasp_data(vasprun_file, verbosity=1):
    """
    Extracts key data from the VASP output using the vasprun_optimized library.
    """
    logging.info(f"Processing VASP file: {vasprun_file}")
    vasp = vasprun(vasprun_file, verbosity=verbosity)

    if vasp.error:
        raise ValueError(f"Error parsing file '{vasprun_file}': {vasp.errormsg}")

    data = {
        "Energy": vasp.values['calculation']['energy'],
        "Energy per atom": vasp.values['calculation']['energy_per_atom'],
        "Final atomic positions": vasp.values['finalpos']['positions'],
        "Elements in the system": vasp.values['elements'],
        "System composition": vasp.values['composition'],
        "Band gap value": vasp.values['gap'],
        "Valence Band Maximum (VBM)": vasp.values['vbm'],
        "Conduction Band Minimum (CBM)": vasp.values['cbm']
    }
    return data, vasp


def display_data(data):
    """
    Prints extracted data in a human-readable format.
    """
    logging.info("Extracted VASP data:")
    pprint.pprint(data)


def generate_plots(vasp, output_dir):
    """
    Generates and saves DOS, BAND, and BAND+DOS plots.
    """
    try:
        logging.info("Generating plots...")
        dos_filename = os.path.join(output_dir, "DOS_graph.png")
        vasp.plot_dos(filename=dos_filename, style="t+spd")
        logging.info(f"DOS plot saved to {dos_filename}")

        band_filename = os.path.join(output_dir, "BAND_graph.png")
        vasp.plot_band(filename=band_filename)
        logging.info(f"BAND plot saved to {band_filename}")

        band_dos_filename = os.path.join(output_dir, "BAND_dos_graph.png")
        vasp.plot_band_dos(filename=band_dos_filename)
        logging.info(f"BAND+DOS plot saved to {band_dos_filename}")

    except Exception as e:
        logging.error(f"Error while generating plots: {e}")
        raise


def main(vasprun_file, output_dir, verbosity=1):
    """
    Main function to process VASP data and generate plots.
    """
    try:
        # Setup logging and validate paths
        setup_logging()
        validate_paths(vasprun_file, output_dir)

        # Extract data
        data, vasp = extract_vasp_data(vasprun_file, verbosity)

        # Display extracted data
        display_data(data)

        # Generate plots
        generate_plots(vasp, output_dir)

    except FileNotFoundError as e:
        logging.error(e)
    except ValueError as e:
        logging.error(e)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    vasprun_file = os.path.join(get_project_path(), "test_cases", "vasprun_CA_U.xml")  # Path to vasprun.xml
    output_directory = os.path.join(get_project_path(), "test_cases")  # Output directory
    verbosity_level = 1  # Verbosity level

    main(vasprun_file, output_directory, verbosity=verbosity_level)
