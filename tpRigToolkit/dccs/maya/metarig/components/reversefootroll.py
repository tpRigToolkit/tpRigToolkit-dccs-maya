#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains foot roll rig metarig implementations for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.core import component, mixin


class FootRollComponent(component.RigComponent, mixin.JointMixin):

    def __init__(self, *args, **kwargs):
        super(FootRollComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_foot_roll_control(None)
        self.set_create_roll_controls(True)
        self.set_create_foot_roll(False)
        self.set_create_ankle_roll(False)
        self.set_toe_rotate_as_locator(False)
        self.set_forward_roll_axis('X')
        self.set_side_roll_axis('Z')
        self.set_top_roll_axis('Y')
        self.set_toe_control_data({})

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(FootRollComponent, self).create()

        joints = self.get_joints()
        if not len(joints) == 3:
            tpRigToolkit.logger.warning('6 joints must be defined (ankle, ball, toe) to create root setup!')
            return

        self.add_attribute('ankle', value=joints[0], attr_type='messageSimple')
        self.add_attribute('ball', value=joints[1], attr_type='messageSimple')
        self.add_attribute('toe', value=joints[2], attr_type='messageSimple')

        tp.Dcc.add_title_attribute(self.foot_roll_control.meta_node, 'FOOT_CONTROLS')

        if self.create_roll_controls:
            tp.Dcc.add_bool_attribute(self.foot_roll_control.meta_node, 'controlVisibility', self.sub_visibility)

        self._create_roll_attributes()

        self._create_toe_rotate_control()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_foot_roll_control(self, control):
        """
        Sets the main control used by foot roll rig setup
        :param control:
        :return:
        """

        if not self.has_attr('foot_roll_control'):
            self.add_attribute('foot_roll_control', value=control, attr_type='messageSimple')
        else:
            self.foot_roll_control = control

    def set_create_roll_controls(self, flag):
        """
        Sets whether roll controls should be created or not
        :param flag: bool
        """

        if not self.has_attr('create_roll_controls'):
            self.add_attribute('create_roll_controls', value=flag, attr_type='bool')
        else:
            self.create_roll_controls = flag

    def set_create_foot_roll(self, flag):
        """
        Sets whether or not foot roll functionality should be added
        :param flag: bool
        """

        if not self.has_attr('create_foot_roll'):
            self.add_attribute('create_foot_roll', value=flag, attr_type='bool')
        else:
            self.create_foot_roll = flag

    def set_create_ankle_roll(self, flag, axis='Z'):
        """
        Sets whether or not ankle roll functionality should be added
        :param flag: bool
        :param axis: str
        """

        if not self.has_attr('create_ankle_roll'):
            self.add_attribute('create_ankle_roll', value=flag, attr_type='bool')
        else:
            self.create_ankle_roll = flag

        if not self.has_attr('ankle_roll_axis'):
            self.add_attribute('ankle_roll_axis', value=axis.upper(), attr_type='string')
        else:
            self.ankle_roll_axis = axis.upper()

    def set_toe_rotate_as_locator(self, flag):
        """
        Sets whether toe rotate control should be created as a control or as a locator
        :param flag: bool
        """

        if not self.has_attr('toe_rotate_as_locator'):
            self.add_attribute('toe_rotate_as_locator', value=flag, attr_type='bool')
        else:
            self.toe_rotate_as_locator = flag

    def set_forward_roll_axis(self, axis):
        """
        Sets forward axis used for roll
        :param axis: str
        """

        if not self.has_attr('forward_roll_axis'):
            self.add_attribute('forward_roll_axis', value=axis.upper(), attr_type='string')
        else:
            self.forward_roll_axis = axis.upper()

    def set_side_roll_axis(self, axis):
        """
        Sets side axis used for roll
        :param axis: str
        """

        if not self.has_attr('side_roll_axis'):
            self.add_attribute('side_roll_axis', value=axis.upper(), attr_type='string')
        else:
            self.side_roll_axis = axis.upper()

    def set_top_roll_axis(self, axis):
        """
        Sets top axis used for roll
        :param axis: str
        """

        if not self.has_attr('top_roll_axis'):
            self.add_attribute('top_roll_axis', value=axis.upper(), attr_type='string')
        else:
            self.top_roll_axis = axis.upper()

    def set_toe_control_data(self, control_data):
        """
        Sets the control data used by the toe control
        :param control_data: dict
        """

        if not self.has_attr('toe_control_data'):
            self.add_attribute(attr='toe_control_data', value=control_data)
        else:
            self.toe_control_data = control_data

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_roll_attributes(self):
        """
        Internal function that creates basic roll attributes
        :return:
        """

        roll_control = self.foot_roll_control.meta_node

        if self.create_foot_roll:
            tp.Dcc.add_double_attribute(roll_control, 'footRoll', keyable=True)
            tp.Dcc.add_double_attribute(roll_control, 'footRoll', default_value=30, footRollAngle=True)

        if self.create_ankle_roll:
            tp.Dcc.add_double_attribute(roll_control, 'ankleRoll', keyable=True)

        for attr_name in ['ballRoll', 'toeRoll', 'heelRoll', 'yawRoll']:
            tp.Dcc.add_double_attribute(roll_control, attr_name, keyable=True)

    def _create_toe_rotate_control(self):
        """
        Internal function that creates toe rotate control
        """

        roll_control = self.foot_roll_control.meta_node

        tp.Dcc.add_double_attribute(roll_control, 'toeRotate', keyable=True)

        if self.toe_rotate_as_locator:
            toe_control = tp.Dcc.create_locator(name=self._get_name(self.name, 'toeRotate', node_type='locator'))
            toe_control_root = tp.Dcc.create_buffer_group(toe_control)
            tp.Dcc.connect_attribute(
                roll_control, 'toeRotate', toe_control, 'rotate{}'.format(self.forward_roll_axis.upper()))
        else:
            toe_control = self.create_control('toeRotate', sub=True, control_data=self.toe_control_data)
            toe_control.hide_translate_attributes()
            toe_control.hide_scale_and_visibility_attributes()
            toe_control_root = toe_control.create_root().meta_node
            toe_control_driver = toe_control.create_auto('driver')
            tp.Dcc.connect_attribute(
                roll_control, 'toeRotate', toe_control_driver.meta_node,
                'rotate{}'.format(self.forward_roll_axis.upper()))

        tp.Dcc.match_translation_rotation(self.ball.meta_node, toe_control_root)

        return toe_control.meta_node, toe_control_root
