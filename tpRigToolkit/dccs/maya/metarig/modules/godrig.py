#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains god rig implementation for metarig in Maya
"""

from tpRigToolkit.dccs.maya.metarig.core import module, mixin


class GodRig(module.RigModule):
    def __init__(self, *args, **kwargs):
        super(GodRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'god'))

    def create(self, *args, **kwargs):
        super(GodRig, self).create(*args, **kwargs)

        control_data = self.control_data if self.has_attr('control_data') and self.control_data else dict()
        main_ctrl = self.create_control('main', control_data=control_data, connect_to_module=False)
        self.add_attribute(attr='main_control', value=main_ctrl, attr_type='messageSimple')
        main_ctrl.create_root()
