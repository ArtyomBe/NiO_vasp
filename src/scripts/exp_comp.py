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
    log_dir = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "TiO2", "Anatase", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "HF_exchange.txt")

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
    Parses the log file to extract AEXX, Energy, and Band Gap values, ensuring unique AEXX entries.
    """
    parsed_data = {}

    try:
        with open(log_file, 'r') as file:
            current_aexx = None
            for line in file:
                aexx_match = re.search(r"AEXX_(\d+)%", line)
                if aexx_match:
                    current_aexx = int(aexx_match.group(1))
                    if current_aexx not in parsed_data:
                        parsed_data[current_aexx] = {"energy": None, "band_gap": None}
                elif current_aexx is not None:
                    energy_match = re.search(r"Energy:\s*(-?\d+\.\d+)", line)
                    if energy_match and parsed_data[current_aexx]["energy"] is None:
                        parsed_data[current_aexx]["energy"] = float(energy_match.group(1))

                    band_gap_match = re.search(r"Band gap:\s*(-?\d+\.\d+)", line)
                    if band_gap_match and parsed_data[current_aexx]["band_gap"] is None:
                        parsed_data[current_aexx]["band_gap"] = float(band_gap_match.group(1))

        parsed_data = {k: v for k, v in parsed_data.items() if v["energy"] is not None and v["band_gap"] is not None}

        aexx_values = sorted(parsed_data.keys())
        energies = [parsed_data[aexx]["energy"] for aexx in aexx_values]
        band_gaps = [parsed_data[aexx]["band_gap"] for aexx in aexx_values]

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
            outfile.write("HF Exchange (%)\tEnergy (eV)\n")
            for x, y in zip(aexx_values, energies):
                outfile.write(f"{x}\t{y}\n")
            outfile.write("\n")

            outfile.write("График 2\n")
            outfile.write("HF Exchange (%)\tBand Gap (eV)\n")
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
            writer.writerow(["HF Exchange (%)", "Band Gap (eV)"])
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
        plt.figure(figsize=(10, 5))
        plt.plot(aexx_values, energies, marker='o', markersize=5, label='Energy')
        plt.title('Energy vs HF Exchange')
        plt.xlabel('HF Exchange (%)')
        plt.ylabel('Energy (eV)')
        plt.grid(True)
        #plt.legend()
        energy_plot_path = os.path.join(output_dir, "Energy_vs_AEXX.png")
        plt.savefig(energy_plot_path, dpi=1200)
        plt.show()
        logging.info(f"Energy vs HF Exchange plot saved to {energy_plot_path}")

        plt.figure(figsize=(10, 5))
        plt.plot(aexx_values, band_gaps, marker='o', markersize=5, color='orange', label='Band Gap')
        plt.xlabel('HF Exchange (%)')
        plt.ylabel('Band Gap (eV)')
        plt.grid(True)
        band_gap_plot_path = os.path.join(output_dir, "BandGap_vs_AEXX.png")
        plt.savefig(band_gap_plot_path, dpi=1200)
        plt.show()
        logging.info(f"Band Gap vs HF Exchange plot saved to {band_gap_plot_path}")
    except Exception as e:
        logging.error(f"An error occurred while plotting graphs: {e}")
        raise


def plot_with_experimental_band_gap(aexx_values, band_gaps, output_dir, experimental_band_gap):
    """
    Строит график Band Gap vs HF Exchange с горизонтальной линией на уровне экспериментального значения.
    """
    try:
        plt.figure(figsize=(10, 5))
        plt.plot(aexx_values, band_gaps, marker='o', markersize=5, color='orange', label='Теоретический Band Gap')
        plt.axhline(y=experimental_band_gap, color='red', linestyle='--', label=f'Экспериментальный Band Gap: {experimental_band_gap:.2f} эВ')
        plt.xlabel('HF Exchange (%)')
        plt.ylabel('Band Gap (eV)')
        plt.grid(True)
        #plt.legend()
        plot_path = os.path.join(output_dir, "BandGap_vs_AEXX_with_exp.png")
        plt.savefig(plot_path, dpi=600)
        plt.show()
        logging.info(f"Band Gap plot with experimental value saved to {plot_path}")
    except Exception as e:
        logging.error(f"An error occurred while plotting Band Gap with experimental line: {e}")
        raise


def main():
    setup_logging()

    project_path = get_project_path()
    log_path = os.path.join(project_path, "output_analysis", "HF_analysis", "TiO2", "Anatase", "logs", "Processing_All_xml_log.txt")
    output_path = os.path.join(project_path, "output_analysis", "HF_analysis", "TiO2", "Anatase", "logs", "HF_coordinates.txt")
    band_gap_csv = os.path.join(project_path, "output_analysis", "HF_analysis", "TiO2", "Anatase", "logs", "AEXX_Band_Gap.csv")
    output_dir = os.path.join(project_path, "output_analysis", "HF_analysis", "TiO2", "Anatase", "graphs")
    os.makedirs(output_dir, exist_ok=True)

    try:
        aexx_values, energies, band_gaps = parse_log_file(log_path)

        if not aexx_values or not energies or not band_gaps:
            logging.warning("No data found to process.")
            return

        sorted_data = sorted(zip(aexx_values, energies, band_gaps), key=lambda x: x[0])
        aexx_values, energies, band_gaps = zip(*sorted_data)

        save_data(output_path, aexx_values, energies, band_gaps)
        save_band_gap_data(band_gap_csv, aexx_values, band_gaps)
        plot_graphs(aexx_values, energies, band_gaps, output_dir)

        # Получение значения от пользователя
        try:
            user_input = input("Введите экспериментальное значение band gap (в эВ): ").strip()
            experimental_band_gap = float(user_input)
            plot_with_experimental_band_gap(aexx_values, band_gaps, output_dir, experimental_band_gap)
        except ValueError:
            logging.warning("Некорректный ввод: экспериментальное значение не распознано. Пропускаем построение с горизонтальной линией.")

    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")


if __name__ == "__main__":
    main()
