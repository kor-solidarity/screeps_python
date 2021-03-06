from typing import List
from defs import *
import random
import miscellaneous
import pathfinding
from _custom_constants import *
from structure_display import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


# 스폰을 메인에서 쪼개기 위한 용도. 현재 어떻게 빼내야 하는지 감이 안잡혀서 공백임.
def run_spawn(all_objs, spawn: StructureSpawn, all_structures: List[Structure], constructions: List[ConstructionSite],
              room_creeps: List[Creep],
              hostile_creeps: List[Creep], divider, counter,
              cpu_bucket_emergency, cpu_bucket_emergency_spawn_start, extractor,
              terminal_capacity, chambro: Room, interval, wall_repairs, objs_for_display, min_hits):
    """


    :param all_objs:
    :param spawn:
    :param all_structures:
    :param constructions:
    :param room_creeps:
    :param hostile_creeps:
    :param divider:
    :param counter:
    :param cpu_bucket_emergency:
    :param cpu_bucket_emergency_spawn_start:
    :param extractor:
    :param terminal_capacity:
    :param chambro:
    :param interval:
    :param wall_repairs:
    :param objs_for_display:
    :param min_hits:
    :return:
    """

    memory = 'memory'
    room_level = spawn.room.controller.level

    # harvester 용 몸체 부위별 크기, 큰 순서, MOVE WORK CARRY size lvl 순
    # WORK SIZE: 8, 7, 5, 3, 2 순
    harvester_body = [8, 8, 8, 2, 8], [6, 7, 4, 2, 8], [3, 5, 1, 1, 0], [2, 3, 2, 1, 0], [1, 2, 1, 1, 0]

    # 위에 몸체 포문 돌릴때 쓰일 기본 구성순서.
    def_body_content = [MOVE, WORK, CARRY]

    spawn_cpu = Game.cpu.getUsed()
    # if spawn is not spawning, try and make one i guess.
    # spawning priority: harvester > hauler > upgrader > melee > etc.
    # checks every 10 + len(Game.spawns) ticks
    if not spawn.spawning and Game.time % counter == divider and chambro.energyAvailable >= 300:

        rand_int = random.randint(0, 99)
        # print('inside spawning check')
        spawn_chk_cpu = Game.cpu.getUsed()

        spawn_room_low = spawn.pos.roomName.lower()

        hostile_around = False
        # 적이 스폰 주변에 있으면 생산 안한다. 추후 수정해야함.

        if hostile_creeps:
            for enemy in hostile_creeps:
                if spawn.pos.inRangeTo(enemy, 2):
                    hostile_around = True
                    break
        if hostile_around and room_level == 8:
            return

        # ALL creeps you have
        creeps = Game.creeps

        # need each number of creeps by type. now all divided by assigned room.
        # assigned_room == 주 작업하는 방. remote 에서 작업하는 애들이면 그쪽으로 보내야함.
        # home_room == 원래 소속된 방. remote 에서 일하는 애들에나 필요할듯.

        creep_harvesters = _.filter(creeps, lambda c: (c.memory.role == 'harvester'
                                                       and c.memory.assigned_room == spawn.pos.roomName
                                                       and not c.memory.flag_name
                                                       and (c.spawning or c.ticksToLive > 80)))
        creep_haulers = _.filter(creeps, lambda c: (c.memory.role == 'hauler'
                                                    and c.memory.assigned_room == spawn.pos.roomName
                                                    and (c.spawning or c.ticksToLive > 100)))
        # todo 추후 추가요망.
        # creep_home_defenders = _.filter(creeps, lambda c: (c.memory.role == 'h_defender'
        #                                                    and c.memory.assigned_room == spawn.pos.roomName
        #                                                    and (c.spawning or
        #                                                         (c.ticksToLive > 200 and c.hits > c.hitsMax * .5)
        #                                                         )))
        creep_miners = _.filter(creeps, lambda c: (c.memory.role == 'miner'
                                                   and c.memory.assigned_room == spawn.pos.roomName
                                                   and (c.spawning or c.ticksToLive > 150)))
        creep_fixers = _.filter(creeps, lambda c: (c.memory.role == 'fixer'
                                                   and c.memory.assigned_room == spawn.pos.roomName
                                                   and (c.spawning or c.ticksToLive > 150)))

        creep_upgraders = _.filter(creeps, lambda c: (c.memory.role == 'upgrader'
                                                      and c.memory.assigned_room == spawn.pos.roomName
                                                      and (c.spawning or c.ticksToLive > 100)))

        # 배정된 허울러 기본값.
        hauler_quota = 1
        # 배정된 업글러 기본값.
        upgrader_quota = 0
        # 현재 혹시 방에서 건설중인 구조물 수
        num_of_constructions = len(spawn.room.find(FIND_CONSTRUCTION_SITES))

        # 크립의 누적 사이즈 2점당 hauler_quota 하나에 대응
        accumulated_size = 0
        for h in creep_haulers:
            accumulated_size += h.memory.size

        # if number of close containers/links are less than that of sources.
        harvest_carry_targets = []

        room_sources: List[Source] = spawn.room.find(FIND_SOURCES)
        # 소스를 따로 떼는 이유: 아래 합치는건 광부를 포함하는거지만 이 sources자체는 에너지 채취만 주관한다.
        num_o_sources = len(room_sources)
        if extractor and extractor.cooldown == 0:
            room_sources.append(extractor)

        containers_and_links = _.filter(all_structures, lambda st: st.structureType == STRUCTURE_CONTAINER
                                                                   or st.structureType == STRUCTURE_LINK)

        # 당장 가용한 에너지가 얼마나 있는가? 초렙 부활할때 활용할 목적.
        energy_at_hand = 0

        # 소스 주변에 자원채취용 컨테이너·링크가 얼마나 있는가 확인.
        for rs in room_sources:
            for s in containers_and_links:
                # 설정된 칸이내에 존재하는가?
                if s.structureType == STRUCTURE_CONTAINER and rs.pos.inRangeTo(s, max_range_to_container):
                    # 실제 거리도 그 이내인가?
                    if len(rs.pos.findPathTo(s, {'ignoreCreeps': True})) <= max_range_to_container:
                        # 여기까지 들어가있으면 요건충족한거.
                        harvest_carry_targets.append(s.id)
                        energy_at_hand += s.store.getCapacity(RESOURCE_ENERGY)
                        break
                elif s.structureType == STRUCTURE_LINK:
                    for m in chambro.memory[STRUCTURE_LINK]:
                        if s.id == m.id and not m.for_store:
                            harvest_carry_targets.append(s.id)
                            energy_at_hand += s.store.getCapacity(RESOURCE_ENERGY)
                            break
            # 소스 근처에 스토리지가 있으면 그것도 확인.
            if spawn.room.storage and len(rs.pos.findPathTo(spawn.room.storage, {'ignoreCreeps': True})) <= 5:
                harvest_carry_targets.append(spawn.room.storage.id)
                energy_at_hand += s.store.getCapacity(RESOURCE_ENERGY)

        if len(harvest_carry_targets) < num_o_sources:
            harvesters_bool = bool(len(creep_harvesters) < num_o_sources * 2)
        # if numbers of creep_harvesters are less than number of sources in the spawn's room.
        else:
            # to count the overall harvesting power. 3k or more == 2, else == 1
            harvester_points = 0

            for harvester_creep in creep_harvesters:
                # size scale:
                # 1 - small sized: 2 in each. regardless of actual capacity. for lvl 3 or less
                # 2 - real standards. suitable for 3k. 4500 not implmented yet.
                harvester_points += harvester_creep.memory.size
            # print('harvester_points', harvester_points)
            if harvester_points < num_o_sources * 2:
                harvesters_bool = True
            else:
                harvesters_bool = False
                # harvesters_bool = bool(len(creep_harvesters) < len(sources))

        # 허울러가 전혀 없는 상황에서 뽑아갈 자원이 있으면 허울러부터.
        if harvesters_bool and len(creep_haulers) == 0 and energy_at_hand >= 300:
            harvesters_bool = False

        if harvesters_bool:
            harvest_counter = 1
            # check if energy_source capacity is 4.5k(4k in case they update, not likely).
            # if is, go for size 4500.
            if room_sources[0].energyCapacity > 4000:
                harvest_counter = 0
            spawn_res = ERR_NOT_ENOUGH_ENERGY
            while spawn_res == ERR_NOT_ENOUGH_ENERGY and harvest_counter <= len(harvester_body) - 1:
                # 단, 만렙하베스터 뽑을 용량이 되는데 허울러가 존재하고 그걸 채울 양이 있으면 그 이하는 거른다.
                if harvest_counter > 1 and len(creep_haulers) and len(creep_harvesters) > 0 \
                        and chambro.energyCapacityAvailable >= 1200:
                    break
                # 두번째 애도 마찬가지.
                if harvest_counter > 2 and len(creep_haulers) \
                        and len(creep_harvesters) > 0 and chambro.energyCapacityAvailable >= 700:
                    break
                hv_body = []
                harvest_body_counter = 0
                # 위에 몸체목록중에 하나를 골라서 그 안에 있는 값대로 하나하나 몸을 구성한다.
                # 주석은 1이라고 가정하면 i 는 [8, 8, 8, 2, 8] 하나씩
                for i in harvester_body[harvest_counter]:
                    if harvest_body_counter < 3:
                        hv_body.extend([def_body_content[harvest_body_counter] for _ in range(i)])
                    harvest_body_counter += 1
                # print("harvester_body[{}]: {}".format(harvest_counter, harvester_body[harvest_counter]))
                spawn_res = spawn.spawnCreep(hv_body, 'hv_{}_{}'.format(spawn_room_low, rand_int),
                                             {memory: {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                                                       'size': harvester_body[harvest_counter][3],
                                                       'level': harvester_body[harvest_counter][4]}})
                harvest_counter += 1
            return

        # 꽉찬 컨테이너 수
        container_full = 0
        # 허울러가 추가로 필요한 경우는 꽉찬 컨테이너의 존재여부다. 2개까지 +1, 3개이상은 +2
        for mem_container in spawn.room.memory[STRUCTURE_CONTAINER]:
            # 업그레이드 용도면 안센다. 단 렙8미만일때만.
            if room_level < 8 and mem_container.for_upgrade:
                continue
            cont_obj: StructureContainer = Game.getObjectById(mem_container.id)
            if cont_obj and cont_obj.store.getUsedCapacity() == cont_obj.store.getCapacity():
                container_full += 1

        # 여기서부터 업글러와 허울러의 할당량을 계산한다.
        # 초대형 업글러 투입 고려
        mega_upgrader = False
        # 업글러 할당량 계산
        # 렙8인 경우는 세이프모드가 발동되는 상태를 유지하게끔만 한다.
        if room_level == 8:
            if spawn.room.controller.ticksToDowngrade < CONTROLLER_DOWNGRADE[8] - 100000 \
                    or (spawn.room.controller.ticksToDowngrade < CONTROLLER_DOWNGRADE[8] - 4900
                        and len(hostile_creeps) > 0):
                upgrader_quota = 1
        # 스토리지가 있으면 안에 에너지량이 절대적인 생성기준이 된다.
        elif spawn.room.storage:
            # 스토리지가 생기면 원칙적으로 스토리지 안 에너지 양 / expected_reserve 값으로 할당량 배정
            # 렙7 이면 9천부터 5천단위로 세자. 그 대신 큰애들로 뽑는다.
            if spawn.room.controller.level == 7 and spawn.room.storage.store.getUsedCapacity(RESOURCE_ENERGY) >= 9000:
                expected_reserve = 5000
                mega_upgrader = True
            else:
                expected_reserve = 3000

            # more than 3k
            if spawn.room.storage.store.getUsedCapacity(RESOURCE_ENERGY) >= expected_reserve:
                upgrader_quota = 1
                # extra upgrader every expected_reserve
                upgrader_quota += int(spawn.room.storage.store.getUsedCapacity(RESOURCE_ENERGY) / expected_reserve)
        # 여기로 넘어왔다는건 스토리지가 없는 상황.
        # 건설할게 있으면 무조건 생산 중단.
        elif num_of_constructions:
            upgrader_quota = 0
        # 방렙 4인데 여기로 왔다는건 스토리지 건설이 안됬다는소리임.
        # 이경우 스토리지 건설이 최우선이기에 업글쪽은 잠시 지양
        # 단, 적이 있는 경우는 예외. 이것도 세이프모드면 통과.
        elif room_level == 4 or len(hostile_creeps) and not chambro.controller.safeMode:
            upgrader_quota = 1
        # 렙4부터는 스토리지 건설이 최우선이기에 업글러 스폰에 총력가하면 망함...
        elif room_level < 4:
            # 저렙인 상태에선 레벨 + 1 값이 적당할거같음. 아직 확실하겐 모르겠음.
            upgrader_quota += room_level + 1

        # 만약 모든 컨테이너중 꽉찬게 하나라도 있으면 업글러 수를 추가해준다.
        if room_level < 8 and container_full:
            # 렙4에서 최우선은 스토리지다.
            if room_level == 4 and not spawn.room.storage:
                upgrader_quota += 1
            else:
                upgrader_quota += container_full * 5

        # 업글러 최대 수 제한.
        if upgrader_quota > 15:
            upgrader_quota = 15

        # 허울러 계산.
        # 컨테이너가 하나라도 꽉찬게 있으면 허울러 추가.
        # 단, 업글러를 뽑아야 하는 상황이면 통과. 건설장이 있으면 예외
        if container_full and upgrader_quota >= len(creep_upgraders):
            if container_full and container_full <= 2:
                hauler_quota += 1
            # 그게 셋 이상이면 둘 추가.
            elif container_full >= 3:
                hauler_quota += 2

        # 허울러 수 계산법: 방별로 지정된 허울러(기본값 1) + 위에 변수값
        # hauler_quota = extra_hauler_pts
        # minimum number of haulers in the room is 1, max 4.
        if hauler_quota <= 0:
            hauler_quota = 1
        elif hauler_quota > 4:
            hauler_quota = 4
        # 단, 초반 허울러가 전혀 필요없는 상황이면(컨테이너 등 적재소가 없으면) 뽑지 않는다
        if spawn.room.controller.level == 1 \
                and not (len(spawn.room.memory[STRUCTURE_CONTAINER])
                         or len(spawn.room.memory[STRUCTURE_LINK])
                         or spawn.room.storage):
            hauler_quota = 0

        if spawn.room.terminal:
            if spawn.room.terminal.store.energy > terminal_capacity + 10000:
                hauler_quota += 1

        # 일반적인 허울러 생산 조건: 방 내 허울러 누적 사이즈가 허울러 할당량을 채우지 못했을 시.
        multiplier = 2
        # todo 이 경우도 생각하긴 해야할거 같은데, 에너지 주변 공간이 부족해서 하나밖에 못캔다던가 등의 조건이 필요함
        # if spawn.room.controller.level < 4:
        #     multiplier = 1
        make_hauler = accumulated_size < hauler_quota * multiplier

        # 렙8이 아니면 허울러는 사이즈 누적 둘까지, 그 후 생산은 필요한 경우에도 업글러가 우선.
        if make_hauler and room_level < 8 and accumulated_size >= 2 and chambro.energyCapacityAvailable >= 400:
            # 업글러의 수가 실제 배정량보다 적으면 업글러부터 만들어야 하므로.
            if upgrader_quota > len(creep_upgraders):
                make_hauler = False

        # print('make_hauler', make_hauler,
        #       'hauler_quota', hauler_quota,
        #       'container_full', container_full,
        #       'accumulated_size', accumulated_size,
        #       'upgrader_quota', upgrader_quota,
        #       'mega_upgrader', mega_upgrader,
        #       'len(creep_upgraders)', len(creep_upgraders),
        #       'energyCapacityAvailable', chambro.energyCapacityAvailable)
        # if spawn.room.storage:
        #     print('storage.store.getUsedCapacity(RESOURCE_ENERGY)',
        #           spawn.room.storage.store.getUsedCapacity(RESOURCE_ENERGY))

        if make_hauler:
            # 순서는 무조건 아래와 같다. 무조건 덩치큰게 장땡.
            # 몸체 부위별 크기, 큰 순서, MOVE WORK CARRY size lvl 순
            # 1200, 800, 500, 250, 150, 100
            hauler_body = [15, 6, 24, 2, 8], \
                          [10, 4, 16, 2, 8], \
                          [7, 4, 10, 2, 4], \
                          [5, 4, 5, 1, 0], \
                          [3, 1, 3, 1, 0], \
                          [2, 1, 2, 1, 0]
            hl_body_counter = 1
            # 크립이 둘 이상이면 긴급으로 간주하고 대형허울러 생성.
            # 일반적으로는 두번째부터.
            if len(creep_haulers) >= 2:
                hl_body_counter = 0
            spawn_res = ERR_NOT_ENOUGH_ENERGY
            while spawn_res == ERR_NOT_ENOUGH_ENERGY and hl_body_counter <= len(hauler_body) - 1:
                hl_body = []
                hl_counter = 0
                hl_cost = 0
                # 위에 몸체목록중에 하나를 골라서 그 안에 있는 값대로 하나하나 몸을 구성한다.
                # 주석은 1이라고 가정하면 i 는 [10, 4, 16, 2, 8] 하나씩
                for i in hauler_body[hl_body_counter]:
                    if hl_counter < 3:
                        hl_body.extend([def_body_content[hl_counter] for _ in range(i)])
                        # 생산비용 계산
                        hl_cost += BODYPART_COST[def_body_content[hl_counter]] * i
                    hl_counter += 1

                # print("hl_body[{}]: {}, hl_cost: {}".format(hl_body_counter, hauler_body[hl_body_counter], hl_cost))
                # print("chambro.energyCapacityAvailable: {}".format(chambro.energyCapacityAvailable))
                # print('hauler_body[hl_body_counter({})][1] {}'
                #       .format(hl_body_counter, hauler_body[hl_body_counter][1]))
                # WORK 1 짜리는 에너지가 그다음 바디를 뽑을 수 있는 상황이 되면
                # 허울러가 전혀 없는게 아닌 한 뽑지 않는다.
                # 단, 1짜리만 뽑을 수 있는 상황이면(렙 3 이하 또는 창고가 없는 경우) 제외.
                # todo ^ this is a temporary solution.
                #
                # if hauler_body[hl_body_counter][1] == 1 \
                #         and chambro.energyCapacityAvailable > hl_cost \
                #         and len(creep_haulers) \
                #         and (chambro.controller.level > 4 or not chambro.storage):
                #     break
                spawn_res = spawn.spawnCreep(hl_body, 'hl_{}_{}'.format(spawn_room_low, rand_int),
                                             {memory: {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                                       'size': hauler_body[hl_body_counter][3],
                                                       'level': hauler_body[hl_body_counter][4]}})
                hl_body_counter += 1
            if not spawn_res == OK:
                print('hauler err', spawn_res)
            return

        # todo need one for ranged one too.
        # player_enemy = miscellaneous.filter_enemies(hostile_creeps, False)
        # if len(player_enemy) > 0 and len(creep_home_defenders) == 0:
        #     spawning_creep = spawn.createCreep(
        #         [ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK,
        #          ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK,
        #          ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK,
        #          ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK,
        #          MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE],
        #         undefined, {'role': 'h_defender', 'assigned_room': spawn.pos.roomName,
        #                     'level': 8})
        #     if not spawning_creep == ERR_NOT_ENOUGH_ENERGY:
        #         print('spawning_creep', spawning_creep)
        #         return

        # if there's an extractor, make a miner.
        if bool(extractor):
            if bool(len(creep_miners) == 0):

                minerals = chambro.find(FIND_MINERALS)
                if minerals[0].mineralAmount != 0 or minerals[0].ticksToRegeneration < 120:
                    # only one is needed
                    if len(creep_miners) > 0:
                        pass
                    # make a miner
                    else:
                        spawning_creep = spawn.spawnCreep(
                            [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                             WORK,
                             WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                             WORK,
                             WORK, WORK, CARRY],
                            'mn_{}_{}'.format(spawn_room_low, rand_int),
                            {memory: {'role': 'miner', 'assigned_room': spawn.pos.roomName, 'level': 5}})
                        if spawning_creep == ERR_NOT_ENOUGH_RESOURCES:
                            spawning_creep = spawn.spawnCreep(
                                [MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                 WORK,
                                 WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY],
                                'mn_{}_{}'.format(spawn_room_low, rand_int),
                                {memory: {'role': 'miner', 'assigned_room': spawn.pos.roomName}})

        # 업글러는 할당량을 채울때까지.
        if len(creep_upgraders) < upgrader_quota:
            # 업글러에 할당할 몸체. 이동 노동 운반 레벨.
            # 뒤로 갈수록 작아지는걸로. 총 7개. 마지막이 렙8때꺼.
            upgrader_body = [13, 20, 6, 7], \
                            [10, 10, 6, 6], \
                            [6, 6, 5, 5], \
                            [3, 4, 2, 0], \
                            [3, 3, 2, 0], \
                            [2, 2, 2, 0], \
                            [1, 1, 1, 0]
            spawn_res = ERR_NOT_ENOUGH_ENERGY
            # 위에 몇번째 몸체를 쓸꺼냐를 결정
            upg_body_counter = 1
            if mega_upgrader:
                upg_body_counter = 0

            while spawn_res == ERR_NOT_ENOUGH_ENERGY and upg_body_counter < 6:
                # 렙8인 경우는 세이프모드가 발동되는 상태를 유지하게끔만 한다.
                if room_level == 8:
                    upg_body_counter = len(upgrader_body) - 1
                upg_body = []
                upg_content_counter = 0
                # 위에 몸체목록중에 하나를 골라서 그 안에 있는 값대로 하나하나 몸을 구성한다.
                # 주석은 1이라고 가정하면 i 는 [10, 10, 6, 7] 하나씩
                for i in upgrader_body[upg_body_counter]:
                    # 워크 2짜리는 3 뽑을 수 있으면 손절.
                    if room_level < 8 and upg_body_counter > 4 and chambro.energyCapacityAvailable >= 550:
                        break

                    if upg_content_counter < 3:
                        upg_body.extend([def_body_content[upg_content_counter] for j in range(i)])
                    upg_content_counter += 1
                # print("upg_body[{}]: {}".format(upg_body_counter, upgrader_body[upg_body_counter]))
                spawn_res = spawn.spawnCreep(upg_body, 'up_{}_{}'.format(spawn_room_low, rand_int),
                                             {memory: {'role': 'upgrader', 'assigned_room': spawn.pos.roomName,
                                                       'level': upgrader_body[upg_body_counter][3]}})
                upg_body_counter += 1
            if not spawn_res == OK and not spawn_res == ERR_NOT_ENOUGH_ENERGY:
                print('ERROR ON spawning upgrader', spawn_res)

        # 초기화 목적.
        if not chambro.memory[options][stop_fixer]:
            chambro.memory[options][stop_fixer] = 1

        # 수리가 필요한 건물이 발견되고 나서 경과한 시간. 뒤에 긴 공식 간소화 목적
        elapsed_fixer_time = Game.time - chambro.memory[options][stop_fixer]

        # 수리할게 있거나 렙 7 이상일때부터 수리병을 부름. 7때는 단지 하나. 8때는 5천에 하나.
        # 그리고 할당량 다 찼는데도 뽑는 경우도 있을 수 있으니 타이머 쟨다.
        # 수리할게 더 없으면 500틱동안 추가 생산을 안한다.
        if elapsed_fixer_time > 500 and len(wall_repairs) and chambro.storage and room_level >= 4 \
                and chambro.storage.store.getUsedCapacity(RESOURCE_ENERGY) >= 5000:

            make_mini = False
            # 원칙적으로는 렙 7부터 본격적으로 생산한다. 그 이하면 소형만 생산.
            if room_level < 7:
                make_mini = True

            max_num_fixers = 0

            # 방 에너지가 반토막인 상태면 스폰 중지
            if chambro.energyAvailable < chambro.energyCapacityAvailable / 2:
                pass

            # 렙8부터 본격적인 작업에 드간다. 그전까진 무의미.
            # 또한 수리할게 더 없는 상황에서 첫 생성을 한거면 하나만 뽑고 천틱 대기한다.
            elif room_level < 8 and (
                    10000 <= chambro.storage.store.getUsedCapacity(RESOURCE_ENERGY) or elapsed_fixer_time <= 2000):
                max_num_fixers = 1

            # 벽수리가 중심인데 수리할 벽이 없으면 의미가 없음.
            elif room_level == 8 and min_hits < chambro.memory[options][repair]:
                # 스토리지에 에너지가 3만 이하면 1로 제한.
                # CPU bucket 부족인 상황에도 적용
                if chambro.storage.store.getUsedCapacity(RESOURCE_ENERGY) < 30000 \
                        or cpu_bucket_emergency > Game.cpu.bucket:
                    max_num_fixers = 1
                # 그 이상인 경우 수리대상 벽 20개당 하나로 제한한다
                # 수리대상 10개당 하나 vs elapsed_fixer_time // 2k vs 스토리지 에너지양 / 3만의 정수
                # 셋중 가장 적은걸로 결정
                else:
                    storage_dividend = int(chambro.storage.store.getUsedCapacity(RESOURCE_ENERGY) / 50000)
                    elapsed_fixer_dividend = int(elapsed_fixer_time / 2000) + 1
                    # dividend_by_repairs = len(wall_repairs) // 10
                    max_num_fixers = _.min([storage_dividend, elapsed_fixer_dividend])

                # 최대값. 임시조치임.
                if max_num_fixers > 5:
                    max_num_fixers = 5
                elif not max_num_fixers:
                    max_num_fixers = 1
            if len(creep_fixers) < max_num_fixers:
                body_structure = {'body': [], 'level': 0}
                # 몸체·렙 구성
                fixer_body = [16, 25, 7, 8]
                if make_mini:
                    fixer_body = [6, 9, 2, 0]
                counter = 0
                for i in fixer_body:
                    if counter < 3:
                        body_structure['body'].extend([def_body_content[counter] for i in range(fixer_body[counter])])
                    else:
                        body_structure['level'] = fixer_body[counter]
                    counter += 1
                spawn_res = spawn.spawnCreep(body_structure['body'], 'fx_{}_{}'.format(spawn_room_low, rand_int),
                                             {memory: {'role': 'fixer', 'assigned_room': spawn.pos.roomName,
                                                       'level': body_structure['level']}})
        if Memory.debug and Game.time % interval == 0:
            print("이 시점까지 스폰 {} 소모량: {}, 이하 remote"
                  .format(spawn.name, round(Game.cpu.getUsed() - spawn_cpu, 2)))

        # REMOTE---------------------------------------------------------------------------
        # ALL remotes.
        flags = Game.flags
        """
        완성될 시 절차:
        - 깃발을 다 둘러본다.
        - 자기소속 깃발이 있을 경우 (W1E2-rm) 옵션에 넣는다. 
            + 각종 기본값을 설정한다.
                + 넣을때 기본값으로 주둔시킬 병사 수를 지정한다. 디폴트 0
                + 도로를 또 깔것인가? 길따라 깐다. 디폴트 0 
            + 모든 컨트롤러 있는 방 루프돌려서 이미 소속된 다른방이 있으면 그거 지운다. 
            + 넣고나서 깃발 지운다. 
        - 추후 특정 이름이 들어간 깃발은 명령어대로 하고 삭제한다. 

        """
        # todo 이거 따로 떼내야함.
        # 메모리화 절차
        for flag_name in Object.keys(flags):
            # 해당 플래그 오브젝트. flag_name 은 말그대로 이름뿐임.
            flag_obj = flags[flag_name]
            # 해당 깃발이 내 소속 방에 있는건지 확인
            controlled = False
            if flag_obj.room and flag_obj.room.controller and flag_obj.room.controller.my:
                controlled = True

            # 깃발 명령어 쪼개는데 필요함.
            name_list = flag_name.split()

            # 포문 끝나고 깃발 삭제할지 확인...
            delete_flag = False
            # 깃발이 있는 방이름.
            flag_room_name = flag_obj.pos.roomName

            # 건물 건설 지정.
            if flag_name.includes(STRUCTURE_LINK) or flag_name.includes(STRUCTURE_CONTAINER) \
                    or flag_name.includes(STRUCTURE_SPAWN) or flag_name.includes(STRUCTURE_EXTENSION) \
                    or flag_name.includes(STRUCTURE_ROAD) or flag_name.includes(STRUCTURE_STORAGE) \
                    or flag_name.includes(STRUCTURE_RAMPART) or flag_name.includes(STRUCTURE_EXTRACTOR):
                # todo 미완성임. -del 하고 섞일 수 있음.
                bld_type = name_list[0]
                # 링크용일 경우.
                if bld_type == STRUCTURE_LINK:
                    bld_plan = flag_obj.room.createConstructionSite(flag_obj.pos, STRUCTURE_LINK)
                # 컨테이너
                elif bld_type == STRUCTURE_CONTAINER:
                    bld_plan = flag_obj.room.createConstructionSite(flag_obj.pos, STRUCTURE_LINK)
                # 스폰
                elif bld_type == STRUCTURE_SPAWN:
                    bld_plan = flag_obj.room.createConstructionSite(flag_obj.pos, STRUCTURE_SPAWN)
                # 익스텐션
                elif bld_type == STRUCTURE_EXTENSION:
                    bld_plan = flag_obj.room.createConstructionSite(flag_obj.pos, STRUCTURE_EXTENSION)
                # storage
                elif bld_type == STRUCTURE_STORAGE:
                    bld_plan = flag_obj.room.createConstructionSite(flag_obj.pos, STRUCTURE_STORAGE)
                # todo 도로랑 램파트는 한번에 쭉 연결하는게 가능함. 그걸 확인해보자.

                print(bld_plan, bld_type)
                # 건설할 건물이 레벨부족 또는 한도초과로 못놓는 경우.
                if bld_plan == ERR_RCL_NOT_ENOUGH or bld_plan == ERR_FULL:
                    # 건설용 메모리 초기화
                    if not chambro.memory.bld_plan:
                        chambro.memory.bld_plan = []
                    # 내 방이 아닌 경우 그냥 삭제.
                    # todo 멀티방이면 어찌할거임?
                    if bld_plan == ERR_RCL_NOT_ENOUGH and not controlled:
                        print('the {} cannot be built in {} - not controlled.'.format(bld_type, flag_obj.pos.roomName))
                    else:
                        print('added bld')
                        # json to put into the bld_plan memory
                        blds = {'type': bld_type, 'pos': flag_obj.pos}
                        chambro.memory.bld_plan.append(blds)

                # 건설이 불가한 경우.
                elif bld_plan == ERR_INVALID_TARGET or bld_plan == ERR_INVALID_ARGS:
                    print('building plan at {}x{}y is wrong: {}'.format(flag_obj.pos.x, flag_obj.pos.y, bld_plan))

                delete_flag = True

            # 방이름/방향 + -rm + 아무글자(없어도됨) << 방을 등록한다.
            if flag_name.find(spawn.room.name) > -1 and flag_name.find('-rm') > -1:
                # 방이름 외 그냥 바로 위라던지 정도의 확인절차
                # wasd 시스템(?) 사용
                rm_loc = name_list.index('-rm')
                target_room = name_list[rm_loc - 1]
                # todo 방향 아직 안찍음
                # 여기에 안뜨면 당연 방이름이 아니라 상대적 위치를 찍은거.
                # if not Game.rooms[target_room]:

                print('-rm')
                # init. remote
                if not Memory.rooms[spawn.room.name].options.remotes:
                    Memory.rooms[spawn.room.name].options.remotes = {}

                # 혹시 다른방에 이 방이 이미 소속돼있는지도 확인한다. 있으면 없앤다.
                for i in Object.keys(Memory.rooms):
                    # 같은방은 건들면 안됨...
                    if i == spawn.room.name:
                        continue
                    found_and_deleted = False
                    if Memory.rooms[i].options:
                        if Memory.rooms[i].options.remotes:
                            # for_num = 0
                            for r in Object.keys(Memory.rooms[i].options.remotes):
                                if r == flag_obj.pos.roomName:
                                    del Memory.rooms[i].options.remotes[r]
                                    # print('del')
                                    found_and_deleted = True
                                    break
                                # for_num += 1
                    if found_and_deleted:
                        break
                # 방이 추가됐는지에 대한 불리언.
                room_added = False
                # 이미 방이 있는지 확인한다.
                for r in Object.keys(Memory.rooms[spawn.room.name].options.remotes):
                    # 있으면 굳이 또 추가할 필요가 없음..
                    if r.roomName == flag_obj.pos.roomName:
                        room_added = True
                        break
                print('room added?', room_added)
                # 추가가 안된 상태면 초기화를 진행
                if not room_added:
                    print('what??')
                    # init = {'roomName': Game.flag_obj.pos.roomName, 'defenders': 1, 'initRoad': 0,
                    #         'display': {'x': Game.flag_obj.pos.x, 'y': Game.flag_obj.pos.y}}
                    init = {'defenders': 1, 'initRoad': 0,
                            'display': {'x': flag_obj.pos.x,
                                        'y': flag_obj.pos.y}}
                    Memory.rooms[spawn.room.name][options][remotes][flag_obj.pos.roomName] = init
                    # Memory.rooms[spawn.room.name][options][remotes].update({flag_obj.pos.roomName: init})
                    print('Memory.rooms[{}][options][remotes][{}]'.format(spawn.room.name,
                                                                          flag_obj.pos.roomName),
                          JSON.stringify(Memory.rooms[spawn.room.name][options][remotes][flag_obj
                                         .pos.roomName]))

                delete_flag = True

            # 주둔할 병사 수 재정의
            if flag_name.find('-def') > -1:
                print("-def")
                number_added = False
                included = name_list.index('-def')
                # 초기화
                number = 0
                # 트라이에 걸린다는건 숫자 빼먹었거나 숫자가 아니라는거.
                try:
                    number = int(name_list[included + 1])
                    number_added = True
                except:
                    print("error for flag {}: no number for -def".format(flag_name))

                if number_added:
                    # 방을 돌린다.
                    for i in Object.keys(Memory.rooms):
                        found = False
                        # 같은방을 찾으면 병사정보를 수정한다.
                        if Memory.rooms[i].options and Memory.rooms[i].options.remotes:
                            for r in Object.keys(Memory.rooms[i].options.remotes):
                                if r == flag_room_name:
                                    Memory.rooms[i].options.remotes[r][defenders] = number
                                    found = True
                        if found:
                            break
                delete_flag = True

            # 방의 수리단계 설정.
            if flag_name.find('-rp') > -1:
                print("'-rp')")

                # 내 방이 아니면 이걸 돌리는 이유가없음....
                if controlled:
                    included = name_list.index('-rp')
                    # 트라이에 걸린다는건 숫자 빼먹었거나 숫자가 아니라는거.
                    try:
                        number = name_list[included + 1]
                        number = int(number)
                        print('repair', number)
                    except:
                        print("error for flag {}: no number for -rp".format(flag_name))
                    # 설정 끝.
                    flag_obj.room.memory.options.repair = number
                    delete_flag = True

            # 방의 운송크립수 설정.
            if flag_name.find('-hl') > -1:

                # 내 방이 아니면 이걸 돌리는 이유가없음....
                if controlled:
                    included = name_list.index('-hl')
                    # 트라이에 걸린다는건 숫자 빼먹었거나 숫자가 아니라는거.
                    try:
                        number = name_list[included + 1]
                        number = int(number)
                    except:
                        print("error for flag {}: no number for -hl".format(flag_name))
                    # 설정 끝.
                    flag_obj.room.memory.options.haulers = number
                    delete_flag = True

            # 방 안에 미네랄 채취 시작
            if flag_name.find('-mine') > -1:
                print('-mine')
                # todo 키퍼방일 경우 추가요망. 현재는 내방만.

                if controlled:
                    mineral_loc = flag_obj.room.find(FIND_MINERALS)[0]
                    # 엑스트랙터 생성
                    mineral_loc.pos.createConstructionSite(STRUCTURE_EXTRACTOR)

                    road_to_spawn = mineral_loc.pos.findPathTo(spawn, {'ignoreCreeps': True})
                    road_len = len(road_to_spawn)
                    counter = 0
                    # 줄따라 놓기
                    for s in road_to_spawn:
                        if counter == 0 or counter == road_len:
                            pass
                        elif counter == 1:
                            posi = __new__(RoomPosition(s.x, s.y, flag_obj.room.name))
                            posi.createConstructionSite(STRUCTURE_CONTAINER)
                        else:
                            posi = __new__(RoomPosition(s.x, s.y, flag_obj.room.name))
                            posi.createConstructionSite(STRUCTURE_ROAD)
                        counter += 1
                delete_flag = True

            # 방내 설정값 표기.
            if flag_name.find('-dsp') > -1:
                print("'-dsp')")

                if not controlled:
                    # 리모트 소속방 찾는다.
                    for chambra_nomo in Object.keys(Game.rooms):
                        set_loc = False
                        if Memory.rooms[chambra_nomo].options:
                            # counter_num = 0

                            for r in Object.keys(Memory.rooms[chambra_nomo].options.remotes):
                                remote_room_name = r
                                # 방이름 이거랑 똑같은지.
                                # 안똑같으면 통과
                                if remote_room_name != flag_obj.pos.roomName:
                                    print('{} != flags[{}].pos.roomName {}'
                                          .format(remote_room_name, flag_name, flag_obj.pos.roomName))
                                    pass
                                else:
                                    print('Memory.rooms[chambra_nomo].options.remotes[counter_num].display'
                                          , Memory.rooms[chambra_nomo].options.remotes[r].display)
                                    if not Memory.rooms[chambra_nomo].options.remotes[r].display:
                                        Memory.rooms[chambra_nomo].options.remotes[r].display = {}
                                    rx = flag_obj.pos.x
                                    ry = flag_obj.pos.y
                                    Memory.rooms[chambra_nomo].options.remotes[r].display.x = rx
                                    Memory.rooms[chambra_nomo].options.remotes[r].display.y = ry
                                    set_loc = True
                                # counter_num += 1
                        if set_loc:
                            break

                # 내 방이 아니면 이걸 돌리는 이유가없음....
                if controlled:
                    # 만일 비어있으면 값 초기화.
                    if not flag_obj.room.memory.options.display:
                        flag_obj.room.memory.options.display = {}
                    # 깃발꽂힌 위치값 등록.
                    print('flagpos {}, {}'.format(flag_obj.pos.x, flag_obj.pos.y))
                    flag_obj.room.memory.options.display['x'] = flag_obj.pos.x
                    flag_obj.room.memory.options.display['y'] = flag_obj.pos.y
                    print('flags[{}].room.memory.options.display {}'
                          .format(flag_name, flag_obj.room.memory.options.display))

                delete_flag = True

            # 방 내 핵채우기 트리거. 예·아니오 토글
            if flag_name.find('-fln') > -1:
                delete_flag = True

                if controlled:
                    if flag_obj.room.memory.options.fill_nuke == 1:
                        flag_obj.room.memory.options.fill_nuke = 0
                    elif flag_obj.room.memory.options.fill_nuke == 0:
                        flag_obj.room.memory.options.fill_nuke = 1
                    else:
                        flag_obj.room.memory.options.fill_nuke = 0

            # 방 내 연구소 채우기 트리거. 예·아니오 토글
            if flag_name.find('-fll') > -1:
                delete_flag = True

                if controlled:
                    if flag_obj.room.memory.options.fill_labs == 1:
                        flag_obj.room.memory.options.fill_labs = 0
                    elif flag_obj.room.memory.options.fill_labs == 0:
                        flag_obj.room.memory.options.fill_labs = 1
                    else:
                        flag_obj.room.memory.options.fill_labs = 0

            # 램파트 토글.
            if flag_name.find('-ram') > -1:

                # 내 방이 아니면 이걸 돌리는 이유가없음....
                if controlled:
                    # 램파트가 열렸는가?
                    if flag_obj.room.memory.options.ramparts_open == 1:
                        # 그럼 닫는다.
                        flag_obj.room.memory.options.ramparts = 2
                    # 그럼 닫힘?
                    elif flag_obj.room.memory.options.ramparts_open == 0:
                        # 열어
                        flag_obj.room.memory.options.ramparts = 1
                    delete_flag = True

            # 타워공격 토글.
            if flag_name.find('-tow') > -1:
                # 내 방이 아니면 이걸 돌리는 이유가없음....
                if controlled:
                    if flag_obj.room.memory.options.tow_atk == 1:
                        flag_obj.room.memory.options.tow_atk = 0
                    else:
                        flag_obj.room.memory.options.tow_atk = 1
                    delete_flag = True

            # 디스플레이 제거. 쓸일은 없을듯 솔까.
            if flag_name.find('-dsprm') > -1:

                # 내 방이 아니면 이걸 돌리는 이유가없음....
                if controlled:
                    # 깃발꽂힌 위치값 제거.
                    flag_obj.room.memory.options.display = {}
                    delete_flag = True

            # 방 안 건설장 다 삭제..
            if flag_name.find('-clr') > -1:
                print("('-clr')")
                # cons = Game.flag_obj.room.find(FIND_CONSTRUCTION_SITES)
                world_const = Game.constructionSites
                for c in Object.keys(world_const):
                    obj = Game.getObjectById(c)
                    if obj.pos.roomName == flag_room_name:
                        obj.remove()
                # 원하는거 찾았으면 더 할 이유가 없으니.
                if found:
                    break
                delete_flag = True

            # remote 배정된 방 삭제조치. 자기 방에서 했을 경우 해당 위치에 배정된 건물을 지운다.
            if flag_name.find('-del') > -1:
                print("'-del')")
                # 자기 방으로 찍었을 경우 찍은 위치에 뭐가 있는지 확인하고 그걸 없앤다.
                if flag_obj.room and flag_obj.room.controller and flag_obj.room.controller.my:
                    print('my room at {}'.format(flag_obj.room.name))
                    # 해당 위치에 건설장 또는 건물이 있으면 없앤다.
                    if len(flag_obj.pos.lookFor(LOOK_CONSTRUCTION_SITES)):
                        print(flag_obj.pos.lookFor(LOOK_CONSTRUCTION_SITES), JSON.stringify())
                        del_res = flag_obj.pos.lookFor(LOOK_CONSTRUCTION_SITES)[0].remove()
                    elif len(flag_obj.pos.lookFor(LOOK_STRUCTURES)):
                        del_res = flag_obj.pos.lookFor(LOOK_STRUCTURES)[0].destroy()
                    # 만약 건물도 건설장도 없으면 해당 위치에 배정된 건설 메모리가 있나 찾아본다
                    elif chambro.memory.bld_plan:
                        num = 0
                        for plan in chambro.memory.bld_plan:
                            if JSON.stringify(plan.pos) == JSON.stringify(flag_obj.pos):
                                chambro.memory.bld_plan.splice(num, 1)
                                print('deleted!')
                            num += 1
                # if its remote room
                else:
                    # 방을 돌린다.
                    for i in Object.keys(Memory.rooms):
                        found = False
                        if Memory.rooms[i].options:
                            print('Memory.rooms[{}].options.remotes {}'.format(i, JSON.stringify(
                                Memory.rooms[i].options.remotes)))
                            print('len(Memory.rooms[{}].options.remotes) {}'.format(i, len(
                                Memory.rooms[i].options.remotes)))
                            # 옵션안에 리모트가 없을수도 있음.. 특히 확장 안했을때.
                            if len(Memory.rooms[i].options.remotes) > 0:
                                # 리모트 안에 배정된 방이 있는지 확인한다.
                                # 아래 포문에 씀.
                                del_number = 0
                                for r in Object.keys(Memory.rooms[i].options.remotes):
                                    print('r', r, 'flag_room_name', flag_room_name)
                                    # 배정된 방을 찾으면 이제 방정보 싹 다 날린다.
                                    if r == flag_room_name:
                                        # del_number = r  # Memory.rooms[i].options.remotes[r]
                                        print('deleting roomInfo Memory.rooms[{}].options.remotes[{}]'
                                              .format(i, r), 'del_number', del_number)
                                        # Memory.rooms[i].options.remotes.splice(del_number, 1)
                                        del Memory.rooms[i].options.remotes[r]
                                        found = True
                                        # 방에 짓고있는것도 다 취소
                                        world_const = Game.constructionSites
                                        for c in Object.keys(world_const):
                                            obj = Game.getObjectById(c)
                                            if obj.pos.roomName == flag_room_name:
                                                obj.remove()
                                        # if Game.flag_obj.room:
                                        #     cons = Game.flag_obj.room.find(FIND_CONSTRUCTION_SITES)
                                        #     for c in cons:
                                        #         c.remove()
                                        break
                                    del_number += 1
                        # 원하는거 찾았으면 더 할 이유가 없으니.
                        if found:
                            break
                delete_flag = True

            # 방 안에 건물확인 스크립트 초기화 조치
            if flag_name.find('-rset') > -1:
                print("resetting")
                if controlled:
                    chambro.memory[options][reset] = 1
                else:
                    print(flag_obj.room.name, '은 내 방이 아님.')
                delete_flag = True

            if delete_flag:
                aa = flag_obj.remove()
                print('delete {}: {}'.format(flag_obj, aa))

        # 이하 진짜 리모트-------------------------------------------------

        # 렙3 아래면 그냥 무시
        if room_level < 3:
            return

        # todo 메모리 떼내야함...
        # print('level', level)
        if len(Memory.rooms[spawn.room.name].options.remotes) > 0:
            # 깃발로 돌렸던걸 메모리로 돌린다.
            for r in Object.keys(Memory.rooms[spawn.room.name].options.remotes):
                # 뒤에 점없는게 필요해서...
                room_name = r
                room_name_low = room_name.lower()
                # if seeing the room is False - need to be scouted
                # if not Game.flags[flag].room:
                if not Game.rooms[room_name]:
                    # look for scouts
                    creep_scouts = _.filter(creeps, lambda c: c.memory.role == 'scout'
                                                              and c.memory.assigned_room == room_name)
                    if len(creep_scouts) < 1:
                        spawn_res = spawn.spawnCreep([MOVE], 'sc_{}_{}'.format(room_name, rand_int),
                                                     {memory: {'role': 'scout', 'assigned_room': room_name}})
                        break
                else:
                    # find creeps with assigned flag. find troops first.
                    remote_troops = _.filter(creeps, lambda c: c.memory.role == 'soldier'
                                                               and c.memory.assigned_room == room_name
                                                               and (c.spawning or (c.hits > c.hitsMax * .6
                                                                                   and c.ticksToLive > 300)))

                    hostiles = Game.rooms[room_name].find(FIND_HOSTILE_CREEPS)

                    # 원래 더 아래에 있었지만 키퍼방 문제가 있는지라...
                    # flag_structures = Game.rooms[room_name].find(FIND_STRUCTURES)
                    flag_structures = all_objs[room_name].all_structures

                    keeper_lair = False
                    if Game.rooms[room_name].memory[STRUCTURE_KEEPER_LAIR] \
                            and len(Game.rooms[room_name].memory[STRUCTURE_KEEPER_LAIR]):
                        keeper_lair = True
                    # 방에 컨트롤러가 없는 경우 가정.
                    flag_room_controller = Game.rooms[room_name].controller
                    flag_room_reserved_by_other = False

                    # 컨트롤러가 있는가?
                    if flag_room_controller:
                        # 있다면...
                        # 주인이 존재하고 내것이 아닌가?
                        if flag_room_controller.owner and not flag_room_controller.my:
                            # 이 경우는 나중에 생각.
                            pass
                        # 예약이 돼있는가?
                        elif flag_room_controller.reservation:
                            # 내가 예약한것이 아닌가?
                            if not flag_room_controller.reservation.username \
                                   == spawn.owner.username:
                                flag_room_reserved_by_other = True

                    #  렙 7부터 항시 상주한다. 단, 설정에 따라 투입자체를 안할수도 있게끔 해야함.
                    # to filter out the allies.
                    # if len(hostiles) > 0:
                    stationed_defenders = Memory.rooms[spawn.room.name].options.remotes[r].defenders
                    # 플러스가 있는 경우 병사가 상주중이므로 NPC 셀 필요가 없다.
                    if stationed_defenders:
                        hostiles = miscellaneous.filter_friend_foe(hostiles)[2]
                    else:
                        hostiles = miscellaneous.filter_friend_foe(hostiles)[0]
                    # 적이 있거나 방이 만렙이고 상주인원이 없을 시.
                    # todo 렙 4 아래면 ?
                    if len(hostiles) + stationed_defenders > len(remote_troops) \
                            or (len(remote_troops) < stationed_defenders and room_level == 8):
                        spawn_res = ERR_NOT_ENOUGH_RESOURCES
                        # second one is the BIG GUY. made in case invader's too strong.
                        # 임시로 0으로 놨음. 구조 자체를 뜯어고쳐야함.
                        # 원래 두 크립이 연동하는거지만 한번 없이 해보자.
                        if len(remote_troops) < len(hostiles) + stationed_defenders and not keeper_lair:
                            # 저렙이면 소형으로 뗀다.
                            if room_level < 5:
                                spawn_res = spawn.spawnCreep(
                                    [MOVE, MOVE, MOVE, MOVE, MOVE, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     HEAL],
                                    'df_{}_{}'.format(room_name_low, rand_int),
                                    {memory: {'role': 'soldier', 'soldier': 'remote_defender',
                                              'assigned_room': room_name, 'home_room': spawn.pos.roomName}})
                            else:
                                spawn_res = spawn.spawnCreep(
                                    [TOUGH, TOUGH, TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                     MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                     MOVE, MOVE, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, HEAL, HEAL, HEAL],
                                    'df_{}_{}'.format(room_name_low, rand_int),
                                    {memory: {'role': 'soldier', 'soldier': 'remote_defender',
                                              'assigned_room': room_name, 'home_room': spawn.pos.roomName}})
                                if spawn_res != OK:
                                    spawn_res = spawn.spawnCreep(
                                        [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, RANGED_ATTACK, RANGED_ATTACK,
                                         RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, HEAL, HEAL],
                                        'df_{}_{}'.format(room_name_low, rand_int),
                                        {memory: {'role': 'soldier', 'soldier': 'remote_defender',
                                                  'assigned_room': room_name, 'home_room': spawn.pos.roomName}})
                        elif keeper_lair and (
                                len(remote_troops) == 0 or len(remote_troops) < len(
                            hostiles) + stationed_defenders):
                            spawn_res = spawn.spawnCreep(
                                # think this is too much for mere invaders
                                [TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE
                                    , MOVE,
                                 MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE
                                    , MOVE,
                                 MOVE, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                 RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                 RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                 RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                 RANGED_ATTACK, HEAL, HEAL, HEAL],
                                'df_{}_{}'.format(room_name_low, rand_int),
                                {memory: {'role': 'soldier', 'soldier': 'remote_defender',
                                          'assigned_room': room_name, 'home_room': spawn.pos.roomName}})
                        return
                        # if spawn_res == OK:
                        #     return
                        # elif spawn_res == ERR_NOT_ENOUGH_RESOURCES:
                        #     pass

                    # 방 안에 적이 있으면 방위병이 생길때까지 생산을 하지 않는다.
                    if len(hostiles) > 0:
                        not_spawning_troops = remote_troops.filter(lambda c: not c.spawning)
                        if not_spawning_troops:
                            pass
                        else:
                            continue

                    # 1. 리서버를 먼저 생산한다. 2. 컨트롤러 예약이 다른 플레이어에 의해 먹혔을 시 대응방안
                    # find creeps with assigned flag.
                    # exclude creeps with less than 100 life ticks so the new guy can be replaced right away
                    remote_harvesters = _.filter(creeps, lambda c: c.memory.role == 'harvester'
                                                                   and c.memory.assigned_room == room_name
                                                                   and (c.spawning or c.ticksToLive > 150))
                    remote_reservers = _.filter(creeps, lambda c: c.memory.role == 'reserver'
                                                                  and c.memory.assigned_room == room_name)
                    # 멀티지역에 만일 인베이더 건물 출몰할 시에 대한 대응방안.
                    remote_guard = _.filter(creeps, lambda c: c.memory.role == 'k_guard'
                                                              and c.memory.assigned_room == room_name
                                                              and (c.spawning or c.ticksToLive > 250))
                    # resources in flag's room
                    # 멀티에 소스가 여럿일 경우 둘을 스폰할 필요가 있다.
                    flag_energy_sources: List[Source] = Game.rooms[room_name].find(FIND_SOURCES)
                    # print('flag_energy_sources', flag_energy_sources)
                    flag_containers: List[Optional[StructureContainer, ConstructionSite]] = \
                        _.filter(flag_structures, lambda s: s.structureType == STRUCTURE_CONTAINER)
                    # 실제로 만들어져 있는 컨테이너. flag_containers 는 건설중인 컨테이너도 포함.
                    flag_built_containers: List[StructureContainer] = _.clone(flag_containers)

                    flag_lairs = _.filter(flag_structures,
                                          lambda s: s.structureType == STRUCTURE_KEEPER_LAIR)
                    flag_mineral = Game.rooms[room_name].find(FIND_MINERALS)
                    # flag_constructions = Game.rooms[room_name].find(FIND_CONSTRUCTION_SITES)
                    flag_constructions = all_objs[room_name].all_constructions

                    flag_containers_const = flag_constructions.filter(lambda s: s.structureType == STRUCTURE_CONTAINER)

                    flag_containers.extend(flag_containers_const)
                    # 컨트롤러가 있고 남의 소유이거나 예약점수가 100 이하일 경우.
                    # 리서버를 하나 파견한다.
                    # if flag_room_controller and len(remote_reservers) == 0 or \
                    #         flag_room_reserved_by_other and flag_room_controller.reservation.ticksToEnd < 100:
                    # print("flag_room_controller", flag_room_controller, 'len(remote_reservers)', len(remote_reservers),
                    #       chambro.name, 'energyCapacityAvailable', chambro.energyCapacityAvailable)
                    # 리서버 확인요령:
                    if flag_room_controller and len(remote_reservers) == 0 and chambro.energyCapacityAvailable >= 1300:
                        # (flag_room_reserved_by_other and flag_room_controller.reservation.ticksToEnd < 100) and \
                        # 본진렙 7이면 최소한의 유지만.
                        if room_level < 7:
                            reserve_cap = 400
                        else:
                            reserve_cap = 2000
                        # 예약되지 않은 컨트롤러거나
                        # 컨트롤러의 예약시간이 본인꺼면서 reserve_cap 값 이하거나
                        # 컨트롤러가 다른사람꺼 + 아군 주둔중일때 만든다
                        if not Game.rooms[room_name].controller.reservation \
                                or (not flag_room_reserved_by_other and
                                    Game.rooms[room_name].controller.reservation.ticksToEnd < reserve_cap) \
                                or (flag_room_reserved_by_other and len(remote_troops) > 0):
                            spawn_res = ERR_NOT_ENOUGH_ENERGY
                            # 몸체크기
                            counter = 5
                            while spawn_res == ERR_NOT_ENOUGH_ENERGY and counter > 1:
                                reserver_body = [MOVE for i in range(counter)]
                                reserver_body.extend([CLAIM for i in range(counter)])
                                spawn_res = spawn.spawnCreep(reserver_body,
                                                             'res_{}_{}'.format(room_name_low, rand_int),
                                                             {memory: {'role': 'reserver', 'home_room': spawn.room.name,
                                                                       'assigned_room': room_name}})
                                # print(room_name, 'counter', counter, 'spawn_res', spawn_res)
                                counter -= 1
                            continue

                    # 에너지 뽑을 수 있을때까지 아래 뽑는건 지양.
                    if (flag_room_controller.owner and not flag_room_controller.my) \
                            or (flag_room_controller.reservation and
                                not flag_room_controller.reservation.username == spawn.owner.username):
                        continue

                    # 에너지소스에 담당 컨테이너가 존재하는가?
                    # container_exist = False
                    # 컨테이너가 소스보다 적으면 새로 짓는거.
                    if len(flag_energy_sources) > len(flag_containers):
                        for es in flag_energy_sources:
                            # 현재 컨테이너가 있는 경우 소스에서 가장 가까운걸 찾는다.
                            if len(flag_containers):
                                closest_cont = es.pos.findClosestByPath(flag_containers, {ignoreCreeps: True})
                                # 4칸이하 거리면 있는거임. 통과
                                if closest_cont and len(es.pos.findPathTo(closest_cont, {ignoreCreeps: True})) <= 4:
                                    continue
                            # 위에 컨티뉴 안걸리면 무조건 여기로 도착함
                            carrier_source_obj = es
                            break

                        # ignore placing roads around sources and controllers alike as much as possible.
                        # 무조건 막을수는 없고, 정 다른길이 없으면 가게끔.
                        objs = flag_energy_sources

                        if flag_room_controller:
                            objs.append(flag_room_controller)
                        if len(flag_mineral) > 0:
                            objs.extend(flag_mineral)
                        if len(flag_lairs):
                            objs.extend(flag_lairs)

                        # 찍을 위치정보. 소스에서 본진방향으로 두번째칸임.
                        target_to_spawn = carrier_source_obj.pos.findPathTo(spawn.room.controller,
                                                                            {'ignoreCreeps': True})
                        const_loc = target_to_spawn[1]

                        print('const_loc:', const_loc)
                        print('const_loc.x {}, const_loc.y {}'.format(const_loc.x, const_loc.y))
                        print('Game.rooms[{}].name: {}'.format(room_name, Game.rooms[room_name].name))
                        # 찍을 좌표: 이게 제대로된 pos 함수
                        constr_pos = __new__(RoomPosition(const_loc.x, const_loc.y, Game.rooms[room_name].name))
                        print('constr_pos:', constr_pos)
                        const_res = constr_pos.createConstructionSite(STRUCTURE_CONTAINER)

                        print('building container at {}({}, {}): {}'
                              .format(room_name, const_loc.x, const_loc.y, const_res))

                        # todo 임시방편일뿐....
                        # 건설위치가 건설을 못하는 곳임 - 거기에 뭐가 있다던가 너무 다른방 입구근처라던가.
                        if const_res == ERR_INVALID_TARGET:
                            # 한칸 더 앞으로 간다.
                            const_loc = target_to_spawn[0]

                            print('const_loc:', const_loc)
                            print('const_loc.x {}, const_loc.y {}'.format(const_loc.x, const_loc.y))
                            print('Game.rooms[{}].name: {}'.format(room_name, Game.rooms[room_name].name))
                            # 찍을 좌표: 이게 제대로된 pos 함수
                            constr_pos = \
                                __new__(RoomPosition(const_loc.x, const_loc.y, Game.rooms[room_name].name))
                            print('constr_pos:', constr_pos)
                            const_res = constr_pos.createConstructionSite(STRUCTURE_CONTAINER)

                        print('objs', objs)
                        # 키퍼가 있으면 중간에 크립도 있는지라.
                        if keeper_lair:
                            for k in chambro.memory[STRUCTURE_KEEPER_LAIR]:
                                if Game.getObjectById(k):
                                    objs.append(Game.getObjectById(k))
                            opts = {'trackCreeps': True, 'refreshMatrix': True, 'pass_walls': False,
                                    'costByArea': {'objects': objs, 'size': 1, 'cost': 6}}
                        else:
                            opts = {'trackCreeps': False, 'refreshMatrix': True, 'pass_walls': False,
                                    'costByArea': {'objects': objs, 'size': 1, 'cost': 6}}

                        # RoomPosition 목록. 컨테이너 건설한 김에 길도 깐다.
                        constr_roads_pos = \
                            PathFinder.search(constr_pos, spawn.pos,
                                              {'plainCost': 2, 'swampCost': 3,
                                               'roomCallback':
                                                   lambda room_name:
                                                   pathfinding.Costs(room_name, opts).load_matrix()}, ).path
                        print('PATH:', JSON.stringify(constr_roads_pos))
                        # 길 찾은 후 스폰이 있는곳까지 도로건설
                        for pos in constr_roads_pos:
                            # 스폰이 있는 곳으로 또 쏠필요는 없음...
                            if pos == spawn.pos:
                                continue
                            pos.createConstructionSite(STRUCTURE_ROAD)
                        print('end container bld')
                        del carrier_source_obj

                    flag_harvest_quota = 0
                    for c in remote_harvesters:
                        if typeof(c.memory.size) == 'object':
                            c.suicide()
                            return
                        flag_harvest_quota += c.memory.size

                    # print('flag_harvest_quota', flag_harvest_quota)
                    enough_remote_harvesters = bool(len(flag_energy_sources) * 2 <= flag_harvest_quota)

                    # 소스 하나당 하베스터 사이즈 2. 현재로선 하베스터가 건설도 한다.
                    if not enough_remote_harvesters:
                        target_energy_source = None

                        # 에너지 하나당 사이즈 2점씩
                        for s in flag_energy_sources:
                            points = 0
                            print("s:", s, s.pos)
                            for c in remote_harvesters:
                                if c.memory.source_num == s.id:
                                    points += c.memory.size
                                print('c.memory.source_num', c.memory.source_num, 'pts:', points)
                            # 2점 미만이면 생성대상
                            if points < 2:
                                target_energy_source = s.id
                                break
                        if target_energy_source:
                            # 4000 for keeper lairs
                            # todo 너무 쉽게죽음. 보강필요. and need medic for keeper remotes
                            regular_spawn = -6
                            if keeper_lair:
                                regular_spawn = spawn.spawnCreep(
                                    [TOUGH, TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                     WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                     CARRY, CARRY, CARRY, CARRY],
                                    "hv_{}_{}".format(room_name_low, rand_int),
                                    {memory: {'role': 'harvester', 'assigned_room': room_name,
                                              'home_room': spawn.room.name, 'source_num': target_energy_source,
                                              'size': 2}})

                            # 키퍼용이 아니면 여기로
                            else:
                                # 용량 안될땐 저렙 하베스터도 허용. 단, 이땐 리서버 안만드니 둘을 만들 필요는 없음.
                                counter = 1
                                if chambro.energyCapacityAvailable < 1200:
                                    counter = 2
                                rm_hv_counter = 0
                                rm_hv_body = []
                                # todo - 수확하는 동시에 컨테이너에 적재가 가능한 경우에만 사용 가능하다.
                                closeBy = \
                                    _.filter(flag_containers,
                                             lambda c: Game.getObjectById(target_energy_source).pos.inRangeTo(c, 2))
                                if len(closeBy) and counter > 1:
                                    rm_hv_body = [MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK,
                                                  WORK, WORK, CARRY]
                                else:
                                    for i in harvester_body[counter]:
                                        if rm_hv_counter < 3:
                                            rm_hv_body.extend([def_body_content[rm_hv_counter] for _ in range(i)])
                                        rm_hv_counter += 1

                                spawning_rem_harv = \
                                    spawn.spawnCreep(rm_hv_body, "hv_{}_{}".format(room_name_low, rand_int),
                                                     {memory: {'role': 'harvester', 'assigned_room': room_name,
                                                               'home_room': spawn.room.name,
                                                               'source_num': target_energy_source,
                                                               'size': 2}})
                            print(spawn.name, 'spawning_rem_harv in', room_name_low, spawning_rem_harv)
                        return

                    # todo 변경: 거리별 점수 할당. 크던 적던 할당을 최우선으로 채운다.
                    #   캐리어의 사이즈는 캐리 하나당 하나씩 증가한다

                    # 작동방식:
                    # 우선 flag_energy_sources(방 내 모든 소스) 로 포문 돌린다.
                    # 그리고 거기서 스폰까지의 거리를 구하고 이에 따라 할당된 사이즈값도 구함.
                    # 그리고 그걸 기존에 있는 캐리어들 사이즈값으로 빼고 남는게 있으면 생산절차 돌입.

                    # 스폰 내 총 에너지량이 25% 이하면 아예 돌리지 않는다.
                    # 안그러면 중간에 자원부족으로 조그만 애들이 스폰될 시 자원 충분해도 그거만 뽑아버림...
                    if chambro.energyAvailable / chambro.energyCapacityAvailable < .25:
                        continue

                    # todo 미네랄 생각해봐야함
                    # 이제 컨테이너에서 가장 가까운 소스 확인한다
                    # 소스 둘 이상에 컨테이너 하나가 배정되는 경우도 있으니 감안해야함.
                    # print(len(flag_energy_sources), "flag_energy_sources in", room_name, ':', flag_energy_sources)
                    for s in flag_energy_sources:
                        # 에너지에서 가장 가까운 컨테이너를 찾는다.
                        closest_cont_to_source: StructureContainer \
                            = s.pos.findClosestByPath(flag_built_containers, {ignoreCreeps: True})
                        # 소스 배정됬나?
                        source_assigned = False
                        if closest_cont_to_source:
                            # 저 컨테이너가 얼마나 떨어져 있는지 확인
                            path_to_cont = s.pos.findPathTo(closest_cont_to_source, {ignoreCreeps: True})
                            # print(s.id, s.pos, 'cont:', closest_cont_to_source.pos, len(path_to_cont))
                            # 4칸이내에 있으면 조건에 맞음.
                            source_assigned = len(path_to_cont) <= 4

                        # 여기서부터 캐리어 본격생산 준비
                        # 이제 컨테이너에서 스폰까지 거리부터 쟨다.
                        if source_assigned:
                            # 먼저 이 소스에 배정된 캐리어 수부터 구한다.
                            # ttl 150 이상 남은 배정된 캐리어
                            carrier_creep = \
                                _.filter(Game.creeps,
                                         lambda c: c.memory.source_num == s.id and c.memory.role == 'carrier'
                                                   and (c.spawning or c.ticksToLive > 150))

                            # ttl 이 좀 남아있는 배정된 캐리어.
                            carrier_creep_healthy = \
                                _.filter(Game.creeps, lambda c: c.memory.source_num == s.id
                                                                and c.memory.role == 'carrier'
                                                                and (c.spawning or c.ticksToLive > 600))

                            # 패스파인딩 할때 최대한 피해야 하는 구간.
                            objs = _.clone(flag_energy_sources)
                            if flag_room_controller:
                                objs.append(flag_room_controller)
                            # does this room have keeper lairs?
                            if len(flag_mineral) > 0:
                                objs.extend(flag_mineral)

                            # 대충 해야하는일: 캐리어의 픽업위치에서 본진거리 확인. 그 후 거리만큼 추가.
                            # 컨테이너에서 본진까지의 거리 크립의 크기는 이거에 좌우된다.
                            distance = 0

                            if keeper_lair:
                                opts = {'trackCreeps': True, 'refreshMatrix': True, 'pass_walls': False,
                                        'costByArea': {'objects': objs, 'size': 1, 'cost': 6}}
                            else:
                                opts = {'trackCreeps': False, 'refreshMatrix': True, 'pass_walls': False,
                                        'costByArea': {'objects': objs, 'size': 1, 'cost': 6}}

                            # 방 안에 링크·컨테이너 목록
                            containers, links = [], []
                            for i in chambro.memory[STRUCTURE_CONTAINER]:
                                containers.append(i.id)
                            for i in chambro.memory[STRUCTURE_LINK]:
                                if i.for_store:
                                    links.append(i.id)
                            for i in constructions:
                                if i.structureType == STRUCTURE_LINK:
                                    links.append(i.id)
                                elif i.structureType == STRUCTURE_CONTAINER:
                                    containers.append(i.id)

                            # 픽업지점에서 적재소까지 길. 적절한 적재소가 없으면 스폰에서 시작
                            # 가장 가까운 적재소를 사전에 찾아서 배정한다.
                            # 이렇게 안하면 길 이상하게 멋대로 파버릴 수 있음...
                            path_spawn_to_pickup = \
                                find_closest_path(spawn, closest_cont_to_source.pos, containers, links, opts)

                            # 픽업 지점부터 스폰까지의 길
                            # path_to_home = PathFinder.search(closest_cont_to_source.pos, spawn.pos,
                            #                                  {'plainCost': 2, 'swampCost': 3,
                            #                                   'roomCallback':
                            #                                       lambda room_name:
                            #                                       pathfinding.Costs(room_name, opts).load_matrix()
                            #                                   }, ).path
                            # 하나하나 세서 집까지 도착하면 거기서 우선 한번 끊고
                            # 캐리어를 위한 컨테이너가 구석지역에 지어졌는지 확인해본다

                            # 위에 길 역순.
                            path_to_home = []

                            for p in path_spawn_to_pickup:
                                if not p.roomName == spawn.room.name:
                                    distance += 1
                                path_to_home.insert(0, p)

                            # 만일 키퍼가 있으면 다 4000짜리니 그만큼 한번에 수확가능한 자원이 많아짐. 그거 반영.
                            if keeper_lair:
                                distance = int(distance * 1.3)

                            work_chance = 0
                            # 캐리어는 방에 건설거리가 있거나 컨테이너 체력이 2/3 이하일때만 워크바디를 넣는다.
                            if closest_cont_to_source.hits <= closest_cont_to_source.hitsMax / 3 * 2 \
                                    or len(flag_constructions):
                                work_chance = 1

                            # 거리의 절반만큼의 거리를 캐리어 사이즈로...
                            # 정확히 뭘 근거였는지 기억이 안나는데 여튼 돌아감.
                            carrier_size = distance / 2
                            # print('init. carrier_size', carrier_size)
                            # 저렙인 상황이면 1/3 처리. 어차피 자잘하게 나와서...
                            if room_level < 4 or not chambro.storage:
                                carrier_size /= 3
                            # 캐리어 크기가 너무 작으면 자원 뽑을때 지장받는걸 포착.
                            elif carrier_size < 3:
                                carrier_size = 3

                            # 만약 캐리어가 전혀 없는데 꽉찼으면 몸 더준다.
                            if closest_cont_to_source.store.getCapacity() \
                                    == closest_cont_to_source.store.getUsedCapacity() \
                                    and not len(carrier_creep):
                                # print('extra BODY for {}'.format(closest_cont_to_source.pos))
                                carrier_size += 3

                            # 만들어야 하는 총 캐리어 사이즈
                            total_carrier_size = _.clone(carrier_size)

                            # 캐리어 사이즈에 값을 다 뺀다.
                            for c in carrier_creep:
                                carrier_size -= c.memory.size

                            # 중간에 용량부족으로 크립이 많이 생산됬을 시 이를 정리하기 위한 용도.
                            if carrier_size > 0:
                                # 모든 캐리어 값에 carrier_creep_healthy 에 해당하는 모든 크립의 사이즈를 뺀다.
                                carrier_size_healthy = _.clone(total_carrier_size)
                                for i in carrier_creep_healthy:
                                    carrier_size_healthy -= i.memory.size
                                if carrier_size_healthy:
                                    carrier_size = carrier_size_healthy

                            # 정수화, 소수점 올림처리
                            if carrier_size % int(carrier_size) > 0:
                                carrier_size += 1
                            carrier_size = int(carrier_size)
                            # print(s.pos, 'total_carrier_size', total_carrier_size, 'final carrier_size', carrier_size)

                            # 캐리어 크기에 따른 충전계산. 크기대비 절반 이상일때만 채운다.

                            # 여기서 실질적인 캐리어 용량 계산
                            spawn_quota = None
                            while carrier_size > 0:
                                # 이제 저 스몰 변수 쓸일이 있을라나...?
                                spawn_quota = determine_carrier_size(carrier_size, work_chance)

                                if len(spawn_quota[0]) <= 50 and spawn_quota[1] <= chambro.energyAvailable:
                                    break
                                carrier_size -= 1
                            # print('final carrier_size', carrier_size, spawn_quota)
                            # 값이 남아있으면 작업에 들어가는거임.
                            if carrier_size > 0:
                                spawning = spawn.spawnCreep(spawn_quota[0],
                                                            'cr_{}_{}'.format(room_name_low, rand_int),
                                                            {memory: {'role': 'carrier',
                                                                      'assigned_room': room_name,
                                                                      'home_room': spawn.pos.roomName,
                                                                      'pickup': closest_cont_to_source.id,
                                                                      'work': work_chance,
                                                                      'source_num': s.id,
                                                                      'size': carrier_size,
                                                                      'total': total_carrier_size,
                                                                      'level': 8,
                                                                      haul_resource: haul_all,
                                                                      to_home: path_to_home,
                                                                      to_pickup: path_spawn_to_pickup}})
                                print(spawn.name, 'spawning carrier in', room_name_low, spawning)
                                return
                    continue
                    # todo 철거반 손봐야함!!
                    # 시퓨 딸리면 안만드는건데... 사실 이제 필요하나 싶긴함.
                    if Game.cpu.bucket > cpu_bucket_emergency + cpu_bucket_emergency_spawn_start:
                        # 아래 철거반 확인용도.
                        regex_dem = '-dem'

                        # 만들지말지 확인용도
                        dem_bool = False
                        # 소속 깃발.
                        dem_flag = None
                        # todo 철거반을 만들었으면 자원회수반도 만든다.
                        # 여기까지 다 건설이 완료됐으면 철거반이 필요한지 확인해본다.
                        for fn in Object.keys(flags):
                            # 로딩안되면 시야에 없단소리. 정찰대 파견한다.
                            if not Game.flags[fn].room:
                                # look for scouts
                                creep_scouts = _.filter(creeps, lambda c: c.memory.role == 'scout'
                                                                          and c.memory.flag_name == fn)
                                if len(creep_scouts) < 1:
                                    spawn_res = spawn.createCreep([MOVE], 'Scout-' + fn,
                                                                  {'role': 'scout'
                                                                      , 'assigned_room': Game.flags[fn].pos.roomName})
                                    break
                            else:
                                # -dem : 철거지역. 이게 들어가면 이 방에 있는 모든 벽이나 잡건물 다 부수겠다는 소리.
                                # print("Game.flags[flag].name {} | fn {}".format(Game.flags[flag].name, fn))
                                if Game.flags[flag].room.name == Game.flags[fn].room.name \
                                        and fn.includes(regex_dem):

                                    # 여기 걸리면 컨테이너도 박살낼지 결정. 근데 쓸일없을듯.
                                    regex_dem_container = '-dema'
                                    demo_container = 0
                                    if fn.includes(regex_dem_container):
                                        demo_container = 1
                                    dem_bool = True
                                    dem_flag = fn
                                    break

                                if dem_bool:
                                    remote_dem = _.filter(creeps, lambda c: c.memory.role == 'demolition'
                                                                            and c.memory.flag_name == dem_flag)
                                    demolish_structures = Game.flags[fn].room.find(FIND_STRUCTURES)

                                    if Game.flags[fn].room.controller:
                                        index = demolish_structures.indexOf(Game.flags[fn].room.controller)
                                        demolish_structures.splice(index, 1)

                                    dem_num = len(remote_dem)
                                else:
                                    dem_num = 0

                                if dem_bool and dem_num == 0:
                                    if room_level < 7:
                                        body = [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                                WORK, WORK,
                                                WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK]
                                    else:
                                        body = [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                                MOVE, MOVE,
                                                MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK,
                                                WORK, WORK,
                                                WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                                WORK, WORK,
                                                WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                                WORK, WORK,
                                                WORK, WORK]
                                    spawning_creep = spawn.createCreep(body, undefined
                                                                       , {'role': 'demolition',
                                                                          'assigned_room': Game.flags[
                                                                              flag].room.name
                                                                           , 'home_room': spawn.room.name
                                                                           , 'demo_container': demo_container
                                                                           , 'flag_name': dem_flag})
                                    if spawning_creep == ERR_NOT_ENOUGH_RESOURCES:
                                        body = [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                                WORK, WORK,
                                                WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK]
                                        spawn.createCreep(body, undefined, {'role': 'demolition',
                                                                            'assigned_room': Game.flags[
                                                                                flag].room.name
                                            , 'home_room': spawn.room.name
                                            , 'demo_container': demo_container
                                            , 'flag_name': dem_flag})
                                    continue
                                # elif

    elif spawn.spawning:
        # 디스플레이 부분 위치조정
        display_loc = display_location(spawn, objs_for_display)
        # todo 디스플레이 부분 위치조정 필요. 다섯칸 간격이면 적당할듯.
        # 벽은 7칸으로.
        # showing process of the spawning creep by %
        spawning_creep = Game.creeps[spawn.spawning.name]
        spawn.room.visual.text(
            '🛠 ' + spawning_creep.memory.role + ' '
            + "{}/{}".format(spawn.spawning.remainingTime - 1, spawn.spawning.needTime),
            display_loc['x'], display_loc['y'],
            {'align': display_loc['align'], 'color': '#EE5927'}
        )
    else:
        # 주변에 있는 크립 회복조치.
        # 스토리지를 가지는 시점부터 충전시작.
        if spawn.room.storage:
            # soldier > harvester > hauler > upgrader > etc.
            # ^ not applied yet idk
            for creep in room_creeps:
                if not spawn.pos.isNearTo(creep) or creep.memory.level < room_level or creep.spawning:
                    continue
                # 일꾼은 무조건 항시 채워준다. 어차피 근접할 가능성 거의없기도 함.
                # 렙4 에서 조건 충족하는 애가 얘뿐이기도 함.
                if creep.memory.role == 'harvester' and creep.ticksToLive <= 1400:
                    spawn.renewCreep(creep)
                    break
                # 스폰을 자주 지나다니는 허울러 특성상
                # 1. 너무 자주 충전되면 스폰 사이 무의미하게 왔다갔다하는 현상 발생. 타임계산은 이를 방지
                # 2. 허울러는 방 중간중간 추가 허울러가 무의미하게 스폰될 가능성이 있는 특성상
                #  틱 300 이상은 채우지 않는다. 300 인 이유는 허울러 둘이 생겼을 경우 약간 보조하기 위한 용도.
                #  둘이 동시생성되는건 지양합시다.
                # 3. 허울러는 기본값으로 한명으로 유지해야 하기에 둘 이상이면 안건든다.
                # 셋중 하나라도 걸리는게 있으면 통과
                if creep.memory.role == 'hauler' and creep.ticksToLive < 300:
                    if Game.time % 3 == 0 \
                            and len(_.filter(Game.creeps,
                                             lambda c: c.memory.role == 'hauler'
                                                       and c.memory.assigned_room == spawn.pos.roomName
                                                       and creep.memory.level >= room_level)) == 1:
                        spawn.renewCreep(creep)
                        break
                # 업글러는 스토리지 자원 삼천당 수리대상의 업글러의 수로 계산한다.
                # 업글러가 둘이면 스토리지에 자원이 최소 3천은 있어야 하는거.
                if creep.memory.role == 'upgrader' and creep.ticksToLive <= 500 and not room_level == 8 and \
                        spawn.room.storage.store.getUsedCapacity(RESOURCE_ENERGY) > 3000:
                    creep_upgraders = _.filter(room_creeps,
                                               lambda c: (c.memory.role == 'upgrader'
                                                          and c.memory.assigned_room == spawn.pos.roomName
                                                          and (c.spawning or c.ticksToLive > 100)
                                                          and c.memory.level >= room_level))
                    if spawn.room.storage.store.getUsedCapacity(RESOURCE_ENERGY) > 10000:
                        storage_amount = (len(creep_upgraders) - 1) * 5000
                    else:
                        storage_amount = (len(creep_upgraders) - 1) * 3000
                    if spawn.room.storage.store.getUsedCapacity(RESOURCE_ENERGY) > storage_amount:
                        spawn.renewCreep(creep)
                        break
                # 수리대상 10개 이하면 거의 끝이란 소리니 회복대상에서 제외
                if creep.memory.role == 'fixer' and creep.ticksToLive <= 500 and len(wall_repairs) > 10:
                    if spawn.room.storage.store.getUsedCapacity(RESOURCE_ENERGY) \
                            >= 50000 * len(_.filter(room_creeps, lambda c: c.memory.role == 'fixer')):
                        spawn.renewCreep(creep)
                        break
                if creep.memory.role == 'carrier' and creep.ticksToLive <= 500:
                    # 1. 캐리어의 크기가 전체크기의 2/3 이상이고
                    # 2. 누적 캐리어의 크기가 총 크기를 넘기지 않으면 채운다.
                    # 3. 컨테이너 체력이 절반 이상 떨어졌으면 WORK 가 없을 가능성이 높으니 이 또한 감안.
                    creeps = Game.creeps
                    current_size = 0
                    for name in Object.keys(creeps):
                        c = creeps[name]
                        if c.memory.role == 'carrier' and c.memory.source_num == creep.memory.source_num:
                            current_size += c.memory.size
                    pickup: StructureContainer = Game.getObjectById(creep.memory.pickup)
                    if creep.memory.size >= creep.memory.total * (2 / 3) \
                            and current_size <= creep.memory.total \
                            and (pickup and pickup.hits > pickup.hitsMax * .5):
                        spawn.renewCreep(creep)
                        break


def determine_carrier_size(criteria: int, work_chance=0, small=False):
    """
    캐리어 바디 계산용 스크립트.

    :param criteria: 몇짜리 크기인지 확인
    :param work_chance: WORK 바디를 넣을지 말지 확인
    :param small: 크기 작게? - 만일 참이면 WORK 6개 배정을 4로 줄인다
    :return: [size], cost
    """

    # 만드는데 드는 비용
    cost = 0

    # 굳이 따로 둔 이유: 캐리 둘에 무브 하나.
    carry_body_odd = [CARRY]
    carry_body_even = [CARRY, MOVE]
    work_body = [WORK, WORK, MOVE]
    body = []

    if small:
        work_size = 1
    else:
        work_size = 2

    # 소수점 다 올림처리.
    if criteria % int(criteria) > 0:
        criteria += 1
    # 여기서 값을 넣는다.
    for i in range(criteria):
        # work 부분부터 넣어본다.
        if work_chance:
            if i < work_size:
                body.extend(work_body)
                cost = add_costs(work_body, cost)
        # 이거부터 들어가야함
        if i % 2 == 0:
            body.extend(carry_body_even)
            cost = add_costs(carry_body_even, cost)
        else:
            body.extend(carry_body_odd)
            cost = add_costs(carry_body_odd, cost)

    return body, cost


def add_costs(body: List[str], cost):
    """
    바디파트별 값 합계

    :param body:
    :param cost:
    :return:
    """
    for i in body:
        cost += BODYPART_COST[i]
    return cost


def find_closest_path(spawn: StructureSpawn, goal: RoomPosition, containers, links, opts):
    """
    캐리어 스폰할 때 가장 가까이 있는 링크·컨테이너의 위치로 경로를 사전에 넣기 위한 용도.

    :param spawn: 시작점. 스폰.
    :param goal: 목적지.
    :param containers: 방 안에 컨테이너 ID.
    :param links: 방 안에 링크 ID.
    :param opts: 외부에서 가져온 패스파인딩 추가옵션
    :return:
    """
    # print('goal', goal, JSON.stringify(goal))
    # 가장 먼저 스토리지가 있는지 확인한다.
    storage: StructureStorage = spawn.room.storage
    result = None
    counter = 0
    if storage:
        constr_roads_pos = \
            PathFinder.search(storage.pos, goal,
                              {'plainCost': 2, 'swampCost': 3,
                               'roomCallback':
                                   lambda room_name:
                                   pathfinding.Costs(room_name, opts).load_matrix()}, ).path
        for i in constr_roads_pos:
            if i.roomName == spawn.room.name:
                counter += 1
        if counter <= 10:
            # print(';storage!')
            result = constr_roads_pos

    if len(links) and not result:
        for i in links:
            if Game.getObjectById(i):
                constr_roads_pos = \
                    PathFinder.search(Game.getObjectById(i).pos, goal,
                                      {'plainCost': 2, 'swampCost': 3,
                                       'roomCallback':
                                           lambda room_name:
                                           pathfinding.Costs(room_name, opts).load_matrix()}, ).path
                counter = 0
                for i in constr_roads_pos:
                    if i.roomName == spawn.room.name:
                        counter += 1
                if counter <= 10:
                    result = constr_roads_pos
                    # print('link!')
                    break

    if len(containers) and not result:
        for i in containers:
            if Game.getObjectById(i):
                constr_roads_pos = \
                    PathFinder.search(Game.getObjectById(i).pos, goal,
                                      {'plainCost': 2, 'swampCost': 3,
                                       'roomCallback':
                                           lambda room_name:
                                           pathfinding.Costs(room_name, opts).load_matrix()}, ).path
                counter = 0
                for i in constr_roads_pos:
                    if i.roomName == spawn.room.name:
                        counter += 1
                if counter <= 10:
                    result = constr_roads_pos
                    # print('cont!')
                    break

    # print('counter', counter, 'result', JSON.stringify(result))
    if result:
        return result

    return PathFinder.search(spawn.pos, goal,
                             {'plainCost': 2, 'swampCost': 3,
                              'roomCallback':
                                  lambda room_name:
                                  pathfinding.Costs(room_name, opts).load_matrix()}, ).path
