from defs import *
import random
import miscellaneous

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
        # print('until hostile check {} cpu'.format(round(Game.cpu.getUsed() - spawn_chk_cpu, 2)))
        # ALL flags.
        flags = Game.flags
        flag_name = []

        # check all flags with same name with the spawn.
        for name in Object.keys(flags):
            flag_cpu = Game.cpu.getUsed()
            # 방이름 + -rm + 아무글자(없어도됨)
            regex = spawn.room.name + r'-rm.*'
            if name.includes(spawn.room.name) and name.includes("-rm"):
                # if re.match(regex, name, re.IGNORECASE):
                # if there is, get it's flag's name out.
                flag_name.append(flags[name].name)
        #     print('one flag loop cpu {}'.format(round(Game.cpu.getUsed() - flag_cpu, 2)))
        # print('flag names: {}'.format(flag_name))
        # print('cpu before the loop: {}'.format(round(Game.cpu.getUsed() - spawn_chk_cpu, 2)))

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
        creep_miners = _.filter(creeps, lambda c: (c.memory.role == 'miner'
                                                   and c.memory.assigned_room == spawn.pos.roomName
                                                   and (c.spawning or c.ticksToLive > 150)))
        # cpu 비상시 고려 자체를 안한다.
        if Game.cpu.bucket > cpu_bucket_emergency + cpu_bucket_emergency_spawn_start:
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
        # print('ext at room {}: {}'.format(chambra_nomo, extractor))
        # 소스 주변에 자원채취용 컨테이너·링크가 얼마나 있는가 확인.
        for rs in room_sources:
            for s in containers_and_links:
                # 세칸이내에 존재하는가?
                if rs.pos.inRangeTo(s, 3):
                    # 실제 거리도 세칸 이내인가?
                    if len(rs.pos.findPathTo(s, {'ignoreCreeps': True})) <= 3:
                        # 여기까지 들어가있으면 요건충족한거.
                        harvest_carry_targets.push(s.id)
                        break

        # print('harvest_carry_targets', harvest_carry_targets)
        # print('sources', sources)
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
            return

        plus = 0
        for harvest_container in harvest_carry_targets:
            # Ĉar uzi getObjectById k.t.p estas tro longa.
            harvest_target = Game.getObjectById(harvest_container)
            # 컨테이너.
            if harvest_target.structureType == STRUCTURE_CONTAINER:
                if _.sum(harvest_target.store) > harvest_target.storeCapacity * .9:
                    plus += 1
                elif _.sum(harvest_target.store) <= harvest_target.storeCapacity * .3:
                    plus -= 1
            # 링크.
            else:
                # if harvest_target.energy == harvest_target.energyCapacity and harvest_target.cooldown == 0:
                #     plus += 1
                if harvest_target.energy <= harvest_target.energyCapacity * .8 or harvest_target.cooldown != 0:
                    plus -= 1

        # 건물이 아예 없을 시
        if len(harvest_carry_targets) == 0:
            plus = -num_o_sources

        hauler_capacity = num_o_sources + 1 + plus
        # minimum number of haulers in the room is 1, max 4
        if hauler_capacity <= 0:
            hauler_capacity = 1
        elif hauler_capacity > 4:
            hauler_capacity = 4

        if spawn.room.terminal:
            if spawn.room.terminal.store.energy > terminal_capacity + 10000:
                hauler_capacity += 1

        if len(creep_haulers) < hauler_capacity:
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

        # print('익스트랙터 {} 광부 {}'.format(extractor, creep_miners))

        # if there's an extractor, make a miner.
        if bool(extractor):
            if bool(len(creep_miners) == 0):
                # print('extractor', extractor)
                # print("extractor: ", bool(extractor))
                # print("len(creep_miners) == 0:", bool(len(creep_miners) == 0))
                # continue
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
            plus = 0
            if len(creep_upgraders) < 2:
                if spawn.room.controller.level == 8:
                    prime_num = 6491
                else:
                    prime_num = 49999
                # some prime number.
                if Game.time % prime_num < 11:
                    plus = 1
                if spawn.room.controller.ticksToDowngrade < 10000:
                    plus += 1

            if spawn.room.controller.level == 8:
                proper_level = 0
            # start making upgraders after there's a storage
            elif spawn.room.controller.level > 2 and spawn.room.storage:

                # if spawn.room.controller.level < 5:
                expected_reserve = 3000
                # else:
                #     expected_reserve = 3000

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

            if len(creep_upgraders) < proper_level + plus:
                if spawn.room.controller.level != 8:
                    big = spawn.createCreep(
                        [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK,
                         WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY]
                        , undefined,
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

        if Memory.debug or Game.time % interval == 0 or Memory.tick_check:
            print("이 시점까지 스폰 {} 소모량: {}, 이하 remote"
                  .format(spawn.name, round(Game.cpu.getUsed() - spawn_cpu, 2)))

        # REMOTE---------------------------------------------------------------------------
        if len(flag_name) > 0:
            for flag in flag_name:
                # print('flag {}'.format(flag))
                # if seeing the room is False - need to be scouted
                if not Game.flags[flag].room:
                    # look for scouts
                    creep_scouts = _.filter(creeps, lambda c: c.memory.role == 'scout'
                                                              and c.memory.assigned_room == Game.flags[
                                                                  flag].pos.roomName)
                    # print('scouts:', len(creep_scouts))
                    if len(creep_scouts) < 1:
                        spawn_res = spawn.createCreep([MOVE], 'Scout-' + flag,
                                                      {'role': 'scout', 'assigned_room': Game.flags[flag].pos.roomName})
                        # print('spawn_res:', spawn_res)
                        break
                else:
                    # find creeps with assigned flag. find troops first.
                    remote_troops = _.filter(creeps, lambda c: c.memory.role == 'soldier'
                                                               and c.memory.assigned_room == Game.flags[
                                                                   flag].pos.roomName
                                                               and (c.spawning or (c.hits > c.hitsMax * .6
                                                                                   and c.ticksToLive > 300)))

                    hostiles = Game.flags[flag].room.find(FIND_HOSTILE_CREEPS)

                    # 원래 더 아래에 있었지만 키퍼방 문제가 있는지라...
                    flag_structures = Game.flags[flag].room.find(FIND_STRUCTURES)

                    keeper_lair = False

                    for s in flag_structures:
                        if s.structureType == STRUCTURE_KEEPER_LAIR:
                            keeper_lair = True
                            break

                    # 방에 컨트롤러가 없는 경우 가정.
                    flag_room_controller = Game.flags[flag].room.controller
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

                    # to filter out the allies.
                    if len(hostiles) > 0:
                        hostiles = miscellaneous.filter_allies(hostiles)
                        # print('len(hostiles) == {} and len(remote_troops) == {}'
                        #       .format(len(hostiles), len(remote_troops)))
                        # if len(hostiles) > 1:
                        #     plus = 1
                        #
                        # else:
                        plus = 0
                        # print(Game.flags[flag].room.name, 'remote_troops', len(remote_troops))
                        if len(hostiles) + plus > len(remote_troops):
                            # 렙7 이하면 스폰 안한다.
                            if spawn.room.controller.level < 7:
                                continue
                            # todo 인베이더일 경우에만 잡으러 간다. npc가 아닐 경우... 카운터를 새로 세야할듯.
                            # 상대방이 AI인가? AI일때만 건드린다.
                            npc_hostile = False
                            for h in hostiles:
                                print("hostiles: {}".format(JSON.stringify(hostiles)))
                                print('h.owner: {}'.format(h.owner.username))
                                if h.owner.username == 'Invader':
                                    print('INVADER ALERT at {}'.format(Game.flags[flag].room.name))
                                    npc_hostile = True

                            # second one is the BIG GUY. made in case invader's too strong.
                            # 임시로 0으로 놨음. 구조 자체를 뜯어고쳐야함.
                            # 원래 두 크립이 연동하는거지만 한번 없이 해보자.
                            if len(remote_troops) == 0 and npc_hostile and not keeper_lair:
                                spawn_res = spawn.createCreep(
                                    [TOUGH, TOUGH, TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                     MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                     MOVE, MOVE, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK, RANGED_ATTACK,
                                     RANGED_ATTACK, HEAL, HEAL, HEAL]
                                    , undefined, {'role': 'soldier', 'soldier': 'remote_defender'
                                        , 'assigned_room': Game.flags[flag].room.name
                                        , 'home_room': spawn.room.name, 'flag_name': flag})
                                continue
                            elif keeper_lair and len(remote_troops) == 0:
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
                                        , 'assigned_room': Game.flags[flag].room.name
                                        , 'home_room': spawn.room.name, 'flag_name': flag})
                                continue

                    # 방 안에 적이 있으면 방위병이 생길때까지 생산을 하지 않는다.
                    if len(hostiles) > 0:
                        not_spawning_troops = remote_troops.filter(lambda c: not c.spawning)
                        if not_spawning_troops:
                            pass
                        else:
                            continue

                    # todo 1. 리서버를 먼져 생산한다. 2. 컨트롤러 예약이 다른 플레이어에 의해 먹혔을 시 대응방안
                    # find creeps with assigned flag.
                    remote_carriers = _.filter(creeps, lambda c: c.memory.role == 'carrier'
                                                                 and c.memory.assigned_room == Game.flags[
                                                                     flag].pos.roomName
                                                                 and (c.spawning or c.ticksToLive > 100))
                    # exclude creeps with less than 100 life ticks so the new guy can be replaced right away
                    remote_harvesters = _.filter(creeps, lambda c: c.memory.role == 'harvester'
                                                                   and c.memory.assigned_room == Game.flags[
                                                                       flag].pos.roomName
                                                                   and (c.spawning or c.ticksToLive > 120))
                    remote_reservers = _.filter(creeps, lambda c: c.memory.role == 'reserver'
                                                                  and c.memory.assigned_room == Game.flags[
                                                                      flag].pos.roomName)

                    # resources in flag's room
                    # 멀티에 소스가 여럿일 경우 둘을 스폰할 필요가 있다.
                    flag_energy_sources = Game.flags[flag].room.find(FIND_SOURCES)
                    # FIND_SOURCES가 필요없는 이유: 어차피 그걸 보지 않고 건설된 컨테이너 수로 따질거기 때문.

                    flag_containers = _.filter(flag_structures,
                                               lambda s: s.structureType == STRUCTURE_CONTAINER)
                    flag_constructions = Game.flags[flag].room.find(FIND_CONSTRUCTION_SITES)

                    # todo 새 작업. - 만일 소스가 너무 가까워서 가운데에 컨테이너 하나 공동으로 놔도 되는 경우?
                    # NUIILFIED. STILL NEED MORE EFFORT
                    # # 만일 컨테이너 수가 소스보다 적은 경우
                    # if len(flag_containers) < len(flag_energy_sources):
                    #     # 먼져 소스중에 서로 5칸이내에 있는지 확인해본다.
                    #     for es in flag_energy_sources:
                    #         for es_a in flag_energy_sources:
                    #             if es.pos.inRangeTo(es_a, 5) and not es_a == es:
                    #                 # 있으면 이제 상호간의 실질 이동거리가 6칸 이내인지 확인해본다.
                    #                 path = es.pos.findPathTo(es_a, {'ignoreCreeps': True})
                    #                 if len(path) <= 6:
                    #
                    #                     # 조건에 맞으면
                    #
                    #     # if len(flag_containers) > 0:
                    #     #     for s in flag_containers:
                    #     #         if s.pos.inRangeTo(flag_energy_sources, 5)
                    #     pass

                    # 캐리어가 소스 수만큼 있는가?
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
                        carrier_pickup = ''

                        # 에너지소스에 담당 컨테이너가 존재하는가?
                        containter_exist = False
                        print('carrier_source 위치:', target_source.pos)
                        # loop all structures. I'm not gonna use filter. just loop it at once.
                        for st in flag_structures:
                            # 컨테이너만 따진다.
                            if st.structureType == STRUCTURE_CONTAINER:
                                # 소스 세칸 이내에 컨테이너가 있는가? 있으면 carrier_pickup으로 배정
                                if target_source.pos.inRangeTo(st, 3):
                                    containter_exist = True
                                    carrier_pickup = st.id
                                    break
                        # 컨테이너가 존재하지 않는 경우.
                        if not containter_exist:
                            # 건설장 존재여부. 없으면 참.
                            no_container_sites = True
                            # 건설장이 존재하는지 확인한다.
                            for gunseol in flag_constructions:
                                if target_source.pos.inRangeTo(gunseol, 3):
                                    # 존재하면 굳이 아래 돌릴필요가 없어짐.
                                    if gunseol.structureType == STRUCTURE_CONTAINER:
                                        no_container_sites = False
                                        break
                            # 건설중인 컨테이너가 없다? 자동으로 하나 건설한다.
                            if no_container_sites:
                                # 찍을 위치정보. 소스에서 본진방향으로 세번째칸임.
                                const_loc = target_source.pos.findPathTo(spawn.room.controller
                                                                         , {'ignoreCreeps': True})[2]

                                print('const_loc:', const_loc)
                                print('const_loc.x {}, const_loc.y {}'.format(const_loc.x, const_loc.y))
                                print('Game.flags[{}].room.name: {}'.format(flag, Game.flags[flag].room.name))
                                # 찍을 좌표: 이게 제대로된 pos 함수
                                constr_pos = __new__(RoomPosition(const_loc.x, const_loc.y
                                                                  , Game.flags[flag].room.name))
                                print('constr_pos:', constr_pos)
                                constr_pos.createConstructionSite(STRUCTURE_CONTAINER)

                                # RoomPosition 목록. 컨테이너 건설한 김에 길도 깐다.
                                constr_roads_pos = \
                                    PathFinder.search(constr_pos, spawn.pos
                                                      , {
                                                          'plainCost': 2
                                                          , 'swampCost': 2
                                                          , 'roomCallback': lambda: miscellaneous.roomCallback(
                                                creeps, Game.flags[flag].room.name, flag_structures
                                                , flag_constructions, False,
                                                True)
                                                      }, ).path
                                # 길 찾은 후 도로건설
                                for pos in constr_roads_pos:
                                    # 방 밖까지 확인할 필요는 없음.
                                    if pos.roomName != constr_pos.roomName:
                                        break
                                    pos.createConstructionSite(STRUCTURE_ROAD)

                        # 대충 해야하는일: 캐리어의 픽업위치에서 본진거리 확인. 그 후 거리만큼 추가.
                        if Game.getObjectById(carrier_pickup):
                            path = Game.getObjectById(carrier_pickup).room.findPath(
                                Game.getObjectById(carrier_pickup).pos, spawn.pos, {'ignoreCreeps': True})
                            distance = len(path)

                            if Game.getObjectById(carrier_pickup).hits \
                                    <= Game.getObjectById(carrier_pickup).hitsMax * .6 \
                                    or len(flag_constructions) > 0:

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
                                # work 부분부터 넣어본다.
                                if work_chance == 1:
                                    work_check += 1
                                    if work_check == 1 or work_check == 3:
                                        for bodypart in work_body:
                                            body.push(bodypart)
                                # 이거부터 들어가야함
                                if i % 2 == 0:
                                    for bodypart in carry_body_even:
                                        body.push(bodypart)
                                else:
                                    for bodypart in carry_body_odd:
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
                            print('body({}): {}'.format(len(body), body))

                            # WORK 파트가 있는가?
                            if work_check > 0:
                                working_part = True
                            else:
                                working_part = False
                            # 크기가 50을 넘기면? 50에 맞춰야함.
                            if len(body) > 50:
                                # WORK 가 있을경우
                                if working_part:
                                    body = [WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, MOVE, MOVE, MOVE,
                                            MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                            MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY]
                                else:
                                    body = [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
                                            MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY,
                                            CARRY, CARRY]

                            spawning = spawn.createCreep(body, undefined,
                                                         {'role': 'carrier',
                                                          'assigned_room': Game.flags[flag].room.name,
                                                          'home_room': spawn.room.name,
                                                          'flag_name': flag, 'pickup': carrier_pickup
                                                             , 'work': working_part,
                                                          'source_num': carrier_source})
                            print('spawning', spawning)
                            if spawning == 0:
                                continue
                            elif spawning == ERR_NOT_ENOUGH_RESOURCES:

                                body = []

                                if work_chance == 1:
                                    for bodypart in work_body:
                                        body.push(bodypart)
                                # 15% 몸집을 줄여본다.
                                if int(distance / 7) == 0:
                                    distance = 1
                                else:
                                    distance = int(distance / 7)
                                for i in range(distance):
                                    if i % 2 == 1:
                                        for bodypart in carry_body_odd:
                                            body.push(bodypart)
                                    else:
                                        for bodypart in carry_body_even:
                                            body.push(bodypart)

                                print('2nd body({}): {}'.format(len(body), body))
                                spawning = spawn.createCreep(
                                    body,
                                    undefined,
                                    {'role': 'carrier', 'assigned_room': Game.flags[flag].room.name,
                                     'flag_name': flag, 'pickup': carrier_pickup, 'work': working_part
                                        , 'home_room': spawn.room.name, 'source_num': carrier_source})

                                print('spawning {}'.format(spawning))
                                continue
                        # 픽업이 존재하지 않는다는건 현재 해당 건물이 없다는 뜻이므로 새로 지어야 함.
                        else:
                            spawning = spawn.createCreep(
                                [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
                                 WORK, WORK, WORK, CARRY, CARRY],
                                undefined,
                                {'role': 'carrier', 'assigned_room': Game.flags[flag].room.name,
                                 'flag_name': flag, 'work': True, 'home_room': spawn.room.name
                                    , 'source_num': carrier_source})
                            if spawning == ERR_NOT_ENOUGH_RESOURCES:
                                spawn.createCreep(
                                    [WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE,
                                     MOVE, MOVE, MOVE, MOVE],
                                    undefined,
                                    {'role': 'carrier', 'assigned_room': Game.flags[flag].room.name,
                                     'flag_name': flag, 'work': True, 'home_room': spawn.room.name
                                        , 'source_num': carrier_source})
                            continue

                    elif len(flag_containers) > len(remote_harvesters):
                        # perfect for 3000 cap
                        regular_spawn = spawn.createCreep(
                            [WORK, WORK, WORK, WORK, WORK, WORK,
                             CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE,
                             MOVE, MOVE]
                            , undefined,
                            {'role': 'harvester', 'assigned_room': Game.flags[flag].room.name,
                             'home_room': spawn.room.name,
                             'size': 2, 'flag_name': flag})
                        # print('what happened:', regular_spawn)
                        if regular_spawn == -6:
                            spawn.createCreep([WORK, WORK, WORK, WORK, WORK,
                                               CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE]
                                              , undefined,
                                              {'role': 'harvester', 'assigned_room': Game.flags[flag].room.name
                                                  , 'home_room': spawn.room.name, 'flag_name': flag})
                            continue

                    elif flag_room_controller:
                        if len(remote_reservers) == 0 \
                                and (not Game.flags[flag].room.controller.reservation
                                     or Game.flags[flag].room.controller.reservation.ticksToEnd < 1200):
                            spawning_creep = spawn.createCreep(
                                [MOVE, MOVE, MOVE, MOVE, CLAIM, CLAIM, CLAIM, CLAIM]
                                , undefined,
                                {'role': 'reserver', 'home_room': spawn.room.name,
                                 'assigned_room': Game.flags[flag].room.name
                                    , 'flag_name': flag})
                            if spawning_creep == ERR_NOT_ENOUGH_RESOURCES:
                                spawning_creep = spawn.createCreep(
                                    [MOVE, MOVE, CLAIM, CLAIM]
                                    , undefined,
                                    {'role': 'reserver', 'home_room': spawn.room.name,
                                     'assigned_room': Game.flags[flag].room.name
                                        , 'flag_name': flag})

                            continue

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
