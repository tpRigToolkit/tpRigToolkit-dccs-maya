#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Ik Limb rig implementation for metarig in Maya
"""

from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import ikchain


class IkLimbRig(module.RigModule, mixin.JointMixin, mixin.ControlMixin):
    def __init__(self, *args, **kwargs):
        super(IkLimbRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        mixin.ControlMixin.__init__(self)
        self.set_name(kwargs.get('name', 'ikLimb'))
        self.set_create_buffer_joints(True, name_for_switch_attribute='switch')
        self.set_buffer_replace(['jnt', 'buffer'])
        self.set_right_side_fix(True)
        self.set_create_ik_buffer_joint(True)
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

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, *args, **kwargs):
        super(IkLimbRig, self).create(*args, **kwargs)

        joints = self.get_joints()

        ik_rig = ikchain.IkChainComponent(name='ikLimbRig{}'.format(self.side.title()))
        self.add_component(ik_rig)
        ik_rig.add_joints(joints)
        ik_rig.set_control_data(self.control_data)
        ik_rig.set_create_buffer_joints(self.create_buffer_joints)
        ik_rig.set_create_sub_controls(self.create_sub_controls)
        ik_rig.set_create_switch(True)
        ik_rig.create()

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
