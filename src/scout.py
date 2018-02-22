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
    if not creep.memory.in_corner and creep.memory.in_corner != 0:
        creep.memory.in_corner = 0

    # todo 방 하나 정찰하고 또 다른곳 가서 등등등.... 하는 역할을 수행해야만 한다.
    # 그리고 지금 확실하게 방안으로 들어가질 않음.
    if not Game.rooms[creep.memory.assigned_room]:
        creep.moveTo(__new__(RoomPosition(25, 25, creep.memory.assigned_room))
                     , {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20, 'range': 20
                     , 'maxOps': 1000})

