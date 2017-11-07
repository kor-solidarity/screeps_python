import harvester
import hauler
import upgrader
import structure as building_action
import scout
import carrier
import soldier
import re
import random
import miscellaneous

# defs is a package which claims to export all constants and some JavaScript objects, but in reality does
#  nothing. This is useful mainly when using an editor like PyCharm, so that it 'knows' that things like Object, Creep,
#  Game, etc. do exist.
from defs import *

# These are currently required for Transcrypt in order to use the following names in JavaScript.
# Without the 'noalias' pragma, each of the following would be translated into something like 'py_Infinity' or
#  'py_keys' in the output file.
__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')

"""
stuff you need now:
- harvester:  
        1. harvest stuff to areas. in this case they also must harvest dropped resources.
        1-1. after this the harvester won't leave anywhere else than areas close to them. distributor will carry 4 them 
        2. if theres no place to collect to they go and help up with upgrading.
        3. there are currently 5 harvesters. when python is made i only need 1 or 2(probably). 
        size: 
    spawn.createCreep([WORK,WORK,WORK,WORK,CARRY,CARRY,CARRY,CARRY,MOVE,MOVE,MOVE,MOVE], undefined, {'role': 'harvester'})
    spawn.createCreep([WORK,WORK,WORK,CARRY,CARRY,CARRY,MOVE,MOVE,MOVE], undefined, {'role': 'harvester'}) - smaller

- upgrader: 
        1. upgrade and repair a bit. 2:1 ratio.
        size:
        ([WORK,WORK,WORK,WORK,CARRY,CARRY,CARRY,MOVE,MOVE,MOVE,MOVE], undefined, {'role': 'upgrader'})
        ([WORK,WORK,CARRY,CARRY,MOVE,MOVE], undefined, {'role': 'upgrader'}) - smaller
- hauler:
        1. so... this guy does all the job carrying resources from one place to another. 
            harvester only collects to storage.
        2. this i need to make it work -  carriers repair as they move to distribute. - 2:1 ratio with 1.  
        size: 
        ([WORK,CARRY,CARRY,CARRY,CARRY,MOVE,MOVE,MOVE,MOVE], undefined, {'role': 'hauler'})
        ([WORK,CARRY,MOVE], undefined, {'role': 'hauler'}) - smaller. 
- carrier:
        1. same with hauler. but focused in remote mining.
        
        
- fighter(melee):
        1. well.... fights off enemy and also attacks.
        2. normally only makes 1 but when there's crisis more are being made.
        ([TOUGH,TOUGH,TOUGH,ATTACK,ATTACK,ATTACK,ATTACK,ATTACK,MOVE,MOVE,MOVE,MOVE,MOVE], undefined, {'role': 'melee'})
        ([TOUGH,ATTACK,ATTACK,MOVE,MOVE,MOVE], undefined, {'role': 'melee'}) - smaller 
- tower:
        1. defends. will repair when there's no enemies around. 


def harvest(role):

UNIVERSAL CODE:
creep.memory.laboro:
0 = HARVEST
1 = WORK(haul, upgrade, transfer, whatever)
2 = RALLY(집합!)
3 = ATTACK
4 = 

creep.memory.source_num:
number of source ur gonna harvest

creep.memory.priority: 작업순서. 

creep.memory.pickup: 빼내올 창고.

creep.memory.flag: 
소속된 지역 깃발. 이걸로 어떤 스폰에서 뭘 뽑아야 할지, 크립 배정 등 일체 관할. 


"""


def main():
    """
    Main game logic loop.
    """

    if not Memory.updateAlliance:
        Memory.updateAlliance = False

    try:
        # adding alliance
        if Game.time % 1 == 0 and Memory.updateAlliance:
            shard_name = Game.shard.name
            if shard_name == 'shard0':
                hostUsername = 'kirk'
            else:
                hostUsername = 'Shibdib'

            hostSegmentId = 1  # 1 for a {}, 2 for a [] or names
            segment = RawMemory.foreignSegment
            if not segment or segment.username.lower() != hostUsername.lower() \
                    or segment.id != hostSegmentId:
                # Replace log() with your logger
                print('Updating activeForeignSegment to:', hostUsername, ':', hostSegmentId)
                RawMemory.setActiveForeignSegment(hostUsername, hostSegmentId)
                Memory.updateAlliance = True
            else:
                print(JSON.parse(RawMemory.foreignSegment['data']))
                Memory.allianceArray = JSON.parse(RawMemory.foreignSegment['data'])
                # Replace log() with your logger
                print('Updating Alliance friendlies to:', JSON.stringify(Memory.allianceArray))
                Memory.updateAlliance = False
    except Exception as err:
        print('Error in RawMemory.foreignSegment handling (alliance):', err)

    try:
        # deleting unused creep memory.
        for name in Object.keys(Memory.creeps):
            if not Game.creeps[name]:
                print('Clearing non-existing creep memory(powered by python™): ' + name)
                del Memory.creeps[name]
                continue

            creep = Game.creeps[name]

            # add creep's age. just for fun lol
            try:  # since this is new....
                if not creep.spawning:
                    creep.memory.age += 1
                    if creep.memory.age % 1500 == 0 and creep.ticksToLive > 50:
                        creep.say("{}차생일!🎂🎉".format(int(creep.memory.age / 1500)), True)
                else:
                    continue
            except:
                continue
    except:
        pass

    # NULLIFIED - no longer check for dropped resources
    # # 아래 initialize_count 기준값. not rational but also affects spawning timer
    # init_count = 20
    #
    # # deletes everything so all can be remade
    # # if Memory.initialize_count > init_count:
    # if Game.time % init_count == 0:
    #     del Memory.dropped_sources

    if Memory.dropped_sources:
        del Memory.dropped_sources

    # cpu limit warning. only works when losing cpu and you have a 10 cpu limit
    if Game.cpu.bucket < 2000 and Game.cpu.limit < 20:
        print('WARNING: Game.cpu.bucket == {}'.format(Game.cpu.bucket))
    # to count the number of creeps passed.
    passing_creep_counter = 0

    # 스트럭쳐 목록 초기화 위한 숫자
    structure_renew_count = 200
    # JSON string to be put into memory
    for_json = ''

    # run everything according to each rooms.
    for chambra_nomo in Object.keys(Game.rooms):

        chambro = Game.rooms[chambra_nomo]

        # ALL .find() functions are done in here. THERE SHOULD BE NONE INSIDE CREEP FUNCTIONS!
        # filters are added in between to lower cpu costs.
        all_structures = chambro.find(FIND_STRUCTURES)

        creeps = chambro.find(FIND_MY_CREEPS)

        constructions = chambro.find(FIND_CONSTRUCTION_SITES)
        dropped_all = chambro.find(FIND_DROPPED_RESOURCES)

        hostile_creeps = chambro.find(FIND_HOSTILE_CREEPS)

        minerals = chambro.find(FIND_MINERALS)

        # 단계별 제곱근값
        square = 7.5
        # list of ALL repairs in the room.
        repairs = all_structures.filter(lambda s: (((s.structureType == STRUCTURE_ROAD
                                                     or s.structureType == STRUCTURE_TOWER
                                                     or s.structureType == STRUCTURE_EXTENSION
                                                     or s.structureType == STRUCTURE_LINK
                                                     or s.structureType == STRUCTURE_LAB
                                                     or s.structureType == STRUCTURE_CONTAINER
                                                     or s.structureType == STRUCTURE_STORAGE)
                                                    and s.hits < s.hitsMax)
                                                   or (s.structureType == STRUCTURE_WALL
                                                       and s.hits < int(square ** chambro.controller.level))
                                                   or (s.structureType == STRUCTURE_RAMPART
                                                       and s.hits < int(square ** chambro.controller.level))))
        # s.pos.isEqualTo(STRUCTURE_SPAWN)

        if not repairs or len(repairs) == 0:
            repairs = []

        # extractors = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_EXTRACTOR)
        for structure in all_structures:
            if structure.structureType == STRUCTURE_EXTRACTOR:
                extractor = structure
                break

        # to filter out the allies.
        if len(hostile_creeps) > 0:
            hostile_creeps = miscellaneous.filter_allies(hostile_creeps)

        # my_structures = _.filter(all_structures, lambda s: s.my == True)
        my_structures = chambro.find(FIND_MY_STRUCTURES)

        spawns = chambro.find(FIND_MY_SPAWNS)
        sources = chambro.find(FIND_SOURCES)

        # Run each creeps
        for chambro_creep in creeps:
            creep = Game.creeps[chambro_creep.name]

            # 만일 생산중이면 그냥 통과
            if creep.spawning:
                if not creep.memory.age and creep.memory.age != 0:
                    creep.memory.age = 0
                continue

            # but if a soldier/harvester.... nope. they're must-be-run creeps
            if creep.memory.role == 'soldier':
                soldier.run_remote_defender(creep, creeps)
                continue
            elif creep.memory.role == 'harvester':
                harvester.run_harvester(creep, all_structures, constructions, creeps, dropped_all, sources)
                """
                Runs a creep as a generic harvester.
                :param creep: The creep to run
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                :param sources: creep.room.find(FIND_SOURCES)
                """
                continue

            # run at (rate * 10)% rate at a time if bucket is less than 2k and ur on 10 cpu limit.
            if Game.cpu.bucket < 2000 and Game.cpu.limit < 20:
                rate = 2
                if random.randint(0, rate) == 0:
                    # print('passed creep:', creep.name)
                    passing_creep_counter += 1
                    continue

            if creep.memory.role == 'upgrader':
                upgrader.run_upgrader(creep, all_structures, sources)

            elif creep.memory.role == 'miner':
                harvester.run_miner(creep, all_structures, minerals)

            elif creep.memory.role == 'hauler':
                hauler.run_hauler(creep, all_structures, constructions,
                                  creeps, dropped_all, repairs, sources)
                """
                :param creep:
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                :param sources: creep.room.find(FIND_SOURCES)
                :return:
                """
            elif creep.memory.role == 'carrier' or creep.memory.role == 'helper_carrier':
                carrier.run_carrier(creep, creeps, all_structures, constructions, dropped_all, repairs, sources)
                """
                technically same with hauler, but more concentrated in carrying itself.
                    and it's for remote mining ONLY.
                :param creep: Game.creep
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                :param sources: creep.room.find(FIND_SOURCES)
                :return:
                """
            elif creep.memory.role == 'scout':
                scout.run_scout(creep)
            elif creep.memory.role == 'reserver':
                upgrader.run_reserver(creep)

        # 스폰 여럿이어서 생길 중복방지.
        room_names = []

        divider = -1
        counter = 10
        # Run each spawn every "counter" turns.
        for nesto in spawns:

            # depict exactly which spawn it is.
            spawn = Game.spawns[nesto.name]

            divider += 1
            if divider > counter:
                divider -= counter

            # this part is made to save memory and seperate functional structures out of spawn loop.
            if Game.time % structure_renew_count == 1 or not Memory.rooms:
                # TESTING PART
                print('check')
                # obj.property === obj['property']

                push_bool = True

                new_json = '{}'
                new_json = JSON.parse(new_json)
                # new_room = {spawn.room.name:{}}
                new_towers = {STRUCTURE_TOWER: []}
                # new_towers = JSON.parse(new_towers)
                new_links = {STRUCTURE_LINK: []}
                new_labs = {STRUCTURE_LAB: []}
                # if not Memory.buildings:
                #     Memory.buildings = {}
                # Memory.buildings[spawn.room.name] = new_json

                for room_name in room_names:
                    print('room_name({}) || spawn.room.name({})'.format(room_name, spawn.room.name))
                    # 순환 돌려서 하나라도 방이름 중복되면 아래 추가 안해야함.
                    if room_name == spawn.room.name:
                        print('check')
                        push_bool = False
                        break

                if push_bool:
                    # find and add towers
                    towers = _.filter(my_structures, {'structureType': STRUCTURE_TOWER})
                    if len(towers) > 0:
                        for tower in towers:
                            new_towers[STRUCTURE_TOWER].push(tower.id)
                        print('new_towers', new_towers[STRUCTURE_TOWER])
                    # find and add links
                    links = _.filter(my_structures, {'structureType': STRUCTURE_LINK})
                    if len(links) > 0:
                        for link in links:
                            new_links[STRUCTURE_LINK].push(link.id)
                        print('new_links', new_links[STRUCTURE_LINK])

                    new_jsons = [new_links, new_towers]
                    for json in new_jsons:
                        if len(json) == 0:
                            continue
                        # structure_type = Object.keys(json)
                        if not Memory.rooms:
                            Memory.rooms = {}
                        if not Memory.rooms[spawn.room.name]:
                            Memory.rooms[spawn.room.name] = {}
                        # print('Object.keys(json)', Object.keys(json))
                        # 실제로 넣을 ID
                        additive = []
                        for js in json[Object.keys(json)]:
                            additive.push(js)

                        Memory.rooms[spawn.room.name][Object.keys(json)] = additive

                    room_names.append(spawn.room.name)

            # if spawn is not spawning, try and make one i guess.
            # spawning priority: harvester > hauler > upgrader > melee > etc.
            # checks every 10 + len(Game.spawns) ticks
            if not spawn.spawning and Game.time % counter == divider:
                # ALL flags.
                flags = Game.flags
                flag_name = []

                # check all flags with same name with the spawn.
                for name in Object.keys(flags):
                    # if re.match(spawn.name, name):
                    if re.match(str(spawn.name).lower(), str(name).lower()):
                        # if there is, get it's flag's name out.
                        flag_name.push(flags[name].name)

                # ALL creeps you have
                creeps = Game.creeps

                # need each number of creeps by type. now all divided by assigned room.
                creep_harvesters = _.filter(creeps, lambda c: (c.memory.role == 'harvester'
                                                               and c.memory.assigned_room == spawn.pos.roomName
                                                               and not c.memory.flag_name
                                                               and (c.spawning or c.ticksToLive > 100)))
                creep_upgraders = _.filter(creeps, lambda c: (c.memory.role == 'upgrader'
                                                              and c.memory.assigned_room == spawn.pos.roomName
                                                              and (c.spawning or c.ticksToLive > 100)))
                creep_haulers = _.filter(creeps, lambda c: (c.memory.role == 'hauler'
                                                            and c.memory.assigned_room == spawn.pos.roomName
                                                            and (c.spawning or c.ticksToLive > 100)))
                creep_miners = _.filter(creeps, lambda c: (c.memory.role == 'miner'
                                                           and c.memory.assigned_room == spawn.pos.roomName
                                                           and (c.spawning or c.ticksToLive > 150)))

                # ﷽
                # if number of close containers/links are less than that of sources.
                harvest_carry_targets = []

                for structure in all_structures:
                    if structure.structureType == STRUCTURE_CONTAINER or structure.structureType == STRUCTURE_LINK:
                        for source in sources:
                            if source.pos.inRangeTo(structure, 3):
                                harvest_carry_targets.push(structure.id)
                                break
                    if len(harvest_carry_targets) >= len(sources):
                        break
                print('harvest_carry_targets', harvest_carry_targets)

                # if len(containers) < len(sources):
                if len(harvest_carry_targets) < len(sources):
                    # print('!!!!')
                    harvesters_bool = bool(len(creep_harvesters) < len(sources) * 2)
                # if numbers of creep_harvesters are less than number of sources in the spawn's room.
                else:
                    # to count the overall harvesting power. 3k or more == 2, else == 1
                    harvester_points = 0

                    for harvester_creep in creep_harvesters:
                        if harvester_creep.memory.size >= 3000:
                            harvester_points += 2
                        else:
                            harvester_points += 1
                    if harvester_points < len(sources) * 2:
                        harvesters_bool = True
                    else:
                        harvesters_bool = False
                        # harvesters_bool = bool(len(creep_harvesters) < len(sources))

                if harvesters_bool:
                    # check if energy_source capacity is 4.5k(4k in case they update, not likely).
                    # if is, go for size 4500.
                    if sources[0].energyCapacity > 4000:
                        regular_spawn = spawn.createCreep(
                            [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK,
                             WORK, WORK,
                             CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY]
                            , undefined,
                            {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                             'size': 4500})
                    else:
                        # perfect for 3000 cap
                        regular_spawn = spawn.createCreep(
                            [WORK, WORK, WORK, WORK, WORK, WORK,
                             CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE,
                             MOVE, MOVE]
                            , undefined,
                            {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                             'size': 3000})
                    # print('what happened:', regular_spawn)
                    if regular_spawn == -6:
                        # one for 1500 cap == need 2
                        if spawn.createCreep(
                                [WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE],
                                undefined,
                                {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                                 'size': 1500}) == -6:
                            spawn.createCreep([MOVE, WORK, WORK, CARRY], undefined,
                                              {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                                               'size': 0})  # final barrier
                    continue

                plus = 0
                for harvest_container in harvest_carry_targets:
                    # 컨테이너와 링크 둘이 공존중.
                    if Game.getObjectById(harvest_container).structureType == STRUCTURE_CONTAINER:
                        if _.sum(Game.getObjectById(harvest_container).store) \
                                > Game.getObjectById(harvest_container).storeCapacity * .89:
                            plus += 1
                        elif _.sum(Game.getObjectById(harvest_container).store) \
                                < Game.getObjectById(harvest_container).storeCapacity * .05:
                            plus -= 1
                    else:
                        if _.sum(Game.getObjectById(harvest_container).energy) \
                                > Game.getObjectById(harvest_container).energyCapacity * .89:
                            plus += 1
                        elif _.sum(Game.getObjectById(harvest_container).energy) \
                                < Game.getObjectById(harvest_container).energyCapacity * .05:
                            plus -= 1

                # for container in containers:
                #     # if container.store[RESOURCE_ENERGY] > container.storeCapacity * .89:
                #     if _.sum(container.store) > container.storeCapacity * .89:
                #         plus += 1
                #     elif _.sum(container.store) < container.storeCapacity * .05:
                #         plus -= 1
                if len(harvest_carry_targets) == 0:
                    plus = -len(sources)
                elif plus < -2:
                    plus = -2
                elif plus > 2:
                    plus = 2

                hauler_capacity = len(sources) + 1 + plus
                # print('hauler_capacity', hauler_capacity)
                # minimum number of haulers in the room is 2
                if hauler_capacity <= 1:
                    hauler_capacity = 2
                # print('hauler_capacity:', hauler_capacity)
                if len(creep_haulers) < hauler_capacity:
                    if spawn.room.energyAvailable >= spawn.room.energyCapacityAvailable * .85:
                        spawning_creep = spawn.createCreep(
                            [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                             CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY],
                            undefined, {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                        'level': 8})

                        if type(spawning_creep) == str:
                            continue
                        print('checking spawning_creep:', spawning_creep)

                    spawning_creep = spawn.createCreep([WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                                                        CARRY, CARRY, MOVE, MOVE, MOVE, MOVE, MOVE],
                                                       undefined,
                                                       {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                                        'level': 5})

                    if spawning_creep == -6:
                        if spawn.createCreep([WORK, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE], undefined,
                                             {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                              'level': 2}) == -6:
                            spawn.createCreep([MOVE, MOVE, WORK, CARRY, CARRY], undefined,
                                              {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                               'level': 0})
                    print('spawning_creep', spawning_creep)
                    print('type', type(spawning_creep))
                    continue

                # if there's an extractor, make a miner.
                if len(extractor) > 0 and len(creep_miners) == 0:

                    # continue
                    if minerals[0].mineralAmount != 0 or minerals[0].ticksToRegeneration < 120:
                        # only one is needed
                        if len(creep_miners) > 0:
                            pass
                        # make a miner
                        else:
                            spawning_creep = spawn.createCreep(
                                [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                 WORK,
                                 WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                 WORK,
                                 WORK, WORK, CARRY], undefined,
                                {'role': 'miner', 'assigned_room': spawn.pos.roomName,
                                 'level': 5})
                            if spawning_creep == 0:
                                continue

                plus = 0
                if len(creep_upgraders) < 2:
                    # some prime number.
                    if Game.time % 59999 < 11:
                        plus = 1
                    if spawn.room.controller.ticksToDowngrade < 10000:
                        plus += 1

                if spawn.room.controller.level == 8:
                    proper_level = 0
                # start making upgraders after there's a storage
                elif spawn.room.controller.level > 2 and spawn.room.storage:
                    expected_reserve = 15000
                    # if there's no storage or storage has less than 6k energy
                    if spawn.room.storage.store[RESOURCE_ENERGY] < 6000 or not spawn.room.storage:
                        proper_level = 1
                    # more than 30k
                    elif spawn.room.storage.store[RESOURCE_ENERGY] >= expected_reserve:
                        proper_level = 1
                        # extra upgrader every 30k
                        proper_level += int(spawn.room.storage.store[RESOURCE_ENERGY] / expected_reserve)
                        # max upgraders: 12
                        if proper_level > 12:
                            proper_level = 12

                    else:
                        proper_level = 1
                else:
                    proper_level = 0

                if len(creep_upgraders) < proper_level + plus \
                        and not (Game.cpu.bucket < 2000):

                    big = spawn.createCreep(
                        [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK,
                         WORK, WORK,
                         WORK,
                         WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY], undefined,
                        {'role': 'upgrader', 'assigned_room': spawn.pos.roomName, 'level': 5})
                    if big == -6:
                        if spawn.createCreep(
                                [WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                                 CARRY, CARRY, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE], undefined,
                                {'role': 'upgrader', 'assigned_room': spawn.pos.roomName, 'level': 3}) == -6:
                            # if spawn.createCreep([WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                            #                       MOVE, MOVE, MOVE, MOVE],
                            #                      undefined, {'role': 'upgrader', 'assigned_room': spawn.pos.roomName}) == -6:
                            spawn.createCreep([WORK, WORK, CARRY, CARRY, MOVE, MOVE], undefined,
                                              {'role': 'upgrader', 'assigned_room': spawn.pos.roomName})
                    continue

                # REMOTE---------------------------------------------------------------------------
                # (Game.getObjectById('59ee87577bfc4f22c043a2ad').room.findPath(
                #     Game.getObjectById('59ee87577bfc4f22c043a2ad').pos,
                #     Game.getObjectById('59bfbb35d84ef70733b4f604').pos)).length

                if len(flag_name) > 0:
                    for flag in flag_name:

                        # if seeing the room is False - need to be scouted
                        if not Game.flags[flag].room:
                            # look for scouts
                            creep_scouts = _.filter(creeps, lambda c: c.memory.role == 'scout'
                                                                      and c.memory.flag_name == flag)
                            # print('scouts:', len(creep_scouts))
                            if len(creep_scouts) < 1:
                                spawn_res = spawn.createCreep([MOVE], 'Scout-' + flag,
                                                              {'role': 'scout', 'flag_name': flag})
                                # print('spawn_res:', spawn_res)
                                break
                        else:
                            # find creeps with assigned flag.
                            remote_troops = _.filter(creeps, lambda c: c.memory.role == 'soldier'
                                                                       and c.memory.flag_name == flag
                                                                       and (c.spawning or (c.hits > c.hitsMax * .6
                                                                                           and c.ticksToLive > 100)))
                            creep_carriers = _.filter(creeps, lambda c: c.memory.role == 'carrier'
                                                                        and c.memory.flag_name == flag)
                            # and (c.spawning or c.ticksToLive > 200))
                            # exclude creeps with less than 100 life ticks so the new guy can be replaced right away
                            creep_harvesters = _.filter(creeps, lambda c: c.memory.role == 'harvester'
                                                                          and c.memory.flag_name == flag
                                                                          and (c.spawning or c.ticksToLive > 120))
                            remote_reservers = _.filter(creeps, lambda c: c.memory.role == 'reserver'
                                                                          and c.memory.flag_name == flag)

                            hostiles = Game.flags[flag].room.find(FIND_HOSTILE_CREEPS)
                            # to filter out the allies.
                            if len(hostiles) > 0:
                                hostiles = miscellaneous.filter_allies(hostiles)
                                print('len(hostiles) == {} and len(remote_troops) == {}'
                                      .format(len(hostiles), len(remote_troops)))
                            if len(hostiles) > 1:
                                plus = 1
                            else:
                                plus = 0
                            # print(Game.flags[flag].room.name, 'remote_troops', len(remote_troops))
                            if len(hostiles) + plus > len(remote_troops):
                                # second one is the BIG GUY. made in case invader's too strong.
                                if len(remote_troops) == 1:
                                    spawn_res = spawn.createCreep(
                                        [TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                         MOVE, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK,
                                         ATTACK, RANGED_ATTACK, HEAL],
                                        undefined, {'role': 'soldier', 'assigned_room': spawn.pos.roomName
                                            , 'flag_name': flag})
                                    continue
                                spawn_res = spawn.createCreep(
                                    # [TOUGH, TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, ATTACK,
                                    #  ATTACK, RANGED_ATTACK, RANGED_ATTACK, HEAL],
                                    [TOUGH, TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, ATTACK, RANGED_ATTACK,
                                     HEAL],
                                    # below too strong and slow spawn for remote defence
                                    # [TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                    #  MOVE, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK,
                                    #  ATTACK, RANGED_ATTACK, HEAL],
                                    # [TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, CARRY, CARRY, ATTACK, ATTACK, ATTACK,
                                    #  ATTACK, ATTACK
                                    #     , RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, HEAL],
                                    undefined, {'role': 'soldier', 'assigned_room': spawn.pos.roomName
                                        , 'flag_name': flag})
                                # if spawn_res == 0:
                                continue

                            # 방 안에 적이 있으면 아예 생산을 하지 않는다! 정찰대와 방위병 빼고.
                            if len(hostiles) > 0:
                                continue

                            # resources in flag's room
                            flag_energy_sources = Game.flags[flag].room.find(FIND_SOURCES)
                            flag_structures = Game.flags[flag].room.find(FIND_STRUCTURES)
                            flag_containers = _.filter(flag_structures,
                                                       lambda s: s.structureType == STRUCTURE_CONTAINER)

                            # 운송크립 확인을 위한 작업.
                            actual_avail_carriers = 0
                            carrier_pickup = None
                            for c in creep_carriers:
                                # 스폰중인가? 생명이 200이상 남았는가? 그러면 숫자 추가한다.
                                if c.spawning or c.ticksToLive > 200:
                                    actual_avail_carriers += 1
                                # 아니면 새로 생성해야하니 픽업값 넣는다.
                                else:
                                    carrier_pickup = c.memory.pickup
                            print('actual_avail_carriers', actual_avail_carriers)
                            # if len(flag_energy_sources) > len(creep_carriers):
                            if len(flag_energy_sources) > actual_avail_carriers:
                                print('pass')
                                print('carrier_pickup', carrier_pickup)
                                # 대충 해야하는일: 캐리어의 픽업위치에서 본진거리 확인. 그 후 거리만큼 추가.
                                if carrier_pickup:
                                    path = Game.getObjectById(carrier_pickup).room.findPath(
                                        Game.getObjectById(carrier_pickup).pos, spawn.pos, {'ignoreCreeps': True})
                                    distance = len(path)
                                    work_chance = random.randint(0, 1)

                                    carry_body_odd = [MOVE, MOVE, CARRY, CARRY, CARRY]
                                    carry_body_even = [MOVE, CARRY, CARRY, CARRY]
                                    work_body = [MOVE, WORK, WORK, MOVE, WORK, WORK]
                                    body = []
                                    for i in range(int(distance / 6)):
                                        if i % 2 == 1:
                                            for bodypart in carry_body_odd:
                                                body.push(bodypart)
                                        else:
                                            for bodypart in carry_body_even:
                                                body.push(bodypart)
                                        if work_chance == 0:
                                            for bodypart in work_body:
                                                body.push(bodypart)
                                    if _.sum(Game.getObjectById(carrier_pickup).store) \
                                        >= Game.getObjectById(carrier_pickup).storeCapacity * .7:
                                        print('extra')
                                        body.push(MOVE)
                                        body.push(CARRY)
                                    print('body', body)
                                    spawning = spawn.createCreep(body, undefined,
                                                      {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                                       'flag_name': flag})
                                    print('spawning', spawning)
                                    if spawning == 0:
                                        continue
                                    elif spawning == ERR_NOT_ENOUGH_RESOURCES:
                                        if work_chance == 0:
                                            body = []
                                            for i in range(int(distance / 6)):
                                                if i % 2 == 1:
                                                    for bodypart in carry_body_odd:
                                                        body.push(bodypart)
                                                else:
                                                    for bodypart in carry_body_even:
                                                        body.push(bodypart)
                                            spawn.createCreep(
                                                body,
                                                undefined,
                                                {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                                 'flag_name': flag})
                                        else:
                                            spawn.createCreep(
                                                [WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE,
                                                 MOVE, MOVE, MOVE, MOVE],
                                                undefined,
                                                {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                                 'flag_name': flag})
                                        continue
                                else:
                                    spawn.createCreep(
                                        [WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE,
                                         MOVE, MOVE, MOVE, MOVE],
                                        undefined,
                                        {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                         'flag_name': flag})
                                    continue

                                # --------------------------------------------------------
                                # # 바꿔야 하는 사안:
                                # # 1. 거리에 따라 바뀌는 용량.
                                # # 2. 1이 되려면 pickup 위치가 필요하다.
                                # # 3. 또한 haul_target 도 필요하다.
                                # # 방법:
                                # # ticksToLive 200 이하의 carrier 크립을 잡아서
                                # # 1. haul_target이 없을 경우, 방 안의 모든 건물을 찾아아
                                # # do you need a heavy load of energy?
                                # big_one = 0
                                #
                                # # if there is a container
                                # if flag_containers:
                                #     # look for containers full,
                                #     for container in flag_containers:
                                #         if container.store[RESOURCE_ENERGY] >= container.storeCapacity * .925:
                                #             big_one = 2
                                #             break
                                #         elif container.store[RESOURCE_ENERGY] >= container.storeCapacity * .60:
                                #             big_one = 1
                                #             break
                                #
                                # big_spawning = ''
                                # if big_one == 2:
                                #     # have 50:50 chance of making 900 or 1000 carryCapacity creep
                                #     chance = random.randint(0, 1)
                                #     if chance == 0:
                                #         big_spawning = spawn.createCreep(
                                #             [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, CARRY, CARRY, CARRY,
                                #              CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                #              CARRY, CARRY, CARRY, CARRY, CARRY], undefined,
                                #             {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                #              'flag_name': flag})
                                #     else:
                                #         big_spawning = spawn.createCreep(
                                #             [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, CARRY, CARRY,
                                #              CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                #              CARRY,
                                #              CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY], undefined,
                                #             {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                #              'flag_name': flag})
                                # elif big_one == 1:
                                #     # spawn have 1 out of 3 chance to make heavy load carrier
                                #     chance = random.randint(0, 2)
                                #     if chance == 0:
                                #         big_spawning = spawn.createCreep(
                                #             [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, CARRY, CARRY, CARRY,
                                #              CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                #              CARRY, CARRY, CARRY, CARRY, CARRY], undefined,
                                #             {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                #              'flag_name': flag})
                                #     else:
                                #         big_spawning = spawn.createCreep(
                                #             [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                #              MOVE,
                                #              WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY,
                                #              CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                #              CARRY,
                                #              CARRY, CARRY], undefined,
                                #             {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                #              'flag_name': flag})
                                # # 600 carry
                                # # [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                # #  WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY,
                                # #  CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                # #  CARRY, CARRY]
                                # spawning = ''
                                # if big_spawning == ERR_NOT_ENOUGH_ENERGY or big_one == 0:
                                #     spawning = spawn.createCreep(
                                #         [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK,
                                #          WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY]
                                #         , undefined,
                                #         {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                #          'flag_name': flag})
                                #
                                # if spawning == ERR_NOT_ENOUGH_ENERGY:
                                #     spawn.createCreep(
                                #         [WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE,
                                #          MOVE, MOVE,
                                #          MOVE, MOVE],
                                #         undefined,
                                #         {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                #          'flag_name': flag})
                                #     continue

                            if len(flag_containers) > len(creep_harvesters):

                                # perfect for 3000 cap
                                regular_spawn = spawn.createCreep(
                                    [WORK, WORK, WORK, WORK, WORK, WORK,
                                     CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE,
                                     MOVE, MOVE]
                                    , undefined,
                                    {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                                     'size': 3000, 'flag_name': flag})
                                # print('what happened:', regular_spawn)
                                if regular_spawn == -6:
                                    spawn.createCreep([WORK, WORK, WORK, WORK, WORK,
                                                       CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE]
                                                      , undefined,
                                                      {'role': 'harvester', 'assigned_room': spawn.pos.roomName
                                                          , 'flag_name': flag})
                                    continue

                            elif len(remote_reservers) == 0 \
                                    and (not Game.flags[flag].room.controller.reservation
                                         or Game.flags[flag].room.controller.reservation.ticksToEnd < 1200):
                                spawning_creep = spawn.createCreep([MOVE, MOVE, MOVE, MOVE, CLAIM, CLAIM, CLAIM, CLAIM]
                                                                   , undefined,
                                                                   {'role': 'reserver',
                                                                    'assigned_room': spawn.pos.roomName
                                                                       , 'flag_name': flag})
                                if type(spawning_creep) == str:
                                    continue
                                else:
                                    print('ERROR? reservers spawning_creep:', spawning_creep)
                                    continue

            elif spawn.spawning:
                # showing process of the spawning creep by %
                spawning_creep = Game.creeps[spawn.spawning.name]
                spawn.room.visual.text(
                    '🛠 ' + spawning_creep.memory.role + ' '
                    + str(int(
                        ((
                             spawn.spawning.needTime - spawn.spawning.remainingTime) / spawn.spawning.needTime) * 100)) + '%',
                    spawn.pos.x + 1,
                    spawn.pos.y,
                    {'align': 'left', 'opacity': 0.8}
                )
            else:
                # 1/3 chance healing
                randint = random.randint(1, 3)

                if randint != 1:
                    continue
                # 이 곳에 필요한거: spawn 레벨보다 같거나 높은 애들 지나갈 때 TTL이 오백 이하면 회복시켜준다.
                # room controller lvl ± 2 에 부합한 경우에만 수리를 실시한다.
                level = Game.spawns[nesto.name].room.controller.level

                for creep in creeps:
                    # 방 안에 있는 크립 중에 회복대상자들.
                    if 100 < creep.ticksToLive < 500 and creep.room.name == spawn.room.name \
                            and (creep.memory.level >= level - 3 and not creep.memory.level <= 0):
                        if spawn.pos.isNearTo(creep):
                            # print(creep.ticksToLive)
                            result = spawn.renewCreep(creep)
                            break

        # loop for ALL STRUCTURES
        if Memory.rooms:
            for room_name in Object.keys(Memory.rooms):
                # 방 이름이 똑같아야만 돈다.
                if room_name == chambra_nomo:
                    # get json list by room name
                    structure_list = Memory.rooms[room_name]
                    # divide them by structure names
                    for building_name in Object.keys(structure_list):

                        if building_name == STRUCTURE_TOWER:
                            for tower in structure_list[building_name]:
                                # sometimes these could die you know....
                                if Game.getObjectById(tower):
                                    building_action.run_tower(Game.getObjectById(tower), all_structures,
                                                              creeps, hostile_creeps, repairs, square)
                        elif building_name == STRUCTURE_LINK:
                            for link in structure_list[building_name]:
                                if Game.getObjectById(link):
                                    building_action.run_links(Game.getObjectById(link), my_structures)
                    break

    if Game.cpu.bucket < 2000 and Game.cpu.limit < 20:
        print('passed creeps:', passing_creep_counter)

    # 스트럭쳐 목록 초기화 위한 작업. 마지막에 다 지워야 운용에 차질이 없음.
    if Game.time % structure_renew_count == 0:
        # del Memory.towers
        # del Memory.links
        del Memory.buildings
        del Memory.rooms

    # cpu counter
    if not Memory.ticks:
        Memory.ticks = 15
    if not Memory.cpu_usage:
        Memory.cpu_usage = [0]
    while len(Memory.cpu_usage) >= Memory.ticks:
        Memory.cpu_usage.splice(0, 1)
    Memory.cpu_usage.push(round(Game.cpu.getUsed(), 2))

    # there's a reason I made it this way...
    if not Memory.tick_check and Memory.tick_check != False:
        Memory.tick_check = False

    interval = 50

    if Game.time % interval == 0 or Memory.tick_check:
        cpu_total = 0
        for cpu in Memory.cpu_usage:
            cpu_total += cpu
        cpu_average = cpu_total / len(Memory.cpu_usage)
        print("average cpu usage in the last {} ticks: {}".format(len(Memory.cpu_usage), cpu_average))
        Memory.tick_check = False


module.exports.loop = main
