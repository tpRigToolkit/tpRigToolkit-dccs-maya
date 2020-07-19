#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Reverse Foot rig implementation for metarig in Maya
"""

"""
NOTES
============================

When setting an IK leg setup, to connect the IK leg with this module we need to parent
the leg Ik to the reverse ankle joint
"""

import tpDcc as tp
from tpDcc.dccs.maya.meta import metanode
from tpDcc.dccs.maya.core import transform as xform_utils, ik as ik_utils

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import buffer, reversefootroll


class JointReverseFootRig(module.RigModule, mixin.JointMixin, mixin.ControlMixin):
    def __init__(self, *args, **kwargs):
        super(JointReverseFootRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        mixin.ControlMixin.__init__(self)
        self.set_name(kwargs.get('name', 'jointReverseIkFoot'))
        self.set_create_buffer_joints(True, name_for_switch_attribute='switch')
        self.set_buffer_replace(['jnt', 'buffer'])
        self.set_create_foot_roll(True)
        self.set_main_control(None)
        self.set_roll_control_data({})
        self.set_attribute_control(None)
        self.set_pivot_locators(None, None, None)
        self.set_ik_leg(None)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, *args, **kwargs):
        super(JointReverseFootRig, self).create(*args, **kwargs)

        joints = self.get_joints()

        buffer_rig = buffer.BufferComponent(name='reverseFootBuffer')
        self.add_component(buffer_rig)
        buffer_rig.add_joints(joints)
        buffer_rig.set_create_buffer_joints(
            self.create_buffer_joints, self.switch_attribute_name, self.switch_node_name)
        buffer_rig.set_create_sub_controls(False)
        buffer_rig.set_buffer_replace(self.buffer_replace)
        buffer_rig.create()

        buffer_joints = buffer_rig.get_buffer_joints() or joints

        if not self.ik_leg:
            if self.main_control_follow:
                self._create_main_control(self.main_control_follow)
            else:
                self._create_main_control(buffer_joints[0])
        else:
            self.set_main_control(self.ik_leg.bottom_control)

        self._create_reverse_chain()
        reverse_joints_chain = self.get_reverse_joints_chain()

        # TODO: Should we check if create buffer joints is True?
        # if self.create_buffer_joints:
        ankle_joint = buffer_joints[0]
        if ankle_joint.has_attr('group_buffer') and ankle_joint.group_buffer:
            ankle_joint = ankle_joint.group_buffer.meta_node
        else:
            ankle_joint = ankle_joint.meta_node

        if self.create_foot_roll:
            foot_roll = reversefootroll.ReverseFootRollComponent(name='reverseFootRoll')
            self.add_component(foot_roll)
            foot_roll.add_joints(reverse_joints_chain)
            foot_roll.set_ik_leg_control(self.main_control)
            foot_roll.set_roll_control_data(self.roll_control_data)
            foot_roll.create()
            tp.Dcc.create_point_constraint(ankle_joint, reverse_joints_chain[-1].meta_node)
        else:
            if self.ik_leg:
                tp.Dcc.create_parent_constraint(ankle_joint, self.ik_leg.bottom_control.meta_node)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_reverse_joints_chain(self, as_meta=True):
        """
        Returns revere joints chain
        :param as_meta: bool
        :return:
        """

        return self.message_list_get('reverse_joints', as_meta=as_meta)

    def set_create_buffer_joints(self, flag, name_for_switch_attribute=None, name_for_switch_node=None):
        """
        Sets whether or not buffer chain should be created
        :param flag: bool
        :param name_for_switch_attribute: str
        :param name_for_switch_node: str
        """

        name_for_switch_attribute = name_for_switch_attribute or ''
        name_for_switch_node = name_for_switch_node or ''

        if not self.has_attr('create_buffer_joints'):
            self.add_attribute('create_buffer_joints', value=flag, attr_type='bool')
        else:
            self.create_buffer_joints = flag

        if not self.has_attr('switch_attribute_name'):
            self.add_attribute('switch_attribute_name', name_for_switch_attribute or '')
        else:
            self.switch_attribute_name = name_for_switch_attribute

        if not self.has_attr('switch_node_name'):
            self.add_attribute('switch_node_name', name_for_switch_node or '')
        else:
            self.switch_node_name = name_for_switch_node

    def set_buffer_replace(self, list_value):
        """
        Sets whether buffer joints will be renamed its prefix or suffix
        :param list_value: list(str, str)
        """

        if not self.has_attr('buffer_replace'):
            self.add_attribute(attr='buffer_replace', value=list_value, attr_type='string')
        else:
            self.buffer_replace = list_value

    def set_attribute_control(self, transform):
        """
        Sets the control that will stores the foot attributes
        :param transform: str
        """

        if not self.has_attr('attribute_control'):
            self.add_attribute(attr='attribute_control', value=transform, attr_type='messageSimple')
        else:
            self.attribute_control = transform

    def set_roll_control_data(self, control_data):
        """
        Sets the control data used by the roll control
        :param control_data: dict
        """

        if not self.has_attr('roll_control_data'):
            self.add_attribute(attr='roll_control_data', value=control_data)
        else:
            self.roll_control_data = control_data

    def set_main_control(self, transform):
        """

        :param transform:
        :return:
        """

        if not self.has_attr('main_control'):
            self.add_attribute(attr='main_control', value=transform, attr_type='messageSimple')
        else:
            self.main_control = transform

    def set_create_foot_roll(self, flag):
        """
        Sets whether or not foot roll functionality should be added
        :param flag: bool
        """

        if not self.has_attr('create_foot_roll'):
            self.add_attribute('create_foot_roll', value=flag, attr_type='bool')
        else:
            self.create_foot_roll = flag

    def set_pivot_locators(self, heel, yaw_in, yaw_out):
        """
        Sets the locators that will be used to setup the reverse foot setup
        :param heel: str
        :param yaw_in: str
        :param yaw_out: str
        """

        if not self.has_attr('heel_pivot_locator'):
            self.add_attribute(attr='heel_pivot_locator', value=heel, attr_type='messageSimple')
        else:
            self.heel_pivot_locator = heel

        if not self.has_attr('yaw_in_pivot_locator'):
            self.add_attribute(attr='yaw_in_pivot_locator', value=heel, attr_type='messageSimple')
        else:
            self.yaw_in_pivot_locator = yaw_in

        if not self.has_attr('yaw_out_pivot_locator'):
            self.add_attribute(attr='yaw_out_pivot_locator', value=heel, attr_type='messageSimple')
        else:
            self.yaw_out_pivot_locator = yaw_out

    def set_ik_leg(self, node):
        """
        Sets the node of the Ik leg this node should be attached to
        :param node:
        :return:
        """

        if not self.has_attr('ik_leg'):
            self.add_attribute('ik_leg', value=node, attr_type='messageSimple')
        else:
            self.ik_leg = node

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_main_control(self, transform=None):
        """
        Internal function that creates main control for reverse foot rig setup
        :param transform: match transform to given transform node
        :return:
        """

        main_control = self.create_control('roll', control_data=self.roll_control_data)
        main_control.create_root()
        main_control.hide_scale_and_visibility_attributes()
        if transform:
            main_control.match_translation_and_rotation(transform)

        self.set_main_control(main_control)

    def _create_reverse_chain(self):
        """
        Internal function
        :return:
        """

        buffer_component = self.get_component_by_class(buffer.BufferComponent)
        if not buffer_component:
            tpRigToolkit.logger.warning('Impossible to create reverse foot rig Ik chain. No buffer component found!')
            return

        buffer_joints = buffer_component.get_buffer_joints(as_meta=False)

        # yaw_in_pivot = self._create_pivot('yawIn', self.yaw_in_pivot_locator.meta_node, self.setup_group.meta_node)
        yaw_in_pivot = self._create_pivot('yawIn', self.yaw_in_pivot_locator.meta_node, self.controls_group.meta_node)
        yaw_out_pivot = self._create_pivot('yawOut', self.yaw_out_pivot_locator.meta_node, yaw_in_pivot)
        heel_pivot = self._create_pivot('heel', self.heel_pivot_locator.meta_node, yaw_out_pivot)
        mid_pivot = self._create_pivot('mid', buffer_joints[1], heel_pivot)
        toe_pivot = self._create_pivot('toe', buffer_joints[2], mid_pivot)
        ball_pivot = self._create_pivot('ball', buffer_joints[1], toe_pivot)
        ankle_pivot = self._create_pivot('ankle', buffer_joints[0], ball_pivot)

        reverse_joints = [yaw_in_pivot, yaw_out_pivot, heel_pivot, mid_pivot, toe_pivot, ball_pivot, ankle_pivot]
        self.message_list_connect(
            'reverse_joints',
            [metanode.validate_obj_arg(joint, 'MetaObject', update_class=True) for joint in reverse_joints])

        # Create IKs
        ankle_handle = self._create_ik_handle('ankle', buffer_joints[0], buffer_joints[1])
        ball_handle = self._create_ik_handle('ball', buffer_joints[1], buffer_joints[2])

        tp.Dcc.set_parent(ankle_handle, self.setup_group.meta_node)
        tp.Dcc.set_parent(ball_handle, self.setup_group.meta_node)

        self.add_attribute(
            attr='ankle_ik_handle', value=metanode.validate_obj_arg(ankle_handle, 'MetaObject', update_class=True),
            attr_type='messageSimple')
        self.add_attribute(
            attr='ball_ik_handle', value=metanode.validate_obj_arg(ball_handle, 'MetaObject', update_class=True),
            attr_type='messageSimple')

        tp.Dcc.set_parent(ankle_handle, ball_pivot)
        tp.Dcc.set_parent(ball_handle, toe_pivot)

        if self.ik_leg:
            if tp.Dcc.attribute_exists(yaw_in_pivot, 'group_buffer'):
                yaw_in_pivot = tp.Dcc.get_message_input(yaw_in_pivot, 'group_buffer')
            tp.Dcc.create_parent_constraint(yaw_in_pivot, self.ik_leg.bottom_control.meta_node, maintain_offset=True)

    def _create_pivot(self, name, transform, parent):
        pivot_joint, pivot_root = self._create_pivot_joint(transform, name)
        tp.Dcc.set_parent(pivot_root, parent)

        return pivot_joint

    def _create_pivot_joint(self, source_transform, name):

        tp.Dcc.clear_selection()
        new_joint = tp.Dcc.create_joint(
            name=self._get_name(self.name, '{}Pivot'.format(name), node_type='joint'), size=2.0)
        joint_buffer = tp.Dcc.create_buffer_group(new_joint)
        xform_utils.MatchTransform(source_transform, joint_buffer).translation()
        xform_utils.MatchTransform(self.get_joints(as_meta=False)[-1], joint_buffer).rotation()

        return new_joint, joint_buffer

    def _create_ik_handle(self, name, start_joint, end_joint):
        name = self._get_name(self.name, name, node_type='ikHandle')
        ik_handle = ik_utils.IkHandle(name)
        ik_handle.set_solver(ik_utils.IkHandle.SOLVER_SC)
        ik_handle.set_start_joint(start_joint)
        ik_handle.set_end_joint(end_joint)

        return ik_handle.create()
