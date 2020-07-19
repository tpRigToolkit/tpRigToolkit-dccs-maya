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
from tpDcc.dccs.maya.core import transform as xform_utils, joint as joint_utils, ik as ik_utils

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import buffer


class ReverseFootRig(module.RigModule, mixin.JointMixin, mixin.ControlMixin):
    def __init__(self, *args, **kwargs):
        super(ReverseFootRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        mixin.ControlMixin.__init__(self)
        self.set_name(kwargs.get('name', 'reverseIkFoot'))
        self.set_create_buffer_joints(True, name_for_switch_attribute='switch')
        self.set_buffer_replace(['jnt', 'buffer'])
        self.set_create_roll_controls(True)
        self.set_main_control_follow(None)
        self.set_roll_control_data({})
        self.set_attribute_control(None)
        self.set_pivot_locators(None, None, None)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, *args, **kwargs):
        super(ReverseFootRig, self).create(*args, **kwargs)

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

        if self.main_control_follow:
            self._create_roll_control(self.main_control_follow)
        else:
            self._create_roll_control(buffer_joints[0])

        self._create_reverse_chain()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

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

    def set_main_control_follow(self, transform):
        """

        :param transform:
        :return:
        """

        if not self.has_attr('main_control_follow'):
            self.add_attribute(attr='main_control_follow', value=transform, attr_type='messageSimple')
        else:
            self.main_control_follow = transform

    def set_create_roll_controls(self, flag):
        """
        Sets whether roll controls should be created or not
        :param flag: bool
        """

        if not self.has_attr('create_roll_controls'):
            self.add_attribute('create_roll_controls', value=flag, attr_type='bool')
        else:
            self.create_roll_controls = flag

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

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _get_attribute_control(self):
        return self.attribute_control if self.attribute_control else self.roll_control

    def _create_roll_control(self, transform):

        roll_control = self.create_control('roll', control_data=self.roll_control_data)
        roll_control.scale_control_shapes((0.8, 0.8, 0.8))
        roll_control.create_root()
        roll_control.hide_keyable_attributes()
        roll_control.match_translation_and_rotation(transform)

        self.add_attribute('roll_control', roll_control, attr_type='messageSimple')

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
        ankle_handle = self._create_ik_handle('ankle', ball_pivot, ankle_pivot)
        ball_handle = self._create_ik_handle('ball', toe_pivot, ball_pivot)
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

    def _create_pivot(self, name, transform, parent):
        pivot_joint, pivot_root = self._create_pivot_joint(transform, name)
        tp.Dcc.set_parent(pivot_root, parent)

        return pivot_joint

    def _create_pivot_joint(self, source_transform, name):

        tp.Dcc.clear_selection()
        new_joint = tp.Dcc.create_joint(
            name=self._get_name(self.name, '{}Pivot'.format(name), node_type='joint'), size=2.0)
        xform_utils.MatchTransform(source_transform, new_joint).translation()
        xform_utils.MatchTransform(self.get_joints(as_meta=False)[-1], new_joint).rotation()
        joint_buffer = tp.Dcc.create_buffer_group(new_joint)

        return new_joint, joint_buffer

    def _create_ik_handle(self, name, start_joint, end_joint):
        name = self._get_name(self.name, name, node_type='ikHandle')
        ik_handle = ik_utils.IkHandle(name)
        ik_handle.set_solver(ik_utils.IkHandle.SOLVER_SC)
        ik_handle.set_start_joint(start_joint)
        ik_handle.set_end_joint(end_joint)

        return ik_handle.create()
