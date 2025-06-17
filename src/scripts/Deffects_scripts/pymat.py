import os
from pymatgen.io.vasp import Vasprun
from utils.utils import get_project_path

def get_bandgap_from_vasprun(vasprun_path):
    """
    Возвращает информацию о band gap из файла vasprun.xml с использованием pymatgen.
    """
    vasprun = Vasprun(vasprun_path)
    band_structure = vasprun.get_band_structure()
    band_gap = band_structure.get_band_gap()

    return band_gap

# Пример использования
if __name__ == "__main__":
    vasprun_path = os.path.join(get_project_path(), "test_cases", "HF_study", "vasprunnn.xml")
    gap_info = get_bandgap_from_vasprun(vasprun_path)

    print("Band gap info:")
    print(f"  Direct gap: {gap_info['direct']}")
    print(f"  Energy gap: {gap_info['energy']} eV")
    print(f"  Transition: {gap_info['transition']}")
