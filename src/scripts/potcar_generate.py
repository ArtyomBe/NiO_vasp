import os
os.environ["PMG_VASP_PSP_DIR"] = "/Users/artyombetekhtin/PycharmProjects/nio_vasp/src/POTCAR_files"

from pymatgen.io.vasp import Potcar

# Определение химических элементов
elements = ["Mn", "O"]

# Создание POTCAR файла (автоматически ищет в PMG_VASP_PSP_DIR)
potcar = Potcar(elements, functional="PBE")

# Запись файла POTCAR
with open("POTCAR", "w") as f:
    f.write(str(potcar))

print("POTCAR файл создан успешно!")

