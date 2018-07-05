"use strict";
global.myFindRoute = function(srcRm, dstRmName) {
    return Game.map.findRoute(srcRm, dstRmName, {
        routeCallback(roomName, fromRoomName) {
                if (('avoidRooms' in Memory) && (Memory.avoidRooms.length > 0)) {
                    if(!!~Memory.avoidRooms.indexOf(roomName)) {
                        return Infinity;
                    }
                }
                return 1;
            }
        });
}

global.getPath = function(creep,rName, igC = false) {
    var rand = function(min,max) { return Math.floor(Math.random()*(max-min+1)+min); }
    creep.memory.prevRoom = creep.room.name;
    let route = global.myFindRoute(creep.room, rName);
    if (typeof route[0] == "undefined") {
        creep.say("No path!");
        return 999;
    }
    let destPos = new RoomPosition(rand(10,40),rand(10,40),route[0].room);
    let endPath = null;
    if (igC) endPath = creep.room.findPath(creep.pos, destPos, {ignoreCreeps: true, maxRooms: 1});
    else endPath = creep.room.findPath(creep.pos, destPos, {ignoreCreeps: false, maxRooms: 1});
    // console.log(creep.name, endPath.length);
    if (Game.flags.hasOwnProperty('Waypoint') && (['scout'].indexOf(creep.memory.role) >= 0)) {
        if (creep.memory.hasOwnProperty('reachedWaypoint') || (creep.room.name == Game.flags.Waypoint.pos.roomName) || (creep.memory.prevPos.roomName == Game.flags.Waypoint.pos.roomName)) {
            creep.memory.reachedWaypoint = true;
            creep.memory.nextDest = Room.serializePath(endPath);
            creep.say("Routing:"+route.length);
            return route.length;
        } else {
            creep.memory.nextDest = creep.room.findPath(creep.pos, Game.flags.Waypoint.pos, {ignoreCreeps: false, serialize: true, maxRooms: 1});
            creep.say("WP Routing...");
            return route.length;
        }
    } else {
        creep.memory.nextDest = Room.serializePath(endPath);
        creep.say("Routing:"+route.length);
        return route.length;
    }
    return 999;
}

// 위랑 실질적인 연관 없음. 그냥 램파트 무시하는 스크립트.
creep.moveTo(target, {
    costCallback: function(roomName, costMatrix) {
        for(let rp of creep.room.structures.ramparts) {
            costMatrix.set(rp.pos.x, rp.pos.y, 0xff);
        }
    }});