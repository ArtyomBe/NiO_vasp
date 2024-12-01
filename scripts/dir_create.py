import numpy as np
import matplotlib.pyplot as plt

# Жёсткое уравнение
def stiff_f(x, y):
    """Правая часть уравнения y'(x) = -1000y + 3000 - 2000e^(-x)."""
    return -1000 * y + 3000 - 2000 * np.exp(-x)

# Аналитическое решение
def stiff_analytical_solution(x):
    """Аналитическое решение y(x) = 3 - 0.998e^(-1000x) - 2.002e^(-x)."""
    return 3 - 0.998 * np.exp(-1000 * x) - 2.002 * np.exp(-x)

# Метод Эйлера
def euler_method(f, x0, y0, x_end, h):
    x = np.arange(x0, x_end + h, h)
    y = np.zeros(len(x))
    y[0] = y0
    for i in range(1, len(x)):
        y[i] = y[i - 1] + h * f(x[i - 1], y[i - 1])
    return x, y

# Метод Рунге-Кутты 4-го порядка
def runge_kutta_method(f, x0, y0, x_end, h):
    x = np.arange(x0, x_end + h, h)
    y = np.zeros(len(x))
    y[0] = y0
    for i in range(1, len(x)):
        k1 = h * f(x[i - 1], y[i - 1])
        k2 = h * f(x[i - 1] + h / 2, y[i - 1] + k1 / 2)
        k3 = h * f(x[i - 1] + h / 2, y[i - 1] + k2 / 2)
        k4 = h * f(x[i - 1] + h, y[i - 1] + k3)
        y[i] = y[i - 1] + (k1 + 2 * k2 + 2 * k3 + k4) / 6
    return x, y

# Метод Адамса
def adams_method(f, x0, y0, x_end, h):
    x = np.arange(x0, x_end + h, h)
    y = np.zeros(len(x))
    # Начальные значения методом Рунге-Кутты 4-го порядка
    y[0] = y0
    for i in range(3):
        k1 = h * f(x[i], y[i])
        k2 = h * f(x[i] + h / 2, y[i] + k1 / 2)
        k3 = h * f(x[i] + h / 2, y[i] + k2 / 2)
        k4 = h * f(x[i] + h, y[i] + k3)
        y[i + 1] = y[i] + (k1 + 2 * k2 + 2 * k3 + k4) / 6
    # Метод Адамса
    for i in range(3, len(x) - 1):
        y_pred = y[i] + h / 24 * (55 * f(x[i], y[i]) - 59 * f(x[i - 1], y[i - 1]) +
                                  37 * f(x[i - 2], y[i - 2]) - 9 * f(x[i - 3], y[i - 3]))
        y[i + 1] = y[i] + h / 24 * (9 * f(x[i + 1], y_pred) + 19 * f(x[i], y[i]) -
                                    5 * f(x[i - 1], y[i - 1]) + f(x[i - 2], y[i - 2]))
    return x, y

# Параметры задачи
x0 = 0
y0 = 0
x_end = 0.005  # Для жёсткости выбираем очень маленький интервал
h_euler = 0.0001  # Шаг для метода Эйлера
h_rk = 0.001  # Шаг для метода Рунге-Кутты
h_adams = 0.0001  # Шаг для метода Адамса

# Решение с разными методами
x_euler, y_euler = euler_method(stiff_f, x0, y0, x_end, h_euler)
x_rk, y_rk = runge_kutta_method(stiff_f, x0, y0, x_end, h_rk)
x_adams, y_adams = adams_method(stiff_f, x0, y0, x_end, h_adams)
x_exact = np.linspace(x0, x_end, 1000)
y_exact = stiff_analytical_solution(x_exact)

# Построение графиков
plt.figure(figsize=(12, 6))
plt.plot(x_exact, y_exact, label="Аналитическое решение", color="black", linewidth=2)
plt.plot(x_euler, y_euler, label="Метод Эйлера", linestyle="--", color="red")
plt.plot(x_rk, y_rk, label="Метод Рунге-Кутты 4-го порядка (h=0.001)", linestyle="--", color="blue")
plt.plot(x_adams, y_adams, label="Метод Адамса", linestyle="-.", color="green")
plt.title("Сравнение методов решения жесткого ОДУ с разными шагами")
plt.xlabel("x")
plt.ylabel("y")
plt.legend()
plt.grid()
plt.show()