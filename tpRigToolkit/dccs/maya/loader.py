#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpRigToolkit-dccs-maya
"""

import os
import inspect
import traceback
import logging.config

from tpDcc.managers import resources
from tpDcc.libs.python import modules

from tpDcc.dccs.maya.meta import metanode
from tpDcc.dccs.maya.managers import metadatamanager


def init(dev=False):
    """
    Initializes module
    """

    logger = create_logger(dev=dev)

    register_resources()

    # Register tpRigToolkit MetaNodes
    meta_nodes_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'metarig')
    for sub_module in modules.iterate_modules(meta_nodes_path):
        file_name = os.path.splitext(os.path.basename(sub_module))[0]
        if file_name.startswith('__') or sub_module.endswith('.pyc'):
            continue
        module_path = modules.convert_to_dotted_path(os.path.normpath(sub_module))
        try:
            sub_module_obj = modules.import_module(module_path, skip_errors=True)
        except Exception:
            logger.error('Error while importing module: {} | {}'.format(module_path, traceback.format_exc()))
            continue
        if not sub_module_obj:
            continue
        for member in modules.iterate_module_members(sub_module_obj, predicate=inspect.isclass):
            if not issubclass(member[1], metanode.MetaNode):
                continue
            metadatamanager.register_meta_class(member[1])


def create_logger(dev=False):
    """
    Returns logger of current module
    """

    logger_directory = os.path.normpath(os.path.join(os.path.expanduser('~'), 'tpRigToolkit-dccs-maya', 'logs'))
    if not os.path.isdir(logger_directory):
        os.makedirs(logger_directory)

    logging_config = os.path.normpath(os.path.join(os.path.dirname(__file__), '__logging__.ini'))

    logging.config.fileConfig(logging_config, disable_existing_loggers=False)
    logger = logging.getLogger('tpRigToolkit-dccs-maya')
    dev = os.getenv('TPDCC_DEV', dev)
    if dev:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    return logger


def register_resources():
    """
    Registers tpRigToolkit-dccs-maya resources path
    """

    resources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
    resources.register_resource(resources_path, key='tpRigToolkit-core')


create_logger()
