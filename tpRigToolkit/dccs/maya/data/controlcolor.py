#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Control color data implementation
"""

from __future__ import print_function, division, absolute_import

import logging
import traceback

import tpDcc as tp
from tpDcc.libs.python import fileio, python, path as path_utils
from tpDcc.dccs.maya.core import shape as shape_utils
from tpDcc.dccs.maya.data import base

from tpRigToolkit.core import data as rig_data
from tpRigToolkit.libs.controlrig.core import controllib
from tpRigToolkit.dccs.maya.data import controlcv

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class ControlColorFileData(base.MayaCustomData, object):
    def __init__(self, name=None, path=None):
        super(ControlColorFileData, self).__init__(name=name, path=path)

    @staticmethod
    def get_data_type():
        return 'maya.control_colors'

    @staticmethod
    def get_data_extension():
        return 'color'

    @staticmethod
    def get_data_title():
        return 'Control Colors'

    def get_file(self):
        directory = self.directory
        file_name = self._get_file_name()
        if self._sub_folder:
            directory = path_utils.join_path(self.directory, '.sub/{}'.format(self._sub_folder))
        file_path = fileio.create_file(file_name, directory)

        return file_path

    def export_data(self, file_path=None, comment='-', create_version=True, *args, **kwargs):
        if not tp.is_maya():
            LOGGER.warning('Data must be exported from within Maya!')
            return False

        file_path = self.get_file()
        if not file_path:
            return

        orig_controls = self._get_data(file_path)

        objects = kwargs.get('objects', list())
        # We make sure that we store the short name of the controls
        objects = [tp.Dcc.node_short_name(obj) for obj in objects]
        controls = objects or controllib.get_controls()
        if not controls:
            LOGGER.warning('No controls found to export.')
            return False
        valid_controls = list()
        for control in controls:
            if not controllib.is_control(control):
                continue
            valid_controls.append(control)
        if not valid_controls:
            LOGGER.warning('No valid controls found to export.')
            return False

        for control in valid_controls:
            color_dict = self._get_color_dict(control)
            if color_dict:
                orig_controls[control] = color_dict

        self._store_all_dict(orig_controls, file_path, comment)

        LOGGER.info('Exported {} data'.format(self.name))

        return True

    def import_data(self, file_path='', objects=None):
        if not tp.is_maya():
            LOGGER.warning('Data must be exported from within Maya!')
            return False

        file_path = file_path or self.get_file()
        all_control_dict = self._get_data(file_path)
        for control in all_control_dict:
            self._set_color_dict(control, all_control_dict[control])

        return True

    def get_curves(self, file_name=None):
        if not file_name:
            file_name = self.get_file()
        curve_dict = self._get_data(file_name)
        keys = curve_dict.keys()
        keys.sort()

        return keys

    def remove_curve(self, curve_name, file_name=None):
        file_name = file_name or self.get_file()
        curve_list = python.force_list(curve_name)
        curve_dict = self._get_data(file_name)
        for curve in curve_list:
            if curve in curve_dict:
                curve_dict.pop(curve)
        self._store_all_dict(curve_dict, file_name, comment='remove curves')

        return True

    def _get_data(self, file_name):
        lines = fileio.get_file_lines(file_name)
        all_controls_dict = dict()
        for line in lines:
            spilt_line = line.split('=')
            if len(spilt_line) == 2:
                color_dict = eval(spilt_line[1])
                control = spilt_line[0].strip()
                all_controls_dict[control] = color_dict

        return all_controls_dict

    def _store_all_dict(self, all_dict, file_name, comment):
        keys = list(all_dict.keys())
        keys.sort()
        lines = list()
        for key in keys:
            lines.append('{} = {}'.format(key, all_dict[key]))
        fileio.write_lines(file_name, lines)

        version = fileio.FileVersion(file_name)
        version.save(comment)

        return True

    def _get_color_dict(self, curve):
        if not tp.Dcc.object_exists(curve):
            return None

        sub_colors = list()
        main_color = None

        if tp.Dcc.get_attribute_value(curve, 'overrideEnabled'):
            main_color = tp.Dcc.get_attribute_value(curve, 'overrideColor')
            if tp.Dcc.attribute_exists(curve, 'overrideColorRGB'):
                curve_rgb = tp.Dcc.get_attribute_value(curve, 'overrideColorRGB')
                curve_rgb_state = tp.Dcc.get_attribute_value(curve, 'overrideRGBColors')
                main_color = [main_color, curve_rgb, curve_rgb_state]

        shapes = shape_utils.get_shapes(curve) or list()
        one_passed = False
        for shape in shapes:
            if tp.Dcc.get_attribute_value(shape, 'overrideEnabled'):
                one_passed = True
            curve_color = tp.Dcc.get_attribute_value(shape, 'overrideColor')
            if tp.Dcc.attribute_exists(shape, 'overrideColorRGB'):
                curve_rgb = tp.Dcc.get_attribute_value(shape, 'overrideColorRGB')
                curve_rgb_state = tp.Dcc.get_attribute_value(shape, 'overrideRGBColors')
                sub_colors.append([curve_color, curve_rgb, curve_rgb_state])
            else:
                sub_colors.append(curve_color)
        if not one_passed and main_color is None:
            return

        return {'main': main_color, 'sub': sub_colors}

    def _set_color_dict(self, curve, color_dict):
        if not tp.Dcc.object_exists(curve):
            return

        main_color = color_dict['main']
        sub_color = color_dict['sub']

        try:
            if main_color > 0:
                current_color = tp.Dcc.get_attribute_value(curve, 'overrideColor')
                if not current_color == main_color:
                    tp.Dcc.set_attribute_value(curve, 'overrideEnabled', True)
                    if main_color:
                        if type(main_color) != list:
                            tp.Dcc.set_attribute_value(curve, 'overrideColor', main_color)
                        else:
                            tp.Dcc.set_attribute_value(curve, 'overrideColor', main_color[0])
                            tp.Dcc.set_attribute_value(curve, 'overrideRGBColors', main_color[2])
                            if len(main_color[1]) == 1:
                                tp.Dcc.set_attribute_value(curve, 'overrideColorRGB', *main_color[1][0])
                            elif len(main_color[1]) > 1:
                                tp.Dcc.set_attribute_value(curve, 'overrideColorRGB', *main_color[1])
                        if main_color[2]:
                            LOGGER.info('{} color of RGB {}'.format(tp.Dcc.node_short_name(curve), main_color[1][0]))
                        else:
                            LOGGER.info('{} color of index {}'.format(tp.Dcc.node_short_name(curve), main_color[1]))

            if sub_color:
                shapes = shape_utils.get_shapes(curve)
                index = 0
                for shape in shapes:
                    sub_current_color = tp.Dcc.get_attribute_value(shape, 'overrideColor')
                    if sub_current_color == sub_color[index]:
                        index += 1
                        continue
                    if sub_color[index] == 0:
                        index += 1
                        continue
                    tp.Dcc.set_attribute_value(shape, 'overrideEnabled', True)
                    if index < len(sub_color):
                        if type(sub_color[index]) != list:
                            tp.Dcc.set_attribute_value(shape, 'overrideColor', sub_color[index])
                        else:
                            tp.Dcc.set_attribute_value(shape, 'overrideColor', sub_color[index][0])
                            tp.Dcc.set_attribute_value(shape, 'overrideRGBColors', sub_color[index][2])
                            if len(sub_color[index][1]) == 1:
                                is_connected = False
                                for channel in 'RGB':
                                    if tp.Dcc.is_attribute_connected(shape, 'overrideColor{}'.format(channel)):
                                        is_connected = True
                                        break
                                if is_connected:
                                    parent = tp.Dcc.node_parent(shape)
                                    if parent and tp.Dcc.attribute_exists(parent, 'color'):
                                        tp.Dcc.set_attribute_value(parent, 'color', sub_color[index][1][0])
                                        override_enabled = tp.Dcc.get_attribute_value(shape, 'overrideEnabled')
                                        if override_enabled:
                                            tp.Dcc.set_attribute_value(shape, 'overrideEnabled', False)
                                            tp.Dcc.set_attribute_value(shape, 'overrideEnabled', True)
                                    else:
                                        LOGGER.warning(
                                            'Impossible to set control color because override color '
                                            'attributes are connected!')
                                else:
                                    tp.Dcc.set_attribute_value(shape, 'overrideColorRGB', sub_color[index][1][0])
                            elif len(sub_color[index][1]) > 1:
                                is_connected = False
                                for channel in 'RGB':
                                    if tp.Dcc.is_attribute_connected(shape, 'overrideColor{}'.format(channel)):
                                        is_connected = True
                                        break
                                if is_connected:
                                    parent = tp.Dcc.node_parent(shape)
                                    if parent and tp.Dcc.attribute_exists(parent, 'color'):
                                        tp.Dcc.set_attribute_value(parent, 'color', sub_color[index][1][0])
                                    else:
                                        LOGGER.warning(
                                            'Impossible to set control color because override color '
                                            'attributes are connected!')
                                else:
                                    tp.Dcc.set_attribute_value(shape, 'overrideColorRGB', sub_color[index][1])
                        if sub_color[index][2]:
                            LOGGER.info('{} color of RGB {}'.format(tp.Dcc.node_short_name(curve), sub_color[index][1][0]))
                        else:
                            LOGGER.info('{} color of index {}'.format(tp.Dcc.node_short_name(curve), sub_color[index][1]))
                    index += 1
        except Exception:
            LOGGER.error('Error while applying color to: "{}" | {}'.format(curve, traceback.format_exc()))


class ControlColorOptionsWidget(controlcv.ControlCVOptionsWidget, object):
    def __init__(self, parent=None):
        super(ControlColorOptionsWidget, self).__init__(parent=parent)

    def ui(self):
        super(ControlColorOptionsWidget, self).ui()

        self._delete_curve_button.setText('Delete Curve Color Data')


class ControlColorPreviewWidget(rig_data.DataPreviewWidget, object):

    OPTIONS_WIDGET = ControlColorOptionsWidget

    def __init__(self, item, parent=None):
        super(ControlColorPreviewWidget, self).__init__(item=item, parent=parent)

        self._export_btn.setText('Save')
        self._export_btn.setVisible(True)
        self._load_btn.setVisible(False)


class ControlColor(rig_data.DataItem, object):
    Extension = '.{}'.format(ControlColorFileData.get_data_extension())
    Extensions = ['.{}'.format(ControlColorFileData.get_data_extension())]
    MenuOrder = 6
    MenuName = ControlColorFileData.get_data_title()
    MenuIconName = 'controls_color_data.png'
    TypeIconName = 'controls_color_data.png'
    DataType = ControlColorFileData.get_data_type()
    DefaultDataFileName = 'new_controlcolor_file'
    PreviewWidgetClass = ControlColorPreviewWidget

    def __init__(self, *args, **kwargs):
        super(ControlColor, self).__init__(*args, **kwargs)

        self.set_data_class(ControlColorFileData)
