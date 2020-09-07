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
        self.set_transform_group_name()
        self.set_rig_group_name()
        self.set_controls_group_name()
        self.set_setup_group_name()
        self.set_transform_group_name()
        self.set_geometry_group_name()
        self.set_extras_group_name()
        self.set_control_size(1.0)
        self.set_sub_control_size(0.8)
        self.set_sub_visibility(False)

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

        if self.transform_group_name:
            self.add_attribute(
                attr='transform_group', value=self.create_group(self.base_name, self.transform_group_name),
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

        if self.geometry_group_name:
            self.add_attribute(
                attr='geometry_group', value=self.create_group(self.base_name, self.geometry_group_name),
                attr_type='messageSimple'
            )

        if self.extras_group_name:
            self.add_attribute(
                attr='extras_group', value=self.create_group(self.base_name, self.extras_group_name),
                attr_type='messageSimple'
            )

        if hasattr(self, 'transform_group'):
            self.transform_group.set_parent(self.main_group)
            self.rig_group.set_parent(self.transform_group)
            self.controls_group.set_parent(self.rig_group)
            self.setup_group.set_parent(self.rig_group)
        else:
            self.rig_group.set_parent(self.main_group)
            self.controls_group.set_parent(self.rig_group)
            self.setup_group.set_parent(self.rig_group)

        if hasattr(self, 'geometry_group'):
            self.geometry_group.set_parent(self.main_group)
        if hasattr(self, 'extras_group'):
            self.extras_group.set_parent(self.main_group)

        self.main_group.hide_attributes()
        if hasattr(self, 'transform_group'):
            self.transform_group.hide_visibility_attribute()
        self.rig_group.hide_keyable_attributes()
        self.setup_group.hide_keyable_attributes(skip_visibility=True)
        self.geometry_group.hide_keyable_attributes(skip_visibility=True)
        self.extras_group.hide_keyable_attributes(skip_visibility=True)

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

    def set_transform_group_name(self, new_name=''):
        """
        Sets the name of the transform group of the character
        This group is optional and only will be created if the user specifies a name for it
        :param new_name: str
        """

        if not self.has_attr('transform_group_name'):
            self.add_attribute(attr='transform_group_name', value=new_name, lock=True)
        else:
            self.transform_group_name = new_name

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

    def set_geometry_group_name(self, new_name=''):
        """
        Sets the name of the geometry group of the character
        This group is optional and only will be created if the user specifies a name for it
        :param new_name: str
        """

        if not self.has_attr('geometry_group_name'):
            self.add_attribute(attr='geometry_group_name', value=new_name, lock=True)
        else:
            self.geometry_group_name = new_name

    def set_extras_group_name(self, new_name=''):
        """
        Sets the name of the extras group of the character
        This group is optional and only will be created if the user specifies a name for it
        :param new_name: str
        """

        if not self.has_attr('extras_group_name'):
            self.add_attribute(attr='extras_group_name', value=new_name, lock=True)
        else:
            self.extras_group_name = new_name

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

    def get_module_by_class(self, module_class, side=None):
        """
        Returns rig module by its class (if exists)
        :param module_class:
        :return: list(RigModule)
        """

        modules_found = list()

        if self.message_list_get('rig_modules', as_meta=False):
            for module in self.message_list_get('rig_modules'):
                if module.__class__ == module_class:
                    if side:
                        if module.has_attr('side') and module.side == side:
                            modules_found.append(module)
                    else:
                        modules_found.append(module)

        return modules_found

    def append_module(self, rig_module):
        """
        Implements RigTaskCharacter append_module() function
        Adds given module to the MetaData list of modules
        """

        if not self.message_list_get('rig_modules', as_meta=False):
            self.message_list_connect('rig_modules', [rig_module], 'character')
        else:
            self.message_list_append('rig_modules', rig_module, 'character')

        # If we define a naming/controls file in the module character, we override module file path
        if rig_module.has_attr('scalable'):
            metautils.MetaAttributeUtils.connect((self, 'scalable'), (rig_module, 'scalable'), lock=True)
        if rig_module.has_attr('naming_file'):
            metautils.MetaAttributeUtils.connect((self, 'naming_file'), (rig_module, 'naming_file'), lock=True)
        if rig_module.has_attr('naming_rule'):
            metautils.MetaAttributeUtils.connect((self, 'naming_rule'), (rig_module, 'naming_rule'), lock=True)
        if rig_module.has_attr('controls_file'):
            metautils.MetaAttributeUtils.connect((self, 'controls_file'), (rig_module, 'controls_file'), lock=True)
        if rig_module.has_attr('control_size'):
            metautils.MetaAttributeUtils.connect((self, 'control_size'), (rig_module, 'control_size'), lock=True)
        if rig_module.has_attr('sub_visibility'):
            metautils.MetaAttributeUtils.connect((self, 'sub_visibility'), (rig_module, 'sub_visibility'), lock=True)
        if rig_module.has_attr('sub_control_size'):
            metautils.MetaAttributeUtils.connect(
                (self, 'sub_control_size'), (rig_module, 'sub_control_size'), lock=True)
