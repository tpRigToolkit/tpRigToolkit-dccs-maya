#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base IK chain rig metarig implementation for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode
from tpDcc.dccs.maya.core import ik as ik_utils, rig as rig_utils

from tpRigToolkit.dccs.maya.metarig.components import buffer


class IkChainComponent(buffer.BufferComponent, object):

    def __init__(self, *args, **kwargs):
        super(IkChainComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'ikChain'))
        self.set_create_buffer_joints(True, name_for_switch_attribute='switch')
        self.set_buffer_replace([['jnt', 'je'], ['ikJnt', 'ikJe']])
        self.set_right_side_fix(True)
        self.set_create_ik_buffer_joint(False)
        self.set_create_top_control(True)
        self.set_create_pole_vector(True)
        self.set_top_control_as_locator(False)
        self.set_negate_right_scale(False)
        self.set_pole_vector_control_data({})
        self.set_pole_vector_visibility(True)
        self.set_pole_angle_joints([])
        self.set_pole_vector_control_offset(1.0)
        self.set_match_bottom_control_to_joint(True)
        self.set_orient_constraint(True)
        self.set_create_sub_controls(False)
        self.set_create_switch(True)
        self.set_joint_index_to_handle(-1)

    # ==============================================================================================
    # OVERRIDES
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

    def create(self):
        super(IkChainComponent, self).create()

        joints = self.get_joints()
        buffer_joints = self.get_buffer_joints() or joints

        if not self.message_list_get('ik_chain', as_meta=False):
            self.message_list_connect('ik_chain', buffer_joints)
        else:
            self.message_list_purge('ik_chain')
            for buffer_joint in buffer_joints:
                self.message_list_append('ik_chain', buffer_joint)

        self._create_ik_handle()

        # if self.create_buffer_joints:
        #     ik_group = self._create_setup_group('ik')
        #     buffer_joints[0].set_parent(ik_group)

        if self.create_top_control:
            self._create_top_control()
        self._create_pole_vector_control()
        self._create_bottom_control()

        if self.create_pole_vector:
            self._create_pole_vector()
            if self.create_top_control:
                maya.cmds.controller(self.pole_vector_control.meta_node, self.top_control.meta_node, p=True)
                maya.cmds.controller(self.bottom_control.meta_node, self.pole_vector_control.meta_node, p=True)
        else:
            if self.create_top_control:
                maya.cmds.controller(self.bottom_control.meta_node, self.top_control.meta_node, p=True)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_ik_chain(self, as_meta=True):
        """
        Returns joints used by Ik chain
        :param as_meta: bool
        """

        return self.message_list_get('ik_chain', as_meta=as_meta)

    def get_pole_angle_joints(self, as_meta=True):
        """
        Returns joints used to calculate the proper position of the pole vector control
        :param as_meta: bool
        """

        return self.message_list_get('pole_angle_joints', as_meta=as_meta)

    def set_right_side_fix(self, flag):
        """
        Sets whether compensation for right side orientation should be applied or not
        :param flag: bool
        """

        if not self.has_attr('right_side_fix'):
            self.add_attribute(attr='right_side_fix', value=flag, attr_type='bool')
        else:
            self.right_side_fix = flag

    def set_create_ik_buffer_joint(self, flag):
        """
        Sets whether or not a buffer should be created in the end IK joint (usually wrist or elbow)
        Used to fix IK offset problems while Ik limb stretching.
        :param flag: bool
        :return:
        """

        if not self.has_attr('create_ik_buffer_joint'):
            self.add_attribute(attr='create_ik_buffer_joint', value=flag, attr_type='bool')
        else:
            self.create_ik_buffer_joint = flag

    def set_create_top_control(self, flag):
        """
        Sets whether or not top control should be created
        :param flag: bool
        """

        if not self.has_attr('create_top_control'):
            self.add_attribute(attr='create_top_control', value=flag, attr_type='bool')
        else:
            self.create_top_control = flag

    def set_create_pole_vector(self, flag):
        """
        Sets whether or not pole vector control should be created
        :param flag: bool
        """

        if not self.has_attr('create_pole_vector'):
            self.add_attribute(attr='create_pole_vector', value=flag, attr_type='bool')
        else:
            self.create_pole_vector = flag

    def set_top_control_as_locator(self, flag):
        """
        Sets whether or not top control should be a locator instead of curve control
        :param flag: bool
        """

        if not self.has_attr('top_control_as_locator'):
            self.add_attribute(attr='top_control_as_locator', value=flag, attr_type='bool')
        else:
            self.top_control_as_locator = flag

    def set_negate_right_scale(self, flag, scale_x=-1, scale_y=-1, scale_z=-1):
        """
        Sets whether the scale of the right side will be negatived. Also we can define the scale values that will
        be applied (by default, (-1, -1, -1)).
        :param flag: bool
        :param scale_x: int
        :param scale_y: int
        :param scale_z: int
        """

        if not self.has_attr('negate_right_scale'):
            self.add_attribute(attr='negate_right_scale', value=flag, attr_type='bool')
        else:
            self.negate_right_scale = flag

        if not self.has_attr('negate_right_scale_values'):
            self.add_attribute(attr='negate_right_scale_values', value=[scale_x, scale_y, scale_z])
        else:
            self.negate_right_scale_values = [scale_x, scale_y, scale_z]

    def set_pole_vector_control_data(self, control_data):
        """
        Sets the control data used for pole vector control
        :param control_data: dict
        """

        if not self.has_attr('pole_vector_control_data'):
            self.add_attribute(attr='pole_vector_control_data', value=control_data)
        else:
            self.pole_vector_control_data = control_data

    def set_pole_vector_visibility(self, flag):
        """
        Sets whether or not pole vector control is visible by default
        :return: bool
        """

        if not self.has_attr('pole_vector_visibility'):
            self.add_attribute(attr='pole_vector_visibility', value=flag, attr_type='bool')
        else:
            self.pole_vector_visibility = flag

    def set_pole_angle_joints(self, joints):
        """
        Sets the joints the pole angle is calculated from
        :param joints: list
        """

        if not self.message_list_get('pole_angle_joints', as_meta=False):
            self.message_list_connect('pole_angle_joints', joints)
        else:
            self.message_list_purge('pole_angle_joints')
            for joint in joints:
                self.message_list_append('pole_angle_joints', joint)

    def set_pole_vector_control_offset(self, value):
        """
        Sets the amount of distance the pole vector control should offset from the mid Ik chain joint
        :param value: float
        """

        if not self.has_attr('pole_vector_control_offset'):
            self.add_attribute(attr='pole_vector_control_offset', value=value, attr_type='float')
        else:
            self.pole_vector_control_offset = value

    def set_match_bottom_control_to_joint(self, flag):
        """
        Sets whether or not to match orientation at th end effector control to the bottom joint or just match
        translation
        :param flag: bool
        """

        if not self.has_attr('match_bottom_control_to_joint'):
            self.add_attribute(attr='match_bottom_control_to_joint', value=flag, attr_type='bool')
        else:
            self.match_bottom_control_to_joint = flag

    def set_orient_constraint(self, flag):
        """
        Sets whether or not the end effector should control the orientation of the Ik handle
        :param flag: bool
        """

        if not self.has_attr('orient_constraint'):
            self.add_attribute(attr='orient_constraint', value=flag, attr_type='bool')
        else:
            self.orient_constraint = flag

    def set_joint_index_to_handle(self, value):
        """
        Sets the index of the joint that Ik handle will be applied to. -1 means last joint of the Ik chain
        :param value: int
        """

        if not self.has_attr('jont_index_to_handle'):
            self.add_attribute(attr='jont_index_to_handle', value=value)
        else:
            self.jont_index_to_handle = value

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _fix_right_side_orient(self, control):
        """
        Internal function that fixes right side control to reverse orientation on YZ channels
        :param control: str, name of the control we want to fix orient of
        """

        if not self.right_side_fix or not tp.Dcc.name_is_right(side=self.side):
            return

        xform_locator = tp.Dcc.create_locator()
        tp.Dcc.match_translation_rotation(control, xform_locator)

        buffer_group = tp.Dcc.create_buffer_group(xform_locator)
        tp.Dcc.set_attribute_value(xform_locator, 'rotateY', 180)
        tp.Dcc.set_attribute_value(xform_locator, 'rotateZ', 180)
        tp.Dcc.match_translation_rotation(xform_locator, control)

        tp.Dcc.delete_object(buffer_group)

    def _create_ik_handle(self):
        """
        Internal function that creates the Ik handle for the Ik limb rig
        :return:
        """

        ik_chain = self.get_ik_chain()

        if self.create_ik_buffer_joint:
            buffer_joint = self._create_buffer_joint()
        else:
            buffer_joint = ik_chain[self.jont_index_to_handle].meta_node

        ik_solver = ik_utils.IkHandle.SOLVER_RP
        ik_handle = tp.Dcc.create_ik_handle(
            self._get_name(self.name, 'ikHandle', node_type='ikHandle'),
            start_joint=ik_chain[0].meta_node, end_joint=buffer_joint, solver_type=ik_solver)
        if self.create_ik_buffer_joint:
            ik_handle_buffer = tp.Dcc.create_buffer_group(ik_handle)

        ik_handle = metanode.validate_obj_arg(ik_handle, 'MetaObject', update_class=True)
        self.add_attribute('ik_handle', value=ik_handle, attr_type='messageSimple')

        if self.create_ik_buffer_joint:
            tp.Dcc.set_parent(ik_handle_buffer, self.setup_group.meta_node)
            tp.Dcc.hide_node(ik_handle_buffer)
        else:
            tp.Dcc.set_parent(ik_handle.meta_node, self.setup_group.meta_node)
            tp.Dcc.hide_node(ik_handle.meta_node)

    def _create_buffer_joint(self):
        """
        Internal function that creates a buffer joint on top of the end joint of the Ik chain
        The scale of this buffer is connected to the inverseScale of the child joint
        :return: str, new created buffer joint
        """

        ik_chain = self.get_ik_chain()

        buffer_joint = tp.Dcc.duplicate_object(ik_chain[self.jont_index_to_handle].meta_node, only_parent=True)
        tp.Dcc.set_parent(ik_chain[self.jont_index_to_handle].meta_node, buffer_joint)
        if not tp.Dcc.is_attribute_connected_to_attribute(
                buffer_joint, 'scale', ik_chain[self.jont_index_to_handle].meta_node, 'inverseScale'):
            tp.Dcc.connect_attribute(
                buffer_joint, 'scale', ik_chain[self.jont_index_to_handle].meta_node, 'inverseScale')

        for axis in 'XYZ':
            for attr_name in ['rotate', 'jointOrient']:
                tp.Dcc.set_attribute_value(
                    ik_chain[self.jont_index_to_handle].meta_node, '{}{}'.format(attr_name, axis), 0)

        return buffer_joint

    def _create_top_control(self):
        """
        Internal function that creates the top control used by the Ik leg rig setup
        """

        if not self.create_top_control:
            return

        ik_chain = self.get_ik_chain()

        if self.top_control_as_locator:
            top_control = tp.Dcc.create_locator(name=self._get_name(self.name, 'topLocator', node_type='locator'))
            top_control = metanode.validate_obj_arg(top_control, 'MetaObject', update_class=True)
        else:
            top_control = self.create_control('topControl')
        tp.Dcc.hide_rotate_attributes(top_control.meta_node)
        tp.Dcc.hide_scale_and_visibility_attributes(top_control.meta_node)

        self.add_attribute(attr='top_control', value=top_control, attr_type='messageSimple')

        if self.top_control_as_locator:
            root_group = top_control
        else:
            root_group = self.top_control.create_root()

        tp.Dcc.match_translation_rotation(ik_chain[0].meta_node, root_group.meta_node)

        self._fix_right_side_orient(root_group.meta_node)

        if self.negate_right_scale and tp.Dcc.name_is_right(side=self.side):
            for i, axis in enumerate('XYZ'):
                tp.Dcc.set_attribute_value(
                    root_group.meta_node, 'scale{}'.format(axis), self.negate_right_scale_values[i])

        tp.Dcc.create_parent_constraint(ik_chain[0].meta_node, top_control.meta_node, maintain_offset=True)

    def _create_bottom_control(self):
        """
        Internal function that creates bottom control of the Ik limb rig setup
        :return: str
        """

        ik_chain = self.get_ik_chain()

        bottom_control = self.create_control('bottom')
        bottom_control.hide_scale_and_visibility_attributes()

        self.add_attribute(attr='bottom_control', value=bottom_control, attr_type='messageSimple')

        if self.create_sub_controls:
            sub_control = self.create_control('bottom', sub=True, visibility_parent_control=bottom_control)
            sub_control.hide_scale_and_visibility_attributes()
            sub_control_buffer = sub_control.create_root()

            self.add_attribute(attr='bottom_sub_control', value=sub_control, attr_type='messageSimple')

            sub_control_buffer.set_parent(bottom_control)

        bottom_control_buffer = bottom_control.create_root()
        bottom_control.create_auto()

        if self.match_bottom_control_to_joint:
            tp.Dcc.match_translation_rotation(
                ik_chain[self.jont_index_to_handle].meta_node, bottom_control_buffer.meta_node)
        else:
            tp.Dcc.match_translation(ik_chain[self.jont_index_to_handle].meta_node, bottom_control_buffer.meta_node)

        self._fix_right_side_orient(bottom_control_buffer.meta_node)

        if self.negate_right_scale and tp.Dcc.name_is_right(self.side):
            for i, axis in enumerate('XYZ'):
                tp.Dcc.set_attribute_value(bottom_control_buffer.meta_node, 'scale', self.negate_right_scale_values[i])

        # TODO: Create world switch?????

        tp.Dcc.create_point_constraint(self.ik_handle.meta_node, bottom_control.meta_node)

        # ik_handle_parent = tp.Dcc.node_parent(self.ik_handle.meta_node)
        # if self.create_sub_controls:
        #     tp.Dcc.set_parent(ik_handle_parent, sub_control.meta_node)
        # else:
        #     tp.Dcc.set_parent(ik_handle_parent, bottom_control.meta_node)

        if self.orient_constraint:
            if self.create_sub_controls:
                tp.Dcc.create_orient_constraint(
                    ik_chain[self.jont_index_to_handle].meta_node, sub_control.meta_node, maintain_offset=True)
            else:
                tp.Dcc.create_orient_constraint(
                    ik_chain[self.jont_index_to_handle].meta_node, bottom_control.meta_node, maintain_offset=True)

    def _create_pole_vector_control(self):
        """
        Internal function that creates control that manages Ik handle pole vector
        """

        pole_vector_control = None
        if self.create_pole_vector:
            pole_vector_control = self.create_control(
                'poleVector', curve_type='cube', control_data=self.pole_vector_control_data)
            pole_vector_control.hide_rotate_attributes()
            pole_vector_control.hide_scale_and_visibility_attributes()

        self.add_attribute(attr='pole_vector_control', value=pole_vector_control, attr_type='messageSimple')

    def _create_pole_vector(self):

        bottom_control = self.bottom_control
        pole_vector_control = self.pole_vector_control

        tp.Dcc.add_title_attribute(bottom_control.meta_node, 'POLE_VECTOR')
        tp.Dcc.add_bool_attribute(bottom_control.meta_node, 'poleVisibility', default_value=self.pole_vector_visibility)

        tp.Dcc.add_integer_attribute(self.bottom_control.meta_node, 'twist')
        if tp.Dcc.name_is_left(self.side):
            tp.Dcc.connect_attribute(self.bottom_control.meta_node, 'twist', self.ik_handle.meta_node, 'twist')
        else:
            multiply_name = self._get_name(self.name, 'poleVectorTwistMult', node_type='multiply')
            tp.Dcc.connect_multiply(
                self.bottom_control.meta_node, 'twist', self.ik_handle.meta_node, 'twist',
                value=-1, multiply_name=multiply_name)

        pole_joints = self._get_pole_joints(as_meta=False)

        pole_vector_buffer_group = pole_vector_control.create_root()

        # TODO: This offset should take into account the scale of the character and (the control?)
        # TODO: The movement of the pole vector should be optional. Add argument to support that.
        pole_vector_position = tp.Dcc.get_pole_vector_position(
            pole_joints[0], pole_joints[1], pole_joints[2], offset=self.pole_vector_control_offset)
        tp.Dcc.move_node(
            pole_vector_buffer_group.meta_node,
            pole_vector_position[0], pole_vector_position[1], pole_vector_position[2])
        # tp.Dcc.match_translation(pole_joints[1], pole_vector_buffer_group.meta_node)

        self._create_pole_vector_constraint()

        name = self._get_name(self.name, 'poleVectorLine', node_type='poleVector')
        rig_line = rig_utils.RiggedLine(pole_joints[1], pole_vector_control.meta_node, name).create()
        tp.Dcc.set_parent(rig_line, self.controls_group.meta_node)

        tp.Dcc.connect_attribute(
            bottom_control.meta_node, 'poleVisibility', pole_vector_buffer_group.meta_node, 'visibility')
        tp.Dcc.connect_attribute(bottom_control.meta_node, 'poleVisibility', rig_line, 'visibility')

    def _get_pole_joints(self, as_meta=True):
        """
        Returns all joints used to setup pole vector angle
        :return: list(str)
        """

        if not self.has_attr('pole_angle_joints') or not self.pole_angle_joints:
            ik_chain = self.get_ik_chain(as_meta=as_meta)
            ik_chain_length = len(ik_chain)
            mid_joint_index = int(len(ik_chain) / 2)
            if ik_chain_length > 3:
                mid_joint_index -= 1
            mid_joint = ik_chain[mid_joint_index]
            pole_angle_joints = [ik_chain[0], mid_joint, ik_chain[self.jont_index_to_handle]]
            self.set_pole_angle_joints(pole_angle_joints)
        else:
            pole_angle_joints = self.get_pole_angle_joints(as_meta=as_meta)

        return pole_angle_joints

    def _create_pole_vector_constraint(self):
        """
        Internal function that creates the pole vector constraint used by the Ik limb rig
        """

        pole_vector_constraint = tp.Dcc.create_pole_vector_constraint(
            self.pole_vector_control.meta_node, self.ik_handle.meta_node)
        pole_vector_constraint = metanode.validate_obj_arg(pole_vector_constraint, 'MetaNode', update_class=True)
        self.add_attribute('pole_vector_constraint', value=pole_vector_constraint, attr_type='messageSimple')
