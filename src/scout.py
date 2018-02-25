from defs import *
import miscellaneous

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
    # if not creep.memory.in_corner and creep.memory.in_corner != 0:
    #     creep.memory.in_corner = 0

    # todo 방 하나 정찰하고 또 다른곳 가서 등등등.... 하는 역할을 수행해야만 한다.

    miscellaneous.get_to_da_room(creep, creep.memory.assigned_room)
