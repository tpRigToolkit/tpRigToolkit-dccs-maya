#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Flexi Plane Rig setup
"""

from __future__ import print_function, division, absolute_import

import maya.cmds

from tpDcc import dcc
from tpDcc.libs.python import mathlib
from tpDcc.dccs.maya.core import follicle, blendshape, curve, cluster, skin

from tpRigToolkit.managers import names
from tpRigToolkit.dccs.maya.core import control


class FlexiPlaneRig(object):
    def __init__(self):
        super(FlexiPlaneRig, self).__init__()

        self._naming_file = None
        self._rule_name = 'node'

        self._length = 2.0
        self._control_size = 0.6
        self._num_joints = 5
        self._top_group = None
        self._global_move_group = None
        self._no_xform_group = None
        self._nurbs_plane = None
        self._nurbs_blendshape_plane = None
        self._nurbs_blendshape_node = None
        self._nurbs_plane_material = None
        self._display_nurbs_plane_as_template = False
        self._follicles = list()
        self._follicles_group = None
        self._joints = list()
        self._global_control = None
        self._start_control = None
        self._mid_control = None
        self._end_control = None
        self._mid_control_material = None
        self._clusters = list()
        self._clusters_group = None
        self._wire_curve = None
        self._wire_node = None
        self._twist_node = None
        self._twist_handle = None

    def create(self):
        dcc.clear_selection()

        self._create_groups()
        self._create_nurbs_plane()
        self._create_follicles()
        self._create_joints()
        self._create_connector_controls()
        self._create_blendshape_setup()
        self._create_wire_setup()
        self._connect_clusters_to_controls()
        self._create_twist_setup()
        self._create_squash_stretch_setup()
        # self._create_test_geometry()

    def _create_groups(self):
        """
        Internal function that creates basic group hierarchy for the flexi rig setup
        """

        self._top_group = dcc.create_empty_group(name=self._get_name('flexiRoot', node_type='group'))
        dcc.hide_keyable_attributes(self._top_group, skip_visibility=True)

        self._global_move_group = dcc.create_empty_group(name=self._get_name('globalMove', node_type='group'))
        dcc.set_parent(self._global_move_group, self._top_group)

        self._extras_group = dcc.create_empty_group(name=self._get_name('extras', node_type='group'))
        dcc.hide_keyable_attributes(self._extras_group, skip_visibility=True)
        dcc.set_parent(self._extras_group, self._top_group)

        self._follicles_group = dcc.create_empty_group(name=self._get_name('follicles', node_type='group'))
        self._clusters_group = dcc.create_empty_group(name=self._get_name('clusters', node_type='group'))
        self._controls_group = dcc.create_empty_group(name=self._get_name('controls', node_type='group'))

        for group in [self._follicles_group, self._clusters_group]:
            dcc.set_parent(group, self._extras_group)
            dcc.hide_keyable_attributes(group, skip_visibility=True)

        dcc.hide_node(self._clusters_group)
        dcc.set_parent(self._controls_group, self._global_move_group)
        dcc.hide_keyable_attributes(self._controls_group, skip_visibility=True)

    def _create_nurbs_plane(self):
        """
        Internal function that creates the NURBS plane that will drive the rig system
        """

        self._nurbs_plane = dcc.create_nurbs_plane(
            name=self._get_name('flexiPlane', node_type='surface'),
            axis=(0, 1, 0), width=self._num_joints * 2, length=self._length, patches_u=self._num_joints,
            construction_history=False)
        dcc.freeze_transforms(self._nurbs_plane, translate=True, rotate=True, scale=True)
        dcc.hide_keyable_attributes(self._nurbs_plane, skip_visibility=True)

        material_name = self._get_name('flexiMat', node_type='material')
        if not dcc.node_exists(material_name):
            self._nurbs_plane_material = dcc.create_lambert_material(
                name=material_name, no_surface_shader=True, color=(0.0, 0.85, 1.0), transparency=(0.8, 0.8, 0.8))
        else:
            self._nurbs_plane_material = material_name
        dcc.apply_shader(self._nurbs_plane_material, self._nurbs_plane)

        if self._display_nurbs_plane_as_template:
            dcc.set_node_template_display(self._nurbs_plane, True)

        nurbs_plane_shape = dcc.list_shapes(self._nurbs_plane)[0]
        dcc.set_node_renderable(nurbs_plane_shape, False)
        dcc.set_attribute_value(nurbs_plane_shape, 'doubleSided', True)

        dcc.set_parent(self._nurbs_plane, self._global_move_group)

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
                dcc.set_parent(new_follicle, self._follicles_group)
                self._follicles.append(new_follicle)

                if u_count > 1:
                    u_pos = mathlib.clamp(0, u_pos + (1.0 / u_count), 1.0)
                if v_count > 1:
                    v_pos = mathlib.clamp(0, v_pos + (1.0 / v_count), 1.0)

        # We make sure that follicles are scaled if global group is scaled
        for flc in self._follicles:
            dcc.create_scale_constraint(flc, self._global_move_group)

    def _create_joints(self):
        for i in range(len(self._follicles)):
            dcc.clear_selection()
            self._joints.append(dcc.create_joint(name=self._get_name('joint', id=i, node_type='joint')))
            dcc.match_translation(self._follicles[i], self._joints[i])
            dcc.set_parent(self._joints[i], self._follicles[i])

    def _create_connector_controls(self):

        self._global_control = control.RigControl(name=self._get_name('global', node_type='control'))
        global_circle1 = maya.cmds.circle(normal=(0, 1, 0), radius=0.3)[0]
        dcc.move_node(global_circle1, 0, 0, -self._length)
        global_circle2 = maya.cmds.circle(normal=(0, 1, 0), radius=0.3)[0]
        dcc.move_node(global_circle2, 0, 0, self._length)
        dcc.freeze_transforms(global_circle1)
        dcc.freeze_transforms(global_circle2)
        self._global_control.set_shape([global_circle1, global_circle2])
        self._global_control.set_color_rgb(255, 255, 0)
        dcc.delete_node([global_circle1, global_circle2])
        for shape in dcc.list_shapes(self._global_control.get()):
            dcc.rename_node(shape, '{}Shape'.format(self._global_control.get()))
        self._global_control.create_root_group()
        dcc.set_parent(self._global_control.get_top(), self._top_group)
        dcc.set_parent(self._global_move_group, self._global_control.get())

        top_end_distance = self._num_joints
        self._start_control = control.RigControl(name=self._get_name('startConnector', node_type='control'))
        self._start_control.set_curve_type(
            'square', color=(255, 255, 0), axis_order='YXZ', control_size=self._control_size)
        dcc.move_node(self._start_control.get_top(), -top_end_distance, 0, 0)

        self._end_control = control.RigControl(name=self._get_name('endConnector', node_type='control'))
        self._end_control.set_curve_type(
            'square', color=(255, 255, 0), axis_order='YXZ', control_size=self._control_size)
        dcc.move_node(self._end_control.get_top(), top_end_distance, 0, 0)

        sphere_control = maya.cmds.polySphere(subdivisionsX=12, subdivisionsY=12, radius=0.3)
        sphere_shape = dcc.list_shapes(sphere_control)[0]
        sphere_material = self._get_name('flexiBendControlMat', node_type='material')
        if not dcc.node_exists(sphere_material):
            self._mid_control_material = dcc.create_surface_shader(shader_name=sphere_material)
            dcc.set_attribute_value(self._mid_control_material, 'outColor', (1, 1, 0))
        else:
            self._mid_control_material = sphere_material
        dcc.apply_shader(self._mid_control_material, sphere_shape)
        dcc.set_node_renderable(sphere_shape, False)
        self._mid_control = control.RigControl(name=self._get_name('midBend', node_type='control'))
        self._mid_control.set_shape(sphere_control)
        maya.cmds.delete(sphere_control)
        mid_control_shape = dcc.list_shapes(self._mid_control.get())[0]
        dcc.rename_node(mid_control_shape, '{}Shape'.format(self._mid_control.get()))

        for connector_control in [self._start_control, self._mid_control, self._end_control]:
            connector_control.create_root_group()
            connector_control.create_auto_group()
            dcc.set_parent(connector_control.get_top(), self._controls_group)

        # Mid control will be positioned in the mid position between start and end controls
        dcc.create_point_constraint(
            self._mid_control.get_buffer_group('auto'), (self._start_control.get(), self._end_control.get()),
            maintain_offset=False)

    def _create_blendshape_setup(self):
        if not self._nurbs_plane:
            return

        self._nurbs_blendshape_plane = dcc.duplicate_node(
            self._nurbs_plane, new_node_name=self._get_name('flexiPlaneBshp', node_type='surface'))[0]
        dcc.move_node(self._nurbs_blendshape_plane, 0, 0, -self._num_joints)

        self._nurbs_blendshape_node = blendshape.create(
            self._nurbs_plane, self._nurbs_blendshape_plane, name=self._get_name('flexiPlane', node_type='blendShape'))
        dcc.set_attribute_value(self._nurbs_blendshape_node, self._nurbs_blendshape_plane, 1.0)

        # Rename blendshape tweak node
        nurbs_plane_shape = dcc.list_shapes(self._nurbs_plane)[0]
        bs_tweak = maya.cmds.listConnections(nurbs_plane_shape, type='tweak')[0]
        dcc.rename_node(bs_tweak, self._get_name('flexiPlaneBshp', node_type='tweak'))

    def _create_wire_setup(self):
        # NOTE: We use wire deform to deform the blendShape plane because allow us to maintain the uniform spacing
        # NOTE: between surface patches while deforming the wired curve

        points_list = [(-self._num_joints, 0, -self._num_joints),
                       (0, 0, -self._num_joints),
                       (self._num_joints, 0, -self._num_joints)]
        self._wire_curve = curve.create_from_point_list(
            points_list, degree=2, name=self._get_name('flexiPlaneWire', node_type='curve'))
        dcc.hide_node(self._wire_curve)
        dcc.center_pivot(self._wire_curve)
        dcc.set_parent(self._wire_curve, self._extras_group)

        # NOTE: We create clusters in relative mode so the transforms in their above groups does not affect them
        start_cluster, start_handle = cluster.create_cluster(
            ['{}.cv[{}]'.format(self._wire_curve, i) for i in range(2)],
            name=self._get_name('wireStart', node_type='cluster'), relative=True, exclusive=False)
        dcc.set_attribute_value(start_handle, 'originX', -(self._num_joints + 1))
        dcc.move_pivot_in_object_space(start_handle, -self._num_joints / 2, 0, 0)

        end_cluster, end_handle = cluster.create_cluster(
            ['{}.cv[{}]'.format(self._wire_curve, i) for i in range(1, 3)],
            name=self._get_name('wireEnd', node_type='cluster'), relative=True, exclusive=False)
        dcc.set_attribute_value(end_handle, 'originX', self._num_joints + 1)
        dcc.move_pivot_in_object_space(end_handle, self._num_joints / 2, 0, 0)

        mid_cluster, mid_handle = cluster.create_cluster(
            '{}.cv[1]'.format(self._wire_curve), name=self._get_name('wireMid', node_type='cluster'),
            relative=True, exclusive=False)
        for cls, handle in zip([start_cluster, mid_cluster, end_cluster], [start_handle, mid_handle, end_handle]):
            self._clusters.append({'node': cls, 'handle': handle})
            dcc.set_parent(handle, self._clusters_group)

        # Make sure that mid CV is only deformer 0.5 by start/end clusters
        # This will give us a linear deformation
        maya.cmds.percent(start_cluster, '{}.cv[1]'.format(self._wire_curve), value=0.5)
        maya.cmds.percent(end_cluster, '{}.cv[1]'.format(self._wire_curve), value=0.5)

        wire_curve_shape = dcc.list_shapes(self._wire_curve)[0]
        wire_tweak = maya.cmds.listConnections(wire_curve_shape, type='tweak')[0]
        dcc.rename_node(wire_tweak, self._get_name('wireCurveClusters', node_type='tweak'))

        # TODO: Dropoff distance should be multiplied by global scale
        blendshape_curve_shape = dcc.list_shapes(self._nurbs_blendshape_plane)[0]
        self._wire_node = maya.cmds.wire(
            self._nurbs_blendshape_plane, wire=self._wire_curve,
            name=self._get_name('wireDeformer', node_type='wire'), dropoffDistance=[0, 20])
        wire_plane_tweak = maya.cmds.listConnections(blendshape_curve_shape, type='tweak')[0]
        dcc.rename_node(wire_plane_tweak, self._get_name('flexiPlaneBshpWire', node_type='tweak'))

    def _connect_clusters_to_controls(self):
        for axis in 'XYZ':
            attr_name = 'translate{}'.format(axis)
            dcc.connect_attribute(self._start_control.get(), attr_name, self._clusters[0]['handle'], attr_name)
            dcc.connect_attribute(self._mid_control.get(), attr_name, self._clusters[1]['handle'], attr_name)
            dcc.connect_attribute(self._end_control.get(), attr_name, self._clusters[-1]['handle'], attr_name)

    def _create_twist_setup(self):

        # Update rotate order for start and end controls to improve twist axis stability
        dcc.set_attribute_value(self._start_control.get(), 'rotateOrder', 3)    # xyz
        dcc.set_attribute_value(self._end_control.get(), 'rotateOrder', 3)      # xyz

        # NOTE: It's important to create the twist deform in front of the deformation chain (so its evaluated before
        # the wire deformer)
        self._twist_node, self._twist_handle = maya.cmds.nonLinear(
            self._nurbs_blendshape_plane, type='twist', frontOfChain=True)
        self._twist_node = dcc.rename_node(self._twist_node, self._get_name('twistDeformer', node_type='twist'))
        self._twist_handle = dcc.rename_node(self._twist_handle, self._get_name('twistHandle', node_type='twist'))
        dcc.set_attribute_value(self._twist_handle, 'rotateZ', 90)
        dcc.hide_node(self._twist_handle)
        dcc.set_parent(self._twist_handle, self._extras_group)

        dcc.connect_attribute(self._start_control.get(), 'rotateX', self._twist_node, 'endAngle')
        dcc.connect_attribute(self._end_control.get(), 'rotateX', self._twist_node, 'startAngle')

    def _create_squash_stretch_setup(self):

        dcc.add_title_attribute(self._global_control.get(), 'volume')
        dcc.add_bool_attribute(self._global_control.get(), 'enable')

        curve_shape = dcc.list_shapes(self._wire_curve)[0]
        curve_info = dcc.create_node('curveInfo', self._get_name('curveLength', node_type='curveInfo'))
        dcc.connect_attribute(curve_shape, 'worldSpace[0]', curve_info, 'inputCurve')
        current_length = dcc.get_attribute_value(curve_info, 'arcLength')
        squash_stretch_divide = dcc.create_node(
            'multiplyDivide', node_name=self._get_name('squashStretchDivide', node_type='multiplyDivide'))
        dcc.set_attribute_value(squash_stretch_divide, 'operation', 2)    # divide
        dcc.set_attribute_value(squash_stretch_divide, 'input1X', current_length)
        dcc.connect_attribute(curve_info, 'arcLength', squash_stretch_divide, 'input2X')
        squash_stretch_volume_multiplier = dcc.create_node(
            'multiplyDivide', node_name=self._get_name('squashStretchVolume', node_type='multiplyDivide'))
        dcc.set_attribute_value(squash_stretch_volume_multiplier, 'input1X', 1.0)
        dcc.connect_attribute(squash_stretch_divide, 'outputX', squash_stretch_volume_multiplier, 'input2X')

        squash_stretch_enabled = dcc.create_node(
            'condition', node_name=self._get_name('squashStretchEnable', node_type='condition'))
        dcc.connect_attribute(self._global_control.get(), 'enable', squash_stretch_enabled, 'firstTerm')
        dcc.set_attribute_value(squash_stretch_enabled, 'secondTerm', 1.0)
        dcc.connect_attribute(squash_stretch_volume_multiplier, 'outputX', squash_stretch_enabled, 'colorIfTrueR')

        for joint in self._joints:
            dcc.connect_attribute(squash_stretch_enabled, 'outColorR', joint, 'scaleY')
            dcc.connect_attribute(squash_stretch_enabled, 'outColorR', joint, 'scaleZ')

    def _create_test_geometry(self):
        for joint in self._joints:
            cube = maya.cmds.polyCube(subdivisionsX=3, subdivisionsY=2, subdivisionsZ=2, width=2.0, ch=False)[0]
            dcc.match_translation(joint, cube)
            maya.cmds.skinCluster(joint, cube, tsb=True)

    def _get_name(self, *args, **kwargs):
        """
        Internal function that returns names used by flexi rig setup taking into consideration current nomenclature
        file and current nomenclature rule
        :return: str
        """

        return names.solve_name(naming_file=self._naming_file, rule_name=self._rule_name, *args, **kwargs)
