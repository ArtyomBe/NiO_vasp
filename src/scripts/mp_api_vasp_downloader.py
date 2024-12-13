import os
import logging
from mp_api.client import MPRester
from utils.utils import get_project_path
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


def generate_vasp_files():
    """
    Fetches structures from Materials Project and generates VASP input files.
    """
    try:
        # Запрос формулы от пользователя
        formula = input("Введите формулу вещества (например, TiO2): ").strip()

        # Проверка формулы
        if not formula:
            logging.error("Формула вещества не может быть пустой!")
            return

        # Базовый путь для сохранения файлов
        base_path = os.path.join(get_project_path(), "inputs")
        substance_folder = os.path.join(base_path, formula)
        os.makedirs(substance_folder, exist_ok=True)

        # Получение API-ключа из переменных окружения
        api_key = os.getenv("MP_API_KEY")
        if not api_key:
            logging.error("API-ключ не найден! Установите переменную окружения 'MP_API_KEY'.")
            return

        # Подключение к Materials Project API
        with MPRester(api_key) as mpr:
            logging.info(f"Подключение к API для формулы: {formula}")
            docs = mpr.materials.search(formula=formula)
            if not docs:
                logging.warning(f"Нет данных для формулы {formula}.")
                return

            mpids = [doc.material_id for doc in docs]

            for mp_id in mpids:
                try:
                    # Получение структуры для текущего mp-id
                    structure = mpr.get_structure_by_material_id(mp_id)

                    # Создание папки для mp-id
                    mp_folder = os.path.join(substance_folder, mp_id)
                    os.makedirs(mp_folder, exist_ok=True)

                    # Генерация POSCAR
                    poscar_path = os.path.join(mp_folder, "POSCAR")
                    structure.to(filename=poscar_path)
                    logging.info(f"Сохранен POSCAR для {mp_id} в {mp_folder}")

                    """
                    # Генерация INCAR и KPOINTS (раскомментируйте при необходимости)
                    vis = MPRelaxSet(structure)  # Используется стандартный набор параметров
                    incar_path = os.path.join(mp_folder, "INCAR")
                    kpoints_path = os.path.join(mp_folder, "KPOINTS")
                    vis.incar.write_file(incar_path)
                    vis.kpoints.write_file(kpoints_path)
                    logging.info(f"Сохранены INCAR и KPOINTS для {mp_id}")
                    """

                except Exception as e:
                    logging.error(f"Ошибка при обработке {mp_id}: {e}")

    except Exception as e:
        logging.error(f"Общая ошибка: {e}")


# Запуск функции
if __name__ == "__main__":
    generate_vasp_files()
