#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains joint functions for tpRigToolkit-dccs-maya
"""

import maya.cmds

from tpDcc.libs.python import mathlib
from tpDcc.dccs.maya.core import decorators, name as name_utils, curve as curve_utils, attribute as attr_utils
from tpDcc.dccs.maya.core import transform as transform_utils

from tpRigToolkit.dccs.maya.core import control


@decorators.undo_chunk
def create_joints_along_curve(curve, count, description='new', attach=True, create_controls=False, controls_file=None):
    """
    Create joints on curve that do not aim at child
    :param curve: str, name of a curve
    :param count: int, number of joints to create
    :param description: str, description for the new created joints
    :param attach: bool, Whether to attach the joints to the curve or not
    :param create_controls: bool, Whether to create controls on top of the created joints
    :param controls_file: str, file used to create new controls shapes
    :return: list(str), list of created joints
    """

    maya.cmds.select(clear=True)

    joints_group = None
    control_group = None

    if create_controls:
        joints_group = maya.cmds.group(empty=True, n=name_utils.find_unique_name('joints_{}'.format(curve)))
        control_group = maya.cmds.group(empty=True, n=name_utils.find_unique_name('controls_{}'.format(curve)))
        maya.cmds.addAttr(control_group, ln='twist', k=True)
        maya.cmds.addAttr(control_group, ln='offsetScale', min=-1, dv=0, k=True)

    joints = list()
    current_length = 0
    percent = 0
    segment = 1.0 / count

    total_length = maya.cmds.arclen(curve)
    part_length = total_length / (count - 1)

    for i in range(count):
        param = curve_utils.get_parameter_from_curve_length(curve, current_length)
        position = curve_utils.get_point_from_curve_parameter(curve, param)
        if attach:
            maya.cmds.select(clear=True)
        new_joint = maya.cmds.joint(p=position, n=name_utils.find_unique_name('{}_jnt'.format(description)))
        maya.cmds.addAttr(new_joint, ln='param', at='double', dv=param, k=True)
        if joints:
            maya.cmds.joint(joints[-1], e=True, zso=True, oj='xyz', sao='yup')
        if attach:
            attach_node = curve_utils.attach_to_curve(new_joint, curve, parameter=param)
            if create_controls:
                maya.cmds.parent(new_joint, joints_group)
                maya.cmds.connectAttr('{}.param'.format(new_joint), '{}.parameter'.format(attach_node))

        current_length += part_length

        if create_controls and attach:
            new_control = control.RigControl(
                name_utils.find_unique_name('tweaker_{}'.format(description)), controls_file=controls_file)
            new_control.set_curve_type('pin')
            new_control.rotate_shape(90, 0, 0)
            new_control.hide_visibility_attribute()
            control_name = new_control.get()
            parameter_value = maya.cmds.getAttr('{}.parameter'.format(attach_node))
            percent_var = attr_utils.NumericAttribute('percent')
            percent_var.set_min_value(0)
            percent_var.set_max_value(10)
            percent_var.set_value(parameter_value * 10)
            percent_var.create(control_name)
            attr_utils.connect_multiply(percent_var.get_full_name(), '{}.parameter'.format(attach_node), 0.1)
            buffer_group = transform_utils.create_buffer_group(control_name)
            for axis in 'XYZ':
                maya.cmds.connectAttr(
                    '{}.position{}'.format(attach_node, axis), '{}.translate{}'.format(buffer_group, axis))
            side = new_control.update_color_respect_side(True, 0.1)
            if side != 'C':
                control_name = maya.cmds.rename(
                    control_name, name_utils.find_unique_name(control_name[0:-3] + '1_{}'.format(side)))

            attr_utils.connect_translate(control_name, new_joint)
            attr_utils.connect_rotate(control_name, new_joint)
            offset = mathlib.fade_sine(percent)
            attr_utils.connect_multiply('{}.twist'.format(control_group), '{}.rotateX'.format(new_joint), offset)
            plus = maya.cmds.createNode('plusMinusAverage', n='plus_{}'.format(control_group))
            maya.cmds.setAttr('{}.input1D[0]'.format(plus), 1)
            attr_utils.connect_multiply(
                '{}.offsetScale'.format(control_group), '{}.input1D[1]'.format(plus), offset, plus=False)
            multiply = attr_utils.MultiplyDivideNode(control_group)
            multiply.input1X_in('{}.output1D'.format(plus))
            multiply.input1Y_in('{}.output1D'.format(plus))
            multiply.input1Z_in('{}.output1D'.format(plus))
            multiply.input2X_in('{}.scaleX'.format(control_name))
            multiply.input2Y_in('{}.scaleY'.format(control_name))
            multiply.input2Z_in('{}.scaleZ'.format(control_name))
            multiply.outputX_out('{}.scaleX'.format(new_joint))
            multiply.outputY_out('{}.scaleY'.format(new_joint))
            multiply.outputZ_out('{}.scaleZ'.format(new_joint))
            maya.cmds.parent(buffer_group, control_group)

        joints.append(new_joint)
        percent += segment

    if create_controls and not attach:
        maya.cmds.parent(joints[0], joints_group)

    return joints, joints_group, control_group
