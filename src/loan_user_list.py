import role_harvester
import role_hauler
import role_upgrader
import structure as building_action
import role_scout
import role_carrier
import role_soldier
import structure_spawn
import role_collector
import random
import miscellaneous

# defs is a package which claims to export all constants and some JavaScript objects, but in reality does
#  nothing. This is useful mainly when using an editor like PyCharm, so that it 'knows' that things like Object, Creep,
#  Game, etc. do exist.
from defs import *

# These are currently required for Transcrypt in order to use the following names in JavaScript.
# Without the 'noalias' pragma, each of the following would be translated into something like 'py_Infinity' or
#  'py_keys' in the output file.
__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')


def populate_loan_list(loan_user='LeagueOfAutomatedNations', loan_segment=99):
    official_server = False
    try:
        servers = ['shard0','shard1','shard2']
        number = servers.index(Game.shard.name)
        if number >= 0:
            official_server = True
    except:
        official_server = False

    if typeof(RawMemory.setActiveForeignSegment) == 'function' and official_server:
        # 업데이트 시간...???
        if not Memory.last_loan_time or not Memory.loan_list:
            Memory.loan_loan_time
        pass
