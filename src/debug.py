from defs import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def debugging_path(creep, path_name, color='white', line_style=undefined):
    """
    크립의 모든 길을 확인하기 위한 스크립트

    :param creep: Game.creeps
    :param path_name: 메모리 안에 저장된 길 목록
    :param color: 무슨 색으로 표기할겨?
    :param line_style: 어떤 스타일의 줄?
    :return:
    """
    # line for to_pickup
    room_list = []
    for i in creep.memory[path_name]:
        # to_pickup 목록에 등장하는 모든 방 확인
        for p in creep.memory[path_name]:
            no_name = True
            # 목록에 하나만 있으면 됨.
            for i in room_list:
                if p.roomName == i:
                    no_name = False
                    break
            if no_name:
                room_list.append(p.roomName)
    path = _.map(creep.memory[path_name], lambda p: __new__(RoomPosition(p.x, p.y, p.roomName)))
    for i in room_list:
        room_path = _.filter(path, lambda p: p.roomName == i)
        Game.rooms[i].visual.poly(room_path, {'fill': 'transparent',
                                  'stroke': color, 'lineStyle': line_style,
                                  'strokeWidth': .15, 'opacity': .8})
        Game.rooms[i].visual.text(creep.name, room_path[int(len(room_path) / 2)], {'color': color, 'font': 0.7})