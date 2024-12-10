from pymatgen.core import Species
from pymatgen.io.cif import CifParser, CifWriter

# Загрузка CIF файла
file_path = '/Users/artyombetekhtin/PycharmProjects/NiO_vasp/test_cases/1010093.cif'
parser = CifParser(file_path)
structure = parser.parse_structures(primitive=True)[0]

# Создание уникальных меток атомов
unique_species = {}
for i, site in enumerate(structure.sites):
    species = list(site.species.keys())[0]
    new_species = Species(species.element.symbol, oxidation_state=species.oxi_state)
    unique_species[species] = new_species

structure = structure.replace_species(unique_species)

# Добавление вакуума вдоль оси c
vacuum_thickness = 15  # Ангстрем
lattice = structure.lattice
new_c = lattice.c * 2 + vacuum_thickness
new_lattice = lattice.matrix.copy()
new_lattice[2][2] = new_c

# Увеличение структуры в 2 раза вдоль оси c
structure.make_supercell([1, 1, 2])
structure.lattice = lattice.__class__(new_lattice)

# Сохранение изменённой структуры
new_cif_path = '/Users/artyombetekhtin/PycharmProjects/NiO_vasp/test_cases/modified_structure.cif'
writer = CifWriter(structure)
writer.write_file(new_cif_path)
print(f"Файл сохранён: {new_cif_path}")
