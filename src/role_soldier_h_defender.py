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


# 본진 수비병. 벽 뚫을려는 놈들 조지는게 목표.
def h_defender(all_structures, creep, creeps, hostile_creeps):
    """

    :param all_structures:
    :param creep:
    :param creeps:
    :param hostile_creeps:
    :return:
    """

    # random blurtin'
    listo = ['Charge!', "KILL!!", "Ypa!", 'CodeIn 🐍!', 'Python 🤘!']

    if creep.memory.assigned_room != creep.room.name:
        miscellaneous.get_to_da_room(creep, creep.memory.assigned_room, False)
        return

    # find the goddamn enemies
    if creep.room.name == creep.memory.assigned_room:
        enemies = hostile_creeps
        enemies = miscellaneous.filter_enemies(enemies)

    if len(enemies) > 0:
        # 공격절차: 걍 뚜까부순다.
        enemy = creep.pos.findClosestByRange(enemies)
        atk = creep.attack(enemy)
        if atk == ERR_NOT_IN_RANGE:
            creep.moveTo(enemy,
                         {'visualizePathStyle': {'stroke': '#FF0000'}, 'ignoreCreeps': False})
    else:
        miscellaneous.get_to_da_room(creep, creep.memory.assigned_room, False)
