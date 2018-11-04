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
def run_spawn(spawn, all_structures, room_creeps, hostile_creeps, divider, counter,
              cpu_bucket_emergency, cpu_bucket_emergency_spawn_start, extractor,
              terminal_capacity, chambro, interval, wall_repairs, spawns_and_links, min_hits):
    """


    :param spawn:
    :param all_structures:
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
    :param spawns_and_links:
    :param min_hits:
    :return:
    """
    # print('yolo')
    memory = 'memory'

    spawn_cpu = Game.cpu.getUsed()
    # if spawn is not spawning, try and make one i guess.
    # spawning priority: harvester > hauler > upgrader > melee > etc.
    # checks every 10 + len(Game.spawns) ticks
    if not spawn.spawning and Game.time % counter == divider:

        rand_int = random.randint(0, 99)
        # print('inside spawning check')
        spawn_chk_cpu = Game.cpu.getUsed()

        hostile_around = False
        # 적이 스폰 주변에 있으면 생산 안한다. 추후 수정해야함.

        if hostile_creeps:
            for enemy in hostile_creeps:
                if spawn.pos.inRangeTo(enemy, 2):
                    hostile_around = True
                    break
        if hostile_around and chambro.controller.level == 8:
            return

        # ALL creeps you have
        creeps = Game.creeps

        # need each number of creeps by type. now all divided by assigned room.
        # assigned_room == 주 작업하는 방. remote에서 작업하는 애들이면 그쪽으로 보내야함.
        # home_room == 원래 소속된 방. remote에서 일하는 애들에나 필요할듯.

        creep_harvesters = _.filter(creeps, lambda c: (c.memory.role == 'harvester'
                                                       and c.memory.assigned_room == spawn.pos.roomName
                                                       and not c.memory.flag_name
                                                       and (c.spawning or c.ticksToLive > 80)))
        creep_haulers = _.filter(creeps, lambda c: (c.memory.role == 'hauler'
                                                    and c.memory.assigned_room == spawn.pos.roomName
                                                    and (c.spawning or c.ticksToLive > 100)))
        # 추후 추가요망.
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
        # cpu 비상시 고려 자체를 안한다. 세이프모드일때도 마찬가지.
        if Game.cpu.bucket > cpu_bucket_emergency + cpu_bucket_emergency_spawn_start \
            or spawn.room.controller.safeModeCooldown:
            creep_upgraders = _.filter(creeps, lambda c: (c.memory.role == 'upgrader'
                                                          and c.memory.assigned_room == spawn.pos.roomName
                                                          and (c.spawning or c.ticksToLive > 100)))

        # ﷽
        # if number of close containers/links are less than that of sources.
        harvest_carry_targets = []

        room_sources = spawn.room.find(FIND_SOURCES)
        # 소스를 따로 떼는 이유: 아래 합치는건 광부를 포함하는거지만 이 sources자체는 에너지 채취만 주관한다.
        num_o_sources = len(room_sources)
        if extractor and extractor.cooldown == 0:
            room_sources.push(extractor)

        containers_and_links = all_structures.filter(lambda st: st.structureType == STRUCTURE_CONTAINER
                                                                or st.structureType == STRUCTURE_LINK)
        # 소스 주변에 자원채취용 컨테이너·링크가 얼마나 있는가 확인.
        for rs in room_sources:
            for s in containers_and_links:
                # 설정된 칸이내에 존재하는가?
                if s.structureType == STRUCTURE_CONTAINER and rs.pos.inRangeTo(s, max_range_to_container):
                    # 실제 거리도 그 이내인가?
                    if len(rs.pos.findPathTo(s, {'ignoreCreeps': True})) <= max_range_to_container:
                        # 여기까지 들어가있으면 요건충족한거.
                        harvest_carry_targets.push(s.id)
                        break
                elif s.structureType == STRUCTURE_LINK:
                    for m in chambro.memory[STRUCTURE_LINK]:
                        if s.id == m.id and not m.for_store:
                            harvest_carry_targets.push(s.id)
                            break
            # 소스 근처에 스토리지가 있으면 그것도 확인. todo 되나 확인요망
            if spawn.room.storage and len(rs.pos.findPathTo(spawn.room.storage, {'ignoreCreeps': True})) <= 3:
                harvest_carry_targets.push(spawn.room.storage.id)

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

        if harvesters_bool:
            # check if energy_source capacity is 4.5k(4k in case they update, not likely).
            # if is, go for size 4500.
            if room_sources[0].energyCapacity > 4000:
                regular_spawn = spawn.spawnCreep(
                    [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK,
                     WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY],
                    '🌾_{}_{}'.format(spawn.pos.roomName, rand_int),
                    {memory: {'role': 'harvester', 'assigned_room': spawn.pos.roomName, 'size': 2}})
            else:
                # perfect for 3000 cap
                regular_spawn = spawn.spawnCreep(
                    [WORK, WORK, WORK, WORK, WORK, WORK,
                     CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE],
                    '🌾_{}_{}'.format(spawn.pos.roomName, rand_int),
                    {memory: {'role': 'harvester', 'assigned_room': spawn.pos.roomName, 'size': 2}})
            # print('what happened:', regular_spawn)
            if regular_spawn == -6:
                # one for 1500 cap == need 2
                if spawn.spawnCreep(
                    [WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE],
                    '🌾_{}_{}'.format(spawn.pos.roomName, rand_int),
                    {memory: {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                              'size': 1}}) == -6:
                    # 3 WORK
                    if spawn.spawnCreep([MOVE, MOVE, WORK, WORK, WORK, CARRY, CARRY],
                                        '🌾_{}_{}'.format(spawn.pos.roomName, rand_int),
                                        {memory: {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                                                  'size': 1}}) == -6:
                        # final barrier
                        spawn.spawnCreep([MOVE, WORK, WORK, CARRY],
                                         '🌾_{}_{}'.format(spawn.pos.roomName, rand_int),
                                         {memory: {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
                                                   'size': 1}})
            return

        plus = 0

        # 위에 컨테이너로 인한 플러스 할때 캐리어용 컨테이너로 추가됬는가?
        carrier_plus = 0
        # 컨테이너와 링크를 하나씩 돌려서 수확용 칸인지 확인하고 이에 plus를 추가한다.
        for mcont in spawn.room.memory[STRUCTURE_CONTAINER]:
            # 우선, 해당 컨테이너가 일반 하베스트인가?
            if mcont.for_harvest == 1:
                # 업그레이드 용도면 안센다. 단 렙8미만일때만.
                if spawn.room.controller.level < 8 and mcont.for_upgrade:
                    continue
                # 60% 이상 차있으면 ++, 꽉차면 두배.
                # 꽉차면 하나로 수정해본다.
                cont_obj = Game.getObjectById(mcont.id)
                #
                if cont_obj and _.sum(cont_obj.store) == cont_obj.storeCapacity:
                    # plus += 2
                    plus += 1
                # elif cont_obj and _.sum(cont_obj.store) > cont_obj.storeCapacity * .6:
                #     plus += 1

            # 캐리어용 컨테이너인가?
            if mcont.for_harvest == 2:
                # 꽉찬경우 새로 추가. 대상은 캐리어용 및 광물용
                cont_obj = Game.getObjectById(mcont.id)
                if cont_obj and _.sum(cont_obj.store) == cont_obj.storeCapacity:
                    # print('plus! remote', mcont.id)
                    carrier_plus += 1
                    # 초반엔 이송거리 문제도 있고 해서 허울러 혼자론 무리일수도 있음.
                    # 렙8 이후에야 어느정도 감당이 된다고 판단.
                    if chambro.controller.level == 8:
                        if carrier_plus == 2 or carrier_plus == 3:
                            plus += 1
                    else:
                        if carrier_plus == 1 or carrier_plus == 3:
                            plus += 1

        # 위와 동일. 링크를 센다.
        for mlink in spawn.room.memory[STRUCTURE_LINK]:
            # 링크는 크게 두종류가 존재한다. 받는것과 주는것.
            # 주는것이 꽉찰때 추가.
            if not mlink.for_store:
                mlink_obj = Game.getObjectById(mlink.id)
                # 링크가 꽉 차고 캐리어용이 아닌 한에 채운다.
                if mlink_obj and mlink_obj.energy == mlink_obj.energyCapacity \
                    and mlink_obj.cooldown == 0 and not mlink.for_harvest:
                    plus += 1
                    print('plus! link {}, harvest: {}'
                          .format(mlink_obj.id, mlink_obj.for_harvest))

        # 건물이 아예 없을 시
        if len(harvest_carry_targets) == 0:
            plus = -num_o_sources

        # 만일 4렙이하면 두배
        if chambro.controller.level < 6:
            plus *= 2

        # 허울러 수 계산법: 방별로 지정된 허울러(기본값 2) + 위에 변수값
        hauler_capacity = Memory.rooms[spawn.room.name].options.haulers + plus
        # minimum number of haulers in the room is 1, max 4. always max when lvl 4 or less
        if hauler_capacity <= 0:
            hauler_capacity = 1
        elif hauler_capacity > 4 or not chambro.storage:
            hauler_capacity = 4

        if spawn.room.terminal:
            if spawn.room.terminal.store.energy > terminal_capacity + 10000:
                hauler_capacity += 1

        if len(creep_haulers) < hauler_capacity:
            # 초기화 용도.
            spawning_creep = ERR_NOT_ENOUGH_ENERGY
            # 순서는 무조건 아래와 같다. 무조건 덩치큰게 장땡.

            # 만일 컨트롤러 레벨이 8일 경우 가장 WORK 높은애 우선 하나.
            # 왜 만든거지...?? NULLIFIED
            # if spawn.room.controller.level == 8:
            #     spawning_creep = spawn.spawnCreep(
            #         [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
            #          MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
            #          CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
            #          CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY],
            #         '🚚_{}_{}'.format(spawn.pos.roomName, rand_int),
            #         {memory: {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
            #                     'level': 8}})

            # 1200
            if len(creep_haulers) >= 2:
                if spawning_creep == ERR_NOT_ENOUGH_ENERGY:
                    spawning_creep = spawn.spawnCreep(
                        [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                         MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK,
                         WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                         CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                         CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY],
                        '🚚_{}_{}'.format(spawn.pos.roomName, rand_int),
                        {memory: {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                  'level': 8}})
            else:
                spawning_creep = ERR_NOT_ENOUGH_ENERGY

            # 800
            if spawning_creep == ERR_NOT_ENOUGH_ENERGY:
                spawning_creep = spawn.spawnCreep(
                    [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, CARRY,
                     CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                     CARRY, CARRY],
                    '🚚_{}_{}'.format(spawn.pos.roomName, rand_int),
                    {memory: {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                              'level': 8}})

            if spawning_creep == ERR_NOT_ENOUGH_ENERGY:
                # 600
                spawning_creep = spawn.spawnCreep(
                    [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                     CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY],
                    '🚚_{}_{}'.format(spawn.pos.roomName, rand_int),
                    {memory: {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                              'level': 8}})

            if spawning_creep == ERR_NOT_ENOUGH_ENERGY:
                # 250
                spawning_creep = spawn.spawnCreep([WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                                                   CARRY, CARRY, MOVE, MOVE, MOVE, MOVE, MOVE],
                                                  '🚚_{}_{}'.format(spawn.pos.roomName, rand_int),
                                                  {memory: {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                                            'level': 5}})

            if spawning_creep == ERR_NOT_ENOUGH_ENERGY:
                if spawn.spawnCreep([WORK, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE],
                                    '🚚_{}_{}'.format(spawn.pos.roomName, rand_int),
                                    {memory: {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                              'level': 2}}) == -6:
                    spawn.spawnCreep([MOVE, MOVE, WORK, CARRY, CARRY],
                                     '🚚_{}_{}'.format(spawn.pos.roomName, rand_int),
                                     {memory: {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                               'level': 0}})

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
                            '⛏_{}_{}'.format(spawn.pos.roomName, rand_int),
                            {memory: {'role': 'miner', 'assigned_room': spawn.pos.roomName, 'level': 5}})
                        if spawning_creep == ERR_NOT_ENOUGH_RESOURCES:
                            spawning_creep = spawn.spawnCreep(
                                [MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                 WORK,
                                 WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY],
                                '⛏_{}_{}'.format(spawn.pos.roomName, rand_int),
                                {memory: {'role': 'miner', 'assigned_room': spawn.pos.roomName}})

        # 업그레이더는 버켓 비상 근접시부터 생산 고려 자체를 안한다.
        if Game.cpu.bucket > cpu_bucket_emergency + cpu_bucket_emergency_spawn_start:
            max_num_upgraders = chambro.memory.options[max_upgraders]
            if spawn.room.controller.level == 8:
                proper_level = 1
            # start making upgraders after there's a storage
            elif spawn.room.storage:
                # print('check2')
                # if spawn.room.controller.level < 5:
                expected_reserve = 3000

                # if there's no storage or storage has less than expected_reserve
                if spawn.room.storage.store[RESOURCE_ENERGY] < expected_reserve or not spawn.room.storage:
                    proper_level = 1
                # more than 30k
                elif spawn.room.storage.store[RESOURCE_ENERGY] >= expected_reserve:
                    proper_level = 1
                    # extra upgrader every expected_reserve
                    proper_level += int(spawn.room.storage.store[RESOURCE_ENERGY] / expected_reserve)
                    # max_num_upgraders
                    if proper_level > max_num_upgraders:
                        proper_level = max_num_upgraders
                else:
                    proper_level = 0
            # 렙4부터는 스토리지 건설이 최우선이기에 업글러 스폰에 총력가하면 망함...
            elif chambro.controller.level < 4:
                # print('chk3')
                # 이시점엔 소형애들만 생성됨.
                # print('이시점엔 소형애들만 생성됨.')
                proper_level = int(max_num_upgraders / 2)
            else:
                # print('checkWTF')
                proper_level = 0
            # print('proper_level', proper_level)
            if len(creep_upgraders) < proper_level:
                if spawn.room.controller.level != 8:
                    big = spawn.spawnCreep(
                        [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK,
                         WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY],
                        '업글_{}_{}'.format(spawn.pos.roomName, rand_int),
                        {memory: {'role': 'upgrader', 'assigned_room': spawn.pos.roomName, 'level': 5}})
                else:
                    big = -6

                # 스폰렙 만땅이면 쿨다운 유지만 하면됨....
                if spawn.room.controller.level == 8:
                    if spawn.room.controller.ticksToDowngrade < CONTROLLER_DOWNGRADE[8] - 100000 \
                        or (spawn.room.controller.ticksToDowngrade < CONTROLLER_DOWNGRADE[8] - 4900
                            and len(hostile_creeps) > 0):
                        spawn.spawnCreep([WORK, WORK, CARRY, CARRY, MOVE, MOVE],
                                         '업글_{}_{}'.format(spawn.pos.roomName, rand_int),
                                         {memory: {'role': 'upgrader', 'assigned_room': spawn.pos.roomName}})
                elif big == -6:
                    small = spawn.spawnCreep(
                        [WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                         CARRY, CARRY, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE],
                        '업글_{}_{}'.format(spawn.pos.roomName, rand_int),
                        {memory: {'role': 'upgrader', 'assigned_room': spawn.pos.roomName, 'level': 3}})
                    if small == -6:
                        little = spawn.spawnCreep([WORK, WORK, WORK, CARRY, MOVE, MOVE],
                                                  '업글_{}_{}'.format(spawn.pos.roomName, rand_int),
                                                  {memory: {'role': 'upgrader', 'assigned_room': spawn.pos.roomName}})
                    if little == -6:
                        spawn.spawnCreep([WORK, WORK, CARRY, CARRY, MOVE, MOVE],
                                         '업글_{}_{}'.format(spawn.pos.roomName, rand_int),
                                         {memory: {'role': 'upgrader', 'assigned_room': spawn.pos.roomName}})

        if not chambro.memory[options][stop_fixer]:
            chambro.memory[options][stop_fixer] = 1

        # 렙 7 이상일때부터 수리병을 부름. 7때는 단지 하나. 8때는 5천에 하나.
        # 그리고 할당량 다 찼는데도 뽑는 경우도 있을 수 있으니 타이머 쟨다.
        # 수리할게 더 없으면 천틱동안 추가 생산을 안한다.
        if Game.time - chambro.memory[options][stop_fixer] > 1000 \
                and len(wall_repairs) and chambro.controller.level >= 7 \
                and chambro.storage and chambro.storage.store[RESOURCE_ENERGY] >= 5000:

            # 렙8부터 본격적인 작업에 드간다. 그전까진 무의미.
            # 또한 수리할게 더 없는 상황에서 첫 생성을 한거면 하나만 뽑고 천틱 대기한다.
            if chambro.controller.level == 7 and chambro.storage.store[RESOURCE_ENERGY] >= 10000 \
                    or Game.time - chambro.memory[options][stop_fixer] <= 3000:
                max_num_fixers = 1
            # 벽수리가 중심인데 수리할 벽이 없으면 의미가 없음.
            elif chambro.controller.level == 8 and min_hits < chambro.memory[options][repair]:
                max_num_fixers = int(chambro.storage.store[RESOURCE_ENERGY] / 20000)
                # todo 최대값. 임시조치임.
                if max_num_fixers > 6:
                    max_num_fixers = 6
            else:
                print('wtf')
                max_num_fixers = 0
            if len(creep_fixers) < max_num_fixers:
                fixer_spawn = spawn.spawnCreep(
                    [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                     WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                     WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                     CARRY], '🛠️_{}_{}'.format(spawn.pos.roomName, rand_int),
                    {memory: {'role': 'fixer', 'assigned_room': spawn.pos.roomName, 'level': 8}})

        if Memory.debug or Game.time % interval == 0 or Memory.tick_check:
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
            # 포문 끝나고 깃발 삭제할지 확인...
            delete_flag = False
            # 깃발이 있는 방이름.
            flag_room_name = flags[flag_name].pos.roomName

            # 방이름 + -rm + 아무글자(없어도됨) << 방을 등록한다.
            if flag_name.includes(spawn.room.name) and flag_name.includes("-rm"):
                print('includes("-rm")')
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
                                if r == Game.flags[flag_name].pos.roomName:
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
                    if r.roomName == Game.flags[flag_name].pos.roomName:
                        room_added = True
                        break
                print('room added?', room_added)
                # 추가가 안된 상태면 초기화를 진행
                if not room_added:
                    print('what??')
                    # init = {'roomName': Game.flags[flag_name].pos.roomName, 'defenders': 1, 'initRoad': 0,
                    #         'display': {'x': Game.flags[flag_name].pos.x, 'y': Game.flags[flag_name].pos.y}}
                    init = {'defenders': 1, 'initRoad': 0,
                            'display': {'x': Game.flags[flag_name].pos.x,
                                        'y': Game.flags[flag_name].pos.y}}
                    Memory.rooms[spawn.room.name][options][remotes][Game.flags[flag_name].pos.roomName] = init
                    # Memory.rooms[spawn.room.name][options][remotes].update({Game.flags[flag_name].pos.roomName: init})
                    print('Memory.rooms[{}][options][remotes][{}]'.format(spawn.room.name,
                                                                          Game.flags[flag_name].pos.roomName),
                          JSON.stringify(Memory.rooms[spawn.room.name][options][remotes][Game.flags[flag_name]
                                         .pos.roomName]))

                delete_flag = True

            # 아래부터 값을 쪼개는데 필요함.
            name_list = flag_name.split()

            # 주둔할 병사 수 재정의
            if flag_name.includes('-def'):
                print("includes('-def')")
                number_added = False
                included = name_list.index('-def')
                # 트라이에 걸린다는건 숫자 빼먹었거나 숫자가 아니라는거.
                # 초기화
                number = 0
                try:
                    number = name_list[included + 1]
                    number = int(number)
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
            if flag_name.includes('-rp'):
                print("includes('-rp')")
                # 내 방 맞음?
                controlled = False
                if flags[flag_name].room.controller:
                    if flags[flag_name].room.controller.my:
                        controlled = True

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
                    flags[flag_name].room.memory.options.repair = number
                    delete_flag = True

            # 방의 운송크립수 설정.
            if flag_name.includes('-hl'):
                # 내 방 맞음?
                controlled = False
                if flags[flag_name].room.controller:
                    if flags[flag_name].room.controller.my:
                        controlled = True

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
                    flags[flag_name].room.memory.options.haulers = number
                    delete_flag = True

            # 방 안에 미네랄 채취 시작
            if flag_name.includes('-mine'):
                print('-mine')
                # 내 방 맞음?
                controlled = False
                # todo 키퍼방일 경우 추가요망. 현재는 내방만.
                if flags[flag_name].room and flags[flag_name].room.controller:
                    if flags[flag_name].room.controller.my:
                        controlled = True

                if controlled:
                    mineral_loc = flags[flag_name].room.find(FIND_MINERALS)[0]
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
                            posi = __new__(RoomPosition(s.x, s.y, flags[flag_name].room.name))
                            posi.createConstructionSite(STRUCTURE_CONTAINER)
                        else:
                            posi = __new__(RoomPosition(s.x, s.y, flags[flag_name].room.name))
                            posi.createConstructionSite(STRUCTURE_ROAD)
                        counter += 1
                delete_flag = True

            # 방내 설정값 표기.
            if flag_name.includes('-dsp'):
                print("includes('-dsp')")
                # 내 방 맞음?
                controlled = False
                if flags[flag_name].room and flags[flag_name].room.controller:
                    if flags[flag_name].room.controller.my:
                        controlled = True
                    # 아니면 리모트임.
                    else:
                        # 리모트 소속방 찾는다.
                        for chambra_nomo in Object.keys(Game.rooms):
                            set_loc = False
                            if Memory.rooms[chambra_nomo].options:
                                # counter_num = 0

                                for r in Object.keys(Memory.rooms[chambra_nomo].options.remotes):
                                    remote_room_name = r
                                    # 방이름 이거랑 똑같은지.
                                    # 안똑같으면 통과
                                    if remote_room_name != flags[flag_name].pos.roomName:
                                        print('{} != flags[{}].pos.roomName {}'
                                              .format(remote_room_name, flag_name, flags[flag_name].pos.roomName))
                                        pass
                                    else:
                                        print('Memory.rooms[chambra_nomo].options.remotes[counter_num].display'
                                              , Memory.rooms[chambra_nomo].options.remotes[r].display)
                                        if not Memory.rooms[chambra_nomo].options.remotes[r].display:
                                            Memory.rooms[chambra_nomo].options.remotes[r].display = {}
                                        rx = flags[flag_name].pos.x
                                        ry = flags[flag_name].pos.y
                                        Memory.rooms[chambra_nomo].options.remotes[r].display.x = rx
                                        Memory.rooms[chambra_nomo].options.remotes[r].display.y = ry
                                        set_loc = True
                                    # counter_num += 1
                            if set_loc:
                                break
                delete_flag = True

                # 내 방이 아니면 이걸 돌리는 이유가없음....
                if controlled:
                    # 만일 비어있으면 값 초기화.
                    if not flags[flag_name].room.memory.options.display:
                        flags[flag_name].room.memory.options.display = {}
                    # 깃발꽂힌 위치값 등록.
                    print('flagpos {}, {}'.format(flags[flag_name].pos.x, flags[flag_name].pos.y))
                    flags[flag_name].room.memory.options.display['x'] = flags[flag_name].pos.x
                    flags[flag_name].room.memory.options.display['y'] = flags[flag_name].pos.y
                    print('flags[{}].room.memory.options.display {}'
                          .format(flag_name, flags[flag_name].room.memory.options.display))

                    delete_flag = True

            # 방 내 핵채우기 트리거. 예·아니오 토글
            if flag_name.includes('-fln'):
                delete_flag = True
                # 내 방 맞음?
                controlled = False
                if flags[flag_name].room.controller:
                    if flags[flag_name].room.controller.my:
                        controlled = True

                if controlled:
                    if flags[flag_name].room.memory.options.fill_nuke == 1:
                        flags[flag_name].room.memory.options.fill_nuke = 0
                    elif flags[flag_name].room.memory.options.fill_nuke == 0:
                        flags[flag_name].room.memory.options.fill_nuke = 1
                    else:
                        flags[flag_name].room.memory.options.fill_nuke = 0

            # 방 내 연구소 채우기 트리거. 예·아니오 토글
            if flag_name.includes('-fll'):
                delete_flag = True
                # 내 방 맞음?
                controlled = False
                if flags[flag_name].room.controller:
                    if flags[flag_name].room.controller.my:
                        controlled = True

                if controlled:
                    if flags[flag_name].room.memory.options.fill_labs == 1:
                        flags[flag_name].room.memory.options.fill_labs = 0
                    elif flags[flag_name].room.memory.options.fill_labs == 0:
                        flags[flag_name].room.memory.options.fill_labs = 1
                    else:
                        flags[flag_name].room.memory.options.fill_labs = 0

            # 램파트 토글.
            if flag_name.includes('-ram'):
                # 내 방 맞음?
                controlled = False
                if flags[flag_name].room.controller:
                    if flags[flag_name].room.controller.my:
                        controlled = True

                # 내 방이 아니면 이걸 돌리는 이유가없음....
                if controlled:
                    # 램파트가 열렸는가?
                    if flags[flag_name].room.memory.options.ramparts_open == 1:
                        # 그럼 닫는다.
                        flags[flag_name].room.memory.options.ramparts = 2
                    # 그럼 닫힘?
                    elif flags[flag_name].room.memory.options.ramparts_open == 0:
                        # 열어
                        flags[flag_name].room.memory.options.ramparts = 1
                    delete_flag = True

            # 타워공격 토글.
            if flag_name.includes('-tow'):
                # 내 방 맞음?
                controlled = False
                if flags[flag_name].room.controller:
                    if flags[flag_name].room.controller.my:
                        controlled = True
                # 내 방이 아니면 이걸 돌리는 이유가없음....
                if controlled:
                    if flags[flag_name].room.memory.options.tow_atk == 1:
                        flags[flag_name].room.memory.options.tow_atk = 0
                    else:
                        flags[flag_name].room.memory.options.tow_atk = 1
                    delete_flag = True

            # 디스플레이 제거. 쓸일은 없을듯 솔까.
            if flag_name.includes('-dsprm'):
                # 내 방 맞음?
                controlled = False
                if flags[flag_name].room.controller:
                    if flags[flag_name].room.controller.my:
                        controlled = True

                # 내 방이 아니면 이걸 돌리는 이유가없음....
                if controlled:
                    # 깃발꽂힌 위치값 제거.
                    flags[flag_name].room.memory.options.display = {}
                    delete_flag = True

            # 방 안 건설장 다 삭제..
            if flag_name.includes('-clr'):
                print("includes('-clr')")
                # cons = Game.flags[flag_name].room.find(FIND_CONSTRUCTION_SITES)
                world_const = Game.constructionSites
                for c in Object.keys(world_const):
                    obj = Game.getObjectById(c)
                    if obj.pos.roomName == flag_room_name:
                        obj.remove()
                # 원하는거 찾았으면 더 할 이유가 없으니.
                if found:
                    break
                delete_flag = True

            # remote 배정된 방 삭제조치.
            if flag_name.includes('-del'):
                print("includes('-del')")
                # 리모트가 아니라 자기 방으로 잘못 찍었을 경우 그냥 통과한다.
                if Game.flags[flag_name].room and Game.flags[flag_name].room.controller \
                    and Game.flags[flag_name].room.controller.my:
                    pass
                else:
                    # 방을 돌린다.
                    for i in Object.keys(Memory.rooms):
                        found = False
                        if Memory.rooms[i].options:
                            # print('Memory.rooms[{}].options.remotes {}'.format(i, Memory.rooms[i].options.remotes))
                            # 옵션안에 리모트가 없을수도 있음.. 특히 확장 안했을때.
                            if len(Memory.rooms[i].options.remotes) > 0:
                                # 리모트 안에 배정된 방이 있는지 확인한다.
                                # 아래 포문에 씀.
                                del_number = 0
                                for r in Object.keys(Memory.rooms[i].options.remotes):
                                    # print('r', r)
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
                                        # if Game.flags[flag_name].room:
                                        #     cons = Game.flags[flag_name].room.find(FIND_CONSTRUCTION_SITES)
                                        #     for c in cons:
                                        #         c.remove()
                                        break
                                    del_number += 1
                        # 원하는거 찾았으면 더 할 이유가 없으니.
                        if found:
                            break
                delete_flag = True

            # 방 안에 건물확인 스크립트 초기화 조치
            if flag_name.includes('-rset'):
                print("resetting")
                # 내 방 맞음? 내방 아니면 이거 돌 이유가 전혀없음.
                controlled = False
                if flags[flag_name].room and flags[flag_name].room.controller \
                    and flags[flag_name].room.controller.my:
                    controlled = True
                if controlled:
                    chambro.memory[options][reset] = 1
                else:
                    print(flags[flag_name].room.name, '은 내 방이 아님.')
                delete_flag = True

            if delete_flag:
                aa = flags[flag_name].remove()
                print('delete {}: {}'.format(flags[flag_name], aa))

        # 이하 진짜 리모트-------------------------------------------------

        # 렙3 이하면 그냥 무시
        if chambro.controller.level < 3:
            return

        if len(Memory.rooms[spawn.room.name].options.remotes) > 0:
            # 깃발로 돌렸던걸 메모리로 돌린다.
            for r in Object.keys(Memory.rooms[spawn.room.name].options.remotes):
                # 뒤에 점없는게 필요해서...
                room_name = r
                # if seeing the room is False - need to be scouted
                # if not Game.flags[flag].room:
                if not Game.rooms[room_name]:
                    # look for scouts
                    creep_scouts = _.filter(creeps, lambda c: c.memory.role == 'scout'
                                                              and c.memory.assigned_room == room_name)
                    if len(creep_scouts) < 1:
                        spawn_res = spawn.spawnCreep([MOVE], '🕵️_{}_{}'.format(spawn.pos.roomName, rand_int),
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
                    flag_structures = Game.rooms[room_name].find(FIND_STRUCTURES)

                    keeper_lair = False

                    for s in flag_structures:
                        if s.structureType == STRUCTURE_KEEPER_LAIR:
                            keeper_lair = True
                            break

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
                            if flag_room_controller.reservation.username \
                                != spawn.owner.username:
                                flag_room_reserved_by_other = True

                    #  렙 7부터 항시 상주한다. 단, 설정에 따라 투입자체를 안할수도 있게끔 해야함.
                    # to filter out the allies.
                    if len(hostiles) > 0 or chambro.controller.level >= 7:
                        plus = Memory.rooms[spawn.room.name].options.remotes[r].defenders
                        # 플러스가 있는 경우 병사가 상주중이므로 NPC 셀 필요가 없다.
                        if plus:
                            hostiles = miscellaneous.filter_enemies(hostiles, False)
                        else:
                            hostiles = miscellaneous.filter_enemies(hostiles, True)
                        # 적이 있거나 방이 만렙이고 상주인원이 없을 시.
                        if len(hostiles) + plus > len(remote_troops) \
                            or (len(remote_troops) < plus and chambro.controller.level == 8):
                            # 렙7 아래면 스폰 안한다.
                            if spawn.room.controller.level < 7:
                                continue

                            spawn_res = ERR_NOT_ENOUGH_RESOURCES
                            # second one is the BIG GUY. made in case invader's too strong.
                            # 임시로 0으로 놨음. 구조 자체를 뜯어고쳐야함.
                            # 원래 두 크립이 연동하는거지만 한번 없이 해보자.
                            if len(remote_troops) < len(hostiles) + plus and not keeper_lair:
                                spawn_res = spawn.spawnCreep(
                                    [TOUGH, TOUGH, TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                     MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                     MOVE, MOVE, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, HEAL, HEAL, HEAL],
                                    '🛡️_{}_{}_{}'.format(spawn.pos.roomName, room_name, rand_int),
                                    {memory: {'role': 'soldier', 'soldier': 'remote_defender',
                                              'assigned_room': room_name, 'home_room': spawn.pos.roomName}})

                            elif keeper_lair and (len(remote_troops) == 0 or len(remote_troops) < len(hostiles) + plus):
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
                                    '🛡️_{}_{}_{}'.format(spawn.pos.roomName, room_name, rand_int),
                                    {memory: {'role': 'soldier', 'soldier': 'remote_defender',
                                              'assigned_room': room_name, 'home_room': spawn.pos.roomName}})

                            if spawn_res == OK:
                                continue
                            elif spawn_res == ERR_NOT_ENOUGH_RESOURCES:
                                pass

                    # 방 안에 적이 있으면 방위병이 생길때까지 생산을 하지 않는다.
                    if len(hostiles) > 0:
                        not_spawning_troops = remote_troops.filter(lambda c: not c.spawning)
                        if not_spawning_troops:
                            pass
                        else:
                            continue

                    # 1. 리서버를 먼져 생산한다. 2. 컨트롤러 예약이 다른 플레이어에 의해 먹혔을 시 대응방안
                    # find creeps with assigned flag.
                    remote_carriers = _.filter(creeps, lambda c: c.memory.role == 'carrier'
                                                                 and c.memory.assigned_room == room_name
                                                                 and (c.spawning or c.ticksToLive > 150))
                    # exclude creeps with less than 100 life ticks so the new guy can be replaced right away
                    remote_harvesters = _.filter(creeps, lambda c: c.memory.role == 'harvester'
                                                                   and c.memory.assigned_room == room_name
                                                                   and (c.spawning or c.ticksToLive > 150))
                    remote_reservers = _.filter(creeps, lambda c: c.memory.role == 'reserver'
                                                                  and c.memory.assigned_room == room_name)

                    # resources in flag's room
                    # 멀티에 소스가 여럿일 경우 둘을 스폰할 필요가 있다.
                    flag_energy_sources = Game.rooms[room_name].find(FIND_SOURCES)

                    flag_containers = _.filter(flag_structures,
                                               lambda s: s.structureType == STRUCTURE_CONTAINER)

                    flag_built_containers = flag_containers

                    flag_lairs = _.filter(flag_structures,
                                          lambda s: s.structureType == STRUCTURE_KEEPER_LAIR)
                    flag_mineral = Game.rooms[room_name].find(FIND_MINERALS)
                    flag_constructions = Game.rooms[room_name].find(FIND_CONSTRUCTION_SITES)

                    flag_containers_const = flag_constructions.filter(lambda s: s.structureType == STRUCTURE_CONTAINER)

                    flag_containers.extend(flag_containers_const)

                    if flag_room_controller and len(remote_reservers) == 0:
                        # 예약되지 않은 컨트롤러거나
                        # 컨트롤러의 예약시간이 1200 이하거나
                        # 컨트롤러가 다른사람꺼 + 아군 주둔중일때 만든다
                        if not Game.rooms[room_name].controller.reservation \
                            or Game.rooms[room_name].controller.reservation.ticksToEnd < 1200 \
                            or (Game.rooms[room_name].controller.reservation.username
                                != spawn.room.controller.owner.username and len(remote_troops) > 0):
                            spawning_creep = spawn.spawnCreep(
                                [MOVE, MOVE, MOVE, MOVE, CLAIM, CLAIM, CLAIM, CLAIM],
                                '⛳_{}_{}_{}'.format(spawn.room.name, room_name, rand_int),
                                {memory: {'role': 'reserver', 'home_room': spawn.room.name,
                                          'assigned_room': room_name}})
                            if spawning_creep == ERR_NOT_ENOUGH_RESOURCES:
                                spawning_creep = spawn.spawnCreep(
                                    [MOVE, MOVE, CLAIM, CLAIM],
                                    '⛳_{}_{}_{}'.format(spawn.room.name, room_name, rand_int),
                                    {memory: {'role': 'reserver', 'home_room': spawn.room.name,
                                              'assigned_room': room_name}})
                            continue
                    # 캐리어가 소스 수 만큼 있는가?
                    if len(flag_energy_sources) > len(remote_carriers):
                        print('flag carrier?')
                        # 픽업으로 배정하는 것이 아니라 자원으로 배정한다.
                        if len(remote_carriers) == 0:
                            # 캐리어가 아예 없으면 그냥 첫 자원으로.
                            carrier_source = flag_energy_sources[0].id
                            target_source = Game.getObjectById(carrier_source)
                        else:
                            # 캐리어가 존재할 시. 각 소스를 돌린다.
                            for s in flag_energy_sources:

                                for c in remote_carriers:
                                    # 캐리어들을 돌려서 만약 캐리어와
                                    if s.id == c.memory.source_num:
                                        continue
                                    else:
                                        # creep.memory.source_num
                                        carrier_source = s.id
                                        # Game.getObjectById(carrier_source) << 이게 너무 길어서.
                                        target_source = Game.getObjectById(carrier_source)
                                        break

                        # creep.memory.pickup
                        carrier_pickup_id = ''

                        # 에너지소스에 담당 컨테이너가 존재하는가?
                        containter_exist = False
                        print('carrier_source 위치:', target_source.pos)
                        # loop all structures. I'm not gonna use filter. just loop it at once.
                        if len(flag_containers) > 0:
                            print('flag_containers', flag_containers)
                            closest_cont = target_source.pos.findClosestByPath(flag_containers,
                                                                               {ignoreCreeps: True})
                            print('closest_cont', closest_cont)
                            if target_source.pos.inRangeTo(closest_cont, 4):
                                containter_exist = True
                                carrier_pickup_id = closest_cont.id

                        # 컨테이너가 존재하지 않는 경우.
                        if not containter_exist:
                            # 건설장 존재여부. 있으면 참.
                            container_sites = False
                            # 건설장이 존재하는지 확인한다.
                            for gunseol in flag_constructions:
                                if target_source.pos.inRangeTo(gunseol, 3):
                                    # 존재하면 굳이 아래 돌릴필요가 없어짐.
                                    if gunseol.structureType == STRUCTURE_CONTAINER:
                                        container_sites = True
                                        break
                            # 건설중인 컨테이너가 없다? 자동으로 하나 건설한다.
                            if not container_sites:
                                # 찍을 위치정보. 소스에서 본진방향으로 두번째칸임.
                                target_to_spawn = target_source.pos.findPathTo(spawn.room.controller,
                                                                               {'ignoreCreeps': True})
                                const_loc = target_to_spawn[1]

                                print('const_loc:', const_loc)
                                print('const_loc.x {}, const_loc.y {}'.format(const_loc.x, const_loc.y))
                                print('Game.rooms[{}].name: {}'.format(room_name, Game.rooms[room_name].name))
                                # 찍을 좌표: 이게 제대로된 pos 함수
                                constr_pos = __new__(RoomPosition(const_loc.x, const_loc.y
                                                                  , Game.rooms[room_name].name))
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
                                    constr_pos = __new__(RoomPosition(const_loc.x, const_loc.y
                                                                      , Game.rooms[room_name].name))
                                    print('constr_pos:', constr_pos)
                                    const_res = constr_pos.createConstructionSite(STRUCTURE_CONTAINER)

                                # ignore placing roads around sources and controllers alike as much as possible.
                                # 무조건 막을수는 없고, 정 다른길이 없으면 가게끔.
                                objs = flag_energy_sources

                                if flag_room_controller:
                                    objs.append(flag_room_controller)
                                # does this room have keeper lairs?
                                if len(flag_mineral) > 0:
                                    objs.extend(flag_mineral)
                                print('objs', objs)
                                # 키퍼가 있으면 중간에 크립도 있는지라.
                                if keeper_lair:
                                    opts = {'trackCreeps': True, 'refreshMatrix': True,
                                            'costByArea': {'objects': objs, 'size': 1, 'cost': 6}}
                                else:
                                    opts = {'trackCreeps': False, 'refreshMatrix': True,
                                            'costByArea': {'objects': objs, 'size': 1, 'cost': 6}}
                                # RoomPosition 목록. 컨테이너 건설한 김에 길도 깐다.
                                constr_roads_pos = \
                                    PathFinder.search(constr_pos, spawn.pos,
                                                      {'plainCost': 3, 'swampCost': 3,
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

                        # 대충 해야하는일: 캐리어의 픽업위치에서 본진거리 확인. 그 후 거리만큼 추가.
                        if Game.getObjectById(carrier_pickup_id):
                            # 크립의 크기는 본진까지의 거리에 따라 좌우된다.
                            distance = 0

                            path = PathFinder.search(Game.getObjectById(carrier_pickup_id).pos, spawn.pos,
                                                     {'plainCost': 3, 'swampCost': 3,
                                                      'roomCallback':
                                                          lambda room_name:
                                                          pathfinding.Costs(room_name, None).load_matrix()
                                                      }, ).path
                            for p in path:
                                if p.roomName == spawn.room.name:
                                    break
                                distance += 1

                            # 만일 키퍼가 있으면 다 4000짜리니 그만큼 한번에 수확가능한 자원이 많아짐. 그거 반영.
                            if keeper_lair:
                                distance = int(distance * 1.3)

                            if Game.getObjectById(carrier_pickup_id).hits \
                                <= Game.getObjectById(carrier_pickup_id).hitsMax * .6 \
                                or len(flag_constructions) > 0:

                                work_chance = 1
                            else:
                                work_chance = random.randint(0, 1)
                            # 굳이 따로 둔 이유: 캐리 둘에 무브 하나.
                            carry_body_odd = [CARRY]
                            carry_body_even = [CARRY, MOVE]
                            work_body = [WORK, WORK, MOVE]
                            body = []

                            carrier_size = int(distance / 2)
                            # 소수점 다 올림처리.
                            if distance % 2 > 0:
                                carrier_size += 1
                            carrier_size += random.randint(0, 1)
                            # 여기서 값을 넣는다.
                            for i in range(carrier_size):
                                # work 부분부터 넣어본다.
                                if work_chance == 1:
                                    if i < 3:
                                        body.extend(work_body)
                                # 이거부터 들어가야함
                                if i % 2 == 0:
                                    body.extend(carry_body_even)
                                else:
                                    body.extend(carry_body_odd)

                            # 크기가 50을 넘기면? 50에 맞춰야함.
                            if len(body) > 50:
                                # WORK 가 있을경우
                                if work_chance:
                                    body = [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                            MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY]
                                else:
                                    body = [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                            MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY]

                            spawning = spawn.spawnCreep(body,
                                                        '🚂_{}_{}_{}'.format(spawn.pos.roomName, room_name, rand_int),
                                                        {memory: {'role': 'carrier',
                                                                  'assigned_room': room_name,
                                                                  'home_room': spawn.pos.roomName,
                                                                  'pickup': carrier_pickup_id, 'work': work_chance,
                                                                  'source_num': carrier_source}})
                            print('spawning', spawning)
                            if spawning == 0:
                                continue
                            elif spawning == ERR_NOT_ENOUGH_RESOURCES:

                                body = []

                                # carrier_size = int(distance / 2)
                                # # 소수점 다 올림처리.
                                # if distance % 2 > 0:
                                #     carrier_size += 1
                                # 여기서 값을 넣는다.
                                carrier_size = int(carrier_size * 5 / 6)
                                if work_chance == 1:
                                    body.extend(work_body)
                                for i in range(carrier_size):
                                    # 이거부터 들어가야함
                                    if i % 2 == 0:
                                        body.extend(carry_body_even)
                                    else:
                                        body.extend(carry_body_odd)

                                print('2nd body({}): {}'.format(len(body), body))
                                spawning = spawn.spawnCreep(
                                    body,
                                    '🚂_{}_{}_{}'.format(spawn.pos.roomName, room_name, rand_int),
                                    {memory: {'role': 'carrier',
                                              'assigned_room': room_name, 'home_room': spawn.pos.roomName,
                                              'pickup': carrier_pickup_id, 'work': work_chance,
                                              'source_num': carrier_source}})

                                print('spawning {}'.format(spawning))
                                continue
                        # 픽업이 존재하지 않는다는건 현재 해당 건물이 없다는 뜻이므로 새로 지어야 함.
                        else:
                            # 중간에 프론티어가 붙은 이유: 이거 속성 건설용이기 때문에 운송용으로 쓸 수 없음.
                            spawning = spawn.spawnCreep(
                                [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                 WORK, WORK, WORK, CARRY, CARRY],
                                '🚂_{}_{}_{}'.format(spawn.pos.roomName, room_name, rand_int),
                                {memory: {'role': 'carrier', 'assigned_room': room_name,
                                          'work': 1, 'home_room': spawn.room.name,
                                          'source_num': carrier_source, 'frontier': 1}})
                            if spawning == ERR_NOT_ENOUGH_RESOURCES:
                                spawn.spawnCreep(
                                    [WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE,
                                     MOVE, MOVE, MOVE, MOVE],
                                    '🚂_{}_{}_{}'.format(spawn.pos.roomName, room_name, rand_int),
                                    {memory: {'role': 'carrier', 'assigned_room': room_name,
                                              'work': 1, 'home_room': spawn.room.name,
                                              'source_num': carrier_source, 'frontier': 1}})
                            continue

                    # 하베스터도 소스 수 만큼! 정확히는 컨테이너 건설여부에 따라 만들어줘야 하는데... 몰라 ㅅㅂ 안해
                    elif len(flag_built_containers) > len(remote_harvesters):
                        # 4000 for keeper lairs
                        # todo 너무 쉽게죽음. 보강필요. and need medic for keeper remotes
                        regular_spawn = -6
                        if keeper_lair:
                            regular_spawn = spawn.spawnCreep(
                                [TOUGH, TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                 WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                 CARRY, CARRY, CARRY, CARRY],
                                "🌽_{}_{}".format(spawn.pos.roomName, rand_int),
                                {memory: {'role': 'harvester', 'assigned_room': room_name,
                                          'home_room': spawn.room.name,
                                          'size': 2}})

                        # perfect for 3000 cap
                        if regular_spawn == -6:
                            regular_spawn = spawn.spawnCreep(
                                [WORK, WORK, WORK, WORK, WORK, WORK,
                                 CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE,
                                 MOVE, MOVE],
                                "🌽_{}_{}".format(spawn.pos.roomName, rand_int),
                                {memory: {'role': 'harvester', 'assigned_room': room_name,
                                          'home_room': spawn.room.name,
                                          'size': 2}})
                        # print('what happened:', regular_spawn)
                        if regular_spawn == -6:
                            spawn.spawnCreep([WORK, WORK, WORK, WORK, WORK,
                                              CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE],
                                             "🌽_{}_{}".format(spawn.pos.roomName, rand_int),
                                             {memory: {'role': 'harvester', 'assigned_room': room_name,
                                                       'home_room': spawn.room.name}})
                            continue
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
                                    if spawn.room.controller.level < 7:
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
        display_loc = display_location(spawn, spawns_and_links)
        # print(display_loc['x'])
        # print(display_loc['y'])
        # print(display_loc['align'])
        # print(spawn.pos.x + display_loc['x'], spawn.pos.y + display_loc['y'], display_loc['align'])
        # if spawn.pos.x > 44:
        #     align = 'right'
        # else:
        #     align = 'left'

        # todo 디스플레이 부분 위치조정 필요. 다섯칸 간격이면 적당할듯.
        # 벽은 7칸으로.
        # showing process of the spawning creep by %
        spawning_creep = Game.creeps[spawn.spawning.name]
        spawn.room.visual.text(
            '🛠 ' + spawning_creep.memory.role + ' '
            + "{}/{}".format(spawn.spawning.remainingTime - 1, spawn.spawning.needTime),
            spawn.pos.x + display_loc['x'],
            spawn.pos.y + display_loc['y'],
            {'align': display_loc['align'], 'opacity': 0.8, 'color': '#EE5927'}
        )
    else:
        # 1/3 chance healing
        randint = random.randint(1, 4)
        if randint != 1:
            return
        # 이 곳에 필요한거: spawn 레벨보다 같거나 높은 애들 지나갈 때 TTL이 오백 이하면 회복시켜준다.
        # room controller lvl ± 2 에 부합한 경우에만 수리를 실시한다.
        level = spawn.room.controller.level
        for creep in room_creeps:
            # 방 안에 있는 크립 중에 회복대상자
            if (100 < creep.ticksToLive < 500) and creep.memory.level >= level:
                if spawn.pos.isNearTo(creep):
                    result = spawn.renewCreep(creep)
                    break
