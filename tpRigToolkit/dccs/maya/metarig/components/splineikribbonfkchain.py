#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Spline Ik & Ribbon Fk Chain implementation for metarig in Maya

Custom Fk chain implementation intended to be used along a Spline Ik or Nurbs Ribbon setup
"""

from tpDcc import dcc
from tpDcc.dccs.maya.core import transform as xform_utils

from tpRigToolkit.dccs.maya.metarig.components import fkchain


class SplineIkRibbonFkChainComponent(fkchain.FkChainComponent, object):
    def __init__(self, *args, **kwargs):
        super(SplineIkRibbonFkChainComponent, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_name(kwargs.get('name', 'spilneIkChainFk'))
        self.set_attach_joints(False)
        self.set_create_buffer_joints(False)
        self.set_orient_controls_to_joints(False)
        self.set_first_control(None)
        self.set_top_sub_control(None)
        self.set_skip_first_control(False)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def _setup(self, transforms=None):
        """
        Internal function that setup the FK chain
        :param transforms: list(str)
        """

        transforms = self.get_handlers(as_meta=True)
        super(SplineIkRibbonFkChainComponent, self)._setup(transforms=transforms)

    def _setup_all_controls(self, control, current_transform, increment):
        """
        Internal function that is called during the FK chain building process.
        This function is called once for each control in the FK chain.
        This function can be override to implement custom FK chain behaviours
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        :param increment: ind, number of control in the FK chain
        """

        match = xform_utils.MatchTransform(current_transform.meta_node, control.top().meta_node)
        match.translation_to_rotate_pivot()

        if self.orient_controls_to_joints:
            if not self.orient_joint:
                jnt = self._get_closest_joint(increment)
            else:
                jnt = self.orient_joint[0]

            match = xform_utils.MatchTransform(jnt, current_transform.meta_node)
            match.rotation()

        cls_cmp = self.get_handlers()

        if self.create_sub_controls:
            sub_ctrl = control.get_sub_controls()[-1]
            dcc.create_parent_constraint(cls_cmp[increment], sub_ctrl.meta_node, maintain_offset=True)
        else:
            dcc.create_parent_constraint(cls_cmp[increment], control.meta_node, maintain_offset=True)

    def _setup_first_control(self, control, current_transform, current_increment):
        """
        Internal function that is called during the FK chain building process.
        This function is called for the first control in the FK chain.
        :param control: str, name of the control in the FK chain
        :param current_transform: str, transform linked to the given Fk chain control
        :param current_increment: ind, number of control in the FK chain
        """

        first_control = self.get_controls()[0]
        self.set_first_control(first_control)
        if self.skip_first_control:
            first_control.delete_shapes()

        if self.create_sub_controls:
            top_sub_control = self.get_sub_controls()[0]
            self.set_top_sub_control(top_sub_control)
            if self.skip_first_control:
                top_sub_control.delete_shapes()

    def _setup_last_control(self, control, current_transform):
        """
         Internal function that is called during the FK chain building process.
         This function is called for the last control in the FK chain.
         :param control: str, name of the control in the FK chain
         :param current_transform: str, transform linked to the given Fk chain control
         """

        if not self.create_sub_controls:
            return

        if self.create_follows:
            pass

    # def _setup_control_greater_than_first(self, control, current_transform, current_increment):
    #     """
    #     Internal function that is called during the FK chain building process.
    #     This function is called for all the controls in the FK chain that are not the first one.
    #     :param control: str, name of the control in the FK chain
    #     :param current_transform: str, transform linked to the given Fk chain control
    #     """
    #
    #     pass

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def set_buffer_joints(self, buffer_joints, clean=True):
        """
        Sets the buffer joints used by this component
        :param buffer_joints:
        :param clean: bool
        :return:
        """

        if not self.message_list_get('buffer_joints', as_meta=False):
            self.message_list_connect('buffer_joints', buffer_joints)
        else:
            if clean:
                self.message_list_purge('buffer_joints')
            for buffer_joint in buffer_joints:
                self.message_list_append('buffer_joints', buffer_joint)

    def set_handlers(self, handlers, clean=True):
        """
        Sets the clusters used by Spline Ik FK chain component
        :param handlers:
        :param clean: bool
        :return:
        """

        if not self.message_list_get('handlers', as_meta=False):
            self.message_list_connect('handlers', handlers)
        else:
            if clean:
                self.message_list_purge('handlers')
            for handler in handlers:
                self.message_list_append('handlers', handler)

    def get_handlers(self, as_meta=False):
        """
        Returns handlers objects
        :return:
        """

        return self.message_list_get('handlers', as_meta=as_meta)

    def set_orient_controls_to_joints(self, flag):
        """
        Sets whether controls orientation should be matched to nearest joint
        :param flag: bool
        """

        if not self.has_attr('orient_controls_to_joints'):
            self.add_attribute(attr='orient_controls_to_joints', value=flag)
        else:
            self.orient_controls_to_joints = flag

    def set_first_control(self, control):
        """
        Sets which is the first control used by this rig
        :param control:
        :return:
        """

        if not self.has_attr('first_control'):
            self.add_attribute(attr='first_control', value=control, attr_type='messageSimple')
        else:
            self.first_control = control

    def set_top_sub_control(self, control):
        """
        Sets which is the top sub control used by this rig
        :param control:
        :return:
        """

        if not self.has_attr('top_sub_control'):
            self.add_attribute(attr='top_sub_control', value=control, attr_type='messageSimple')
        else:
            self.top_sub_control = control

    def set_skip_first_control(self, flag):
        """
        Sets if first control should be skipped or not
        :param flag: bool
        """

        if not self.has_attr('skip_first_control'):
            self.add_attribute(attr='skip_first_control', value=flag)
        else:
            self.skip_first_control = flag

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _get_closest_joint(self, increment):
        handlers = self.get_handlers()
        current_handler = handlers[increment]

        return xform_utils.get_closest_transform(current_handler, self.get_buffer_joints(as_meta=False))

    def _create_sub_control(self, id=None):
        """
        Internal function that creates a sub control for this rig component
        :return: RigControl
        """

        sub_control = self._create_control(sub=True, id=id)

        return sub_control
