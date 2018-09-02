function harvestSource(flag, transferTo) {
    if(flag.room != undefined) {
        var thisContainer = flag.pos.findInRange(FIND_STRUCTURES, 3)[0];
        var thisSource = flag.pos.findInRange(FIND_SOURCES, 1)[0];
        var thisCSite = flag.pos.findInRange(FIND_MY_CONSTRUCTION_SITES, 3)[0];
    }
    if(Game.time % 60 == 0 && thisSource.energyCapacity < 1501) {
        console.log(thisSource.energyCapacity);
        flag.memory.lowCap = true;
    }
    if(flag.memory.harvesters == undefined) {
        flag.memory.harvesters = [];
    }
    if(flag.memory.carriers == undefined) {
        flag.memory.carriers = [];
    }
    if(flag.memory.harvesters.length < h) {
        if(flag.memory.lowCap = true && CRoom.energyCapacityAvailable > 549) {
            var newName = spawnCreep([WORK,WORK,WORK,CARRY,MOVE,MOVE,MOVE], "harvester");
        } else {
            var newName = spawnCreep(HarvesterSA, "harvester");
        }
        if(newName != undefined) {
            flag.memory.harvesters.push(newName);
        }
    }
    if(flag.memory.carriers.length < 1) {
        var newName = spawnCreep(CarrierSA, "Carrier");
        if(newName != undefined) {
            flag.memory.carriers.push(newName);
        }
    }
    for(let name of flag.memory.harvesters) {
        if(Game.creeps[name] == undefined) {
            let index = flag.memory.harvesters.indexOf(name);
            flag.memory.harvesters.splice(index, 1);
            break;
        }
        let creep = Game.creeps[name];
        if(creep.carry.energy == 0) {
            creep.memory.state = 1;
        }
        if(creep.carry.energy > creep.carryCapacity - 8) {
            creep.memory.state = 2;
        }
        if(creep.memory.state == undefined) {
            creep.memory.state = 2;
        }
        if(creep.memory.state == 1) {
            if(creep.room == flag.room) {
                myharvest(creep, thisSource);
            }
            else {
                creep.moveTo(flag);
            }
        }
        if(creep.memory.state == 2) {
            if(thisCSite != undefined) {
                mybuild(creep, thisCSite);
            } else if(thisContainer == undefined || flag.memory.carriers.length == 0) {
                mytransfer(creep, Spawns[0], RESOURCE_ENERGY);
            } else if(thisContainer.hits < thisContainer.hitsMax) {
                myrepair(creep, thisContainer);
            } else {
                mytransfer(creep, thisContainer, RESOURCE_ENERGY);
            }
        }
    }
    for(let name of flag.memory.carriers) {
        if(!Game.creeps[name]) {
            let index = flag.memory.carriers.indexOf(name);
            flag.memory.carriers.splice(index, 1);
            break;
        }
        let creep = Game.creeps[name];
        if(creep.carry.energy == 0) {
            creep.memory.state = 1;
        }
        if(creep.carry.energy == creep.carryCapacity) {
            creep.memory.state = 2;
        }
        if(creep.memory.state == undefined) {
            creep.memory.state = 2;
        }
        if(creep.memory.state == 1) {
            if(creep.room == flag.room) {
                mywithdraw(creep, thisContainer, RESOURCE_ENERGY);
            }
            else {
                creep.moveTo(flag);
            }
        }
        if(creep.memory.state == 2) {
            if(transferTo != undefined) {
                mytransfer(creep, transferTo, RESOURCE_ENERGY);
            }
            else {
                mytransfer(creep, Spawns[0], RESOURCE_ENERGY);
            }
        }
    }
}