import random
from defs import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')

"""
제목 그대로 잡다한 기능들 총집합. 메인에서 굳이 반복작업 안하려고 만든거. 
"""


def filter_allies(hostile_creeps):
    """
    filter out allies(ones must not be killed) from FIND_HOSTILE_CREEPS
    :param hostile_creeps:
    :return:
    """
    ally_list = Memory.allianceArray
    for hostile in hostile_creeps:
        # this is an NPC
        if hostile.owner.username == 'Invader':
            continue
        # print('hostile.owner.username:', hostile.owner.username)
        for ally in ally_list:
            # print('ally.username:', ally.username)
            # if hostile's name is equal to ally's name it's excluded
            if hostile.owner.username == ally.username:
                hostile_creeps.splice(hostile_creeps.indexOf(hostile), 1)
                break

    return hostile_creeps


def pick_pickup(creep, creeps, storages, terminal_capacity=10000, upgrade=False):
    """
    designate pickup memory by targeted haulers/upgraders
    :param terminal_capacity:
    :param creep: 크립본인
    :param creeps: 방안에 모든 크립
    :param storages: 대상 자원.
    :param upgrade: 이걸 찾는 대상이 컨트롤러 업글하는애인가?
    :return storage: closest storage with energy left
    """
    # print("{} the {} upgrade: {}".format(creep.name, creep.memory.role, upgrade))
    # storage with closest.... yeah

    if upgrade and creep.room.storage:
        storages.push(creep.room.storage)
    # closest_storage = creep.pos.findClosestByRange(storages)

    # creeps.
    portist_kripoj = creeps
    # will filter for leftover energy,
    # tldr - if theres already a creep going for it, dont go unless there's some for you.
    while not creep.memory.pickup or len(storages) > 0:
        # print('checkj')
        # safety trigger
        if len(storages) == 0:
            break

        # no_full_container = True
        # if not upgrade:
        #     for s in storages:
        #         if s.structureType == STRUCTURE_CONTAINER and _.sum(s.store) > s.storeCapacity * .85:
        #             if random.randint(0, 1):
        #                 loop_storage = s
        #                 no_full_container = False
        #                 break
        # if no_full_container:
        # to distinguish storage var. with storages inside while loop.
        loop_storage = creep.pos.findClosestByRange(storages)

        if not loop_storage:
            break

        # if storage is a link, which only holds energy
        if loop_storage.structureType == STRUCTURE_LINK:
            stored_energy = loop_storage.energy
        # 컨트롤러 근처에 있는 컨테이너는 수확에서 제외한다. 다만 업그레이더가 아닐때만!
        elif not upgrade and loop_storage.structureType == STRUCTURE_CONTAINER \
                and loop_storage.pos.inRangeTo(loop_storage.room.controller, 6):
            if loop_storage.pos.inRangeTo(loop_storage.room.controller, 6):
                sources = loop_storage.room.find(FIND_SOURCES)
                sources.push(loop_storage.room.find(FIND_MINERALS)[0])
                # 컨테이너가 소스 옆에 있을 경우 삭제한다. 둘이 있을 경우 좀 골때린데...
                for s in sources:
                    # if s.pos.inRangeTo(loop_storage, 3):
                    # 직접거리도 세칸 이내인가? 맞으면 그걸 없앤다.
                    if len(loop_storage.pos.findPathTo(s, {'ignoreCreeps': True})) <= 3:
                        loop_index = storages.indexOf(loop_storage)
                        # storages.remove(loop_storage)
                        storages.splice(loop_index, 1)
                        loop_storage = creep.pos.findClosestByRange(storages)
                        if upgrade:
                            stored_energy = loop_storage.store[RESOURCE_ENERGY]
                        else:
                            stored_energy = _.sum(loop_storage.store)
                        break

        # else == container or storage.
        else:
            if upgrade:
                stored_energy = loop_storage.store[RESOURCE_ENERGY]
            else:
                stored_energy = _.sum(loop_storage.store)

        for kripo in portist_kripoj:
            # if hauler dont have pickup, pass
            if not kripo.memory.pickup:
                continue
            else:
                # if same id, drop the amount the kripo can carry.
                if loop_storage.id == kripo.memory.pickup:
                    # print('loop_storage.id({}) ==
                    # kripo.memory.pickup({})'.format(loop_storage.id, kripo.memory.pickup))
                    stored_energy -= kripo.carryCapacity
                    # print('stored_energy:', stored_energy)
                else:
                    continue
        # if leftover stored_energy has enough energy for carry, set pickup.
        if stored_energy >= int(creep.carryCapacity * .45):
            return loop_storage.id
            # creep.memory.pickup = loop_storage.id
            # break
        else:
            index = storages.indexOf(loop_storage)
            # storages.remove(loop_storage)
            storages.splice(index, 1)

    # 여기까지 왔다면 현재 남은 빼갈 자원이 없다는거임. 그럼 터미널 스토리지를 각각 확인해서 거기 빈게있으면 빼간다.
    if creep.room.terminal and creep.room.terminal.store[RESOURCE_ENERGY] >= terminal_capacity + creep.carryCapacity:
        return creep.room.terminal.id
    elif creep.room.storage and creep.room.storage.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5:
        return creep.room.storage.id
    else:
        # 그거마저 없으면 그냥 에러.
        return ERR_INVALID_TARGET


def roomCallback(creeps, roomName, structures, constructions=None, ignoreRoads=False, ignoreCreeps=False):
    """
    PathFinder 관련.
    :param structures:
    :param constructions:
    :param creeps: 모든 크립
    :param roomName:
    :param ignoreRoads:
    :param ignoreCreeps:
    :return:
    """
    room = Game.rooms[roomName]

    if not room:
        return

    if len(constructions) > 0:
        for c in constructions:
            structures.push(c)

    costs = __new__(PathFinder.CostMatrix())

    for struct in structures:
        if struct.structureType == STRUCTURE_ROAD and not ignoreRoads:
            print('not ignoreRoad')
            print('struct.type: {} | pos: {}'.format(struct.structureType, struct.pos))
            # 도로 최우선
            costs.set(struct.pos.x, struct.pos.y, 1)

        elif struct.structureType != STRUCTURE_CONTAINER and (struct.structureType != STRUCTURE_RAMPART or not struct.my):
            costs.set(struct.pos.x, struct.pos.y, 0xff)

    if not ignoreCreeps:
        for creep in creeps:
            # 크립 무시함
            costs.set(creep.pos.x, creep.pos.y, 0xff)

    return costs


def calc_size(distance, divisor=6, work_chance=False):
    """
    거리에 따른 멀티 운송크립의 BODY 크기를 구함. 메인에 늘어지는거 방지. 아직 미완성
    :param distance:
    :param divisor:
    :param work_chance:
    :return: body []
    """
    # todo 이거 현재 리모트 허울러 쪽에 있는건데 여기로 함수화 시킵시다.
    # 굳이 따로 둔 이유: 캐리 둘에 무브 하나.
    carry_body_odd = [MOVE, CARRY, CARRY, CARRY]
    carry_body_even = [MOVE, MOVE, CARRY, CARRY, CARRY]
    work_body = [MOVE, WORK, WORK, MOVE, WORK, WORK]
    body = []
    work_check = 0

    for i in range(int(distance / divisor)):
        # work 부분부터 넣어본다.
        if work_chance == 1:
            work_check += 1
            if work_check == 1 or work_check == 4:
                for bodypart in work_body:
                    body.push(bodypart)
            # 본격적인 운송용 들어가야함
            if i % 2 == 0:
                for bodypart in carry_body_even:
                    body.push(bodypart)
            else:
                for bodypart in carry_body_odd:
                    body.push(bodypart)

    # 거리 나머지값 반영.
    if distance % 6 > 2:
        body.push(MOVE)
        body.push(CARRY)
