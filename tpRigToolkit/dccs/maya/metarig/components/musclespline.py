#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Muscle Spline metarig component implementation for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode

from tpRigToolkit.dccs.maya.core import musclespline
from tpRigToolkit.dccs.maya.metarig.core import component, mixin


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
            controls_group.rig_module = None
            controls_group.delete()
        self.controls_group = spline_controls_group
        drivens_group = metanode.validate_obj_arg(muscle_spline.drivens_group, 'MetaObject', update_class=True)
        setup_group = self.get_setup_group()
        if setup_group:
            setup_group.rig_module = None
            setup_group.delete()
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
            self.controls_group.set_parent(rig_module.character.controls_group)
            self.setup_group.set_parent(rig_module.character.setup_group)

            spline_node = self.get_message('spline_node')[0]
            node_parent = maya.cmds.listRelatives(spline_node, parent=True, fullPath=True)[0]
            maya.cmds.parent(node_parent, rig_module.character.setup_group.meta_node)

        maya.cmds.delete(muscle_spline.main_group)

        source_transforms = self.message_list_get('source_transforms', as_meta=False) or list()
        if len(source_transforms) != len(muscle_spline.root_groups):
            maya.logger.warning(
                'To automatically connect Muscle Spline controls to source transforms the number of transforms to '
                'attach should match. Source transfroms ({}); Root Groups: ({})'.format(
                    len(source_transforms), len(muscle_spline.root_groups)))
            maya.logger.info('Only start and end controls will be attached ...')
            self._connect_start_end_controls(muscle_spline)
        else:
            self._connect_all_controls(muscle_spline)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

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
            tp.Dcc.create_parent_constraint(root_group, source_transform, maintain_offset=False)

        # Disable jiggle attributes in muscle spline controls
        for ctrl in muscle_spline.controls:
            ctrl.zero_out_jiggle_attributes()
            ctrl.lock_and_hide_jiggle_attributes()

        # constraint muscle spline control scale to muscle spline drivens
        # TODO: In a future this will be implemented inside core muscleSpline, if that's the case
        # TODO: this code won't be necessary anymore.
        for control, driven in zip(spline_controls, muscle_spline.drivens):
            tp.Dcc.create_scale_constraint(driven, control, maintain_offset=False)

    def _connect_all_controls(self, muscle_spline):
        source_transforms = self.message_list_get('source_transforms', as_meta=False) or list()
        spline_controls = [spline_control.control for spline_control in muscle_spline.controls]

        for source_transform, root_group, driven in zip(
                source_transforms, muscle_spline.root_groups, muscle_spline.drivens):
            tp.Dcc.create_parent_constraint(root_group, source_transform, maintain_offset=False)

        # Disable jiggle attributes in muscle spline controls
        for ctrl in muscle_spline.controls:
            ctrl.zero_out_jiggle_attributes()
            ctrl.lock_and_hide_jiggle_attributes()

        # constraint muscle spline control scale to muscle spline drivens
        # TODO: In a future this will be implemented inside core muscleSpline, if that's the case
        # TODO: this code won't be necessary anymore.
        for control, driven in zip(spline_controls, muscle_spline.drivens):
            tp.Dcc.create_scale_constraint(driven, control, maintain_offset=False)
