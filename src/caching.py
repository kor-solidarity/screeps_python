from defs import *


__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def caching(renewing):
    """
    ĉi tio def-o caĉas ĉiuj strukturoj al memoro.
    :param renewing: Ĉu tiu def-o rekonstruas malaperis strukturojn?
                    se jes, rekonstruas, se ne, nur eliminas tiujn el memoro.
                    Memory.renewing
    :return:
    """
    '''
    objective for this place:
        - cache memory for all objects in the rooms.
        - divide them by rooms.
        - then by types. technically each objects need 3 elements - their assigned room, ID, and structureType
        - each room needs: 
            *bool(checked) - for not overlapping same room.
    '''

    # initializing
    for name in Object.keys(Memory.rooms):
        if not Memory.rooms.name.checked:
            Memory.rooms.name.checked

    # unue, filter all spawns in the game.
    for name in Object.keys(Game.spawns):
        room_name = Game.spawns[name].room.name
        Memory.room.room_name