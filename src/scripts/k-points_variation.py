import matplotlib.pyplot as plt
import os
from utils.utils import get_project_path

# Data
x_points = [2, 3, 4]
band_gap_values = [4.89279, 5.29979, 4.8209]
energy_values = [-68.99529934, -68.9690341, -69.0106054]
time_seconds = [2102.141, 8551.097, 61051.312]

# Output directory
output_dir = os.path.join(get_project_path(), "output_analysis", "KPOINTS_study", "graphs")
os.makedirs(output_dir, exist_ok=True)

def plot_graph(x, y, xlabel, ylabel, title, marker, color, filename=None):
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, marker=marker, linestyle='-', color=color, label=ylabel)
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.title(title, fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    if filename:
        plt.savefig(os.path.join(output_dir, filename), dpi=300, bbox_inches='tight')
    plt.show()


# Plot: Band Gap vs K-POINTS
plot_graph(
    x_points,
    band_gap_values,
    xlabel='K-POINTS',
    ylabel='Band Gap',
    title='Band Gap Variation with K-POINTS',
    marker='o',
    color='blue',
    filename='Band_Gap_vs_KPOINTS.png'
)

# Plot: Energy vs K-POINTS
plot_graph(
    x_points,
    energy_values,
    xlabel='K-POINTS',
    ylabel='Energy',
    title='Energy Variation with K-POINTS',
    marker='s',
    color='red',
    filename='Energy_vs_KPOINTS.png'
)

# Plot: Time vs K-POINTS
plot_graph(
    x_points,
    time_seconds,
    xlabel='K-POINTS',
    ylabel='Time (s)',
    title='Time Consumption with K-POINTS',
    marker='^',
    color='green',
    filename='Time_vs_KPOINTS.png'
)
