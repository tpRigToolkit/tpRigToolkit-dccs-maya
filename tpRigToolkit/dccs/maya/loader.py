#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpRigToolkit-dccs-maya
"""

import os
import logging.config

# =================================================================================

PACKAGE = 'tpRigToolkit.dccs.maya'

# =================================================================================


def init(dev=False):
    """
    Initializes module
    """

    from tpDcc.libs.python import importer
    from tpDcc.dccs.maya import loader
    from tpRigToolkit.dccs.maya import register

    logger = create_logger(dev=dev)
    register.register_class('logger', logger)

    importer.init_importer(package=PACKAGE)

    # We update the registered meta classes
    loader.create_metadata_manager()


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
    if dev:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    return logger
