from defs import *
import harvest_stuff
import random

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_upgrader(creep, all_structures):
    """
    :param creep:
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :return:
    """
    # upgrader = upgrades the room. UPGRADES ONLY
    vis_key = "visualizePathStyle"
    stroke_key = "stroke"

    # in case it's gonna die soon. this noble act is only allowed if there's a storage in the room.
    if creep.ticksToLive < 30 and _.sum(creep.carry) != 0 and creep.room.storage:
        creep.say('endIsNear')
        for minerals in Object.keys(creep.carry):
            print('minerals:', minerals)
            transfer_minerals_result = creep.transfer(creep.room.storage, minerals)
            print(transfer_minerals_result)
            if transfer_minerals_result == ERR_NOT_IN_RANGE:
                creep.moveTo(creep.room.storage, {'visualizePathStyle': {'stroke': '#ffffff'}})
                break
            elif transfer_minerals_result == 0:
                break
        return
    elif creep.ticksToLive < 30 and creep.room.storage:
        creep.say('TTL:' + creep.ticksToLive)
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
            if result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.pickup),
                             {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
            elif result == 0:
                del creep.memory.pickup
                creep.memory.laboro = 1
            return

        # find containers that are full.
        full_containers = all_structures.filter(lambda s: ((s.structureType == STRUCTURE_STORAGE
                                                            and s.store[RESOURCE_ENERGY] >- creep.carryCapacity * .5)
                                                           or (s.structureType == STRUCTURE_CONTAINER
                                                               and s.store[RESOURCE_ENERGY] >= s.storeCapacity * .9)))
        # get energy from these firsthand
        if len(full_containers) > 0:

            if not creep.memory.pickup:
                # randomly choose which storage to go to
                random_storage_num = random.randint(0, len(full_containers) - 1)
                storage = full_containers[random_storage_num]
                creep.memory.pickup = storage['id']

            result = harvest_stuff.grab_energy(creep, creep.memory.pickup, True)

            if result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.pickup),
                             {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
            elif result == 0:
                creep.memory.laboro = 1
            return

        # find any storages with any energy inside
        storages = all_structures.filter(lambda s: ((s.structureType == STRUCTURE_STORAGE
                                                     or s.structureType == STRUCTURE_CONTAINER)
                                                    and s.store[RESOURCE_ENERGY] > 0)
                                                   or (s.structureType == STRUCTURE_LINK
                                                       and s.energy >= 150
                                                       and not (
            s.pos.x < 5 or s.pos.x > 44 or s.pos.y < 5 or s.pos.y > 44))
                                         )
        try:  # if there's no storage, just pass
            if creep.room.storage.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5:
                storages.push(creep.room.storage)
        except:
            pass
        # if there are any storages to harvest from, go get it.
        if len(storages) > 0:
            if not creep.memory.pickup:
                # pick storage firsthand if there are any
                if creep.room.storage and creep.room.storage.store[RESOURCE_ENERGY] > creep.carryCapacity * .8:
                    creep.memory.pickup = creep.room.storage.id
                else:
                    # randomly choose which storage to go to
                    random_storage_num = random.randint(0, len(storages) - 1)
                    storage = storages[random_storage_num]
                    creep.memory.pickup = storage['id']

            result = harvest_stuff.grab_energy(creep, creep.memory.pickup, True)
            if result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.pickup),
                             {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
            elif result == 0:
                del creep.memory.pickup
                creep.memory.laboro = 1
        # if not, manually harvest
        else:
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

        if _.sum(creep.carry) == 0:
            creep.memory.laboro = 0
            creep.say('🔄 수확하러갑세!', True)


def run_reserver(creep):
    """
    :param creep:
    :return:
    """
    try:

        # if creep is not in it's flag's room.
        if creep.room.name != Game.flags[creep.memory.flag_name].room.name:
            # go.
            creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'}})
            return
        # if in.
        else:
            # reserve the room
            creep_action = creep.reserveController(creep.room.controller)
            if creep_action == ERR_NOT_IN_RANGE:
                creep.moveTo(creep.room.controller, {'visualizePathStyle': {'stroke': '#ffffff'}})
                return
            elif creep_action == OK:
                if Game.time % 2 == 0:
                    creep.say('🏴🏴🏴🏴🏴', True)
                else:
                    creep.say('ONWARD!!', True)
            else:
                creep.say(creep_action)

    except:
        print("ERR!!!")
        creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'}})
