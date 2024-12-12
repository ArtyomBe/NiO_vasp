import os

from mp_api.client import MPRester

from utils.utils import get_project_path


def generate_vasp_files():
    # Запрос формулы от пользователя
    formula = input("Введите формулу вещества (например, TiO2): ").strip()

    # Базовый путь для сохранения файлов
    base_path = os.path.join(get_project_path(), "inputs")
    substance_folder = os.path.join(base_path, formula)
    os.makedirs(substance_folder, exist_ok=True)

    # Подключение к Materials Project API
    with MPRester("ZA65p8KgTDcyhsEeL186AST4KYoxuIW5") as mpr:
        docs = mpr.materials.search(formula=formula)
        mpids = [doc.material_id for doc in docs]

        for mp_id in mpids:
            # Получение структуры для текущего mp-id
            structure = mpr.get_structure_by_material_id(mp_id)

            # Создание папки для mp-id
            mp_folder = os.path.join(substance_folder, mp_id)
            os.makedirs(mp_folder, exist_ok=True)

            # Генерация POSCAR с pymatgen
            poscar_path = os.path.join(mp_folder, "POSCAR")
            structure.to(filename=poscar_path)

            """
            # Генерация INCAR и KPOINTS
            vis = MPRelaxSet(structure)  # Используется стандартный набор параметров
            incar_path = os.path.join(mp_folder, "INCAR")
            kpoints_path = os.path.join(mp_folder, "KPOINTS")
            vis.incar.write_file(incar_path)
            vis.kpoints.write_file(kpoints_path)
            """

            print(f"Сохранены файлы для {mp_id} в {mp_folder}")


# Запуск функции
generate_vasp_files()
