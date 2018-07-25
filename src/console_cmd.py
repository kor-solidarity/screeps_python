from defs import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')

"""
이 작업이 하는 짓: 
제목대로 콘솔 명령어를 이행한다. 깃발갖고 한걸 이걸로 옮기는 사업인 셈.

"""

def find_room(obj):
    # is this id?
    if Game.getObjectById(obj):
        return Game.getObjectById(obj).pos.roomName
    else:
        # 이름인가?
        for creep in Object.keys(Game.creeps):
            if obj.lower() == creep.lower():
                return Game.creeps[creep].pos.roomName
        # 스폰이름인가?
        for spawn in Object.keys(Game.spawns):
            if obj.lower() == spawn.lower():
                return Game.spawns[spawn].pos.roomName
        # 방이름인가?



def command(map_obj, cmd):
    for flag_name in Object.keys(flags):
        # 포문 끝나고 깃발 삭제할지 확인...
        delete_flag = False
        # 깃발이 있는 방이름.
        flag_room_name = flags[flag_name].pos.roomName

        # 방이름 + -rm + 아무글자(없어도됨) << 방을 등록한다.
        if flag_name.includes(spawn.room.name) and flag_name.includes("-rm"):
            print('includes("-rm")')
            # init. remote
            if not Memory.rooms[spawn.room.name].options.remotes:
                Memory.rooms[spawn.room.name].options.remotes = []

            # 혹시 다른방에 이 방이 이미 소속돼있는지도 확인한다. 있으면 없앤다.
            for i in Object.keys(Memory.rooms):
                # 같은방은 건들면 안됨...
                if i == spawn.room.name:
                    continue
                found_and_deleted = False
                if Memory.rooms[i].options:
                    print('? yolo?')
                    if Memory.rooms[i].options.remotes:
                        for r in Memory.rooms[i].options.remotes:
                            if r.roomName == Game.flags[flag_name].room.name:
                                del r
                                found_and_deleted = True
                                break
                if found_and_deleted:
                    break
            # 방이 추가됐는지에 대한 불리언.
            room_added = False
            # 이미 방이 있는지 확인한다.
            for r in Memory.rooms[spawn.room.name].options.remotes:
                # 있으면 굳이 또 추가할 필요가 없음..
                if r.roomName == Game.flags[flag_name].pos.roomName:
                    room_added = True
                    break
            print('room added?', room_added)
            # 추가가 안된 상태면 초기화를 진행
            if not room_added:
                init = {'roomName': Game.flags[flag_name].pos.roomName, 'defenders': 1, 'initRoad': 0,
                        'display': {'x': Game.flags[flag_name].pos.x, 'y': Game.flags[flag_name].pos.y}}
                Memory.rooms[spawn.room.name].options.remotes.append(init)

            delete_flag = True

        # 아래부터 값을 쪼개는데 필요함.
        name_list = flag_name.split()

        # 주둔할 병사 수 재정의
        if flag_name.includes('-def'):
            print("includes('-def')")
            number_added = False
            included = name_list.index('-def')
            # 트라이에 걸린다는건 숫자 빼먹었거나 숫자가 아니라는거.
            try:
                number = name_list[included + 1]
                number = int(number)
                number_added = True
            except:
                print("error for flag {}: no number for -def".format(flag_name))

            if number_added:
                # 방을 돌린다.
                for i in Object.keys(Memory.rooms):
                    found = False
                    # 같은방을 찾으면 병사정보를 수정한다.
                    if Memory.rooms[i].options.remotes:
                        for r in Memory.rooms[i].options.remotes:
                            if r.roomName == flag_room_name:
                                r.defenders = number
                                found = True
                    if found:
                        break
            delete_flag = True

        # 방의 수리단계 설정.
        if flag_name.includes('-rp'):
            print("includes('-rp')")
            # 내 방 맞음?
            controlled = False
            if flags[flag_name].room.controller:
                if flags[flag_name].room.controller.my:
                    controlled = True

            # 내 방이 아니면 이걸 돌리는 이유가없음....
            if controlled:
                included = name_list.index('-rp')
                # 트라이에 걸린다는건 숫자 빼먹었거나 숫자가 아니라는거.
                try:
                    number = name_list[included + 1]
                    number = int(number)
                    print('repair', number)
                except:
                    print("error for flag {}: no number for -rp".format(flag_name))
                # 설정 끝.
                flags[flag_name].room.memory.options.repair = number
                delete_flag = True

        # 방의 운송크립수 설정.
        if flag_name.includes('-hl'):
            # 내 방 맞음?
            controlled = False
            if flags[flag_name].room.controller:
                if flags[flag_name].room.controller.my:
                    controlled = True

            # 내 방이 아니면 이걸 돌리는 이유가없음....
            if controlled:
                included = name_list.index('-hl')
                # 트라이에 걸린다는건 숫자 빼먹었거나 숫자가 아니라는거.
                try:
                    number = name_list[included + 1]
                    number = int(number)
                except:
                    print("error for flag {}: no number for -hl".format(flag_name))
                # 설정 끝.
                flags[flag_name].room.memory.options.haulers = number
                delete_flag = True

        # 방내 설정값 표기.
        if flag_name.includes('-dsp'):
            print("includes('-dsp')")
            # 내 방 맞음?
            controlled = False
            if flags[flag_name].room and flags[flag_name].room.controller:
                if flags[flag_name].room.controller.my:
                    controlled = True
                # 아니면 리모트임.
                else:
                    # 리모트 소속방 찾는다.
                    for chambra_nomo in Object.keys(Game.rooms):
                        set_loc = False
                        if Memory.rooms[chambra_nomo].options:
                            counter_num = 0
                            for r in Memory.rooms[chambra_nomo].options.remotes:
                                remote_room_name = r.roomName
                                # 방이름 이거랑 똑같은지.
                                # 안똑같으면 통과
                                if remote_room_name != flags[flag_name].pos.roomName:
                                    print('{} != flags[{}].pos.roomName {}'
                                          .format(remote_room_name, flag_name, flags[flag_name].pos.roomName))
                                    pass
                                else:
                                    print('Memory.rooms[chambra_nomo].options.remotes[counter_num].display'
                                          , Memory.rooms[chambra_nomo].options.remotes[counter_num].display)
                                    if not Memory.rooms[chambra_nomo].options.remotes[counter_num].display:
                                        Memory.rooms[chambra_nomo].options.remotes[counter_num].display = {}
                                    rx = flags[flag_name].pos.x
                                    ry = flags[flag_name].pos.y
                                    Memory.rooms[chambra_nomo].options.remotes[counter_num].display.x = rx
                                    Memory.rooms[chambra_nomo].options.remotes[counter_num].display.y = ry
                                    set_loc = True
                                counter_num += 1
                        if set_loc:
                            break
            delete_flag = True

            # 내 방이 아니면 이걸 돌리는 이유가없음....
            if controlled:
                # 만일 비어있으면 값 초기화.
                if not flags[flag_name].room.memory.options.display:
                    flags[flag_name].room.memory.options.display = {}
                # 깃발꽂힌 위치값 등록.
                print('flagpos {}, {}'.format(flags[flag_name].pos.x, flags[flag_name].pos.y))
                flags[flag_name].room.memory.options.display['x'] = flags[flag_name].pos.x
                flags[flag_name].room.memory.options.display['y'] = flags[flag_name].pos.y
                print('flags[{}].room.memory.options.display {}'
                      .format(flag_name, flags[flag_name].room.memory.options.display))

                delete_flag = True

        # 방 내 핵채우기 트리거. 예·아니오 토글
        if flag_name.includes('-fln'):
            delete_flag = True
            # 내 방 맞음?
            controlled = False
            if flags[flag_name].room.controller:
                if flags[flag_name].room.controller.my:
                    controlled = True

            if controlled:
                if flags[flag_name].room.memory.options.fill_nuke == 1:
                    flags[flag_name].room.memory.options.fill_nuke = 0
                elif flags[flag_name].room.memory.options.fill_nuke == 0:
                    flags[flag_name].room.memory.options.fill_nuke = 1
                else:
                    flags[flag_name].room.memory.options.fill_nuke = 0

        # 방 내 연구소 채우기 트리거. 예·아니오 토글
        if flag_name.includes('-fll'):
            delete_flag = True
            # 내 방 맞음?
            controlled = False
            if flags[flag_name].room.controller:
                if flags[flag_name].room.controller.my:
                    controlled = True

            if controlled:
                if flags[flag_name].room.memory.options.fill_labs == 1:
                    flags[flag_name].room.memory.options.fill_labs = 0
                elif flags[flag_name].room.memory.options.fill_labs == 0:
                    flags[flag_name].room.memory.options.fill_labs = 1
                else:
                    flags[flag_name].room.memory.options.fill_labs = 0

        # 램파트 토글.
        if flag_name.includes('-ram'):
            # 내 방 맞음?
            controlled = False
            if flags[flag_name].room.controller:
                if flags[flag_name].room.controller.my:
                    controlled = True

            # 내 방이 아니면 이걸 돌리는 이유가없음....
            if controlled:
                # 램파트가 열렸는가?
                if flags[flag_name].room.memory.options.ramparts_open == 1:
                    # 그럼 닫는다.
                    flags[flag_name].room.memory.options.ramparts = 2
                # 그럼 닫힘?
                elif flags[flag_name].room.memory.options.ramparts_open == 0:
                    # 열어
                    flags[flag_name].room.memory.options.ramparts = 1
                delete_flag = True

        # 타워공격 토글.
        if flag_name.includes('-tow'):
            # 내 방 맞음?
            controlled = False
            if flags[flag_name].room.controller:
                if flags[flag_name].room.controller.my:
                    controlled = True
            # 내 방이 아니면 이걸 돌리는 이유가없음....
            if controlled:
                if flags[flag_name].room.memory.options.tow_atk == 1:
                    flags[flag_name].room.memory.options.tow_atk = 0
                else:
                    flags[flag_name].room.memory.options.tow_atk = 1
                delete_flag = True

        # 디스플레이 제거. 쓸일은 없을듯 솔까.
        if flag_name.includes('-dsprm'):
            # 내 방 맞음?
            controlled = False
            if flags[flag_name].room.controller:
                if flags[flag_name].room.controller.my:
                    controlled = True

            # 내 방이 아니면 이걸 돌리는 이유가없음....
            if controlled:
                # 깃발꽂힌 위치값 제거.
                flags[flag_name].room.memory.options.display = {}
                delete_flag = True

        # 방 안 건설장 다 삭제..
        if flag_name.includes('-clr'):
            print("includes('-clr')")
            cons = Game.flags[flag_name].room.find(FIND_CONSTRUCTION_SITES)

            for c in cons:
                c.remove()
            # 원하는거 찾았으면 더 할 이유가 없으니.
            if found:
                break
            delete_flag = True

        # remote 배정된 방 삭제조치.
        if flag_name.includes('-del'):
            print("includes('-del')")
            # 리모트가 아니라 자기 방으로 잘못 찍었을 경우 그냥 통과한다.
            if Game.flags[flag_name].room and Game.flags[flag_name].room.controller \
                and Game.flags[flag_name].room.controller.my:
                pass
            else:
                # 방을 돌린다.
                for i in Object.keys(Memory.rooms):
                    found = False
                    if Memory.rooms[i].options:
                        # print('Memory.rooms[{}].options.remotes {}'.format(i, Memory.rooms[i].options.remotes))
                        # 옵션안에 리모트가 없을수도 있음.. 특히 확장 안했을때.
                        if len(Memory.rooms[i].options.remotes) > 0:
                            # 리모트 안에 배정된 방이 있는지 확인한다.
                            for r in Memory.rooms[i].options.remotes:
                                # print('r', r)
                                # 배정된 방을 찾으면 이제 방정보 싹 다 날린다.
                                if r.roomName == flag_room_name:
                                    del_number = Memory.rooms[i].options.remotes.index(r)
                                    print(
                                        'deleting roomInfo Memory.rooms[{}].options.remotes[{}]'
                                            .format(i, del_number))
                                    Memory.rooms[i].options.remotes.splice(del_number, 1)
                                    found = True
                                    # 방에 짓고있는것도 다 취소
                                    if Game.flags[flag_name].room:
                                        cons = Game.flags[flag_name].room.find(FIND_CONSTRUCTION_SITES)
                                        for c in cons:
                                            c.remove()
                    # 원하는거 찾았으면 더 할 이유가 없으니.
                    if found:
                        break
            delete_flag = True

        if delete_flag:
            aa = flags[flag_name].remove()