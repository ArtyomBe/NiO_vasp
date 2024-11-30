# Предположим, что весь ваш код находится в файле vasprun_builder.py
import sys
import pprint
sys.path.append('/Users/artyombetekhtin/PycharmProjects/All_for_Quants/vasprun-xml/builder/vasprun_builder/vasper_max.py')

from vasprun_builder.vasper_max_corrected import vasprun

#from vasprun_builder import IR

# Создание экземпляра класса vasprun
vasp = vasprun('vasprun.xml', verbosity=1)

# Проверка на наличие ошибок
if vasp.error:
    print("Ошибка при разборе файла:", vasp.errormsg)
else:
    # Доступ к различным данным
    print("Энергия:", vasp.values['calculation']['energy'])
    print("Энергия на атом:", vasp.values['calculation']['energy_per_atom'])
    print("Финальные позиции атомов:", vasp.values['finalpos']['positions'])
    print("Элементы системы:", vasp.values['elements'])
    print("Состав системы:", vasp.values['composition'])
    print("Значение запрещенной зоны (band gap):", vasp.values['gap'])
    print("Координаты верхней валентной зоны (VBM):", vasp.values['vbm'])
    print("Координаты нижней проводящей зоны (CBM):", vasp.values['cbm'])
    vasp.plot_dos(filename="DOS_graph", xlim=[-10, 10], ylim=[-6, 6])
    vasp.plot_band(filename="BAND_graph")
    vasp.plot_band_dos(filename="BAND_dos_graph")