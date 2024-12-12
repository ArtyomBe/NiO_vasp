# Project: Advanced NiO Surface Modeling with VASP

### About the Project

This repository is dedicated to advanced modeling and analysis of Nickel Oxide (NiO) surfaces using the **VASP**
software package. The project focuses on investigating the electronic, geometric, and magnetic properties of NiO
surfaces with various Miller indices. Key objectives include calculating surface energies, band structures, density of
states (DOS), adsorption properties, and thermodynamic properties.

The goal is to provide computational chemists and materials scientists with automated, reproducible workflows and tools
for analyzing NiO surfaces at the atomic scale.

![The quantum chemical model of NiO: visualization of the structure, molecular orbitals and simulation data performed in VASP.](. src/documentation/NiO_visualisation.png)
---

### About the Author

This project is developed and maintained by **Artyom Betekhtin**, a computational chemist and graduate student at the *
*[Infochemistry Scientific Center at ITMO University](https://infochemistry.ru/)**. I specialize in density functional
theory (DFT) to study molecular systems, surface modeling, and thermodynamic properties.

I am also a member of **[Group 24](https://theorchem.ru/wiki/Группа_теоретической_химии_(№24)_ИОХ_РАН) at ZIOC RAS**,
contributing to projects on surface chemistry and catalyst design. My work combines theoretical and computational
chemistry to explore material behavior at the atomic level.

How you can contact with me:

- [ORCID identifier](https://orcid.org/0009-0005-6805-9492)
- [Email me 1](mailto:work.betekhtin@gmail.com)
- [Email me 2](mailto:a.betekhtin@alumni.nsu.ru)

### Features

- **VASP Input/Output Automation**: Scripts for generating and managing VASP input files (POSCAR, INCAR, KPOINTS, etc.)
  and parsing output files (OUTCAR, vasprun.xml).
- **Surface Energy Calculation**: Automated scripts to compute and compare surface energies for different Miller-indexed
  surfaces.
- **Magnetic Moment Setup**: Configuration for initial magnetic moments and spin-polarized calculations.
- **Band Structure and DOS Analysis**: Tools for post-processing electronic structure data using `pymatgen`
  and `vaspkit`.
- **Visualization**: Integration with **VESTA** for structure visualization and tools for adding vacuum layers for slab
  models.
- **Automation with SLURM**: Batch job scripts for submitting and monitoring calculations on HPC clusters.

---

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

---

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

---

### Use Cases

- Exploration of surface stability and adsorption behavior.
- Comparison of electronic properties across different Miller-indexed surfaces.
- Validation of experimental results through computational modeling.
- Generation of publication-quality plots for energy, DOS, and band structures.

---

### Contributions

Feel free to fork this repository, submit issues, or make pull requests to improve the project. Contributions to
additional analysis features or compatibility with other DFT codes are welcome!

---

### License

This project is licensed under the MIT License. See `LICENSE` for details.

