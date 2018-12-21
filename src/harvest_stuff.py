from defs import *
from movement import *
from _custom_constants import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')

# 자원 얻는 방식에 대한 그 모든것은 여기로 간다.


def harvest_energy(creep, source_id):
    """
    자원을 캐고 없으면 다음껄로(다음번호) 보낸다.

    :param creep: the creep. do i have to tell you? intended for harvesters and upgraders.
    :param source_id: ID of the energy source.
    :return: ain't returning shit.
    """
    vis_key = "visualizePathStyle"
    stroke_key = "stroke"

    if not creep.pos.isNearTo(Game.getObjectById(source_id)):
        harvested = ERR_NOT_IN_RANGE
    elif Game.getObjectById(source_id).energy == 0:
        harvested = ERR_NOT_ENOUGH_RESOURCES
    # activate the harvest cmd.
    else:
        harvested = creep.harvest(Game.getObjectById(source_id))

    # is sources too far out?
    if harvested == ERR_NOT_IN_RANGE:
        # then go.
        creep.moveTo(Game.getObjectById(source_id), {vis_key: {stroke_key: '#ffffff'},
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
    :param only_energy: bool, 에너지만 뽑을 것인가?
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
        # 스토어가 있는 경우면 에너지 외 다른것도 있을 수 있단거
        if Game.getObjectById(pickup).store:
            # storage: 뽑아가고 싶은 자원의 총량
            if only_energy:
                storage = Game.getObjectById(pickup).store[RESOURCE_ENERGY]
            else:
                storage = _.sum(Game.getObjectById(pickup).store)
            if storage < (creep.carryCapacity - _.sum(creep.carry)) * min_capacity:
                del pickup
                # print('checkpoint?')
                return ERR_NOT_ENOUGH_ENERGY
        else:
            if Game.getObjectById(pickup).energy < (creep.carryCapacity - _.sum(creep.carry)) * min_capacity:
                del pickup
                # print('checkpoint222')
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


def grab_energy_new(creep, min_capacity=.5):
    """
    grabbing energy from local storages(container, storage, etc.)

    :param creep:
    :param min_capacity:
    :return: any creep.withdraw return codes
    """
    # we will make new script for some stuff.

    # 어느 종류의 물건을 뽑을 것인가?
    resource_type = creep.memory[haul_resource]

    if not resource_type:
        creep.say('허울타입X!!')
        return ERR_INVALID_ARGS

    # 아이디 추출
    pickup_obj = Game.getObjectById(creep.memory.pickup)

    # 존재하지 않는 물건이거나 용량 저장하는게 없으면 이 작업을 못함.
    if not pickup_obj:
        return ERR_INVALID_TARGET
    elif not (pickup_obj.store or pickup_obj.energy or pickup_obj.mineralAmount):
        return ERR_NOT_ENOUGH_ENERGY

    # if there's no energy in the pickup target, delete it
    # 스토어가 있는 경우면 에너지 외 다른것도 있을 수 있단거
    if pickup_obj.store:
        # storage: 뽑아가고 싶은 자원의 총량
        if resource_type == haul_all:
            storage = _.sum(pickup_obj.store)
        elif resource_type == haul_all_but_energy:
            storage = _.sum(pickup_obj.store) - pickup_obj.store[RESOURCE_ENERGY]
        else:
            storage = pickup_obj.store[resource_type]

    # 대상이 연구소일 경우.
    elif pickup_obj.structureType == STRUCTURE_LAB:
        # 뭘 뽑을거냐에 따라 다름
        if resource_type == RESOURCE_ENERGY:
            storage = pickup_obj.energy
        # 근데 이건 이리 두기만 한거지 사실 쓸 이유가 없음.
        elif resource_type == haul_all:
            storage = pickup_obj.energy + pickup_obj.mineralAmount
        else:
            storage = pickup_obj.mineralAmount
    # todo NUKES AND POWERSPAWN
    # 그외는 전부 링크나 등등. 에너지만 보면 됨 이건.
    else:
        storage = pickup_obj.energy
        # if pickup_obj.energy < (creep.carryCapacity - _.sum(creep.carry)) * min_capacity:
        #     del pickup
        #     # print('checkpoint222')
        #     return ERR_NOT_ENOUGH_ENERGY

    if storage < (creep.carryCapacity - _.sum(creep.carry)) * min_capacity:
        return ERR_NOT_ENOUGH_ENERGY

    # 근처에 없으면 아래 확인하는 의미가 없다.
    if not pickup_obj.pos.isNearTo(creep):
        # print(creep.name, 'not in range wtf', pickup_obj.pos.isNearTo(creep))
        return ERR_NOT_IN_RANGE

    # 스토어만 있는 경우면
    # todo POWERSPAWN
    if pickup_obj.store:
        carry_objects = pickup_obj.store
    else:
        carry_objects = pickup_obj.energy

    # 모든 종류의 자원을 뽑아가려는 경우. 여기서 끝낸다.
    if resource_type == haul_all:
        # 포문 돌려서 하나하나 빼간다.
        if len(carry_objects) > 1:
            for resource in Object.keys(carry_objects):
                # 우선 에너지면 통과.
                if resource == RESOURCE_ENERGY:
                    continue
                # if there's no such resource, pass it to next loop.
                if pickup_obj.store[resource] == 0:
                    continue

                # pick it up.
                result = creep.withdraw(pickup_obj, resource)

                if result == ERR_NOT_ENOUGH_RESOURCES:
                    creep.say('NO_resource')

                return result
        else:
            result = creep.withdraw(pickup_obj, RESOURCE_ENERGY)
            return result

    # 에너지 빼고 모든걸 뽑을 경우
    elif resource_type == haul_all_but_energy:
        storage = _.sum(pickup_obj.store) - pickup_obj.store[RESOURCE_ENERGY]
        if len(carry_objects) > 1:
            for resource in Object.keys(carry_objects):
                # 우선 에너지면 통과.
                if resource == RESOURCE_ENERGY:
                    continue
                # if there's no such resource, pass it to next loop.
                if pickup_obj.store[resource] == 0:
                    continue

                # pick it up.
                result = creep.withdraw(pickup_obj, resource)

                if result == ERR_NOT_ENOUGH_RESOURCES:
                    creep.say('NO_resource')
        else:
            result = ERR_NOT_ENOUGH_ENERGY
    # 특정 자원만 뽑을 경우
    else:
        result = creep.withdraw(pickup_obj, creep.memory[haul_resource])

    return result


def transfer_stuff(creep):
    """
    transfer()를

    :param creep:
    :return:
    """


def pick_drops(creep, only_energy=False):
    """
    떨궈진 물건 줍기.
    존재여부, 내용물 여부, 거리 순으로 확인하고 시행.

    :param creep:
    :param only_energy: 에너지만 줍는가? 기본값 거짓
    :return:
    """
    # print('++++++++++++++++++++++++++++++++++++')
    # print('pick {}'.format(creep.name))
    # creep.memory.dropped 이건 떨군거 집을때 모든 크립 공통
    pickup_obj = Game.getObjectById(creep.memory.dropped)
    # 존재하는가?
    if not pickup_obj:
        return ERR_INVALID_TARGET

    # 내용물이 있는지 확인.
    if only_energy and not ((pickup_obj.store and pickup_obj.store[RESOURCE_ENERGY]) or pickup_obj.energy):
        return ERR_NOT_ENOUGH_ENERGY
    elif not ((pickup_obj.store and _.sum(pickup_obj.store)) or pickup_obj.energy):
        return ERR_NOT_ENOUGH_ENERGY

    # 근처에 없으면 이걸 돌릴 이유가 없다.
    if not pickup_obj.pos.isNearTo(creep):
        return ERR_NOT_IN_RANGE

    # 두 경우만 존재한다. 떨궈졌냐? 무덤이냐. 스토어 있음 무덤
    if pickup_obj.store:
        # print('store')
        # 에너지만 잡는거면 에너지만 본다.
        if only_energy:
            if pickup_obj.store[RESOURCE_ENERGY]:
                return creep.withdraw(pickup_obj, RESOURCE_ENERGY)
            else:
                return ERR_NOT_ENOUGH_ENERGY
        else:
            # print('els')
            # 에너지가 안에 있는지 확인.
            if len(Object.keys(pickup_obj.store)) > 1:
                for resource in Object.keys(pickup_obj.store):
                    # 에너지는 마지막에 챙긴다.
                    if resource == RESOURCE_ENERGY:
                        continue
                    else:
                        return creep.withdraw(pickup_obj, resource)
            else:
                return creep.withdraw(pickup_obj, RESOURCE_ENERGY)
    # 떨군거
    else:
        # print('nStore')
        if only_energy and pickup_obj.resourceType != RESOURCE_ENERGY:
            return ERR_INVALID_TARGET
        else:
            return creep.pickup(pickup_obj, RESOURCE_ENERGY)
