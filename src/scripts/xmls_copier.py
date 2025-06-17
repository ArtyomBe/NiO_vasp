import os
import shutil
import re
from utils.utils import get_project_path

# Пути
project_path = get_project_path()
source_dir = os.path.join(project_path, "HF_study", "TiO2", "OUTPUTS", "Anatase")
destination_dir = os.path.join(project_path, "output_analysis", "HF_analysis", "TiO2", "Anatase", "xmls")

# Пути
#source_dir = "/Users/artyombetekhtin/Desktop/Кванты/NiO/HF_percentage_study/TiO2/OUTPUTS/Anatase"
#destination_dir = "/Users/artyombetekhtin/PycharmProjects/nio_vasp/src/output_analysis/HF_analysis/TiO2/Anatase/xmls"

# Очищаем целевую директорию
if os.path.exists(destination_dir):
    for file in os.listdir(destination_dir):
        file_path = os.path.join(destination_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
else:
    os.makedirs(destination_dir)

# Шаблон названия папки: <число>_percent
pattern = re.compile(r"^(\d+)_percent$")

for folder_name in os.listdir(source_dir):
    match = pattern.match(folder_name)
    if not match:
        continue

    number = match.group(1)
    folder_path = os.path.join(source_dir, folder_name)

    old_vasprun = os.path.join(folder_path, "vasprun.xml")
    renamed_vasprun = os.path.join(folder_path, f"vasprun{number}.xml")

    # Переименование, если нужно
    if os.path.exists(old_vasprun):
        os.rename(old_vasprun, renamed_vasprun)
        print(f"🔁 Переименован: {old_vasprun} → {renamed_vasprun}")
    elif not os.path.exists(renamed_vasprun):
        print(f"⚠️ Нет vasprun.xml и vasprun{number}.xml в {folder_name}")
        continue  # Пропускаем, если нужного файла нет

    # Копирование в целевую папку
    destination_path = os.path.join(destination_dir, f"vasprun{number}.xml")
    shutil.copyfile(renamed_vasprun, destination_path)
    print(f"✔ Скопирован: {renamed_vasprun} → {destination_path}")
