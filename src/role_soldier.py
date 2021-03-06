from typing import List

from defs import *
import random
import miscellaneous
import movement

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


# only for defending the remote room from ai
def run_remote_defender(all_objs, all_structures, creep: Creep, creeps: List[Creep], hostile_creeps: List[Creep], lairs=None):
    """
    blindly search and kills npc invaders

    :param all_objs:
    :param all_structures:
    :param creep:
    :param creeps: creep.room.find(FIND_MY_CREEPS)
    :param hostile_creeps: 적
    :param lairs:
    :return:
    """

    assigned_room_objs = all_objs[creep.memory.assigned_room]

    # in case there's no creep for visual
    if creep.room.name != creep.memory.assigned_room:
        if len(hostile_creeps) > 0:
            close_enemy = _.filter(hostile_creeps, lambda c: c.pos.inRangeTo(creep, 3))
            if len(close_enemy) > 0:
                e = creep.pos.findClosestByRange(close_enemy)
                creep.rangedAttack(e)
        if creep.hits != creep.hitsMax:
            creep.heal(Game.getObjectById(creep.id))
        if assigned_room_objs:
            # if there's no enemy in the room, just get there. If there is, head to one of them.
            if len(assigned_room_objs['hostile_creeps']):
                movement.ranged_move(creep, assigned_room_objs['hostile_creeps'][0].id, creeps)
            elif len(assigned_room_objs['hostile_structures']):
                movement.ranged_move(creep, assigned_room_objs['hostile_structures'][0].id, creeps)
            else:
                movement.get_to_da_room(creep, creep.memory.assigned_room, False)
        else:
            movement.get_to_da_room(creep, creep.memory.assigned_room, False)
        return

    if not creep.memory.keeper_lair and not creep.memory.keeper_lair == 0:
        for s in all_structures:
            if s.structureType == STRUCTURE_KEEPER_LAIR:
                creep.memory.keeper_lair = 1
                break
        # 여기 도달했으면 키퍼방이 아닌거.
        if not creep.memory.keeper_lair:
            creep.memory.keeper_lair = 0

    # find the goddamn enemies
    if creep.room.name == creep.memory.assigned_room:
        enemies = hostile_creeps
        # 혹시 npc 건물이 있는지도 확인한다.
        hostile_buildings = _.filter(all_structures, lambda s: (s.owner and s.owner.username == 'Invader'))
    else:
        enemies = Game.rooms[creep.memory.assigned_room].find(FIND_HOSTILE_CREEPS)
        enemies = miscellaneous.filter_enemies(enemies)
        hostile_buildings = None
    # print('hostile_buildings', hostile_buildings)

    if len(enemies) > 0 or len(hostile_buildings):
        if creep.memory.keeper_lair_spawning:
            del creep.memory.keeper_lair_spawning

        # 거리안에 없으면 무조건 펑펑 터친다
        creep.rangedMassAttack()

        if len(enemies):
            enemy: Creep = creep.pos.findClosestByRange(enemies)
        else:
            enemy: Structure = creep.pos.findClosestByRange(hostile_buildings)
        distance = creep.pos.getRangeTo(enemy)
        # 거리유지
        if distance < 3:
            goals = _.map(enemies, lambda: miscellaneous.find_distance(enemy))
            # print("goals:", goals)
            f = PathFinder.search(creep.pos, goals, {'flee': True})
            creep.cancelOrder('rangedMassAttack')
            creep.rangedAttack(enemy)
            position = f.path[0]
            creep.move(creep.pos.getDirectionTo(position))
            evading = True
        elif distance == 3:
            creep.cancelOrder('rangedMassAttack')
            creep.rangedAttack(enemy)
            creep.heal(Game.getObjectById(creep.id))
        else:
            if creep.hits < creep.hitsMax:
                creep.cancelOrder('rangedMassAttack')
                creep.heal(Game.getObjectById(creep.id))

            movement.ranged_move(creep, enemy.id, creeps)

    # no enemies? heal the comrades and gtfo of the road
    else:
        wounded = _.filter(creeps, lambda c: c.hits < c.hitsMax)

        if len(wounded) > 0:
            closest = creep.pos.findClosestByRange(wounded)
            if creep.pos.isNearTo(closest):
                heal = creep.heal(closest)
            else:
                heal = creep.rangedHeal(closest)

            if heal != OK:
                movement.ranged_move(creep, closest.id, creeps)
                # creep.moveTo(closest, {'visualizePathStyle': {'stroke': '#FF0000', 'opacity': .25}})

        # elif creep.memory.keeper_lair:
        # 방에 컨트롤러가 없다는건 키퍼레어가 있단 소리니..
        elif not creep.room.controller:
            # 스폰시간이 가장 낮은 키퍼레어로 다가가서 대기탄다.
            if not creep.memory.keeper_lair_spawning:
                lairs = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_KEEPER_LAIR)
                closest_lair = _.min(lairs, lambda l: l.ticksToSpawn)
                creep.memory.keeper_lair_spawning = closest_lair.id

            closest_lair_obj = Game.getObjectById(creep.memory.keeper_lair_spawning)
            if not creep.pos.inRangeTo(closest_lair_obj, 2):
                creep.moveTo(closest_lair_obj, {'visualizePathStyle': {'stroke': '#FF0000', 'opacity': .25}
                    , 'range': 3, 'reusePath': 10})
        else:
            # 아무것도 없으면 대기탄다
            if not creep.pos.inRangeTo(__new__(RoomPosition(25, 25, creep.memory.assigned_room)), 22):
                res = movement.get_to_da_room(creep, creep.memory.assigned_room, False)


# todo 키퍼방 키퍼제거용
def keeper_defender(all_structures, creep, creeps, hostile_creeps):
    """
    키퍼방 내 키퍼 엔피시 척살용 크립

    :param all_structures:
    :param creep:
    :param creeps:
    :param hostile_creeps:
    :return:
    """


def remote_healer(creep, creeps, hostile_creeps):
    """
    위 크립 치료용 크립.
    :param creep:
    :param creeps:
    :param hostile_creeps:
    :return:
    """


def defender(creep, hostile_creeps):
    """
    방어용 저격수
    :param Game.creeps creep:
    :param RoomObject.find(FIND_HOSTILE_CREEPS) hostile_creeps:
    :return:
    """
    # hostile_creeps
    return


def demolition(creep, structures):
    """
    건물 철거반. 도로와 컨테이너 빼고 다 부순다. 컨테이너는 메모리 유무.
    :param creep:
    :param structures:
    :return:
    """

    try:
        if creep.memory.assigned_room != creep.room.name:
            creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'},
                                                              'reusePath': 50})
            return
    except:
        # 방안에 있으면 상관없음. 깃발을 임의로 지울경우에 해당.
        if creep.room.name == creep.memory.assigned_room:
            pass
        else:
            print('no visual for flag "{}"'.format(creep.memory.flag_name))
            return

    # 도착하면 가장 가까이 있는 건물 파괴한다.
    if not creep.memory.target:
        # array = 0
        # 도로와 컨테이너는 제외

        # 컨테이너 포함할 경우.
        if creep.memory.demo_container:
            dem_structures = structures.filter(lambda s: (s.structureType == STRUCTURE_TOWER
                                                          or s.structureType == STRUCTURE_EXTENSION
                                                          or s.structureType == STRUCTURE_LINK
                                                          or s.structureType == STRUCTURE_LAB
                                                          or s.structureType == STRUCTURE_CONTAINER
                                                          or s.structureType == STRUCTURE_STORAGE
                                                          or s.structureType == STRUCTURE_WALL
                                                          or s.structureType == STRUCTURE_RAMPART))
        else:
            dem_structures = structures.filter(lambda s: (s.structureType == STRUCTURE_TOWER
                                                          or s.structureType == STRUCTURE_EXTENSION
                                                          or s.structureType == STRUCTURE_LINK
                                                          or s.structureType == STRUCTURE_LAB
                                                          or s.structureType == STRUCTURE_STORAGE
                                                          or s.structureType == STRUCTURE_WALL
                                                          or s.structureType == STRUCTURE_RAMPART))
        print(JSON.stringify(dem_structures))
        print()
        creep.memory.target = creep.pos.findClosestByRange(dem_structures).id

        target = Game.getObjectById(creep.memory.target)
        # 타겟이 없다: 일 다 끝났으니 깃발 빼고 자살좀.
        if not target:
            Game.flags[creep.memory.flag_name].remove()
            creep.suicide()
            return

    target = Game.getObjectById(creep.memory.target)

    dismantle = creep.dismantle(target)
    creep.say(dismantle)
    if dismantle == ERR_NOT_IN_RANGE:
        creep.moveTo(target, {'visualizePathStyle': {'stroke': '#c0c0c0'}, 'reusePath': 50})
    elif dismantle == 0:
        # if dismantle == 0:
        if Game.time % 3 == 0:
            creep.say('철거중 💣💣', True)
    elif dismantle == ERR_INVALID_TARGET:
        del creep.memory.target
