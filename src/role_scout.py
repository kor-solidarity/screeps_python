from defs import *
import movement

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_scout(creep, enemy_constructions):
    """
    just for basic scouting purpose.

    :param creep:
    :param enemy_constructions: 적 건물계획
    :return:
    """

    # todo 방 하나 정찰하고 또 다른곳 가서 등등등.... 하는 역할을 수행해야만 한다.

    if creep.memory.assigned_room == creep.room.name and len(enemy_constructions):
        # 같은 방에 있는 경우 방 내 적 세력의 건물이 있는지 확인한다. 다 밟아!!
        if creep.memory.step_target and not Game.getObjectById(creep.memory.step_target):
            del creep.memory.step_target
        if not creep.memory.step_target:
            step_target = creep.pos.findClosestByRange(enemy_constructions)
            creep.memory.step_target = step_target.id
        if creep.memory.step_target:
            movement.movi(creep, creep.memory.step_target, 0, 5)
        return

    movement.get_to_da_room(creep, creep.memory.assigned_room)
