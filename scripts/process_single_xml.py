import os
import pprint
from libs.vasprun_optimized import vasprun

# Main function
def main(vasprun_file, output_dir, verbosity=1):
    try:
        # Create an instance of the vasprun class
        vasp = vasprun(vasprun_file, verbosity=verbosity)

        # Check for errors
        if vasp.error:
            raise ValueError(f"Error parsing file: {vasp.errormsg}")

        # Print main data
        print("VASP Data:")
        pprint.pprint({
            "Energy": vasp.values['calculation']['energy'],
            "Energy per atom": vasp.values['calculation']['energy_per_atom'],
            "Final atomic positions": vasp.values['finalpos']['positions'],
            "Elements in the system": vasp.values['elements'],
            "System composition": vasp.values['composition'],
            "Band gap value": vasp.values['gap'],
            "Valence Band Maximum (VBM)": vasp.values['vbm'],
            "Conduction Band Minimum (CBM)": vasp.values['cbm']
        })

        # Generate plots
        generate_plots(vasp, output_dir)

    except Exception as e:
        print(f"An error occurred: {e}")


# Function to generate plots
def generate_plots(vasp, output_dir):
    try:
        print("Generating plots...")

        # Check if the directory exists, and create it if necessary
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save plots in the specified directory
        dos_filename = os.path.join(output_dir, "DOS_graph.png")
        vasp.plot_dos(filename=dos_filename, style="t+spd")
        print(f"DOS plot saved as '{dos_filename}'")

        band_filename = os.path.join(output_dir, "BAND_graph.png")
        vasp.plot_band(filename=band_filename)
        print(f"BAND plot saved as '{band_filename}'")

        band_dos_filename = os.path.join(output_dir, "BAND_dos_graph.png")
        vasp.plot_band_dos(filename=band_dos_filename)
        print(f"BAND+DOS plot saved as '{band_dos_filename}'")

    except Exception as e:
        print(f"Error while generating plots: {e}")


# Entry point
if __name__ == "__main__":
    vasprun_file = '../test_cases/vasprun_CA_no_U.xml'  # Specify the path to your vasprun.xml
    output_directory = '/Users/artyombetekhtin/PycharmProjects/NiO_vasp/test_cases'  # Directory for saving plots
    verbosity_level = 1  # Verbosity level
    main(vasprun_file, output_directory, verbosity=verbosity_level)
