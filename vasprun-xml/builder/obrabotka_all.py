import os
import sys
import shutil
from xml.etree import ElementTree as ET

sys.path.append(
    '/Users/artyombetekhtin/PycharmProjects/All_for_Quants/vasprun-xml/builder/vasprun_builder/vasper_max.py')
from vasprun_builder.vasper_max_corrected import vasprun

# Директория с XML-файлами и для сохранения графиков
input_directory = '/Users/artyombetekhtin/PycharmProjects/All_for_Quants/vasprun-xml/builder/xmls'
output_directory = os.path.join(input_directory, 'graphs')
log_file_path = os.path.join(output_directory, 'processing_log.txt')


def prepare_output_directory(output_dir):
    """
    Очищает директорию для сохранения графиков или создаёт её, если её не существует
    """
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    print(f"Директория для графиков подготовлена: {output_dir}")


def log_to_file(log_path, message):
    """
    Записывает сообщение в лог-файл
    """
    with open(log_path, 'a') as log_file:
        log_file.write(message + '\n')


def parse_filename_suffix(xml_file):
    """
    Парсит XML-файл и возвращает суффикс для названия файла графика
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Ищем значение GGA
    gga = root.find(".//i[@name='GGA']")
    gga_suffix = f"_{gga.text}" if gga is not None and gga.text else ""

    # Ищем значение LDAU
    ldau = root.find(".//i[@name='LDAU']")
    ldau_suffix = "_U" if ldau is not None and ldau.text.strip() == "T" else "_no_U"

    # Ищем значение METAGGA
    metagga = root.find(".//i[@name='METAGGA']")
    metagga_suffix = f"_{metagga.text}" if metagga is not None and metagga.text else ""

    return gga_suffix + ldau_suffix + metagga_suffix


def process_xml_files(input_dir, output_dir, log_path):
    """
    Обрабатывает все XML-файлы в указанной директории и сохраняет графики в указанную папку
    """
    for filename in os.listdir(input_dir):
        if filename.endswith('.xml'):
            filepath = os.path.join(input_dir, filename)
            print(f"Обработка файла: {filepath}")
            log_to_file(log_path, f"--- Обработка файла: {filename} ---")

            # Создание экземпляра vasprun
            try:
                vasp = vasprun(filepath, verbosity=1)
            except Exception as e:
                error_msg = f"Ошибка при создании экземпляра vasprun для файла {filename}: {e}"
                print(error_msg)
                log_to_file(log_path, error_msg)
                continue

            # Проверка на ошибки
            if vasp.error:
                error_msg = f"Ошибка при разборе файла {filename}: {vasp.errormsg}"
                print(error_msg)
                log_to_file(log_path, error_msg)
                continue

            # Генерация суффикса для файлов
            suffix = parse_filename_suffix(filepath)

            # Логирование данных
            log_data = (
                f"Файл: {filename}{suffix}\n"
                f"Энергия: {vasp.values['calculation']['energy']}\n"
                f"Энергия на атом: {vasp.values['calculation']['energy_per_atom']}\n"
                f"Элементы системы: {vasp.values['elements']}\n"
                f"Состав системы: {vasp.values['composition']}\n"
                f"Значение запрещенной зоны (band gap): {vasp.values['gap']}\n"
                f"Координаты верхней валентной зоны (VBM): {vasp.values['vbm']}\n"
                f"Координаты нижней проводящей зоны (CBM): {vasp.values['cbm']}\n"
            )
            print(log_data)
            log_to_file(log_path, log_data)

            # Построение графиков с уникальными именами
            try:
                dos_path = os.path.join(output_dir, f"DOS_graph{suffix}.png")
                band_path = os.path.join(output_dir, f"BAND_graph{suffix}.png")
                band_dos_path = os.path.join(output_dir, f"BAND_dos_graph{suffix}.png")

                vasp.plot_dos(filename=dos_path, xlim=[-10, 10], ylim=[-6, 6])
                vasp.plot_band(filename=band_path)
                vasp.plot_band_dos(filename=band_dos_path)
                success_msg = f"Графики сохранены: {dos_path}, {band_path}, {band_dos_path}"
                print(success_msg)
                log_to_file(log_path, success_msg)
            except Exception as e:
                error_msg = f"Ошибка при построении графиков для файла {filename}: {e}"
                print(error_msg)
                log_to_file(log_path, error_msg)


# Подготовка директории для графиков
prepare_output_directory(output_directory)

# Удаление старого лог-файла, если он существует
if os.path.exists(log_file_path):
    os.remove(log_file_path)

# Запуск обработки файлов
process_xml_files(input_directory, output_directory, log_file_path)
