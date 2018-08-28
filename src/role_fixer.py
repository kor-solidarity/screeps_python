from defs import *
from movement import *
import harvest_stuff
import random
import miscellaneous
from _custom_constants import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_fixer(creep, all_structures, constructions, creeps, dropped_all, repairs, terminal_capacity):
    """
    :param creep:
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
    :param creeps: creep.room.find(FIND_MY_CREEPS)
    :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
    :param repairs: look at main.
    :param terminal_capacity: 방 안의 터미널 내 에너지 최소값.
    :return:
    """
    # todo 이 픽서가 하는 역할:
    # 기본적으로 허울러 수리와 동일하다. 다만 차이는 그거만 한다는거. 그리고 램파트 중심이다.

    """
    repair_target == 수리 목표.
    pickup == 에너지 빼갈 대상.
    """

    end_is_near = 20
    # in case it's gonna die soon. this noble act is only allowed if there's a storage in the room.
    if creep.ticksToLive < end_is_near and _.sum(creep.carry) != 0 and creep.room.storage:
        creep.say('endIsNear')
        if creep.memory.haul_target:
            del creep.memory.haul_target
        elif creep.memory.pickup:
            del creep.memory.pickup
        for minerals in Object.keys(creep.carry):
            # print('minerals:', minerals)
            transfer_minerals_result = creep.transfer(creep.room.storage, minerals)
            # print(transfer_minerals_result)
            if transfer_minerals_result == ERR_NOT_IN_RANGE:
                creep.moveTo(creep.room.storage, {'visualizePathStyle': {'stroke': '#ffffff'}})
                break
            elif transfer_minerals_result == 0:
                break
        return
    elif creep.ticksToLive < end_is_near:
        creep.suicide()
        return

    # 자원이 없으면 초기화
    if _.sum(creep.carry) == 0 and creep.memory.laboro != 0:
        creep.memory.laboro = 0
        creep.say('🚛보급!', True)
        del creep.memory.repair_target

    # laboro: 0 == pickup something.
    if creep.memory.laboro == 0:

        if creep.memory.pickup and not Game.getObjectById(creep.memory.pickup):
            del creep.memory.pickup

        if not creep.memory.pickup:
            # 근처에 보이는거 아무거나 집는다. 허울러와 동일.
            # find anything with any resources inside
            storages = all_structures.filter(lambda s:
                                             ((s.structureType == STRUCTURE_CONTAINER
                                               or s.structureType == STRUCTURE_STORAGE)
                                              and s.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5)
                                             or (s.structureType == STRUCTURE_LINK
                                                 and s.energy >= creep.carryCapacity * .5))
            pickup_id = miscellaneous.pick_pickup(creep, creeps, storages, terminal_capacity)
            # 만일 연구소를 안채우기로 했으면 거기서도 뽑는다.
            if Memory.rooms[creep.room.name].options.fill_labs == 0:
                labs = all_structures \
                    .filter(lambda s: s.structureType == STRUCTURE_LAB and s.energy >= creep.carryCapacity * .5)
                storages.extend(labs)
        # todo 아무것도 없는 상태에서 이게 절대!! 스폰되선 안됨.... 그건 있을 수 없는 일임....
        if pickup_id == ERR_INVALID_TARGET:
            pass
        else:
            creep.memory.pickup = pickup_id
        # 집는다
        result = harvest_stuff.grab_energy(creep, creep.memory.pickup, True)

        creep.say('진행중:', result)

        if result == ERR_NOT_IN_RANGE:
            move_it = creep.moveTo(Game.getObjectById(creep.memory.pickup),
                                   {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 25})
            if move_it == ERR_NO_PATH:
                for c in creeps:
                    if creep.pos.inRangeTo(c, 1) and not c.name == creep.name:
                        mv = creep.moveTo(c)
                        break
        # 집었으면 다음으로 넘어간다.
        elif result == 0:
            creep.say('최전선으로!⛟', True)
            creep.memory.laboro = 1
        # 내용물이 없으면 삭제하고 다른거 찾아야함.
        elif result == ERR_NOT_ENOUGH_ENERGY:
            creep.say('💢 없잖음!', True)
            del creep.memory.pickup
            return
        else:
            del creep.memory.pickup
            return

    # 1 == 본격적인 수리작업 시작.
    if creep.memory.laboro == 1:
        # 우선 생략
        # if not creep.memory.repair_target:

        # todo 임시로 우선 이리 간단히 둔건데 추후 더 만들어놔야함.

        # 기본적으로 수리는 벽, 방어막 중심으로 짠다. 만일 없으면.... 애초에 이걸 뽑는 이유가 없음.
        if len(repairs) > 0:
            creep.memory.repair_target = creep.pos.findClosestByRange(repairs).id
            repair = Game.getObjectById(creep.memory.repair_target)
        # no repairs? GTFO
        else:
            creep.memory.priority = 0
            return
        repair_result = creep.repair(repair)
        # print('{} the {}: repair_result {}'.format(creep.name, creep.memory.role, repair_result))
        if repair_result == ERR_NOT_IN_RANGE:
            creep.moveTo(repair, {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 10, 'range': 3})
        elif repair_result == ERR_INVALID_TARGET:
            del creep.memory.repair_target
