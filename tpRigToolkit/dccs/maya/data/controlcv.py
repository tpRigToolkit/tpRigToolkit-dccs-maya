#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Control CV position data implementation
"""

from __future__ import print_function, division, absolute_import

import logging

import tpDcc as tp
from tpDcc.dccs.maya.data import base
from tpDcc.libs.python import fileio, path as path_utils
from tpDcc.dccs.maya.core import shape as shape_utils

from tpRigToolkit.core import data as rig_data
from tpRigToolkit.dccs.maya.core import curve
from tpRigToolkit.libs.controlrig.core import controllib

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class ControlCVsFileData(base.MayaCustomData, object):
    def __init__(self, name=None, path=None):
        super(ControlCVsFileData, self).__init__(name=name, path=path)

    @staticmethod
    def get_data_type():
        return 'maya.controlcvs'

    @staticmethod
    def get_data_extension():
        return 'cvs'

    @staticmethod
    def get_data_title():
        return 'Control CVs'

    def export_data(self, file_path=None, comment='-', create_version=True, *args, **kwargs):
        if not tp.is_maya():
            LOGGER.warning('Data must be exported from within Maya!')
            return False

        objects = kwargs.get('objects', list())
        # We make sure that we store the short name of the controls
        objects = [tp.Dcc.node_short_name(obj) for obj in objects]

        library = self._initialize_library(file_path)
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

        for control in controls:
            library.add_curve(control)

        file_path = library.write_data_to_file()

        version = fileio.FileVersion(file_path)
        version.save(comment)

        return True

    def import_data(self, file_path='', objects=None):
        if not tp.is_maya():
            LOGGER.warning('Data must be exported from within Maya!')
            return False

        library = self._initialize_library(file_path)

        if objects:
            # We make sure that we store the short name of the controls
            objects = [tp.Dcc.node_short_name(obj) for obj in objects]
        controls = objects or controllib.get_controls()
        for control in controls:
            shapes = shape_utils.get_shapes(control)
            if not shapes:
                continue
            library.set_shape_to_curve(control, control, check_curve=True)

        self._center_view()

        LOGGER.info('Imported {} data'.format(self.name))

        return True

    def _initialize_library(self, file_name=None):
        if file_name:
            directory = path_utils.get_dirname(file_name)
            name = path_utils.get_basename(file_name)
        else:
            path = self.get_file()
            directory = path_utils.get_dirname(path)
            name = self.name

        library = curve.CurveDataInfo(extension=self.get_data_extension())
        library.set_directory(directory)

        if file_name:
            library.set_active_library(name, skip_extension=True)
        else:
            library.set_active_library(name)

        return library


class ControlCVPreviewWidget(rig_data.DataPreviewWidget, object):
    def __init__(self, item, parent=None):
        super(ControlCVPreviewWidget, self).__init__(item=item, parent=parent)


class ControlCV(rig_data.DataItem, object):
    Extension = '.{}'.format(ControlCVsFileData.get_data_extension())
    Extensions = ['.{}'.format(ControlCVsFileData.get_data_extension())]
    MenuOrder = 6
    MenuName = ControlCVsFileData.get_data_title()
    MenuIconName = 'control.png'
    TypeIconName = 'control.png'
    DataType = ControlCVsFileData.get_data_type()
    DefaultDataFileName = 'new_controlcv_file'
    PreviewWidgetClass = ControlCVPreviewWidget

    def __init__(self, *args, **kwargs):
        super(ControlCV, self).__init__(*args, **kwargs)

        self.set_data_class(ControlCVsFileData)
