import os
from ase.io import read, write
from ase.build import surface

def generate_bulk_structures(cif_file, miller_indices, layers=3, output_dir="bulk_xyz"):
    """Генерирует объемные структуры (bulk) для заданных индексов Миллера и сохраняет их в формате XYZ."""
    bulk = read(cif_file)
    os.makedirs(output_dir, exist_ok=True)

    for hkl in miller_indices:
        slab = surface(bulk, hkl, layers)  # Создание bulk-структуры без вакуума
        xyz_filename = os.path.join(output_dir, f"bulk_{hkl[0]}{hkl[1]}{hkl[2]}.xyz")
        write(xyz_filename, slab)

# Пример использования
cif_file = "/Users/artyombetekhtin/PycharmProjects/nio_vasp/src/test_cases/c-MnO.cif"  # Указать путь к файлу
miller_indices = [(1, 0, 0), (2, 0, 0), (3, 0, 0), (4, 0, 0)]  # Заданные индексы Миллера

generate_bulk_structures(cif_file, miller_indices)