from defs import *
import harvest_stuff
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


def run_hauler(creep, all_structures, constructions, creeps, dropped_all, repairs, terminal_capacity):
    """
    :param creep:
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
    :param creeps: creep.room.find(FIND_MY_CREEPS)
    :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES)
    :param repairs: look at main.
    :param terminal_capacity: 방 안의 터미널 내 에너지 최소값.
    :return:
    """

    # this guy's job: carrying energy from containers. repairing stuff on the way.
    # and when all those are done it's gonna construct. repairing stuff on the way.
    # when all those are done it's gonna repair stuff around.
    # and when that's all done they're going for upgrade.

    # IMPORTANT: when hauler does a certain work, they must finish them before doing anything else!

    """
    haul_target == 운송 목적지.
    repair_target == 수리 목표.
    upgrade_target == 업그레이드 목표
    build_target == 건설 목표
    dropped_target == 근처에 떨어져있는 리소스
    pickup == 에너지 빼갈 대상.
    to_storage == 스토리지로 운송할 것인가?(불리언)
    """

    # 운송업 외 다른일은 지극히 제한적으로만 써야한다.
    # 주의! 1 == 100%
    outer_work_perc = .7

    max_energy_in_storage = 500000

    # priority 0 통과했는가? 통과했으면 priority 1 쓸때 스트럭쳐 필터 안해도됨.
    passed_priority_0 = False

    # 혹시 딴짓하다 옆방으로 새는거에 대한 대비
    if not creep.memory.upgrade_target:
        creep.memory.upgrade_target = Game.rooms[creep.memory.assigned_room].controller['id']

    end_is_near = 30
    # in case it's gonna die soon. this noble act is only allowed if there's a storage in the room.
    if creep.ticksToLive < end_is_near and _.sum(creep.carry) != 0 and creep.room.storage:
        creep.say('endIsNear')
        if creep.memory.haul_target:
            del creep.memory.haul_target
        elif creep.memory.pickup:
            del creep.memory.pickup
        for minerals in Object.keys(creep.carry):
            # print('minerals:', minerals)
            transfer_minerals_result = creep.transfer(creep.room.storage, minerals)
            # print(transfer_minerals_result)
            if transfer_minerals_result == ERR_NOT_IN_RANGE:
                creep.moveTo(creep.room.storage, {'visualizePathStyle': {'stroke': '#ffffff'}})
                break
            elif transfer_minerals_result == 0:
                break
        return
    elif creep.ticksToLive < end_is_near and creep.room.storage:
        creep.suicide()
        # if creep.memory.haul_target:
        #     del creep.memory.haul_target
        # elif creep.memory.pickup:
        #     del creep.memory.pickup
        # creep.say('TTL:' + creep.ticksToLive)
        # creep.moveTo(creep.room.controller,
        #              {'visualizePathStyle': {'stroke': '#ffffff'}, 'ignoreRoads': True, 'ignoreCreeps': True
        #                  , 'reusePath': 40})
        return

    # if there's nothing to carry then get to harvesting.
    # being not zero also includes being None lol
    if _.sum(creep.carry) == 0 and creep.memory.laboro != 0:
        creep.memory.laboro = 0
        creep.say('🚛운송투쟁!', True)
        del creep.memory.to_storage
        del creep.memory.haul_target
        del creep.memory.build_target
        del creep.memory.repair_target

    elif _.sum(creep.carry) > creep.carryCapacity * .90 and creep.memory.laboro == 0:
        if creep.memory.dropped_target:
            del creep.memory.dropped_target
            # Memory.initialize_count += 2
        if creep.memory.pickup:
            del creep.memory.pickup
        creep.memory.laboro = 1
        creep.memory.priority = 0

    # laboro: 0 == pickup something.
    if creep.memory.laboro == 0:
        # 1. look for dropped resources and get them
        # 2. if 1 == False, look for storage|containers to get the energy from.
        # 3. if 2 == False, you harvest on ur own.
        dropped = creep.pos.findClosestByRange(dropped_all)

        # if there's no dropped_target and there's dropped_all
        if not creep.memory.dropped_target and len(dropped_all) > 0:
            for dropped in dropped_all:
                # if there's a dropped resources near 5
                if creep.pos.inRangeTo(dropped, 5):
                    # if not energy and there's no storage, pass.
                    if not creep.room.storage and dropped.resourceType != RESOURCE_ENERGY:
                        continue
                    else:
                        creep.memory.dropped_target = dropped['id']
                        # print(dropped['id'])
                        creep.say('⛏BITCOINS!', True)
                        break

        # if there is a dropped target and it's there.
        if creep.memory.dropped_target:
            item = Game.getObjectById(creep.memory.dropped_target)
            grab = creep.pickup(item)
            if grab == 0:
                del creep.memory.dropped_target
                creep.say('♻♻♻', True)
                return
            elif grab == ERR_NOT_IN_RANGE:
                creep.moveTo(item, {'visualizePathStyle': {'stroke': '#0000FF', 'opacity': .25}, 'reusePath': 10})
                return
            # if target's not there, go.
            elif grab == ERR_INVALID_TARGET:
                del creep.memory.dropped_target
                for dropped in dropped_all:
                    # if there's a dropped resources near 5
                    if creep.pos.inRangeTo(dropped, 5):
                        creep.memory.dropped_target = dropped_all['id']
                        return

        else:
            # only search if there's nothing to pick up.
            if not creep.memory.pickup:

                # find any containers/links with any resources inside
                storages = all_structures.filter(lambda s:
                                                 (s.structureType == STRUCTURE_CONTAINER
                                                  and _.sum(s.store) >= creep.carryCapacity * .45)
                                                 or (s.structureType == STRUCTURE_LINK
                                                     and s.energy >= creep.carryCapacity * .45
                                                     and not
                                                     (s.pos.x < 5 or s.pos.x > 44 or s.pos.y < 5 or s.pos.y > 44)))
                # 위 목록 중에서 가장 가까이 있는 컨테이너를 뽑아간다. 만약 뽑아갈 대상이 없을 시 터미널, 스토리지를 각각 찾는다.
                pickup_id = miscellaneous.pick_pickup(creep, creeps, storages, terminal_capacity)
                if pickup_id == ERR_INVALID_TARGET:
                    pass
                else:
                    creep.memory.pickup = pickup_id

            # if creep already have pickup memory, no need to search for storage.
            else:
                storage = []

            if storage or creep.memory.pickup:
                if not creep.memory.pickup:
                    creep.memory.pickup = storage

                # did hauler got order to grab only energy?
                if creep.memory.only_energy:
                    only_energy = True
                    del creep.memory.only_energy
                else:
                    only_energy = False
                # grabs any resources left in the storage if there are any.
                result = harvest_stuff.grab_energy(creep, creep.memory.pickup, only_energy)
                if result == ERR_NOT_IN_RANGE:
                    move_it = creep.moveTo(Game.getObjectById(creep.memory.pickup),
                                           {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 25})

                    if move_it == ERR_NO_PATH:
                        for c in creeps:
                            if creep.pos.inRangeTo(c, 1) and not c.name == creep.name:
                                mv = creep.moveTo(c)
                                break
                elif result == 0:
                    creep.say('BEEP BEEP⛟', True)
                    # if _.sum(creep.carry) >= creep.carryCapacity * .5:
                    del creep.memory.pickup
                    creep.memory.laboro = 1
                    creep.memory.priority = 0
                elif result == ERR_NOT_ENOUGH_ENERGY:
                    del creep.memory.pickup
                    return
                # other errors? just delete 'em
                else:
                    print('{} the {} in  {} - grab_energy() ELSE ERROR: {}'.format(creep.name, creep.memory.role
                                                                                   , creep.room.name, result))
                    del creep.memory.pickup

            else:
                # if there's nothing in the storage they harvest on their own.
                if not creep.memory.source_num:
                    creep.memory.source_num = creep.pos.findClosestByRange(creep.room.find(FIND_SOURCES)).id

                harvest_stuff.harvest_energy(creep, creep.memory.source_num)
        # 꽉차면 초기화작업과 작업변환.
        if _.sum(creep.carry) >= creep.carryCapacity:
            del creep.memory.source_num
            creep.memory.laboro = 1
            creep.memory.priority = 0

    # get to work.
    elif creep.memory.laboro == 1:
        # PRIORITY
        # 1. carry them to storage, spawns, towers, etc
        # 2. if 1 is all full, start building local. and 1/3 chance to build despite 1 == True
        # 3. repair. in fact, repair everything on the way during phase 1 and 2
        # 4. upgrade along with role.upgrader
        # in order for these phases to work, we need to label their each works and don't let them do
        # something else other than this one.

        if not creep.memory.priority:
            creep.memory.priority = 0

        # if their priority is not decided. gonna need to pick it firsthand.
        if creep.memory.priority == 0:
            passed_priority_0 = True

            # 40% 이상 채우지 않으면 건설은 없다. 건설보다 운송이 더 시급하기 때문.
            if len(constructions) > 0 and creep.room.energyAvailable >= creep.room.energyCapacityAvailable * .4:
                # for 1/3 chance going to phase 2.
                picker = random.randint(0, 2)
            else:
                picker = 0
            # defining structures to fill the energy on. originally above of this spot but replaced for cpu eff.
            # towers only fills 80% since it's gonna repair here and there all the time.
            structures = all_structures.filter(lambda s: ((s.structureType == STRUCTURE_SPAWN
                                                           or s.structureType == STRUCTURE_EXTENSION)
                                                          and s.energy < s.energyCapacity)
                                                         or (s.structureType == STRUCTURE_TOWER
                                                             and s.energy < s.energyCapacity * 0.8)
                                                         or (s.structureType == STRUCTURE_STORAGE
                                                             and s.store[RESOURCE_ENERGY] < max_energy_in_storage)
                                                         or (s.structureType == STRUCTURE_TERMINAL
                                                             and s.store[RESOURCE_ENERGY] < terminal_capacity))

            container = all_structures.filter(lambda s:
                                              s.structureType == STRUCTURE_CONTAINER
                                              and s.pos.inRangeTo(creep.room.controller, 6)
                                              and _.sum(s.store) < s.storeCapacity)
            extra_container_to_fill = 0
            extra_container_to_be_filled = 0
            # 업그레이드용 컨테이너가 보일 경우.
            if len(container) > 0:
                # print('cont!!{}'.format(container))
                for ct in container:
                    sources = creep.room.find(FIND_SOURCES)
                    sources.push(creep.room.find(FIND_MINERALS)[0])

                    for_upgrade = False
                    # 컨테이너가 소스 옆에 있을 경우 대상이 아니니 삭제한다.
                    for s in sources:
                        # 크립거리가 세칸 이내인가? 맞으면 하비스터 용도니 넣지 않는다.
                        if len(ct.pos.findPathTo(s, {'ignoreCreeps': True})) <= 3:
                            pass
                        else:
                            # 세칸 이내가 아니면 업그레이드 용도 맞음. 고로 넣는다.
                            for_upgrade = True
                            break
                    if for_upgrade:
                        extra_container_to_be_filled += 2000
                        extra_container_to_fill += _.sum(ct.store)
                        structures.push(ct)
                        # print('there\'s a container!')

            # 스토리지에서 자원을 캐고 현재 에너지가 90% 이상 찬 경우 발전에 보탠다.
            if creep.room.storage and \
                    (creep.pos.inRangeTo(creep.room.storage, 1)
                     and (creep.room.energyAvailable + extra_container_to_fill)
                            > (creep.room.energyCapacityAvailable + extra_container_to_be_filled) * .9):

                chance = random.randint(0, 2)
                if chance == 0:
                    creep.say('💎물류,염려말라!', True)
                    creep.memory.priority = 1

                    # 여기서 스토리지를 목록에서 없앤다. 스토리지는 항상 마지막에 채운다.
                    index = structures.indexOf(creep.room.storage)
                    structures.splice(index, 1)
                    # print('delete?', structures)

                elif chance == 1:
                    creep.say('🔥 위대한 발전!', True)
                    creep.memory.priority = 4
                elif chance == 2:
                    creep.say('☭ 세상을 고치자!', True)
                    creep.memory.priority = 3

            elif len(structures) > 0 and (picker != 2 or not len(constructions) > 0):
                creep.say('🔄물류,염려말라!', True)
                creep.memory.priority = 1

                # 여기서 스토리지를 목록에서 없앤다. 스토리지는 항상 마지막에 채운다.
                index = structures.indexOf(creep.room.storage)
                structures.splice(index, 1)
                # print('delete?', structures)

            elif len(constructions) > 0 or picker == 2:
                creep.say('🚧 건설투쟁!', True)
                creep.memory.priority = 2
            elif len(repairs) > 0:
                creep.say('⚒ 수리!', True)
                creep.memory.priority = 3
            else:
                creep.say('⚡ 위대한 발전!', True)
                creep.memory.priority = 4

        # priority 1: transfer
        if creep.memory.priority == 1:
            # print("{}, to_storage?: {}".format(creep.name, creep.memory.to_storage))
            # if creep is assigned to store to storage
            # all resources must be stored
            if creep.memory.to_storage:
                for resource in Object.keys(creep.carry):
                    storage_transfer = creep.transfer(creep.room.storage, resource)
                    if storage_transfer == ERR_NOT_IN_RANGE:
                        move_it = creep.moveTo(creep.room.storage, {'visualizePathStyle': {'stroke': '#ffffff'}
                            , 'reusePath': 20})
                        # 사각지대 안에 갇힐 경우 크립이 겹친거니 바로옆 크립 아무한테나 간다.
                        # print('{} the {} moveit: {}'.format(creep.name, creep.memory.role, move_it))
                        if move_it == ERR_NO_PATH:
                            for c in creeps:
                                if creep.pos.inRangeTo(c, 1) and not c.name == creep.name:
                                    creep.moveTo(c)
                                    break
                        break
                    elif storage_transfer == 0:
                        break
                    else:
                        print('to storage error:', storage_transfer)
            else:
                # check if haul_target's capacity is full
                if creep.memory.haul_target:
                    target = Game.getObjectById(creep.memory.haul_target)
                    # haul_target 이 중간에 폭파되거나 등등...
                    if not target:
                        del creep.memory.haul_target
                    elif target.structureType != STRUCTURE_CONTAINER and target.energy >= target.energyCapacity:
                        del creep.memory.haul_target
                    elif _.sum(target.store) >= target.storeCapacity:
                        del creep.memory.haul_target

                # haul_target == cela adreso por porti la energion.
                if not creep.memory.haul_target and creep.carry.energy > 0:
                    if not passed_priority_0:
                        # todo 업그레이더 전용 컨테이너가 존재할 경우 거기다가도 보내야함. 추가합시다.
                        structures = all_structures.filter(lambda s: ((s.structureType == STRUCTURE_SPAWN
                                                                       or s.structureType == STRUCTURE_EXTENSION
                                                                       or s.structureType == STRUCTURE_NUKER)
                                                                      and s.energy < s.energyCapacity)
                                                                     or (s.structureType == STRUCTURE_TOWER
                                                                         and s.energy < s.energyCapacity * 0.8))

                        container = all_structures.filter(lambda s:
                                                          s.structureType == STRUCTURE_CONTAINER
                                                          and s.pos.inRangeTo(creep.room.controller, 6)
                                                          and _.sum(s.store) < s.storeCapacity)
                        # 업그레이드용 컨테이너가 보일 경우.
                        if len(container) > 0:
                            # print('cont!!{}'.format(container))
                            for ct in container:
                                sources = creep.room.find(FIND_SOURCES)
                                sources.push(creep.room.find(FIND_MINERALS)[0])

                                for_upgrade = False
                                # 컨테이너가 소스 옆에 있을 경우 대상이 아니니 삭제한다.
                                for s in sources:
                                    # 크립거리가 세칸 이내인가? 맞으면 하비스터 용도니 넣지 않는다.
                                    if len(ct.pos.findPathTo(s, {'ignoreCreeps': True})) <= 3:
                                        pass
                                    else:
                                        # 세칸 이내가 아니면 업그레이드 용도 맞음. 고로 넣는다.
                                        for_upgrade = True
                                        break
                                if for_upgrade:
                                    structures.push(ct)
                                    # print('there\'s a container!')

                    portist_kripoj = _.filter(creeps, lambda c: c.memory.role == 'hauler')

                    while not creep.memory.haul_target or len(structures) > 0:
                        # size_counter is used to determines the number of creeps that can be added to the haul_target.
                        size_counter = 0

                        # if theres no structures to haul to, then no reason to do this loop
                        if len(structures) == 0:
                            break

                        structure = creep.pos.findClosestByRange(structures)

                        for kripo in portist_kripoj:
                            # se nomo de kripo estas sama kun ĉi tiu creep-o aŭ kripo ne havas haul_target, transsaltu
                            if creep.name == kripo or not kripo.memory.haul_target:
                                continue

                            # se kripo.memory.haul_target estas sama kun structure.id, ankaŭ transsaltu.
                            if kripo.memory.haul_target == structure.id:
                                # SED se structure estas tower(turo) aŭ spawn(nesto), kalkulu la grandeco(size).
                                if structure.structureType != STRUCTURE_EXTENSION:
                                    # se la structure estas turo
                                    if structure.structureType == STRUCTURE_TOWER:
                                        # 현재 세 경우가 필요함.
                                        # 1. 70% 이상 찬 경우: 하나만 있으면 됨.
                                        # 2. 35%-70% 찬 경우: 2.
                                        # 3. 그 이하: 3
                                        # 위의 역순으로 나열
                                        if structure.energy < structure.energyCapacity * .3:
                                            # nur plusas 1 ĉar en ĉi tio stato ni bezonas 3 kripoj
                                            size_counter += 1

                                        elif structure.energy < structure.energyCapacity * .65:
                                            size_counter += 2
                                        else:
                                            size_counter += 3
                                    # se la structure estas NUKER
                                    elif structure.structureType == STRUCTURE_NUKER:
                                        if structure.energy <= structure.energyCapacity * .999:
                                            # nur plusas 1 ĉar en ĉi tio stato ni bezonas 3 kripoj
                                            size_counter += 1
                                        else:
                                            size_counter += 3
                                    # 업글용 컨테이너일 경우? 원리는 타워와 똑같다.
                                    elif structure.structureType == STRUCTURE_CONTAINER:
                                        if _.sum(structure.store) < structure.storeCapacity * .5:
                                            # nur plusas 1 ĉar en ĉi tio stato ni bezonas 3 kripoj
                                            size_counter += 1
                                        elif _.sum(structure.store) < structure.storeCapacity * .8:
                                            size_counter += 2
                                        else:
                                            size_counter += 3
                                        # print('STRUCTURE_CONTAINER, counter: {}'.format(size_counter))
                                    # aŭ estas nesto
                                    else:
                                        # if spawn's energy is half-full, only one hauler is needed.
                                        if structure.energy > structure.energyCapacity * .5:
                                            size_counter += 3
                                        else:
                                            size_counter += 2
                                # alia == structure estas extension-o
                                else:
                                    size_counter += 3

                        # if STRUCTURE_SPAWN is right next to creep and has 90% or more energy, no need to haul there.
                        # made to avoid chance of haulers getting healed multiple times and getting stuck
                        if structure.structureType == STRUCTURE_SPAWN:
                            if creep.pos.isNearTo(Game.getObjectById(structure.id)) \
                                    and structure.energy >= structure.energyCapacity * .9:

                                size_counter += 3

                        # size_counter estas malpli ol 3 == structure povas asigni al creep-o
                        if size_counter < 3:
                            # asignu ID kaj brakigi.
                            creep.memory.haul_target = structure.id
                            break

                        else:
                            index = structures.indexOf(structure)
                            structures.splice(index, 1)

                # if we have something that's not energy
                if _.sum(creep.carry) != 0 and creep.carry[RESOURCE_ENERGY] == 0:
                    ht = Game.getObjectById(creep.memory.haul_target)
                    if ht:
                        # 만약 이 시점에서 에너지 자원을 배분중이면 취소한다.
                        if ht.structureType == STRUCTURE_EXTENSION or ht.structureType == STRUCTURE_SPAWN or \
                                        ht.structureType == STRUCTURE_NUKER or ht.structureType == STRUCTURE_TOWER:
                            del creep.memory.haul_target

                    if not ht:
                        minerals = creep.room.find(FIND_MINERALS)

                        # 터미널이 존재하고 크립이 가지고 있는 템이 방에서 나오는 자원일 경우 터미널에 넣는다.
                        if creep.room.terminal and creep.carry[minerals[0].mineralType] > 0:
                            creep.memory.haul_target = creep.room.terminal.id
                        else:
                            creep.memory.haul_target = creep.room.storage.id
                    # reset
                    ht = Game.getObjectById(creep.memory.haul_target)

                    for minerals in Object.keys(creep.carry):

                        transfer_minerals_result = creep.transfer(ht, minerals)

                        if transfer_minerals_result == ERR_NOT_IN_RANGE:
                            creep.moveTo(ht, {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
                            break
                        elif transfer_minerals_result == 0:
                            break

                else:
                    # todo 컨테이너 꽉 찼을 경우 목표취소 안한다. 이거 수정해야함. 근접한 후에서야 -8 오류뜲
                    # transfer_result = creep.transfer(structure, RESOURCE_ENERGY)
                    transfer_result = creep.transfer(Game.getObjectById(creep.memory.haul_target), RESOURCE_ENERGY)
                    if transfer_result == ERR_NOT_IN_RANGE:
                        if len(repairs) > 0:
                            repair = creep.pos.findClosestByRange(repairs)
                            creep.repair(repair)

                        creep.moveTo(Game.getObjectById(creep.memory.haul_target),
                                     {'visualizePathStyle': {'stroke': '#ffffff'}, 'ignoreCreeps': True
                                      # , 'reusePath': 40, 'ignore': constructions})
                                         , 'reusePath': 40})
                    # if done, check if there's anything left. if there isn't then priority resets.
                    elif transfer_result == ERR_INVALID_TARGET:
                        del creep.memory.haul_target

                        # chk if there's something to build
                        if len(constructions) > 0:
                            creep.say('🚧 공사전환!', True)
                            creep.memory.priority = 2
                            return

                        # in case there's no storage
                        try:
                            # ERR_INVALID_TARGET == nothing to store == look for storage with energy less than 5k
                            # first, look for terminal and check if energy is less than 5k
                            if creep.room.terminal and creep.room.terminal.store[RESOURCE_ENERGY] <= terminal_capacity:
                                creep.say('경제활성화!', True)
                                creep.memory.haul_target = creep.room.terminal.id
                                creep.moveTo(Game.getObjectById(creep.memory.haul_target),
                                             {'visualizePathStyle': {'stroke': '#ffffff'}, 'ignoreCreeps': True,
                                              'reusePath': 40, 'range': 1})
                                return
                            elif creep.room.storage \
                                    and creep.room.storage.store[RESOURCE_ENERGY] < max_energy_in_storage:
                                creep.say('📦 저장합시다', True)
                                # creep
                                creep.memory.to_storage = True
                                move_it = creep.moveTo(creep.room.storage, {'visualizePathStyle': {'stroke': '#ffffff'}
                                                       , 'reusePath': 20})
                                return
                            else:
                                creep.say('발전으로!', True)
                                creep.memory.priority = 4
                                return
                        except:
                            print('no storage I guess')
                        creep.memory.priority = 0
                        del creep.memory.to_storage
                    elif transfer_result == 0:
                        # creep.say('done!')
                        del creep.memory.haul_target
                    else:
                        creep.say(transfer_result)
                        del creep.memory.haul_target

        # priority 2: build
        elif creep.memory.priority == 2:

            if not creep.memory.build_target:

                closest_construction = creep.pos.findClosestByRange(constructions)
                # 이 시점에서 안뜨면 건설할게 없는거임.
                if not closest_construction:
                    creep.say("지을게 없군 👏", True)
                    creep.memory.priority = 0
                    return
                else:
                    creep.memory.build_target = closest_construction.id

            build_result = creep.build(Game.getObjectById(creep.memory.build_target))

            if build_result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.build_target)
                             , {'visualizePathStyle': {'stroke': '#ffffff'}, 'range': 3, 'reusePath': 10})

            # if there's nothing to build or something
            elif build_result == ERR_INVALID_TARGET:
                # creep.memory.priority = 0
                del creep.memory.build_target
                return

            # if having anything other than energy when not on priority 1 switch to 1
            if _.sum(creep.carry) != 0 and creep.carry[RESOURCE_ENERGY] == 0:
                creep.memory.priority = 1
                del creep.memory.build_target

        # priority 3: repair
        elif creep.memory.priority == 3:
            if creep.memory.repair_target:
                repair = Game.getObjectById(creep.memory.repair_target)
                if repair.hits == repair.hitsMax:
                    del creep.memory.repair_target

            if not creep.memory.repair_target:
                if len(repairs) > 0:
                    creep.memory.repair_target = creep.pos.findClosestByRange(repairs).id
                    repair = Game.getObjectById(creep.memory.repair_target)
                # no repairs? GTFO
                else:
                    creep.memory.priority = 0
                    return

            repair_result = creep.repair(repair)
            # print('{} the {}: repair_result {}'.format(creep.name, creep.memory.role, repair_result))
            if repair_result == ERR_NOT_IN_RANGE:
                creep.moveTo(repair, {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 10, 'range': 3})
            elif repair_result == ERR_INVALID_TARGET:
                del creep.memory.repair_target

            # 어쨌건 운송이 주다. 다만 레벨 8이면 수리에 전념할 수 있다.
            if (_.sum(creep.carry) < creep.carryCapacity * outer_work_perc and creep.room.controller.level != 8) \
                    or creep.carry[RESOURCE_ENERGY] == 0:
                creep.memory.priority = 1

        # priority 4: upgrade the controller
        elif creep.memory.priority == 4:
            upgrade_result = creep.upgradeController(Game.getObjectById(creep.memory.upgrade_target))
            if upgrade_result == ERR_NOT_IN_RANGE:
                creep.moveTo(Game.getObjectById(creep.memory.upgrade_target)
                             , {'visualizePathStyle': {'stroke': '#ffffff'}, 'range': 3, 'reusePath': 10})
            # if having anything other than energy when not on priority 1 switch to 1
            # 운송크립은 발전에 심혈을 기울이면 안됨.
            if (creep.carry[RESOURCE_ENERGY] <= 0 or _.sum(creep.carry) <= creep.carryCapacity * outer_work_perc) \
                    and creep.room.controller.level > 3:
                creep.memory.priority = 1
                creep.say('복귀!', True)
                del creep.memory.to_storage
                return

        if _.sum(creep.carry) == 0:
            creep.memory.priority = 0
            creep.memory.laboro = 0
            del creep.memory.to_storage
