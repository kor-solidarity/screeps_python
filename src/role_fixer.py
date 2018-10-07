from defs import *
from movement import *
import harvest_stuff
import random
from miscellaneous import *
from _custom_constants import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_fixer(creep, all_structures, constructions, creeps, repairs, min_wall, terminal_capacity):
    """
    기본적으로 허울러 수리와 동일하다. 다만 차이는 그거만 한다는거. 그리고 램파트 중심이다.
    상황에 따라 건설도 건든다.

    :param creep:
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
    :param creeps: creep.room.find(FIND_MY_CREEPS)
    :param repairs: look at main.
    :param min_wall: 최저 방벽.
    :param terminal_capacity: 방 안의 터미널 내 에너지 최소값.
    :return:
    """

    """
    repair_target == 수리 목표.
    pickup == 에너지 빼갈 대상.
    """

    end_is_near = 20
    # in case it's gonna die soon. this noble act is only allowed if there's a storage in the room.
    if (creep.memory.die or creep.ticksToLive < end_is_near) and _.sum(creep.carry) != 0 and creep.room.storage:
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
    elif (creep.memory.die or creep.ticksToLive < end_is_near) and creep.room.storage:
        creep.suicide()
        return

    # 자원이 없으면 초기화
    if _.sum(creep.carry) == 0 and creep.memory.laboro != 0:
        creep.memory.laboro = 0
        creep.say('🚛보급!', True)
        del creep.memory.repair_target
        del creep.memory.last_swap

    # laboro: 0 == pickup something.
    if creep.memory.laboro == 0:

        if creep.memory.pickup and \
            (not Game.getObjectById(creep.memory.pickup)
             or not Game.getObjectById(creep.memory.pickup).room.name == creep.memory.assigned_room):
            del creep.memory.pickup

        if not creep.room.name == creep.memory.assigned_room and not creep.memory.pickup:
            get_to_da_room(creep, creep.memory.assigned_roomm, False)
            return

        if not creep.memory.pickup:
            # if not creep.room.name == creep.memory.assigned_room:
            #     all_structures = Game.rooms[creep.memory.assigned_room].find(FIND_STRUCTURES)
            # 근처에 보이는거 아무거나 집는다. 허울러와 동일.
            # find anything with any resources inside
            storages = all_structures.filter(lambda s:
                                             ((s.structureType == STRUCTURE_CONTAINER
                                               or s.structureType == STRUCTURE_STORAGE)
                                              and s.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5)
                                             or (s.structureType == STRUCTURE_LINK
                                                 and s.energy >= creep.carryCapacity * .5))
            # 만일 연구소를 안채우기로 했으면 거기서도 뽑는다.
            if Memory.rooms[creep.room.name].options.fill_labs == 0:
                labs = all_structures \
                    .filter(lambda s: s.structureType == STRUCTURE_LAB and s.energy >= creep.carryCapacity * .5)
                storages.extend(labs)
            pickup_id = pick_pickup(creep, creeps, storages, terminal_capacity)
            # todo 아무것도 없는 상태에서 이 크립이 절대!! 스폰되선 안됨.... 그건 있을 수 없는 일임....
            if pickup_id == ERR_INVALID_TARGET:
                creep.say('🧟..🧠', True)
                return
            else:
                creep.memory.pickup = pickup_id
        # 집는다
        result = harvest_stuff.grab_energy(creep, creep.memory.pickup, True)

        # creep.say('진행중:', result)

        if result == ERR_NOT_IN_RANGE:
            result = harvest_stuff.grab_energy(creep, creep.memory.pickup, True)
            if result == ERR_NOT_IN_RANGE:
                # 현재 위치한 곳이 이전 틱에도 있던곳인지 확인하고 옮기는 등의 절차.
                swap_check = check_loc_and_swap_if_needed(creep, creeps, True)
                # 아무 문제 없으면 평소마냥 움직이는거.
                if swap_check == OK:
                    res = movi(creep, creep.memory.pickup, ignoreCreeps=True, reusePath=40)
                # 확인용. 아직 어찌할지 못정함....
                elif swap_check == ERR_NO_PATH:
                    creep.say('ERR_NO_PATH')
                # 위 둘 외에 다른게 넘어왔다는 소리는 실질적으로 어느 위치를 갔다는게 아니라
                # 다른 크립와 위치 바꿔치기를 시전했다는 소리. 메모리 옮긴다.
                else:
                    creep.memory.last_swap = swap_check
        # 집었으면 다음으로 넘어간다.
        elif result == 0:
            creep.say('최전선으로!⛟', True)
            creep.memory.laboro = 1
            del creep.memory.last_swap
            del creep.memory.pickup
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
        if creep.memory.repair_target and Game.getObjectById(creep.memory.repair_target).hits \
            == Game.getObjectById(creep.memory.repair_target).hitsMax:
            del creep.memory.repair_target
        # 우선 생략
        if not creep.memory.repair_target:
            if len(min_wall):
                creep.memory.repair_target = min_wall.id
            else:
                closest = creep.pos.findClosestByRange(repairs)
                if closest:
                    creep.memory.repair_target = closest.id
                else:
                    if not creep.room.memory[options][stop_fixer] == Game.time:
                        creep.room.memory[options][stop_fixer] = Game.time
                    creep.memory.die = 1

        if creep.pos.inRangeTo(Game.getObjectById(creep.memory.repair_target), 3):
            repairs = [Game.getObjectById(creep.memory.repair_target)]
        repair_on_the_way(creep, repairs, constructions, True, True)

        if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.repair_target), 6):
            # 현재 위치한 곳이 이전 틱에도 있던곳인지 확인하고 옮기는 등의 절차.
            swap_check = check_loc_and_swap_if_needed(creep, creeps, True)
            # 아무 문제 없으면 평소마냥 움직이는거.
            if swap_check == OK:
                movi(creep, creep.memory.repair_target, 3, 40, True)
            # 확인용. 아직 어찌할지 못정함....
            elif swap_check == ERR_NO_PATH:
                creep.say('ERR_NO_PATH')
            # 위 둘 외에 다른게 넘어왔다는 소리는 실질적으로 어느 위치를 갔다는게 아니라
            # 다른 크립와 위치 바꿔치기를 시전했다는 소리. 메모리 옮긴다.
            else:
                creep.memory.last_swap = swap_check
        elif creep.pos.inRangeTo(Game.getObjectById(creep.memory.repair_target), 3):
            pass
        else:
            movi(creep, creep.memory.repair_target, 3, 5)
