#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for metarig characters for Maya
"""

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode, metaobject


class RigCharacter(metanode.MetaNode, object):
    def __init__(self, *args, **kwargs):
        super(RigCharacter, self).__init__(*args, **kwargs)

    def set_main_group_name(self, new_name='main_group'):
        """
        Set the name of the controls group for the character
        If the character has no controls group, it will be created
        :param new_name: str, new name of the group
        """

        if self.has_attr('main_group'):
            self.controls_group.rename(new_name, rename_child_links=True, type='group')
        else:
            new_grp = self.create_group(group_name=new_name)
            self.add_attribute(attr='main_group', value=new_grp, attr_type='messageSimple')

    def set_controls_group_name(self, new_name='controls'):
        """
        Set the name of the controls group for the character
        If the character has no controls group, it will be created
        :param new_name: str, new name of the group
        """

        if self.has_attr('controls_group'):
            self.controls_group.rename(new_name, rename_child_links=True, type='group')
        else:
            new_grp = self.create_group(group_name=new_name)
            self.add_attribute(attr='controls_group', value=new_grp, attr_type='messageSimple')

    def set_rig_group_name(self, new_name='rig'):
        """
        Set the name of the rig group for the character
        If the character has no controls group, it will be created
        :param new_name: str, new name of the group
        """

        if self.has_attr('rig_group'):
            self.rig_group.rename(new_name, rename_child_links=True, type='group')
        else:
            new_grp = self.create_group(group_name=new_name)
            self.add_attribute(attr='rig_group', value=new_grp, attr_type='messageSimple')

    def create_group(self, group_name):
        """
        Function that creates new groups for the character
        :param group_name: str, name of the group
        """

        new_group = metaobject.MetaObject(name=group_name, name_kwargs={'type': 'group'}, node_type='transform')
        new_group.add_attribute('character', self, 'messageSimple')

        return new_group

    def create(self):
        """
        Function that creates character
        This function should be called only when all options are already setup
        """

        if not self.has_attr('main_group'):
            self.set_main_group_name()
        if not self.has_attr('controls_group'):
            self.set_controls_group_name()
        if not self.has_attr('rig_group'):
            self.set_rig_group_name()

        self.controls_group.set_parent(self.main_group)
        self.rig_group.set_parent(self.main_group)
