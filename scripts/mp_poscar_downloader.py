import os
from mp_api.client import MPRester


def save_poscars_by_formula():
    # Базовый путь для сохранения файлов
    base_path = "/Users/artyombetekhtin/PycharmProjects/NiO_vasp/inputs"

    # Запрос формулы от пользователя
    formula = input("Введите формулу вещества (например, TiO2): ").strip()

    # Создание подпапки для вещества
    substance_folder = os.path.join(base_path, formula)
    os.makedirs(substance_folder, exist_ok=True)

    # Подключение к Materials Project API
    with MPRester("ZA65p8KgTDcyhsEeL186AST4KYoxuIW5") as mpr:
        # Поиск материалов по формуле
        docs = mpr.materials.search(formula=formula)

        # Получение списка ID
        mpids = [doc.material_id for doc in docs]

    # Обработка каждого mp-id
    for mp_id in mpids:
        with MPRester("ZA65p8KgTDcyhsEeL186AST4KYoxuIW5") as mpr:
            # Получение структуры для текущего mp-id
            structure = mpr.get_structure_by_material_id(mp_id)

            # Путь для текущей папки mp-id
            mp_folder = os.path.join(substance_folder, mp_id)

            # Создание папки для mp-id, если она не существует
            os.makedirs(mp_folder, exist_ok=True)

            # Путь для сохранения POSCAR
            poscar_path = os.path.join(mp_folder, "POSCAR")

            # Сохранение структуры в POSCAR
            structure.to(filename=poscar_path)

    print(f"POSCAR файлы для вещества {formula} сохранены в папку: {substance_folder}")


# Запуск функции
save_poscars_by_formula()
