import os
import shutil
import logging

from utils.utils import get_project_path

# Шаблон содержимого файла INCAR
BASE_CONTENT = """SYSTEM   = LDAU_study_c_V2O5
# Начальные условия
ISTART   = 0            # Начать расчет с нуля
# Магнитные свойства
ISPIN    = 2            # Спиновый расчет
# Энергетические параметры
ENMAX    = 520.0        # Энергия отсечки для плоскостных волн
EDIFF    = 1E-3         # Критерий сходимости по энергии (более строгий для HSE)
# Размывание для изоляторов
ISMEAR   = -5           # Метод размывания Тетраэдра
SIGMA    = 0.1          # Ширина размывания (для HSE не влияет на результат)
# Смешивание плотности
AMIX     = 0.2          # Прямое смешивание для плотности
BMIX     = 0.00001      # Взвешенное смешивание для плотности
AMIX_MAG = 0.8          # Прямое смешивание для магнитной плотности
BMIX_MAG = 0.00001      # Взвешенное смешивание для магнитной плотности
# Вывод данных
LORBIT   = 11           # Проектированная плотность состояний (PDOS)
# Орбитальное смешивание
LMAXMIX  = 4            # Максимальный L для смешивания орбиталей (до f-орбиталей)
# Оптимизация структуры
IBRION   = 2            # Конъюгированный градиент для оптимизации геометрии

LHFCALC  = .TRUE.       # Включить гибридный функционал
AEXX     = 0.15         # Процент обмена Хартри-Фока фиксирован на 15%
# Учет параметра Хаббарда
LDAU      = .TRUE.      # Включить DFT+U
LDAUTYPE  = 2           # Тип схемы DFT+U (с использованием U и J)
LDAUL     = 2 -1        # Значение L (2 = d-орбитали для Ni, -1 = отключено для O)
LDAUU     = {ldauu:.2f} 0.00   # Значение U
LDAUPRINT = 2           # Полный вывод данных DFT+U
"""

def setup_logging():
    """
    Configures logging for the script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

def create_incar_file(folder_path, ldauu):
    """
    Creates an INCAR file with the specified LDAUU value.
    """
    incar_path = os.path.join(folder_path, "INCAR")
    with open(incar_path, "w") as file:
        file.write(BASE_CONTENT.format(ldauu=ldauu))
    logging.info(f"INCAR file created at {incar_path}")

def copy_additional_files(source_path, destination_path):
    """
    Copies additional required files (KPOINTS, POTCAR, POSCAR, run_vaspSW.sh) to the destination folder.
    """
    for filename in ["KPOINTS", "POTCAR", "POSCAR", "run_vaspSW.sh"]:
        source_file = os.path.join(source_path, filename)
        destination_file = os.path.join(destination_path, filename)

        if not os.path.exists(source_file):
            raise FileNotFoundError(f"Source file {source_file} does not exist.")

        shutil.copy(source_file, destination_file)
        logging.info(f"Copied {source_file} to {destination_file}")

def generate_ldau_folders(base_path, source_path, interval=(0, 10), step=0.1):
    """
    Generates folders and files for different LDAUU values within a specified interval and step.
    """
    try:
        start, end = interval
        num_steps = int((end - start) / step) + 1

        for i in range(num_steps):
            ldauu = start + i * step  # Значение LDAUU
            folder_name = f"U_{ldauu:.1f}"  # Имя папки для текущего значения U
            folder_path = os.path.join(base_path, folder_name)  # Полный путь к папке

            # Создаем папку, если она не существует
            os.makedirs(folder_path, exist_ok=True)
            logging.info(f"Folder created: {folder_path}")

            # Создаем файл INCAR
            create_incar_file(folder_path, ldauu)

            # Копируем дополнительные файлы
            copy_additional_files(source_path, folder_path)

        logging.info("All files and folders successfully created!")

    except FileNotFoundError as fnf_error:
        logging.error(fnf_error)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

def main():
    setup_logging()

    #base_path = "/Users/artyombetekhtin/Desktop/Кванты/NiO/LDAU_study/MnO/INPUTS"
    #source_path = os.path.join(get_project_path(), "test_cases", "MnO", "c_MnO")
    base_path = os.path.join(get_project_path(), "LDAU_study", "MnO", "INPUTS")
    source_path = os.path.join(get_project_path(), "test_cases", "MnO", "c_MnO")

    generate_ldau_folders(base_path, source_path, interval=(0, 10), step=0.1)

if __name__ == "__main__":
    main()