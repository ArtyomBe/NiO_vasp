import os
import pprint
from libs.vasprun_optimized import vasprun
"""
This code performs the following actions:

1. Analyzes the VASP xml file (vasprun.xml) using the specialized library `vasprun_optimized'. 
   The main task is to extract data from a file, such as:
   - Total energy of the system and energy per atom.
   - Final atomic positions.
   - The composition of the system (elements and their proportion).
   - The value of the energy gap (Band Gap), the position of the VBM (valence band) and CBM (conduction band).

2. Displays the basic data extracted from vasprun.xml, in a convenient form using the `pprint` library.

3. Generates and saves the following graphs in the specified directory:
   - State Density Graph (DOS).
   - A graph of the BAND structure.
   - Combined graph of the band structure and density of states (BAND+DOS).

4. Checks for errors when parsing the file and generating graphs, and also creates an output directory if it is missing.

The code is designed to analyze a single xml file and visualize the results, which makes it convenient to interpret VASP calculation data.
"""

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
    vasprun_file = '../test_cases/vasprun_CA_U.xml'  # Specify the path to your vasprun.xml
    output_directory = '/Users/artyombetekhtin/PycharmProjects/NiO_vasp/test_cases'  # Directory for saving plots
    verbosity_level = 1  # Verbosity level
    main(vasprun_file, output_directory, verbosity=verbosity_level)
