#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig component to create SplineIK setup

This Spline Ik setup uses clusters
"""

from __future__ import print_function, division, absolute_import

import logging

import maya.cmds

from tpDcc import dcc
from tpDcc.dccs.maya.meta import metanode
from tpDcc.dccs.maya.core import curve as curve_utils, ik as ik_utils, transform as xform_utils
from tpDcc.dccs.maya.core import cluster as cluster_utils, attribute as attr_utils

from tpRigToolkit.dccs.maya.metarig.components import attach, joint

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class SplineIkCluster(joint.JointComponent, object):
    def __init__(self, *args, **kwargs):
        super(SplineIkCluster, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'splineIkCluster'))
        self.set_control_count(2)
        self.set_span_count(2)
        self.set_orig_curve(None)
        self.set_curve(None)
        self.set_ik_handle(None)
        self.set_ik_curve(None)
        self.set_start_locator(None)
        self.set_end_locator(None)
        self.set_stretch_control(None)
        self.set_stretchy(True)
        self.set_closest_y(False)
        self.set_wire_hires(False)
        self.set_advanced_twist(True)
        self.set_stretch_on_off(False)
        self.set_stretch_axis('X')
        self.set_last_pivot_top_value(False)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        """
        Creates Ribbon
        """

        super(SplineIkCluster, self).create()

        self._create_curve(self.control_count - 1)
        self._create_clusters()
        self._create_spline_ik()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_control_count(self, value):
        """
        Set the number of controls in the module
        :param value: int
        """

        if not self.has_attr('control_count'):
            self.add_attribute(attr='control_count', value=value)
        else:
            self.control_count = value

    def set_span_count(self, span_count):
        """
        Sets the number of spans the Spline IK curve/Ribbon surface should have
        :param span_count: int
        """

        if not self.has_attr('span_count'):
            self.add_attribute(attr='span_count', value=span_count)
        else:
            self.span_count = span_count

    def set_advanced_twist(self, flag):
        """
        Sets if we should use Spline IK top-bottom advanced twist
        :param flag: bool
        """

        if not self.has_attr('advanced_twist'):
            self.add_attribute(attr='advanced_twist', value=flag)
        else:
            self.advanced_twist = flag

    def set_stretch_on_off(self, flag):
        """
        Sets whether to add a stretch on/off attribute
        :param flag: flag
        """

        if not self.has_attr('create_stretch_switch'):
            self.add_attribute(attr='create_stretch_switch', value=flag)
        else:
            self.create_stretch_switch = flag

    def set_stretchy(self, flag):
        """
        Sets whether the joints should stretch to match the Spline IK or not
        :param flag: bool
        :return:
        """

        if not self.has_attr('stretchy'):
            self.add_attribute(attr='stretchy', value=flag)
        else:
            self.stretchy = flag

    def set_wire_hires(self, flag):
        """
        Sets whether wire should be applied or not
        :param flag: bool
        :return:
        """

        if not self.has_attr('wire_hires'):
            self.add_attribute(attr='wire_hires', value=flag)
        else:
            self.wire_hires = flag

    def set_closest_y(self, flag):
        """
        Sets whether closest Y axis should be applied or not
        This can solve flipping in some cases.
        :param flag: bool
        :return:
        """

        if not self.has_attr('closest_y'):
            self.add_attribute(attr='closest_y', value=flag)
        else:
            self.closest_y = flag

    def set_stretch_axis(self, axis_letter):
        """
        Sets the axis the joints should stretch on
        :param axis_letter: str
        """

        axis_list = ['X', 'Y', 'Z']
        if axis_letter == axis_list[0] or axis_letter == axis_list[0].lower():
            axis_letter = 0
        elif axis_letter == axis_list[1] or axis_letter == axis_list[1].lower():
            axis_letter = 1
        elif axis_letter == axis_list[2] or axis_letter == axis_list[2].lower():
            axis_letter = 2

        if not self.has_attr('stretch_axis'):
            self.add_attribute(
                attr='stretch_axis',
                enumName=':'.join(axis_list),
                attr_type='enum',
                value=axis_letter
            )
        else:
            self.stretch_axis = axis_letter

    def set_stretch_control(self, control):
        """
        Sets the control that will have stretchy control attribute
        :param control: str
        """

        if not self.has_attr('stretch_control'):
            self.add_attribute(attr='stretch_control', value=control, attr_type='messageSimple')
        else:
            self.stretch_control = control

    def set_orig_curve(self, orig_curve):
        """
        Set the orig curve from the Spline IK curve
        :param orig_curve: str
        """

        if not self.has_attr('orig_curve'):
            self.add_attribute(attr='orig_curve', value=orig_curve, attr_type='messageSimple')
        else:
            self.orig_curve = orig_curve

    def set_curve(self, curve):
        """
        Set the curve that the controls should move and the joints should follow when using Spline IK
        :param curve: str
        """

        if not self.has_attr('curve'):
            self.add_attribute(attr='curve', value=curve, attr_type='messageSimple')
        else:
            self.curve = curve

    def set_ik_handle(self, ik_handle):
        """
        Sets ik handle used by splineIk component
        :param ik_handle: str
        """

        if not self.has_attr('ik_handle'):
            self.add_attribute(attr='ik_handle', value=ik_handle, attr_type='messageSimple')
        else:
            self.ik_handle = ik_handle

    def set_ik_curve(self, ik_curve):
        """
        Sets curve used by SplineIK wire
        :param ik_curve: str
        """

        if not self.has_attr('ik_curve'):
            self.add_attribute(attr='ik_curve', value=ik_curve, attr_type='messageSimple')
        else:
            self.ik_curve = ik_curve

    def set_last_pivot_top_value(self, flag):
        """
        Sets the last pivot on the curve to the top of the curve
        :param flag: bool
        """

        if not self.has_attr('last_pivot_top_value'):
            self.add_attribute('last_pivot_top_value', value=flag)
        else:
            self.last_pivot_top_value = flag

    def set_start_locator(self, start_locator):
        """
        Sets the start locator used by Spline IK handle
        :param start_locator: str
        """
        if not self.has_attr('start_locator'):
            self.add_attribute(attr='start_locator', value=start_locator, attr_type='messageSimple')
        else:
            self.start_locator = start_locator

    def set_end_locator(self, end_locator):
        """
        Sets the end locator used by Spline IK handle
        :param end_locator: str
        """
        if not self.has_attr('end_locator'):
            self.add_attribute(attr='end_locator', value=end_locator, attr_type='messageSimple')
        else:
            self.end_locator = end_locator

    def get_attach_component(self):
        attach_component = None

        rig_module = self.get_rig_module()
        if not rig_module:
            return

        if rig_module.has_component(attach.AttachJointsComponent):
            attach_component = rig_module.get_component_by_class(attach.AttachJointsComponent)
        elif self.has_component(attach.AttachJointsComponent):
            attach_component = self.get_component_by_class(attach.AttachJointsComponent)

        return attach_component

    def get_clusters(self, as_meta=False):
        """
        Returns clusters objects created by cluster component
        :return:
        """

        return self.message_list_get('cluster_handles', as_meta=as_meta)

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_curve(self, span_count):
        """
        Internal function that creates the curve that handles ribbon Spline Ik setup
        :param span_count: int, number of spans in the curve
        """

        if self.curve:
            return

        orig_curve_name = self._get_name(self.name, 'splineCurve', node_type='origCurve')
        curve_name = self._get_name(self.name, 'splineCurve', node_type='curve')
        orig_crv = curve_utils.transforms_to_curve(
            transforms=self.get_joints(as_meta=False),
            spans=self.span_count,
            name=orig_curve_name
        )
        dcc.set_attribute_value(orig_crv, 'inheritsTransform', False)
        new_crv = dcc.duplicate_node(orig_crv)[0]
        dcc.rebuild_curve(
            new_crv, replace_original=True, rebuild_type=0, end_knots=1, keep_range=False, keep_control_points=False,
            keep_end_points=True, keep_tangents=False, spans=span_count, degree=3)

        orig_crv = metanode.validate_obj_arg(orig_crv, 'MetaObject', update_class=True)
        self.set_orig_curve(orig_crv)
        new_crv = metanode.validate_obj_arg(new_crv, 'MetaObject', update_class=True)
        self.set_curve(new_crv.meta_node)

        self.curve.rename(curve_name, auto_rename=False)

        self.orig_curve.set_parent(self.setup_group)
        self.curve.set_parent(self.setup_group)

    def _create_clusters(self):
        """
        Internal function that creates the cluster that deform the curve of the spline ik setup
        """

        # TODO: If cluster handlers already exist we should be able to remove them and recreate them
        if self.has_attr('cluster_handles'):
            return

        cluster_name = self._get_name(self.name, 'splineIkCluster', node_type='cluster')
        last_pivot_end = True if self.last_pivot_top_value else False

        cluster_curve = cluster_utils.ClusterCurve(geometry=self.curve.meta_node, name=cluster_name)
        cluster_curve.set_first_cluster_pivot_at_start(True)
        cluster_curve.set_last_cluster_pivot_at_end(last_pivot_end)
        cluster_curve.set_join_ends(True)
        cluster_curve.create()

        cluster_handles = cluster_curve.get_cluster_handle_list()
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

    def _setup_stretchy(self):
        rig_module = self.get_rig_module()
        if not rig_module:
            LOGGER.warning('RigComponent {} is not connected to a RigModule!'.format(self.base_name))
            return

        attach = self.get_attach_component()
        if not attach:
            return

        if not self.stretchy or not self.stretch_control:
            return

        attr_utils.create_title(self.stretch_control.meta_node, 'STRETCH')
        ik_utils.create_spline_ik_stretch(
            curve=self.ik_curve,
            joints=self.get_joints(as_meta=False)[:-1],
            prefix_name=self.base_name,
            node_for_attribute=self.stretch_control.meta_node,
            create_stretch_on_off=self.create_stretch_switch,
            scale_axis=self.stretch_axis
        )

    def _create_spline_ik(self):
        """
        Internal function that creates Spline Ik setup
        """

        self._wire_hires(self.curve)

        joints = self.get_joints(as_meta=False)

        children = dcc.list_relatives(joints[-1], full_path=False)
        if children:
            for child in children:
                dcc.set_parent_to_world(child)

        start_joint = joints[0]
        end_joint = joints[-1]

        handle = ik_utils.IkHandle(self._get_name(self.name, 'splineHandle', node_type='ikHandle'))
        handle.set_solver(handle.SOLVER_SPLINE)
        handle.set_start_joint(start_joint)
        handle.set_end_joint(end_joint)
        handle.set_curve(self.ik_curve.meta_node)
        handle = handle.create()
        self.set_ik_handle(handle)

        if self.closest_y:
            dcc.set_attribute_value(handle, 'dWorldUpAxis', 2)

        if children:
            for child in children:
                dcc.set_parent(child, joints[-1])

        dcc.set_parent(handle, self.setup_group.meta_node)

        if self.advanced_twist:
            start_locator = dcc.create_locator(name=self._get_name(self.name, 'twistStart', node_type='locator'))
            end_locator = dcc.create_locator(name=self._get_name(self.name, 'twistEnd', node_type='locator'))
            self.set_start_locator(start_locator)
            self.set_end_locator(end_locator)
            dcc.hide_node(start_locator)
            dcc.hide_node(end_locator)

            match = xform_utils.MatchTransform(joints[0], start_locator)
            match.translation_rotation()
            match = xform_utils.MatchTransform(joints[-1], end_locator)
            match.translation_rotation()

            # TODO: If we change forward axis different to X in our original chain this will not work
            # TODO: The same if we change the up axis (by default its Y)
            ik_handle = self.ik_handle[0]
            dcc.set_attribute_value(ik_handle, 'dTwistControlEnable', True)
            dcc.set_attribute_value(ik_handle, 'dWorldUpType', 4)    # Object Rotation Up (Start/End)
            dcc.connect_attribute(start_locator, 'worldMatrix', ik_handle, 'dWorldUpMatrix')
            dcc.connect_attribute(end_locator, 'worldMatrix', ik_handle, 'dWorldUpMatrixEnd')

    def _wire_hires(self, crv):
        if self.span_count == self.control_count:
            self.ik_curve = crv
            return

        if self.wire_hires:
            self.ik_curve = dcc.duplicate_node(self.orig_curve.meta_node)[0]
            dcc.set_attribute_value(self.ik_curve.meta_node, 'inheritsTransform', True)
            self.ik_curve = dcc.rename_node(
                self.ik_curve.meta_node, self._get_name(self.name, node_type='curve'))
            dcc.rebuild_curve(
                self.ik_curve.meta_node, construction_history=False, spans=self.span_count, replace_original=True,
                rebuild_type=0, end_knots=1, keep_range=False, keep_control_points=False, keep_end_points=True,
                keep_tangents=False, degree=3)
            wire_name = self._get_name(self.name, node_type='wire')
            wire, base_crv = maya.cmds.wire(
                self.ik_curve.meta_node, w=crv, dds=[(0, 1000000)], gw=False, n=wire_name)
            dcc.set_attribute_value('{}BaseWire'.format(base_crv), 'inheritsTransform', True)
        else:
            dcc.rebuild_curve(
                crv.meta_node, construction_history=True, spans=self.span_count, replace_original=True,
                rebuild_type=0, end_knots=1, keep_range=False, keep_control_points=False, keep_end_points=True,
                keep_tangents=False, degree=3)

            self.ik_curve = crv
