import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import fsolve

# Определение параметров
T_values = np.linspace(0, 1, 200)  # Температура от 0 до 1
tau_values = np.linspace(0.1, 2, 200)  # Напряжение от 0.1 до 2
T_grid, tau_grid = np.meshgrid(T_values, tau_values)


# Функция для вычисления параметра γ
def calculate_gamma(T, tau):
    alpha = 0.5 * (1 - 1 / tau)  # Вычисляем α
    beta = 0.5 - T  # Вычисляем β
    if beta != 0:
        return alpha / (8 * beta)
    else:
        return np.inf  # Если β = 0, γ → ∞


# Функция для решения кубического уравнения
def cubic_eq(x, gamma):
    return 2 * x ** 3 - x - gamma


# Определение фаз
phase = np.zeros_like(T_grid)

for i in range(T_grid.shape[0]):
    for j in range(T_grid.shape[1]):
        T = T_grid[i, j]
        tau = tau_grid[i, j]
        gamma = calculate_gamma(T, tau)

        # Решение уравнения
        guesses = [-1, 0, 1]  # Начальные приближения
        roots = []
        for guess in guesses:
            root, info, ier, msg = fsolve(cubic_eq, guess, args=(gamma,), full_output=True)
            if ier == 1 and np.isreal(root):
                x = np.real(root[0])
                if -1 <= x <= 1:  # Только физически допустимые корни
                    roots.append(x)
        roots = np.unique(np.round(roots, 5))  # Убираем дубли
        num_roots = len(roots)

        # Классификация фаз
        if num_roots == 1:
            phase[i, j] = 1  # Фаза I
        elif num_roots == 3:
            phase[i, j] = 2  # Фаза II
        else:
            phase[i, j] = 0  # Переходная область

# Линии фазовых переходов
gamma_c = np.sqrt(2 / 27)
alpha_c = 8 * (0.5 - T_values) * gamma_c
tau_line_2nd = 1 / (1 - 2 * alpha_c)  # Линия второго рода

alpha_c = 8 * (0.5 - T_values) * (-gamma_c)
tau_line_1st = 1 / (1 - 2 * alpha_c)  # Линия первого рода

# Построение диаграммы
# Исправление цветовой шкалы для фаз
plt.figure(figsize=(10, 7))
cmap = plt.get_cmap('coolwarm', 3)
contour = plt.contourf(T_grid, tau_grid, phase, levels=[-0.5, 0.5, 1.5, 2.5], cmap=cmap, alpha=0.8)

# Линии фазовых переходов
plt.plot(T_values, tau_line_2nd, color='blue', linestyle='--', linewidth=2, label='Линия второго рода')
plt.plot(T_values, tau_line_1st, color='red', linestyle='-.', linewidth=2, label='Линия первого рода')

# Настройки графика
plt.xlim(0, 1)
plt.ylim(0, 2)
plt.xlabel('Температура $T$', fontsize=12)
plt.ylabel('Механическое напряжение $\\tau$', fontsize=12)
plt.title('Фазовая диаграмма магнитной наночастицы', fontsize=14)

# Исправление цветовой шкалы
cbar = plt.colorbar(contour, label='Фаза')
cbar.set_ticks([0, 1, 2])
cbar.set_ticklabels(['Переходная', 'Фаза I', 'Фаза II'])

plt.legend(loc='upper right')
plt.grid(alpha=0.3)
plt.show()
