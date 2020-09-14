import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode


def get_character_module(character_name):
    """
    Return root module of the given character name
    :param character_name: str
    :return: str
    """

    from tpRigToolkit.dccs.maya.metarig.core import character

    network_nodes = maya.cmds.ls(type='network')
    for network_node in network_nodes:
        attrs = maya.cmds.listAttr(network_node)
        if 'meta_class' in attrs and 'meta_node_id' in attrs:
            meta_class = maya.cmds.getAttr('{}.meta_class'.format(network_node))
            module_name = maya.cmds.getAttr('{}.meta_node_id'.format(network_node))
            if module_name != character_name:
                continue
            if meta_class == character.RigCharacter.__name__:
                return metanode.validate_obj_arg(network_node, 'RigCharacter')
            else:
                for sub_class in character.RigCharacter.__subclasses__():
                    if meta_class == sub_class.__name__:
                        return metanode.validate_obj_arg(network_node, sub_class.__name__)

    return None


def build_character(character_name):
    """
    Function that creates the associated Character MetaNode for this rig module
    :return: metanode.MetaNode
    """

    from tpRigToolkit.dccs.maya.metarig.core import character

    character = character.RigCharacter(name=character_name)
    character.create()

    return character


def find_rig_module(module_name):
    """
    Find a component by its name
    :param module_name: str
    :return:
    """

    network_nodes = maya.cmds.ls(type='network')
    for network_node in network_nodes:
        attrs = maya.cmds.listAttr(network_node)
        if 'meta_class' in attrs and 'meta_node_id' in attrs:
            meta_class = maya.cmds.getAttr('{}.meta_class'.format(network_node))
            rig_type = maya.cmds.getAttr('{}.rig_type'.format(network_node))
            meta_module_name = maya.cmds.getAttr('{}.meta_node_id'.format(network_node))
            if rig_type == 'module' and meta_module_name == module_name:
                return metanode.validate_obj_arg(network_node, meta_class)

    return None
