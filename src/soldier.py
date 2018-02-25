from defs import *
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


# only for defending the remote room from ai
def run_remote_defender(all_structures, creep, creeps, hostile_creeps):
    """
    blindly search and kills npc invaders
    :param creep:
    :param creeps: creep.room.find(FIND_MY_CREEPS)
    :param hostile_creeps: 적
    :return:
    """

    # random blurtin'
    listo = ['Charge!', "KILL!!", "Ypa!", 'CodeIn 🐍!', 'Python 🤘!']

    try:  # incase there's no creep for visual
        if creep.room.name != creep.memory.assigned_room:
            miscellaneous.get_to_da_room(creep, creep.memory.assigned_room)
            return
    except:
        miscellaneous.get_to_da_room(creep, creep.memory.assigned_room)
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
    if creep.room.name != Game.flags[creep.memory.flag_name].room.name:
        enemies = hostile_creeps
    else:
        enemies = Game.flags[creep.memory.flag_name].room.find(FIND_HOSTILE_CREEPS)

    if len(enemies) > 0:

        if creep.memory.keeper_lair_spawning:
            del creep.memory.keeper_lair_spawning

        # 거리안에 없으면 무조건 펑펑 터친다
        creep.rangedMassAttack()
        enemy = creep.pos.findClosestByRange(enemies)

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
            if creep.rangedAttack(enemy) == ERR_NO_BODYPART:
                creep.heal(Game.getObjectById(creep.id))
        else:
            if creep.hits < creep.hitsMax and not distance < 5:
                creep.cancelOrder('rangedMassAttack')
                creep.heal(Game.getObjectById(creep.id))
            creep.moveTo(enemy, {'visualizePathStyle': {'stroke': '#FF0000'}, 'ignoreCreeps': False})

        # attack result NULLIFIED
        # atk_res = creep.attack(enemy)
        #
        # if atk_res == ERR_NOT_IN_RANGE:
        #
        #     rand_int = random.randint(0, len(listo)-1)
        #     creep.say(listo[rand_int], True)
        #     creep.heal(Game.getObjectById(creep.id))
        #     creep.moveTo(enemy, {'visualizePathStyle': {'stroke': '#FF0000'}, 'ignoreCreeps': False})
        # elif atk_res == OK:
        #     return
        # else:
        #     print(creep.name, 'ATK ERR:', atk_res)
    # no enemies? heal the comrades and gtfo of the road
    else:
        wounded = _.filter(creeps, lambda c: c.hits < c.hitsMax)

        if len(wounded) > 0:
            closest = creep.pos.findClosestByRange(wounded)
            heal = creep.heal(closest)

            if heal != 0:
                creep.moveTo(closest, {'visualizePathStyle': {'stroke': '#FF0000', 'opacity': .25}})

        elif creep.memory.keeper_lair:
            # 스폰시간이 가장 낮은 키퍼레어로 다가가서 대기탄다.
            if not creep.memory.keeper_lair_spawning:
                lairs = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_KEEPER_LAIR)
                closest_lair = _.min(lairs, lambda l: l.ticksToSpawn)
                creep.memory.keeper_lair_spawning = closest_lair.id

            closest_lair_obj = Game.getObjectById(creep.memory.keeper_lair_spawning)
            if not creep.pos.inRangeTo(closest_lair_obj, 3):
                creep.moveTo(closest_lair_obj, {'visualizePathStyle': {'stroke': '#FF0000', 'opacity': .25}
                             , 'range': 3, 'reusePath': 10})

        else:
            # todo what if there's no containers??
            if not creep.memory.recycle_loc:
                containers = _.filter(all_structures, lambda s: s.structureType == STRUCTURE_CONTAINER)
                closest_container = creep.pos.findClosestByRange(containers)
                creep.memory.recycle_loc = closest_container.id
            if Game.getObjectById(creep.memory.recycle_loc):
                if creep.pos.inRangeTo(Game.getObjectById(creep.memory.recycle_loc), 0):
                    creep.suicide()
                else:
                    creep.moveTo(Game.getObjectById(creep.memory.recycle_loc)
                                 , {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 50})
            # just to get the creep off the road
            # creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'},
            #                                                   'reusePath': 50})


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
        if Game.flags[creep.memory.flag_name].room.name != creep.room.name:
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
