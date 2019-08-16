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
        del creep.memory.path

    # laboro: 0 == pickup something.
    if creep.memory.laboro == 0:

        if creep.memory.pickup and \
            (not Game.getObjectById(creep.memory.pickup)
             or not Game.getObjectById(creep.memory.pickup).room.name == creep.memory.assigned_room):
            del creep.memory.pickup

        if not creep.room.name == creep.memory.assigned_room and not creep.memory.pickup:
            get_to_da_room(creep, creep.memory.assigned_roomm, False)
            return

        # todo 떨궈진거 줍기

        # # if there is a dropped target and it's there.
        # if creep.memory.dropped:
        #     if not Game.rooms[creep.memory.assigned_room].storage:
        #         energy_only = True
        #     else:
        #         energy_only = False
        #
        #     item_pickup_res = harvest_stuff.pick_drops(creep, energy_only)
        #
        #     item = Game.getObjectById(creep.memory.dropped)
        #     # 오브젝트가 아예없음
        #     if item_pickup_res == ERR_INVALID_TARGET:
        #         creep.say("삐빅, 없음", True)
        #         del creep.memory.dropped
        #     # 내용물 없음
        #     elif item_pickup_res == ERR_NOT_ENOUGH_ENERGY:
        #         creep.say("💢 텅 비었잖아!", True)
        #         del creep.memory.dropped
        #     # 멀리있음
        #     elif item_pickup_res == ERR_NOT_IN_RANGE:
        #         movi(creep, creep.memory.dropped, 0, 10, False, 2000, '#0000FF')
        #
        #     elif item_pickup_res == OK:
        #         creep.say('♻♻♻', True)
        #         return
        # # if there's no dropped but there's dropped_all
        # if not creep.memory.dropped and len(dropped_all) > 0:
        #     # 떨어진거 확인 범위.
        #     drop_range = 5
        #     if creep.memory.all_full:
        #         drop_range = 20
        #     for drop in dropped_all:
        #         # if there's a dropped resources near 5
        #         if creep.pos.inRangeTo(drop, drop_range):
        #             # 스토리지가 없으면 에너지 외엔 못넣어서 엉킴. 통과.
        #             if not creep.room.storage:
        #                 if drop.store and not drop.store[RESOURCE_ENERGY]:
        #                     continue
        #                 elif drop.resourceType != RESOURCE_ENERGY:
        #                     continue
        #                 energy_only = True
        #             else:
        #                 energy_only = False
        #             # todo 크립당 자기 수용량을 넘지 못한다. 나중에 하는걸로.
        #             # for c in creeps:
        #             #     if c.memory.dropped == drop['id']:
        #
        #             creep.memory.dropped = drop['id']
        #
        #             item_pickup_res = pick_drops(creep, energy_only)
        #             creep.say('⛏BITCOINS!', True)
        #             if item_pickup_res == ERR_NOT_IN_RANGE:
        #                 movi(creep, creep.memory.dropped, 0, 10, False, 2000, '#0000FF')
        #             elif item_pickup_res == OK:
        #                 pass
        #             else:
        #                 creep.say('drpERR {}'.format(item_pickup_res))
        #             break
        #     if creep.memory.all_full:
        #         del creep.memory.all_full

        if not creep.memory.pickup:
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
            # 아무것도 없는 상태에서 이 크립이 절대!! 스폰되선 안됨.... 그건 있을 수 없는 일임....
            if pickup_id == ERR_INVALID_TARGET:
                creep.say('🧟..🧠', True)
                return
            else:
                creep.memory.pickup = pickup_id
        # 집는다
        result = harvest_stuff.grab_energy(creep, creep.memory.pickup, True)

        # creep.say('진행중:', result)

        if result == ERR_NOT_IN_RANGE:
            path = _.map(creep.memory.path, lambda p: __new__(RoomPosition(p.x, p.y, creep.room.name)))
            # 메모리에 있는걸 최우선적으로 찾는다.
            move_by_path = move_with_mem(creep, creep.memory.pickup, 0, path)
            if move_by_path[0] == OK and move_by_path[1]:
                creep.memory.path = move_by_path[2]

        # 집었으면 다음으로 넘어간다.
        elif result == 0:
            creep.say('최전선으로!⛟', True)
            creep.memory.laboro = 1
            del creep.memory.path
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
        if not Game.getObjectById(creep.memory.repair_target):
            del creep.memory.repair_target
        if creep.memory.repair_target and Game.getObjectById(creep.memory.repair_target).hits \
                == Game.getObjectById(creep.memory.repair_target).hitsMax:
            del creep.memory.repair_target
        # 표적이 없으면 찾는다. 우선 가장 체력낮은걸 찾는다
        if not creep.memory.repair_target:
            if len(min_wall):
                creep.memory.repair_target = min_wall.id
            # 없다면 수리할 벽은 목표치만큼 다 채웠단거니 아무거나 찾는다.
            else:
                closest = creep.pos.findClosestByRange(repairs)
                if closest:
                    creep.memory.repair_target = closest.id
                # 그마저도 없으면 더이상 수리크립이 있을 이유가 없음.
                else:

                    creep.memory.die = 1
                    return

        if creep.pos.inRangeTo(Game.getObjectById(creep.memory.repair_target), 3):
            repairs = [Game.getObjectById(creep.memory.repair_target)]
        repair_on_the_way(creep, repairs, constructions, True, True)

        if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.repair_target), 6):
            path = _.map(creep.memory.path, lambda p: __new__(RoomPosition(p.x, p.y, creep.room.name)))
            # 메모리에 있는걸 최우선적으로 찾는다.
            move_by_path = move_with_mem(creep, creep.memory.repair_target, 3, path)
            if move_by_path[0] == OK and move_by_path[1]:
                creep.memory.path = move_by_path[2]

        elif creep.pos.inRangeTo(Game.getObjectById(creep.memory.repair_target), 3):
            pass
        else:
            if creep.memory.path:
                del creep.memory.path
            movi(creep, creep.memory.repair_target, 3, 5)
