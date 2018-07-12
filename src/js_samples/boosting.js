// Put this somewhere that runs every tick
// there, you can just write some simple logic on your creep like "do I need boosts but don't have them? run getBoost"
if (typeof global.boostParts == "undefined") {
    global.boostParts = {};
    for (let part in BOOSTS)
    {
        for (let boost in BOOSTS[part])
        {
            global.boostParts[boost] = part;
        }
    }
    global.boostList = Object.keys(global.boostParts);
}

Creep.prototype.getBoost = function(theBoost) {
    if ((typeof global.boostList != "undefined") && !!~global.boostList.indexOf(theBoost)) {
        let boostedParts = 0;
        boostedParts += _.sum(this.body, function(aPart) {
            if ((typeof aPart.boost != "undefined") && (aPart.boost == theBoost)) return 1;
            else return 0;
        });
        if (boostedParts == this.getActiveBodyparts(boostParts[theBoost])) return true;
        let myLabs = this.room.find(FIND_MY_STRUCTURES, {filter: {structureType: STRUCTURE_LAB, mineralType: theBoost}});
        if (myLabs.length > 0) {
            let bRet = myLabs[0].boostCreep(this);
            if (bRet == OK) return true;
            else if (bRet == ERR_NOT_IN_RANGE) this.moveTo(myLabs[0]);
        }
    }
    return false;
}