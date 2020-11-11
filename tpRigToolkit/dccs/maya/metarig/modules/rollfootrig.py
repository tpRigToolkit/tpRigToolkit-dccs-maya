#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Foot rig implementation for metarig in Maya
"""

import logging

from tpDcc import dcc
from tpDcc.dccs.maya.core import transform as xform_utils

from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import buffer

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class RollFootRig(module.RigModule, mixin.JointMixin, mixin.ControlMixin):
    def __init__(self, *args, **kwargs):
        super(RollFootRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        mixin.ControlMixin.__init__(self)
        self.set_name(kwargs.get('name', 'reverseIkFoot'))
        self.set_create_buffer_joints(True, name_for_switch_attribute='switch')
        self.set_buffer_replace(['jnt', 'buffer'])
        self.set_duplicate_replace(['jnt', 'pivot'])
        self.set_create_roll_controls(True)
        self.set_main_control_follow(None)
        self.set_roll_control_data({})
        self.set_attribute_control(None)
        self.set_pivot_locators(None, None, None)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, *args, **kwargs):
        super(RollFootRig, self).create(*args, **kwargs)

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

        attribute_control = self._get_attribute_control()
        dcc.add_title_attribute(attribute_control.meta_node, 'FOOT_PIVOTS')

        if self.create_roll_controls:
            pass

        self._create_ik_chain()

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

    def set_duplicate_replace(self, list_value):
        """
        Sets whether duplicated reverse foot joints will be renamed its prefix or suffix
        :param list_value: list(str, str)
        """

        if not self.has_attr('duplicate_replace'):
            self.add_attribute(attr='duplicate_replace', value=list_value, attr_type='string')
        else:
            self.duplicate_replace = list_value

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

    def _create_ik_chain(self):
        """
        Internal function that creates main Ik chain for reverse foot rig
        """

        buffer_component = self.get_component_by_class(buffer.BufferComponent)
        if not buffer_component:
            LOGGER.warning('Impossible to create reverse foot rig Ik chain. No buffer component found!')
            return

        buffer_joints = buffer_component.get_buffer_joints(as_meta=False)
        duplicate = xform_utils.DuplicateHierarchy(buffer_joints[0])
        duplicate.only_these(buffer_joints)

        if self.create_buffer_joints:
            duplicate.set_replace(self.buffer_replace[1], self.duplicate_replace[1])
        else:
            duplicate.set_replace(self.duplicate_replace[0], self.duplicate_replace[1])

        joints = duplicate.create()

        parent = dcc.node_parent(joints[0])
        if parent != self.setup_group.meta_node:
            dcc.set_parent(joints[0], self.setup_group)

        self.message_list_connect('ik_joints', joints)

        # Attach Ik joints to the buffer joints
        for i in range(len(joints)):
            dcc.create_parent_constraint(buffer_joints[i], joints[i])

        ik_joints = self.message_list_get('ik_joints')

        self.add_attribute(attr='ankle', value=ik_joints[0], attr_type='messageSimple')
        self.add_attribute(attr='ball', value=ik_joints[1], attr_type='messageSimple')
        self.add_attribute(attr='toe', value=ik_joints[2], attr_type='messageSimple')

        return ik_joints

    def _create_pivot(self, name, transform, parent):
        pivot_joint, pivot_root, pivot_driver = self._create_pivot_joint(transform, name)
        dcc.set_parent(pivot_root, parent)

        return pivot_joint

    def _create_pivot_joint(self, source_transform, name):

        dcc.clear_selection()
        new_joint = dcc.create_joint(
            name=self._get_name(self.name, '{}Pivot'.format(name), node_type='joint'), size=2.0)
        xform_utils.MatchTransform(source_transform, new_joint).translation()
        xform_utils.MatchTransform(self.get_joints(as_meta=False)[-1], new_joint)
        joint_buffer = dcc.create_buffer_group(new_joint)
        joint_driver = dcc.create_buffer_group(joint_buffer, suffix='driver')

        # attribute_control = self._get_attribute_control()
        # attribute_name = '{}Pivot'.format(name)
        # dcc.add_double_attribute(attribute_control.meta_node, attribute_name, keyable=True)
        # dcc.connect_attribute(attribute_control.meta_node, attribute_name, joint_buffer, 'rotateY')

        return new_joint, joint_buffer, joint_driver
