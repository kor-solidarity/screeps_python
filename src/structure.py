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


def run_tower(tower, hostile_creeps, repairs, malsana_amikoj):
    """

    :param tower:
    :param all_structures: tower.room.find(FIND_STRUCTURES)
    :param creeps: tower.room.find(FIND_MY_CREEPS)
    :param hostile_creeps: tower.room.find(FIND_HOSTILE_CREEPS)
    :param repairs: repair stuffs.
    :param malsana_amikoj:
    :return:
    """
    # tower havas du laborojn.
    # 1. serĉas por malamikoj kaj morti ilin.
    # 2. heal creeps. and then 3
    # 3. se tie ne estas malamikojn, serĉas por konstruaĵoj kiu bezonas repari kaj repari ĝin.

    if tower.energy < tower.energyCapacity * 0.25 and len(hostile_creeps) == 0\
            and len(malsana_amikoj) == 0:
        return

    if tower.room.memory.options.tow_atk and len(hostile_creeps) > 0 and len(malsana_amikoj) > 0:
        flip = random.randint(0, 1)
        if flip == 1:
            malsana_amiko = tower.pos.findClosestByRange(malsana_amikoj)
            tower.heal(malsana_amiko)
        else:
            hostile_creep = tower.pos.findClosestByRange(hostile_creeps)
            tower.attack(hostile_creep)
    elif tower.room.memory.options.tow_atk and len(hostile_creeps) > 0:
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


def run_links(link_id):
    """
    distributing energy to links
    :param link_id: room.memory[STRUCTURE_LINK][i].id
    :old_param my_structures: .find(FIND_MY_STRUCTURES) - NULLIFIED
    :return:
    """

    # todo 테두리로 확인하는게 아니라 내부에 진짜 에너지가 제대로 있는지 확인한다.
    # 내부(테두리 5칸 이상 이내)에 있는 링크는 작동을 안한다.
    link = Game.getObjectById(link_id)
    # current link
    me = _.filter(Game.getObjectById(link_id).room.memory[STRUCTURE_LINK], lambda l: l.id == link_id)[0]

    if link.pos.x > 44:
        align = 'right'
    else:
        align = 'left'

    # 저장용 링크인건가?
    if me.for_store:
        # 만일 링크에 에너지가 있으면 표시한다. 굳이 눌러볼 필요 없게.
        if link.energy > 0:
            link.room.visual.text(' 💎{}'.format(link.energy),
                                  link.pos.x + 0, link.pos.y, {'align': align, 'opacity': 0.8, 'font': 0.45})
        return

    # 여기 밑으로 내려왔으면 해당 링크는 에너지 전송용이다.

    if link.energy:
        link.room.visual.text(' 💎{}|{}'.format(link.energy, link.cooldown),
                              link.pos.x + 0, link.pos.y, {'align': align, 'opacity': 0.8})
    else:
        return

    # all links that are for_store and have energy store left
    inside_links = _.filter(Game.getObjectById(link_id).room.memory[STRUCTURE_LINK],
                            lambda l:
                            l.for_store == 1
                            and Game.getObjectById(l.id).energy < Game.getObjectById(l.id).energyCapacity - 100)

    # 쏠준비 됨? 그럼 날려!
    if link.cooldown == 0 and link.energy >= 140 and len(inside_links) > 0:
        # 내부(테두리 5칸 이상 이내)에 있는 링크 중 무작위 하나를 고르고 거기에 보낸다.
        # 만일 없으면? 애초부터 이 설계와 안맞게 만든거. 몰라ㅆㅂ
        random_int = random.randint(0, len(inside_links) - 1)
        transfer_result = link.transferEnergy(Game.getObjectById(inside_links[random_int].id))
