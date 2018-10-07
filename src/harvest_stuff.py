from defs import *
from movement import *

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

    if not creep.pos.isNearTo(Game.getObjectById(source_num)):
        harvested = ERR_NOT_IN_RANGE
    elif Game.getObjectById(source_num).energy == 0:
        harvested = ERR_NOT_ENOUGH_RESOURCES
    # activate the harvest cmd.
    else:
        harvested = creep.harvest(Game.getObjectById(source_num))

    # is sources too far out?
    # creep.say(harvested)
    if harvested == ERR_NOT_IN_RANGE:
        # then go.
        creep.moveTo(Game.getObjectById(source_num), {vis_key: {stroke_key: '#ffffff'},
                                                      'maxOps': 5000})

    # did the energy from the sources got depleted?
    # PROCEED TO NEXT PHASE IF THERE ARE ANYTHING IN CARRY
    # well.... not much important now i guess.
    elif harvested == ERR_NOT_ENOUGH_RESOURCES:
        # do with what you have anyways...
        if _.sum(creep.carry) > 0:
            creep.say('🐜 SOURCES')
            creep.memory.laboro = 1

    return harvested


def grab_energy(creep, pickup, only_energy, min_capacity=.5):
    """
    grabbing energy from local storages(container, storage, etc.)

    :param creep:
    :param pickup: creep.memory.pickup 가장 가까운 또는 목표 storage의 ID
    :param only_energy: bool
    :param min_capacity:
    :return: any creep.withdraw return codes
    """
    # we will make new script for some stuff.

    if not Game.getObjectById(pickup):
        # print(creep.name, 'invalid wtf')
        del pickup
        return ERR_INVALID_TARGET

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

    # 근처에 없으면 아래 확인하는 의미가 없다.
    if not Game.getObjectById(pickup).pos.isNearTo(creep):
        # print(creep.name, 'not in range wtf', Game.getObjectById(pickup).pos.isNearTo(creep))
        return ERR_NOT_IN_RANGE

    # check if memory.pickup has store API or not
    if Game.getObjectById(pickup).store:
        carry_objects = Game.getObjectById(pickup).store
    else:
        carry_objects = Game.getObjectById(pickup).energy

    # 에너지만 있는 대상이거나 에너지만 뽑으라고 설정된 경우.
    if len(carry_objects) == 0 or only_energy:
        result = creep.withdraw(Game.getObjectById(pickup), RESOURCE_ENERGY)
        return result

    # STRUCTURE_CONTAINER || STRUCTURE_STORAGE
    else:
        # 에너지 외 다른 자원을 먼져 뽑는걸 원칙으로 한다.
        # 에너지 외 다른게 있을 경우
        if len(carry_objects) > 1:
            for resource in Object.keys(carry_objects):
                # 우선 에너지면 통과.
                if resource == RESOURCE_ENERGY:
                    continue
                # if there's no such resource, pass it to next loop.
                if Game.getObjectById(pickup).store[resource] == 0:
                    continue

                # pick it up.
                result = creep.withdraw(Game.getObjectById(pickup), resource)

                if result == ERR_NOT_ENOUGH_RESOURCES:
                    print(resource)
                else:
                    # 오직 잡기 결과값만 반환한다. 이 함수에서 수거활동 외 활동을 금한다!
                    return result
        else:
            result = creep.withdraw(Game.getObjectById(pickup), RESOURCE_ENERGY)
            return result


def pick_drops(creep, pickup, only_energy):
    """
    pick up dropped resources, or tombstones.

    :param creep:
    :param pickup: 집을 대상 id
    :param only_energy:
    :return:
    """

    pickup_obj = Game.getObjectById(pickup)
    if not pickup_obj:
        return ERR_INVALID_TARGET

    # 근처에 없으면 이걸 돌릴 이유가 없다.
    if not pickup_obj.pos.isNearTo(creep):
        return ERR_NOT_IN_RANGE

    # 두 경우만 존재한다. 떨궈졌냐? 무덤이냐
    # 무덤?
    if pickup_obj.store:
        for resource in Object.keys(pickup_obj.store):
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

        if only_energy and pickup_obj.resourceType != RESOURCE_ENERGY:
            return ERR_INVALID_TARGET
        else:
            grab_action = creep.pickup(pickup_obj)

            return grab_action
