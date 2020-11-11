#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains abstract implementation for tpRigTask rig components for Maya
"""

from __future__ import print_function, division, absolute_import

import logging

from tpDcc.dccs.maya.meta import metanode

from tpRigToolkit.dccs.maya.metarig.core import mixin

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class RigComponent(metanode.MetaNode, mixin.CoreMixin, mixin.ControlMixin):
    def __init__(self, *args, **kwargs):
        super(RigComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.CoreMixin.__init__(self)
        mixin.ControlMixin.__init__(self)
        self.set_name(kwargs.get('name', 'component'))

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        """
        Creates the rig component
        This function should be extended in custom rig components
        This function only must be called once rig component setup is done
        """

        mixin.CoreMixin.create(self)
        mixin.ControlMixin.create(self)

        self.add_attribute('rig_type', 'component', attr_type='string', lock=True)
        rig_module = self.get_rig_module()
        if rig_module:
            self.controls_group.set_parent(rig_module.controls_group)
            self.setup_group.set_parent(rig_module.setup_group)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_parent(self):
        """
        Returns the parent object of this object (module this component is attached to)
        """

        return self.get_rig_module()

    def connect_to_module(self, module):
        """
        Connects rig component to given RigModule
        :param module: RigModule
        """

        module.add_component(self)

    def get_rig_module(self):
        """
        Returns RigModule linked to this RigComponent
        :return: RigModule
        """

        if not self.has_attr('rig_module'):
            return None

        rig_module = self.get_message('rig_module', as_meta=True)
        if not rig_module:
            return None

        return rig_module[0]

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

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _check_joint(self, jnt):
        """
        Internal function used to check the validity of the given joints
        :param jnt: list
        """

        if not jnt:
            LOGGER.warning('No joint to check')
            return False

        if not jnt or not jnt.node_type() == 'joint':
            LOGGER.warning('Joint node: "{}" is not valid!'.format(jnt))
            return False

        return True

    def _check_locator(self, loc):
        """
        Internal function used to check the validity of the given locators
        :param loc: list
        """

        if not loc:
            LOGGER.warning('No locator to check')
            return False

        if not loc or not loc.node_type() == 'transform':
            LOGGER.warning('Locator node: "{}" is not valid!'.format(loc))
            return False

        return True
