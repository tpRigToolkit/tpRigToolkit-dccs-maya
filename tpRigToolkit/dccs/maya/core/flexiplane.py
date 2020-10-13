#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Flexi Plane Rig setup
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
from tpDcc.libs.python import mathlib
from tpDcc.dccs.maya.core import follicle

import tpRigToolkit
from tpRigToolkit.libs.controlrig.core import controllib


class FlexiPlaneRig(object):
    def __init__(self):
        super(FlexiPlaneRig, self).__init__()

        self._naming_file = None
        self._rule_name = 'node'

        self._num_joints = 5
        self._top_group = None
        self._global_move_group = None
        self._no_xform_group = None
        self._nurbs_plane = None
        self._nurbs_plane_material = None
        self._display_nurbs_plane_as_template = False
        self._follicles = list()
        self._follicles_group = None
        self._joints = list()
        self._start_control = None
        self._end_control = None
        self._joints_controls = list()

    def create(self):
        tp.Dcc.clear_selection()

        self._create_groups()
        self._create_nurbs_plane()
        self._create_follicles()
        self._create_joints()
        self._create_controls()

    def _create_groups(self):
        """
        Internal function that creates basic group hierarchy for the flexi rig setup
        """

        self._top_group = tp.Dcc.create_empty_group(name=self._get_name('flexiRoot', node_type='group'))
        tp.Dcc.lock_translate_attributes(self._top_group)
        tp.Dcc.lock_rotate_attributes(self._top_group)
        tp.Dcc.lock_scale_attributes(self._top_group)

        self._global_move_group = tp.Dcc.create_empty_group(name=self._get_name('globalMove', node_type='group'))
        tp.Dcc.set_parent(self._global_move_group, self._top_group)

        self._no_xform_group = tp.Dcc.create_empty_group(name=self._get_name('noXForm', node_type='group'))
        tp.Dcc.disable_transforms_inheritance(self._no_xform_group, lock=True)
        tp.Dcc.hide_node(self._no_xform_group)
        tp.Dcc.lock_translate_attributes(self._top_group)
        tp.Dcc.lock_rotate_attributes(self._top_group)
        tp.Dcc.lock_scale_attributes(self._top_group)
        tp.Dcc.set_parent(self._no_xform_group, self._top_group)

        self._follicles_group = tp.Dcc.create_empty_group(name=self._get_name('follicles', node_type='group'))
        tp.Dcc.set_parent(self._follicles_group, self._top_group)

    def _create_nurbs_plane(self):
        """
        Internal function that creates the NURBS plane that will drive the rig system
        """

        self._nurbs_plane = tp.Dcc.create_nurbs_plane(
            axis=(0, 1, 0), width=self._num_joints * 2, length=2.0, patches_u=self._num_joints,
            construction_history=True)
        tp.Dcc.rotate_node(self._nurbs_plane, 0, -90, 0)
        tp.Dcc.freeze_transforms(self._nurbs_plane, translate=True, rotate=True, scale=True)

        material_name = self._get_name('flexiMat', node_type='material')
        if not tp.Dcc.object_exists(material_name):
            self._nurbs_plane_material = tp.Dcc.create_lambert_material(
                name=material_name, no_surface_shader=True, color=(0.0, 0.85, 1.0), transparency=(0.8, 0.8, 0.8))
        else:
            self._nurbs_plane_material = material_name
        tp.Dcc.apply_shader(self._nurbs_plane_material, self._nurbs_plane)

        if self._display_nurbs_plane_as_template:
            tp.Dcc.set_node_template_display(self._nurbs_plane, True)

        tp.Dcc.set_node_renderable(self._nurbs_plane, False)

    def _create_follicles(self):
        """
        Internal function that creates the follicles that will drive rig joints setup transforms
        :return:
        """
        u_count = self._num_joints
        v_count = 1

        for i in range(v_count):
            u_pos = (1.0 / u_count) * 0.5
            v_pos = (1.0 / v_count) * 0.5

            for j in range(u_count):
                follicle_name = self._get_name('follicle', id=j, node_type='follicle')
                new_follicle = follicle.create_surface_follicle(
                    self._nurbs_plane, follicle_name, [u_pos, v_pos], hide_follicle=True)
                tp.Dcc.set_parent(new_follicle, self._follicles_group)
                self._follicles.append(new_follicle)

                if u_count > 1:
                    u_pos = mathlib.clamp(0, u_pos + (1.0 / u_count), 1.0)
                if v_count > 1:
                    v_pos = mathlib.clamp(0, v_pos + (1.0 / v_count), 1.0)

    def _create_joints(self):
        for i in range(len(self._follicles)):
            tp.Dcc.clear_selection()
            self._joints.append(tp.Dcc.create_joint(name=self._get_name('joint', id=i, node_type='joint')))
            tp.Dcc.match_translation(self._follicles[i], self._joints[i])

    def _create_controls(self):
        pass

    def _get_name(self, *args, **kwargs):
        """
        Internal function that returns names used by flexi rig setup taking into consideration current nomenclature
        file and current nomenclature rule
        :return: str
        """

        return tpRigToolkit.NamesMgr().solve_name(
            naming_file=self._naming_file, rule_name=self._rule_name, *args, **kwargs)
