#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for metarig modules for Maya
"""

from tpDcc.dccs.maya.meta import metanode, metaobject

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.core import utils


class RigModule(metanode.MetaNode, object):
    def __init__(self, *args, **kwargs):
        super(RigModule, self).__init__(*args, **kwargs)

        if self.cached:
            return

        # self.set_create_sub_controls(False)

    def get_character_name(self):
        """
        Returns the name of the character linked to this module
        :return: str
        """

        if not self.has_attr('root_module'):
            tpRigToolkit.logger.warning('Rig module {} is not connected to a character!'.format(self.base_name))
            return None

        # TODO: Here se should check if the MetaNode is of type RigCharacter

        return self.root_module.base_name

    def connect_to_character(self, character_name):
        """
        Connects rig module to its respective Character Node
        """

        character = utils.get_character_module(character_name)
        if not character:
            character = utils.build_character(character_name)

        character.append_module(self)

        if self.has_attr('controls_group') and self.controls_group.is_valid():
            self.controls_group.set_parent(character.controls_group)

    def set_controls_group_name(self, new_name='controls'):
        """
        Set the name of the controls group for the rig module
        If the module has no controls group, it will be created
        :param new_name: str, new name of the group
        """

        if self.has_attr('controls_group'):
            self.controls_group.rename(new_name, rename_child_links=True)
        else:
            self.add_attribute(
                attr='controls_group',
                value=self.create_group('{}_{}'.format(self.base_name, new_name)),
                attr_type='messageSimple'
            )

    def set_setup_group_name(self, new_name='setup'):
        """
        Set the name of the setup group for the rig module
        If the module has no setup group, it will be created
        :param new_name: str
        """
        if self.has_attr('setup_group'):
            self.setup_group.rename(new_name, rename_child_links=True)
        else:
            self.add_attribute(
                attr='setup_group', value=self.create_group('{}_{}'.format(
                    self.base_name, new_name)), attr_type='messageSimple')
        self.setup_group.hide()

    def create_group(self, group_name):
        """
        Function that creates new groups for the character
        :param group_name: str, name of the group
        """

        new_group = metaobject.MetaObject(name=group_name, name_kwargs={'type': 'group'}, node_type='transform')
        new_group.add_attribute(attr='rig_module', value=self, attr_type='messageSimple')

        return new_group

    def create(self, character_name, *args, **kwargs):
        """
        Creates the rig module
        This function should be extended in custom rig modules
        This function only must be called once rig module setup is done
        :param character_name: str
        :param args:
        :param kwargs:
        """

        tpRigToolkit.logger.info(
            'Creating MetaRig module: {} | Name: {}'.format(self.__class__.__name__, self.base_name))

        if not self.has_attr('controls_group'):
            self.set_controls_group_name()
        if not self.has_attr('setup_group'):
            self.set_setup_group_name()
