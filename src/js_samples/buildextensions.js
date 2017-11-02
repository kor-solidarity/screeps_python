function buildExtensions(spawn) {
    if (spawn.room.controller.level >= 2) {
        if (_.filter(spawn.room.memory.structureCache, 'type', 'extension').length < spawn.room.getExtensionCount()) {
            let x;
            let y;
            for (let i = 1; i < 8; i++) {
                x = getRandomInt(-_.round(i, 0), _.round(i, 0));
                y = getRandomInt(-_.round(i, 0), _.round(i, 0));
                let pos = new RoomPosition(spawn.pos.x + x, spawn.pos.y + y, spawn.pos.roomName);
                if (pos.checkForAllStructure().length > 0 || pos.getRangeTo(spawn) === 1) continue;
                switch (pos.createConstructionSite(STRUCTURE_EXTENSION)) {
                    case OK:
                        if (pos.findInRange(FIND_STRUCTURES, 1, {filter: (s) => s.structureType === STRUCTURE_ROAD}).length > 0) continue;
                        let path = spawn.room.findPath(spawn.pos, pos, {
                            maxOps: 10000, serialize: false, ignoreCreeps: true, maxRooms: 1, ignoreRoads: false
                        });
                        for (let p = 0; p < path.length; p++) {
                            if (path[p] !== undefined) {
                                let build = new RoomPosition(path[p].x, path[p].y, spawn.room.name);
                                const roadCheck = build.lookFor(LOOK_STRUCTURES);
                                const constructionCheck = build.lookFor(LOOK_CONSTRUCTION_SITES);
                                if (constructionCheck.length > 0 || roadCheck.length > 0) {
                                } else {
                                    build.createConstructionSite(STRUCTURE_ROAD);
                                }
                            }
                        }
                        continue;
                    case ERR_RCL_NOT_ENOUGH:
                        break;
                }
            }
        }
    }
}