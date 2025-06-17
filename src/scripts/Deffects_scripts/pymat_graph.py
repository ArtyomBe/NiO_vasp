import os
import matplotlib.pyplot as plt
from pymatgen.io.vasp import Vasprun
from pymatgen.electronic_structure.plotter import BSPlotter
from utils.utils import get_project_path

def plot_band_structure(vasprun_path, save_path="band_structure.png"):
    """
    Строит график зонной структуры из vasprun.xml и сохраняет как PNG.
    """
    vasprun = Vasprun(vasprun_path, parse_projected_eigen=True)
    band_structure = vasprun.get_band_structure(line_mode=True)

    plotter = BSPlotter(band_structure)
    plotter.get_plot()  # Возвращает axes, а не fig

    fig = plt.gcf()  # Получаем текущую figure от matplotlib
    fig.savefig(save_path, bbox_inches='tight', dpi=300)
    print(f"Band structure saved to: {save_path}")
    plt.show()


if __name__ == "__main__":
    vasprun_path = os.path.join(get_project_path(), "test_cases", "HF_study", "vasprunnn.xml")  # Укажи путь к своему vasprun.xml
    plot_band_structure(vasprun_path)
