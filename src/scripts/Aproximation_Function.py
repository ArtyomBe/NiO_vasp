import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy.optimize import curve_fit
from numpy.polynomial import Polynomial
from utils.utils import get_project_path

# Determining the file path
filename = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "logs", "AEXX_Band_Gap.csv")
output_dir = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "graphs", "Approximations_Graph")
summary_file = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "logs", "Approximations_Info.txt")
os.makedirs(output_dir, exist_ok=True)

# Uploading data from a CSV file
data = pd.read_csv(filename)
x = data["AEXX (%)"].astype(float)
y = data["Band Gap (eV)"].astype(float)


# Defining functions
def linear(x, a, b):
    return a * x + b


def quadratic(x, a, b, c):
    return a * x ** 2 + b * x + c


def logarithmic(x, a, b):
    return a * np.log(x + 1) + b


def exponential(x, a, b, c):
    return a * np.exp(b * x) + c


# Function for fitting and calculating metrics
def fit_and_evaluate(func, x, y):
    popt, _ = curve_fit(func, x, y, maxfev=5000)
    y_pred = func(x, *popt)
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mae = mean_absolute_error(y, y_pred)
    return popt, r2, rmse, mae, y_pred


def polynomial_fit(x, y, degree):
    p = Polynomial.fit(x, y, deg=degree)
    y_pred = p(x)
    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    mae = mean_absolute_error(y, y_pred)
    return p.convert().coef, r2, rmse, mae, y_pred


# Models for approximation
models = {
    "Linear": linear,
    "Quadratic": quadratic,
    "Logarithmic": logarithmic,
    "Exponential": exponential,
}

# Saving graphs and results
results = []
for name, func in models.items():
    params, r2, rmse, mae, y_pred = fit_and_evaluate(func, x, y)
    plt.figure(figsize=(7, 5))
    plt.scatter(x, y, label="Initial data", color="black", s=10)
    plt.plot(x, y_pred, label=f"{name} (R²={r2:.4f})", color="red")
    if name == "Linear":
        equation = f"y = {params[0]:.4f}x + {params[1]:.4f}"
    elif name == "Quadratic":
        equation = f"y = {params[0]:.6f}x² + {params[1]:.4f}x + {params[2]:.4f}"
    elif name == "Logarithmic":
        equation = f"y = {params[0]:.4f}ln(x+1) + {params[1]:.4f}"
    elif name == "Exponential":
        equation = f"y = {params[0]:.4e}exp({params[1]:.4f}x) + {params[2]:.4e}"

    equation_text = f"Function: {equation}\nR²: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}"
    plt.text(0.05, 0.95, equation_text, transform=plt.gca().transAxes, fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle="round", alpha=0.1))
    plt.title(f"{name} Approximation")
    plt.xlabel("AEXX (%)")
    plt.ylabel("Band Gap (eV)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{name}_approximation.png"), dpi=1200, bbox_inches="tight")
    plt.close()

    results.append(f"{name} Approximation:\nEquation: {equation}\nR^2 = {r2:.4f}\nRMSE = {rmse:.4f}\nMAE = {mae:.4f}\n")

# Polynomial approximations up to the 10th degree
for degree in range(1, 11):
    poly_params, r2, rmse, mae, y_pred = polynomial_fit(x, y, degree)
    plt.figure(figsize=(8, 6))  # Increased chart size
    plt.scatter(x, y, label="Initial data", color="black", s=10)
    plt.plot(x, y_pred, label=f"Polynomial Degree {degree} (R²={r2:.4f})", color="blue")

    # Form the equation for the polynomial
    equation = " + ".join([f"{coef:.4e}x^{i}" for i, coef in enumerate(poly_params)][::-1])
    equation_text = f"Function: {equation}\nR²: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}"
    plt.text(0.05, 0.95, equation_text, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle="round", alpha=0.1))

    plt.title(f"Polynomial Degree {degree} Approximation")
    plt.xlabel("AEXX (%)")
    plt.ylabel("Band Gap (eV)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"Polynomial_Degree_{degree}_approximation.png"), dpi=1200,
                bbox_inches="tight")
    plt.close()

    results.append(
        f"Polynomial Degree {degree} Approximation:\nEquation: {equation}\nR^2 = {r2:.4f}\nRMSE = {rmse:.4f}\nMAE = {mae:.4f}\n")

# Writing the results to a file
with open(summary_file, "w") as f:
    f.write("\n".join(results))

print(f"Results saved to {summary_file}")
print(f"Graphs saved to {output_dir}")
