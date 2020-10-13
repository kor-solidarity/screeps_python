from defs import *
import harvest_stuff
import random
import miscellaneous
from action.logistics import *
import movement
import pathfinding

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_upgrader(creep, creeps, all_structures, repairs, constructions, dropped_all):
    """
    :param creep:
    :param creeps:
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param repairs: 수리대상들
    :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
    :param dropped_all: 떨군 자원과 비석
    :return:
    """
    # memory.pickup = 자원 가져올 대상.
    # upgrader = upgrades the room. UPGRADES ONLY

    # todo 터미널 안에 용량인데... 이거 추후 바꿔야함.
    terminal_capacity = 10000

    # in case it's gonna die soon. this noble act is only allowed if there's a storage in the room.
    if creep.ticksToLive < 30 and creep.store.getUsedCapacity() != 0 and creep.room.storage:
        miscellaneous.repair_on_the_way(creep, repairs, constructions)
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
    elif creep.ticksToLive < 30 and creep.room.storage:
        # 죽어가는데 굳이 턴날릴 필요 없다.
        creep.suicide()
        return

    # 혹시 딴짓하다 옆방으로 새는거에 대한 대비 - it really happened lol
    if not creep.memory.upgrade_target:
        creep.memory.upgrade_target = creep.room.controller.id
    elif not creep.memory.laboro and creep.memory.laboro != 0:
        creep.memory.laboro = 0

    # setting laboro
    if creep.store.getUsedCapacity() == 0 and creep.memory.laboro == 1:
        creep.memory.laboro = 0
        creep.say('🔄 수확하러갑세!', True)
    # if carry is full and upgrading is false: go and upgrade
    elif creep.store.getUsedCapacity() >= creep.store.getCapacity() * .5 and creep.memory.laboro == 0:
        creep.say('⚡ Upgrade', True)
        creep.memory.laboro = 1
        del creep.memory.source_num
        del creep.memory.pickup

    # when you have to harvest. laboro: 0 == HARVEST
    if creep.memory.laboro == 0:

        # todo 자원캐기 방식:
        # 업글은 렙8 도달전까지 필수임. 업글러가 무조건 최우선권 가져야함.
        # 우선 원칙적으로 컨트롤러 옆에 업글러 전용 컨테이너/링크가 있어야함. >> 확인완료
        # 없으면? 아무 컨테이너나 찾는다. >> 이거 미구현임.
        # 그것도 없으면? 캔다...
        # 이렇게 합시다.

        if creep.memory.dropped:
            harvest_stuff.pick_drops_act(creep, True)
        # 중간에 떨군거 있으면 집는다.
        if not creep.memory.dropped and len(dropped_all) > 0:
            harvest_stuff.filter_drops(creep, dropped_all, 5, True)
        if creep.memory.dropped:
            harvest_stuff.pick_drops_act(creep, True)
            return

        # 배정된 저장소가 없을 경우
        if not creep.memory.pickup:
            # 전용 컨테이너가 있고 채워짐?
            jeonyong = False
            # 업글 전용 컨테이너 목록
            la_containers = []
            # 모든 컨테이너 목록 - 업글에 용량이 없을때 대비
            total_containers = []

            pickup_id = ERR_INVALID_TARGET
            # 업글용 컨테이너/링크를 우선적으로 따로 뽑는다 - 방렙 8인 경우에만.
            if not Game.getObjectById(creep.memory.upgrade_target).level == 8:
                if creep.room.memory[STRUCTURE_CONTAINER]:
                    for s in creep.room.memory[STRUCTURE_CONTAINER]:
                        obj = Game.getObjectById(s.id)
                        if obj:
                            total_containers.append(obj)
                            if s.for_upgrade:
                                la_containers.append(obj)

                if creep.room.memory[STRUCTURE_LINK]:
                    for s in creep.room.memory[STRUCTURE_LINK]:
                        obj = Game.getObjectById(s.id)
                        if obj:
                            if s.for_store:
                                total_containers.append(obj)
                            if s.for_upgrade:
                                la_containers.append(obj)

            if creep.room.storage:
                total_containers.append(creep.room.storage)
            pickup_id = miscellaneous.pick_pickup(creep, creeps, total_containers)

            # 픽업 가져올게 없는 경우.
            # 위에 찾는게 없는 경우:
            if pickup_id == ERR_INVALID_TARGET:
                # print(creep.name, 'pickup_id == ERR_INVALID_TARGET')
                # todo 다른방법 강구요망
                if creep.room.terminal and \
                        creep.room.terminal.store[RESOURCE_ENERGY] >= \
                        terminal_capacity + creep.store.getCapacity():
                    creep.memory.pickup = creep.room.terminal.id
                elif creep.room.storage and creep.room.storage.store[RESOURCE_ENERGY] >= creep.store.getCapacity() * .5:
                    creep.memory.pickup = creep.room.storage.id
                else:
                    # print('pass')
                    pass
            else:
                creep.memory.pickup = pickup_id

        # 픽업 없으면 그냥 수동으로 동네 에너지를 캔다..
        if not creep.memory.pickup:
            if not creep.memory.source_num:
                creep.memory.source_num = creep.pos.findClosestByRange(creep.room.find(FIND_SOURCES)).id
            harvest_stuff.harvest_energy(creep, creep.memory.source_num)

        # se vi jam havas pickup, ne bezonas sercxi por ujojn
        if creep.memory.pickup:
            result = harvest_stuff.grab_energy(creep, creep.memory.pickup, True)
            if result == ERR_NOT_IN_RANGE:
                # path = _.map(creep.memory.path, lambda p: __new__(RoomPosition(p.x, p.y, creep.room.name)))
                move_by_path = movement.move_with_mem(creep, creep.memory.pickup, 0)
                if move_by_path[0] == OK and move_by_path[1]:
                        creep.memory.path = move_by_path[2]

            elif result == 0:
                del creep.memory.last_swap
                del creep.memory.pickup
                del creep.memory.path
                creep.memory.laboro = 1
            elif result == ERR_NOT_ENOUGH_ENERGY or result == ERR_INVALID_TARGET:
                del creep.memory.pickup

    # laboro: 1 == UPGRADE
    if creep.memory.laboro == 1:
        movement.ranged_move(creep, creep.memory.upgrade_target, creeps)
        miscellaneous.repair_on_the_way(creep, repairs, constructions, True)
        transfer_nearest(creep, all_structures)

    return


def run_reserver(creep):
    """
    :param creep:
    :return:
    """

    # 방이 안보이면 우선 갑시다.
    if not Game.rooms[creep.memory.assigned_room]:
        if Game.time % 2 == 0:
            creep.say('👁', True)
        movement.get_to_da_room(creep, creep.memory.assigned_room, False)
        return
    elif Game.rooms[creep.memory.assigned_room].controller:
        creep.memory.upgrade_target = Game.rooms[creep.memory.assigned_room].controller.id
    else:
        creep.suicide()

    # reserve the room
    creep_action = creep.reserveController(creep.room.controller)
    # creep.say(creep_action)
    if creep_action == ERR_NOT_IN_RANGE:
        # 5칸이내 들어가기 전까진 패스파인딩 갑시다.
        if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.upgrade_target), 5):
            move_by_path = movement.move_with_mem(creep, creep.memory.upgrade_target, 1)

            if move_by_path[0] == OK and move_by_path[1]:
                path = move_by_path[2]
            elif not move_by_path[0] == OK and not move_by_path[0] == ERR_TIRED:
                creep.say('업글중: {}'.format(move_by_path[0]))

        else:
            res = movement.movi(creep, creep.memory.upgrade_target, 1)
            del creep.memory.path
            creep.say(res)
    elif creep_action == OK:
        if Game.time % 2 == 0:
            creep.say('우리가 접수!', True)
    # not my controller == attack
    elif creep_action == ERR_INVALID_TARGET:
        creep.attackController(Game.getObjectById(creep.memory.upgrade_target))
        if Game.time % 2 == 0:
            creep.say('🔥🔥🔥🔥', True)
        else:
            creep.say('몰아내자!!', True)
    else:
        creep.say(creep_action)


def get_path(creep, creeps, target):
    """
    크립이 엉킬걸 대비해서 패스파인딩을 할때 컨트롤러 주변에 있는
    업글러도 장애물로 간주하고 거르기 하기 위한 독자 패스파인딩

    :param creep: 크립 오브젝트
    :param creeps: 방 안 모든 크립스
    :param target: 타겟 오브젝트, 거의 100% 컨트롤러일듯
    :return:
    """

    # 오브젝트가 아니면 로딩
    if typeof(target) == 'string':
        target = Game.getObjectById(target)
    # 업글러 중에 컨트롤러 범위 내에 있는애들 전부
    upgraders = _.filter(creeps,
                         lambda c: (c.memory.role == 'upgrader' or c.memory.role == 'hauler')
                         and c.memory.assigned_room == creep.room.name and c.pos.inRangeTo(target, 4))

    opts = {'trackCreeps': False, 'refreshMatrix': True, 'pass_walls': False,
            'costByArea': {'objects': upgraders, 'size': 0, 'cost': 100}}

    # 돌아올 패스 어레이
    path_arr = creep.pos.findPathTo(target,
                                 {'plainCost': 2, 'swampCost': 3, 'ignoreCreeps': True, 'range': 3,
                                  'costCallback':
                                      lambda room_name: pathfinding.Costs(room_name, opts).load_matrix()})

    return _.map(path_arr, lambda p: __new__(RoomPosition(p.x, p.y, creep.pos.roomName)))
