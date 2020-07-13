#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig component to create FK joint chains controlled by a curve
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import transform as xform_utils, name as name_utils, attribute as attr_utils

from tpRigToolkit.dccs.maya.metarig.components import fkcurl, splineikribbon, nurbsribbon


class FKCurveComponent(fkcurl.FkCurlNoScale, object):
    def __init__(self, *args, **kwargs):
        super(FKCurveComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'fkCurve'))
        self.set_curve(None)
        self.set_orient_joint(None)
        self.set_skip_first_control(False)
        self.set_control_count(3)
        self.set_span_count(self.control_count)
        self.set_use_ribbon(False)
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

        super(FKCurveComponent, self).create()

        spine_joints = self.get_buffer_joints(as_meta=True) or self.get_joints(as_meta=True)

        # First we do a pass to create clusters depending the type of fk curve we want to create (ribbon or splineIK)
        if self.use_ribbon:
            ribbon_cmp = nurbsribbon.NurbsRibbon(name='{}NurbsRibbon'.format(self.name))
            self.add_component(ribbon_cmp)
            ribbon_cmp.add_joints(spine_joints)
            ribbon_cmp.create()
        else:
            spline_ik = splineikribbon.SplineIkRibbon(name='{}SplineIk'.format(self.name))
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
        super(FKCurveComponent, self)._setup(transforms)

        if not self.use_ribbon:
            self._attach_ik_spline_to_controls()

    #     if self.use_ribbon:
    #         ribbon_cmp.create()
    #         ribbon_cmp.add_joints(buffer_joints, clean=True)
    #     else:
    #         spline_ik.add_joints(buffer_joints, clean=True)
    #         spline_ik.set_stretch_control(self.get_controls(as_meta=False)[-1])
    #         for ctrl in self.get_controls():
    #             spline_ik.add_control(ctrl)
    #         spline_ik.create()
    #         if buffer_joints != spine_joints:
    #             controls = self.get_controls(as_meta=False)
    #             buffer_joints = self.get_buffer_joints(as_meta=False)
    #             follow = space_utils.create_follow_group(controls[0], buffer_joints[0])
    #
    #     if self.aim_end_vectors:
    #         self._create_aims()

    def _setup(self, transforms=None):
        """
        We override this function to avoid to execute the FK chain setup before clusters are created
        We are forced to call super at the beginning to make sure that all parent modules attributes
        are inherited by this component (naming file, etc).

        We call this at the end of the creat function
        :param transforms:
        :return:
        """

        pass

    def _setup_all_controls(self, control, current_transform, increment):

        match = xform_utils.MatchTransform(current_transform.meta_node, control.top().meta_node)
        match.translation_to_rotate_pivot()

        if self.orient_controls_to_joints:
            if not self.orient_joint:
                jnt = self._get_closest_joint(increment)
            else:
                jnt = self.orient_joint[0]

            match = xform_utils.MatchTransform(jnt, current_transform.meta_node)
            match.rotation()

        cls_cmp = self.get_clusters()

        if self.create_sub_controls:
            sub_ctrl = control.get_sub_controls()[-1]
            tp.Dcc.create_parent_constraint(cls_cmp[increment], sub_ctrl.meta_node, maintain_offset=True)
        else:
            tp.Dcc.create_parent_constraint(cls_cmp[increment], control.meta_node, maintain_offset=True)

    def _setup_first_control(self, control, current_transform, current_increment):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the first control in the FK chain.
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        :param current_increment: ind, number of control in the FK chain
        """

        first_control = self.get_controls()[0]
        self.set_first_control(first_control)
        if self.skip_first_control:
            first_control.delete_shapes()

        if self.create_sub_controls:
            top_sub_control = self.get_sub_controls()[0]
            self.set_top_sub_control(top_sub_control)
            if self.skip_first_control:
                top_sub_control.delete_shapes()

    def _setup_last_control(self, control, current_transform):
        """
         Internal function that is called during the FK chain building process.
         This function is called for the last control in the FK chain.
         :param control: str, name of the control in the FK chain
         :param current_transform: str, transform linked to the given Fk chain control
         """

        if not self.create_sub_controls:
            return

        if self.create_follows:
            pass

    # def _setup_control_greater_than_first(self, control, current_transform, current_increment):
    #     """
    #     Internal function that is called during the FK chain building process.
    #     This function is called for all the controls in the FK chain that are not the first one.
    #     :param control: str, name of the control in the FK chain
    #     :param current_transform: str, transform linked to the given Fk chain control
    #     """
    #
    #     pass

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_clusters(self, as_meta=False):
        cmp = self.get_curve_component()
        if cmp:
            cls_cmp = cmp.get_clusters(as_meta=as_meta)
            return cls_cmp

        return None

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
        Sets the number of spans the Spline IK curve/Ribbon surface should have
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

    def set_use_ribbon(self, flag):
        """
        Sets if a ribbon should be used to rig FKCurve or not
        :param flag: bool
        """

        if not self.has_attr('use_ribbon'):
            self.add_attribute(attr='use_ribbon', value=flag)
        else:
            self.use_ribbon = flag

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
        Returns curve component applied (Ribbon or SplineIK)
        """

        if self.has_component(splineikribbon.SplineIkRibbon):
            return self.get_component_by_class(splineikribbon.SplineIkRibbon)
        elif self.has_component(nurbsribbon.NurbsRibbon):
            return self.get_component_by_class(nurbsribbon.NurbsRibbon)

        return None

    def _get_closest_joint(self, increment):
        cmp_cls = self.get_clusters()
        current_cls = cmp_cls[increment]

        return xform_utils.get_closest_transform(current_cls, self.get_buffer_joints(as_meta=False))

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_sub_control(self, id=None):
        """
        Internal function that creates a sub control for this rig component
        :return: RigControl
        """

        sub_control = self._create_control(sub=True, id=id)

        return sub_control

    def _create_aims(self):

        clusters = self.get_clusters(as_meta=False)
        sub_controls = self.get_sub_controls(as_meta=False)
        controls = self.get_controls(as_meta=False)

        maya.cmds.delete(maya.cmds.listRelatives(clusters[0], ad=True, type='constraint'))
        maya.cmds.delete(maya.cmds.listRelatives(clusters[-1], ad=True, type='constraint'))

        aim1 = tp.Dcc.create_empty_group(
            name=name_utils.find_unique_name('{}'.format(self._get_name('aimCluster', type='group'))))
        aim2 = tp.Dcc.create_empty_group(
            name=name_utils.find_unique_name('{}'.format(self._get_name('aimCluster', type='group'))))

        xform_aim1 = xform_utils.create_buffer_group(aim1)
        xform_aim2 = xform_utils.create_buffer_group(aim2)

        xform_utils.MatchTransform(sub_controls[0], xform_aim1).translation()
        xform_utils.MatchTransform(sub_controls[-1], xform_aim1).translation()

        tp.Dcc.create_parent_constraint(xform_aim1, sub_controls[0], maintain_offset=True)
        tp.Dcc.create_parent_constraint(xform_aim1, sub_controls[-1], maintain_offset=True)

        mid_control_id = len(sub_controls) / 2

        maya.cmds.aimConstraint(sub_controls[mid_control_id], aim1, wuo=controls[0], wut='objectrotation')
        maya.cmds.aimConstraint(sub_controls[mid_control_id], aim2, wuo=controls[-1], wut='objectrotation')

        tp.Dcc.set_parent(clusters[0], aim1)
        tp.Dcc.set_parent(clusters[-1], aim2)

        tp.Dcc.set_parent(xform_aim1, xform_aim2, self.setup_group.meta_node)

    def _attach_ik_spline_to_controls(self):
        """
        Internal function that connects the spline Ik setup with the controls of the Fk chain
        """

        spline_ik_component = self.get_component_by_class(splineikribbon.SplineIkRibbon)
        if not spline_ik_component:
            return

        if not self.attach_joints:
            return

        controls = self.get_controls(as_meta=False)
        sub_controls = self.get_sub_controls(as_meta=False)

        if self.advanced_twist:
            if self.has_attr('top_sub_control') and self.top_sub_control:
                tp.Dcc.set_parent(spline_ik_component.start_locator[0], sub_controls[0])
            else:
                if not sub_controls:
                    tp.Dcc.set_parent(spline_ik_component.start_locator[0], controls[0])
                else:
                    tp.Dcc.set_parent(spline_ik_component.start_locator[0], sub_controls[0])

            if sub_controls:
                tp.Dcc.set_parent(spline_ik_component.end_locator[0], sub_controls[-1])
            else:
                tp.Dcc.set_parent(spline_ik_component.end_locator[0], controls[-1])
        else:
            buffer_joints = self.get_buffer_joints(as_meta=False)
            joints = self.get_joints(as_meta=False)

            if buffer_joints != joints:
                follow = tp.Dcc.create_follow_group(controls[0], buffer_joints[0])
                tp.Dcc.set_parent(follow, self.setup_group)

            var = attr_utils.NumericAttribute('twist')
            var.set_variable_type(attr_utils.AttributeTypes.Double)
            var.create(controls[0])
            var.connect_out('{}.twist'.format(spline_ik_component.ik_handle.meta_node))



