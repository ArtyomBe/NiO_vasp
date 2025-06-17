import os
from pymatgen.io.vasp import Potcar
from utils.utils import get_project_path

# Установка пути к директории с POTCAR-файлами
potcar_dir = os.path.join(get_project_path(), "POTCAR_files")
os.environ["PMG_VASP_PSP_DIR"] = potcar_dir

# Определение химических элементов
elements = ["Mn", "O"]

# Создание POTCAR файла
potcar = Potcar(elements, functional="PBE")

# Запись файла POTCAR
with open("POTCAR", "w") as f:
    f.write(str(potcar))

print("POTCAR файл создан успешно!")
