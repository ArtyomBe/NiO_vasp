import pandas as pd
import matplotlib.pyplot as plt
import os
from utils.utils import get_project_path

base_path = get_project_path()
tio2 = pd.read_csv(os.path.join(base_path, "output_analysis", "HF_analysis", "TiO2", "Anatase", "logs", "AEXX_Band_Gap_TiO2.csv"))
nio = pd.read_csv(os.path.join(base_path, "output_analysis", "HF_analysis", "NiO", "logs", "AEXX_Band_Gap_NiO.csv"))

#tio2 = pd.read_csv("/Users/artyombetekhtin/PycharmProjects/nio_vasp/src/output_analysis/HF_analysis/TiO2/Anatase/logs/AEXX_Band_Gap_TiO2.csv")
#nio = pd.read_csv("/Users/artyombetekhtin/PycharmProjects/nio_vasp/src/output_analysis/HF_analysis/NiO/logs/AEXX_Band_Gap_NiO.csv")

# Вывод названий колонок
print("TiO2 columns:", tio2.columns)
print("NiO columns:", nio.columns)

# Попробуем использовать правильные имена (замени на нужные, если будут отличия)
x_col = tio2.columns[0]
y_col_tio2 = tio2.columns[1]
y_col_nio = nio.columns[1]

# Построение графика
plt.figure(figsize=(9 / 2.54, 3.5 / 2.54))  # Размер в дюймах
plt.plot(tio2[x_col], tio2[y_col_tio2], label='TiO$_2$', color='blue', linewidth=2)
plt.plot(nio[x_col], nio[y_col_nio], label='NiO', color='red', linewidth=2)

# Экспериментальные значения
plt.axhline(y=3.20, color='blue', linestyle='--', linewidth=1)
plt.axhline(y=4.30, color='red', linestyle='--', linewidth=1)

# Подписи
#plt.text(60, 3.3, 'TiO$_2$: Linear', color='blue', fontsize=8)
plt.text(20, 4.5, 'NiO: Kink at ~15%', color='red', fontsize=8)

# Оформление
plt.xlabel('HF Exchange Fraction (%)', fontsize=8)
plt.ylabel('Band Gap (eV)', fontsize=8)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
plt.legend(fontsize=8, loc='lower right')
plt.grid(True, linestyle='--', alpha=0.4)
plt.tight_layout()

# Сохранение
#plt.savefig("TOC_Graphic.png", dpi=300)
plt.show()
