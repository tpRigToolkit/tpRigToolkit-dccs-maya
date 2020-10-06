#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Control rotate order data implementation
"""

from __future__ import print_function, division, absolute_import

import logging

from tpRigToolkit.dccs.maya.data import attributes
from tpRigToolkit.libs.controlrig.core import controllib

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class ControlRotateOrderFileData(attributes.AttributesFileData, object):
    def __init__(self, name=None, path=None):
        super(ControlRotateOrderFileData, self).__init__(name=name, path=path)

    @staticmethod
    def get_data_type():
        return 'maya.control_rotateOrder'

    @staticmethod
    def get_data_extension():
        return 'attr'

    @staticmethod
    def get_data_title():
        return 'Control Rotate Order'

    def _get_scope(self, objects):
        controls = objects or controllib.get_controls()
        if not controls:
            LOGGER.warning('No controls found to export attributes of.')
            return None
        valid_controls = list()
        for control in controls:
            if not controllib.is_control(control):
                continue
            valid_controls.append(control)
        if not valid_controls:
            LOGGER.warning('No valid controls found to export attributes of')
            return None

        return valid_controls

    def _get_attributes(self, node):
        return ['rotateOrder']

    def _get_shapes(self, node):
        return list()


class ControlRotateOrderData(attributes.AttributesData, object):
    Extension = '.{}'.format(ControlRotateOrderFileData.get_data_extension())
    Extensions = ['.{}'.format(ControlRotateOrderFileData.get_data_extension())]
    MenuOrder = 10
    MenuName = ControlRotateOrderFileData.get_data_title()
    MenuIconName = 'attributes_data.png'
    TypeIconName = 'attributes_data.png'
    DataType = ControlRotateOrderFileData.get_data_type()
    DefaultDataFileName = 'new_attributes_file'

    def __init__(self, *args, **kwargs):
        super(ControlRotateOrderData, self).__init__(*args, **kwargs)

        self.set_data_class(ControlRotateOrderFileData)
