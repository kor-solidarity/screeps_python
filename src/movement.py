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

    # 아래 moveTo()를 무조건 실행하면 생CPU 0.2가 나가니 그거 방지용도임.
    if creep.pos.isEqualTo(target_obj):
        return OK

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
    # 임시방편. 저장된 길 시리얼번호가 아예 없는경우가 포착됨. 우선 날려봐본다.
    if not creep.memory._move['path']:
        del creep.memory._move
    if avoid_id:
        del avoid_id
    return ERR_NO_PATH


def move_using_swap(creep, creeps, target, ignore_creeps=True, reuse_path=40,
                    avoid_id=False, avoid_role=False, ranged=0):
    """
    크립의 이동 종결자.
    이동은 두가지 뿐이다. 바로앞까지 가는가 아니면 몇칸이상 남겨도 되는가.
    그리고 이 이동은 지속적인 수정이 필요한 이동이 아니면 사용을 금지한다.
    물론 이건 군인 외 해당사항이 거의 없으리라고 봄.

    :param creep: 크립 본인
    :param creeps: 방 안 모든 다른 크립들
    :param target: 가는 목표 ID
    :param ignore_creeps: 크립교체를 안할 것인가? 이거 생각좀 해봐야함 필요한지. 기본값 거짓
    :param reuse_path: 길 재사용 숫자... 이것도 필요한가?? 기본값 40
    :param avoid_id: 자리교체 후 교체할 필요가 생겼을때 똑같은 상대와 중복해 옮기는걸 안할건가? 기본값 거짓
    :param avoid_role: 특정 롤 가진 크립이랑 교체를 하는가? 기본값 참.... 이거랑 위에 필요없을듯.
    :param ranged: 목표지점과 떨어져있어도 되는가? 3칸. 기본값 거짓.
    :return:
    """

    # 현재 위치한 곳이 이전 틱에도 있던곳인지 확인하고 옮기는 등의 절차.
    # swap_check = check_loc_and_swap_if_needed(creep, creeps, True)

    # 일정 거리 내로 들어오는 경우. 3이 일반적이고 그 이상 갈일 없을듯.
    if ranged > 0 and creep.pos.inRangeTo(Game.getObjectById(target), ranged * 2):
        res = movi(creep, target, ignoreCreeps=ignore_creeps, reusePath=10, range_to=ranged)
        return res

    # -------------------------------------------------------------
    # check_loc_and_swap_if_needed()
    if not avoid_id:
        avoid_id = creep.memory.last_swap
    else:
        avoid_id = 0
    # 직책도 마찬가지.
    if not avoid_role:
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
        swap_check = swapping(creep, creeps, avoid_id, avoid_role)
    else:
        swap_check = OK
    # -------------------------------------------------------------
    # 아무 문제 없으면 평소마냥 움직이는거.
    if swap_check == OK:
        # # 일정 거리 내로 들어오는 경우. 3이 일반적이고 그 이상 갈일 없을듯.
        # if ranged <= 1 and creep.pos.inRangeTo(Game.getObjectById(target), ranged*2):
        #     res = movi(creep, target, ignoreCreeps=ignore_creeps, reusePath=10, range_to=ranged)
        # # 바로앞까지 붙거나
        # else:
        res = movi(creep, target, ignoreCreeps=ignore_creeps, reusePath=reuse_path, range_to=ranged)
        return res
    # 확인용. 아직 어찌할지 못정함....
    elif swap_check == ERR_NO_PATH:
        # del creep.memory._move
        creep.say('ERR_NO_PATH')
        return ERR_NO_PATH
    # 위 둘 외에 다른게 넘어왔다는 소리는 실질적으로 어느 위치를 갔다는게 아니라
    # 다른 크립와 위치 바꿔치기를 시전했다는 소리. 메모리 옮긴다.
    else:
        creep.memory.last_swap = swap_check
        return OK