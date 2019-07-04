from defs import *
import harvest_stuff
from miscellaneous import *
from _custom_constants import *
from movement import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


'''
- harvester:  
        1. harvest stuff to areas. in this case they also must harvest dropped resources.
        1-1. after this the harvester won't leave anywhere else than areas close to them. distributor will carry 4 them 
        2. if theres no place to collect they go and help up with upgrading.
        3. there are currently 5 harvesters. when python is made i only need 1 or 2(probably). 
        size: 
    spawn.createCreep([WORK,WORK,WORK,WORK,CARRY,CARRY,CARRY,CARRY,MOVE,MOVE,MOVE,MOVE], undefined, {role: 'harvester'})
    spawn.createCreep([WORK,WORK,WORK,CARRY,CARRY,CARRY,MOVE,MOVE,MOVE], undefined, {role: 'harvester'}) - smaller

'''


def run_harvester(creep, all_structures, constructions, room_creeps, dropped_all):
    """
    Runs a creep as a generic harvester.

    :param creep: The creep to run
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
    :param room_creeps: creep.room.find(FIND_MY_CREEPS)
    :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
    """
    vis_key = "visualizePathStyle"
    stroke_key = "stroke"
    # 할당된 방에 없으면 방으로 우선 가고 본다.
    if not creep.memory.source_num and creep.room.name != creep.memory.assigned_room:
        get_to_da_room(creep, creep.memory.assigned_room, False)
        return

    # no memory.laboro? make one.
    if not creep.memory.laboro and creep.memory.laboro != 0:
        """
        0 = harvest
        1 = carry-to-storage|container / upgrade
        """
        creep.memory.laboro = 0

    # if there's no source_num, need to distribute it.
    if not creep.memory.source_num:

        # 하베스터의 담당 방 내 소스 아이디 목록
        sources = []
        for r in Game.rooms[creep.memory.assigned_room].memory.resources.energy:
            sources.append(r)
        my_room = creep.memory.assigned_room
        # 같은 방에 있는 모든 하베스터를 찾는다.
        rikoltist_kripoj = _.filter(Game.creeps,
                                    lambda c: (c.spawning or c.ticksToLive > 100)
                                               and c.memory.role == 'harvester'
                                               and not c.name == creep.name
                                               and creep.memory.assigned_room == c.memory.assigned_room)
        # 소속된 방 내 모든 스트럭쳐.
        # structures = Game.rooms[creep.memory.assigned_room]
        # 방 안에 있는 모든 컨테이너들. 슬슬 의미가 없어지는듯
        # remote_containers = _.filter(structures, lambda s: s.structureType == STRUCTURE_CONTAINER)

        # -------------------------------------------------------

        # NULLIFIED
        # if creep.memory.assigned_room and creep.room.name != creep.memory.assigned_room:
        #     try:
        #         # normale, kripos ne devus havi .find() en la skripto, sed ĉi tio estas por malproksima regiono do...
        #         # sources = Game.flags[creep.memory.flag_name].room.find(FIND_SOURCES)
        #         sources = Game.rooms[creep.memory.assigned_room].find(FIND_SOURCES)
        #         # my_room = Game.flags[creep.memory.flag_name].room.name
        #         my_room = creep.memory.assigned_room
        #         # room_creeps = Game.flags[creep.memory.flag_name].room.find(FIND_MY_CREEPS)
        #         room_creeps = Game.rooms[creep.memory.assigned_room].find(FIND_MY_CREEPS)
        #         rikoltist_kripoj = _.filter(room_creeps,
        #                                     lambda c: (c.spawning or c.ticksToLive > 100)
        #                                               and c.memory.role == 'harvester'
        #                                               and not c.name == creep.name)
        #         remote_structures = my_room.find(FIND_STRUCTURES)
        #         remote_containers = _.filter(remote_structures, lambda s: s.structureType == STRUCTURE_CONTAINER)
        #         # print('???', remote_structures )
        #     except:
        #         print('no room_creeps in the remote at room {}!'.format(creep.memory.assigned_room))
        #         return
        # else:
        #     sources = creep.room.find(FIND_SOURCES)
        #     my_room = creep.room.name
        #     rikoltist_kripoj = _.filter(room_creeps,
        #                                 lambda c: (c.spawning or c.ticksToLive > 100)
        #                                           and c.memory.role == 'harvester'
        #                                           and not c.name == creep.name)
        #     if creep.memory.flag_name:
        #         remote_containers = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_CONTAINER)

        # tie estas 3 kazojn en ĉi tie:
        # 1 - no room_creeps at all.
        # 2 - there is a creep working already(1 or 2)
        # 3 - more than 2 room_creeps working
        # kazo 1
        if len(rikoltist_kripoj) == 0:
            print('creep {} assigning harvest - rikoltist_kripoj 0'.format(creep.name))
            # 담당구역이 현재 크립이 있는곳이다?
            # if my_room == creep.room.name:
            #     se tie ne estas iu kripoj simple asignu 0
            creep.memory.source_num = sources[0]

            # 멀티방용 배정
            # NULLIFIED - 의도는 컨테이너가 근처에 있는 자원을 우선적으로 건든다는건데... 솔까 의미있나? ㄲㅈ
            # else:
            #     # 에너지 일일히 돌린다.
            #     for energy in sources:
            #         done = False
            #         print('remote_containers', remote_containers)
            #         # 컨테이너 거리 측정해서 4칸이내에 존재하는게 있으면 그걸로 붙는다.
            #         for s in remote_containers:
            #             print('energy', energy)
            #             if s.pos.inRangeTo(energy, 4):
            #                 print('inrange', energy.id)
            #                 creep.memory.source_num = energy.id
            #                 done = True
            #                 break
            #         if done:
            #             break
            #     # 있어야 하는게 정상인데 진짜 없으면 그냥 맨 첫번째꺼 배정
            #     if not creep.memory.source_num:
            #         creep.memory.source_num = sources[0].id

        # kazo 2
        elif len(rikoltist_kripoj) < len(sources):
            # to check for sources not overlapping
            for i in range(len(sources)):
                source_assigned = False
                # print('-----', i, '-----', sources[i])
                for kripo in rikoltist_kripoj:
                    # if the creep is same with current creep, or dont have memory assigned, pass.
                    if not kripo.memory.source_num:
                        continue
                    # print('creep:{} || TTL: {}'.format(kripo, kripo.ticksToLive))
                    # print('creep.memory.source_num:', kripo.memory.source_num)
                    # if memory.source_num == i, means it's already taken. pass.
                    if kripo.memory.source_num == sources[i]:
                        # print('kripo.memory.source_num({}) == i({})'.format(kripo.memory.source_num, i))
                        source_assigned = True
                        break
                        # add the number to check.
                    # print('is checker({}) == i({})? : '.format(checker, i), bool(checker == i))
                if not source_assigned:
                    creep.memory.source_num = sources[i]
                    break

        # kazo 3
        elif len(rikoltist_kripoj) >= len(sources):
            # print('creep {} - case 3: 자원채취꾼 수가 소스의 수 이상이다.'.format(creep.name))
            # 각 자원별 숫자총합이 2 이상이면 거기엔 배치할 필요가 없는거임.
            # trovu kripoj kun memory.size malpli ol 3k
            for i in range(len(sources)):
                # print('-----', i, '-----')
                # for counting number of room_creeps.
                counter = 0
                for kripo in rikoltist_kripoj:
                    # print('creep {}\'s source_num: {}'.format(kripo.name, kripo.memory.source_num))
                    # if the creep is same with current creep, or dont have memory assigned, pass.
                    if not kripo.memory.source_num:
                        # print('------pass------')
                        continue
                    # if there's a creep with 3k < size, moves to another i automatically.
                    if kripo.memory.source_num == sources[i]:
                        counter += kripo.memory.size
                    # print('counter:', counter)
                # se counter estas malpli ol du, asignu la nuna i.
                # print('counter:', counter)
                if counter < 2:
                    # print('counter is less than 2')
                    creep.memory.source_num = sources[i]
                    break

        # se la kripo ankoraŭ ne asignita?
        # trovu iu i kun 3k. sed ĉi tio ne devus okazi.

        # 위에가 안걸려서 이게 뜨는 이유: 이미 다 꽉차있거나 크립이 아예 없는거임.
        # needs to be done: 아래.
        # 이게 또 뜨는 경우가 아예 없는거 외에 이미 꽉찬건데 이 경우에는 아직 살아있는애가 있어서 겹치는 경우인데
        # 이럴때는 우선 크립의 ttl, 그리고 크립의 담당 수확지역을 찾는다.
        if not creep.memory.source_num:
            my_creeps = room_creeps
            harvester_that_is_gonna_die_soon = _.filter(my_creeps, lambda c: c.memory.role == 'harvester'
                                                                             and c.tickstolive < 100)
            # print('harvester_that_is_gonna_die_soon:', harvester_that_is_gonna_die_soon)
            if len(harvester_that_is_gonna_die_soon) > 0:
                creep.memory.source_num = harvester_that_is_gonna_die_soon[0].memory.source_num
            else:
                creep.memory.source_num = sources[0].id

    # If you have nothing but on laboro 1 => get back to harvesting.
    if _.sum(creep.carry) == 0 and not creep.memory.laboro == 0:
        if creep.ticksToLive < 5:
            return
        creep.say('☭ 다이나믹 로동!', True)
        creep.memory.laboro = 0
    # if capacity is full(and on harvest phase), get to next work.
    elif (_.sum(creep.carry) >= creep.carryCapacity and creep.memory.laboro == 0) or creep.ticksToLive < 5:
        if creep.ticksToLive < 5:
            creep.say('이제 갈시간 👋', True)
        else:
            creep.say('수확이다!🌾🌾', True)
        creep.memory.laboro = 1

        # 혹여나 배정된 컨테이너가 너무 멀리 있으면 리셋 용도.
        if Game.getObjectById(creep.memory.container):
            if not Game.getObjectById(creep.memory.source_num).pos.inRangeTo(creep.memory.container, 3):
                del creep.memory.pickup

        del creep.memory.pickup

    # harvesting job. if on harvest(laboro == 0) and carrying energy is smaller than carryCapacity
    if creep.memory.laboro == 0:
        # print(creep.name, creep.memory.dropped)
        # pickup any dropped resources on the way
        if not creep.memory.dropped:
            if dropped_all:
                for drop in dropped_all:
                    # not energy? pass
                    if drop.resourceType != RESOURCE_ENERGY:
                        continue
                    elif drop.store:
                        if drop.store.energy == 0:
                            continue
                    # print('drop', drop)
                    if creep.pos.inRangeTo(drop, 3):
                        creep.memory.dropped = drop.id
                        creep.moveTo(creep.memory.dropped, {'visualizePathStyle':
                                                           {'stroke': '#0000FF', 'opacity': .25}})
                        return
        else:
            grab_result = harvest_stuff.pick_drops(creep, True)
            creep.say('cc{}'.format(grab_result))
            if grab_result == ERR_NOT_IN_RANGE:

                creep.moveTo(Game.getObjectById(creep.memory.dropped), {'visualizePathStyle':
                                                                       {'stroke': '#0000FF', 'opacity': .25}})
                return
            elif grab_result == ERR_INVALID_TARGET:
                del creep.memory.dropped

        if _.sum(creep.carry) > creep.carryCapacity - 10:
            creep.memory.laboro = 1
        else:
            harvest = harvest_stuff.harvest_energy(creep, creep.memory.source_num)

    # if carryCapacity is full - then go to nearest container or storage to store the energy.
    if creep.memory.laboro == 1:
        # 자원을 옮길 위치
        if not creep.memory.container:
            # find ALL containers(whether its full doesn't matter)
            containers = _.filter(all_structures,
                                  lambda s: s.structureType == STRUCTURE_CONTAINER)
            proper_links = _.filter(creep.room.memory[STRUCTURE_LINK], lambda s: s.for_store == 0)
            proper_link = []
            for i in proper_links:
                if i:
                    proper_link.append(Game.getObjectById(i.id))
            if len(proper_link) > 0:
                containers.extend(proper_link)
            if creep.room.storage and creep.room.controller.my:
                print('add container')
                containers.append(creep.room.storage)
                # 4칸이내에 스토리지가 있으면 거기로 옮긴다
                if len(creep.pos.findPathTo(creep.room.storage, {ignoreCreeps: True})) < 5:
                    creep.memory.container = creep.room.storage.id
            # print(creep.name, containers)
            closest = \
                Game.getObjectById(creep.memory.source_num).pos.findClosestByPath(containers, {ignoreCreeps: True})

            # print('storage', closest)

            if not closest:
                pass
            # 근처에 스토리지가 있는게 아니면 낭비임. 그냥 주변에 건설이나 실시한다.
            elif not Game.getObjectById(creep.memory.source_num).pos.inRangeTo(closest, max_range_to_container):
                del creep.memory.container
            else:
                creep.memory.container = closest.id

        if creep.memory.container:
            container_obj = Game.getObjectById(creep.memory.container)
            if not container_obj:
                del creep.memory.container
                return

            if not Game.getObjectById(creep.memory.source_num).pos\
                    .inRangeTo(container_obj, max_range_to_container):
                # print('huh?')
                del creep.memory.container
                return

            # HARVESTER ONLY HARVEST ENERGY(AND MAYBE RARE METALS(?)). JUST LET'S NOT MAKE IT DO SOMETHING ELSE.
            # result = creep.transfer(storage, RESOURCE_ENERGY)
            if not creep.pos.isNearTo(container_obj):
                result = ERR_NOT_IN_RANGE
                creep.moveTo(Game.getObjectById(creep.memory.container),
                             {'reusePath': 3, vis_key: {stroke_key: '#ffffff'}})
            elif not container_obj:
                result = ERR_INVALID_TARGET
                del creep.memory.container
            elif container_obj.structureType == STRUCTURE_LINK \
                    and container_obj.energy == container_obj.energyCapacity\
                    or _.sum(container_obj.store) == container_obj.storeCapacity:
                result = ERR_FULL
                creep.say('차면 찬대로!', True)
                creep.memory.laboro = 0
            else:
                result = creep.transfer(Game.getObjectById(creep.memory.container), RESOURCE_ENERGY)

            # todo 링크 하베스트 최우선으로. nu, ankaŭ devas havi la....  
            # 본인의 소스 담당 크립중에 사이즈 2짜리 크립이 존재하는지 확인. 있으면 자살한다. 이때는 굳이 있어봐야 공간낭비.
            if result == 0 and creep.memory.size == 1:
                # print('{} the {}: 0'.format(creep.name, creep.memory.role))
                for c in room_creeps:
                    if c.memory.role == 'harvester' and c.memory.size > 1 and c.ticksToLive > 200:
                        # print('creep check?: {}'.format(c.name))
                        if c.memory.source_num == creep.memory.source_num:
                            creep.moveTo(Game.getObjectById(creep.memory.source_num))
                            creep.suicide()

        else:
            # if there's no storage to go to, technically do the hauler's job(transfer and building).
            # below is exact copy.
            spawns_and_extensions = _.filter(all_structures,
                                             lambda s: ((s.structureType == STRUCTURE_SPAWN
                                                         or s.structureType == STRUCTURE_EXTENSION)
                                                        and s.energy < s.energyCapacity))
            spawn_or_extension = creep.pos.findClosestByRange(spawns_and_extensions)
            transfer_result = creep.transfer(spawn_or_extension, RESOURCE_ENERGY)
            if transfer_result == ERR_NOT_IN_RANGE:
                creep.moveTo(spawn_or_extension, {'visualizePathStyle': {'stroke': '#ffffff'},
                                                  'ignoreCreeps': True})
            elif transfer_result == ERR_INVALID_TARGET:
                construction = creep.pos.findClosestByRange(constructions)
                build_result = creep.build(construction)
                if build_result == ERR_NOT_IN_RANGE:
                    creep.moveTo(construction, {'visualizePathStyle': {'stroke': '#ffffff'}})

    return


def run_miner(creep, all_structures):
    """
    for mining minerals.

    :param creep: The creep to run
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param minerals: creep.room.find(FIND_MINERALS)
    :return:
    """

    # process:
    # 1. look for minerals and go there.
    # 2. mine and store

    # no memory.laboro? make one.
    if not creep.memory.laboro:
        """
        0 = harvest
        1 = carry-to-storage|container / upgrade
        """
        creep.memory.laboro = 0

    # memory.extractor == extractor dude. what else.
    # memory.mineral == mineral
    if not creep.memory.extractor or not creep.memory.mineral:
        try:
            minerals = creep.room.find(FIND_MINERALS)
            for s in all_structures:
                if s.structureType == STRUCTURE_EXTRACTOR:
                    creep.memory.extractor = s.id
                    break

            # extractors = all_structures.filter(lambda s: s.structureType == STRUCTURE_EXTRACTOR)
            # there's only one mineral per room anyway.
            # creep.memory.extractor = extractors[0].id
            creep.memory.mineral = minerals[0].id
        except:
            creep.say("광물못캐!!", True)
            return

    # If you have nothing but on laboro 1 => get back to harvesting.
    if _.sum(creep.carry) == 0 and creep.memory.laboro == 1:
        # if about to die, just die lol
        if creep.ticksToLive < 5:
            return
        creep.say('☭ 다이나믹 로동!', True)
        creep.memory.laboro = 0
    # if capacity is full(and on harvest phase), get to next work.
    elif (_.sum(creep.carry) >= creep.carryCapacity and creep.memory.laboro == 0) or creep.ticksToLive < 5:

        creep.memory.laboro = 1

    # mine
    if creep.memory.laboro == 0:
        # 바로옆이 아니면 우선 다가간다.
        if not creep.pos.isNearTo(Game.getObjectById(creep.memory.mineral)):
            creep.moveTo(Game.getObjectById(creep.memory.mineral), {'visualizePathStyle':
                                                                    {'stroke': '#0000FF', 'opacity': .25},
                                                                    'ignoreCreeps': True, 'reusePath': 40})
            return
        # 쿨다운이 존재하면 어차피 못캐니 통과합시다.
        elif Game.getObjectById(creep.memory.extractor).cooldown:
            return

        mine_result = creep.harvest(Game.getObjectById(creep.memory.mineral))
        # 위 기능들로 인해 이제 의미없는 작업이 된듯..?
        # se ne estas en atingopovo(reach), iru.
        if mine_result == ERR_NOT_IN_RANGE\
                or mine_result == ERR_NOT_ENOUGH_ENERGY:
            creep.moveTo(Game.getObjectById(creep.memory.mineral), {'visualizePathStyle':
                                                                    {'stroke': '#0000FF', 'opacity': .25},
                                                                    'ignoreCreeps': True, 'reusePath': 40})
        # if mined successfully or cooldown in effect
        elif mine_result == 0:
            pass
        else:
            print('mine error:', mine_result)
        return

    # put them into the container
    elif creep.memory.laboro == 1:

        if Game.time % 2 == 0:
            creep.say('⚒s of 🌏', True)
        else:
            creep.say('UNITE!', True)
        # no container? go find it
        if not creep.memory.container:
            # find ALL storages(whether its full doesn't matter)
            storages = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_STORAGE
                                                          or s.structureType == STRUCTURE_CONTAINER)
            # print(storages)
            storage = creep.pos.findClosestByRange(storages)
            print('storage:', storage)
            print('id:', storage.id)
            creep.memory.container = storage.id
            # for_harvest 설정 바꾼다.
            check_for_carrier_setting(creep, creep.memory.container)

        if creep.memory.container:
            # runs for each type of resources. you know the rest.
            for resource in Object.keys(creep.carry):
                # if creep.carry()
                mineral_transfer = creep.transfer(Game.getObjectById(creep.memory.container), resource)
                # print('res: {}, trans: {}'.format(resource, mineral_transfer))
                if mineral_transfer == ERR_NOT_IN_RANGE:
                    creep.moveTo(Game.getObjectById(creep.memory.container), {'visualizePathStyle': {'stroke': '#ffffff'}})
                    break
                elif mineral_transfer == 0:
                    # print('OK')
                    break
                elif mineral_transfer == ERR_INVALID_TARGET:
                    print('ERROR?')
                    del creep.memory.container
                    break
                elif mineral_transfer == ERR_NOT_ENOUGH_ENERGY:
                    continue
                else:
                    # print('mineral_transfer ERROR:', mineral_transfer)
                    pass
        else:
            print("WTF no container????")

    return


# def run_demolition_collector(creep, dropped_all, )