from defs import *
import harvest_stuff

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


'''
- harvester:  
        1. harvest stuff to areas. in this case they also must harvest dropped resources.
        1-1. after this the harvester won't leave anywhere else than areas close to them. distributor will carry 4 them 
        2. if theres no place to collect they go and help up with upgrading.
        3. there are currently 5 harvesters. when python is made i only need 1 or 2(probably). 
        size: 
    spawn.createCreep([WORK,WORK,WORK,WORK,CARRY,CARRY,CARRY,CARRY,MOVE,MOVE,MOVE,MOVE], undefined, {role: 'harvester'})
    spawn.createCreep([WORK,WORK,WORK,CARRY,CARRY,CARRY,MOVE,MOVE,MOVE], undefined, {role: 'harvester'}) - smaller

'''


def run_harvester(creep, all_structures, constructions, creeps, dropped_all, sources):
    """
    Runs a creep as a generic harvester.
    :param creep: The creep to run
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
    :param creeps: creep.room.find(FIND_MY_CREEPS)
    :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
    :param sources: creep.room.find(FIND_SOURCES)
    """
    vis_key = "visualizePathStyle"
    stroke_key = "stroke"

    # 소속된 깃발이 있는 방에 없으면 있는 방으로 우선 가고 본다.
    if creep.memory.flag_name and Game.flags[creep.memory.flag_name].pos.roomName != creep.pos.roomName:
        creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle':
                                                                  {'stroke': '#ADD8E6', 'opacity': .25}})
        return

    # no memory.laboro? make one.
    if not creep.memory.laboro and creep.memory.laboro != 0:
        """
        0 = harvest
        1 = carry-to-storage|container / upgrade
        """
        creep.memory.laboro = 0

    # if there's no source_num, need to distribute it.
    if not creep.memory.source_num and creep.memory.source_num != 0:
        # added ifs for remotes
        if creep.memory.flag_name and creep.room.name != Game.flags[creep.memory.flag_name].pos.roomName:
            # normale, kripos ne devus havi .find() en la skripto, sed ĉi tio estas por malproksima regiono do...
            sources = Game.flags[creep.memory.flag_name].room.find(FIND_SOURCES)
            my_area = Game.flags[creep.memory.flag_name].room
            creeps = Game.flags[creep.memory.flag_name].room.find(FIND_MY_CREEPS)
            rikoltist_kripoj = _.filter(creeps,
                                        lambda c: (c.spawning or c.ticksToLive > 100) and c.memory.role == 'harvester')
            # kripoj_3k_aux_pli = _.filter(creeps,
            #                              lambda c: c.tickstolive > 100 and c.memory.size >= 3000
            #                              and c.memory.role == 'harvester')
        else:
            my_area = creep.room
            rikoltist_kripoj = _.filter(creeps,
                                        lambda c: (c.spawning or c.ticksToLive > 100) and c.memory.role == 'harvester')
            # kripoj_3k_aux_pli = _.filter(creeps,
            #                              lambda c: c.tickstolive > 100 and c.memory.size >= 3000
            #                              and c.memory.role == 'harvester')
        print('creeps:', creeps)
        print('kripo:', rikoltist_kripoj)
        print('current creep:', creep.name)
        print('len(rikoltist_kripoj): {} || len(sources): {}'.format(len(rikoltist_kripoj), len(sources)))

        # tie estus 3 kazoj en ĉi tio:
        # 1 - no creeps at all.
        # 2 - there is a creep working already(1 or 2)
        # 3 - more than 2 creeps working
        # kazo 1
        if len(rikoltist_kripoj) == 0:
            # print('case 1')
            # se tie ne estas iu kripoj simple asignu 0
            creep.memory.source_num = 0
        # kazo 2
        elif len(rikoltist_kripoj) <= len(sources):
            # print('case 2')
            # to check for sources not overlapping
            checker = 0
            for source in range(len(sources)):
                # print('-----', source, '-----')
                for kripo in rikoltist_kripoj:
                    # if the creep is same with current creep, or dont have memory assigned, pass.
                    if creep.name == kripo.name or \
                            (not kripo.memory.source_num and kripo.memory.source_num != 0):
                        continue
                    # print('creep:{} || TTL: {}'.format(kripo, kripo.ticksToLive))
                    # print('creep.memory.source_num:', kripo.memory.source_num)
                    # if memory.source_num == source, means it's already taken. pass.
                    if kripo.memory.source_num == source:
                        # print('kripo.memory.source_num({}) == source({})'.format(kripo.memory.source_num, source))
                        # add the number to check.
                        checker += 1
                    # print('is checker({}) == source({})? : '.format(checker, source), bool(checker == source))
                    if checker == source:
                        # print('did it got in?')
                        creep.memory.source_num = source
                        break
                if creep.memory.source_num or creep.memory.source_num == 0:
                    break
        # kazo 3
        elif len(rikoltist_kripoj) > len(sources):
            # print('case 3')
            # to check the number of sources
            checker = 0
            # trovu kripoj kun memory.size malpli ol 3k
            for source in range(len(sources)):
                # print('-----', source, '-----')
                # for counting number of creeps.
                counter = 0
                for kripo in rikoltist_kripoj:
                    # print('creep:', kripo)
                    # print('creep.memory.source_num:', kripo.memory.source_num)
                    # if the creep is same with current creep, or dont have memory assigned, pass.
                    if creep.name == kripo.name or \
                            (not kripo.memory.source_num and kripo.memory.source_num != 0):
                        # print('------pass------')
                        continue
                    # if there's a creep with 3k < size, moves to another source automatically.
                    if kripo.memory.source_num == source:
                        if kripo.memory.size >= 3000:
                            counter += 1
                        counter += 1
                # se counter estas malpli ol du, asignu la nuna source.
                # print('counter:', counter)
                if counter < 2:
                    # print('counter is less than 2')
                    creep.memory.source_num = source
                    break

        # se la kripo ankoraŭ ne asignita?
        # trovu iu source kun 3k. sed ĉi tio ne devus okazi.

        # 위에가 안걸려서 이게 뜨는 이유: 이미 다 꽉차있거나 크립이 아예 없는거임.
        # needs to be done: 아래.
        # 이게 또 뜨는 경우가 아예 없는거 외에 이미 꽉찬건데 이 경우에는 아직 살아있는애가 있어서 겹치는 경우인데
        # 이럴때는 우선 크립의 ttl, 그리고 크립의 담당 수확지역을 찾는다.
        # print('creep.memory.source_num:', creep.memory.source_num)
        if not creep.memory.source_num and creep.memory.source_num != 0:
            my_creeps = creeps
            harvester_that_is_gonna_die_soon = _.filter(my_creeps, lambda c: c.memory.role == 'harvester'
                                                                             and c.tickstolive < 100)
            # print('harvester_that_is_gonna_die_soon:', harvester_that_is_gonna_die_soon)
            if len(harvester_that_is_gonna_die_soon) > 0:
                creep.memory.source_num = harvester_that_is_gonna_die_soon[0].memory.source_num
            else:
                creep.memory.source_num = 0

    # If you have nothing but on laboro 1 => get back to harvesting.
    if _.sum(creep.carry) == 0 and creep.memory.laboro == 1:
        if creep.ticksToLive < 5:
            return
        creep.say('☭ 다이나믹 로동!', True)
        creep.memory.laboro = 0
    # if capacity is full(and on harvest phase), get to next work.
    elif (_.sum(creep.carry) >= creep.carryCapacity and creep.memory.laboro == 0) or creep.ticksToLive < 5:
        creep.say('民衆民主主義萬世', True)
        creep.memory.laboro = 1
        del creep.memory.pickup

    # harvesting job. if on harvest(laboro == 0) and carrying energy is smaller than carryCapacity
    if creep.memory.laboro == 0:

        # pickup any dropped resources on the way
        if not creep.memory.pickup:
            dropped = _.filter(dropped_all, lambda c: c.resourceType == RESOURCE_ENERGY)
            if dropped:
                for drop in dropped:
                    # not energy? pass
                    if drop.resourceType != RESOURCE_ENERGY:
                        pass
                    if creep.pos.inRangeTo(drop, 3):
                        creep.memory.pickup = drop.id
                        creep.moveTo(creep.memory.pickup, {'visualizePathStyle':
                                                           {'stroke': '#0000FF', 'opacity': .25}})
                        return
        else:

            grab_result = creep.pickup(Game.getObjectById(creep.memory.pickup))
            # print(creep.memory.pickup)
            # creep.say(grab_result)
            if grab_result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.pickup), {'visualizePathStyle':
                                                                       {'stroke': '#0000FF', 'opacity': .25}})
                return
            elif grab_result == ERR_INVALID_TARGET:
                del creep.memory.pickup
            # elif grab_result == ERR_NOT_ENOUGH_RESOURCES:

                # creep.moveTo(Game.getObjectById(creep.memory.pickup), {'visualizePathStyle':
                #                                                        {'stroke': '#0000FF', 'opacity': .25}})
                # return
            # creep.say(grab_result)
        harvest_stuff.harvest_energy(creep, sources, creep.memory.source_num)

    # if carryCapacity is full - then go to nearest container or storage to store the energy.
    elif creep.memory.laboro == 1:
        if not creep.memory.container:
            # find ALL storages(whether its full doesn't matter)
            storages = _.filter(all_structures, lambda s: (s.structureType == STRUCTURE_STORAGE
                                                           or s.structureType == STRUCTURE_CONTAINER
                                                           or s.structureType == STRUCTURE_LINK))

            storage = creep.pos.findClosestByRange(storages)
            # print('len(storage):', len(storage))
            
            if len(storage) == 0:
                del creep.memory.container
            else:
                creep.memory.container = storage.id
        # find ALL storages(whether its full doesn't matter)
        # storages = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_STORAGE
        #                                           or s.structureType == STRUCTURE_CONTAINER)

        if creep.memory.container:
            # storage = creep.pos.findClosestByRange(storages)
            # HARVESTER ONLY HARVEST ENERGY(AND MAYBE RARE METALS(?)). JUST LET'S NOT MAKE IT DO SOMETHING ELSE.
            # result = creep.transfer(storage, RESOURCE_ENERGY)
            result = creep.transfer(Game.getObjectById(creep.memory.container), RESOURCE_ENERGY)

            # if not in range, get there, duh.
            if result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.container),
                             {'reusePath': 3, vis_key: {stroke_key: '#ffffff'}})
            elif result == ERR_INVALID_TARGET:
                del creep.memory.container
            elif result == ERR_FULL:
                creep.say('차면 찬대로!', True)
                creep.memory.laboro = 0
        else:
            # if there's no storage to go to, technically do the hauler's job(transfer and building).
            # below is exact copy.
            spawns_and_extensions = _.filter(all_structures, lambda s: ((s.structureType == STRUCTURE_SPAWN
                                                              or s.structureType == STRUCTURE_EXTENSION)
                                                              and s.energy < s.energyCapacity))
            spawn_or_extension = creep.pos.findClosestByRange(spawns_and_extensions)
            transfer_result = creep.transfer(spawn_or_extension, RESOURCE_ENERGY)
            if transfer_result == ERR_NOT_IN_RANGE:
                creep.moveTo(spawn_or_extension, {'visualizePathStyle': {'stroke': '#ffffff'},
                                                  'ignoreCreeps': True})
            elif transfer_result == ERR_INVALID_TARGET:
                construction = creep.pos.findClosestByRange(constructions)
                build_result = creep.build(construction)
                if build_result == ERR_NOT_IN_RANGE:
                    creep.moveTo(construction, {'visualizePathStyle': {'stroke': '#ffffff'}})

    return


def run_miner(creep, all_structures, minerals):
    """
    for mining minerals.
    :param creep: The creep to run
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param minerals: creep.room.find(FIND_MINERALS)
    :return:
    """

    # process:
    # 1. look for minerals and go there.
    # 2. mine and store

    # no memory.laboro? make one.
    if not creep.memory.laboro:
        """
        0 = harvest
        1 = carry-to-storage|container / upgrade
        """
        creep.memory.laboro = 0

    # memory.extractor == extractor dude. what else.
    # memory.mineral == mineral
    if not creep.memory.extractor or not creep.memory.mineral:
        try:
            # minerals = creep.room.find(FIND_MINERALS)
            extractors = all_structures.filter(lambda s: s.structureType == STRUCTURE_EXTRACTOR)
            # there's only one mineral per room anyway.
            creep.memory.extractor = extractors[0].id
            creep.memory.mineral = minerals[0].id
        except:
            creep.say("광물못캐!!", True)
            return


    # If you have nothing but on laboro 1 => get back to harvesting.
    if _.sum(creep.carry) == 0 and creep.memory.laboro == 1:
        # if about to die, just die lol
        if creep.ticksToLive < 5:
            return
        creep.say('☭ 다이나믹 로동!', True)
        creep.memory.laboro = 0
    # if capacity is full(and on harvest phase), get to next work.
    elif (_.sum(creep.carry) >= creep.carryCapacity and creep.memory.laboro == 0) or creep.ticksToLive < 5:

        creep.memory.laboro = 1

    # mine
    if creep.memory.laboro == 0:
        mine_result = creep.harvest(Game.getObjectById(creep.memory.mineral))
        # se ne estas en atingopovo(reach), iru.
        if mine_result == ERR_NOT_IN_RANGE\
                or mine_result == ERR_NOT_ENOUGH_ENERGY:
            creep.moveTo(Game.getObjectById(creep.memory.mineral), {'visualizePathStyle':
                                                                    {'stroke': '#0000FF', 'opacity': .25},
                                                                    'ignoreCreeps': True, 'reusePath': 40})
        # if mined successfully or cooldown in effect
        elif mine_result == 0\
                or mine_result == ERR_TIRED:
            pass
        else:
            print('mine error:', mine_result)
        return

    # put them into the container
    elif creep.memory.laboro == 1:

        if Game.time % 2 == 0:
            creep.say('⚒s of 🌏', True)
        else:
            creep.say('UNITE!', True)
        # no container? go find it
        if not creep.memory.container:
            # find ALL storages(whether its full doesn't matter)
            storages = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_STORAGE
                                                          or s.structureType == STRUCTURE_CONTAINER)
            # print(storages)
            storage = creep.pos.findClosestByRange(storages)
            print('storage:', storage)
            print('id:', storage.id)
            creep.memory.container = storage.id

        if creep.memory.container:
            # runs for each type of resources. you know the rest.
            for resource in Object.keys(creep.carry):
                # if creep.carry()
                mineral_transfer = creep.transfer(Game.getObjectById(creep.memory.container), resource)
                # print('res: {}, trans: {}'.format(resource, mineral_transfer))
                if mineral_transfer == ERR_NOT_IN_RANGE:
                    creep.moveTo(Game.getObjectById(creep.memory.container), {'visualizePathStyle': {'stroke': '#ffffff'}})
                    break
                elif mineral_transfer == 0:
                    # print('OK')
                    break
                elif mineral_transfer == ERR_INVALID_TARGET:
                    print('ERROR?')
                    del creep.memory.container
                    break
                elif mineral_transfer == ERR_NOT_ENOUGH_ENERGY:
                    continue
                else:
                    # print('mineral_transfer ERROR:', mineral_transfer)
                    pass
        else:
            print("WTF no container????")

    return
