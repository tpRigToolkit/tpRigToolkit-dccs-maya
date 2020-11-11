#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for metarig modules for Maya
"""

import logging

from tpDcc.dccs.maya.meta import metanode

from tpRigToolkit.dccs.maya.metarig.core import mixin

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class RigModule(metanode.MetaNode, mixin.CoreMixin, mixin.ControlMixin):
    def __init__(self, *args, **kwargs):
        super(RigModule, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.CoreMixin.__init__(self)
        mixin.ControlMixin.__init__(self)
        self.set_name(kwargs.get('name', 'module'))

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self, *args, **kwargs):
        """
        Creates the rig module
        This function should be extended in custom rig modules
        This function only must be called once rig module setup is done
        :param args:
        :param kwargs:
        """

        self.add_attribute('rig_type', 'module', attr_type='string', lock=True)

        mixin.CoreMixin.create(self)
        mixin.ControlMixin.create(self)

        self.controls_group.set_parent(self.character.controls_group)
        self.setup_group.set_parent(self.character.setup_group)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_parent(self):
        """
        Returns the parent object of this object (character this component is attached to)
        """

        return self.get_character()

    def get_character(self):
        """
        Returns the character linked to this module
        :return:
        """

        if not self.has_attr('character'):
            LOGGER.warning('Rig module {} is not connected to a character!'.format(self.base_name))
            return None

        # TODO: Here se should check if the MetaNode is of type RigCharacter

        return self.character

    def set_character(self, character):
        """
        Sets the character of this module
        :param character:
        """

        character.append_module(self)

    def get_character_name(self):
        """
        Returns the name of the character linked to this module
        :return: str
        """

        character = self.get_character()
        if not character:
            return

        return character.base_name

    def add_component(self, component):
        """
        Adds a new rig component to the rig module
        :param component: RigComponent
        """

        if not self.message_list_get('components', as_meta=False):
            self.message_list_connect('components', [component], 'rig_module')
        else:
            self.message_list_append('components', component, 'rig_module')

        cmp_components = component.get_components()
        if cmp_components:
            for component in cmp_components:
                component.message_list_connect('rig_module', self)

        self.connect_core_attributes(component)
        self.connect_naming_attributes(component)
        self.connect_controls_attributes(component)

    def get_components(self, as_meta=True):
        """
        Returns a list of components attached to this rig module
        :param as_meta: bool
        """

        if not self.message_list_get('components', as_meta=False):
            return list()

        return self.message_list_get('components', as_meta=as_meta)

    def get_component_by_class(self, component_class, as_meta=True):
        """
        Returns component of given class
        :param component_class: str
        :param as_meta: bool
        :return: RigComponent
        """

        if not self.has_component(component_class):
            return None

        for component in self.get_components(as_meta=True):
            if component.__class__ == component_class:
                if as_meta:
                    return component
                else:
                    return component.meta_node
        return None

    def get_component_by_name(self, component_name, as_meta=True):
        """
        Returns component by name
        :param component_name: str
        :param as_meta: bool
        :return: RigComponent
        """

        all_components = self.get_components() or list()
        for component in all_components:
            if component.name == component_name:
                if as_meta:
                    return component
                else:
                    return component.meta_node

        return None

    def has_component(self, component_class):
        """
        Implements RigTaskModule has_component() function
        Checks if RigModule has a component of the given class attached to it
        :param component_class:
        :return:
        """

        rig_components = self.get_components()
        for component in rig_components:
            if component.__class__ == component_class:
                return True

        return False
