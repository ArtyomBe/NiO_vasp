# Project: Advanced NiO Surface Modeling with VASP
### About the Author
This project is developed and maintained by **Artyom Betekhtin**, a computational chemist and graduate student at the **[Infochemistry Scientific Center at ITMO University](https://infochemistry.ru/)**, the leading institution in computational and theoretical chemistry. My primary research focuses on applying density functional theory (DFT) to investigate molecular systems, chemical reactivity, and thermodynamic properties. I aim to integrate advanced mathematical techniques with quantum chemistry to uncover fundamental insights into material and molecular behavior.

I am also an active member of **[Group 24](https://theorchem.ru/wiki/Группа_теоретической_химии_(№24)_ИОХ_РАН) at the Federal State Budgetary Institution of Science N. D. Zelinsky Institute of Organic Chemistry of the Russian Academy of Sciences [(ZIOC RAS)](https://zioc.ru/)**, where I contribute to collaborative projects involving surface modeling, adsorption studies, and catalyst design. My work bridges theoretical and computational chemistry to provide insights into material behavior at the atomic scale.
#### Research and Expertise:
I specialize in **reaction mechanisms**, **thermodynamic stability**, and **enantioselectivity studies**, employing state-of-the-art quantum chemical methods. My expertise includes:

- Proficiency in **ORCA**, **VASP**, **Quantum ESPRESSO**, **xTB**, and **GoodVibes**, with hands-on experience in optimizing workflows for complex molecular and solid-state systems.
- Advanced thermodynamic calculations, leveraging **def2-TZVPD basis sets** and **PBE0-D3BJ functional** for accurate modeling of reaction energetics.
- Modeling reaction mechanisms, such as the **mechanism of TMSCl reactions** and **white phosphorus functionalization**, incorporating kinetic and thermodynamic insights.
- Development of scripts for automated processing of computational outputs, including **automated job management** and **post-processing of electronic structure data**.
- Analysis of electronic properties, including band structures, density of states (DOS), and reaction pathways, with a strong focus on **transition states and intermediates**.

#### Current Projects:
1. **Enantioselectivity of TMSCl Reactions**  
   - Investigating reaction selectivity using DFT to elucidate stereochemical preferences and develop predictive models for asymmetric synthesis.
2. **Mechanistic Study of White Phosphorus Functionalization**  
   - Modeling a photocatalytic reaction mechanism from literature to understand selective activation and functionalization of white phosphorus.
3. **Application of Nanoparticles**  
   - Exploring the surface chemistry and potential applications of nanostructured materials for catalysis and advanced functional materials.

#### Mathematical and Theoretical Focus:
As a researcher with a strong mathematical background, I prioritize the application of linear algebra, differential equations, and mathematical analysis to quantum chemistry problems. My approach ensures rigorous derivation and interpretation of results, offering a deeper understanding of molecular and material systems.

Through this repository, I aim to provide a resource hub for computational chemists and materials scientists, emphasizing reproducibility, automation, and methodological clarity. I welcome collaboration and feedback to advance the field of computational chemistry together.
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