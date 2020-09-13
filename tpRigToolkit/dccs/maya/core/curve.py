#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions to handle curve related data in Maya
"""

import os
import logging

import tpDcc as tp
from tpDcc.libs.python import python, folder, fileio, path as path_utils
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import api, shape as shape_utils

from tpRigToolkit.core import utils
from tpRigToolkit.dccs.maya.data import curves

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class CurveToData(object):
    def __init__(self, curve):
        curve_shapes = self._get_shapes(curve)
        self._curves = list()
        self._curve_mobjects = list()
        self._curve_functions = list()

        for curve_shape in curve_shapes:
            if not curve_shape:
                LOGGER.warning('{} is not a NURBS curve'.format(curve_shape))
                continue
            self._curves.append(curve_shape)
            self._curve_mobjects.append(api.node_name_to_mobject(curve_shape))
            self._curve_functions.append(api.NurbsCurveFunction(self._curve_mobjects[-1]))

    def _get_shapes(self, curve):
        """
        Internal function that returns a list of all the shapes that are part of the curve
        :param curve: str
        :return: list(str)
        """

        curves = python.force_list(curve)
        curve_shapes = list()
        for curve in curves:
            if not tp.Dcc.node_type(curve) == 'nurbsCurve':
                shapes = tp.Dcc.list_shapes(curve, full_path=True) or list()
                for shape in shapes:
                    if tp.Dcc.node_type(shape) == 'nurbsCurve':
                        if not tp.Dcc.get_attribute_value(shape, 'intermediateObject'):
                            curve_shapes.append(shape)

        return curve_shapes

    def get_degree(self, index=0):
        """
        Returns the degree of the curve in given index
        :param index: int, shape index starting from 0.
        :return: int, number of degrees
        """

        return self._curve_functions[index].get_degree()

    def get_knots(self, index=0):
        """
        Returns CV knots of the curve in given index
        :param index: int, shape index starting from 0
        :return: list(str), list of knots
        """

        return self._curve_functions[index].get_knot_values()

    def get_cvs(self, index=0):
        """
        Returns list of all CVs of the curve in given index
        :param index: int, shape index starting from 0
        :return: list(float)
        """

        return_value = list()

        cvs = self._curve_functions[index].get_cv_positions()
        for cv in cvs:
            return_value.append(cv[0])
            return_value.append(cv[1])
            return_value.append(cv[2])

        return return_value

    def get_cv_count(self, index=0):
        """
        Returns the total number of CVs in given shape index
        :param index: int, shape index starting from 0
        :return: int
        """

        return self._curve_functions[index].get_cv_count()

    def get_span_count(self, index=0):
        """
        Returns the total number of spans in given shape index
        :param index: int, shape index starting from 0
        :return: int
        """

        return self._curve_functions[index].get_span_count()

    def get_form(self, index=0):
        """
        Returns the form of the curve in given shape index
        :param index: int, shape index startin from 0
        :return: int
        """

        return self._curve_functions[index].get_form() - 1

    def create_curve_list(self):

        curve_arrays = list()

        for i in range(len(self._curves)):
            nurbs_curved_array = list()
            knots = self.get_knots(i)
            cvs = self.get_cvs(i)
            nurbs_curved_array.append(self.get_degree(i))
            nurbs_curved_array.append(self.get_span_count(i))
            nurbs_curved_array.append(self.get_form(i))
            nurbs_curved_array.append(0)
            nurbs_curved_array.append(3)
            nurbs_curved_array.append(len(knots))
            nurbs_curved_array += knots
            nurbs_curved_array.append(self.get_cv_count(i))
            nurbs_curved_array += cvs
            curve_arrays.append(nurbs_curved_array)

        return curve_arrays

    def create_mel_list(self):
        mel_curve_data_list = list()

        curve_arrays = self.create_curve_list()
        for curve_array in curve_arrays:
            mel_curve_data = ''
            for nurbs_data in curve_array:
                mel_curve_data += ' {}'.format(nurbs_data)
            mel_curve_data_list.append(mel_curve_data)

        return mel_curve_data_list


class CurveDataInfo(object):
    def __init__(self, extension=None):
        self._libraries = dict()
        self._library_curves = dict()
        self._active_library = None
        self._curves_data_path = None

        extension = extension or '.curves'
        if not extension.startswith('.'):
            extension = '.{}'.format(extension)
        self._extension = extension

        self._load_libraries()
        self._initialize_library_curve()

    # ==============================================================================================
    # PROPERTIES
    # ==============================================================================================

    @property
    def active_library(self):
        return self._active_library

    @active_library.setter
    def active_library(self, active_library):
        self._active_library = active_library

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_directory(self, directory_path):
        self._curves_data_path = directory_path
        self._libraries = dict()
        self._load_libraries()
        self._library_curves = dict()
        self._initialize_library_curve()

    def get_active_library(self):
        return self._active_library

    def set_active_library(self, library_name, skip_extension=False):
        if not skip_extension:
            file_name = '{}{}'.format(library_name, self._extension)
        else:
            file_name = library_name

        library_path = fileio.create_file(file_name, self._curves_data_path)
        self._active_library = library_name
        self._library_curves[library_name] = dict()
        if skip_extension:
            self.load_data_file(library_path)
        else:
            self.load_data_file()

    def get_library_names(self):
        return self._libraries.keys()

    def get_curve_names(self):
        if not self._active_library:
            LOGGER.warning('Must set active library before running this function')
            return

        return self._library_curves[self._active_library].keys()

    def load_data_file(self, file_path=None):
        if not self._active_library:
            LOGGER.warning('Must set active library before running this function.')
            return
        if not file_path:
            file_path = path_utils.join_path(
                self._curves_data_path, '{}{}'.format(self._active_library, self._extension))

        last_line_curve = False
        curve_name = ''
        curve_data = ''
        curve_type = ''
        curve_data_lines = list()

        read_file = fileio.FileReader(file_path)
        data_lines = read_file.read()
        for line in data_lines:
            if line.startswith('->'):
                if curve_data_lines:
                    self._library_curves[self._active_library][curve_name] = [curve_data_lines, curve_type]
                    curve_type = ''
                    curve_name = ''
                    curve_data = ''
                line_split = line.split()
                curve_name = line_split[1]
                if len(line_split) > 2:
                    curve_type = line_split[2]
                    if not curve_type:
                        curve_type = ''
                curve_name = curve_name.strip()
                last_line_curve = True
                curve_data_lines = list()
            if not line.startswith('->') and last_line_curve:
                line = line.strip()
                if line:
                    curve_data = line
                    curve_data = curve_data.strip()
                    curve_data_lines.append(curve_data)

        if curve_data_lines:
            self._library_curves[self._active_library][curve_name] = [curve_data_lines, curve_type]

    def write_data_to_file(self):
        if not self._active_library:
            LOGGER.warning('Must set active library before running this function')
            return

        file_path = path_utils.join_path(self._curves_data_path, '{}{}'.format(self._active_library, self._extension))
        write_file = fileio.FileWriter(file_path)
        current_library = self._library_curves[self._active_library]
        lines = list()
        curves = current_library.keys()
        curves.sort()
        for curve in curves:
            curve_data_lines, curve_type = current_library[curve]
            if not curve_type:
                if tp.Dcc.attribute_exists(curve, 'curveType'):
                    curve_type = tp.Dcc.get_attribute_value(curve, 'curveType')
            if curve != curve_type:
                lines.append('-> {} {}'.format(curve, curve_type))
            if curve == curve_type:
                lines.append('-> {}'.format(curve))

            for curve_data in curve_data_lines:
                lines.append('{}'.format(curve_data))

        write_file.write(lines)

        return file_path

    def set_shape_to_curve(self, curve, curve_in_library, check_curve=False, add_curve_type_attribute=True):
        if not self._active_library:
            LOGGER.warning('Must set active library before running this function')
            return

        mel_data_list, original_curve_type = self._get_curve_data(curve_in_library, self._active_library)
        if not mel_data_list:
            return
        curve_type_value = self._get_curve_type(curve)
        if not curve_type_value or not maya.cmds.objExists(curve_type_value):
            curve_type_value = curve_in_library

        if check_curve:
            is_curve = self._is_curve_of_type(curve, curve_in_library)
            if not is_curve:
                return

        self._match_shapes_to_data(curve, mel_data_list)

        if mel_data_list:
            set_nurbs_data_mel(curve, mel_data_list)

        shape_utils.rename_shapes(curve)

        if add_curve_type_attribute:
            self._set_curve_type(curve, curve_type_value)

    def add_curve(self, curve, library_name=None):
        if not curve:
            return
        if library_name:
            self.set_active_library(library_name)
        else:
            library_name = self._active_library
            if not self._active_library:
                LOGGER.warning('Must set active library before running this function')
                return

        mel_data_list = self._get_mel_data_list(curve)
        curve_type = curve
        if tp.Dcc.attribute_exists(curve, 'curveType'):
            curve_type = tp.Dcc.get_attribute_value(curve, 'curveType')

        transform = self._get_curve_parent(curve)
        if library_name:
            self._library_curves[library_name][transform] = [mel_data_list, curve_type]

    def remove_curve(self, curve, library_name=None):
        if not curve:
            return False

        if not library_name:
            library_name = self._active_library
            if not self._active_library:
                LOGGER.warning('Must set active library before running this function')
                return False

        transform = self._get_curve_parent(curve)
        if library_name in self._library_curves:
            if transform in self._library_curves[library_name]:
                self._library_curves[library_name].pop(transform)
                return True

        return False

    def create_curve(self, curve_name):
        if not self._active_library:
            LOGGER.warning('Must set active library before running this function')
            return False

        curve_shape = tp.Dcc.create_node('nurbsCurve')
        parent = tp.Dcc.node_parent(curve_shape, full_path=False)
        parent = maya.cmds.rename(parent, curve_name)

        self.set_shape_to_curve(parent, curve_name)

        return parent

    def create_curves(self):
        if not self._active_library:
            LOGGER.warning('Must set active library before running this function')
            return False

        curves_dict = self._library_curves[self._active_library]
        keys = list(curves_dict)
        keys.sort()
        for key in keys:
            self.create_curve(key)

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _get_curves_data_path(self):
        current_path = curves.__path__[0]
        custom_curve_path = utils.get_custom('custom_curve_path')
        if custom_curve_path and os.path.isdir(custom_curve_path):
            curve_data = os.path.join(custom_curve_path)
            folder.create_folder(curve_data)
            LOGGER.info('Using custom curve directory: {}'.format(custom_curve_path))
            current_path = custom_curve_path

        self._curves_data_path = current_path

        return self._curves_data_path

    def _load_libraries(self):
        curves_data_path = self._curves_data_path or self._get_curves_data_path()
        files = os.listdir(curves_data_path)
        for filename in files:
            if filename.endswith(self._extension):
                split_file = filename.split('.')
                self._library_curves[split_file[0]] = filename

    def _initialize_library_curve(self):
        names = self.get_library_names()
        for name in names:
            self._library_curves[name] = dict()

    def _get_curve_data(self, curve_name, curve_library):
        curve_dict = self._library_curves[curve_library]
        if curve_name not in curve_dict:
            LOGGER.warning('{} is not in the curve library {}'.format(curve_name, curve_library))
            return None, None

        return curve_dict[curve_name]

    def _get_curve_parent(self, curve):
        parent = curve
        if tp.Dcc.object_exists(curve):
            if tp.Dcc.node_type(curve) == 'nurbsCurve':
                parent = tp.Dcc.node_parent(curve)
            else:
                parent = curve

        return parent

    def _get_mel_data_list(self, curve):
        curve_data = CurveToData(curve)
        mel_data_list = curve_data.create_mel_list()

        return mel_data_list

    def _get_curve_type(self, curve):
        curve_type_value = None
        if tp.Dcc.attribute_exists(curve, 'curveType'):
            curve_type_value = tp.Dcc.get_attribute_value(curve, 'curveType')

        return curve_type_value

    def _set_curve_type(self, curve, curve_type_value):
        create_curve_type_attribute(curve, curve_type_value)

    def _is_curve_of_type(self, curve, type_curve):
        mel_data_list, original_curve_type = self._get_curve_data(type_curve, self._active_library)
        if not mel_data_list:
            return False
        if not original_curve_type:
            return True
        curve_type_value = self._get_curve_type(curve)
        if curve_type_value and curve_type_value != original_curve_type:
            return False

        return True

    def _match_shapes_to_data(self, curve, data_list):

        found = list()

        shapes = get_shapes(curve)
        if not shapes:
            return

        shape_color = None
        if len(shapes):
            shape_color = tp.Dcc.get_attribute_value(shapes[0], 'overrideColor')
            shape_color_enabled = tp.Dcc.get_attribute_value(shapes[0], 'overrideEnabled')

        for shape in shapes:
            if tp.Dcc.node_type(shape) == 'nurbsCurve':
                found.append(shape)

        if len(found) > len(data_list):
            tp.Dcc.delete_object(found[len(data_list):])
        if len(found) < len(data_list):
            current_index = len(found)
            for i in range(current_index, len(data_list)):
                curve_shape = maya.cmds.createNode('nurbsCurve')
                if shape_color is not None and shape_color_enabled:
                    tp.Dcc.set_attribute_value(curve_shape, 'overrideEnabled', True)
                    tp.Dcc.set_attribute_value(curve_shape, 'overrideColor', shape_color)
                parent = tp.Dcc.node_parent(curve_shape)
                maya.cmds.parent(curve_shape, curve, r=True, s=True)
                tp.Dcc.delete_object(parent)


def get_shapes(transform):
    if shape_utils.is_a_shape(transform):
        parent = maya.cmds.listRelatives(transform, p=True, f=True)
        shapes = maya.cmds.listRelatives(parent, s=True, f=True, ni=True)
    else:
        shapes = maya.cmds.listRelatives(transform, s=True, f=True, ni=True)

    found = list()
    if not shapes:
        return found
    for shape in shapes:
        if maya.cmds.nodeType(shape) == 'nurbsCurve':
            found.append(shape)

    return found


def create_curve_type_attribute(node, value):
    if not tp.Dcc.attribute_exists(node, 'curveType'):
        tp.Dcc.add_string_attribute(node, 'curveType', lock=False)
    if value is not None and value != node:
        tp.Dcc.set_attribute_value(node, 'curveType', value)
    tp.Dcc.unlock_attribute(node, 'curveType')
    tp.Dcc.keyable_attribute(node, 'curveType')


def set_nurbs_data(curve, curve_data_array):
    maya.cmds.setAttr('{}.cc'.format(curve), *curve_data_array, type='nurbsCurve')


def set_nurbs_data_mel(curve, mel_curve_data):
    current_unit = maya.cmds.currentUnit(query=True)

    try:
        maya.cmds.currentUnit(linear='cm')
        shapes = get_shapes(curve)
        mel_curve_data = python.force_list(mel_curve_data)
        data_count = len(mel_curve_data)
        create_input = tp.Dcc.get_attribute_input('{}.create'.format(curve))
        if create_input:
            LOGGER.warning(
                '{} has history. Disconnecting create attribute on curve. This will allow CV position change'.format(curve))
            maya.cmds.disconnectAttr(create_input, '{}.create'.format(curve))

        for i in range(data_count):
            attribute = '{}.cc'.format(shapes[i])
            if i < data_count:
                maya.mel.eval('setAttr "{}" -type "nurbsCurve" {}'.format(attribute, mel_curve_data[i]))
    except Exception as exc:
        LOGGER.error('Error while setting NURBS MEL data: {}'.format(exc))
    finally:
        maya.cmds.currentUnit(linear=current_unit)


def get_library_shape_names():
    curve_info = CurveDataInfo()
    curve_info.set_active_library('default_curves')

    return curve_info.get_curve_names()


def add_curve_to_default(curve_name):
    """
    Adds a new curve to the default library.
    :param curve_name: str
    """

    curve_info = CurveDataInfo()
    curve_info.add_curve(curve_name, 'default_curves')
    curve_info.write_data_to_file()
