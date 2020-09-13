#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains buffer rig metarig implementations for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
from tpDcc.dccs.maya.core import joint as joint_utils, transform as xform_utils

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.components import joint, attach


class BufferComponent(joint.JointComponent, object):
    def __init__(self, *args, **kwargs):
        super(BufferComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_attach_joints(True)
        self.set_build_hierarchy(False)
        self.set_create_buffer_joints(True, name_for_switch_attribute='switch')
        self.set_attach_type(attach.AttachJointsComponent.ATTACH_TYPE_CONSTRAINT)
        self.set_buffer_replace(['jnt', 'buffer'])
        self.set_create_switch(False)
        self.set_switch_controls_group(None)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(BufferComponent, self).create()

        if self.create_buffer_joints:
            buffer_joints = self._duplicate_joints()
            joints = self.get_joints(as_meta=False)

            attach_component = attach.AttachJointsComponent(name='{}Attach'.format(self.name))
            attach_component.set_attach_joints(True)
            attach_component.set_source_and_target_joints(source_joints=buffer_joints, target_joints=joints)
            attach_component.set_create_switch(self.create_switch)
            attach_component.set_switch_controls_group(self.switch_controls_group or self.controls_group)
            self.add_component(attach_component)
            attach_component.create()
            attach_component.delete_setup()
            attach_component.delete_control()

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def add_joints(self, joints, clean=False):
        """
         Appends new joints to the module
         :param joints: list<variant>
         """

        joints = super(BufferComponent, self).add_joints(joints=joints, clean=clean)

        if len(joints) <= 0:
            return

        if not self.message_list_get('buffer_joints', as_meta=False):
            self.message_list_connect('buffer_joints', joints)
        else:
            if clean:
                self.message_list_purge('buffer_joints')
            for jnt in joints:
                self.message_list_append('buffer_joints', jnt)

        return joints

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_buffer_joints(self, as_meta=True):
        """
        Returns a list of buffer joints
        :return: list
        """

        return self.message_list_get('buffer_joints', as_meta=as_meta)

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

    def set_build_hierarchy(self, flag):
        """
        Sets whether or not buffer joint hierarchy should be duplicated or build from scratch
        :param flag: bool
        """

        if not self.has_attr('build_hierarchy'):
            self.add_attribute('build_hierarchy', value=flag, attr_type='bool')
        else:
            self.build_hierarchy = flag

    def set_attach_type(self, attach_type):
        """
        Sets which attach type will be used to constraint the original chain
        :param attach_type: int or str
        """

        attach_type_list = joint_utils.AttachJoints.AttachType.get_string_list()
        if attach_type == attach_type_list[0]:
            attach_type = 0
        elif attach_type == attach_type_list[1]:
            attach_type = 1

        if not self.has_attr('attach_type'):
            self.add_attribute(
                attr='attach_type',
                enumName=':'.join(attach_type_list),
                attr_type='enum',
                value=attach_type
            )
        else:
            self.attach_type = attach_type

    def set_buffer_replace(self, list_value):
        """
        Sets whether buffer joints will be renamed its prefix or suffix
        :param list_value: list(str, str)
        """

        if not self.has_attr('buffer_replace'):
            self.add_attribute(attr='buffer_replace', value=list_value, attr_type='string')
        else:
            self.buffer_replace = list_value

    def set_create_switch(self, flag):
        """
        Sets whether or not create switch functionality should be executed or not
        :param flag: bool
        """

        if not self.has_attr('create_switch'):
            self.add_attribute(attr='create_switch', value=flag, attr_type='bool')
        else:
            self.create_switch = flag

    def set_switch_controls_group(self, group):
        """
        Sets the controls group that is used to switch visibility of
        :param group:
        """

        if not self.has_attr('switch_controls_group'):
            self.add_attribute(attr='switch_controls_group', value=group, attr_type='messageSimple')
        else:
            self.switch_controls_group = group

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _duplicate_joints(self):
        """
        Internal function that duplicates the original joints of the buffer rig
        :return: list(str), list of new duplicated joints
        """

        rig_module = self.get_rig_module()
        if not rig_module:
            tpRigToolkit.logger.warning(
                'RigComponent {} is not connected to a RigModule ...'.format(self.base_name))
            return

        setup_group = rig_module.setup_group or self.setup_group
        if not setup_group or not setup_group.is_valid_mobject():
            tpRigToolkit.logger.warning(
                'RigComponent {} | No Setups group found. Aborting joint duplication ...'.format(self.base_name))
            return

        joints = self.get_joints(as_meta=False)

        if self.create_buffer_joints:
            if not joints:
                tpRigToolkit.logger.warning('No joints defined to duplicate!')
                return
            if self.build_hierarchy:
                build_hierarchy = joint_utils.BuildJointHierarchy()
                build_hierarchy.set_transforms(joints)
                build_hierarchy.set_replace(self.buffer_replace[0], self.buffer_replace[1])
                buffer_joints = build_hierarchy.create()
            else:
                duplicate_hierarchy = xform_utils.DuplicateHierarchy(joints[0])
                duplicate_hierarchy.stop_at(joints[-1])
                duplicate_hierarchy.only_these(joints)
                duplicate_hierarchy.set_replace(self.buffer_replace[0], self.buffer_replace[1])
                buffer_joints = duplicate_hierarchy.create()
            if not buffer_joints:
                tpRigToolkit.logger.warning('No Buffer Joints duplicated!')
            else:
                self.message_list_connect('buffer_joints', buffer_joints)
                tp.Dcc.set_parent(buffer_joints[0], setup_group.meta_node)
        else:
            joints = rig_module.get_joints()
            self.message_list_connect('buffer_joints', joints)

        return self.message_list_get('buffer_joints', as_meta=False)
