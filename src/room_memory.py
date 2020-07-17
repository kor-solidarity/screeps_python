from _custom_constants import *

# defs is a package which claims to export all constants and some JavaScript objects, but in reality does
#  nothing. This is useful mainly when using an editor like PyCharm, so that it 'knows' that things like Object, Creep,
#  Game, etc. do exist.
from defs import *
import miscellaneous

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
원래 메인에 있던 방별 메모리 갱신을 편의상 이곳으로 옮김.  
"""


# 모든 방에 있는 메모리를 한꺼번에 뽑기.
# 사전에 자원·건물현황·적 구분 등을 싹 다 돌린다.
def init_memory():
    """
    뽑혀야 하는 메모리 목록:
    1. 방 안 모든 정보:
        - 건물

    :return:
    """
    for room_name in Object.keys(Game.rooms):
        chambro = Game.rooms[room_name]
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
        # todo 임시니 변경요망
        if chambro.controller:
            if chambro.terminal and chambro.controller.level < 8:
                terminal_capacity = 1000
            else:
                terminal_capacity = 10000

    # 여기에 모든게 들어가 있어야 한다.
    room_info = {}

    return room_info


# 본진 관련
def refresh_base_stats(chambro: Room, all_structures, fix_rating, min_wall, spawns):
    """
    방 내 메모리 현황 갱신을 위한 함수.
    잘 바뀌지 않는 사안들()

    :param chambro: 오브젝트화된 방
    :param all_structures: 방 안 모든 스트럭쳐
    :param fix_rating: 방 안 수리등급
    :param min_wall: 방 안에 가장 낮은 체력의 방벽
    :param spawns: 방 안에 모든 스폰
    :return:
    """
    creeps_memory = []
    for c in Object.keys(Memory.creeps):
        creeps_memory.append(Memory.creeps[c])

    distance_to_controller = 5

    # 방 안 건물/소스현황 갱신.
    structure_cpu = Game.cpu.getUsed()

    # 내 방이 아닌데 내 방마냥 현황이 적혀있으면 초기화한다.
    # todo 방에 대한 기초신상 다 턴다.
    if chambro.controller and not chambro.controller.my and chambro.memory[options]:
        chambro.memory = {}

    # 방 안에 소스랑 미네랄 현황 확인
    if not chambro.memory[resources] or chambro.memory.options and chambro.memory.options.reset:
        room_sources = chambro.find(FIND_SOURCES)
        room_minerals = chambro.find(FIND_MINERALS)
        chambro.memory[resources] = {energy: [], minerals: []}
        for rs in room_sources:
            chambro.memory[resources][energy].append(rs.id)
        for rm in room_minerals:
            chambro.memory[resources][minerals].append(rm.id)
        del room_sources
    # 이 방에 키퍼가 있는지 확인.
    if not chambro.memory[STRUCTURE_KEEPER_LAIR]:
        chambro.memory[STRUCTURE_KEEPER_LAIR] = []
        room_str = chambro.find(FIND_STRUCTURES)
        for s in room_str:
            if s.structureType == STRUCTURE_KEEPER_LAIR:
                chambro.memory[keeper].append(s.id)

    # 본진인가?
    if chambro.controller and chambro.controller.my:
        # 이거 돌리는데 얼마나 걸리는지 확인하기 위한 작업.
        # 목록 초기화.
        if not chambro.memory[STRUCTURE_TOWER] or chambro.memory.options.reset:
            chambro.memory[STRUCTURE_TOWER] = []
        if not chambro.memory[STRUCTURE_LINK] or chambro.memory.options.reset:
            chambro.memory[STRUCTURE_LINK] = []
        if not chambro.memory[STRUCTURE_CONTAINER] or chambro.memory.options.reset:
            chambro.memory[STRUCTURE_CONTAINER] = []
        if not chambro.memory[STRUCTURE_LAB] or chambro.memory.options.reset:
            chambro.memory[STRUCTURE_LAB] = []
        # 렙8이 되면 기존에 업글 등의 역할이 배정된것들 초기화 해야함. 그 용도
        if not chambro.memory[room_lvl] or chambro.memory.options.reset:
            chambro.memory[room_lvl] = 1
            # 아래 레벨 확인 용도.
            past_lvl = chambro.memory[room_lvl]
            chambro.memory[room_lvl] = chambro.controller.level

        # 방 안에 스토리지 오브젝트. 너무 길어서.
        room_storage = chambro.storage
        # 만일 스토리지 용량이 부족한데 랩 채우게끔 되있으면 뽑아간다.
        if chambro.memory[options].fill_labs and room_storage and room_storage.store.energy < 2000:
            chambro.memory[options].fill_labs = 0
        # 역으로 스토리지가 꽉 찼는데 안채우게 되있으면 넣는다.
        if not chambro.memory[options].fill_labs and room_storage \
                and room_storage.storeCapacity - _.sum(room_storage.store) < chambro.memory[options][max_energy]:
            chambro.memory[options].fill_labs = 1

        # 방 안 스토리지 자원이 꽉 찼는데 수리레벨이 남아있을 경우 한단계 올린다.
        # max energy 계산법:
        # 스토리지 내 남은 공간이 max_energy 보다 적으면 발동하는거임.
        # 이름이 좀 꼬였는데 별수없음...
        if room_storage \
                and room_storage.storeCapacity - _.sum(room_storage.store) < chambro.memory[options][max_energy] + 10000 \
                and not len(min_wall) and chambro.memory[options][repair] < 150 \
                and chambro.controller.level == 8:
            chambro.memory[options][repair] += 1

        # 방에 수리할 벽이 없을 경우 확인한 시간 갱신한다.
        elif not len(min_wall):
            chambro.memory[options][stop_fixer] = Game.time

        # 만약 리페어가 너무 아래로 떨어졌을 시 리페어값을 거기에 맞게 낮춘다.
        elif min_wall.hits // fix_rating < chambro.memory[options][repair] - 1:
            chambro.memory[options][repair] = min_wall.hits // fix_rating + 1
            # 이때 픽서 수 하나짜리로 초기화.
            chambro.memory[options][stop_fixer] = Game.time - 400
        # 렙8 아래면 픽서 카운터는 천을 넘지 않는다. 숫자 잔뜩뜨는거 보기싫어서..
        elif chambro.controller.level < 8 and Game.time - chambro.memory[options][stop_fixer] >= 1000:
            print('reset repair time')
            chambro.memory[options][stop_fixer] = Game.time - 500

        # 매번 완전초기화 하면 너무 자원낭비. 수량 틀릴때만 돌린다.
        # 타워세기.
        str_towers = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_TOWER)
        if not len(str_towers) == len(chambro.memory[STRUCTURE_TOWER]):
            chambro.memory[STRUCTURE_TOWER] = []
            for stt in str_towers:
                chambro.memory[STRUCTURE_TOWER].push(stt.id)

        # add links. 위와 동일한 원리.
        # todo 여기뿐 아니라 캐려쪽도 해당인데, 거리에 따라 업글용인지 등등을 확인하는건 다 여기서만!
        str_links = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_LINK)
        if not len(str_links) == len(chambro.memory[STRUCTURE_LINK]) or not past_lvl == chambro.memory[room_lvl]:
            chambro.memory[STRUCTURE_LINK] = []
            range_required = 5
            # 안보내는 조건은 주변 range_required 거리 내에 컨트롤러·스폰·스토리지가 있을 시.
            storage_points = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_STORAGE
                                                                or s.structureType == STRUCTURE_SPAWN
                                                                or s.structureType == STRUCTURE_TERMINAL)
            print("roomName", chambro.name, 'lvl', chambro.controller.level)
            # NULLIFIED - 거리기준 문제로 별도로센다.
            # 만렙이 아닐 경우 컨트롤러 근처에 있는것도 센다.
            # if not chambro.controller.level == 8:
            #     storage_points.append(chambro.controller)

            # 링크는 크게 두 종류가 존재한다. 하나는 보내는거, 또하난 받는거.
            for stl in str_links:
                # 0이면 보내는거.
                _store = 0
                # 1이면 업글용인거.
                _upgrade = 0
                # 링크에서 가장 가까이 있는 storage_points
                closest_storage = stl.pos.findClosestByPath(storage_points, {ignoreCreeps: True})
                # 링크에서 가장 가까이 있는 storage_points 까지의 거리
                path_to_closest_storage = stl.pos.findPathTo(closest_storage, {ignoreCreeps: True})
                # 링크에서 컨트롤러까지의 길
                path_to_controller = stl.pos.findPathTo(chambro.controller, {'ignoreCreeps': True, 'range': 3})

                # 거리가 조건에 충족하면 우선 저장용임.
                if len(path_to_closest_storage) <= range_required or len(path_to_controller) <= range_required:
                    _store = 1

                # 만일 저장용이긴 한데  컨트롤러 근처에만 있는 경우 너무 먼거라 더이상 쓸모없음.
                # 이 경우 안에 남아있는 자원이 없으면 더 이상 운송용으로 쓰지 않는다.
                if _store and not len(path_to_closest_storage) <= range_required \
                        and stl.store.getUsedCapacity(RESOURCE_ENERGY) == 0:
                    _store = 0

                # 저장용이면 컨트롤러 근처에 있는지도 센다. 업글용인지 확인할 용도
                if _store and not chambro.controller.level == 8:
                    # 컨트롤러가 스토리지보다 더 가까울 경우 업글용으로 분류한다.
                    if len(path_to_controller) < len(path_to_closest_storage):
                        _upgrade = 1

                # 추가한다
                chambro.memory[STRUCTURE_LINK] \
                    .push({'id': stl.id, for_upgrade: _upgrade, for_store: _store, 'received_time': 1})

        # 컨테이너
        str_cont = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_CONTAINER)
        # if not len(str_cont) == len(chambro.memory[STRUCTURE_CONTAINER]):
        if True:
            chambro.memory[STRUCTURE_CONTAINER] = []
            # 컨테이너는 크게 세종류가 존재한다.
            # 하베스터용, 캐리어용, 업그레이더용.
            # 각각 뭐냐에 따라 채울지 말지, 그리고 얼마나 차면 새 허울러를 추가할지를 정한다.

            # 하베스터용은 그냥 소스 근처(4이내)에 컨테이너가 존재하는지 확인한다. 캐리어는 당연 정반대.
            # 업그레이더용은 컨트롤러 근처에 있는지 확인한다.

            for stc in str_cont:
                # 하베스터 저장용인가? 맞으면 1, 만일 캐리어 운송용이면 2. 2는 캐리어 쪽에서 건든다.
                # 0 이면 방업글 끝나면 계속 갖고있을 이유가 없는 잉여인 셈.
                _harvest = 0
                # 방 업글용인가?
                _upgrade = 0

                room_sources = []
                for e in chambro.memory[resources][energy]:
                    room_sources.append(Game.getObjectById(e))
                for e in chambro.memory[resources][minerals]:
                    room_sources.append(Game.getObjectById(e))
                # print(room_sources)
                for rs in room_sources:
                    # 컨테이너 주변 4칸이내에 소스가 있는지 확인한다.
                    if len(stc.pos.findPathTo(rs, {'ignoreCreeps': True})) <= 4:
                        # 있으면 이 컨테이너는 하베스터 저장용.
                        _harvest = 1
                        break
                # _harvest 값에 영향을 주는건 캐리어도 있다.
                carrier_mem = _.filter(creeps_memory, lambda c: c.role == 'carrier' and len(c.haul_destos))
                for c in carrier_mem:
                    for td in c.haul_destos:
                        if stc.id == td.id:
                            _harvest = 1
                            break
                    if _harvest == 1:
                        break

                # 확인 끝났으면 이제 방 업글용인지 확인한다. 방렙 8 미만인가?
                if chambro.controller.level < 8:
                    # 컨테이너와의 거리가 컨트롤러에 비해 다른 스폰 또는 스토리지보다 더 먼가?
                    # 컨트롤러부터의 실제 거리가 distance_to_controller 값 이하인가?

                    # 컨테이너와 컨트롤러간의 거리
                    controller_dist = \
                        len(stc.pos.findPathTo(chambro.controller, {'ignoreCreeps': True, 'range': 3}))
                    # 컨테이너에서 가장 가까운 스폰
                    closest_spawn = stc.pos.findClosestByPath(spawns, {'ignoreCreeps': True})
                    # 컨테이너에서 가장 가까운 스폰까지 거리
                    closest_spawn_dist = len(stc.pos.findPathTo(closest_spawn, {'ignoreCreeps': True}))
                    # 스토리지가 있으면 그 거리도 쟨다
                    closest_storage_dist = 1000
                    if room_storage:
                        closest_storage_dist = len(stc.pos.findPathTo(room_storage, {'ignoreCreeps': True}))
                    # 조건충족하면 업글용으로 분류 - 컨트롤러에서 distance_to_controller 이내 + 스폰과 스토리지보다 가깝
                    # 그리고 이 조건은 스토리지 지어질때까지 무시.
                    # print('container at x{}y{}, controller_dist {}, closest_spawn_dist {}, closest_storage_dist {}'
                    #       .format(stc.pos.x, stc.pos.y, controller_dist, closest_spawn_dist, closest_storage_dist))
                    if room_storage and controller_dist <= distance_to_controller and \
                            controller_dist < closest_storage_dist and controller_dist < closest_spawn_dist:
                        _upgrade = 1
                        print('x{}y{}에 {}, 업글컨테이너로 분류'.format(stc.pos.x, stc.pos.y, stc.id))
                chambro.memory[STRUCTURE_CONTAINER] \
                    .append({'id': stc.id, for_upgrade: _upgrade, for_harvest: _harvest})

        # todo 연구소
        # 연구소는 렙8 되기 전까지 건들지 않는다. 또한 모든 랩의 수가 10개여야만 찾는다.
        # if chambro.controller.level == 8 and len(chambro.memory[STRUCTURE_LAB]) == 0\
        #         or chambro.memory[options][reset]:
        #     yeongusoj = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_LAB)
        #     if len(yeongusoj) == 10:
        #         lab_list = []
        #         # 연구소는 크게 세종류가 존재한다.
        #         # 실제 작업용 연구소(1), 그 작업물을 받는 연구소(2), 크립업글을 위해 저장하는 연구소(3).
        #         # 여기서는 작업용과 작업물 받는 연구소 두 부류만이 중요하다.
        #         for y in yeongusoj:
        #             lab_jongryu = 1
        #             # 작업용 연구소는 주변 모든 연구소들과 2칸이내로 밀접해야 한다.
        #             for ys in yeongusoj:
        #                 if not y.pos.inRangeTo(ys, 2):
        #                     lab_jongryu = 2
        #                     break
        #             # 어떤 미네랄이 안에 있는거지?
        #             if y.mineralType:
        #                 mineral_jongryu = y.mineralType
        #             else:
        #                 mineral_jongryu = None
        #
        #             lab_info = {y.id: {lab_type: lab_jongryu, mineral_type: mineral_jongryu}}
        #             lab_list.append(lab_info)
        #
        #         # 3번종류의 연구소인지 확인한다.
        #         #
        #         if

    # 여기로 왔으면 내 방이 아닌거.
    else:
        # 방이 아닌 경우에 필요한 물건:
        # 1. 자원 위치. - 이미 있음
        # 2. 컨테이너 위치
        pass

    if Memory.debug or chambro.controller and chambro.controller.my and chambro.memory.options.reset:
        print('{}방 메모리에 건물현황 갱신하는데 {}CPU 소모'
              .format(chambro.name, round(Game.cpu.getUsed() - structure_cpu, 2)))
        chambro.memory.options.reset = 0
