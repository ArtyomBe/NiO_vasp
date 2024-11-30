#!/usr/bin/env  python
# encoding: utf-8
#from version import __version__
from lxml import etree
import numpy as np
from pprint import pprint
from optparse import OptionParser
import pandas as pd
from tabulate import tabulate
import warnings

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
plt.style.use("bmh")


def smear_data(data, sigma):
    """
    Apply Gaussian smearing to spectrum y value.

    Args:
        sigma: Std dev for Gaussian smear function
    """
    from scipy.ndimage import gaussian_filter1d

    # Оптимизация вычисления diff с использованием NumPy
    diff = np.diff(data[:, 0])
    avg_x_per_step = np.mean(diff)

    # Проверка на корректность значений
    if avg_x_per_step <= 0:
        raise ValueError("x-values in 'data' must be monotonically increasing.")

    # Применяем размытие
    data[:, 1] = gaussian_filter1d(data[:, 1], sigma / avg_x_per_step)
    return data


class units:
    am2kg = 1.6605402e-27
    ev2j = 1.60217733e-19
    plank = 6.626075e-34
    c = 2.99792458e+10
    pi = 3.1415926
    proton_mass = 1836
    ev2hartree = 27.211386245988
    a2bohr = 0.529
    ev2cm = 8065.6

class vasprun:
    """
    parse vasprun.xml and return all useful info to self.values

    Args:
        vasp_file: the path of vasprun.xml
        verbosity: output error msgs or not
    """

    def __init__(self, vasp_file='vasprun.xml', verbosity=0):
        """
        Initialize the vasprun parser.

        Args:
            vasp_file (str): Path to the vasprun.xml file (default: 'vasprun.xml').
            verbosity (int): Verbosity level (default: 0). If > 0, prints warnings.
        """
        self.error = False
        self.errormsg = ''
        self.values = {}

        try:
            # Парсим XML и извлекаем корень
            doc = etree.parse(vasp_file).getroot()

            # Основные этапы обработки
            self.parse_vaspxml(doc)
            self.get_band_gap()

            # Расчет энергии на атом
            positions = self.values.get('finalpos', {}).get('positions', [])
            energy = self.values.get('calculation', {}).get('energy', None)

            if positions and energy is not None:
                N_atom = len(positions)
                if N_atom > 0:
                    self.values['calculation']['energy_per_atom'] = energy / N_atom
                else:
                    raise ValueError("Number of atoms (N_atom) is zero.")
            else:
                raise KeyError("Missing required data: 'finalpos.positions' or 'calculation.energy'.")

        except etree.XMLSyntaxError:
            self.error = True
            self.errormsg = 'Corrupted file found: unable to parse vasprun.xml'
        except (KeyError, ValueError) as e:
            self.error = True
            self.errormsg = f"Data error: {e}"

        # Обработка ошибок на основе уровня verbosity
        if verbosity > 0 and self.error:
            print("----------Warning---------------")
            print(self.errormsg)
            print("--------------------------------")

    def parse_vaspxml(self, xml_object):
        """
        Parse the vasprun.xml structure and extract information.

        Args:
            xml_object: Root element of the XML document.
        """
        tag_parsers = {
            "incar": self.parse_i_tag_collection,
            "kpoints": self.parse_kpoints,
            "parameters": self.parse_parameters,
            "atominfo": self.parse_atominfo,
            "calculation": self.parse_calculation_wrapper,
            "structure": self.parse_structure
        }

        # Рекурсивный парсинг тегов
        for child in xml_object.iterchildren():
            tag = child.tag
            if tag in tag_parsers:
                # Используем маппинг для вызова функции
                result = tag_parsers[tag](child)
                if result is not None:
                    self.values[tag] = result
            else:
                # Для неизвестных тегов запускаем рекурсию
                self.values.setdefault(tag, {})
                self.values[tag] = self.parse_vaspxml(child)

        # Очищаем словарь после обработки
        self.dict_clean(self.values)

    def parse_atominfo(self, atominfo):
        """
        Extract information from the <atominfo> tag.
        """
        self.values["name_array"] = self.parse_name_array(atominfo)
        self.values["composition"] = self.parse_composition(atominfo)
        self.values["elements"] = self.get_element(self.values["composition"])
        self.values["formula"] = self.get_formula(self.values["composition"])
        self.values["pseudo_potential"], self.values["potcar_symbols"], \
            self.values["valence"], self.values["mass"] = self.get_potcar(atominfo)

    def parse_calculation_wrapper(self, calculation):
        """
        Wrapper for parsing <calculation> tag and handling SCF checks.
        """
        calculation_data, scf_count = self.parse_calculation(calculation)
        self.values["calculation"] = calculation_data

        # Проверка на сходимость SCF
        nelm = self.values.get('parameters', {}).get('electronic', {}).get('electronic convergence', {}).get('NELM',
                                                                                                             None)
        if nelm == scf_count:
            self.error = True
            self.errormsg = 'SCF is not converged'
        else:
            self.error = False

        # Проверка на спин-орбитальное взаимодействие
        spin_params = self.values.get('parameters', {}).get('electronic', {}).get('electronic spin', {})
        self.spin = spin_params.get('LSORBIT', False) or spin_params.get('ISPIN', 1) == 2

    def parse_structure(self, structure):
        """
        Handle <structure> tags, specifically 'finalpos'.
        """
        if structure.attrib.get("name") == "finalpos":
            return self.parse_finalpos(structure)
        return None

    @staticmethod
    def dict_clean(d: dict) -> dict:
        """
        Recursively removes keys with empty dictionaries or None values from a dictionary.

        Args:
            d (dict): The input dictionary to clean.

        Returns:
            dict: A new dictionary without empty or None values.
        """
        if not isinstance(d, dict):
            raise ValueError("Input must be a dictionary.")

        cleaned_dict = {}
        for key, value in d.items():
            if isinstance(value, dict):
                # Рекурсивно очищаем вложенные словари
                nested = vasprun.dict_clean(value)
                if nested:  # Добавляем только непустые словари
                    cleaned_dict[key] = nested
            elif value is not None:  # Удаляем None
                cleaned_dict[key] = value

        return cleaned_dict

    def parse_finalpos(self, finalpos):
        """
        Extract the final configuration (e.g., lattice, positions) from the <finalpos> tag.

        Args:
            finalpos: An XML element containing <varray> tags with configuration data.

        Returns:
            dict: A dictionary where keys are attribute names (e.g., 'positions', 'basis') and
                  values are parsed arrays of corresponding data.

        Raises:
            ValueError: If the <varray> tag does not have a 'name' attribute.
        """
        if finalpos is None:
            raise ValueError("Input 'finalpos' cannot be None.")

        result = {}
        for varray in finalpos.iter("varray"):
            name = varray.attrib.get("name")
            if not name:
                raise ValueError("<varray> tag is missing the 'name' attribute.")

            # Парсим содержимое <varray>
            parsed_data = self.parse_varray(varray)
            if parsed_data is not None:
                result[name] = parsed_data
            else:
                raise ValueError(f"Failed to parse <varray> with name: {name}")

        return result

    def parse_dynmat(self, dynmat):
        """
        Parse the <dynmat> tag to extract Hessian, eigenvalues, and eigenvectors.

        Args:
            dynmat: XML element containing <varray> and <v> tags.

        Returns:
            tuple: (hessian, eigenvalues, eigenvectors), where each is a list or array.

        Raises:
            ValueError: If required data is missing or cannot be parsed.
        """
        if dynmat is None:
            raise ValueError("Input 'dynmat' cannot be None.")

        # Инициализируем переменные
        hessian = None
        eigenvectors = None
        eigenvalues = []

        # Парсим теги <varray>
        for va in dynmat.findall("varray"):
            name = va.attrib.get("name")
            if name == "hessian":
                hessian = self.parse_varray(va)
            elif name == "eigenvectors":
                eigenvectors = self.parse_varray(va)

        # Проверяем, что необходимые данные найдены
        if hessian is None or eigenvectors is None:
            raise ValueError("Missing required data: 'hessian' or 'eigenvectors'.")

        # Фактор для преобразования значений
        factor = np.sqrt(units.ev2j / 1e-20 / units.am2kg) * units.plank / units.ev2j / (2 * units.pi)

        # Парсим теги <v> для eigenvalues
        try:
            for v in dynmat.findall("v"):
                eigenvalues.extend(
                    np.sqrt(np.abs(float(value))) * factor for value in v.text.split()
                )
        except ValueError as e:
            raise ValueError(f"Failed to parse eigenvalues in <v>: {e}")

        return hessian, eigenvalues, eigenvectors

    def parse_born_chg(self, charge):
        """
        Extract Born charges from the <charge> tag.

        Args:
            charge: XML element containing <set> tags with Born charge tensors.

        Returns:
            list: A list of Born charge tensors (as arrays or nested lists).

        Raises:
            ValueError: If the input element does not contain valid data.
        """
        if charge is None:
            raise ValueError("Input 'charge' cannot be None.")

        born_charges = []
        for set_element in charge.findall('set'):
            # Парсим содержимое каждого <set>
            parsed_charges = self.parse_varray(set_element)
            if parsed_charges is not None:
                born_charges.append(parsed_charges)
            else:
                raise ValueError("Failed to parse a <set> element in Born charges.")

        if not born_charges:
            raise ValueError("No valid Born charges found in the input element.")

        return born_charges

    def parse_i_tag_collection(self, itags_collection):
        """
        Parse a collection of <i> tags and convert their values based on their type.

        Args:
            itags_collection: XML element containing multiple <i> tags.

        Returns:
            dict: A dictionary where keys are attribute names from <i> tags
                  and values are the parsed data.

        Raises:
            ValueError: If an <i> tag is missing a 'name' attribute.
        """
        if itags_collection is None:
            raise ValueError("Input 'itags_collection' cannot be None.")

        parsed_data = {}
        for info in itags_collection.findall("i"):
            name = info.attrib.get("name")
            if not name:
                raise ValueError("<i> tag is missing the 'name' attribute.")

            type_ = info.attrib.get("type")  # Избегаем конфликтов с зарезервированным словом `type`
            content = info.text.strip() if info.text else None

            # Преобразуем значение в соответствующий тип
            parsed_value = self.assign_type(type_, content)
            if parsed_value is not None:
                parsed_data[name] = parsed_value
            else:
                raise ValueError(f"Failed to parse <i> tag with name: {name}")

        return parsed_data

    @staticmethod
    def parse_varray_pymatgen(elem):
        """
        Parse <varray> elements into a list of values or logical states.

        Args:
            elem: XML element <varray> containing <v> elements with numerical or logical data.

        Returns:
            list: A nested list (matrix) of parsed values.

        Raises:
            ValueError: If the input element contains invalid or unexpected data.
        """

        def _safe_float(value):
            """
            Safely convert a string to a float, handling special cases like overflow ('*******').
            """
            try:
                return float(value)
            except ValueError:
                value = value.strip()
                if value == '*' * len(value):
                    warnings.warn("Float overflow ('*******') encountered. Replacing with np.nan.")
                    return np.nan
                raise ValueError(f"Cannot convert value '{value}' to float.")

        if elem is None or not elem.tag == "varray":
            raise ValueError("Input element must be a valid <varray> XML element.")

        if elem.get("type") == 'logical':
            # Обрабатываем тип logical (например, T/F)
            return [[i.strip() in ('T', 'True', '1') for i in v.text.split()] for v in elem.findall("v")]

        # Обрабатываем числовые значения
        return [[_safe_float(i) for i in v.text.split()] for v in elem.findall("v")]

    def parse_v(self, v):
        """
        Parse a single <v> element into a list of floats.

        Args:
            v: XML element <v> containing space-separated numeric values.

        Returns:
            list: A list of floats extracted from the <v> element.

        Raises:
            ValueError: If the input element does not contain valid numeric data.
        """
        if v is None or v.text is None:
            raise ValueError("Input <v> element is empty or missing text.")

        try:
            return [float(n) for n in v.text.split()]
        except ValueError as e:
            raise ValueError(f"Failed to parse numeric data in <v>: {v.text}. Error: {e}")

    @staticmethod
    @staticmethod
    def parse_varray(varray):
        """
        Parse a <varray> XML element into a nested list of numerical values.

        Args:
            varray: XML element <varray> containing <v> tags with numeric data.

        Returns:
            list: A nested list (matrix) of integers or floats, depending on the "type" attribute.

        Raises:
            ValueError: If a <v> tag contains invalid or non-numeric data.
        """
        if varray is None or varray.tag != "varray":
            raise ValueError("Input must be a valid <varray> element.")

        varray_type = varray.get("type", "float")  # Default type is float

        # Определяем парсер для числовых типов
        if varray_type == "int":
            parser = int
        elif varray_type == "float":
            parser = float
        else:
            raise ValueError(f"Unsupported 'type' attribute in <varray>: {varray_type}")

        # Парсим содержимое <v>
        matrix = []
        for v in varray.findall("v"):
            if v.text is None or not v.text.strip():
                raise ValueError("Empty or missing text in <v> tag.")
            try:
                row = [parser(number) for number in v.text.split()]
                matrix.append(row)
            except ValueError as e:
                raise ValueError(f"Failed to parse row in <v>: {v.text}. Error: {e}")

        return matrix

    @staticmethod
    # Удалите декоратор @staticmethod, если он там есть
    def parse_varray(self, varray):
        """
        Parse a <varray> XML element into a nested list of numerical values.

        Args:
            varray: XML element <varray> containing <v> tags with numeric data.

        Returns:
            list: A nested list (matrix) of integers or floats, depending on the "type" attribute.
        """
        if varray is None or varray.tag != "varray":
            raise ValueError("Input must be a valid <varray> element.")

        varray_type = varray.get("type", "float")  # Default type is float

        # Определяем парсер для числовых типов
        if varray_type == "int":
            parser = int
        elif varray_type == "float":
            parser = float
        else:
            raise ValueError(f"Unsupported 'type' attribute in <varray>: {varray_type}")

        # Парсим содержимое <v>
        matrix = []
        for v in varray.findall("v"):
            if v.text is None or not v.text.strip():
                raise ValueError("Empty or missing text in <v> tag.")
            try:
                row = [parser(number) for number in v.text.split()]
                matrix.append(row)
            except ValueError as e:
                raise ValueError(f"Failed to parse row in <v>: {v.text}. Error: {e}")

        return matrix

    @staticmethod
    def assign_type(type_, content):
        """
        Convert a string to a specified type.

        Args:
            type_ (str): The target type ("logical", "int", "float", "string", or None).
            content (str): The string to convert.

        Returns:
            Union[bool, int, float, str, list]: Converted value based on the type.

        Raises:
            ValueError: If the conversion fails or the type is unsupported.
        """
        if not isinstance(content, str):
            raise ValueError("Content must be a string.")

        # Удаляем лишние пробелы
        content = content.strip()

        # Логический тип
        if type_ == "logical":
            if content in ('T', 'True', 'true', '1'):
                return True
            elif content in ('F', 'False', 'false', '0'):
                return False
            raise ValueError(f"Invalid logical value: '{content}'.")

        # Целочисленный тип
        if type_ == "int":
            try:
                if " " in content:
                    return [int(value) for value in content.split()]
                return int(content)
            except ValueError as e:
                raise ValueError(f"Failed to convert to int: '{content}'. Error: {e}")

        # Тип с плавающей точкой
        if type_ in ("float", None):  # None по умолчанию обрабатывается как float
            try:
                if " " in content:
                    return [float(value) for value in content.split()]
                return float(content)
            except ValueError as e:
                raise ValueError(f"Failed to convert to float: '{content}'. Error: {e}")

        # Строковой тип
        if type_ == "string":
            return content

        # Если тип неизвестен
        raise ValueError(f"Unsupported type: '{type_}'.")

    @staticmethod
    def parse_composition(atom_info):
        """
        Parse the atomic composition from the <atominfo> XML element.

        Args:
            atom_info: XML element <atominfo> containing atomic information.

        Returns:
            dict: A dictionary where keys are atomic symbols and values are their counts.

        Raises:
            ValueError: If the <atominfo> element or its required children are missing.
        """
        if atom_info is None:
            raise ValueError("Input 'atom_info' cannot be None.")

        # Ищем массив с именем "atoms"
        atoms_array = atom_info.find(".//array[@name='atoms']")
        if atoms_array is None:
            raise ValueError("The <atominfo> element does not contain an <array> with name='atoms'.")

        # Извлекаем состав
        composition = {}
        for rc in atoms_array.findall(".//rc"):
            c_element = rc.find("c")
            if c_element is None or c_element.text is None:
                raise ValueError(f"Invalid <rc>: missing <c> element or text.")
            atom_name = c_element.text.strip()
            composition[atom_name] = composition.get(atom_name, 0) + 1

        return composition

    @staticmethod
    def get_element(atom_names_dictionary):
        """
        Extract unique element names from an atomic composition dictionary.

        Args:
            atom_names_dictionary (dict): Dictionary with element symbols as keys
                                          and their counts as values.

        Returns:
            list: A list of unique element symbols.

        Raises:
            ValueError: If the input is not a dictionary or contains invalid keys.
        """
        if not isinstance(atom_names_dictionary, dict):
            raise ValueError("Input must be a dictionary with element symbols as keys.")

        # Убираем лишние пробелы в ключах и возвращаем список уникальных элементов
        return [atom_name.strip() for atom_name in atom_names_dictionary.keys()]

    @staticmethod
    def get_formula(atom_names_dictionary, skip_ones=True):
        """
        Generate a chemical formula from an atomic composition dictionary.

        Args:
            atom_names_dictionary (dict): Dictionary with element symbols as keys
                                          and their counts as values.
            skip_ones (bool): If True, omit the number "1" from the formula.

        Returns:
            str: A string representing the chemical formula.

        Raises:
            ValueError: If the input is not a valid dictionary or contains invalid data.
        """
        if not isinstance(atom_names_dictionary, dict):
            raise ValueError("Input must be a dictionary with element symbols as keys and counts as values.")

        # Проверяем корректность значений
        formula_parts = []
        for atom_name, count in atom_names_dictionary.items():
            if not isinstance(atom_name, str) or not atom_name.strip():
                raise ValueError(f"Invalid atom name: {atom_name}")
            if not isinstance(count, (int, float)) or count <= 0:
                raise ValueError(f"Invalid count for atom {atom_name}: {count}")

            # Убираем пробелы из имени и добавляем к формуле
            atom_name = atom_name.strip()
            count_part = f"{int(count)}" if count != 1 or not skip_ones else ""
            formula_parts.append(f"{atom_name}{count_part}")

        # Собираем формулу в одну строку
        return "".join(formula_parts)

    def get_potcar(self, atominfo):
        """
        Parse the POTCAR information from the <atominfo> element.

        Args:
            atominfo: XML element containing <array name="atomtypes">.

        Returns:
            tuple:
                - dict: Information about labels, potential types, and functionals.
                - list: Symbols of POTCAR files.
                - list: Valence for each atom type.
                - list: Mass for each atom type.

        Raises:
            ValueError: If the required data is missing or malformed.
        """
        if atominfo is None:
            raise ValueError("Input 'atominfo' cannot be None.")

        # Ищем массив с именем "atomtypes"
        atomtypes_array = atominfo.find(".//array[@name='atomtypes']")
        if atomtypes_array is None:
            raise ValueError("The <atominfo> element does not contain an <array name='atomtypes'>.")

        # Извлекаем элементы <c> и проверяем их количество
        columns = list(atomtypes_array.iter("c"))
        if len(columns) % 5 != 0:
            raise ValueError("Unexpected number of <c> elements in 'atomtypes' array.")

        # Инициализация результатов
        pseudo = {"labels": [], "pot_type": [], "functional": []}
        potcar_symbols = []
        valences = []
        masses = []

        # Извлечение данных
        for i in range(0, len(columns), 5):
            # Масса атома
            mass = float(columns[i + 2].text.strip())
            masses.append(mass)

            # Валентность
            valence = float(columns[i + 3].text.strip())
            valences.append(valence)

            # Информация о потенциале
            potcar_data = columns[i + 4].text.strip().split()
            if len(potcar_data) < 2:
                raise ValueError(f"Invalid POTCAR data: {columns[i + 4].text}")

            potential = potcar_data[0].split("_")
            pot_type = potential[0]
            functional = potential[1] if len(potential) > 1 else "unknown"

            label = potcar_data[1]
            pseudo["labels"].append(label)
            pseudo["pot_type"].append(pot_type)
            pseudo["functional"].append(functional)

            # Символ POTCAR
            potcar_symbols.append(f"{functional} {label}")

        return pseudo, potcar_symbols, valences, masses

    @staticmethod
    def parse_name_array(atominfo):
        """
        Extract atom names from the <atominfo> XML element.

        Args:
            atominfo: XML element containing <array name="atoms">.

        Returns:
            list: A list of atom names.

        Raises:
            ValueError: If the required <array name="atoms"> or its contents are missing.
        """
        if atominfo is None:
            raise ValueError("Input 'atominfo' cannot be None.")

        # Ищем массив с именем "atoms"
        atoms_array = atominfo.find(".//array[@name='atoms']")
        if atoms_array is None:
            raise ValueError("The <atominfo> element does not contain an <array name='atoms'>.")

        # Извлекаем имена атомов из <set>
        atom_names = []
        for rc in atoms_array.findall(".//rc"):
            c_element = rc.find("c")
            if c_element is None or c_element.text is None:
                raise ValueError(f"Invalid <rc>: missing <c> element or text.")
            atom_names.append(c_element.text.strip())

        if not atom_names:
            raise ValueError("No atom names found in the <atominfo> element.")

        return atom_names

    #    def parse_eigenvalue(self, eigenvalue):
#        eigenvalue = eigenvalue.find("array")
#        eigenvalues = self.parse_array(eigenvalue)
#        return eigenvalues
    def parse_parameters(self, parameters_element):
        """
        Parse the <parameters> XML element into a nested dictionary.

        Args:
            parameters_element: XML element <parameters> containing nested <separator> and <i> tags.

        Returns:
            dict: A nested dictionary of parsed parameters.

        Raises:
            ValueError: If the input is missing required attributes or elements.
        """
        if parameters_element is None:
            raise ValueError("Input 'parameters_element' cannot be None.")

        parameters = {}

        # Обрабатываем каждый <separator> в <parameters>
        for separator in parameters_element.findall("separator"):
            name = separator.attrib.get("name")
            if not name:
                raise ValueError("A <separator> element is missing the 'name' attribute.")

            # Извлекаем параметры на первом уровне
            parameters[name] = self.parse_i_tag_collection(separator)

            # Обрабатываем вложенные <separator>
            for sub_separator in separator.findall("separator"):
                sub_name = sub_separator.attrib.get("name")
                if not sub_name:
                    raise ValueError("A nested <separator> element is missing the 'name' attribute.")

                # Добавляем вложенные параметры
                parameters[name][sub_name] = self.parse_i_tag_collection(sub_separator)

        return parameters

    def parse_eigenvalue(self, eigenvalue):
        """
        Parse eigenvalues from the <eigenvalues> XML element.

        Args:
            eigenvalue: XML element <eigenvalues> containing <array> with data.

        Returns:
            list: Parsed eigenvalues as a nested list.

        Raises:
            ValueError: If the <eigenvalues> or its required <array> element is missing.
        """
        if eigenvalue is None:
            raise ValueError("Input 'eigenvalue' cannot be None.")

        # Проверяем наличие элемента <array>
        eigenvalue_array = eigenvalue.find("array")
        if eigenvalue_array is None:
            raise ValueError("<eigenvalues> element does not contain a required <array> child.")

        # Парсим массив данных
        try:
            eigenvalues = self.parse_array(eigenvalue_array)
        except ValueError as e:
            raise ValueError(f"Failed to parse eigenvalues from <array>: {e}")

        if not eigenvalues:
            raise ValueError("No eigenvalues found in the <array> element.")

        return eigenvalues

    def parse_dos(self, dos):
        """
        Parse the density of states (DOS) from the <dos> XML element.

        Args:
            dos: XML element <dos> containing <total> and <partial> DOS data.

        Returns:
            tuple:
                - t_dos (list): Total DOS as a list of arrays.
                - p_dos (list): Partial DOS as a nested list of arrays.

        Raises:
            ValueError: If the required elements are missing or malformed.
        """
        if dos is None:
            raise ValueError("Input 'dos' cannot be None.")

        def parse_array_sets(array_element):
            """Helper function to parse all <set> elements in an <array>."""
            return [
                self.parse_varray_pymatgen(set_element)
                for set_element in array_element.findall("set")
            ]

        # Parse total DOS
        t_dos = []
        total_element = dos.find("total")
        if total_element is not None:
            total_array = total_element.find("array")
            if total_array is not None:
                t_dos = parse_array_sets(total_array)
            else:
                raise ValueError("<total> element in <dos> is missing an <array> child.")
        else:
            raise ValueError("<dos> element does not contain a <total> child.")

        # Parse partial DOS
        p_dos = []
        partial_element = dos.find("partial")
        if partial_element is not None:
            partial_array = partial_element.find("array")
            if partial_array is not None:
                for set_element in partial_array.findall("set"):
                    p_dos.append(parse_array_sets(set_element))
        # Возвращаем обе DOS
        return t_dos, p_dos

    def parse_projected(self, projected_element):
        """
        Parse projected data from the <projected> XML element.

        Args:
            projected_element: XML element <projected> containing <array> with nested <set> data.

        Returns:
            list: A nested list of projected data.

        Raises:
            ValueError: If the required elements are missing or malformed.
        """
        if projected_element is None:
            raise ValueError("Input 'projected_element' cannot be None.")

        # Проверяем наличие <array> внутри <projected>
        array_element = projected_element.find("array")
        if array_element is None:
            raise ValueError("<projected> element does not contain an <array> child.")

        # Рекурсивный парсинг вложенных <set>
        def parse_nested_sets(set_element):
            """
            Recursively parse nested <set> elements.
            """
            parsed_data = []
            for sub_set in set_element.findall("set"):
                if sub_set.find("set") is not None:
                    # Если есть вложенные <set>, вызываем рекурсию
                    parsed_data.append(parse_nested_sets(sub_set))
                else:
                    # Если нет вложенных <set>, парсим данные
                    parsed_data.append(self.parse_varray_pymatgen(sub_set))
            return parsed_data

        # Начинаем парсинг с верхнего уровня
        top_level_set = array_element.find("set")
        if top_level_set is None:
            raise ValueError("<array> in <projected> does not contain a <set> child.")

        projected_data = parse_nested_sets(top_level_set)
        return projected_data

    def parse_calculation(self, calculation_element):
        """
        Parse the <calculation> XML element and extract relevant data.

        Args:
            calculation_element: XML element <calculation>.

        Returns:
            tuple:
                - dict: Extracted calculation data.
                - int: SCF step count.

        Raises:
            ValueError: If the required elements are missing or malformed.
        """
        if calculation_element is None:
            raise ValueError("Input 'calculation_element' cannot be None.")

        # Инициализация результатов
        result = {
            "stress": [],
            "efermi": 0.0,
            "force": [],
            "eband_eigenvalues": [],
            "energy": 0.0,
            "tdos": [],
            "pdos": [],
            "projected": [],
            "born_charges": [],
            "hessian": [],
            "normal_modes_eigenvalues": [],
            "normal_modes_eigenvectors": [],
            "epsilon_ion": [],
            "pion": [],
            "psp1": [],
            "psp2": [],
            "pelc": []
        }
        scf_count = 0

        # Обработка дочерних элементов
        for child in calculation_element.iterchildren():
            tag = child.tag
            name = child.attrib.get("name")

            if tag == "varray":
                if name == "stress":
                    result["stress"] = self.parse_varray(child)
                elif name == "forces":
                    result["force"] = self.parse_varray(child)
                elif name == "epsilon_ion":
                    result["epsilon_ion"] = self.parse_varray(child)

            elif tag == "dos":
                result["efermi"] = float(child.find(".//i[@name='efermi']").text or 0.0)
                result["tdos"], result["pdos"] = self.parse_dos(child)

            elif tag == "projected":
                result["projected"] = self.parse_projected(child)

            elif tag == "eigenvalues":
                result["eband_eigenvalues"] = self.parse_eigenvalue(child)

            elif tag == "scstep":
                scf_count += sum(
                    1
                    for energy in child.findall(".//energy/i[@name='e_fr_energy']")
                )

            elif tag == "energy":
                e_fr_energy = child.find(".//i[@name='e_fr_energy']")
                result["energy"] = float(e_fr_energy.text) if e_fr_energy is not None else 1e9

            elif tag == "array":
                if name == "born_charges":
                    result["born_charges"] = self.parse_born_chg(child)

            elif tag == "dynmat":
                result["hessian"], result["normal_modes_eigenvalues"], result[
                    "normal_modes_eigenvectors"] = self.parse_dynmat(child)

            elif tag == "v":
                parsed_v = self.parse_v(child)
                if name == "PION":
                    result["pion"] = parsed_v
                elif name == "PSP1":
                    result["psp1"] = parsed_v
                elif name == "PSP2":
                    result["psp2"] = parsed_v
                elif name == "PELC":
                    result["pelc"] = parsed_v

        return result, scf_count

    def parse_kpoints(self, kpoints_element):
        """
        Parse k-point data from the <kpoints> XML element.

        Args:
            kpoints_element: XML element <kpoints> containing k-point data.

        Returns:
            dict: A dictionary with keys:
                - 'list': List of k-point coordinates.
                - 'weights': List of k-point weights.
                - 'divisions': List of mesh divisions.
                - 'mesh_scheme': Mesh generation scheme.
        Raises:
            ValueError: If required elements are missing or malformed.
        """
        if kpoints_element is None:
            raise ValueError("Input 'kpoints_element' cannot be None.")

        # Инициализация словаря
        kpoints_dict = {'list': [], 'weights': [], 'divisions': [], 'mesh_scheme': ''}

        # Парсинг <generation>
        generation = kpoints_element.find("generation")
        if generation is not None:
            kpoints_dict['mesh_scheme'] = generation.attrib.get('param', '')
            divisions_element = generation.find(".//i[@name='divisions']")
            if divisions_element is not None and divisions_element.text:
                try:
                    kpoints_dict['divisions'] = [int(x) for x in divisions_element.text.split()]
                except ValueError as e:
                    raise ValueError(f"Invalid divisions data: {divisions_element.text}. Error: {e}")

        # Парсинг <varray>
        for varray in kpoints_element.findall("varray"):
            name = varray.attrib.get("name", "")
            if name == "kpointlist":
                kpoints_dict['list'] = self.parse_varray(varray)
            elif name == "weights":
                kpoints_dict['weights'] = self.parse_varray(varray)

        return kpoints_dict

    def get_bands(self):
        """
        Compute the valence band index (IBAND) and occupation status (occupy).

        Returns:
            tuple:
                - int: Valence band index (IBAND).
                - bool: Occupation status (True if fully occupied, False otherwise).

        Raises:
            ValueError: If required data is missing or invalid.
        """
        # Проверяем, что необходимые параметры существуют
        try:
            total_electrons = int(self.values['parameters']['electronic']['NELECT'])
            spin_polarized = self.values['parameters']['electronic']['electronic spin'].get('ISPIN', 1) == 2
        except KeyError as e:
            raise ValueError(f"Missing parameter in input data: {e}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid NELECT value: {e}")

        # Учитываем спин
        factor = 1 if spin_polarized else 2

        # Вычисляем IBAND и состояние occupy
        IBAND = total_electrons // factor
        occupy = total_electrons % factor == 0

        # Сохраняем в self.values
        self.values["bands"] = IBAND
        self.values["occupy"] = occupy

        return IBAND, occupy

    @staticmethod
    def get_cbm(kpoints, efermi, eigens, IBAND):
        """
        Calculate the Conduction Band Minimum (CBM) for a given band index.

        Args:
            kpoints (np.ndarray): Array of k-points, shape (N_kpoints, 3).
            efermi (float): Fermi energy level.
            eigens (np.ndarray): Eigenvalues, shape (N_kpoints, N_bands, spin).
            IBAND (int): Band index for the conduction band.

        Returns:
            dict: A dictionary with keys:
                - 'kpoint': The k-point where the CBM occurs.
                - 'value': The energy value of the CBM relative to efermi.

        Raises:
            ValueError: If the inputs are invalid or indices are out of bounds.
        """
        # Проверяем входные данные
        if not (isinstance(kpoints, np.ndarray) and kpoints.ndim == 2 and kpoints.shape[1] == 3):
            raise ValueError("Invalid kpoints: Must be a 2D array with shape (N_kpoints, 3).")

        if not (isinstance(eigens, np.ndarray) and eigens.ndim >= 2):
            raise ValueError("Invalid eigens: Must be a 2D or 3D array.")

        if IBAND < 0 or IBAND >= eigens.shape[1]:
            raise ValueError(f"Invalid IBAND index: Must be between 0 and {eigens.shape[1] - 1}.")

        # Поиск индекса минимального значения
        ind = np.argmin(eigens[:, IBAND, 0])  # Предполагается spin=0 для первого спина
        cbm_kpoint = kpoints[ind]
        cbm_value = eigens[ind, IBAND, 0] - efermi

        return {'kpoint': cbm_kpoint, 'value': cbm_value}

    @staticmethod
    def get_cbm(kpoints, efermi, eigens, IBAND):
        """
        Calculate the Conduction Band Minimum (CBM) for a given band index.

        Args:
            kpoints (np.ndarray): Array of k-points, shape (N_kpoints, 3).
            efermi (float): Fermi energy level.
            eigens (np.ndarray): Eigenvalues, shape (N_kpoints, N_bands, spin).
            IBAND (int): Band index for the conduction band.

        Returns:
            dict: A dictionary with keys:
                - 'kpoint': The k-point where the CBM occurs.
                - 'value': The energy value of the CBM relative to efermi.

        Raises:
            ValueError: If the inputs are invalid or indices are out of bounds.
        """
        # Проверяем входные данные
        if not (isinstance(kpoints, np.ndarray) and kpoints.ndim == 2 and kpoints.shape[1] == 3):
            raise ValueError("Invalid kpoints: Must be a 2D array with shape (N_kpoints, 3).")

        if not (isinstance(eigens, np.ndarray) and eigens.ndim >= 2):
            raise ValueError("Invalid eigens: Must be a 2D or 3D array.")

        if IBAND < 0 or IBAND >= eigens.shape[1]:
            raise ValueError(f"Invalid IBAND index: Must be between 0 and {eigens.shape[1] - 1}.")

        # Поиск индекса минимального значения
        ind = np.argmin(eigens[:, IBAND, 0])  # Предполагается spin=0 для первого спина
        cbm_kpoint = kpoints[ind]
        cbm_value = eigens[ind, IBAND, 0] - efermi

        return {'kpoint': cbm_kpoint, 'value': cbm_value}

    def get_band_gap(self):
        """
        Compute the band gap, CBM, and VBM, and determine if the material is metallic.

        Updates:
            - self.values['gap']: Band gap value (eV).
            - self.values['cbm']: CBM information {'kpoint': ..., 'value': ...}.
            - self.values['vbm']: VBM information {'kpoint': ..., 'value': ...}.
            - self.values['metal']: True if material is metallic, False otherwise.

        Raises:
            ValueError: If required data is missing or malformed.
        """
        # Вызываем get_bands для вычисления IBAND и occupy
        self.get_bands()
        IBAND = self.values['bands']
        occupy = self.values['occupy']

        # Инициализация значений
        self.values['metal'] = False
        self.values['gap'] = None
        self.values['cbm'] = None
        self.values['vbm'] = None

        # Если валентная зона полностью занята
        if occupy:
            try:
                efermi = self.values["calculation"]["efermi"]
                eigens = np.array(self.values['calculation']['eband_eigenvalues'])
                kpoints = np.array(self.values['kpoints']['list'])

                # Проверка согласования размерностей
                if eigens.shape[0] > kpoints.shape[0]:
                    kpoints = np.tile(kpoints, [2, 1])

                # Получаем CBM и VBM
                cbm = self.get_cbm(kpoints, efermi, eigens, IBAND)
                vbm = self.get_vbm(kpoints, efermi, eigens, IBAND - 1)

                # Вычисляем ширину запрещённой зоны
                band_gap = cbm['value'] - vbm['value']
                if band_gap < 0:
                    self.values['metal'] = True
                    band_gap = 0

                # Обновляем значения
                self.values['gap'] = band_gap
                self.values['cbm'] = cbm
                self.values['vbm'] = vbm

            except KeyError as e:
                raise ValueError(f"Missing required calculation data: {e}")
            except IndexError as e:
                raise ValueError(f"Index out of bounds during CBM or VBM calculation: {e}")
        else:
            # Если валентная зона не полностью занята, считаем материал металлическим
            self.values['metal'] = True
            self.values['gap'] = 0

    def eigenvalues_by_band(self, band=0):
        """
        Extract eigenvalues for the specified band and adjust by the Fermi level.

        Args:
            band (int): Index of the band to extract eigenvalues from.

        Returns:
            np.ndarray: Array of eigenvalues adjusted by the Fermi level.

        Raises:
            ValueError: If the band index is out of bounds or data is missing.
        """
        # Проверяем, что необходимые данные существуют
        try:
            efermi = self.values["calculation"]["efermi"]
            eigens = np.array(self.values["calculation"]["eband_eigenvalues"])
        except KeyError as e:
            raise ValueError(f"Missing required calculation data: {e}")

        # Проверяем, что band в допустимых пределах
        if not (0 <= band < eigens.shape[1]):
            raise ValueError(f"Band index {band} is out of bounds. Valid range: 0 to {eigens.shape[1] - 1}.")

        # Извлечение собственных значений для указанной зоны
        eigenvalues = eigens[:, band, 0]  # Предполагается, что spин=0
        return eigenvalues - efermi

    def show_eigenvalues_by_band(self, bands=[0]):
        """
        Display eigenvalues for specified bands along k-points.

        Args:
            bands (list): List of band indices to display eigenvalues for.

        Raises:
            ValueError: If required data is missing or indices are invalid.
        """
        # Проверяем, что kpoints и eigenvalues существуют
        try:
            kpoints = np.array(self.values['kpoints']['list'])
            spin_polarized = self.values.get('spin', False)
        except KeyError as e:
            raise ValueError(f"Missing required k-points or spin data: {e}")

        if kpoints.ndim != 2 or kpoints.shape[1] != 3:
            raise ValueError("Invalid k-points data: Must be a 2D array with shape (N_kpoints, 3).")

        # Подготовка данных для вывода
        col_data = {'K-points': [tuple(kpt) for kpt in kpoints]}

        for band in bands:
            eigenvalues = self.eigenvalues_by_band(band)
            if spin_polarized:
                if len(eigenvalues) % 2 != 0:
                    raise ValueError("Spin-polarized eigenvalues should have an even number of entries.")
                eigens = eigenvalues.reshape(-1, 2)  # Разделяем на "up" и "down"
                col_data[f'band{band}_up'] = eigens[:, 0]
                col_data[f'band{band}_down'] = eigens[:, 1]
            else:
                col_data[f'band{band}'] = eigenvalues

        # Создание DataFrame и вывод
        df = pd.DataFrame(col_data)
        print(tabulate(df, headers='keys', tablefmt='grid'))

    def export_incar(self, filename=None, print_incar=True):
        """
        Export INCAR parameters to a file or print to console.

        Args:
            filename (str, optional): Path to the file where INCAR data will be saved.
            print_incar (bool, optional): Whether to print INCAR data to the console.

        Raises:
            ValueError: If 'incar' data is missing in self.values.
            IOError: If there is an error writing to the file.
        """
        # Проверяем, что данные INCAR существуют
        incar_data = self.values.get('incar')
        if not incar_data:
            raise ValueError("INCAR data is missing in self.values['incar'].")

        # Формируем строки для записи
        contents = [f"{key} = {value}\n" for key, value in incar_data.items()]

        # Сохраняем в файл, если указан путь
        if filename:
            try:
                with open(filename, 'w') as file:
                    file.writelines(contents)
                print(f"INCAR data successfully exported to {filename}.")
            except IOError as e:
                raise IOError(f"Error writing INCAR data to file '{filename}': {e}")

        # Выводим на экран, если указано
        if print_incar:
            print("INCAR Data:")
            print("".join(contents))

        # Сохраняем для внутреннего использования
        self.incar = contents

    def export_kpoints(self, filename=None):
        """
        Export k-points data to a file or print to console.

        Args:
            filename (str, optional): Path to the file where k-points will be saved.

        Raises:
            ValueError: If k-points data is missing or malformed.
            IOError: If there is an error writing to the file.
        """
        # Проверяем наличие данных о k-точках
        try:
            kpoints_list = np.array(self.values['kpoints']['list'])
            weights = np.array(self.values['kpoints']['weights'])
        except KeyError as e:
            raise ValueError(f"Missing k-points data in self.values: {e}")

        if kpoints_list.ndim != 2 or kpoints_list.shape[1] != 3:
            raise ValueError("Invalid k-points data: Must be a 2D array with shape (N_kpoints, 3).")
        if len(weights) != len(kpoints_list):
            raise ValueError("Mismatch between the number of k-points and weights.")

        # Формируем содержимое
        contents = ["KPOINTS\n"]
        contents.append(f"{len(kpoints_list)}\n")
        contents.append("Cartesian\n")
        for kpt, wt in zip(kpoints_list, weights):
            contents.append(f"{kpt[0]:10.4f} {kpt[1]:10.4f} {kpt[2]:10.4f} {wt[0]:10.4f}\n")

        # Сохраняем в файл или выводим в консоль
        if filename:
            try:
                with open(filename, 'w') as file:
                    file.writelines(contents)
                print(f"K-points data successfully exported to {filename}.")
            except IOError as e:
                raise IOError(f"Error writing k-points data to file '{filename}': {e}")
        else:
            print("K-points Data:")
            print("".join(contents))

    def export_poscar(self, filename):
        """
        Export atomic structure data to a POSCAR file.

        Args:
            filename (str): Path to the output POSCAR file.

        Raises:
            ValueError: If required data is missing or malformed.
            IOError: If there is an error writing to the file.
        """
        try:
            # Проверяем, что все данные присутствуют
            composition = self.values["composition"]
            atom_names = self.values["name_array"]
            lattice = np.array(self.values["finalpos"]["basis"])
            positions = np.array(self.values["finalpos"]["positions"])
        except KeyError as e:
            raise ValueError(f"Missing required data for POSCAR export: {e}")

        if lattice.shape != (3, 3):
            raise ValueError("Lattice basis must be a 3x3 matrix.")
        if positions.shape[1] != 3:
            raise ValueError("Positions must be a Nx3 matrix.")

        # Формируем содержимое файла POSCAR
        contents = []

        # Строка заголовка
        header = "".join([f"{key}{composition[key]}" for key in composition.keys()])
        contents.append(f"{header}\n")

        # Масштабный коэффициент
        contents.append("1.0\n")

        # Матрица решётки
        for vector in lattice:
            contents.append(f"{vector[0]:12.6f} {vector[1]:12.6f} {vector[2]:12.6f}\n")

        # Названия атомов
        contents.append(" ".join(f"{key}" for key in composition.keys()) + "\n")

        # Количество атомов каждого типа
        contents.append(" ".join(f"{composition[key]}" for key in composition.keys()) + "\n")

        # Координаты атомов
        contents.append("Direct\n")
        for position in positions:
            contents.append(f"{position[0]:12.6f} {position[1]:12.6f} {position[2]:12.6f}\n")

        # Записываем в файл
        try:
            with open(filename, 'w') as file:
                file.writelines(contents)
            print(f"POSCAR data successfully exported to {filename}.")
        except IOError as e:
            raise IOError(f"Error writing POSCAR data to file '{filename}': {e}")

    def parse_bandpath(self):
        """
        Parse the band path from k-points and reciprocal lattice basis.

        Raises:
            ValueError: If required data is missing or malformed.
        """
        try:
            kpts = np.array(self.values['kpoints']['list'])
            rec_basis = np.array(self.values['finalpos']['rec_basis'])
        except KeyError as e:
            raise ValueError(f"Missing required data for band path parsing: {e}")

        if kpts.ndim != 2 or kpts.shape[1] != 3:
            raise ValueError("Invalid k-points: Must be a 2D array with shape (N_kpoints, 3).")
        if rec_basis.shape != (3, 3):
            raise ValueError("Invalid reciprocal basis: Must be a 3x3 matrix.")

        # Определяем, образуют ли точки прямую линию
        def is_inline(kpt, path):
            if len(path) < 2:
                return True
            v1 = np.array(kpt) - np.array(path[-1])
            v2 = np.array(path[-1]) - np.array(path[-2])
            v1_norm, v2_norm = np.linalg.norm(v1), np.linalg.norm(v2)
            if v1_norm < 1e-3:
                return False
            cos_angle = np.dot(v1, v2) / (v1_norm * v2_norm)
            return abs(cos_angle - 1) < 1e-2

        # Разделяем k-точки на сегменты пути
        paths, path = [], []
        for i, kpt in enumerate(kpts):
            if is_inline(kpt, path):
                path.append(kpt)
            else:
                paths.append(path)
                path = [kpt]
        if path:
            paths.append(path)

        # Вычисляем расстояния и путь
        band_points, band_paths = [], []
        pointer = 0
        for path in paths:
            path = np.array(path)
            distances = np.linalg.norm(np.dot(path[1:] - path[:-1], rec_basis), axis=1)
            segment = np.concatenate(([pointer], pointer + np.cumsum(distances)))
            band_paths.extend(segment)
            pointer = segment[-1]
            band_points.append(pointer)

        # Обновляем self.values
        self.values['band_paths'] = np.array(band_paths)
        self.values['band_points'] = band_points

    def plot_band(self, ax=None, filename=None, style='normal', ylim=[-20, 3],
                  xlim=None, plim=[0.0, 0.5], labels=None, saveBands=False, dpi=1200):
        """
        Plot the band structure.

        Args:
            ax (matplotlib.axes.Axes, optional): Axes object to draw on. If None, a new figure is created.
            filename (str, optional): File path to save the plot.
            style (str, optional): Plot style ('normal' or 'projected').
            ylim (list, optional): Y-axis energy limits.
            xlim (list, optional): X-axis limits.
            plim (list, optional): Color scale limits for 'projected' style.
            labels (list, optional): Custom x-axis tick labels.
            saveBands (bool, optional): If True, save band data to files.
            dpi (int, optional): DPI for the saved plot.

        Returns:
            matplotlib.axes.Axes: Axes object with the plot.

        Raises:
            ValueError: If required data is missing or malformed.
        """
        if ax is None:
            fig, ax = plt.subplots()

        # Проверяем наличие необходимых данных
        try:
            self.parse_bandpath()
            efermi = self.values["calculation"]["efermi"]
            eigens = np.array(self.values["calculation"]["eband_eigenvalues"])
            paths = np.array(self.values["band_paths"])
            band_pts = self.values["band_points"]
            proj = np.array(self.values["calculation"]["projected"]) if style == 'projected' else None
        except KeyError as e:
            raise ValueError(f"Missing required data for plotting: {e}")

        if eigens.ndim != 3 or eigens.shape[2] != 1:
            raise ValueError("Invalid eigenvalues: Must be a 3D array with shape (N_kpts, N_bands, 1).")

        n_kpts, n_bands, _ = eigens.shape
        cm = plt.cm.get_cmap('RdYlBu') if style == 'projected' else None

        # Строим зоны
        for band_idx in range(n_bands):
            band = eigens[:, band_idx, 0] - efermi

            # Пропускаем зоны за пределами ylim
            if np.all(band < ylim[0]) or np.all(band > ylim[1]):
                continue

            if style == 'projected' and proj is not None:
                # Проецируемые зоны
                projection = proj[:, band_idx, :, :].sum(axis=(1, 2))
                projection = np.clip(projection, plim[0], plim[1])
                ax.scatter(paths, band, c=projection, cmap=cm, s=10, vmin=plim[0], vmax=plim[1])
            else:
                # Обычные зоны
                ax.plot(paths, band, c='black', lw=1.0)

            # Сохранение данных зон
            if saveBands:
                data_to_save = [band]
                if style == 'projected' and proj is not None:
                    data_to_save.append(projection)
                np.savetxt(f"band_{band_idx:04d}.dat", np.column_stack(data_to_save))

        # Добавляем вертикальные линии для точек
        for pt in band_pts:
            ax.axvline(x=pt, ls='-', color='k', alpha=0.5)

        # Настраиваем цветовую шкалу для 'projected'
        if style == 'projected' and cm is not None:
            cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=cm, norm=plt.Normalize(vmin=plim[0], vmax=plim[1])),
                                ax=ax, orientation='horizontal', pad=0.1)
            cbar.set_label("Projection Intensity")

        # Настройка осей
        ax.set_ylabel("Energy (eV)")
        ax.set_ylim(ylim)
        ax.set_xlim(xlim or [0, paths[-1]])
        ax.set_xticks([] if labels is None else [0] + band_pts)
        if labels:
            ax.set_xticklabels(labels)

        # Сохранение или возврат графика
        if filename:
            plt.savefig(filename, dpi=dpi)
            print(f"Band structure plot saved to {filename}.")
        return ax

    def get_dos(self, rows, style='t'):
        """
        Extract the Density of States (DOS) based on the specified style.

        Args:
            rows (slice): Rows of energy values to extract DOS for.
            style (str): Style of DOS extraction:
                - 't': Total DOS.
                - 's', 'p', 'd': Orbital-specific DOS.
                - 'a<atom_index>' or 'a<element>': Atomic DOS for specified atom(s).

        Returns:
            tuple: (list of DOS arrays, list of labels).

        Raises:
            ValueError: If required data is missing or style is invalid.
        """
        # Проверка наличия данных
        try:
            tdos = np.array(self.values['calculation']['tdos'])
            pdos = np.array(self.values['calculation']['pdos'])
            a_array = self.values["name_array"]
        except KeyError as e:
            raise ValueError(f"Missing required data for DOS extraction: {e}")

        if tdos.ndim != 3 or pdos.ndim != 4:
            raise ValueError("Invalid DOS data: tdos must be 3D and pdos must be 4D.")

        N_atom = len(a_array)
        mydos, labels = [], []

        if style == 't':  # Total DOS
            for spin in tdos:
                mydos.append(spin[rows, 1])  # Второй столбец содержит DOS
                labels.append('Total')

        elif style in ['s', 'p', 'd']:  # Orbital-specific DOS
            orbital_indices = {'s': [1], 'p': [2, 3, 4], 'd': [5, 6, 7, 8, 9]}[style]
            for spin in pdos:
                spd = np.sum(spin[:, :, orbital_indices], axis=2)  # Суммируем по орбитальным индексам
                mydos.append(np.sum(spd[rows], axis=0))  # Суммируем по атомам
                labels.append(style)

        elif style.startswith('a'):  # Atomic DOS
            if style[1:].isdigit():
                atom_indices = [int(style[1:])]
            else:
                element = style[1:]
                atom_indices = [i for i, name in enumerate(a_array) if name == element]

            if not atom_indices:
                raise ValueError(f"No atoms match the given style: {style}")

            for spin in pdos:
                spd = np.sum(spin[atom_indices, :, :], axis=0)  # Суммируем по атомам
                mydos.append(np.sum(spd[rows, :], axis=1))  # Суммируем по орбитам
                labels.append(style[1:])

        else:
            raise ValueError(f"Invalid style: {style}")

        # Добавляем метки для спин-поляризованных данных
        if len(labels) == 2:
            labels[0] += '-up'
            labels[1] += '-down'
            mydos[1] *= -1  # Инвертируем спин Down

        return mydos, labels

    def plot_dos(self, ax=None, filename=None, smear=None, flip=False,
                 style='t', xlim=[-3, 3], ylim=[None, None], dos_range=[0, None], dpi=1200):
        """
        Plot the Density of States (DOS).

        Args:
            ax (matplotlib.axes.Axes, optional): Axes object to draw on. If None, a new figure is created.
            filename (str, optional): File path to save the plot.
            smear (float, optional): Gaussian smearing width for smoothing DOS curves.
            flip (bool, optional): Flip the axes (Energy on y-axis, DOS on x-axis).
            style (str, optional): Style of DOS ('t' for total, 's', 'p', 'd', or 'a<element>' for atomic).
            xlim (list, optional): Energy range for the x-axis.
            ylim (list, optional): DOS range for the y-axis.
            dos_range (list, optional): Range of DOS values for flipping axes.
            dpi (int, optional): DPI for the saved plot.

        Returns:
            matplotlib.axes.Axes: Axes object with the plot.

        Raises:
            ValueError: If required data is missing or malformed.
        """
        # Проверка данных
        try:
            efermi = self.values['calculation']['efermi']
            tdos = np.array(self.values['calculation']['tdos'][0])
        except KeyError as e:
            raise ValueError(f"Missing required data for DOS plotting: {e}")

        if tdos.ndim != 2 or tdos.shape[1] < 2:
            raise ValueError("Invalid tdos data: Must be a 2D array with at least 2 columns.")

        # Вычисляем энергии относительно уровня Ферми
        tdos[:, 0] -= efermi
        energies = tdos[:, 0]
        valid_rows = (energies > xlim[0]) & (energies < xlim[1])
        energies = energies[valid_rows]

        # Подготовка данных для графика
        dos_data = {}
        for opt in style.split('+'):
            if opt == 'spd':
                options = ['s', 'p', 'd']
            elif opt == 'a':
                options = [f'a{el}' for el in self.values.get('elements', [])]
            else:
                options = [opt]

            for option in options:
                dos, labels = self.get_dos(valid_rows, option)
                for data, label in zip(dos, labels):
                    dos_data[label] = data

        if ax is None:
            fig, ax = plt.subplots()

        # Рисуем DOS
        for label, dos in dos_data.items():
            if smear:
                dos = smear_data(np.column_stack((energies, dos)), smear)[:, 1]
            if flip:
                ax.plot(dos, energies, label=label)
            else:
                ax.plot(energies, dos, label=label)

        # Настройка осей и подписей
        if flip:
            ax.set_xlabel("DOS (States/eV)")
            ax.set_ylabel("Energy (eV)")
            ax.set_ylim(xlim)
            x_min, x_max = ax.get_xlim()
            if dos_range[0] is not None: x_min = dos_range[0]
            if dos_range[1] is not None: x_max = dos_range[1]
            ax.set_xlim(x_min, x_max)
        else:
            ax.set_xlabel("Energy (eV)")
            ax.set_ylabel("DOS")
            ax.set_xlim(xlim)
            y_min, y_max = ylim
            if y_min is None: y_min = ax.get_ylim()[0]
            if y_max is None: y_max = ax.get_ylim()[1]
            ax.set_ylim(y_min, y_max)

        # Легенда
        ax.legend(loc='upper right')

        # Сохранение или возврат осей
        if filename:
            plt.savefig(filename, dpi=dpi)
            print(f"DOS plot saved to {filename}.")
        return ax

    def plot_band_dos(self, filename=None, band_style='normal', dos_style='t+a', smear=None,
                      e_range=[-10, 3], dos_max=None, plim=[0.0, 0.5],
                      band_labels=None, figsize=(6, 4), dpi=1200):
        """
        Plot the band structure and DOS in a combined figure.

        Args:
            filename (str, optional): File path to save the plot.
            band_style (str, optional): Style of the band structure plot.
            dos_style (str, optional): Style of the DOS plot.
            smear (float, optional): Gaussian smearing width for smoothing DOS curves.
            e_range (list, optional): Energy range for both band structure and DOS.
            dos_max (float, optional): Maximum value for DOS.
            plim (list, optional): Projection limits for 'projected' style.
            band_labels (list, optional): Labels for k-point ticks in the band structure.
            figsize (tuple, optional): Size of the figure.
            dpi (int, optional): DPI for the saved plot.

        Returns:
            matplotlib.figure.Figure: Figure object containing the plot.

        Raises:
            ValueError: If required data for band structure or DOS is missing.
        """
        # Создание фигуры с подграфиками
        fig = plt.figure(figsize=figsize)
        gs = gridspec.GridSpec(1, 2, width_ratios=[2, 1])

        # Подграфик для зон
        ax_band = plt.subplot(gs[0])
        try:
            ax_band = self.plot_band(ax_band, style=band_style, ylim=e_range, plim=plim, labels=band_labels)
        except ValueError as e:
            raise ValueError(f"Error plotting band structure: {e}")

        # Подграфик для DOS
        ax_dos = plt.subplot(gs[1])
        try:
            ax_dos = self.plot_dos(ax_dos, style=dos_style, smear=smear, xlim=e_range, dos_range=[0, dos_max],
                                   flip=True)
        except ValueError as e:
            raise ValueError(f"Error plotting DOS: {e}")

        # Сохранение графика
        if filename:
            try:
                plt.savefig(filename, dpi=dpi, bbox_inches='tight')
                print(f"Combined band structure and DOS plot saved to {filename}.")
            except IOError as e:
                raise IOError(f"Error saving plot to file '{filename}': {e}")

        return fig

class IR:
    """
    A class to compute the IR intensity and dielectric tensors.
    """
    def __init__(self, born_chgs, eigenvalues, eigenvectors, mass, vol):
        """
        Initialize IR computation with input parameters.

        Args:
            born_chgs (np.ndarray): Born effective charge tensors [N_atom, 3, 3].
            eigenvalues (np.ndarray): Vibrational frequencies [N_modes].
            eigenvectors (np.ndarray): Normal mode eigenvectors [N_modes, N_atoms * 3].
            mass (np.ndarray): Atomic masses [N_atoms].
            vol (float): Unit cell volume.

        Raises:
            ValueError: If input data dimensions are inconsistent or missing.
        """
        # Проверка входных данных
        self._validate_inputs(born_chgs, eigenvalues, eigenvectors, mass, vol)

        self.born_chgs = np.array(born_chgs)
        self.freqs = np.array(eigenvalues)
        self.modes = np.reshape(eigenvectors, (len(eigenvalues), -1, 3))
        self.mass = np.array(mass)
        self.vol = vol
        self.Natom = len(born_chgs)

        self.IRs = []
        self.epsilons = []

        # Вычисляем IR интенсивности и тензоры
        for mode, freq in zip(self.modes, self.freqs):
            IR_intensity = self._compute_ir_intensity(mode)
            self.IRs.append(IR_intensity)

            if abs(IR_intensity) > 1e-2 and abs(freq) > 5e-3:
                epsilon = self._compute_epsilon(mode, freq)
            else:
                epsilon = np.zeros((3, 3)).flatten()

            self.epsilons.append(epsilon)

        # Преобразуем результаты в numpy массивы
        self.IRs = np.array(self.IRs)
        self.epsilons = np.array(self.epsilons)

    def _validate_inputs(self, born_chgs, eigenvalues, eigenvectors, mass, vol):
        """Validate input data for dimensions and consistency."""
        if not isinstance(born_chgs, np.ndarray) or born_chgs.shape[1:] != (3, 3):
            raise ValueError("Born charges must be an array with shape (N_atom, 3, 3).")
        if not isinstance(eigenvalues, np.ndarray) or eigenvalues.ndim != 1:
            raise ValueError("Eigenvalues must be a 1D array of frequencies.")
        if not isinstance(eigenvectors, np.ndarray) or eigenvectors.shape[1] != len(born_chgs) * 3:
            raise ValueError("Eigenvectors must have shape (N_modes, N_atoms * 3).")
        if not isinstance(mass, np.ndarray) or len(mass) != len(born_chgs):
            raise ValueError("Mass must be a 1D array with one value per atom.")
        if not isinstance(vol, (int, float)) or vol <= 0:
            raise ValueError("Volume must be a positive float.")

    def _compute_ir_intensity(self, mode):
        """Compute the IR intensity for a given mode."""
        mode = np.reshape(mode, (self.Natom, 3))
        dipole = np.einsum("ij,ijk->k", mode, self.born_chgs)  # Быстрое вычисление диполя
        return np.sum(dipole**2)

    def _compute_epsilon(self, mode, freq):
        """Compute the dielectric tensor for a given mode."""
        return compute_epsilon_by_modes(mode, freq, self.born_chgs, self.vol, self.mass)

    def show(self):
        """
        Display IR intensities and dielectric tensors in a formatted table.

        Raises:
            ValueError: If required data is missing or malformed.
        """
        # Проверяем, что данные присутствуют
        if not hasattr(self, 'IRs') or not hasattr(self, 'freqs') or not hasattr(self, 'epsilons'):
            raise ValueError("IR object is missing required attributes (IRs, freqs, epsilons).")

        if len(self.IRs) != len(self.freqs) or len(self.IRs) != len(self.epsilons):
            raise ValueError("Inconsistent data lengths for IR intensities, frequencies, and tensors.")

        # Заголовок таблицы
        header = "\n   {:>10s}    {:>12s}    {:>12s}    {:>12s}    {:>12s}".format(
            "Freq (cm⁻¹)", "IR Intensity", "E_xx", "E_yy", "E_zz"
        )
        print(header)
        print("-" * len(header))

        # Форматированный вывод каждой строки
        for ir, freq, eps in zip(self.IRs, self.freqs, self.epsilons):
            freq_cm1 = freq * units.ev2cm
            if isinstance(eps, np.ndarray) and eps.size >= 9:
                print("{:12.3f} {:12.3f} {:12.3f} {:12.3f} {:12.3f}".format(
                    freq_cm1, ir, eps[0], eps[4], eps[8]))
            else:
                print("{:12.3f} {:12.3f} {:>12s} {:>12s} {:>12s}".format(
                    freq_cm1, ir, "N/A", "N/A", "N/A"))

        # Подсчёт и вывод суммы тензоров
        try:
            eps_sum = np.sum(self.epsilons, axis=0)
            if eps_sum.size >= 9:
                print("\n{:25s} {:12.3f} {:12.3f} {:12.3f}".format(
                    "Total E_xx, E_yy, E_zz", eps_sum[0], eps_sum[4], eps_sum[8]))
            else:
                print("\nTotal epsilon data unavailable or malformed.")
        except Exception as e:
            print(f"\nError during epsilon summation: {e}")


def compute_epsilon_by_modes(mode, freq, z, V, mass):
    """
    Compute the dielectric tensor for a given vibrational mode.

    Args:
        mode (np.ndarray): Normal mode eigenvector [N_atoms, 3].
        freq (float): Vibrational frequency (in eV).
        z (np.ndarray): Born effective charge tensors [N_atoms, 3, 3].
        V (float): Unit cell volume (in Å³).
        mass (np.ndarray): Atomic masses [N_atoms].

    Returns:
        np.ndarray: Flattened dielectric tensor (3x3).

    Raises:
        ValueError: If input data dimensions or values are invalid.
    """
    # Проверка входных данных
    if mode.ndim != 2 or mode.shape[1] != 3:
        raise ValueError("Mode must be a 2D array with shape (N_atoms, 3).")
    if z.ndim != 3 or z.shape[1:] != (3, 3):
        raise ValueError("Born charges must have shape (N_atoms, 3, 3).")
    if len(mass) != len(z):
        raise ValueError("Mass array length must match the number of atoms in Born charges.")
    if freq <= 0:
        raise ValueError("Frequency must be a positive value.")
    if V <= 0:
        raise ValueError("Volume must be a positive value.")

    # Преобразование единиц
    freq_hartree = freq / units.ev2hartree
    V_bohr3 = V / (units.a2bohr ** 3)  # Объём в кубических боровах

    # Вычисление эффективного заряда Z*
    mass_sqrt = np.sqrt(mass)[:, np.newaxis]  # Приводим массы к виду [N_atoms, 1]
    zt = np.einsum("ij,ijk,ik->k", mode, z, 1 / mass_sqrt)

    # Вычисление диэлектрического тензора
    epsilon = np.outer(zt, zt) / (freq_hartree ** 2)

    # Применяем масштабный фактор
    factor = 4 * units.pi / V_bohr3 / units.proton_mass
    epsilon *= factor

    return epsilon.flatten()