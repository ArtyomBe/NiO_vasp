# Contributing to NiO_vasp Repository

Thank you for your interest in contributing to the **NiO_vasp** repository! This document provides guidelines to ensure
a smooth contribution process.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [How to Contribute](#how-to-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting Enhancements](#suggesting-enhancements)
    - [Submitting Changes](#submitting-changes)
3. [Code Style Guidelines](#code-style-guidelines)
4. [Pull Request Process](#pull-request-process)
5. [Support and Questions](#support-and-questions)

---

## Getting Started

Before contributing, ensure that you have:

- A basic understanding of VASP and Python.
- Access to tools such as Python 3.8+ and any dependencies specified in the `requirements.txt` file.
- Familiarity with Git for version control.

To set up the project locally:

1. Clone the repository:
    ```bash
    git clone https://github.com/ArtyomBe/NiO_vasp.git
    cd NiO_vasp
    ```
2. Install the required Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

---

## How to Contribute

### Reporting Bugs

If you encounter a bug, please open an issue with the following details:

- A clear description of the bug.
- Steps to reproduce the issue.
- Expected behavior versus actual behavior.
- Relevant logs, error messages, or screenshots.

### Suggesting Enhancements

If you have ideas for improving the repository:

- Open an issue with the label `enhancement`.
- Provide a detailed description of the proposed change and its benefits.

### Submitting Changes

If you'd like to fix a bug, add a feature, or enhance the documentation:

1. Fork the repository.
2. Create a new branch for your changes:
    ```bash
    git checkout -b feature/your-feature-name
    ```
3. Make your changes, following the code style guidelines below.
4. Commit your changes with a clear message:
    ```bash
    git commit -m "Add feature: description of your change"
    ```
5. Push the branch to your fork:
    ```bash
    git push origin feature/your-feature-name
    ```
6. Submit a pull request to the main repository.

---

## Code Style Guidelines

To maintain consistency:

- Follow [PEP 8](https://pep8.org/) for Python code.
- Use meaningful variable and function names.
- Include docstrings for all functions and classes.
- Add comments where necessary for clarity.
- Use relative imports where possible, especially for internal modules like `libs/vasprun_optimized.py`.

For example:

```python
def example_function(parameter):
    """
    Brief description of the function.

    Args:
        parameter (type): Description of the parameter.

    Returns:
        type: Description of the return value.
    """
    pass
