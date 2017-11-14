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


# only for defending the remote room from ai
def run_remote_defender(creep, creeps, hostile_creeps):
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
        if creep.room.name != Game.flags[creep.memory.flag_name].room.name:
            creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'}})
            return
    except:
        creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'}})
        return
    # find the goddamn enemies
    if creep.room.name != Game.flags[creep.memory.flag_name].room.name:
        enemies = hostile_creeps
    else:
        enemies = Game.flags[creep.memory.flag_name].room.find(FIND_HOSTILE_CREEPS)

    if len(enemies) > 0:

        enemy = creep.pos.findClosestByRange(enemies)

        # distance = creep.pos.getRangeTo(enemy)
        creep.rangedAttack(enemy)

        # attack result
        atk_res = creep.attack(enemy)

        if atk_res == ERR_NOT_IN_RANGE:

            rand_int = random.randint(0, len(listo)-1)
            creep.say(listo[rand_int], True)
            creep.heal(Game.getObjectById(creep.id))
            creep.moveTo(enemy, {'visualizePathStyle': {'stroke': '#FF0000'}, 'ignoreCreeps': False})
        elif atk_res == OK:
            return
        else:
            print(creep.name, 'ATK ERR:', atk_res)
    # no enemies? heal the comrades and gtfo of the road
    else:
        wounded = _.filter(creeps, lambda c: c.hits < c.hitsMax)

        if len(wounded) > 0:
            closest = creep.pos.findClosestByRange(wounded)
            heal = creep.heal(closest)

            if heal != 0:
                creep.moveTo(closest, {'visualizePathStyle': {'stroke': '#FF0000', 'opacity': .25}})
        else:
            # just to get the creep off the road
            creep.moveTo(Game.flags[creep.memory.flag_name], {'visualizePathStyle': {'stroke': '#ffffff'},
                                                              'reusePath': 50})


def defender(creep, hostile_creeps):
    """
    방어용 저격수
    :type creep: Game.creeps
    :type hostile_creeps: dict[str, Creep]
    :return:
    """
    hostile_creeps

# def run_defender(creep, creeps, )