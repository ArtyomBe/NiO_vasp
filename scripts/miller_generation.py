import numpy as np

def miller_to_rotation(h, k, l):
    # Нормализуем вектор нормали (h, k, l)
    normal = np.array([h, k, l])
    normal_magnitude = np.linalg.norm(normal)
    n = normal / normal_magnitude

    # Находим второй вектор, ортогональный нормали
    # Выбираем вектор, который гарантированно не коллинеарен нормали
    if h != 0 or k != 0:
        u = np.array([-k, h, 0])  # Вектор, перпендикулярный (h, k, l) в плоскости x-y
    else:
        u = np.array([0, -l, k])  # Для случая, когда нормаль направлена по z

    # Нормализуем второй вектор
    u_magnitude = np.linalg.norm(u)
    u = u / u_magnitude

    # Третий вектор определяется векторным произведением (ортонормальность)
    v = np.cross(n, u)

    # Составляем матрицу вращения
    rotation_matrix = np.array([n, u, v])
    return rotation_matrix.T  # Транспонируем для получения матрицы вращения

# Пример использования
h, k, l = 1, 1, 1  # Введите индексы Миллера
rotation_matrix = miller_to_rotation(h, k, l)
rotation_matrix = rotation_matrix
print("Матрица вращения для поверхности {", h, k, l, "}:\n", rotation_matrix)
