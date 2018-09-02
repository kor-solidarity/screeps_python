from defs import *
from movement import *
import harvest_stuff
import random
from miscellaneous import *
from _custom_constants import *

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
    structures = []

    # 스토리지 내 에너지값. 사실 저 엘스문 걸릴경우는 허울러가 실수로 다른방 넘어갔을 뿐....
    if creep.room.memory.options and creep.room.memory.options[max_energy]:
        max_energy_in_storage = creep.room.memory.options[max_energy]
    else:
        max_energy_in_storage = 600000

    # priority 0 통과했는가? 통과했으면 priority 1 쓸때 스트럭쳐 필터 안해도됨.
    passed_priority_0 = False

    # 혹시 딴짓하다 옆방으로 새는거에 대한 대비
    if not creep.memory.upgrade_target:
        creep.memory.upgrade_target = Game.rooms[creep.memory.assigned_room].controller['id']

    end_is_near = 10
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
    if _.sum(creep.carry) == 0 and not creep.memory.laboro == 0:
        creep.memory.laboro = 0
        creep.say('🚛운송투쟁!', True)
        del creep.memory.to_storage
        del creep.memory.haul_target
        del creep.memory.build_target
        del creep.memory.repair_target
        del creep.memory.last_swap

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
        del creep.memory.last_swap

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
                    # if not energy and there's no storage, 스토리지 못넣어서 엉킴 통과.
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
            if creep.memory.pickup and not Game.getObjectById(creep.memory.pickup):
                del creep.memory.pickup
            # only search if there's nothing to pick up.
            if not creep.memory.pickup:
                # 방 안에 에너지수용량이 총량의 30% 이하면 반반 확률로 스토리지로 직접 빼러 간다.
                # 물론 안에 에너지가 있어야겠지.
                if creep.room.energyAvailable <= creep.room.energyCapacityAvailable * .30 \
                        and creep.room.storage and creep.room.storage.store[RESOURCE_ENERGY] > 600:
                    to_storage_chance = random.randint(0, 1)
                else:
                    to_storage_chance = 0

                if not to_storage_chance:
                    # find any containers/links with any resources inside
                    storages = all_structures.filter(lambda s:
                                                     (s.structureType == STRUCTURE_CONTAINER
                                                      and _.sum(s.store) >= creep.carryCapacity * .5)
                                                     or (s.structureType == STRUCTURE_LINK
                                                         and s.energy >= creep.carryCapacity * .5))
                else:
                    if creep.room.storage and \
                            creep.room.storage.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5:
                        storages = [creep.room.storage]
                    else:
                        storages = []

                # 위 목록 중에서 가장 가까이 있는 컨테이너를 뽑아간다.
                # 만약 뽑아갈 대상이 없을 시 터미널, 스토리지를 각각 찾는다.
                # 만일 연구소를 안채우기로 했으면 거기서도 뽑는다.
                if Memory.rooms[creep.room.name].options.fill_labs == 0:
                    # print('no nuke')
                    labs = all_structures \
                        .filter(lambda s: s.structureType == STRUCTURE_LAB and s.energy >= creep.carryCapacity * .5)
                    storages.extend(labs)

                pickup_id = pick_pickup(creep, creeps, storages, terminal_capacity)
                # print('pickupId', pickup_id)
                if pickup_id == ERR_INVALID_TARGET:
                    pass
                else:
                    creep.memory.pickup = pickup_id

            # if creep already have pickup memory, no need to search for storage.
            else:
                storage = 0

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
                    # 현재 위치한 곳이 이전 틱에도 있던곳인지 확인하고 옮기는 등의 절차.
                    swap_check = check_loc_and_swap_if_needed(creep, creeps, True)

                    # 아무 문제 없으면 평소마냥 움직이는거.
                    if swap_check == OK:
                        movi(creep, creep.memory.pickup, 0, 40, True)
                    # 확인용. 아직 어찌할지 못정함....
                    elif swap_check == ERR_NO_PATH:
                        creep.say('ERR_NO_PATH')
                    # 위 둘 외에 다른게 넘어왔다는 소리는 실질적으로 어느 위치를 갔다는게 아니라
                    # 다른 크립와 위치 바꿔치기를 시전했다는 소리. 메모리 옮긴다.
                    else:
                        creep.memory.last_swap = swap_check
                # 근데 이거 절대 뜰일없음...
                elif result == ERR_NO_PATH:
                    # 모듈화한걸로 대체시도
                    swapping(creep, creeps)
                # 온전하게 집었을 경우.
                # 여러 자원을 뽑아야 하는 경우도 있는지라 이거 한번에 laboro 를 1로 전환하지 않는다.
                elif result == 0:
                    creep.say('BEEP BEEP⛟', True)

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
            get_to_da_room(creep, creep.memory.assigned_room, False)
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
                structures = grab_haul_list(creep.room.name, all_structures, True)
                # 위에 함수로 대체
                # structures = all_structures.filter(lambda s: ((s.structureType == STRUCTURE_SPAWN
                #                                                or s.structureType == STRUCTURE_EXTENSION)
                #                                               and s.energy < s.energyCapacity)
                #                                              or (s.structureType == STRUCTURE_TOWER
                #                                                  and s.energy < s.energyCapacity * 0.8)
                #                                              or (s.structureType == STRUCTURE_STORAGE
                #                                                  and s.store[RESOURCE_ENERGY] < max_energy_in_storage)
                #                                              or (s.structureType == STRUCTURE_TERMINAL
                #                                                  and s.store[RESOURCE_ENERGY] < terminal_capacity))
                # # 핵에 에너지 넣는걸로 함?
                # if Memory.rooms[creep.room.name].options.fill_nuke:
                #     nuke_structure_add = all_structures.filter(lambda s: s.structureType == STRUCTURE_NUKER
                #                                                and s.energy < s.energyCapacity)
                #     structures.extend(nuke_structure_add)
                # # 연구소에 에너지 넣는걸로 함?
                # if Memory.rooms[creep.room.name].options.fill_labs:
                #     structure_add = all_structures.filter(lambda s: s.structureType == STRUCTURE_LAB
                #                                                and s.energy < s.energyCapacity)
                #     structures.extend(structure_add)
                #
                # container = []
                # # for_upgrade :스토리지가 컨트롤러에서 많이 떨어져 있을때 대비해 두는 컨테이너.
                # if creep.room.controller.level < 8:
                #     for rcont in creep.room.memory[STRUCTURE_CONTAINER]:
                #         # 업글용 컨테이너고 수확저장용도가 아닌가? 그러면 허울러가 넣는다.
                #         if rcont.for_upgrade and not rcont.for_harvest:
                #             if Game.getObjectById(rcont.id) \
                #                     and not _.sum(Game.getObjectById(rcont.id).store) \
                #                     == Game.getObjectById(rcont.id).storeCapacity:
                #                 container.extend([Game.getObjectById(rcont.id)])
                #
                # structures.extend(container)
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
            elif len(repairs) > 0 and creep.room.controller.level > 1:
                creep.say('☭ 세상을 고치자!', True)
                creep.memory.priority = 3
            else:
                creep.say('⚡ 위대한 발전!', True)
                creep.memory.priority = 4

        # priority 1: transfer
        if creep.memory.priority == 1:
            # todo 모든걸 다 건드려야 함....
            # 1. 우선 모든 운송은 다 크립 쌩깐다!
            # 2. 스토리지용 운송 없앤다.
            # 3. 터미널 이송 등 재설정.

            """
            절차는 다음과 같다. 
            1. haul_target이 있는지 확인한다. 없으면 다음으로 넘어간다. 여기까진 동일. 
            2. 만일 에너지가 다 떨어졌는데 안에 뭔가가 있을 경우. - 방에서 생산하는거면 터미널로. haul_target 을 그걸로 지정한다. 
            3. 터미널대상이 아니면 스토리지로 가야겠지? haul_target를 스토리지로 하고 이때 전부 꼴아박는걸로 하면 되잖음.

            """
            # 단순 초기화 용도.
            transfer_minerals_result = -100
            haul_target_filtered = 0

            # 근처에 컨트롤러랑 리페어 대상 있으면 건들면서 간다.
            repair_on_the_way(creep, repairs)

            # check if haul_target's capacity is full
            target = Game.getObjectById(creep.memory.haul_target)
            # haul_target 이 중간에 폭파되거나 이미 꽉 찼을 시...
            if not target \
                or (target.structureType == STRUCTURE_TOWER and target.energy >= target.energyCapacity - 20) \
                or (target.structureType != STRUCTURE_CONTAINER and target.energy >= target.energyCapacity) \
                or _.sum(target.store) >= target.storeCapacity:
                del creep.memory.haul_target
            # 에너지 외 자원 운송중인데 대상이 에너지 채우는거면 통과한다.
            if target and \
                    (target.structureType == STRUCTURE_EXTENSION
                     or target.structureType == STRUCTURE_TOWER
                     or target.structureType == STRUCTURE_NUKER
                     or target.structureType == STRUCTURE_SPAWN) \
                    and creep.carry[RESOURCE_ENERGY] == 0:
                del creep.memory.haul_target

            if not creep.memory.haul_target:
                # 위에 priority 0 거치지 않았으면 여기 지금 텅 비었음.
                if not len(structures):
                    # 크립 허울대상 확인
                    structures = grab_haul_list(creep.room.name, all_structures)
                # 이 경우 기준점: 크립이 에너지를 가지고 있는가?
                if creep.carry[RESOURCE_ENERGY] > 0:
                    # 목표타겟 확보.
                    haul_target_filtered = filter_haul_targets(creep, structures, creeps)
                    if haul_target_filtered == ERR_INVALID_TARGET:
                        del creep.memory.haul_target
                    else:
                        creep.memory.haul_target = haul_target_filtered
                # 에너지가 아니면 다른걸 저 기준에 맞지 않으므로 새로 찾아야함.
                if not creep.carry[RESOURCE_ENERGY] > 0 or haul_target_filtered == ERR_INVALID_TARGET:
                    minerals = creep.room.find(FIND_MINERALS)
                    # 터미널이 존재하고 크립이 가지고 있는 템이 방에서 나오는 자원일 경우 터미널에 넣는다.
                    if creep.room.terminal and creep.carry[minerals[0].mineralType] > 0:
                        # creep.memory.
                        creep.memory.haul_target = creep.room.terminal.id
                    # 그외는 싹 스토리지로. 여럿이 붙으면? 알게뭐야.
                    else:
                        if len(constructions) > 0:
                            creep.say('🚧 공사전환!', True)
                            creep.memory.priority = 2
                        elif creep.room.storage:
                            creep.say('📦 저장합시다', True)
                            creep.memory.haul_target = creep.room.storage.id
                        # 스토리지가 없으면?
            # 이 시점까지 타겟이 없다면 스토리지고 뭐고 넣을 수 있는 공간이 전혀 없다는거.
            if not creep.memory.haul_target:
                if len(constructions) > 0:
                    creep.say('🚧 공사전환!', True)
                    creep.memory.priority = 2
                elif len(repairs) > 0 and creep.room.controller.level > 4:
                    creep.say('✊단결투쟁!', True)
                    creep.memory.priority = 3
                else:
                    creep.say('⚡ 발전에총력!', True)
                    creep.memory.priority = 4

            # haul_target 있으면 우선 거기로 간다.
            if creep.memory.haul_target:
                target = Game.getObjectById(creep.memory.haul_target)
                # if creep.name == 'Dominic':
                #     print('creep.pos.isNearTo(target)', creep.pos.isNearTo(target))
                # 당장 넣을 수 있는 상황이 아니면 간다.
                if not creep.pos.isNearTo(target):
                    # 먼져 위치확인.
                    swap_check = check_loc_and_swap_if_needed(creep, creeps, True)
                    if swap_check == OK:
                        movi(creep, creep.memory.haul_target, 0, 40, True)
                    elif swap_check == ERR_NO_PATH:
                        creep.say('noPathWTF')
                        # pass
                    else:
                        creep.memory.last_swap = swap_check
                # 바로 옆이면 시작.
                else:
                    # 에너지만 들어가는것인가?
                    if target.structureType == STRUCTURE_EXTENSION \
                            or target.structureType == STRUCTURE_TOWER \
                            or target.structureType == STRUCTURE_NUKER \
                            or target.structureType == STRUCTURE_SPAWN:
                        only_energy = True
                    else:
                        only_energy = False

                    # 이제 넣는다. 어차피 에너지를 옮기는게 가장 중요하기 때문에 그외에 뭐가 어디로 들어가는진 알바아님...
                    if only_energy:
                        transfer_minerals_result = creep.transfer(target, RESOURCE_ENERGY)
                    else:
                        for minerals in Object.keys(creep.carry):
                            transfer_minerals_result = creep.transfer(target, minerals)
                            if transfer_minerals_result == 0:
                                break
                            elif transfer_minerals_result == ERR_FULL:
                                creep.memory.pickup = creep.room.terminal.id
                    # 에너지만 넣은 상태면 바로 다음으로 넘어간다.
                    if only_energy and (transfer_minerals_result == OK or transfer_minerals_result == ERR_FULL):
                        # print(creep, 'transfer_minerals_result', transfer_minerals_result)
                        # 크립 허울대상 확인
                        structures = grab_haul_list(creep.room.name, all_structures)
                        for s in structures:
                            if s.id == creep.memory.haul_target:
                                s_index = structures.indexOf(s)
                                structures.splice(s_index, 1)
                                break
                        del creep.memory.haul_target
                        if len(structures):
                            # 목표타겟 확보.
                            haul_target = filter_haul_targets(creep, structures, creeps)
                            if haul_target == ERR_INVALID_TARGET:
                                del creep.memory.haul_target
                            else:
                                creep.memory.haul_target = haul_target
                        # 스트럭쳐가 텅 비었다는건 즉 채울건 다 채웠다는 소리. 스토리지로 보낸다.
                        else:
                            if creep.room.storage:
                                creep.say('📦 저장합시다', True)
                                creep.memory.haul_target = creep.room.storage.id
                    else:
                        pass

            # 이 시점에 haul_target 이 있으면 거기로 간다.
            if creep.memory.haul_target and not transfer_minerals_result == -100:
                target = Game.getObjectById(creep.memory.haul_target)
                move = movi(creep, creep.memory.haul_target, 0, 40, True)

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
                if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.build_target), 6):
                    # 현재 위치한 곳이 이전 틱에도 있던곳인지 확인하고 옮기는 등의 절차.
                    swap_check = check_loc_and_swap_if_needed(creep, creeps, True)
                    # creep.say('swap {}'.format(swap_check))
                    # 아무 문제 없으면 평소마냥 움직이는거.
                    if swap_check == OK:
                        movi(creep, creep.memory.build_target, 6, 40, True)
                    # 확인용. 아직 어찌할지 못정함....
                    elif swap_check == ERR_NO_PATH:
                        creep.say('ERR_NO_PATH')
                    # 위 둘 외에 다른게 넘어왔다는 소리는 실질적으로 어느 위치를 갔다는게 아니라
                    # 다른 크립와 위치 바꿔치기를 시전했다는 소리. 메모리 옮긴다.
                    else:
                        creep.memory.last_swap = swap_check
                else:
                    build_result = movi(creep, creep.memory.build_target, 3, 5)
                    creep.say('build {}'.format(build_result), True)

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
                del creep.memory.last_swap
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
                if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.repair_target), 6):
                    # 현재 위치한 곳이 이전 틱에도 있던곳인지 확인하고 옮기는 등의 절차.
                    swap_check = check_loc_and_swap_if_needed(creep, creeps, True)
                    # 아무 문제 없으면 평소마냥 움직이는거.
                    if swap_check == OK:
                        movi(creep, creep.memory.repair_target, 3, 40, True)
                    # 확인용. 아직 어찌할지 못정함....
                    elif swap_check == ERR_NO_PATH:
                        creep.say('ERR_NO_PATH')
                    # 위 둘 외에 다른게 넘어왔다는 소리는 실질적으로 어느 위치를 갔다는게 아니라
                    # 다른 크립와 위치 바꿔치기를 시전했다는 소리. 메모리 옮긴다.
                    else:
                        creep.memory.last_swap = swap_check
                else:
                    creep.moveTo(Game.getObjectById(creep.memory.repair_target)
                                 , {'visualizePathStyle': {'stroke': '#ffffff'}, 'range': 3, 'reusePath': 10})
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
                if not creep.pos.inRangeTo(Game.getObjectById(creep.memory.upgrade_target), 6):
                    # 현재 위치한 곳이 이전 틱에도 있던곳인지 확인하고 옮기는 등의 절차.
                    swap_check = check_loc_and_swap_if_needed(creep, creeps, True)
                    # 아무 문제 없으면 평소마냥 움직이는거.
                    if swap_check == OK:
                        movi(creep, creep.memory.upgrade_target, 3, 40, True)
                    # 확인용. 아직 어찌할지 못정함....
                    elif swap_check == ERR_NO_PATH:
                        creep.say('ERR_NO_PATH')
                    # 위 둘 외에 다른게 넘어왔다는 소리는 실질적으로 어느 위치를 갔다는게 아니라
                    # 다른 크립와 위치 바꿔치기를 시전했다는 소리. 메모리 옮긴다.
                    else:
                        creep.memory.last_swap = swap_check
                else:
                    movi(creep, creep.memory.upgrade_target, 3, 10)

            elif upgrade_result == ERR_NO_BODYPART:
                creep.say('운송이 본분!', True)
                creep.memory.priority = 1
                return

            # if having anything other than energy when not on priority 1 switch to 1
            # 운송크립은 발전에 심혈을 기울이면 안됨.
            if (creep.carry[RESOURCE_ENERGY] <= 0 or _.sum(creep.carry) <= creep.carryCapacity * outer_work_perc) \
                    and creep.room.controller.level > 4:
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

    :param creep: 크립(..)
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
def grab_haul_list(roomName, totalStructures, add_storage=False):
    """
    위에 허울러가 에너지를 채울 목록 확인.

    :param roomName: 방이름.
    :param totalStructures: 본문 all_structures 와 동일
    :param add_storage: 스토리지를 포함할 것인가? priority == 0 인 상황 아니면 포함할일이 없음.
    :return: 허울러의 에너지 채울 대상목록
    """
    # 초기화
    structures = []

    # defining structures to fill the energy on. originally above of this spot but replaced for cpu eff.
    # towers only fills 80% since it's gonna repair here and there all the time.
    structures = totalStructures.filter(lambda s: ((s.structureType == STRUCTURE_SPAWN
                                                    or s.structureType == STRUCTURE_EXTENSION)
                                                   and s.energy < s.energyCapacity)
                                                  or (s.structureType == STRUCTURE_TOWER
                                                      and s.energy < s.energyCapacity * 0.8)
                                                  or (s.structureType == STRUCTURE_TERMINAL
                                                      and s.store[RESOURCE_ENERGY] < 10000))

    if add_storage:
        structures.extend(totalStructures.filter
                          (lambda s: s.structureType == STRUCTURE_STORAGE
                                     and s.store[RESOURCE_ENERGY] < Game.rooms[roomName].memory.options[max_energy]))
        # print('if add_storage', structures)
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
            # 업글용 컨테이너고 수확저장용도가 아닌가? 그러면 허울러가 넣는다. 80% 이하로 차있을때만.
            if rcont.for_upgrade and not rcont.for_harvest \
                    and _.sum(Game.getObjectById(rcont.id).store) < Game.getObjectById(rcont.id).storeCapacity * .8:
                container.append(Game.getObjectById(rcont.id))

    structures.extend(container)

    return structures
