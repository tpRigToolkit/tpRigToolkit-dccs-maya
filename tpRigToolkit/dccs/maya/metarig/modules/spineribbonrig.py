#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Spine implementation using Nurbs Ribbon for metarig in Maya
"""

from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import buffer, nurbsribbon


class NurbsRibbonSpineRig(module.RigModule, mixin.JointMixin):
    def __init__(self, *args, **kwargs):
        super(NurbsRibbonSpineRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_name(kwargs.get('name', 'nurbsRibbonSpine'))

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, *args, **kwargs):
        super(NurbsRibbonSpineRig, self).create(*args, **kwargs)

        # Component that creates buffer joints from the original Fk chain
        buffer_rig = buffer.BufferComponent(name='spineSplineIkBuffer')
        self.add_component(buffer_rig)
        buffer_rig.add_joints(self.get_joints())
        buffer_rig.set_create_sub_controls(False)
        buffer_rig.create()

        ribbon_rig = nurbsribbon.NurbsRibbon(name='spineNurbsRibbon')
        self.add_component(ribbon_rig)
        ribbon_rig.add_joints(buffer_rig.get_buffer_joints())
        ribbon_rig.create()
