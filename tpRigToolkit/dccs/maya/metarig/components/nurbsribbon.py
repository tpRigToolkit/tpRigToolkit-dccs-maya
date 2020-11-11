#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig component to create Ribbon setups
"""

from __future__ import print_function, division, absolute_import

from tpDcc import dcc
from tpDcc.dccs.maya.meta import metanode
from tpDcc.dccs.maya.core import geometry as geo_utils, transform as xform_utils, cluster as cluster_utils
from tpDcc.dccs.maya.core import rivet as rivet_utils, follicle as follicle_utils

from tpRigToolkit.managers import names
from tpRigToolkit.dccs.maya.metarig.components import joint


class NurbsRibbon(joint.JointComponent, object):
    def __init__(self, *args, **kwargs):
        super(NurbsRibbon, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name('nurbsRibbon')
        self.set_control_count(2)
        self.set_span_count(2)
        self.set_surface(None)
        self.set_ribbon_offset(1.0)
        self.set_ribbon_offset_axis('Y')
        self.set_ribbon_follicle(False)
        self.set_create_ribbon_buffer_group(False)
        self.set_ribbon_joint_aim(False, [0, 0, 1])
        self.set_last_pivot_top_value(False)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, *args, **kwargs):
        """
        Creates Ribbon
        """

        super(NurbsRibbon, self).create()

        self._create_surface(self.control_count - 1)
        self._create_clusters()
        self._attach_geo()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_ribbon_follows(self, as_meta=True):
        """
        Return list of follicles or rivets used that are driven by the ribbon surface and that drives the joints
        :return:
        """

        return self.message_list_get('ribbon_follows', as_meta=as_meta)

    def get_clusters(self, as_meta=False):
        """
        Returns clusters objects created by cluster component
        :return:
        """

        return self.message_list_get('cluster_handles', as_meta=as_meta)

    def set_control_count(self, value):
        """
        Set the number of controls in the module
        :param value: int
        """

        if not self.has_attr('control_count'):
            self.add_attribute(attr='control_count', value=value)
        else:
            self.control_count = value

    def set_surface(self, surface):
        """
        Set the NURBS surface that the controls should move and the joints should follow when using ribbon
        :param surface: str
        """

        if not self.has_attr('surface'):
            self.add_attribute(attr='surface', value=surface, attr_type='messageSimple')
        else:
            self.surface = surface

    def set_span_count(self, span_count):
        """
        Sets the number of spans the Spline IK curve/Ribbon surface should have
        :param span_count: int
        """

        if not self.has_attr('span_count'):
            self.add_attribute(attr='span_count', value=span_count)
        else:
            self.span_count = span_count

    def set_ribbon_offset(self, float_value):
        """
        Set the width of the ribbon
        :param float_value: float
        """

        if not self.has_attr('ribbon_offset'):
            self.add_attribute(attr='ribbon_offset', value=float_value, attr_type='float')
        else:
            self.ribbon_offset = float_value

    def set_ribbon_offset_axis(self, axis_letter):
        """
        Sets which axis the ribbon width is offset on
        :param axis_letter: str
        """

        axis_list = ['X', 'Y', 'Z']
        if axis_letter == axis_list[0] or axis_letter == axis_list[0].lower():
            axis_letter = 0
        elif axis_letter == axis_list[1] or axis_letter == axis_list[1].lower():
            axis_letter = 1
        elif axis_letter == axis_list[2] or axis_letter == axis_list[2].lower():
            axis_letter = 2

        if not self.has_attr('ribbon_offset_axis'):
            self.add_attribute(
                attr='ribbon_offset_axis',
                enumName=':'.join(axis_list),
                attr_type='enum',
                value=axis_letter
            )
        else:
            self.ribbon_offset_axis = axis_letter

    def set_ribbon_follicle(self, flag):
        """
        Sets whether follicles will be used to attach joints to the ribbon surface.
        If not, rivets will be used
        :param flag: bool
        """

        if not self.has_attr('ribbon_follicle'):
            self.add_attribute(attr='ribbon_follicle', value=flag)
        else:
            self.ribbon_follicle = flag

    def set_create_ribbon_buffer_group(self, flag):
        """
        Sets whether or not a top group should be created where all follicles will be parented into
        :param flag: bool
        """

        if not self.has_attr('create_ribbon_buffer_group'):
            self.add_attribute(attr='create_ribbon_buffer_group', value=flag)
        else:
            self.create_ribbon_buffer_group = flag

    def set_ribbon_joint_aim(self, flag, up_vector=None):
        """
        Sets the ribbon aim options to use
        :param flag: bool
        :param up_vector: list(float, float, float)
        """

        up_vector = up_vector if up_vector is not None else [0, 0, 1]

        if not self.has_attr('aim_ribbon_joints'):
            self.add_attribute('aim_ribbon_joints', value=flag)
        else:
            self.aim_ribbon_joints = flag

        if not self.has_attr('aim_ribbon_joints_up'):
            self.add_attribute('aim_ribbon_joints_up', value=up_vector)
        else:
            self.aim_ribbon_joints_up = up_vector

    def set_last_pivot_top_value(self, flag):
        """
        Sets the last pivot on the curve to the top of the curve
        :param flag: bool
        """

        if not self.has_attr('last_pivot_top_value'):
            self.add_attribute('last_pivot_top_value', value=flag)
        else:
            self.last_pivot_top_value = flag

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_surface(self, span_count):
        """
        Internal function that creates the ribbon surface
        :param span_count: int, number of spans for the ribbon surface
        """

        surface_name = self._get_name(self.name, 'nurbsRibbonSurface', node_type='geometry')
        surface = geo_utils.transforms_to_nurbs_surface(
            transforms=self.get_joints(as_meta=False),
            name=surface_name,
            spans=span_count,
            offset_amount=self.ribbon_offset,
            offset_axis=self.ribbon_offset_axis
        )

        dcc.set_attribute_value(surface, 'inheritsTransform', False)
        surface = metanode.validate_obj_arg(surface, 'MetaObject', update_class=True)
        self.set_surface(surface)
        self.surface.set_parent(self.setup_group)

    def _create_clusters(self):
        """
        Internal function that creates the clusters used by the Nurbs ribbon setup
        :return:
        """

        # TODO: If cluster handlers already exist we should be able to remove them and recreate them
        if self.has_attr('cluster_handles'):
            return

        cluster_name = self._get_name(self.name, 'nurbsRibbon', node_type='cluster')
        last_pivot_end = True if self.last_pivot_top_value else False

        cluster_surface = cluster_utils.ClusterSurface(geometry=self.surface.meta_node, name=cluster_name)
        cluster_surface.set_first_cluster_pivot_at_start(True)
        cluster_surface.set_last_cluster_pivot_at_end(last_pivot_end)
        cluster_surface.set_join_ends(True)
        cluster_surface.create()

        cluster_handles = cluster_surface.get_cluster_handle_list()
        handles = [metanode.validate_obj_arg(handle, 'MetaObject', update_class=True) for handle in cluster_handles]

        if not self.message_list_get('cluster_handles', as_meta=False):
            self.message_list_connect('cluster_handles', handles)
        else:
            self.message_list_purge('cluster_handles')
            for handle in handles:
                self.message_list_append('cluster_handles', handle)

        clusters_group = self._create_setup_group('clusters')
        if not self.has_attr('clusters_group'):
            self.add_attribute(attr='clusters_group', value=clusters_group, attr_type='messageSimple')
        else:
            self.clusters_group = clusters_group
        for handle in handles:
            handle.set_parent(clusters_group)

        return handles

    def _attach_geo(self):
        if not self.attach_joints:
            return

        group_name = 'rivets'
        if self.ribbon_follicle:
            group_name = 'follicles'
        rivet_group = self._create_setup_group(group_name)

        joints = self.get_joints(as_meta=False)
        ribbon_follows = list()

        for joint in joints:
            buffer_group = None

            if self.create_ribbon_buffer_group:
                base_name = self.name if self.has_attr('name') and self.name else self.base_name
                naming_file, naming_rule = self._get_naming_data()
                parsed_name = names.parse_name(self.base_name, naming_file=naming_file, rule_name=naming_rule)
                if parsed_name:
                    # TODO: Allow to put the root in the first key (prefix) or in the last one (suffix)
                    parsed_name[list(parsed_name.keys())[-1]] = group_name
                    buffer_group_name = self._get_name(group_name, 'ribbonBuffer', node_type='group')
                else:
                    buffer_group_name = self._get_name(base_name, group_name, 'ribbonBuffer', node_type='group')
                buffer_group = dcc.create_empty_group(name=buffer_group_name)
                driver = dcc.create_buffer_group(buffer_group)
                dcc.match_translation_rotation(joint, driver)

            if buffer_group:
                if self.ribbon_follicle:
                    follicle = follicle_utils.follicle_to_surface(driver, self.surface.meta_node, constraint=False)
                    nurb_follow = follicle
                    dcc.set_attribute_value(follicle, 'inheritsTransform', False)
                    dcc.create_parent_constraint(joint, buffer_group, maintain_offset=True)
                    dcc.set_parent(follicle, rivet_group.meta_node)
                else:
                    rivet = rivet_utils.attach_to_surface(driver, self.surface.meta_node, constraint=False)
                    nurb_follow = rivet
                    dcc.set_attribute_value(rivet, 'inheritsTransform', False)
                    dcc.create_parent_constraint(joint, buffer_group, maintain_offset=True)
                    dcc.set_parent(rivet, rivet_group.meta_node)
            else:
                if self.ribbon_follicle:
                    follicle = follicle_utils.follicle_to_surface(joint, self.surface.meta_node, constraint=False)
                    nurb_follow = follicle
                    dcc.set_attribute_value(follicle, 'inheritsTransform', False)
                    dcc.set_parent(follicle, rivet_group.meta_node)
                else:
                    rivet = rivet_utils.attach_to_surface(joint, self.surface.meta_node, constraint=False)
                    nurb_follow = rivet
                    dcc.set_attribute_value(rivet, 'inheritsTransform', False)
                    dcc.set_parent(rivet, rivet_group.meta_node)

            ribbon_follows.append(nurb_follow)

        if not self.message_list_get('ribbon_follows', as_meta=False):
            self.message_list_connect('ribbon_follows', ribbon_follows)
        else:
            self.message_list_purge('ribbon_follows')
            for ribbon_follow in ribbon_follows:
                self.message_list_append('ribbon_follows', ribbon_follow)

        if self.aim_ribbon_joints:
            self._attach_aim()

    def _attach_aim(self):
        last_follow = None
        last_parent = None

        joints = self.get_joints(as_meta=False)
        ribbon_follows = self.get_ribbon_follows(as_meta=False)

        for joint, ribbon_follow in zip(joints, ribbon_follows):
            relatives = dcc.list_relatives(ribbon_follow, relative_type='transform')
            for child in relatives:
                shape_type = dcc.node_shape_type(child)
                if shape_type == 'locator':
                    relatives = child

            if last_follow:
                axis = xform_utils.get_axis_aimed_at_child(joint)
                dcc.create_aim_constraint(
                    last_follow, joint, aim_vector=axis, up_vector=self.aim_ribbon_joints_up,
                    world_up_axis='objectrotation', world_up_object=last_parent, maintain_offset=True
                )

            last_follow = relatives
            last_parent = ribbon_follow
