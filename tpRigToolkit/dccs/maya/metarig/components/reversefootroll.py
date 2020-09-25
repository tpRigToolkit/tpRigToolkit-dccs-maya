#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains foot roll rig metarig implementations for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode
from tpDcc.dccs.maya.core import ik as ik_utils, constraint as cns_utils

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.core import component, mixin


class ReverseFootRollComponent(component.RigComponent, mixin.JointMixin):

    def __init__(self, *args, **kwargs):
        super(ReverseFootRollComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_foot_roll_control(None)
        self.set_ik_leg_control(None)
        self.set_create_roll_control(True)
        self.set_mirror_yaw(False)
        self.set_forward_roll_axis('Y')
        self.set_side_roll_axis('X')
        self.set_top_roll_axis('Z')
        self.set_toe_control_data(dict())
        self.set_roll_control_data(dict())
        self.set_create_reverse_foot_hierarchy(False)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(ReverseFootRollComponent, self).create()

        reverse_foot_joints = self.get_reverse_joints()
        if not len(reverse_foot_joints) == 7:
            tpRigToolkit.logger.warning(
                '7 reverse joints must be defined (yawIn, yawOut, heel, mid, toe, ball, ankle) '
                'to create root setup ({} joints defined)!'.format(len(reverse_foot_joints)))
            return

        self.add_attribute('yawin', value=reverse_foot_joints[0], attr_type='messageSimple')
        self.add_attribute('yawout', value=reverse_foot_joints[1], attr_type='messageSimple')
        self.add_attribute('heel', value=reverse_foot_joints[2], attr_type='messageSimple')
        self.add_attribute('mid', value=reverse_foot_joints[3], attr_type='messageSimple')
        self.add_attribute('toe', value=reverse_foot_joints[4], attr_type='messageSimple')
        self.add_attribute('ball', value=reverse_foot_joints[5], attr_type='messageSimple')
        self.add_attribute('ankle', value=reverse_foot_joints[6], attr_type='messageSimple')

        if not self.foot_roll_control:
            self._create_roll_control()

        tp.Dcc.add_title_attribute(self.foot_roll_control.meta_node, 'FOOT_CONTROLS')

        self._create_roll_attributes()
        self._setup_reverse_hierarchy()
        self._create_and_connect_ik_handles()

        # self._create_bank_roll()
        # self._create_mid_pivot_rotate()
        # self._create_forward_roll()

        # Parent root reverse joint setup to component setup group
        self.ankle.set_parent(self.setup_group)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_reverse_joints(self):
        """
        Returns reverse foot joints
        :return:
        """

        return self.message_list_get('reverse_foot_joints')

    def set_reverse_joints(self, joints):
        """
        Sets list of joints used by reverse foot setup
        :return:
        """

        if not self.message_list_get('reverse_foot_joints', as_meta=False):
            self.message_list_connect('reverse_foot_joints', joints)
        else:
            self.message_list_purge('reverse_foot_joints')
            for jnt in joints:
                self.message_list_append('reverse_foot_joints', jnt)

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

    def set_create_reverse_foot_hierarchy(self, flag):
        """
        Sets whether or not reverse foot hierarchy should be created automatically
        :param flag:
        :return:
        """

        if not self.has_attr('create_reverse_foot_hierarchy'):
            self.add_attribute(attr='create_reverse_foot_hierarchy', value=flag)
        else:
            self.create_reverse_foot_hierarchy = flag

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

    def _create_and_connect_ik_handles(self):
        """
        Internal function that creates Ik handles used for reverse foot setup
        """

        joints = self.get_joints()

        ik_solver = ik_utils.IkHandle.SOLVER_SC

        ball_joint = joints[1].meta_node
        toe_joint = joints[-1].meta_node

        # Cleanup constraints if those joints have them
        cns_utils.delete_constraints(ball_joint)
        cns_utils.delete_constraints(toe_joint)

        ankle_ball_ik_handle = tp.Dcc.create_ik_handle(
            self._get_name(self.name, 'ankleBallRevIkHandle', node_type='ikHandle'),
            start_joint=joints[0].meta_node, end_joint=ball_joint, solver_type=ik_solver)
        ball_toe_ik_handle = tp.Dcc.create_ik_handle(
            self._get_name(self.name, 'ballToeRevIkHandle', node_type='ikHandle'),
            start_joint=ball_joint, end_joint=toe_joint, solver_type=ik_solver)

        ankle_ball_ik_handle = metanode.validate_obj_arg(ankle_ball_ik_handle, 'MetaObject', update_class=True)
        ball_toe_ik_handle = metanode.validate_obj_arg(ball_toe_ik_handle, 'MetaObject', update_class=True)

        self.message_list_connect('ik_handles', [ankle_ball_ik_handle, ball_toe_ik_handle], 'reverse_foot')

        # Parent Ik handles to specific reverse foot joints
        ball_toe_ik_handle.set_parent(self.mid)
        ankle_ball_ik_handle.set_parent(self.ball)
        # tp.Dcc.create_point_constraint(ball_toe_ik_handle.meta_node, self.mid.meta_node, maintain_offset=True)
        # tp.Dcc.create_point_constraint(ankle_ball_ik_handle.meta_node, self.ball.meta_node, maintain_offset=True)

    def _setup_reverse_hierarchy(self):
        """
        Internal function used to setup reverse hierarchy
        """

        if not self.create_reverse_foot_hierarchy:
            return

        self.mid.set_parent(self.ball)
        self.ball.set_parent(self.yawout)
        self.yawout.set_parent(self.yawin)
        self.yawin.set_parent(self.heel)
        self.heel.set_parent(self.toe)
        self.toe.set_parent(self.ankle)

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


class ExpressionReverseFootRollComponent(ReverseFootRollComponent, object):

    def __init__(self, *args, **kwargs):
        super(ExpressionReverseFootRollComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'footRoll'))
        self.set_foot_roll_control(None)
        self.set_ik_leg_control(None)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(ExpressionReverseFootRollComponent, self).create()

    def _create_roll_attributes(self):

        roll_control = self.foot_roll_control.meta_node

        tp.Dcc.add_double_attribute(roll_control, 'footRoll', keyable=True)
        tp.Dcc.add_double_attribute(roll_control, 'toeLift', default_value=45, keyable=True)
        tp.Dcc.add_double_attribute(roll_control, 'toeStraight', default_value=70, keyable=True)
        tp.Dcc.add_double_attribute(roll_control, 'bank', keyable=True)
        tp.Dcc.add_double_attribute(roll_control, 'heelRotate', keyable=True)
        tp.Dcc.add_double_attribute(roll_control, 'toeRotate', keyable=True)
        tp.Dcc.add_double_attribute(roll_control, 'toeWiggle', keyable=True)
