import os
import shutil
import logging
from xml.etree import ElementTree as ET
from libs.vasprun_optimized import vasprun

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("../output_analysis/surfaces/1_0_0/graphs/processing_log.txt", mode='w'),
        logging.StreamHandler()
    ]
)


def prepare_output_directory(output_dir: str):
    """
    Создаёт или очищает директорию для сохранения графиков.
    """
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    logging.info(f"Директория для графиков подготовлена: {output_dir}")


def parse_filename_suffix(xml_file: str) -> str:
    """
    Парсит XML-файл и возвращает суффикс для названия файла графика.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        gga = root.find(".//i[@name='GGA']")
        gga_suffix = f"_{gga.text}" if gga is not None and gga.text else ""

        ldau = root.find(".//i[@name='LDAU']")
        ldau_suffix = "_U" if ldau is not None and ldau.text.strip() == "T" else "_no_U"

        metagga = root.find(".//i[@name='METAGGA']")
        metagga_suffix = f"_{metagga.text}" if metagga is not None and metagga.text else ""

        return gga_suffix + ldau_suffix + metagga_suffix
    except Exception as e:
        logging.error(f"Ошибка при парсинге XML-файла {xml_file}: {e}")
        return "_unknown"


def process_file(filepath: str, output_dir: str):
    """
    Обрабатывает один файл vasprun.xml и генерирует графики.
    """
    logging.info(f"Обработка файла: {filepath}")

    try:
        vasp = vasprun(filepath, verbosity=1)
    except Exception as e:
        logging.error(f"Ошибка при создании экземпляра vasprun для файла {filepath}: {e}")
        return

    if vasp.error:
        logging.error(f"Ошибка при разборе файла {filepath}: {vasp.errormsg}")
        return

    # Генерация суффикса для файла
    suffix = parse_filename_suffix(filepath)

    # Логгирование данных
    logging.info(
        f"Файл: {os.path.basename(filepath)}{suffix}\n"
        f"Энергия: {vasp.values['calculation']['energy']}\n"
        f"Энергия на атом: {vasp.values['calculation']['energy_per_atom']}\n"
        f"Элементы системы: {vasp.values['elements']}\n"
        f"Состав системы: {vasp.values['composition']}\n"
        f"Значение запрещенной зоны (band gap): {vasp.values['gap']}\n"
        f"Координаты верхней валентной зоны (VBM): {vasp.values['vbm']}\n"
        f"Координаты нижней проводящей зоны (CBM): {vasp.values['cbm']}"
    )

    # Построение графиков
    try:
        dos_path = os.path.join(output_dir, f"DOS_graph{suffix}.png")
        band_path = os.path.join(output_dir, f"BAND_graph{suffix}.png")
        band_dos_path = os.path.join(output_dir, f"BAND_dos_graph{suffix}.png")

        vasp.plot_dos(filename=dos_path)
        vasp.plot_band(filename=band_path)
        vasp.plot_band_dos(filename=band_dos_path)
        logging.info(f"Графики сохранены: {dos_path}, {band_path}, {band_dos_path}")
    except Exception as e:
        logging.error(f"Ошибка при построении графиков для файла {filepath}: {e}")


def process_xml_files(input_dir: str, output_dir: str):
    """
    Обрабатывает все XML-файлы в директории.
    """
    xml_files = [f for f in os.listdir(input_dir) if f.endswith('.xml')]
    if not xml_files:
        logging.warning("В директории нет XML-файлов для обработки.")
        return

    for filename in xml_files:
        filepath = os.path.join(input_dir, filename)
        process_file(filepath, output_dir)


if __name__ == "__main__":
    # Путь к директории с XML-файлами
    input_directory = '/Users/artyombetekhtin/PycharmProjects/NiO_vasp/vasprun-xml/builder/xmls'
    output_directory = os.path.join(input_directory, 'graphs')

    # Подготовка директории и запуск обработки
    prepare_output_directory(output_directory)
    process_xml_files(input_directory, output_directory)
