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


def filter_enemies(foreign_creeps, count_ai=True):
    """
    filter out allies(ones must not be killed) from FIND_HOSTILE_CREEPS
    :param foreign_creeps:
    :param count_ai:
    :return:
    """
    ally_list = Memory.allianceArray
    enemy_list = []
    for hostile in foreign_creeps:
        enemy = True
        # this is an NPC
        if hostile.owner.username == 'Invader':
            # 평소엔 필요없는거지만 가끔가다 NPC를 세면 안되는 경우가 있음...
            # if not count_ai:
            #     foreign_creeps.splice(foreign_creeps.indexOf(hostile), 1)
            if count_ai:
                enemy_list.append(hostile)
            continue

        # print('hostile.owner.username:', hostile.owner.username)
        for ally in ally_list:
            # print('ally.username:', ally.username)
            # if hostile's name is equal to ally's name it's excluded
            if hostile.owner.username == ally:
                enemy = False
                break
        # filter out creeps without any harm.
        if enemy:
            is_civilian = True
            # print('hostile.body', hostile.body)
            for body in hostile.body:
                # print('enemybody {}, {}'.format(body, body['type']))
                if body['type'] == ATTACK \
                  or body['type'] == RANGED_ATTACK or body['type'] == HEAL or body['type'] == WORK:
                    is_civilian = False
                    break
            # if not is_civilian:
            #     foreign_creeps.splice(foreign_creeps.indexOf(hostile), 1)
            if not is_civilian:
                enemy_list.append(hostile)
        # else:
        #     foreign_creeps.splice(foreign_creeps.indexOf(hostile), 1)

    # return foreign_creeps
    return enemy_list


def filter_friends(foreign_creeps):
    """
    find allies(ones must not be killed) from FIND_HOSTILE_CREEPS
    :param foreign_creeps:
    :return:
    """
    ally_list = Memory.allianceArray
    friends = []
    for foreigns in foreign_creeps:
        for ally in ally_list:
            # if it's one of our allies add to list
            if foreigns.owner.username == ally:
                friends.append(foreigns)

    return friends


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

        # to distinguish storage var. with storages inside while loop.
        loop_storage = creep.pos.findClosestByRange(storages)

        if not loop_storage:
            break
        # if loop_storage only holds energy
        if loop_storage.energy:
            stored_energy = loop_storage.energy
        # 컨트롤러 근처에 있는 컨테이너는 수확에서 제외한다. 다만 업그레이더가 아닐때만!
        # todo 이 컨테이너 확인을 메모리가 존재할때만 하고 거리도 실질적으로 맞게 변환해야한다.
        elif not upgrade and loop_storage.structureType == STRUCTURE_CONTAINER \
                and creep.room.memory.options.upgrade_cont \
                and loop_storage.pos.inRangeTo(loop_storage.room.controller, 6):
            if loop_storage.pos.inRangeTo(loop_storage.room.controller, 6):
                sources = loop_storage.room.find(FIND_SOURCES)
                sources.push(loop_storage.room.find(FIND_MINERALS)[0])
                # 컨테이너가 소스 옆에 있을 경우 삭제한다. 둘이 있을 경우 좀 골때린데...
                for s in sources:
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
        if stored_energy >= int((creep.carryCapacity - _.sum(creep.carry)) * .45):
            return loop_storage.id

        else:
            index = storages.indexOf(loop_storage)
            storages.splice(index, 1)

    # 여기까지 왔다면 현재 남은 빼갈 자원이 없다는거임. 그럼 터미널 스토리지를 각각 확인해서 거기 빈게있으면 빼간다.
    if creep.room.terminal and creep.room.terminal.store[RESOURCE_ENERGY] >= terminal_capacity + creep.carryCapacity:
        return creep.room.terminal.id
    elif creep.room.storage and creep.room.storage.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5:
        return creep.room.storage.id
    else:
        # 그거마저 없으면 그냥 에러.
        return ERR_INVALID_TARGET


def roomCallback(creeps, roomName, structures, constructions=None
                 , ignoreRoads=False, ignoreCreeps=False):
    """
    PathFinder 관련. 원래 도로까는 용도로 짠거라 그거 위주로 돼있음.
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

    # 컨트롤러 근처엔 절대! 도로를 깔지 않는다.
    if room.controller:
        costs.set(room.controller.pos.x, room.controller.pos.y + 1, 0xff)
        costs.set(room.controller.pos.x, room.controller.pos.y - 1, 0xff)
        costs.set(room.controller.pos.x + 1, room.controller.pos.y, 0xff)
        costs.set(room.controller.pos.x + 1, room.controller.pos.y + 1, 0xff)
        costs.set(room.controller.pos.x + 1, room.controller.pos.y - 1, 0xff)
        costs.set(room.controller.pos.x - 1, room.controller.pos.y, 0xff)
        costs.set(room.controller.pos.x - 1, room.controller.pos.y + 1, 0xff)
        costs.set(room.controller.pos.x - 1, room.controller.pos.y - 1, 0xff)

    for struct in structures:
        if struct.structureType == STRUCTURE_ROAD and not ignoreRoads:
            print('not ignoreRoad')
            print('struct.type: {} | pos: {}'.format(struct.structureType, struct.pos))
            # 도로 최우선
            costs.set(struct.pos.x, struct.pos.y, 1)

        elif struct.structureType != STRUCTURE_CONTAINER and (
            struct.structureType != STRUCTURE_RAMPART or not struct.my):
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


def find_distance(creep, distance=5):
    return {'pos': creep.pos, 'range': distance}


def clear_orders():
    my_orders = Game.market.orders
    for order in Object.keys(my_orders):
        if my_orders[order]['remainingAmount'] != 0:
            continue
        if my_orders[order]['active']:
            continue
        if my_orders[order]['amount'] != 0:
            continue
        print('DELETING OLD ORDER: room {}, id {}, remaining amount {}'.format(
            my_orders[order]['roomName'], my_orders[order]['id']
            , my_orders[order]['remainingAmount']))
        Game.market.cancelOrder(order)


def get_to_da_room(creep, roomName, ignoreRoads=True):
    """

    :param creep:
    :param roomName:
    :return:
    """
    # 이 명령은 단순히 시야확보 등의 발령목적으로 보내버리는거기 때문에
    # 방 안에 있으면 무조건 ignoreRoads가 참이여야함
    if creep.room.name == roomName:
        ignoreRoads = True
    result = creep.moveTo(__new__(RoomPosition(25, 25, roomName))
                          , {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20, 'range': 21
                              , 'maxOps': 1000, 'ignoreRoads': ignoreRoads})
    return result
