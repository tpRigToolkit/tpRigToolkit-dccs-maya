#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig component to create FK joint chains controlled by a Spline Ik
"""

from __future__ import print_function, division, absolute_import

import maya.cmds

from tpDcc import dcc
from tpDcc.dccs.maya.core import transform as xform_utils, name as name_utils

from tpRigToolkit.dccs.maya.metarig.components import fkchain, splineikcluster


class FkSplineIkComponent(fkchain.FkChainComponent, object):
    def __init__(self, *args, **kwargs):
        super(FkSplineIkComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'fkCurve'))
        self.set_curve(None)
        self.set_orient_joint(None)
        self.set_skip_first_control(False)
        self.set_control_count(3)
        self.set_span_count(self.control_count)
        self.set_advanced_twist(True)
        self.set_orient_controls_to_joints(False)
        self.set_aim_end_vectors(False)
        self.set_first_control(None)
        self.set_top_sub_control(None)
        self.set_create_follows(True)
        self.set_create_bottom_follow(False)
        self.set_stretch_on_off(False)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):

        super(FkSplineIkComponent, self).create()

        spine_joints = self.get_buffer_joints(as_meta=True) or self.get_joints(as_meta=True)

        spline_ik = splineikcluster.SplineIkCluster(name='{}SplineIk'.format(self.name))
        self.add_component(spline_ik)
        spline_ik.add_joints(joints=spine_joints)
        spline_ik.set_curve(self.curve)
        spline_ik.set_control_count(self.control_count)
        spline_ik.set_stretch_on_off(self.create_stretch_switch)
        spline_ik.set_advanced_twist(self.advanced_twist)
        spline_ik.create()

        # This is the functionality that _setup function would call.
        # We must do it here because at this point clusters (which are the transforms that will
        # be managed by the FK chain are available)
        clusters = self.get_clusters(as_meta=True)
        transforms = clusters if clusters else spine_joints
        super(FkSplineIkComponent, self)._setup(transforms)

        self._attach_ik_spline_to_controls()

    #     spline_ik.add_joints(buffer_joints, clean=True)
    #     spline_ik.set_stretch_control(self.get_controls(as_meta=False)[-1])
    #     for ctrl in self.get_controls():
    #         spline_ik.add_control(ctrl)
    #     spline_ik.create()
    #     if buffer_joints != spine_joints:
    #         controls = self.get_controls(as_meta=False)
    #         buffer_joints = self.get_buffer_joints(as_meta=False)
    #         follow = space_utils.create_follow_group(controls[0], buffer_joints[0])
    #
    # if self.aim_end_vectors:
    #     self._create_aims()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_curve(self, curve):
        """
        Set the curve that the controls should move and the joints should follow
        :param curve: str
        """

        if not self.has_attr('curve'):
            self.add_attribute(attr='curve', value=curve, attr_type='messageSimple')
        else:
            self.curve = curve

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
        Sets the number of spans the Spline IK curve surface should have
        :param span_count: int
        """

        if not self.has_attr('span_count'):
            self.add_attribute(attr='span_count', value=span_count)
        else:
            self.span_count = span_count

    def set_skip_first_control(self, flag):
        """
        Sets if first control should be skipped or not
        :param flag: bool
        """

        if not self.has_attr('skip_first_control'):
            self.add_attribute(attr='skip_first_control', value=flag)
        else:
            self.skip_first_control = flag

    def set_create_follows(self, flag):
        """
        By default first and last controls fade influence up the sub controls of the setup.
        If this is False, the top and bottom controls will no longer affect the mid sub controls
        :param flag: bool
        """

        if not self.has_attr('create_follows'):
            self.add_attribute(attr='create_follows', value=flag)
        else:
            self.create_follows = flag

    def set_create_bottom_follow(self, flag):
        """
        If True, this wll cause the last control in the Fk chain to have a follow fade on sub controls up the
        chain. If create_follows is set to False, this attribute will be ignored.
        :param flag: bool
        """

        if not self.has_attr('create_bottom_follow'):
            self.add_attribute(attr='create_bottom_follow', value=flag)
        else:
            self.create_bottom_follow = flag

    def set_orient_joint(self, joint):
        """
        Sets a joint to match orientation of the controls to
        :param joint: str, name of the joint
        """

        if not self.has_attr('orient_joint'):
            self.add_attribute(attr='orient_joint', value=joint, attr_type='messageSimple')
        else:
            self.orient_joint = joint

    def set_orient_controls_to_joints(self, flag):
        """
        Sets whether controls orientation should be matched to nearest joint
        :param flag: bool
        """

        if not self.has_attr('orient_controls_to_joints'):
            self.add_attribute(attr='orient_controls_to_joints', value=flag)
        else:
            self.orient_controls_to_joints = flag

    def set_aim_end_vectors(self, flag):
        """
        Sets whether the first and last clusters should aim the mid control
        :param flag: bool
        """

        if not self.has_attr('aim_end_vectors'):
            self.add_attribute(attr='aim_end_vectors', value=flag)
        else:
            self.aim_end_vectors = flag

    def set_first_control(self, control):
        """
        Sets which is the first control used by this rig
        :param control:
        :return:
        """

        if not self.has_attr('first_control'):
            self.add_attribute(attr='first_control', value=control, attr_type='messageSimple')
        else:
            self.first_control = control

    def set_top_sub_control(self, control):
        """
        Sets which is the top sub control used by this rig
        :param control:
        :return:
        """

        if not self.has_attr('top_sub_control'):
            self.add_attribute(attr='top_sub_control', value=control, attr_type='messageSimple')
        else:
            self.top_sub_control = control

    def set_stretch_on_off(self, flag):
        """
        Sets whether to add a stretch on/off attribute
        :param flag: flag
        """

        if not self.has_attr('create_stretch_switch'):
            self.add_attribute(attr='create_stretch_switch', value=flag)
        else:
            self.create_stretch_switch = flag

    def set_advanced_twist(self, flag):
        """
        Sets if we should use Spline IK top-bottom advanced twist
        :param flag: bool
        """

        if not self.has_attr('advanced_twist'):
            self.add_attribute(attr='advanced_twist', value=flag)
        else:
            self.advanced_twist = flag

    def get_curve_component(self):
        """
        Returns curve component applied (SplineIK)
        """

        return self.get_component_by_class(splineikcluster.SplineIkCluster)

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_aims(self):

        clusters = self.get_clusters(as_meta=False)
        sub_controls = self.get_sub_controls(as_meta=False)
        controls = self.get_controls(as_meta=False)

        maya.cmds.delete(maya.cmds.listRelatives(clusters[0], ad=True, type='constraint'))
        maya.cmds.delete(maya.cmds.listRelatives(clusters[-1], ad=True, type='constraint'))

        aim1 = dcc.create_empty_group(
            name=name_utils.find_unique_name('{}'.format(self._get_name('aimCluster', type='group'))))
        aim2 = dcc.create_empty_group(
            name=name_utils.find_unique_name('{}'.format(self._get_name('aimCluster', type='group'))))

        xform_aim1 = xform_utils.create_buffer_group(aim1)
        xform_aim2 = xform_utils.create_buffer_group(aim2)

        xform_utils.MatchTransform(sub_controls[0], xform_aim1).translation()
        xform_utils.MatchTransform(sub_controls[-1], xform_aim1).translation()

        dcc.create_parent_constraint(xform_aim1, sub_controls[0], maintain_offset=True)
        dcc.create_parent_constraint(xform_aim1, sub_controls[-1], maintain_offset=True)

        mid_control_id = len(sub_controls) / 2

        maya.cmds.aimConstraint(sub_controls[mid_control_id], aim1, wuo=controls[0], wut='objectrotation')
        maya.cmds.aimConstraint(sub_controls[mid_control_id], aim2, wuo=controls[-1], wut='objectrotation')

        dcc.set_parent(clusters[0], aim1)
        dcc.set_parent(clusters[-1], aim2)

        dcc.set_parent(xform_aim1, xform_aim2, self.setup_group.meta_node)
