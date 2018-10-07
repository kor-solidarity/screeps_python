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
__pragma__('kwargs')


# noinspection PyPep8Naming
def movi(creep, target, range_to=0, reusePath=20, ignoreCreeps=False, maxOps=2000, color='#ffffff'):
    """
    크립 움직이는거 관련.

    :param creep: 크립
    :param target: 목표 ID
    :param range_to: 거리, 기본값 1
    :param reusePath: 재사용틱, 기본값 20
    :param ignoreCreeps: 크립무시여부, 기본값 False
    :param maxOps: 패스파인딩 할때 돌릴 시뮬 수. 기본값 2천
    :param color: 기본값 #ffffff
    :return: 결과
    """
    # print(creep.name, 'range_to', range_to)
    target_obj = Game.getObjectById(target)
    return creep.moveTo(target_obj, {'range': range_to, 'ignoreCreeps': ignoreCreeps
                        , 'visualizePathStyle': {'stroke': color},
                                     'reusePath': reusePath, 'maxOps': maxOps})


def check_loc_and_swap_if_needed(creep, creeps, avoid_id=False, avoid_role=False):
    """
    크립이 현위치에 계속 있는지 확인.
    안움직였으면 카운터 올리고 다섯번 넘기면 주변에 있는 크립 하나랑 위치교체한다.
    이 옵션을 쓴다면 move_ticks, cur_loc, last_swap 이 메모리들을 가지고 다녀야 함.
    또한 이건 여기서만 쓰기 때문에 이 안에서 다 처리한다.

    :param creep:
    :param creeps:
    :param avoid_id:
    :param avoid_role:
    :return:
        성공적으로(?) 이동완료됬으면 이동한 크립 아이디 반환. 상호변환 할일이 없으면 오케이,
        옮겨야하는데 못옮기면 ERR_NO_PATH
    """

    # 지나친 크립이고 뭐고 다 무시하고 지나갈때도 존재함. 근데 엥간해선 없을듯.
    if avoid_id:
        avoid_id = creep.memory.last_swap
    else:
        avoid_id = 0
    # 직책도 마찬가지.
    if avoid_role:
        avoid_role = creep.memory.role
    else:
        avoid_role = 0

    # 없으면 1로 초기화.
    if not creep.memory.move_ticks:
        creep.memory.move_ticks = 1

    # checking current location - only needed when check in par with move_ticks
    if not creep.memory.cur_loc:
        creep.memory.cur_loc = creep.pos
    if not creep.fatigue == 0:
        pass
    # 현재 크립위치와 대조해본다. 동일하면 move_ticks 에 1 추가 아니면 1로 초기화.
    elif JSON.stringify(creep.memory.cur_loc) == JSON.stringify(creep.pos):
        creep.memory.move_ticks += 1
    else:
        creep.memory.move_ticks = 1
        # renew
        creep.memory.cur_loc = creep.pos
    # 5보다 더 올라갔다는건 앞에 뭔가에 걸렸다는 소리.
    if creep.memory.move_ticks > 5 and creep.fatigue == 0:
        # 아래만 단독으로 돌릴일이... 있긴 할라나? 어쨌건 우선 그리 돌림
        return swapping(creep, creeps, avoid_id, avoid_role)
    else:
        return OK


def swapping(creep, creeps, avoid_id='', avoid_role=''):
    """
    길막할 경우 위치변환.

    :param creep:
    :param creeps:
    :param avoid_id:
    :param avoid_role:
    :return:
    """
    for c in creeps:
        if creep.pos.inRangeTo(c, 1) and not c.name == creep.name \
                and not (c.id == avoid_id or c.memory.role == avoid_role):
            creep.say('GTFO', True)
            mv = c.moveTo(creep)
            creep.moveTo(c)
            return c.id
    creep.memory.move_ticks = 1
    if avoid_id:
        del avoid_id
    return ERR_NO_PATH


# def move_using_swap(creep, creeps, avoid_id=False, avoid_role=False):