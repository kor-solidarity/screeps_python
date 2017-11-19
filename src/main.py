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

    if not Memory.updateAlliance and Memory.updateAlliance != False:
        Memory.updateAlliance = True

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

    if not Memory.debug and not Memory.debug == False:
        Memory.debug = True
    try:
        if Memory.debug:
            print(JSON.stringify(Memory.rooms))

            # 각 방 이름.
            for rooms in Object.keys(Memory.rooms):
                structure_list = Memory.rooms[rooms]
                # structure_list에는 각각 타입별 머시기가 들어있다.

            # for items in Memory.rooms:
            #     print(JSON.stringify(items))

            Memory.debug = False
    except:
        print('error in Memory.debug part')

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
                soldier.run_remote_defender(creep, creeps, hostile_creeps)
                continue
            elif creep.memory.role == 'harvester':
                harvester.run_harvester(creep, all_structures, constructions, creeps, dropped_all)
                """
                Runs a creep as a generic harvester.
                :param creep: The creep to run
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
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
                upgrader.run_upgrader(creep, all_structures)

            elif creep.memory.role == 'miner':
                harvester.run_miner(creep, all_structures, minerals)

            elif creep.memory.role == 'hauler':
                hauler.run_hauler(creep, all_structures, constructions,
                                  creeps, dropped_all, repairs)
                """
                :param creep:
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                :return:
                """
            elif creep.memory.role == 'carrier':
                carrier.run_carrier(creep, creeps, all_structures, constructions, dropped_all, repairs)
                """
                technically same with hauler, but more concentrated in carrying itself.
                    and it's for remote mining ONLY.
                :param creep: Game.creep
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                :return:
                """
            elif creep.memory.role == 'scout':
                scout.run_scout(creep)
            elif creep.memory.role == 'reserver':
                upgrader.run_reserver(creep)

        # 멀티자원방 관련 스크립트
        if Game.time % structure_renew_count == 1 or not Memory.rooms:
            for name in Object.keys(Game.flags):
                try:
                    # 깃발 위치가 현 방과 이름이 같은가?
                    if Game.flags[name].room.name == chambra_nomo:
                        # 깃발 하나만 꽂으면 끝남.
                        break
                except:
                    pass

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

            # this part is made to save memory and separate functional structures out of spawn loop.
            if Game.time % structure_renew_count == 1 or not Memory.rooms:
                # TESTING PART
                print('check')
                # obj.property === obj['property']

                push_bool = True

                new_json = '{}'
                new_json = JSON.parse(new_json)

                new_towers = {STRUCTURE_TOWER: []}

                new_links = {STRUCTURE_LINK: []}
                new_labs = {STRUCTURE_LAB: []}

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
                hostile_around = False
                # 적이 주변에 있으면 생산 안한다. 추후 수정해야함.

                if hostile_creeps:
                    for enemy in hostile_creeps:
                        if spawn.pos.inRangeTo(enemy, 2):
                            hostile_around = True
                            break
                if hostile_around:
                    continue

                # ALL flags.
                flags = Game.flags
                flag_name = []

                # check all flags with same name with the spawn.
                for name in Object.keys(flags):

                    # 방이름 + -rm + 아무글자(없어도됨)
                    regex = spawn.room.name + r'-rm.*'
                    if re.match(regex, name, re.IGNORECASE):
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

                sources = nesto.room.find(FIND_SOURCES)

                for structure in all_structures:
                    if structure.structureType == STRUCTURE_CONTAINER or structure.structureType == STRUCTURE_LINK:
                        for source in sources:
                            if source.pos.inRangeTo(structure, 3):
                                harvest_carry_targets.push(structure.id)
                                break
                    if len(harvest_carry_targets) >= len(sources):
                        break

                if len(harvest_carry_targets) < len(sources):
                    # and not spawn.pos.inRangeTo(2, hostile_creeps[0]):
                    harvesters_bool = bool(len(creep_harvesters) < len(sources) * 2)
                # if numbers of creep_harvesters are less than number of sources in the spawn's room.
                else:
                    # to count the overall harvesting power. 3k or more == 2, else == 1
                    harvester_points = 0

                    for harvester_creep in creep_harvesters:
                        # size scale:
                        # 1 - small sized: 2 in each. regardless of actual capacity. for lvl 3 or less
                        # 2 - real standards. suitable for 3k. 4500 not implmented yet.
                        harvester_points += harvester_creep.memory.size

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
                             'size': 2})
                    else:
                        # perfect for 3000 cap
                        regular_spawn = spawn.createCreep(
                            [WORK, WORK, WORK, WORK, WORK, WORK,
                             CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE,
                             MOVE, MOVE]
                            , undefined,
                            {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                             'size': 2})
                    # print('what happened:', regular_spawn)
                    if regular_spawn == -6:
                        # one for 1500 cap == need 2
                        if spawn.createCreep(
                                [WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE],
                                undefined,
                                {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                                 'size': 1}) == -6:
                            spawn.createCreep([MOVE, WORK, WORK, CARRY], undefined,
                                              {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                                               'size': 1})  # final barrier
                    continue

                plus = 0
                for harvest_container in harvest_carry_targets:
                    # Ĉar uzi getObjectById k.t.p estas tro longa.
                    harvest_target = Game.getObjectById(harvest_container)
                    # 컨테이너.
                    if harvest_target.structureType == STRUCTURE_CONTAINER:
                        if _.sum(harvest_target.store) >= harvest_target.storeCapacity * .9:
                            plus += 1
                        elif _.sum(harvest_target.store) <= harvest_target.storeCapacity * .4:
                            plus -= 1
                    # 링크.
                    else:
                        if harvest_target.energy >= harvest_target.energyCapacity * .9:
                            plus += 1
                        elif harvest_target.energy <= harvest_target.energyCapacity * .4:
                            plus -= 1

                # 건물이 아예 없을 시
                if len(harvest_carry_targets) == 0:
                    plus = -len(sources)

                hauler_capacity = len(sources) + 1 + plus
                # minimum number of haulers in the room is 1, max 4
                if hauler_capacity <= 0:
                    # if len(harvest_carry_targets) == 0:
                    #     hauler_capacity = 1
                    # else:
                    hauler_capacity = 1
                elif hauler_capacity > 4:
                    hauler_capacity = 4

                if len(creep_haulers) < hauler_capacity:
                    # first hauler is always 250 sized. - 'balance' purpose(idk just made it up)
                    if spawn.room.energyAvailable >= spawn.room.energyCapacityAvailable * .85 \
                            and len(creep_haulers) != 0:
                        spawning_creep = spawn.createCreep(
                            [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                             CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY],
                            undefined, {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                        'level': 8})
                    else:
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
                    if Game.time % 6491 < 11:
                        plus = 1
                    if spawn.room.controller.ticksToDowngrade < 10000:
                        plus += 1

                if spawn.room.controller.level == 8:
                    proper_level = 0
                # start making upgraders after there's a storage
                elif spawn.room.controller.level > 2 and spawn.room.storage:

                    if spawn.room.controller.level < 5:
                        expected_reserve = 2500
                    else:
                        expected_reserve = 7000

                    # if there's no storage or storage has less than 6k energy
                    if spawn.room.storage.store[RESOURCE_ENERGY] < expected_reserve or not spawn.room.storage:
                        proper_level = 1
                    # more than 30k
                    elif spawn.room.storage.store[RESOURCE_ENERGY] >= expected_reserve:
                        proper_level = 1
                        # extra upgrader every expected_reserve
                        proper_level += int(spawn.room.storage.store[RESOURCE_ENERGY] / expected_reserve)
                        # max upgraders: 12
                        if proper_level > 12:
                            proper_level = 12

                    else:
                        proper_level = 1
                elif spawn.room.energyCapacityAvailable <= 1000:
                    # 어차피 여기올쯤이면 소형애들만 생성됨.
                    proper_level = 4
                else:
                    proper_level = 0

                if len(creep_upgraders) < proper_level + plus \
                        and not (Game.cpu.bucket < 2000):
                    if spawn.room.controller.level != 8:
                        big = spawn.createCreep(
                            [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK,
                             WORK, WORK,
                             WORK,
                             WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY], undefined,
                            {'role': 'upgrader', 'assigned_room': spawn.pos.roomName, 'level': 5})
                    else:
                        big = -6
                    if big == -6:
                        small = spawn.createCreep(
                            [WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                             CARRY, CARRY, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE], undefined,
                            {'role': 'upgrader', 'assigned_room': spawn.pos.roomName, 'level': 3})
                        if small == -6:
                            little = spawn.createCreep([WORK, WORK, WORK, CARRY, MOVE, MOVE], undefined,
                                                       {'role': 'upgrader', 'assigned_room': spawn.pos.roomName})
                        if little == -6:
                            spawn.createCreep([WORK, WORK, CARRY, CARRY, MOVE, MOVE], undefined,
                                              {'role': 'upgrader', 'assigned_room': spawn.pos.roomName})
                    continue

                # REMOTE---------------------------------------------------------------------------
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
                            remote_carriers = _.filter(creeps, lambda c: c.memory.role == 'carrier'
                                                                         and c.memory.flag_name == flag
                                                                         and c.spawning or c.ticksToLive > 100)
                                                                              # or not
                                                                              # (c.memory.frontier and c.memory.pickup
                                                                              #     and c.ticksToLive < 1350)))

                            # exclude creeps with less than 100 life ticks so the new guy can be replaced right away
                            remote_harvesters = _.filter(creeps, lambda c: c.memory.role == 'harvester'
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
                                # 임시조치. 한번 그냥 적들어오면 아무것도 안해보자.
                                continue

                                # second one is the BIG GUY. made in case invader's too strong.
                                # 임시로 0으로 놨음. 구조 자체를 뜯어고쳐야함.
                                if len(remote_troops) == 0:
                                    spawn_res = spawn.createCreep(
                                        [TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                         MOVE, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK,
                                         ATTACK, RANGED_ATTACK, HEAL],
                                        undefined, {'role': 'soldier', 'assigned_room': spawn.pos.roomName
                                            , 'flag_name': flag})
                                    continue
                                spawn_res = spawn.createCreep(
                                    [TOUGH, TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, ATTACK, RANGED_ATTACK,
                                     HEAL],
                                    undefined, {'role': 'soldier', 'assigned_room': spawn.pos.roomName
                                        , 'flag_name': flag})
                                # if spawn_res == 0:
                                continue

                            # 방 안에 적이 있으면 아예 생산을 하지 않는다! 정찰대와 방위병 빼고.
                            if len(hostiles) > 0:
                                continue

                            # resources in flag's room
                            # 멀티에 소스가 여럿일 경우 둘을 스폰할 필요가 있다.
                            flag_energy_sources = Game.flags[flag].room.find(FIND_SOURCES)
                            # FIND_SOURCES가 필요없는 이유: 어차피 그걸 보지 않고 건설된 컨테이너 수로 따질거기 때문.
                            flag_structures = Game.flags[flag].room.find(FIND_STRUCTURES)
                            flag_containers = _.filter(flag_structures,
                                                       lambda s: s.structureType == STRUCTURE_CONTAINER)

                            # # 운송크립 확인을 위한 작업.
                            # actual_avail_carriers = 0
                            # carrier_pickup = None
                            # # 현재 하나짜리인지라 다중이로 바꿔야함.
                            # for c in remote_carriers:
                            #     # 스폰중인가? 생명이 100이상 남았는가? 그러면 숫자 추가한다.
                            #     if c.spawning or c.ticksToLive > 100:
                            #         actual_avail_carriers += 1
                            #         # 프론티어 불이 존재하고 픽업이 존재할 시 건설작업 끝난거니 셈에서 제외하고 픽업값 넣는다.
                            #         if c.memory.frontier and c.memory.pickup and c.ticksToLive < 1350:
                            #             actual_avail_carriers -= 1
                            #             carrier_pickup = c.memory.pickup
                            #
                            #     # 아니면 새로 생성해야하니 픽업값 넣는다.
                            #     else:
                            #         carrier_pickup = c.memory.pickup

                            # 캐리어가 소스 수만큼 있는가?
                            if len(flag_energy_sources) > len(remote_carriers):
                                print('flag carrier?')
                                # 픽업으로 배정하는 것이 아니라 자원으로 배정한다.
                                if len(remote_carriers) == 0:
                                    carrier_source = flag_energy_sources[0].id
                                else:
                                    for s in flag_energy_sources:

                                        for c in remote_carriers:
                                            if s.id == c.memory.source_num:
                                                continue
                                            else:
                                                carrier_source = s.id
                                                break

                                carrier_pickup = None
                                source_num = None

                                # carrier_source에서 주변에 컨테이너가 있는지 확인한다.
                                for s in carrier_source:

                                    # 에너지소스에 담당 컨테이너가 존재하는가?
                                    containter_exist = False
                                    # 컨테이너에 담당 캐리어가 존재하는가?
                                    carrier_exist = False

                                    for sc in flag_containers:
                                        # 범위안에 컨테이너가 존재하는가?
                                        if s.pos.inRangeTo(sc, 3):
                                            containter_exist = True
                                            # 그 컨테이너에 담당된 캐리어가 존재하는가? 존재한다면 그게 배정돼선 안됨.
                                            for c in remote_carriers:
                                                if c.memory.pickup == sc.id:
                                                    carrier_exist = True
                                                    break

                                        if containter_exist:
                                            # 컨테이너가 존재하고 담당 캐리어가 존재할 경우 배정할 필요가 없다.
                                            # 캐리어가 존재하지 않을 경우 배정한다.
                                            if not carrier_exist:
                                                carrier_pickup = sc.id
                                                source_num = s.id
                                                break

                                    # 소스번호가 배정됐다는 것은 설정이 끝났다는 소리.
                                    if source_num:
                                        break
                                    # 에너지 근처 컨테이너가 존재하지 않을 경우는?
                                    elif not containter_exist:



                                # se tie ne estas carrier_pickup, unue, vi povas trovi harvesters.
                                if not Game.getObjectById(carrier_pickup):
                                    # print('remote_harvesters', bool(remote_harvesters))
                                    if bool(remote_harvesters):
                                        # kaj asignu el havester-a container
                                        carrier_pickup = remote_harvesters[0].memory.container
                                # 건물도 없고 캐리어도 없다 - 건설을 해야함.
                                if len(flag_containers) == 0 and len(remote_carriers) == 0:
                                    carrier_pickup = None
                                # 그게 아닌 경우는 컨테이너 번호를 찾아 매긴다.
                                else:
                                    # 컨테이너 하나씩 돌려서 캐리어 확인.
                                    for ujo in flag_containers:
                                        # 컨테이너에 배정된 크립이 없는가?
                                        no_designation = True

                                        for c in remote_carriers:
                                            # 만일 캐리어의 carrier_pickup과 겹치는 컨테이너 아이디가 있으면
                                            #  현재 존재하는거니 넘기는거. 한마디로 그 컨테이너 배정할필요가 없다.
                                            if c.memory.pickup == ujo.id:
                                                no_designation = False
                                                break
                                        # 배정이 안되있을 경우 - 얘 배정해야함.
                                        if no_designation:
                                            carrier_pickup = ujo.id
                                            break

                                # 대충 해야하는일: 캐리어의 픽업위치에서 본진거리 확인. 그 후 거리만큼 추가.
                                if Game.getObjectById(carrier_pickup):
                                    path = Game.getObjectById(carrier_pickup).room.findPath(
                                        Game.getObjectById(carrier_pickup).pos, spawn.pos, {'ignoreCreeps': True})
                                    distance = len(path)

                                    if _.sum(Game.getObjectById(carrier_pickup).store) \
                                            >= Game.getObjectById(carrier_pickup).storeCapacity * .8:
                                        work_chance = 1
                                    else:
                                        work_chance = random.randint(0, 1)
                                    # 굳이 따로 둔 이유: 캐리 둘에 무브 하나.
                                    carry_body_odd = [MOVE, CARRY, CARRY, CARRY]
                                    carry_body_even = [MOVE, MOVE, CARRY, CARRY, CARRY]
                                    work_body = [MOVE, WORK, WORK, MOVE, WORK, WORK]
                                    body = []

                                    work_check = 0
                                    for i in range(int(distance / 6)):
                                        # 이거부터 들어가야함
                                        if i % 2 == 0:
                                            for bodypart in carry_body_even:
                                                body.push(bodypart)
                                        else:
                                            for bodypart in carry_body_odd:
                                                body.push(bodypart)
                                        if work_chance == 0:
                                            work_check += 1
                                            if work_check == 1 or work_check == 4:
                                                for bodypart in work_body:
                                                    body.push(bodypart)
                                    # 거리 나머지값 반영.
                                    if distance % 6 > 2:
                                        body.push(MOVE)
                                        body.push(CARRY)
                                    if _.sum(Game.getObjectById(carrier_pickup).store) \
                                            >= Game.getObjectById(carrier_pickup).storeCapacity * .8:
                                        print('extra')
                                        if distance % 6 <= 2:
                                            body.push(MOVE)
                                        body.push(CARRY)
                                    print('body', body)

                                    if work_check > 0:
                                        working = True
                                    else:
                                        working = False

                                    spawning = spawn.createCreep(body, undefined,
                                                                 {'role': 'carrier',
                                                                  'assigned_room': spawn.pos.roomName,
                                                                  'flag_name': flag, 'pickup': carrier_pickup
                                                                     , 'work': working})
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
                                                 'flag_name': flag, 'pickup': carrier_pickup, 'work': working})
                                        else:
                                            spawn.createCreep(
                                                [WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE,
                                                 MOVE, MOVE, MOVE, MOVE],
                                                undefined,
                                                {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                                 'flag_name': flag, 'pickup': carrier_pickup, 'frontier': True
                                                    , 'work': True})
                                        continue
                                # 픽업이 존재하지 않는다는건 현재 해당 건물이 없다는 뜻이므로 새로 지어야 함.
                                else:
                                    spawning = spawn.createCreep(
                                        [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                         WORK, WORK, WORK, CARRY, CARRY],
                                        undefined,
                                        {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                         'flag_name': flag, 'frontier': True, 'work': True})
                                    if spawning == ERR_NOT_ENOUGH_RESOURCES:
                                        spawn.createCreep(
                                            [WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE,
                                             MOVE, MOVE, MOVE, MOVE],
                                            undefined,
                                            {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
                                             'flag_name': flag, 'frontier': True, 'work': True})
                                    continue

                            if len(flag_containers) > len(remote_harvesters):
                                # perfect for 3000 cap
                                regular_spawn = spawn.createCreep(
                                    [WORK, WORK, WORK, WORK, WORK, WORK,
                                     CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE,
                                     MOVE, MOVE]
                                    , undefined,
                                    {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                                     'size': 2, 'flag_name': flag})
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
                                if spawning_creep == ERR_NOT_ENOUGH_RESOURCES:
                                    spawning_creep = spawn.createCreep([MOVE, MOVE, CLAIM, CLAIM]
                                        , undefined,
                                        {'role': 'reserver', 'assigned_room': spawn.pos.roomName
                                            , 'flag_name': flag})

                                continue

            elif spawn.spawning:
                # showing process of the spawning creep by %
                spawning_creep = Game.creeps[spawn.spawning.name]
                spawn.room.visual.text(
                    '🛠 ' + spawning_creep.memory.role + ' '
                    + str(int(
                        ((spawn.spawning.needTime - spawn.spawning.remainingTime)
                         / spawn.spawning.needTime) * 100)) + '%',
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
        # 멀티방 건물정보 저장. 현재는 아무기능 안한다.
        if Game.time % structure_renew_count == 1:
            # 정규식으로 확인. -rm 으로 끝나는 깃발은 다 멀티자원방이기 때문에 그걸 확인한다.
            regex_flag = r'.+-rm'
            for flag in Object.keys(Game.flags):
                if re.match(regex_flag, flag, re.IGNORECASE):
                    pass

        # loop for ALL STRUCTURES
        if Memory.rooms:
            for room_name in Object.keys(Memory.rooms):
                # 방 이름이 똑같아야만 돈다.
                if room_name == chambra_nomo:
                    # get json list by room name
                    structure_list = Memory.rooms[room_name]
                    # 현 방의 레벨
                    current_lvl = Game.rooms[room_name].controller.level

                    # divide them by structure names
                    for building_name in Object.keys(structure_list):
                        if building_name == 'remote':
                            # 재건 관련 지역
                            if Game.time % 47 == 0:
                                pass
                        elif building_name == STRUCTURE_TOWER:
                            # 수리작업을 할때 벽·방어막 체력 만 이하가 있으면 그걸 최우선으로 고친다.
                            # 적이 있을 시 수리 자체를 안하니 있으면 아예 무시.
                            if len(hostile_creeps) == 0 and current_lvl > 4:
                                for repair_wall_rampart in repairs:
                                    if repair_wall_rampart.structureType == STRUCTURE_WALL \
                                            or repair_wall_rampart.structureType == STRUCTURE_RAMPART:
                                        if repair_wall_rampart.hits < current_lvl ** square - 3:
                                            repairs = [repair_wall_rampart]
                                            break

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
        print("{} total creeps, average cpu usage in the last {} ticks: {}, and current CPU bucket: {}"
              .format(len(Game.creeps), len(Memory.cpu_usage), cpu_average, Game.cpu.bucket))
        Memory.tick_check = False


module.exports.loop = main
