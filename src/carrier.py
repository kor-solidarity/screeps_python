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
    :param creep: Game.creep
    :param creeps: creep.room.find(FIND_MY_CREEPS)
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param constructions: FIND_CONSTRUCTION_SITES
    :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
    :param repairs:
    :param sources: creep.room.find(FIND_SOURCES)
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
        creep.say('TTL: ' + creep.ticksToLive)
        creep.moveTo(Game.rooms[creep.memory.assigned_room].controller,
                     {'visualizePathStyle': {'stroke': '#ffffff'}, 'ignoreRoads': True, 'reusePath': 40})
        return

    if _.sum(creep.carry) == 0 and creep.memory.laboro != 0:
        creep.memory.laboro = 0
        creep.memory.priority = 0
    elif _.sum(creep.carry) == creep.carryCapacity and creep.memory.laboro != 1:
        creep.memory.laboro = 1
        creep.memory.priority = 0

    # laboro: 0 == pickup something.
    if creep.memory.laboro == 0:

        # if there's no dropped_target and there's dropped_all
        if not creep.memory.dropped_target and len(dropped_all) > 0:
            for dropped in dropped_all:
                # carrier will only take energy
                if dropped.resourceType != RESOURCE_ENERGY:
                    continue
                # if there's a dropped resources near 5
                if creep.pos.inRangeTo(dropped, 5):
                    creep.memory.dropped_target = dropped['id']
                    print(dropped['id'])
                    creep.say('⛏BITCOINS!', True)
                    break

        # if there is a dropped target and it's there.
        if creep.memory.dropped_target:
            item = Game.getObjectById(creep.memory.dropped_target)
            grab = creep.pickup(item)
            if grab == 0:
                del creep.memory.dropped_target
                creep.say('♻♻♻', True)
                return
            elif grab == ERR_NOT_IN_RANGE:
                creep.moveTo(item, {'visualizePathStyle':
                                        {'stroke': '#0000FF', 'opacity': .25}, 'reusePath': 10})
                return
            # if target's not there, go.
            elif grab == ERR_INVALID_TARGET:
                del creep.memory.dropped_target
                for dropped in dropped_all:
                    # if there's a dropped resources near 5
                    if creep.pos.inRangeTo(dropped, 5):
                        creep.memory.dropped_target = dropped_all['id']

        # if there's pickup, no need to go through all them below.
        # creep.memory.pickup == id of the container carrier's gonna pick up
        if creep.memory.pickup:
            # 1. if 1 == False, look for storage|containers to get the energy from.
            # 2. if 2 == False, you harvest on ur own.

            result = harvest_stuff.grab_energy(creep, creep.memory.pickup, True)
            # print(creep.name, result)
            if result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.pickup),
                             {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 25})
            elif result == 0:
                creep.say('BEEP BEEP⛟', True)
                # if _.sum(creep.carry) >= creep.carryCapacity * .5:
                creep.memory.laboro = 1
                creep.memory.priority = 0
            elif result == ERR_NOT_ENOUGH_ENERGY:
                if _.sum(creep.carry) > 0:
                    creep.memory.laboro = 1
                    creep.memory.priority = 0
                return
            # other errors? just delete 'em
            else:
                print(creep.name, 'grab_energy() ELSE ERROR:', result)
                del creep.memory.pickup
            return

        # no pickup target? then it's a start!
        else:

            # 여기로 왔다는건 이제 막 스폰을 했거나 기존 컨테이너가 부셔졌다는 소리. 한마디로 not creep.memory.pickup == True
            # 수정:
            # 이게 뜨면 무조건 먼져 담당구역으로 간다. 간 후 담당 리소스를 확인한다.(이건 스폰 시 자동)
            # 그 후에 배정받은 픽업이 존재하는지 확인한다.
            # 배정받은 픽업이 존재하면 그걸로 끝. 없으면 건설담당인 셈. 자원 캔다.

            # 우선 반대편에 컨테이너가 있는지 확인한다. 있으면 그걸로 배정. 동시에 크립의 배정도 따진다.
            # 없을 경우 본진의 자원을 빼쓴다. 우선 스토리지 유무를 확인하고 거기에 에너지가 있으면 빼간다.
            # 스토리지가 없을 경우 컨테이너를 확인한다.
            # 다 없다? 그럼 자원캔다.....

            # no_remote == True == remote 컨테이너가 없다.
            # 있으면 거깄는 컨테이너 지정하기 위해 검색.
            if not creep.memory.no_remote and not creep.memory.build_target:
                # all buildings in the remote room. made in case
                try:
                    if Game.flags[creep.memory.flag_name].room.name == creep.room.name:
                        remote_structures = all_structures
                        remote_construction_sites = constructions
                    else:
                        remote_structures = Game.flags[creep.memory.flag_name].room.find(FIND_STRUCTURES)
                        remote_construction_sites = \
                            Game.flags[creep.memory.flag_name].room.find(FIND_CONSTRUCTION_SITES)
                except:
                    print('no visual in the room {}!'.format(Game.flags[creep.memory.flag_name].room))
                    return

                remote_containers = _.filter(remote_structures, lambda s: s.structureType == STRUCTURE_CONTAINER)
                # 여기에 걸린다면 본진에서 자원을 빼야한단 소리.
                if remote_construction_sites and len(remote_containers) == 0:
                    creep.memory.no_remote = True
                # 컨테이너가 있으면 그걸로 배정. 하나뿐 아니라 쪼개야 하는데 이건 나중에.
                else:
                    creep.memory.pickup = remote_containers[0].id
                    return

            # 컨테이너 확인용도.
            if creep.memory.no_remote == False and creep.room.name == Game.flags[creep.memory.flag_name].room.name \
                and len(_.filter(all_structures, lambda s: s.structureType == STRUCTURE_CONTAINER)) > 0:
                # 사실상 위에꺼 복붙
                remote_containers = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_CONTAINER)
                # 여기에 걸린다면 본진에서 자원을 빼야한단 소리.
                if len(remote_containers) == 0:
                    creep.memory.no_remote = True
                # 컨테이너가 있으면 그걸로 배정. 하나뿐 아니라 쪼개야 하는데 이건 나중에.
                else:
                    creep.memory.pickup = remote_containers[0].id
                    return

            try:
                # carrier_pickup == 첫 스폰 시 건설작업이 필요할 경우 자원 뽑아가는 위치
                # there's no remote structures and no carrier_pickup
                if creep.memory.no_remote and not creep.memory.carrier_pickup:
                    # find any containers/links with any resources inside
                    storages = all_structures.filter(lambda s:
                                                     (s.structureType == STRUCTURE_CONTAINER
                                                      and _.sum(s.store) >= creep.carryCapacity * .5)
                                                     or (s.structureType == STRUCTURE_LINK
                                                         and s.energy >= creep.carryCapacity * .5
                                                         and not
                                                         (s.pos.x < 5 or s.pos.x > 44 or s.pos.y < 5 or s.pos.y > 44)))
                    carrier_pickup = miscellaneous.pick_pickup(creep, creeps, storages)
                    if carrier_pickup == ERR_INVALID_TARGET:
                        if not creep.memory.source_num:
                            if not creep.room.name == Game.flags[creep.memory.flag_name].room.name:
                                creep.moveTo(Game.flags[creep.memory.flag_name])
                                return
                            source = creep.pos.findClosestByRange(creep.room.find(FIND_SOURCES))

                            creep.memory.source_num = source.id
                        harvest_stuff.harvest_energy(creep, creep.memory.source_num)
                    else:
                        creep.memory.carrier_pickup = carrier_pickup

                # 픽업이 정해졌지만 리모트 방에 없을 경우. 픽업으로 가서 뽑는다.
                elif creep.memory.carrier_pickup and not creep.room.name == Game.flags[creep.memory.flag_name].room.name:
                    result = harvest_stuff.grab_energy(creep, creep.memory.carrier_pickup, True)
                    # print('result:', result)
                    if result == ERR_NOT_IN_RANGE:
                        creep.moveTo(Game.getObjectById(creep.memory.carrier_pickup),
                                     {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 25})
                    elif result == 0:
                        creep.say('건설현장으로!', True)
                        # if _.sum(creep.carry) >= creep.carryCapacity * .5:
                        creep.memory.laboro = 1
                        creep.memory.priority = 1
                    elif result == ERR_NOT_ENOUGH_ENERGY:
                        del creep.memory.carrier_pickup
                        return
                    # other errors? just delete 'em
                    else:
                        print(creep.name, 'grab_energy() ELSE ERROR:', result)
                        del creep.memory.carrier_pickup
                    return
                # 아직 공사작업을 해야 하는데 크립이 방 안에 있으면? 리소스로 간다.
                elif creep.room.name == Game.flags[creep.memory.flag_name].room.name:
                    if not creep.memory.source_num:
                        source = creep.pos.findClosestByRange(creep.room.find(FIND_SOURCES))
                        creep.memory.source_num = source.id
                    harvest_stuff.harvest_energy(creep, creep.memory.source_num)
            except:
                print('no visual in the room where flag "{}" is located'.format(creep.memory.flag_name))
                return

    # getting to work.
    elif creep.memory.laboro == 1:
        # PRIORITY
        # 1. if there's something to construct, do that first.
        # 2. else, carry energy or whatever to the nearest link of the assigned_room
        # 3. repair

        if creep.memory.priority == 0:
            # print(creep.name)
            # made for cases carriers dont have WORK
            creep_body_has_work = False
            for body in creep.body:
                if body.type == 'work':
                    creep_body_has_work = True
                    break

            try:
                # construction sites. only find if creep is not in its flag location.
                if creep.room.name != Game.flags[creep.memory.flag_name].room.name:
                    constructions = Game.flags[creep.memory.flag_name].room.find(FIND_CONSTRUCTION_SITES)
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

        if creep.memory.priority != 1:
            if len(repairs) > 0:
                repair = creep.pos.findClosestByRange(repairs)

        # PRIORITY 1: construct
        if creep.memory.priority == 1:
            if not creep.memory.work:
                creep.memory.priority = 2
                creep.say('건설못함 ㅠㅠ', True)
                return

            try:
                # dont have a build_target and not in proper room - get there firsthand.
                if Game.flags[creep.memory.flag_name].room.name != creep.room.name and not creep.memory.build_target:

                    # constructions = Game.flags[creep.memory.flag_name].room.find(FIND_CONSTRUCTION_SITES)
                    # print('?', constructions)

                    creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'}
                                                                      , 'reusePath': 25})
                    return
            except:
                print('no visual in flag {}'.format(creep.memory.flag_name))
                return

            # print('construction:', construction)
            if not creep.memory.build_target:
                construction = creep.pos.findClosestByRange(constructions)
                if not construction:
                    creep.memory.priority = 0
                    creep.memory.laboro = 0
                    creep.memory.no_remote = False
                    return
                creep.memory.build_target = construction.id

            build_result = creep.build(Game.getObjectById(creep.memory.build_target))  # construction)
            creep.say(build_result)
            # print('build_result:', build_result)
            if build_result == ERR_NOT_IN_RANGE:
                move_res = creep.moveTo(Game.getObjectById(creep.memory.build_target)
                                        , {'visualizePathStyle': {'stroke': '#ffffff'},  'reusePath': 25, 'range': 3})
                # print('move_res:', move_res)
            # if there's nothing to build or something
            elif build_result == ERR_INVALID_TARGET:
                # if there's no more construction sites, get back grabbing energy.
                if len(constructions) == 0:
                    creep.memory.priority = 0
                    creep.memory.laboro = 0
                    creep.memory.no_remote = False
                    del creep.memory.build_target
                    return
                # if there are more, return to priority 0 to decide what to do.
                else:
                    creep.memory.priority = 0
                    creep.memory.no_remote = False
                    del creep.memory.build_target
            elif build_result == ERR_NO_BODYPART:
                creep.memory.priority = 2
                creep.say('건설못함..', True)
                return

        # PRIORITY 2: carry 'em
        elif creep.memory.priority == 2:

            # fixed container/link target to move to.
            if not creep.memory.haul_target:
                # all_structures in the home room
                home_structures = Game.rooms[creep.memory.assigned_room].find(FIND_STRUCTURES)

                # find links outside the filter and containers
                outside_links_and_containers = _.filter(home_structures, lambda s:
                                                        s.structureType == STRUCTURE_CONTAINER
                                                        or (s.structureType == STRUCTURE_LINK and
                                                            (s.pos.x < 5 or s.pos.x > 44
                                                             or s.pos.y < 5 or s.pos.y > 44)))

            # if you're not in the assigned_room and no haul_target
            if creep.room.name != Game.rooms[creep.memory.assigned_room].name and not creep.memory.haul_target:
                # at first it was to move to controller. but somehow keep getting an error, so let's try
                if len(repairs) > 0:
                    creep.repair(repair)
                creep.moveTo(outside_links_and_containers[0],
                             {'visualizePathStyle': {'stroke': '#ffffff'}, 'ignoreCreeps': True, 'reusePath': 40})
                return

            if not creep.memory.haul_target:
                # print('this going here?')
                link_or_container = creep.pos.findClosestByRange(outside_links_and_containers)

                creep.memory.haul_target = link_or_container.id

            # transfer_result = creep.transfer(link_or_container, RESOURCE_ENERGY)
            transfer_result = creep.transfer(Game.getObjectById(creep.memory.haul_target), RESOURCE_ENERGY)
            # creep.say(transfer_result)
            # print(creep.name, 'transfer_result', transfer_result)

            if transfer_result == ERR_NOT_IN_RANGE:
                if len(repairs) > 0:
                    creep.repair(repair)
                creep.moveTo(Game.getObjectById(creep.memory.haul_target)
                             , {'visualizePathStyle': {'stroke': '#ffffff'}
                             , 'ignoreCreeps': True, 'reusePath': 40})

                return
                # creep.moveTo(link_or_container, {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 10})
            # if done, check if there's anything left. if there isn't then priority resets.
            elif transfer_result == ERR_INVALID_TARGET:
                creep.memory.priority = 0
            elif transfer_result == 0:
                # 이동 완료했는데 픽업도없고 그렇다고 일할수있는것도 아니면 죽어야함.
                if not Game.getObjectById(creep.memory.pickup) and not creep.memory.work:
                    creep.suicide()

        # 수리
        elif creep.memory.priority == 3:

            repair_result = creep.repair(repair)
            try:
                if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.pickup), 3)\
                        or _.sum(creep.carry) <= creep.carryCapacity * .35:
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
        return
