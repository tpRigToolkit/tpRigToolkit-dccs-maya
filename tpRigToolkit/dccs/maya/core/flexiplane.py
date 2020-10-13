#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Flexi Rig setup
"""

from __future__ import print_function, division, absolute_import

import tpDcc as tp

import tpRigToolkit


class FlexiRig(object):
    def __init__(self, **kwargs):
        super(FlexiRig, self).__init__()

        self._naming_file = None
        self._rule_name = 'node'

        self._top_group = None
        self._global_move_group = None
        self._no_xform_group = None

    def create(self):
        tp.Dcc.clear_selection()

        self._create_groups()

    def _create_groups(self):
        """
        Internal function that creates basic group hierarchy for the flexi rig setup
        """
        
        self._top_group = tp.Dcc.create_empty_group(name=self._get_name('flexiRoot', node_type='group'))
        tp.Dcc.lock_translate_attributes(self._top_group)
        tp.Dcc.lock_rotate_attributes(self._top_group)
        tp.Dcc.lock_scale_attributes(self._top_group)

        self._global_move_group = tp.Dcc.create_empty_group(name=self._get_name('globalMove', node_type='group'))
        tp.Dcc.set_parent(self._global_move_group, self._top_group)

        self._no_xform_group = tp.Dcc.create_empty_group(name=self._get_name('noXForm', node_type='group'))
        tp.Dcc.disable_transforms_inheritance(self._no_xform_group, lock=True)
        tp.Dcc.hide_node(self._no_xform_group)
        tp.Dcc.lock_translate_attributes(self._top_group)
        tp.Dcc.lock_rotate_attributes(self._top_group)
        tp.Dcc.lock_scale_attributes(self._top_group)
        tp.Dcc.set_parent(self._no_xform_group, self._top_group)

    def _get_name(self, *args, **kwargs):
        return tpRigToolkit.NamesMgr().solve_name(
            naming_file=self._naming_file, rule_name=self._rule_name, *args, **kwargs)

