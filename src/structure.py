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


def run_tower(tower, all_structures, creeps, hostile_creeps, repairs, square):
    """

    :param tower:
    :param all_structures: tower.room.find(FIND_STRUCTURES)
    :param creeps: tower.room.find(FIND_MY_CREEPS)
    :param hostile_creeps: tower.room.find(FIND_HOSTILE_CREEPS)
    :param repairs: repair stuffs.
    :param square: 제곱근값. 별건 아니고 건물확인차 쓰이는거임.
    :return:
    """
    # tower havas du laborojn.
    # 1. serĉas por malamikoj kaj mortigi ĝin.
    # 2. heal creeps. and then 3
    # 3. se tie ne estas malamikojn, serĉas por konstruaĵoj kiu bezonas repari kaj repari ĝin.

    # print('hostile: ', hostile_creeps)

    if tower.energy < tower.energyCapacity * 0.25 and len(hostile_creeps) == 0:
        return

    malsana_amikoj = _.filter(creeps, lambda c: c.hits < c.hitsMax)

    if len(hostile_creeps) > 0 and len(malsana_amikoj) > 0:
        flip = random.randint(0, 1)
        if flip == 1:
            malsana_amiko = tower.pos.findClosestByRange(malsana_amikoj)
            tower.heal(malsana_amiko)
        else:
            hostile_creep = tower.pos.findClosestByRange(hostile_creeps)
            tower.attack(hostile_creep)
    elif len(hostile_creeps) > 0:
        hostile_creep = tower.pos.findClosestByRange(hostile_creeps)
        tower.attack(hostile_creep)
    elif len(malsana_amikoj) > 0:
        malsana_amiko = tower.pos.findClosestByRange(malsana_amikoj)
        tower.heal(malsana_amiko)
    else:
        if tower.energy < tower.energyCapacity * 0.25:
            return
        else:
            repair = tower.pos.findClosestByRange(repairs)
            tower.repair(repair)


def run_links(link, my_structures):
    """
    distributing energy to links
    :param link: _.filter(my_structures,  {'structureType': STRUCTURE_LINK})
    :param my_structures: .find(FIND_MY_STRUCTURES)
    :return:
    """
    # 내부(테두리 5칸 이상 이내)에 있는 링크는 작동을 안한다.
    if not (link.pos.x < 5 or link.pos.x > 44 or link.pos.y < 5 or link.pos.y > 44):
        return

    if link.cooldown == 0 and link.energy >= 140:
        # links with any energy left in storage and inside the boundaries
        inside_links = my_structures.filter(lambda s: s.structureType == STRUCTURE_LINK
                                            and not (s.pos.x < 5 or s.pos.x > 44 or s.pos.y < 5 or s.pos.y > 44)
                                            and s.energy <= s.energyCapacity - 100)

        if len(inside_links) > 0:
            # 내부(테두리 5칸 이상 이내)에 있는 링크 중 무작위 하나를 고르고 거기에 보낸다.
            # 만일 없으면? 애초부터 이 설계와 안맞게 만든거. 몰라ㅆㅂ
            random_int = random.randint(0, len(inside_links) - 1)
            transfer_result = link.transferEnergy(inside_links[random_int])
