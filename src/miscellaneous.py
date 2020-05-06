import random
from defs import *
from _custom_constants import *


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
    NULLIFIED - 왜 배정한거지??? 필요성이 전혀 없다.
    배정된 컨테이너의 for_harvest 가 캐리어용(2)으로 배정할 자격이 되는지 확인한다.

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
                    ml.for_store = 0
                    return
                else:
                    ml.for_harvest = 2
                    ml.for_store = 0
                    return
        # 위에 포문 안에서 리턴이 안된단건 링크가 등록이 안됬단 소리임.
        creep.room.memory.options.reset = 1
        return


def filter_friend_foe(foreign_creeps):
    """
    크립목록에서 적과 아군 필터링한다.

    :param foreign_creeps: 적 크립 전부
    :return: [[적 전부], [적 NPC], [적 플레이어], [동맹]]
    """

    ally_list = _.clone(Memory.allianceArray)
    # ally_list.extend(Memory.friendly)
    # print(ally_list)
    if Memory.friendly and len(Memory.friendly) > 0:
        ally_list.extend(Memory.friendly)

    # 모든 적
    all_enemies = []
    # 엔피시
    npc_enemies = []
    # 적 플레이어
    player_enemies = []
    # 동맹군
    friendly = []
    for hostile in foreign_creeps:
        enemy = True
        # this is an NPC
        # 소스키퍼도 존재하는데 이건 생각좀...
        if hostile.owner.username == 'Invader':
            # 엔피씨면 모든적과 엔피시로
            all_enemies.append(hostile)
            npc_enemies.append(hostile)
            continue
        # 동맹군 필터링
        for ally in ally_list:
            # if hostile's name is equal to ally's name it's excluded
            if hostile.owner.username == ally:
                friendly.append(hostile)
                enemy = False
                break

        if enemy:
            for body in hostile.body:
                # 움직일수만 있는놈 빼고 다 잡는다.
                if body['type'] != MOVE:
                    all_enemies.append(hostile)
                    player_enemies.append(hostile)
                    break

    return [all_enemies, npc_enemies, player_enemies, friendly]


def pick_pickup(creep, creeps, pickup_targets, terminal_capacity=10000, upgrade=False):
    """
    designate pickup memory by targeted haulers/upgraders/fixers

    :param terminal_capacity:
    :param creep: 크립본인
    :param creeps: 방안에 모든 크립, 또는 비교대상인 모든 크립
    :param pickup_targets: 뽑아갈 대상 자원.
    :param upgrade: 이걸 찾는 대상이 컨트롤러 업글하는애인가?
    :return storage: closest storage with energy left
    """
    # 업글 관련해서전용
    passed_upgr = False

    # will filter for leftover energy,
    # tldr - if theres already a creep going for it, dont go unless there's some for you.
    while not creep.memory.pickup or len(pickup_targets) > 0:
        # just init.
        stored_energy = 0
        # safety trigger
        if len(pickup_targets) == 0:
            break

        # 가장 가까운 대상
        # loop_storage = creep.pos.findClosestByRange(pickup_targets)
        loop_storage = creep.pos.findClosestByPath(pickup_targets, {ignoreCreeps: True})

        if not loop_storage:
            break

        if loop_storage.structureType == STRUCTURE_LAB or loop_storage.structureType == STRUCTURE_LINK:
            stored_energy = loop_storage.energy

        # todo 이 컨테이너 확인을 메모리가 존재할때만 하고 거리도 실질적으로 맞게 변환해야한다.
        # 예전엔 대상을 찾아서 이게 업글용인건지(즉 소스근처가 아닌거) 확인용도였음. 이제 그건 컨테이너 메모리에 적혀있음.
        # 컨테이너인 경우
        elif loop_storage.structureType == STRUCTURE_CONTAINER:
            #
            stored_energy = _.sum(loop_storage.store)

        elif loop_storage.structureType == STRUCTURE_STORAGE:
            if upgrade:
                stored_energy = loop_storage.store[RESOURCE_ENERGY]
                # print('the storage energy', stored_energy)
            else:
                stored_energy = _.sum(loop_storage.store)
        # 위에 해당사항 없으면 뽑는 대상 자체가 아닌거임.
        else:
            stored_energy = 0

        if stored_energy:
            for c in creeps:
                # if hauler dont have pickup, pass
                if not c.memory.pickup:
                    continue
                else:
                    # if same id, drop the amount the c can carry.
                    if loop_storage.id == c.memory.pickup:
                        stored_energy -= c.carryCapacity
                    else:
                        continue
        # if leftover stored_energy has enough energy for carry, set pickup.
        if stored_energy >= int((creep.carryCapacity - _.sum(creep.carry)) * .5):
            return loop_storage.id

        else:
            index = pickup_targets.indexOf(loop_storage)
            pickup_targets.splice(index, 1)

    # 와일문 안에서 답이 안나왔으면 망.
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


def repair_on_the_way(creep, repairs, constructions, upgrader=False, irregular=False):
    """
    운송크립 운송작업중 주변에 컨트롤러나 수리해야하는거 등 있으면 무조건 하고 지나간다.

    :param creep:
    :param repairs:
    :param constructions:
    :param upgrader: 크립이 업글러일때만 설정. 기본값 거짓
    :param irregular: 크립에게 항시 업글 안시키려는 의도. 엥간해선 안씀.
    :return: result constants maybe?
    """
    laboro = False

    # 일할수있는애긴 함?
    if creep.memory.work == 1:
        laboro = True

    elif not creep.memory.work == 0:
        for body in creep.body:
            if body['type'] == WORK:
                laboro = True
                creep.memory.work = 1
                break
        if not laboro:
            creep.memory.work = 0

    # 혹시 WORK가 없으면 이걸 돌리는 의미가 없어짐.
    if not laboro:
        return ERR_NO_BODYPART

    # 내 컨트롤러고 그게 렙8이 아니거나 현 크립이 업글러인지? 둘중하나면 시행.
    # 이 작업은 렙8될때까지 모두가 방발전에 총력을 다해야 하는 상황이기에 만들어졌음.
    if (creep.room.controller and creep.room.controller.my and creep.room.controller.level < 8) \
            or upgrader:
        if irregular:
            if Game.time % 5 == 0:
                run_upg = True
            else:
                run_upg = False
        else:
            run_upg = True
        if creep.pos.inRangeTo(creep.room.controller, 3) and run_upg:
            creep.upgradeController(creep.room.controller)
    # 건설과 수리 둘중 하나만.
    bld = ERR_UNDONE_CONSTANT
    if len(constructions) > 0:
        building = creep.pos.findClosestByRange(constructions)
        if creep.pos.inRangeTo(building, 3):
            bld = creep.build(building)
    if len(repairs) > 0 and not bld == 0:
        repair = creep.pos.findClosestByRange(repairs)
        if repair and creep.pos.inRangeTo(repair, 3):
            creep.repair(repair)


# def map_changer(map_name, desto):

