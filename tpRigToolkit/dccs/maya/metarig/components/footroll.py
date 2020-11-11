#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains foot roll rig metarig implementations for Maya
"""

from __future__ import print_function, division, absolute_import

import logging

import maya.cmds

from tpDcc import dcc
from tpDcc.dccs.maya.meta import metanode, metautils

from tpRigToolkit.dccs.maya.metarig.core import component, mixin

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class FootRollComponent(component.RigComponent, mixin.JointMixin):

    def __init__(self, *args, **kwargs):
        super(FootRollComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        mixin.JointMixin.__init__(self)
        self.set_name(kwargs.get('name', 'footRoll'))
        self.set_foot_control(None)
        self.set_create_roll_controls(True)
        self.set_create_foot_roll(False)
        self.set_create_ankle_roll(False)
        self.set_toe_rotate_as_locator(False)
        self.set_mirror_yaw(False)
        self.set_forward_roll_axis('X')
        self.set_side_roll_axis('Z')
        self.set_top_roll_axis('Y')
        self.set_toe_control_data({})
        self.set_ik_leg(None)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(FootRollComponent, self).create()

        joints = self.get_joints()
        if not len(joints) == 7:
            LOGGER.warning(
                '6 joints must be defined (yawIn, yawOut, heel, mid, toe, ball, ankle) to create root setup!')
            return

        self.add_attribute('yawin', value=joints[0], attr_type='messageSimple')
        self.add_attribute('yawout', value=joints[1], attr_type='messageSimple')
        self.add_attribute('heel', value=joints[2], attr_type='messageSimple')
        self.add_attribute('ankle', value=joints[3], attr_type='messageSimple')
        self.add_attribute('ball', value=joints[4], attr_type='messageSimple')
        self.add_attribute('toe', value=joints[5], attr_type='messageSimple')

        dcc.add_title_attribute(self.foot_roll_control.meta_node, 'FOOT_CONTROLS')

        if self.create_roll_controls:
            dcc.add_bool_attribute(self.foot_roll_control.meta_node, 'controlVisibility', self.sub_visibility)

        self._create_roll_attributes()

        self._create_toe_rotate_control()
        self._create_toe_roll()
        self._create_heel_roll()
        self._create_yawout_roll()
        self._create_yawin_roll()
        self._create_ball_roll()

        if self.create_foot_roll:
            self._create_foot_roll()

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_foot_roll_control(self, control):
        """
        Sets the main control used by foot roll rig setup
        :param control:
        :return:
        """

        if not self.has_attr('foot_roll_control'):
            self.add_attribute('foot_roll_control', value=control, attr_type='messageSimple')
        else:
            self.foot_roll_control = control

    def set_create_roll_controls(self, flag):
        """
        Sets whether roll controls should be created or not
        :param flag: bool
        """

        if not self.has_attr('create_roll_controls'):
            self.add_attribute('create_roll_controls', value=flag, attr_type='bool')
        else:
            self.create_roll_controls = flag

    def set_create_foot_roll(self, flag):
        """
        Sets whether or not foot roll functionality should be added
        :param flag: bool
        """

        if not self.has_attr('create_foot_roll'):
            self.add_attribute('create_foot_roll', value=flag, attr_type='bool')
        else:
            self.create_foot_roll = flag

    def set_create_ankle_roll(self, flag, axis='Z'):
        """
        Sets whether or not ankle roll functionality should be added
        :param flag: bool
        :param axis: str
        """

        if not self.has_attr('create_ankle_roll'):
            self.add_attribute('create_ankle_roll', value=flag, attr_type='bool')
        else:
            self.create_ankle_roll = flag

        if not self.has_attr('ankle_roll_axis'):
            self.add_attribute('ankle_roll_axis', value=axis.upper(), attr_type='string')
        else:
            self.ankle_roll_axis = axis.upper()

    def set_toe_rotate_as_locator(self, flag):
        """
        Sets whether toe rotate control should be created as a control or as a locator
        :param flag: bool
        """

        if not self.has_attr('toe_rotate_as_locator'):
            self.add_attribute('toe_rotate_as_locator', value=flag, attr_type='bool')
        else:
            self.toe_rotate_as_locator = flag

    def set_mirror_yaw(self, flag):
        """
        Sets whether yaw rotation should be mirrored or not
        NOTE: Mirror is only applied on right side components.
        :param flag: bool
        """

        if not self.has_attr('mirror_yaw'):
            self.add_attribute('mirror_yaw', value=flag, attr_type='bool')
        else:
            self.mirror_yaw = flag

    def set_forward_roll_axis(self, axis):
        """
        Sets forward axis used for roll
        :param axis: str
        """

        if not self.has_attr('forward_roll_axis'):
            self.add_attribute('forward_roll_axis', value=axis.upper(), attr_type='string')
        else:
            self.forward_roll_axis = axis.upper()

    def set_side_roll_axis(self, axis):
        """
        Sets side axis used for roll
        :param axis: str
        """

        if not self.has_attr('side_roll_axis'):
            self.add_attribute('side_roll_axis', value=axis.upper(), attr_type='string')
        else:
            self.side_roll_axis = axis.upper()

    def set_top_roll_axis(self, axis):
        """
        Sets top axis used for roll
        :param axis: str
        """

        if not self.has_attr('top_roll_axis'):
            self.add_attribute('top_roll_axis', value=axis.upper(), attr_type='string')
        else:
            self.top_roll_axis = axis.upper()

    def set_toe_control_data(self, control_data):
        """
        Sets the control data used by the toe control
        :param control_data: dict
        """

        if not self.has_attr('toe_control_data'):
            self.add_attribute(attr='toe_control_data', value=control_data)
        else:
            self.toe_control_data = control_data

    def set_ik_leg(self, node):
        """
        Sets the node of the Ik leg this node should be attached to
        :param node:
        :return:
        """

        if not self.has_attr('ik_leg'):
            self.add_attribute('ik_leg', value=node, attr_type='messageSimple')
        else:
            self.ik_leg = node

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_roll_control(self, source_transform, name, sub=False, no_control=False, scale=-1):
        """

        :param source_transform:
        :param name:
        :param sub:
        :param no_control:
        :param scale:
        :return:
        """

        if self.create_roll_controls:
            new_control = self.create_control(name, sub=sub)
            new_control.scale_control_shapes(scale=(scale, scale, scale))
            root_group = new_control.create_root()
            driver_group = new_control.create_auto('driver')
            new_control.match_translation(source_transform)
            new_control.match_rotation(self.get_joints()[-1])
            new_control.hide_scale_and_visibility_attributes()
            new_control.hide_translate_attributes()

            if dcc.attribute_exists(self.foot_roll_control.meta_node, 'controlVisibility'):
                control_shape = new_control.get_shapes()
                for shape in control_shape:
                    dcc.connect_attribute(self.foot_roll_control.meta_node, 'controlVisibility', shape, 'visibility')

        if not self.create_roll_controls or no_control:
            new_control = dcc.create_empty_group(name=self._get_name(self.name, name, node_type='control'))
            root_group = dcc.create_buffer_group(new_control)
            driver_group = dcc.create_buffer_group(new_control, suffix='driver')
            # TODO: We should connect buffer and driver groups to new control using messages
            dcc.match_translation(root_group, source_transform)
            dcc.match_rotation(root_group, self.get_joints(as_meta=False)[-1])
            new_control = metanode.validate_obj_arg(new_control, 'MetaObject', update_class=True)
            root_group = metanode.validate_obj_arg(root_group, 'MetaObject', update_class=True)
            driver_group = metanode.validate_obj_arg(driver_group, 'MetaObject', update_class=True)

        return new_control, root_group, driver_group

    def _create_roll_attributes(self):
        """
        Internal function that creates basic roll attributes
        :return:
        """

        roll_control = self.foot_roll_control.meta_node

        if self.create_foot_roll:
            dcc.add_double_attribute(roll_control, 'footRoll', keyable=True)
            dcc.add_double_attribute(roll_control, 'footRoll', default_value=30, footRollAngle=True)

        if self.create_ankle_roll:
            dcc.add_double_attribute(roll_control, 'ankleRoll', keyable=True)

        for attr_name in ['ballRoll', 'toeRoll', 'heelRoll', 'yawRoll']:
            dcc.add_double_attribute(roll_control, attr_name, keyable=True)

    def _create_toe_rotate_control(self):
        """
        Internal function that creates toe rotate control
        """

        roll_control = self.foot_roll_control.meta_node

        dcc.add_double_attribute(roll_control, 'toeRotate', keyable=True)

        if self.toe_rotate_as_locator:
            toe_control = dcc.create_locator(name=self._get_name(self.name, 'toeRotate', node_type='locator'))
            toe_control_root = dcc.create_buffer_group(toe_control)
            dcc.connect_attribute(
                roll_control, 'toeRotate', toe_control, 'rotate{}'.format(self.forward_roll_axis.upper()))
        else:
            toe_control = self.create_control('toeRotate', sub=True, control_data=self.toe_control_data)
            toe_control.hide_translate_attributes()
            toe_control.hide_scale_and_visibility_attributes()
            toe_control_root = toe_control.create_root().meta_node
            toe_control_driver = toe_control.create_auto('driver')
            dcc.connect_attribute(
                roll_control, 'toeRotate', toe_control_driver.meta_node,
                'rotate{}'.format(self.forward_roll_axis.upper()))

        dcc.match_translation_rotation(self.ball.meta_node, toe_control_root)

        return toe_control.meta_node, toe_control_root

    def _create_toe_roll(self):

        toe_roll_control, toe_roll_root, toe_roll_driver = self._create_roll_control(self.toe.meta_node, 'toe')
        toe_roll_root.set_parent(self.heel)

        for driven_keys in [(0, 0), (10, 45), (-10, -45)]:
            maya.cmds.setDrivenKeyframe(
                '{}.rotate{}'.format(toe_roll_driver.meta_node, self.forward_roll_axis),
                cd='{}.toeRoll'.format(self.foot_roll_control.meta_node),
                driverValue=driven_keys[0], value=driven_keys[1], itt='spline', ott='spline'
            )

        maya.cmds.setInfinity(
            '{}.rotate{}'.format(toe_roll_driver.meta_node, self.forward_roll_axis), postInfinite='linear')
        maya.cmds.setInfinity(
            '{}.rotate{}'.format(toe_roll_driver.meta_node, self.forward_roll_axis), preInfinite='linear')

        self.add_attribute('toe_roll', value=toe_roll_driver, attr_type='messageSimple')

        return toe_roll_control

    def _create_heel_roll(self):

        heel_roll_control, heel_roll_root, heel_roll_driver = self._create_roll_control(self.heel.meta_node, 'heel')
        heel_roll_root.set_parent(self.toe_roll)

        for driven_keys in [(0, 0), (-10, -45), (10, 45)]:
            maya.cmds.setDrivenKeyframe(
                '{}.rotate{}'.format(heel_roll_driver.meta_node, self.forward_roll_axis),
                cd='{}.heelRoll'.format(self.foot_roll_control.meta_node),
                driverValue=driven_keys[0], value=driven_keys[1], itt='spline', ott='spline'
            )

        maya.cmds.setInfinity(
            '{}.rotate{}'.format(heel_roll_driver.meta_node, self.forward_roll_axis), postInfinite='linear')
        maya.cmds.setInfinity(
            '{}.rotate{}'.format(heel_roll_driver.meta_node, self.forward_roll_axis), preInfinite='linear')

        self.add_attribute('heel_roll', value=heel_roll_driver, attr_type='messageSimple')

        return heel_roll_control

    def _create_yawout_roll(self):

        yawout_roll_control, yawout_roll_root, yawout_roll_driver = self._create_roll_control(
            self.yawout.meta_node, 'yawOut')
        yawout_roll_root.set_parent(self.heel_roll)

        final_value = 10
        if self.mirror_yaw and dcc.name_is_right(self.side):
            final_value = -10
        final_other_value = -45
        if self.mirror_yaw and dcc.name_is_right(self.side):
            final_other_value = 45

        for driven_keys in [(0, 0), (final_value, final_other_value)]:
            maya.cmds.setDrivenKeyframe(
                '{}.rotate{}'.format(yawout_roll_driver.meta_node, self.side_roll_axis),
                cd='{}.yawRoll'.format(self.foot_roll_control.meta_node),
                driverValue=driven_keys[0], value=driven_keys[1], itt='spline', ott='spline'
            )

        if self.mirror_yaw and dcc.name_is_right(self.side):
            maya.cmds.setInfinity(
                '{}.rotate{}'.format(yawout_roll_driver.meta_node, self.side_roll_axis), preInfinite='linear')
        else:
            maya.cmds.setInfinity(
                '{}.rotate{}'.format(yawout_roll_driver.meta_node, self.side_roll_axis), postInfinite='linear')

        self.add_attribute('yawout_roll', value=yawout_roll_control, attr_type='messageSimple')

        return yawout_roll_control

    def _create_yawin_roll(self):

        yawin_roll_control, yawin_roll_root, yawin_roll_driver = self._create_roll_control(
            self.yawin.meta_node, 'yawIn')
        yawin_roll_root.set_parent(self.yawout_roll)

        final_value = -10
        if self.mirror_yaw and dcc.name_is_right(self.side):
            final_value = 10
        final_other_value = 45
        if self.mirror_yaw and dcc.name_is_right(self.side):
            final_other_value = -45

        for driven_keys in [(0, 0), (final_value, final_other_value)]:
            maya.cmds.setDrivenKeyframe(
                '{}.rotate{}'.format(yawin_roll_driver.meta_node, self.side_roll_axis),
                cd='{}.yawRoll'.format(self.foot_roll_control.meta_node),
                driverValue=driven_keys[0], value=driven_keys[1], itt='spline', ott='spline'
            )

        if self.mirror_yaw and dcc.name_is_right(self.side):
            maya.cmds.setInfinity(
                '{}.rotate{}'.format(yawin_roll_driver.meta_node, self.side_roll_axis), postInfinite='linear')
        else:
            maya.cmds.setInfinity(
                '{}.rotate{}'.format(yawin_roll_driver.meta_node, self.side_roll_axis), preInfinite='linear')

        self.add_attribute('yawin_roll', value=yawin_roll_control, attr_type='messageSimple')

        return yawin_roll_control

    def _create_ball_roll(self):
        ball_roll_control, ball_roll_root, ball_roll_driver = self._create_roll_control(self.ball.meta_node, 'ball')
        ball_roll_root.set_parent(self.yawin_roll)

        for driven_keys in [(0, 0), (10, 45), (-10, -45)]:
            maya.cmds.setDrivenKeyframe(
                '{}.rotate{}'.format(ball_roll_driver.meta_node, self.forward_roll_axis),
                cd='{}.ballRoll'.format(self.foot_roll_control.meta_node),
                driverValue=driven_keys[0], value=driven_keys[1], itt='spline', ott='spline'
            )

        maya.cmds.setInfinity(
            '{}.rotate{}'.format(ball_roll_driver.meta_node, self.forward_roll_axis), postInfinite='linear')
        maya.cmds.setInfinity(
            '{}.rotate{}'.format(ball_roll_driver.meta_node, self.forward_roll_axis), preInfinite='linear')

        if self.create_ankle_roll:
            metautils.MetaAttributeUtils.connect(
                (self.foot_roll_control, 'ankleRoll'), (ball_roll_driver, 'rotate{}'.format(self.ankle_roll_axis)))

        self.add_attribute('ball_roll', value=ball_roll_driver, attr_type='messageSimple')

        return ball_roll_control

    def _create_foot_roll(self):
        pass
