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

# NULLIFIED
# def memory_carry(creep):
#     """
#     define the CARRY size of the creep.
#     creep.carryCapacity
#     :param creep:
#     :return:
#     """
#
#     if not creep.carryCapacity:
#         carry_size = 0
#         for body in creep.body:
#             if body.type == 'carry':
#                 carry_size += 50
#
#         creep.carryCapacity = carry_size
#         return
#     # if there is a carry memory. this def. is unneeded.
#     else:
#         return


def pick_pickup(creep, creeps, storages):
    """
    designate pickup memory by targeted haulers
    :param creep: 크립본인
    :param creeps: 방안에 모든 크립
    :param storages: 대상 자원.
    :return storage: closest storage with energy left
    """
    # print('-------------name', creep.name)

    # if there's no empty storage at all
    # if len(storages) == 0:
    #     return ERR_INVALID_TARGET

    # storage with closest.... yeah
    closest_storage = creep.pos.findClosestByRange(storages)

    # hauler creep NULLIFIED
    # portist_kripoj = _.filter(creeps, lambda c: c.memory.role == 'hauler')
    # creeps.
    portist_kripoj = creeps
    # will filter for leftover energy,
    # tldr - if theres already a creep going for it, dont go unless there's some for you.
    while not creep.memory.pickup or len(storages) > 0:
        # print('storages:', storages)
        # safety trigger
        if len(storages) == 0:
            break

        # to distinguish storage var. with storages inside while loop.
        loop_storage = creep.pos.findClosestByPath(storages)

        # if storage is a link, which only holds energy
        if loop_storage.structureType == STRUCTURE_LINK:
            stored_energy = loop_storage.energy
        # else == container or storage.
        else:
            stored_energy = _.sum(loop_storage.store)

        # print('designated storage: {}, stored_energy: {}'.format(loop_storage, stored_energy))

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
        if stored_energy >= creep.carryCapacity * .5:
            return loop_storage.id
            # creep.memory.pickup = loop_storage.id
            # break
        else:
            index = storages.indexOf(loop_storage)
            # storages.remove(loop_storage)
            storages.splice(index, 1)

    # if all storages are occupied or empty, check for storage,
    # and just get to the closest one if storage is missing too.
    if not creep.memory.pickup:
        if creep.room.storage and creep.room.storage.store[RESOURCE_ENERGY] >= creep.carryCapacity * .5:
            return creep.room.storage.id
            # creep.memory.pickup = creep.room.storage.id
            # 이건 왜...??
            # creep.memory.only_energy = True
        else:
            if not closest_storage:
                return ERR_INVALID_TARGET
            return closest_storage.id
            # creep.memory.pickup = closest_storage.id

    return closest_storage
