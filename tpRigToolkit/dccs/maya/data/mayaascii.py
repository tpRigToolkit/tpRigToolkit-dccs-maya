#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains data Maya ASCII widget
"""

from __future__ import print_function, division, absolute_import

import os

import tpDcc as tp
from tpDcc.libs.qt.widgets.library import utils

from tpDcc.dccs.maya.core import helpers
from tpDcc.dccs.maya.data import base as maya_base

from tpRigToolkit.core import data


class MayaAsciiPreviewWidget(data.DataPreviewWidget, object):
    def __init__(self, item, parent=None):
        super(MayaAsciiPreviewWidget, self).__init__(item=item, parent=parent)

    def ui(self):
        super(MayaAsciiPreviewWidget, self).ui()

        self._export_btn.setText('Save')
        self._export_btn.setVisible(True)


class MayaAsciiTransferObject(utils.TransferObject, object):

    # For Maya ASCII files we do not need to store objects data
    DEFAULT_DATA = {'metadata': {}}

    def data_to_save(self):
        """
        Overrides utils.TransferObject data_to_save function
        :return: dict
        """

        data = super(MayaAsciiTransferObject, self).data_to_save()
        # data.pop('references', list())

        return data


class MayaAscii(data.DataItem, object):

    Extension = '.{}'.format(maya_base.MayaAsciiFileData.get_data_extension())
    Extensions = ['.{}'.format(maya_base.MayaAsciiFileData.get_data_extension())]
    MenuOrder = 2
    MenuName = maya_base.MayaAsciiFileData.get_data_title()
    MenuIconName = 'maya_ascii_data.png'
    TypeIconPath = 'maya_ascii_data.png'
    DataType = maya_base.MayaAsciiFileData.get_data_type()
    DefaultDataFileName = 'new_maya_ascii_file'
    PreviewWidgetClass = MayaAsciiPreviewWidget

    def __init__(self, *args, **kwargs):
        super(MayaAscii, self).__init__(*args, **kwargs)

        self.set_transfer_class(MayaAsciiTransferObject)
        self.set_data_class(maya_base.MayaAsciiFileData)

    def context_menu(self, menu):
        """
        Overrides base data.DataItem context_menu function
        :return:
        """

        student_icon = tp.ResourcesMgr().icon('student')
        menu.addAction(student_icon, 'Clean Student License', self._on_clean_student_license)

    def _on_clean_student_license(self):
        """
        Internal callback function that is triggered when user presses Clean Student License action
        """

        file_path = os.path.join(self.path(), self.name())
        if not os.path.isfile(file_path):
            return

        if not helpers.file_has_student_line(file_path):
            return False

        valid_clean = helpers.clean_student_line(file_path)

        return valid_clean

    def info(self):
        """
        Returns the info to display to the user
        :return: list(dict)
        """

        info_list = super(MayaAscii, self).info() or list()

        info_list = [{k: v for k, v in d.items() if v != 'contains'} for d in info_list]

        return info_list
