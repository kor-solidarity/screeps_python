from defs import *
import harvest_stuff
import random
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

    # 인생정리모드 돌입(?)
    end_is_near = 40

    # 
    min_distance_to_other_containers = 6

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

    if _.sum(creep.carry) == 0 and creep.memory.laboro != 0:
        creep.memory.laboro = 0
        creep.memory.priority = 0

        if not creep.memory.build_target:
            # 본진에 물건 다 올렸을때만 가동.
            # 컨테이너와 링크 둘 다 존재하면 캐리어가 컨테이너에 있는 에너지를 링크에 옮겨넣을지 확인한다.
            if creep.memory.container and creep.memory.link_target:
                # print('refill setting', creep.name, creep.memory.refill)
                # 크립에 리필작업이 설정이 안되있는가?
                if not creep.memory.refill:
                    creep.memory.refill = 1
                    # print('null')
                # 크립이 리필작업을 수행중이었나? 그럼 다 한걸로 친다.
                elif creep.memory.refill == 1:
                    creep.memory.refill = 2
                    # print('1')
                # 엘스가 걸린다면 refill == 2.
                # 리필 다 하고 리모트에서 새로 가져오는중이었단거. 리필확인해야함.
                else:
                    # print('els')
                    creep.memory.refill = 1
            # 해당사항 없으면 리필작업 할필요없음.
            else:
                # print('refill wtf', creep.name)
                creep.memory.refill = 0

        del creep.memory.build_target

    elif _.sum(creep.carry) >= creep.carryCapacity * .6 and creep.memory.laboro != 1:
        creep.say('?!?')
        creep.memory.laboro = 1

    if creep.memory.haul_target and not Game.getObjectById(creep.memory.haul_target):
        del creep.memory.haul_target

    # laboro: 0 == pickup something.
    if creep.memory.laboro == 0:
        # 운송 시작할 시 컨테이너에 자원이 있고 근처 할당된 링크가 꽉 안참? 그럼 컨테이너에서 링크로 옮긴다.
        # memory.refill 로 확인한다 0이면 컨테이너가 아예없는거, 1이면 확인해야함. 2면 이미 확인함.
        # 확인을 아직 안했고 크립이 본진이며, 링크 ID를 저장해두고 있는가?
        if creep.memory.refill == 1 and creep.room.name == creep.memory.home_room \
                and creep.memory.link_target:
            # 시작전 컨테이너가 존재하는지 확인.
            if creep.memory.container and not Game.getObjectById(creep.memory.container):
                del creep.memory.container

            # 링크안에 에너지가 꽉 찬 상태면 어차피 못채우니 끝.
            if Game.getObjectById(creep.memory.link_target).energyCapacity == \
                    Game.getObjectById(creep.memory.link_target).energy:
                creep.memory.refill = 2
            # 저장된 컨테이너가 없으면 이걸 돌릴 이유가 없음.
            elif not creep.memory.container:
                creep.memory.refill = 0
            # 만일 컨테이너에 내용물이 남아있으면 작업시작.
            elif Game.getObjectById(creep.memory.container).store[RESOURCE_ENERGY] > 0:
                grab = harvest_stuff.grab_energy(creep, creep.memory.container, True, 0)
                creep.say("refill {}".format(grab))
                # 컨테이너가 없으면 통과.
                if grab == ERR_INVALID_TARGET:
                    del creep.memory.container
                    creep.memory.refill = 0
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
                return
            else:
                creep.memory.refill = 2

        # if there's no dropped and there's dropped_all
        if not creep.memory.dropped and len(dropped_all) > 0:
            for drop in dropped_all:
                # carrier will only take energy
                # 크립정보 있으면 비석.
                if drop.creep:
                    if not drop.store[RESOURCE_ENERGY]:
                        continue
                elif drop.resourceType != RESOURCE_ENERGY:
                    continue
                # if there's a dropped resources near 5
                if creep.pos.inRangeTo(drop, 5):
                    creep.memory.dropped = drop['id']
                    print(drop['id'])
                    creep.say('⛏BITCOINS!', True)
                    break

        # if there is a dropped target and it's there.
        if creep.memory.dropped:
            item = Game.getObjectById(creep.memory.dropped)
            if not item:
                creep.say('')
                del creep.memory.dropped
                return
            # if the target is a tombstone
            if item.creep:
                if _.sum(item.store) == 0:
                    creep.say("💢 텅 비었잖아!", True)
                    del creep.memory.dropped
                    return
                # for resource in Object.keys(item.store):
                grab = harvest_stuff.grab_energy(creep, creep.memory.dropped, False, 0)
            else:
                grab = creep.pickup(item)

            if grab == 0:
                del creep.memory.dropped
                creep.say('♻♻♻', True)
            elif grab == ERR_NOT_IN_RANGE:
                creep.moveTo(item,
                             {'visualizePathStyle': {'stroke': '#0000FF', 'opacity': .25},
                              'reusePath': 10})
                return
            # if target's not there, go.
            elif grab == ERR_INVALID_TARGET:
                del creep.memory.dropped
                for drop in dropped_all:
                    # if there's a dropped resources near 5
                    if creep.pos.inRangeTo(drop, 5):
                        creep.memory.dropped = dropped_all['id']

        # if there's pickup, no need to go through all them below.
        # creep.memory.pickup == id of the container carrier's gonna pick up
        if creep.memory.pickup:
            # 1. if 1 == False, look for storage|containers to get the energy from.
            # 2. if 2 == False, you harvest on ur own.
            result = harvest_stuff.grab_energy(creep, creep.memory.pickup, False, 0.0)
            # print(creep.name, result)
            if result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.pickup),
                             {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 25})
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
            # 이게 안뜬다는건 방이 안보인다는 소리. 우선 가고본다.
            # 캐리어가 소스 없는 방으로 갈리가....
            if not Game.rooms[creep.memory.assigned_room]:
                get_to_da_room(creep, creep.memory.assigned_room, False)
                return

            # 여기로 왔다는건 할당 컨테이너가 없다는 소리. 한마디로 not creep.memory.pickup == True
            # 수정:
            # 이게 뜨면 무조건 먼져 담당구역으로 간다. 간 후 담당 리소스를 확인한다.(이건 스폰 시 자동)
            # 그 후에 배정받은 픽업이 존재하는지 확인한다.
            # 배정받은 픽업이 존재하면 그걸로 끝. 없으면 건설담당인 셈. 자원 캔다.

            # pickup이 없으니 자원캐러 간다.
            harvest = harvest_stuff.harvest_energy(creep, creep.memory.source_num)
            # print(creep.name, 'harvest', harvest)
            if harvest == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.source_num)
                             , {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 25})
            # 컨테이너 건설을 해야 하는데 일을 못하는 놈이면 죽어라.
            elif harvest == ERR_NO_BODYPART:
                creep.suicide()
                return
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
            if not creep_body_has_work:
                creep.say('🔄물류,염려말라!', True)
                creep.memory.priority = 2
            elif len(constructions) > 0:
                creep.say('🚧 건설투쟁!', True)
                creep.memory.priority = 1
            else:
                # 수리할 것이 있는가? 있으면 확률 발동. 없으면 1 고정. 20% 이하 체력건물이 있으면 100%
                # 이제 있을때만 적용.
                if len(repairs) > 0:
                    random_chance = 1
                    if creep.memory.pickup:
                        for repair in repairs:
                            if Game.getObjectById(creep.memory.pickup).pos.inRangeTo(repair, 3):
                                if repair.hits <= repair.hitsMax * .6:
                                    random_chance = 0
                                    break
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
                    # constructions = Game.flags[creep.memory.flag_name].room.find(FIND_CONSTRUCTION_SITES)
                    # print('?', constructions)
                    get_to_da_room(creep, creep.memory.assigned_room, False)
                    # creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'}
                    #     , 'reusePath': 25})
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
            # if you're not in the home_room and no haul_target
            if creep.room.name != creep.memory.home_room and not creep.memory.haul_target:
                # at first it was to move to controller.
                # but somehow keep getting an error, so let's try
                if len(repairs) > 0 and creep.memory.work:
                    repair = creep.pos.findClosestByRange(repairs)
                    creep.repair(repair)
                get_to_da_room(creep, creep.memory.home_room, False)
                return

            # fixed container/link target to move to.
            if not creep.memory.haul_target:
                # all_structures in the home room
                # home_structures = Game.rooms[creep.memory.home_room].find(FIND_STRUCTURES)
                # find links outside the filter and containers
                outside_links_and_containers = \
                    _.filter(all_structures,
                             lambda s: s.structureType == STRUCTURE_CONTAINER or s.structureType == STRUCTURE_STORAGE
                             or s.structureType == STRUCTURE_LINK)

                link_or_container = creep.pos.findClosestByRange(outside_links_and_containers)

                # 메모리를 뜯어서 캐리어용인지 마킹을 한다.
                if link_or_container.structureType == STRUCTURE_CONTAINER:
                    creep.memory.container = link_or_container.id
                    check_for_carrier_setting(creep, link_or_container)
                elif link_or_container.structureType == STRUCTURE_LINK:
                    check_for_carrier_setting(creep, link_or_container)

                creep.memory.haul_target = link_or_container.id

            transfer_result = creep.transfer(Game.getObjectById(creep.memory.haul_target), RESOURCE_ENERGY)
            if transfer_result == ERR_NOT_IN_RANGE:
                creep.memory.err_full = 0
                if len(repairs) > 0 and creep.memory.work:
                    repair = creep.pos.findClosestByRange(repairs)
                    creep.repair(repair)
                # counter for checking the current location
                if not creep.memory.move_ticks and not creep.memory.move_ticks == 0:
                    creep.memory.move_ticks = 0
                # checking current location - only needed when check in par with move_ticks
                if not creep.memory.cur_Location:
                    creep.memory.cur_Location = creep.pos
                else:
                    # 만약 있으면 현재 크립위치와 대조해본다. 동일하면 move_ticks 에 1 추가 아니면 1로 초기화.

                    if JSON.stringify(creep.memory.cur_Location) \
                            == JSON.stringify(creep.pos):
                        creep.memory.move_ticks += 1
                    else:
                        creep.memory.move_ticks = 0
                # renew
                creep.memory.cur_Location = creep.pos

                # 걸린다는건 앞에 뭔가로 걸렸다는 소리.
                if creep.memory.move_ticks > 1:
                    for c in creeps:
                        if creep.pos.inRangeTo(c, 1) and not c.name == creep.name\
                                and not c.memory.role == 'carrier' and not c.id == creep.memory.last_switch:
                            creep.say('GTFO', True)
                            # 바꿔치기.
                            c.moveTo(creep)
                            creep.moveTo(c)
                            # 여럿이 겹쳤을때 마지막 움직였던애랑 계속 바꿔치기 안하게끔.
                            creep.memory.last_switch = c.id
                            return
                    # 여기까지 왔으면 틱이 5 넘겼는데 주변에 크립이 없는거임...
                    creep.memory.move_ticks = 0

                # 해당사항 없으면 그냥 평소처럼 움직인다.
                else:
                    creep.moveTo(Game.getObjectById(creep.memory.haul_target),
                                 {'visualizePathStyle': {'stroke': '#ffffff'},
                                  'ignoreCreeps': True, 'reusePath': 40})
                return
                # creep.moveTo(link_or_container, {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 10})
            # if done, check if there's anything left. if there isn't then priority resets.
            elif transfer_result == ERR_INVALID_TARGET:
                creep.memory.err_full = 0
                creep.memory.priority = 0
                del creep.memory.haul_target
            elif transfer_result == OK:
                creep.memory.err_full = 0
                # 교차이동한 크립이 있었으면 초기화
                if creep.memory.last_switch:
                    del creep.memory.last_switch

                if not creep.memory.refill and creep.memory.link_target and creep.memory.container:
                    creep.memory.refill = 1

                # 이동 완료했는데 픽업도없고 그렇다고 일할수있는것도 아니면 죽어야함.
                # 프론티어일 경우도 해당.
                if (not Game.getObjectById(creep.memory.pickup) and not creep.memory.work) \
                        or creep.memory.frontier:
                    creep.suicide()
                    return
                # 옮긴 대상이 링크인지? 아니면 링크로 교체.
                elif not Game.getObjectById(creep.memory.haul_target).structureType == STRUCTURE_LINK:
                    if creep.memory.link_target:
                        if not Game.getObjectById(creep.memory.link_target):
                            del creep.memory.link_target
                    if creep.memory.container:
                        if not Game.getObjectById(creep.memory.container):
                            del creep.memory.container
                    # 캐리어는 기본적으로 링크로 운송하는게 원칙이다.
                    # 방금 옮긴 대상건물이 링크가 아니면 찾아서 등록한다. 진짜 없으면... 걍 없는거...
                    if not creep.memory.link_target and not creep.memory.no_link:
                        links = _.filter(all_structures,
                                         lambda s: s.structureType == STRUCTURE_LINK)
                        # 방 안에 링크가 있는지 확인.
                        if len(links) > 0:
                            # 있으면 가장 가까운거 찾고 그게 6칸이내에 있으면
                            # 추후 옮긴대상이 링크가 아닐 경우를 대비한 아이디로 등록한다.
                            closest_link = creep.pos.findClosestByPath(links)
                            if len(creep.room.findPath(creep.pos, closest_link.pos,
                                                       {'ignoreCreeps': True})) <= 6:
                                creep.memory.link_target = closest_link.id
                                check_for_carrier_setting(creep, Game.getObjectById(creep.memory.link_target))
                            else:
                                # 크립 주변에 링크가 없다는 소리. 위에 루프문 매번 반복 안하기 위해 생성.
                                creep.memory.no_link = 1
                    creep.memory.haul_target = creep.memory.link_target
                    # 다음번에 안세고 바로 컨테이너행인듯
                    creep.memory.err_full = 3
                # 링크일 경우 한번 주변에 컨테이너가 있나 둘러봅시다
                elif Game.getObjectById(creep.memory.haul_target).structureType == STRUCTURE_LINK:
                    # 컨테이너가 있으면 통과.
                    if creep.memory.container:
                        pass
                    # 없으면 찾아보기. 방법은 위에 컨테이너일때 찾는 절차와 동일하다.
                    elif not creep.memory.no_container:
                        hr_containers = _.filter(all_structures,
                                                 lambda s: s.structureType == STRUCTURE_CONTAINER)
                        # 컨테이너 못찾았으면 다음에 또 무의미하게 찾을필요 없으니.
                        checked_alt_cont = False
                        if len(hr_containers):
                            closest_cont = creep.pos.findClosestByPath(hr_containers)
                            if len(creep.room.findPath(creep.pos, closest_cont.pos,
                                                       {'ignoreCreeps': True})) <= 6:
                                checked_alt_cont = True
                                creep.memory.container = closest_cont.id
                                check_for_carrier_setting(creep, Game.getObjectById(creep.memory.container))
                        if not checked_alt_cont:
                            creep.memory.no_container = 1

            # only happens inside the home room
            elif transfer_result == ERR_FULL:
                if not creep.memory.err_full and not creep.memory.err_full == 0:
                    creep.memory.err_full = 0
                creep.memory.err_full += 1

                # 다 꽉찼으면 즉각 교체
                if creep.memory.err_full > 1:
                    # find links outside the filter and containers
                    home_links_and_containers = \
                        _.filter(all_structures,
                                 lambda s: (s.structureType == STRUCTURE_CONTAINER and _.sum(s.store) < s.storeCapacity)
                                 or (s.structureType == STRUCTURE_LINK and s.energy < s.energyCapacity)
                                 or (s.structureType == STRUCTURE_STORAGE))
                    # 근처에 있는걸로 갈아탄다.
                    link_or_container = creep.pos.findClosestByPath(home_links_and_containers)

                    # 5칸이상 떨어졌으면 교체대상이 아님.
                    if link_or_container and \
                            len(creep.room.findPath(creep.pos, link_or_container.pos, {'ignoreCreeps': True})) <= 5:
                        creep.memory.haul_target = link_or_container.id
                        # 컨테이너나 링크로 갈아탈 경우 캐려용인지 확인한다.
                        if link_or_container.structureType == STRUCTURE_CONTAINER:
                            creep.memory.container = link_or_container.id
                            check_for_carrier_setting(creep, link_or_container)
                        elif link_or_container.structureType == STRUCTURE_LINK:
                            check_for_carrier_setting(creep, link_or_container)
                        creep.say('교체!', True)
                        creep.memory.err_full = 0
                        creep.moveTo(Game.getObjectById(creep.memory.haul_target),
                                     {'visualizePathStyle': {'stroke': '#ffffff'},
                                      'ignoreCreeps': True, 'reusePath': 40})
                    # 교체대상이 전혀 없으면 대기타야함...
                    else:
                        creep.memory.err_full = -10
                        creep.say('꽉참...{}'.format(creep.memory.err_full))
                else:
                    creep.say('꽉참...{}'.format(creep.memory.err_full))
            # 에너지 외 다른게 있는 상황. 이 경우 그냥 다 떨군다.
            elif transfer_result == ERR_NOT_ENOUGH_ENERGY:
                stores = creep.carry
                for s in Object.keys(stores):
                    if s == RESOURCE_ENERGY:
                        continue
                    a = creep.drop(s)
                    break


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
