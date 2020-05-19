from defs import *
import random
import movement
import miscellaneous

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def collector(creep, creeps, dropped_all, all_structures):
    """
    대충 옆방에 있는 떨어져있는 모든 찌꺼기들 처리한다.
    :return:
    """
    # 주변에 떨어져있는 자원 집는게 유일한 일임.

    # in case it's gonna die soon. this noble act is only allowed if there's a storage in the room.
    # todo 자원 뽑아오는게 스토리지가 아닐 경우 스토리지로 반납하러 가는길에 죽을 가능성이 있음.
    if creep.ticksToLive < 50 and creep.store.getUsedCapacity() != 0 and creep.room.storage:
        creep.say('endIsNear')
        for minerals in Object.keys(creep.store):
            # print('minerals:', minerals)
            transfer_minerals_result = creep.transfer(creep.room.storage, minerals)
            # print(transfer_minerals_result)
            if transfer_minerals_result == ERR_NOT_IN_RANGE:
                creep.moveTo(creep.room.storage, {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 10})
                break
            elif transfer_minerals_result == 0:
                break
        return
    elif creep.ticksToLive < 50 and creep.room.storage:
        # 죽어가는데 굳이 턴날릴 필요 없다.
        creep.suicide()
        return

    if creep.hitsMax > creep.hits:
        creep.heal()
    
    # setting laboro
    if creep.store.getUsedCapacity() == 0 and creep.memory.laboro == 1:
        creep.memory.laboro = 0
        creep.say('🧹쓸러~', True)
    # if carry is full and upgrading is false: go and upgrade
    elif creep.store.getUsedCapacity() == creep.store.getCapacity() and creep.memory.laboro == 0:
        creep.say('티끌모아태산', True)
        creep.memory.laboro = 1

    # 0이면 채취.
    if creep.memory.laboro == 0:
        # 채취대상방에 있는지 확인한다. 없으면 우선 이동한다.
        if creep.room.name != creep.memory.assigned_room:
            movement.get_to_da_room(creep, creep.memory.assigned_room)
            return
        else:
            # 방에 빈 자원이 있는지 확인한다.
            if creep.memory.target:
                res = creep.pickup(creep.memory.target)

                if res == ERR_NOT_IN_RANGE:
                    move = movement.movi(creep, creep.memory.target, reusePath=20)
                elif res == ERR_FULL:
                    creep.say('꽉차면 귀환!', True)
                    creep.memory.laboro = 1

                elif res == ERR_INVALID_TARGET:
                    del creep.memory.target
            # 목표물이 없을 경우 찾는다...
            else:
                # 찾고 거길 향해 전진.
                closest_resource = creep.pos.findClosestByRange(dropped_all)
                if not closest_resource:
                    # 만일 소스가 없으면 철거반 따라간다
                    demolition_man = creeps.filter(lambda c: c.memory.role == 'demolition'
                                                               and c.memory.assigned_room == creep.memory.assigned_room)
                    closest_guy = creep.pos.findClosestByRange(demolition_man)

                    move = movement.movi(creep, closest_guy.id, reusePath=20)
                else:
                    creep.memory.target = closest_resource.id

                    move = movement.movi(creep, creep.memory.target, reusePath=20)

                if move == ERR_INVALID_TARGET:
                    movement.get_to_da_room(creep, creep.memory.assigned_room)

    # 1이면 복귀한다.
    elif creep.memory.laboro == 1:
        # haul_target == 자원넣을 통.
        if not creep.memory.haul_target:
            # 원래 방으로 돌아가고 본다.
            if creep.room.name != creep.memory.home_room:
                movement.get_to_da_room(creep, creep.memory.home_room)
            else:
                # 만일 가지고 있는게 에너지 뿐일 경우 - 링크로 가도 됨.
                if creep.store.getUsedCapacity() == creep.store[RESOURCE_ENERGY]:
                    # 에너지만 있으면 1, 더 있으면 2
                    creep.memory.sources = 1
                    containers_and_links = all_structures.filter(lambda s: s.structureType == STRUCTURE_CONTAINER
                                                                 or s.structureType == STRUCTURE_LINK)
                else:
                    creep.memory.sources = 2
                    containers_and_links = all_structures.filter(lambda s: s.structureType == STRUCTURE_CONTAINER)

                haul_target = creep.pos.findClosestByRange(containers_and_links)

                # 배정한다
                creep.memory.haul_target = haul_target.id

                move = movement.movi(creep, creep.memory.haul_target, reusePath=20)

        # 통이 있으면! 가서 넣는다
        else:

            if creep.memory.sources == 2:
                # 만일 가진자원이 둘 이상인데 링크에 배정된 상태면 삭제하고 재배치해야함.
                if Game.getObjectById(creep.memory.haul_target).structureType == STRUCTURE_LINK:
                    del creep.memory.haul_target
                    containers = all_structures.filter(lambda s: s.structureType == STRUCTURE_CONTAINER)

                    haul_target = creep.pos.findClosestByRange(containers)
                    creep.memory.haul_target = haul_target.id

            for resource in Object.keys(creep.store):
                storage_transfer = creep.transfer(Game.getObjectById(creep.memory.haul_target), resource)

                if storage_transfer == ERR_NOT_IN_RANGE:
                    move_it = movement.movi(creep, creep.memory.haul_target)
                    # 사각지대 안에 갇힐 경우 크립이 겹친거니 바로옆 크립 아무한테나 간다.
                    if move_it == ERR_NO_PATH:
                        for c in Game.creeps:
                            if creep.pos.inRangeTo(c, 1) and not c.name == creep.name:
                                creep.moveTo(c)
                                break
                    break
                elif storage_transfer == 0:
                    break
                else:
                    print('carrier transfer error:', storage_transfer)
            # move = movement.movi(creep, creep.memory.haul_target, reusePath=20)