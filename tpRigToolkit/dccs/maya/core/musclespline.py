#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya Muscle Spine
"""

from __future__ import print_function, division, absolute_import

import logging
import traceback

import maya.cmds

from tpDcc import dcc
from tpDcc.dccs.maya.core import transform as transform_utils
from tpDcc.libs.qt.core import qtutils

LOGGER = logging.getLogger('tpRigToolkit-dccs-maya')


class MuscleSpline(object):
    def __init__(self, **kwargs):
        super(MuscleSpline, self).__init__()

        self._name = kwargs.pop('name', 'Char01_Spine')
        self._size = kwargs.pop('size', 1.0)
        self._insertion_controls = kwargs.pop('insertion_controls', 3)
        self._control_type = kwargs.pop('control_type', 'cube')
        self._driven_joints = kwargs.pop('driven_joints', 5)
        self._driven_type = kwargs.pop('driven_type', 'joint')
        self._constraint_mid_controls = kwargs.pop('constraint_mid_controls', False)
        self._lock_controls_scale = kwargs.pop('lock_scale', True)
        self._lock_jiggle_attributes = kwargs.pop('lock_jiggle_attributes', False)
        self._control_suffix = kwargs.pop('control_suffix', 'ctrl')
        self._joint_suffix = kwargs.pop('joint_suffix', 'jnt')
        self._group_suffix = kwargs.pop('group_suffix', 'grp')
        self._create_sets = kwargs.pop('create_sets', True)
        self._driven_suffix = kwargs.pop('driven_suffix', 'drv')
        self._main_muscle_set_name = kwargs.pop('main_muscle_set_name', 'setMUSCLERIGS')
        self._muscle_set_suffix = kwargs.pop('muslce_set_suffix', 'RIG')
        self._muscle_spline_name = kwargs.pop('muscle_spline_name', 'muscleSpline')
        self._controls_group_suffix = kwargs.pop('controls_group_suffix', 'controls')
        self._joints_group_suffix = kwargs.pop('joints_group_suffix', 'joints')
        self._root_group_suffix = kwargs.pop('root_group_suffix', 'root')
        self._auto_group_suffix = kwargs.pop('auto_group_suffix', 'auto')

        self._main_group = None
        self._spline_node = None
        self._controls_group = None
        self._controls = list()
        self._constraint_groups = list()
        self._root_groups = list()
        self._drivens_group = None
        self._drivens = list()

    @property
    def main_group(self):
        return self._main_group

    @property
    def spline_node(self):
        return self._spline_node

    @property
    def controls_group(self):
        return self._controls_group

    @property
    def root_groups(self):
        return self._root_groups

    @property
    def controls(self):
        return self._controls

    @property
    def drivens_group(self):
        return self._drivens_group

    @property
    def drivens(self):
        return self._drivens

    def create(self):
        if not maya.cmds.pluginInfo('MayaMuscle.mll', query=True, loaded=True):
            LOGGER.info('Maya Muscle Plugin is not loaded. Trying to load ...')
            try:
                maya.cmds.loadPlugin('MayaMuscle.mll')
            except Exception:
                LOGGER.error('Impossible to load Maya Muscle plugin: {}!'.format(traceback.format_exc()))
                return False

        base_name = self._name
        if not maya.cmds.objExists(self._main_muscle_set_name) and self._create_sets:
            maya.cmds.sets(name=self._main_muscle_set_name, empty=True)

        set_rig = 'set{}{}'.format(base_name, self._muscle_set_suffix)
        if not maya.cmds.objExists(set_rig) and self._create_sets:
            maya.cmds.sets(name=set_rig, empty=True)
            maya.cmds.sets(set_rig, include=self._main_muscle_set_name)

        test1 = maya.cmds.objExists('{}_{}'.format(base_name, self._muscle_spline_name))
        test2 = maya.cmds.objExists('{}_{}'.format(self._muscle_spline_name, self._group_suffix))
        if test1 or test2:
            msg = 'A muscle spline with given name "{}" already exists.' \
                  '\nPlease choose a different one.'.format(self._name)
            LOGGER.warning(msg)
            qtutils.show_warning(parent=None, title='Muscle Spline already exists!', warning=msg)
            return False

        # create main group
        self._main_group = maya.cmds.group(
            name='{}_{}_{}'.format(base_name, self._muscle_spline_name, self._group_suffix), empty=True, world=True)
        self._add_to_set(set_rig, self._main_group)

        # create spline node
        self._spline_node = maya.cmds.createNode(
            'cMuscleSpline', name='{}_{}Shape'.format(base_name, self._muscle_spline_name))
        self._spline_node_xform = maya.cmds.rename(
            maya.cmds.listRelatives(self._spline_node, parent=True, type='transform'),
            '{}_{}'.format(base_name, self._muscle_spline_name))
        maya.cmds.setAttr('{}.inheritsTransform'.format(self._spline_node_xform), False)
        for attr in ['DISPLAY', 'TANGENTS', 'LENGTH']:
            maya.cmds.setAttr('{}.{}'.format(self._spline_node, attr), lock=True)
        for xform in 'trs':
            for axis in 'xyz':
                maya.cmds.setAttr('{}.{}{}'.format(self._spline_node_xform, xform, axis), lock=True, keyable=False)
        maya.cmds.connectAttr('time1.outTime', '{}.inTime'.format(self._spline_node), force=True)
        self._add_to_set(set_rig, self._spline_node)

        # make some useful attributes of cMuscleSpline node available in channel box
        for attr in ['curLen', 'pctSquash', 'pctStretch']:
            maya.cmds.addAttr(self._spline_node, longName=attr, keyable=True)
        maya.cmds.connectAttr('{}.curLen'.format(self._spline_node), '{}.outLen'.format(self._spline_node))
        maya.cmds.connectAttr('{}.pctSquash'.format(self._spline_node), '{}.outPctSquash'.format(self._spline_node))
        maya.cmds.connectAttr('{}.pctStretch'.format(self._spline_node), '{}.outPctStretch'.format(self._spline_node))

        # create group for the controls
        self._controls_group = maya.cmds.group(
            name='{}_{}_{}'.format(
                base_name, self._muscle_spline_name, self._controls_group_suffix), empty=True, world=True)
        # maya.cmds.setAttr('{}.inheritsTransform'.format(self._controls_group), False)
        maya.cmds.parent(self._controls_group, self._main_group)
        for xform in 'trs':
            for axis in 'xyz':
                maya.cmds.setAttr('{}.{}{}'.format(self._controls_group, xform, axis), lock=True, keyable=False)
        self._add_to_set(set_rig, self._controls_group)

        # create drivens group
        self._drivens_group = maya.cmds.group(
            name='{}_{}_{}'.format(base_name, self._muscle_spline_name, self._joints_group_suffix),
            empty=True, world=True)
        maya.cmds.setAttr('{}.inheritsTransform'.format(self._drivens_group), False)
        maya.cmds.parent(self._drivens_group, self._main_group)
        for xform in 'trs':
            for axis in 'xyz':
                maya.cmds.setAttr('{}.{}{}'.format(self._drivens_group, xform, axis), lock=True, keyable=False)
        self._add_to_set(set_rig, self._drivens_group)

        # create controls
        ctrl_attrs_list = ['worldMatrix', 'tangentLength', 'jiggle', 'jiggleX', 'jiggleY', 'jiggleZ',
                           'jiggleImpact', 'jiggleImpactStart', 'jiggleImpactStop', 'cycle', 'rest']
        spline_node_attrs_list = ['insertMatrix', 'tangentLength', 'jiggle', 'jiggleX', 'jiggleY', 'jiggleZ',
                                  'jiggleImpact', 'jiggleImpactStart', 'jiggleImpactStop', 'cycle', 'rest']

        self._controls = list()
        self._constraint_groups = list()
        self._root_groups = list()
        for i in range(self._insertion_controls):
            ctrl_name = '{}_{}_{}_{}'.format(base_name, self._muscle_spline_name, i, self._control_suffix)
            new_ctrl = MuscleSplineControl(ctrl_name, self._control_type, self._size).create()
            root_grp = maya.cmds.group(
                name=ctrl_name.replace(self._control_suffix, self._root_group_suffix), empty=True, world=True)
            cns_grp = maya.cmds.group(
                name=ctrl_name.replace(self._control_suffix, self._auto_group_suffix), empty=True, world=True)
            new_ctrl.root = root_grp
            new_ctrl.auto = cns_grp
            dcc.add_message_attribute(new_ctrl.control, 'root')
            dcc.add_message_attribute(new_ctrl.control, 'auto')
            dcc.connect_message_attribute(root_grp, new_ctrl.control, 'root')
            dcc.connect_message_attribute(cns_grp, new_ctrl.control, 'auto')

            self._controls.append(new_ctrl)
            self._root_groups.append(root_grp)
            self._constraint_groups.append(cns_grp)

            # place controls and its groups vertically on Y axis
            for xform_node in [new_ctrl.control, root_grp, cns_grp]:
                maya.cmds.xform(xform_node, translation=(0, i * self._size, 0), absolute=True, worldSpace=True)

            maya.cmds.parent(new_ctrl.control, cns_grp)
            maya.cmds.parent(cns_grp, root_grp)
            maya.cmds.parent(root_grp, self._controls_group)

            # color controls (yellow)
            ctrl_shapes = maya.cmds.listRelatives(new_ctrl.control, shapes=True) or list()
            for ctrl_shape in ctrl_shapes:
                maya.cmds.setAttr('{}.overrideEnabled'.format(ctrl_shape), True)
                maya.cmds.setAttr('{}.overrideColor'.format(ctrl_shape), 17)

            # make middle controls jiggle by default
            jiggle = 1.0
            if i == 0 or i == (self._insertion_controls - 1):
                jiggle = 0.0

            maya.cmds.addAttr(
                new_ctrl.control, longName='tangentLength', shortName='tanlen', minValue=0.0, dv=1.0, k=True)
            maya.cmds.addAttr(new_ctrl.control, longName='jiggle', shortName='jig', defaultValue=jiggle, keyable=True)
            maya.cmds.addAttr(new_ctrl.control, longName='jiggleX', shortName='jigX', defaultValue=jiggle, keyable=True)
            maya.cmds.addAttr(new_ctrl.control, longName='jiggleY', shortName='jigY', defaultValue=jiggle, keyable=True)
            maya.cmds.addAttr(new_ctrl.control, longName='jiggleZ', shortName='jigZ', defaultValue=jiggle, keyable=True)
            maya.cmds.addAttr(new_ctrl.control, longName='jiggleImpact', shortName='jigimp', dv=(0.5 * jiggle), k=True)
            maya.cmds.addAttr(new_ctrl.control, longName='jiggleImpactStart', shortName='jigimpst', dv=1000, k=True)
            maya.cmds.addAttr(new_ctrl.control, longName='jiggleImpactStop', shortName='jigimpsp', dv=0.001, k=True)
            maya.cmds.addAttr(new_ctrl.control, longName='cycle', shortName='cyc', minValue=1.0, dv=12.0, k=True)
            maya.cmds.addAttr(new_ctrl.control, longName='rest', shortName='rst', minValue=1.0, dv=24.0, k=True)
            for attr in ['tangentLength', 'jiggle', 'jiggleX', 'jiggleX', 'jiggleY', 'jiggleZ', 'jiggleImpact',
                         'jiggleImpactStart', 'jiggleImpactStop', 'cycle', 'rest']:
                maya.cmds.setAttr('{}.{}'.format(new_ctrl.control, attr), lock=self._lock_jiggle_attributes)

            if self._lock_controls_scale:
                for xform in ['s']:
                    for axis in ['x', 'y', 'z']:
                        maya.cmds.setAttr('{}.{}{}'.format(new_ctrl.control, xform, axis), lock=True, keyable=False)
            maya.cmds.setAttr('{}.visibility'.format(new_ctrl.control), lock=True, keyable=False)

            # connect attributes
            ctrl_attrs = ['{}.{}'.format(new_ctrl.control, attr) for attr in ctrl_attrs_list]
            spline_node_attrs = [
                '{}.controlData[{}].{}'.format(self._spline_node, i, attr) for attr in spline_node_attrs_list]
            for ctrl_attr, spline_node_attr in zip(ctrl_attrs, spline_node_attrs):
                maya.cmds.connectAttr(ctrl_attr, spline_node_attr)

        # for each in-between control (not in the start and end control) we will use the constraint group above it
        # and constraint it to the top and bottom groups. Doing this, mid controls will follow top and end controls.
        # Also, we will aim constraints so in-between controls always aim start and end controls
        blend = ''

        if self._constraint_mid_controls:
            for i in range(1, self._insertion_controls - 1):
                # get point constraint weight and create point constraint for intermediate controls
                pct = 1.0 * i / (self._insertion_controls - 1.0)
                maya.cmds.pointConstraint(self._controls[0].control, self._constraint_groups[i], weight=(1.0 - pct))
                maya.cmds.pointConstraint(
                    self._controls[self._insertion_controls - 1].control, self._constraint_groups[i], weight=pct)

                # create aim groups
                # we create one for the forward aim and another one for the back aim, then we have to orient between
                # both at the right amount
                grp_aim_fwd = maya.cmds.group(
                    name='{}_aimFwd_{}_{}'.format(base_name, i, self._group_suffix), empty=True, world=True)
                grp_aim_bck = maya.cmds.group(
                    name='{}_aimBack_{}_{}'.format(base_name, str(i), self._group_suffix), empty=True, world=True)
                for grp in [grp_aim_fwd, grp_aim_bck]:
                    transform_utils.match_translation(grp, self._controls[i].control)
                self._add_to_set(set_rig, [self._root_groups[i], grp_aim_fwd, grp_aim_bck])

                # aim forward group will aim the last control and aim Back group will aim to the first control this
                # will give a twist behaviour on the aim groups
                a_constraint = maya.cmds.aimConstraint(
                    self._controls[self._insertion_controls - 1].control, grp_aim_fwd, weight=1, aimVector=(0, 1, 0),
                    upVector=(1, 0, 0), worldUpVector=(1, 0, 0), worldUpType="objectrotation",
                    worldUpObject=self._controls[self._insertion_controls - 1].control)[0]
                b_constraint = maya.cmds.aimConstraint(
                    self._controls[0].control, grp_aim_bck, weight=1, aimVector=(0, -1, 0), upVector=(1, 0, 0),
                    worldUpVector=(1, 0, 0), worldUpType="objectrotation", worldUpObject=self._controls[0].control)[0]
                self._add_to_set(set_rig, [a_constraint, b_constraint])

                # now we drive the aims with the up info (we do this, only once) ...
                if i == 1:
                    # make sure that the up axis attribute exists on  the cMuscleNode ...
                    if not maya.cmds.objExists('{}.upAxis'.format(self._spline_node)):
                        maya.cmds.addAttr(
                            self._spline_node, at="enum", longName="upAxis", enumName="X-Axis=0:Z-Axis=1", keyable=True)

                    # use this blend to select the return the Z axis (vector 0,0,1) or X axis (vector 1,0,0)
                    blend = maya.cmds.createNode(
                        'blendColors', name='{}_{}_AimBlend'.format(base_name, self._muscle_spline_name))
                    maya.cmds.connectAttr('{}.upAxis'.format(self._spline_node), '{}.blender'.format(blend))
                    maya.cmds.setAttr('{}.color1'.format(blend), 0, 0, 1)
                    maya.cmds.setAttr('{}.color2'.format(blend), 1, 0, 0)
                    self._add_to_set(set_rig, blend)

                # each aim constraint up vector will follow the up axis attribute of the cMuscleSpineNode
                # we can switch between Z or X up axis if you get flipping when rotating controls
                for cons in [a_constraint, b_constraint]:
                    maya.cmds.connectAttr('{}.output'.format(blend), '{}.upVector'.format(cons))
                    maya.cmds.connectAttr('{}.output'.format(blend), '{}.worldUpVector'.format(cons))

                # aim groups also will follow start and end controls (so it will be positioned at the same
                # position of its respective control)
                p_cons_fwd1 = maya.cmds.pointConstraint(self._controls[0].control, grp_aim_fwd, weight=(1.0 - pct))[0]
                p_cons_fwd2 = maya.cmds.pointConstraint(
                    self._controls[self._insertion_controls - 1].control, grp_aim_fwd, weight=pct)[0]
                p_cons_back1 = maya.cmds.pointConstraint(self._controls[0].control, grp_aim_bck, weight=(1.0 - pct))[0]
                p_cons_back2 = maya.cmds.pointConstraint(
                    self._controls[self._insertion_controls - 1].control, grp_aim_bck, weight=pct)[0]
                self._add_to_set(set_rig, [p_cons_fwd1, p_cons_fwd2, p_cons_back1, p_cons_back2])

                # auto groups will follow the orientation of the aim groups. So, the controls (which are child of
                # the auto groups) will follow the aim orientation
                o_cons_bck = maya.cmds.orientConstraint(grp_aim_bck, self._constraint_groups[i], weight=(1.0 - pct))[0]
                maya.cmds.setAttr('{}.interpType'.format(o_cons_bck), 2)
                o_cons_fwd = maya.cmds.orientConstraint(grp_aim_fwd, self._constraint_groups[i], weight=pct)[0]
                maya.cmds.setAttr('{}.interpType'.format(o_cons_fwd), 2)
                self._add_to_set(set_rig, [o_cons_bck, o_cons_fwd])

                # create root grops for each one of the aim groups (so its xfrorms are zeroed out)
                grp_aim_fwd_root = maya.cmds.group(
                    name='{}_{}_grpAimFwd_{}'.format(base_name, self._muscle_spline_name, self._root_group_suffix),
                    empty=True, world=True)
                grp_aim_bck_root = maya.cmds.group(
                    name='{}_{}_grpAimBck_{}'.format(base_name, self._muscle_spline_name, self._root_group_suffix),
                    empty=True, world=True)
                transform_utils.match_translation(grp_aim_fwd_root, grp_aim_fwd)
                transform_utils.match_translation(grp_aim_bck_root, grp_aim_bck)
                self._add_to_set(set_rig, [grp_aim_fwd_root, grp_aim_bck_root])

                maya.cmds.parent(grp_aim_fwd, grp_aim_fwd_root)
                maya.cmds.parent(grp_aim_bck, grp_aim_fwd_root)
                maya.cmds.parent(grp_aim_fwd_root, self._root_groups[i])
                maya.cmds.parent(grp_aim_bck_root, self._root_groups[i])

        self._drivens = list()
        for i in range(self._driven_joints):
            # get normalized values between 0 and 1 and the correct name
            u = i / (self._driven_joints - 1.0)
            name = '{}_{}_{}_{}'.format(base_name, self._muscle_spline_name, i, self._driven_suffix)
            if self._driven_type == "joint":
                self._drivens.append(maya.cmds.joint(name=name))
            elif self._driven_type == "circleY":
                ctrl = maya.cmds.circle(
                    name=name, degree=3, center=[0, 0, 0], normal=[0, 1, 0], sweep=360, radius=1.0 * self._size,
                    useTolerance=False, sections=8, constructionHistory=False)[0]
                self._drivens.append(ctrl)
            else:
                self._drivens.append(maya.cmds.group(name=name, empty=True, world=True))

            maya.cmds.select(clear=True)
            maya.cmds.addAttr(self._drivens[i], longName="uValue", minValue=0.0, maxValue=1.0, defaultValue=u, k=True)
            maya.cmds.parent(self._drivens[i], self._drivens_group)
            self._add_to_set(set_rig, self._drivens[i])
            maya.cmds.connectAttr(
                '{}.uValue'.format(self._drivens[i]),
                '{}.readData[{}].readU'.format(self._spline_node, i), force=True)
            maya.cmds.connectAttr(
                '{}.rotateOrder'.format(self._drivens[i]),
                '{}.readData[{}].readRotOrder'.format(self._spline_node, i), force=True)
            maya.cmds.connectAttr(
                '{}.outputData[{}].outTranslate'.format(self._spline_node, i),
                '{}.translate'.format(self._drivens[i]))
            maya.cmds.connectAttr(
                '{}.outputData[{}].outRotate'.format(self._spline_node, i),
                '{}.rotate'.format(self._drivens[i]))

        spline_length = maya.cmds.getAttr('{}.outLen'.format(self._spline_node))
        maya.cmds.setAttr('{}.lenDefault'.format(self._spline_node), spline_length)
        maya.cmds.setAttr('{}.lenSquash'.format(self._spline_node), spline_length * 0.5)
        maya.cmds.setAttr('{}.lenStretch'.format(self._spline_node), spline_length * 2.0)

        # TODO: If lock control scale is not enabled we should automatically sclae constraint drivens to controls
        # TODO: We should handle all scenarios (same amount of both,
        #  more controls than drivens and more drivens than controls)
        # if not self._lock_controls_scale:
        #     for ctrl, jnt in zip(self._controls, self._drivens):

        maya.cmds.select(self._main_group)

        return self._spline_node

    def _add_to_set(self, set_name, objects_to_add):
        if not self._create_sets:
            return

        maya.cmds.sets(objects_to_add, include=set_name)


class MuscleSplineControl(object):
    def __init__(self, name, type, size):
        super(MuscleSplineControl, self).__init__()

        self._name = name
        self._type = type
        self._size = size

        self._ctrl = None
        self._root = None
        self._auto = None

    @property
    def control(self):
        return self._ctrl

    @property
    def root(self):
        return self._root

    @root.setter
    def root(self, node):
        self._root = node

    @property
    def auto(self):
        return self._auto

    @auto.setter
    def auto(self, node):
        self._auto = node

    def create(self):
        self._ctrl = None
        self._root = None
        self._auto = None

        if self._type == 'cube':
            ctrl_def_size = 0.25 * self._size
            self._ctrl = maya.cmds.curve(
                name=self._name,
                degree=1,
                point=[(-ctrl_def_size, ctrl_def_size, ctrl_def_size), (ctrl_def_size, ctrl_def_size, ctrl_def_size),
                       (ctrl_def_size, ctrl_def_size, -ctrl_def_size), (-ctrl_def_size, ctrl_def_size, -ctrl_def_size),
                       (-ctrl_def_size, ctrl_def_size, ctrl_def_size), (-ctrl_def_size, -ctrl_def_size, ctrl_def_size),
                       (-ctrl_def_size, -ctrl_def_size, -ctrl_def_size),
                       (ctrl_def_size, -ctrl_def_size, -ctrl_def_size), (ctrl_def_size, -ctrl_def_size, ctrl_def_size),
                       (-ctrl_def_size, -ctrl_def_size, ctrl_def_size), (ctrl_def_size, -ctrl_def_size, ctrl_def_size),
                       (ctrl_def_size, ctrl_def_size, ctrl_def_size), (ctrl_def_size, ctrl_def_size, -ctrl_def_size),
                       (ctrl_def_size, -ctrl_def_size, -ctrl_def_size),
                       (-ctrl_def_size, -ctrl_def_size, -ctrl_def_size),
                       (-ctrl_def_size, ctrl_def_size, -ctrl_def_size)],
                knot=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
        elif self._type == 'circleY':
            self._ctrl = maya.cmds.circle(
                name=self._name, degree=3, center=[0, 0, 0], normal=[0, 1, 0], sweep=360, radius=0.25 * self._size,
                useTolerance=False, sections=8, constructionHistory=False)[0]
        elif self._type == 'null':
            self._ctrl = maya.cmds.group(name=self._name, empty=True, world=True)

        return self

    def zero_out_jiggle_attributes(self):
        """
        Zero out all jiggle attributes of the muscleSpline control
        """

        for attr in ['jiggle', 'jiggleX', 'jiggleX', 'jiggleY', 'jiggleZ', 'jiggleImpact']:
            maya.cmds.setAttr('{}.{}'.format(self._ctrl, attr), 0.0)

    def lock_and_hide_jiggle_attributes(self):
        for attr in ['tangentLength', 'jiggle', 'jiggleX', 'jiggleX', 'jiggleY', 'jiggleZ', 'jiggleImpact',
                     'jiggleImpactStart', 'jiggleImpactStop', 'cycle', 'rest']:
            maya.cmds.setAttr('{}.{}'.format(self._ctrl, attr), lock=True, keyable=False)
            maya.cmds.setAttr('{}.{}'.format(self._ctrl, attr), channelBox=False)
