#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig component to create SplineIK setup

This Spline Ik setup uses joints and a skin cluster to deform the spline Ik curve

Limitations:
    - The mid joint of the Spline Ik setup only can deform the curve using translation (no twisting)
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode
from tpDcc.dccs.maya.core import curve as curve_utils, ik as ik_utils, transform as xform_utils, skin as skin_utils
from tpDcc.dccs.maya.core import deformer as deform_utils, attribute as attr_utils

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.components import attach, joint, buffer


class SplineIkSkin(buffer.BufferComponent, object):
    def __init__(self, *args, **kwargs):
        super(SplineIkSkin, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'splineIkSkin'))
        self.set_create_buffer_joints(True)
        self.set_control_count(2)
        self.set_span_count(2)
        self.set_orig_curve(None)
        self.set_curve(None)
        self.set_ik_handle(None)
        self.set_ik_curve(None)
        self.set_start_marker(None)
        self.set_mid_marker(None)
        self.set_end_marker(None)
        self.set_closest_y(False)
        self.set_wire_hires(False)
        self.set_advanced_twist(True)
        self.set_last_pivot_top_value(False)
        self.set_align_start_end_markers_rotation(True)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        """
        Creates Ribbon
        """

        super(SplineIkSkin, self).create()

        self._create_curve(self.control_count - 1)
        self._create_marker_joints()
        self._create_spline_ik()

        buffer_joints = self.get_buffer_joints(as_meta=True)
        if buffer_joints:
            buffer_joints[0].set_parent(self.setup_group)

        self.delete_control()

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

    def set_align_start_end_markers_rotation(self, flag):
        """
        Sets whether or not start and end marker joints should have the same orientation of the original joints
        :param flag: bool
        """

        if not self.has_attr('align_start_end_markers_rotation'):
            self.add_attribute('align_start_end_markers_rotation', value=flag)
        else:
            self.align_start_end_markers_rotation = flag

    def set_start_marker(self, start_marker):
        """
        Sets the start marker joint used to deform spline ik curve
        :param start_marker: str
        """
        if not self.has_attr('start_marker'):
            self.add_attribute(attr='start_marker', value=start_marker, attr_type='messageSimple')
        else:
            self.start_marker = start_marker

    def set_mid_marker(self, mid_marker):
        """
        Sets the mid marker joint used to deform spline ik curve
        :param mid_marker: str
        """
        if not self.has_attr('mid_marker'):
            self.add_attribute(attr='mid_marker', value=mid_marker, attr_type='messageSimple')
        else:
            self.mid_marker = mid_marker

    def set_end_marker(self, end_marker):
        """
        Sets the end marker joint used to deform spline ik curve
        :param end_marker: str
        """
        if not self.has_attr('end_marker'):
            self.add_attribute(attr='end_marker', value=end_marker, attr_type='messageSimple')
        else:
            self.end_marker = end_marker

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

    def set_advanced_twist(self, flag):
        """
        Sets if we should use Spline IK top-bottom advanced twist
        :param flag: bool
        """

        if not self.has_attr('advanced_twist'):
            self.add_attribute(attr='advanced_twist', value=flag)
        else:
            self.advanced_twist = flag

    def get_marker_joints(self, as_meta=False):
        """
        Returns marker joints objects
        :return:
        """

        return self.message_list_get('marker_joints', as_meta=as_meta)

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

        joints = self.get_buffer_joints(as_meta=False) or self.get_joints(as_meta=False)

        orig_curve_name = self._get_name(self.name, 'splineCurve', node_type='origCurve')
        curve_name = self._get_name(self.name, 'splineCurve', node_type='curve')
        orig_crv = curve_utils.transforms_to_curve(transforms=joints, spans=self.span_count, name=orig_curve_name)
        tp.Dcc.set_attribute_value(orig_crv, 'inheritsTransform', False)
        new_crv = tp.Dcc.duplicate_object(orig_crv)
        tp.Dcc.rebuild_curve(
            new_crv, replace_original=True, rebuild_type=0, end_knots=1, keep_range=False, keep_control_points=False,
            keep_end_points=True, keep_tangents=False, spans=span_count, degree=3)

        orig_crv = metanode.validate_obj_arg(orig_crv, 'MetaObject', update_class=True)
        self.set_orig_curve(orig_crv)
        new_crv = metanode.validate_obj_arg(new_crv, 'MetaObject', update_class=True)
        self.set_curve(new_crv.meta_node)

        self.curve.rename(curve_name, auto_rename=False)

        self.orig_curve.set_parent(self.setup_group)
        self.curve.set_parent(self.setup_group)

    def _create_marker_joints(self):
        """
        Internal function that creates the marker joints that deform the curve of the spline ik setup
        """

        # TODO: If marker joints already exist we should be able to remove them and recreate them
        if self.has_attr('marker_joints'):
            return

        joint_name = self._get_name(self.name, 'splineIkSkin', node_type='joint')
        last_pivot_end = True if self.last_pivot_top_value else False

        skin_curve = skin_utils.SkinJointCurve(geometry=self.curve.meta_node, name=joint_name, joint_radius=2.0)
        skin_curve.set_first_joint_pivot_at_start(True)
        skin_curve.set_last_joint_pivot_at_end(last_pivot_end)
        skin_curve.set_join_ends(True)
        skin_curve.create()

        marker_joints = skin_curve.get_joints_list()
        marker_joints = [metanode.validate_obj_arg(joint, 'MetaObject', update_class=True) for joint in marker_joints]

        if not self.message_list_get('marker_joints', as_meta=False):
            self.message_list_connect('marker_joints', marker_joints)
        else:
            self.message_list_purge('marker_joints')
            for marker_joint in marker_joints:
                self.message_list_append('marker_joints', marker_joint)

        for marker_joint in marker_joints:
            marker_joint.set_parent(self.setup_group)

        mid_marker_index = int(len(marker_joints)/2)
        marker_joints[0].rename(self._get_name(self.name, 'markerStart', node_type='locator'))
        marker_joints[mid_marker_index].rename(self._get_name(self.name, 'markerMid', node_type='locator'))
        marker_joints[-1].rename(self._get_name(self.name, 'markerEnd', node_type='locator'))

        self.set_start_marker(marker_joints[0])
        self.set_mid_marker(marker_joints[mid_marker_index])
        self.set_end_marker(marker_joints[-1])

        return marker_joints

    def _create_spline_ik(self):
        """
        Internal function that creates Spline Ik setup
        """

        self._wire_hires(self.curve)

        joints = self.get_buffer_joints(as_meta=False) or self.get_joints(as_meta=False)

        children = tp.Dcc.list_relatives(joints[-1], full_path=False)
        if children:
            for child in children:
                tp.Dcc.set_parent_to_world(child)

        start_joint = joints[0]
        end_joint = joints[-1]

        handle = ik_utils.IkHandle(self._get_name(self.name, 'splineHandle', node_type='ikHandle'))
        handle.set_solver(handle.SOLVER_SPLINE)
        handle.set_start_joint(start_joint)
        handle.set_end_joint(end_joint)
        handle.set_curve(self.ik_curve.meta_node)
        handle = handle.create()
        handle = metanode.validate_obj_arg(handle, 'MetaObject', update_class=True)
        self.set_ik_handle(handle)

        if self.closest_y:
            tp.Dcc.set_attribute_value(handle.meta_node, 'dWorldUpAxis', 2)

        if children:
            for child in children:
                tp.Dcc.set_parent(child, joints[-1])

        handle.set_parent(self.setup_group)

        if self.advanced_twist:
            ik_handle = self.ik_handle.meta_node
            start_marker = self.start_marker.meta_node
            end_marker = self.end_marker.meta_node

            # NOTE: This is moving the start and end joint markers while they are already skinned
            # NOTE: We enable the move skinned joints option before moving the joints
            maya.mel.eval('moveJointsMode 1')
            match = xform_utils.MatchTransform(joints[0], start_marker)
            match.translation_rotation() if self.align_start_end_markers_rotation else match.translation()
            match = xform_utils.MatchTransform(joints[-1], end_marker)
            match.translation_rotation() if self.align_start_end_markers_rotation else match.translation()

            # TODO: Maybe this is not the desired behaviour in some scenarios. Add argument to handle it.
            # TODO: When working with broken rigs, the last joint cannot have the desired orientation, so instead of
            # TODO: orienting the end marker to the last joint we orient it to the immediate child of the last join
            if self.align_start_end_markers_rotation:
                match = xform_utils.MatchTransform(joints[-2], end_marker)
                match.rotation()

            maya.mel.eval('moveJointsMode 0')

            # TODO: If we change forward axis different to X in our original chain this will not work
            # TODO: The same if we change the up axis (by default its Y)
            tp.Dcc.set_attribute_value(ik_handle, 'dTwistControlEnable', True)
            tp.Dcc.set_attribute_value(ik_handle, 'dWorldUpType', 4)    # Object Rotation Up (Start/End)
            tp.Dcc.connect_attribute(start_marker, 'worldMatrix', ik_handle, 'dWorldUpMatrix')
            tp.Dcc.connect_attribute(end_marker, 'worldMatrix', ik_handle, 'dWo rldUpMatrixEnd')

    def _wire_hires(self, crv):
        if self.span_count == self.control_count:
            self.ik_curve = crv
        else:
            if self.wire_hires:
                self.ik_curve = tp.Dcc.duplicate_object(self.orig_curve.meta_node)
                tp.Dcc.set_attribute_value(self.ik_curve.meta_node, 'inheritsTransform', True)
                self.ik_curve = tp.Dcc.rename_node(
                    self.ik_curve.meta_node, self._get_name(self.name, node_type='curve'))
                tp.Dcc.rebuild_curve(
                    self.ik_curve.meta_node, construction_history=False, spans=self.span_count, replace_original=True,
                    rebuild_type=0, end_knots=1, keep_range=False, keep_control_points=False, keep_end_points=True,
                    keep_tangents=False, degree=3)
                wire_name = self._get_name(self.name, node_type='wire')
                wire, base_crv = maya.cmds.wire(
                    self.ik_curve.meta_node, w=crv, dds=[(0, 1000000)], gw=False, n=wire_name)
                tp.Dcc.set_attribute_value('{}BaseWire'.format(base_crv), 'inheritsTransform', True)
            else:
                tp.Dcc.rebuild_curve(
                    crv.meta_node, construction_history=True, spans=self.span_count, replace_original=True,
                    rebuild_type=0, end_knots=1, keep_range=False, keep_control_points=False, keep_end_points=True,
                    keep_tangents=False, degree=3)

                self.ik_curve = crv
