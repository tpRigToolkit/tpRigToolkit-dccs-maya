#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Muscle Spline metarig component implementation for Maya
"""

from __future__ import print_function, division, absolute_import

import logging

import maya.cmds

from tpDcc import dcc
from tpDcc.dccs.maya.meta import metanode

from tpRigToolkit.dccs.maya.core import musclespline
from tpRigToolkit.dccs.maya.metarig.core import component, mixin

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class MuscleSplineComponent(component.RigComponent, mixin.JointMixin, mixin.ControlMixin):
    def __init__(self, *args, **kwargs):
        super(MuscleSplineComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        mixin.ControlMixin.__init__(self)
        self.set_name(kwargs.get('name', 'muscleSpline'))
        self.set_num_insertion_controls(3)
        self.set_num_driven_joints(5)
        self.set_constraint_mid_controls(False)
        self.set_lock_controls_scale(True)
        self.set_lock_jiggle_attributes(False)
        self.set_create_sets(False)
        self.set_spline_node(None)
        self.set_create_bendy_controls_visibility_attribute(True)
        self.set_attributes_control(None)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(MuscleSplineComponent, self).create()

        muscle_spline = musclespline.MuscleSpline(
            name=self.name, size=self.scale, insertion_controls=self.num_insertion_controls,
            driven_joints=self.num_driven_joints, constraint_mid_controls=self.constraint_mid_controls,
            lock_scale=self.lock_controls_scale, lock_jiggle_attributes=self.lock_jiggle_attributes,
            create_sets=self.create_sets
        )
        muscle_spline.create()

        spline_node = metanode.validate_obj_arg(muscle_spline.spline_node, 'MetaNode', update_class=True)
        self.set_spline_node(spline_node)
        spline_controls_group = metanode.validate_obj_arg(muscle_spline.controls_group, 'MetaObject', update_class=True)
        controls_group = self.get_controls_group()
        if controls_group:
            spline_controls_group.set_parent(controls_group)
        else:
            self.controls_group = spline_controls_group
        # dcc.set_attribute_value(muscle_spline.drivens_group, 'visibility', False)
        drivens_group = metanode.validate_obj_arg(muscle_spline.drivens_group, 'MetaObject', update_class=True)
        setup_group = self.get_setup_group()
        if setup_group:
            drivens_group.set_parent(setup_group)
        else:
            self.setup_group = drivens_group
        root_groups = metanode.validate_obj_list_arg(muscle_spline.root_groups, 'MetaObject', update_class=True)
        self.message_list_connect('root_groups', root_groups)
        # TODO: This misses the auto/root connection
        spline_controls = [spline_control.control for spline_control in muscle_spline.controls]
        controls = metanode.validate_obj_list_arg(spline_controls, 'RigControl', update_class=True)
        for control in controls:
            self._add_control(control)
        spline_drivens = metanode.validate_obj_list_arg(muscle_spline.drivens, 'MetaObject', update_class=True)
        self.add_joints(spline_drivens)

        rig_module = self.get_rig_module()
        if rig_module:
            spline_node = self.get_message('spline_node')[0]
            node_parent = maya.cmds.listRelatives(spline_node, parent=True, fullPath=True)[0]
            maya.cmds.parent(node_parent, self.setup_group.meta_node)

        maya.cmds.delete(muscle_spline.main_group)

        source_transforms = self.message_list_get('source_transforms', as_meta=False) or list()
        if len(source_transforms) != len(muscle_spline.root_groups):
            LOGGER.warning(
                'To automatically connect Muscle Spline controls to source transforms the number of transforms to '
                'attach should match. Source transfroms ({}); Root Groups: ({})'.format(
                    len(source_transforms), len(muscle_spline.root_groups)))
            LOGGER.info('Only start and end controls will be attached ...')
            self._connect_start_end_controls(muscle_spline)
        else:
            self._connect_all_controls(muscle_spline)

        self._create_attributes()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_auto_control_groups(self, as_meta=True):
        """
        Returns all auto control groups of the muscle spline controls
        :return: list
        """

        auto_groups = list()

        controls = self.get_controls()
        if not controls:
            return auto_groups

        for control in controls:
            auto_group = dcc.get_message_input(control.meta_node, 'auto')
            if not auto_group or not dcc.node_exists(auto_group):
                continue
            if as_meta:
                auto_groups.append(metanode.validate_obj_arg(auto_group, 'MetaObject', update_class=True))
            else:
                auto_groups.append(auto_group)

        return auto_groups

    def get_root_control_groups(self, as_meta=True):
        """
        Returns all root control groups of the muscle spline controls
        :return: list
        """

        root_groups = list()

        controls = self.get_controls()
        if not controls:
            return root_groups

        for control in controls:
            root_group = dcc.get_message_input(control.meta_node, 'root')
            if not root_group or not dcc.node_exists(root_group):
                continue
            if as_meta:
                root_groups.append(metanode.validate_obj_arg(root_group, 'MetaObject', update_class=True))
            else:
                root_groups.append(root_group)

        return root_groups

    def set_num_insertion_controls(self, value):
        if not self.has_attr('num_insertion_controls'):
            self.add_attribute(attr='num_insertion_controls', value=value)
        else:
            self.num_insertion_controls = value

    def set_num_driven_joints(self, value):
        if not self.has_attr('num_driven_joints'):
            self.add_attribute(attr='num_driven_joints', value=value)
        else:
            self.num_driven_joints = value

    def set_constraint_mid_controls(self, flag):
        if not self.has_attr('constraint_mid_controls'):
            self.add_attribute(attr='constraint_mid_controls', value=flag)
        else:
            self.constraint_mid_controls = flag

    def set_lock_controls_scale(self, flag):
        if not self.has_attr('lock_controls_scale'):
            self.add_attribute(attr='lock_controls_scale', value=flag)
        else:
            self.lock_controls_scale = flag

    def set_lock_jiggle_attributes(self, flag):
        if not self.has_attr('lock_jiggle_attributes'):
            self.add_attribute(attr='lock_jiggle_attributes', value=flag)
        else:
            self.lock_jiggle_attributes = flag

    def set_create_sets(self, flag):
        if not self.has_attr('create_sets'):
            self.add_attribute(attr='create_sets', value=flag)
        else:
            self.create_sets = flag

    def set_spline_node(self, spline_node):
        if not self.has_attr('spline_node'):
            self.add_attribute(attr='spline_node', value=spline_node, attr_type='messageSimple')
        else:
            self.spline_node = spline_node

    def set_source_transforms(self, source_transforms, clean=False):
        if not self.message_list_get('source_transforms', as_meta=False):
            self.message_list_connect('source_transforms', source_transforms)
        else:
            if clean:
                self.message_list_purge('source_transforms')
            for xform in source_transforms:
                self.message_list_append('source_transforms', xform)

    def set_create_bendy_controls_visibility_attribute(self, flag):
        if not self.has_attr('create_bendy_controls_visibility_attribute'):
            self.add_attribute(attr='create_bendy_controls_visibility_attribute', value=flag)
        else:
            self.create_bendy_controls_visibility_attribute = flag

    def set_attributes_control(self, control):
        """
        Sets the control where rig module specific attributes will be stored
        :param control:
        :return:
        """

        if not self.has_attr('attributes_control'):
            self.add_attribute(attr='attributes_control', value=control, attr_type='messageSimple')
        else:
            self.attributes_control = control

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _connect_start_end_controls(self, muscle_spline):
        source_transforms = self.message_list_get('source_transforms', as_meta=False) or list()
        spline_controls = [spline_control.control for spline_control in muscle_spline.controls]

        for source_transform, root_group, driven in zip(
                [source_transforms[0], source_transforms[-1]],
                [muscle_spline.root_groups[0], muscle_spline.root_groups[-1]],
                [muscle_spline.drivens[0], muscle_spline.drivens[-1]]):

            dcc.create_parent_constraint(root_group, source_transform, maintain_offset=False)
            dcc.delete_constraints(root_group, constraint_type='parentConstraint')
            dcc.create_point_constraint(root_group, source_transform, maintain_offset=False)
            ori_cns = dcc.create_orient_constraint(root_group, source_transform, maintain_offset=True)
            dcc.set_attribute_value(ori_cns, 'interpType', 2)        # Shortest

        # Disable jiggle attributes in muscle spline controls
        for ctrl in muscle_spline.controls:
            ctrl.zero_out_jiggle_attributes()
            ctrl.lock_and_hide_jiggle_attributes()

        # constraint muscle spline control scale to muscle spline drivens
        # TODO: In a future this will be implemented inside core muscleSpline, if that's the case
        # TODO: this code won't be necessary anymore.
        for control, driven in zip(spline_controls, muscle_spline.drivens):
            dcc.create_scale_constraint(driven, control, maintain_offset=False)

    def _connect_all_controls(self, muscle_spline):
        source_transforms = self.message_list_get('source_transforms', as_meta=False) or list()
        spline_controls = [spline_control.control for spline_control in muscle_spline.controls]

        for source_transform, root_group, driven in zip(
                source_transforms, muscle_spline.root_groups, muscle_spline.drivens):
            dcc.create_parent_constraint(root_group, source_transform, maintain_offset=False)
            dcc.delete_constraints(root_group, constraint_type='parentConstraint')
            dcc.create_point_constraint(root_group, source_transform, maintain_offset=False)
            ori_cns = dcc.create_orient_constraint(root_group, source_transform, maintain_offset=True)
            dcc.set_attribute_value(ori_cns, 'interpType', 2)        # Shortest

        # Disable jiggle attributes in muscle spline controls
        for ctrl in muscle_spline.controls:
            ctrl.zero_out_jiggle_attributes()
            ctrl.lock_and_hide_jiggle_attributes()

        # constraint muscle spline control scale to muscle spline drivens
        # TODO: In a future this will be implemented inside core muscleSpline, if that's the case
        # TODO: this code won't be necessary anymore.
        for control, driven in zip(spline_controls, muscle_spline.drivens):
            dcc.create_scale_constraint(driven, control, maintain_offset=False)

    def _create_attributes(self):
        if not self.create_bendy_controls_visibility_attribute or not self.attributes_control:
            return False

        controls_group = self.get_controls_group()
        if not controls_group:
            return False

        dcc.add_title_attribute(self.attributes_control.meta_node, 'BENDY_CONTROLS')

        bendy_attr_name = 'bendy_visibility'
        if not dcc.attribute_exists(self.attributes_control.meta_node, bendy_attr_name):
            dcc.add_integer_attribute(
                self.attributes_control.meta_node, bendy_attr_name,
                default_value=0, min_value=0, max_value=1, keyable=False)

        dcc.connect_attribute(
            self.attributes_control.meta_node, bendy_attr_name, controls_group.meta_node, 'visibility')

        return True
