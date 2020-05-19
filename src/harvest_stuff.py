from defs import *
import movement
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


def harvest_energy(creep: Creep, source_id):
    """
    자원을 캐고 없으면 다음껄로(다음번호) 보낸다.

    :param creep: the creep. do i have to tell you? intended for harvesters.
    :param source_id: ID of the energy source.
    :return: harvest-related result
    """

    # 개편: 어차피 다 게임 API 가 잡아주는데 굳이 미리 에러 띄우기 전에 에러배정 해줄 필요가 없음..
    # 처음 만들때 OK 아니어도 시퓨 먹는줄 착각한것도 한몫

    harvested = creep.harvest(Game.getObjectById(source_id))

    # 떨어져있거나 비었는데 옆에 없으면 우선 간다.
    if harvested == ERR_NOT_IN_RANGE or \
            harvested == ERR_NOT_ENOUGH_RESOURCES and not creep.pos.isNearTo(Game.getObjectById(source_id)):
        if not creep.pos.inRangeTo(Game.getObjectById(source_id), 6):
            move_by_path = movement.move_with_mem(creep, source_id)
            if move_by_path[0] == OK and move_by_path[1]:
                path = move_by_path[2]
        else:
            creep.moveTo(Game.getObjectById(source_id), {'visualizePathStyle': {'stroke': '#ffffff'}, 'maxOps': 5000})
    # 빈 상태에 안에 뭔가가 있으면 그대로 우선 있는거 처리
    elif harvested == ERR_NOT_ENOUGH_RESOURCES and creep.store.getUsedCapacity() > 0:
        creep.say('🐜 SOURCES')
        harvested = ERR_NOT_ENOUGH_RESOURCES_AND_CARRYING_SOMETHING

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
            if storage < (creep.store.getCapacity() - creep.store.getUsedCapacity()) * min_capacity:
                del pickup
                # print('checkpoint?')
                return ERR_NOT_ENOUGH_ENERGY
        else:
            if Game.getObjectById(pickup).energy < (creep.store.getCapacity() - creep.store.getUsedCapacity()) * min_capacity:
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
    # 의미가 있나? 없애보자
    # if not Game.getObjectById(pickup).pos.isNearTo(creep):
    #     return ERR_NOT_IN_RANGE

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


def grab_energy_new(creep, resource_type, min_capacity=.5):
    """
    grabbing energy from local storages(container, storage, etc.)

    :param creep:
    :param resource_type: 어떤 리소스를 뽑아갈거임?
    :param min_capacity: 뽑을 시 크립의
    :return: any creep.withdraw return codes
    """
    # we will make new script for some stuff.

    if not resource_type:
        creep.say('허울타입X!!')
        return ERR_INVALID_ARGS

    # 아이디 추출
    pickup_obj = Game.getObjectById(creep.memory.pickup)

    # 존재하지 않는 물건이거나 용량 저장하는게 없으면 이 작업을 못함.
    if not pickup_obj:
        return ERR_INVALID_TARGET
    elif not (pickup_obj.store or pickup_obj.energy or pickup_obj.mineralAmount):
        print(creep.name, "harvest_stuff.grab_energy_new")
        return ERR_NOT_ENOUGH_ENERGY

    # 스토어가 있는 경우면 에너지 외 다른것도 있을 수 있단거
    # 리소스가 여러 소스 다 수용할 수 있는 경우.
    if pickup_obj.store.getCapacity():
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
    if storage < (creep.store.getCapacity() - creep.store.getUsedCapacity()) * min_capacity:
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
        # for a in Object.keys(carry_objects):
        #     print(a)
        # print(len(carry_objects))
        # 포문 돌려서 하나하나 빼간다.
        if len(carry_objects) >= 1:
            for resource in Object.keys(carry_objects):
                # 리소스가 에너지인데 carry_objects 가 1개 이상이면 통과
                if resource == RESOURCE_ENERGY and len(carry_objects) != 1:
                    continue
                # pick it up.
                result = creep.withdraw(pickup_obj, resource)

                if result == ERR_NOT_ENOUGH_RESOURCES:
                    creep.say('NO_resource')

                return result
        else:
            # result = creep.withdraw(pickup_obj, RESOURCE_ENERGY)
            return ERR_NOT_ENOUGH_RESOURCES

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


def filter_drops(creep, _drops, target_range, only_energy=False):
    """
    떨궈진거 주울때 여럿이 안몰리게끔 분류.
    허울러의 grab_haul_list 함수와 거의 비슷함

    :param creep:
    :param _drops: 자원 및 자원있는 비석. 여기서 다 필터 거친다. 굳이 필터한 상태로 가져올 필요 없음.
    :param target_range: 찾을 최대거리
    :param only_energy:
    :return: target 이 있으면 해당 템의 ID를 메모리에 넣고 아님 만다. 반환값 의미없음
    """
    drops = _.clone(_drops)
    # 돌려보낼 아이디
    target = 0

    while len(drops):
        drop = creep.pos.findClosestByRange(drops)
        # target_range 밖이면 손절
        if not creep.pos.inRangeTo(drop, target_range):
            index = drops.indexOf(drop)
            drops.splice(index, 1)
            continue

        # only_energy 면 에너지 있나만 본다. 다른건 무시
        if only_energy:
            # 스토어에 에너지가 없거나 리소스타입이 존재하면 에너지가 아닌게 있는거임.
            if (drop.store and not drop.store[RESOURCE_ENERGY]) \
                    or (drop.resourceType and drop.resourceType != RESOURCE_ENERGY):
                index = drops.indexOf(drop)
                drops.splice(index, 1)
                continue
        # 안에 자원 계산.
        # todo 지금 폐허 못잡음
        if drop.store:
            resource_amount = _.sum(drop.store)
        else:
            resource_amount = drop.amount
        # 모든 크립 조사.
        for cr in Object.keys(Game.creeps):
            c = Game.creeps[cr]
            if not c.id == creep.id and c.memory.dropped and c.memory.dropped == drop.id:
                resource_amount -= c.store.getCapacity()
        # 리소스 양이 다른 크립이 가져가고도 남아있으면 선택한다.
        if resource_amount > 0:
            target = drop.id
            break
        # 위에서 브레이크 안걸렸으면 다음으로.
        index = drops.indexOf(drop)
        drops.splice(index, 1)
        continue

    if target:
        creep.memory.dropped = target
        creep.say('⛏BITCOINS!', True)

    return target


def pick_drops(creep, only_energy=False):
    """
    떨궈진 물건 줍기.
    존재여부, 내용물 여부, 거리 순으로 확인하고 시행.

    :param creep:
    :param only_energy: 에너지만 줍는가? 기본값 거짓
    :return:
    """

    # creep.memory.dropped_all 이건 떨군거 집을때 모든 크립 공통
    pickup_obj = Game.getObjectById(creep.memory.dropped)
    # 존재하는가?
    if not pickup_obj:
        return ERR_INVALID_TARGET
    # print(creep.name, only_energy, pickup_obj)

    # 내용물이 있는지 확인.
    # 에너지만 줍고 무덤인데 에너지가 없거나
    # 떨군거고 리소스타입이 에너지가 아닌 경우
    # print(pickup_obj)
    if only_energy \
            and ((pickup_obj.store and not pickup_obj.store[RESOURCE_ENERGY])
                 or pickup_obj.amount and not pickup_obj.resourceType == RESOURCE_ENERGY):
        # print('ch1')
        return ERR_NOT_ENOUGH_ENERGY
    # 무덤인데 내용물이 없는 경우. 떨궜는데 내용물이 없으면 자동삭제되니 무관
    elif pickup_obj.store and not _.sum(pickup_obj.store):
        # print('ch2')
        return ERR_NOT_ENOUGH_ENERGY

    # 근처에 없으면 이걸 돌릴 이유가 없다.
    if not pickup_obj.pos.isNearTo(creep):
        return ERR_NOT_IN_RANGE

    # 두 경우만 존재한다. 떨궈졌냐? 무덤이냐. 스토어 있음 무덤
    if pickup_obj.store:
        # 에너지만 잡는거면 에너지만 본다.
        if only_energy:
            if pickup_obj.store[RESOURCE_ENERGY]:
                return creep.withdraw(pickup_obj, RESOURCE_ENERGY)
            else:
                return ERR_NOT_ENOUGH_ENERGY
        else:
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
        if only_energy and pickup_obj.resourceType != RESOURCE_ENERGY:
            return ERR_INVALID_TARGET
        else:
            return creep.pickup(pickup_obj, RESOURCE_ENERGY)


def pick_drops_act(creep, only_energy=False):
    """
    위에 pick_drops 와 같이가는 함수. 위에 결과를 토대로 크립 활동 통일.

    :param creep:
    :param only_energy:
    :return:
    """

    item_pickup_res = pick_drops(creep, only_energy)
    # 없음
    if item_pickup_res == ERR_INVALID_TARGET:
        creep.say("삐빅, 없음", True)
        del creep.memory.dropped
    elif item_pickup_res == ERR_NOT_ENOUGH_ENERGY:
        creep.say("텅비었다..", True)
        del creep.memory.dropped
    # 멀리있음
    elif item_pickup_res == ERR_NOT_IN_RANGE:
        movement.move_with_mem(creep, creep.memory.dropped)
    elif item_pickup_res == OK:
        creep.say('♻♻♻', True)
        del creep.memory.path
    else:
        creep.say('drpERR {}'.format(item_pickup_res))

    return item_pickup_res
