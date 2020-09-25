#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Control CV position data implementation
"""

from __future__ import print_function, division, absolute_import

import logging

from Qt.QtWidgets import *

import tpDcc as tp
from tpDcc.libs.python import fileio, python, path as path_utils
from tpDcc.libs.qt.widgets import buttons, dividers, search
from tpDcc.libs.qt.widgets.library import loadwidget
from tpDcc.dccs.maya.data import base
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

        LOGGER.info('Exported {} data'.format(self.name))

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

    def get_curves(self, file_name=None):
        library = self._initialize_library(file_name)
        library.set_active_library(self.name)
        curves = library.get_curve_names()

        return curves

    def remove_curve(self, curve_name, file_name=None):
        curves_list = python.force_list(curve_name)
        library = self._initialize_library(file_name)
        library.set_active_library(self.name)
        for curve in curves_list:
            library.remove_curve(curve)
        library.write_data_to_file()

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


class ControlCVOptionsWidget(loadwidget.OptionsFileWidget, object):
    def __init__(self, parent=None):
        super(ControlCVOptionsWidget, self).__init__(parent=parent)

    def ui(self):
        super(ControlCVOptionsWidget, self).ui()

        self._search_line = search.SearchFindWidget(parent=self)
        self._search_line.set_placeholder_text('Filter Names')
        self._curves_list = QListWidget()
        self._curves_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._curves_list.setSelectionMode(self._curves_list.ExtendedSelection)
        self._curves_list.setSortingEnabled(True)
        self._delete_curve_button = buttons.BaseButton('Delete Curve CVs data', parent=self)

        self.main_layout.addWidget(self._search_line)
        self.main_layout.addWidget(self._curves_list)
        self.main_layout.addWidget(dividers.Divider())
        self.main_layout.addWidget(self._delete_curve_button)

    def setup_signals(self):
        self._search_line.textChanged.connect(self._on_filter_names)
        self._delete_curve_button.clicked.connect(self._on_remove_curves)

    def refresh(self):
        self._curves_list.clear()

        if not self._data_object:
            return

        curves = self._data_object.get_curves()
        if not curves:
            return

        for curve_name in curves:
            item = QListWidgetItem(curve_name)
            self._curves_list.addItem(item)

    def _on_filter_names(self):
        self._unhide_names()
        for i in range(self._curves_list.count()):
            item = self._curves_list.item(i)
            text = str(item.text())
            filter_text = self._search_line.text()
            if text.find(filter_text) == -1:
                item.setHidden(True)

    def _on_remove_curves(self):
        items = self._curves_list.selectedItems()
        if not items:
            return

        for item in items:
            curve_name = str(item.text())
            removed = self._data_object.remove_curve(curve_name)
            if removed:
                index = self._curves_list.indexFromItem(item)
                remove_item = self._curves_list.takeItem(index.row())
                del remove_item

    def _unhide_names(self):
        for i in range(self._curves_list.count()):
            item = self._curves_list.item(i)
            item.setHidden(False)


class ControlCVPreviewWidget(rig_data.DataPreviewWidget, object):

    OPTIONS_WIDGET = ControlCVOptionsWidget

    def __init__(self, item, parent=None):
        super(ControlCVPreviewWidget, self).__init__(item=item, parent=parent)

        self._export_btn.setText('Save')
        self._export_btn.setVisible(True)
        self._load_btn.setVisible(False)


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
