#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains data Maya Skin Cluster weights widget
"""

from __future__ import print_function, division, absolute_import

from tpDcc.dccs.maya.data import skin as maya_skin

from tpRigToolkit.core import data


class MayaSkinClusterWeightsPreivewWidget(data.DataPreviewWidget, object):
    def __init__(self, item, parent=None):
        super(MayaSkinClusterWeightsPreivewWidget, self).__init__(item=item, parent=parent)


class MayaSkinClusterWeights(data.DataItem, object):

    Extension = '.{}'.format(maya_skin.SkinWeightsData.get_data_extension())
    Extensions = ['.{}'.format(maya_skin.SkinWeightsData.get_data_extension())]
    MenuName = maya_skin.SkinWeightsData.get_data_title()
    MenuOrder = 4
    MenuIconPath = 'skin_weights_data.png'
    TypeIconPath = 'skin_weights_data.png'
    DataType = maya_skin.SkinWeightsData.get_data_type()
    PreviewWidgetClass = MayaSkinClusterWeightsPreivewWidget

    def __init__(self, *args, **kwargs):
        super(MayaSkinClusterWeights, self).__init__(*args, **kwargs)

        self.set_data_class(maya_skin.SkinWeightsData)
