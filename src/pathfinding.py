import random
from defs import *

__pragma__('noalias', 'name')
__pragma__('noalias', 'undefined')
__pragma__('noalias', 'Infinity')
__pragma__('noalias', 'keys')
__pragma__('noalias', 'get')
__pragma__('noalias', 'set')
__pragma__('noalias', 'type')
__pragma__('noalias', 'update')

# SPECIAL THANKS TO THE CREATOR - Kenji.

"""
1. js_global._costs = {'base': {}, 'rooms': {}, 'creeps': {}}
    * place this above main.py
2. You can get a matrix with Costs(room_name, opts).load_matrix()
    * opts = {'trackCreeps': True} will add creeps to the matrix
    
3. place those two maintenance functions in a file and import it into main.py.
    At the very end of main.py, place the following: module_name.run_maintenance()
"""

# For this to work, you need to place the following OUTSIDE main (right above it is fine)
# js_global._costs = {'base': {}, 'rooms': {}, 'creeps': {}}
# Costs(room_name, opts).load_matrix()
# So, to get a matrix, you provide this to your callback: `Costs(room_name, opts).load_matrix()`

# that's it.  if you want to want to consider other creeps,
# you can do `Costs(room_name, {'trackCreeps': True}).load_matrix()`

# otherwise it ignores creeps by default.


class Costs:
    """Class for managing and generating CostMatrix objects"""

    def __init__(self, room_name, opts):
        self.id = room_name
        self.opts = opts or {}

        self.costs = js_global._costs
        self.room = Game.rooms[room_name]

    def load_matrix(self):
        """Loads and returns deserialized form of cost matrix stored in
        js_global._costs.

        js_global._costs properties:
            base: Serialized form of matrix reflecting all structures positions
                in a room.
            rooms:
                Deserialized form of matrices found in `base`.
            creeps: Clones of matrices found found in `rooms` that
                reflect creep positions in a room.

        `rooms` and `creeps` are emptied at the end of each tick
     """

        if (self.id not in self.costs.base) or self.opts.refreshMatrix:
            self.generate_new_matrix()

        if self.id not in self.costs.rooms:
            self.costs.rooms[self.id] = self.unpack(self.costs.base[self.id])

        if self.opts.trackCreeps:
            return self.add_creeps()

        return self.costs.rooms[self.id]

    def generate_new_matrix(self):
        """Creates a new instance of `CostMatrix` that reflects the positions of
        structures in a room.

        If the room is not visible, the result is not stored for future use.
        Regardless of whether or not the room is visible, the result is stored
        for use in the current tick.
        """

        new_matrix = __new__(PathFinder.CostMatrix)
        print('new_matrix: ', JSON.stringify(new_matrix))
        if self.add_structures(new_matrix) == OK:
            self.costs.base[self.id] = self.pack(new_matrix)

        self.costs.rooms[self.id] = new_matrix

    def add_structures(self, matrix):
        """Modifies matrix object to reflect structures in room; if the room
        doesn't exist in Game.rooms, ERR_INVALID_TARGET is returned"""

        if not self.room:
            return ERR_INVALID_TARGET

        objects = self.room.find(FIND_STRUCTURES)
        if _.size(Game.constructionSites):
            sites = self.room.find(FIND_MY_CONSTRUCTION_SITES, {'filter':
                lambda s: OBSTACLE_OBJECT_TYPES.includes(s.structureType)
            })
            objects = objects.concat(sites)

        for obj in objects:

            if obj.structureType == STRUCTURE_ROAD:
                cost = 1
            elif obj.structureType == STRUCTURE_RAMPART:
                cost = 0 if (obj.my or obj.isPublic) else 255
            elif obj.structureType == STRUCTURE_CONTAINER:
                cost = 10
            else:
                cost = 255

            if cost > matrix.get(obj.pos.x, obj.pos.y):
                matrix.set(obj.pos.x, obj.pos.y, cost)

        return OK

    def add_creeps(self):
        """Modifies clone of matrix found at self.costs.rooms[self.id] to
        reflect creep positions in room.  If the target room is undefined, the
        base matrix found in self.rooms is returned"""

        if self.id in self.costs.creeps:
            return self.costs.creeps[self.id]

        if not self.room:
            return self.costs.rooms[self.id]

        self.costs.creeps[self.id] = matrix = self.costs.rooms[self.id].clone()
        for creep in self.room.find(FIND_CREEPS):
            matrix.set(creep.pos.x, creep.pos.y, 255)

        return self.costs.creeps[self.id]

    @staticmethod
    def unpack(matrix):
        """Returns a deserialized form of matrix that can be used by
        PathFinder.search()"""

        return PathFinder.CostMatrix.deserialize(JSON.parse(matrix))

    @staticmethod
    def pack(matrix):
        """Returns serialized form of matrix that can be cached"""
        print('pack(matrix)', JSON.stringify(matrix))
        return JSON.stringify(matrix.serialize())


# Place these anywhere and run them at the end of main.py, they just need to be run last

# Using this will help with CPU as it caches the cost matrix objects.
# The two functions above cleanup
# `js_global._costs = {'base': {}, 'rooms': {}, 'creeps': {}}`
# without it, you would be using really old matrix objects that might not be relevant.
# EDIT: just run `run_maintenance()`, it will call the other function when needed

def run_maintenance():
    """cleans up global costs cache"""

    costs_cache = js_global._costs
    for room in _.keys(costs_cache.rooms):
        del costs_cache.rooms[room]
        del costs_cache.creeps[room]

    if not Game.time % 250:
        reset_cached_matrices()


def reset_cached_matrices():
    """Deletes stored CostMatrix objects in js_global._costs.base if room object
    associated with CostMatrix is visible"""

    for room in _.keys(js_global._costs.base):
        if not (room in Game.rooms):
            continue
        del js_global._costs.base[room]