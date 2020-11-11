#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Attribute data implementation
"""

from __future__ import print_function, division, absolute_import

import os
import logging

import maya.cmds

from tpDcc import dcc
from tpDcc.libs.python import folder, fileio
from tpDcc.dccs.maya.data import base

from tpRigToolkit.core import data as rig_data

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class AttributesFileData(base.MayaCustomData, object):

    REMOVABLE_ATTRIBUTES = ['dofMask', 'inverseScaleX', 'inverseScaleY', 'inverseScaleZ']

    def __init__(self, name=None, path=None):
        super(AttributesFileData, self).__init__(name=name, path=path)

    @staticmethod
    def get_data_type():
        return 'maya.attributes'

    @staticmethod
    def get_data_extension():
        return 'attr'

    @staticmethod
    def get_data_title():
        return 'Attributes'

    def export_data(self, file_path=None, comment='-', create_version=True, *args, **kwargs):
        if not dcc.is_maya():
            LOGGER.warning('Data must be exported from within Maya!')
            return False

        file_path = self.get_file()
        if not file_path:
            return

        if not os.path.isdir(file_path):
            folder.create_folder(file_path)

        objects = kwargs.get('objects', None)

        scope = self._get_scope(objects=objects)
        if not scope:
            return False

        data_extension = self.get_data_extension()
        if not data_extension.startswith('.'):
            data_extension = '.{}'.format(data_extension)

        for obj in scope:
            LOGGER.info('Exporting attributes of {}'.format(obj))
            file_name = fileio.create_file('{}{}'.format(obj, data_extension), file_path)
            lines = list()
            attributes_to_export = self._get_attributes(obj)
            shapes = self._get_shapes(obj)
            if shapes:
                shape = shapes[0]
                shape_attributes = self._get_shape_attributes(shape)
                if shape_attributes:
                    attributes_to_export = list(set(attributes_to_export).union(shape_attributes))
            if not attributes_to_export:
                continue

            for attribute_to_export in attributes_to_export:
                try:
                    value = dcc.get_attribute_value(obj, attribute_to_export)
                except Exception:
                    continue
                lines.append("[ '{}', {} ]".format(attribute_to_export, value))

            write_file = fileio.FileWriter(file_name)
            write_file.write(lines)

        version = fileio.FileVersion(os.path.dirname(file_path))
        if version.has_versions():
            version = fileio.FileVersion(file_path)
            version.save(comment)

        LOGGER.info('Exported {} data successfully!'.format(self.name))

        return True

    def import_data(self, file_path='', objects=None):
        if not dcc.is_maya():
            LOGGER.warning('Data must be exported from within Maya!')
            return False

        file_path = self.get_file()
        if not file_path:
            return

        valid_import = True
        selection = dcc.selected_nodes(full_path=False)
        current_extension = self.get_data_extension()
        full_extension = current_extension
        if not full_extension.startswith('.'):
            full_extension = '.{}'.format(full_extension)

        files_to_search = selection if selection else folder.get_files_with_extension(current_extension, file_path)
        for file_name in files_to_search:
            if not file_name.endswith(full_extension):
                file_name = '{}{}'.format(file_name, full_extension)
            full_path = os.path.join(file_path, file_name)
            if not os.path.isfile(full_path):
                continue
            node_name = file_name.split('.')[0]
            if not dcc.node_exists(node_name):
                LOGGER.warning(
                    'Skipping attribute import for "{}". It does not exist in current scene'.format(node_name))
                valid_import = False
                continue
            lines = fileio.get_file_lines(full_path)
            for line in lines:
                if not line:
                    continue
                line_list = eval(line)
                attribute_name = line_list[0]
                attribute_value = line_list[1]
                attribute = '{}.{}'.format(node_name, attribute_name)
                if not dcc.attribute_exists(node_name, attribute_name):
                    LOGGER.warning('"{}" does not exist. Impossible to set attribute value.'.format(attribute))
                    valid_import = False
                    continue
                if dcc.is_attribute_locked(node_name, attribute_name):
                    continue
                if dcc.is_attribute_connected(node_name, attribute_name):
                    continue
                if attribute_value is None:
                    continue
                try:
                    dcc.set_attribute_value(node_name, attribute_name, attribute_value)
                except Exception as exc:
                    LOGGER.warning('Impossible to set {} to {}: "{}" '.format(attribute, attribute_value, exc))

        dcc.select_node(selection)

        if valid_import:
            LOGGER.info('Imported attributes successfully!')
        else:
            LOGGER.warning('Import attributes with warnings!')

        return valid_import

    def _get_scope(self, objects):
        """
        Internal function that returns the list nodes to retrieve attributes of
        :return: list(str)
        """

        selection = dcc.selected_nodes(full_path=False)
        if not selection:
            LOGGER.warning('Nothing selected. Please select at least one node to export attributes of.')
            return None

        return selection

    def _get_attributes(self, node):
        found_attributes = list()

        attributes = maya.cmds.listAttr(node, scalar=True, m=True, array=True)
        for attribute in attributes:
            if not dcc.is_attribute_connected(node, attribute):
                found_attributes.append(attribute)

        for removable_attribute in self.REMOVABLE_ATTRIBUTES:
            if removable_attribute in found_attributes:
                found_attributes.remove(removable_attribute)

        return found_attributes

    def _get_shapes(self, node):
        return dcc.list_shapes(node, full_path=False)

    def _get_shape_attributes(self, shape):
        return self._get_attributes(shape)


class AttributesPreviewWidget(rig_data.DataPreviewWidget, object):
    def __init__(self, item, parent=None):
        super(AttributesPreviewWidget, self).__init__(item=item, parent=parent)

        self._export_btn.setText('Save')
        self._export_btn.setVisible(True)
        self._load_btn.setVisible(False)


class AttributesData(rig_data.DataItem, object):
    Extension = '.{}'.format(AttributesFileData.get_data_extension())
    Extensions = ['.{}'.format(AttributesFileData.get_data_extension())]
    MenuOrder = 7
    MenuName = AttributesFileData.get_data_title()
    MenuIconName = 'attributes_data.png'
    TypeIconName = 'attributes_data.png'
    DataType = AttributesFileData.get_data_type()
    DefaultDataFileName = 'new_attributes_file'
    PreviewWidgetClass = AttributesPreviewWidget

    def __init__(self, *args, **kwargs):
        super(AttributesData, self).__init__(*args, **kwargs)

        self.set_data_class(AttributesFileData)
