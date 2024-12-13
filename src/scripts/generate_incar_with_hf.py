import os
import shutil
import logging

from utils.utils import get_project_path

# Шаблон содержимого файла INCAR
BASE_CONTENT = """SYSTEM   = percentage_study_NiO
# Начальные условия
ISTART   = 0            # Начать расчет с нуля
# Магнитные свойства
ISPIN    = 2            # Спиновый расчет
MAGMOM = 2.0 -2.0 2.0 -2.0 4*0.0
# Энергетические параметры
ENMAX    = 250.0        # Энергия отсечки для плоскостных волн
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
# Учет функционала HSE06
LHFCALC  = .TRUE.       # Включить гибридный функционал
AEXX     = {aexx:.2f}         # Процент обмена Хартри-Фока
# Учет параметра Хаббарда
LDAU      = .TRUE.      # Включить DFT+U
LDAUTYPE  = 2           # Тип схемы DFT+U (с использованием U и J)
LDAUL     = 2 -1        # Значение L (2 = d-орбитали для Ni, -1 = отключено для O)
LDAUU     = 6.30 0.00   # Значение U (6.30 эВ для Ni, 0.0 для O)
LDAUJ     = 1.00 0.00   # Значение J (1.00 эВ для Ni, 0.0 для O)
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


def create_incar_file(folder_path, aexx):
    """
    Creates an INCAR file with the specified AEXX value.
    """
    incar_path = os.path.join(folder_path, "INCAR")
    with open(incar_path, "w") as file:
        file.write(BASE_CONTENT.format(aexx=aexx))
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


def generate_folders(base_path, source_path):
    """
    Generates folders and files for different AEXX values.
    """
    try:
        for i in range(0, 101):
            aexx = i / 100  # Значение AEXX (в долях от 0.00 до 1.00)
            folder_name = f"{i}_percent"  # Имя папки для текущего процента
            folder_path = os.path.join(base_path, folder_name)  # Полный путь к папке

            # Создаем папку, если она не существует
            os.makedirs(folder_path, exist_ok=True)
            logging.info(f"Folder created: {folder_path}")

            # Создаем файл INCAR
            create_incar_file(folder_path, aexx)

            # Копируем дополнительные файлы
            copy_additional_files(source_path, folder_path)

        logging.info("All files and folders successfully created!")

    except FileNotFoundError as fnf_error:
        logging.error(fnf_error)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def main():
    setup_logging()

    base_path = "/Users/artyombetekhtin/Desktop/Кванты/NiO/HF_percentage_study/INPUTS/"
    source_path = os.path.join(get_project_path(), "test_cases")

    generate_folders(base_path, source_path)


if __name__ == "__main__":
    main()
