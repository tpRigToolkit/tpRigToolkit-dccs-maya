#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Spine implementation using Nurbs Ribbon for metarig in Maya
"""

from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import buffer, nurbsribbon, splineikribbonfkchain


class NurbsRibbonSpineRig(module.RigModule, mixin.JointMixin):
    def __init__(self, *args, **kwargs):
        super(NurbsRibbonSpineRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_name(kwargs.get('name', 'nurbsRibbonSpine'))
        self.set_create_buffer_joints(True, name_for_switch_attribute='switch')
        self.set_control_count(2)
        self.set_span_count(self.control_count)
        self.set_match_to_rotation(True)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, *args, **kwargs):
        super(NurbsRibbonSpineRig, self).create(*args, **kwargs)

        # Component that creates buffer joints from the original Fk chain
        buffer_rig = buffer.BufferComponent(name='spineSplineIkBuffer')
        self.add_component(buffer_rig)
        buffer_rig.add_joints(self.get_joints())
        buffer_rig.set_create_buffer_joints(
            self.create_buffer_joints, self.switch_attribute_name, self.switch_node_name)
        buffer_rig.set_create_sub_controls(False)
        buffer_rig.create()

        ribbon_rig = nurbsribbon.NurbsRibbon(name='spineNurbsRibbon')
        self.add_component(ribbon_rig)
        ribbon_rig.add_joints(buffer_rig.get_buffer_joints())
        ribbon_rig.set_control_count(self.control_count)
        ribbon_rig.set_span_count(self.span_count)
        ribbon_rig.create()
        handlers = ribbon_rig.get_clusters(as_meta=True)

        # Create Fk rig setup that will manage clusters
        fk_rig = splineikribbonfkchain.SplineIkRibbonFkChainComponent(name='spineSplineIkChainFk')
        self.add_component(fk_rig)
        fk_rig.add_joints(self.get_joints())
        fk_rig.set_create_sub_controls(self.create_sub_controls)
        fk_rig.set_match_to_rotation(self.match_to_rotation)
        fk_rig.set_control_size(self.control_size)
        fk_rig.set_control_data(self.control_data)
        fk_rig.set_buffer_joints(buffer_rig.get_buffer_joints())
        fk_rig.set_handlers(handlers)
        fk_rig.create()

        self.set_main_control(fk_rig.get_main_control())
        for ctrl in fk_rig.get_controls():
            self._add_control(ctrl)
        for sub_ctrl in fk_rig.get_sub_controls():
            self._add_sub_control(sub_ctrl)

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
