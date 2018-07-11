import role_harvester
import role_hauler
import role_upgrader
import structure as building_action
import role_scout
import role_carrier
import role_soldier
import structure_spawn
import role_collector
import random
import pathfinding
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

js_global._costs = {'base': {}, 'rooms': {}, 'creeps': {}}


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
        if Game.time % 1001 == 0 or Memory.updateAlliance:
            ally_start = Game.cpu.getUsed()
            Memory.updateAlliance = False
            shard_name = Game.shard.name
            shards = ['shard0', 'shard1', 'shard2']
            official_server = False
            for s in shards:
                if s == shard_name:
                    official_server = True
                    break

            if official_server:
                hostSegmentId = 99
                hostUsername = 'LeagueOfAutomatedNations'
                RawMemory.setActiveForeignSegment(hostUsername, hostSegmentId)
                data = JSON.parse(RawMemory.foreignSegment.data)

                my_rooms = _.filter(Game.rooms, lambda r: r.controller and r.controller.my)
                # JSON으로 된 얼라목록을 반환함.
                my_name = my_rooms[0].controller.owner.username
                # 내 얼라명
                alliance_name = None

                # 안에 얼라목록으로 도배된게 좌르르르 있음.
                for d in Object.keys(data):
                    # 하나하나 뜯어본다.
                    for nomo in data[d]:
                        # 내이름이 있으면 그걸로 처리.
                        if nomo == my_name:
                            alliance_name = d
                            break
                    if alliance_name:
                        break
                if alliance_name:
                    Memory.allianceArray = data[alliance_name]
                    print('alliance list for {} '
                          'updated using {} CPUs'.format(alliance_name, round(Game.cpu.getUsed() - ally_start, 2)))
                else:
                    Memory.allianceArray = []
                    print('alliance not updated. not alligned with any.'
                          ' {} CPU used'.format(round(Game.cpu.getUsed() - ally_start, 2)))

            else:
                Memory.allianceArray = []
                print('alliance not updated - private server. '
                      '{} CPU used'.format(round(Game.cpu.getUsed() - ally_start, 2)))

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
        # print('test')
        # print(JSON.stringify(pathfinding.Costs(chambra_nomo, None).load_matrix()))
        # print('----------------------')
        chambro_cpu = Game.cpu.getUsed()
        chambro = Game.rooms[chambra_nomo]

        # 게임 내 수동조작을 위한 초기화 설정. 단, 방이 우리꺼일 경우에만 적용.
        if chambro.controller:
            if chambro.controller.my:
                if not Memory.rooms[chambra_nomo]:
                    Memory.rooms[chambra_nomo] = {}
                if not Memory.rooms[chambra_nomo].options:
                    Memory.rooms[chambra_nomo] = {'options': {}}
                # repair level - 벽, 방어막에만 적용
                if not Memory.rooms[chambra_nomo].options.repair\
                        and not Memory.rooms[chambra_nomo].options.repair == 0:
                    Memory.rooms[chambra_nomo]['options'].repair = 5
                # 운송크립의 수. 기본수가 숫자만큼 많아진다. 물론 최대치는 무조건 4
                if not Memory.rooms[chambra_nomo].options.haulers \
                        and not Memory.rooms[chambra_nomo].options.haulers == 0:
                    Memory.rooms[chambra_nomo].options.haulers = 0
                # 핵사일로 채울거임? 채우면 1 아님 0. 안채울 경우 핵미사일 안에 에너지 빼감.
                if not Memory.rooms[chambra_nomo].options.fill_nuke \
                        and not Memory.rooms[chambra_nomo].options.fill_nuke == 0:
                    Memory.rooms[chambra_nomo].options.fill_nuke = 1
                # 연구소 에너지 채울거임?
                if not Memory.rooms[chambra_nomo].options.fill_labs \
                        and not Memory.rooms[chambra_nomo].options.fill_labs == 0:
                    Memory.rooms[chambra_nomo].options.fill_labs = 1

                # 방어막 열건가? 0 = 통과, 1 = 연다, 2 = 닫는다.
                if not Memory.rooms[chambra_nomo].options.ramparts \
                        and not Memory.rooms[chambra_nomo].options.ramparts == 0:
                    Memory.rooms[chambra_nomo].options.ramparts = 0
                # 방어막이 열려있는지 확인. 0이면 닫힌거. 위에꺼랑 같이 연동함.
                if not Memory.rooms[chambra_nomo].options.ramparts_open \
                        and not Memory.rooms[chambra_nomo].options.ramparts_open == 0:
                    Memory.rooms[chambra_nomo].options.ramparts_open = 0

        # ALL .find() functions are done in here. THERE SHOULD BE NONE INSIDE CREEP FUNCTIONS!
        # filters are added in between to lower cpu costs.
        all_structures = chambro.find(FIND_STRUCTURES)

        room_creeps = chambro.find(FIND_MY_CREEPS)

        malsana_amikoj = _.filter(room_creeps, lambda c: c.hits < c.hitsMax)

        constructions = chambro.find(FIND_CONSTRUCTION_SITES)
        dropped_all = chambro.find(FIND_DROPPED_RESOURCES)
        tomes = chambro.find(FIND_TOMBSTONES)
        if tomes:
            for t in tomes:
                if _.sum(t.store) > 0:
                    dropped_all.push(t)

        # 필터하면서 목록을 삭제하는거 같음.... 그래서 이리 초기화
        foreign_creeps = chambro.find(FIND_HOSTILE_CREEPS)
        nukes = chambro.find(FIND_NUKES)
        # init. list
        hostile_creeps = []
        allied_creeps = []
        # to filter out the allies.
        if len(foreign_creeps) > 0:
            hostile_creeps = miscellaneous.filter_enemies(foreign_creeps)
            allied_creeps = miscellaneous.filter_friends(foreign_creeps)

        if chambro.controller:
            # 수리점수는 방별 레벨제를 쓴다. 기본값은 5, 최대 60까지 가능.

            if bool(nukes):
                repair_pts = 5200000
            else:
                repair_pts = 500
        else:
            square = 4
            repair_pts = 500

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
                                                        and s.hits < s.hitsMax)))

            # 확인작업: 루프문을 돌려서 5M 단위로 끊는다. 최저는 300.
            wall_repairs = all_structures.filter(lambda s: ((s.structureType == STRUCTURE_WALL
                                                             and s.hits < 300)
                                                            or (s.structureType == STRUCTURE_RAMPART
                                                                and (s.hits < 300 and chambro.controller.level > 1))))
            # 이게 참이 아니라면 내 방이 아니기 때문에 아래 옵션필터가 없음. 그거 걸러내기.
            my_room = True
            # 방에 컨트롤러가 있는가?
            if chambro.controller:
                # 그게 내껀가?
                if not chambro.controller.my:
                    my_room = False
            else:
                my_room = False

            # 최저에 해당하는 벽이 있으면 그걸 최우선으로 잡는다.
            if len(wall_repairs) or not my_room:
                repairs.extend(wall_repairs)
            else:
                if Memory.rooms[chambra_nomo]['options'].repair > 0:
                    # 루프문을 돌려서 5M 단위로 끊는다.
                    for i in range(1, Memory.rooms[chambra_nomo]['options'].repair + 1):
                        repair_pts = i * 5000000
                        wall_repairs = all_structures.filter(lambda s: ((s.structureType == STRUCTURE_WALL
                                                                         and s.hits < int(repair_pts))
                                                                        or (s.structureType == STRUCTURE_RAMPART
                                                                            and (s.hits < int(repair_pts)
                                                                                 and chambro.controller.level > 1))))

                        # 뭔가 있으면 그대로 넣고 끝.
                        if len(wall_repairs) > 0:
                            repairs.extend(wall_repairs)
                            break
                else:
                    # 리페어 레벨이 1 아래면 당장 돈이 없단 소리므로 최소한의 값만 채운다.
                    repair_pts = 50000
                    wall_repairs = all_structures.filter(lambda s: ((s.structureType == STRUCTURE_WALL
                                                                     and s.hits < int(repair_pts))
                                                                    or (s.structureType == STRUCTURE_RAMPART
                                                                        and (s.hits < int(repair_pts)
                                                                             and chambro.controller.level > 1))))

                    # 뭔가 있으면 그대로 넣고 끝.
                    if len(wall_repairs) > 0:
                        repairs.extend(wall_repairs)
                        break

        if not repairs or len(repairs) == 0:
            repairs = []

        my_structures = chambro.find(FIND_MY_STRUCTURES)

        extractor = _.filter(my_structures, lambda s: s.structureType == STRUCTURE_EXTRACTOR)

        spawns = chambro.find(FIND_MY_SPAWNS)

        # Run each creeps
        for chambro_creep in room_creeps:
            creep_cpu = Game.cpu.getUsed()

            creep = Game.creeps[chambro_creep.name]
            # 만일 생산중이면 그냥 통과
            if creep.spawning:
                if not creep.memory.age and creep.memory.age != 0:
                    creep.memory.age = 0
                continue

            # but if a soldier/harvester.... nope. they're must-be-run creeps
            if creep.memory.role == 'soldier':
                role_soldier.run_remote_defender(all_structures, creep, room_creeps, hostile_creeps)

            elif creep.memory.role == 'harvester':
                role_harvester.run_harvester(creep, all_structures, constructions, room_creeps, dropped_all)
                """
                Runs a creep as a generic harvester.
                :param creep: The creep to run
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                """

            elif creep.memory.role == 'hauler':
                role_hauler.run_hauler(creep, all_structures, constructions,
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
                role_carrier.run_carrier(creep, room_creeps, all_structures, constructions, dropped_all, repairs)
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
                role_upgrader.run_upgrader(creep, room_creeps, all_structures)

            elif creep.memory.role == 'miner':
                role_harvester.run_miner(creep, all_structures)
            elif creep.memory.role == 'scout':
                role_scout.run_scout(creep)
            elif creep.memory.role == 'reserver':
                role_upgrader.run_reserver(creep)
            elif creep.memory.role == 'demolition':
                role_soldier.demolition(creep, all_structures)

            elif creep.memory.role == 'g_collector':
                role_collector.collector(creep, room_creeps, dropped_all, all_structures)

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

                            # 한놈만 팬다.
                            if len(hostile_creeps) > 1:
                                enemy = [hostile_creeps[0]]
                            else:
                                enemy = hostile_creeps

                            for tower in structure_list[building_name]:
                                # sometimes these could die you know....
                                the_tower = Game.getObjectById(tower)
                                if the_tower:
                                    room_cpu_num += 1
                                    building_action.run_tower(the_tower, enemy, repairs, malsana_amikoj)

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

        # 아군만 있으면 방어막을 연다. 역으로 적이 보이면 열린거 닫는다.
        rampart_bool = False
        if Game.rooms[chambra_nomo].controller:
            if Game.rooms[chambra_nomo].controller.my:
                if len(hostile_creeps) > 0:
                    Memory.rooms[chambra_nomo].options.ramparts = 2
                elif len(allied_creeps) > 0:
                    Memory.rooms[chambra_nomo].options.ramparts = 1
                rampart_bool = True

        if rampart_bool and Memory.rooms[chambra_nomo].options:
            tm = Game.cpu.getUsed()
            if Memory.rooms[chambra_nomo].options.ramparts:
                # 몇개 건드렸는지 확인용도.
                ramparts_used = 0
                # 1이면 방어막 연다.
                if Memory.rooms[chambra_nomo].options.ramparts == 1:
                    # ramparts_open은 1이면 다 열렸다는 소리. 아님 닫힌거.
                    if not Memory.rooms[chambra_nomo].options.ramparts_open:
                        ramparts = all_structures.filter(lambda s: (s.structureType == STRUCTURE_RAMPART))
                        for r in ramparts:
                            if not r.isPublic:
                                ramparts_used += 1
                                r.setPublic(True)
                        Memory.rooms[chambra_nomo].options.ramparts_open = 1
                        print('opening {} ramparts in {}. {} CPU used.'.format(ramparts_used, chambra_nomo,
                                                                               round(Game.cpu.getUsed() - tm, 2)))
                # 2면 방어막 닫는다.
                elif Memory.rooms[chambra_nomo].options.ramparts == 2:
                    # 방식은 위의 정반대
                    if Memory.rooms[chambra_nomo].options.ramparts_open:
                        ramparts = all_structures.filter(lambda s: (s.structureType == STRUCTURE_RAMPART))
                        for r in ramparts:
                            if r.isPublic:
                                ramparts_used += 1
                                r.setPublic(False)
                        Memory.rooms[chambra_nomo].options.ramparts_open = 0
                        print('closing {} ramparts in {}. {} CPU used.'
                              .format(ramparts_used, chambra_nomo, round(Game.cpu.getUsed() - tm, 2)))
                else:
                    print('invalid value set on ramparts. initializing...')
                # 끝나면 초기화.
                Memory.rooms[chambra_nomo].options.ramparts = 0

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

    pathfinding.run_maintenance()

    if Game.time % interval == 0 or Memory.tick_check:
        cpu_total = 0
        for cpu in Memory.cpu_usage:
            cpu_total += cpu
        cpu_average = cpu_total / len(Memory.cpu_usage)
        print("{} total creeps, average cpu usage in the last {} ticks: {}, and current CPU bucket: {}"
              .format(len(Game.creeps), len(Memory.cpu_usage), round(cpu_average, 2), Game.cpu.bucket))
        Memory.tick_check = False


module.exports.loop = main
