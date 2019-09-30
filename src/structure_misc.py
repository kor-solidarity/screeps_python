from defs import *
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
        # NULLIFIED
        # # 스토리지 안에 에너지가 오천이상일 경우 수리를 아예 안한다. 스토리지가 아예 없으면야...
        # if (tower.room.storage and tower.room.storage.store[LOOK_ENERGY] > 5000) \
        #         or not tower.room.storage:
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

    link = Game.getObjectById(link_id)

    # 방렙이 몇이냐에 따라 쏘기 시작하는 최저수량을 규정한다.
    if link.room.controller.level >= 7:
        amount_to_shoot = 800
    else:
        amount_to_shoot = 200

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
        if link.energy > 0:
            link.room.visual.text(' {}'.format(link.energy),
                                  link.pos.x, display_loc.y,
                                  {'align': align, 'color': '#EE5927'})
        return

    # 여기 밑으로 내려왔으면 해당 링크는 에너지 전송용이다.
    link.room.visual.text('{}|{}'.format(link.energy, link.cooldown),
                          link.pos.x, display_loc.y,
                          {'align': align, 'color': '#EE5927'})
    # 에너지가 없으면 아래를 돌릴 이유가 없음.
    if not link.energy:
        return

    # all links that are for_store and have energy store left
    inside_links = _.filter(Game.getObjectById(link_id).room.memory[STRUCTURE_LINK],
                            lambda l:
                            Game.getObjectById(l.id)
                            and
                            l.for_store == 1
                            and
                            Game.getObjectById(l.id).energy < Game.getObjectById(l.id).energyCapacity - 100)

    # 쏠준비 됨? 그럼 날려!
    if link.cooldown == 0 and link.energy >= amount_to_shoot and len(inside_links) > 0:
        # 내부(테두리 5칸 이상 이내)에 있는 링크 중 무작위 하나를 고르고 거기에 보낸다.
        # 만일 없으면? 애초부터 이 설계와 안맞게 만든거. 몰라ㅆㅂ
        # random_int = random.randint(0, len(inside_links) - 1)
        # 가장 에너지를 안가지고 있는 링크에 던진다.
        # todo 만약 중복이면 가장 가까운거에 던진다.
        if not len(inside_links) == 1:
            # print(JSON.stringify(inside_links))
            inside_links = _.min(inside_links,
                             lambda l: Game.getObjectById(l.id).energy)
        else:
            inside_links = inside_links[0]
            # print('min_link', min_link)
        # 해당 링크가 에너지를 받은 시간 갱신. 링크의 전송시간을 낭비하지 않게 하기 위해 고안.
        if not inside_links.received_time or \
                not inside_links.received_time == Game.time:
            transfer_result = link.transferEnergy(Game.getObjectById(inside_links.id))

            if transfer_result == OK:
                inside_links.received_time = Game.time

