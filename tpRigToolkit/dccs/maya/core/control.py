#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig control implementation for Maya
"""

import os

import tpDcc as tp
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.core import decorators, shape as shape_utils, node as node_utils, curve as curve_utils
from tpDcc.dccs.maya.core import name as name_utils, transform as transform_utils, attribute as attr_utils

from tpRigToolkit.libs.controlrig.core import controllib


class RigControl(object):
    """
    Creates a curve based control
    """

    def __init__(self, name, tag=True, curve_type=None, controls_file=None):
        self._control = name
        self._curve_type = curve_type
        self._controls_file = controls_file

        if not maya.cmds.objExists(self._control):
            self._create(tag)

        self._shapes = shape_utils.get_shapes(self._control)
        if not self._shapes:
            maya.logger.warning('{} has no shapes'.format(self._control))

    def get(self):
        """
        Returns name of the control
        :return: str
        """

        return self._control

    def get_buffer_group(self, name='buffer'):
        """
        Returns transform group located above the control
        :return: str
        """

        return transform_utils.get_buffer_group(self.get(), name)

    def translate_shape(self, x, y, z):
        """
        Translates control shapes curve CVs in object space
        :param x: float
        :param y: float
        :param z: float
        """

        components = self._get_components()
        if not components:
            return False

        maya.cmds.move(x, y, z, components, relative=True, os=True, wd=True)

        return True

    def rotate_shape(self, x, y, z):
        """
        Rotates control shapes curve CVs in object space
        :param x: float
        :param y: float
        :param z: float
        """

        components = self._get_components()
        if not components:
            return False

        maya.cmds.rotate(x, y, z, components, relative=True)

        return True

    def scale_shape(self, x, y, z, use_pivot=True):
        """
        Scales control shapes curve CVs in object space
        :param x: float
        :param y: float
        :param z: float
        :param use_pivot: bool
        """

        components = self._get_components()
        if not components:
            return False

        if use_pivot:
            pivot = maya.cmds.xform(self.get(), query=True, rp=True, ws=True)
        else:
            shapes = shape_utils.get_shapes_of_type(self.get(), shape_type='nurbsCurve')
            if not shapes:
                return False
            components = shape_utils.get_components_from_shapes(shapes)
            bounding = transform_utils.BoundingBox(components)
            pivot = bounding.get_center()

        if components:
            maya.cmds.scale(x, y, z, components, pivot=pivot, r=True)

        return True

    def show_translate_attributes(self):
        """
        Unlocks and set keyable the control's translate attributes
        """

        for axis in 'XYZ':
            maya.cmds.setAttr('{}.translate{}'.format(self.get(), axis), l=False, k=True)

    def show_rotate_attributes(self):
        """
        Unlocks and set keyable the control's rotate attributes
        """

        for axis in 'XYZ':
            maya.cmds.setAttr('{}.rotate{}'.format(self.get(), axis), l=False, k=True)

    def show_scale_attributes(self):
        """
        Unlocks and set keyable the control's scale attributes
        """

        for axis in 'XYZ':
            maya.cmds.setAttr('{}.scale{}'.format(self.get(), axis), l=False, k=True)

    def hide_attributes(self, attributes=None):
        """
        Locks and hide the given attributes on the control. If no attributes given, hide translate, rotate, scale and
        visibility
        :param attributes:
        :return:
        """

        if attributes:
            attr_utils.hide_attributes(self.get(), attributes)
        else:
            self.hide_translate_attributes()
            self.hide_rotate_attributes()
            self.hide_scale_and_visibility_attributes()

    def hide_translate_attributes(self):
        """
        Locks and hide translate attributes on the control
        """

        return attr_utils.hide_attributes(self.get(), ['translate{}'.format(axis) for axis in 'XYZ'])

    def hide_rotate_attributes(self):
        """
        Locks and hide rotate attributes on the control
        """

        return attr_utils.hide_attributes(self.get(), ['rotate{}'.format(axis) for axis in 'XYZ'])

    def hide_scale_attributes(self):
        """
        Locks and hide scale attributes on the control
        """

        return attr_utils.hide_attributes(self.get(), ['scale{}'.format(axis) for axis in 'XYZ'])

    def hide_visibility_attribute(self):
        """
        Locks and hide the visibility attribute on the control
        """

        return attr_utils.hide_attributes(self.get(), ['visibility'])

    def hide_scale_and_visibility_attributes(self):
        """
        Locks and hide the visibility and scale attributes on the control
        """

        self.hide_scale_attributes()
        self.hide_visibility_attribute()

    def hide_keyable_attributes(self):
        """
        Locks and hide all keyable attributes on the control
        """

        return attr_utils.hide_keyable_attributes(self.get())

    def create_buffer_group(self):
        """
        Creates a buffer group above the control
        :return: str
        """

        return transform_utils.create_buffer_group(self.get())

    def set_controls_file(self, controls_file):
        """
        Sets the file used to load controls curve data from
        :param controls_file: str
        """

        self._controls_file = controls_file

    @decorators.undo_chunk
    def set_color(self, value):
        """
        Sets the color of the control shapes
        :param value: int, Maya color override index
        """

        shapes = shape_utils.get_shapes(self.get())
        if not shapes:
            return False

        node_utils.set_color(shapes, value)

    @decorators.undo_chunk
    def set_color_rgb(self, r=0, g=0, b=0):
        """
        Sets the RGB color of the control shapes
        Only supported in versions of Maya greater or equal to 2015
        :param r: float
        :param g: float
        :param b: float
        """

        shapes = shape_utils.get_shapes(self.get())
        if not shapes:
            return False

        node_utils.set_rgb_color(shapes, [r, g, b])

    @decorators.undo_chunk
    def set_rotate_order(self, xyz_order):
        """
        Sets the rotate order of the control
        :param xyz_order: str ('xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx')
        """

        xyz_orders = ['xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx']

        if type(xyz_order) == int:
            value = xyz_order
        else:
            value = 0
            if xyz_order in xyz_orders:
                value = xyz_orders.index(xyz_order)

        return maya.cmds.setAttr('{}.rotateOrder'.format(self.get(), value))

    @decorators.undo_chunk
    def set_curve_type(self, type_name=None):
        """
        Updates the curves of the control with the given control type
        :param type_name: str
        """

        if not type_name:
            if maya.cmds.objExists('{}.curveType'.format(self.get())):
                type_name = maya.cmds.getAttr('{}.curveType'.format(self.get()))
        if not type_name:
            maya.logger.warning('Impossible to set curve type because not type name given!')
            return False

        shapes = shape_utils.get_shapes(self.get())
        color = node_utils.get_rgb_color(shapes[0]) if shapes else 0
        controls_lib = self._get_controls_lib()
        control_exists = controls_lib.control_exists(type_name)
        if not control_exists:
            maya.logger.warning(
                'Impossible to set curve type because control library does not contains shape {}'.format(type_name))
            return False

        control_data = controls_lib.get_control_data_by_name(type_name)
        if not control_data:
            return False

        css = controls_lib.create_control(
            shape_data=control_data.shapes,
            target_object=self.get(),
            color=color
        )
        controls_lib.set_shape(self._control, css)
        self._shapes = shape_utils.get_shapes(self.get())
        string_attr = attr_utils.StringAttribute('curveType')
        string_attr.create(self._control)
        string_attr.set_value(type_name)
        maya.cmds.select(clear=True)

        return True

    @decorators.undo_chunk
    def set_curve_as_text(self, text):
        """
        Updates the curves of the control with the given text (as curves)
        :param text: str
        """

        shapes = shape_utils.get_shapes(self.get())
        color = node_utils.get_rgb_color(shapes[0])
        curve_utils.set_shapes_as_text_curve(self.get(), text)
        self._shapes = shape_utils.get_shapes(self.get())
        node_utils.set_color(self._shapes, color)
        maya.cmds.select(clear=True)

        return True

    @decorators.undo_chunk
    def set_to_joint(self, joint=None, scale_compensate=False):
        """
        Updates the control to have a joint as its main transform type
        :param joint: str, name of a joint to use. If not given, the joint will be created automatically
        :param scale_compensate: bool, Whether to connect scale of parent to inverseScale of joint. This causes
            the group above the joint to be able to change scale value without affect the control's look
        """

        maya.cmds.select(clear=True)

        name = self.get()
        joint_given = True
        temp_parent = None
        curve_type_value = ''

        if not joint:
            joint = maya.cmds.joint()
            maya.cmds.delete(maya.cmds.parentConstraint(name, joint))
            maya.cmds.delete(maya.cmds.parentConstraint(name, joint))
            buffer_group = maya.cmds.group(empty=True, n=name_utils.find_unique_name('temp_{}'.format(joint)))
            maya.cmds.parent(buffer_group, self.get())
            maya.cmds.parent(joint, buffer_group)
            maya.cmds.makeIdentity(buffer_group, t=True, r=True, s=True, jo=True, apply=True)
            maya.cmds.parent(joint, w=True)
            temp_parent = maya.cmds.listRelatives(joint, p=True)
            maya.cmds.delete(buffer_group)
            joint_given = False

        shapes = shape_utils.get_shapes_of_type(self.get(), shape_type='nurbsCurve') or list()
        for shape in shapes:
            maya.cmds.parent(shape, joint, r=True, s=True)

        if joint_given:
            transform_utils.transfer_relatives(name, joint, reparent=False)
        else:
            parent = maya.cmds.listRelatives(name, p=True)
            if parent:
                maya.cmds.parent(joint, parent)
                if temp_parent:
                    maya.cmds.delete(temp_parent)
                maya.cmds.makeIdentity(joint, r=True, s=True, apply=True)
            transform_utils.transfer_relatives(name, joint)
            if scale_compensate:
                parent = maya.cmds.listRelatives(joint, p=True)
                if parent:
                    maya.cmds.connectAttr('{}.scale'.format(parent[0]), '{}.inverseScale'.format(joint))

        transfer = attr_utils.TransferAttributes()
        transfer.transfer_control(name, joint)
        attr_utils.transfer_output_connections(name, joint)

        maya.cmds.setAttr('{}.radius'.format(joint), l=True, k=False, cb=False)
        maya.cmds.setAttr('{}.drawStyle'.format(joint), 2)

        if maya.cmds.objExists('{}.curveType'.format(name)):
            curve_type_value = maya.cmds.getAttr('{}.curveType'.format(name))

        maya.cmds.delete(name)

        if not joint_given:
            joint = maya.cmds.rename(joint, name)

        self._control = joint

        if joint_given:
            shape_utils.rename_shapes(self._control)

        string_attr = attr_utils.StringAttribute('curveType')
        string_attr.create(joint)
        string_attr.set_value(curve_type_value)

        return True

    @decorators.undo_chunk
    def rename(self, new_name):
        """
        Gives a new name to the control
        :param new_name: str
        :return: str
        """

        new_name = name_utils.find_unique_name(new_name)
        self._rename_message_groups(self.get(), new_name)
        new_name = maya.cmds.rename(self.get(), new_name)
        constraints = maya.cmds.listRelatives(new_name, type='constraint')
        if constraints:
            for constraint in constraints:
                new_constraint = constraint.replace(self.get(), new_name)
                maya.cmds.rename(constraint, new_constraint)
        self._control = new_name
        shape_utils.rename_shapes(self._control)

        return self._control

    @decorators.undo_chunk
    def delete_shapes(self):
        """
        Deletes all control shapes
        """

        self._shapes = shape_utils.get_shapes(self.get())
        maya.cmds.delete(self._shapes)
        self._shapes = list()

    @decorators.undo_chunk
    def copy_shapes(self, transform):
        """
        Copies all shapes from the given transform to the control transform
        :param transform: str
        """

        if not shape_utils.has_shape_of_type(transform, 'nurbsCurve'):
            return

        orig_shapes = shape_utils.get_shapes_of_type(self.get(), shape_type='nurbsCurve')

        temp = maya.cmds.duplicate(transform)[0]
        maya.cmds.parent(temp, self.get())
        maya.cmds.makeIdentity(temp, apply=True, t=True, r=True, s=True)

        shapes = shape_utils.get_shapes_of_type(temp, shape_type='nurbsCurve')
        color = None
        colors = dict()
        if shapes:
            index = 0
            for shape in shapes:
                if index < len(orig_shapes) and index < len(shapes):
                    color = node_utils.get_rgb_color(orig_shapes[index])
                colors[shape] = color
                if color:
                    if type(color) != list:
                        node_utils.set_color(shape, color)
                    else:
                        node_utils.set_rgb_color(shape, [color[0], color[1], color[2]])
                maya.cmds.parent(shape, self.get(), r=True, shape=True)
                index += 1

        maya.cmds.delete(orig_shapes)
        maya.cmds.delete(temp)

        shape_utils.rename_shapes(self.get())

    @decorators.undo_chunk
    def update_color_respect_side(self, sub=False, center_tolerance=0.001):
        """
        Updates control shapes color taking into account the position of the control (left, right or center)
        :param sub: bool, Whether to set the color to sub colors
        :param center_tolerance: float, distance the control can be from center before it is considered left or right
        :return:str, side of the control as letter ('L', 'R' or 'C')
        """

        position = maya.cmds.xform(self.get(), query=True, ws=True, t=True)
        if position[0] > 0:
            color_value = tp.Dcc.get_color_of_side('L', sub)
            side = 'L'
        elif position[0] < 0:
            color_value = tp.Dcc.get_color_of_side('R', sub)
            side = 'R'
        elif center_tolerance > position[0] > center_tolerance * -1:
            color_value = tp.Dcc.get_color_of_side('C', sub)
            side = 'C'

        if type(color_value) == int or type(color_value) == float:
            self.set_color(int(color_value))
        else:
            self.set_color_rgb(color_value[0], color_value[1], color_value[2])

        return side

    def _get_controls_lib(self):
        """
        Internal function that returns control library used to create the control
        :return:  controllib.ControlLib
        """

        controls_lib = controllib.ControlLib()
        if self._controls_file and os.path.isfile(self._controls_file):
            controls_lib.controls_file = self._controls_file

        return controls_lib

    def _create(self, tag=True):
        """
        Internal function that forces the creation of the control curve
        :param tag: bool, Whether or not to tag the new control curve
        """

        self._control = maya.cmds.circle(ch=False, n=self._control, normal=[1, 0, 0])[0]
        if self._curve_type:
            self.set_curve_type(self._curve_type)
        if tag:
            try:
                maya.cmds.controller(self._control)
            except Exception:
                pass

    def _get_components(self):
        """
        Internal function that returns the geometry components of the control curve
        :return: list(str)
        """

        self._shapes = shape_utils.get_shapes(self._control)
        return shape_utils.get_components_from_shapes(self._shapes)

    def _rename_message_groups(self, search_name, replace_name):
        message_attrs = attr_utils.get_message_attributes(search_name)
        if message_attrs:
            for attr_name in message_attrs:
                attr_node = '{}.{}'.format(search_name, attr_name)
                if attr_name.startswith('group'):
                    node = attr_utils.get_attribute_input(attr_node, True)
                    if node.find(search_name) > -1:
                        new_node = node.replace(search_name, replace_name)
                        self._rename_message_groups(node, new_node)
                        constraints = maya.cmds.listRelatives(node, type='constraint')
                        if constraints:
                            for constraint in constraints:
                                new_constraint = constraint.replace(node, new_node)
                                maya.cmds.rename(constraint, new_constraint)
                        maya.cmds.rename(node, new_node)


def rename_control(old_name, new_name):
    """
    Renames given control name with the new one
    :param old_name: str
    :param new_name: str
    :return: str
    """

    return RigControl(old_name).rename(new_name)
