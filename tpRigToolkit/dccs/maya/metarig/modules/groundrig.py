#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains ground rig implementation for metarig in Maya
"""

import logging

from tpDcc import dcc

from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import joint

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class GroundRig(module.RigModule, mixin.JointMixin):
    def __init__(self, *args, **kwargs):
        super(GroundRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_name(kwargs.get('name', 'ground'))

    def create(self, *args, **kwargs):
        super(GroundRig, self).create(*args, **kwargs)

        all_ctrls = list()

        joints = self.get_joints()
        if not joints:
            logger.warning('Impossible to create ground rig because no joints defined!')
            return False

        ground_joint = joints[0]

        joint_component = joint.JointComponent(name='groundJoint')
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
            dcc.create_parent_constraint(joints[0].meta_node, main_ctrl.meta_node)
            if self.scalable:
                dcc.create_scale_constraint(joints[0].meta_node, main_ctrl.meta_node)

        self.controls_group.set_parent(self.character.controls_group)

        joint_component.delete_setup()
        self.delete_setup()

        return True
