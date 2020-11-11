#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains foot roll rig metarig implementations for Maya
"""

from __future__ import print_function, division, absolute_import

import logging

import maya.cmds

from tpDcc import dcc
from tpDcc.dccs.maya.meta import metanode
from tpDcc.dccs.maya.core import ik as ik_utils, constraint as cns_utils, animation as anim_utils

from tpRigToolkit.dccs.maya.metarig.core import component, mixin

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class ReverseFootRollComponent(component.RigComponent, mixin.JointMixin):

    def __init__(self, *args, **kwargs):
        super(ReverseFootRollComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_ik_leg_control(None)
        self.set_create_roll_control(True)
        self.set_roll_control(None)
        self.set_roll_control_data(dict())
        self.set_mirror_yaw(False)
        self.set_forward_roll_axis('Y')
        self.set_side_roll_axis('X')
        self.set_top_roll_axis('Z')
        self.set_toe_control_data(dict())
        self.set_create_reverse_foot_hierarchy(False)
        self.set_create_pivot_manipulators(True)
        self.set_pivot_translate_axis('Y')

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(ReverseFootRollComponent, self).create()

        reverse_foot_joints = self.get_reverse_joints()
        if not len(reverse_foot_joints) == 7:
            LOGGER.warning(
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

        if not self.roll_control and self.create_roll_control:
            self._create_roll_control()

        dcc.add_title_attribute(self.ik_leg_control.meta_node, 'FOOT_CONTROLS')

        self._create_roll_attributes()

        self._setup_reverse_hierarchy()
        self._create_and_connect_ik_handles()

        self._create_bank_roll()
        self._create_mid_pivot_rotate()
        self._create_forward_roll()

        self._create_pivot_manipulators()

        # Parent root reverse joint setup to component setup group
        if self.create_pivot_manipulators:
            self.yawin_pivot_group.set_parent(self.setup_group)
            if self.ik_leg_control:
                dcc.create_parent_constraint(
                    self.yawin_pivot_group.meta_node, self.ik_leg_control.meta_node, maintain_offset=True)
        else:
            # self.ankle.set_parent(self.setup_group)
            # self.yawin.set_parent(self.setup_group
            reverse_foot_joints[0].set_parent(self.setup_group)
            if self.ik_leg_control:
                dcc.create_parent_constraint(
                    reverse_foot_joints[0].meta_node, self.ik_leg_control.meta_node, maintain_offset=True)

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

    def set_roll_control(self, control):
        """
        Sets the main control used by foot roll rig setup
        :param control:
        :return:
        """

        if not self.has_attr('roll_control'):
            self.add_attribute('roll_control', value=control, attr_type='messageSimple')
        else:
            self.roll_control = control

    def set_create_roll_control(self, flag):
        """
        Sets whether roll control should be created or not
        :param flag: bool
        """

        if not self.has_attr('create_roll_control'):
            self.add_attribute('create_roll_control', value=flag, attr_type='bool')
        else:
            self.create_roll_control = flag

    def set_roll_control_data(self, control_data):
        """
        Sets the control data used by the roll control
        :param control_data: dict
        """

        if not self.has_attr('roll_control_data'):
            self.add_attribute(attr='roll_control_data', value=control_data)
        else:
            self.roll_control_data = control_data

    def set_pivot_control_data(self, control_data):
        """
        Sets the control data used by the pivot controls
        :param control_data: dict
        """

        if not self.has_attr('pivot_control_data'):
            self.add_attribute(attr='pivot_control_data', value=control_data)
        else:
            self.pivot_control_data = control_data

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

    def set_pivot_translate_axis(self, axis):
        """
        Sets pivot translate axis used for pivot setup
        :param axis: str
        """

        if not self.has_attr('pivot_translate_axis'):
            self.add_attribute('pivot_translate_axis', value=axis.upper(), attr_type='string')
        else:
            self.pivot_translate_axis = axis.upper()

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

    def set_create_reverse_foot_hierarchy(self, flag):
        """
        Sets whether or not reverse foot hierarchy should be created automatically
        :param flag: bool
        :return:
        """

        if not self.has_attr('create_reverse_foot_hierarchy'):
            self.add_attribute(attr='create_reverse_foot_hierarchy', value=flag)
        else:
            self.create_reverse_foot_hierarchy = flag

    def set_create_pivot_manipulators(self, flag):
        """
        Sets whether or not reverse foot pivot manipulator is created
        This allow animator to set the reverse foot roll rotation pivots on the fly
        :param flag: bool
        :return:
        """

        if not self.has_attr('create_pivot_manipulators'):
            self.add_attribute(attr='create_pivot_manipulators', value=flag)
        else:
            self.create_pivot_manipulators = flag

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_roll_control(self, transform=None):
        """
        Internal function that creates the foot control for this rig setup
        :param transform:
        :return:
        """

        roll_control = self.create_control('roll', control_data=self.roll_control_data)
        roll_control.scale_control_shapes((0.8, 0.8, 0.8))
        roll_control.create_root()
        roll_control.hide_translate_attributes()
        roll_control.hide_scale_and_visibility_attributes()

        transform = transform or self.ball
        if transform:
            roll_control.match_translation_and_rotation(transform)

        self.set_roll_control(roll_control)

        if self.ik_leg_control:
            dcc.create_parent_constraint(
                roll_control.top().meta_node, self.ik_leg_control.meta_node, maintain_offset=True)

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

        ankle_ball_ik_handle = dcc.create_ik_handle(
            self._get_name(self.name, 'ankleBallRevIkHandle', node_type='ikHandle'),
            start_joint=joints[0].meta_node, end_joint=ball_joint, solver_type=ik_solver)
        ball_toe_ik_handle = dcc.create_ik_handle(
            self._get_name(self.name, 'ballToeRevIkHandle', node_type='ikHandle'),
            start_joint=ball_joint, end_joint=toe_joint, solver_type=ik_solver)

        ankle_ball_ik_handle = metanode.validate_obj_arg(ankle_ball_ik_handle, 'MetaObject', update_class=True)
        ball_toe_ik_handle = metanode.validate_obj_arg(ball_toe_ik_handle, 'MetaObject', update_class=True)

        self.message_list_connect('ik_handles', [ankle_ball_ik_handle, ball_toe_ik_handle], 'reverse_foot')

        # Parent Ik handles to specific reverse foot joints
        ball_toe_ik_handle.set_parent(self.mid)
        ankle_ball_ik_handle.set_parent(self.ball)
        # dcc.create_point_constraint(ball_toe_ik_handle.meta_node, self.mid.meta_node, maintain_offset=True)
        # dcc.create_point_constraint(ankle_ball_ik_handle.meta_node, self.ball.meta_node, maintain_offset=True)

    def _setup_reverse_hierarchy(self):
        """
        Internal function used to setup reverse hierarchy
        """

        if not self.create_reverse_foot_hierarchy:
            return

        self.ankle.set_parent(self.ball)
        self.ball.set_parent(self.toe)
        self.toe.set_parent(self.mid)
        self.mid.set_parent(self.heel)
        self.heel.set_parent(self.yawout)
        self.yawout.set_parent(self.yawin)

        # self.mid.set_parent(self.yawout)
        # self.ball.set_parent(self.yawout)
        # self.yawout.set_parent(self.yawin)
        # self.yawin.set_parent(self.heel)
        # self.heel.set_parent(self.toe)
        # self.toe.set_parent(self.ankle)

        # Reverse joint display is disabled by default
        # for reverse_joint in [self.ankle, self.ball, self.toe, self.mid, self.heel, self.yawout, self.yawin]:
        #     dcc.set_attribute_value(reverse_joint.meta_node, 'drawStyle', 2)

    def _create_roll_attributes(self):
        """
        Internal function that creates basic roll attributes
        :return:
        """

        foot_control = self.ik_leg_control
        if not foot_control:
            return

        foot_control = foot_control.meta_node

        dcc.add_double_attribute(foot_control, 'ballRoll', keyable=True)
        dcc.add_double_attribute(foot_control, 'toeRoll', keyable=True)
        dcc.add_double_attribute(foot_control, 'heelRoll', keyable=True)
        dcc.add_double_attribute(foot_control, 'yawRoll', keyable=True)

    def _create_bank_roll(self):

        roll_control = self.roll_control
        if not roll_control:
            return

        roll_control = roll_control.meta_node

        bank_cond = maya.cmds.createNode('condition', name=self._get_name(self.name, 'bankRoll', node_type='condition'))
        dcc.set_attribute_value(bank_cond, 'operation', 2)   # Greater Than
        dcc.set_attribute_value(bank_cond, 'colorIfFalseR', 0.0)
        dcc.connect_attribute(roll_control, 'rotate{}'.format(self.side_roll_axis), bank_cond, 'firstTerm')
        dcc.connect_attribute(roll_control, 'rotate{}'.format(self.side_roll_axis), bank_cond, 'colorIfTrueR')
        dcc.connect_attribute(roll_control, 'rotate{}'.format(self.side_roll_axis), bank_cond, 'colorIfFalseG')
        dcc.connect_attribute(bank_cond, 'outColorR', self.yawin.meta_node, 'rotate{}'.format(self.side_roll_axis))
        dcc.connect_attribute(bank_cond, 'outColorG', self.yawout.meta_node, 'rotate{}'.format(self.side_roll_axis))

    def _create_mid_pivot_rotate(self):

        roll_control = self.roll_control
        if not roll_control:
            return

        roll_control = roll_control.meta_node

        dcc.connect_attribute(
            roll_control, 'rotate{}'.format(self.top_roll_axis),
            self.mid.meta_node, 'rotate{}'.format(self.top_roll_axis))

    def _create_forward_roll(self):

        roll_control = self.roll_control
        if not roll_control:
            return

        roll_control = roll_control.meta_node

        forward_cond = maya.cmds.createNode(
            'condition', name=self._get_name(self.name, 'forwardRoll', node_type='condition'))
        dcc.set_attribute_value(forward_cond, 'operation', 4)  # Less Than
        dcc.set_attribute_value(forward_cond, 'colorIfFalseR', 0.0)
        dcc.connect_attribute(roll_control, 'rotate{}'.format(self.forward_roll_axis), forward_cond, 'firstTerm')
        dcc.connect_attribute(roll_control, 'rotate{}'.format(self.forward_roll_axis), forward_cond, 'colorIfTrueR')
        dcc.connect_attribute(roll_control, 'rotate{}'.format(self.forward_roll_axis), forward_cond, 'colorIfFalseG')
        dcc.connect_attribute(
            forward_cond, 'outColorR', self.heel.meta_node, 'rotate{}'.format(self.forward_roll_axis))

        if not dcc.attribute_exists(roll_control, 'weight'):
            dcc.add_float_attribute(roll_control, 'weight', min_value=0.0, max_value=1.0)

        forward_blend = maya.cmds.createNode(
            'blendColors', name=self._get_name(self.name, 'forwardRoll', node_type='blendColors'))
        dcc.connect_attribute(roll_control, 'weight', forward_blend, 'blender')
        dcc.connect_attribute(forward_cond, 'outColorG', forward_blend, 'color1R')
        dcc.connect_attribute(forward_cond, 'outColorG', forward_blend, 'color2G')
        dcc.connect_attribute(
            forward_blend, 'outputR', self.toe.meta_node, 'rotate{}'.format(self.forward_roll_axis))
        dcc.connect_attribute(
            forward_blend, 'outputG', self.ball.meta_node, 'rotate{}'.format(self.forward_roll_axis))

    def _create_pivot_manipulators(self):
        if not self.create_pivot_manipulators:
            return

        # Recreate reverse hierarchy to make sure that bank joints have a buffer group
        # IMPORTANT: This will make the buffer group of yawin to be the root of the reverse chain.
        yawin_pivot_group = dcc.create_empty_group(name=self._get_name(self.name, 'yawInPivot', node_type='group'))
        yawin_pivot_group = metanode.validate_obj_arg(yawin_pivot_group, 'MetaObject', update_class=True)
        dcc.match_translation_rotation(self.yawin.meta_node, yawin_pivot_group.meta_node)
        yawout_pivot_group = dcc.create_empty_group(
            name=self._get_name(self.name, 'yawOutPivot', node_type='group'))
        yawout_pivot_group = metanode.validate_obj_arg(yawout_pivot_group, 'MetaObject', update_class=True)
        dcc.match_translation_rotation(self.yawout.meta_node, yawout_pivot_group.meta_node)
        heel_pivot_group = dcc.create_empty_group(name=self._get_name(self.name, 'heelPivot', node_type='group'))
        heel_pivot_group = metanode.validate_obj_arg(heel_pivot_group, 'MetaObject', update_class=True)
        dcc.match_translation_rotation(self.heel.meta_node, heel_pivot_group.meta_node)

        yawin_parent = dcc.node_parent(self.yawin.meta_node)
        self.yawin.set_parent(yawin_pivot_group)
        yawout_pivot_group.set_parent(self.yawin)
        self.yawout.set_parent(yawout_pivot_group)
        self.heel.set_parent(heel_pivot_group)
        heel_pivot_group.set_parent(self.yawout)
        if yawin_parent:
            dcc.set_parent(yawin_pivot_group.meta_node, yawin_parent)

        bank_in_pivot_control = self.create_control('bankInPivot', control_data=self.pivot_control_data)
        bank_in_pivot_control.create_root()
        bank_in_pivot_control.match_translation_and_rotation(self.yawin.meta_node)
        bank_in_pivot_control.hide_scale_and_visibility_attributes()
        bank_in_pivot_control.hide_rotate_attributes()

        bank_out_pivot_control = self.create_control('bankOutPivot', control_data=self.pivot_control_data)
        bank_out_pivot_control.create_root()
        bank_out_pivot_control.match_translation_and_rotation(self.yawout.meta_node)
        bank_out_pivot_control.hide_scale_and_visibility_attributes()
        bank_out_pivot_control.hide_rotate_attributes()

        for axis in 'XYZ':
            if axis == self.pivot_translate_axis.upper():
                continue
            attr_name = 'translate{}'.format(axis)
            dcc.lock_attribute(bank_out_pivot_control.meta_node, attr_name)
            dcc.hide_attribute(bank_out_pivot_control.meta_node, attr_name)
            dcc.hide_attribute(bank_in_pivot_control.meta_node, attr_name)
            dcc.lock_attribute(bank_in_pivot_control.meta_node, attr_name)

        # TODO: This should be a property of the component (and the rig module it belongs it). In the last term,
        # TODO: this property should be fined in the character/project
        is_mirror = True

        # TODO: This property should be defined in the component
        dst_to_move = 10

        if is_mirror:
            self._setup_pivot_manipulators_mirror_driven_keys(
                bank_in_pivot_control, bank_out_pivot_control, dst_to_move)
        else:
            self._setup_pivot_manipulators_driven_keys(bank_in_pivot_control, bank_out_pivot_control, dst_to_move)

        if self.ik_leg_control:
            dcc.create_parent_constraint(
                bank_in_pivot_control.top().meta_node, self.ik_leg_control.meta_node, maintain_offset=True)
            dcc.create_parent_constraint(
                bank_out_pivot_control.top().meta_node, self.ik_leg_control.meta_node, maintain_offset=True)

        self.add_attribute('yawin_pivot_group', value=yawin_pivot_group, attr_type='messageSimple')
        self.add_attribute('bank_in_pivot_control', value=bank_in_pivot_control, attr_type='messageSimple')
        self.add_attribute('bank_out_pivot_control', value=bank_out_pivot_control, attr_type='messageSimple')

    def _setup_pivot_manipulators_driven_keys(self, bank_in_pivot_control, bank_out_pivot_control, dst_to_move):

        bank_in_driver_attr_name = 'translate{}'.format(self.pivot_translate_axis.upper())
        bank_in_driver_attr = '{}.{}'.format(bank_in_pivot_control.meta_node, bank_in_driver_attr_name)
        current_in_driver_attr_value = dcc.get_attribute_value(
            bank_in_pivot_control.meta_node, bank_in_driver_attr_name)
        bank_in_driven_attr_name = 'translate{}'.format(self.pivot_translate_axis.upper())
        bank_in_driven_attr = '{}.{}'.format(self.yawin.meta_node, bank_in_driven_attr_name)
        current_in_driven_attr_value = dcc.get_attribute_value(self.yawin.meta_node, bank_in_driven_attr_name)

        bank_out_driver_attr_name = 'translate{}'.format(self.pivot_translate_axis.upper())
        bank_out_driver_attr = '{}.{}'.format(bank_out_pivot_control.meta_node, bank_out_driver_attr_name)
        current_out_driver_attr_value = dcc.get_attribute_value(
            bank_out_pivot_control.meta_node, bank_out_driver_attr_name)
        bank_out_driven_attr_name = 'translate{}'.format(self.pivot_translate_axis.upper())
        bank_out_driven_attr = '{}.{}'.format(self.yawout.meta_node, bank_out_driven_attr_name)
        current_out_driven_attr_value = dcc.get_attribute_value(self.yawout.meta_node, bank_out_driven_attr_name)

        heel_driven_attr_name = 'translate{}'.format(self.pivot_translate_axis.upper())
        heel_driven_attr = '{}.{}'.format(self.heel.meta_node, heel_driven_attr_name)
        heel_driven_attr_value = dcc.get_attribute_value(self.heel.meta_node, heel_driven_attr_name)

        anim_utils.quick_driven_key(
            source=bank_in_driver_attr, target=bank_in_driven_attr,
            source_values=[current_in_driver_attr_value, -dst_to_move, dst_to_move],
            target_values=[current_in_driven_attr_value, current_in_driven_attr_value - dst_to_move,
                           current_in_driven_attr_value + dst_to_move],
            infinite=True)

        anim_utils.quick_driven_key(
            source=bank_in_driver_attr, target=bank_out_driven_attr,
            source_values=[current_in_driver_attr_value, -dst_to_move, dst_to_move],
            target_values=[current_out_driven_attr_value, current_out_driven_attr_value + dst_to_move,
                           current_out_driven_attr_value - dst_to_move],
            infinite=True)

        anim_utils.quick_driven_key(
            source=bank_out_driver_attr, target=bank_out_driven_attr,
            source_values=[current_out_driver_attr_value, dst_to_move, -dst_to_move],
            target_values=[current_out_driven_attr_value, current_out_driven_attr_value + dst_to_move,
                           current_out_driven_attr_value - dst_to_move], infinite=True)

        anim_utils.quick_driven_key(
            source=bank_out_driver_attr, target=heel_driven_attr,
            source_values=[current_out_driver_attr_value, dst_to_move, -dst_to_move],
            target_values=[heel_driven_attr_value, heel_driven_attr_value - dst_to_move,
                           current_out_driven_attr_value + dst_to_move], infinite=True)

    def _setup_pivot_manipulators_mirror_driven_keys(self, bank_in_pivot_control, bank_out_pivot_control, dst_to_move):

        is_right = dcc.name_is_right(self.side)

        bank_in_driver_attr_name = 'translate{}'.format(self.pivot_translate_axis.upper())
        bank_in_driver_attr = '{}.{}'.format(bank_in_pivot_control.meta_node, bank_in_driver_attr_name)
        current_in_driver_attr_value = dcc.get_attribute_value(
            bank_in_pivot_control.meta_node, bank_in_driver_attr_name)
        bank_in_driven_attr_name = 'translate{}'.format(self.pivot_translate_axis.upper())
        bank_in_driven_attr = '{}.{}'.format(self.yawin.meta_node, bank_in_driven_attr_name)
        current_in_driven_attr_value = dcc.get_attribute_value(self.yawin.meta_node, bank_in_driven_attr_name)

        bank_out_driver_attr_name = 'translate{}'.format(self.pivot_translate_axis.upper())
        bank_out_driver_attr = '{}.{}'.format(bank_out_pivot_control.meta_node, bank_out_driver_attr_name)
        current_out_driver_attr_value = dcc.get_attribute_value(
            bank_out_pivot_control.meta_node, bank_out_driver_attr_name)
        bank_out_driven_attr_name = 'translate{}'.format(self.pivot_translate_axis.upper())
        bank_out_driven_attr = '{}.{}'.format(self.yawout.meta_node, bank_out_driven_attr_name)
        current_out_driven_attr_value = dcc.get_attribute_value(self.yawout.meta_node, bank_out_driven_attr_name)

        heel_driven_attr_name = 'translate{}'.format(self.pivot_translate_axis.upper())
        heel_driven_attr = '{}.{}'.format(self.heel.meta_node, heel_driven_attr_name)
        heel_driven_attr_value = dcc.get_attribute_value(self.heel.meta_node, heel_driven_attr_name)

        anim_utils.quick_driven_key(
            source=bank_in_driver_attr, target=bank_in_driven_attr,
            source_values=[current_in_driver_attr_value, -dst_to_move, dst_to_move],
            target_values=[current_in_driven_attr_value, current_in_driven_attr_value - (
                -dst_to_move if is_right else dst_to_move),
                           current_in_driven_attr_value + (-dst_to_move if is_right else dst_to_move)],
            infinite=True)

        anim_utils.quick_driven_key(
            source=bank_in_driver_attr, target=bank_out_driven_attr,
            source_values=[current_in_driver_attr_value, -dst_to_move, dst_to_move],
            target_values=[current_out_driven_attr_value, current_out_driven_attr_value + (
                -dst_to_move if is_right else dst_to_move),
                           current_out_driven_attr_value - (-dst_to_move if is_right else dst_to_move)],
            infinite=True)

        anim_utils.quick_driven_key(
            source=bank_out_driver_attr, target=bank_out_driven_attr,
            source_values=[current_out_driver_attr_value, dst_to_move, -dst_to_move],
            target_values=[current_out_driven_attr_value, current_out_driven_attr_value + (
                -dst_to_move if is_right else dst_to_move),
                           current_out_driven_attr_value - (-dst_to_move if is_right else dst_to_move)], infinite=True)

        anim_utils.quick_driven_key(
            source=bank_out_driver_attr, target=heel_driven_attr,
            source_values=[current_out_driver_attr_value, dst_to_move, -dst_to_move],
            target_values=[heel_driven_attr_value, heel_driven_attr_value - (-dst_to_move if is_right else dst_to_move),
                           current_out_driven_attr_value + (-dst_to_move if is_right else dst_to_move)], infinite=True)


class ExpressionReverseFootRollComponent(ReverseFootRollComponent, object):

    def __init__(self, *args, **kwargs):
        super(ExpressionReverseFootRollComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'footRoll'))
        self.set_foot_control(None)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(ExpressionReverseFootRollComponent, self).create()

        self._create_foot_expressions()

    def _create_roll_attributes(self):

        roll_control = self.foot_control.meta_node

        dcc.add_double_attribute(roll_control, 'footRoll', keyable=True)
        dcc.add_double_attribute(roll_control, 'toeLift', default_value=45, keyable=True)
        dcc.add_double_attribute(roll_control, 'toeStraight', default_value=70, keyable=True)
        dcc.add_double_attribute(roll_control, 'bank', keyable=True)
        dcc.add_double_attribute(roll_control, 'heelRotate', keyable=True)
        dcc.add_double_attribute(roll_control, 'toeRotate', keyable=True)
        dcc.add_double_attribute(roll_control, 'toeWiggle', keyable=True)

    def _create_bank_roll(self):
        pass

    def _create_mid_pivot_rotate(self):
        pass

    def _create_forward_roll(self):
        pass

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_foot_expressions(self):
        """
        Internal function that creates foot roll expressions
        """

        roll_control = dcc.node_short_name(self.foot_control.meta_node)
        yaw_in_joint = dcc.node_short_name(self.yawin.meta_node)
        yaw_out_joint = dcc.node_short_name(self.yawout.meta_node)
        heel_joint = dcc.node_short_name(self.heel.meta_node)
        mid_joint = dcc.node_short_name(self.mid.meta_node)
        toe_joint = dcc.node_short_name(self.toe.meta_node)
        ball_joint = dcc.node_short_name(self.ball.meta_node)
        ankle_joint = dcc.node_short_name(self.ankle.meta_node)

        toe_wiggle_expr = """
        // toe wiggle
        {1}.rotateX = {0}.toeWiggle;
        
        // toe spin                            
        {2}.rotateY = {0}.toeRotate;
        
        // heel spin
        {3}.rotateY = {0}.heelRotate;
        
        // bank in
        {4}.rotateZ = (min(0, {0}.bank)) * -1;
        
        // bank out
        {5}.rotateZ = (max(0, {0}.bank)) * -1;
        
        // foot roll (heel)
        {3}.rotateX = min(0, {0}.footRoll);
        
        // foot roll (toe)
        {2}.rotateX = linstep({0}.toeLift, {0}.toeStraight, {0}.footRoll) * {0}.footRoll;
        
        // foot roll (ball)
        {6}.rotateX = (linstep(0, {0}.toeLift, {0}.footRoll)) * (1 - (linstep({0}.toeLift, {0}.toeStraight, {0}.footRoll))) * {0}.footRoll;
        """.format(roll_control, mid_joint, toe_joint, heel_joint, yaw_in_joint, yaw_out_joint, ball_joint)

        maya.cmds.expression(
            name=self._get_name(self.name, 'footRev', node_type='expression'), string=toe_wiggle_expr)
