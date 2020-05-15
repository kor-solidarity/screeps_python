from defs import *
import movement
from harvest_stuff import *
import random
import miscellaneous
from _custom_constants import *
from debug import *

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
    this guy's job: carrying energy from containers. repairing stuff on the way.
    and when all those are done it's gonna construct. repairing stuff on the way.
    when all those are done it's gonna repair stuff around.
    and when that's all done they're going for upgrade.

    :param creep:
    :param all_structures: creep.room.find(FIND_STRUCTURES)
    :param constructions: creep.room.find(FIND_CONSTRUCTION_SITES)
    :param creeps: creep.room.find(FIND_MY_CREEPS)
    :param dropped_all: creep.room.find(FIND_DROPPED_RESOURCES) + creep.room.find(FIND_TOMBSTONES)
    :param repairs: look at main.
    :param terminal_capacity: 방 안의 터미널 내 에너지 최소값.
    :return:
    """

    # IMPORTANT: when hauler does a certain work, they must finish them before doing anything else!

    """
    haul_target == 운송 목적지.
    repair_target == 수리 목표.
    upgrade_target == 업그레이드 목표
    build_target == 건설 목표
    dropped_all == 근처에 떨어져있는 리소스
    pickup == 에너지 빼갈 대상.
    """

    # 운송업 외 다른일은 지극히 제한적으로만 써야한다. 운송 외 일할때 가지고 있으면서 일할 수 있는 최소량...?? 설명이 안되네
    # 주의! 1 == 100%
    outer_work_perc = .7

    structures = []
    path = []
    # debug = False
    hauler_path_color = 'floralWhite'

    # 초기화
    if not creep.memory.size:
        creep.memory.size = 1

    # NULLIFIED - max_energy_in_storage 는 더이상 쓰이지 않는다.
    # 스토리지 내 허용되는 최대 수용 에너지값. == 스토리지 전체량에서 에너지 아닌걸 제외한 값에서 max_energy를 뺀 값
    # 사실 저 엘스문 걸릴경우는 허울러가 실수로 다른방 넘어갔을 뿐....
    # if creep.room.memory.options and creep.room.memory.options[max_energy] and creep.room.storage:
    #     max_energy_in_storage = \
    #         creep.room.storage.storeCapacity \
    #         - (_.sum(creep.room.storage.store) - creep.room.storage.store[RESOURCE_ENERGY]) \
    #         - creep.room.memory.options[max_energy]
    # else:
    #     max_energy_in_storage = 600000

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
            if not creep.pos.isNearTo(creep.room.storage):
                transfer_minerals_result = ERR_NOT_IN_RANGE
            else:
                transfer_minerals_result = creep.transfer(creep.room.storage, minerals)
            if transfer_minerals_result == ERR_NOT_IN_RANGE:
                creep.moveTo(creep.room.storage, {'visualizePathStyle': {'stroke': '#ffffff'}})
                break
            elif transfer_minerals_result == 0:
                break
            else:
                print('endNearSomething', creep.name, transfer_minerals_result)
                creep.say('END?? {}'.format(transfer_minerals_result))
        return
    elif creep.ticksToLive < end_is_near and creep.room.storage:
        creep.suicide()
        return

    # if there's nothing to carry then get to harvesting.
    # being not zero also includes being None lol
    if _.sum(creep.carry) == 0 and not creep.memory.laboro == 0:
        creep.say('🚛운송투쟁!', True)
        init_memory(creep, 0)

    elif creep.memory.laboro == 0 and \
            ((_.sum(creep.carry) >= creep.carryCapacity * .5
              and creep.memory.laboro == 0 and not creep.memory.dropped)
             or _.sum(creep.carry) == creep.carryCapacity):

        init_memory(creep, 1)

    if creep.memory.debug:
        if creep.memory.path:
            debugging_path(creep, 'path', 'white', 'dashed')

    # laboro: 0 == pickup something.
    if creep.memory.laboro == 0:
        # 1. look for dropped_all resources and get them
        # 2. if 1 == False, look for storage|containers to get the energy from.
        # 3. if 2 == False, you harvest on ur own.

        # 떨군게 존재하는가?
        if creep.memory.dropped and not Game.getObjectById(creep.memory.dropped):
            del creep.memory.dropped
        # 떨군게 무덤이고 내용물이 있는가?
        elif creep.memory.dropped and Game.getObjectById(creep.memory.dropped) \
                and Game.getObjectById(creep.memory.dropped).deathTime \
                and not Game.getObjectById(creep.memory.dropped).store.getUsedCapacity():
            creep.say('무덤버려')
            del creep.memory.dropped

        # 소속된 방에 스토어가 없으면 에너지만 줍는다
        energy_only = False
        if not Game.rooms[creep.memory.assigned_room].storage:
            energy_only = True

        # if there's no dropped_all but there's dropped_all
        if not creep.memory.dropped and len(dropped_all) > 0:
            # 떨어진거 확인 범위.
            drop_range = 5
            # 모든게 꽉 찬 상황이면 정리
            if creep.memory.all_full:
                drop_range = 50

            dropped_target = filter_drops(creep, dropped_all, drop_range, energy_only)

        # if there is a dropped_all target and it's there.
        if creep.memory.dropped:
            # 에너지 외 다른게 있을수도 있어서.
            if pick_drops_act(creep, energy_only) == 0:
                return

        if creep.memory.all_full:
            del creep.memory.all_full

        # 여기까지 떨군게 없으면 일반 컨테이너로.
        if not creep.memory.dropped:
            if creep.memory.pickup and not Game.getObjectById(creep.memory.pickup):
                del creep.memory.pickup
            # only search if there's nothing to pick up.
            if not creep.memory.pickup:
                # 방 안에 에너지수용량이 총량의 30% 이하면 픽업대상에 스토리지도 포함한다.
                # 단, 저렙일 시 50% 까지.
                # 물론 안에 에너지가 있어야겠지.
                # todo 미네랄 옮기는것도 해야함.
                if ((creep.room.controller.level < 6
                     and creep.room.energyAvailable <= creep.room.energyCapacityAvailable * .5)
                    or
                    (creep.room.energyAvailable <= creep.room.energyCapacityAvailable * .3)) \
                        and creep.room.storage and creep.room.storage.store.getCapacity(RESOURCE_ENERGY):
                    to_storage_chance = 1
                else:
                    to_storage_chance = 0

                storages = []
                # find any containers/links with any resources inside
                for c in creep.room.memory[STRUCTURE_CONTAINER]:
                    # 업글용이 아닌거 걸러낸다. 만렙일때만.
                    # 만약 스토리지가 없는 상황이고 건설가능한 렙이면 업글용도 뽑아간다. 스토리지 확보가 최우선
                    if not Game.getObjectById(creep.memory.upgrade_target).level == 8:
                        if Game.getObjectById(creep.memory.upgrade_target).level > 3 \
                                and not Game.getObjectById(creep.memory.upgrade_target).room.storage:
                            pass
                        elif c[for_upgrade]:
                            continue
                    container = Game.getObjectById(c.id)
                    if container and _.sum(container.store) >= creep.carryCapacity * .5:
                        storages.append(container)

                for l in creep.room.memory[STRUCTURE_LINK]:
                    # 업글용 링크는 무시
                    if not Game.getObjectById(creep.memory.upgrade_target).level == 8:
                        if l[for_upgrade]:
                            continue
                    # 저장용 링크가 아니면 역시 무시
                    if not l[for_store]:
                        continue
                    link = Game.getObjectById(l.id)
                    if link and link.energy >= creep.carryCapacity * .5:
                        storages.append(link)

                if to_storage_chance:
                    storages.append(creep.room.storage)

                # 위 목록 중에서 가장 가까이 있는 컨테이너를 뽑아간다.
                # 만약 뽑아갈 대상이 없을 시 터미널, 스토리지를 각각 찾는다.
                # 만일 연구소를 안채우기로 했으면 거기서도 뽑는다.
                if Memory.rooms[creep.room.name].options and Memory.rooms[creep.room.name].options.fill_labs == 0:
                    labs = all_structures \
                        .filter(lambda s: s.structureType == STRUCTURE_LAB and s.energy >= creep.carryCapacity * .5)
                    storages.extend(labs)
                    # todo 터미널의 경우 얼마나 뽑을 수 있는지 명확하게 해야할 것.
                pickup_id = miscellaneous.pick_pickup(creep, creeps, storages, terminal_capacity)

                # 뽑아갈 게 없는 경우
                if pickup_id == ERR_INVALID_TARGET:
                    # 우선 허울러가 채워야할 대상이 있긴 한지부터 확인해보자.
                    # 건설장 있나?
                    if len(constructions):
                        pass
                    # 에너지가 꽉찬건지 확인
                    elif Game.getObjectById(creep.memory.upgrade_target).room.energyAvailable == \
                            Game.getObjectById(creep.memory.upgrade_target).room.energyCapacityAvailable:
                        # 전부 차있음?
                        _full = True
                        # 아래 조건문에 하나라도 걸리면 굳이 채울 필요가 없는거.
                        # 타워중에 덜 찬게 있나 확인
                        if creep.room.memory[STRUCTURE_TOWER]:
                            for t in creep.room.memory[STRUCTURE_TOWER]:
                                # print('Game.getObjectById({}).energy {}'.format(t, Game.getObjectById(t).energy))
                                if Game.getObjectById(t).store.getUsedCapacity() \
                                        < Game.getObjectById(t).store.getCapacity() * .8:
                                    print('tower not full')
                                    _full = False
                                    break
                        # 업글러용 컨테이너가 있는지, 그리고 이게 2/3 이상 채워진건지 확인
                        if _full and creep.room.memory[STRUCTURE_CONTAINER] and not creep.room.controller.level == 8:
                            for c in creep.room.memory[STRUCTURE_CONTAINER]:
                                target = Game.getObjectById(c.id)
                                # 2/3 이상 채워져 있으면 끝.
                                if c.for_store and target.store.getUsedCapacity() < target.store.getCapacity() * 2/3:
                                    print('upgrader container not full')
                                    _full = False
                                    break
                        # 핵 채우기
                        if creep.room.memory.options and creep.room.memory.options.fill_nuke:
                            nuker = all_structures.filter(lambda s: s.structureType == STRUCTURE_NUKER)
                            if len(nuker):
                                nuker = nuker[0]
                                if nuker.energy < nuker.energyCapacity:
                                    _full = False
                        # 발전소 채우기
                        if creep.room.memory.options and creep.room.memory.options.fill_labs:
                            labs = all_structures.filter(lambda s: s.structureType == STRUCTURE_LAB)
                            if len(labs):
                                for l in labs:
                                    if l.energy < l.energyCapacity:
                                        _full = False
                                        break

                        # print('_full', _full)
                        # 채울게 없으면 잉여롭게 계속 뭐 뽑으려 하지 말고 활동중단
                        if _full:
                            # 꽉 차서 활동중단임을 표시.
                            if not creep.memory.all_full:
                                creep.memory.all_full = 1
                            return
                    # 위에 걸리는거 없으면
                    # todo 다른방법 강구요망
                    if creep.room.terminal and creep.room.terminal.store[RESOURCE_ENERGY] >= \
                            terminal_capacity + creep.carryCapacity:
                        creep.memory.pickup = creep.room.terminal.id
                    elif creep.room.storage and \
                            creep.room.storage.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5:
                        creep.memory.pickup = creep.room.storage.id
                    else:
                        pass
                else:
                    creep.memory.pickup = pickup_id

            # 픽업대상이 존재하는 경우
            if creep.memory.pickup:
                pickup_obj = Game.getObjectById(creep.memory.pickup)
                # 만일 어떤 종류의 자원을 빼갈지 결정이 안된 경우.
                # todo 어떤 형태의 리소스를 가지는지 확인.
                if pickup_obj and not creep.memory[haul_resource]:
                    # 컨테이너일 경우 모든걸 다 빼가는걸 원칙으로 하되 업글용 컨테이너가 있으면 에너지만 제외.
                    if pickup_obj.structureType == STRUCTURE_CONTAINER:
                        # 렙 8일때만 찾으면 됨.
                        if not creep.room.controller.level == 8:
                            for s in creep.room.memory[STRUCTURE_CONTAINER]:
                                if s.id == pickup_obj.id and s[for_upgrade]:
                                    # 단, 스토리지가 없는 경우 예외.
                                    if Game.getObjectById(creep.memory.upgrade_target).level > 3 \
                                            and not Game.getObjectById(creep.memory.upgrade_target).room.storage:
                                        creep.memory[haul_resource] = RESOURCE_ENERGY
                                    else:
                                        creep.memory[haul_resource] = haul_all_but_energy
                        # 위 해당사항 없으면 우선 다 뽑아간다.
                        if not creep.memory[haul_resource]:
                            creep.memory[haul_resource] = haul_all
                    # todo 임시방편임. 추후 변경필요함.
                    elif Game.getObjectById(creep.memory.pickup).structureType == STRUCTURE_LAB \
                            or Game.getObjectById(creep.memory.pickup).structureType == STRUCTURE_STORAGE \
                            or Game.getObjectById(creep.memory.pickup).structureType == STRUCTURE_TERMINAL:
                        creep.memory[haul_resource] = RESOURCE_ENERGY
                    else:
                        creep.memory[haul_resource] = haul_all

                result = grab_energy_new(creep, creep.memory.haul_resource)
                # creep.say(result)
                if result == ERR_NOT_IN_RANGE:
                    # 메모리에 있는걸 최우선적으로 찾는다.
                    move_by_path = movement.move_with_mem(creep, creep.memory.pickup, 0)
                    if move_by_path[0] == OK and move_by_path[1]:
                        creep.memory.path = move_by_path[2]

                # 여러 자원을 뽑아야 하는 경우도 있는지라 이거 한번에 laboro 를 1로 전환하지 않는다.
                elif result == 0:
                    creep.say('BEEP BEEP⛟', True)
                    del creep.memory.path
                elif result == ERR_NOT_ENOUGH_ENERGY:
                    del creep.memory.pickup
                    del creep.memory.path
                    del creep.memory[haul_resource]
                    return
                # other errors? just delete 'em
                else:
                    creep.say('ERR {}'.format(result))
                    del creep.memory.pickup
                    del creep.memory.path

            else:
                # 픽업대상이 없어서 뽑아야할때도 주변에 모든 떨궈진 자원을 찾아본다.
                if not creep.memory.all_full:
                    creep.memory.all_full = 1
                # if there's nothing in the storage they harvest on their own.
                if not creep.memory.source_num:
                    creep.memory.source_num = creep.pos.findClosestByRange(creep.room.find(FIND_SOURCES)).id

                harvest_energy(creep, creep.memory.source_num)
        # 꽉차면 초기화작업과 작업변환.
        if _.sum(creep.carry) >= creep.carryCapacity:
            init_memory(creep, 1)

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
            movement.get_to_da_room(creep, creep.memory.assigned_room, False)
            return

        if not creep.memory.priority and not creep.memory.priority == 0:
            creep.memory.priority = 0

        # if their priority is not decided. gonna need to pick it firsthand.
        if creep.memory.priority == 0:
            passed_priority_0 = True

            # 전체 에너지의 99% 이상 채우지 않으면 건설은 없다. 건설보다 운송이 더 시급하기 때문.
            if len(constructions) > 0 and creep.room.energyAvailable >= creep.room.energyCapacityAvailable * .99:
                picker = 1
            else:
                picker = 0
            if not picker:
                # defining structures to fill the energy on. originally above of this spot but replaced for cpu eff.
                # towers only fills 80% since it's gonna repair here and there all the time.
                structures = grab_haul_list(creep, creep.room.name, all_structures, True)
            else:
                structures = []
            # print('picker {} and len(structures) {}'.format(picker, len(structures)))
            #
            if not picker and len(structures) > 0:
                creep.say('🔄물류,염려말라!', True)
                creep.memory.priority = 1

                # 스토리지는 항상 마지막에 채운다. 우선 있는지 확인부터 한거
                if creep.room.storage and creep.room.storage.storeCapacity - _.sum(creep.room.storage.store):
                    index = structures.indexOf(creep.room.storage)
                    structures.splice(index, 1)

            elif len(constructions) > 0:
                creep.say('🚧건설,염려말라!', True)
                creep.memory.priority = 2
            elif len(repairs) > 0 and creep.room.controller.level >= 3:
                creep.say('🔧 세상을 고치자!', True)
                creep.memory.priority = 3
            else:
                creep.say('⚡ 위대한 발전!', True)
                creep.memory.priority = 4

        # priority 1: transfer
        if creep.memory.priority == 1:
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
            miscellaneous.repair_on_the_way(creep, repairs, constructions)

            # check if haul_target's capacity is full
            target = Game.getObjectById(creep.memory.haul_target)
            # haul_target 이 중간에 폭파되거나 이미 꽉 찼을 시...
            if not target \
                    or ((target.structureType == STRUCTURE_TOWER and target.energy >= target.energyCapacity - 20)
                        or (target.structureType == STRUCTURE_CONTAINER
                            and target.energy >= target.energyCapacity * .9)
                        or ((target.structureType == STRUCTURE_SPAWN or target.structureType == STRUCTURE_EXTENSION)
                            and target.energy == target.energyCapacity)
                        or _.sum(target.store) == target.storeCapacity):
                # print(creep.name, 'FULL')
                del creep.memory.haul_target
            # 에너지 외 자원 운송중인데 대상이 에너지 채우는거면 통과한다.
            if target and \
                    (target.structureType == STRUCTURE_EXTENSION
                     or target.structureType == STRUCTURE_TOWER
                     or target.structureType == STRUCTURE_NUKER
                     or target.structureType == STRUCTURE_SPAWN) \
                    and not creep.store.getCapacity(RESOURCE_ENERGY):
                # print(creep.name, 'RES NULL')
                del creep.memory.haul_target

            if not creep.memory.haul_target:
                # 위에 priority 0 거치지 않았으면 여기 지금 텅 비었음.
                if not len(structures):
                    # 크립 허울대상 확인
                    structures = grab_haul_list(creep, creep.room.name, all_structures)
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
                        if len(constructions) > 0 and creep.carry[RESOURCE_ENERGY] > 0:
                            creep.say('🚧 공사전환!', True)
                            creep.memory.priority = 2
                        elif creep.room.storage and _.sum(creep.room.storage.store) < creep.room.storage.storeCapacity:
                            creep.say('📦 저장합시다', True)
                            creep.memory.haul_target = creep.room.storage.id
                        # 스토리지가 없으면?
            # 이 시점까지 타겟이 없다면 스토리지고 뭐고 넣을 수 있는 공간이 전혀 없다는거.
            if not creep.memory.haul_target:
                if len(constructions) > 0:
                    creep.say('🚧 공사전환~', True)
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
                # 당장 넣을 수 있는 상황이 아니면 간다.
                if not creep.pos.isNearTo(target):
                    # path = _.map(creep.memory.path, lambda p: __new__(RoomPosition(p.x, p.y, creep.room.name)))
                    move_by_path = movement.move_with_mem(creep, creep.memory.haul_target, 0)
                    # if move_by_path[0] == OK or move_by_path[0] == ERR_TIRED:
                    if move_by_path[0] == OK and move_by_path[1]:
                        creep.memory.path = move_by_path[2]

                # 바로 옆이면 시작.
                else:
                    # 에너지만 들어가는것인가?
                    if target.structureType == STRUCTURE_EXTENSION \
                            or target.structureType == STRUCTURE_TOWER \
                            or target.structureType == STRUCTURE_NUKER \
                            or target.structureType == STRUCTURE_SPAWN \
                            or target.structureType == STRUCTURE_LAB:
                        only_energy = True
                    # todo 이거 임시임, 뭘 넣을지 완전히 뜯어고친다.
                    elif target.structureType == STRUCTURE_CONTAINER:
                        # 렙8이 아닐 경우 대상이 업글용인지 확인한다.
                        if not creep.room.controller.level == 8:
                            a = 0
                            for s in creep.room.memory[STRUCTURE_CONTAINER]:
                                if s.id == target.id and s[for_upgrade]:
                                    only_energy = True
                                    a = 1
                                    break
                            if not a:
                                only_energy = False
                        else:
                            only_energy = False

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
                                if creep.room.terminal:
                                    creep.memory.pickup = creep.room.terminal.id
                    # 에너지만 넣은 상태면 바로 다음으로 넘어간다.
                    if only_energy and (transfer_minerals_result == OK or transfer_minerals_result == ERR_FULL):

                        # 크립 허울대상 확인
                        structures = grab_haul_list(creep, creep.room.name, all_structures)
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
                        # 스트럭쳐가 텅 비었다는건 채울건 다 채웠다는 소리.
                        else:
                            # 건설할게 있으면 공사전환, 아니면 스토리지로
                            if len(constructions) > 0 and creep.carry[RESOURCE_ENERGY] > 0:
                                creep.say('🚧 공사전환!', True)
                                creep.memory.priority = 2
                                del creep.memory.path
                            elif creep.room.storage:
                                creep.say('📦 저장합시다', True)
                                del creep.memory.path
                                creep.memory.haul_target = creep.room.storage.id
                    else:
                        pass

            # 이 시점에 haul_target 이 있으면 거기로 간다.
            if creep.memory.haul_target and not transfer_minerals_result == -100 \
                    and not creep.pos.isNearTo(Game.getObjectById(creep.memory.haul_target)):
                # path = _.map(creep.memory.path, lambda p: __new__(RoomPosition(p.x, p.y, creep.room.name)))
                move_by_path = movement.move_with_mem(creep, creep.memory.haul_target, 0)

                if move_by_path[1]:
                    path = move_by_path[2]
        # priority 2: build
        if creep.memory.priority == 2:
            # 빌드타겟 존재하는지 확인
            if creep.memory.build_target and not Game.getObjectById(creep.memory.build_target):
                del creep.memory.build_target
            # 만일 방이 만렙 아니면 컨트롤러 업글도 병행
            if creep.room.controller and creep.room.controller.my and creep.room.controller.level < 8:
                creep.upgradeController(Game.getObjectById(creep.memory.upgrade_target))

            if not creep.memory.build_target:
                closest_construction = creep.pos.findClosestByRange(constructions)
                # 이 시점에서 안뜨면 건설할게 없는거임.
                if not closest_construction:
                    creep.say("지을게 없군 👏", True)
                    creep.memory.priority = 0
                    del creep.memory.path
                    return
                else:
                    creep.memory.build_target = closest_construction.id

            build_result = creep.build(Game.getObjectById(creep.memory.build_target))

            if build_result == ERR_NOT_IN_RANGE:
                movement.ranged_move(creep, creep.memory.build_target, creeps, 3)

            # if there's nothing to build or something
            elif build_result == ERR_INVALID_TARGET:
                # creep.memory.priority = 0
                del creep.memory.build_target
                return

            elif build_result == ERR_NO_BODYPART:
                creep.say('운송이 본분!', True)
                creep.memory.priority = 1
                del creep.memory.path
                return

            # if having anything other than energy when not on priority 1 switch to 1
            if _.sum(creep.carry) != 0 and creep.carry[RESOURCE_ENERGY] == 0:
                creep.memory.priority = 1
                del creep.memory.path
                del creep.memory.build_target
        # priority 3: repair
        elif creep.memory.priority == 3:
            if creep.memory.repair_target:
                repair = Game.getObjectById(creep.memory.repair_target)
                # 수리대상 체력이 꽉차거나 방 안에 채워진 에너지가 80% 이하면 교체확인.
                # 허울러는 무조건 이름처럼 운송이 주다!
                if repair.hits == repair.hitsMax \
                        or creep.room.energyAvailable <= creep.room.energyCapacityAvailable * .8:
                    del creep.memory.repair_target
                    # 당장 수리대상이 수리완료했을 때 채워야 하는 대상이 있으면 바로 전환한다.
                    hauling_need = False

                    # 에너지가 부족하거나 건설대상이 있는지 확인
                    if creep.room.energyAvailable < creep.room.energyCapacityAvailable or len(constructions):
                        hauling_need = True

                    if not hauling_need:
                        # 핵이 있고 채움대상인지 확인.
                        nuker = all_structures.filter(lambda s: s.structureType == STRUCTURE_NUKER)
                        if len(nuker):
                            nuker = nuker[0]
                        else:
                            nuker = None
                        if creep.room.memory.options.fill_nuke and nuker and nuker.energy < nuker.energyCapacity:
                            hauling_need = True

                        # 연구소도 확인
                        labs = all_structures.filter(lambda s: s.structureType == STRUCTURE_LAB)
                        if not hauling_need and creep.room.memory.options.fill_labs and len(labs):
                            for l in labs:
                                if l.energy < l.energyCapacity:
                                    hauling_need = True
                                    break
                    if hauling_need:
                        creep.memory.priority = 1
                        del creep.memory.path
                        creep.say('다시 채우러~', True)
                        return

            if not creep.memory.repair_target:
                if len(repairs) > 0:
                    creep.memory.repair_target = creep.pos.findClosestByRange(repairs).id
                    repair = Game.getObjectById(creep.memory.repair_target)
                # no repairs? GTFO
                else:
                    creep.memory.priority = 0
                    del creep.memory.path
                    return

            repair_result = creep.repair(repair)

            if repair_result == ERR_NOT_IN_RANGE:
                movement.ranged_move(creep, creep.memory.repair_target, creeps)

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
            movement.ranged_move(creep, creep.memory.upgrade_target, creeps, 3)

            miscellaneous.repair_on_the_way(creep, repairs, constructions, True)

            # if having anything other than energy when not on priority 1 switch to 1
            # 운송크립은 발전에 심혈을 기울이면 안됨.
            if creep.carry[RESOURCE_ENERGY] <= 0 \
                    or creep.room.energyAvailable < creep.room.energyCapacityAvailable * outer_work_perc \
                    or len(constructions):
                creep.memory.priority = 1
                creep.say('복귀!', True)
                return


def filter_haul_targets(creep, haul_targets, haulers):
    """
    위에 허울러가 에너지 채울 컨테이너 등을 선택하는 함수.

    :param creep: 크립(..)
    :param haul_targets: 에너지 채울 대상.
    :param haulers: 허울러라 써있지만 실질적으로는 모든 크립.
    :return: creep.memory.haul_target 에 들어갈 아이디.
    """

    if len(haul_targets) == 0:
        return ERR_INVALID_TARGET

    # 애초에 이게 있으면 여기오면 안되지만...
    if creep.memory.haul_target:
        return creep.memory.haul_target

    # 목표를 찾았는지 확인용도
    found = 0

    # 목표 컨테이너 초기화 용도.
    target = None

    while not found or len(haul_targets) > 0:
        # size_counter is used to determines the number of creeps that can be added to the haul_target.
        size_counter = 0

        # if theres no structures to haul to, then no reason to do this loop
        if len(haul_targets) == 0:
            break

        # 가장 가까운 건물.
        structure = creep.pos.findClosestByPath(haul_targets, {ignoreCreeps: True})

        for kripo in haulers:
            # 크립이름이 똑같거나 운송표적이 없으면 건너뛴다. 볼필요없음.
            if creep.name == kripo or not kripo.memory.haul_target:
                continue

            # kripo.memory.haul_target == structure.id, 건너뛴다
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
                        elif _.sum(structure.store) < structure.storeCapacity * .7:
                            size_counter += 2
                        else:
                            size_counter += 3
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
        # but, if that's the only one, ok...
        if structure.structureType == STRUCTURE_SPAWN:
            if creep.pos.isNearTo(Game.getObjectById(structure.id)) \
                    and structure.energy >= structure.energyCapacity * .9 and not len(haul_targets) == 1:
                size_counter += 3

        # size_counter estas malpli ol 3 == structure povas asigni al creep-o
        if size_counter < 3:
            # asignu ID kaj brakigi.
            target = structure.id
            found = 1
            break

        else:
            index = haul_targets.indexOf(structure)
            haul_targets.splice(index, 1)

    if found:
        return target
    else:
        return ERR_INVALID_TARGET


# noinspection PyPep8Naming
def grab_haul_list(creep: Creep, roomName, totalStructures, add_storage=False):
    """
    위에 허울러가 에너지를 채울 목록 확인.

    :param creep:
    :param roomName: 방이름.
    :param totalStructures: 본문 all_structures 와 동일
    :param add_storage: 스토리지를 포함할 것인가? priority == 0 인 상황 아니면 포함할일이 없음.
    :return: 허울러의 에너지 채울 대상목록
    """

    # defining structures to fill the energy on. originally above of this spot but replaced for cpu eff.
    # towers only fills 80% since it's gonna repair here and there all the time.
    structures = totalStructures.filter(lambda s: ((s.structureType == STRUCTURE_SPAWN
                                                    or s.structureType == STRUCTURE_EXTENSION)
                                                   and s.energy < s.energyCapacity)
                                                  or (s.structureType == STRUCTURE_TOWER
                                                      and s.energy < s.energyCapacity * 0.8)
                                                  or (s.structureType == STRUCTURE_TERMINAL
                                                      and s.store[RESOURCE_ENERGY] < 10000))

    # 스토리지에 넣을 양이 있을때 추가하는거임.
    # 기준: 스토리지에 남은 양이 max_energy 값 이상일 경우
    # 변경: 스토리지에 남은 양이 있는 경우
    if add_storage:
        structures.extend(totalStructures.filter
                          (lambda s: s.structureType == STRUCTURE_STORAGE
                                     # and s.storeCapacity - _.sum(s.store) >= Game.rooms[roomName].memory.options[max_energy]))
                                     and s.storeCapacity - _.sum(s.store) > 0))

    # 핵에 에너지 넣는걸로 함?
    if Memory.rooms[roomName].options and Memory.rooms[roomName].options.fill_nuke:
        nuke_structure_add = totalStructures.filter(lambda s: s.structureType == STRUCTURE_NUKER
                                                              and s.energy < s.energyCapacity)
        structures.extend(nuke_structure_add)
    # 연구소에 에너지 넣는걸로 함?
    if Memory.rooms[roomName].options and Memory.rooms[roomName].options.fill_labs:
        structure_add = totalStructures \
            .filter(lambda s: s.structureType == STRUCTURE_LAB and s.energy < s.energyCapacity)
        structures.extend(structure_add)

    container = []
    # for_upgrade :스토리지가 컨트롤러에서 많이 떨어져 있을때 대비해 두는 컨테이너.
    # 렙 8이하에 에너지가 있을때만 찾는다
    if Game.rooms[roomName].controller.level < 8 and creep.store.getCapacity(RESOURCE_ENERGY):
        for rcont in Game.rooms[roomName].memory[STRUCTURE_CONTAINER]:
            cont_obj = Game.getObjectById(rcont.id)
            if not cont_obj:
                continue
            # 업글용 컨테이너고 수확저장용도가 아닌가? 그러면 허울러가 넣는다. 2/3 이하로 차있을때만.
            if rcont.for_upgrade and not rcont.for_harvest \
                    and cont_obj.store.getUsedCapacity() < cont_obj.store.getCapacity() * 2/3:
                # 단, 스토리지를 만들 렙(4이상)이고 스토리지가 없으면 안넣는다.
                # 방 내 에너지가 안 찼을때도 통과
                if 4 <= creep.room.controller.level and not creep.room.storage \
                        or creep.room.energyAvailable < creep.room.energyCapacityAvailable * .95:
                    continue
                container.append(Game.getObjectById(rcont.id))

    structures.extend(container)

    return structures


def init_memory(creep, init_to):
    """
    전환할때 각종 메모리 초기화.

    :param creep:
    :param init_to: 몇으로 바꾸는 것인가?? 그거에 맞게 메모리 삭제.
    :return: None
    """

    # 0으로 바꿀 경우.
    if init_to == 0:
        creep.memory.laboro = 0
        del creep.memory.haul_target
        del creep.memory.build_target
        del creep.memory.repair_target
        del creep.memory[haul_resource]

    # 1로 바꾸는 경우.
    elif init_to == 1:
        creep.memory.laboro = 1
        creep.memory.priority = 0
        del creep.memory.pickup
        del creep.memory.source_num
        del creep.memory.path
