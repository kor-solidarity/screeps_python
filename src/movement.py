from defs import *
from pathfinding import *
from _custom_constants import *
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
def movi(creep, target, range_to=0, reusePath=20, ignore_creeps=False, maxOps=3000, color='#ffffff'):
    """
    크립 움직이는거 관련.

    :param creep: 크립
    :param target: 목표 ID, or RoomPosition
    :param range_to: 거리, 기본값 1
    :param reusePath: 재사용틱, 기본값 20
    :param ignore_creeps: 크립무시여부, 기본값 False
    :param maxOps: 패스파인딩 할때 돌릴 시뮬 수. 기본값 2천
    :param color: 기본값 #ffffff
    :return: 결과
    """

    if typeof(target) == 'string':
        target_obj = Game.getObjectById(target)
    else:
        # print('els')
        target_obj = target

    # 아래 moveTo()를 무조건 실행하면 생CPU 0.2가 나가니 그거 방지용도임.
    if creep.pos.isEqualTo(target_obj):
        return OK

    return creep.moveTo(target_obj, {'range': range_to, ignoreCreeps: ignore_creeps,
                                     'visualizePathStyle': {'stroke': color},
                                     'reusePath': reusePath, 'maxOps': maxOps})


# noinspection PyPep8Naming
def get_to_da_room(creep, roomName, ignoreRoads=False):
    """
    특정 방으로 무작정 보내기.
    갈때는 시리얼화된 길 타고 간다

    :param creep:
    :param roomName: 가려고 하는 방이름.
    :param ignoreRoads: 기본값 참.
    :return:
    """
    # 이 명령이 목적 방에서도 도는 경우 단순히 시야확보 등의 발령목적으로 보내버리는거기 때문에
    # 방 안에 있으면 무조건 ignoreRoads가 참이여야함
    if creep.room.name == roomName:
        ignoreRoads = True
    # 방 안에 없는 경우 길 저장해서 간다
    else:
        path = []
        if creep.memory.path:
            path = _.map(creep.memory.path, lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))
        return move_with_mem(creep, __new__(RoomPosition(25, 25, roomName)), 20, path)

    if creep.room.name == roomName and creep.pos.inRangeTo(creep.room.controller, 5):
        # return ERR_NO_PATH
        return 'yolo'

    result = creep.moveTo(__new__(RoomPosition(25, 25, roomName)),
    # result = creep.moveTo(Game.rooms[roomName].controller,
                          {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 15,
                           'range': 21, 'maxOps': 1000, 'ignoreRoads': ignoreRoads})
    return result


def check_loc_and_swap_if_needed(creep, creeps, avoid_id=False, avoid_role=False, path=[]):
    """
    크립이 현위치에 계속 있는지 확인.
    안움직였으면 카운터 올리고 다섯번 넘기면 주변에 있는 크립 하나랑 위치교체한다.
    이 옵션을 쓴다면 move_ticks, cur_loc, last_swap 이 메모리들을 가지고 다녀야 함.
    또한 이건 여기서만 쓰기 때문에 이 안에서 다 처리한다.

    :param creep:
    :param creeps:
    :param avoid_id:
    :param avoid_role:
    :param path: [RoomPosition] 지정된 길로 가고있는 경우 그걸 감안해야함.
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
        # 만일 길따라 가고 있는 경우가 아니면 스와핑.
        if not len(path):
            # 아래만 단독으로 돌릴일이... 있긴 할라나? 어쨌건 우선 그리 돌림
            return swapping(creep, creeps, avoid_id, avoid_role)
        # 길따라 가는 경우면 길앞에 있는애랑 교대
        else:
            creep_located = False
            for p in path:
                # 길위에 크립 위치를 찾았는지?
                if creep_located:
                    for i in p.look():
                        # 앞에 크립이 존재하고 그게 내꺼면 교대.
                        if i.type == 'creep' and i.creep.my:
                            Game.getObjectById(i.creep.id).moveTo(creep)
                            creep.moveTo(Game.getObjectById(i.creep.id))
                            creep.say('GTFO', True)
                            break
                    break
                if p == creep.pos:
                    creep_located = True

    else:
        return OK


def draw_path(creep, path_arr, color='white'):
    """
    크립의 길이 저장된 경우 크립위치에서 해당 길까지 줄을 긋는다.

    :param creep:
    :param path_arr: RoomPosition 어레이
    :param color: 줄 그릴 색
    :return:
    """
    creep_pos_checked = False
    # 줄이 찍힐 RoomPosition 목록
    points = []

    for p in path_arr:
        # 같은 방에 있는거만 그린다
        if not p.roomName == creep.pos.roomName:
            continue
        # 크립이 있는 곳을 찍는다.
        if not creep_pos_checked and JSON.stringify(creep.pos) == JSON.stringify(p):
            creep_pos_checked = True
        elif creep_pos_checked:
            points.append(p)

    if len(points) > 1:
        return Game.rooms[creep.pos.roomName]\
            .visual.poly(points, {'fill': 'transparent',
                                  'stroke': color, 'lineStyle': 'dashed',
                                  'strokeWidth': .15, 'opacity': .2})
    return ERR_NO_PATH


def get_findPathTo(start, target, range=0, ignore_creeps=True):
    """
    findPathTo 를 이용한 길찾기
    todo 이거 패스파인딩으로 완전히 바꿉시다.

    :param start: 출발지. 아이디여도 되고 포지션 오브젝트도 됨
    :param target: 목적지. 출발지와 동일
    :param range: 거리.
    :param ignore_creeps: 크립을 무시하는가? 통상은 무조건 무시한다.
    :return:
    """
    if typeof(start) == 'string':
        start = Game.getObjectById(start)
    if typeof(target) == 'string':
        target = Game.getObjectById(target)
    if start.pos:
        start = start.pos
    if target.pos:
        target = target.pos

    # 같은 방일 경우 이걸 쓰고, 아니면 패스파인더 호출한다.
    if start.roomName == target.roomName:
        path = start.findPathTo(target,
                                {'maxOps': 5000, ignoreCreeps: ignore_creeps, 'range': range})
        path = _.map(path, lambda p: __new__(RoomPosition(p.x, p.y, start.roomName)))
    else:
        path = PathFinder.search(start, target,
                                 {'plainCost': 2, 'swampCost': 6,
                                  'roomCallback':
                                      lambda room_name:
                                      Costs(room_name, {}).load_matrix()},).path

    return path


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
    if creep.memory._move and not creep.memory._move['path']:
        del creep.memory._move
    if avoid_id:
        del avoid_id
    return ERR_NO_PATH


def pathfinder_for_creep(creep, creeps, target, ignore_creeps=True):
    """
    패스파인딩을 다 여기로 통합.

    :param creep:
    :param creeps:
    :param target:
    :param ignore_creeps:
    :return:
    """
    pass


# todo MUST BE NULLIFIED - outdated and inefficient
def move_using_swap(creep, creeps, target, ignore_creeps=True, reuse_path=40,
                    avoid_id=False, avoid_role=False, ranged=0):
    """
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
        print('ranged > 0 and ')
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
        # print('target', target)
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


# todo path=[] 부분 제거요망
def move_with_mem(creep, target, target_range=0, path=[], path_mem='path', repath=True, pathfinder=False):
    """
    저장된 패스 메모리따라 움직일 모든 코드는 여기에 들어간다.
    움직이려 하는데 안움직이면 앞자리 애랑 교대까지.

    :param creep: 크립
    :param target: 갈 표적 아이디 또는 RoomPosition
    :param target_range: 설명 필요없을듯
    :param path: 최초 지정된 길. 존재하면 사용. 보통 creep.memory.path 에서 알아서 뽑아감
    :param path_mem: 메모리에 저장된 길목록 이름. 기본값은 'path'
    :param repath: 도로가 안맞을 시 다시 길찾기를 시도할건가? 기본값 True
    :param pathfinder: 패스파인더를 쓸지 여부. 안쓰면 그냥 findPathTo 쓰는거. 당장은 안넣는걸로.
    :return: [결과값(int), 길이 교체됬는지 확인여부(bool), 최종적으로 쓰인 길(list)]
    """

    # creep.memory[path_mem] 에 저장되있는 RoomPosition 어레이값
    path = []
    # path 반환 용도
    changed_path = False
    # 새 길을 찾아야 하는가
    need_new_path = False

    # path_mem 메모리가 있나 확인해보고 path값에 대입해 넣는다
    if creep.memory[path_mem]:
        path = _.map(creep.memory[path_mem], lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))
    # 없으면 새 길 파야함.
    else:
        need_new_path = True
    # NULLIFIED - 패스가 없으면 무작정 넘기는게 아님
    # 새 길을 찾아야 하는가
    # need_new_path = False
    # if not len(path):
    #     changed_path = True
    # # path 반환 용도
    # else:
    #     changed_path = False

    # if creep.memory.path:
    #     print(creep.name, 'creep.memory.path[0]', creep.memory.path[0], typeof(creep.memory.path[0]), typeof(path[0]))
    # 타겟이 아이디인 경우 pos만 추출
    if typeof(target) == 'string':
        target = Game.getObjectById(target).pos

    # creep.memory.old_target == 이전 목적지의 pos 값. 이동중 목적지 등이 바뀌는 경우를 위해 필요.
    # 크립의 구 목표가 없거나 구 목표와 현 목표 아이디가 일치하지 않는 경우 새 길을 파야 한다.
    if not creep.memory.old_target or not JSON.stringify(creep.memory.old_target) == JSON.stringify(target):
        need_new_path = True
        creep.memory.old_target = target
    # 도로가 없음 만들어야하니.
    elif not creep.memory[path_mem] or not len(path):
        need_new_path = True

    move_by_path = ERR_NOT_FOUND
    counter = 0
    while move_by_path == ERR_NOT_FOUND and counter < 3:
        counter += 1
        # 길 새로 안짜는거면 패스파인딩 과정 자체를 거른다.
        if not repath:
            pass
        # 길 새로 짜야하는 경우 짠다.
        elif need_new_path or not creep.memory[path_mem]:
            path_array = get_findPathTo(creep.pos, target, target_range)
            # print(JSON.stringify(path_array))
            path_array.insert(0, creep.pos)

            creep.memory[path_mem] = path_array
            need_new_path = False
            changed_path = True
            path = _.map(creep.memory[path_mem], lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))
        # 여기까지 새 도로가 필요없으면 가지고 있는거 돌려본다.
        move_by_path = creep.moveByPath(path)
        if move_by_path == ERR_NOT_FOUND or move_by_path == ERR_INVALID_ARGS:
            # print('typeof(path): {}, move_by_path: {}'
            #       .format(bool(typeof(path) == 'object'), move_by_path))  # True
            if creep.memory.debug:
                print(creep.name, 'ERR_NOT_FOUND {} {}x{}y'.format(creep.pos.roomName, creep.pos.x, creep.pos.y))
            # 도로 새로 찾는게 아니면 여기서 끝
            if not repath:
                return move_by_path, False, path
            del creep.memory[path_mem]
    if move_by_path == ERR_TIRED:
        pass
    elif not move_by_path == OK:
        creep.say("mwm {}".format(move_by_path))

    # OK가 떠도 실제로 움직였나 확인한다.
    elif move_by_path == OK:

        # 현 위치에서 움직이지 않고 있는지 확인하기 위한 메모리
        if not creep.memory.move_ticks:
            creep.memory.move_ticks = 1
        # checking current location - only needed when check in par with move_ticks
        if not creep.memory.cur_loc:
            creep.memory.cur_loc = creep.pos

        # 현재 크립위치와 대조해본다. 동일하면 move_ticks 에 1 추가 아니면 1로 초기화.
        if JSON.stringify(creep.memory.cur_loc) == JSON.stringify(creep.pos):
            creep.memory.move_ticks += 1
        else:
            # 안 동일하면 초기화.
            creep.memory.move_ticks = 1
            creep.memory.cur_loc = creep.pos

        # 세번 못움직이면 바로 길 앞 크립과 위치교체 간다.
        if creep.memory.move_ticks > 3:
            creep_located = False
            for p in path:
                # 이전 길 위에 본 크립 위치를 찾았는지?
                if creep_located:
                    # print('creep_located')
                    for i in p.look():
                        # print(JSON.stringify(i))
                        # 앞에 크립이 존재하고 그게 내꺼면 교대.
                        if i.type == 'creep' and i.creep.my:
                            Game.getObjectById(i.creep.id).moveTo(creep)
                            move_by_path = creep.moveTo(Game.getObjectById(i.creep.id))
                            creep.say('교대좀', True)
                            break
                    break

                # 현재 포문상 위치가 이 크립의 위치와 동일한가? 그럼 이 위치 다음 크립과 교체하는거임.
                if JSON.stringify(p) == JSON.stringify(creep.pos):
                    creep_located = True

        # 혹시 패스가 크립위가 아니라 바로 옆에 있어서 패스 안겹치는 경우가 있으면 맨 앞에 크립위치 패스에 추가함.
        mem_in_path = False
        for p in path:
            if JSON.stringify(creep.pos) == JSON.stringify(p):
                mem_in_path = True
                break
        if not mem_in_path:
            if creep.pos.isNearTo(__new__(RoomPosition(path[0].x, path[0].y, path[0].roomName))):
                path.insert(0, __new__(RoomPosition(creep.pos.x, creep.pos.y, creep.pos.roomName)))
    if len(path):
        path_res = draw_path(creep, path)

    return move_by_path, changed_path, path


def get_bld_upg_path(creep, creeps, target):
    """
    크립이 엉킬걸 대비해서 패스파인딩을 할때 컨트롤러 주변에 있는
    크립들도 장애물로 간주하고 거르기 하기 위한 독자 패스파인딩.
    건설·업글 등 3칸이내로 들어가야 하는 모든 역할이 대상.

    :param creep: 크립 오브젝트
    :param creeps: 방 안 모든 크립스
    :param target: 타겟 오브젝트, 보통은 ID
    :return:
    """

    # 오브젝트가 아니면 로딩
    if typeof(target) == 'string':
        target = Game.getObjectById(target)
    # 표적 범위 내에 있는 크립들 중 역할특성상 한곳에 머무는 애 전부
    upgraders = _.filter(creeps,
                         lambda c: c.memory.assigned_room == creep.room.name
                         and (c.memory.role == 'upgrader' or c.memory.role == 'hauler'
                              or c.memory.role == 'fixer' or c.memory.role == 'harvester')
                         and c.pos.inRangeTo(target, 4))
    # print(upgraders)
    opts = {'trackCreeps': False, 'refreshMatrix': True, 'pass_walls': False,
            'costByArea': {'objects': upgraders, 'size': 0, 'cost': 100}}

    # 돌아올 패스 어레이
    path_arr = creep.pos.findPathTo(target,
                                 {'plainCost': 2, 'swampCost': 3, 'ignoreCreeps': True, 'range': 3,
                                  'costCallback':
                                      lambda room_name: Costs(room_name, opts).load_matrix()})

    return _.map(path_arr, lambda p: __new__(RoomPosition(p.x, p.y, creep.pos.roomName)))
