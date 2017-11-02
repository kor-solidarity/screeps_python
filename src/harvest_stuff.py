from defs import *
import random

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')

# 자원 얻는 방식에 대한 그 모든것은 여기로 간다.


def harvest_energy(creep, sources, source_num):
    """
    자원을 캐고 없으면 다음껄로(다음번호) 보낸다.

    :param creep: the creep. do i have to tell you? intended for harvesters and upgraders.
    :param sources: name says it all. ENERGY_SOURCES list
    :param source_num: sources[creep.memory.source_num]. no use unless
    :return: ain't returning shit.
    """
    vis_key = "visualizePathStyle"
    stroke_key = "stroke"

    # if capacity is full, get to next work.
    # DELETE ALL THIS AND MOVE THEM TO CREEPS.
    # THIS FUNC. MUST WORK ONLY ON HARVESTING
    if _.sum(creep.carry) >= creep.carryCapacity:
        # print('creep.carry.energy >= creep.carryCapacity')
        # print('creep.memory.role:', creep.memory.role)
        creep.memory.laboro = 1
        if creep.memory.role == 'upgrader':
            # print('upgrader')
            # randomly chooses which source to harvest from. not really efficient, but avoids harvester interruption
            total_sources = len(sources)
            # print('number of sources:', total_sources)
            creep.memory.source_num = random.randint(0, total_sources-1)
            creep.say('⚡ Upgrade', True)
        elif creep.memory.role == 'harvester':
            # print('harvester')
            # if harvester, just reset source_num to 0. would need to edit this as i expand.
            creep.memory.source_num = 0
            creep.say('民衆民主主義萬世!', True)
        elif creep.memory.role == 'hauler' or creep.memory.role == 'carrier':
            # print('hauler')
            creep.say('일꾼생산해라좀', True)

    # activate the harvest cmd.
    if creep.memory.role == 'harvester':
        harvested = creep.harvest(sources[source_num])
    else:
        harvested = creep.harvest(creep.pos.findClosestByRange(sources))

    # is sources too far out?
    # creep.say(harvested)
    if harvested == ERR_NOT_IN_RANGE:
        # then go.
        if creep.memory.role == 'hauler':
            creep.moveTo(creep.pos.findClosestByRange(sources), {vis_key: {stroke_key: '#ffffff'}})
        else:
            creep.moveTo(sources[source_num], {vis_key: {stroke_key: '#ffffff'}})
            # creep.say(a)
    # did the energy from the sources got depleted?
    # PROCEED TO NEXT PHASE IF THERE ARE ANYTHING IN CARRY
    # well.... not much important now i guess.
    elif harvested == ERR_NOT_ENOUGH_RESOURCES:
        # if hauler they just have to wait for anything to pop up...
        if creep.memory.role == 'hauler':
            pass
        elif _.sum(creep.carry) > 0:
            creep.say('🐜 SOURCES')
            # do with what you have first...
            creep.memory.laboro = 1


def grab_energy(creep, pickup, only_energy):
    """
    grabbing energy from local storages(container, storage, etc.)
    :param creep:
    :param pickup: creep.memory. 가장 가까운 또는 목표 storage의 ID
    :param only_energy: bool
    :return: any creep.withdraw return codes
    """
    # we will make new script for some stuff.
    
    # NULLIFIED
    # pickup = pickup targetted to pick up.
    # get to the fixed location.
    # if not pickup:
    #     pickup = pickup['id']

    # if there's no energy in the pickup target, delete it
    try:
        # print(pickup, 'type:', Game.getObjectById(pickup).structureType)
        if Game.getObjectById(pickup).structureType != STRUCTURE_LINK:
            if _.sum(Game.getObjectById(pickup).store) < (creep.carryCapacity - _.sum(creep.carry)) * .5:
                del pickup
                # print('checkpoint?')
                return ERR_NOT_ENOUGH_ENERGY
        else:
            if Game.getObjectById(pickup).energy < (creep.carryCapacity - _.sum(creep.carry)) * .5:
                del pickup
                # print('checkpoint??')
                return ERR_NOT_ENOUGH_ENERGY

    # if there's something else popped up, you suck.
    except:
        print('ERROR HAS OCCURED!!!!!!!!!!!!!!!!!!!!')
        print(creep.name, 'pickup obj:', Game.getObjectById(pickup))
        creep.say('ERROR!')
        return ERR_INVALID_TARGET

    # check if memory.pickup is link or not.
    if Game.getObjectById(pickup).structureType == STRUCTURE_CONTAINER \
            or Game.getObjectById(pickup).structureType == STRUCTURE_STORAGE:
        carry_objects = Game.getObjectById(pickup).store
    else:
        carry_objects = Game.getObjectById(pickup).energy

    # -----------------------------------------------

    # check_name = 'Layla'
    # if creep.name == check_name:
    #     print('len(carry_objects):', len(carry_objects))

    # if len(carry_objects) == STRUCTURE_LINK
    if len(carry_objects) == 0:
        # pick it up.
        return creep.withdraw(Game.getObjectById(pickup), RESOURCE_ENERGY)

        return grab_action

        # NULLIFIED. All actions except actually grabbing the resources will not be done in here.
        # creep.say(grab_action)
        if grab_action == ERR_NOT_IN_RANGE:
            creep.moveTo(Game.getObjectById(pickup),
                         {'visualizePathStyle': {'stroke': '#ffffff'}})

        elif grab_action == 0:
            # idk why but they're returning 0 before actually grabbing.
            del pickup
            # a part switching to new laboro, let's not do that in shared script.
            if creep.memory.role == 'hauler' or creep.memory.role == 'carrier':
                creep.memory.laboro = 1
                creep.memory.priority = 0
                creep.say('BEEP BEEP⛟', True)

        # other errors? just delete 'em
        else:
            del pickup

    # else == STRUCTURE_CONTAINER || STRUCTURE_STORAGE
    else:
        # resources = Object.keys(carry_objects)
        # for some_resources in resources:
        #     if Game.getObjectById(pickup).store[some_resources] == 0:
        #         resources.splice(some_resources, 1)
        for resource in Object.keys(carry_objects):
            # if the creep only need to pick up energy.
            if only_energy and resource != 'energy':
                continue
            # and there's no energy there
            elif only_energy and Game.getObjectById(pickup).store[resource] == 0:
                creep.say('noEnergy')
                print('noEnergy')
                del pickup
                return ERR_NOT_ENOUGH_ENERGY

            # # only hauler and carrier should withdraw something else than energy.
            # if (creep.memory.role != 'hauler' and creep.memory.role != 'carrier') \
            #         and resource != 'energy':
            #     continue

            # # if not a hauler AND selected container doesn't have any energy, delete this
            # # not supposed to get in here AT ALL THO.
            # elif (creep.memory.role != 'hauler' and creep.memory.role != 'carrier') \
            #         and Game.getObjectById(pickup).store[resource] == 0:
            #
            #     creep.say('noEnergy')
            #
            #     del pickup
            #
            #     return


            # if creep.name == check_name:
                # print('ID:', Game.getObjectById(pickup).id)
                # print('Object.keys(carry_objects):', Object.keys(carry_objects))
                # print('len(Object.keys(carry_objects)):', len(Object.keys(carry_objects)))
                # print('Game.getObjectById(pickup).store[', resource, ']:', Game.getObjectById(pickup).store[resource])
            # if there's no such resource, pass it to next loop.
            if Game.getObjectById(pickup).store[resource] == 0:
                # if creep.name == check_name:
                #     print('WTF')
                continue

            # pick it up.
            grab_action = creep.withdraw(Game.getObjectById(pickup), resource)

            if grab_action == ERR_NOT_ENOUGH_RESOURCES:
                print(resource)
            # print(creep.name, 'grab_action:', grab_action)
            # 오직 잡기 결과값만 반환한다. 이 함수에서 수거활동 외 활동을 금한다!
            return grab_action

            # if creep.name == check_name:
            #     print('grabs???:', grab_action)
            if grab_action == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(pickup),
                             {'visualizePathStyle': {'stroke': '#ffffff'}})

            elif grab_action == 0:
                # idk why but they're returning 0 before actually grabbing.
                del pickup
                # a part switching to new laboro, let's not do that in shared script.
                if creep.memory.role == 'hauler' or creep.memory.role == 'carrier' \
                        or creep.memory.role == 'helper_carrier':
                    if _.sum(creep.carry) >= creep.carryCapacity * .5:
                        creep.memory.laboro = 1
                        creep.memory.priority = 0
                    if resource == 'energy':
                        creep.say('BEEP BEEP⛟', True)
                    else:
                        creep.say("GRAB 💎s", True)

                break

            # other errors? just delete 'em
            else:
                print(creep.name, 'ELSE ERROR:', grab_action)
                del pickup

    # ------------------------------------------------


def pick_drops(creep, drop):
    """
    pick up dropped resources
    :param creep:
    :param drop:
    :return:
    """
    # 떨군머시기 위치 찾기
    dropped_pickups = creep.room.find(FIND_DROPPED_RESOURCES)
    creeps_pickup = dropped_pickups.filter(lambda d: d.id == creep.memory.dropped_target['id'])

    # it returned as an array. so need to select one(tho there is only one)
    result = creep.pickup(creeps_pickup[0])

    if result == ERR_NOT_IN_RANGE:
        # creep.moveTo(creep.memory.dropped_target['pos'], {'visualizePathStyle': {'stroke': '#0000FF'}})
        creep.moveTo(creeps_pickup[0], {'visualizePathStyle':
                                            {'stroke': '#0000FF', 'opacity': .25}})
    # if you picked it up or it's not there anymore.
    elif result == 0:
        # 집거나 없어서 못먹을 경우 우선 적재량 35%을 채웠는지 확인한다.
        # 안 채웠으면 계속 수확
        if _.sum(creep.carry) > creep.carryCapacity * .35:
            # creep.say(result)
            del creep.memory.dropped_target
            creep.memory.laboro = 1
            creep.memory.priority = 0
    elif result == ERR_INVALID_TARGET:
        del creep.memory.dropped_target



    pass
