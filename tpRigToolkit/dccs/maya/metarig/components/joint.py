#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains joint rig metarig implementations for Maya
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.python import python

from tpRigToolkit.dccs.maya.metarig.core import component


class JointRig(component.RigComponent, object):

    def __init__(self, *args, **kwargs):
        super(JointRig, self).__init__(*args, **kwargs)

        if self.cached:
            return

        self.set_attach_joints(True)

    def set_attach_joints(self, flag):
        """
        Sets whether joints should be attached to rig module controls or not
        :param flag: bool
        """

        if not self.has_attr('attach_joints'):
            self.add_attribute(attr='attach_joints', value=flag)
        else:
            self.attach_joints = flag

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

    def _check_joint(self, jnt):
        """
        Internal function used to check the validity of the given joints
        :param jnt: list
        """

        if not jnt:
            self.logger.warning('No joint to check')
            return False

        if not jnt or not jnt.node_type() == 'joint':
            self.logger.warning('Joint: "{}" is not valid!'.format(jnt))
            return False

        return True



