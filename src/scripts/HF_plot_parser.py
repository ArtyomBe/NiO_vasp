import os
import re
import logging
import matplotlib.pyplot as plt
import csv
from utils.utils import get_project_path


def setup_logging():
    """
    Configures logging for the script and saves logs in a specific directory.
    """
    # Determine the path to the folder for saving logs
    log_dir = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "logs")
    os.makedirs(log_dir, exist_ok=True)  # Creating a folder if it does not exist

    # The full path to the log file
    log_file = os.path.join(log_dir, "HF_exchange.txt")

    # Setting up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, mode='w')
        ]
    )


def parse_log_file(log_file):
    """
    Parses the log file to extract AEXX, Energy, and Band Gap values.
    """
    aexx_values = []
    energies = []
    band_gaps = []

    try:
        with open(log_file, 'r') as file:
            current_aexx = None
            for line in file:
                # Match AEXX
                aexx_match = re.search(r"AEXX_(\d+)%", line)
                if aexx_match:
                    current_aexx = int(aexx_match.group(1))  # Extract AEXX
                elif current_aexx is not None:
                    # Match Energy
                    energy_match = re.search(r"Energy:\s*(-?\d+\.\d+)", line)
                    # Match Band Gap
                    band_gap_match = re.search(r"Band gap:\s*(-?\d+\.\d+)", line)
                    if energy_match:
                        energies.append(float(energy_match.group(1)))
                    if band_gap_match:
                        band_gaps.append(float(band_gap_match.group(1)))
                        aexx_values.append(current_aexx)  # Save AEXX only when both values are extracted
                        current_aexx = None  # Reset for next block
        return aexx_values, energies, band_gaps
    except FileNotFoundError:
        logging.error(f"File {log_file} not found.")
        raise
    except Exception as e:
        logging.error(f"An error occurred while parsing the log file: {e}")
        raise


def save_data(output_file, aexx_values, energies, band_gaps):
    """
    Saves the extracted data to a file.
    """
    try:
        with open(output_file, 'w') as outfile:
            outfile.write("График 1\n")
            outfile.write("AEXX (%)\tEnergy (eV)\n")
            for x, y in zip(aexx_values, energies):
                outfile.write(f"{x}\t{y}\n")
            outfile.write("\n")

            outfile.write("График 2\n")
            outfile.write("AEXX (%)\tBand Gap (eV)\n")
            for x, y in zip(aexx_values, band_gaps):
                outfile.write(f"{x}\t{y}\n")
        logging.info(f"Data saved to {output_file}")
    except Exception as e:
        logging.error(f"An error occurred while saving data: {e}")
        raise


def save_band_gap_data(csv_file, aexx_values, band_gaps):
    """
    Saves AEXX and Band Gap data to a CSV file.
    """
    try:
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["AEXX (%)", "Band Gap (eV)"])
            for x, y in zip(aexx_values, band_gaps):
                writer.writerow([x, y])
        logging.info(f"Band Gap data saved to {csv_file}")
    except Exception as e:
        logging.error(f"An error occurred while saving Band Gap data: {e}")
        raise


def plot_graphs(aexx_values, energies, band_gaps, output_dir):
    """
    Plots and saves graphs for Energy and Band Gap against AEXX.
    """
    try:
        # Plot Energy vs AEXX
        plt.figure(figsize=(10, 5))
        plt.plot(aexx_values, energies, marker='o', label='Energy')
        plt.title('Energy vs AEXX')
        plt.xlabel('AEXX (%)')
        plt.ylabel('Energy (eV)')
        plt.grid(True)
        plt.legend()
        energy_plot_path = os.path.join(output_dir, "Energy_vs_AEXX.png")
        plt.savefig(energy_plot_path, dpi=1200)
        plt.show()
        logging.info(f"Energy vs AEXX plot saved to {energy_plot_path}")

        # Plot Band Gap vs AEXX
        plt.figure(figsize=(10, 5))
        plt.plot(aexx_values, band_gaps, marker='o', color='orange', label='Band Gap')
        plt.title('Band Gap vs AEXX')
        plt.xlabel('AEXX (%)')
        plt.ylabel('Band Gap (eV)')
        plt.grid(True)
        plt.legend()
        band_gap_plot_path = os.path.join(output_dir, "BandGap_vs_AEXX.png")
        plt.savefig(band_gap_plot_path, dpi=1200)
        plt.show()
        logging.info(f"Band Gap vs AEXX plot saved to {band_gap_plot_path}")
    except Exception as e:
        logging.error(f"An error occurred while plotting graphs: {e}")
        raise


def main():
    setup_logging()

    project_path = get_project_path()
    log_path = os.path.join(project_path, "output_analysis", "HF_analysis", "logs", "Processing_All_xml_log.txt")
    output_path = os.path.join(project_path, "output_analysis", "HF_analysis", "logs", "HF_coordinates.txt")
    band_gap_csv = os.path.join(project_path, "output_analysis", "HF_analysis", "logs", "AEXX_Band_Gap.csv")
    output_dir = os.path.join(project_path, "output_analysis", "HF_analysis", "graphs")

    try:
        aexx_values, energies, band_gaps = parse_log_file(log_path)

        if not aexx_values or not energies or not band_gaps:
            logging.warning("No data found to process.")
            return

        # Sort data by AEXX values
        sorted_data = sorted(zip(aexx_values, energies, band_gaps), key=lambda x: x[0])
        aexx_values, energies, band_gaps = zip(*sorted_data)

        save_data(output_path, aexx_values, energies, band_gaps)
        save_band_gap_data(band_gap_csv, aexx_values, band_gaps)
        plot_graphs(aexx_values, energies, band_gaps, output_dir)

    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")


if __name__ == "__main__":
    main()
