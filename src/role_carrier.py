from defs import *
import harvest_stuff
import random
import miscellaneous

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

    # 현 문제점:
    # - 건설 필요 시 배정.(?)
    # - 운송 시 목표지점 배정관련: 자꾸 스폰당시 위치에서 가장 가까운거에 해버림.
    # - 원래 픽업위치 파괴됐을 시 배정 관련. 방에 자원이 둘일때 엉켜버림. 수리가 시급함.

    end_is_near = 40
    # in case it's gonna die soon. switch to some other
    if _.sum(creep.carry) > 0 and creep.ticksToLive < end_is_near and \
            (creep.memory.laboro == 0 or (creep.memory.laboro == 1 and creep.memory.priority != 2)):
        creep.say('endIsNear')
        creep.memory.laboro = 1
        creep.memory.priority = 2
    elif _.sum(creep.carry) == 0 and creep.ticksToLive < end_is_near:
        creep.suicide()
        # creep.say('TTL: ' + creep.ticksToLive)
        # creep.moveTo(Game.getObjectById(creep.memory.upgrade_target),
        #              {'visualizePathStyle': {'stroke': '#ffffff'}, 'ignoreRoads': True, 'reusePath': 40})
        return
    elif not creep.memory.upgrade_target:
        creep.memory.upgrade_target = creep.room.controller['id']
    elif not creep.memory.home_room:
        creep.memory.home_room = creep.room.name

    if _.sum(creep.carry) == 0 and creep.memory.laboro != 0:
        creep.memory.laboro = 0
        creep.memory.priority = 0
        del creep.memory.build_target
    elif _.sum(creep.carry) == creep.carryCapacity and creep.memory.laboro != 1:
        creep.memory.laboro = 1

        if len(constructions) > 0:
            creep.memory.priority = 1
        else:
            creep.memory.priority = 2

    # laboro: 0 == pickup something.
    if creep.memory.laboro == 0:
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
            result = harvest_stuff.grab_energy(creep, creep.memory.pickup, True, 0.0)
            # print(creep.name, result)
            if result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.pickup),
                             {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 25})
            elif result == 0:
                creep.say('BEEP BEEP⛟', True)
                # if _.sum(creep.carry) >= creep.carryCapacity * .5:
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
                miscellaneous.get_to_da_room(creep, creep.memory.assigned_room, False)
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

        # if creep.memory.priority != 1:
        #     if len(repairs) > 0 and creep.memory.work:
        #         # cccc = Game.cpu.getUsed()
        #         repair = creep.pos.findClosestByRange(repairs)
        #         # bbbb = Game.cpu.getUsed() - cccc
        #         # print("repair = creep.pos.findClosestByRange(repairs) cost {} cpu".format(round(bbbb, 2)))

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
                    miscellaneous.get_to_da_room(creep, creep.memory.assigned_room, False)
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
                if len(constructions) == 0:
                    creep.memory.priority = 0
                    creep.memory.laboro = 0
                    del creep.memory.build_target
                    return
                # if there are more, return to priority 0 to decide what to do.
                else:
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
                miscellaneous.get_to_da_room(creep, creep.memory.home_room, False)
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

                # 만일 컨테이너일 경우 메모리를 뜯어서 캐리어용인지 마킹을 한다.
                if link_or_container.structureType == STRUCTURE_CONTAINER \
                        or link_or_container.structureType == STRUCTURE_LINK:
                    check_for_carrier_setting(creep, link_or_container)

                creep.memory.haul_target = link_or_container.id

            transfer_result = creep.transfer(Game.getObjectById(creep.memory.haul_target), RESOURCE_ENERGY)
            if transfer_result == ERR_NOT_IN_RANGE:
                creep.memory.err_full = 0
                # creep.say(ERR_NOT_IN_RANGE)
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
                    creep.moveTo(Game.getObjectById(creep.memory.haul_target)
                                 , {'visualizePathStyle': {'stroke': '#ffffff'}
                                     , 'ignoreCreeps': True, 'reusePath': 40})
                return
                # creep.moveTo(link_or_container, {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 10})
            # if done, check if there's anything left. if there isn't then priority resets.
            elif transfer_result == ERR_INVALID_TARGET:
                creep.memory.err_full = 0
                creep.memory.priority = 0
                del creep.memory.haul_target
            elif transfer_result == 0:
                creep.memory.err_full = 0
                if creep.memory.last_switch:
                    del creep.memory.last_switch

                # 이동 완료했는데 픽업도없고 그렇다고 일할수있는것도 아니면 죽어야함.
                # 프론티어일 경우도 해당.
                if (not Game.getObjectById(creep.memory.pickup) and not creep.memory.work) \
                        or creep.memory.frontier:
                    creep.suicide()
                    return
                # 옮긴 대상이 링크인지? 아니면 링크로 교체.
                elif not Game.getObjectById(creep.memory.haul_target).structureType \
                         == STRUCTURE_LINK:
                    # 캐리어는 기본적으로 링크로 운송하는게 원칙이다.
                    # 방금 옮긴 대상건물이 링크가 아니면 찾아서 등록한다. 진짜 없으면... 걍 없는거...
                    if not creep.memory.link_target and not creep.memory.no_link:
                        links = _.filter(all_structures,
                                         lambda s: s.structureType == STRUCTURE_LINK)
                        if len(links) > 0:
                            closest_link = creep.pos.findClosestByPath(links)
                            if len(creep.room.findPath(creep.pos, closest_link.pos,
                                                       {'ignoreCreeps': True})) <= 5:
                                creep.memory.link_target = closest_link.id
                            else:
                                # 크립 주변에 링크가 없다는 소리. 위에 루프문 매번 반복 안하기 위해 생성.
                                creep.memory.no_link = 1
                    creep.memory.haul_target = creep.memory.link_target
                    creep.memory.err_full = 3
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
                        # 크립이
                        if link_or_container.structureType == STRUCTURE_CONTAINER\
                                or link_or_container.structureType == STRUCTURE_LINK:
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
