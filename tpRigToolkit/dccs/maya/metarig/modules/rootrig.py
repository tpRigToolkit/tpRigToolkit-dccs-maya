#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains root rig implementation for metarig in Maya
"""

from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import fkchain


class RootRig(module.RigModule, mixin.JointMixin):
    def __init__(self, *args, **kwargs):
        super(RootRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_name(kwargs.get('name', 'root'))

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, *args, **kwargs):
        super(RootRig, self).create(*args, **kwargs)

        fk_rig = fkchain.FkChainComponent(name='rootFkChain')
        self.add_component(fk_rig)

        fk_rig.add_joints(self.get_joints())
        if self.has_attr('control_data') and self.control_data:
            fk_rig.set_control_data(self.control_data)
        fk_rig.set_create_sub_controls(self.create_sub_controls)
        fk_rig.set_hide_sub_controls_translate(False)
        fk_rig.create()

        self.set_main_control(fk_rig.get_main_control())

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

    def get_main_control(self, as_meta=True):
        """
        Returns the main control of the rig
        First we check if main_control attribute exist. If not the first control in the list of controls.
        :return:
        """

        return self.main_control
