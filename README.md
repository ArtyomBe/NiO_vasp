# Project: Advanced NiO Surface Modeling with VASP

### Description
This GitHub repository contains all the necessary scripts, configuration files, and tools used for advanced modeling and analysis of Nickel Oxide (NiO) surfaces using the **VASP** software package. The project is focused on exploring the electronic, geometric, and magnetic properties of NiO surfaces with various Miller indices. Key goals include calculating surface energies, band structures, density of states (DOS), adsorption properties, and thermodynamic properties.

### Features
- **VASP Input/Output Automation**: Scripts for generating and managing VASP input files (POSCAR, INCAR, KPOINTS, etc.) and parsing output files (OUTCAR, vasprun.xml).
- **Surface Energy Calculation**: Automated scripts to compute and compare surface energies for different Miller-indexed surfaces.
- **Magnetic Moment Setup**: Configuration for initial magnetic moments and spin-polarized calculations.
- **Band Structure and DOS Analysis**: Tools for post-processing electronic structure data using `pymatgen` and `vaspkit`.
- **Infrared (IR) Spectrum Calculations**: Configuration and analysis scripts for IR spectrum generation.
- **Automation with SLURM**: Batch job scripts for submitting and monitoring calculations on HPC clusters using SLURM.
- **Visualization**: Integration with **VESTA** for structure visualization and tools for adding vacuum layers for slab models.

### Tools and Dependencies
- **Python Scripts**:
  - Automated setup of VASP calculations.
  - Analysis of results (surface energies, band gap, charge density).
  - Visualization of key results (DOS, band structure, magnetic moments).
- **VASP Files**:
  - Sample INCAR, POSCAR, KPOINTS, and POTCAR templates for various surface calculations.
- **Batch Scripts**:
  - Optimized SLURM batch scripts for efficient use of HPC resources.
- **External Tools**:
  - **VESTA** for visualization.
  - **pymatgen** for data parsing and analysis.

### Getting Started
1. Clone the repository:
   ```bash
   git clone https://github.com/ArtyomBe/NiO_vasp.git
   cd NiO_vasp
   ```
2. Set up dependencies using `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
3. Prepare your surface model (POSCAR) and customize the INCAR file for your calculation.
4. Submit calculations to your HPC cluster using the provided SLURM scripts.
5. Post-process results using the analysis scripts provided.

### Use Cases
- Exploration of surface stability and adsorption behavior.
- Comparison of electronic properties across different Miller-indexed surfaces.
- Validation of experimental results through computational modeling.
- Generation of publication-quality plots for energy, DOS, and IR spectra.

### Contributions
Feel free to fork this repository, submit issues, or make pull requests to improve the project. Contributions to additional analysis features or compatibility with other DFT codes are welcome!

### License
This project is licensed under the MIT License. See `LICENSE` for details.
