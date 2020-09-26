import role_harvester
import role_hauler
import role_fixer
import role_upgrader
import structure_misc
import structure_display
import role_scout
import role_carrier
import role_soldier
import structure_spawn
import role_collector
import random
import pathfinding
import miscellaneous
import role_soldier_h_defender
from _custom_constants import *
import room_memory

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

# 패스파인딩 관련
js_global._costs = {'base': {}, 'rooms': {}, 'creeps': {}}


def main():
    """
    Main game logic loop.
    """

    cpu_bucket_emergency = 1000
    cpu_bucket_emergency_spawn_start = 2500
    if not Memory.debug and Memory.debug != False:
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
        if Game.time % 2000 == 0 or Memory.updateAlliance or not Memory.allianceArray:
            ally_start = Game.cpu.getUsed()
            # 수동으로 친구를 넣을때 사용함
            if not Memory.friendly:
                Memory.friendly = []

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
                    print('alliance not updated. not allied with any.',
                          '{} CPU used'.format(round(Game.cpu.getUsed() - ally_start, 2)))

            else:
                Memory.allianceArray = []
                print('alliance not updated - private server of {}. '
                      '{} CPU used'.format(shard_name, round(Game.cpu.getUsed() - ally_start, 2)))

    except Exception as err:
        print('Error in RawMemory.foreignSegment handling (alliance):', err)

    try:
        waste = Game.cpu.getUsed()
        # deleting unused creep memory.
        for name in Object.keys(Memory.creeps):
            if not Game.creeps[name]:
                if Memory.debug:
                    print('Clearing non-existing creep memory(powered by python™): ' + name)
                del Memory.creeps[name]
                continue

            creep: Creep = Game.creeps[name]

            # add creep's age. just for fun lol
            try:  # since this is new....
                if not creep.spawning:
                    if not creep.memory.birthday:
                        creep.memory.birthday = Game.time
                    if (Game.time - creep.memory.birthday) % 1500 < 2 and creep.ticksToLive > 50 \
                            and Game.time - creep.memory.birthday > 10:
                        age = (Game.time - creep.memory.birthday) // 1500
                        creep.say("{}차생일!🎂🎉".format(age), True)
                    # TTL 확인 용도
                    elif creep.ticksToLive % 40 == 0:
                        creep.say(creep.ticksToLive)
                    # 100만틱마다 경축빰빠레!
                    elif Game.time % 1000000 < 2000:
                        # 첫시작인 경우
                        if Game.time < 5000:
                            creep.say('NewTick!🎉', True)
                        else:
                            creep.say('{}M ticks🎉🍾'.format(int(Game.time / 1000000)), True)
                else:
                    continue
            except:
                continue
        if Memory.debug:
            print('time wasted for fun: {} cpu'.format(round(Game.cpu.getUsed() - waste, 2)))
    except:
        pass

    # to count the number of creeps passed in case of CPU limit reached.
    passing_creep_counter = 0

    # 스트럭쳐 목록 초기화 위한 숫자
    structure_renew_count = 100

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
        if Memory.debug:
            print('attempting to clear market records...')
        miscellaneous.clear_orders()

    # 좀 아래에 CPU 계산 디스플레이 용도.
    if Memory.cpu_usage:
        all_cpu = _.sum(Memory.cpu_usage)
        avg_cpu = round(all_cpu / len(Memory.cpu_usage), 2)
        last_cpu = Memory.cpu_usage[Memory.cpu_usage.length - 1]

    # todo 당장 안쓰고있지만 조만간 처리요망
    # 모든 방 안에 있는 모든 주요 오브젝트는 여기에 다 통합보관된다.
    all_objs = {}
    # 사전에 자원·건물현황·적 구분 등을 싹 다 돌린다.
    # for chambra_nomo in Object.keys(Game.rooms):
    #     # 찾아야 하는 대상: 각 방에 대한 모든것.
    #     chambro = Game.rooms[chambra_nomo]
    #
    #     # ALL .find() functions are done in here. THERE SHOULD BE NONE INSIDE CREEP FUNCTIONS!
    #     # filters are added in between to lower cpu costs.
    #     all_structures = {'all_structures': chambro.find(FIND_STRUCTURES)}
    #
    #     room_creeps = {'room_creeps': chambro.find(FIND_MY_CREEPS)}
    #
    #     malsanaj_amikoj = {'malsanaj_amikoj': _.filter(room_creeps, lambda c: c.hits < c.hitsMax)}
    #
    #     enemy_constructions = {'enemy_constructions': chambro.find(FIND_HOSTILE_CONSTRUCTION_SITES)}
    #     my_constructions = {'my_constructions': chambro.find(FIND_MY_CONSTRUCTION_SITES)}
    #     # 바로아래 이유로 딕셔너리화하진 않음.
    #     dropped_all = chambro.find(FIND_DROPPED_RESOURCES)
    #     tombs = chambro.find(FIND_TOMBSTONES)
    #     ruins = chambro.find(FIND_RUINS)
    #     if tombs:
    #         for t in tombs:
    #             if _.sum(t.store) > 0:
    #                 dropped_all.append(t)
    #     if ruins:
    #         for r in ruins:
    #             if _.sum(r.store) > 0:
    #                 dropped_all.append(r)
    #     dropped_all = {'dropped_all': dropped_all}
    #
    #     # 필터하면서 목록을 삭제하는거 같음.... 그래서 이리 초기화
    #     foreign_creeps = chambro.find(FIND_HOSTILE_CREEPS)
    #     nukes = {'nukes': chambro.find(FIND_NUKES)}
    #     # [[적 전부], [적 NPC], [적 플레이어], [동맹]]
    #     friends_and_foes = miscellaneous.filter_friend_foe(foreign_creeps)
    #     # init. list
    #     hostile_creeps = {'hostile_creeps': friends_and_foes[0]}
    #     allied_creeps = {'allied_creeps': friends_and_foes[3]}
    #
    #     room_objs = {chambra_nomo: {all_structures, room_creeps, malsanaj_amikoj, enemy_constructions, my_constructions,
    #                                 dropped_all, nukes, hostile_creeps, allied_creeps}}

    # run everything according to each rooms.
    for chambra_nomo in Object.keys(Game.rooms):
        chambro_cpu = Game.cpu.getUsed()
        chambro = Game.rooms[chambra_nomo]

        # fix_rating = stop_fixer 급수별 램파트 수리 양.
        # 레벨8 진입전까진 렙 하나당 100k씩 추가, 리페어렙 1 유지.
        if chambro.controller and chambro.controller.level < 8:
            fix_rating = 100000 * chambro.controller.level
        else:
            fix_rating = 2000000

        # todo 여기 메모리 맨아래로 옮겨야함
        # todo 방폭되면 거깄는 메모리 제거요망
        # 게임 내 수동조작을 위한 초기화 설정. 단, 방이 우리꺼일 경우에만 적용.
        if chambro.controller and chambro.controller.my:
            # 방 메모리가 아예 없을경우.
            if not Memory.rooms:
                Memory.rooms = {}
            if not Memory.rooms[chambra_nomo]:
                Memory.rooms[chambra_nomo] = {}
            if not Memory.rooms[chambra_nomo].options:
                Memory.rooms[chambra_nomo] = {options: {}}
            # repair level - 벽·방어막에만 적용. 렙하나당 이백만
            if not Memory.rooms[chambra_nomo].options.repair \
                    and not Memory.rooms[chambra_nomo][options][repair] == 0:
                Memory.rooms[chambra_nomo][options][repair] = 1
            # 스토리지 안 채울 최대 에너지량. 기본값 5만
            if not Memory.rooms[chambra_nomo].options[max_energy]:
                Memory.rooms[chambra_nomo].options[max_energy] = 50000
            # 타워 공격시킬건가? 1이면 공격. 또한 매 1만턴마다 리셋한다.
            if (not Memory.rooms[chambra_nomo].options.tow_atk
                and not Memory.rooms[chambra_nomo].options.tow_atk == 0) \
                    or Game.time % 10000 == 0:
                Memory.rooms[chambra_nomo].options.tow_atk = 1
            # 핵사일로 채울거임? 채우면 1 아님 0. 안채울 경우 핵미사일 안에 에너지 빼감.
            if not Memory.rooms[chambra_nomo].options.fill_nuke \
                    and not Memory.rooms[chambra_nomo].options.fill_nuke == 0:
                Memory.rooms[chambra_nomo].options.fill_nuke = 1
            # 연구소 에너지 채울거임?
            if not Memory.rooms[chambra_nomo].options.fill_labs \
                    and not Memory.rooms[chambra_nomo].options.fill_labs == 0:
                Memory.rooms[chambra_nomo].options.fill_labs = 1
            # 체력이 지정량보다 떨어진 방어막이 없다는걸 확인한 시간.
            # 수리해야할 방어막이 없으면 수리크립을 뽑을필요가 없음.
            if not chambro.memory[options][stop_fixer]:
                chambro.memory[options][stop_fixer] = Game.time

            # 방어막 열건가? 0 = 통과, 1 = 연다, 2 = 닫는다.
            if not Memory.rooms[chambra_nomo].options.ramparts \
                    and not Memory.rooms[chambra_nomo].options.ramparts == 0:
                Memory.rooms[chambra_nomo].options.ramparts = 0
            # 방어막이 열려있는지 확인. 0이면 닫힌거. 위에꺼랑 같이 연동함.
            if not Memory.rooms[chambra_nomo].options.ramparts_open \
                    and not Memory.rooms[chambra_nomo].options.ramparts_open == 0:
                Memory.rooms[chambra_nomo].options.ramparts_open = 0

            # 각종현황(현재는 링크·타워만) 초기화 할것인가?
            if not Memory.rooms[chambra_nomo].options.reset \
                    and not Memory.rooms[chambra_nomo].options.reset == 0:
                Memory.rooms[chambra_nomo].options.reset = 1

            # 화면안에 위에 설정값들 표기.
            if Memory.rooms[chambra_nomo].options.display \
                    and len(Memory.rooms[chambra_nomo].options.display) > 0:
                remotes_txt = ''
                if Memory.rooms[chambra_nomo].options.remotes:
                    # 방이름으로 돌린다.
                    for r in Object.keys(Memory.rooms[chambra_nomo][options][remotes]):
                        # 지정된 리모트 추가
                        remotes_txt += r

                        # 배정된 병사 수 추가
                        defendistoj = Memory.rooms[chambra_nomo][options][remotes][r][defenders]
                        remotes_txt += '({}) '.format(defendistoj)

                        # 각 리모트에도 설정한다. 당연하지만 안에 시야를 확보했을 경우만...
                        if Memory.rooms[chambra_nomo].options.remotes[r].display \
                                and Game.rooms[r]:
                            rx = Memory.rooms[chambra_nomo].options.remotes[r].display.x
                            ry = Memory.rooms[chambra_nomo].options.remotes[r].display.y
                            Game.rooms[r].visual.text('-def {}'.format(defendistoj), rx, ry)

                # 각 메모리 옵션별 값.
                repair_txt = Memory.rooms[chambra_nomo][options][repair]
                ramparts_txt = Memory.rooms[chambra_nomo].options.ramparts
                ramp_open_txt = Memory.rooms[chambra_nomo].options.ramparts_open
                nuke_txt = Memory.rooms[chambra_nomo].options.fill_nuke
                lab_txt = Memory.rooms[chambra_nomo].options.fill_labs
                tow_txt = Memory.rooms[chambra_nomo].options.tow_atk
                energy_txt = Memory.rooms[chambra_nomo].options[max_energy]
                stop_fixer_txt = Game.time - chambro.memory[options][stop_fixer]

                # 찍힐 좌표
                disp_x = Memory.rooms[chambra_nomo].options.display.x
                disp_y = Memory.rooms[chambra_nomo].options.display.y

                # \n doesnt work
                # print('mmr;', Memory.cpu_usage[-1])
                chambro.visual.text('lastCPU {}, {} 틱당평균 {}, 버켓 {}'
                                    .format(last_cpu, len(Memory.cpu_usage), avg_cpu, Game.cpu.bucket),
                                    disp_x, disp_y + 0)
                chambro.visual.text('remotes(def): {}'.format(remotes_txt),
                                    disp_x, disp_y + 1)
                chambro.visual.text('수리: {} | 방벽(open): {}({})'
                                    .format(repair_txt, ramparts_txt, ramp_open_txt),
                                    disp_x, disp_y + 2)
                chambro.visual.text('fillNuke/Labs: {}/{}, tow_atk/reset: {}/{}'
                                    .format(nuke_txt, lab_txt, tow_txt, 10000 - Game.time % 10000),
                                    disp_x, disp_y + 3)
                chambro.visual.text('E할당량: {} | 수리X: {}'.format(str(int(energy_txt / 1000)) + 'k', stop_fixer_txt),
                                    disp_x, disp_y + 4)
                # chambro.visual.text(display_txt, disp_x, disp_y+2)

            # 컨테이너 안에 물건들 총합
            if len(chambro.memory[STRUCTURE_CONTAINER]):
                for c in chambro.memory[STRUCTURE_CONTAINER]:
                    the_container = Game.getObjectById(c.id)
                    if the_container and _.sum(the_container.store):
                        chambro.visual.text(str(_.sum(the_container.store)), the_container.pos,
                                            {'color': '#EE5927', 'font': 0.5})

            # bld_plan - 건설예약설정.
            if not chambro.memory.bld_plan:
                chambro.memory.bld_plan = []
            # 건설예약시스템(?)
            if chambro.memory.bld_plan:
                num = 0
                for plan in chambro.memory.bld_plan:
                    try:
                        # print(plan)
                        if plan.type == STRUCTURE_LINK:
                            ball = '🔗'
                        elif plan.type == STRUCTURE_EXTENSION:
                            ball = 'ⓔ'
                        elif plan.type == STRUCTURE_ROAD:
                            ball = 'ⓡ'
                        elif plan.type == STRUCTURE_RAMPART:
                            ball = '🛡️'
                        elif plan.type == STRUCTURE_STORAGE:
                            ball = 'ⓢ'
                        elif plan.type == STRUCTURE_SPAWN:
                            ball = '🏭'
                        # 우선 같은 지역에 해당 건물 또는 다른 무언가가 있는지 확인.
                        site = chambro.lookForAt(LOOK_STRUCTURES, plan.pos.x, plan.pos.y)
                        # print('site', site)
                        if len(site):
                            # 있으면 해당 건설은 유효하지 않다. 삭제한다.
                            chambro.memory.bld_plan.splice(num, 1)
                            continue
                        # 이미 건설장이 있는 경우 대기한다. 뭔가 완전히 완공되지 않는 한 해당 옵션은 계속된다.
                        elif len(chambro.lookForAt(LOOK_CONSTRUCTION_SITES, plan.pos.x, plan.pos.y)):
                            pass
                        else:
                            # 건설시도.
                            place_plan = __new__(RoomPosition(plan.pos.x, plan.pos.y, plan.pos.roomName)) \
                                .createConstructionSite(plan.type)
                            # print(place_plan, 'place_plan')
                            # 어떤 타입의 건물인지 명시
                            chambro.visual.text(ball, plan.pos.x, plan.pos.y)
                        # 만일 타겟이
                        # if place_plan == ERR_INVALID_ARGS or place_plan == ERR_INVALID_ARGS:

                        # 건설 완료하기 전까지 계속 기록 남긴다. - 무기한 연기
                        # if not place_plan == ERR_RCL_NOT_ENOUGH:
                        #     del plan
                    except:
                        chambro.memory.bld_plan.splice(num, 1)
                    num += 1

        # ALL .find() functions are done in here. THERE SHOULD BE NONE INSIDE CREEP FUNCTIONS!
        # filters are added in between to lower cpu costs.
        all_structures = chambro.find(FIND_STRUCTURES)

        room_creeps = chambro.find(FIND_MY_CREEPS)

        malsana_amikoj = _.filter(room_creeps, lambda c: c.hits < c.hitsMax)

        enemy_constructions = chambro.find(FIND_HOSTILE_CONSTRUCTION_SITES)
        my_constructions = chambro.find(FIND_MY_CONSTRUCTION_SITES)
        dropped_all = chambro.find(FIND_DROPPED_RESOURCES)
        tombs = chambro.find(FIND_TOMBSTONES)
        ruins = chambro.find(FIND_RUINS)
        if ruins:
            for r in ruins:
                if _.sum(r.store) > 0:
                    dropped_all.append(r)
        if tombs:
            for t in tombs:
                if _.sum(t.store) > 0:
                    dropped_all.append(t)

        # 필터하면서 목록을 삭제하는거 같음.... 그래서 이리 초기화
        foreign_creeps = chambro.find(FIND_HOSTILE_CREEPS)
        nukes = chambro.find(FIND_NUKES)
        # [[적 전부], [적 NPC], [적 플레이어], [동맹]]
        friends_and_foes = miscellaneous.filter_friend_foe(foreign_creeps)
        # init. list
        hostile_creeps = friends_and_foes[0]
        hostile_human = friends_and_foes[2]
        allied_creeps = friends_and_foes[3]

        # 초기화.
        terminal_capacity = 0
        # 방 안의 터미널 내 에너지 최소값.
        if chambro.controller:
            if chambro.terminal and chambro.controller.level < 8:
                terminal_capacity = 1000
            else:
                terminal_capacity = 10000

        # todo 방렙 8 아래면?
        # 핵이 있으면 비상!! 수리수치를 올린다.
        if bool(nukes):
            if chambro.memory[options][repair] < 5:
                chambro.memory[options][repair] = 5
            nuke_extra = 150000
        else:
            nuke_extra = 0
        # 모든 수리대상 찾는다. 분류는 위에 크립·타워 등에 따라 거른다.
        repairs = all_structures.filter(lambda s: (s.structureType == STRUCTURE_ROAD
                                                   or s.structureType == STRUCTURE_TOWER
                                                   or s.structureType == STRUCTURE_EXTENSION
                                                   or s.structureType == STRUCTURE_LINK
                                                   or s.structureType == STRUCTURE_LAB
                                                   or s.structureType == STRUCTURE_CONTAINER
                                                   or s.structureType == STRUCTURE_STORAGE
                                                   or s.structureType == STRUCTURE_SPAWN
                                                   or s.structureType == STRUCTURE_POWER_SPAWN)
                                                  and s.hits < s.hitsMax)
        # print('WTFR', JSON.stringify(repairs))
        if chambro.controller and chambro.controller.my:
            # 방에 있는 모든 수리대상 장벽·방어막
            wall_repairs = all_structures.filter(lambda s: (s.structureType == STRUCTURE_RAMPART
                                                            or s.structureType == STRUCTURE_WALL)
                                                           and s.hits < chambro.memory[options][
                                                               repair] * fix_rating + nuke_extra)

        # 벽을 본다.
        all_repairs = []
        if not len(wall_repairs) == 0:
            # 지도에서 가장 낮은 체력의 방벽
            min_wall = _.min(wall_repairs, lambda s: s.hits)
            # 가장 낮은 체력의 방벽이 몇? 여기서 필요한건 아님.
            min_hits = int(min_wall.hits / fix_rating)
            # repairs.extend(wall_repairs)
            all_repairs.extend(repairs)
            all_repairs.extend(wall_repairs)
        else:
            min_wall = []
            min_hits = 0
            all_repairs.extend(repairs)

        my_structures = chambro.find(FIND_MY_STRUCTURES)

        extractor = _.filter(my_structures, lambda s: s.structureType == STRUCTURE_EXTRACTOR)

        spawns = chambro.find(FIND_MY_SPAWNS)
        damaged_bld = _.filter(my_structures,
                               lambda s: (s.structureType == STRUCTURE_EXTENSION or
                                          s.structureType == STRUCTURE_SPAWN) and s.hits < s.hitsMax)
        # 건물이 공격당하고 있고 그게 잉간이면 세이프모드 발동
        if len(damaged_bld) and len(hostile_human) and \
                chambro.controller.safeModeAvailable and not chambro.controller.safeModeCooldown:
            chambro.controller.activateSafeMode()
        # Run each creeps
        for chambro_creep in room_creeps:
            creep_cpu = Game.cpu.getUsed()

            creep = Game.creeps[chambro_creep.name]
            # 만일 생산중이면 그냥 통과
            if creep.spawning:
                if not creep.memory.age and creep.memory.age != 0:
                    creep.memory.age = 0
                if not creep.memory.birthplace:
                    creep.memory.birthplace = creep.pos
                continue

            # but if a soldier/harvester.... nope. they're must-be-run creeps
            if creep.memory.role == 'soldier':
                role_soldier.run_remote_defender(all_structures, creep, room_creeps, hostile_creeps)

            elif creep.memory.role == 'h_defender':
                role_soldier_h_defender.h_defender(all_structures, creep, room_creeps, hostile_creeps)

            elif creep.memory.role == 'harvester':
                role_harvester.run_harvester(creep, all_structures, my_constructions, room_creeps, dropped_all)
                """
                Runs a creep as a generic harvester.
                :param creep: The creep to run
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                """

            elif creep.memory.role == 'hauler':
                role_hauler.run_hauler(creep, all_structures, my_constructions,
                                       room_creeps, dropped_all, all_repairs, terminal_capacity)
                """
                :param creep:
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
                :param creeps: creep.room.find(FIND_MY_CREEPS)
                :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
                :return:
                """
            elif creep.memory.role == 'fixer':
                role_fixer.run_fixer(creep, all_structures, my_constructions,
                                     room_creeps, all_repairs, min_wall, terminal_capacity, dropped_all)
                """
                :param creep:
                :param all_structures: creep.room.find(FIND_STRUCTURES)
                :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
                :param creeps: creep.room.find(FIND_MY_CREEPS))
                :return:
                """
            elif creep.memory.role == 'carrier':
                role_carrier.run_carrier(creep, room_creeps, all_structures, my_constructions, dropped_all, all_repairs)
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
                role_upgrader.run_upgrader(creep, room_creeps, all_structures,
                                           all_repairs, my_constructions, dropped_all)

            elif creep.memory.role == 'miner':
                role_harvester.run_miner(creep, all_structures)
            elif creep.memory.role == 'scout':
                role_scout.run_scout(creep, enemy_constructions)
            elif creep.memory.role == 'reserver':
                role_upgrader.run_reserver(creep)
            elif creep.memory.role == 'demolition':
                role_soldier.demolition(creep, all_structures)

            elif creep.memory.role == 'g_collector':
                role_collector.collector(creep, room_creeps, dropped_all, all_structures)
            # 크립의 CPU 사용량 명시.
            if not creep.memory.cpu_usage:
                creep.memory.cpu_usage = []

            creep_cpu_end = Game.cpu.getUsed() - creep_cpu
            creep.room.visual.text(round(creep_cpu_end, 2), creep.pos, {'color': 'FloralWhite', 'font': 0.35})

            creep.memory.cpu_usage.append(round(creep_cpu_end, 2))
            # cpu_usage 는 cpu_count 에 명시된 숫자 만큼만 센다. 그 이상 누적되면 오래된 순으로 자른다.
            while len(creep.memory.cpu_usage) > cpu_count:
                creep.memory.cpu_usage.splice(0, 1)
            # 총값확인용도
            total_creep_cpu_num += 1
            total_creep_cpu += creep_cpu_end

        room_cpu = Game.cpu.getUsed()
        room_cpu_num = 0

        # 방 안 건물/소스현황 갱신.
        # 1차 발동조건: structure_renew_count 만큼의 턴이 지났는가? 또는 스폰있는 방에 리셋명령을 내렸는가?
        if Game.time % structure_renew_count == 0 or (chambro.memory.options and chambro.memory.options.reset):
            room_memory.refresh_base_stats(chambro, all_structures, fix_rating, min_wall, spawns)

        # 스폰과 링크목록. 디스플레이 적용하거나 할때 걸릴 수도 있는 오브젝트 전부.
        objs_for_disp = []
        objs_for_disp.extend(spawns)

        if chambro.memory:
            if chambro.memory[STRUCTURE_LINK] and len(chambro.memory[STRUCTURE_LINK]) > 0:
                for link in chambro.memory[STRUCTURE_LINK]:
                    if Game.getObjectById(link.id):
                        objs_for_disp.append(Game.getObjectById(link.id))
            if chambro.memory[STRUCTURE_CONTAINER] and len(chambro.memory[STRUCTURE_CONTAINER]) > 0:
                for c in chambro.memory[STRUCTURE_CONTAINER]:
                    if Game.getObjectById(c.id):
                        objs_for_disp.append(Game.getObjectById(c.id))

        # STRUCTURE_TOWER
        if chambro.memory[STRUCTURE_TOWER] and len(chambro.memory[STRUCTURE_TOWER]) > 0:
            # 수리는 크게 두종류만 한다. 도로와 컨테이너는 체력 20% 이하면 수리. 나머지는 무조건.
            tow_repairs = repairs.filter(lambda s: (s.structureType != STRUCTURE_ROAD
                                                    and s.structureType != STRUCTURE_CONTAINER)
                                                   or (s.structureType == STRUCTURE_CONTAINER
                                                       and s.hits < s.hitsMax * .2)
                                                   or (s.structureType == STRUCTURE_ROAD
                                                       and s.hits < s.hitsMax * .2))
            # 벽수리는 5천까지만. 다만 핵이 있으면 예외.
            if min_wall.hits < 5000 or bool(nukes):
                # print('min_wall', min_wall)
                tow_repairs.append(min_wall)
            # print('tow', JSON.stringify(tow_repairs))
            # 한놈만 팬다.
            if len(hostile_creeps) > 1:
                enemy = [hostile_creeps[0]]
            else:
                enemy = hostile_creeps
            for_str = 0
            for i in chambro.memory[STRUCTURE_TOWER]:
                if Game.getObjectById(i):
                    room_cpu_num += 1
                    structure_misc.run_tower(Game.getObjectById(i), enemy, tow_repairs, malsana_amikoj)
                else:
                    chambro.memory[STRUCTURE_TOWER].splice(for_str, 1)
                for_str += 1

        # STRUCTURE_LINK
        if chambro.memory[STRUCTURE_LINK] and len(chambro.memory[STRUCTURE_LINK]) > 0:
            # for_str = 0
            # 링크가 없는게 있는지 먼져 확인.
            link_missing = True
            while link_missing:
                for_str = 0
                for link_chk in chambro.memory[STRUCTURE_LINK]:
                    # 존재하지 않으면 삭제하는거.
                    if not Game.getObjectById(link_chk.id):
                        chambro.memory[STRUCTURE_LINK].splice(for_str, 1)
                        break
                    for_str += 1
                link_missing = False

            for link in chambro.memory[STRUCTURE_LINK]:
                if not link:
                    chambro.memory.options.reset = 1
                    continue
                room_cpu_num += 1
                structure_misc.run_links(link.id, objs_for_disp)

        # check every 20 ticks.
        if Game.time % 20 == 0 and chambro.memory[STRUCTURE_CONTAINER] \
                and len(chambro.memory[STRUCTURE_CONTAINER]) > 0:
            for_str = 0
            for cc in chambro.memory[STRUCTURE_CONTAINER]:
                if not Game.getObjectById(cc.id):
                    chambro.memory[STRUCTURE_CONTAINER].splice(for_str, 1)
                for_str += 1
                room_cpu_num += 1

        if (Memory.debug and Game.time % interval == 0) and room_cpu_num > 0:
            end = Game.cpu.getUsed()
            # print("end {} start {}".format(round(end, 2), round(room_cpu, 2)))
            room_cpu_avg = (end - room_cpu) / room_cpu_num
            print("{} structures ran in {} total with avg. {} cpu, tot. {} cpu"
                  .format(room_cpu_num, chambra_nomo, round(room_cpu_avg, 2), round(end - room_cpu, 2)))

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

            if Memory.debug and Game.time % interval == 0:
                print('방 {} 루프에서 스폰 {} 준비시간 : {} cpu'.format(nesto.room.name, nesto.name
                                                             , round(Game.cpu.getUsed() - spawn_cpu, 2)))

            structure_spawn.run_spawn(nesto, all_structures, room_creeps, hostile_creeps, divider, counter,
                                      cpu_bucket_emergency, cpu_bucket_emergency_spawn_start, extractor,
                                      terminal_capacity, chambro, interval, wall_repairs, objs_for_disp,
                                      min_hits)

            spawn_cpu_end = Game.cpu.getUsed() - spawn_cpu
            if Memory.debug and Game.time % interval == 0:
                print('spawn {} used {} cpu'.format(spawn.name, round(spawn_cpu_end, 2)))
        # 방에 컨트롤러가 내꺼면 다음렙까지 남은 업글점수 표기
        if chambro.controller and chambro.controller.my and not chambro.controller.level == 8:
            disp_loc = structure_display.display_location(chambro.controller, objs_for_disp, 3)
            chambro.visual.text(str(chambro.controller.progressTotal - chambro.controller.progress),
                                disp_loc.x, disp_loc.y,
                                {'align': disp_loc['align'], 'opacity': 0.8, 'color': '#EE5927'})
        # 맨 위 visual 부분 정산
        chambro.visual.text('visual size: {}'.format(Game.rooms[chambra_nomo].visual.getSize()),
                            disp_x, disp_y + 5)

    if Game.cpu.bucket < cpu_bucket_emergency:
        print('passed creeps:', passing_creep_counter)

    if Memory.debug and Game.time % interval == 0:
        print("total of {} creeps run with avg. {} cpu, tot. {} cpu"
              .format(total_creep_cpu_num, round(total_creep_cpu / total_creep_cpu_num, 2), round(total_creep_cpu, 2)))

    # 텅빈메모리 제거작업
    # 게임 기본값으로 생기는거라 못없앰.
    # if Game.time % structure_renew_count == 0:
    #     for n in Object.keys(Memory.rooms):
    #         if not Object.keys(Memory.rooms[n])[0]:
    #             del Memory.rooms[n]
    #             print('{}방 메모리 텅비어서 삭제'.format(n))

    # adding total cpu
    # while len(Memory.cpu_usage.total) >= Memory.ticks:
    while len(Memory.cpu_usage) >= Memory.ticks:
        Memory.cpu_usage.splice(0, 1)
    # 소수점 다 올림처리. 겜에서도 그리 간주함.
    Memory.cpu_usage.push(int(Game.cpu.getUsed()) + 1)

    pathfinding.run_maintenance()


module.exports.loop = main
