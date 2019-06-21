from defs import *
import harvest_stuff
import random
from miscellaneous import *
from movement import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_upgrader(creep, creeps, all_structures, repairs, constructions):
    """
    :param creep:
    :param creeps:
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param repairs: 수리대상들
    :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
    :return:
    """
    # memory.pickup = 자원 가져올 대상.
    # upgrader = upgrades the room. UPGRADES ONLY

    # todo 터미널 안에 용량인데... 이거 추후 바꿔야함.
    terminal_capacity = 10000

    # in case it's gonna die soon. this noble act is only allowed if there's a storage in the room.
    if creep.ticksToLive < 30 and _.sum(creep.carry) != 0 and creep.room.storage:
        creep.say('endIsNear')
        for minerals in Object.keys(creep.carry):
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
    if _.sum(creep.carry) == 0 and creep.memory.laboro == 1:
        creep.memory.laboro = 0
        creep.say('🔄 수확하러갑세!', True)
    # if carry is full and upgrading is false: go and upgrade
    elif _.sum(creep.carry) >= creep.carryCapacity * .5 and creep.memory.laboro == 0:
        creep.say('⚡ Upgrade', True)
        creep.memory.laboro = 1
        del creep.memory.source_num

    # when you have to harvest. laboro: 0 == HARVEST
    if creep.memory.laboro == 0:

        # todo 자원캐기 방식: 지랄하지말고 컨테이너 다 뽑아갑시다.
        # 업글은 렙8 도달전까지 필수임. 업글러가 무조건 최우선권 가져야함.
        # 우선 원칙적으로 컨트롤러 옆에 업글러 전용 컨테이너/링크가 있어야함. >> 확인완료
        # 없으면? 아무 컨테이너나 찾는다. >> 이거 미구현임.
        # 그것도 없으면? 캔다...
        # 이렇게 합시다.

        # 배정된 저장소가 없을 경우
        if not creep.memory.pickup:
            # 전용 컨테이너가 있고 채워짐?
            jeonyong = False
            # 전용 컨테이너 목록
            la_containers = []

            pickup_id = ERR_INVALID_TARGET
            # # 업글용 컨테이너 따로 뽑는다 - 방렙 8이 아니고 방에 컨테이너가 있는 경우.
            # if not Game.getObjectById(creep.memory.upgrade_target).level == 8\
            #         and creep.room.memory[STRUCTURE_CONTAINER]:
            #     for s in creep.room.memory[STRUCTURE_CONTAINER]:
            #         obj = Game.getObjectById(s.id)
            #         if obj and s.for_upgrade:
            #             la_containers.append(obj)
            #     for s in creep.room.memory[STRUCTURE_LINK]:
            #         obj = Game.getObjectById(s.id)
            #         if obj and s.for_upgrade:
            #             la_containers.append(obj)
            #     # 가장 먼져 전용 컨테이너를 찾는다.
            #     pickup_id = pick_pickup(creep, creeps, la_containers, 10000, True)
            #     # print('ch1 pickup_id', pickup_id)

            # --------------------새작업
            # 소속된 업글용 컨테이너와 링크를 찾는다.
            # testing - 기존 업글전용으로 배정된 것 제외한 모든 컨테이너가 대상.
            for s in creep.room.memory[STRUCTURE_CONTAINER]:
                obj = Game.getObjectById(s.id)
                # if obj and s.for_upgrade:
                if obj:
                    la_containers.append(obj)

            for s in creep.room.memory[STRUCTURE_LINK]:
                obj = Game.getObjectById(s.id)
                # if obj and s.for_upgrade:
                if obj and s.for_store:
                    la_containers.append(obj)
            # testing - 이 조건 폐지.
            # 만일 렙 8인 경우, 즉, 업글용 컨테이너가 필요 없어졌을 경우, 스토리지에서 뽑아가도 된다.
            # if not Game.getObjectById(creep.memory.upgrade_target).level == 8 \
            #         and creep.room.memory[STRUCTURE_CONTAINER]:
            if creep.room.storage:
                la_containers.append(creep.room.storage)
            # 이제 픽업 시전
            pickup_id = pick_pickup(creep, creeps, la_containers, 10000, True)
            # --------------------새작업 끝
            # # 전용 컨테이너를 못찾으면 끝.
            # if pickup_id == ERR_INVALID_TARGET:
            #     la_containers = []
            #     # find any storages with any energy inside
            #     # containers_or_links = all_structures.filter(lambda s: (s.structureType == STRUCTURE_CONTAINER
            #     #                                             and s.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5))
            #     #
            #     for s in creep.room.memory[STRUCTURE_CONTAINER]:
            #         obj = Game.getObjectById(s.id)
            #         if obj and s.for_upgrade:
            #             la_containers.append(obj)
            #     for s in creep.room.memory[STRUCTURE_LINK]:
            #         obj = Game.getObjectById(s.id)
            #         if obj and s.for_upgrade:
            #             la_containers.append(obj)
            #
            #     # 링크를 찾는다.
            #     # links = []
            #     # for link in creep.room.memory[STRUCTURE_LINK]:
            #     #     if not link:
            #     #         continue
            #     #     # 저장용인 링크만 중요함.
            #     #     if link.for_store:
            #     #         if Game.getObjectById(link.id):
            #     #             links.extend([Game.getObjectById(link.id)])
            #     # containers_or_links.extend(links)
            #     if creep.room.storage:
            #         la_containers.append(creep.room.storage)
            #
            #     # 가장 가까운곳에서 빼오는거임. 원래 스토리지가 최우선이었는데 바뀜.
            #     pickup_id = pick_pickup(creep, creeps, la_containers, 10000, True)

            # 픽업 가져올게 없는 경우.
            # 위에 찾는게 없는 경우:
            if pickup_id == ERR_INVALID_TARGET:
                # print(creep.name, 'pickup_id == ERR_INVALID_TARGET')
                # todo 다른방법 강구요망
                if creep.room.terminal and \
                        creep.room.terminal.store[RESOURCE_ENERGY] >= \
                        terminal_capacity + creep.carryCapacity:
                    creep.memory.pickup = creep.room.terminal.id
                elif creep.room.storage and creep.room.storage.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5:
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
                # 현재 위치한 곳이 이전 틱에도 있던곳인지 확인하고 옮기는 등의 절차.
                swap_check = check_loc_and_swap_if_needed(creep, creeps, True)
                # 아무 문제 없으면 평소마냥 움직이는거.
                if swap_check == OK:
                    movi(creep, creep.memory.pickup, 0, 40, True)
                # 확인용. 아직 어찌할지 못정함....
                elif swap_check == ERR_NO_PATH:
                    creep.say('ERR_NO_PATH')
                # 위 둘 외에 다른게 넘어왔다는 소리는 실질적으로 어느 위치를 갔다는게 아니라
                # 다른 크립와 위치 바꿔치기를 시전했다는 소리. 메모리 옮긴다.
                else:
                    creep.memory.last_swap = swap_check
            elif result == 0:
                del creep.memory.last_swap
                del creep.memory.pickup
                creep.memory.laboro = 1
            elif result == ERR_NOT_ENOUGH_ENERGY or result == ERR_INVALID_TARGET:
                del creep.memory.pickup

    # laboro: 1 == UPGRADE
    if creep.memory.laboro == 1:

        if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.upgrade_target), 6):
            # 현재 위치한 곳이 이전 틱에도 있던곳인지 확인하고 옮기는 등의 절차.
            swap_check = check_loc_and_swap_if_needed(creep, creeps, True)
            # 아무 문제 없으면 평소마냥 움직이는거.
            if swap_check == OK:
                movi(creep, creep.memory.upgrade_target, 3, 40, True)
            # 확인용. 아직 어찌할지 못정함....
            elif swap_check == ERR_NO_PATH:
                creep.say('ERR_NO_PATH')
            # 위 둘 외에 다른게 넘어왔다는 소리는 실질적으로 어느 위치를 갔다는게 아니라
            # 다른 크립와 위치 바꿔치기를 시전했다는 소리. 메모리 옮긴다.
            else:
                creep.memory.last_swap = swap_check
        else:
            movi(creep, creep.memory.upgrade_target, 3, 5)

        repair_on_the_way(creep, repairs, constructions, True)

        # up_tar = Game.getObjectById(creep.memory.upgrade_target)
        # result = creep.upgradeController(up_tar)
        # # if there's no controller around, go there.
        # if result == ERR_NOT_IN_RANGE:
        #     if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.upgrade_target), 6):
        #         # 현재 위치한 곳이 이전 틱에도 있던곳인지 확인하고 옮기는 등의 절차.
        #         swap_check = check_loc_and_swap_if_needed(creep, creeps, True)
        #         # 아무 문제 없으면 평소마냥 움직이는거.
        #         if swap_check == OK:
        #             movi(creep, creep.memory.upgrade_target, 3, 40, True)
        #         # 확인용. 아직 어찌할지 못정함....
        #         elif swap_check == ERR_NO_PATH:
        #             creep.say('ERR_NO_PATH')
        #         # 위 둘 외에 다른게 넘어왔다는 소리는 실질적으로 어느 위치를 갔다는게 아니라
        #         # 다른 크립와 위치 바꿔치기를 시전했다는 소리. 메모리 옮긴다.
        #         else:
        #             creep.memory.last_swap = swap_check
        #     else:
        #         movi(creep, creep.memory.upgrade_target, 3, 10)

    return


def run_reserver(creep):
    """
    :param creep:
    :return:
    """

    # 메모리에 표적을 만들어둔다.
    if not creep.memory.upgrade_target:
        # print('rooms[creep.memory.assigned_room]', Game.rooms[creep.memory.assigned_room])
        if not Game.rooms[creep.memory.assigned_room]:
            get_to_da_room(creep, creep.memory.assigned_room, False)
            return
        elif Game.rooms[creep.memory.assigned_room].controller:
            creep.memory.upgrade_target = Game.rooms[creep.memory.assigned_room].controller.id
        else:
            creep.suicide()

    # reserve the room
    creep_action = creep.reserveController(creep.room.controller)
    # creep.say(creep_action)
    if creep_action == ERR_NOT_IN_RANGE:
        # res = creep.moveTo(Game.getObjectById(creep.memory.upgrade_target),
        #                    {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
        res = movi(creep, creep.memory.upgrade_target)
        # creep.say(res)
    elif creep_action == OK:
        if Game.time % 2 == 0:
            creep.say('🇰🇵 🇰🇷', True)
        else:
            creep.say('ONWARD!!', True)
    # not my controller == attack
    elif creep_action == ERR_INVALID_TARGET:
        creep.attackController(Game.getObjectById(creep.memory.upgrade_target))
        if Game.time % 2 == 0:
            creep.say('🔥🔥🔥🔥', True)
        else:
            creep.say('몰아내자!!', True)
    else:
        creep.say(creep_action)

    # try:
    #
    #     # if creep is not in it's flag's room.
    #     if creep.room.name != creep.memory.assigned_room:
    #         get_to_da_room(creep, creep.memory.assigned_room, False)
    #     # if in.
    #     else:
    #         # reserve the room
    #         creep_action = creep.reserveController(creep.room.controller)
    #         if creep_action == ERR_NOT_IN_RANGE:
    #             res = creep.moveTo(creep.room.controller, {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
    #             creep.say(res)
    #         elif creep_action == OK:
    #             if Game.time % 2 == 0:
    #                 creep.say('🇰🇵 🇰🇷', True)
    #             else:
    #                 creep.say('ONWARD!!', True)
    #         # not my controller == attack
    #         elif creep_action == ERR_INVALID_TARGET:
    #             creep.attackController(creep.room.controller)
    #             if Game.time % 2 == 0:
    #                 creep.say('🔥🔥🔥🔥', True)
    #             else:
    #                 creep.say('몰아내자!!', True)
    #         else:
    #             creep.say(creep_action)
    #
    # except:
    #     print("ERR!!!")
    #     creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
