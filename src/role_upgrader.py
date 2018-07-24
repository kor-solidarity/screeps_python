from defs import *
import harvest_stuff
import random
import miscellaneous

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_upgrader(creep, creeps, all_structures):
    """
    :param creep:
    :param creeps:
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :return:
    """
    # memory.pickup = 자원 가져올 대상.
    # upgrader = upgrades the room. UPGRADES ONLY
    vis_key = "visualizePathStyle"
    stroke_key = "stroke"

    # in case it's gonna die soon. this noble act is only allowed if there's a storage in the room.
    # todo 자원 뽑아오는게 스토리지가 아닐 경우 스토리지로 반납하러 가는길에 죽을 가능성이 있음.
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
        creep.memory.upgrade_target = creep.room.controller['id']
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
        # se vi jam havas pickup, ne bezonas sercxi por ujojn
        if creep.memory.pickup:
            result = harvest_stuff.grab_energy(creep, creep.memory.pickup, True)
            # print('result', result)
            if result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.pickup),
                             {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
            elif result == 0:
                del creep.memory.pickup
                creep.memory.laboro = 1
            elif result == ERR_NOT_ENOUGH_ENERGY or result == ERR_INVALID_TARGET:
                del creep.memory.pickup
            return

        if not creep.memory.pickup:
            # find any storages with any energy inside
            containers_or_links = all_structures.filter(lambda s: (s.structureType == STRUCTURE_CONTAINER
                                                        and s.store[RESOURCE_ENERGY] > 0)
                                                        or (s.structureType == STRUCTURE_LINK
                                                            and s.energy >= 150
                                                            and not (s.pos.x < 5 or s.pos.x > 44
                                                                     or s.pos.y < 5 or s.pos.y > 44)))
            # 가장 가까운곳에서 빼오는거임. 원래 스토리지가 최우선이었는데 바뀜.
            pickup_id = miscellaneous.pick_pickup(creep, creeps, containers_or_links, 10000, True)

            if pickup_id == ERR_INVALID_TARGET:
                pass
            else:
                creep.memory.pickup = pickup_id

        if not creep.memory.pickup:
            if not creep.memory.source_num:
                creep.memory.source_num = creep.pos.findClosestByRange(creep.room.find(FIND_SOURCES)).id
            harvest_stuff.harvest_energy(creep, creep.memory.source_num)

    # laboro: 1 == UPGRADE
    elif creep.memory.laboro == 1:

        result = creep.upgradeController(Game.getObjectById(creep.memory.upgrade_target))
        # if there's no controller around, go there.
        if result == ERR_NOT_IN_RANGE:
            creep.moveTo(Game.getObjectById(creep.memory.upgrade_target),
                         {vis_key: {stroke_key: '#FFFFFF'}, 'range': 3})

    return


def run_reserver(creep):
    """
    :param creep:
    :return:
    """
    try:

        # if creep is not in it's flag's room.
        if creep.room.name != creep.memory.assigned_room:
            miscellaneous.get_to_da_room(creep, creep.memory.assigned_room, False)
        # if in.
        else:
            # reserve the room
            creep_action = creep.reserveController(creep.room.controller)
            if creep_action == ERR_NOT_IN_RANGE:
                creep.moveTo(creep.room.controller, {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
            elif creep_action == OK:
                if Game.time % 2 == 0:
                    creep.say('🇰🇵 🇰🇷', True)
                else:
                    creep.say('ONWARD!!', True)
            # not my controller == attack
            elif creep_action == ERR_INVALID_TARGET:
                creep.attackController(creep.room.controller)
                if Game.time % 2 == 0:
                    creep.say('🔥🔥🔥🔥', True)
                else:
                    creep.say('몰아내자!!', True)
            else:
                creep.say(creep_action)

    except:
        print("ERR!!!")
        creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
