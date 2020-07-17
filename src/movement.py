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
def movi(creep, target, range_to=0, reusePath=20, ignore_creeps=False, maxOps=5000, color='#ffffff'):
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
        return move_with_mem(creep, __new__(RoomPosition(25, 25, roomName)), 20)

    # todo 이거 왜 쓴거였지...? 아마도 크립이 컨트롤러 업글 길막 때문인듯...? 조치바람
    # if creep.room.name == roomName and creep.pos.inRangeTo(creep.room.controller, 5):
    #     # return ERR_NO_PATH
    #     return 'yolo'

    result = creep.moveTo(__new__(RoomPosition(25, 25, roomName)),
                          # result = creep.moveTo(Game.rooms[roomName].controller,
                          {'visualizePathStyle': {'stroke': '#ffffff'}, 'reusePath': 15,
                           'range': 21, 'maxOps': 1500, 'ignoreRoads': ignoreRoads})
    return result


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
        return Game.rooms[creep.pos.roomName] \
            .visual.poly(points, {'fill': 'transparent',
                                  'stroke': color, 'lineStyle': 'dashed',
                                  'strokeWidth': .15, 'opacity': .2})
    return ERR_NO_PATH


def get_findPathTo(start, target, target_range=0, ignore_creeps=True):
    """
    findPathTo 를 이용한 길찾기. 다만 방 밖으로 나가는 경우 패스파인더를 돌린다

    :param start: 출발지. 아이디여도 되고 포지션 오브젝트도 됨
    :param target: 목적지. 출발지와 동일
    :param target_range: 거리.
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
                                {'maxOps': 5000, ignoreCreeps: ignore_creeps, 'range': target_range})
        path = _.map(path, lambda p: __new__(RoomPosition(p.x, p.y, start.roomName)))
    else:
        path = \
            PathFinder.search(start, target,
                              {'plainCost': 3, 'swampCost': 6, 'maxOps': 5000,
                               'roomCallback':
                                   lambda room_name:
                                   Costs(room_name, {'trackCreeps': bool(not ignoreCreeps)}).load_matrix()}, ).path

    return path


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


def move_with_mem(creep, target, target_range=0, path_mem='path', repath=True):
    """
    저장된 패스 메모리따라 움직일 모든 코드는 여기에 들어간다.
    움직이려 하는데 안움직이면 앞자리 애랑 교대까지.

    :param creep: 크립
    :param target: 갈 표적 아이디 또는 RoomPosition
    :param target_range: 설명 필요없을듯
    :param path_mem: 메모리에 저장된 길목록 이름. 기본값은 'path'
    :param repath: 도로가 안맞을 시 다시 길찾기를 시도할건가? 기본값 True
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

    # 타겟이 아이디인 경우 pos만 추출
    if typeof(target) == 'string':
        target = Game.getObjectById(target).pos

    # creep.memory.old_target == 이전 목적지의 pos 값. 이동중 목적지 등이 바뀌는 경우를 위해 필요.
    # 크립의 구 목표가 없거나 구 목표와 현 목표 아이디가 일치하지 않는 경우 새 길을 파야 한다.
    if not creep.memory.old_target \
            or not JSON.stringify(creep.memory.old_target) == JSON.stringify(target):
        need_new_path = True
        creep.memory.old_target = target
    # 도로가 없음 만들어야하니.
    elif not creep.memory[path_mem] or not len(path):
        need_new_path = True

    move_by_path = ERR_NOT_FOUND
    counter = 0
    while move_by_path == ERR_NOT_FOUND and counter < 3:
        counter += 1
        # 길 새로 짜야하는 경우 짠다.
        if repath and (need_new_path or not creep.memory[path_mem]):
            path_array = get_findPathTo(creep.pos, target, target_range)
            # 크립 본인의 위치도 길에 포함시킨다.
            path_array.insert(0, creep.pos)
            creep.memory[path_mem] = path_array
            need_new_path = False
            changed_path = True
            path = _.map(creep.memory[path_mem], lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))
        # 여기까지 새 도로가 필요없으면 가지고 있는거 돌려본다.
        move_by_path = creep.moveByPath(path)
        if move_by_path == ERR_NOT_FOUND or move_by_path == ERR_INVALID_ARGS:
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

        # creep.say('mt:' + creep.memory.move_ticks)

        # 세번 못움직이면 바로 길 앞 크립과 위치교체 간다.
        if creep.memory.move_ticks > 3:
            creep_located = False
            for p in path:
                # 이전 길 위에 본 크립 위치를 찾았는지?
                if creep_located and p.lookFor(LOOK_CREEPS):
                    # 찾았으면 그 앞에 크립이 길막중이니 교대한다
                    front_creep = p.lookFor(LOOK_CREEPS)[0]
                    if front_creep and front_creep.my:
                        front_creep.moveTo(creep)
                        move_by_path = creep.moveTo(front_creep)
                        creep.say('교대좀', True)
                    break

                # 현재 포문상 위치가 이 크립의 위치와 동일한가? 그럼 이 위치 다음 크립과 교체하는거임.
                if JSON.stringify(p) == JSON.stringify(creep.pos):
                    creep_located = True
            # 위 포문에서 안걸렸으면 도로 첫위치 바로 옆에있을 가능성이 매우 높음.
            if not creep_located and creep.pos.isNearTo(path[0]):
                if path[0].lookFor(LOOK_CREEPS):
                    # 찾았으면 그 앞에 크립이 길막중이니 교대한다
                    front_creep = p.lookFor(LOOK_CREEPS)[0]
                    if front_creep and front_creep.my:
                        front_creep.moveTo(creep)
                        move_by_path = creep.moveTo(front_creep)
                        creep.say('교대좀', True)

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


def get_bld_upg_path(creep, creeps, target, target_range=3):
    """
    크립이 엉킬걸 대비해서 패스파인딩을 할때 컨트롤러 주변에 있는
    크립들도 장애물로 간주하고 거르기 하기 위한 독자 패스파인딩.
    건설·업글 등 3칸이내로 들어가야 하는 모든 역할이 대상.

    :param creep: 크립 오브젝트
    :param creeps: 방 안 모든 크립스
    :param target: 타겟 오브젝트의 pos 값, 보통은 ID
    :param target_range: 사정거리, 기본값 3
    :return:
    """

    # 오브젝트가 아니면 로딩
    if typeof(target) == 'string':
        target = Game.getObjectById(target).pos
    # todo 크립이 안골라져 있으면 방 안에 모든 크립을 찾는다. 아직 미적용
    # 표적 범위 내에 있는 크립들 중 역할특성상 한곳에 머무는 애 전부
    upgraders = _.filter(creeps,
                         lambda c: c.memory.assigned_room == creep.room.name
                                   and (c.memory.role == 'upgrader' or c.memory.role == 'hauler'
                                        or c.memory.role == 'fixer' or c.memory.role == 'harvester')
                                   and c.pos.inRangeTo(target, target_range + 1))
    opts = {'trackCreeps': False, 'refreshMatrix': True, 'pass_walls': False,
            'costByArea': {'objects': upgraders, 'size': 0, 'cost': 100}}

    # 돌아올 패스 어레이
    path_arr = creep.pos.findPathTo(target,
                                    {'plainCost': 3, 'swampCost': 6, 'ignoreCreeps': True, 'range': 3,
                                     'costCallback':
                                         lambda room_name: Costs(room_name, opts).load_matrix()})
    # 크립 본인의 위치도 길에 포함시킨다.
    path_arr.insert(0, creep.pos)
    return _.map(path_arr, lambda p: __new__(RoomPosition(p.x, p.y, creep.pos.roomName)))


def ranged_move(creep, target, creeps, target_range=3):
    """
    크립들 수리·업글 등 방내에서 사거리가 걸린 일을 할때 접근하는 방법이 동일함.
    그걸 감안해서 이에따른 이동방법을 통일하는 작업

    :param creep:
    :param target: ID 또는 RoomPosition
    :param creeps: 방 안 모든 크립
    :param target_range: 사정거리, 기본값 3
    :return:
    """
    # time1 = Game.cpu.getUsed()
    # id 일 경우 RoomPosition 만 빼간다
    if typeof(target) == 'string':
        target = Game.getObjectById(target).pos

    # target_range * 2 의 값만큼 가까이 들어오지 않았으면 저장된 길을 따라 들어간다
    if not creep.pos.inRangeTo(target, target_range * 2):
        if not creep.memory.path or not JSON.stringify(creep.memory.old_target) == JSON.stringify(target):
            creep.memory.path = get_bld_upg_path(creep, creeps, target)
            # move_with_mem() 과 연동시키기 위한 목적
            creep.memory.old_target = target
        # 독자적인 패스파인딩을 쓰기 때문에 repath 는 거짓
        move_by_path = move_with_mem(creep, target, target_range, 'path', False)
        # 통상적인 다른 move_with_mem 과는 다르게 어차피 두번째 어레이 반환값은 무조건 거짓임
        if move_by_path[0] == OK:
            pass
            # creep.say('ROK')
        # 이게 뜰리가 없긴 하겠다만.. 길 안보인다 뜨면 재시도
        elif move_by_path[0] == ERR_NOT_FOUND:
            creep.memory.path = get_bld_upg_path(creep, creeps, target)
            creep.memory.old_target = target
            move_by_path = move_with_mem(creep, target, target_range, 'path', False)
            creep.say('레인지뭅걸림??')
            if not move_by_path[0] == OK and not move_by_path[0] == ERR_TIRED:
                creep.say('2레인지: {}'.format(move_by_path[0]))
        elif move_by_path[0] == OK and not move_by_path[0] == ERR_TIRED:
            creep.say('1레인지: {}'.format(move_by_path[0]))
    # 만일 target_range * 2 이내 거리면 일반 무브 적용
    elif not creep.pos.inRangeTo(target, target_range):
        if creep.memory.path:
            del creep.memory.path
        movi(creep, target, target_range, 3)
