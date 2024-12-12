import matplotlib.pyplot as plt

"""
This code builds three graphs to analyze the effect of the number of K-POINTS on various system parameters:

1. "Band Gap Variation with K-POINTS": shows the dependence of the energy gap (Band Gap) depends on the number of K-POINTS. 
   The graph helps to understand how the Band Gap changes when the Brillouin point grid varies.

2. "Energy Variation with K-POINTS": demonstrates the change in the energy of the system depending on the number of K-POINTS.
   This graph is useful for evaluating the energy stability of calculations with increasing accuracy.

3. "Time Consumption with K-POINTS": Displays the time spent on calculations (in seconds) when the number of K-POINTS changes.
   The graph gives an idea of the increase in computational costs with increasing grid density.

All graphs have clear axis signatures, legends and a grid for easy analysis.
"""

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
