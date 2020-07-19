#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig component to add stretch functionality to already created Fk chains
"""

from __future__ import print_function, division, absolute_import

from tpDcc.dccs.maya.core import attribute as attr_utils, ik as ik_utils

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.core import component, mixin


class SplineIkStretch(component.RigComponent, mixin.JointMixin):
    def __init__(self, *args, **kwargs):
        super(SplineIkStretch, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_name('fkStretch')
        self.set_ik_curve(None)
        self.set_stretch_on_off(False)
        self.set_stretch_axis('X')
        self.set_stretch_attribute_control(None)
        self.set_stretch_attribute_name('STRETCH')

    def create(self):
        super(SplineIkStretch, self).create()

        if not self.ik_curve:
            tpRigToolkit.logger.warning('Impossible to create spline ik stretch setup because no ik curve is defined!')
            return

        if not self.stretch_attribute_control:
            tpRigToolkit.logger.warning('Impossible to create spline ik stretch setup because no control is defined!')
            return

        joints = self.get_joints(as_meta=False)
        if not joints:
            tpRigToolkit.logger.warning('Impossible to create spline ik stretch setup because no joints are defined!')
            return

        attr_utils.create_title(self.stretch_attribute_control.meta_node, self.stretch_attribute_name)
        ik_utils.create_spline_ik_stretch(
            self.ik_curve.meta_node, joints[:-1], self.stretch_attribute_control.meta_node,
            self.create_stretch, self.stretch_axis
        )

    def set_ik_curve(self, curve):
        """
        Sets Ik curve used in the Spline Ik setup
        :param curve:
        """

        if not self.has_attr('ik_curve'):
            self.add_attribute(attr='ik_curve', value=curve, attr_type='messageSimple')
        else:
            self.ik_curve = curve

    def set_stretch_on_off(self, flag):
        """
        Sets whether to add a stretch on/off attribute
        This allows animators to turn on/off the stretch effect over time
        :param flag: flag
        """

        if not self.has_attr('create_stretch'):
            self.add_attribute(attr='create_stretch', value=flag)
        else:
            self.create_stretch = flag

    def set_stretch_axis(self, axis_letter):
        """
        Sets the axis that the joints should stretch on
        :param axis_letter: str
        """

        if not self.has_attr('stretch_axis'):
            self.add_attribute(attr='stretch_axis', value=axis_letter)
        else:
            self.stretch_axis = axis_letter

    def set_stretch_attribute_controls(self, node_name):
        """
        Sets the control where stretch attribute will be added
        :param node_name: str
        """

        if not self.has_attr('stretch_attribute_control'):
            self.add_attribute(attr='stretch_attribute_control', value=node_name, attr_type='messageSimple')
        else:
            self.stretch_attribute_control = node_name

    def set_stretch_attribute_name(self, attribute_name):
        """
        Defines the name of the attribute that will be used to manage the stretch
        :param attribute_name: str
        """

        if not self.has_attr('stretch_attribute_name'):
            self.add_attribute(attr='stretch_attribute_name', value=attribute_name)
        else:
            self.stretch_attribute_name = attribute_name
