from defs import *
import harvest_stuff
import miscellaneous
from _custom_constants import *
from typing import List
import movement

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
        1. harvest stuff to areas. in this case they also must harvest dropped_all resources.
        1-1. after this the harvester won't leave anywhere else than areas close to them. distributor will carry 4 them 
        2. if theres no place to collect they go and help up with upgrading.
        3. there are currently 5 harvesters. when python is made i only need 1 or 2(probably). 
        size: 
    spawn.createCreep([WORK,WORK,WORK,WORK,CARRY,CARRY,CARRY,CARRY,MOVE,MOVE,MOVE,MOVE], undefined, {role: 'harvester'})
    spawn.createCreep([WORK,WORK,WORK,CARRY,CARRY,CARRY,MOVE,MOVE,MOVE], undefined, {role: 'harvester'}) - smaller

'''


def run_harvester(creep: Creep, all_structures: List[Structure], constructions: List[ConstructionSite],
                  room_creeps: List[Creep], dropped_all: List[Resource]):
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

    # NULLIFIED
    # 할당된 방을 볼 수 없으면 방으로 우선 가고 본다.
    # if not creep.memory.source_num and creep.room.name != creep.memory.assigned_room:
    # if creep.room.name != creep.memory.assigned_room and not Game.rooms[creep.memory.assigned_room]:
    #     movement.get_to_da_room(creep, creep.memory.assigned_room, False)
    #     return

    # no memory.laboro? make one.
    if not creep.memory.laboro and creep.memory.laboro != 0:
        """
        0 = harvest
        1 = carry-to-storage|container / upgrade
        """
        creep.memory.laboro = 0

    if creep.memory.debug:
        print(creep.name, 'sourceNum:', creep.memory.source_num, bool(creep.memory.source_num))

    # if there's no source_num, need to distribute it.
    if not creep.memory.source_num and Game.rooms[creep.memory.assigned_room]:
        # print(creep.name, 'no source', JSON.stringify(Game.rooms[creep.memory.assigned_room].memory.resources))
        # 하베스터의 담당 방 내 소스 아이디 목록
        sources = []
        for r in Game.rooms[creep.memory.assigned_room].memory.resources.energy:
            sources.append(r)
        # my_room_name = creep.memory.assigned_room
        # 같은 방에 있는 모든 하베스터를 찾는다.
        rikoltist_kripoj = _.filter(Game.creeps,
                                    lambda c: (c.spawning or c.ticksToLive > 100)
                                              and c.memory.role == 'harvester'
                                              and not c.name == creep.name
                                              and creep.memory.assigned_room == c.memory.assigned_room)

        # tie estas 3 kazojn en ĉi tie:
        # 1 - no room_creeps at all.
        # 2 - there is a creep working already(1 or 2)
        # 3 - more than 2 room_creeps working
        # kazo 1
        if len(rikoltist_kripoj) == 0:
            # print('creep {} assigning harvest - rikoltist_kripoj 0'.format(creep.name))
            # 담당구역이 현재 크립이 있는곳이다?
            # if my_room == creep.room.name:
            #     se tie ne estas iu kripoj simple asignu 0
            creep.memory.source_num = sources[0]

        # kazo 2
        elif len(rikoltist_kripoj) < len(sources):
            # to check for sources not overlapping
            for i in range(len(sources)):
                source_assigned = False

                for kripo in rikoltist_kripoj:
                    # if the creep is same with current creep, or dont have memory assigned, pass.
                    if not kripo.memory.source_num:
                        continue

                    # if memory.source_num == i, means it's already taken. pass.
                    if kripo.memory.source_num == sources[i]:
                        source_assigned = True
                        break
                        # add the number to check.
                    # print('is checker({}) == i({})? : '.format(checker, i), bool(checker == i))
                if not source_assigned:
                    creep.memory.source_num = sources[i]
                    creep.memory.source_num = sources[i]
                    break

        # kazo 3 -
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
                # print('counter:', counter, typeof(counter))
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
            # print(sources, len(sources), sources[0])
            my_creeps = room_creeps
            harvester_that_is_gonna_die_soon = _.filter(my_creeps,
                                                        lambda c: c.memory.role == 'harvester' and c.tickstolive < 100
                                                                  and c.memory.source_num)
            # print('harvester_that_is_gonna_die_soon:', harvester_that_is_gonna_die_soon)
            if len(harvester_that_is_gonna_die_soon) > 0:
                creep.memory.source_num = harvester_that_is_gonna_die_soon[0].memory.source_num
            else:
                creep.memory.source_num = sources[0]
    # 크립메모리에 소스가 없고 방을 조회할 수 없는 상황이면 우선 가고본다.
    elif not creep.memory.source_num and not Game.rooms[creep.memory.assigned_room]:
        movement.get_to_da_room(creep, creep.memory.assigned_room, False)
        return

    # If you have nothing but on laboro 1 => get back to harvesting.
    if creep.store.getUsedCapacity() == 0 and not creep.memory.laboro == 0:
        if creep.ticksToLive < 5:
            return
        creep.say('☭☭', True)
        creep.memory.laboro = 0
    # if capacity is full(and on harvest phase), get to next work.
    elif (
            creep.store.getUsedCapacity() >= creep.store.getCapacity() and creep.memory.laboro == 0) or creep.ticksToLive < 5:
        if creep.ticksToLive < 5:
            creep.say('이제 갈시간 👋', True)
        else:
            creep.say('수확이다!🌾🌾', True)
        creep.memory.laboro = 1

        # 혹여나 배정된 컨테이너가 너무 멀리 있으면 리셋 용도.
        if Game.getObjectById(creep.memory.container):
            if not Game.getObjectById(creep.memory.source_num) \
                    .pos.inRangeTo(Game.getObjectById(creep.memory.container), max_range_to_container):
                del creep.memory.pickup

        del creep.memory.pickup

    # harvesting job. if on harvest(laboro == 0) and carrying energy is smaller than carryCapacity
    if creep.memory.laboro == 0:
        if creep.memory.dropped and not Game.getObjectById(creep.memory.dropped):
            del creep.memory.dropped

        # if there's no dropped_all but there's dropped_all
        if not creep.memory.dropped and len(dropped_all) > 0:
            dropped_target = harvest_stuff.filter_drops(creep, dropped_all, 3, True)

        # if there is a dropped_all target and it's there.
        if creep.memory.dropped:
            item_pickup_res = harvest_stuff.pick_drops_act(creep, True)
            if item_pickup_res == ERR_NOT_IN_RANGE or item_pickup_res == OK:
                return

        if not Game.getObjectById(creep.memory.source_num):
            del creep.memory.source_num
            return

        if creep.store.getUsedCapacity() > creep.store.getCapacity() - 10:
            creep.say('🚜 대충 찼다', True)
            creep.memory.laboro = 1
        else:
            # print(creep.name, creep.pos, creep.memory.source_num)
            harvest = harvest_stuff.harvest_energy(creep, creep.memory.source_num)

            # 대부분의 harvest_energy() 에서 실행됬음. 다만 일부 안된거 조치.
            if harvest == ERR_INVALID_TARGET:
                # 없는 타겟이면 어 우선 같은 방인지 확인하고 방이 맞으면 방으로 먼저 보내고 아니면 삭제조치.
                if creep.room.name == creep.memory.assigned_room:
                    del creep.memory.source_num
                else:
                    movement.get_to_da_room(creep, creep.memory.assigned_room, False)
            elif harvest == ERR_NOT_ENOUGH_RESOURCES_AND_CARRYING_SOMETHING:
                creep.memory.laboro = 1

    # if carryCapacity is full - then go to nearest container or storage to store the energy.
    if creep.memory.laboro == 1:
        # todo 긴급: 현재 기존 목적지가 없어졌을 경우에 대한 대비가 없다.
        # 새 작동원리:
        #   조건에 맞는 목록뽑기.
        #   뽑았으면 우선 링크로. 전부 꽉찼으면 근처 다른 컨테이너로.
        # 자원을 옮길 잠정적 목록부터 생성.
        if not creep.memory.haul_destos or len(creep.memory.haul_destos) == 0:
            creep.memory.haul_destos = []
            if creep.room.name == creep.memory.assigned_room :
                # find ALL containers(whether its full doesn't matter)
                containers = _.filter(all_structures,
                                      lambda s: s.structureType == STRUCTURE_CONTAINER)
                # store 0으로 분류된 링크 - 전송용인거
                proper_links = _.filter(creep.room.memory[STRUCTURE_LINK],
                                        lambda s: s.for_store == 0 and Game.getObjectById(s.id))
            # 무슨 이유로 하베스터 위치가 자기 방 안에 있는 상황이 아니면 그 방 쪽을 찾아야 한다.
            elif Game.rooms[creep.memory.assigned_room]:
                containers = _.filter(Game.rooms[creep.memory.assigned_room].find(FIND_STRUCTURES),
                                      lambda s: s.structureType == STRUCTURE_CONTAINER)
                proper_links = _.filter(Game.rooms[creep.memory.assigned_room].memory[STRUCTURE_LINK],
                                        lambda s: s.for_store == 0 and Game.getObjectById(s.id))
            else:
                creep.say('방이 안보여!?')
            # 오브젝트화해서 넣는거.
            proper_link_objs = []
            for i in proper_links:
                proper_link_objs.append(Game.getObjectById(i.id))

            source_obj = Game.getObjectById(creep.memory.source_num)
            # print(source_obj, creep.memory.source_num)
            # 스토리지가 존재하면 스토리지부터 찾는다.
            if creep.room.storage and creep.room.controller.my:
                # print(creep.name, 'add container')
                # 소스에서 지정된 거리 이내에 스토리지가 있으면 거기로 옮긴다
                if len(source_obj.pos.findPathTo(creep.room.storage, {ignoreCreeps: True})) <= max_range_to_container:
                    creep.memory.haul_destos.append(creep.room.storage.id)

            # 스토리지가 없으면 무조건 다 넣는다.
            if not len(creep.memory.haul_destos):
                if len(containers):
                    for c in containers:
                        if len(source_obj.pos.findPathTo(c, {ignoreCreeps: True})) <= max_range_to_container:
                            creep.memory.haul_destos.append(c.id)
                if len(proper_links):
                    for l in proper_link_objs:
                        if len(source_obj.pos.findPathTo(l, {ignoreCreeps: True})) <= max_range_to_container:
                            creep.memory.haul_destos.append(l.id)

        # 자원을 옮길 곳이 없는 경우 배정
        if not creep.memory.container:
            desto_objs: List[RoomObject] = []
            for i in range(len(creep.memory.haul_destos)):
                target_obj = Game.getObjectById(creep.memory.haul_destos[i])
                if target_obj:
                    desto_objs.append(target_obj)
                else:
                    del creep.memory.haul_destos[i]

            storage_obj: List[StructureContainer] = _.filter(desto_objs, lambda o: o.structureType == STRUCTURE_STORAGE)
            link_objs = _.filter(desto_objs, lambda o: o.structureType == STRUCTURE_LINK
                                                       and o.store.getFreeCapacity(RESOURCE_ENERGY))
            container_objs = _.filter(desto_objs, lambda o: o.structureType == STRUCTURE_CONTAINER
                                                            and o.store.getFreeCapacity())

            if len(storage_obj):
                creep.memory.container = storage_obj[0].id
            if not creep.memory.container and len(link_objs):
                for i in link_objs:
                    creep.memory.container = i.id
                    break
            if not creep.memory.container and len(container_objs):
                for i in container_objs:
                    creep.memory.container = i.id
                    break

        if creep.memory.container:
            container_obj = Game.getObjectById(creep.memory.container)
            if not container_obj:
                del creep.memory.container
                return

            if not Game.getObjectById(creep.memory.source_num).pos \
                    .inRangeTo(container_obj, max_range_to_container):
                del creep.memory.container
                return

            # HARVESTER ONLY HARVEST ENERGY(AND MAYBE RARE METALS(?)).
            # LET'S JUST NOT MAKE IT DO SOMETHING ELSE.
            # result = creep.transfer(storage, RESOURCE_ENERGY)
            result = creep.transfer(Game.getObjectById(creep.memory.container), RESOURCE_ENERGY)
            if result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.container),
                             {'reusePath': 3, vis_key: {stroke_key: '#ffffff'}})
            elif result == ERR_INVALID_TARGET:
                del creep.memory.container
            elif result == ERR_FULL:
                creep.say('차면 찬대로!', True)
                creep.memory.laboro = 0
                del creep.memory.container

            # 본인의 소스 담당 크립중에 사이즈 2짜리 크립이 존재하는지 확인. 있으면 자살한다. 이때는 굳이 있어봐야 공간낭비.
            if result == 0 and creep.memory.size == 1:
                # print('{} the {}: 0'.format(creep.name, creep.memory.role))
                for c in room_creeps:
                    if c.memory.role == 'harvester' and c.memory.size > 1 and c.ticksToLive > 200:
                        # print('creep check?: {}'.format(c.name))
                        if c.memory.source_num == creep.memory.source_num:
                            creep.moveTo(Game.getObjectById(creep.memory.source_num))
                            creep.suicide()
            if result == 0:
                del creep.memory.container
                creep.say("🚜🌾🌾", True)
                creep.memory.laboro = 0

        else:
            # if there's no storage to go to, technically do the hauler's job(transfer and building).
            # below is exact copy.
            transfer_result = ERR_INVALID_TARGET
            # 렙1일때만 채운다. 그 후는 순전히 허울러 몫.
            if creep.room.controller.my and creep.room.controller.level == 1:
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
                construction: ConstructionSite = creep.pos.findClosestByRange(constructions)
                build_result = creep.build(construction)
                if build_result == ERR_NOT_IN_RANGE:
                    movement.movi(creep, construction.id, 3)


def run_miner(creep: Creep, all_structures):
    """
    for mining minerals.

    :param creep: The creep to run
    :param all_structures: creep.room.find(FIND_STRUCTURES)
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
    if creep.store.getUsedCapacity() == 0 and creep.memory.laboro == 1:
        # if about to die, just die lol
        if creep.ticksToLive < 5:
            return
        creep.say('☭☭', True)
        creep.memory.laboro = 0
    # if capacity is full(and on harvest phase), get to next work.
    elif (
            creep.store.getUsedCapacity() >= creep.store.getCapacity() and creep.memory.laboro == 0) or creep.ticksToLive < 5:

        creep.memory.laboro = 1

    # mine
    if creep.memory.laboro == 0:

        mine_result = creep.harvest(Game.getObjectById(creep.memory.mineral))

        # 멀리있으면 다가간다
        if mine_result == ERR_NOT_IN_RANGE:
            if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.mineral), 6):
                move_by_path = movement.move_with_mem(creep, creep.memory.mineral)
                if move_by_path[0] == OK:
                    if move_by_path[1]:
                        creep.memory.path = move_by_path[2]
                else:
                    creep.say('{}'.format(move_by_path[0]))
            else:
                if creep.memory.path:
                    del creep.memory.path
                movement.movi(creep, creep.memory.mineral, 0, 3)

        # ----------------------------------------------------------------
        # 바로옆이 아니면 우선 다가간다.
        if not creep.pos.isNearTo(Game.getObjectById(creep.memory.mineral)):
            if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.mineral), 6):
                move_by_path = movement.move_with_mem(creep, creep.memory.mineral)
                if move_by_path[0] == OK and move_by_path[1]:
                    creep.memory.path = move_by_path[2]
                else:
                    creep.say('🌾 move{}'.format(move_by_path[0]))
            else:
                if creep.memory.path:
                    del creep.memory.path
                movement.movi(creep, creep.memory.mineral, 0, 3)
            return
        # 쿨다운이 존재하면 어차피 못캐니 통과합시다.
        elif Game.getObjectById(creep.memory.extractor).cooldown:
            return

        mine_result = creep.harvest(Game.getObjectById(creep.memory.mineral))
        # 위 기능들로 인해 이제 의미없는 작업이 된듯..?
        # se ne estas en atingopovo(reach), iru.
        if mine_result == ERR_NOT_IN_RANGE or mine_result == ERR_NOT_ENOUGH_ENERGY:
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
            # print('storage:', storage)
            # print('id:', storage.id)
            creep.memory.container = storage.id
            # for_harvest 설정 바꾼다.
            miscellaneous.check_for_carrier_setting(creep, creep.memory.container)

        if creep.memory.container:
            # runs for each type of resources. you know the rest.
            for resource in Object.keys(creep.store):
                mineral_transfer = creep.transfer(Game.getObjectById(creep.memory.container), resource)
                # print('res: {}, trans: {}'.format(resource, mineral_transfer))
                if mineral_transfer == ERR_NOT_IN_RANGE:
                    creep.moveTo(Game.getObjectById(creep.memory.container),
                                 {'visualizePathStyle': {'stroke': '#ffffff'}})
                    break
                elif mineral_transfer == 0:
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
