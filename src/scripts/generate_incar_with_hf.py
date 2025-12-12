import os
import shutil
import logging

from utils.utils import get_project_path

# Шаблон содержимого файла INCAR
BASE_CONTENT = """SYSTEM  = NiO
NCORE   = 8

ENCUT   = 600
ALGO    = Fast
IBRION  = 2
ISIF    = 3
NSW     = 1000
POTIM   = 0.2

EDIFF   = 1.0e-06
ISYM    = 0
LREAL   = .FALSE.

ISMEAR  = 0
SIGMA   = 0.05

PREC    = Accurate
ADDGRID = .TRUE.

NWRITE  = 1
LCHARG  = .FALSE.
LWAVE   = .FALSE.
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

    #base_path = "/Users/artyombetekhtin/Desktop/Кванты/NiO/HF_percentage_study/V2O5/INPUTS"
    base_path = os.path.join(get_project_path(), "HF_study", "INPUTS", "TiO2")
    source_path = os.path.join(get_project_path(), "test_cases", "NiO")

    generate_folders(base_path, source_path)


if __name__ == "__main__":
    main()
