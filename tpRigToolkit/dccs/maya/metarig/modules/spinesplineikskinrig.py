#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Spine implementation using Spline Ik for metarig in Maya

This module uses the following components:
    - Buffer Rig: to create buffer joints for the original joint chain.
    - Skin Spline Ik: to create Spline Ik using skin.
    - Fk Chain: to create Fk controls to manage Spline Ik ribbon clusters
"""

import tpDcc as tp
from tpDcc.dccs.maya.core import attribute as attr_utils

from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import buffer, splineikcluster, splineikskin


class SplineIkSpineSkinRig(module.RigModule, mixin.JointMixin):
    def __init__(self, *args, **kwargs):
        super(SplineIkSpineSkinRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_name(kwargs.get('name', 'splineIkSpine'))
        self.set_curve(None)
        self.set_control_count(3)
        self.set_advanced_twist(True)
        self.set_span_count(self.control_count)
        self.set_create_buffer_joints(True, name_for_switch_attribute='switch')
        self.set_match_to_rotation(True)
        self.set_stretch_on_off(False)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, *args, **kwargs):
        super(SplineIkSpineSkinRig, self).create(*args, **kwargs)

        # Component that creates buffer joints from the original Fk chain
        buffer_rig = buffer.BufferComponent(name='spineSplineIkBuffer')
        self.add_component(buffer_rig)
        buffer_rig.add_joints(self.get_joints())
        buffer_rig.set_create_sub_controls(False)
        buffer_rig.create()

        # Component that creates basic spline Ik setup
        spline_ik_rig = splineikskin.SplineIkSkin(name='spineSplineIkSkin')
        self.add_component(spline_ik_rig)
        spline_ik_rig.add_joints(buffer_rig.get_buffer_joints())
        spline_ik_rig.set_curve(self.curve)
        spline_ik_rig.set_control_count(self.control_count)
        spline_ik_rig.create()

        # Create Fk rig setup that will manage clusters
        fk_rig = SplineIkChainFkComponent(name='spineSplineIkChainFk')
        self.add_component(fk_rig)
        fk_rig.add_joints(self.get_joints())
        fk_rig.set_buffer_joints(buffer_rig.get_buffer_joints())
        fk_rig.set_clusters(clusters)
        fk_rig.create()

        # self.set_main_control(fk_rig.get_main_control())
        # for ctrl in fk_rig.get_controls():
        #     self._add_control(ctrl)
        # for sub_ctrl in fk_rig.get_sub_controls():
        #     self._add_sub_control(sub_ctrl)
        #
        # self._attach_ik_spline_to_controls()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_control_data(self, control_dict):
        """
        Sets the control data used by this rig module
        :param control_dict: dict
        """

        if not self.has_attr('control_data'):
            self.add_attribute(attr='control_data', value=control_dict)
        else:
            self.control_data = control_dict

    def set_main_control(self, main_control):
        """
        Returns main control of this module
        :return:
        """

        if not self.has_attr('main_control'):
            self.add_attribute(attr='main_control', value=main_control, attr_type='messageSimple')
        else:
            self.main_control = main_control

    def set_create_buffer_joints(self, flag, name_for_switch_attribute=None, name_for_switch_node=None):
        """
        Sets whether or not buffer chain should be created
        :param flag: bool
        :param name_for_switch_attribute: str
        :param name_for_switch_node: str
        """

        name_for_switch_attribute = name_for_switch_attribute or ''
        name_for_switch_node = name_for_switch_node or ''

        if not self.has_attr('create_buffer_joints'):
            self.add_attribute('create_buffer_joints', value=flag, attr_type='bool')
        else:
            self.create_buffer_joints = flag

        if not self.has_attr('switch_attribute_name'):
            self.add_attribute('switch_attribute_name', name_for_switch_attribute or '')
        else:
            self.switch_attribute_name = name_for_switch_attribute

        if not self.has_attr('switch_node_name'):
            self.add_attribute('switch_node_name', name_for_switch_node or '')
        else:
            self.switch_node_name = name_for_switch_node

    def get_main_control(self, as_meta=True):
        """
        Returns the main control of the rig
        First we check if main_control attribute exist. If not the first control in the list of controls.
        :return:
        """

        return self.main_control

    def set_match_to_rotation(self, flag):
        """
        Sets whether FK controls should match joints rotation or not
        :param flag: bool
        """

        if not self.has_attr('match_to_rotation'):
            self.add_attribute(attr='match_to_rotation', value=flag)
        else:
            self.match_to_rotation = flag

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

    def set_stretch_on_off(self, flag):
        """
        Sets whether to add a stretch on/off attribute
        :param flag: flag
        """

        if not self.has_attr('create_stretch'):
            self.add_attribute(attr='create_stretch', value=flag)
        else:
            self.create_stretch = flag

    def set_advanced_twist(self, flag):
        """
        Sets if we should use Spline IK top-bottom advanced twist
        :param flag: bool
        """

        if not self.has_attr('advanced_twist'):
            self.add_attribute(attr='advanced_twist', value=flag)
        else:
            self.advanced_twist = flag

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _attach_ik_spline_to_controls(self):
        """
        Internal function that connects the spline Ik setup with the controls of the Fk chain
        """

        spline_ik_component = self.get_component_by_class(splineikcluster.SplineIkCluster)
        if not spline_ik_component:
            return

        fk_chain_component = self.get_component_by_class(SplineIkChainFkComponent)
        if not fk_chain_component:
            return

        controls = fk_chain_component.get_controls(as_meta=False)
        sub_controls = fk_chain_component.get_sub_controls(as_meta=False)

        if self.advanced_twist:
            if fk_chain_component.has_attr('top_sub_control') and fk_chain_component.top_sub_control:
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
