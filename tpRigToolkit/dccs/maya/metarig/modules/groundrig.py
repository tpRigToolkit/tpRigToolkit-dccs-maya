#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ground rig implementation for metarig in Maya
"""

import tpDcc as tp
from tpDcc.dccs.maya.meta import metanode

from tpRigToolkit.dccs.maya.metarig.core import module
from tpRigToolkit.dccs.maya.metarig.components import joint


class GroundRig(module.RigModule, object):
    def __init__(self, *args, **kwargs):
        super(GroundRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'ground'))
        self.set_ground_joint_name(self._get_name(self.base_name, 'ground', node_type='joint'))
        self.set_create_sub_controls(True)
        self.set_scalable(False)

    def set_ground_joint_name(self, name):
        """
        Sets the name of the joint that will be used as the ground joint
        NOTE: This name MUST be the final name of the joint, no naming rules will be applied to them
        :param name:str
        """

        if not self.has_attr('ground_joint_name'):
            self.add_attribute('ground_joint_name', value=name, attr_type='string')
        else:
            self.ground_joint_name = name

    def set_scalable(self, flag):
        """
        Sets whether or not this control can be scaled
        :param flag: bool
        """

        if not self.has_attr('scalable'):
            self.add_attribute('scalable', flag, attr_type='bool')
        else:
            self.scalable = flag

    def create(self, character_name, *args, **kwargs):
        super(GroundRig, self).create(character_name, *args, **kwargs)

        all_ctrls = list()

        ground_joint = metanode.validate_obj_arg(self.ground_joint_name, 'MetaObject', update_class=True)

        joint_component = joint.JointRig(name='groundJoint')
        self.add_component(joint_component)
        joint_component.add_joints(ground_joint)
        joint_component.create()

        # Main Control
        main_ctrl = joint_component.create_control('main')
        main_ctrl.create_root()
        self.add_attribute(attr='main_control', value=main_ctrl, attr_type='messageSimple')
        self._add_control(main_ctrl)
        all_ctrls.append(main_ctrl)

        if self.create_sub_controls:
            sub_ctrl_1 = joint_component.create_control('mainSub', sub=True, id=0, visibility_parent_control=main_ctrl)
            sub_ctrl_1.create_root()
            sub_ctrl_1.set_parent(main_ctrl)
            main_ctrl.add_sub_control(sub_ctrl_1)

            sub_ctrl_2 = joint_component.create_control('mainSub', sub=True, id=1, visibility_parent_control=main_ctrl)
            sub_ctrl_2.create_root()
            sub_ctrl_2.set_parent(sub_ctrl_1)
            main_ctrl.add_sub_control(sub_ctrl_2)

            all_ctrls.extend([sub_ctrl_1, sub_ctrl_2])

        for ctrl in all_ctrls:
            if self.scalable:
                ctrl.hide_visibility_attribute()
            else:
                ctrl.hide_scale_and_visibility_attributes()

        main_ctrl.match_translation_and_rotation(ground_joint)

        # TODO: Check if we need to parent the join always to main or use the last sub control when
        # TODO: create sub controls functionality is enabled
        joints = joint_component.get_joints()
        if joints and joint_component.attach_joints:
            tp.Dcc.create_parent_constraint(joints[0].meta_node, main_ctrl.meta_node)
            if self.scalable:
                tp.Dcc.create_scale_constraint(joints[0].meta_node, main_ctrl.meta_node)

        self.controls_group.set_parent(self.character.controls_group)

        joint_component.delete_setup()
        self.delete_setup()
