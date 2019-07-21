from defs import *
from harvest_stuff import *
import pathfinding
from miscellaneous import *
from _custom_constants import *
import movement

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_carrier(creep, creeps, all_structures, constructions, dropped_all, repairs):
    """
    technically same with hauler, but more concentrated in carrying itself.
        and it's for remote mining ONLY.

    :param Game.creep creep: Game.creep
    :param creeps: creep.room.find(FIND_MY_CREEPS)
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param constructions: FIND_CONSTRUCTION_SITES
    :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
    :param repairs:
    :return:
    """

    # todo 현 문제점:
    # - 건설 필요 시 배정.(?)
    # - 운송 시 목표지점 배정관련: 자꾸 스폰당시 위치에서 가장 가까운거에 해버림.
    # - 원래 픽업위치 파괴됐을 시 배정 관련. 방에 자원이 둘일때 엉켜버림. 수리가 시급함.
    # - 운송중 떨어진거 주웠는데 일정량보다 많으면 걍 돌아가게끔. 방금 뭔 10남았는데 계속가...

    # 임시 초기화 방편 - todo 추후 필요 없어야함.
    if not creep.memory.size:
        creep.memory.size = 2

    # 인생정리모드 돌입용(?) 값.
    end_is_near = 40

    # in case it's gonna die soon. switch to some other
    if _.sum(creep.carry) > 0 and creep.ticksToLive < end_is_near and \
            (creep.memory.laboro == 0 or (creep.memory.laboro == 1 and creep.memory.priority != 2)):
        creep.say('endIsNear')
        creep.memory.laboro = 1
        creep.memory.priority = 2
    elif _.sum(creep.carry) == 0 and creep.ticksToLive < end_is_near:
        creep.suicide()
        return
    elif not creep.memory.upgrade_target:
        creep.memory.upgrade_target = creep.room.controller['id']
    elif not creep.memory.home_room:
        creep.memory.home_room = creep.room.name
    elif not creep.memory[haul_resource]:
        creep.memory[haul_resource] = haul_all

    # 픽업에 저장된 길이 있나 확인한다. 우선 이리 만들긴 했는데 스폰부터 메모리화되서 의미가 없어진듯
    # if not creep.memory[to_pickup] and Game.getObjectById(creep.memory.pickup):
    # todo 함수로 빼낸다.
    # 상식적으로 없을수가 없음....
    if not creep.memory[to_pickup]:
        if Game.getObjectById(creep.memory.pickup):
            target_obj = Game.getObjectById(creep.memory.pickup)
        else:
            target_obj = Game.getObjectById(creep.memory.source_num)
        # print(Game.getObjectById(creep.memory.pickup))
        objs = []
        for i in target_obj.room.memory[resources][RESOURCE_ENERGY]:
            objs.append(Game.getObjectById(i))
        for i in target_obj.room.memory[resources][minerals]:
            objs.append(Game.getObjectById(i))
        # for i in Game.getObjectById(creep.memory.pickup).room.memory[STRUCTURE_KEEPER_LAIR]:
        #     objs.append(Game.getObjectById(i))
        opts = {'trackCreeps': False, 'refreshMatrix': True, 'pass_walls': False,
                'costByArea': {'objects': objs, 'size': 1, 'cost': 6}}
        if creep.memory.birthplace:
            birthplace = RoomPosition(creep.memory.birthplce.x, creep.memory.birthplce.y, creep.memory.birthplce.roomName)
        else:
            birthplace = creep.pos
        # 가는길 저장.
        creep.memory[to_pickup] = \
            PathFinder.search(birthplace, target_obj.pos,
                              {'plainCost': 2, 'swampCost': 3,
                               'roomCallback':
                                   lambda room_name:
                                   pathfinding.Costs(room_name, opts).load_matrix()
                               }, ).path
        # 그리고 위에꺼 그대로 역순으로 나열해서 돌아가는길 저장.
        creep.memory[to_home] = []
        for r in creep.memory[to_pickup]:
            creep.memory[to_home].insert(0, r)
    # 초기화 작업
    if _.sum(creep.carry) == 0 and creep.memory.laboro != 0:
        creep.memory.laboro = 0
        creep.memory.priority = 0

        # creep.memory.refill = 0은 컨테이너 아예 없음, 1은 리필 확인요망, 2는 리필 완료, 다음 자원빼올때까지 확인 안해도 된단거.
        # 리필의 필요성:
        # 원칙적으로 캐리어는 링크로 운송을 해야하는데 만약 중간에 링크 공간부족으로 컨테이너에 넣었으면 중간중간 빼서 링크로 재배송
        if not creep.memory.refill and not creep.memory.refill == 0:
            creep.memory.refill = 2
        del creep.memory.haul_target
        del creep.memory.build_target
        creep.say('가즈아 ✈', True)

    elif _.sum(creep.carry) >= creep.carryCapacity * .6 and creep.memory.laboro != 1 \
            and not creep.memory.container_full:
        creep.memory.laboro = 1

    if creep.memory.haul_target and not Game.getObjectById(creep.memory.haul_target):
        del creep.memory.haul_target

    # laboro: 0 == pickup something.
    if creep.memory.laboro == 0:
        # 운송 시작할 시 컨테이너에 자원이 있고 근처 할당된 링크가 꽉 안참? 그럼 컨테이너에서 링크로 옮긴다.
        # memory.refill 로 확인한다 0이면 컨테이너가 아예없는거, 1이면 확인해야함. 2면 이미 확인함.
        # 확인을 아직 안했고 크립이 본진이며, 링크 ID를 저장해두고 있는가?

        if creep.memory.refill == 1 and creep.room.name == creep.memory.home_room:

            # print(creep.name, 'refill')
            # 여기서 컨테이너가 있긴 한지 한번 확인.
            container_exist = False
            for h in creep.memory.haul_destos:
                if h.type == STRUCTURE_CONTAINER:
                    container_exist = True
                    break
            # print('container_exist', container_exist, 'memory.container {} refill {}'.format(creep.memory.container, creep.memory.refill))
            # 컨테이너가 없으면 아래 포문 돌 필요가 전혀없음.
            if not container_exist:
                creep.memory.refill = 0

            # 컨테이너 메모리는 리필할때 뽑아갈 컨테이너를 찾기 위한 용도
            if not creep.memory.container and creep.memory.refill:
                # 시작전 컨테이너/link 가 존재하는지 확인.
                containers = []
                links = []
                for h in creep.memory.haul_destos:
                    h_obj = Game.getObjectById(h.id)
                    if not h_obj:
                        continue
                    if h.type == STRUCTURE_CONTAINER and h_obj.store.energy > 0:
                        containers.append(h_obj)
                    if h.type == STRUCTURE_LINK and not h_obj.energy == h_obj.energyCapacity:
                        links.append(h_obj)
                    del h_obj
                # print('len(links) {} len(containers) {}'.format(len(links), len(containers)))
                # 컨테이너나 링크 둘 중 하나라도 없으면 의미가 없음
                if not len(links) or not len(containers):
                    creep.memory.refill = 2
                else:
                    # 컨테이너에서 필요한걸 뽑아간다.
                    creep.memory.container = creep.pos.findClosestByRange(containers).id

            # 위에서 뽑았으면 이제 작업시작 가능
            if creep.memory.container:
                # todo 지금 리필 시행 한번 하면 그걸로 끝이여야 하는데 링크나 컨테이너 둘중하나가 떨어질때까지 계속함...
                grab = grab_energy(creep, creep.memory.container, True, 0)
                creep.say("refill {}".format(grab))
                print(creep.name, 'refill res: ', grab)
                # 컨테이너가 없으면 통과.
                if grab == ERR_INVALID_TARGET:
                    del creep.memory.container
                    creep.memory.refill = 2
                # 에너지가 없으면 통과.
                elif grab == ERR_NOT_ENOUGH_ENERGY:
                    creep.memory.refill = 2
                # 떨어져 있으면 당연 다가간다.
                elif grab == ERR_NOT_IN_RANGE:
                    movement.movi(creep, creep.memory.container)
                # 온전히 잡았으면 다 잡은거마냥 행동한다. 링크로 옮기기 위한 절차.
                elif grab == OK:
                    creep.memory.laboro = 1
                    creep.memory.priority = 2
                    creep.memory.refill = 2
                    del creep.memory.container
                    del creep.memory.haul_target
                return
            # 이게 안떠야 정상이긴 한데 뭐 컨테이너 배정된게 없으면 계속 할일하는거
            elif not creep.memory.refill == 0:
                creep.memory.refill = 2

        # if there is a dropped target and it's there.
        if creep.memory.dropped:
            item_pickup_res = pick_drops(creep, True)
            item = Game.getObjectById(creep.memory.dropped)
            if item_pickup_res == ERR_INVALID_TARGET:
                creep.say("삐빅, 없음", True)
                del creep.memory.dropped
            # 내용물 없음
            elif item_pickup_res == ERR_NOT_ENOUGH_ENERGY:
                creep.say("💢 텅 비었잖아!", True)
                del creep.memory.dropped
            # 멀리있음
            elif item_pickup_res == ERR_NOT_IN_RANGE:
                movement.movi(creep, creep.memory.dropped, 0, 10, False, 2000, '#0000FF')
                return
            elif item_pickup_res == OK:
                creep.say('♻♻♻', True)
                return

        # if there's no dropped and there's dropped_all
        # todo 자원이 있는 방 안에 있으면 집는다.
        if creep.memory.age > 50 and not creep.memory.dropped and len(dropped_all) > 0:
            for drop in dropped_all:
                # carrier will only take energy
                # 크립정보 있으면 비석.
                if drop.creep and not drop.store[RESOURCE_ENERGY]:
                    continue
                elif drop.resourceType != RESOURCE_ENERGY:
                    continue

                creep.memory.dropped = drop['id']

                item_pickup_res = pick_drops(creep, True)
                creep.say('⛏BITCOINS!', True)
                if item_pickup_res == ERR_NOT_IN_RANGE:
                    movement.movi(creep, creep.memory.dropped, 0, 10, False, 2000, '#0000FF')
                elif item_pickup_res == OK:
                    pass
                else:
                    creep.say('drpERR {}'.format(item_pickup_res))

                break

        # if there's pickup, no need to go through all them below.
        # creep.memory.pickup == id of the container carrier's gonna pick up
        if creep.memory.pickup:
            # todo 움직이는 루트를 완전히 메모리에 넣는다.
            # 이때 해야하는 변수는 크게 두가지.
            # 중간에 떨궈진 물건이 있어서 주워야 해서 경로이탈, 돌아오는길에 컨테이너랑 길이 없는경우.

            # 1. if 1 == False, look for storage|containers to get the energy from.
            # 2. if 2 == False, you harvest on ur own.
            # result = grab_energy(creep, creep.memory.pickup, False, 0.0)
            # todo 개뻘짓인듯, 일반 무브먼트 기능으로 합칩시다.
            result = grab_energy_new(creep, creep.memory[haul_resource])
            # *******************************************************************
            if result == ERR_NOT_IN_RANGE:

                path = _.map(creep.memory.to_pickup, lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))
                move_by_path = move_with_mem(creep, None, 0, path, 'to_pickup', False)
                if move_by_path[0] == OK and move_by_path[1]:
                    creep.memory.path = move_by_path[2]

                # 크립위치가 길과 안맞는 경우.
                elif move_by_path[0] == ERR_NOT_FOUND:

                    # 가장 가까이 있는 길을 찾아나선다.
                    closest = creep.pos.findClosestByRange(path)
                    print(JSON.stringify(closest))
                    creep.say('탈선x{}y{}'.format(closest.x, closest.y))
                    # movement.movi(creep, closest)
                    path = _.map(creep.memory.path, lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))
                    move_by_path = move_with_mem(creep, closest, 0, path)
                    if move_by_path[0] == OK and move_by_path[1]:
                        creep.memory.path = move_by_path[2]
                elif not move_by_path[0] == OK:
                    creep.say('ERR {}'.format(move_by_path[0]))

            elif result == 0:
                creep.say('BEEP BEEP⛟', True)
                # 컨테이너 안에 에너지 외 다른게 들어가 있으면 빼내 없애야 하기에 한 조치.
                if (len(Game.getObjectById(creep.memory.pickup).store) == 2
                        and Game.getObjectById(creep.memory.pickup).store[RESOURCE_ENERGY] == 0) \
                        or len(Game.getObjectById(creep.memory.pickup).store) == 1:
                    creep.memory.laboro = 1

                    if creep.memory.container_full:
                        creep.memory.container_full = 0
                        creep.memory.priority = 2
                    else:
                        creep.memory.priority = 0
                    # 리필할 대상이 있고 완료하고 왔을경우 재설정한다.
                    if creep.memory.refill == 2:
                        creep.memory.refill = 1
            elif result == ERR_NOT_ENOUGH_ENERGY:
                if _.sum(creep.carry) > creep.carryCapacity * .4:
                    creep.memory.laboro = 1
                    creep.memory.priority = 0

                else:
                    harvest = creep.harvest(Game.getObjectById(creep.memory.source_num))
                    # creep.say('harv {}'.format(harvest))
                    if harvest == ERR_NOT_IN_RANGE:
                        creep.moveTo(Game.getObjectById(creep.memory.source_num),
                                     {'visualizePathStyle': {'stroke': '#ffffff'},
                                      'reusePath': 25})
                    # 자원 캘수가 없으면 자원 채워질때까지 컨테이너 위치에서 대기탄다.
                    elif harvest == ERR_NO_BODYPART or harvest == ERR_NOT_ENOUGH_RESOURCES:
                        if not creep.pos.isNearTo(Game.getObjectById(creep.memory.pickup)):
                            creep.moveTo(Game.getObjectById(creep.memory.pickup)
                                         , {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 25})
                return
            # 파괴되거나 하면 메모리 삭제.
            elif result == ERR_INVALID_TARGET:
                del creep.memory.pickup
            # other errors? just delete 'em
            else:
                print(creep.name, 'grab_energy() ELSE ERROR:', result)
                del creep.memory.pickup
            return

        # no pickup target? then it's a start!
        else:
            # 방이 안보이거나 크립이 자원과 떨어져있을 경우.
            if not Game.rooms[creep.memory.assigned_room]\
                    or not creep.pos.inRangeTo(Game.getObjectById(creep.memory.source_num), 5):

                # 스폰될때 자동으로 현위치에서 길이 배정되기 때문에 없으면 애초부터 잘못 스폰된거.
                path = \
                    _.map(creep.memory[to_pickup],
                          lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))

                moving = creep.moveByPath(path)

                if moving == OK:
                    path = _.map(creep.memory.to_pickup, lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))
                    move_by_path = move_with_mem(creep, None, 0, path, 'to_pickup', False)

                    if not move_by_path[0] == OK:
                        creep.say('투픽업탈선:{}'.format(move_by_path[0]))

                # 크립위치가 길과 안맞는 경우.
                elif moving == ERR_NOT_FOUND:
                    # 가장 가까이 있는 길을 찾아나선다.
                    closest_loc = creep.pos.findClosestByRange(path)
                    path = _.map(creep.memory.path, lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))
                    move_by_path = move_with_mem(creep, closest_loc, 0, path)
                    if move_by_path[0] == OK and move_by_path[1]:
                        creep.memory.path = move_by_path[2]
                    creep.say('픽업탈선:{}'.format(move_by_path[0]))

                else:
                    creep.say('ERR {}'.format(moving))

            else:
                # 여기로 왔다는건 할당 컨테이너가 없다는 소리. 한마디로 not creep.memory.pickup == True
                # 수정:
                # 이게 뜨면 무조건 먼져 담당구역으로 간다. 간 후 담당 리소스를 확인한다.(이건 스폰 시 자동)
                # 그 후에 배정받은 픽업이 존재하는지 확인한다.
                # 배정받은 픽업이 존재하면 그걸로 끝. 없으면 건설담당인 셈. 자원 캔다.

                # pickup이 없으니 자원캐러 간다.
                harvest = harvest_energy(creep, creep.memory.source_num)
                # print(creep.name, 'harvest', harvest)
                if harvest == ERR_NOT_IN_RANGE:
                    creep.moveTo(Game.getObjectById(creep.memory.source_num)
                                 , {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 25})
                # 컨테이너 건설을 해야 하는데 일을 못하는 놈이면 죽어라.
                elif harvest == ERR_NO_BODYPART:
                    creep.suicide()
                    return
                else:
                    creep.say('hrvst {}'.format(harvest))

                # 매 틱마다 픽업이 있는지 확인한다. 있으면 바로 등록.
                # 같은 방일때만 확인한다.
                if creep.room.name == Game.rooms[creep.memory.assigned_room].name:
                    for s in all_structures:
                        if s.structureType == STRUCTURE_CONTAINER:
                            if Game.getObjectById(creep.memory.source_num).pos.inRangeTo(s, 3):
                                creep.memory.pickup = s.id

    # getting to work.
    elif creep.memory.laboro == 1:
        # PRIORITY
        # 1. if there's something to construct, do that first.
        # 2. else, carry energy or whatever to the nearest link of the home_room
        # 3. repair

        if creep.memory.priority == 0:

            # made for cases carriers dont have WORK
            creep_body_has_work = creep.memory.work

            try:
                # construction sites. only find if creep is not in its flag location.
                if creep.room.name != creep.memory.assigned_room:
                    constructions = Game.rooms[creep.memory.assigned_room].find(FIND_MY_CONSTRUCTION_SITES)
            except:
                # 이게 걸리면 지금 반대쪽 방에 아무것도 없어서 시야확보 안됐단 소리.
                return
            # if there's no WORK in carrier they cant do fix or build at all.
            # 또는 컨테이너 풀 메모리가 활성화된 경우: 픽업 꽉차서 재실행된거임.
            if not creep_body_has_work or creep.memory.container_full:
                creep.say('🔄물류,염려말라!', True)
                creep.memory.priority = 2
                creep.memory.container_full = 0
            elif len(constructions) > 0:
                creep.say('🚧 건설투쟁!', True)
                creep.memory.priority = 1
            else:
                # 수리할 것이 있는가? 있으면 확률 발동. 없으면 1 고정. 20% 이하 체력건물이 있으면 100%
                # 이제 있을때만 적용.
                if len(repairs) > 0:
                    random_chance = 1
                    if creep.memory.pickup:
                        pick_obj = Game.getObjectById(creep.memory.pickup)
                        if pick_obj and pick_obj.pos.inRangeTo(creep, 3):
                            if pick_obj.hits <= pick_obj.hitsMax * .6:
                                random_chance = 0

                else:
                    random_chance = random.randint(0, 10)

                if random_chance != 0:
                    creep.say('🔄물류,염려말라!', True)
                    creep.memory.priority = 2
                # 9% 확률로 발동함.
                else:
                    creep.say('🔧REGULAR✔⬆', True)
                    creep.memory.priority = 3

        # PRIORITY 1: construct
        if creep.memory.priority == 1:
            if not creep.memory.work:
                creep.memory.priority = 2
                creep.say('건설못함 ㅠㅠ', True)
                return

            try:
                # dont have a build_target and not in proper room - get there firsthand.
                if creep.memory.assigned_room != creep.room.name and not creep.memory.build_target:

                    get_to_da_room(creep, creep.memory.assigned_room, False)

                    return
            except:
                print('no visual in room {}'.format(creep.memory.assigned_room))
                return

            # print('construction:', construction)
            if not creep.memory.build_target:
                construction = creep.pos.findClosestByRange(constructions)
                if not construction:
                    creep.memory.priority = 0
                    creep.memory.laboro = 0
                    return
                creep.memory.build_target = construction.id

            build_result = creep.build(Game.getObjectById(creep.memory.build_target))  # construction)
            creep.say(build_result)
            # print('build_result:', build_result)
            if build_result == ERR_NOT_IN_RANGE:
                move_res = creep.moveTo(Game.getObjectById(creep.memory.build_target)
                                        , {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 10, 'range': 3})
                # print('move_res:', move_res)
            # if there's nothing to build or something
            elif build_result == ERR_INVALID_TARGET:
                # if there's no more construction sites, get back grabbing energy.
                if len(constructions) == 0 and _.sum(creep.carry) >= creep.carryCapacity * .6:
                    # print(creep.name, 'con', 11)
                    creep.memory.priority = 2
                    del creep.memory.build_target
                elif len(constructions) == 0:
                    # print(creep.name, 'con', 22)
                    creep.memory.priority = 0
                    creep.memory.laboro = 0
                    del creep.memory.build_target
                # if there are more, return to priority 0 to decide what to do.
                else:
                    # print(creep.name, 'con', 33)
                    creep.memory.priority = 0
                    del creep.memory.build_target
            elif build_result == ERR_NO_BODYPART:
                creep.memory.priority = 2
                creep.say('건설못함..', True)
                return

        # PRIORITY 2: carry 'em
        elif creep.memory.priority == 2:

            if len(repairs) > 0 and creep.memory.work:
                repair_on_the_way(creep, repairs, constructions, False, True)

            # 우선 무작정 본진으로 간다. 지정된 길 이용하면 됨.
            if not creep.room.name == creep.memory[home_room]:
                path = []
                for i in creep.memory[to_home]:
                    path.append(__new__(RoomPosition(i.x, i.y, i.roomName)))

                # 우선 길따라 가되 만약 탈선되면 길에서 가장 가까운 곳으로 이동.
                move_by_path = move_with_mem(creep, creep.memory.pickup, 0, path, to_home, False)
                if move_by_path[0] == OK:
                    passed_block = move_with_mem_block_check(creep, path)
                    if not passed_block == OK:
                        creep.say('막힘: {}'.format(passed_block))
                # 만일 길에서 벗어났을 경우 가장 가까운 곳으로 이동.
                elif move_by_path[0] == ERR_NOT_FOUND:
                    move = movi(creep, creep.pos.findClosestByRange(path))
                    creep.say('집 탈선:{}'.format(move))

            # 본진도착
            else:
                # todo haul_destos 또는 그 안에 건물이 없어졌을시 대비 필요
                # 캐리어가 갈 수 있는 컨테이너·링크 등등
                haul_target_objs = []

                # TOTAL OVERHAUL
                # 캐리어가 방으로 들어오는 지점을 기준으로 조건에 맞는 모든 운반 목적지를 찾아 등록한다.
                if not creep.memory.haul_destos or not len(creep.memory.haul_destos):
                    # 기준점.
                    gijun = None
                    for i in creep.memory[to_home]:
                        if i.roomName == creep.memory.home_room:
                            gijun = __new__(RoomPosition(i.x, i.y, i.roomName))
                            break

                    if not gijun:
                        gijun = creep.pos
                    # {아이디, 타입}
                    # 캐리어가 방 진입시 자원떨굴 최대거리.
                    max_drop_distance = 6
                    # 예외적으로 스토리지는 10칸까지 찾는다.
                    distance_storage = 10
                    # 초기화. 데스토에 들어가야하는 목록: 아이디와 타입.
                    creep.memory.haul_destos = []

                    # 스토리지가 가까이 있으면 딴거 다 버리고 여따 모읍시다.
                    if creep.room.storage \
                            and len(gijun.findPathTo(creep.room.storage, {'ignoreCreeps': True})) <= distance_storage:
                        creep.memory.haul_destos.append({'id': creep.room.storage.id, 'type': STRUCTURE_STORAGE})
                    else:
                        # 방 안에 모든 전송용 링크목록
                        haul_link_objs = []
                        
                        # 전송용 링크
                        for l in creep.room.memory[STRUCTURE_LINK]:
                            if not l[for_store]:
                                haul_link_objs.append(Game.getObjectById(l.id))
                        # 모든 컨테이너.
                        # for c in creep.room.memory[STRUCTURE_CONTAINER]:
                        #     haul_target_objs.append(Game.getObjectById(c.id))

                        # print(creep.name, creep.pos.roomName, haul_link_objs)
                        # 거리조건 맞는애들로 추린다.
                        haul_target_objs = \
                            haul_link_objs.filter(
                                lambda h: len(h.pos.findPathTo(gijun, {'ignoreCreeps': True})) <= max_drop_distance)
                        # print('haul_target_objs', (haul_target_objs))
                        # 링크가 그래서 있음?
                        if len(haul_target_objs):
                            # 컨테이너는 링크에서 가장 가까운거중 max_drop_distance 절반거리 이하 값인 애들만 선택.
                            for c in creep.room.memory[STRUCTURE_CONTAINER]:
                                c_obj = Game.getObjectById(c.id)
                                closest_link = c_obj.pos.findClosestByPath(haul_link_objs, {'ignoreCreeps': True})
                                if c_obj.pos.findPathTo(closest_link, {'ignoreCreeps': True}) <= int(max_drop_distance / 2):
                                    haul_target_objs.append(c_obj)
                        # 링크가 없는 경우 컨테이너만 있다는건데 이 경우 링크찾는것과 동일한 기준으로 간다.
                        else:
                            for c in creep.room.memory[STRUCTURE_CONTAINER]:
                                c_obj = Game.getObjectById(c.id)
                                if c_obj and len(c_obj.pos.findPathTo(gijun, {'ignoreCreeps': True})) <= max_drop_distance:
                                    haul_target_objs.append(c_obj)

                        for i in haul_target_objs:
                            creep.memory.haul_destos.append({'id': i.id, 'type': i.structureType})
                        # 이전에 데스토 설정이 안되서 목록화가 안됬을 경우임.
                        if len(creep.memory.haul_destos) and creep.memory.no_desto:
                            del creep.memory.no_desto

                # 배정된 목표지가 있는가?
                if not creep.memory.haul_target:
                    # 링크인 동시에 내용물이 빈 애를 찾는다.
                    links = creep.memory.haul_destos\
                        .filter(lambda h: h.type == STRUCTURE_LINK and Game.getObjectById(h.id)
                                and Game.getObjectById(h.id).energy < Game.getObjectById(h.id).energyCapacity)

                    target_objs = []
                    # 링크가 있으면 링크가 우선권을 가진다.
                    if len(links):
                        for l in links:
                            target_objs.append(Game.getObjectById(l.id))
                    # 없으면 목록중 가장 가까운거.
                    else:
                        for l in creep.memory.haul_destos:
                            target_objs.append(Game.getObjectById(l.id))

                    print(creep.name, target_objs)
                    creep.memory.haul_target = creep.pos.findClosestByRange(target_objs).id
                    # creep.memory.haul_target = link_or_container.id
                # 여기까지 왔는데 없으면 중대한 오류임....
                # 공격으로 부셔졌던가 만들고 있는 중이거나 둘중하나
                if not creep.memory.haul_target:
                    # creep.say('목표가없다!')
                    # 여튼 없으면 가장 가까운거 집어야함 별 수 없음.
                    creep.memory.no_desto = 1
                    if creep.room.storage:
                        haul_target_objs.append(creep.room.storage)

                    creep.memory.haul_target = creep.pos.findClosestByRange(haul_target_objs).id

                # 허울타겟 인스턴스화
                haul_obj = Game.getObjectById(creep.memory.haul_target)
                # 이제 다가가는거.
                if creep.pos.isNearTo(haul_obj):
                    if creep.carry[RESOURCE_ENERGY] == 0:
                        transfer_result = ERR_NOT_ENOUGH_ENERGY
                    else:
                        transfer_result = creep.transfer(haul_obj, RESOURCE_ENERGY)
                else:
                    transfer_result = ERR_NOT_IN_RANGE

                if transfer_result == ERR_NOT_IN_RANGE:
                    if creep.memory.err_full:
                        creep.memory.err_full = 0

                    path = _.map(creep.memory.path, lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))
                    move_by_path = move_with_mem(creep, Game.getObjectById(creep.memory.haul_target), 0, path)
                    if move_by_path[0] == OK and move_by_path[1]:
                        creep.memory.path = move_by_path[2]
                # if done, check if there's anything left. if there isn't then priority resets.
                elif transfer_result == ERR_INVALID_TARGET:
                    creep.memory.err_full = 0
                    creep.memory.priority = 0
                    del creep.memory.haul_target
                # 잘 된 경우
                elif transfer_result == OK:
                    creep.memory.err_full = 0

                    # 이동 완료했는데 픽업도없고 그렇다고 일할수있는것도 아니면 죽어야함. 프론티어일 경우도 해당.
                    if (not Game.getObjectById(creep.memory.pickup) and not creep.memory.work) \
                            or creep.memory.frontier:
                        creep.suicide()
                        return

                    # 바로 새로운 대상을 찾기위해 허울타겟 제거.
                    del creep.memory.haul_target

                    # 리필 설정 없고 크립 메모리에 타겟이 있고 메모리에 컨테이너가 있는 경우 리필설정을 한다.
                    print(creep.name, 'transfer OK', creep.memory.refill)

                    # 링크일 경우 컨테이너 데스토가 존재하면 거기에 있는거 한번 빼야함. 캐리어는 기본적으로 링크에 자원을 넣는다.
                    # 또한 리필분류가 2일 경우에만 건든다.
                    if haul_obj.structureType == STRUCTURE_LINK:  # and creep.memory.refill == 2:
                        # 에너지가 있는 컨테이너가 있는지 확인...?
                        containers = creep.memory.haul_destos\
                            .filter(lambda h: h.type == STRUCTURE_CONTAINER and Game.getObjectById(h.id).store.energy > 0)

                        # 있으면 어쨌건 리필 가동.
                        if len(containers):
                            creep.memory.refill = 1
                    # 리필 초기화 보류. 생각보다 좀 써야할듯
                    # 리필이 1 뜬 상태면 현재 리필 진행중이라는 소리니 한번만 하고 종료.
                    # elif creep.memory.refill == 1:
                    #     creep.memory.refill = 2

                # 꽉차서 운송이 안되면 다른걸로 교체. 다만 운송대상이 스토리지면 빌때까지 무한대기.
                elif transfer_result == ERR_FULL and not creep.memory.haul_target == creep.room.storage.id:
                    # 카운터 설정
                    if not creep.memory.err_full and not creep.memory.err_full == 0:
                        creep.memory.err_full = 0
                    creep.memory.err_full += 1
                    # 카운터가 찼으면 즉각 교체. 교체는 링크를 우선적으로 택한다.
                    if creep.memory.err_full > 1:
                        links = []
                        # 교체할 대상이 존재하는가?
                        all_destos = []
                        # 스토리지면 빌때까지 무한대기
                        if not creep.memory.haul_target == creep.room.storage.id:
                            # print('not storage')
                            for h in creep.memory.haul_destos:
                                # 아이디 중복이면 당연 무시
                                if creep.memory.haul_target == h.id:
                                    continue
                                d_obj = Game.getObjectById(h.id)
                                print(h.type)
                                # 링크 + 안에 빈공간 존재.
                                if h.type == STRUCTURE_LINK and not d_obj.energy == d_obj.energyCapacity:
                                    # print('link')
                                    links.append(d_obj)
                                    all_destos.append(d_obj)
                                # container and not full
                                elif h.type == STRUCTURE_CONTAINER and not _.sum(d_obj.store) == d_obj.storeCapacity:
                                    # print('container')
                                    all_destos.append(d_obj)
                                # print('------')
                                del d_obj
                        # print('links {}'.format(len(links)))
                        # print('all_destos {}'.format(len(all_destos)))
                        # 초기화 용도.
                        the_target = None
                        # 링크가 존재하면 교체 들어간다.
                        if len(links):
                            the_target = creep.pos.findClosestByRange(links)
                        # 링크가 없으면 그외 남아있는게 있나 확인
                        if not the_target and len(all_destos):
                            the_target = creep.pos.findClosestByRange(all_destos)
                        # print('the_target', the_target)
                        if the_target:
                            # 타겟이 재설정됬으면 바로 이동시작한다.
                            if not the_target.pos.isNearTo(creep):
                                movi(creep, the_target, 0, 20, True)
                            else:
                                creep.transfer(the_target, RESOURCE_ENERGY)
                            creep.memory.haul_target = the_target.id
                            creep.say('변경')
                        # 이마저도 없으면 카운터 다시센다.
                        else:
                            creep.memory.err_full = -5
                            creep.say('꽉참...{}'.format(creep.memory.err_full))

                    else:
                        creep.say('꽉참...{}'.format(creep.memory.err_full))
                # 에너지 외 다른게 있는 상황. 근데 현재 개편이 많이되서 쓸일이 없을듯.
                elif transfer_result == ERR_NOT_ENOUGH_ENERGY:
                    # 떨구라고 명령
                    just_drop = True
                    stores = creep.carry
                    # 스토리지가 있는 경우에만 에너지를 별도로 저장한다. 해당사항 없으면 다 떨굶
                    if creep.room.storage:
                        if haul_obj.structureType == STRUCTURE_CONTAINER or haul_obj.structureType == STRUCTURE_STORAGE:
                            for s in Object.keys(stores):
                                if s == RESOURCE_ENERGY:
                                    continue
                                a = creep.transfer(haul_obj, s)
                                break
                        # 여기에 걸린다는건 링크라는거임. 교체시도.
                        elif creep.room.storage:
                            for h in creep.memory.haul_destos:
                                if h.type == STRUCTURE_STORAGE or h.type == STRUCTURE_CONTAINER:
                                    creep.memory.haul_target = h.id
                                    just_drop = False
                                    break
                    if just_drop:
                        for s in Object.keys(stores):
                            if s == RESOURCE_ENERGY:
                                continue
                            a = creep.drop(s)
                            break
                else:
                    creep.say('ERR {}'.format(transfer_result))

        # 수리
        elif creep.memory.priority == 3:
            if not creep.memory.work:
                creep.memory.priority = 2
                creep.say('운송만 하겠수다', True)

            repair = creep.pos.findClosestByRange(repairs)
            repair_result = creep.repair(repair)
            try:
                # 컨테이너와 3칸이상 떨어지면 복귀한다.
                if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.pickup), 3) \
                        or creep.carry.energy == 0:
                    creep.memory.laboro = 0
                    creep.memory.priority = 0
                    creep.say('🐜는 뚠뚠', True)
                    return
            except:
                # 여기 걸리면 컨테이너가 삭제된거임...
                creep.say('?? 컨테이너가!', True)
                del creep.memory.pickup
                creep.memory.priority = 1
                return

            if repair_result == ERR_NOT_IN_RANGE:
                creep.moveTo(repair, {'visualizePathStyle': {'stroke': '#ffffff'}})
            elif repair_result == ERR_INVALID_TARGET:
                creep.memory.priority = 0
            elif repair_result == ERR_NO_BODYPART:
                creep.memory.priority = 2
            elif repair_result == 0:
                if _.sum(Game.getObjectById(creep.memory.pickup).store) \
                        == Game.getObjectById(creep.memory.pickup).storeCapacity:
                    creep.say('수리보다 운송!', True)
                    creep.memory.laboro = 0
                    creep.memory.priority = 0
                    # 컨테이너 꽉차서 라보로 0인걸 표기.
                    creep.memory.container_full = 1
        return
