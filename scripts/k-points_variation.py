import matplotlib.pyplot as plt

# Data
x_points = [2, 3, 4]
band_gap_values = [4.89279, 5.29979, 4.8209]
energy_values = [-68.99529934, -68.9690341, -69.0106054]
time_seconds = [2102.141, 8551.097, 61051.312]

# Plot: Band Gap vs K-POINTS
plt.figure(figsize=(8, 6))
plt.plot(x_points, band_gap_values, marker='o', linestyle='-', label='Band Gap')
plt.xlabel('K-POINTS', fontsize=14)
plt.ylabel('Band Gap', fontsize=14)
plt.title('Band Gap Variation with K-POINTS', fontsize=16)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=12)
plt.show()

# Plot: Energy vs K-POINTS
plt.figure(figsize=(8, 6))
plt.plot(x_points, energy_values, marker='s', linestyle='-', color='red', label='Energy')
plt.xlabel('K-POINTS', fontsize=14)
plt.ylabel('Energy', fontsize=14)
plt.title('Energy Variation with K-POINTS', fontsize=16)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=12)
plt.show()

# Plot: Seconds vs K-POINTS
plt.figure(figsize=(8, 6))
plt.plot(x_points, time_seconds, marker='^', linestyle='-', color='green', label='Seconds')
plt.xlabel('K-POINTS', fontsize=14)
plt.ylabel('Seconds', fontsize=14)
plt.title('Time Consumption with K-POINTS', fontsize=16)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(fontsize=12)
plt.show()
