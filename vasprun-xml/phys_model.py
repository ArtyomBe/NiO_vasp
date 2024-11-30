import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# Задаем параметры
A = B = C = 1/2

# Функция для вычисления производной
def dPhi_dtheta(theta, T, tau):
    return -(B - A / tau) * np.sin(theta) + 2 * (C - T) * np.sin(4 * theta)

# Функция для нахождения равновесного значения угла
def equilibrium_theta(T, tau):
    # Начальное приближение для метода fsolve
    theta_initial = np.pi / 4
    theta_solution, = fsolve(dPhi_dtheta, theta_initial, args=(T, tau))
    return theta_solution

# Сетки значений T и tau
T_values = np.linspace(0.01, 1, 100)
tau_values = np.linspace(0.01, 2, 100)

# Матрица для хранения значений угла theta
theta_matrix = np.zeros((len(T_values), len(tau_values)))

# Вычисляем равновесные значения theta для каждой пары (T, tau)
for i, T in enumerate(T_values):
    for j, tau in enumerate(tau_values):
        theta_matrix[i, j] = equilibrium_theta(T, tau)

# Построение фазовой диаграммы
T_grid, tau_grid = np.meshgrid(T_values, tau_values)
plt.contourf(T_grid, tau_grid, theta_matrix.T, levels=50, cmap='viridis')
plt.colorbar(label='Равновесный угол θ')
plt.xlabel('Температура T')
plt.ylabel('Механическое напряжение τ')
plt.title('Фазовая диаграмма магнитной наночастицы')
plt.show()