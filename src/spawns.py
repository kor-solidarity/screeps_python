# from defs import *
# import random
#
# __pragma__('noalias', 'name')
# __pragma__('noalias', 'undefined')
# __pragma__('noalias', 'Infinity')
# __pragma__('noalias', 'keys')
# __pragma__('noalias', 'get')
# __pragma__('noalias', 'set')
# __pragma__('noalias', 'type')
# __pragma__('noalias', 'update')
#
# # 스폰을 메인에서 쪼개기 위한 용도. 현재 어떻게 빼내야 하는지 감이 안잡혀서 공백임.
#
#
# def run_spawn():
#
#     divider += 1
#     if divider > counter:
#         divider -= counter
#
#     # this part is made to save memory and separate functional structures out of spawn loop.
#     if Game.time % structure_renew_count == 1 or not Memory.rooms:
#         # TESTING PART
#         print('check')
#         # obj.property === obj['property']
#
#         push_bool = True
#
#         new_json = '{}'
#         new_json = JSON.parse(new_json)
#
#         new_towers = {STRUCTURE_TOWER: []}
#
#         new_links = {STRUCTURE_LINK: []}
#         new_labs = {STRUCTURE_LAB: []}
#
#         for room_name in room_names:
#             print('room_name({}) || spawn.room.name({})'.format(room_name, spawn.room.name))
#             # 순환 돌려서 하나라도 방이름 중복되면 아래 추가 안해야함.
#             if room_name == spawn.room.name:
#                 print('check')
#                 push_bool = False
#                 break
#
#         if push_bool:
#             # find and add towers
#             towers = _.filter(my_structures, {'structureType': STRUCTURE_TOWER})
#             if len(towers) > 0:
#                 for tower in towers:
#                     new_towers[STRUCTURE_TOWER].push(tower.id)
#                 print('new_towers', new_towers[STRUCTURE_TOWER])
#             # find and add links
#             links = _.filter(my_structures, {'structureType': STRUCTURE_LINK})
#             if len(links) > 0:
#                 for link in links:
#                     new_links[STRUCTURE_LINK].push(link.id)
#                 print('new_links', new_links[STRUCTURE_LINK])
#
#             new_jsons = [new_links, new_towers]
#             for json in new_jsons:
#                 if len(json) == 0:
#                     continue
#                 # structure_type = Object.keys(json)
#                 if not Memory.rooms:
#                     Memory.rooms = {}
#                 if not Memory.rooms[spawn.room.name]:
#                     Memory.rooms[spawn.room.name] = {}
#                 # print('Object.keys(json)', Object.keys(json))
#                 # 실제로 넣을 ID
#                 additive = []
#                 for js in json[Object.keys(json)]:
#                     additive.push(js)
#
#                 Memory.rooms[spawn.room.name][Object.keys(json)] = additive
#
#             room_names.append(spawn.room.name)
#
#     # if spawn is not spawning, try and make one i guess.
#     # spawning priority: harvester > hauler > upgrader > melee > etc.
#     # checks every 10 + len(Game.spawns) ticks
#     if not spawn.spawning and Game.time % counter == divider:
#         hostile_around = False
#         # 적이 주변에 있으면 생산 안한다. 추후 수정해야함.
#
#         if hostile_creeps:
#             for enemy in hostile_creeps:
#                 if spawn.pos.inRangeTo(enemy, 2):
#                     hostile_around = True
#                     break
#         if hostile_around:
#             continue
#
#         # ALL flags.
#         flags = Game.flags
#         flag_name = []
#
#         # check all flags with same name with the spawn.
#         for name in Object.keys(flags):
#
#             # 방이름 + -rm + 아무글자(없어도됨)
#             regex = spawn.room.name + r'-rm.*'
#             if re.match(regex, name, re.IGNORECASE):
#                 # if there is, get it's flag's name out.
#                 flag_name.push(flags[name].name)
#
#         # ALL creeps you have
#         creeps = Game.creeps
#
#         # need each number of creeps by type. now all divided by assigned room.
#         creep_harvesters = _.filter(creeps, lambda c: (c.memory.role == 'harvester'
#                                                        and c.memory.assigned_room == spawn.pos.roomName
#                                                        and not c.memory.flag_name
#                                                        and (c.spawning or c.ticksToLive > 100)))
#         creep_upgraders = _.filter(creeps, lambda c: (c.memory.role == 'upgrader'
#                                                       and c.memory.assigned_room == spawn.pos.roomName
#                                                       and (c.spawning or c.ticksToLive > 100)))
#         creep_haulers = _.filter(creeps, lambda c: (c.memory.role == 'hauler'
#                                                     and c.memory.assigned_room == spawn.pos.roomName
#                                                     and (c.spawning or c.ticksToLive > 100)))
#         creep_miners = _.filter(creeps, lambda c: (c.memory.role == 'miner'
#                                                    and c.memory.assigned_room == spawn.pos.roomName
#                                                    and (c.spawning or c.ticksToLive > 150)))
#
#         # ﷽
#         # if number of close containers/links are less than that of sources.
#         harvest_carry_targets = []
#
#         sources = nesto.room.find(FIND_SOURCES)
#
#         for structure in all_structures:
#             if structure.structureType == STRUCTURE_CONTAINER or structure.structureType == STRUCTURE_LINK:
#                 for source in sources:
#                     if source.pos.inRangeTo(structure, 3):
#                         harvest_carry_targets.push(structure.id)
#                         break
#             if len(harvest_carry_targets) >= len(sources):
#                 break
#
#         if len(harvest_carry_targets) < len(sources):
#             # and not spawn.pos.inRangeTo(2, hostile_creeps[0]):
#             harvesters_bool = bool(len(creep_harvesters) < len(sources) * 2)
#         # if numbers of creep_harvesters are less than number of sources in the spawn's room.
#         else:
#             # to count the overall harvesting power. 3k or more == 2, else == 1
#             harvester_points = 0
#
#             for harvester_creep in creep_harvesters:
#                 # size scale:
#                 # 1 - small sized: 2 in each. regardless of actual capacity. for lvl 3 or less
#                 # 2 - real standards. suitable for 3k. 4500 not implmented yet.
#                 harvester_points += harvester_creep.memory.size
#
#             if harvester_points < len(sources) * 2:
#                 harvesters_bool = True
#             else:
#                 harvesters_bool = False
#                 # harvesters_bool = bool(len(creep_harvesters) < len(sources))
#
#         if harvesters_bool:
#             # check if energy_source capacity is 4.5k(4k in case they update, not likely).
#             # if is, go for size 4500.
#             if sources[0].energyCapacity > 4000:
#                 regular_spawn = spawn.createCreep(
#                     [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK,
#                      WORK, WORK,
#                      CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY]
#                     , undefined,
#                     {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
#                      'size': 2})
#             else:
#                 # perfect for 3000 cap
#                 regular_spawn = spawn.createCreep(
#                     [WORK, WORK, WORK, WORK, WORK, WORK,
#                      CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE,
#                      MOVE, MOVE]
#                     , undefined,
#                     {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
#                      'size': 2})
#             # print('what happened:', regular_spawn)
#             if regular_spawn == -6:
#                 # one for 1500 cap == need 2
#                 if spawn.createCreep(
#                         [WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE],
#                         undefined,
#                         {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
#                          'size': 1}) == -6:
#                     spawn.createCreep([MOVE, WORK, WORK, CARRY], undefined,
#                                       {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
#                                        'size': 1})  # final barrier
#             continue
#
#         plus = 0
#         for harvest_container in harvest_carry_targets:
#             # Ĉar uzi getObjectById k.t.p estas tro longa.
#             harvest_target = Game.getObjectById(harvest_container)
#             # 컨테이너.
#             if harvest_target.structureType == STRUCTURE_CONTAINER:
#                 if _.sum(harvest_target.store) >= harvest_target.storeCapacity * .9:
#                     plus += 1
#                 elif _.sum(harvest_target.store) <= harvest_target.storeCapacity * .4:
#                     plus -= 1
#             # 링크.
#             else:
#                 if harvest_target.energy >= harvest_target.energyCapacity * .9:
#                     plus += 1
#                 elif harvest_target.energy <= harvest_target.energyCapacity * .4:
#                     plus -= 1
#
#         # 건물이 아예 없을 시
#         if len(harvest_carry_targets) == 0:
#             plus = -len(sources)
#
#         hauler_capacity = len(sources) + 1 + plus
#         # minimum number of haulers in the room is 1, max 4
#         if hauler_capacity <= 0:
#             hauler_capacity = 1
#         elif hauler_capacity > 4:
#             hauler_capacity = 4
#
#         if len(creep_haulers) < hauler_capacity:
#             # first hauler is always 250 sized. - 'balance' purpose(idk just made it up)
#             if spawn.room.energyAvailable >= spawn.room.energyCapacityAvailable * .85 \
#                     and len(creep_haulers) != 0:
#                 spawning_creep = spawn.createCreep(
#                     [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, CARRY, CARRY, CARRY,
#                      CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY],
#                     undefined, {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
#                                 'level': 8})
#             else:
#                 spawning_creep = spawn.createCreep([WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
#                                                     CARRY, CARRY, MOVE, MOVE, MOVE, MOVE, MOVE],
#                                                    undefined,
#                                                    {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
#                                                     'level': 5})
#
#             if spawning_creep == -6:
#                 if spawn.createCreep([WORK, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE], undefined,
#                                      {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
#                                       'level': 2}) == -6:
#                     spawn.createCreep([MOVE, MOVE, WORK, CARRY, CARRY], undefined,
#                                       {'role': 'hauler', 'assigned_room': spawn.pos.roomName,
#                                        'level': 0})
#
#             continue
#
#         # if there's an extractor, make a miner.
#         if len(extractor) > 0 and len(creep_miners) == 0:
#             # continue
#             if minerals[0].mineralAmount != 0 or minerals[0].ticksToRegeneration < 120:
#                 # only one is needed
#                 if len(creep_miners) > 0:
#                     pass
#                 # make a miner
#                 else:
#                     spawning_creep = spawn.createCreep(
#                         [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
#                          WORK,
#                          WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
#                          WORK,
#                          WORK, WORK, CARRY], undefined,
#                         {'role': 'miner', 'assigned_room': spawn.pos.roomName,
#                          'level': 5})
#                     if spawning_creep == 0:
#                         continue
#
#         plus = 0
#         if len(creep_upgraders) < 2:
#             # some prime number.
#             if Game.time % 6491 < 11:
#                 plus = 1
#             if spawn.room.controller.ticksToDowngrade < 10000:
#                 plus += 1
#
#         if spawn.room.controller.level == 8:
#             proper_level = 0
#         # start making upgraders after there's a storage
#         elif spawn.room.controller.level > 2 and spawn.room.storage:
#
#             if spawn.room.controller.level < 5:
#                 expected_reserve = 2500
#             else:
#                 expected_reserve = 7000
#
#             # if there's no storage or storage has less than 6k energy
#             if spawn.room.storage.store[RESOURCE_ENERGY] < expected_reserve or not spawn.room.storage:
#                 proper_level = 1
#             # more than 30k
#             elif spawn.room.storage.store[RESOURCE_ENERGY] >= expected_reserve:
#                 proper_level = 1
#                 # extra upgrader every expected_reserve
#                 proper_level += int(spawn.room.storage.store[RESOURCE_ENERGY] / expected_reserve)
#                 # max upgraders: 12
#                 if proper_level > 12:
#                     proper_level = 12
#
#             else:
#                 proper_level = 1
#         elif spawn.room.energyCapacityAvailable <= 1000:
#             # 어차피 여기올쯤이면 소형애들만 생성됨.
#             proper_level = 4
#         else:
#             proper_level = 0
#
#         if len(creep_upgraders) < proper_level + plus \
#                 and not (Game.cpu.bucket < 2000):
#             if spawn.room.controller.level != 8:
#                 big = spawn.createCreep(
#                     [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK,
#                      WORK, WORK,
#                      WORK,
#                      WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY], undefined,
#                     {'role': 'upgrader', 'assigned_room': spawn.pos.roomName, 'level': 5})
#             else:
#                 big = -6
#             if big == -6:
#                 small = spawn.createCreep(
#                     [WORK, WORK, WORK, WORK, WORK, WORK, CARRY, CARRY, CARRY,
#                      CARRY, CARRY, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE], undefined,
#                     {'role': 'upgrader', 'assigned_room': spawn.pos.roomName, 'level': 3})
#                 if small == -6:
#                     little = spawn.createCreep([WORK, WORK, WORK, CARRY, MOVE, MOVE], undefined,
#                                                {'role': 'upgrader', 'assigned_room': spawn.pos.roomName})
#                 if little == -6:
#                     spawn.createCreep([WORK, WORK, CARRY, CARRY, MOVE, MOVE], undefined,
#                                       {'role': 'upgrader', 'assigned_room': spawn.pos.roomName})
#             continue
#
#         # REMOTE---------------------------------------------------------------------------
#         if len(flag_name) > 0:
#             for flag in flag_name:
#
#                 # if seeing the room is False - need to be scouted
#                 if not Game.flags[flag].room:
#                     # look for scouts
#                     creep_scouts = _.filter(creeps, lambda c: c.memory.role == 'scout'
#                                                               and c.memory.flag_name == flag)
#                     # print('scouts:', len(creep_scouts))
#                     if len(creep_scouts) < 1:
#                         spawn_res = spawn.createCreep([MOVE], 'Scout-' + flag,
#                                                       {'role': 'scout', 'flag_name': flag})
#                         # print('spawn_res:', spawn_res)
#                         break
#                 else:
#                     # find creeps with assigned flag.
#                     remote_troops = _.filter(creeps, lambda c: c.memory.role == 'soldier'
#                                                                and c.memory.flag_name == flag
#                                                                and (c.spawning or (c.hits > c.hitsMax * .6
#                                                                                    and c.ticksToLive > 100)))
#                     remote_carriers = _.filter(creeps, lambda c: c.memory.role == 'carrier'
#                                                                  and c.memory.flag_name == flag
#                                                                  and (c.spawning or c.ticksToLive > 100))
#                     # exclude creeps with less than 100 life ticks so the new guy can be replaced right away
#                     remote_harvesters = _.filter(creeps, lambda c: c.memory.role == 'harvester'
#                                                                    and c.memory.flag_name == flag
#                                                                    and (c.spawning or c.ticksToLive > 120))
#                     remote_reservers = _.filter(creeps, lambda c: c.memory.role == 'reserver'
#                                                                   and c.memory.flag_name == flag)
#
#                     hostiles = Game.flags[flag].room.find(FIND_HOSTILE_CREEPS)
#                     # to filter out the allies.
#                     if len(hostiles) > 0:
#                         hostiles = miscellaneous.filter_allies(hostiles)
#                         print('len(hostiles) == {} and len(remote_troops) == {}'
#                               .format(len(hostiles), len(remote_troops)))
#                     if len(hostiles) > 1:
#                         plus = 1
#
#                     else:
#                         plus = 0
#                     # print(Game.flags[flag].room.name, 'remote_troops', len(remote_troops))
#                     if len(hostiles) + plus > len(remote_troops):
#                         # 임시조치. 한번 그냥 적들어오면 아무것도 안해보자.
#                         continue
#
#                         # second one is the BIG GUY. made in case invader's too strong.
#                         # 임시로 0으로 놨음. 구조 자체를 뜯어고쳐야함.
#                         if len(remote_troops) == 0:
#                             spawn_res = spawn.createCreep(
#                                 [TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE,
#                                  MOVE, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK, ATTACK,
#                                  ATTACK, RANGED_ATTACK, HEAL],
#                                 undefined, {'role': 'soldier', 'assigned_room': spawn.pos.roomName
#                                     , 'flag_name': flag})
#                             continue
#                         spawn_res = spawn.createCreep(
#                             [TOUGH, TOUGH, TOUGH, MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, ATTACK, RANGED_ATTACK,
#                              HEAL],
#                             undefined, {'role': 'soldier', 'assigned_room': spawn.pos.roomName
#                                 , 'flag_name': flag})
#                         # if spawn_res == 0:
#                         continue
#
#                     # 방 안에 적이 있으면 아예 생산을 하지 않는다! 정찰대와 방위병 빼고.
#                     if len(hostiles) > 0:
#                         continue
#
#                     # resources in flag's room
#                     # 멀티에 소스가 여럿일 경우 둘을 스폰할 필요가 있다.
#                     flag_energy_sources = Game.flags[flag].room.find(FIND_SOURCES)
#                     # FIND_SOURCES가 필요없는 이유: 어차피 그걸 보지 않고 건설된 컨테이너 수로 따질거기 때문.
#                     flag_structures = Game.flags[flag].room.find(FIND_STRUCTURES)
#                     flag_containers = _.filter(flag_structures,
#                                                lambda s: s.structureType == STRUCTURE_CONTAINER)
#                     flag_constructions = Game.flags[flag].room.find(FIND_CONSTRUCTION_SITES)
#
#                     # 캐리어가 소스 수만큼 있는가?
#                     if len(flag_energy_sources) > len(remote_carriers):
#                         print('flag carrier?')
#                         # 픽업으로 배정하는 것이 아니라 자원으로 배정한다.
#                         if len(remote_carriers) == 0:
#                             # 캐리어가 아예 없으면 그냥 첫 자원으로.
#                             carrier_source = flag_energy_sources[0].id
#                             target_source = Game.getObjectById(carrier_source)
#                         else:
#                             # 캐리어가 존재할 시. 각 소스를 돌린다.
#                             for s in flag_energy_sources:
#
#                                 for c in remote_carriers:
#                                     # 캐리어들을 돌려서 만약 캐리어와
#                                     if s.id == c.memory.source_num:
#                                         continue
#                                     else:
#                                         # creep.memory.source_num
#                                         carrier_source = s.id
#                                         # Game.getObjectById(carrier_source) << 이게 너무 길어서.
#                                         target_source = Game.getObjectById(carrier_source)
#                                         break
#
#                         # creep.memory.pickup
#                         carrier_pickup = ''
#
#                         # 에너지소스에 담당 컨테이너가 존재하는가?
#                         containter_exist = False
#
#                         print('carrier_source 위치:', target_source.pos)
#
#                         # loop all structures. I'm not gonna use filter. just loop it at once.
#                         for st in flag_structures:
#                             # 컨테이너만 따진다.
#                             if st.structureType == STRUCTURE_CONTAINER:
#                                 # 소스 세칸 이내에 컨테이너가 있는가? 있으면 carrier_pickup으로 배정
#                                 if target_source.pos.inRangeTo(st, 3):
#                                     containter_exist = True
#                                     carrier_pickup = st.id
#                                     break
#                         # 컨테이너가 존재하지 않는 경우.
#                         if not containter_exist:
#                             no_container_sites = True
#                             # 건설장이 존재하는지 확인한다.
#                             for gunseol in flag_constructions:
#                                 if target_source.pos.inRangeTo(gunseol, 3):
#                                     # 존재하면 굳이 아래 돌릴필요가 없어짐.
#                                     if gunseol.structureType == STRUCTURE_CONTAINER:
#                                         no_container_sites = False
#                                         break
#                             # 건설중인 컨테이너가 없다? 자동으로 하나 건설한다.
#                             if no_container_sites:
#                                 # 찍을 위치정보. 소스에서 본진방향으로 세번째칸임.
#                                 const_loc = target_source.pos.findPathTo(Game.rooms[nesto.room.name].controller)[2]
#                                 print('const_loc:', const_loc)
#                                 print('const_loc.x {}, const_loc.y {}'.format(const_loc.x, const_loc.y))
#                                 print('Game.flags[{}].room.name: {}'.format(flag, Game.flags[flag].room.name))
#                                 # 찍을 좌표: 이게 제대로된 pos 함수
#                                 constr_pos = __new__(RoomPosition(const_loc.x, const_loc.y
#                                                                   , Game.flags[flag].room.name))
#                                 print('constr_pos:', constr_pos)
#                                 constr_pos.createConstructionSite(STRUCTURE_CONTAINER)
#
#                         # 대충 해야하는일: 캐리어의 픽업위치에서 본진거리 확인. 그 후 거리만큼 추가.
#                         if Game.getObjectById(carrier_pickup):
#                             path = Game.getObjectById(carrier_pickup).room.findPath(
#                                 Game.getObjectById(carrier_pickup).pos, spawn.pos, {'ignoreCreeps': True})
#                             distance = len(path)
#
#                             if _.sum(Game.getObjectById(carrier_pickup).store) \
#                                     >= Game.getObjectById(carrier_pickup).storeCapacity * .8:
#                                 work_chance = 1
#                             else:
#                                 work_chance = random.randint(0, 1)
#                             # 굳이 따로 둔 이유: 캐리 둘에 무브 하나.
#                             carry_body_odd = [MOVE, CARRY, CARRY, CARRY]
#                             carry_body_even = [MOVE, MOVE, CARRY, CARRY, CARRY]
#                             work_body = [MOVE, WORK, WORK, MOVE, WORK, WORK]
#                             body = []
#
#                             work_check = 0
#                             for i in range(int(distance / 6)):
#                                 # 이거부터 들어가야함
#                                 if i % 2 == 0:
#                                     for bodypart in carry_body_even:
#                                         body.push(bodypart)
#                                 else:
#                                     for bodypart in carry_body_odd:
#                                         body.push(bodypart)
#                                 if work_chance == 0:
#                                     work_check += 1
#                                     if work_check == 1 or work_check == 4:
#                                         for bodypart in work_body:
#                                             body.push(bodypart)
#                             # 거리 나머지값 반영.
#                             if distance % 6 > 2:
#                                 body.push(MOVE)
#                                 body.push(CARRY)
#                             if _.sum(Game.getObjectById(carrier_pickup).store) \
#                                     >= Game.getObjectById(carrier_pickup).storeCapacity * .8:
#                                 print('extra')
#                                 if distance % 6 <= 2:
#                                     body.push(MOVE)
#                                 body.push(CARRY)
#                             print('body', body)
#
#                             # WORK 파트가 있는가?
#                             if work_check > 0:
#                                 working_part = True
#                             else:
#                                 working_part = False
#
#                             spawning = spawn.createCreep(body, undefined,
#                                                          {'role': 'carrier',
#                                                           'assigned_room': spawn.pos.roomName,
#                                                           'flag_name': flag, 'pickup': carrier_pickup
#                                                              , 'work': working_part, 'source_num': carrier_source})
#                             print('spawning', spawning)
#                             if spawning == 0:
#                                 continue
#                             elif spawning == ERR_NOT_ENOUGH_RESOURCES:
#                                 if work_chance == 0:
#                                     body = []
#                                     for i in range(int(distance / 6)):
#                                         if i % 2 == 1:
#                                             for bodypart in carry_body_odd:
#                                                 body.push(bodypart)
#                                         else:
#                                             for bodypart in carry_body_even:
#                                                 body.push(bodypart)
#                                     spawn.createCreep(
#                                         body,
#                                         undefined,
#                                         {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
#                                          'flag_name': flag, 'pickup': carrier_pickup, 'work': working_part
#                                             , 'source_num': carrier_source})
#                                 else:
#                                     spawn.createCreep(
#                                         [WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE,
#                                          MOVE, MOVE, MOVE, MOVE],
#                                         undefined,
#                                         {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
#                                          'flag_name': flag, 'pickup': carrier_pickup
#                                             , 'work': True, 'source_num': carrier_source})
#                                 continue
#                         # 픽업이 존재하지 않는다는건 현재 해당 건물이 없다는 뜻이므로 새로 지어야 함.
#                         else:
#                             spawning = spawn.createCreep(
#                                 [MOVE, MOVE, MOVE, MOVE, MOVE, MOVE, WORK, WORK, WORK, WORK, WORK, WORK, WORK,
#                                  WORK, WORK, WORK, CARRY, CARRY],
#                                 undefined,
#                                 {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
#                                  'flag_name': flag, 'work': True
#                                     , 'source_num': carrier_source})
#                             if spawning == ERR_NOT_ENOUGH_RESOURCES:
#                                 spawn.createCreep(
#                                     [WORK, WORK, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE,
#                                      MOVE, MOVE, MOVE, MOVE],
#                                     undefined,
#                                     {'role': 'carrier', 'assigned_room': spawn.pos.roomName,
#                                      'flag_name': flag, 'work': True
#                                         , 'source_num': carrier_source})
#                             continue
#
#                     if len(flag_containers) > len(remote_harvesters):
#                         # perfect for 3000 cap
#                         regular_spawn = spawn.createCreep(
#                             [WORK, WORK, WORK, WORK, WORK, WORK,
#                              CARRY, CARRY, CARRY, CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE,
#                              MOVE, MOVE]
#                             , undefined,
#                             {'role': 'harvester', 'assigned_room': spawn.pos.roomName,
#                              'size': 2, 'flag_name': flag})
#                         # print('what happened:', regular_spawn)
#                         if regular_spawn == -6:
#                             spawn.createCreep([WORK, WORK, WORK, WORK, WORK,
#                                                CARRY, CARRY, CARRY, MOVE, MOVE, MOVE, MOVE]
#                                               , undefined,
#                                               {'role': 'harvester', 'assigned_room': spawn.pos.roomName
#                                                   , 'flag_name': flag})
#                             continue
#
#                     elif len(remote_reservers) == 0 \
#                             and (not Game.flags[flag].room.controller.reservation
#                                  or Game.flags[flag].room.controller.reservation.ticksToEnd < 1200):
#                         spawning_creep = spawn.createCreep([MOVE, MOVE, MOVE, MOVE, CLAIM, CLAIM, CLAIM, CLAIM]
#                                                            , undefined,
#                                                            {'role': 'reserver',
#                                                             'assigned_room': spawn.pos.roomName
#                                                                , 'flag_name': flag})
#                         if spawning_creep == ERR_NOT_ENOUGH_RESOURCES:
#                             spawning_creep = spawn.createCreep([MOVE, MOVE, CLAIM, CLAIM]
#                                                                , undefined,
#                                                                {'role': 'reserver', 'assigned_room': spawn.pos.roomName
#                                                                    , 'flag_name': flag})
#
#                         continue
#
#     elif spawn.spawning:
#         # showing process of the spawning creep by %
#         spawning_creep = Game.creeps[spawn.spawning.name]
#         spawn.room.visual.text(
#             '🛠 ' + spawning_creep.memory.role + ' '
#             + str(int(
#                 ((spawn.spawning.needTime - spawn.spawning.remainingTime)
#                  / spawn.spawning.needTime) * 100)) + '%',
#             spawn.pos.x + 1,
#             spawn.pos.y,
#             {'align': 'left', 'opacity': 0.8}
#         )
#     else:
#         # 1/3 chance healing
#         randint = random.randint(1, 3)
#
#         if randint != 1:
#             continue
#         # 이 곳에 필요한거: spawn 레벨보다 같거나 높은 애들 지나갈 때 TTL이 오백 이하면 회복시켜준다.
#         # room controller lvl ± 2 에 부합한 경우에만 수리를 실시한다.
#         level = Game.spawns[nesto.name].room.controller.level
#
#         for creep in creeps:
#             # 방 안에 있는 크립 중에 회복대상자들.
#             if 100 < creep.ticksToLive < 500 and creep.room.name == spawn.room.name \
#                     and (creep.memory.level >= level - 3 and not creep.memory.level <= 0):
#                 if spawn.pos.isNearTo(creep):
#                     # print(creep.ticksToLive)
#                     result = spawn.renewCreep(creep)
#                     break