from typing import List, Optional

from defs import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def transfer_nearest(creep: Creep, structures: List[Structure], structure_types: List[str] = []):
    """
    크립이 근접한 건물에 에너지 넣는게 가능한 상황이면 넣는다.
    non-haulers to transfer energy to any nearby structures if it's not full.

    :param creep:
    :param structures:
    :param structure_types: in case there are more structures to be filled. must be structureType
    :return:
    """
    result = ERR_NOT_FOUND
    # 스폰과 익스텐션중에 빈거 + 바로옆
    nearby_target = _.filter(structures,
                             lambda s: (s.structureType == STRUCTURE_EXTENSION
                                        or s.structureType == STRUCTURE_SPAWN
                                        or s.structureType == STRUCTURE_TOWER)
                                       and s.store.getFreeCapacity(RESOURCE_ENERGY) and creep.pos.isNearTo(s))
    if not len(nearby_target) and len(structure_types) > 0:
        for structure_name in structure_types:
            extra = _.filter(structures,
                             lambda s: (s.structureType == structure_name)
                                       and s.store.getFreeCapacity(RESOURCE_ENERGY) and creep.pos.isNearTo(s))
            nearby_target.extend(extra)
    if len(nearby_target):
        # 가장 가까이 있는 것 중에서도 한번에 가장 많이 넣을 수 있는걸 골라서 넣는다
        target = _.max(nearby_target, lambda s: s.store.getFreeCapacity(RESOURCE_ENERGY))
        result = creep.transfer(target, RESOURCE_ENERGY)
    return result
