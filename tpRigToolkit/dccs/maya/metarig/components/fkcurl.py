#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig component to add curl functionality to already created Fk chains
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.python import python
from tpDcc.dccs.maya.core import attribute as attr_utils

from tpRigToolkit.dccs.maya.metarig.core import component


class FkCurlNoScale(component.RigComponent, object):
    def __init__(self, *args, **kwargs):
        super(FkCurlNoScale, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name('fkCurlNoScale')
        self.set_skip_increments([])
        self.set_curl_axis('X')
        self.set_curl_attribute_title('')
        self.set_curl_attribute_name('curl')

    def create(self):
        super(FkCurlNoScale, self).create()

        if not self.has_attr('curl_axis') or not self.curl_axis:
            return

        curl_controls = self.get_curl_controls()

        # If we do not define a curl control, we define it. First control in the Fk chain
        if not self.has_attr('curl_control') or not self.curl_control:
            self.set_curl_control(curl_controls[0])

        title = 'CURL'
        if self.curl_attribute_title:
            title = 'CURL_{}'.format(self.curl_attribute_title)
        if not dcc.node_exists('{}.{}'.format(self.curl_control.meta_node, title)):
            title = attr_utils.EnumAttribute(title)
            title.create(self.curl_control.meta_node)

        for i, curl_control in enumerate(curl_controls):

            if not curl_control.has_attr('auto_group') or not curl_control.auto_group:
                curl_control.create_auto(id=i)

            if self.curl_axis != 'All':
                self._attach_curl_axis(curl_control.auto_group.meta_node, i)
            else:
                for axis in ['x', 'y', 'z']:
                    self._attach_curl_axis(curl_control.auto_group.meta_node, i, axis)

    def get_curl_axis(self):
        """
        Returns curl axis as string
        :return: str
        """

        if self.curl_axis == 0:
            return 'All'
        elif self.curl_axis == 1:
            return 'X'
        elif self.curl_axis == 2:
            return 'Y'
        elif self.curl_axis == 3:
            return 'Z'

        return None

    def get_curl_controls(self):
        """
        Returns the list of controls managed by the curl control
        :return: list<RigControl>
        """

        return self.message_list_get('curl_controls')

    def set_skip_increments(self, integers_list):
        """
        Sets which FK controls increments are skipped
        :param integers_list: list<int>, list of integers
            - [0]: will the first increment
            - [0, 1]: will skip the first increments
            - etc
        """

        if not self.has_attr('skip_increments'):
            self.add_attribute(attr='skip_increments', value=integers_list)
        else:
            self.skip_increments = integers_list

    def set_curl_axis(self, axis_letter):
        """
        Sets the axis where curls should happen
        :param axis_letter: str ('X', 'Y', 'Z')
        """

        axis_list = ['X', 'Y', 'Z']
        if axis_letter == axis_list[0] or axis_letter == axis_list[0].lower():
            axis_letter = 1
        elif axis_letter == axis_list[1] or axis_letter == axis_list[1].lower():
            axis_letter = 2
        elif axis_letter == axis_list[2] or axis_letter == axis_list[2].lower():
            axis_letter = 3

        enum_name = 'All:' + ':'.join(axis_list)

        if not self.has_attr('curl_axis'):
            self.add_attribute(
                attr='curl_axis',
                enumName=enum_name,
                attr_type='enum',
                value=axis_letter
            )
        else:
            self.curl_axis = axis_letter

    def set_curl_attribute_title(self, title):
        """
        Sets the title of the curl attribute title
        :param title: str
        """

        if not self.has_attr('curl_attribute_title'):
            self.add_attribute(attr='curl_attribute_title', value=title)
        else:
            self.curl_attribute_title = title

    def set_curl_attribute_name(self, name):
        """
        Sets the name of the curl attribute
        :param name: str
        """

        if not self.has_attr('curl_attribute_name'):
            self.add_attribute(attr='curl_attribute_name', value=name)
        else:
            self.curl_attribute_name = name

    def set_curl_control(self, ctrl):
        """
        Sets the control that will have the curl control added to it
        :param ctrl: RigControl
        """

        if not self.has_attr('curl_control'):
            self.add_attribute(attr='curl_control', value=ctrl, attr_type='messageSimple')
        else:
            self.curl_control = ctrl

    def set_curl_controls(self, controls_list):
        """
        Sets the list of controls (in order) that will be managed by the curl
        :param controls_list: RigControl
        """

        controls_list = python.force_list(controls_list)

        if not self.message_list_get('curl_controls'):
            self.message_list_connect('curl_controls', controls_list)
        else:
            self.message_list_purge('curl_controls')
            self.message_list_connect('curl_controls', controls_list)

    def _attach_curl_axis(self, auto, current_increment, axis=None):
        """
        Internal function that setups the curl functionality for the FK chain
        :param auto: driver group of the fk chain control
        :param current_increment: int
        :param axis: str
        """

        if self.skip_increments and current_increment in self.skip_increments:
            return

        if not self.curl_attribute_name:
            attr_name = 'curl'
        else:
            attr_name = self.curl_attribute_name

        if axis is None:
            curl_axis = self.get_curl_axis()
        else:
            curl_axis = axis
            attr_name = '{}{}'.format(attr_name, axis)

        curl_attr = attr_utils.NumericAttribute(attr_name)
        curl_attr.set_variable_type(attr_utils.AttributeTypes.Double)
        curl_attr.create(self.curl_control.meta_node)
        curl_attr.connect_out('{}.rotate{}'.format(auto, curl_axis))
