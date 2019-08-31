from defs import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def run_lab(lab_id, room):
    """
    자세한 설명은 생략한다.

    :param lab:
    :param room: Game.room[name]
    :return:
    """

    # 아이디 없으면 거름
    if not Game.getObjectById(lab_id):
        return


