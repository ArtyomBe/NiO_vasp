from ase.build import bulk, surface
from ase.io import write

# Создаем элементарную ячейку NiO в NaCl-структуре
nio_bulk = bulk('NiO', 'rocksalt', a=4.17)

# Генерируем поверхность (100) с тремя слоями и 15 Å вакуума
surface_nio_100 = surface(nio_bulk, (1, 0, 0), layers=10, vacuum=15)

# Сохраняем в формате POSCAR
write('POSCAR', surface_nio_100)
