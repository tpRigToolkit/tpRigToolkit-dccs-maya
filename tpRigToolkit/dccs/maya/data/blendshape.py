#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains data Maya BlenShape weights widget
"""

from __future__ import print_function, division, absolute_import

import os
from collections import OrderedDict

import tpDcc as tp
from tpDcc.libs.python import folder, fileio, name as name_utils, path as path_utils
import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.data import base
from tpDcc.dccs.maya.core import decorators, geometry, curve, deformer, blendshape as bs_utils

from tpRigToolkit.core import data


class BlendShapeWeightsData(base.MayaCustomData, object):
    def __init__(self, name=None, path=None):
        super(BlendShapeWeightsData, self).__init__(name=name, path=path)

    @staticmethod
    def get_data_type():
        return 'maya.blendshape_weights'

    @staticmethod
    def get_data_extension():
        return 'bsw'

    @staticmethod
    def get_data_title():
        return 'BlendShape Weights'

    def export_data(self, file_path=None, comment='-', create_version=True, *args, **kwargs):

        if not tp.is_maya():
            maya.logger.warning('Data must be exported from within Maya!')
            return False

        file_path = file_path or self.get_file()

        file_folder = os.path.dirname(file_path)

        meshes = geometry.get_selected_meshes()
        curves = curve.get_selected_curves()
        surfaces = geometry.get_selected_surfaces()
        meshes.extend(curves)
        meshes.extend(surfaces)

        blendshapes_found = list()
        for mesh in meshes:
            blendshapes = deformer.find_deformer_by_type(mesh, 'blendShape', return_all=True) or list()
            blendshapes_found.extend(blendshapes)
        if not blendshapes_found:
            maya.logger.warning('No blendshapes to export')
            return

        for blendshape_name in blendshapes_found:
            blendshape = bs_utils.BlendShape(blendshape_name)
            mesh_count = blendshape.get_mesh_count()
            targets = blendshape.get_target_names()

            blendshape_path = folder.create_folder(blendshape_name, file_path)

            for target in targets:
                target_path = folder.create_folder(str(target), blendshape_path)
                for i in range(mesh_count):
                    weights = blendshape.get_weights()
                    target_mesh_weights_file_name = fileio.create_file('mesh_{}.weights'.format(i), target_path)
                    fileio.write_lines(target_mesh_weights_file_name, [weights])

            for i in range(mesh_count):
                weights = blendshape.get_weights(mesh_index=i)
                base_mesh_weights_file_name = fileio.create_file('base_{}.weights'.format(i), blendshape_path)
                fileio.write_lines(base_mesh_weights_file_name, [weights])

        maya.logger.info('BlendShape export operation completed successfully!')

        version = fileio.FileVersion(file_folder)
        version.save(comment)

        return True

    @decorators.undo_chunk
    def import_data(self, file_path='', objects=None):
        if not tp.is_maya():
            maya.logger.warning('Data must be exported from within Maya!')
            return False

        file_path = file_path or self.get_file()
        if not file_path or not os.path.isdir(file_path):
            maya.logger.warning('Impossible to import blendShape weights from: "{}"'.format(file_path))
            return False

        folders = folder.get_folders(file_path)

        for folder_found in folders:
            if tp.Dcc.object_exists(folder_found) and tp.Dcc.node_type(folder_found) == 'blendShape':
                blendshape_folder = folder_found
                blendshape_path = path_utils.join_path(file_path, folder_found)
                base_files = folder.get_files_with_extension('weights', blendshape_path)
                for file_name in base_files:
                    if file_name.startswith('base'):
                        file_path = path_utils.join_path(blendshape_path, file_name)
                        lines = fileio.get_file_lines(file_path)
                        weights = eval(lines[0])
                        index = name_utils.get_last_number(file_name)
                        blendshape = bs_utils.BlendShape(blendshape_folder)
                        blendshape.set_weights(weights, mesh_index=index)

                targets = folder.get_folders(blendshape_path)
                for target in targets:
                    if maya.cmds.objExists('{}.{}'.format(blendshape_folder, target)):
                        target_path = path_utils.join_path(blendshape_path, target)
                        files = folder.get_files_with_extension('weights', target_path)
                        for file_name in files:
                            if file_name.startswith('mesh'):
                                file_path = path_utils.join_path(target_path, file_name)
                                lines = fileio.get_file_lines(file_path)
                                weights = eval(lines[0])
                                index = name_utils.get_last_number(file_name)
                                blendshape = bs_utils.BlendShape(blendshape_folder)
                                blendshape.set_weights(weights, target, mesh_index=index)

        self._center_view()

        maya.logger.info('Imported "{}" BlendShape data'.format(self.name))

        return True


class MayaBlendShapeWeightsPreviewWidget(data.DataPreviewWidget, object):
    def __init__(self, item, parent=None):
        super(MayaBlendShapeWeightsPreviewWidget, self).__init__(item=item, parent=parent)

        self._export_btn.setText('Save')
        self._export_btn.setVisible(True)
        self._load_btn.setVisible(False)


class MayaBlendShapeWeights(data.DataItem, object):

    Extension = '.{}'.format(BlendShapeWeightsData.get_data_extension())
    Extensions = ['.{}'.format(BlendShapeWeightsData.get_data_extension())]
    MenuName = BlendShapeWeightsData.get_data_title()
    MenuOrder = 10
    MenuIconName = 'blendshape_weights_data.png'
    TypeIconPath = 'blendshape_weights_data.png'
    DataType = BlendShapeWeightsData.get_data_type()
    PreviewWidgetClass = MayaBlendShapeWeightsPreviewWidget

    def __init__(self, *args, **kwargs):
        super(MayaBlendShapeWeights, self).__init__(*args, **kwargs)

        self.set_data_class(BlendShapeWeightsData)


class SHAPESBlendShapeData(base.MayaCustomData, object):
    def __init__(self, name=None, path=None):
        super(SHAPESBlendShapeData, self).__init__(name=name, path=path)

    @staticmethod
    def get_data_type():
        return 'maya.shapes_data'

    @staticmethod
    def get_data_extension():
        return 'shapes'

    @staticmethod
    def get_data_title():
        return 'SHAPES BlendShapes Data'

    def export_data(self, file_path=None, comment='-', create_version=True, *args, **kwargs):

        if not tp.is_maya():
            maya.logger.warning('Data must be exported from within Maya!')
            return False

        if not tp.Dcc.is_plugin_loaded('SHAPESTools'):
            valid_load = tp.Dcc.load_plugin('SHAPESTools')
            if not valid_load:
                maya.logger.warning('Shapes is not installed. Impossible to export SHAPES data.')
                return False
        if not tp.Dcc.is_plugin_loaded('weightDriver'):
            tp.Dcc.load_plugin('weightDriver')

        # We force the load of SHAPES scripts
        for shape_script in [
            'SHAPES_vars', 'SHAPES_actions', 'SHAPES_array', 'SHAPES_animation', 'SHAPES_combo', 'SHAPES_common',
            'SHAPES_data', 'SHAPES_driver', 'SHAPES_global', 'SHAPES_jobs', 'SHAPES_list', 'SHAPES_main',
            'SHAPES_mirror', 'SHAPES_regions', 'SHAPES_sculpt', 'SHAPES_set', 'SHAPES_ui', 'SHAPES_utilities',
            'SHAPES_weights', 'SHAPES_poseInterpolator', 'SHAPES_uiWorkspaceControl']:
            try:
                maya.mel.eval('{};'.format(shape_script))
            except Exception as exc:
                pass

        file_path = file_path or self.get_file()

        file_folder = os.path.dirname(file_path)

        meshes = geometry.get_selected_meshes()
        curves = curve.get_selected_curves()
        surfaces = geometry.get_selected_surfaces()
        meshes.extend(curves)
        meshes.extend(surfaces)

        if not meshes:
            maya.logger.warning('No meshes to export')
            return False

        blendshapes_found = list()
        blendshapes_map = OrderedDict()
        for mesh in meshes:
            blendshapes = deformer.find_deformer_by_type(mesh, 'blendShape', return_all=True) or list()
            if not blendshapes:
                continue
            valid_blendshapes = list()
            for blend in blendshapes:
                if blend in blendshapes_found:
                    maya.logger.warning(
                        'BlendShape node with name "{0}" already retrieved. Skipping '
                        'blendShape node "{0}" from mesh "{1}"'.format(blend, mesh))
                    continue
                valid_blendshapes.append(blend)
            blendshapes_found.extend(blendshapes)
            blendshapes_map[mesh] = valid_blendshapes

        if not blendshapes_found:
            maya.logger.warning('No blendshapes to export')
            return

        for mesh_name, blendshapes in blendshapes_map.items():
            mesh_folder = folder.create_folder(mesh_name, file_path)
            for blendshape_name in blendshapes:
                blendshape = bs_utils.BlendShape(blendshape_name)
                targets = blendshape.get_target_names()
                if not targets:
                    maya.logger.warning(
                        'Skipping export of blendShape "{}" in mesh "{}" because no targets found!'.format(
                            blendshape_name, mesh_name))
                    continue
                blendshape_path = folder.create_folder(blendshape_name, mesh_folder)

                maya.mel.eval('SHAPES;')
                maya.cmds.select(mesh_name)
                maya.mel.eval('shapesMain_getMeshSelection 1;')
                maya.cmds.optionVar(iv=('SHAPESUseCustomDataPath', 1), sv=('SHAPESCustomDataPath', blendshape_path))
                maya.cmds.optionVar(iv=('SHAPESUseCustomNodeDataExportPath', 0))
                maya.mel.eval('optionMenu -e -v "{}" shpUI_bsOption'.format(blendshape_name))
                maya.mel.eval('shapesUtil_exportShapeSetup 1 "{}" ""'.format(blendshape_path))

                # This does not exports the blendShape data
                # maya.mel.eval('shapesUtil_exportShapeSetup 1 "{}" "{}"'.format(blendshape_path, blendshape_name))

        maya.logger.info('SHAPES BlendShape data export operation completed successfully!')

        version = fileio.FileVersion(file_folder)
        version.save(comment)

        return True

    @decorators.undo_chunk
    def import_data(self, file_path='', objects=None):
        if not tp.is_maya():
            maya.logger.warning('Data must be exported from within Maya!')
            return False

        file_path = file_path or self.get_file()
        if not file_path or not os.path.isdir(file_path):
            maya.logger.warning('Impossible to import SHAPES blendShape weights from: "{}"'.format(file_path))
            return False

        folders = folder.get_folders(file_path)

        for mesh_name in folders:
            if not tp.Dcc.object_exists(mesh_name):
                maya.logger.warning(
                    'Skipping blendShapes data import for mesh "{}". No mesh with than '
                    'name found in current scene!'.format(mesh_name))
                continue

            mesh_folder = os.path.join(file_path, mesh_name)
            blendshape_folders = folder.get_folders(mesh_folder)
            for blendshape_folder in blendshape_folders:
                mel_shape_file = os.path.join(
                    mesh_folder, blendshape_folder, '{}.mel'.format(blendshape_folder))
                if not os.path.isfile(mel_shape_file):
                    maya.logger.warning(
                        'Skipping blendShape "{}" data import . No SHAPES blendShape MEL file found: "{}"'.format(
                            blendshape_folder, mel_shape_file))
                    continue
                mel_shape_file = mel_shape_file.replace('\\', '/')

                if tp.Dcc.object_exists(blendshape_folder):
                    # TODO: Instead of skipping we should remove that blendShape
                    maya.logger.warning(
                        'Skipping blendShape "{0}" data import. BlendShape node with '
                        'name already in scene'.format(blendshape_folder))
                    continue

                maya.cmds.select(mesh_name)
                maya.mel.eval('SHAPES;')
                maya.mel.eval('shapesMain_getMeshSelection 1;')
                maya.cmds.refresh()
                maya.mel.eval('shapesUtil_performImportShapeSetup "{}"'.format(mel_shape_file))
                maya.cmds.select(mesh_name)
                maya.mel.eval('shapesMain_getMeshSelection 1;')

        self._center_view()

        maya.logger.info('Imported "{}" SHAPES BlendShape data'.format(self.name))

        return True


class MayaSHAPESBlendShapeWeightsPreviewWidget(data.DataPreviewWidget, object):
    def __init__(self, item, parent=None):
        super(MayaSHAPESBlendShapeWeightsPreviewWidget, self).__init__(item=item, parent=parent)

        self._export_btn.setText('Save')
        self._export_btn.setVisible(True)
        self._load_btn.setVisible(False)


class MayaSHAPESBlendShapeWeights(data.DataItem, object):

    Extension = '.{}'.format(SHAPESBlendShapeData.get_data_extension())
    Extensions = ['.{}'.format(SHAPESBlendShapeData.get_data_extension())]
    MenuName = SHAPESBlendShapeData.get_data_title()
    MenuOrder = 15
    MenuIconName = 'shapes_data.png'
    TypeIconPath = 'shapes_data.png'
    DataType = SHAPESBlendShapeData.get_data_type()
    PreviewWidgetClass = MayaSHAPESBlendShapeWeightsPreviewWidget

    def __init__(self, *args, **kwargs):
        super(MayaSHAPESBlendShapeWeights, self).__init__(*args, **kwargs)

        self.set_data_class(SHAPESBlendShapeData)
