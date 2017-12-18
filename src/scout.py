from defs import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_scout(creep):
    """
    just for basic scouting purpose.
    :param creep:
    :return:
    """
    if Game.flags[creep.memory.flag_name]:
        creep.moveTo(Game.flags[creep.memory.flag_name],
                     {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20,
                      'maxOps': 1000})

