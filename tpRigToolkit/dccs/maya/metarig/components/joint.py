#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains joint rig metarig implementations for Maya
"""

from __future__ import print_function, division, absolute_import

from tpRigToolkit.dccs.maya.metarig.core import component, mixin


class JointComponent(component.RigComponent, mixin.JointMixin):

    def __init__(self, *args, **kwargs):
        super(JointComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_attach_joints(True)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_attach_joints(self, flag):
        """
        Sets whether joints should be attached to rig module controls or not
        :param flag: bool
        """

        if not self.has_attr('attach_joints'):
            self.add_attribute(attr='attach_joints', value=flag)
        else:
            self.attach_joints = flag
