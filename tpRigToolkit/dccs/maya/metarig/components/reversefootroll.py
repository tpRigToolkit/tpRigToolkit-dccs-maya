#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains foot roll rig metarig implementations for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode, metautils

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.core import component, mixin


class ReverseFootRollComponent(component.RigComponent, mixin.JointMixin):

    def __init__(self, *args, **kwargs):
        super(ReverseFootRollComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_foot_roll_control(None)
        self.set_create_roll_control(True)
        self.set_mirror_yaw(False)
        self.set_forward_roll_axis('Y')
        self.set_side_roll_axis('X')
        self.set_top_roll_axis('Z')
        self.set_toe_control_data({})

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(ReverseFootRollComponent, self).create()

        joints = self.get_joints()
        if not len(joints) == 7:
            tpRigToolkit.logger.warning(
                '6 joints must be defined (yawIn, yawOut, heel, mid, toe, ball, ankle) to create root setup!')
            return

        self.add_attribute('yawin', value=joints[0], attr_type='messageSimple')
        self.add_attribute('yawout', value=joints[1], attr_type='messageSimple')
        self.add_attribute('heel', value=joints[2], attr_type='messageSimple')
        self.add_attribute('mid', value=joints[3], attr_type='messageSimple')
        self.add_attribute('toe', value=joints[4], attr_type='messageSimple')
        self.add_attribute('ball', value=joints[5], attr_type='messageSimple')
        self.add_attribute('ankle', value=joints[6], attr_type='messageSimple')

        if not self.foot_roll_control:
            self._create_roll_control()

        tp.Dcc.add_title_attribute(self.foot_roll_control.meta_node, 'FOOT_CONTROLS')

        self._create_roll_attributes()

        self._create_bank_roll()
        self._create_mid_pivot_rotate()
        self._create_forward_roll()

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

    def set_create_roll_control(self, flag):
        """
        Sets whether roll control should be created or not
        :param flag: bool
        """

        if not self.has_attr('create_roll_control'):
            self.add_attribute('create_roll_control', value=flag, attr_type='bool')
        else:
            self.create_roll_control = flag

    def set_mirror_yaw(self, flag):
        """
        Sets whether yaw rotation should be mirrored or not
        NOTE: Mirror is only applied on right side components.
        :param flag: bool
        """

        if not self.has_attr('mirror_yaw'):
            self.add_attribute('mirror_yaw', value=flag, attr_type='bool')
        else:
            self.mirror_yaw = flag

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

    def set_ik_leg_control(self, control):
        """
        Sets the control of the Leg Ik this reverse foot roll setup should be attached into
        :param control:
        """

        if not self.has_attr('ik_leg_control'):
            self.add_attribute('ik_leg_control', value=control, attr_type='messageSimple')
        else:
            self.ik_leg_control = control

    def set_roll_control_data(self, control_data):
        """
        Sets the control data used by the roll control
        :param control_data: dict
        """

        if not self.has_attr('roll_control_data'):
            self.add_attribute(attr='roll_control_data', value=control_data)
        else:
            self.roll_control_data = control_data

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_roll_control(self, transform=None):
        """
        Internal function that creates the roll control for this rig setup
        :param transform:
        :return:
        """

        roll_control = self.create_control('roll', control_data=self.roll_control_data)
        roll_control.scale_control_shapes((0.8, 0.8, 0.8))
        roll_control.create_root()
        roll_control.hide_scale_and_visibility_attributes()

        transform = transform or self.ik_leg_control
        if transform:
            roll_control.match_translation_and_rotation(transform)

        self.set_foot_roll_control(roll_control)

        if self.ik_leg_control:
            roll_control.set_parent(self.ik_leg_control)

    def _create_roll_attributes(self):
        """
        Internal function that creates basic roll attributes
        :return:
        """

        roll_control = self.foot_roll_control.meta_node

        tp.Dcc.add_double_attribute(roll_control, 'weight', min_value=0, max_value=1, keyable=True)

    def _create_bank_roll(self):

        roll_control = self.foot_roll_control.meta_node

        bank_cond = maya.cmds.createNode('condition', name=self._get_name(self.name, 'bankRoll', node_type='condition'))
        tp.Dcc.set_attribute_value(bank_cond, 'operation', 2)   # Greater Than
        tp.Dcc.set_attribute_value(bank_cond, 'colorIfFalseR', 0.0)
        tp.Dcc.connect_attribute(roll_control, 'rotate{}'.format(self.side_roll_axis), bank_cond, 'firstTerm')
        tp.Dcc.connect_attribute(roll_control, 'rotate{}'.format(self.side_roll_axis), bank_cond, 'colorIfTrueR')
        tp.Dcc.connect_attribute(roll_control, 'rotate{}'.format(self.side_roll_axis), bank_cond, 'colorIfFalseG')
        tp.Dcc.connect_attribute(bank_cond, 'outColorR', self.yawin.meta_node, 'rotate{}'.format(self.side_roll_axis))
        tp.Dcc.connect_attribute(bank_cond, 'outColorG', self.yawout.meta_node, 'rotate{}'.format(self.side_roll_axis))

    def _create_mid_pivot_rotate(self):

        roll_control = self.foot_roll_control.meta_node

        tp.Dcc.connect_attribute(
            roll_control, 'rotate{}'.format(self.top_roll_axis),
            self.mid.meta_node, 'rotate{}'.format(self.top_roll_axis))

    def _create_forward_roll(self):

        roll_control = self.foot_roll_control.meta_node

        forward_cond = maya.cmds.createNode(
            'condition', name=self._get_name(self.name, 'forwardRoll', node_type='condition'))
        tp.Dcc.set_attribute_value(forward_cond, 'operation', 4)  # Less Than
        tp.Dcc.set_attribute_value(forward_cond, 'colorIfFalseR', 0.0)
        tp.Dcc.connect_attribute(roll_control, 'rotate{}'.format(self.forward_roll_axis), forward_cond, 'firstTerm')
        tp.Dcc.connect_attribute(roll_control, 'rotate{}'.format(self.forward_roll_axis), forward_cond, 'colorIfTrueR')
        tp.Dcc.connect_attribute(roll_control, 'rotate{}'.format(self.forward_roll_axis), forward_cond, 'colorIfFalseG')
        tp.Dcc.connect_attribute(
            forward_cond, 'outColorR', self.heel.meta_node, 'rotate{}'.format(self.forward_roll_axis))

        forward_blend = maya.cmds.createNode(
            'blendColors', name=self._get_name(self.name, 'forwardRoll', node_type='blendColors'))
        tp.Dcc.connect_attribute(roll_control, 'weight', forward_blend, 'blender')
        tp.Dcc.connect_attribute(forward_cond, 'outColorG', forward_blend, 'color1R')
        tp.Dcc.connect_attribute(forward_cond, 'outColorG', forward_blend, 'color2G')
        tp.Dcc.connect_attribute(
            forward_blend, 'outputR', self.toe.meta_node, 'rotate{}'.format(self.forward_roll_axis))
        tp.Dcc.connect_attribute(
            forward_blend, 'outputG', self.ball.meta_node, 'rotate{}'.format(self.forward_roll_axis))
