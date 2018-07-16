let ramparts = _.filter(creep.room.lookForAt(LOOK_STRUCTURES,creep.pos),
    (struct) => (struct.structureType == STRUCTURE_RAMPART));
if ((ramparts.length == 0) && (creep.room.defcon < 5)) {
	creep.safeMoveTo(enemy.pos);
} else {
	if ((ramparts.length > 0) && (creep.room.defcon < 5) && (creep.pos.getRangeTo(enemy) > 3)) {
		if (ramparts[0].internal) {
			creep.safeMoveTo(enemy.pos);
		} else {
			creep.safeMoveTo(Game.spawns[creep.room.memory.spawns[0]].pos);
		}
	} else if (creep.room.defcon == 5) {
		creep.moveTo(enemy, {maxRooms: 1});
	}
}

//// And below goes in prototypes
Creep.prototype.safeMoveTo = function(dest) {
    if (!(dest instanceof RoomPosition)) return ERR_INVALID_ARGS;
    PathFinder.use(true);
    let aPath = this.room.findPath(this.pos, dest, {range: 1, maxRooms: 1,
        costCallback: function(roomName, costMatrix) {
            if (_.isUndefined(global.costMatrixes)) {
                global.costMatrixes = [];
            }
            if (_.isUndefined(global.costMatrixes[roomName])) {
                let ccRoom = Game.rooms[roomName];
                if (!ccRoom) {
                    console.log("safeMoveTo room name failure!");
                    return costMatrix;
                }
                let myRamparts = ccRoom.find(FIND_MY_STRUCTURES, {filter: {structureType: STRUCTURE_RAMPART}});
                if (myRamparts.length > 0) {
                    for (let cmr = (myRamparts.length-1); cmr >= 0; cmr--) {
                        if (!myRamparts[cmr].internal) {
                            let theCost = 50 + (myRamparts[cmr].pos.getRangeTo(dest)*50);
                            costMatrix.set(myRamparts[cmr].pos.x,myRamparts[cmr].pos.y, theCost);
                            //console.log(myRamparts[cmr].pos.x,myRamparts[cmr].pos.y, theCost);
                        }
                    }
                }
                global.costMatrixes[roomName] = costMatrix.clone();
            } else {
                costMatrix = global.costMatrixes[roomName];
            }
            return costMatrix;
        }
    });
    return this.moveByPath(aPath);
}