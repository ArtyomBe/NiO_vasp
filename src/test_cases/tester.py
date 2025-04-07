from pymatgen.io.vasp import Vasprun
vasp = Vasprun("vasprun53.xml", parse_projected_eigen=True)
bs = vasp.get_band_structure()
print(bs.get_band_gap())
