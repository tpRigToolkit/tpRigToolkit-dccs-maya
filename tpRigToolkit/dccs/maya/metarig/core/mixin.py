#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains mixin classes to compose functionality in different components/modules
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
from tpDcc.libs.python import python
from tpDcc.dccs.maya.core import attribute as attr_utils, node as node_utils
from tpDcc.dccs.maya.meta import metaobject, metautils

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.core import control


class CoreMixin(object):
    """
    Mixing that defines core functions necessary for rig modules and components
    """

    def __init__(self):

        super(CoreMixin, self).__init__()

        self.set_name('')
        self.set_side('center')
        self.set_scalable(False)
        self.set_scale(1.0)
        self.set_naming_file('')
        self.set_naming_rule('default')

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_root_parent(self):
        """
        Returns the root module (should be a character) of this rig/component
        :return:
        """

        parent = self.get_parent()
        if not parent:
            return True

        while True:
            temp_parent = parent
            parent = parent.get_parent()
            if not parent:
                return temp_parent

    def get_setup_group(self):
        """
        Returns group where setup should be stored
        :return:
        """

        if self.has_attr('setup_group') and tp.Dcc.object_exists(self.setup_group.meta_node):
            return self.setup_group
        else:
            parent = self.get_parent()
            if not parent:
                return

            return parent.setup_group

    def create(self, *args, **kwargs):
        """
        Function that creates the module/component
        """

        if not self.has_attr('setup_group_name'):
            self.set_setup_group_name()

        self.add_attribute(
            attr='setup_group',
            value=self.create_group(self.base_name, self.setup_group_name),
            attr_type='messageSimple'
        )
        self.setup_group.hide()

    def set_name(self, name):
        """
        Sets the base name of the rig module
        :param name: str
        """

        if not self.has_attr('name'):
            self.add_attribute(attr='name', value=name, lock=True)
        else:
            self.name = name

    def set_setup_group_name(self, new_name='setup'):
        """
        Set the name of the setup group for the rig module
        If the module has no setup group, it will be created
        :param new_name: str
        """

        if not self.has_attr('setup_group_name'):
            self.add_attribute(attr='setup_group_name', value=new_name, lock=True)
        else:
            self.setup_group_name = new_name

    def set_side(self, side):
        """
        Sets the side of the rig module
        :param side: str
        """

        if not self.has_attr('side'):
            self.add_attribute(attr='side', value=side, attr_type='string')
        else:
            self.side = side

    def set_scale(self, scale):
        """
        Set the global scale of this rig module
        :param scale:
        """

        if not self.has_attr('scale'):
            self.add_attribute(attr='scale', value=scale)
        else:
            self.scale = scale

    def set_scalable(self, flag):
        """
        Sets whether or not this character is scalable
        :param flag: bool
        """

        if not self.has_attr('scalable'):
            self.add_attribute(attr='scalable', value=flag)
        else:
            self.scalable = flag

    def set_naming_file(self, file_path):
        """
        Sets the file path used to manage the naming of the file
        :param file_path: str
        """

        if not self.has_attr('naming_file'):
            self.add_attribute(attr='naming_file', value=file_path, attr_type='string')
        else:
            self.naming_file = file_path

    def set_naming_rule(self, naming_rule):
        """
        Sets the naming rule used by this rig module
        :param naming_rule: str
        """

        if not self.has_attr('naming_rule'):
            self.add_attribute(attr='naming_rule', value=naming_rule, attr_type='string')
        else:
            self.naming_rule = naming_rule

    def create_group(self, *args, **kwargs):
        """
        Function that creates new groups for the character
        """

        attr_name = kwargs.pop('attr_name', None)
        kwargs['node_type'] = 'group'
        new_group = metaobject.MetaObject(name=self._get_name(*args, **kwargs), node_type='transform')
        if attr_name:
            self.add_attribute(attr=attr_name, value=new_group, attr_type='messageSimple')
        self._post_create_group(new_group)

        return new_group

    def delete_setup(self):
        """
        Deletes all groups and nodes related with rig module setup
        """

        if not self.has_attr('setup_group'):
            tpRigToolkit.loger.warning('Setup group does not exists!')
            return

        if self.setup_group.is_valid_mobject():
            if node_utils.is_empty(self.setup_group.meta_node, no_user_attributes=False, no_connections=False):
                self.setup_group.delete()
                if self.has_attr('setup_group'):
                    self.delete_attribute('setup_group')
                return

            if node_utils.is_empty(self.setup_group.meta_node):
                tpRigToolkit.logger.warning('Setup Group is not empty. Skipping deletion ...')

        if not self.setup_group.is_valid():
            tpRigToolkit.logger.warning('Setup Group does not exists! Skipping deletion ...')

    def delete_control(self):
        """
        Deletes all groups and nodes related with rig module setup
        """

        if not self.has_attr('controls_group'):
            tpRigToolkit.loger.warning('Controls group does not exists!')
            return

        if self.controls_group.is_valid_mobject():
            if node_utils.is_empty(self.controls_group.meta_node, no_user_attributes=False, no_connections=False):
                self.controls_group.delete()
                if self.has_attr('controls_group'):
                    self.delete_attribute('controls_group')
                return

            if node_utils.is_empty(self.controls_group.meta_node):
                tpRigToolkit.logger.warning('controls_group Group is not empty. Skipping deletion ...')

        if not self.controls_group.is_valid():
            tpRigToolkit.logger.warning('Controls Group does not exists! Skipping deletion ...')

    def connect_core_attributes(self, component):
        """
        Function that connects core attributes of this modules/component to the given one
        :param component: RigComponent or RigModule
        """

        component.set_side(self.side)
        metautils.MetaAttributeUtils.connect((self, 'side'), (component, 'side'), lock=True)

    def connect_naming_attributes(self, component):
        """
        Function that connects all the control related attributes of this module/component to the given one
        :param component: RigComponent or RigModule
        :return:
        """

        component.set_naming_file(self.naming_file)
        metautils.MetaAttributeUtils.connect((self, 'naming_file'), (component, 'naming_file'), lock=True)
        component.set_naming_rule(self.naming_rule)
        metautils.MetaAttributeUtils.connect((self, 'naming_rule'), (component, 'naming_rule'), lock=True)

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _get_name(self, *args, **kwargs):
        """
        Internal function that returns a proper name for elements of the rig module
        :param name: str
        :param node_type: str
        :return: str
        """

        naming_file = self.naming_file if self.has_attr('naming_file') else None
        naming_rule = self.naming_rule if self.has_attr('naming_rule') else None

        return tpRigToolkit.NamesMgr().solve_name(
            side=self.side, naming_file=naming_file, rule_name=naming_rule, *args, **kwargs)

    def _prepare_attribute(self, attribute_name):
        """
        Internal function that makes sure that given attribute is ready to be set
        If the attribute is connected, the connection is removed
        """
        metautils.MetaAttributeUtils.break_connection((self, attribute_name))

    def _post_create_group(self, new_group):
        """
        Internal callback function that is called after a rig module group is created
        :param new_group: str
        """

        new_group.add_attribute(attr='rig_module', value=self, attr_type='messageSimple')

    def _create_setup_group(self, name):
        """
        Internal function that creates a new group inside the setup group
        :param name: str
        """

        group = self.create_group('setup', name)
        if self.setup_group:
            group.set_parent(self.setup_group)

        return group


class ControlMixin(object):

    def __init__(self):
        # We do not set a default control color. If we do it, we force the control color to be this one
        # and if would ignore the control data color.
        # self.set_control_color([1.0, 1.0, 1.0])

        super(ControlMixin, self).__init__()

        self.set_create_sub_controls(False)
        self.set_hide_sub_controls_translate(False)
        self.set_control_size(1.0)
        self.set_sub_control_size(0.8)
        self.set_control_shape('circle')
        self.set_sub_control_shape('circle')
        self.set_control_color([1.0, 1.0, 1.0])
        self.set_control_data({})
        self.set_control_offset_axis('')
        self.set_sub_visibility(False)
        self.set_use_side_color(True)
        self.set_controls_group_name('controls')
        self.set_controls_file('')

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def create(self):
        """
        Function that creates the component
        """

        if not self.has_attr('controls_group_name'):
            self.set_controls_group_name()

        self.add_attribute(
            attr='controls_group',
            value=self.create_group(self.base_name, self.controls_group_name),
            attr_type='messageSimple'
        )

    def get_controls(self, as_meta=True):
        """
        Returns controls of the rig module
        :return: list
        """

        return self.message_list_get('controls', as_meta=as_meta)

    def get_main_control(self, as_meta=True):
        """
        Returns the main control of the rig
        First we check if main_control attribute exist. If not the first control in the list of controls.
        :return:
        """

        if self.has_attr('main_control') and self.main_control:
            return self.main_control

        all_controls = self.get_controls(as_meta=as_meta)
        if not all_controls:
            return None

        return all_controls[0]

    def get_last_control(self, check_sub_controls=True, as_meta=True):
        """
        Returns last control available in the module/component
        If check_sub_controls is True, te last control would be the last sub control
        :param as_meta: bool
        :return:
        """

        if check_sub_controls:
            sub_controls = self.get_sub_controls(as_meta=as_meta)
            if sub_controls:
                return sub_controls[-1]

        all_controls = self.get_controls(as_meta=as_meta)
        if not all_controls:
            return None

        return all_controls[-1]

    def get_sub_controls(self, as_meta=True):
        """
        Returns sub controls of the rig module
        :param as_meta: bool
        :return: list
        """

        sub_ctrls = list()
        for ctrl in self.get_controls():
            subs = ctrl.get_sub_controls(as_meta=as_meta)
            sub_ctrls.extend(subs)

        return sub_ctrls

    def get_controls_group(self):
        """
        Returns group where controls should be stored
        :return:
        """

        if self.has_attr('controls_group') and tp.Dcc.object_exists(self.controls_group.meta_node):
            return self.controls_group
        else:
            parent = self.get_parent()
            if not parent:
                return

            return parent.controls_group

    def get_controls_size(self):
        """
        Returns the size of the module/component controls taking into account the total scale of their connections
        :return:
        """

        control_size = self.control_size
        parent = self.get_parent()
        while True:
            if not parent:
                break
            if parent.has_attr('scale'):
                control_size *= parent.scale
            parent = parent.get_parent()

        return control_size

    def get_sub_controls_size(self):
        """
        Returns the size of the module/component sub controls taking into account the total scale of their connections
        :return:
        """

        sub_control_size = self.sub_control_size
        parent = self.get_parent()
        while True:
            if not parent:
                break
            if parent.has_attr('scale'):
                sub_control_size *= parent.scale
            parent = parent.get_parent()

        return sub_control_size

    def set_controls_file(self, file_path):
        """
        Sets the file path used to create the controls of the module
        :param file_path: str
        """

        if not self.has_attr('controls_file'):
            self.add_attribute(attr='controls_file', value=file_path, attr_type='string')
        else:
            self._prepare_attribute('controls_file')
            self.controls_file = file_path

    def set_create_sub_controls(self, flag):
        """
        Sets sub controls should be created or not
        :param flag: flag
        """

        if not self.has_attr('create_sub_controls'):
            self.add_attribute(attr='create_sub_controls', value=flag)
        else:
            self._prepare_attribute('create_sub_controls')
            self.create_sub_controls = flag

    def set_controls_group_name(self, new_name='controls'):
        """
        Set the name of the controls group for the rig module
        If the module has no controls group, it will be created
        :param new_name: str, new name of the group
        """

        if not self.has_attr('controls_group_name'):
            self.add_attribute(attr='controls_group_name', value=new_name, lock=True)
        else:
            self._prepare_attribute('controls_group_name')
            self.controls_group_name = new_name

    def set_control_size(self, size):
        """
        Set the size that controls will have during creation
        :param size: float
        """

        if not self.has_attr('control_size'):
            self.add_attribute(attr='control_size', value=size)
        else:
            self._prepare_attribute('control_size')
            self.control_size = size

    def set_sub_control_size(self, size):
        """
        Set the size of the sub controls
        :param size: float
        """

        if not self.has_attr('sub_control_size'):
            self.add_attribute(attr='sub_control_size', value=size)
        else:
            self._prepare_attribute('sub_control_size')
            self.sub_control_size = size

    def set_control_data(self, control_dict):
        """
        Sets the control data used by this rig module
        :param control_dict: dict
        """

        if not self.has_attr('control_data'):
            self.add_attribute(attr='control_data', value=control_dict)
        else:
            self._prepare_attribute('control_data')
            self.control_data = control_dict

    def set_hide_sub_controls_translate(self, flag):
        """
        Sets whether translate channels on sub controls need to be hide or not
        :param flag: bool
        """

        if not self.has_attr('hide_sub_controls_translate'):
            self.add_attribute(attr='hide_sub_controls_translate', value=flag)
        else:
            self._prepare_attribute('hide_sub_controls_translate')
            self.hide_sub_controls_translate = flag

    def set_sub_visibility(self, flag):
        """
        Set the sub visibility of the sub controls of the rig module
        :param flag: bool
        """

        if not self.has_attr('sub_visibility'):
            self.add_attribute(attr='sub_visibility', value=flag)
        else:
            self._prepare_attribute('sub_visibility')
            self.sub_visibility = flag

    def set_control_shape(self, shape_name):
        """
        Sets the control shape
        :param shape_name: str
        """

        if not self.has_attr('control_shape'):
            self.add_attribute(attr='control_shape', value=shape_name, attr_type='string')
        else:
            self._prepare_attribute('control_shape')
            self.control_shape = shape_name

    def set_sub_control_shape(self, shape_name):
        """
        Sets the control shape
        :param shape_name: str
        """

        if not self.has_attr('sub_control_shape'):
            self.add_attribute(attr='sub_control_shape', value=shape_name, attr_type='string')
        else:
            self._prepare_attribute('sub_control_shape')
            self.sub_control_shape = shape_name

    def set_control_offset_axis(self, axis_letter):
        """
        Sets the axis that the control curves will offset to. This happens by rotation the control in 90
        degrees on the given axis.
        This is good for lining up the control CVs to a different axis than its default
        :param axis_letter: str, letter of the axis to offset the control CVs around ('x', 'y', 'z')
        """

        axis_letter = axis_letter or ''
        if not self.has_attr('control_offset_axis'):
            self.add_attribute('control_offset_axis', value=axis_letter.lower(), attr_type='string')
        else:
            self._prepare_attribute('control_offset_axis')
            self.control_offset_axis = axis_letter.lower()

    def set_control_color(self, color):
        """
        Sets the control color of the shape
        :param color: list(float, float, float)
        :return:
        """

        if not self.has_attr('control_color'):
            self.add_attribute('control_color', value=color, attr_type='double3')
        else:
            self._prepare_attribute('control_color')
            self.control_color = color

    def set_use_side_color(self, flag):
        """
        Sets whether control color should be defined by the side where control is placed
        :param flag: bool
        """

        if not self.has_attr('use_side_color'):
            self.add_attribute('use_side_color', value=flag, attr_type='bool')
        else:
            self._prepare_attribute('use_side_color')
            self.use_side_color = flag

    def create_control(self, name=None, sub=False, connect_to_module=True, *args, **kwargs):
        """
        Creates a new RigControl attached to this rig module
        :param name: str, name of the control
        :param sub: bool, Whether the control is a sub control or not
        :param connect_to_module: bool, If True, new control will be connected to the RigModule
        :return:
        """

        root_module = self.get_root_parent()

        control_size = self.get_sub_controls_size() if sub else self.get_controls_size()

        # Sub control never can be bigger that main control, if that's the case we reduce the sub control size to fit
        # inside the main control
        if sub and control_size >= self.get_controls_size():
            control_size = self.get_controls_size()
            control_size = control_size * 0.9

        # TODO: Sub controls should define its own data. At this moment if control data is defined, the same is
        # used for both controls and sub controls
        control_type = self.sub_control_shape if sub else self.control_shape
        control_data = kwargs.pop(
            'control_data',
            self.control_data if self.has_attr('control_data') and self.control_data else dict()) or dict()
        if 'control_name' in control_data:
            control_type = control_data['control_name']

        node_base_name = tp.Dcc.node_short_name(self.base_name)
        node_type = 'subControl' if sub else 'control'
        new_ctrl = control.RigControl(name=self._get_name(node_base_name, name, node_type=node_type, *args, **kwargs))
        new_ctrl.set_name(name)
        new_ctrl.set_control_side(self.side)
        new_ctrl.set_control_size(control_size)

        # For controls, we use the following color
        # 1) If use side color is on, we use that color
        # 2) If control data defines a color we use that color
        # 3) If control defines a color we use that color

        control_color = self.control_color if self.has_attr('control_color') else None
        if control_data and 'color' in control_data and control_data['color']:
            control_color = control_data['color']
        if self.use_side_color:
            if sub and root_module.has_attr('sub_control_side_colors'):
                control_color = root_module.sub_control_side_colors.get(self.side, None)
            elif root_module.has_attr('control_side_colors'):
                control_color = root_module.control_side_colors.get(self.side, None)
        if control_color:
            new_ctrl.set_control_color(control_color)
        new_ctrl.set_control_data(control_data)
        new_ctrl.set_control_type(control_type)

        # We connect the control to the rig module so we can access to the rig module info such as for example
        # to retrieve the naming file or the controls file
        new_ctrl.add_attribute(attr='rig_module', value=self, attr_type='messageSimple')

        new_ctrl.create()

        # If we are creating multiple sub controls we scale accordingly
        # TODO: This is not a good idea. If we create more than 10 sub controls (altough usually we only need 3)
        # TODO: the final scale will be SUPER small. This should be done in a place where we know the total amount
        # TODO: of sub controls we want to create.
        scale_to_apply = None
        if sub and 'sub_id' in kwargs:
            i = kwargs['sub_id']
            if i > 0:
                scale_factor = 0.1 * i
                scale_to_apply = 1.0 - scale_factor
        if scale_to_apply:
            new_ctrl.scale_control_shapes(scale_to_apply)

        if connect_to_module:
            if not sub:
                self._add_control(new_ctrl)
            else:
                self._add_sub_control(new_ctrl)

        if sub:
            # If we pass a control, the visibility of this control will be handle by the given control
            visibility_parent_control = kwargs.get('visibility_parent_control', None)
            if visibility_parent_control:
                self._connect_sub_visibility(visibility_parent_control, new_ctrl)

        new_ctrl.set_parent(self.controls_group)

        # Control attribute value will handle the drawingOverrides color of the shape
        shapes = new_ctrl.get_shapes()
        for shp in shapes:
            tp.Dcc.connect_attribute(
                new_ctrl.meta_node, 'color.colorX', shp, 'drawOverride.overrideColorRGB.overrideColorR')
            tp.Dcc.connect_attribute(
                new_ctrl.meta_node, 'color.colorY', shp, 'drawOverride.overrideColorRGB.overrideColorG')
            tp.Dcc.connect_attribute(
                new_ctrl.meta_node, 'color.colorZ', shp, 'drawOverride.overrideColorRGB.overrideColorB')

        if not self.scalable:
            new_ctrl.hide_scale_attributes()

        new_ctrl.hide_visibility_attribute()

        return new_ctrl

    def connect_controls_attributes(self, component):
        """
        Function that connects all the control related attributes of this module/component to the given one
        :param component: RigComponent or RigModule
        :return:
        """

        if component.has_attr('controls_file') and self.controls_file:
            component.set_controls_file(self.controls_file)
            metautils.MetaAttributeUtils.connect((self, 'controls_file'), (component, 'controls_file'), lock=True)
        if component.has_attr('control_size') and self.control_size:
            component.set_control_size(self.control_size)
            metautils.MetaAttributeUtils.connect((self, 'control_size'), (component, 'control_size'), lock=True)
        if component.has_attr('sub_control_size') and self.sub_control_size:
            component.set_sub_control_size(self.sub_control_size)
            metautils.MetaAttributeUtils.connect((self, 'sub_control_size'), (component, 'sub_control_size'), lock=True)
        if component.has_attr('control_color') and self.control_color:
            component.set_control_color(self.control_color)
            metautils.MetaAttributeUtils.connect((self, 'control_color'), (component, 'control_color'), lock=True)
        if component.has_attr('control_data') and self.control_data:
            component.set_control_data(self.control_data)
            metautils.MetaAttributeUtils.connect((self, 'control_data'), (component, 'control_data'), lock=True)
        if component.has_attr('control_shape') and self.control_shape:
            component.set_control_shape(self.control_shape)
            metautils.MetaAttributeUtils.connect((self, 'control_shape'), (component, 'control_shape'), lock=True)
        if component.has_attr('sub_control_shape') and self.sub_control_shape:
            component.set_sub_control_shape(self.sub_control_shape)
            metautils.MetaAttributeUtils.connect(
                (self, 'sub_control_shape'), (component, 'sub_control_shape'), lock=True)
        if component.has_attr('sub_visibility') and self.sub_visibility:
            component.set_sub_visibility(self.sub_visibility)
            metautils.MetaAttributeUtils.connect((self, 'sub_visibility'), (component, 'sub_visibility'), lock=True)
        if component.has_attr('use_side_color') and self.use_side_color:
            component.set_use_side_color(self.use_side_color)
            metautils.MetaAttributeUtils.connect((self, 'use_side_color'), (component, 'use_side_color'), lock=True)
        if component.has_attr('control_offset_axis') and self.control_offset_axis:
            component.set_control_offset_axis(self.control_offset_axis)
            metautils.MetaAttributeUtils.connect(
                (self, 'control_offset_axis'), (component, 'control_offset_axis'), lock=True)
        if component.has_attr('create_sub_controls') and self.create_sub_controls:
            component.set_create_sub_controls(self.create_sub_controls)
            metautils.MetaAttributeUtils.connect(
                (self, 'create_sub_controls'), (component, 'create_sub_controls'), lock=True)
        if component.has_attr('hide_sub_controls_translate') and self.hide_sub_controls_translate:
            component.set_hide_sub_controls_translate(self.hide_sub_controls_translate)
            metautils.MetaAttributeUtils.connect(
                (self, 'hide_sub_controls_translate'), (component, 'hide_sub_controls_translate'), lock=True)

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _add_control(self, control):
        """
        Adds a new control to the list of controls
        :param control: RigControl
        """

        if not self.message_list_get('controls', as_meta=False):
            self.message_list_connect('controls', [control])
        else:
            self.message_list_append('controls', control)

    def _add_sub_control(self, control):
        """
        Adds a new sub control to the list of sub controls
        :param control: RigControl
        """

        if not self.message_list_get('sub_controls', as_meta=False):
            self.message_list_connect('sub_controls', [control])
        else:
            self.message_list_append('sub_controls', control)

    def _connect_sub_visibility(self, ctrl, sub_ctrl):
        """
        Connect sub control shapes visibility into given attribute
        :param ctrl:  RigControl we want to connect visibility into
        :param sub_ctrl: RigControl, sub control
        """

        # Visibility manager attribute will be created if does not already exists
        main_vis_attr = '{}.subVisibility'.format(ctrl.meta_node)

        shapes = sub_ctrl.get_shapes()
        for shp in shapes:
            attr_utils.connect_visibility(main_vis_attr, shp, self.sub_visibility)


class JointMixin(object):
    def __init__(self):
        super(JointMixin, self).__init__()

        # ==============================================================================================
        # BASE
        # ==============================================================================================

    def has_joints(self):
        """
        Returns whether the RigJoint module has added joints or not
        :return: bool
        """

        if not self.message_list_get('joints', as_meta=False):
            return False

        return True

    def get_joints(self, as_meta=True):
        """
        Returns list of joints of the module
        :return: list<MetaObject>
        """

        return self.message_list_get('joints', as_meta=as_meta)

    def add_joints(self, joints, clean=False):
        """
        Appends new joints to the module
        :param joints: list<variant>
        """

        if not joints:
            return

        joints = python.force_list(joints)

        valid_joints = list()
        for jnt in joints:
            valid_jnt = self._check_joint(jnt)
            if valid_jnt:
                valid_joints.append(jnt)

        if len(valid_joints) <= 0:
            return

        if not self.message_list_get('joints', as_meta=False):
            self.message_list_connect('joints', valid_joints)
        else:
            if clean:
                self.message_list_purge('joints')
            for jnt in valid_joints:
                self.message_list_append('joints', jnt)

        return valid_joints

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _check_joint(self, jnt):
        """
        Internal function used to check the validity of the given joints
        :param jnt: list
        """

        if not jnt:
            tpRigToolkit.logger.warning('No joint to check')
            return False

        if not jnt or not jnt.node_type() == 'joint':
            tpRigToolkit.logger.warning('Joint: "{}" is not valid!'.format(jnt))
            return False

        return True

