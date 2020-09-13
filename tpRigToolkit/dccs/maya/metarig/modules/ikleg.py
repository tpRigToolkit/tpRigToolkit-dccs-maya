#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Ik Leg rig implementation for metarig in Maya
"""

from tpRigToolkit.dccs.maya.metarig.modules import iklimbrig


class IkLegRig(iklimbrig.IkLimbRig):
    def __init__(self, *args, **kwargs):
        super(IkLegRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'ikLeg'))
