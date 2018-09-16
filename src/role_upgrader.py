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

        if not creep.memory.pickup:
            # 전용 컨테이너가 있고 채워짐?
            jeonyong = False
            la_containers = []
            if creep.room.memory[STRUCTURE_CONTAINER]:
                for s in creep.room.memory[STRUCTURE_CONTAINER]:
                    obj = Game.getObjectById(s.id)
                    if obj and s.for_upgrade:
                        la_containers.append(obj)
                # 가장 먼져 전용 컨테이너를 찾는다.
                pickup_id = pick_pickup(creep, creeps, la_containers, 10000, True)
            # 전용 컨테이너를 못찾으면 끝.
            if pickup_id == ERR_INVALID_TARGET:
                # todo 업글용 컨테이너 뽑는코드 따로 만들어야함.
                # find any storages with any energy inside
                containers_or_links = all_structures.filter(lambda s: (s.structureType == STRUCTURE_CONTAINER
                                                            and s.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5))
                # 링크를 찾는다.
                links = []
                for link in creep.room.memory[STRUCTURE_LINK]:
                    if not link:
                        continue
                    # 저장용인 링크만 중요함.
                    if link.for_store:
                        if Game.getObjectById(link.id):
                            links.extend([Game.getObjectById(link.id)])
                containers_or_links.extend(links)
                if creep.room.storage:
                    containers_or_links.extend([creep.room.storage])

                # 가장 가까운곳에서 빼오는거임. 원래 스토리지가 최우선이었는데 바뀜.
                pickup_id = pick_pickup(creep, creeps, containers_or_links, 10000, True)

            if pickup_id == ERR_INVALID_TARGET:
                print(creep.name, 'pickup_id == ERR_INVALID_TARGET')
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
        creep.say(res)
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
