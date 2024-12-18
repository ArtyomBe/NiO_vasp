import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from concurrent.futures import ProcessPoolExecutor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from scipy.optimize import curve_fit
from numpy.polynomial import Polynomial
from utils.utils import get_project_path

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Defining functions
def linear(x, a, b):
    return a * x + b

def quadratic(x, a, b, c):
    return a * x ** 2 + b * x + c

def logarithmic(x, a, b):
    return a * np.log(x + 1) + b

def exponential(x, a, b, c):
    return a * np.exp(b * x) + c

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

def create_and_save_plot(x, y, y_pred, title, equation_text, filename):
    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, label="Initial data", color="black", s=10)
    plt.plot(x, y_pred, label=title, color="blue")
    plt.text(0.05, 0.95, equation_text, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle="round", alpha=0.1))
    plt.title(title)
    plt.xlabel("AEXX (%)")
    plt.ylabel("Band Gap (eV)")
    plt.legend()
    plt.tight_layout()
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2)
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()

def process_model(args):
    name, func, x, y, output_dir = args
    try:
        params, r2, rmse, mae, y_pred = fit_and_evaluate(func, x, y)
        if name == "Linear":
            equation = f"y = {params[0]:.4f}x + {params[1]:.4f}"
        elif name == "Quadratic":
            equation = f"y = {params[0]:.6f}x² + {params[1]:.4f}x + {params[2]:.4f}"
        elif name == "Logarithmic":
            equation = f"y = {params[0]:.4f}ln(x+1) + {params[1]:.4f}"
        elif name == "Exponential":
            equation = f"y = {params[0]:.4e}exp({params[1]:.4f}x) + {params[2]:.4e}"

        equation_text = f"Function: {equation}\\nR²: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}"
        filename = os.path.join(output_dir, f"{name}_approximation.png")
        create_and_save_plot(x, y, y_pred, f"{name} Approximation", equation_text, filename)

        return f"{name} Approximation:\\nEquation: {equation}\\nR^2 = {r2:.4f}\\nRMSE = {rmse:.4f}\\nMAE = {mae:.4f}\\n"
    except Exception as e:
        logging.error("Error processing model %s: %s", name, e)
        return None

def process_polynomial(args):
    degree, x, y, output_dir = args
    try:
        poly_params, r2, rmse, mae, y_pred = polynomial_fit(x, y, degree)
        equation = " + ".join([f"{coef:.4e}x^{i}" for i, coef in enumerate(poly_params)][::-1])
        equation_text = f"Function: {equation}\\nR²: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}"
        filename = os.path.join(output_dir, f"Polynomial_Degree_{degree}_approximation.png")
        create_and_save_plot(x, y, y_pred, f"Polynomial Degree {degree} Approximation", equation_text, filename)

        return f"Polynomial Degree {degree} Approximation:\\nEquation: {equation}\\nR^2 = {r2:.4f}\\nRMSE = {rmse:.4f}\\nMAE = {mae:.4f}\\n"
    except Exception as e:
        logging.error("Error processing polynomial degree %d: %s", degree, e)
        return None

if __name__ == '__main__':
    # Determining the file path
    filename = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "logs", "AEXX_Band_Gap.csv")
    output_dir = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "graphs", "Approximations_Graph")
    summary_file = os.path.join(get_project_path(), "output_analysis", "HF_analysis", "logs", "Approximations_Info.txt")

    # Create directory and clear it if it already exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Uploading data from a CSV file
    data = pd.read_csv(filename)
    if data.isnull().values.any():
        raise ValueError("Input data contains missing values.")

    x = data["AEXX (%)"].astype(float)
    y = data["Band Gap (eV)"].astype(float)

    # Models for approximation
    models = {
        "Linear": linear,
        "Quadratic": quadratic,
        "Logarithmic": logarithmic,
        "Exponential": exponential,
    }

    # Parallel processing
    results = []
    with ProcessPoolExecutor() as executor:
        model_results = executor.map(process_model, [(name, func, x, y, output_dir) for name, func in models.items()])
        results.extend([r for r in model_results if r])

        poly_results = executor.map(process_polynomial, [(degree, x, y, output_dir) for degree in range(1, 11)])
        results.extend([r for r in poly_results if r])

    # Writing the results to a file
    try:
        with open(summary_file, "w") as f:
            f.write("\\n".join(results))
        logging.info("Results saved to %s", summary_file)
        logging.info("Graphs saved to %s", output_dir)
    except Exception as e:
        logging.error("Error saving results: %s", e)
