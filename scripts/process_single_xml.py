import pprint
from libs.vasprun_optimized import vasprun

# Основная функция
def main(vasprun_file, verbosity=1):
    try:
        # Создание экземпляра класса vasprun
        vasp = vasprun(vasprun_file, verbosity=verbosity)

        # Проверка на ошибки
        if vasp.error:
            raise ValueError(f"Ошибка при разборе файла: {vasp.errormsg}")

        # Вывод основных данных
        print("Данные VASP:")
        pprint.pprint({
            "Энергия": vasp.values['calculation']['energy'],
            "Энергия на атом": vasp.values['calculation']['energy_per_atom'],
            "Финальные позиции атомов": vasp.values['finalpos']['positions'],
            "Элементы системы": vasp.values['elements'],
            "Состав системы": vasp.values['composition'],
            "Значение запрещенной зоны (band gap)": vasp.values['gap'],
            "Координаты верхней валентной зоны (VBM)": vasp.values['vbm'],
            "Координаты нижней проводящей зоны (CBM)": vasp.values['cbm']
        })

        # Построение графиков
        generate_plots(vasp)

    except Exception as e:
        print(f"Произошла ошибка: {e}")


# Функция для построения графиков
def generate_plots(vasp):
    try:
        print("Создание графиков...")
        vasp.plot_dos(filename="DOS_graph")
        print("График DOS сохранён как 'DOS_graph.png'")
        vasp.plot_band(filename="BAND_graph")
        print("График BAND сохранён как 'BAND_graph.png'")
        vasp.plot_band_dos(filename="BAND_dos_graph")
        print("График BAND+DOS сохранён как 'BAND_dos_graph.png'")
    except Exception as e:
        print(f"Ошибка при создании графиков: {e}")


# Точка входа
if __name__ == "__main__":
    vasprun_file = '../test_cases/vasprun_CA_no_U.xml'  # Укажите путь к вашему vasprun.xml
    verbosity_level = 1  # Уровень детализации
    main(vasprun_file, verbosity=verbosity_level)
