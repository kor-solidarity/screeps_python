from defs import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def check_for_destroyed_buildings(memory):
    # 특정 분기마다 저장된 위치에 건물이 없으면 배정된 건물을 짓는다.
    return