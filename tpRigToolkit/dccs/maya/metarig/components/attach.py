#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig component to handle joint attachments
"""

from __future__ import print_function, division, absolute_import

import logging

from tpDcc import dcc
from tpDcc.dccs.maya.core import joint as joint_utils, rig as rig_utils
from tpDcc.dccs.maya.meta import metanode

from tpRigToolkit.dccs.maya.metarig.core import component

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class AttachJointsComponent(component.RigComponent, object):

    ATTACH_TYPE_CONSTRAINT = joint_utils.AttachJoints.AttachType.CONSTRAINT
    ATTACH_TYPE_MATRIX = joint_utils.AttachJoints.AttachType.MATRIX

    def __init__(self, *args, **kwargs):
        super(AttachJointsComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_attach_joints(True)
        self.set_create_switch(False)
        self.set_auto_switch_visibility(True)
        self.set_attach_type(self.ATTACH_TYPE_CONSTRAINT)
        self.set_switch_attribute_name('switch')
        self.set_buffer_replace(['jnt', 'buffer'])
        self.set_switch_controls_group(None)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(AttachJointsComponent, self).create()

        self.attach()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_buffer_replace(self, list_value):
        """
        Sets whether buffer joints will be renamed its prefix or suffix
        :param list_value: list(str, str)
        """

        if not self.has_attr('buffer_replace'):
            self.add_attribute(attr='buffer_replace', value=list_value, attr_type='string')
        else:
            self.buffer_replace = list_value

    def set_attach_joints(self, flag):
        """
        Sets whether or not attach functionality is enabled
        :param flag: bool
        :return:
        """

        if not self.has_attr('attach_joints'):
            self.add_attribute(attr='attach_joints', value=flag, attr_type='bool')
        else:
            self.attach_joints = flag

    def set_create_switch(self, flag):
        """
        Sets whether or not create switch functionality should be executed or not
        :param flag: bool
        """

        if not self.has_attr('create_switch'):
            self.add_attribute(attr='create_switch', value=flag, attr_type='bool')
        else:
            self.create_switch = flag

    def set_switch_attribute_name(self, attr_name):
        """
        Sets the attribute name that handles switch functionality
        :param attr_name: str
        """

        if not self.has_attr('switch_attribute_name'):
            self.add_attribute(attr='switch_attribute_name', value=attr_name, attr_type='string')
        else:
            self.switch_attribute_name = attr_name

    def set_auto_switch_visibility(self, flag):
        """
        Sets whether or not, when attaching more than one joint chain, control group visibility will be managed
        by an attribute added to the first joint.
        :param flag: bool
        """

        if not self.has_attr('auto_switch_visibility'):
            self.add_attribute(attr='auto_switch_visibility', value=flag, attr_type='bool')
        else:
            self.auto_switch_visibility = flag

    def set_attach_type(self, attach_type):
        """
        Sets which attach type is used in case joints are attached
        :param attach_type: int (ATTACH_TYPE_CONSTRAINT = 0; ATTACH_TYPE_MATRIX = 1)
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

    def attach(self):
        """
        Attaches source joints to target joints
        """

        if not self.attach_joints:
            LOGGER.warning('Attach joints skipped ...')
            return

        source_joints = self.message_list_get('source_joints', as_meta=False)
        target_joints = self.message_list_get('target_joints', as_meta=False)

        meta_source_chain = metanode.validate_obj_list_arg(source_joints, 'MetaObject', update_class=True)
        meta_target_chain = metanode.validate_obj_list_arg(target_joints, 'MetaObject', update_class=True)
        self.set_source_and_target_joints(meta_source_chain, meta_target_chain)
        self.set_attach_type(joint_utils.AttachJoints.AttachType.CONSTRAINT)

        attach_joints = joint_utils.AttachJoints(
            source_joints=source_joints,
            target_joints=target_joints,
            create_switch=self.create_switch,
            switch_attribute_name=self.switch_attribute_name
        )
        attach_joints.set_attach_type(self.attach_type)
        attach_joints.create()
        remap_nodes = attach_joints.remap_nodes
        for remap_node in remap_nodes:
            remap_split = remap_node.split('_')[:-1]
            dcc.rename_node(
                remap_node, self._get_name(self.name, '_'.join(remap_split), node_type='remapValue'))

        if dcc.attribute_exists(target_joints[0], self.switch_attribute_name):
            switch = rig_utils.RigSwitch(target_joints[0])
            weight_count = switch.get_weight_count()
            if weight_count > 0:
                if self.auto_switch_visibility:
                    switch_controls_group = self.switch_controls_group.meta_node if self.switch_controls_group else None
                    switch_controls_group = switch_controls_group or self.controls_group.meta_node
                    switch.add_groups_to_index((weight_count - 1), switch_controls_group)
                switch.create()
                switch_conditions = switch.conditions
                for _, condition in switch_conditions.items():
                    dcc.rename_node(condition, self._get_name(self.name, 'switch', node_type='condition'))

    def detach(self):
        raise NotImplementedError('Detach functionality is not implemented yet!')

    def set_source_and_target_joints(self, source_joints, target_joints):
        """
        Set the source and target joints to match transforms of
        :param source_joints:
        :param target_joints:
        :return:
        """

        if len(source_joints) != len(target_joints):
            LOGGER.warning('Source and Target joints do not match their length!')
            return

        # Connect source joints
        if not self.message_list_get('source_joints', as_meta=False):
            self.message_list_connect('source_joints', source_joints)
        else:
            self.message_list_purge('source_joints')
            self.message_list_connect('source_joints', source_joints)

        # Connect target joints
        if not self.message_list_get('target_joints', as_meta=False):
            self.message_list_connect('target_joints', target_joints)
        else:
            self.message_list_purge('target_joints')
            self.message_list_connect('target_joints', target_joints)

    def set_switch_controls_group(self, group):
        """
        Sets the controls group that is used to switch visibility of
        :param group:
        """

        if not self.has_attr('switch_controls_group'):
            self.add_attribute(attr='switch_controls_group', value=group, attr_type='messageSimple')
        else:
            self.switch_controls_group = group
