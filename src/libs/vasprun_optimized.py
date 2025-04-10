#!/usr/bin/env  python
# encoding: utf-8
# from version import __version__
import warnings

import matplotlib as mpl
import numpy as np
import pandas as pd
from lxml import etree

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
    from scipy.ndimage.filters import gaussian_filter1d

    diff = [data[i + 1, 0] - data[i, 0] for i in range(len(data) - 1)]
    avg_x_per_step = np.sum(diff) / len(diff)
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
        self.error = False
        self.errormsg = ''
        self.values = {}
        try:
            doc = etree.parse(vasp_file)
            doc = doc.getroot()
            self.parse_vaspxml(doc)
            self.get_band_gap()
            N_atom = len(self.values['finalpos']['positions'])
            if N_atom > 0:
                self.values['calculation']['energy_per_atom'] = self.values['calculation']['energy'] / N_atom
            else:
                raise ValueError("Number of atoms (N_atom) is zero.")
        except etree.XMLSyntaxError:
            self.error = True
            self.errormsg = 'corrupted file found'
        except ValueError as e:
            self.error = True
            self.errormsg = str(e)

        if verbosity > 0 and self.error:
            print("----------Warning---------------")
            print(self.errormsg)
            print("--------------------------------")

    def parse_vaspxml(self, xml_object):
        """
        parse the following tags

        - incar
        - kpoints
        - atominfo - composition, elements, formula
        - calculation - eigenvalues, energy, dos, fermi energy, stress, force
        - finalpos - lattice, rec_lat, positions
        """

        for child in xml_object.iterchildren():
            self.values.setdefault(child.tag, {})
            if child.tag == "incar":
                self.values[child.tag] = self.parse_i_tag_collection(child)
            elif child.tag == "kpoints":
                self.values[child.tag] = self.parse_kpoints(child)
            elif child.tag == "parameters":
                self.values[child.tag] = self.parse_parameters(child)
            elif child.tag == "atominfo":
                self.values["name_array"] = self.parse_name_array(child)
                self.values["composition"] = self.parse_composition(child)
                self.values["elements"] = self.get_element(self.values["composition"])
                self.values["formula"] = self.get_formula(self.values["composition"])
                self.values["pseudo_potential"], self.values["potcar_symbols"], \
                    self.values["valence"], self.values["mass"] = \
                    self.get_potcar(child)
            elif child.tag == "calculation":
                self.values["calculation"], scf_count = self.parse_calculation(child)
                if self.values['parameters']['electronic']['electronic convergence']['NELM'] == scf_count:
                    self.error = True
                    self.errormsg = 'SCF is not converged'
                else:
                    self.error = False  # if last SCF is fine, results are fine

                if self.values['parameters']['electronic']['electronic spin']['LSORBIT'] \
                        or self.values['parameters']['electronic']['electronic spin']['ISPIN'] == 2:
                    self.spin = True
                else:
                    self.spin = False
            elif child.tag == "structure" and child.attrib.get("name") == "finalpos":
                self.values["finalpos"] = self.parse_finalpos(child)
            elif child.tag not in ("i", "r", "v", "incar", "kpoints", "atominfo", "calculation"):
                self.values[child.tag] = self.parse_vaspxml(child)
            self.dict_clean(self.values)

    @staticmethod
    def dict_clean(dict_del):
        """
        Delete the keys that is {} and None
        Loops recursively over nested dictionaries.
        """
        dict_foo = dict_del.copy()  # Used as iterator to avoid the 'DictionaryHasChanged' error
        for key in dict_foo.keys():
            if isinstance(dict_foo[key], dict):
                vasprun.dict_clean(dict_del[key])

            if dict_foo[key] == {} or dict_foo[key] is None:
                try:
                    del dict_del[key]
                except KeyError:
                    pass

        return dict_del

    def parse_finalpos(self, finalpos):
        """
        obtain final configuration
        """
        d = {}
        for i in finalpos.iter("varray"):
            name = i.attrib.get("name")
            d[name] = self.parse_varray(i)
        return d

    def parse_dynmat(self, dynmat):
        hessian, eigenvalues, eigenvectors = [], [], []
        for va in dynmat.findall("varray"):
            if va.attrib.get("name") == "hessian":
                hessian = self.parse_varray(va)
            elif va.attrib.get("name") == "eigenvectors":
                eigenvectors = self.parse_varray(va)
        factor = np.sqrt(units.ev2j / 1e-20 / units.am2kg)
        for v in dynmat.findall("v"):
            for i in v.text.split():
                eigenvalues.append(np.sqrt(abs(float(i))) * factor * units.plank / units.ev2j / 2 / units.pi)
        return hessian, eigenvalues, eigenvectors

    def parse_born_chg(self, charge):
        """
        obtain the born charge
        """
        chg = []
        for info in charge.findall('set'):
            chg.append(self.parse_varray(info))
        return chg

    def parse_i_tag_collection(self, itags_collection):
        d = {}
        for info in itags_collection.findall("i"):
            name = info.attrib.get("name")
            type = info.attrib.get("type")
            content = info.text
            d[name] = self.assign_type(type, content)
        return d

    @staticmethod
    def parse_varray_pymatgen(elem):
        def _vasprun_float(f):
            """
            Large numbers are often represented as ********* in the vasprun.
            This function parses these values as np.nan
            """
            try:
                return float(f)
            except ValueError as e:
                f = f.strip()
                if f == '*' * len(f):
                    warnings.warn('Float overflow (*******) encountered in vasprun')
                    return np.nan
                raise e

        if elem.get("type", None) == 'logical':
            m = [[True if i == 'T' else False for i in v.text.split()] for v in elem]
        else:
            m = [[_vasprun_float(i) for i in v.text.split()] for v in elem]

        return m

    def parse_v(self, v):
        """
        obtain final configuration
        """
        return [float(n) for n in v.text.split()]

    @staticmethod
    def parse_varray(varray):
        if varray.get("type") == 'int':
            m = [[int(number) for number in v.text.split()] for v in varray.findall("v")]
        else:
            try:
                m = [[float(number) for number in v.text.split()] for v in varray.findall("v")]
            except ValueError:
                m = [[0 for number in v.text.split()] for v in varray.findall("v")]
        return m

    @staticmethod
    def parse_array(array):
        array_dictionary = {}
        values = []
        dimension_list = {}
        field_list = []

        for dimension in array.findall("dimension"):
            dimension_list[dimension.attrib.get("dim")] = dimension.text

        for field in array.findall("field"):
            field_list.append(field.text)

        for r in array.iter("r"):
            values.append([float(number) for number in r.text.split()])

        array_dictionary["value"] = values
        array_dictionary['dimensions'] = dimension_list
        array_dictionary['fields'] = field_list

        return array_dictionary

    @staticmethod
    def assign_type(type, content):
        if type == "logical":
            content = content.replace(" ", "")
            if content in ('T', 'True', 'true'):
                return True
            elif content in ('F', 'False', 'false'):
                return False
            else:
                warnings.warn("logical text " + content + " not T, True, true, F, False, false, set to False")
            return False
        elif type == "int":
            return int(content) if len(content.split()) == 1 else [int(number) for number in content.split()]
        elif type == "string":
            return content
        elif type is None:
            return float(content) if len(content.split()) == 1 else [float(number) for number in content.split()]
        else:
            warnings.warn("New type: " + type + ", set to string")
        return content

    @staticmethod
    def parse_composition(atom_info):
        atom_names = {}
        for set in atom_info.findall("array"):

            if set.attrib.get("name") == "atoms":
                for rc in set.iter("rc"):
                    atom_name = rc.find("c").text.replace(" ", '')
                    if atom_name in atom_names:
                        atom_names[atom_name] += 1
                    else:
                        atom_names[atom_name] = 1

                break
        return atom_names

    @staticmethod
    def get_element(atom_names_dictionary):
        elements = []
        for atom_name in atom_names_dictionary:
            elements.append(atom_name.replace(" ", ""))
        return elements

    @staticmethod
    def get_formula(atom_names_dictionary):
        formula = ''
        for atom_name in atom_names_dictionary:
            formula += atom_name.replace(' ', '') + str(atom_names_dictionary[atom_name])
        return formula

    def get_potcar(self, child):
        """
        parse the potcar information

        - {'labels': ['O', 'Sr_sv'], 'pot_type': 'paw', 'functional': 'pbe'}
        - ['PAW_PBE', 'N', '08Apr2002']
        """
        pseudo = {'labels': [], 'pot_type': [], 'functional': []}
        potcar_symbol = []
        valence = []
        mass = []
        for i in child.iterchildren():
            if i.tag == "array" and i.attrib.get("name") == 'atomtypes':
                ll = list(i.iter('c'))
                for i in range(3, len(ll), 5):
                    valence.append(float(ll[i].text))

                for i in range(2, len(ll), 5):
                    mass.append(float(ll[i].text))

                for i in range(4, len(ll), 5):
                    text = ll[i].text.split()
                    label = text[1]
                    pot = text[0].split('_')[0]
                    try:
                        xc = text[0].split('_')[1]
                    except IndexError:
                        xc = 'unknown'
                    pseudo['labels'].append(label)
                    pseudo['pot_type'].append(pot)
                    pseudo['functional'].append(xc)
                    potcar_symbol.append(xc + ' ' + label)
        return pseudo, potcar_symbol, valence, mass

    @staticmethod
    def parse_name_array(atominfo):
        atom_names = []
        for array in atominfo.findall("array"):
            if array.attrib["name"] == "atoms":
                atom_names = [rc.find("c").text.strip() for rc in array.find("set")]

        if not atom_names:
            raise ValueError("No atomname found in file")

        return atom_names

    def parse_parameters(self, child):
        parameters = {}
        for i in child:
            if i.tag == "separator":
                name = i.attrib.get("name")
                d = self.parse_i_tag_collection(i)
                parameters[name] = d
                for ii in i:
                    if ii.tag == "separator":
                        name2 = ii.attrib.get("name")
                        d2 = self.parse_i_tag_collection(ii)
                        parameters[name][name2] = d2
        return parameters

    def parse_eigenvalue(self, eigenvalue):
        eigenvalues = []
        for s in eigenvalue.find("array").find("set").findall("set"):
            for ss in s.findall("set"):
                eigenvalues.append(self.parse_varray_pymatgen(ss))
        return eigenvalues

    def parse_dos(self, dos):
        t_dos = []
        p_dos = []
        for s in dos.find("total").find("array").findall("set"):
            for ss in s.findall("set"):
                t_dos.append(self.parse_varray_pymatgen(ss))
        if dos.find("partial") is not None:
            if len(dos.find("partial")) > 0:
                for s in dos.find("partial").find("array").findall("set"):
                    for i, ss in enumerate(s.findall("set")):
                        p = []
                        for sss in ss.findall("set"):
                            p.append(self.parse_varray_pymatgen(sss))
                        p_dos.append(p)

        return t_dos, p_dos

    def parse_projected(self, proj):
        projected = []
        for s in proj.find("array").find("set").findall("set"):
            for ss in s.findall("set"):
                p = []
                for sss in ss.findall("set"):
                    p.append(self.parse_varray_pymatgen(sss))
                projected.append(p)

        return projected

    def parse_calculation(self, calculation):
        stress = []
        force = []
        efermi = 0.0
        eigenvalues = []
        energy = 0.0
        scf_count = 0
        tdos = []
        pdos = []
        born_chgs = []
        hessian = []
        dyn_eigenvalues = []
        dyn_eigenvectors = []
        epsilon_ion = []
        epsilon_ = []
        proj = []
        pion = []
        psp1 = []
        psp2 = []
        pelc = []

        for i in calculation.iterchildren():
            if i.attrib.get("name") == "stress":
                stress = self.parse_varray(i)
            elif i.attrib.get("name") == "forces":
                force = self.parse_varray(i)
            elif i.tag == "dos":
                for j in i.findall("i"):
                    if j.attrib.get("name") == "efermi":
                        efermi = float(j.text)
                        break
                tdos, pdos = self.parse_dos(i)
            elif i.tag == "projected":
                proj = self.parse_projected(i)
            elif i.tag == "eigenvalues":
                eigenvalues = self.parse_eigenvalue(i)
            elif i.tag == "scstep":
                for j in i.iterchildren():
                    if j.tag == 'energy':
                        for e in j.findall("i"):
                            if e.attrib.get("name") == "e_fr_energy":
                                scf_count += 1

            elif i.tag == "energy":
                for e in i.findall("i"):
                    if e.attrib.get("name") == "e_fr_energy":
                        try:
                            energy = float(e.text)
                        except ValueError:
                            energy = 1000000000
                    else:
                        Warning("No e_fr_energy found in <calculation><energy> tag, energy set to 0.0")
            elif i.tag == "array" and i.attrib.get("name") == "born_charges":
                born_chgs = self.parse_born_chg(i)
            elif i.tag == "varray" and i.attrib.get("name") == "epsilon_ion":
                epsilon_ion = self.parse_varray(i)

            elif i.tag == "dynmat":
                hessian, dyn_eigenvalues, dyn_eigenvectors = self.parse_dynmat(i)

            elif i.tag == "v":
                if i.attrib.get("name") == "PION":
                    pion = self.parse_v(i)
                elif i.attrib.get("name") == "PSP1":
                    psp1 = self.parse_v(i)
                elif i.attrib.get("name") == "PSP2":
                    psp2 = self.parse_v(i)
                elif i.attrib.get("name") == "PELC":
                    pelc = self.parse_v(i)

        calculation = {}
        calculation["stress"] = stress
        calculation["efermi"] = efermi
        calculation["force"] = force
        calculation["eband_eigenvalues"] = eigenvalues
        calculation["energy"] = energy
        calculation["tdos"] = tdos
        calculation["pdos"] = pdos
        calculation["projected"] = proj
        calculation["born_charges"] = born_chgs
        calculation["hessian"] = hessian
        calculation["normal_modes_eigenvalues"] = dyn_eigenvalues
        calculation["normal_modes_eigenvectors"] = dyn_eigenvectors
        calculation["epsilon_ion"] = epsilon_ion
        calculation["pion"] = pion
        calculation["psp1"] = psp1
        calculation["psp2"] = psp2
        calculation["pelc"] = pelc
        return calculation, scf_count

    def parse_kpoints(self, kpoints):
        kpoints_dict = {'list': [], 'weights': [], 'divisions': [], 'mesh_scheme': ''}

        for i in kpoints.iterchildren():
            if i.tag == 'generation':
                kpoints_dict['mesh_scheme'] = i.attrib.get('param')
                for j in i.iterchildren():
                    if j.attrib.get("name") == 'divisions':
                        kpoints_dict['divisions'] = [int(number) for number in j.text.split()]
                        break

        for va in kpoints.findall("varray"):
            name = va.attrib["name"]
            if name == "kpointlist":
                kpoints_dict['list'] = self.parse_varray(va)
            elif name == "weights":
                kpoints_dict['weights'] = self.parse_varray(va)

        return kpoints_dict

    def get_bands(self):
        """
        Function for computing the valence band index from the count of electrons

        Args:
            None

        Returns:
            bands: an integer number
            occupy: bool number
        """
        valence = self.values['valence']
        composition = self.values['composition']
        total = int(self.values['parameters']['electronic']['NELECT'])

        # if self.spin:
        #    fac = 1
        # else:
        #    fac = 2
        fac = 2

        if total % 2 == 0:
            IBAND = int(total / fac)
            occupy = True
        else:
            IBAND = int(total / fac) + 1
            occupy = False

        self.values["bands"] = IBAND
        self.values["occupy"] = occupy

    @staticmethod
    def get_cbm(kpoints, efermi, eigens, IBAND):
        ind = np.argmin(eigens[:, IBAND, 0])
        pos = kpoints[ind]
        value = eigens[ind, IBAND, 0] - efermi
        return {'kpoint': pos, 'value': value}

    @staticmethod
    def get_vbm(kpoints, efermi, eigens, IBAND):
        ind = np.argmax(eigens[:, IBAND, 0])
        pos = kpoints[ind]
        value = eigens[ind, IBAND, 0] - efermi
        return {'kpoint': pos, 'value': value}

    def get_band_gap(self):
        self.get_bands()
        IBAND = self.values['bands']
        occupy = self.values['occupy']
        self.values['metal'] = False
        self.values['gap'] = None
        self.values['cbm'] = None
        self.values['vbm'] = None
        if occupy is True:
            efermi = self.values["calculation"]["efermi"]
            eigens = np.array(self.values['calculation']['eband_eigenvalues'])
            kpoints = np.array(self.values['kpoints']['list'])
            if np.shape(eigens)[0] > np.shape(kpoints)[0]:
                kpoints = np.tile(kpoints, [2, 1])

            cbm = self.get_cbm(kpoints, efermi, eigens, IBAND)
            vbm = self.get_vbm(kpoints, efermi, eigens, IBAND - 1)
            self.values['gap'] = cbm['value'] - vbm['value']
            self.values['cbm'] = cbm
            self.values['vbm'] = vbm
            if self.values['gap'] < 0:
                self.values['metal'] = True
                self.values['gap'] = 0
        else:
            self.values['metal'] = True
            self.values['gap'] = 0

    def eigenvalues_by_band(self, band=0):
        efermi = self.values["calculation"]["efermi"]
        eigens = np.array(self.values['calculation']['eband_eigenvalues'])
        return eigens[:, band, 0] - efermi

    def show_eigenvalues_by_band(self, bands=None):
        if bands is None:
            bands = [0]
        kpts = self.values['kpoints']['list']
        col_name = {'K-points': kpts}
        for band in bands:
            eigen = self.eigenvalues_by_band(band)
            if self.spin:
                eigens = np.reshape(eigen, [int(len(eigen) / 2), 2])
                name1 = 'band' + str(band) + 'up'
                name2 = 'band' + str(band) + 'down'
                col_name[name1] = eigens[:, 0]
                col_name[name2] = eigens[:, 1]
            else:
                name = 'band' + str(band)
                col_name[name] = eigen
        df = pd.DataFrame(col_name)
        print(df)

    def export_incar(self, filename=None, print_incar=True):
        """export incar"""
        contents = []
        for key in self.values['incar'].keys():
            content = key + ' = ' + str(self.values['incar'][key])
            content += '\n'
            contents.append(str(content))
        if filename is not None:
            with open(filename, 'w') as f:
                f.writelines(contents)
        elif print_incar:
            print(contents)
        self.incar = contents

    def export_kpoints(self, filename=None):
        """export kpoints"""
        contents = ['KPOINTS\n']
        contents += str(len(self.values['kpoints']['list'])) + '\n'
        contents += ['Cartesian\n']
        for kpt, wt in zip(self.values['kpoints']['list'], self.values['kpoints']['weights']):
            content = "{:10.4f} {:10.4f} {:10.4f} {:10.4f}".format(kpt[0], kpt[1], kpt[2], wt[0])
            if filename is None:
                print(content)
            else:
                content += '\n'
                contents.append(str(content))
        if filename is not None:
            with open(filename, 'w') as f:
                f.writelines(contents)

    def export_poscar(self, filename):
        """
        export poscar

        Args:
            filename: string
        Returns:
            a POSCAR file
        """

        comp = self.values["composition"]
        atomNames = self.values["name_array"]
        latt = self.values["finalpos"]["basis"]
        pos = self.values["finalpos"]["positions"]

        with open(filename, 'w') as f:
            string = ''
            for key in comp.keys():
                string += key
                string += str(comp[key])
            string += '\n'
            f.write(string)
            f.write('1.0\n')
            f.write('{:12.6f} {:12.6f} {:12.6f}\n'.format(latt[0][0], latt[0][1], latt[0][2]))
            f.write('{:12.6f} {:12.6f} {:12.6f}\n'.format(latt[1][0], latt[1][1], latt[1][2]))
            f.write('{:12.6f} {:12.6f} {:12.6f}\n'.format(latt[2][0], latt[2][1], latt[2][2]))
            for key in comp.keys():
                f.write('{:4s}'.format(key))
            f.write('\n')
            for key in comp.keys():
                f.write('{:4d}'.format(comp[key]))
            f.write('\n')
            f.write('Direct\n')
            for coor in pos:
                f.write('{:12.6f} {:12.6f} {:12.6f}\n'.format(coor[0], coor[1], coor[2]))

    def parse_bandpath(self):
        kpts = self.values['kpoints']['list']
        rec_basis = np.array(self.values['finalpos']['rec_basis'])

        def inline(kpt, path):
            if len(path) < 2:
                return True
            else:
                v1 = np.array(kpt) - np.array(path[-1])
                v2 = np.array(path[-1]) - np.array(path[-2])
                v1_norm = np.linalg.norm(v1)
                v2_norm = np.linalg.norm(v2)
                if v1_norm < 1e-3:
                    return False
                else:
                    cos = np.dot(v1, v2) / v1_norm / v2_norm
                    if abs(cos - 1) < 1e-2:
                        return True
                    else:
                        # print(kpt, path[-2], path[-1], angle, np.dot(v1, v2)/v1_norm/v2_norm)
                        return False

        paths = []
        path = []
        for i, kpt in enumerate(kpts):
            if inline(kpt, path):
                path.append(kpt)
                if i == len(kpts) - 1:
                    paths.append(path)
            else:
                paths.append(path)
                path = []
                path.append(kpt)

        band_points = []
        pointer = 0
        for i, path in enumerate(paths):
            path = np.array(path)
            dist = np.linalg.norm(np.dot(path[0, :] - path[-1, :], rec_basis))
            x = np.linspace(pointer, pointer + dist, len(path[:, 0]))
            if i == 0:
                band_paths = x
            else:
                band_paths = np.hstack((band_paths, x))
            pointer += dist
            band_points.append(pointer)

        self.values['band_paths'] = band_paths
        self.values['band_points'] = band_points

    def plot_band(self, ax=None, filename=None, style='normal', ylim=[-25, 10],
                  xlim=None, plim=[0.0, 0.5], labels=None, saveBands=False, dpi=300):
        """
        plot the bandstructure

        Args:
            filename: string
            styles: string (`normal` or `projected`)
            ylim: list, the range of energy values on the y-axis, e.g. [-5, 3]
            xlim: list, the range of values on the x-axis (optional)
            plim: float (the ratio of color plot in the `projected` mode)

        Returns:
            A figure with band structure
        """
        if ax is None: fig, ax = plt.subplots()

        self.parse_bandpath()
        efermi = self.values["calculation"]["efermi"]
        eigens = np.array(self.values['calculation']['eband_eigenvalues'])
        paths = self.values['band_paths']
        band_pts = self.values['band_points']
        proj = np.array(self.values["calculation"]["projected"])  # [N_kpts, N_band, Ions, 9]
        cm = plt.cm.get_cmap('RdYlBu')
        nkpt, nband, nocc = np.shape(eigens)
        for i in range(nband):
            band = eigens[:, i, 0] - efermi
            if np.all(band < ylim[0]) or np.all(band > ylim[1]):
                continue
            p = np.empty([len(paths)])
            for kpt, _ in enumerate(paths):
                p[kpt] = np.sum(proj[kpt, i, :, :])
            if len(band) / len(paths) == 2:
                ax.plot(paths, band[:len(paths)], c='black', lw=1.0)
                ax.plot(paths, band[len(paths):], c='red', lw=1.0)
            else:
                ax.plot(paths, band, c='black', lw=1.0)
            if style == 'projected':
                p[p < plim[0]] = plim[0]
                p[p > plim[1]] = plim[1]
                ax.scatter(paths, band, c=p, vmin=plim[0], vmax=plim[1], cmap=cm, s=10)
                if saveBands:
                    np.savetxt('band%04d.dat' % i, np.transpose([band, p]))
            else:
                if saveBands:
                    np.savetxt('band%04d.dat' % i, band)

        for pt in band_pts:
            ax.axvline(x=pt, ls='-', color='k', alpha=0.5)

        if style == 'projected':
            cbar = plt.colorbar(orientation='horizontal',
                                ticks=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
                                )
            cbar.set_label('ratio of projected DOS')  # , fontsize=12)

        ax.set_ylabel("Energy (eV)")
        ax.set_ylim(ylim)

        # Set xlim if provided
        if xlim is not None:
            ax.set_xlim(xlim)
        else:
            ax.set_xlim([0, paths[-1]])

        ax.set_xticks([])

        # Manually setup the xlabels
        if labels is not None:
            xticks = [0] + band_pts
            print('ticks', xticks)
            print('labels', labels)
            ax.set_xticks(xticks)
            ax.set_xticklabels(labels)

        if filename is None:
            return ax  # plt.show()
        else:
            plt.savefig(filename, dpi=dpi)

    def get_dos(self, rows, style='t'):

        mydos = []
        labels = []
        a_array = self.values["name_array"]
        N_atom = len(a_array)
        tdos = np.array(self.values['calculation']['tdos'])
        pdos = np.array(self.values['calculation']['pdos'])
        a, b, c, d = np.shape(pdos)
        pdos = np.reshape(pdos, [b, a, c, d])
        if style == 't':
            for spin in tdos:
                mydos.append(spin[rows, 1])
                labels.append('Total')

        elif style in ['s', 'p', 'd']:
            for spin in pdos:
                spd = spin[0, :, :]
                for i in range(1, N_atom):
                    spd += spin[i, :, :]

                if style == 's':
                    mydos.append(spd[rows, 1])
                elif style == 'p':
                    mydos.append(spd[rows, 2] + spd[rows, 3] + spd[rows, 4])
                else:
                    mydos.append(spd[rows, 5] + spd[rows, 6] + spd[rows, 7] + spd[rows, 8] + spd[rows, 9])
                labels.append(style)

        # element based
        elif style[0] == 'a':
            if style[1].isdigit():
                ids = style[1].split('-')
                start, end = int(ids[0]), int(ids[1])
                ids = range(start, end + 1)
            else:
                ele = style[1:]
                ids = []
                for i in range(N_atom):
                    if ele == a_array[i]:
                        ids.append(i)
            for spin in pdos:
                spd = spin[ids[0], :, :]
                for i in ids[1:]:
                    spd += spin[i, :, :]
                mydos.append(spd[rows, 1] + spd[rows, 2] + spd[rows, 3] + spd[rows, 4] + \
                             spd[rows, 5] + spd[rows, 6] + spd[rows, 7] + spd[rows, 8] + spd[rows, 9])
                labels.append(style[1:])

        if len(labels) == 2:
            labels[0] += '-up'
            labels[1] += '-down'
            mydos[1] *= -1
        return mydos, labels

    def plot_dos(self, ax=None, filename=None, smear=None, flip=False,
                 style='t', xlim=None, ylim=None, dos_range=[0, None], dpi=300):
        """
        plot the DOS

        Args:
            ax: default None
            filename: string
            styles: string (`t` or `s` or `t+spd`)
            xlim: list, the range of energy values on the x-axis, e.g. [-5, 3]
            ylim: list, the range of DOS values on the y-axis (optional)
            smear: float (the width of smearing, default: None)
            flip: whether or not flip the x/y

        Returns:
            A figure with band structure
            :param dos_range:
        """
        if ylim is None:
            ylim = [None, None]
        if xlim is None:
            xlim = [None, None]
        efermi = self.values['calculation']['efermi']
        tdos = np.array(self.values['calculation']['tdos'][0])
        tdos[:, 0] -= efermi
        e = tdos[:, 0]

        # Automatically determine xlim if not provided
        if xlim == [None, None]:  # If no xlim provided
            xlim = [min(e), max(e)]
        elif None in xlim:  # Partially provided xlim
            x_min = xlim[0] if xlim[0] is not None else min(e)
            x_max = xlim[1] if xlim[1] is not None else max(e)
            xlim = [x_min, x_max]

        rows = (e > xlim[0]) & (e < xlim[1])
        e = e[rows]
        plt_obj = {}
        options = []
        for option in style.split('+'):
            if option == 'spd':
                options.extend(['s', 'p', 'd'])
            elif option == 'a':
                for ele in self.values['elements']:
                    options.append('a' + ele)
            else:
                options.append(option)
        for style in options:
            mydos, labels = self.get_dos(rows, style)
            for data, label in zip(mydos, labels):
                plt_obj[label] = data

        if ax is None: fig, ax = plt.subplots()

        lines1 = []
        lines2 = []
        labels1 = []
        labels2 = []
        all_y_values = []  # Collect all y-values for ylim determination

        for label in plt_obj.keys():
            e = np.reshape(e, [len(e), 1])
            data = np.reshape(plt_obj[label], [len(e), 1])
            if smear is not None:
                print("Apply smear", smear)
                data = np.hstack((e, data))
                data = smear_data(data, smear)
                data = data[:, 1]

            all_y_values.extend(data.flatten())  # Add data for ylim calculation

            ls = '-' if label == 'Total' else '--'
            if label.find('down') > 0:
                if flip:
                    lines2 += ax.plot(data, e, ls=ls)
                else:
                    lines2 += ax.plot(e, data, ls=ls)
                labels2.append(label)
            else:
                if flip:
                    lines1 += ax.plot(data, e, ls=ls)
                else:
                    lines1 += ax.plot(e, data, ls=ls)
                labels1.append(label)

        leg1 = ax.legend(lines1, [label for label in labels1],
                         fancybox=True,
                         loc='upper right')

        leg1.get_frame().set_alpha(0.5)
        if len(lines2) > 0:
            from matplotlib.legend import Legend
            leg2 = Legend(ax, lines2, [label for label in labels2],
                          fancybox=True, loc='lower right')
            ax.add_artist(leg2)
            leg2.get_frame().set_alpha(0.5)

        if flip:
            ax.set_xlabel("DOS (States/eV)")
            ax.set_ylim(xlim)
            x_min, x_max = ax.get_xlim()
            if dos_range[0] is not None: x_min = dos_range[0]
            if dos_range[1] is not None: x_max = dos_range[1]
            ax.set_xlim(x_min - 1, x_max + 1)
        else:
            ax.set_xlabel("Energy (eV)")
            ax.set_ylabel("DOS")
            ax.set_xlim(xlim)

            # Automatically set ylim based on data range
            if ylim == [None, None]:  # If no ylim provided
                y_min, y_max = min(all_y_values) - 1, max(all_y_values) + 1
            else:  # Use provided limits if specified
                y_min, y_max = ylim
                if y_min is None: y_min = min(all_y_values) - 1
                if y_max is None: y_max = max(all_y_values) + 1
            ax.set_ylim(y_min, y_max)

        if filename is None:
            return ax
        else:
            plt.savefig(filename, dpi=dpi)

    def plot_band_dos(self, filename=None, band_style='normal', dos_style='t+a', smear=None,
                      e_range=[-10, 3], dos_max=None, plim=[0.0, 0.5],
                      band_labels=None, figsize=(16, 9), dpi=300):
        """
        Plot band structure and density of states (DOS) with the specified settings.

        Args:
            filename (str): Path to save the plot (optional).
            band_style (str): Style of band plot.
            dos_style (str): Style of DOS plot.
            smear (float): Smearing factor for DOS.
            e_range (list): Energy range [min, max].
            dos_max (float): Maximum value for DOS.
            plim (list): Plot limits for DOS.
            band_labels (list): Labels for high-symmetry points in band structure.
            figsize (tuple): Figure size in inches. Default is (16, 9) for 1920x1080 pixels.
            dpi (int): Dots per inch for the plot resolution. Default is 120 for moderate quality.
        """

        fig = plt.figure(figsize=figsize)
        gs = gridspec.GridSpec(1, 2, width_ratios=[2, 1])
        ax1 = plt.subplot(gs[0])
        ax1 = self.plot_band(ax1, style=band_style, ylim=e_range, plim=plim, labels=band_labels)
        ax2 = plt.subplot(gs[1])
        ax2 = self.plot_dos(ax2, style=dos_style, smear=smear, xlim=e_range, dos_range=[0, dos_max], flip=True)
        plt.savefig(filename, dpi=dpi)


class IR:
    """
    A class to compute the IR intensity
    """

    def __init__(self, born_chgs, eigenvalues, eigenvectors, mass, vol):
        self.born_chgs = np.array(born_chgs)
        self.modes = eigenvectors
        self.freqs = eigenvalues
        self.Natom = len(born_chgs)
        IRs = []
        epsilons = []
        for mode, freq in zip(self.modes, self.freqs):
            IRx, IRy, IRz = 0, 0, 0
            mode = np.reshape(mode, [self.Natom, 3])
            for i in range(self.Natom):
                for j in range(3):
                    IRx += mode[i, j] * self.born_chgs[i, j, 0]
                    IRy += mode[i, j] * self.born_chgs[i, j, 1]
                    IRz += mode[i, j] * self.born_chgs[i, j, 2]
            IR = IRx ** 2 + IRy ** 2 + IRz ** 2
            IRs.append(IR)
            if abs(IR) > 1e-2 and abs(freq) > 5e-3:
                # IR active, compute the epsilon
                epsilons.append(compute_epsilon_by_modes(mode, freq, self.born_chgs, vol, mass))
            else:
                epsilons.append(np.zeros([3, 3]).flatten())
                # print('IR inactive, skip this mode')
        self.IRs = np.array(IRs)
        self.epsilons = epsilons

    def show(self):
        print("\n   Freq(cm-1)    IR Intensity     E_xx         E_yy         E_zz")
        for ir, freq, eps in zip(self.IRs, self.freqs, self.epsilons):
            # Checking the eps size to avoid errors
            if isinstance(eps, np.ndarray) and eps.size >= 9:
                print("{:12.3f} {:12.3f} {:12.3f} {:12.3f} {:12.3f}".format(
                    freq * units.ev2cm, ir, eps[0], eps[4], eps[8]))
            else:
                print("{:12.3f} {:12.3f} {:>12s} {:>12s} {:>12s}".format(
                    freq * units.ev2cm, ir, 'N/A', 'N/A', 'N/A'))

        # Summation of epsilon with verification
        try:
            eps_sum = np.sum(self.epsilons, axis=0)
            if eps_sum.size >= 9:
                print("{:25s} {:12.3f} {:12.3f} {:12.3f}".format('Total', eps_sum[0], eps_sum[1], eps_sum[2]))
                print("{:25s} {:12.3f} {:12.3f} {:12.3f}".format('Total', eps_sum[3], eps_sum[4], eps_sum[5]))
                print("{:25s} {:12.3f} {:12.3f} {:12.3f}".format('Total', eps_sum[6], eps_sum[7], eps_sum[8]))
            else:
                print("Total epsilon data unavailable or malformed.")
        except Exception as e:
            print(f"Error during epsilon summation: {e}")


def compute_epsilon_by_modes(mode, freq, z, V, mass):
    """Compute the epsilon for the given mode"""
    # transform all units to hartree
    freq = freq / units.ev2hartree
    V = V / (units.a2bohr ** 3)  # bohr
    # mass = mass*units.proton_mass

    # compute the mode effiective charge tensors Z* (3 component)
    zt = np.zeros(3)
    for alpha in range(3):
        for beta in range(3):
            for i in range(len(z)):
                zt[alpha] += z[i, alpha, beta] * mode[i, beta] / np.sqrt(mass[i])
                # zt[alpha] += z[i, alpha, beta] * mode[i, beta]
                # zt[alpha] += z[i, alpha, beta] * mode[i, beta] / mass[i]
    epsilon = np.zeros([3, 3])
    # compute the epsilon
    for alpha in range(3):
        for beta in range(3):
            epsilon[alpha, beta] = zt[alpha] * zt[beta] / ((freq) ** 2)
    factor = 4 * units.pi / V / units.proton_mass
    epsilon *= factor
    return epsilon.flatten()


def safe_compute_epsilon_by_modes(mode, freq, z, V, mass):
    """
    A secure call to compute_epsilon_by_modes with input data validation.
    """
    # Checking the availability of data
    if mode is None:
        raise ValueError("The 'mode' parameter (eigenvector) is missing.")
    if freq is None:
        raise ValueError("The 'freq' parameter (mode frequency) is missing.")
    if z is None:
        raise ValueError("The 'z' parameter (Born charges) is missing.")
    if V is None or V <= 0:
        raise ValueError("The parameter 'V' (cell volume) is missing or incorrect.")
    if mass is None or len(mass) == 0:
        raise ValueError("The 'mass' parameter is missing.")

    # All parameters are correct, we call the main function
    return compute_epsilon_by_modes(mode, freq, z, V, mass)