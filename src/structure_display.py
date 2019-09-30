# defs is a package which claims to export all constants and some JavaScript objects, but in reality does
#  nothing. This is useful mainly when using an editor like PyCharm, so that it 'knows' that things like Object, Creep,
#  Game, etc. do exist.
from defs import *
from _custom_constants import *

# These are currently required for Transcrypt in order to use the following names in JavaScript.
# Without the 'noalias' pragma, each of the following would be translated into something like 'py_Infinity' or
#  'py_keys' in the output file.
__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def display_location(target_obj: Game.structures, other_objs, distance=5):
    """
    현황 디스플레이 관련.
    Ĉefe Link kaj Spawn

    :param target_obj: 디스플레이 대상
    :param other_objs: 디스플레이에 걸릴 수 있는 여러 요소들()
    :param distance:
    :return: {'x': x값, 'y': y값, 'align': 어디로 쏠릴건지.} 오브젝트의 위치를 감안한 값임.
    """

    """
    - 오른쪽 5칸이내에 다른물건이 있는가.
    - 왼쪽 5칸엔?
    - 아래 1칸?
    - 위?
    """
    time_st = Game.cpu.getUsed()
    # print('other_objs', other_objs)
    # 각 위치에 디스플레이가 곤란한가?
    smth_at_right = False
    smth_at_left = False
    smth_at_top = False
    smth_at_bottom = False

    stop = False

    # print('target_obj.pos', JSON.stringify(target_obj.pos))

    # 본체가 x축 오른쪽 끝에 있어서 오른쪽에 표기를 못한다.
    if target_obj.pos.x > 49 - distance:
        # print('target_obj.pos.x > 44 smth_at_right')
        smth_at_right = True
    # 왼쪽 끝에 있음.
    elif target_obj.pos.x < 0 + distance:
        # print('target_obj.pos.x < 5 smth_at_left')
        smth_at_left = True
    # print('check1')
    while not stop:
        # print('while not stop')
        stop = True
        if not smth_at_right:
            # print('not smth_at_right')
            # x축 오른쪽 distance값 이내에 뭔가 있는가?
            for o in other_objs:
                if target_obj.id == o.id:
                    continue
                # 같은 선에 있는지도 확인.
                if o.pos.y == target_obj.pos.y:
                    # if distance <= target_obj.pos.x - o.pos.x:
                    # 0 아래로 내려가면 의미가 없음...
                    # print('o.pos.x', o.pos.x, 'target_obj.pos.x', target_obj.pos.x)
                    if 0 <= o.pos.x - target_obj.pos.x <= distance:
                        # print('smth_at_right')
                        stop = False
                        smth_at_right = True
                        break
        # x축 왼쪽?
        elif not smth_at_left:
            # print('not smth_at_left')
            for o in other_objs:
                if target_obj.id == o.id:
                    continue
                if o.pos.y == target_obj.pos.y:
                    # print('target_obj.pos.x', target_obj.pos.x, 'o.pos.x', o.pos.x)
                    if 0 <= target_obj.pos.x - o.pos.x <= distance:
                        # print('smth_at_left')
                        stop = False
                        smth_at_left = True
                        break
        # 바로위에 뭐가 있는가?
        # 위나 아래를 확인할때는 양옆 distance의 반값(소수점내림)으로 계산한다.
        elif not smth_at_top:
            # print('not smth_at_top')
            for o in other_objs:
                if target_obj.id == o.id:
                    continue
                # 바로위에 있는거만 보면됨
                if o.pos.y == target_obj.pos.y + 1:
                    # print('o.pos', JSON.stringify(o.pos), 'target_obj.pos', JSON.stringify(target_obj.pos))
                    # print('o.pos.y', o.pos.y, 'target_obj.pos.y + 1 =', target_obj.pos.y + 1)
                    half_dist = int(distance/2)
                    if not half_dist:
                        half_dist = 1
                    # 이번엔 절대값만 안넘기면 된다.
                    # print('abs(target_obj.pos.x - o.pos.x)', abs(target_obj.pos.x - o.pos.x))
                    if half_dist >= abs(target_obj.pos.x - o.pos.x):
                        smth_at_top = True
                        # print('smth_at_top')
                        stop = False
                        break
        # 여기까지 왔으면 아래있는지 확인.
        elif not smth_at_bottom:
            # print('not smth_at_bottom')
            for o in other_objs:
                if target_obj.id == o.id:
                    continue
                # 바로 아래에 있는거만 보면됨
                if o.pos.y == target_obj.pos.y - 1:
                    half_dist = int(distance/2)
                    if not half_dist:
                        half_dist = 1

                    if half_dist >= abs(target_obj.pos.x - o.pos.x):
                        smth_at_bottom = True
                        # print('smth_at_bottom')
                        stop = False
                        break
        # 여기까지 왔으면 사방에 다 뭔가가 있단 소리니...
        else:
            print('else')
            # 우측에 걍 놓는다.
            # print(target_obj.structureType, 'none')
            pass

    # 오른쪽에 놔도 되는가 - 가로막는게 없는가?
    if not smth_at_right:
        return {'x': target_obj.pos.x + 1, 'y': target_obj.pos.y + 0, 'align': left}
    # 왼쪽?
    elif not smth_at_left:
        return {'x': target_obj.pos.x - 1, 'y': target_obj.pos.y + 0, 'align': right}
    elif not smth_at_top:
        return {'x': target_obj.pos.x + 0, 'y': target_obj.pos.y + 1, 'align': center}
    elif not smth_at_bottom:
        return {'x': target_obj.pos.x + 0, 'y': target_obj.pos.y - 1, 'align': center}
    else:
        return {'x': target_obj.pos.x + 1, 'y': target_obj.pos.y + 0, 'align': left}
