from defs import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')

"""
제목 그대로 잡다한 기능들 총집합. 메인에서 굳이 반복작업 안하려고 만든거. 
"""


def filter_allies(hostile_creeps):
    """
    filter out allies(ones must not be killed) from FIND_HOSTILE_CREEPS
    :param hostile_creeps:
    :return:
    """
    ally_list = Memory.allianceArray
    for hostile in hostile_creeps:
        # this is an NPC
        if hostile.owner.username == 'Invader':
            continue
        # print('hostile.owner.username:', hostile.owner.username)
        for ally in ally_list:
            # print('ally.username:', ally.username)
            # if hostile's name is equal to ally's name it's excluded
            if hostile.owner.username == ally.username:
                hostile_creeps.splice(hostile_creeps.indexOf(hostile), 1)
                break

    return hostile_creeps


def pick_pickup(creep, creeps, storages, terminal_capacity=10000):
    """
    designate pickup memory by targeted haulers
    :param terminal_capacity:
    :param creep: 크립본인
    :param creeps: 방안에 모든 크립
    :param storages: 대상 자원.
    :return storage: closest storage with energy left
    """
    # storage with closest.... yeah
    closest_storage = creep.pos.findClosestByRange(storages)

    # creeps.
    portist_kripoj = creeps
    # print('storages', storages)
    # will filter for leftover energy,
    # tldr - if theres already a creep going for it, dont go unless there's some for you.
    while not creep.memory.pickup or len(storages) > 0:
        # print('checkj')
        # safety trigger
        if len(storages) == 0:
            break

        # to distinguish storage var. with storages inside while loop.
        loop_storage = creep.pos.findClosestByRange(storages)

        if not loop_storage:
            break

        # if storage is a link, which only holds energy
        if loop_storage.structureType == STRUCTURE_LINK:
            stored_energy = loop_storage.energy
        # else == container or storage.
        else:
            stored_energy = _.sum(loop_storage.store)

        for kripo in portist_kripoj:
            # if hauler dont have pickup, pass
            if not kripo.memory.pickup:
                continue
            else:
                # if same id, drop the amount the kripo can carry.
                if loop_storage.id == kripo.memory.pickup:
                    # print('loop_storage.id({}) ==
                    # kripo.memory.pickup({})'.format(loop_storage.id, kripo.memory.pickup))
                    stored_energy -= kripo.carryCapacity
                    # print('stored_energy:', stored_energy)
                else:
                    continue
        # if leftover stored_energy has enough energy for carry, set pickup.
        if stored_energy >= int(creep.carryCapacity * .45):
            return loop_storage.id
            # creep.memory.pickup = loop_storage.id
            # break
        else:
            index = storages.indexOf(loop_storage)
            # storages.remove(loop_storage)
            storages.splice(index, 1)

    # needs extra maintenance
    # if all storages are occupied or empty, check for storage,
    # and just get to the closest one if storage is missing too.
    if not creep.memory.pickup:
        if creep.room.terminal and \
                        creep.room.terminal.store[RESOURCE_ENERGY] >= terminal_capacity + creep.carryCapacity:
            return creep.room.terminal.id
        elif creep.room.storage and creep.room.storage.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5:
            return creep.room.storage.id
        else:
            if not closest_storage:
                return ERR_INVALID_TARGET
            return closest_storage.id
            # creep.memory.pickup = closest_storage.id

    return closest_storage


def roomCallback(creeps, roomName, structures, constructions=None, ignoreRoads=False, ignoreCreeps=False):
    """
    PathFinder 관련.
    :param structures:
    :param constructions:
    :param creeps: 모든 크립
    :param roomName:
    :param ignoreRoads:
    :param ignoreCreeps:
    :return:
    """
    room = Game.rooms[roomName]

    if not room:
        return

    if len(constructions) > 0:
        for c in constructions:
            structures.push(c)

    costs = __new__(PathFinder.CostMatrix())

    for struct in structures:
        if struct.structureType == STRUCTURE_ROAD and not ignoreRoads:
            print('not ignoreRoad')
            print('struct.type: {} | pos: {}'.format(struct.structureType, struct.pos))
            # 도로 최우선
            costs.set(struct.pos.x, struct.pos.y, 1)

        elif struct.structureType != STRUCTURE_CONTAINER and (struct.structureType != STRUCTURE_RAMPART or not struct.my):
            costs.set(struct.pos.x, struct.pos.y, 0xff)

    if not ignoreCreeps:
        for creep in creeps:
            # 크립 무시함
            costs.set(creep.pos.x, creep.pos.y, 0xff)

    return costs
