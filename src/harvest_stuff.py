from defs import *
import random

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')

# 자원 얻는 방식에 대한 그 모든것은 여기로 간다.


def harvest_energy(creep, source_num):
    """
    자원을 캐고 없으면 다음껄로(다음번호) 보낸다.

    :param creep: the creep. do i have to tell you? intended for harvesters and upgraders.
    :param source_num: ID of the energy source.
    :return: ain't returning shit.
    """
    vis_key = "visualizePathStyle"
    stroke_key = "stroke"

    # if capacity is full, get to next work.
    # DELETE ALL THIS AND MOVE THEM TO CREEPS.
    # THIS FUNC. MUST WORK ONLY ON HARVESTING
    if _.sum(creep.carry) == creep.carryCapacity:
        creep.memory.laboro = 1
        if creep.memory.role == 'harvester':
            creep.say('民衆民主主義萬世!', True)
        else:
            creep.say('일꾼생산해라좀', True)
        return 0

    # activate the harvest cmd.
    harvested = creep.harvest(Game.getObjectById(source_num))

    # is sources too far out?
    # creep.say(harvested)
    if harvested == ERR_NOT_IN_RANGE:
        # then go.
        creep.moveTo(Game.getObjectById(source_num), {vis_key: {stroke_key: '#ffffff'}})

    # did the energy from the sources got depleted?
    # PROCEED TO NEXT PHASE IF THERE ARE ANYTHING IN CARRY
    # well.... not much important now i guess.
    elif harvested == ERR_NOT_ENOUGH_RESOURCES:
        # do with what you have anyways...
        if _.sum(creep.carry) > 0:
            creep.say('🐜 SOURCES')
            creep.memory.laboro = 1

    return harvested


def grab_energy(creep, pickup, only_energy, min_capacity=.4):
    """
    grabbing energy from local storages(container, storage, etc.)
    :param creep:
    :param pickup: creep.memory. 가장 가까운 또는 목표 storage의 ID
    :param only_energy: bool
    :param min_capacity:
    :return: any creep.withdraw return codes
    """
    # we will make new script for some stuff.

    # if there's no energy in the pickup target, delete it
    try:
        if Game.getObjectById(pickup).store:
            if _.sum(Game.getObjectById(pickup).store) < (creep.carryCapacity - _.sum(creep.carry)) * min_capacity:
                del pickup
                # print('checkpoint?')
                return ERR_NOT_ENOUGH_ENERGY
        else:
            if Game.getObjectById(pickup).energy < (creep.carryCapacity - _.sum(creep.carry)) * min_capacity:
                del pickup
                # print('checkpoint??')
                return ERR_NOT_ENOUGH_ENERGY

    # if there's something else popped up, you suck.
    except:
        print('ERROR HAS OCCURED!!!!!!!!!!!!!!!!!!!!')
        print('{} the {} in room {}, pickup obj: {}'.format(creep.name, creep.memory.role
                                                            , creep.room.name, Game.getObjectById(pickup)))
        creep.say('ERROR!')
        return ERR_INVALID_TARGET

    # check if memory.pickup has store API or not
    if Game.getObjectById(pickup).store:
        carry_objects = Game.getObjectById(pickup).store
    else:
        carry_objects = Game.getObjectById(pickup).energy

    # print('len(carry_objects)', len(carry_objects))

    if len(carry_objects) == 0:
        # print('pick it up.')
        result = creep.withdraw(Game.getObjectById(pickup), RESOURCE_ENERGY)
        # print(result)
        # pick it up.
        return result

    # else == STRUCTURE_CONTAINER || STRUCTURE_STORAGE
    else:

        for resource in Object.keys(carry_objects):
            # if the creep only need to pick up energy.
            if only_energy and resource != 'energy':
                continue
            # and there's no energy there
            elif only_energy and Game.getObjectById(pickup).store[resource] == 0:
                creep.say('noEnergy')
                # print('noEnergy')
                # del pickup
                return ERR_NOT_ENOUGH_ENERGY

            # if there's no such resource, pass it to next loop.
            if Game.getObjectById(pickup).store[resource] == 0:
                # if creep.name == check_name:
                #     print('WTF')
                continue

            # pick it up.
            grab_action = creep.withdraw(Game.getObjectById(pickup), resource)

            if grab_action == ERR_NOT_ENOUGH_RESOURCES:
                print(resource)

            # 오직 잡기 결과값만 반환한다. 이 함수에서 수거활동 외 활동을 금한다!
            return grab_action


def pick_drops(creep, pickup, only_energy):
    """
    pick up dropped resources, or tombstones.
    :param creep:
    :param pickup: 집을 대상 id
    :param only_energy:
    :return:
    """

    creeps_pickup = Game.getObjectById(pickup)
    if not creeps_pickup:
        return ERR_INVALID_TARGET
    # 두 경우만 존재한다. 떨궈졌냐? 무덤이냐
    # 무덤?
    if creeps_pickup.store:
        for resource in Object.keys(creeps_pickup.store):
            # if the creep only need to pick up energy.
            if only_energy and resource != RESOURCE_ENERGY:
                continue
            # and there's no energy there
            if only_energy and Game.getObjectById(pickup).store[resource] == 0:
                # creep.say('noEnergy')
                return ERR_NOT_ENOUGH_ENERGY

            # if there's no such resource, pass it to next loop.
            if Game.getObjectById(pickup).store[resource] == 0:
                continue

            # pick it up.
            grab_action = creep.withdraw(Game.getObjectById(pickup), resource)

            if grab_action == ERR_NOT_ENOUGH_RESOURCES:
                print('ERR_NOT_ENOUGH_RESOURCES', resource)
            # 오직 잡기 결과값만 반환한다. 이 함수에서 수거활동 외 활동을 금한다!
            return grab_action
    # 떨군거
    else:

        if only_energy and creeps_pickup.resourceType != RESOURCE_ENERGY:
            return ERR_INVALID_TARGET
        else:
            grab_action = creep.pickup(creeps_pickup)

            return grab_action
