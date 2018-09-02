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
# todo 주제별로 다 분류해야함.


def check_for_carrier_setting(creep, target_obj):
    """
    배정된 컨테이너의 for_harvest가 캐리어용(2)으로 배정할 자격이 되는지 확인한다.
    :param creep:
    :param target_obj: 대상 타겟. 링크 또는 컨테이너.
    :return: 여기서 배정작업까지 다 끝내기 때문에 뭘 따로 반환할 필요가 없다.
    """
    # print('check for carrier setting', target_obj.structureType, target_obj.id)
    if target_obj.structureType == STRUCTURE_CONTAINER:
        # 메모리를 뜯어서 캐리어용인지 마킹을 한다.
        for mc in creep.room.memory[STRUCTURE_CONTAINER]:
            if mc.id == target_obj.id:
                # print('memory checked, mc harvest {}'.format(mc.for_harvest))
                # 이미 2면 건들필요가 있음?
                if mc.for_harvest == 2:
                    # print(target_obj.id, '는 이미 포 하베스트 2')
                    return
                # 하베스트설정이 2(캐리어용)가 아니고 5칸이내에 존재하면 캐리어용이니 2로 바꾼다.
                elif not mc.for_harvest == 2 and creep.pos.inRangeTo(target_obj, 5) \
                        and len(creep.pos.findPathTo(target_obj, {'ignoreCreep': True})) <= 5:
                    mc.for_harvest = 2
                    # print(target_obj.id, '변환완료')
                    return
                # print('WTFFF')
                return
    elif target_obj.structureType == STRUCTURE_LINK:
        for ml in creep.room.memory[STRUCTURE_LINK]:
            # 캐리어용인지 마킹하는거.
            if ml.id == target_obj.id:
                if ml.for_harvest == 2:
                    return
                else:
                    ml.for_harvest = 2
                    return
        # 위에 포문 안에서 리턴이 안된단건 링크가 등록이 안됬단 소리임.
        creep.room.memory.options.reset = 1
        return


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
            if count_ai:
                enemy_list.append(hostile)
            continue

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
                # 움직일수만 있는놈 빼고 다 적임.
                if body['type'] != MOVE:
                    is_civilian = False
                    break

            if not is_civilian:
                enemy_list.append(hostile)
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
    designate pickup memory by targeted haulers/upgraders/fixers
    :param terminal_capacity:
    :param creep: 크립본인
    :param creeps: 방안에 모든 크립
    :param storages: 대상 자원.
    :param upgrade: 이걸 찾는 대상이 컨트롤러 업글하는애인가?
    :return storage: closest storage with energy left
    """
    # print("{} the {} upgrade: {}".format(creep.name, creep.memory.role, upgrade))
    # storage with closest.... yeah
    # if creep.memory.role == 'hauler': print(creep.name, storages)
    # creeps.
    portist_kripoj = creeps
    # 업글전용
    passed_upgr = False
    # if upgrade:
    #     print('start')
    # will filter for leftover energy,
    # tldr - if theres already a creep going for it, dont go unless there's some for you.
    while not creep.memory.pickup or len(storages) > 0:
        # just init.
        stored_energy = 0
        # safety trigger
        if len(storages) == 0:
            break

        loop_storage = []

        # to distinguish storage var. with storages inside while loop.
        # 만일 업글이면 for_upgrade 로 분류된 컨테이너에서 최우선으로 자원을 뽑는다.
        if creep.room.controller.level < 8 and upgrade and not passed_upgr:
            u_con_list = []
            for cont in storages:
                # 실제 보유중인 컨테이너 중에서 찾는다.
                if cont.structureType == STRUCTURE_CONTAINER:
                    for u_cont in creep.room.memory[STRUCTURE_CONTAINER]:
                        if u_cont.for_upgrade and (u_cont.id == cont.id):
                            if Game.getObjectById(u_cont.id):
                                u_con_list.append(Game.getObjectById(u_cont.id))
                                break
            if len(u_con_list):
                loop_storage = creep.pos.findClosestByRange(u_con_list)
            passed_upgr = True
        if not len(loop_storage):
            loop_storage = creep.pos.findClosestByRange(storages)

        if not loop_storage:
            break
        # if upgrade:
        #     print('type', loop_storage.structureType)
        # if loop_storage only holds energy - STRUCTURE_LINK and STRUCTURE_LAB
        if loop_storage.structureType == STRUCTURE_LINK or loop_storage.structureType == STRUCTURE_LAB:
            stored_energy = loop_storage.energy

        # todo 이 컨테이너 확인을 메모리가 존재할때만 하고 거리도 실질적으로 맞게 변환해야한다.
        # 예전엔 대상을 찾아서 이게 업글용인건지(즉 소스근처가 아닌거) 확인용도였음. 이제 그건 컨테이너 메모리에 적혀있음.
        # 컨테이너인 경우
        elif loop_storage.structureType == STRUCTURE_CONTAINER:
            # 메모리에 있는건지 확인.
            available = False
            # 우선 업글용도인지 확인한다.
            for cont in creep.room.memory[STRUCTURE_CONTAINER]:
                # 아이디 맞는지 확인하고.
                if cont.id == loop_storage.id:
                    available = True
                    # 크립과 컨테이너가 업글용인가?
                    if cont.for_upgrade and upgrade:
                        stored_energy = loop_storage.store[RESOURCE_ENERGY]
                    # 업글용이면 허울러, 건들지말것. 다만 캐리어용이면 일부 챙길 수 있음. 꽉찼을때 한정.
                    # 그리고 방렙 8이면 업글용이 의미가 없어짐. 맘것 가져갑시다.
                    elif cont.for_upgrade and cont.for_harvest == 2 \
                            and (_.sum(loop_storage.store) == loop_storage.storeCapacity
                                 or creep.room.controller.level == 8):
                        # if creep.memory.role == 'hauler': print('wtf')
                        stored_energy = _.sum(loop_storage.store)

                    # 그냥 포 업그레이드가 아니면 전부 쓸 수 있음.
                    elif not cont.for_upgrade:
                        # if creep.memory.role == 'hauler': print('so what')
                        stored_energy = _.sum(loop_storage.store)

                    break

        # else == storage.
        else:
            if upgrade:
                stored_energy = loop_storage.store[RESOURCE_ENERGY]
                # print('the storage energy', stored_energy)
            else:
                stored_energy = _.sum(loop_storage.store)

        if stored_energy:
            for kripo in portist_kripoj:
                # if hauler dont have pickup, pass
                if not kripo.memory.pickup:
                    continue
                else:
                    # if same id, drop the amount the kripo can carry.
                    if loop_storage.id == kripo.memory.pickup:
                        stored_energy -= kripo.carryCapacity
                        # if upgrade:
                        #     print('stored_energy:', stored_energy)
                    else:
                        continue
        # if leftover stored_energy has enough energy for carry, set pickup.
        if stored_energy >= int((creep.carryCapacity - _.sum(creep.carry)) * .5):
            # if creep.memory.role == 'hauler':
            #     print('return', loop_storage.id)
            return loop_storage.id

        else:
            index = storages.indexOf(loop_storage)
            storages.splice(index, 1)

    # 여기까지 왔다면 현재 남은 빼갈 자원이 없다는거임. 그럼 터미널 스토리지를 각각 확인해서 거기 빈게있으면 빼간다.
    if creep.room.terminal and creep.room.terminal.store[RESOURCE_ENERGY] >= terminal_capacity + creep.carryCapacity:
        return creep.room.terminal.id
    elif creep.room.storage and creep.room.storage.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5:
        # if creep.memory.role == 'hauler': print('huH???')
        return creep.room.storage.id
    else:
        # 그거마저 없으면 그냥 에러.
        return ERR_INVALID_TARGET


# noinspection PyPep8Naming
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


# noinspection PyPep8Naming
def get_to_da_room(creep, roomName, ignoreRoads=True):
    """

    :param creep:
    :param roomName:
    :param ignoreRoads:
    :return:
    """
    # 이 명령은 단순히 시야확보 등의 발령목적으로 보내버리는거기 때문에
    # 방 안에 있으면 무조건 ignoreRoads가 참이여야함
    if creep.room.name == roomName:
        ignoreRoads = True
    result = creep.moveTo(__new__(RoomPosition(25, 25, roomName))
                          , {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 15, 'range': 21
                              , 'maxOps': 1000, 'ignoreRoads': ignoreRoads})
    return result


def swapping(creep, creeps, avoid_id=0, avoid_role=''):
    """
    길막할 경우 위치변환.
    :param creep:
    :param creeps:
    :param avoid_id:
    :param avoid_role:
    :return:
    """
    for c in creeps:
        if creep.pos.inRangeTo(c, 1) and not c.name == creep.name \
                and not (c.id == avoid_id or c.memory.role == avoid_role):
            creep.say('GTFO', True)
            mv = c.moveTo(creep)
            creep.moveTo(c)
            return c.id

    return ERR_NO_PATH


def repair_on_the_way(creep, repairs):
    """
    운송크립 운송작업중 주변에 컨트롤러나 수리해야하는거 있으면 무조건 하고 지나간다.
    :param creep:
    :param repairs:
    :return:
    """
    if creep.room.controller and creep.room.controller.my and creep.room.controller.level < 8:
        creep.upgradeController(Game.getObjectById(creep.memory.upgrade_target))
    if len(repairs) > 0:
        repair = creep.pos.findClosestByRange(repairs)
        creep.repair(repair)