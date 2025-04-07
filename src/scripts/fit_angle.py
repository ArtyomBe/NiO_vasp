import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Загрузка данных
file_path = '/Users/artyombetekhtin/PycharmProjects/nio_vasp/src/output_analysis/HF_analysis/NiO/logs/AEXX_Band_Gap.csv'
data = pd.read_csv(file_path)

# Извлечение данных и удаление последней точки, если это 100%
x = data.iloc[:, 0].values
y = data.iloc[:, 1].values
if x[-1] == 100:
    x = x[:-1]
    y = y[:-1]

# Точка излома на 15%
split_index = np.where(x >= 15)[0][0]
x1, y1 = x[:split_index], y[:split_index]
x2, y2 = x[split_index:], y[split_index:]

# Аппроксимация линейными функциями
def linear(x, a, b):
    return a * x + b

params1, _ = curve_fit(linear, x1, y1)
params2, _ = curve_fit(linear, x2, y2)

slope1 = params1[0]
slope2 = params2[0]
angle_rad = np.arctan(abs((slope2 - slope1) / (1 + slope1 * slope2)))
angle_deg = np.degrees(angle_rad)

# Точка перегиба
kink_x = x[split_index]
kink_y = linear(kink_x, *params1)

# Прямые аппроксимации
x_fit1 = np.linspace(0, 100, 100)
y_fit1 = linear(x_fit1, *params1)
x_fit2 = np.linspace(0, 100, 100)
y_fit2 = linear(x_fit2, *params2)

# Область заливки справа от 15%
x_fill = np.linspace(15, 100, 500)
y1_fill = linear(x_fill, *params1)
y2_fill = linear(x_fill, *params2)

# График
plt.figure(figsize=(10, 6))
plt.plot(x, y, 'o', label='Data', color='orange')
plt.plot(x_fit1, y_fit1, label='Fit 1 (0–22%)', color='blue', linewidth=2)
plt.plot(x_fit2, y_fit2, label='Fit 2 (9–50%)', color='green', linewidth=2)
plt.plot(kink_x, kink_y, 'ro', label='Kink Point (15%)')
plt.axvline(x=kink_x, linestyle='--', color='red')

# Корректная заливка между двумя кривыми
plt.fill_between(x_fill, y1_fill, y2_fill, color='gray', alpha=0.3, label='Gap between fits')

plt.xlabel('HF Exchange (%)')
plt.ylabel('Band Gap (eV)')
#plt.title(f'Piecewise Linear Fit — Angle ≈ {angle_deg:.2f}° at Kink')
#plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
print(angle_deg)