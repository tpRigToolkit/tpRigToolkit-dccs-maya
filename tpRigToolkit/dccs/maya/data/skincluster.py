#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains data Maya Skin Cluster weights widget
"""

from __future__ import print_function, division, absolute_import

import os
import json
import threading
from collections import OrderedDict

import tpDcc as tp
import tpDcc.dccs.maya as maya
from tpDcc.libs.python import fileio, folder, path as path_utils
from tpDcc.dccs.maya.data import base
from tpDcc.dccs.maya.core import helpers, shape as shape_utils, deformer as deform_utils
from tpDcc.dccs.maya.core import decorators as maya_decorators, scene as scene_utils, geometry as geo_utils

from tpRigToolkit.core import data


class SkinWeightsData(base.MayaCustomData, object):
    def __init__(self, name=None, path=None):
        super(SkinWeightsData, self).__init__(name=name, path=path)

    @staticmethod
    def get_data_type():
        return 'maya.skin_weights'

    @staticmethod
    def get_data_extension():
        return 'skin'

    @staticmethod
    def get_data_title():
        return 'Skin Weights'

    def export_data(self, file_path=None, comment='-', create_version=True, *args, **kwargs):

        if not tp.is_maya():
            maya.logger.warning('Data must be exported from within Maya!')
            return False

        file_path = file_path or self.get_file()

        objects = kwargs.get('objects', None)
        if not objects:
            objects = tp.Dcc.selected_nodes(full_path=True)
        if not objects:
            maya.logger.warning(
                'Nothing selected to export skin weights of. Please, select a mesh,'
                ' curve, NURBS surface or lattice with skin weights to export')
            return False

        file_folder = os.path.dirname(file_path)

        # Check that all objects that we are going to export have at least one skin cluster node associated
        # Make sure also that all objects skin output folder have been created
        obj_dirs = OrderedDict()
        skin_nodes = OrderedDict()
        geo_paths = OrderedDict()
        skin_weights = OrderedDict()
        for obj in objects:
            if shape_utils.is_a_shape(obj):
                obj = tp.Dcc.node_parent(obj, full_path=True)
            obj_filename = obj
            if obj.find('|') > -1:
                obj_filename = obj_filename.replace('|', '.')
                if obj_filename.startswith('.'):
                    obj_filename = obj_filename[1:]
            if obj_filename.find(':') > -1:
                obj_filename = obj_filename.replace(':', '-')

            skin = deform_utils.find_deformer_by_type(obj, 'skinCluster')
            if not skin:
                maya.logger.warning('Skin exported failed! No skinCluster node found on "{}"'.format(obj))
                return False

            geo_path = path_utils.join_path(file_folder, obj_filename)
            if path_utils.is_dir(geo_path):
                folder.delete_folder(obj_filename, file_folder)
            geo_path = folder.create_folder(obj_filename, file_folder)
            if not geo_path:
                maya.logger.error(
                    'Unable to create skin weights directory: "{}" in "{}"'.format(obj_filename, file_folder))
                return False

            weights = deform_utils.get_skin_weights(skin)

            obj_dirs[obj] = obj_filename
            skin_nodes[obj] = skin
            geo_paths[obj] = geo_path
            skin_weights[obj] = weights

        for (obj, skin_node), (_, geo_path), (_, skin_weights) in zip(
                skin_nodes.items(), geo_paths.items(), skin_weights.items()):

            maya.logger.info('Exporting weights: {} > {} --> "{}"'.format(obj, skin_node, geo_path))

            info_lines = list()
            info_file = fileio.create_file('influence.info', geo_path)

            for influence in skin_weights:
                if influence is None or influence == 'None':
                    continue
                weight_list = skin_weights[influence]
                if not weight_list:
                    continue
                thread = MayaLoadWeightFileThread()
                influence_line = thread.run(influence, skin_node, skin_weights[influence], geo_path)
                if influence_line:
                    info_lines.append(influence_line)

            writer = fileio.FileWriter(info_file)
            writer.write(info_lines)

            settings_file = fileio.create_file('settings.info', geo_path)
            setting_lines = list()
            if shape_utils.has_shape_of_type(obj, 'mesh'):
                self._export_mesh_obj(obj, geo_path)

            if tp.Dcc.attribute_exists(skin_node, 'blendWeights'):
                blend_weights = deform_utils.get_skin_blend_weights(skin_node)
                setting_lines.append("['blendWeights', {}]".format(blend_weights))
            if tp.Dcc.attribute_exists(skin_node, 'skinningMethod'):
                skin_method = tp.Dcc.get_attribute_value(skin_node, 'skinningMethod')
                setting_lines.append("['skinningMethod', {}]".format(skin_method))

            write_settings = fileio.FileWriter(settings_file)
            write_settings.write(setting_lines)

            maya.logger.info('Skin weights exported successfully: {} > {} --> "{}"'.format(obj, skin_node, geo_path))

        data_to_save = OrderedDict()
        for obj, obj_filename in obj_dirs.items():
            data_to_save[obj] = {'enabled': True, 'folder': obj_filename}
        with open(file_path, 'w') as fh:
            json.dump(data_to_save, fh)

        maya.logger.info('Skin weights export operation completed successfully!')

        version = fileio.FileVersion(file_folder)
        version.save(comment)

        return True

    @maya_decorators.undo_chunk
    def import_data(self, file_path='', objects=None):
        """
        Loads data object
        :param file_path: str, file path of file to load
        """

        if not tp.is_maya():
            maya.logger.warning('Data must be exported from within Maya!')
            return False

        file_path = file_path or self.get_file()
        if not file_path or not os.path.isfile(file_path):
            maya.logger.warning('Impossible to import skin weights from: "{}"'.format(file_path))
            return False

        with open(file_path, 'r') as fh:
            skin_data = json.load(fh)
        if not skin_data:
            maya.logger.warning('No skin data found in file: "{}"'.format(file_path))
            return False

        file_folder = os.path.dirname(file_path)
        folders = folder.get_folders(file_folder)

        if not objects:
            objects = tp.Dcc.selected_nodes(full_path=True) or list()
        for obj in objects:
            if obj in skin_data:
                continue
            skin_data[obj] = {'folder': tp.Dcc.node_short_name(obj), 'enabled': True}

        for obj, obj_data in skin_data.items():
            obj_folder = obj_data.get('folder', None)
            if not obj_folder:
                continue
            obj_enabled = obj_data.get('enabled', False) and obj_folder in folders
            obj_path = path_utils.clean_path(os.path.join(file_folder, obj_folder))
            if not obj_enabled or not os.path.isdir(obj_path):
                continue
            obj_exists = tp.Dcc.object_exists(obj)
            if not obj_exists:
                continue

            self._import_skin_weights(obj_path, obj)

        self._center_view()

        maya.logger.info('Imported "{}" skin data'.format(self.name))

        return True

    def get_skin_meshes(self, file_path=None):
        """
        Returns all skinned meshes fro ma .skin file
        :param file_path: str
        :return: list(str)
        """

        if not tp.is_maya():
            return

        file_path = file_path or self.get_file()
        if not file_path or not os.path.isfile(file_path):
            return
        skin_path = path_utils.join_path(path_utils.get_dirname(file_path), self.name)

        meshes = None
        if path_utils.is_dir(skin_path):
            meshes = folder.get_folders(skin_path)

        return meshes

    def remove_mesh(self, mesh, file_path=None):
        """
        Removes a mesh from a .skin file
        :param mesh: str
        :param file_path: str
        :return: bool
        """

        if not tp.is_maya():
            return

        file_path = file_path or self.get_file()
        if not file_path or not os.path.isfile(file_path):
            return
        skin_path = path_utils.join_path(path_utils.get_dirname(file_path), self.name)

        folder.delete_folder(mesh, skin_path)
        test_path = path_utils.join_path(skin_path, mesh)

        return bool(path_utils.is_dir(test_path))

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    def _export_mesh_obj(self, mesh, data_path):
        """
        Internal function that exports given mesh object (creates a backup of the mesh in disk)
        :param mesh: str
        :param data_path: str
        """

        helpers.load_plugin('objExport')

        envelope_value = deform_utils.get_skin_envelope(mesh)
        deform_utils.set_skin_envelope(mesh, 0)

        maya.cmds.select(mesh)
        original_path = tp.Dcc.scene_name()
        mesh_path = '{}/mesh.obj'.format(data_path)

        try:
            maya.cmds.file(rename=mesh_path)
            maya.cmds.file(
                force=True,
                options="groups=0;ptgroups=0;materials=0;smoothing=0;normals=0",
                type="OBJexport",
                preserveReferences=False,
                exportSelected=True
            )
        finally:
            maya.cmds.file(rename=original_path)

        deform_utils.set_skin_envelope(mesh, envelope_value)

    def _import_mesh_obj(self, data_path):
        """
        Internal function that imports mesh object stored in given path
        :param data_path: str, path that contains already exported mesh object
        :return: str, name of the imported mesh
        """

        mesh_path = path_utils.join_path(data_path, 'mesh.obj')
        if not path_utils.is_file(mesh_path):
            return None

        track = scene_utils.TrackNodes()
        track.load(node_type='mesh')
        maya.cmds.file(mesh_path, i=True, type='OBJ', ignoreVersion=True, options='mo=1')
        delta = track.get_delta()
        if delta:
            delta = tp.Dcc.node_parent(delta, full_path=True)

        return delta

    def _import_skin_weights(self, data_path, mesh):

        if not tp.Dcc.object_exists(mesh) or not os.path.isdir(data_path):
            return False

        is_valid_mesh = False
        shape_types = ['mesh', 'nurbsSurface', 'nurbsCurve', 'lattice']
        for shape_type in shape_types:
            if shape_utils.has_shape_of_type(mesh, shape_type):
                is_valid_mesh = True
                break
        if not is_valid_mesh:
            maya.logger.warning(
                'Node "{}" is not a valid mesh node! Currently supported nodes include: {}'.format(mesh, shape_types))
            return False

        maya.logger.info('Importing skin clusters {} --> "{}"'.format(mesh, data_path))

        influence_dict = self._get_influences(data_path)
        if not influence_dict:
            maya.logger.warning('No influences data found for: {}'.format(mesh))
            return False

        influences = influence_dict.keys()
        if not influences:
            maya.logger.warning('No influences found for: "{}"'.format(mesh))
            return False
        influences.sort()
        maya.logger.debug('Influences found for {}: {}'.format(mesh, influences))

        short_name = tp.Dcc.node_short_name(mesh)
        transfer_mesh = None

        if shape_utils.has_shape_of_type(mesh, 'mesh'):
            orig_mesh = self._import_mesh_obj(data_path)
            if orig_mesh:
                mesh_match = geo_utils.is_mesh_compatible(orig_mesh, mesh)
                if not mesh_match:
                    transfer_mesh = mesh
                    mesh = orig_mesh
                else:
                    tp.Dcc.delete_object(orig_mesh)

        # Check if there are duplicated influences and also for the creation of influences that does not currently
        # in the scene
        add_joints = list()
        remove_entries = list()
        for influence in influences:
            joints = tp.Dcc.list_nodes(influence, full_path=True)
            if type(joints) == list and len(joints) > 1:
                add_joints.append(joints[0])
                conflicting_count = len(joints)
                maya.logger.warning(
                    'Found {} joints with name {}. Using only the first one: {}'.format(
                        conflicting_count, influence, joints[0]))
                remove_entries.append(influence)
                influence = joints[0]
            if not tp.Dcc.object_exists(influence):
                tp.Dcc.clear_selection()
                maya.cmds.joint(n=influence, p=influence_dict[influence]['position'])
        for entry in remove_entries:
            influences.remove(entry)
        influences += add_joints

        # Create skin cluster and removes if it already exists
        skin_cluster = deform_utils.find_deformer_by_type(mesh, 'skinCluster')
        if skin_cluster:
            tp.Dcc.delete_object(skin_cluster)
        skin_cluster = maya.cmds.skinCluster(
            influences, mesh, tsb=True, n=tp.Dcc.find_unique_name('skin_%s' % short_name))[0]
        tp.Dcc.set_attribute_value(skin_cluster, 'normalizeWeights', 0)
        deform_utils.set_skin_weights_to_zero(skin_cluster)

        influence_index = 0
        influence_index_dict = deform_utils.get_skin_influences(skin_cluster, return_dict=True)
        progress_bar = tp.DccProgressBar('Import Skin', len(influence_dict.keys()))
        for influence in influences:
            orig_influence = influence
            if influence.count('|') > 1:
                split_influence = influence.split('|')
                if len(split_influence) > 1:
                    influence = split_influence[-1]
            progress_bar.status('Importing skin mesh: {}, influence: {}'.format(short_name, influence))
            if 'weights' not in influence_dict[orig_influence]:
                maya.logger.warning('Weights msissing for influence: {}. Skipping it ...'.format(influence))
                continue
            weights = influence_dict[orig_influence]['weights']
            if influence not in influence_index_dict:
                continue
            index = influence_index_dict[influence]

            # attr = '{}.weightList[*].weights[{}]'.format(skin_cluster, index)
            # NOTE: his was not faster, zipping zero weights is much faster than setting all the weights
            # maya.cmds.setAttr(attr, *weights )

            for i in range(len(weights)):
                weight = float(weights[i])
                if weight == 0 or weight < 0.0001:
                    continue
                attr = '{}.weightList[{}].weights[{}]'.format(skin_cluster, i, index)
                maya.cmds.setAttr(attr, weight)
            progress_bar.inc()

            if progress_bar.break_signaled():
                break
            influence_index += 1
        progress_bar.end()

        maya.cmds.skinCluster(skin_cluster, edit=True, normalizeWeights=1)
        maya.cmds.skinCluster(skin_cluster, edit=True, forceNormalizeWeights=True)

        settings_path = path_utils.join_path(data_path, 'settings.info')
        if path_utils.is_file(settings_path):
            lines = fileio.get_file_lines(settings_path)
            for line in lines:
                test_line = line.strip()
                if not test_line:
                    continue
                line_list = eval(line)
                attr_name = line_list[0]
                value = line_list[1]
                if attr_name == 'blendWeights':
                    deform_utils.set_skin_blend_weights(skin_cluster, value)
                else:
                    if tp.Dcc.attribute_exists(skin_cluster, attr_name):
                        tp.Dcc.set_attribute_value(skin_cluster, attr_name, value)

        if transfer_mesh:
            maya.logger.info('Import sking weights: mesh topology does not match. Trying to transfer topology ...')
            deform_utils.skin_mesh_from_mesh(mesh, transfer_mesh)
            tp.Dcc.delete_object(mesh)

        maya.logger.info('Import skinCluster weights: {} from {}'.format(short_name, data_path))

        return True

    def _get_influences(self, folder_path):
        """
        Internal function that returns a dictionary containing influences data from influence files
        contained in the given directory
        :param folder_path: str, path that contains influence file
        :return: dict, influence data
        """

        influence_dict = dict()

        files = fileio.get_files(folder_path)
        if not files:
            return influence_dict
        info_file = path_utils.join_path(folder_path, 'influence.info')
        if not path_utils.is_file(info_file):
            return influence_dict

        info_lines = fileio.get_file_lines(info_file)
        for line in info_lines:
            if not line:
                continue
            line_dict = eval(line)
            influence_dict.update(line_dict)

        for influence in files:
            if not influence.endswith('.weights') or influence == 'influence.info':
                continue
            read_thread = MayaReadWeightFileThread()
            try:
                influence_dict = read_thread.run(influence_dict, folder_path, influence)
            except Exception as exc:
                maya.logger.error(
                    'Errors with influence "{}" while reading weight file: "{}" | {}'.format(influence, info_file, exc))

        return influence_dict


class MayaLoadWeightFileThread(threading.Thread, object):
    def __init__(self):
        super(MayaLoadWeightFileThread, self).__init__()

    def run(self, influence_index, skin, weights, file_path):
        influence_name = deform_utils.get_skin_influence_at_index(influence_index, skin)
        if not influence_name or not tp.Dcc.object_exists(influence_name):
            return
        weight_path = fileio.create_file('{}.weights'.format(influence_name), file_path)
        if not path_utils.is_file(weight_path):
            maya.logger.warning('"{}" is not a valid path to save skin weights into!'.format(file_path))
            return

        writer = fileio.FileWriter(weight_path)
        writer.write_line(weights)

        influence_position = tp.Dcc.node_world_space_translation(influence_name)

        return "{'%s' : {'position' : %s}}" % (influence_name, str(influence_position))


class MayaReadWeightFileThread(threading.Thread):
    def __init__(self):
        super(MayaReadWeightFileThread, self).__init__()

    def run(self, influence_dict, folder_path, influence):
        file_path = path_utils.join_path(folder_path, influence)

        influence = influence.split('.')[0]

        lines = fileio.get_file_lines(file_path)

        if not lines:
            influence_dict[influence]['weights'] = None
            return influence_dict

        weights = eval(lines[0])

        if influence in influence_dict:
            influence_dict[influence]['weights'] = weights

        return influence_dict


class MayaSkinClusterWeightsPreviewWidget(data.DataPreviewWidget, object):
    def __init__(self, item, parent=None):
        super(MayaSkinClusterWeightsPreviewWidget, self).__init__(item=item, parent=parent)

        self._export_btn.setText('Save')
        self._export_btn.setVisible(True)
        self._load_btn.setVisible(False)


class MayaSkinClusterWeights(data.DataItem, object):

    Extension = '.{}'.format(SkinWeightsData.get_data_extension())
    Extensions = ['.{}'.format(SkinWeightsData.get_data_extension())]
    MenuName = SkinWeightsData.get_data_title()
    MenuOrder = 4
    MenuIconName = 'skin_weights_data.png'
    TypeIconPath = 'skin_weights_data.png'
    DataType = SkinWeightsData.get_data_type()
    PreviewWidgetClass = MayaSkinClusterWeightsPreviewWidget

    def __init__(self, *args, **kwargs):
        super(MayaSkinClusterWeights, self).__init__(*args, **kwargs)

        self.set_data_class(SkinWeightsData)


class NgSkinWeightsData(SkinWeightsData, object):
    def __init__(self, name=None, path=None):
        super(NgSkinWeightsData, self).__init__(name=name, path=path)

    @staticmethod
    def get_data_type():
        return 'maya.ng_skin_weights'

    @staticmethod
    def get_data_extension():
        return 'json'

    @staticmethod
    def get_data_title():
        return 'Ng Skin Weights'

    def export_data(self, file_path=None, comment='-', create_version=True, *args, **kwargs):

        if not tp.is_maya():
            maya.logger.warning('Data must be exported from within Maya!')
            return False

        try:
            if not tp.Dcc.is_plugin_loaded('ngSkinTools2'):
                tp.Dcc.load_plugin('ngSkinTools2')
            import ngSkinTools2
            from ngSkinTools2 import api as ngst_api
        except ImportError:
            maya.logger.warning('NgSkinTools 2.0 is not installed. Impossible to export ngSkin data')
            return False

        file_path = file_path or self.get_file()

        objects = kwargs.get('objects', None)
        if not objects:
            objects = tp.Dcc.selected_nodes(full_path=True)
        if not objects:
            maya.logger.warning(
                'Nothing selected to export skin weights of. Please, select a mesh,'
                ' curve, NURBS surface or lattice with skin weights to export')
            return False

        file_folder = os.path.dirname(file_path)

        # Check that all objects that we are going to export have at least one skin cluster node associated
        # Make sure also that all objects skin output folder have been created
        obj_dirs = OrderedDict()
        skin_nodes = OrderedDict()
        geo_paths = OrderedDict()
        skin_weights = OrderedDict()
        for obj in objects:
            if shape_utils.is_a_shape(obj):
                obj = tp.Dcc.node_parent(obj, full_path=True)
            obj_filename = obj
            if obj.find('|') > -1:
                obj_filename = obj_filename.replace('|', '.')
                if obj_filename.startswith('.'):
                    obj_filename = obj_filename[1:]
            if obj_filename.find(':') > -1:
                obj_filename = obj_filename.replace(':', '-')

            skin = deform_utils.find_deformer_by_type(obj, 'skinCluster')
            if not skin:
                maya.logger.warning('Skin exported failed! No skinCluster node found on "{}"'.format(obj))
                return False

            geo_path = path_utils.join_path(file_folder, obj_filename)
            if path_utils.is_dir(geo_path):
                folder.delete_folder(obj_filename, file_folder)
            geo_path = folder.create_folder(obj_filename, file_folder)
            if not geo_path:
                maya.logger.error(
                    'Unable to create skin weights directory: "{}" in "{}"'.format(obj_filename, file_folder))
                return False

            weights = deform_utils.get_skin_weights(skin)

            obj_dirs[obj] = obj_filename
            skin_nodes[obj] = skin
            geo_paths[obj] = geo_path
            skin_weights[obj] = weights

        for (obj, skin_node), (_, geo_path), (_, skin_weights) in zip(
                skin_nodes.items(), geo_paths.items(), skin_weights.items()):

            maya.logger.info('Exporting weights: {} > {} --> "{}"'.format(obj, skin_node, geo_path))

            info_lines = list()
            info_file = fileio.create_file('influence.info', geo_path)

            for influence in skin_weights:
                if influence is None or influence == 'None':
                    continue
                weight_list = skin_weights[influence]
                if not weight_list:
                    continue

                influence_name = deform_utils.get_skin_influence_at_index(influence, skin_node)
                if not influence_name or not tp.Dcc.object_exists(influence_name):
                    continue

                influence_position = tp.Dcc.node_world_space_translation(influence_name)
                influence_line = "{'%s' : {'position' : %s}}" % (influence_name, str(influence_position))
                info_lines.append(influence_line)

            writer = fileio.FileWriter(info_file)
            writer.write(info_lines)

            settings_file = fileio.create_file('settings.info', geo_path)
            setting_lines = list()
            if shape_utils.has_shape_of_type(obj, 'mesh'):
                self._export_mesh_obj(obj, geo_path)

            setting_lines.append("['skinNodeName', '{}']".format(tp.Dcc.node_short_name(skin_node)))
            if tp.Dcc.attribute_exists(skin_node, 'blendWeights'):
                blend_weights = deform_utils.get_skin_blend_weights(skin_node)
                setting_lines.append("['blendWeights', {}]".format(blend_weights))
            if tp.Dcc.attribute_exists(skin_node, 'skinningMethod'):
                skin_method = tp.Dcc.get_attribute_value(skin_node, 'skinningMethod')
                setting_lines.append("['skinningMethod', {}]".format(skin_method))

            write_settings = fileio.FileWriter(settings_file)
            write_settings.write(setting_lines)

            ng_skin_file_name = os.path.join(geo_path, 'ngdata.json')
            ngst_api.export_json(obj, file=ng_skin_file_name)

            maya.logger.info('Skin weights exported successfully: {} > {} --> "{}"'.format(obj, skin_node, geo_path))

        data_to_save = OrderedDict()
        for obj, obj_filename in obj_dirs.items():
            data_to_save[obj] = {'enabled': True, 'folder': obj_filename}
        with open(file_path, 'w') as fh:
            json.dump(data_to_save, fh)

        maya.logger.info('Skin weights export operation completed successfully!')

        version = fileio.FileVersion(os.path.dirname(file_path))
        if version.has_versions():
            version = fileio.FileVersion(file_path)
            version.save(comment)

        return True

    def _import_skin_weights(self, data_path, mesh):
        if not tp.Dcc.object_exists(mesh) or not os.path.isdir(data_path):
            return False

        try:
            if not tp.Dcc.is_plugin_loaded('ngSkinTools2'):
                tp.Dcc.load_plugin('ngSkinTools2')
            import ngSkinTools2
            from ngSkinTools2 import api as ngst_api
        except ImportError:
            maya.logger.warning('NgSkinTools 2.0 is not installed. Impossible to import ngSkin data')
            return False

        ng_skin_data_path = path_utils.join_path(data_path, 'ngdata.json')
        if not path_utils.is_file(ng_skin_data_path):
            maya.logger.warning(
                'No Ng Skin Data file found: "{}", aborting import skin weights operation ...'.format(
                    ng_skin_data_path))
            return False

        is_valid_mesh = False
        shape_types = ['mesh', 'nurbsSurface', 'nurbsCurve', 'lattice']
        for shape_type in shape_types:
            if shape_utils.has_shape_of_type(mesh, shape_type):
                is_valid_mesh = True
                break
        if not is_valid_mesh:
            maya.logger.warning(
                'Node "{}" is not a valid mesh node! Currently supported nodes include: {}'.format(mesh, shape_types))
            return False

        maya.logger.info('Importing skin clusters {} --> "{}"'.format(mesh, data_path))

        influence_dict = self._get_influences(data_path)
        if not influence_dict:
            maya.logger.warning('No influences data found for: {}'.format(mesh))
            return False

        influences = influence_dict.keys()
        if not influences:
            maya.logger.warning('No influences found for: "{}"'.format(mesh))
            return False
        influences.sort()
        maya.logger.debug('Influences found for {}: {}'.format(mesh, influences))

        short_name = tp.Dcc.node_short_name(mesh)
        transfer_mesh = None

        if shape_utils.has_shape_of_type(mesh, 'mesh'):
            orig_mesh = self._import_mesh_obj(data_path)
            if orig_mesh:
                mesh_match = geo_utils.is_mesh_compatible(orig_mesh, mesh)
                if not mesh_match:
                    transfer_mesh = mesh
                    mesh = orig_mesh
                else:
                    tp.Dcc.delete_object(orig_mesh)

        # Check if there are duplicated influences and also for the creation of influences that does not currently
        # in the scene
        add_joints = list()
        remove_entries = list()
        for influence in influences:
            joints = tp.Dcc.list_nodes(influence, full_path=True)
            if type(joints) == list and len(joints) > 1:
                add_joints.append(joints[0])
                conflicting_count = len(joints)
                maya.logger.warning(
                    'Found {} joints with name {}. Using only the first one: {}'.format(
                        conflicting_count, influence, joints[0]))
                remove_entries.append(influence)
                influence = joints[0]
            if not tp.Dcc.object_exists(influence):
                tp.Dcc.clear_selection()
                maya.cmds.joint(n=influence, p=influence_dict[influence]['position'])
        for entry in remove_entries:
            influences.remove(entry)
        influences += add_joints

        settings_data = dict()
        settings_path = path_utils.join_path(data_path, 'settings.info')
        if path_utils.is_file(settings_path):
            lines = fileio.get_file_lines(settings_path)
            for line in lines:
                test_line = line.strip()
                if not test_line:
                    continue
                line_list = eval(line)
                attr_name = line_list[0]
                value = line_list[1]
                settings_data[attr_name] = value

        # Create skin cluster and removes if it already exists
        skin_cluster = deform_utils.find_deformer_by_type(mesh, 'skinCluster')
        if skin_cluster:
            tp.Dcc.delete_object(skin_cluster)

        skin_node_name = settings_data.pop('skinNodeName', 'skin_{}'.format(short_name))
        skin_cluster = maya.cmds.skinCluster(
            influences, mesh, tsb=True, n=tp.Dcc.find_unique_name(skin_node_name))[0]
        tp.Dcc.set_attribute_value(skin_cluster, 'normalizeWeights', 0)
        deform_utils.set_skin_weights_to_zero(skin_cluster)

        # TODO: This Influence mapping configuration should be generated during export and imported here as JSON file
        # Import ng skin data
        config = ngst_api.InfluenceMappingConfig()
        config.use_distance_matching = True
        config.use_label_matching = True
        config.use_name_matching = True

        ngst_api.import_json(mesh, file=ng_skin_data_path, influences_mapping_config=config)

        maya.cmds.skinCluster(skin_cluster, edit=True, normalizeWeights=1)
        maya.cmds.skinCluster(skin_cluster, edit=True, forceNormalizeWeights=True)

        for attr_name, value in settings_data.items():
            if attr_name == 'blendWeights':
                deform_utils.set_skin_blend_weights(skin_cluster, value)
            else:
                if tp.Dcc.attribute_exists(skin_cluster, attr_name):
                    tp.Dcc.set_attribute_value(skin_cluster, attr_name, value)

        if transfer_mesh:
            maya.logger.info('Import sking weights: mesh topology does not match. Trying to transfer topology ...')
            deform_utils.skin_mesh_from_mesh(mesh, transfer_mesh)
            tp.Dcc.delete_object(mesh)

        maya.logger.info('Import skinCluster weights: {} from {}'.format(short_name, data_path))

        return True

    def _get_influences(self, folder_path):
        influence_dict = dict()

        info_file = path_utils.join_path(folder_path, 'influence.info')
        if not path_utils.is_file(info_file):
            return influence_dict

        info_lines = fileio.get_file_lines(info_file)
        for line in info_lines:
            if not line:
                continue
            line_dict = eval(line)
            influence_dict.update(line_dict)

        return influence_dict


class NgSkinClusterWeightsPreviewWidget(MayaSkinClusterWeightsPreviewWidget, object):
    def __init__(self, item, parent=None):
        super(NgSkinClusterWeightsPreviewWidget, self).__init__(item=item, parent=parent)


class NgSkinClusterWeights(data.DataItem, object):

    Extension = '.{}'.format(NgSkinWeightsData.get_data_extension())
    Extensions = ['.{}'.format(NgSkinWeightsData.get_data_extension())]
    MenuName = NgSkinWeightsData.get_data_title()
    MenuOrder = 4
    MenuIconName = 'ng_skin_weights_data'
    DataType = NgSkinWeightsData.get_data_type()
    PreviewWidgetClass = NgSkinClusterWeightsPreviewWidget

    def __init__(self, *args, **kwargs):
        super(NgSkinClusterWeights, self).__init__(*args, **kwargs)

        self.set_data_class(NgSkinWeightsData)
