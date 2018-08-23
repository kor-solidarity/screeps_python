from defs import *
from movement import *
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
    dropped == 근처에 떨어져있는 리소스
    pickup == 에너지 빼갈 대상.
    to_storage == 스토리지로 운송할 것인가?(불리언)
    """

    # 운송업 외 다른일은 지극히 제한적으로만 써야한다.
    # 주의! 1 == 100%
    outer_work_perc = .7

    max_energy_in_storage = 600000

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

    elif creep.memory.laboro == 0 and \
            ((_.sum(creep.carry) >= creep.carryCapacity * .5
              and creep.memory.laboro == 0 and not creep.memory.dropped)
                or _.sum(creep.carry) == creep.carryCapacity):
        # if creep.memory.dropped:
        #     del creep.memory.dropped
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

        # if there is a dropped target and it's there.
        if creep.memory.dropped:
            item = Game.getObjectById(creep.memory.dropped)
            if not item:
                del creep.memory.dropped
            else:
                # if the target is a tombstone
                if item.creep:
                    if _.sum(item.store) == 0:
                        creep.say("💢 텅 비었잖아!", True)
                        del creep.memory.dropped
                    # for resource in Object.keys(item.store):
                    grab = harvest_stuff.grab_energy(creep, creep.memory.dropped, False, 0)
                else:
                    grab = creep.pickup(item)
                if grab == 0:
                    # del creep.memory.dropped
                    creep.say('♻♻♻', True)
                    return
                elif grab == ERR_NOT_IN_RANGE:
                    creep.moveTo(item, {'visualizePathStyle': {'stroke': '#0000FF', 'opacity': .25}, 'reusePath': 10})
                    return
                # if target's not there, go.
                elif grab == ERR_INVALID_TARGET:
                    creep.say('ERR', grab)
                    del creep.memory.dropped
                    for drop in dropped_all:
                        # if there's a dropped resources near 5
                        if creep.pos.inRangeTo(drop, 5):
                            creep.memory.dropped = dropped_all['id']

        # if there's no dropped and there's dropped_all
        if not creep.memory.dropped and len(dropped_all) > 0:
            for drop in dropped_all:
                # if there's a dropped resources near 5
                if creep.pos.inRangeTo(drop, 5):
                    # if not energy and there's no storage, pass.
                    if not creep.room.storage and drop.resourceType != RESOURCE_ENERGY:
                        continue
                    else:
                        creep.memory.dropped = drop['id']
                        # print(dropped['id'])
                        creep.say('⛏BITCOINS!', True)
                        creep.moveTo(Game.getObjectById(creep.memory.dropped),
                                     {'visualizePathStyle': {'stroke': '#0000FF', 'opacity': .25}, 'reusePath': 10})
                        break

        if not creep.memory.dropped:
            # only search if there's nothing to pick up.
            if not creep.memory.pickup:

                # find any containers/links with any resources inside
                storages = all_structures.filter(lambda s:
                                                 (s.structureType == STRUCTURE_CONTAINER
                                                  and _.sum(s.store) >= creep.carryCapacity * .5)
                                                 or (s.structureType == STRUCTURE_LINK
                                                     and s.energy >= creep.carryCapacity * .5))

                # 위 목록 중에서 가장 가까이 있는 컨테이너를 뽑아간다.
                # 만약 뽑아갈 대상이 없을 시 터미널, 스토리지를 각각 찾는다.
                # 만일 연구소를 안채우기로 했으면 거기서도 뽑는다.
                if Memory.rooms[creep.room.name].options.fill_labs == 0:
                    # print('no nuke')
                    labs = all_structures\
                        .filter(lambda s: s.structureType == STRUCTURE_LAB and s.energy >= creep.carryCapacity * .5)
                    storages.extend(labs)

                pickup_id = miscellaneous.pick_pickup(creep, creeps, storages, terminal_capacity)
                # print('pickupId', pickup_id)
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

                # did hauler got order to grab only energy? or lab/storage where there can be multiple sources?
                if creep.memory.only_energy or Game.getObjectById(creep.memory.pickup).structureType == STRUCTURE_LAB \
                        or Game.getObjectById(creep.memory.pickup).structureType == STRUCTURE_STORAGE:
                    only_energy = True
                    del creep.memory.only_energy
                else:
                    only_energy = False
                # grabs any resources left in the storage if there are any.
                result = harvest_stuff.grab_energy(creep, creep.memory.pickup, only_energy)
                # print(creep.name, creep.memory.pickup, result)
                if result == ERR_NOT_IN_RANGE:
                    move_it = creep.moveTo(Game.getObjectById(creep.memory.pickup),
                                           {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 25})
                    # print('moveIt', move_it)
                    if move_it == ERR_NO_PATH:
                        for c in creeps:
                            if creep.pos.inRangeTo(c, 1) and not c.name == creep.name:
                                mv = creep.moveTo(c)
                                break
                # 온전하게 집었을 경우.
                # 여러 자원을 뽑아야 하는 경우도 있는지라 이거 한번에 laboro 를 1로 전환하지 않는다.
                elif result == 0:
                    creep.say('BEEP BEEP⛟', True)
                    # if _.sum(creep.carry) >= creep.carryCapacity * .5:
                    # del creep.memory.pickup
                    # creep.memory.laboro = 1
                    # creep.memory.priority = 0

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

        if creep.room.name != creep.memory.assigned_room:
            miscellaneous.get_to_da_room(creep, creep.memory.assigned_room, False)
            return

        if not creep.memory.priority and not creep.memory.priority == 0:
            creep.memory.priority = 0

        # if their priority is not decided. gonna need to pick it firsthand.
        if creep.memory.priority == 0:
            passed_priority_0 = True

            # 전체 에너지의 90% 이상 채우지 않으면 건설은 없다. 건설보다 운송이 더 시급하기 때문.
            if len(constructions) > 0 and creep.room.energyAvailable >= creep.room.energyCapacityAvailable * .9:
                # for 1/3 chance going to phase 2.
                picker = random.randint(0, 2)
            else:
                picker = 0
            if not picker:
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
                # 핵에 에너지 넣는걸로 함?
                if Memory.rooms[creep.room.name].options.fill_nuke:
                    nuke_structure_add = all_structures.filter(lambda s: s.structureType == STRUCTURE_NUKER
                                                               and s.energy < s.energyCapacity)
                    structures.extend(nuke_structure_add)
                # 연구소에 에너지 넣는걸로 함?
                if Memory.rooms[creep.room.name].options.fill_labs:
                    structure_add = all_structures.filter(lambda s: s.structureType == STRUCTURE_LAB
                                                               and s.energy < s.energyCapacity)
                    structures.extend(structure_add)

                container = []
                # for_upgrade :스토리지가 컨트롤러에서 많이 떨어져 있을때 대비해 두는 컨테이너.
                if creep.room.controller.level < 8:
                    for rcont in creep.room.memory[STRUCTURE_CONTAINER]:
                        # 업글용 컨테이너고 수확저장용도가 아닌가? 그러면 허울러가 넣는다.
                        if rcont.for_upgrade and not rcont.for_harvest:
                            if Game.getObjectById(rcont.id) \
                                    and not _.sum(Game.getObjectById(rcont.id).store) \
                                    == Game.getObjectById(rcont.id).storeCapacity:
                                container.extend([Game.getObjectById(rcont.id)])

                structures.extend(container)
            else:
                structures = []

            if not picker and len(structures) > 0:
                creep.say('🔄물류,염려말라!', True)
                creep.memory.priority = 1

                # 여기서 스토리지를 목록에서 없앤다.
                # 스토리지는 항상 마지막에 채운다. 우선 있는지 확인부터 한거
                if creep.room.storage and \
                        creep.room.storage.store[RESOURCE_ENERGY] < max_energy_in_storage:
                    index = structures.indexOf(creep.room.storage)
                    structures.splice(index, 1)

            elif len(constructions) > 0:
                creep.say('🚧건설,염려말라!', True)
                creep.memory.priority = 2
            elif len(repairs) > 0:
                creep.say('☭ 세상을 고치자!', True)
                creep.memory.priority = 3
            else:
                creep.say('⚡ 위대한 발전!', True)
                creep.memory.priority = 4

        # priority 1: transfer
        if creep.memory.priority == 1:
            # if creep is assigned to store to storage - all resources must be stored
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
                    elif target.structureType == STRUCTURE_TOWER and target.energy >= target.energyCapacity - 20:
                        del creep.memory.haul_target
                    elif target.structureType != STRUCTURE_CONTAINER and target.energy >= target.energyCapacity:
                        del creep.memory.haul_target
                    elif _.sum(target.store) >= target.storeCapacity:
                        del creep.memory.haul_target

                # haul_target == 에너지 배송해야하는 목적지.
                if not creep.memory.haul_target and creep.carry.energy > 0:
                    if not passed_priority_0:
                        structures = all_structures.filter(lambda s: ((s.structureType == STRUCTURE_SPAWN
                                                                       or s.structureType == STRUCTURE_EXTENSION)
                                                                      and s.energy < s.energyCapacity)
                                                                     or (s.structureType == STRUCTURE_TOWER
                                                                         and s.energy < s.energyCapacity * 0.8))
                        # 핵을 넣는걸로 함?
                        if Memory.rooms[creep.room.name].options.fill_nuke:
                            nuke_structure_add = all_structures.filter(lambda s: s.structureType == STRUCTURE_NUKER
                                                                                 and s.energy < s.energyCapacity)
                            structures.extend(nuke_structure_add)
                        # 연구소 채우는걸로 함?
                        if Memory.rooms[creep.room.name].options.fill_labs:
                            structure_add = all_structures.filter(lambda s: s.structureType == STRUCTURE_LAB
                                                                            and s.energy < s.energyCapacity)
                            structures.extend(structure_add)

                        # 업그레이드용 컨테이너가 보일 경우.
                        # 만렙때 기능 끈다.
                        container = []
                        # for_upgrade :스토리지가 컨트롤러에서 많이 떨어져 있을때 대비해 두는 컨테이너.
                        if creep.room.controller.level < 8:
                            for rcont in creep.room.memory[STRUCTURE_CONTAINER]:
                                # 업글용 컨테이너고 수확저장용도가 아닌가? 그러면 허울러가 넣는다.
                                if rcont.for_upgrade and not rcont.for_harvest:
                                    if Game.getObjectById(rcont.id) \
                                        and not _.sum(Game.getObjectById(rcont.id).store) \
                                                == Game.getObjectById(rcont.id).storeCapacity:
                                        container.extend([Game.getObjectById(rcont.id)])
                        structures.extend(container)

                    portist_kripoj = _.filter(creeps, lambda c: c.memory.role == 'hauler')

                    # 목표타겟 확보.
                    haul_target = filter_haul_targets(creep, structures, portist_kripoj)
                    if haul_target == ERR_INVALID_TARGET:
                        del creep.memory.haul_target
                    else:
                        creep.memory.haul_target = haul_target

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
                    # 니가 가진것이 에너지느뇨
                    transfer_result = creep.transfer(Game.getObjectById(creep.memory.haul_target), RESOURCE_ENERGY)
                    # 멀리 떨어져 있으면 당연히 가서 붙는다...
                    if transfer_result == ERR_NOT_IN_RANGE:
                        if len(repairs) > 0:
                            repair = creep.pos.findClosestByRange(repairs)
                            creep.repair(repair)

                        # counter for checking the current location
                        if not creep.memory.move_ticks:
                            creep.memory.move_ticks = 1

                        # checking current location - only needed when check in par with move_ticks
                        if not creep.memory.cur_Location:
                            creep.memory.cur_Location = creep.pos
                        else:
                            # 만약 있으면 현재 크립위치와 대조해본다. 동일하면 move_ticks 에 1 추가 아니면 1로 초기화.

                            if JSON.stringify(creep.memory.cur_Location) \
                                    == JSON.stringify(creep.pos):
                                creep.memory.move_ticks += 1
                            else:
                                creep.memory.move_ticks = 1
                        # renew
                        creep.memory.cur_Location = creep.pos

                        # 5보다 더 올라갔다는건 앞에 뭔가에 걸렸다는 소리.
                        if creep.memory.move_ticks > 5:
                            for c in creeps:
                                if creep.pos.inRangeTo(c, 1) and not c.name == creep.name \
                                        and not c.id == creep.memory.last_switch:
                                    creep.say('GTFO', True)
                                    # 바꿔치기.
                                    mv = c.moveTo(creep)
                                    creep.moveTo(c)
                                    creep.memory.move_ticks = 1
                                    # 여럿이 겹쳤을때 마지막 움직였던애랑 계속 바꿔치기 안하게끔.
                                    creep.memory.last_switch = c.id
                                    return

                            # 여기까지 왔으면 틱이 5 넘겼는데 주변에 크립이 없는거임...
                            creep.memory.move_ticks = 1

                        # 해당사항 없으면 그냥 평소처럼 움직인다.
                        else:
                            # se nur moveTo, vi ne povas pasi se la kripo lokigis
                            movi(creep, creep.memory.haul_target, 0, 40, True)

                            if creep.memory.last_switch:
                                del creep.memory.last_switch
                    # if done, check if there's anything left. if there isn't then priority resets.
                    elif transfer_result == ERR_INVALID_TARGET:
                        del creep.memory.haul_target

                        # chk if there's something to build
                        if len(constructions) > 0:
                            creep.say('🚧 공사전환!', True)
                            creep.memory.priority = 2
                            creep.memory.move_ticks = 1
                            return

                        # 건설대상도 없을 경우 터미널 비었나 확인한다. 그리고 채움.
                        # 그후에 저장고가 있는지 확인한다. 있으면 넣는다.
                        # 방렙이 8인가? 아니면 발전에 간다.
                        # 그 다음은 50/50 확률로 저장 또는 수리를 한다.
                        # 단, 이때 운송크립 전원이 수리·발전중이면 무조건 저장고로 간다.

                        # 터미널이 있는가?
                        if creep.room.terminal:
                            # 터미널에 쌓인 에너지가 설정해둔 양 이하인가? 그러면 넣는다.
                            if creep.room.terminal.store[RESOURCE_ENERGY] <= terminal_capacity:
                                creep.say('경제활성화!', True)
                                creep.memory.haul_target = creep.room.terminal.id
                                creep.moveTo(Game.getObjectById(creep.memory.haul_target),
                                             {'visualizePathStyle': {'stroke': '#ffffff'}, 'ignoreCreeps': True,
                                              'reusePath': 40})
                                return

                        # 스토리지 존재.
                        if creep.room.storage:
                            # 스토리지에 할당량 만큼의 에너지가 있는가? 없으면 가즈아.
                            if creep.room.storage.store[RESOURCE_ENERGY] < max_energy_in_storage:
                                creep.say('📦 저장합시다', True)
                                creep.memory.to_storage = True
                                move_it = creep.moveTo(creep.room.storage,
                                                       {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 20})
                                creep.memory.move_ticks = 1
                                return
                        # 여기까지 왔다는건 수리·발전밖에 없단 소리임.
                        # 방 레벨이 8 이하인가? 그럼 발전에 보탠다.
                        if creep.room.controller.level != 8:
                            creep.say('발전으로!', True)
                            creep.memory.move_ticks = 1
                            creep.memory.priority = 4
                            return

                        # 여기까지 오면 이제 진짜 수리뿐인데... 무조건, 무조건!! 운송크립 하나는 운송에만 전념해야 한다.

                        # 크립중에 공사·운송을 하는 애가 남아있는가?
                        leftover_haulers = creeps.filter(lambda c: c.memory.role == 'hauler' \
                                                           and c.name != creep.name
                                                           and (c.memory.priority == 1 or c.memory.priority == 2))
                        # 있으면 수리 가즈아, 다만 이건 렙 8때만 적용된다.
                        if leftover_haulers and creep.room.controller.level == 8:
                            creep.say('✊단결투쟁!', True)
                            creep.memory.priority = 3
                            creep.memory.move_ticks = 1
                            return
                        # 없으면 laboro = 0 초기화
                        else:
                            creep.say('끝일수록 처음처럼!', True)
                            creep.memory.laboro = 0
                            creep.memory.move_ticks = 1
                            del creep.memory.haul_target
                            del creep.memory.to_storage
                            return

                    elif transfer_result == 0 or transfer_result == ERR_FULL:
                        # creep.say('done!')
                        creep.memory.move_ticks = 1
                        # 다 끝나면 바로 다음 목적지로 보내야한다.
                        end_structures = all_structures.filter(lambda s: ((s.structureType == STRUCTURE_SPAWN
                                                                       or s.structureType == STRUCTURE_EXTENSION)
                                                                      and s.energy < s.energyCapacity)
                                                                     or (s.structureType == STRUCTURE_TOWER
                                                                         and s.energy < s.energyCapacity * 0.8))
                        # 핵을 넣는걸로 함?
                        if Memory.rooms[creep.room.name].options.fill_nuke:
                            nuke_structure_add = all_structures.filter(lambda s: s.structureType == STRUCTURE_NUKER
                                                                                 and s.energy < s.energyCapacity)
                            end_structures.extend(nuke_structure_add)
                        # 연구소를 채우는걸로 함?
                        if Memory.rooms[creep.room.name].options.fill_labs:
                            structure_add = all_structures.filter(lambda s: s.structureType == STRUCTURE_LAB
                                                                            and s.energy < s.energyCapacity)
                            end_structures.extend(structure_add)
                        for s in end_structures:
                            if s.id == creep.memory.haul_target:
                                s_index = end_structures.indexOf(s)
                                end_structures.splice(s_index, 1)
                                break
                        del creep.memory.haul_target
                        # print(creep.name, 'end_structures', end_structures)
                        # print(len(end_structures))
                        if len(end_structures) == 0:
                            target = ERR_INVALID_TARGET
                        else:
                            target = filter_haul_targets(creep, end_structures, creeps)
                        # creep.say('a', target)
                        if target == ERR_INVALID_TARGET:
                            return
                        else:
                            creep.memory.haul_target = target
                            if not creep.pos.isNearTo(target):
                                movi(creep, creep.memory.haul_target, 0, 40, True)

                    else:
                        creep.say(transfer_result)
                        creep.memory.move_ticks = 1
                        del creep.memory.haul_target

        # priority 2: build
        elif creep.memory.priority == 2:

            if creep.memory.build_target and not Game.getObjectById(creep.memory.build_target):
                del creep.memory.build_target

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

            elif build_result == ERR_NO_BODYPART:
                creep.say('운송이 본분!', True)
                creep.memory.priority = 1
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

            elif repair_result == ERR_NO_BODYPART:
                creep.say('운송이 본분!', True)
                creep.memory.priority = 1
                return

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

            elif upgrade_result == ERR_NO_BODYPART:
                creep.say('운송이 본분!', True)
                creep.memory.priority = 1
                return

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


def filter_haul_targets(creep, ujoj, haulers):
    """
    위에 허울러가 에너지 채울 컨테이너 등을 선택하는 함수.
    :param creep:
    :param ujoj: 에너지 채울 대상.
    :param haulers: 허울러라 써있지만 실질적으로는 모든 크립.
    :return: creep.memory.haul_target 에 들어갈 아이디.
    """
    # print(creep.name, 'len(ujoj)[filter_haul_targets]', len(ujoj), ujoj)
    if len(ujoj) == 0:
        return ERR_INVALID_TARGET

    # 애초에 이게 있으면 여기오면 안되지만...
    if creep.memory.haul_target:
        return creep.memory.haul_target

    # 목표를 찾았는지 확인용도
    found = 0

    # 목표 컨테이너 초기화 용도.
    target = None

    while not found or len(ujoj) > 0:
        # size_counter is used to determines the number of creeps that can be added to the haul_target.
        size_counter = 0

        # if theres no structures to haul to, then no reason to do this loop
        if len(ujoj) == 0:
            break

        # 가장 가까운 건물.
        structure = creep.pos.findClosestByRange(ujoj)

        for kripo in haulers:
            # 크립이름이 똑같거나 운송표적이 없으면 건너뛴다. 볼필요없음.
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
                    # aŭ estas nesto aŭ lab
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
            target = structure.id
            found = 1
            break

        else:
            index = ujoj.indexOf(structure)
            ujoj.splice(index, 1)

    if found:
        return target
    else:
        return ERR_INVALID_TARGET


# noinspection PyPep8Naming
def grab_haul_list(roomName, totalStructures):
    """
    위에 허울러가 에너지를 채울 목록 확인.
    :param roomName: 방이름.
    :param totalStructures: 본문 all_structures 와 동일
    :param get_storage: 스토리지를 포함할 것인가? priority == 0 인 상황 아니면 포함할일이 없음.
    :return: 허울러의 에너지 채울 대상목록
    """
    # defining structures to fill the energy on. originally above of this spot but replaced for cpu eff.
    # towers only fills 80% since it's gonna repair here and there all the time.
    structures = totalStructures.filter(lambda s: ((s.structureType == STRUCTURE_SPAWN
                                                   or s.structureType == STRUCTURE_EXTENSION)
                                                  and s.energy < s.energyCapacity)
                                                 or (s.structureType == STRUCTURE_TOWER
                                                     and s.energy < s.energyCapacity * 0.8)
                                                 or (s.structureType == STRUCTURE_STORAGE
                                                     and s.store[RESOURCE_ENERGY] < 800000)
                                                 or (s.structureType == STRUCTURE_TERMINAL
                                                     and s.store[RESOURCE_ENERGY] < 10000))
    # 핵에 에너지 넣는걸로 함?
    if Memory.rooms[roomName].options.fill_nuke:
        nuke_structure_add = totalStructures.filter(lambda s: s.structureType == STRUCTURE_NUKER
                                                             and s.energy < s.energyCapacity)
        structures.extend(nuke_structure_add)
    # 연구소에 에너지 넣는걸로 함?
    if Memory.rooms[roomName].options.fill_labs:
        structure_add = totalStructures.filter(lambda s: s.structureType == STRUCTURE_LAB
                                                        and s.energy < s.energyCapacity)
        structures.extend(structure_add)

    container = []
    # for_upgrade :스토리지가 컨트롤러에서 많이 떨어져 있을때 대비해 두는 컨테이너.
    if Game.rooms[roomName].controller.level < 8:
        for rcont in Game.rooms[roomName].memory[STRUCTURE_CONTAINER]:
            # 업글용 컨테이너고 수확저장용도가 아닌가? 그러면 허울러가 넣는다.
            if rcont.for_upgrade and not rcont.for_harvest \
                    and not _.sum(Game.getObjectById(rcont.id).store) == Game.getObjectById(rcont.id).storeCapacity:
                container.append(Game.getObjectById(rcont.id))

    structures.extend(container)

    return structures
