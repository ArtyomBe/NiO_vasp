import matplotlib.pyplot as plt
import numpy as np

# Константы и параметры
k_B = 1.380649e-23
N = 200  # Для демонстрации; для N=10^4 очень долгий расчет
T_init = 300.0
V_init = 1e-22
m = 1e-28
a = -1e-20  # Дж·нм^3
b = 1e-21  # Дж·нм^5
nm_to_m = 1e-9
a_SI = a * (nm_to_m ** 3)
b_SI = b * (nm_to_m ** 5)

dt = 1e-14
steps_equil = 2000
steps_relax = 4000
cutoff = 2e-9


def initialize_positions(N, L):
    return np.random.rand(N, 3) * L


def initialize_velocities(N, T, m):
    sigma = np.sqrt(k_B * T / m)
    v = np.random.normal(0, sigma, (N, 3))
    v -= v.mean(axis=0)
    return v


def apply_boundaries(r, v, L):
    # Отражение от стенок
    for i in range(3):
        mask_low = r[:, i] < 0
        mask_high = r[:, i] > L
        v[mask_low, i] = -v[mask_low, i]
        r[mask_low, i] = -r[mask_low, i]
        v[mask_high, i] = -v[mask_high, i]
        r[mask_high, i] = 2 * L - r[mask_high, i]
    return r, v


def compute_forces(r):
    F = np.zeros_like(r)
    Np = r.shape[0]
    for i in range(Np):
        for j in range(i + 1, Np):
            rij = r[j] - r[i]
            dist = np.linalg.norm(rij)
            if dist < cutoff:
                dist2 = dist * dist
                dist4 = dist2 * dist2
                dist6 = dist4 * dist2
                Fmag = (3 * a_SI / dist4 + 5 * b_SI / dist6)
                fij = Fmag * (rij / dist)
                F[i] += fij
                F[j] -= fij
    return F


def compute_temperature(v, m):
    KE = 0.5 * m * np.mean(np.sum(v * v, axis=1))
    T = (2.0 / 3.0) * KE / k_B
    return T


def compute_pressure(r, v, F, V):
    # вириальный метод
    T = compute_temperature(v, m)
    P_ideal = N * k_B * T / V
    pair_sum = 0.0
    Np = r.shape[0]
    for i in range(Np):
        for j in range(i + 1, Np):
            rij = r[j] - r[i]
            dist = np.linalg.norm(rij)
            if dist < cutoff:
                dist2 = dist * dist
                dist4 = dist2 * dist2
                dist6 = dist4 * dist2
                Fmag = (3 * a_SI / dist4 + 5 * b_SI / dist6)
                fij = Fmag * (rij / dist)
                pair_sum += np.dot(rij, fij)
    P = P_ideal + (1.0 / (3.0 * V)) * 0.5 * pair_sum
    return P


def run_simulation_for_volume(V_final):
    # Копируем логику из исходного кода:
    L_init = V_init ** (1 / 3)
    r = initialize_positions(N, L_init)
    v = initialize_velocities(N, T_init, m)

    # Стабилизация при исходном объеме
    for step in range(steps_equil):
        F = compute_forces(r)
        v += 0.5 * F / m * dt
        r += v * dt
        r, v = apply_boundaries(r, v, L_init)
        F = compute_forces(r)
        v += 0.5 * F / m * dt

    # Увеличение объема до V_final
    L_final = V_final ** (1 / 3)
    for step in range(steps_relax):
        F = compute_forces(r)
        v += 0.5 * F / m * dt
        r += v * dt
        r, v = apply_boundaries(r, v, L_final)
        F = compute_forces(r)
        v += 0.5 * F / m * dt

    T_final = compute_temperature(v, m)
    P_final = compute_pressure(r, v, F, V_final)
    return T_final, P_final


# Сгенерируем ряд объемов: от V_init до 3*V_init, например, 5 точек
V_factors = [1.0, 1.5, 2.0, 2.5, 3.0]
V_list = [factor * V_init for factor in V_factors]

T_list = []
P_list = []

for Vf in V_list:
    T_val, P_val = run_simulation_for_volume(Vf)
    T_list.append(T_val)
    P_list.append(P_val)

# Построим графики из файла с результатами
volume, temperature, pressure = np.loadtxt("simulation_results.txt", skiprows=1, unpack=True)

fig, ax1 = plt.subplots()
ax1.plot(volume, temperature, 'o-', color='blue', label='T(V)')
ax1.set_xlabel('Объем (м^3)')
ax1.set_ylabel('Температура (K)', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')

ax2 = ax1.twinx()
ax2.plot(volume, pressure, 'o-r', label='P(V)')
ax2.set_ylabel('Давление (Па)', color='red')
ax2.tick_params(axis='y', labelcolor='red')

plt.title('Зависимость T и P от V при последовательном увеличении объема')
plt.grid(True)
plt.tight_layout()

# Сохраняем графики
plt.savefig('T_P_vs_V.png', dpi=600, format='png')  # Можно выбрать другой формат, например 'pdf' или 'svg'
plt.close(fig)  # Закрываем фигуру, чтобы освободить память
