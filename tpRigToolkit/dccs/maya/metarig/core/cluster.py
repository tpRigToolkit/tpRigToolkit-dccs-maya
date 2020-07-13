#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains rig component to create clusters
"""

from __future__ import print_function, division, absolute_import

# TODO
"""
It would be nice to be able to work with cluster and their handles as MetaObjects. At this moment we only support
transforms and nodes that can be created using createNode function.
Clusters are a special kind of objects and we need to threat them in a different way.
We should override MetaNode __create_node__ function to handle the creation of the cluster using cluster command.
Then we also need to convert the handle into a MetaObject and link them using a message attribute
"""

# from tpDcc.dccs.maya.meta import metanode, metaobject
# from tpDcc.dccs.maya.core import deformer as def_utils
#
#
# class ClusterSurface(metaobject.MetaObject, object):
#     def __init__(self, *args, **kwargs):
#         kwargs['node_type'] = 'cluster'
#         super(ClusterSurface, self).__init__(*args, **kwargs)
#
#         if self.cached:
#             return
#
#         self.set_join_ends(False)
#         self.set_join_both_ends(False)
#         self.set_first_cluster_pivot_at_start(True)
#         self.set_last_cluster_pivot_at_end(True)
#         self.set_cluster_u(True)
#
#     def create(self):
#         cluster_surface = def_utils.ClusterSurface(self.geometry, self.base_name)
#         cluster_surface.set_first_cluster_pivot_at_start(self.first_cluster_pivot_at_start)
#         cluster_surface.set_last_cluster_pivot_at_end(self.last_cluster_pivot_at_end)
#         cluster_surface.set_join_ends(self.join_ends)
#         cluster_surface.set_join_both_ends(self.join_both_ends)
#         cluster_surface.create()
#
#         self._set_handles(cluster_surface.get_cluster_handle_list())
#
#     def get_clusters(self, as_meta=False):
#         return self.message_list_get('clusters', as_meta=as_meta)
#
#     def set_geometry(self, geo):
#         if not self.has_attr('geometry'):
#             self.add_attribute(attr='geometry', value=geo, attr_type='messageSimple')
#         else:
#             self.geometry = geo
#
#     def set_clusters_group(self, cluster_group):
#         if not self.has_attr('clusters_group'):
#             self.add_attribute(attr='clusters_group', value=cluster_group, attr_type='messageSimple')
#         else:
#             self.clusters_group = cluster_group
#
#     def set_first_cluster_pivot_at_start(self, flag):
#         if not self.has_attr('first_cluster_pivot_at_start'):
#             self.add_attribute(attr='first_cluster_pivot_at_start', value=flag)
#         else:
#             self.first_cluster_pivot_at_start = flag
#
#     def set_last_cluster_pivot_at_end(self, flag):
#         if not self.has_attr('last_cluster_pivot_at_end'):
#             self.add_attribute(attr='last_cluster_pivot_at_end', value=flag)
#         else:
#             self.last_cluster_pivot_at_end = flag
#
#     def set_join_ends(self, flag):
#         if not self.has_attr('join_ends'):
#             self.add_attribute(attr='join_ends', value=flag)
#         else:
#             self.join_ends = flag
#
#     def set_join_both_ends(self, flag):
#         if not self.has_attr('join_both_ends'):
#             self.add_attribute(attr='join_both_ends', value=flag)
#         else:
#             self.join_both_ends = flag
#
#     def set_cluster_u(self, flag):
#         if not self.has_attr('cluster_u'):
#             self.add_attribute(attr='cluster_u', value=flag)
#         else:
#             self.cluster_u = flag
#
#     def _set_handles(self, handles):
#         handles = metanode.validate_obj_list_arg(handles, 'MetaObject', update_class=True)
#         if not self.message_list_get('clusters', as_meta=False):
#             self.message_list_connect('clusters', handles)
#         else:
#             self.message_list_purge('clusters')
#             self.message_list_connect('clusters', handles)
#
#
# class ClusterCurve(ClusterSurface, object):
#     def __init__(self, *args, **kwargs):
#         super(ClusterCurve, self).__init__(*args, **kwargs)
#
#         if self.cached:
#             return
#
#     def create(self):
#         cluster_surface = def_utils.ClusterCurve(self.geometry, self.base_name)
#         cluster_surface.set_first_cluster_pivot_at_start(self.first_cluster_pivot_at_start)
#         cluster_surface.set_last_cluster_pivot_at_end(self.last_cluster_pivot_at_end)
#         cluster_surface.set_join_ends(self.join_ends)
#         cluster_surface.set_join_both_ends(self.join_both_ends)
#         cluster_surface.create()
#         self._set_handles(cluster_surface.get_cluster_handle_list())
#
#     def set_cluster_u(self, flag):
#         pass
