#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for metarig characters for Maya
"""

from tpDcc.dccs.maya.meta import metanode, metautils

from tpRigToolkit.dccs.maya.metarig.core import mixin


class RigCharacter(metanode.MetaNode, mixin.CoreMixin):
    def __init__(self, *args, **kwargs):
        super(RigCharacter, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.CoreMixin.__init__(self)

        self.set_name(kwargs.get('name', 'character'))
        self.set_main_group_name()
        self.set_rig_group_name()
        self.set_controls_group_name()
        self.set_setup_group_name()
        self.set_control_size(1.0)
        self.set_sub_control_size(0.8)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        """
        Function that creates character
        This function should be called only when all options are already setup
        """

        self.add_attribute('rig_type', 'character', attr_type='string', lock=True)

        self.add_attribute(
            attr='main_group', value=self.create_group(self.base_name, self.main_group_name),
            attr_type='messageSimple'
        )
        self.add_attribute(
            attr='controls_group', value=self.create_group(self.base_name, self.controls_group_name),
            attr_type='messageSimple'
        )
        self.add_attribute(
            attr='rig_group', value=self.create_group(self.base_name, self.rig_group_name),
            attr_type='messageSimple'
        )
        self.add_attribute(
            attr='setup_group', value=self.create_group(self.base_name, self.setup_group_name),
            attr_type='messageSimple'
        )

        self.controls_group.set_parent(self.main_group)
        self.rig_group.set_parent(self.main_group)
        self.setup_group.set_parent(self.main_group)

    def _post_create_group(self, new_group):
        """
        Internal callback function that is called after a rig module group is created
        :param new_group: str
        """

        new_group.add_attribute('character', self, 'messageSimple')

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_parent(self):
        """
        Returns the parent object of this object. A character has no parent.
        """

        return None

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_main_group_name(self, new_name='main'):
        """
        Set the name of the controls group for the character
        If the character has no controls group, it will be created
        :param new_name: str, new name of the group
        """

        if not self.has_attr('main_group_name'):
            self.add_attribute(attr='main_group_name', value=new_name, lock=True)
        else:
            self.main_group_name = new_name

    def set_rig_group_name(self, new_name='rig'):
        """
        Set the name of the rig group for the character
        If the character has no controls group, it will be created
        :param new_name: str, new name of the group
        """

        if not self.has_attr('rig_group_name'):
            self.add_attribute(attr='rig_group_name', value=new_name, lock=True)
        else:
            self.rig_group_name = new_name

    def set_controls_group_name(self, new_name='controls'):
        """
        Set the name of the controls group for the rig module
        If the module has no controls group, it will be created
        :param new_name: str, new name of the group
        """

        if not self.has_attr('controls_group_name'):
            self.add_attribute(attr='controls_group_name', value=new_name, lock=True)
        else:
            self.controls_group_name = new_name

    def set_control_size(self, size):
        """
        Set the size that controls will have during creation
        :param size: float
        """

        if not self.has_attr('control_size'):
            self.add_attribute(attr='control_size', value=size)
        else:
            self.control_size = size

    def set_sub_control_size(self, size):
        """
        Set the size of the sub controls
        :param size: float
        """

        if not self.has_attr('sub_control_size'):
            self.add_attribute(attr='sub_control_size', value=size)
        else:
            self.sub_control_size = size

    def set_sub_visibility(self, flag):
        """
        Sets whether or not sub controls should be visible by default
        :param flag: bool
        """

        if not self.has_attr('sub_visibility'):
            self.add_attribute(attr='sub_visibility', value=flag)
        else:
            self.sub_visibility = flag

    def set_control_side_colors(self, side_colors):
        """
        Defines that maps the control color used for each side
        :param side_colors: dict(str, list)
        """

        if not self.has_attr('control_side_colors'):
            self.add_attribute(attr='control_side_colors', value=side_colors)
        else:
            self.control_side_colors = side_colors

    def set_sub_control_side_colors(self, side_colors):
        """
        Defines that maps the sub control color used for each side
        :param side_colors: dict(str, list)
        """

        if not self.has_attr('sub_control_side_colors'):
            self.add_attribute(attr='sub_control_side_colors', value=side_colors)
        else:
            self.sub_control_side_colors = side_colors

    def set_controls_file(self, file_path):
        """
        Sets the file path used to create the controls of the module
        :param file_path: str
        """

        if not self.has_attr('controls_file'):
            self.add_attribute(attr='controls_file', value=file_path, attr_type='string')
        else:
            self.controls_file = file_path

    def get_module_by_name(self, module_name):
        """
        Returns rig module with given name (if exists)
        :param module_name: str
        :return: RigModule
        """

        if self.message_list_get('rig_modules', as_meta=False):
            for module in self.message_list_get('rig_modules'):
                if module.base_name == module_name:
                    return module

        return None

    def get_module_by_class(self, module_class):
        """
        Returns rig module by its class (if exists)
        :param module_class:
        :return: RigModule
        """

        if self.message_list_get('rig_modules', as_meta=False):
            for module in self.message_list_get('rig_modules'):
                if module.__class__ == module_class:
                    return module

        return None

    def append_module(self, rig_module):
        """
        Implements RigTaskCharacter append_module() function
        Adds given module to the MetaData list of modules
        """

        if not self.message_list_get('rig_modules', as_meta=False):
            self.message_list_connect('rig_modules', [rig_module], 'character')
        else:
            self.message_list_append('rig_modules', rig_module, 'character')

        # # If we define a naming/controls file in the module character, we override module file path
        if rig_module.has_attr('scalable'):
            rig_module.set_scalable(self.scalable)
            metautils.MetaAttributeUtils.connect((self, 'scalable'), (rig_module, 'scalable'), lock=True)
        if rig_module.has_attr('naming_file'):
            rig_module.set_naming_file(self.naming_file)
            metautils.MetaAttributeUtils.connect((self, 'naming_file'), (rig_module, 'naming_file'), lock=True)
        if rig_module.has_attr('naming_rule'):
            rig_module.set_naming_rule(self.naming_rule)
            metautils.MetaAttributeUtils.connect((self, 'naming_rule'), (rig_module, 'naming_rule'), lock=True)
        if rig_module.has_attr('controls_file'):
            rig_module.set_controls_file(self.controls_file)
            metautils.MetaAttributeUtils.connect((self, 'controls_file'), (rig_module, 'controls_file'), lock=True)
        if rig_module.has_attr('control_size'):
            rig_module.set_control_size(self.control_size)
            metautils.MetaAttributeUtils.connect((self, 'control_size'), (rig_module, 'control_size'), lock=True)
        if rig_module.has_attr('sub_visibility'):
            rig_module.set_sub_visibility(self.sub_visibility)
            metautils.MetaAttributeUtils.connect((self, 'sub_visibility'), (rig_module, 'sub_visibility'), lock=True)
        if rig_module.has_attr('sub_control_size'):
            rig_module.set_sub_control_size(self.sub_control_size)
            metautils.MetaAttributeUtils.connect(
                (self, 'sub_control_size'), (rig_module, 'sub_control_size'), lock=True)

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

        self.connect_naming_attributes(component)

        component.set_scalable(self.scalable)
        metautils.MetaAttributeUtils.connect((self, 'scalable'), (component, 'scalable'), lock=True)
        component.set_controls_file(self.controls_file)
        metautils.MetaAttributeUtils.connect((self, 'controls_file'), (component, 'controls_file'), lock=True)
        component.set_control_size(self.control_size)
        metautils.MetaAttributeUtils.connect((self, 'control_size'), (component, 'control_size'), lock=True)
        component.set_sub_control_size(self.sub_control_size)
        metautils.MetaAttributeUtils.connect((self, 'sub_control_size'), (component, 'sub_control_size'), lock=True)
        component.set_sub_visibility(self.sub_visibility)
        metautils.MetaAttributeUtils.connect((self, 'sub_visibility'), (component, 'sub_visibility'), lock=True)

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