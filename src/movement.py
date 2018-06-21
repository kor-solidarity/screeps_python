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


def movi(creep, target, range=0, reusePath=20, ignoreCreeps=False, color='#ffffff'):
    target = Game.getObjectById(target)
    return creep.moveTo(target, {'range': range, 'ignoreCreeps': ignoreCreeps
                        , 'visualizePathStyle': {'stroke': color}, 'reusePath': reusePath})
