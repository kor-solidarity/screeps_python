from typing import List

from defs import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def transfer_nearest(creep: Creep, structures: List[Structure]):
    """
    크립에서 근접한 건물에 에너지 넣는게 가능한 상황이면 넣는다.

    :param creep:
    :param structures:
    :return:
    """
    # 스폰과 익스텐션중에 빈거 + 바로옆
    nearby_target = _.filter(structures,
                             lambda s: (s.structureType == STRUCTURE_EXTENSION
                                        or s.structureType == STRUCTURE_SPAWN
                                        or s.structureType == STRUCTURE_TOWER)
                                       and s.store.getFreeCapacity(RESOURCE_ENERGY) and creep.pos.isNearTo(s))

    # print(creep.name, spn_ext)
    if len(nearby_target):
        # 가장 가까이 있는 것 중에서도 한번에 가장 많이 넣을 수 있는걸 골라서 넣는다
        target = _.max(nearby_target, lambda s: s.store.getFreeCapacity(RESOURCE_ENERGY))
        # print('spn_ext', spn_ext)
        # print(creep.name, creep.pos, spn_ext[0].structureType, spn_ext[0].pos)
        return creep.transfer(target, RESOURCE_ENERGY)
    return ERR_NOT_FOUND
