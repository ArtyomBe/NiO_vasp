from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.plotter import BSPlotter

vasprun = Vasprun("/Users/artyombetekhtin/PycharmProjects/NiO_vasp/test_cases/vasprun.xml", parse_projected_eigen=True)
band_structure = vasprun.get_band_structure()
plotter = BSPlotter(band_structure)
plotter.get_plot().show()
