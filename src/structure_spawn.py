from defs import *
import random
import miscellaneous
import pathfinding

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


# 스폰을 메인에서 쪼개기 위한 용도. 현재 어떻게 빼내야 하는지 감이 안잡혀서 공백임.
def run_spawn(spawn, all_structures, room_creeps, hostile_creeps, divider, counter, cpu_bucket_emergency
              , cpu_bucket_emergency_spawn_start, extractor, terminal_capacity, chambro, interval):
    # print('yolo')
    spawn_cpu = Game.cpu.getUsed()
    # if spawn is not spawning, try and make one i guess.
    # spawning priority: harvester > hauler > upgrader > melee > etc.
    # checks every 10 + len(Game.spawns) ticks
    if not spawn.spawning and Game.time % counter == divider:

        # print('inside spawning check')
        spawn_chk_cpu = Game.cpu.getUsed()

        hostile_around = False
        # 적이 스폰 주변에 있으면 생산 안한다. 추후 수정해야함.

        if hostile_creeps:
            for enemy in hostile_creeps:
                if spawn.pos.inRangeTo(enemy, 2):
                    hostile_around = True
                    break
        if hostile_around:
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
        creep_home_defenders = _.filter(creeps, lambda c: (c.memory.role == 'h_defender'
                                                           and c.memory.assigned_room == spawn.pos.roomName
                                                           and (c.spawning or
                                                                (c.ticksToLive > 200 and c.hits > c.hitsMax * .5)
                                                                )))
        creep_miners = _.filter(creeps, lambda c: (c.memory.role == 'miner'
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
                # 세칸이내에 존재하는가?
                if s.structureType == STRUCTURE_CONTAINER and rs.pos.inRangeTo(s, 3):
                    # 실제 거리도 세칸 이내인가?
                    if len(rs.pos.findPathTo(s, {'ignoreCreeps': True})) <= 3:
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
                regular_spawn = spawn.createCreep(
                    [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK,
                     WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY], undefined,
                    {'role': 'harvester', 'assigned_room': spawn.pos.roomName, 'size': 2})
            else:
                # perfect for 3000 cap
                regular_spawn = spawn.createCreep(
                    [WORK, WORK, WORK, WORK, WORK, WORK,
                     CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE], undefined,
                    {'role': 'harvester', 'assigned_room': spawn.pos.roomName, 'size': 2})
            # print('what happened:', regular_spawn)
            if regular_spawn == -6:
                # one for 1500 cap == need 2
                if spawn.createCreep(
                        [WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE], undefined,
                        {'role': 'harvester', 'assigned_room': spawn.pos.roomName, 'size': 1}) == -6:
                    # final barrier
                    spawn.createCreep([MOVE, WORK, WORK, CARRY], undefined,
                                      {'role': 'harvester', 'assigned_room': spawn.pos.roomName, 'size': 1})
            return

        plus = 0
        for harvest_container in harvest_carry_targets:
            # Ĉar uzi getObjectById k.t.p estas tro longa.
            harvest_target = Game.getObjectById(harvest_container)
            # 컨테이너.
            if harvest_target.structureType == STRUCTURE_CONTAINER:
                if _.sum(harvest_target.store) >= harvest_target.storeCapacity * .6:
                    plus += 1
            # 링크.
            elif harvest_target.structureType == STRUCTURE_LINK:
                # 링크가 꽉차고 + 쿨다운 0일때 1추가.
                if harvest_target.energy == harvest_target.energyCapacity \
                        and harvest_target.cooldown == 0:
                    for l in Memory.rooms[spawn.room.name][STRUCTURE_LINK]:
                        if l.id == harvest_target.id and not l.for_store:
                            for rs in room_sources:
                                if len(harvest_target.pos.findPathTo(rs, {'ignoreCreep': True})) < 5:
                                    print('l.id {} == harvest_target.id {}, energy: {}'
                                          .format(l.id, harvest_target.id, harvest_target.energy))
                                    plus += 1
                                    break

        # 건물이 아예 없을 시
        if len(harvest_carry_targets) == 0:
            plus = -num_o_sources

        # 허울러 수 계산법: 방별로 지정된 허울러(기본값 2) + 위에 변수값
        hauler_capacity = Memory.rooms[spawn.room.name].options.haulers + plus
        # minimum number of haulers in the room is 1, max 4
        if hauler_capacity <= 0:
            hauler_capacity = 1
        elif hauler_capacity > 4:
            hauler_capacity = 4

        if spawn.room.terminal:
            if spawn.room.terminal.store.energy > terminal_capacity + 10000:
                hauler_capacity += 1

        if len(creep_haulers) < hauler_capacity:
            # 초기화 용도.
            spawning_creep = ERR_NOT_ENOUGH_ENERGY
            # 순서는 무조건 아래와 같다. 무조건 덩치큰게 장땡.
            # 만일 컨트롤러 레벨이 8일 경우 가장 WORK 높은애 우선 하나.
            if spawn.room.controller.level == 8:
                spawning_creep = spawn.createCreep(
                    [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                     MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                     CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                     CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY],
                    undefined, {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                'level': 8})

            # 1200
            if len(creep_haulers) >= 2:
                if spawning_creep == ERR_NOT_ENOUGH_ENERGY:
                    spawning_creep = spawn.createCreep(
                        [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                         MOVE, WORK,
                         WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                         CARRY,
                         CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                         CARRY,
                         CARRY, CARRY],
                        undefined, {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                    'level': 8})
            else:
                spawning_creep = ERR_NOT_ENOUGH_ENERGY

            # 800
            if spawning_creep == ERR_NOT_ENOUGH_ENERGY:
                spawning_creep = spawn.createCreep(
                    [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, CARRY,
                     CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                     CARRY, CARRY],
                    undefined, {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                'level': 8})

            if spawning_creep == ERR_NOT_ENOUGH_ENERGY:
                # 600
                spawning_creep = spawn.createCreep(
                    [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                     CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY],
                    undefined, {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                'level': 8})

            if spawning_creep == ERR_NOT_ENOUGH_ENERGY:
                # 250
                spawning_creep = spawn.createCreep([WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
                                                    CARRY, CARRY, MOVE, MOVE, MOVE, MOVE, MOVE],
                                                   undefined,
                                                   {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                                    'level': 5})

            if spawning_creep == ERR_NOT_ENOUGH_ENERGY:
                if spawn.createCreep([WORK, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE], undefined,
                                     {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                      'level': 2}) == -6:
                    spawn.createCreep([MOVE, MOVE, WORK, CARRY, CARRY], undefined,
                                      {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
                                       'level': 0})

            return

        # todo NULLIFIED - need one for ranged one too.
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
                        spawning_creep = spawn.createCreep(
                            [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                             WORK,
                             WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                             WORK,
                             WORK, WORK, CARRY], undefined,
                            {'role': 'miner', 'assigned_room': spawn.pos.roomName,
                             'level': 5})
                        if spawning_creep == ERR_NOT_ENOUGH_RESOURCES:
                            spawning_creep = spawn.createCreep(
                                [MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                 WORK,
                                 WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY],
                                undefined,
                                {'role': 'miner', 'assigned_room': spawn.pos.roomName})

                        if spawning_creep == 0:
                            return

        # 업그레이더는 버켓 비상 근접시부터 생산 고려 자체를 안한다.
        if Game.cpu.bucket > cpu_bucket_emergency + cpu_bucket_emergency_spawn_start:

            if spawn.room.controller.level == 8:
                proper_level = 1
            # start making upgraders after there's a storage
            elif spawn.room.controller.level > 2 and spawn.room.storage:

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
                    # max upgraders: 12
                    if proper_level > 12:
                        proper_level = 12
                else:
                    proper_level = 0
            elif spawn.room.energyCapacityAvailable <= 1000:
                # 어차피 여기올쯤이면 소형애들만 생성됨.
                proper_level = 4
            else:
                proper_level = 0

            if len(creep_upgraders) < proper_level:
                if spawn.room.controller.level != 8:
                    big = spawn.createCreep(
                        [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK,
                         WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY]
                        , undefined,
                        {'role': 'upgrader', 'assigned_room': spawn.pos.roomName, 'level': 5})
                else:
                    big = -6

                # 스폰렙 만땅이면 쿨다운 유지만 하면됨....
                if spawn.room.controller.level == 8:
                    if spawn.room.controller.ticksToDowngrade < CONTROLLER_DOWNGRADE[8] - 100000 \
                            or (spawn.room.controller.ticksToDowngrade < CONTROLLER_DOWNGRADE[8] - 4900
                                and len(hostile_creeps) > 0):
                        spawn.createCreep([WORK, WORK, CARRY, CARRY, MOVE, MOVE], undefined,
                                          {'role': 'upgrader', 'assigned_room': spawn.pos.roomName})
                elif big == -6:
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
                    Memory.rooms[spawn.room.name].options.remotes = []

                # 혹시 다른방에 이 방이 이미 소속돼있는지도 확인한다. 있으면 없앤다.
                for i in Object.keys(Memory.rooms):
                    # 같은방은 건들면 안됨...
                    if i == spawn.room.name:
                        continue
                    found_and_deleted = False
                    if Memory.rooms[i].options:
                        print('? yolo?')
                        if Memory.rooms[i].options.remotes:
                            for r in Memory.rooms[i].options.remotes:
                                if r.roomName == Game.flags[flag_name].room.name:
                                    del r
                                    found_and_deleted = True
                                    break
                    if found_and_deleted:
                        break
                # 방이 추가됐는지에 대한 불리언.
                room_added = False
                # 이미 방이 있는지 확인한다.
                for r in Memory.rooms[spawn.room.name].options.remotes:
                    # 있으면 굳이 또 추가할 필요가 없음..
                    if r.roomName == Game.flags[flag_name].pos.roomName:
                        room_added = True
                        break
                print('room added?', room_added)
                # 추가가 안된 상태면 초기화를 진행
                if not room_added:
                    init = {'roomName': Game.flags[flag_name].pos.roomName, 'defenders': 1, 'initRoad': 0,
                            'display': {'x': Game.flags[flag_name].pos.x, 'y': Game.flags[flag_name].pos.y}}
                    Memory.rooms[spawn.room.name].options.remotes.append(init)

                delete_flag = True

            # 아래부터 값을 쪼개는데 필요함.
            name_list = flag_name.split()

            # 주둔할 병사 수 재정의
            if flag_name.includes('-def'):
                print("includes('-def')")
                number_added = False
                included = name_list.index('-def')
                # 트라이에 걸린다는건 숫자 빼먹었거나 숫자가 아니라는거.
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
                        if Memory.rooms[i].options.remotes:
                            for r in Memory.rooms[i].options.remotes:
                                if r.roomName == flag_room_name:
                                    r.defenders = number
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
                                counter_num = 0
                                for r in Memory.rooms[chambra_nomo].options.remotes:
                                    remote_room_name = r.roomName
                                    # 방이름 이거랑 똑같은지.
                                    # 안똑같으면 통과
                                    if remote_room_name != flags[flag_name].pos.roomName:
                                        print('{} != flags[{}].pos.roomName {}'
                                              .format(remote_room_name, flag_name, flags[flag_name].pos.roomName))
                                        pass
                                    else:
                                        print('Memory.rooms[chambra_nomo].options.remotes[counter_num].display'
                                              , Memory.rooms[chambra_nomo].options.remotes[counter_num].display)
                                        if not Memory.rooms[chambra_nomo].options.remotes[counter_num].display:
                                            Memory.rooms[chambra_nomo].options.remotes[counter_num].display = {}
                                        rx = flags[flag_name].pos.x
                                        ry = flags[flag_name].pos.y
                                        Memory.rooms[chambra_nomo].options.remotes[counter_num].display.x = rx
                                        Memory.rooms[chambra_nomo].options.remotes[counter_num].display.y = ry
                                        set_loc = True
                                    counter_num += 1
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
                cons = Game.flags[flag_name].room.find(FIND_CONSTRUCTION_SITES)

                for c in cons:
                    c.remove()
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
                                for r in Memory.rooms[i].options.remotes:
                                    # print('r', r)
                                    # 배정된 방을 찾으면 이제 방정보 싹 다 날린다.
                                    if r.roomName == flag_room_name:
                                        del_number = Memory.rooms[i].options.remotes.index(r)
                                        print(
                                            'deleting roomInfo Memory.rooms[{}].options.remotes[{}]'
                                                .format(i, del_number))
                                        Memory.rooms[i].options.remotes.splice(del_number, 1)
                                        found = True
                                        # 방에 짓고있는것도 다 취소
                                        if Game.flags[flag_name].room:
                                            cons = Game.flags[flag_name].room.find(FIND_CONSTRUCTION_SITES)
                                            for c in cons:
                                                c.remove()
                        # 원하는거 찾았으면 더 할 이유가 없으니.
                        if found:
                            break
                delete_flag = True

            if delete_flag:
                aa = flags[flag_name].remove()

        if len(Memory.rooms[spawn.room.name].options.remotes) > 0:
            # 깃발로 돌렸던걸 메모리로 돌린다.
            for r in Memory.rooms[spawn.room.name].options.remotes:
                # 뒤에 점없는게 필요해서...
                room_name = r.roomName
                # if seeing the room is False - need to be scouted
                # if not Game.flags[flag].room:
                if not Game.rooms[room_name]:
                    # look for scouts
                    creep_scouts = _.filter(creeps, lambda c: c.memory.role == 'scout'
                                                              and c.memory.assigned_room == room_name)
                    if len(creep_scouts) < 1:
                        spawn_res = spawn.createCreep([MOVE], 'Scout-' + room_name + str(random.randint(0, 50)),
                                                      {'role': 'scout', 'assigned_room': room_name})
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

                    #  렙 8부터 항시 상주한다. 단, 설정에 따라 투입자체를 안할수도 있게끔 해야함.
                    # to filter out the allies.
                    if len(hostiles) > 0 or chambro.controller.level == 8:
                        plus = r.defenders

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
                                spawn_res = spawn.createCreep(
                                    [TOUGH, TOUGH, TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                     MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                     MOVE, MOVE, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, HEAL, HEAL, HEAL]
                                    , undefined, {'role': 'soldier', 'soldier': 'remote_defender'
                                        , 'assigned_room': room_name
                                        , 'home_room': spawn.room.name})

                            elif keeper_lair and (len(remote_troops) == 0 or len(remote_troops) < len(hostiles) + plus):
                                spawn_res = spawn.createCreep(
                                    # think this is too much for mere invaders
                                    [TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE
                                        , MOVE,
                                     MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE
                                        , MOVE,
                                     MOVE, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, HEAL, HEAL, HEAL]
                                    , undefined, {'role': 'soldier', 'soldier': 'remote_defender'
                                        , 'assigned_room': room_name
                                        , 'home_room': spawn.room.name})

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
                                                                   and (c.spawning or c.ticksToLive > 120))
                    remote_reservers = _.filter(creeps, lambda c: c.memory.role == 'reserver'
                                                                  and c.memory.assigned_room == room_name)

                    # resources in flag's room
                    # 멀티에 소스가 여럿일 경우 둘을 스폰할 필요가 있다.
                    flag_energy_sources = Game.rooms[room_name].find(FIND_SOURCES)

                    flag_containers = _.filter(flag_structures,
                                               lambda s: s.structureType == STRUCTURE_CONTAINER)

                    flag_lairs = _.filter(flag_structures,
                                          lambda s: s.structureType == STRUCTURE_KEEPER_LAIR)
                    flag_mineral = Game.rooms[room_name].find(FIND_MINERALS)
                    flag_constructions = Game.rooms[room_name].find(FIND_CONSTRUCTION_SITES)

                    if flag_room_controller and len(remote_reservers) == 0:
                        # 예약되지 않은 컨트롤러거나
                        # 컨트롤러의 예약시간이 1200 이하거나
                        # 컨트롤러가 다른사람꺼 + 아군 주둔중일때 만든다
                        if not Game.rooms[room_name].controller.reservation \
                                or Game.rooms[room_name].controller.reservation.ticksToEnd < 1200 \
                                or (Game.rooms[room_name].controller.reservation.username
                                    != spawn.room.controller.owner.username and len(remote_troops) > 0):
                            spawning_creep = spawn.createCreep(
                                [MOVE, MOVE, MOVE, MOVE, CLAIM, CLAIM, CLAIM, CLAIM]
                                , undefined,
                                {'role': 'reserver', 'home_room': spawn.room.name,
                                 'assigned_room': room_name})
                            if spawning_creep == ERR_NOT_ENOUGH_RESOURCES:
                                spawning_creep = spawn.createCreep(
                                    [MOVE, MOVE, CLAIM, CLAIM]
                                    , undefined,
                                    {'role': 'reserver', 'home_room': spawn.room.name,
                                     'assigned_room': room_name})
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
                        for st in flag_containers:
                            # 컨테이너만 따진다.
                            if st.structureType == STRUCTURE_CONTAINER:
                                # 가까이 있으면 하나의 컨테이너로 퉁치기.
                                # 소스 세칸 이내에 컨테이너가 있는가? 있으면 carrier_pickup으로 배정
                                if target_source.pos.inRangeTo(st, 3):
                                    containter_exist = True
                                    carrier_pickup_id = st.id
                                    break
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
                                const_loc = target_source.pos.findPathTo(spawn.room.controller
                                                                         , {'ignoreCreeps': True})[1]

                                print('const_loc:', const_loc)
                                print('const_loc.x {}, const_loc.y {}'.format(const_loc.x, const_loc.y))
                                print('Game.rooms[{}].name: {}'.format(room_name, Game.rooms[room_name].name))
                                # 찍을 좌표: 이게 제대로된 pos 함수
                                constr_pos = __new__(RoomPosition(const_loc.x, const_loc.y
                                                                  , Game.rooms[room_name].name))
                                print('constr_pos:', constr_pos)
                                constr_pos.createConstructionSite(STRUCTURE_CONTAINER)

                                # ignore placing roads around sources and controllers alike as much as possible.
                                # 무조건 막을수는 없고, 정 다른길이 없으면 가게끔.
                                objs = flag_energy_sources

                                if flag_room_controller:
                                    objs.push(flag_room_controller)
                                # does this room have keeper lairs?
                                # if len(flag_lairs) > 0:
                                #     objs.extend(flag_lairs)
                                if len(flag_mineral) > 0:
                                    objs.extend(flag_mineral)

                                # 키퍼가 있으면 중간에 크립도 있는지라.
                                if keeper_lair:
                                    opts = {'trackCreeps': True,
                                            'costByArea': {'objects': [objs], 'size': 1, 'cost': 6}}
                                else:
                                    opts = {'trackCreeps': False,
                                            'costByArea': {'objects': [objs], 'size': 1, 'cost': 6}}

                                # RoomPosition 목록. 컨테이너 건설한 김에 길도 깐다.
                                constr_roads_pos = \
                                    PathFinder.search(constr_pos, spawn.pos,
                                                      {'plainCost': 2, 'swampCost': 2,
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
                                                     {'plainCost': 2, 'swampCost': 2,
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
                            # carry_body_odd = [MOVE, CARRY, CARRY, CARRY]
                            # carry_body_even = [MOVE, MOVE, CARRY, CARRY, CARRY]
                            carry_body_odd = [CARRY]
                            carry_body_even = [CARRY, MOVE]
                            carry_body_extra = [MOVE, CARRY]
                            work_body = [WORK, WORK, MOVE]
                            body = []

                            carrier_size = int(distance / 2)
                            # 소수점 다 올림처리.
                            if distance % 2 > 0:
                                carrier_size += 1
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

                            spawning = spawn.createCreep(body, undefined,
                                                         {'role': 'carrier',
                                                          'assigned_room': room_name,
                                                          'home_room': spawn.room.name,
                                                          'pickup': carrier_pickup_id
                                                             , 'work': work_chance,
                                                          'source_num': carrier_source})
                            print('spawning', spawning)
                            if spawning == 0:
                                continue
                            elif spawning == ERR_NOT_ENOUGH_RESOURCES:

                                body = []

                                if work_chance == 1:
                                    body.extend(work_body)
                                # 15% 몸집을 줄여본다.
                                if int(distance / 7) == 0:
                                    distance = 1
                                else:
                                    distance = int(distance / 7)
                                    if distance % 7 > 0:
                                        carrier_size += 1
                                for i in range(distance):
                                    if i % 2 == 0:
                                        body.extend(carry_body_even)
                                    else:
                                        body.extend(carry_body_odd)

                                print('2nd body({}): {}'.format(len(body), body))
                                spawning = spawn.createCreep(
                                    body,
                                    undefined,
                                    {'role': 'carrier', 'assigned_room': room_name,
                                     'pickup': carrier_pickup_id, 'work': work_chance
                                        , 'home_room': spawn.room.name, 'source_num': carrier_source})

                                print('spawning {}'.format(spawning))
                                continue
                        # 픽업이 존재하지 않는다는건 현재 해당 건물이 없다는 뜻이므로 새로 지어야 함.
                        else:
                            # 중간에 프론티어가 붙은 이유: 이거 속성 건설용이기 때문에 운송용으로 쓸 수 없음.
                            spawning = spawn.createCreep(
                                [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                 WORK, WORK, WORK, CARRY, CARRY],
                                undefined,
                                {'role': 'carrier', 'assigned_room': room_name
                                    , 'work': 1, 'home_room': spawn.room.name
                                    , 'source_num': carrier_source, 'frontier': 1})
                            if spawning == ERR_NOT_ENOUGH_RESOURCES:
                                spawn.createCreep(
                                    [WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE,
                                     MOVE, MOVE, MOVE, MOVE],
                                    undefined,
                                    {'role': 'carrier', 'assigned_room': room_name,
                                     'work': 1, 'home_room': spawn.room.name
                                        , 'source_num': carrier_source, 'frontier': 1})
                            continue

                    # elif len(flag_containers) > len(remote_harvesters):
                    # 하베스터도 소스 수 만큼!
                    elif len(flag_energy_sources) > len(remote_harvesters):
                        # 4000 for keeper lairs
                        # todo 너무 쉽게죽음. 보강필요. and need medic for keeper remotes
                        regular_spawn = -6
                        if keeper_lair:
                            regular_spawn = spawn.createCreep(
                                [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                 CARRY, CARRY, CARRY, CARRY], undefined,
                                {'role': 'harvester', 'assigned_room': room_name,
                                 'home_room': spawn.room.name,
                                 'size': 2})

                        # perfect for 3000 cap
                        if regular_spawn == -6:
                            regular_spawn = spawn.createCreep(
                                [WORK, WORK, WORK, WORK, WORK, WORK,
                                 CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE,
                                 MOVE, MOVE]
                                , undefined,
                                {'role': 'harvester', 'assigned_room': room_name,
                                 'home_room': spawn.room.name,
                                 'size': 2})
                        # print('what happened:', regular_spawn)
                        if regular_spawn == -6:
                            spawn.createCreep([WORK, WORK, WORK, WORK, WORK,
                                               CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE]
                                              , undefined,
                                              {'role': 'harvester', 'assigned_room': room_name
                                                  , 'home_room': spawn.room.name})
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
        if spawn.pos.x > 44:
            align = 'right'
        else:
            align = 'left'

        # showing process of the spawning creep by %
        spawning_creep = Game.creeps[spawn.spawning.name]
        spawn.room.visual.text(
            '🛠 ' + spawning_creep.memory.role + ' '
            + "{}/{}".format(spawn.spawning.remainingTime - 1, spawn.spawning.needTime),
            spawn.pos.x + 1,
            spawn.pos.y,
            {'align': align, 'opacity': 0.8}
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
