from defs import *
from typing import List
from structure_display import *
import random

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_tower(tower, hostile_creeps, repairs, wounded):
    """

    :param tower:
    :param all_structures: tower.room.find(FIND_STRUCTURES)
    :param creeps: tower.room.find(FIND_MY_CREEPS)
    :param hostile_creeps: tower.room.find(FIND_HOSTILE_CREEPS)
    :param repairs: repair stuffs.
    :param wounded:
    :return:
    """
    # tower havas du laborojn.
    # 1. serĉas por malamikoj kaj morti ilin.
    # 2. heal creeps. and then 3
    # 3. se tie ne estas malamikojn, serĉas por konstruaĵoj kiu bezonas repari kaj repari ĝin.

    # 타워에 에너지가 25% 미만이고 적 또는 치료해야 할 아군이 없으면 통과한다.
    if tower.store.getUsedCapacity(RESOURCE_ENERGY) < tower.store.getCapacity(RESOURCE_ENERGY) * 0.25 and \
            len(hostile_creeps) == 0 and len(wounded) == 0:
        return

    if tower.room.memory.options.tow_atk and len(hostile_creeps) > 0 and len(wounded) > 0:
        flip = random.randint(0, 1)
        if flip == 1:
            closest_wounded = tower.pos.findClosestByRange(wounded)
            tower.heal(closest_wounded)
        else:
            hostile_creep = tower.pos.findClosestByRange(hostile_creeps)
            tower.attack(hostile_creep)
    elif tower.room.memory.options.tow_atk and len(hostile_creeps) > 0:
        hostile_creep = tower.pos.findClosestByRange(hostile_creeps)
        tower.attack(hostile_creep)
    elif len(wounded) > 0:
        closest_wounded = tower.pos.findClosestByRange(wounded)
        tower.heal(closest_wounded)
    else:
        if tower.store.getUsedCapacity(RESOURCE_ENERGY) < tower.store.getCapacity(RESOURCE_ENERGY) * 0.25:
            return
        # 타워는 수리 최후의 보루다. 당장 수리 안하면 박살날 위기에 처해지지 않는 이상 안건든다.
        else:
            repair = tower.pos.findClosestByRange(repairs)
            tower.repair(repair)


def run_links(link_id, objs_for_disp):
    """
    distributing energy to links

    :param link_id: room.memory[STRUCTURE_LINK][i].id
    :param objs_for_disp:
    :return:
    """

    link: StructureLink = Game.getObjectById(link_id)

    # if link.room.controller.level >= 7:
    # 쏘기 시작하는 최저수량. 무조건 꽉찼을때 지른다.
    amount_to_shoot = 800

    # current link
    me = _.filter(Game.getObjectById(link_id).room.memory[STRUCTURE_LINK],
                  lambda l: l.id == link_id)[0]

    display_loc = display_location(link, objs_for_disp, 3)
    align = display_loc['align']
    # if link.pos.x > 44:
    #     align = 'right'
    # else:
    #     align = 'left'

    # 저장용 링크인건가?
    if me.for_store:
        # 만일 링크에 에너지가 있으면 표시한다. 굳이 눌러볼 필요 없게.
        if link.store.getUsedCapacity(RESOURCE_ENERGY) > 0:
            link.room.visual.text(' {}'.format(link.store.getUsedCapacity(RESOURCE_ENERGY)),
                                  link.pos.x, display_loc.y,
                                  {'align': align, 'color': '#EE5927'})
        return

    # 여기 밑으로 내려왔으면 해당 링크는 에너지 전송용이다.
    link.room.visual.text('{}|{}'.format(link.store.getUsedCapacity(RESOURCE_ENERGY), link.cooldown),
                          link.pos.x, display_loc.y,
                          {'align': align, 'color': '#EE5927'})
    # 에너지가 없으면 아래를 돌릴 이유가 없음.
    if not link.store.getUsedCapacity(RESOURCE_ENERGY):
        return

    # all links that are for_store and have energy store left
    _inside_links = _.filter(Game.getObjectById(link_id).room.memory[STRUCTURE_LINK],
                             lambda l:
                             Game.getObjectById(l.id)
                             and
                             l.for_store == 1
                             and
                             Game.getObjectById(l.id).store.getUsedCapacity(RESOURCE_ENERGY) < 600)
    inside_links = []
    for l in _inside_links:
        inside_links.append(Game.getObjectById(l.id))

    # 쏠준비 됨? 그럼 날려!
    if link.cooldown == 0 and link.store.getUsedCapacity(RESOURCE_ENERGY) >= amount_to_shoot and len(inside_links) > 0:
        # 내부(테두리 5칸 이상 이내)에 있는 링크 중 무작위 하나를 고르고 거기에 보낸다.
        # 만일 없으면? 애초부터 이 설계와 안맞게 만든거. 몰라ㅆㅂ
        # 가장 에너지를 안가지고 있는 링크에 던진다.
        # todo 만약 중복이면 가장 가까운거에 던진다.
        if not len(inside_links) == 1:
            inside_links = find_closest_and_empty_link(link, inside_links)
        else:
            inside_links = inside_links[0]
        # 해당 링크가 에너지를 받은 시간 갱신. 링크의 전송시간을 낭비하지 않게 하기 위해 고안.
        if not inside_links.received_time or not inside_links.received_time == Game.time:
            transfer_result = link.transferEnergy(Game.getObjectById(inside_links.id))

            if transfer_result == OK:
                inside_links.received_time = Game.time


# 링크 쏠 위치를 정하기 위한 스크립트.
def find_closest_and_empty_link(target_obj: StructureLink, links: List[StructureLink]):
    """
    링크가 에너지를 전송할 때 가장 가까이 그리고 많이 보낼 수 있는 표적 고르기

    :param target_obj:
    :param links:
    :return:
    """
    # 먼저 가장 적은 양의 에너지를 가진 녀석을 고른다.
    minimum_stored = _.min(links, lambda l: l.store.getUsedCapacity(RESOURCE_ENERGY))
    minimum_val = minimum_stored.store.getUsedCapacity(RESOURCE_ENERGY)
    list_of_minimums = []
    # 여럿 있는지 확인
    for s in links:
        if s.store.getUsedCapacity(RESOURCE_ENERGY) == minimum_val:
            list_of_minimums.append(s)
    # 그중에 가장 가까이 있는걸 고른다.
    obj_for_return = target_obj.pos.findClosestByRange(list_of_minimums)

    return obj_for_return
