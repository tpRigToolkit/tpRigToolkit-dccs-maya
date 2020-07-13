#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains root rig implementation for metarig in Maya
"""

from tpRigToolkit.dccs.maya.metarig.core import module, mixin
from tpRigToolkit.dccs.maya.metarig.components import fkchain


class FkSpineRig(module.RigModule, mixin.JointMixin):
    def __init__(self, *args, **kwargs):
        super(FkSpineRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_name(kwargs.get('name', 'fkSpine'))
        self.set_create_buffer_joints(True, name_for_switch_attribute='switch')
        self.set_match_to_rotation(True)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, character_name, *args, **kwargs):
        super(FkSpineRig, self).create(character_name, *args, **kwargs)

        fk_rig = fkchain.FkChainComponent(name='spineFkChain')
        self.add_component(fk_rig)

        fk_rig.add_joints(self.get_joints())
        if self.has_attr('control_data') and self.control_data:
            fk_rig.set_control_data(self.control_data)
        fk_rig.set_create_sub_controls(True)
        fk_rig.set_hide_sub_controls_translate(False)
        fk_rig.set_match_to_rotation(self.match_to_rotation)
        fk_rig.create()

        self.set_main_control(fk_rig.get_main_control())

        if not self.message_list_get('controls', as_meta=False):
            self.message_list_connect('controls', fk_rig.get_controls())
        else:

            self.message_list_purge('controls')
            for control in fk_rig.get_controls():
                self.message_list_append('controls', control)

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
