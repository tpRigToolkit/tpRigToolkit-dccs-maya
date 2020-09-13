#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Ik Arm rig implementation for metarig in Maya
"""

from tpRigToolkit.dccs.maya.metarig.modules import iklimbrig


class IkArmRig(iklimbrig.IkLimbRig):
    def __init__(self, *args, **kwargs):
        super(IkArmRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'ikArm'))
