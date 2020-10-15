#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains control metarig implementations for Maya
"""

from __future__ import print_function, division, absolute_import

import os

import tpDcc as tp
from tpDcc.libs.curves.core import curveslib

import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import transform, attribute, shape
from tpDcc.dccs.maya.meta import metaobject, metautils

import tpRigToolkit


class RigControl(metaobject.MetaObject, object):
    def __init__(self, node=None, name=None, *args, **kwargs):
        super(RigControl, self).__init__(node=node, name=name, *args, **kwargs)

        if self.cached:
            return

        self.set_control_type('circle')
        self.set_control_size(1.0)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def __verify__(self, *args, **kwargs):
        return True

    def set_parent(self, target=False, parent_top=True):
        """
        Overrides set parent to parent proper root/auto nodes if necessary
        :param target: str, parent transform node name
        :param parent_top: bool, Whether to parent ctrl transform or take into account also root/auto groups
        :return:
        """

        node_to_parent = self.meta_node

        if parent_top:
            if self.has_attr('mirror_group') and self.mirror_group.is_valid_mobject():
                node_to_parent = self.mirror_group.meta_node
            elif self.has_attr('root_group') and self.root_group.is_valid_mobject():
                node_to_parent = self.root_group.meta_node
            else:
                if self.has_attr('auto_group') and self.auto_group.is_valid_mobject():
                    node_to_parent = self.auto_group.meta_node

        return metautils.MetaTransformUtils.set_parent(node_to_parent, target)

    def rename(self, name, rename_child_links=False):
        """
        Override to also rename root/auto groups if necessary
        :param name: str
        :param rename_child_links: bool
        """

        super(RigControl, self).rename(name, rename_child_links)

        if self.has_attr('auto_group') and self.auto_group.is_valid_mobject():
            self.auto_group.rename(name + '_auto')
        if self.has_attr('root_group') and self.root_group.is_valid_mobject():
            self.root_group.rename(name + '_root')

    def snap(self, source, snap_pivot=False):
        """
        Override to also move root/auto groups if necessary
        :param source: str
        :param snap_pivot: bool
        :return:
        """

        target = self._get_top_group()
        source = source.meta_node if hasattr(source, 'meta_node') else source

        transform.snap(target.meta_node, source, snap_pivot)

    def match_translation(self, source):
        """
        Override to also move root/auto groups if necessary
        Matches transforms translation into given target translation
        :param source:
        """

        target = self._get_top_group()
        source = source.meta_node if hasattr(source, 'meta_node') else source

        maya.cmds.delete(maya.cmds.pointConstraint(source, target.meta_node))
        # transform.match_translation(target.meta_node, source)

        if tp.Dcc.name_is_right(self.side) and self.has_attr('mirror_group'):
            # tp.Dcc.set_attribute_value(target.meta_node, 'scaleZ', 1.0)
            tp.Dcc.set_attribute_value(self.meta_node, 'rotateY', 0.0)

    def match_rotation(self, source):
        """
        Override to also rotate root/auto groups if necessary
        Matches transforms rotation into given target rotation
        :param source:
        """

        target = self._get_top_group()
        source = source.meta_node if hasattr(source, 'meta_node') else source

        maya.cmds.delete(maya.cmds.orientConstraint(source, target.meta_node))
        # transform.match_rotation(target.meta_node, source)

        if tp.Dcc.name_is_right(self.side) and self.has_attr('mirror_group'):
            # tp.Dcc.set_attribute_value(target.meta_node, 'scaleZ', 1.0)
            tp.Dcc.set_attribute_value(self.meta_node, 'rotateY', 0.0)

    def match_translation_and_rotation(self, source):
        """
        Override to also move root/auto groups if necessary
        Matches transforms translation and rotation into given target translation and rotation
        :param source:
        """

        target = self._get_top_group()
        source = source.meta_node if hasattr(source, 'meta_node') else source

        maya.cmds.delete(maya.cmds.pointConstraint(source, target.meta_node))
        maya.cmds.delete(maya.cmds.orientConstraint(source, target.meta_node))
        # transform.match_translation_rotation(target.meta_node, source)

        if tp.Dcc.name_is_right(self.side) and self.has_attr('mirror_group'):
            # tp.Dcc.set_attribute_value(target.meta_node, 'scaleZ', 1.0)
            tp.Dcc.set_attribute_value(self.meta_node, 'rotateY', 0.0)

    def match_scale(self, source):
        """
        Override to also move root/auto groups if necessary
        Matches transforms scale into given target scale
        :param source:
        """

        target = self._get_top_group()
        source = source.meta_node if hasattr(source, 'meta_node') else source

        transform.match_scale(target.meta_node, source)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def get_rig_module(self):
        """
        Returns the rig module this controls is linked to
        :return: RigModule or None
        """

        if not self.has_attr('rig_module'):
            tpRigToolkit.logger.warning('Control {} is not connected to a rig module!'.format(self.base_name))
            return None

        rig_module = self.get_message('rig_module', as_meta=True)
        if not rig_module:
            return None

        return rig_module[0]

    def set_name(self, name):
        """
        Sets the base namne of the rig control
        :param name: str
        """

        if not self.has_attr('name'):
            self.add_attribute('name', name, attr_type='string')
        else:
            self.name = name

    def set_control_side(self, control_side):
        """
        Sets the side of the control
        :param control_side: str
        :return:
        """

        if not self.has_attr('side'):
            self.add_attribute('side', control_side, attr_type='string')
        else:
            self.side = control_side

    def set_control_type(self, control_type):
        """
        Sets the control that the control needs to use
        Control type is a name of a valid controllib.ControlManager control
        :param control_type: str
        """

        if not self.has_attr('type'):
            self.add_attribute('type', control_type, attr_type='string')
        else:
            self.type = control_type

    def set_control_size(self, control_size):
        """
        Sets the control that the control needs to use
        Control type is a name of a valid controllib.ControlManager control
        :param control_type: str
        """

        if not self.has_attr('size'):
            self.add_attribute('size', control_size, attr_type='float', hidden=True)
        else:
            self.size = control_size

    def set_control_color(self, color):
        """
        Sets the control color of the shape
        :param color: list(float, float, float)
        :return:
        """

        if not self.has_attr('color'):
            self.add_attribute('color', value=color, attr_type='double3', hidden=True)
        else:
            self.color = color

        # Maya does not refresh properly shape color when connecting directly to them
        # We must update overrideEnabled attribute to force the refresh
        if tp.Dcc.object_exists(self.meta_node):
            for shape in self.get_shapes():
                tp.Dcc.set_attribute_value(shape, 'overrideEnabled', False)
                tp.Dcc.set_attribute_value(shape, 'overrideEnabled', True)

    def set_control_data(self, control_dict=None):
        """
        Sets the control data used by this control
        :param control_dict: dict
        """

        control_dict = control_dict if control_dict is not None else dict()
        if not self.has_attr('control_data'):
            self.add_attribute('control_data', control_dict, attr_type='string')
        else:
            self.control_data = control_dict

    def set_controls_path(self, file_path):
        """
        Sets the controls file path used to create this control
        :param file_path: str
        """

        if not self.has_attr('controls_path'):
            self.add_attribute('controls_path', file_path, attr_type='string')
        else:
            self.controls_path = file_path

    def create_root(self, group_name='root', *args, **kwargs):
        """
        Create the root_transform of the control rig to the given node
        :param group_name: str, name of node to be the new root of the control
        """

        ignore_warnings = kwargs.get('ignore_warnings', False)

        if self.has_attr('root_group') and maya.cmds.objExists(self.root_group.meta_node):
            if not ignore_warnings:
                tpRigToolkit.logger.warning('Impossible to create root group because it already exists!')
            return self.root_group

        base_name = self.name if self.has_attr('name') and self.name else self.base_name

        naming_file, naming_rule = self._get_naming_data()

        parsed_name = tpRigToolkit.NamesMgr().parse_name(self.base_name, naming_file=naming_file, rule_name=naming_rule)
        if parsed_name:
            # TODO: Allow to put the root in the first key (prefix) or in the last one (suffix)
            parsed_name[list(parsed_name.keys())[-1]] = group_name
            kwargs.update(parsed_name)
            new_group = self._create_group(force_suffix=False, *args, **kwargs)
        else:
            new_group = self._create_group(base_name, group_name, *args, **kwargs)

        # MIRROR BEHAVIOUR
        # TODO: This should be optional
        mirror_group = None
        if tp.Dcc.name_is_right(self.side):
            if parsed_name:
                # TODO: Allow to put the root in the first key (prefix) or in the last one (suffix)
                parsed_name[list(parsed_name.keys())[-1]] = 'mirror'
                kwargs.update(parsed_name)
                mirror_group = self._create_group(force_suffix=False, *args, **kwargs)
            else:
                mirror_group = self._create_group(base_name, group_name, *args, **kwargs)
            tp.Dcc.set_attribute_value(mirror_group.meta_node, 'scaleX', -1)
            mirror_group.set_parent(self.get_parent())
            self.add_attribute(attr='mirror_group', value=mirror_group, attr_type='messageSimple')

        self.add_attribute(attr='root_group', value=new_group, attr_type='messageSimple')
        if not self.has_attr('auto_group'):
            if mirror_group:
                new_group.set_parent(mirror_group)
                self.set_parent(new_group, parent_top=False)
                for xform in 'trs':
                    for axis in 'xyz':
                        attr_value = 1.0 if xform == 's' else 0.0
                        tp.Dcc.set_attribute_value(new_group.meta_node, '{}{}'.format(xform, axis), attr_value)
            else:
                new_group.set_parent(self.get_parent())
                self.set_parent(new_group, parent_top=False)
        else:
            if mirror_group:
                new_group.set_parent(mirror_group)
            else:
                new_group.set_parent(self.auto_group.get_parent())
            self.auto_group.set_parent(new_group)

        if not self.has_attr('root_group'):
            self.add_attribute(attr='root_group', value=new_group, attr_type='messageSimple')
        else:
            self.root_group = new_group

        return new_group

    def create_auto(self, group_name='auto', *args, **kwargs):
        """
        Set the auto of the control rig to the given node
        :param group_name: str, name of node to be the new root of the control
        """

        if self.has_attr('auto_group') and maya.cmds.objExists(self.auto_group.meta_node):
            tpRigToolkit.logger.warning('Impossible to create auto group because it already exists!')
            return self.auto_group

        base_name = self.name if self.has_attr('name') and self.name else self.base_name

        naming_file, naming_rule = self._get_naming_data()

        parsed_name = tpRigToolkit.NamesMgr().parse_name(self.base_name, naming_file=naming_file, rule_name=naming_rule)
        if parsed_name:
            # TODO: Allow to put the root in the first key (prefix) or in the last one (suffix)
            parsed_name[list(parsed_name.keys())[-1]] = group_name
            kwargs.update(parsed_name)
            new_group = self._create_group(force_suffix=False, *args, **kwargs)
        else:
            new_group = self._create_group(base_name, group_name, *args, **kwargs)

        self.add_attribute(attr='auto_group', value=new_group, attr_type='messageSimple')
        new_group.set_parent(self.get_parent())
        self.set_parent(new_group, parent_top=False)
        if self.has_attr('root_group'):
            if not new_group.get_parent(as_meta=True) == self.root_group:
                new_group.set_parent(self.root_group)
            for xform in 'trs':
                for axis in 'xyz':
                    attr_value = 1.0 if xform == 's' else 0.0
                    tp.Dcc.set_attribute_value(new_group.meta_node, '{}{}'.format(xform, axis), attr_value)

        if not self.has_attr('auto_group'):
            self.add_attribute(attr='auto_group', value=new_group, attr_type='messageSimple')
        else:
            self.auto_group = new_group

        return new_group

    def remove_root(self):
        """
        Deletes the root group of the rig control and updates its hierarchy
        """

        if self.has_attr('root_group') and self.auto_group.is_valid_mobject():
            root_parent = self.root_group.get_parent()
            if self.has_attr('auto_group') and self.auto_group.is_valid_mobject():
                self.auto_group.set_parent(root_parent)
            else:
                self.set_parent(root_parent, parent_top=False)
            self.root_group.delete()

    def remove_auto(self):
        """
        Deletes the auto group of the rig control and updates its hierarchy
        """

        if self.has_attr('auto_group') and self.auto_group.is_valid_mobject():
            auto_parent = self.auto_group.get_parent()
            self.set_parent(auto_parent, parent_top=False)
            self.auto_group.delete()

    def top(self):
        """
        Returns the high node in the root-auto-control hierarchy
        :return:
        """

        if self.has_attr('mirror_group') and self.mirror_group.is_valid_mobject():
            return self.mirror_group
        elif self.has_attr('root_group') and self.root_group.is_valid_mobject():
            return self.root_group
        else:
            if self.has_attr('auto_group') and self.auto_group.is_valid_mobject():
                return self.auto_group

        return self

    def translate_control_shapes(self, x, y, z):
        """
        Translates the shape curve CVs in object space
        :param x: float
        :param y: float
        :param z: float
        """

        comps = self.get_shapes_components()
        if comps:
            maya.cmds.move(x, y, z, comps, relative=True, os=True)

    def rotate_control_shapes(self, x, y, z):
        """
        Rotates the shape curve in object space
        :param x: float
        :param y: float
        :param z: float
        """

        comps = self._get_components()
        if comps:
            maya.cmds.rotate(x, y, z, comps, relative=True)

    def scale_control_shapes(self, scale, use_pivot=True, relative=True):
        """
        Scales the shape curve CVs relative to the current scale
        :param scale: variant, float || list<float, float, float>
        :param use_pivot: bool
        :param relative: bool
        """

        comps = self.get_shapes_components()
        if use_pivot:
            pivot = maya.cmds.xform(self.meta_node, query=True, rp=True, ws=True)
        else:
            shapes = self.get_shapes(intermediates=False)
            comps = shape.get_components_from_shapes(shapes)
            bounding_box = transform.BoundingBox(comps)
            pivot = bounding_box.get_center()

        if comps:
            if type(scale) in [list, tuple]:
                if relative:
                    maya.cmds.scale(scale[0], scale[1], scale[2], comps, pivot=pivot, r=True)
                else:
                    maya.cmds.scale(scale[0], scale[1], scale[2], comps, pivot=pivot, a=True)
            else:
                if relative:
                    maya.cmds.scale(scale, scale, scale, comps, pivot=pivot, r=True)
                else:
                    maya.cmds.scale(scale, scale, scale, comps, pivot=pivot, a=True)

    def hide_attributes(self, attributes=None):
        """
        Lock and hide the given attributes on the control. If no attributes given, hide translate, rotate, scale and visibility
        :param attributes: list<str>, list of attributes to hide and lock (['translateX', 'translateY'])
        """

        if attributes:
            attribute.hide_attributes(self.meta_node, attributes)
        else:
            self.hide_translate_attributes()
            self.hide_rotate_attributes()
            self.hide_scale_attributes()
            self.hide_visibility_attribute()

    def hide_translate_attributes(self):
        """
        Lock and hide the translate attributes on the control
        """

        attribute.lock_translate_attributes(self.meta_node)

    def hide_rotate_attributes(self):
        """
        Lock and hide the rotate attributes on the control
        """

        attribute.lock_rotate_attributes(self.meta_node)

    def hide_scale_attributes(self):
        """
        Lock and hide the scale attributes on the control
        """

        attribute.lock_scale_attributes(self.meta_node)

    def hide_visibility_attribute(self):
        """
        Lock and hide the visibility attribute on the control
        """

        attribute.lock_attributes(self.meta_node, ['visibility'], hide=True)

    def hide_scale_and_visibility_attributes(self):
        """
        lock and hide the visibility and scale attributes on the control
        """

        self.hide_scale_attributes()
        self.hide_visibility_attribute()

    def hide_keyable_attributes(self):
        """
        Lock and hide all keyable attributes on the control
        """

        attribute.hide_keyable_attributes(self.meta_node)

    def show_translate_attributes(self):
        """
        Unlock and set keyable the control translate attributes
        """

        for axis in 'XYZ':
            maya.cmds.setAttr('{}.translate{}'.format(self.meta_node, axis), l=False, k=True)

    def show_rotate_attributes(self):
        """
        Unlock and set keyable the control rotate attributes
        """

        for axis in 'XYZ':
            maya.cmds.setAttr('{}.rotate{}'.format(self.meta_node, axis), l=False, k=True)

    def show_scale_attributes(self):
        """
        Unlock and set keyable the control scale attributes
        """

        for axis in 'XYZ':
            maya.cmds.setAttr('{}.scale{}'.format(self.meta_node, axis), l=False, k=True)

    def add_sub_control(self, sub_ctrl):
        """
        Adds a new sub control into the list of sub controls
        :param sub_ctrl: RigControl
        """

        if not self.message_list_get('sub_controls', as_meta=False):
            self.message_list_connect('sub_controls', [sub_ctrl], 'main_control')
        else:
            self.message_list_append('sub_controls', sub_ctrl, 'main_control')

    def get_sub_controls(self, as_meta=True):
        """
        Returns a list with all sub controls of this control
        :return: list<RigControl>
        """

        return self.message_list_get('sub_controls', as_meta=as_meta)

    def delete_shapes(self):
        """
        Delete all shapes beneath the control
        """

        shapes = self.get_shapes()
        maya.cmds.delete(shapes)

    def create(self):

        rig_module = self.get_rig_module()

        control_data = self.control_data if self.has_attr('control_data') and self.control_data else dict()

        curve_type = None
        if control_data:
            curve_type = control_data.get('control_type', None)
        if not curve_type:
            curve_type = self.type if self.has_attr('type') else 'circle'

        controls_path = None
        if self.has_attr('controls_path') and os.path.isdir(self.controls_path):
            controls_path = self.controls_path
        elif rig_module and rig_module.has_attr('controls_path') and \
                rig_module.controls_path and os.path.isfile(rig_module.controls_path):
            controls_path = rig_module.controls_path
        controls_path = controls_path if controls_path and os.path.isdir(controls_path) else None

        color = self.color if self.has_attr('color') and self.color else control_data.get('color', (1.0, 1.0, 1.0))

        if self.has_attr('size'):
            size = self.size * control_data.get('control_size', 1.0)
            if size != self.size:
                self.size = size
        else:
            size = control_data.get('control_size', 1.0)
            self.size = size

        # We scale the offset taking into account the module size
        # offset = (mathlib.Vector(*[0.0, 0.0, 0.0]) * size).list()

        curveslib.create_curve(
            curve_type=curve_type, curves_path=controls_path, curve_name='tempControl', curve_size=size,
            translate_offset=(0.0, 0.0, 0.0), color=color, parent=self.meta_node)

        if self.has_attr('create_root_group') and self.create_root_group:
            self.create_root()
        if self.has_attr('create_auto_group') and self.create_auto_group:
            self.create_auto()

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _get_naming_data(self):
        """
        Internal function that returns naming file and naming rule used by this control
        :return: tuple(str, str)
        """

        rig_module = self.get_rig_module()

        naming_file = self.naming_file if self.has_attr('naming_file') else None
        naming_rule = self.naming_rule if self.has_attr('naming_rule') else None
        if not naming_file and rig_module and rig_module.has_attr('naming_file'):
            naming_file = rig_module.naming_file
        if not naming_rule and rig_module and rig_module.has_attr('naming_rule'):
            naming_rule = rig_module.naming_rule
        naming_file = naming_file if naming_file and os.path.isfile(naming_file) else None

        return naming_file, naming_rule

    def _get_name(self, *args, **kwargs):
        """
        Internal function that returns a proper name for elements of the rig control
        :param name: str
        :param node_type: str
        :return: str
        """

        naming_file, naming_rule = self._get_naming_data()

        kwargs['side'] = self.side
        return tpRigToolkit.NamesMgr().solve_name(naming_file=naming_file, rule_name=naming_rule, *args, **kwargs)

    def _get_top_group(self):
        """
        Returns the root group of this control
        Root, auto or the control itself
        :return:
        """

        top_group = self
        if self.has_attr('auto_group') and self.auto_group.is_valid_mobject():
            top_group = self.auto_group
        if self.has_attr('root_group') and self.root_group.is_valid_mobject():
            top_group = self.root_group

        return top_group

    def _create_group(self, *args, **kwargs):
        """
        Internal function that creates new groups for the rig control
        :param group_name: str, name of the group
        :return:
        """

        if kwargs.get('force_suffix', True):
            kwargs['node_type'] = 'group'
        new_group = metaobject.MetaObject(name=self._get_name(*args, **kwargs), node_type='transform')
        new_group.add_attribute(attr='control', value=self, attr_type='messageSimple')

        return new_group
