#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base FK chain rig metarig implementation for Maya
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp
import tpDcc.dccs.maya as maya

import tpRigToolkit
from tpRigToolkit.dccs.maya.metarig.components import buffer


class FkChainComponent(buffer.BufferComponent, object):

    def __init__(self, *args, **kwargs):
        super(FkChainComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_buffer_replace([['jnt', 'je'], ['fkJnt', 'fkJe']])
        self.set_skip_increments([])
        self.set_match_to_rotation(True)
        self.set_offset_rotation([])        # [0, 0, 0]
        self.set_increment_offset_rotation()

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def create(self):
        super(FkChainComponent, self).create()

        self._setup()

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def set_skip_increments(self, integers_list):
        """
        Sets which FK controls increments are skipped
        :param integers_list: list<int>, list of integers
            - [0]: will the first increment
            - [0, 1]: will skip the first increments
            - etc
        """

        if not self.has_attr('skip_increments'):
            self.add_attribute(attr='skip_increments', value=integers_list)
        else:
            self.skip_increments = integers_list

    def set_match_to_rotation(self, flag):
        """
        Sets whether FK controls should match joints rotation or not
        :param flag: bool
        """

        if not self.has_attr('match_to_rotation'):
            self.add_attribute(attr='match_to_rotation', value=flag)
        else:
            self.match_to_rotation = flag

    def set_offset_rotation(self, rotation_vector):
        """
        Sets the rotation vector that will be used to offset controls rotation
        For example, a value of [0, 90, 0] will rotate the root group of the control 90 degrees on the Y axis
        """

        if not self.has_attr('offset_rotation'):
            self.add_attribute(attr='offset_rotation', value=rotation_vector)
        else:
            self.offset_rotation = rotation_vector

    def set_increment_offset_rotation(self, increment=None, rotation_vector=None):
        """
        Sets the rotation vector that will be used to offset the control with the given index
        :param increment: int, index of the control we want to use in the FK chain
        :param rotation_vector: list
        """

        if rotation_vector is None:
            rotation_vector = list()

        if not self.has_attr('increment_offset_rotation'):
            self.add_attribute(attr='increment_offset_rotation', value=[[]])
        else:
            self.increment_offset_rotation[increment] = rotation_vector

    def set_transforms(self, transforms, clean=False):
        if not self.message_list_get('transforms', as_meta=False):
            self.message_list_connect('transforms', transforms)
        else:

            if clean:
                self.message_list_purge('transforms')
            for xform in transforms:
                self.message_list_append('transforms', xform)

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _create_control(self, sub=False, id=0, name=None, **kwargs):
        """
        Internal function that creates a new control for the FK chain
        :param sub: bool
        :param id: int
        """

        control_name = name or 'fkChain'
        sub_id = kwargs.pop('sub_id', None)
        if sub_id is not None:
            new_control = self.create_control(name=control_name, id=id, sub=sub, sub_id=sub_id)
        else:
            new_control = self.create_control(name=control_name, id=id, sub=sub)

        self._set_control_attributes(new_control)

        new_control.create_root(id=id)
        new_control.create_auto(id=id)

        # if len(self.get_controls(as_meta=False)) == 1:
        #     new_control.set_parent(self.get_controls_group())
        #
        if self.create_sub_controls and not sub:
            for i in range(0, 2):
                sub_letter = 'A' if i == 0 else 'B'
                sub_control = self._create_control(name='subControl{}'.format(sub_letter), id=id, sub_id=i, sub=True)
                self._connect_sub_visibility(new_control, sub_control)
                if self.hide_sub_controls_translate:
                    sub_control.hide_translate_attributes()
                sub_control.hide_scale_and_visibility_attributes()
                sub_control.match_translation_and_rotation(new_control)
                new_control.add_sub_control(sub_control)
                if i == 0:
                    sub_control.set_parent(new_control)
                    maya.cmds.controller(sub_control.meta_node, new_control.meta_node, p=True)
                else:
                    sub_control.set_parent(new_control.get_sub_controls()[-2])      # index -1 it the control itself
                    maya.cmds.controller(sub_control.meta_node, new_control.get_sub_controls()[-2].meta_node, p=True)

        return new_control

    def _attach(self, control, target_transform, increment):

        if not self.attach_joints:
            return

        if self.create_sub_controls:
            control = self.get_controls()[-1]

        self._create_before_attach_joints()

        xform = control.top()
        if xform:
            offset_rotation = None
            if self.offset_rotation:
                offset_rotation = self.offset_rotation
            if increment and increment in self.increment_offset_rotation:
                offset_rotation = self.increment_offset_rotation[increment]
            if offset_rotation:
                tp.Dcc.rotate_node_in_object_space(xform, offset_rotation)

        tp.Dcc.create_parent_constraint(target_transform, control.meta_node, maintain_offset=True)
        if self.scalable:
            tp.Dcc.create_scale_constraint(target_transform, control.meta_node, maintain_offset=True)
            control.show_scale_attributes()

    def _setup(self, transforms=None):
        """
        Internal function that setup the FK chain
        :param transforms: list(str)
        """

        if transforms is None:
            transforms = self.get_buffer_joints(as_meta=True)
        if not transforms:
            tpRigToolkit.logger.warning('Impossible to create FK chain because buffer joints are not created yet!')
            return

        found_to_skip = list()

        if self.skip_increments:
            for increment in self.skip_increments:
                found_xform = None
                try:
                    found_xform = transforms[increment]
                except Exception:
                    pass
                if found_xform:
                    found_to_skip.append(found_xform)

        current_increment = 0

        for i in range(len(transforms)):
            if transforms[i] in found_to_skip:
                current_increment += 1
                continue
            current_increment = i

            fk_ctrl = self._create_control(id=current_increment)
            self._setup_increment(fk_ctrl, transforms, current_increment)

    def _setup_increment(self, ctrl, transform_list, increment):
        """
        Internal callback function that setup Fk chain taking into account the control we are working on
        :param ctrl: str
        :param transform_list: list
        :param increment: int, current index of the control in the Fk chain
        """

        self.set_transforms(transform_list, clean=True)
        current_transform = transform_list[increment]
        self._setup_all_controls(ctrl, current_transform, increment)
        if increment == 0:
            self._setup_first_control(ctrl, current_transform, increment)
        if increment == (len(transform_list) - 1):
            self._setup_last_control(ctrl, current_transform)
        if increment > 0:
            self._setup_control_greater_than_first(ctrl, current_transform, increment)
        if increment < len(transform_list):
            self._setup_control_lower_than_last(ctrl, current_transform)
        if len(transform_list) > increment > 0:
            self._setup_control_lower_than_last_and_greater_than_first(ctrl, current_transform)
        if increment == (len(transform_list) - 1) or increment == 0:
            self._setup_first_or_last_control(ctrl, current_transform)

    def _setup_all_controls(self, control, current_transform, increment):
        """
        Internal function that is called during the FK chain building process.
        This function is called once for each control in the FK chain.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        :param increment: ind, number of control in the FK chain
        """

        if self.match_to_rotation:
            tp.Dcc.match_rotation(current_transform.meta_node, control.top().meta_node)

        tp.Dcc.match_translation(current_transform.meta_node, control.top().meta_node)
        tp.Dcc.match_scale(current_transform.meta_node, control.top().meta_node)
        tp.Dcc.match_translation_to_rotate_pivot(current_transform.meta_node, control.top().meta_node)

    def _setup_first_control(self, control, current_transform, current_increment):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the first control in the FK chain.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        :param current_increment: ind, number of control in the FK chain
        """

        self._attach(control, current_transform.meta_node, current_increment)

    def _setup_last_control(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the last control in the FK chain.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        pass

    def _setup_control_greater_than_first(self, control, current_transform, current_increment):
        """
        Internal function that is called during the FK chain building process.
        This function is called for all the controls in the FK chain that are not the first one.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        self._attach(control, current_transform.meta_node, current_increment)

        controls = self.get_controls(as_meta=True)

        if self.create_sub_controls:
            parent_ctrl = controls[current_increment - 1].get_sub_controls()[-1]
        else:
            parent_ctrl = controls[current_increment - 1]
        if not parent_ctrl:
            tpRigToolkit.logger.warning('Impossible to retrieve FK Parent control for: {}'.format(control))
            return
        control.set_parent(parent_ctrl)

    def _setup_control_lower_than_last(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the FK chain controls that are lower than the last control
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        pass

    def _setup_first_or_last_control(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the FK chain controls that are lower than the last control and are not the first one
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        pass

    def _setup_control_lower_than_last_and_greater_than_first(self, control, current_transform):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the FK chain first and last controls.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        """

        pass

    def _create_before_attach_joints(self):
        """
        Internal function that is called before attaching FK joints
        Override in inherited classes
        """

        pass

    def _set_control_attributes(self, control):
        """
        Internal function that setup the attributes of the control that is going to be created
        :param control: RigControl
        """

        control.hide_scale_attributes()
