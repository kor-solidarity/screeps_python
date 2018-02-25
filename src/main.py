import harvester
import hauler
import upgrader
import structure as building_action
import scout
import carrier
import soldier
import structure_spawn
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

    cpu_bucket_emergency = 1000
    cpu_bucket_emergency_spawn_start = 2500
    if not Memory.debug and not Memory.debug == False:
        Memory.debug = False
    interval = 50
    if Memory.debug:
        print()
        print('----- NEW TICK -----')

    # cpu counter
    if not Memory.ticks:
        Memory.ticks = 15
    if not Memory.cpu_usage:
        Memory.cpu_usage = []
        # 아래는 나중에 추가로 넣을 수도 있는 사항. 아직은 넣지 않는다.
        # Memory.cpu_usage.total = []
        # Memory.cpu_usage.creep = []
        # Memory.cpu_usage.buildings = []

    if not Memory.updateAlliance and Memory.updateAlliance != False:
        Memory.updateAlliance = True

    try:
        # adding alliance. um.... this code use 0.05 CPU o.O
        if Game.time % 997 == 0 and Memory.updateAlliance:
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
        waste = Game.cpu.getUsed()
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
        if Memory.debug:
            print('time wasted for fun: {} cpu'.format(round(Game.cpu.getUsed() - waste, 2)))
    except:
        pass

    # NULLIFIED
    # if not Memory.debug and not Memory.debug == False:
    #     Memory.debug = True
    # try:
    #     if Memory.debug:
    #         print(JSON.stringify(Memory.rooms))
    #
    #         # 각 방 이름. 방 통째로 삭제하는거 때문에 넣음.
    #         for rooms in Object.keys(Memory.rooms):
    #             structure_list = Memory.rooms[rooms]
    #
    #         Memory.debug = False
    # except:
    #     print('error in Memory.debug part')

    if Memory.dropped_sources:
        del Memory.dropped_sources

    # to count the number of creeps passed.
    passing_creep_counter = 0

    # 스트럭쳐 목록 초기화 위한 숫자
    structure_renew_count = 200
    # JSON string to be put into memory
    for_json = ''

    if Memory.debug:
        # 0.05정도
        print('base setup time: {} cpu'.format(round(Game.cpu.getUsed(), 2)))

    # cpu limit warning. only works when losing cpu and you have a 10 cpu limit
    if Game.cpu.bucket < cpu_bucket_emergency and Game.cpu.limit < 20:
        print('WARNING: Game.cpu.bucket == {}'.format(Game.cpu.bucket))

    total_creep_cpu = 0
    total_creep_cpu_num = 0

    # total spawns ran
    spawn_run_num = 0

    # 때에따라 한번씩 빈주문 삭제
    if Game.time % 80000 == 0:
        print('attempting to clear market records...')
        miscellaneous.clear_orders()

    # run everything according to each rooms.
    for chambra_nomo in Object.keys(Game.rooms):
        chambro_cpu = Game.cpu.getUsed()
        chambro = Game.rooms[chambra_nomo]

        # ALL .find() functions are done in here. THERE SHOULD BE NONE INSIDE CREEP FUNCTIONS!
        # filters are added in between to lower cpu costs.
        all_structures = chambro.find(FIND_STRUCTURES)

        room_creeps = chambro.find(FIND_MY_CREEPS)

        malsana_amikoj = _.filter(room_creeps, lambda c: c.hits < c.hitsMax)

        constructions = chambro.find(FIND_CONSTRUCTION_SITES)
        dropped_all = chambro.find(FIND_DROPPED_RESOURCES)

        hostile_creeps = chambro.find(FIND_HOSTILE_CREEPS)
        nukes = chambro.find(FIND_NUKES)

        # to filter out the allies.
        if len(hostile_creeps) > 0:
            hostile_creeps = miscellaneous.filter_allies(hostile_creeps)

        if chambro.controller:
            # 단계별 제곱근값
            square = chambro.controller.level
            if square < 4:
                square = 4
            if bool(nukes) and square > 5:
                repair_pts = 5200000
            else:
                repair_pts = square ** square
        else:
            square = 4
            repair_pts = square ** square

        # 방 안의 터미널 내 에너지 최소값.
        if chambro.controller:
            if chambro.terminal and chambro.controller.level < 8:
                terminal_capacity = 1000
            else:
                terminal_capacity = 10000

        if bool(nukes):
            # list of ALL repairs in the room.
            repairs = all_structures.filter(lambda s: (((s.structureType == STRUCTURE_ROAD
                                                         or s.structureType == STRUCTURE_TOWER
                                                         or s.structureType == STRUCTURE_EXTENSION
                                                         or s.structureType == STRUCTURE_LINK
                                                         or s.structureType == STRUCTURE_LAB
                                                         or s.structureType == STRUCTURE_CONTAINER
                                                         or s.structureType == STRUCTURE_STORAGE)
                                                        and s.hits < s.hitsMax)
                                                       or ((s.structureType == STRUCTURE_WALL
                                                            and s.hits < int(repair_pts))
                                                           or (s.structureType == STRUCTURE_RAMPART
                                                               and ((s.hits < int(repair_pts))
                                                                    or (s.pos == nukes[0].pos
                                                                        and (s.hits < int(repair_pts * 2))))
                                                               and chambro.controller.level > 1))))

        else:
            # list of ALL repairs in the room.
            repairs = all_structures.filter(lambda s: (((s.structureType == STRUCTURE_ROAD
                                                         or s.structureType == STRUCTURE_TOWER
                                                         or s.structureType == STRUCTURE_EXTENSION
                                                         or s.structureType == STRUCTURE_LINK
                                                         or s.structureType == STRUCTURE_LAB
                                                         or s.structureType == STRUCTURE_CONTAINER
                                                         or s.structureType == STRUCTURE_STORAGE)
                                                        and s.hits < s.hitsMax)
                                                       or ((s.structureType == STRUCTURE_WALL
                                                            and s.hits < int(repair_pts))
                                                           or (s.structureType == STRUCTURE_RAMPART
                                                               and (s.hits < int(repair_pts)
                                                                    and chambro.controller.level > 1)))))

        if not repairs or len(repairs) == 0:
            repairs = []

        my_structures = chambro.find(FIND_MY_STRUCTURES)

        # ext_cpu = Game.cpu.getUsed()
        # extractor = None
        extractor = _.filter(my_structures, lambda s: s.structureType == STRUCTURE_EXTRACTOR)
        # print('extractor:', extractor)
        # if my_structures:
        #     for structure in my_structures:
        #         # print('structure.structureType: {}'.format(structure.structureType))
        #         if structure.structureType == STRUCTURE_EXTRACTOR:
        #             extractor = structure
        #             # print('ext?', extractor)
        #             break

        # print('ext cpu: {}'.format(round(Game.cpu.getUsed() - ext_cpu, 3)))

        # print('room {} extr? {}'.format(chambra_nomo, extractor))

        # my_structures = _.filter(all_structures, lambda s: s.my == True)

        spawns = chambro.find(FIND_MY_SPAWNS)

        # print("preparation time for room {}: {} cpu".format(chambro.name, round(Game.cpu.getUsed() - chambro_cpu, 2)))

        # Run each creeps
        for chambro_creep in room_creeps:
            creep_cpu = Game.cpu.getUsed()

            creep = Game.creeps[chambro_creep.name]
            # 만일 생산중이면 그냥 통과
            if creep.spawning:
                if not creep.memory.age and creep.memory.age != 0:
                    creep.memory.age = 0
                # print("{} spawning speed : {} cpu".format(creep.name, round(Game.cpu.getUsed() - creep_cpu, 3)))
                continue

            # but if a soldier/harvester.... nope. they're must-be-run creeps
            if creep.memory.role == 'soldier':
                soldier.run_remote_defender(all_structures, creep, room_creeps, hostile_creeps)

            elif creep.memory.role == 'harvester':
                harvester.run_harvester(creep, all_structures, constructions, room_creeps, dropped_all)
                """
                Runs a creep as a generic harvester.
                :param creep: The creep to run
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                """

            elif creep.memory.role == 'hauler':
                hauler.run_hauler(creep, all_structures, constructions,
                                  room_creeps, dropped_all, repairs, terminal_capacity)
                """
                :param creep:
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                :return:
                """
            elif creep.memory.role == 'carrier':
                carrier.run_carrier(creep, room_creeps, all_structures, constructions, dropped_all, repairs)
                """
                technically same with hauler, but more concentrated in carrying itself.
                    and it's for remote mining ONLY.
                :param creep: Game.creep
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                :return:
                """

            # run at (rate * 10)% rate at a time if bucket is less than 2k and ur on 10 cpu limit.
            if Game.cpu.bucket < cpu_bucket_emergency and not (
                    creep.memory.role == 'soldier' or creep.memory.role == 'harvester'):
                rate = 2
                if random.randint(0, rate) == 0:
                    # print('passed creep:', creep.name)
                    passing_creep_counter += 1
                    continue

            if creep.memory.role == 'upgrader':
                upgrader.run_upgrader(creep, room_creeps, all_structures)

            elif creep.memory.role == 'miner':
                harvester.run_miner(creep, all_structures)
            elif creep.memory.role == 'scout':
                scout.run_scout(creep)
            elif creep.memory.role == 'reserver':
                upgrader.run_reserver(creep)
            elif creep.memory.role == 'demolition':
                soldier.demolition(creep, all_structures)

            # print('{} apswning: {}'.format(creep.name, creep.spawning))
            creep_cpu_end = Game.cpu.getUsed() - creep_cpu
            # 총값확인용도
            total_creep_cpu_num += 1
            total_creep_cpu += creep_cpu_end
            # if Memory.debug:
            #     print('{} the {} of room {} used {} cpu'
            #           .format(creep.name, creep.memory.role, creep.room.name, round(creep_cpu_end, 2)))

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

        # loop for ALL STRUCTURES
        if Memory.rooms:
            room_cpu = Game.cpu.getUsed()
            room_cpu_num = 0
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
                            continue
                        elif building_name == STRUCTURE_TOWER:
                            # 수리작업을 할때 벽·방어막 체력 만 이하가 있으면 그걸 최우선으로 고친다.
                            # 적이 있을 시 수리 자체를 안하니 있으면 아예 무시.
                            if len(hostile_creeps) == 0 and current_lvl > 4 and Game.cpu.bucket > cpu_bucket_emergency:
                                for repair_obj in repairs:
                                    if (repair_obj.structureType == STRUCTURE_WALL
                                        or repair_obj.structureType == STRUCTURE_RAMPART) \
                                            and repair_obj.hits < 300:
                                        repairs = [repair_obj]
                                        break
                                    elif (repair_obj.structureType == STRUCTURE_CONTAINER
                                          or repair_obj.structureType == STRUCTURE_ROAD) \
                                            and repair_obj.hits < repair_obj.hitsMax * .05:
                                        repairs = [repair_obj]
                                        break

                            for tower in structure_list[building_name]:
                                # sometimes these could die you know....
                                the_tower = Game.getObjectById(tower)
                                if the_tower:
                                    room_cpu_num += 1
                                    building_action.run_tower(the_tower, hostile_creeps, repairs, malsana_amikoj)
                        elif building_name == STRUCTURE_LINK:
                            for link in structure_list[building_name]:
                                if Game.getObjectById(link):
                                    room_cpu_num += 1
                                    building_action.run_links(Game.getObjectById(link), my_structures)
                    break

            if room_cpu_num > 0 and (Memory.debug or Game.time % interval == 0 or Memory.tick_check):
                end = Game.cpu.getUsed()
                # print("end {} start {}".format(round(end, 2), round(room_cpu, 2)))
                room_cpu_avg = (end - room_cpu) / room_cpu_num
                print("{} structures ran in {} total with avg. {} cpu, tot. {} cpu"
                      .format(room_cpu_num, room_name, round(room_cpu_avg, 2), round(end - room_cpu, 2)))

        # 스폰 여럿이어서 생길 중복방지.
        room_names = []

        divider = -1
        counter = 10
        room_spawn_cpu = Game.cpu.getUsed()
        # Run each spawn every "counter" turns.
        for nesto in spawns:

            spawn_cpu = Game.cpu.getUsed()
            # depict exactly which spawn it is.
            spawn = Game.spawns[nesto.name]

            divider += 1
            if divider > counter:
                divider -= counter

            # this part is made to save memory and separate functional structures out of spawn loop.
            if Game.time % structure_renew_count == 1 or not Memory.rooms:
                # TESTING PART
                # print('check')
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
                        # print('check')
                        push_bool = False
                        break

                if push_bool:
                    # find and add towers
                    # 1. todo 새 방식 제안: 메모리에 있는 방을 한번 돌려서 없으면 삭제.
                    # 2. 동시에 방 안에 있는 스트럭쳐들 돌려서 메모리에 있는지 확인.
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

            if Memory.debug or Game.time % interval == 0 or Memory.tick_check:
                print('방 {} 루프에서 스폰 {} 준비시간 : {} cpu'.format(nesto.room.name, nesto.name
                                                             , round(Game.cpu.getUsed() - spawn_cpu, 2)))

            structure_spawn.run_spawn(nesto, all_structures, room_creeps, hostile_creeps, divider, counter
                                      , cpu_bucket_emergency, cpu_bucket_emergency_spawn_start, extractor
                                      , terminal_capacity, chambro, interval)

            spawn_cpu_end = Game.cpu.getUsed() - spawn_cpu
            if Memory.debug or Game.time % interval == 0 or Memory.tick_check:
                print('spawn {} used {} cpu'.format(spawn.name, round(spawn_cpu_end, 2)))

    if Game.cpu.bucket < cpu_bucket_emergency:
        print('passed creeps:', passing_creep_counter)

    if Memory.debug or Game.time % interval == 0 or Memory.tick_check:
        print("total of {} creeps run with avg. {} cpu, tot. {} cpu"
              .format(total_creep_cpu_num, round(total_creep_cpu / total_creep_cpu_num, 2), round(total_creep_cpu, 2)))

    # 스트럭쳐 목록 초기화 위한 작업. 마지막에 다 지워야 운용에 차질이 없음.
    # 추후 정리해야 하는 사안일듯.
    # NULLIFIED
    # if Game.time % structure_renew_count == 0:
    #     del Memory.rooms

    # todo 스폰을 위한 크립 캐시화.
    # adding total cpu
    # while len(Memory.cpu_usage.total) >= Memory.ticks:
    while len(Memory.cpu_usage) >= Memory.ticks:
        Memory.cpu_usage.splice(0, 1)
        # Memory.cpu_usage.total.splice(0, 1)
    Memory.cpu_usage.push(round(Game.cpu.getUsed(), 2))
    # Memory.cpu_usage.total.push(round(Game.cpu.getUsed(), 2))

    # there's a reason I made it this way...
    if not Memory.tick_check and Memory.tick_check != False:
        Memory.tick_check = False

    if Game.time % interval == 0 or Memory.tick_check:
        cpu_total = 0
        for cpu in Memory.cpu_usage:
            cpu_total += cpu
        cpu_average = cpu_total / len(Memory.cpu_usage)
        print("{} total creeps, average cpu usage in the last {} ticks: {}, and current CPU bucket: {}"
              .format(len(Game.creeps), len(Memory.cpu_usage), round(cpu_average, 2), Game.cpu.bucket))
        Memory.tick_check = False


module.exports.loop = main
