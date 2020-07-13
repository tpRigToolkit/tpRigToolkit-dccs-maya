#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains neck rig implementation for metarig in Maya
"""

from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import fkcurvechain


class NeckRig(module.RigModule, mixin.JointMixin):
    def __init__(self, *args, **kwargs):
        super(NeckRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_name(kwargs.get('name', 'neck'))
        self.set_control_count(3)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, character_name, *args, **kwargs):
        super(NeckRig, self).create(character_name, *args, **kwargs)

        fk_curve_chain = NeckRigFkCurveComponent(name='neckFkCurve')
        self.add_component(fk_curve_chain)
        fk_curve_chain.add_joints(self.get_joints())
        fk_curve_chain.set_create_buffer_joints(False)
        fk_curve_chain.set_control_count(self.control_count)
        fk_curve_chain.create()

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


class NeckRigFkCurveComponent(fkcurvechain.FKCurveComponent, object):
    def __init__(self, *args, **kwargs):
        super(NeckRigFkCurveComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

    def _setup_first_control(self, control, current_transform, current_increment):
        self.set_first_control(control)
