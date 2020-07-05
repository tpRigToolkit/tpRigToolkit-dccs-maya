import tpDcc.dccs.maya as maya
from tpDcc.dccs.maya.meta import metanode


def get_character_module(character_name):
    """
    Return root module of the given character name
    :param character_name: str
    :return: str
    """

    modules = maya.cmds.ls(type='network')
    for module in modules:
        attrs = maya.cmds.listAttr(module)
        if 'meta_class' in attrs and 'meta_node_id' in attrs:
            meta_class = maya.cmds.getAttr('{}.meta_class'.format(module))
            module_name = maya.cmds.getAttr('{}.meta_node_id'.format(module))
            if meta_class == 'RigCharacter' and module_name == character_name:
                return metanode.validate_obj_arg(module, 'RigCharacter')

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
