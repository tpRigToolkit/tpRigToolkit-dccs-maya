#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig component to create Ribbon setups
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
from tpDcc.dccs.maya.meta import metanode
from tpDcc.dccs.maya.core import geometry as geo_utils, deformer as deform_utils

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
        self.set_ribbon_buffer_group(False)
        self.set_ribbon_joint_aim(False, [0, 0, 1])
        self.set_last_pivot_top_value(False)

    def create(self, *args, **kwargs):
        """
        Creates Ribbon
        """

        super(NurbsRibbon, self).create()

        self._create_surface(self.control_count - 1)
        self._create_clusters()

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

    def set_ribbon_buffer_group(self, flag):
        """
        Sets whether or not a top group should be created where all follicles will be parented into
        :param flag: bool
        """

        if not self.has_attr('ribbon_buffer_group'):
            self.add_attribute(attr='ribbon_buffer_group', value=flag)
        else:
            self.ribbon_buffer_group = flag

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

        tp.Dcc.set_attribute_value(surface, 'inheritsTransform', False)
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

        cluster_surface = deform_utils.ClusterSurface(geometry=self.surface.meta_node, name=cluster_name)
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

        for handle in handles:
            handle.set_parent(self.setup_group)

        return handles

