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
