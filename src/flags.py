from defs import *
import random
import miscellaneous
import pathfinding
from _custom_constants import *
from structure_display import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')

# todo 정리 후 원래 스폰에 있던거 전부 제거요망

# REMOTE---------------------------------------------------------------------------
# ALL remotes.
flags = Game.flags
"""
완성될 시 절차:
- 깃발을 다 둘러본다.
- 자기소속 깃발이 있을 경우 (W1E2-rm) 옵션에 넣는다. 
    + 각종 기본값을 설정한다.
        + 넣을때 기본값으로 주둔시킬 병사 수를 지정한다. 디폴트 0
        + 도로를 또 깔것인가? 길따라 깐다. 디폴트 0 
    + 모든 컨트롤러 있는 방 루프돌려서 이미 소속된 다른방이 있으면 그거 지운다. 
    + 넣고나서 깃발 지운다. 
- 추후 특정 이름이 들어간 깃발은 명령어대로 하고 삭제한다. 

"""
# 메모리화 절차
for flag_name in Object.keys(flags):
    # 해당 플래그 오브젝트. flag_name 은 말그대로 이름뿐임.
    flag_obj = flags[flag_name]
    # 해당 깃발이 내 소속 방에 있는건지 확인
    controlled = False
    if flag_obj.room and flag_obj.room.controller and flag_obj.room.controller.my:
        controlled = True

    # 깃발 명령어 쪼개는데 필요함.
    name_list = flag_name.split()

    # 포문 끝나고 깃발 삭제할지 확인...
    delete_flag = False
    # 깃발이 있는 방이름.
    flag_room_name = flag_obj.pos.roomName

    # 건물 건설 지정.
    if flag_name.includes(STRUCTURE_LINK) or flag_name.includes(STRUCTURE_CONTAINER) \
            or flag_name.includes(STRUCTURE_SPAWN) or flag_name.includes(STRUCTURE_EXTENSION) \
            or flag_name.includes(STRUCTURE_ROAD) or flag_name.includes(STRUCTURE_STORAGE) \
            or flag_name.includes(STRUCTURE_RAMPART) or flag_name.includes(STRUCTURE_EXTRACTOR):
        # todo 미완성임. -del 하고 섞일 수 있음.
        bld_type = name_list[0]
        # 링크용일 경우.
        if bld_type == STRUCTURE_LINK:
            bld_plan = flag_obj.room.createConstructionSite(flag_obj.pos, STRUCTURE_LINK)
        # 컨테이너
        elif bld_type == STRUCTURE_CONTAINER:
            bld_plan = flag_obj.room.createConstructionSite(flag_obj.pos, STRUCTURE_LINK)
        # 스폰
        elif bld_type == STRUCTURE_SPAWN:
            bld_plan = flag_obj.room.createConstructionSite(flag_obj.pos, STRUCTURE_SPAWN)
        # 익스텐션
        elif bld_type == STRUCTURE_EXTENSION:
            bld_plan = flag_obj.room.createConstructionSite(flag_obj.pos, STRUCTURE_EXTENSION)
        # storage
        elif bld_type == STRUCTURE_STORAGE:
            bld_plan = flag_obj.room.createConstructionSite(flag_obj.pos, STRUCTURE_STORAGE)
        # todo 도로랑 램파트는 한번에 쭉 연결하는게 가능함. 그걸 확인해보자.

        print(bld_plan, bld_type)
        # 건설할 건물이 레벨부족 또는 한도초과로 못놓는 경우.
        if bld_plan == ERR_RCL_NOT_ENOUGH or bld_plan == ERR_FULL:
            # 건설용 메모리 초기화
            if not chambro.memory.bld_plan:
                chambro.memory.bld_plan = []
            # 내 방이 아닌 경우 그냥 삭제.
            # todo 멀티방이면 어찌할거임?
            if bld_plan == ERR_RCL_NOT_ENOUGH and not controlled:
                print('the {} cannot be built in {} - not controlled.'.format(bld_type, flag_obj.pos.roomName))
            else:
                print('added bld')
                # json to put into the bld_plan memory
                blds = {'type': bld_type, 'pos': flag_obj.pos}
                chambro.memory.bld_plan.append(blds)

        # 건설이 불가한 경우.
        elif bld_plan == ERR_INVALID_TARGET or bld_plan == ERR_INVALID_ARGS:
            print('building plan at {}x{}y is wrong: {}'.format(flag_obj.pos.x, flag_obj.pos.y, bld_plan))

        delete_flag = True

    # 방이름/방향 + -rm + 아무글자(없어도됨) << 방을 등록한다.
    if flag_name.includes(spawn.room.name) and flag_name.includes("-rm"):
        # 방이름 외 그냥 바로 위라던지 정도의 확인절차
        # wasd 시스템(?) 사용
        rm_loc = name_list.index('-rm')
        target_room = name_list[rm_loc - 1]
        # todo 방향 아직 안찍음
        # 여기에 안뜨면 당연 방이름이 아니라 상대적 위치를 찍은거.
        # if not Game.rooms[target_room]:

        print('includes("-rm")')
        # init. remote
        if not Memory.rooms[spawn.room.name].options.remotes:
            Memory.rooms[spawn.room.name].options.remotes = {}

        # 혹시 다른방에 이 방이 이미 소속돼있는지도 확인한다. 있으면 없앤다.
        for i in Object.keys(Memory.rooms):
            # 같은방은 건들면 안됨...
            if i == spawn.room.name:
                continue
            found_and_deleted = False
            if Memory.rooms[i].options:
                if Memory.rooms[i].options.remotes:
                    # for_num = 0
                    for r in Object.keys(Memory.rooms[i].options.remotes):
                        if r == flag_obj.pos.roomName:
                            del Memory.rooms[i].options.remotes[r]
                            # print('del')
                            found_and_deleted = True
                            break
                        # for_num += 1
            if found_and_deleted:
                break
        # 방이 추가됐는지에 대한 불리언.
        room_added = False
        # 이미 방이 있는지 확인한다.
        for r in Object.keys(Memory.rooms[spawn.room.name].options.remotes):
            # 있으면 굳이 또 추가할 필요가 없음..
            if r.roomName == flag_obj.pos.roomName:
                room_added = True
                break
        print('room added?', room_added)
        # 추가가 안된 상태면 초기화를 진행
        if not room_added:
            print('what??')
            # init = {'roomName': Game.flag_obj.pos.roomName, 'defenders': 1, 'initRoad': 0,
            #         'display': {'x': Game.flag_obj.pos.x, 'y': Game.flag_obj.pos.y}}
            init = {'defenders': 1, 'initRoad': 0,
                    'display': {'x': flag_obj.pos.x,
                                'y': flag_obj.pos.y}}
            Memory.rooms[spawn.room.name][options][remotes][flag_obj.pos.roomName] = init
            # Memory.rooms[spawn.room.name][options][remotes].update({flag_obj.pos.roomName: init})
            print('Memory.rooms[{}][options][remotes][{}]'.format(spawn.room.name,
                                                                  flag_obj.pos.roomName),
                  JSON.stringify(Memory.rooms[spawn.room.name][options][remotes][flag_obj
                                 .pos.roomName]))

        delete_flag = True

    # 주둔할 병사 수 재정의
    if flag_name.includes('-def'):
        print("includes('-def')")
        number_added = False
        included = name_list.index('-def')
        # 초기화
        number = 0
        # 트라이에 걸린다는건 숫자 빼먹었거나 숫자가 아니라는거.
        try:
            number = int(name_list[included + 1])
            number_added = True
        except:
            print("error for flag {}: no number for -def".format(flag_name))

        if number_added:
            # 방을 돌린다.
            for i in Object.keys(Memory.rooms):
                found = False
                # 같은방을 찾으면 병사정보를 수정한다.
                if Memory.rooms[i].options and Memory.rooms[i].options.remotes:
                    for r in Object.keys(Memory.rooms[i].options.remotes):
                        if r == flag_room_name:
                            Memory.rooms[i].options.remotes[r][defenders] = number
                            found = True
                if found:
                    break
        delete_flag = True

    # 방의 수리단계 설정.
    if flag_name.includes('-rp'):
        print("includes('-rp')")

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
            flag_obj.room.memory.options.repair = number
            delete_flag = True

    # 방의 운송크립수 설정.
    if flag_name.includes('-hl'):

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
            flag_obj.room.memory.options.haulers = number
            delete_flag = True

    # 방 안에 미네랄 채취 시작
    if flag_name.includes('-mine'):
        print('-mine')
        # todo 키퍼방일 경우 추가요망. 현재는 내방만.

        if controlled:
            mineral_loc = flag_obj.room.find(FIND_MINERALS)[0]
            # 엑스트랙터 생성
            mineral_loc.pos.createConstructionSite(STRUCTURE_EXTRACTOR)

            road_to_spawn = mineral_loc.pos.findPathTo(spawn, {'ignoreCreeps': True})
            road_len = len(road_to_spawn)
            counter = 0
            # 줄따라 놓기
            for s in road_to_spawn:
                if counter == 0 or counter == road_len:
                    pass
                elif counter == 1:
                    posi = __new__(RoomPosition(s.x, s.y, flag_obj.room.name))
                    posi.createConstructionSite(STRUCTURE_CONTAINER)
                else:
                    posi = __new__(RoomPosition(s.x, s.y, flag_obj.room.name))
                    posi.createConstructionSite(STRUCTURE_ROAD)
                counter += 1
        delete_flag = True

    # 방내 설정값 표기.
    if flag_name.includes('-dsp'):
        print("includes('-dsp')")

        if not controlled:
            # 리모트 소속방 찾는다.
            for chambra_nomo in Object.keys(Game.rooms):
                set_loc = False
                if Memory.rooms[chambra_nomo].options:
                    # counter_num = 0

                    for r in Object.keys(Memory.rooms[chambra_nomo].options.remotes):
                        remote_room_name = r
                        # 방이름 이거랑 똑같은지.
                        # 안똑같으면 통과
                        if remote_room_name != flag_obj.pos.roomName:
                            print('{} != flags[{}].pos.roomName {}'
                                  .format(remote_room_name, flag_name, flag_obj.pos.roomName))
                            pass
                        else:
                            print('Memory.rooms[chambra_nomo].options.remotes[counter_num].display'
                                  , Memory.rooms[chambra_nomo].options.remotes[r].display)
                            if not Memory.rooms[chambra_nomo].options.remotes[r].display:
                                Memory.rooms[chambra_nomo].options.remotes[r].display = {}
                            rx = flag_obj.pos.x
                            ry = flag_obj.pos.y
                            Memory.rooms[chambra_nomo].options.remotes[r].display.x = rx
                            Memory.rooms[chambra_nomo].options.remotes[r].display.y = ry
                            set_loc = True
                        # counter_num += 1
                if set_loc:
                    break

        # 내 방이 아니면 이걸 돌리는 이유가없음....
        if controlled:
            # 만일 비어있으면 값 초기화.
            if not flag_obj.room.memory.options.display:
                flag_obj.room.memory.options.display = {}
            # 깃발꽂힌 위치값 등록.
            print('flagpos {}, {}'.format(flag_obj.pos.x, flag_obj.pos.y))
            flag_obj.room.memory.options.display['x'] = flag_obj.pos.x
            flag_obj.room.memory.options.display['y'] = flag_obj.pos.y
            print('flags[{}].room.memory.options.display {}'
                  .format(flag_name, flag_obj.room.memory.options.display))

        delete_flag = True

    # 방 내 핵채우기 트리거. 예·아니오 토글
    if flag_name.includes('-fln'):
        delete_flag = True

        if controlled:
            if flag_obj.room.memory.options.fill_nuke == 1:
                flag_obj.room.memory.options.fill_nuke = 0
            elif flag_obj.room.memory.options.fill_nuke == 0:
                flag_obj.room.memory.options.fill_nuke = 1
            else:
                flag_obj.room.memory.options.fill_nuke = 0

    # 방 내 연구소 채우기 트리거. 예·아니오 토글
    if flag_name.includes('-fll'):
        delete_flag = True

        if controlled:
            if flag_obj.room.memory.options.fill_labs == 1:
                flag_obj.room.memory.options.fill_labs = 0
            elif flag_obj.room.memory.options.fill_labs == 0:
                flag_obj.room.memory.options.fill_labs = 1
            else:
                flag_obj.room.memory.options.fill_labs = 0

    # 램파트 토글.
    if flag_name.includes('-ram'):

        # 내 방이 아니면 이걸 돌리는 이유가없음....
        if controlled:
            # 램파트가 열렸는가?
            if flag_obj.room.memory.options.ramparts_open == 1:
                # 그럼 닫는다.
                flag_obj.room.memory.options.ramparts = 2
            # 그럼 닫힘?
            elif flag_obj.room.memory.options.ramparts_open == 0:
                # 열어
                flag_obj.room.memory.options.ramparts = 1
            delete_flag = True

    # 타워공격 토글.
    if flag_name.includes('-tow'):
        # 내 방이 아니면 이걸 돌리는 이유가없음....
        if controlled:
            if flag_obj.room.memory.options.tow_atk == 1:
                flag_obj.room.memory.options.tow_atk = 0
            else:
                flag_obj.room.memory.options.tow_atk = 1
            delete_flag = True

    # 디스플레이 제거. 쓸일은 없을듯 솔까.
    if flag_name.includes('-dsprm'):

        # 내 방이 아니면 이걸 돌리는 이유가없음....
        if controlled:
            # 깃발꽂힌 위치값 제거.
            flag_obj.room.memory.options.display = {}
            delete_flag = True

    # 방 안 건설장 다 삭제..
    if flag_name.includes('-clr'):
        print("includes('-clr')")
        # cons = Game.flag_obj.room.find(FIND_CONSTRUCTION_SITES)
        world_const = Game.constructionSites
        for c in Object.keys(world_const):
            obj = Game.getObjectById(c)
            if obj.pos.roomName == flag_room_name:
                obj.remove()
        # 원하는거 찾았으면 더 할 이유가 없으니.
        if found:
            break
        delete_flag = True

    # remote 배정된 방 삭제조치. 자기 방에서 했을 경우 해당 위치에 배정된 건물을 지운다.
    if flag_name.includes('-del'):
        print("includes('-del')")
        # 자기 방으로 찍었을 경우 찍은 위치에 뭐가 있는지 확인하고 그걸 없앤다.
        if flag_obj.room and flag_obj.room.controller \
                and flag_obj.room.controller.my:
            print('my room at {}'.format(flag_obj.room.name))
            # 해당 위치에 건설장 또는 건물이 있으면 없앤다.
            if len(flag_obj.pos.lookFor(LOOK_CONSTRUCTION_SITES)):
                print(flag_obj.pos.lookFor(LOOK_CONSTRUCTION_SITES), JSON.stringify())
                del_res = flag_obj.pos.lookFor(LOOK_CONSTRUCTION_SITES)[0].remove()
            elif len(flag_obj.pos.lookFor(LOOK_STRUCTURES)):
                del_res = flag_obj.pos.lookFor(LOOK_STRUCTURES)[0].destroy()
            # 만약 건물도 건설장도 없으면 해당 위치에 배정된 건설 메모리가 있나 찾아본다
            elif chambro.memory.bld_plan:
                num = 0
                for plan in chambro.memory.bld_plan:
                    if JSON.stringify(plan.pos) == JSON.stringify(flag_obj.pos):
                        chambro.memory.bld_plan.splice(num, 1)
                        print('deleted!')
                    num += 1
        # if its remote room
        else:
            # 방을 돌린다.
            for i in Object.keys(Memory.rooms):
                found = False
                if Memory.rooms[i].options:
                    print('Memory.rooms[{}].options.remotes {}'.format(i, JSON.stringify(
                        Memory.rooms[i].options.remotes)))
                    print('len(Memory.rooms[{}].options.remotes) {}'.format(i, len(
                        Memory.rooms[i].options.remotes)))
                    # 옵션안에 리모트가 없을수도 있음.. 특히 확장 안했을때.
                    if len(Memory.rooms[i].options.remotes) > 0:
                        # 리모트 안에 배정된 방이 있는지 확인한다.
                        # 아래 포문에 씀.
                        del_number = 0
                        for r in Object.keys(Memory.rooms[i].options.remotes):
                            print('r', r, 'flag_room_name', flag_room_name)
                            # 배정된 방을 찾으면 이제 방정보 싹 다 날린다.
                            if r == flag_room_name:
                                # del_number = r  # Memory.rooms[i].options.remotes[r]
                                print('deleting roomInfo Memory.rooms[{}].options.remotes[{}]'
                                      .format(i, r), 'del_number', del_number)
                                # Memory.rooms[i].options.remotes.splice(del_number, 1)
                                del Memory.rooms[i].options.remotes[r]
                                found = True
                                # 방에 짓고있는것도 다 취소
                                world_const = Game.constructionSites
                                for c in Object.keys(world_const):
                                    obj = Game.getObjectById(c)
                                    if obj.pos.roomName == flag_room_name:
                                        obj.remove()
                                # if Game.flag_obj.room:
                                #     cons = Game.flag_obj.room.find(FIND_CONSTRUCTION_SITES)
                                #     for c in cons:
                                #         c.remove()
                                break
                            del_number += 1
                # 원하는거 찾았으면 더 할 이유가 없으니.
                if found:
                    break
        delete_flag = True

    # 방 안에 건물확인 스크립트 초기화 조치
    if flag_name.includes('-rset'):
        print("resetting")
        if controlled:
            chambro.memory[options][reset] = 1
        else:
            print(flag_obj.room.name, '은 내 방이 아님.')
        delete_flag = True

    if delete_flag:
        aa = flag_obj.remove()
        print('delete {}: {}'.format(flag_obj, aa))
