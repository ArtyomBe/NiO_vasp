import matplotlib.pyplot as plt

"""
This code builds three graphs to analyze the effect of the number of K-POINTS on various system parameters.
"""

# Data
x_points = [2, 3, 4]
band_gap_values = [4.89279, 5.29979, 4.8209]
energy_values = [-68.99529934, -68.9690341, -69.0106054]
time_seconds = [2102.141, 8551.097, 61051.312]

def plot_graph(x, y, xlabel, ylabel, title, marker, color, filename=None):
    """
    Plots a graph with the given data and styling options.

    Args:
        x (list): X-axis data.
        y (list): Y-axis data.
        xlabel (str): Label for the X-axis.
        ylabel (str): Label for the Y-axis.
        title (str): Title of the graph.
        marker (str): Marker style for the plot.
        color (str): Color for the plot line.
        filename (str, optional): If provided, saves the graph to the given filename.
    """
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, marker=marker, linestyle='-', color=color, label=ylabel)
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.title(title, fontsize=16)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    if filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
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

# Plot: Seconds vs K-POINTS
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
