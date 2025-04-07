import random
import numpy as np
import time
import tracemalloc
import timeit


class TuringMachine:
    def __init__(self, tape, keys, noise):
        self.tape = tape
        self.keys = keys
        self.noise = noise
        self.head = 0  # Позиция головки на ленте (не используется в текущей реализации).
        self.result = []  # Результат шифрования.
        self.operations_count = 0  # Счетчик операций.

    def read_matrix(self):
        """Считывание исходной матрицы сообщения."""
        return self.tape

    def multiply_matrices(self, A, B):
        """Перемножение двух матриц."""
        self.operations_count += len(A) * len(B[0]) * len(B)
        return np.dot(A, B).tolist()

    def add_matrices(self, A, B):
        """Сложение двух матриц."""
        self.operations_count += len(A) * len(A[0])
        return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

    def encrypt(self):
        """Процесс шифрования сообщения."""
        self.operations_count = 0
        message_matrix = self.read_matrix()
        result_matrix = message_matrix
        for i, key in enumerate(self.keys):
            result_matrix = self.multiply_matrices(result_matrix, key)
            result_matrix = self.add_matrices(result_matrix, self.noise[i])
        self.result = result_matrix
        return result_matrix

    def decrypt(self, inverse_keys):
        """Процесс расшифровки сообщения с использованием обратных ключей."""
        self.operations_count = 0
        result_matrix = self.result
        for i in range(len(inverse_keys) - 1, -1, -1):
            result_matrix = self.add_matrices(result_matrix, [[-x for x in row] for row in self.noise[i]])
            result_matrix = self.multiply_matrices(result_matrix, inverse_keys[i])
        return result_matrix


def text_to_matrix(text, cols):
    unicode_values = [ord(char) for char in text]
    rows = (len(unicode_values) + cols - 1) // cols
    matrix = [[0] * cols for _ in range(rows)]
    for i, val in enumerate(unicode_values):
        matrix[i // cols][i % cols] = val
    return matrix


def matrix_to_text(matrix, original_length):
    chars = []
    count = 0
    for row in matrix:
        for value in row:
            value = round(value)
            if count < original_length:
                chars.append(chr(value))
                count += 1
    return ''.join(chars)


def is_invertible(matrix):
    np_matrix = np.array(matrix)
    return np.linalg.det(np_matrix) != 0


def generate_invertible_matrix(size, min_val=1, max_val=100):
    while True:
        matrix = generate_random_matrix(size, size, min_val, max_val)
        if is_invertible(matrix):
            return matrix


def generate_random_matrix(rows, cols, min_val=1, max_val=100):
    return [[random.randint(min_val, max_val) for _ in range(cols)] for _ in range(rows)]


def invert_matrix(matrix):
    np_matrix = np.array(matrix)
    inverse = np.linalg.inv(np_matrix)
    return inverse.tolist()


if __name__ == "__main__":
    try:
        user_text = input("Введите текст для шифрования: ")
        if not user_text.strip():
            raise ValueError("Ввод текста не может быть пустым.")

        original_length = len(user_text)
        message = text_to_matrix(user_text, cols=2)

        # Генерация ключевых и шумовых матриц.
        key1 = generate_invertible_matrix(2)
        key2 = generate_invertible_matrix(2)
        noise1 = generate_random_matrix(len(message), 2, 1, 5)
        noise2 = generate_random_matrix(len(message), 2, 1, 5)
        inv_key1 = invert_matrix(key1)
        inv_key2 = invert_matrix(key2)

        tm = TuringMachine(message, [key1, key2], [noise1, noise2])

        # Замер времени шифрования
        start_time = time.time()
        tracemalloc.start()
        encrypted = tm.encrypt()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        encryption_time = time.time() - start_time

        print("\nЗашифрованное сообщение:", encrypted)
        print(f"Время шифрования: {encryption_time:.6f} секунд")
        print(f"Использование памяти: {current / 1024:.2f} KB; Пиковое использование: {peak / 1024:.2f} KB")
        print(f"Количество операций при шифровании: {tm.operations_count}")

        # Замер времени расшифровки
        start_time = time.time()
        tracemalloc.start()
        decrypted = tm.decrypt([inv_key1, inv_key2])
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        decryption_time = time.time() - start_time

        print("\nРасшифрованное сообщение:")
        print(matrix_to_text(decrypted, original_length))
        print(f"Время расшифровки: {decryption_time:.6f} секунд")
        print(f"Использование памяти: {current / 1024:.2f} KB; Пиковое использование: {peak / 1024:.2f} KB")
        print(f"Количество операций при расшифровке: {tm.operations_count}")

        # Производительность на множестве запусков
        encryption_performance = timeit.timeit("tm.encrypt()", globals=globals(), number=100)
        decryption_performance = timeit.timeit("tm.decrypt([inv_key1, inv_key2])", globals=globals(), number=100)
        print(f"\nСреднее время шифрования за 100 запусков: {encryption_performance / 100:.6f} секунд")
        print(f"Среднее время расшифровки за 100 запусков: {decryption_performance / 100:.6f} секунд")

    except Exception as e:
        print("Ошибка:", e)
