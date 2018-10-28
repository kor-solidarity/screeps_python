"use strict";
var labs = {
    findLab: function(theLabs,desiredMineral) {
        for (let i = 0, len = theLabs.length; i < len; i++) {
            if ((theLabs[i].mineralAmount >= 5) && (theLabs[i].mineralType == desiredMineral)) return theLabs[i];
            else if ((theLabs[i].mineralAmount == 0) && theLabs[i].memory.hasOwnProperty('mineral') && (theLabs[i].memory.mineral == desiredMineral)) return theLabs[i];
        }
        return null;
    }
    ,
    setLabSources: function(theLabs) {
        let sRet = true;
        if (typeof global.labReact == "undefined") {
            global.labReact = {}; // From stevetrov. Changed Memory to global instead.
            for (let i in REACTIONS)
            {
                for (let j in REACTIONS[i])
                {
                    labReact[REACTIONS[i][j]] = [i,j];
                }
            }
        }

        for (let i = 0, len = theLabs.length; i < len; i++) {
            if (theLabs[i].memory.hasOwnProperty('mineral') && (theLabs[i].memory.mineral != null)) {
                if (baseMinerals.indexOf(theLabs[i].memory.mineral) >= 0) continue;
                else {
                    let neededReaction = global.labReact[theLabs[i].memory.mineral];
                    if ((typeof neededReaction != "undefined") && (neededReaction.length == 2)) {
                        let lab1 = this.findLab(theLabs,neededReaction[0]);
                        let lab2 = this.findLab(theLabs,neededReaction[1]);
                        if ((lab1 != null) && (lab2 != null)) {
                            if ((theLabs[i].pos.getRangeTo(lab1) <= 2) && (theLabs[i].pos.getRangeTo(lab2) <= 2)) {
                            theLabs[i].memory.lab1 = lab1.id;
                            theLabs[i].memory.lab2 = lab2.id;
                                continue;
                            } else {
                                console.log(theLabs[i].room.name, "Sources for lab", theLabs[i].id, "mineral", theLabs[i].memory.mineral, "are too far away!");
                                sRet = false;
                            }
                        } else {
                            if ((theLabs[i].memory.mineral == theLabs[i].mineralType) && (theLabs[i].mineralAmount >= 5)) {
                                theLabs[i].memory.lab1 = null;
                                theLabs[i].memory.lab2 = null;
                                sRet = true;
                            } else {
                                console.log(theLabs[i].room.name, "Failed to set sources for lab", theLabs[i].id, "mineral", theLabs[i].memory.mineral);
                                sRet = false;
                            }
                        }
                    } else {
                        //console.log(theLabs[i].room.name, "Failed to calculate reaction for lab", theLabs[i].id, "mineral", theLabs[i].memory.mineral);
                        sRet = false;
                    }
                }
            }
        }
        return sRet;
    }
    ,
    doReactions: function(theLabs) {
        if (typeof global.labReact == "undefined") {
            global.labReact = {}; // From stevetrov. Changed Memory to global instead.
            for (let i in REACTIONS)
            {
                for (let j in REACTIONS[i])
                {
                    labReact[REACTIONS[i][j]] = [i,j];
                }
            }
        }

        let rRet = ERR_INVALID_TARGET;

        const compoundsToLimit = [RESOURCE_ZYNTHIUM_KEANITE, RESOURCE_UTRIUM_LEMERGITE, RESOURCE_HYDROXIDE,
        RESOURCE_UTRIUM_HYDRIDE,
        RESOURCE_UTRIUM_OXIDE,
        RESOURCE_KEANIUM_HYDRIDE,
        RESOURCE_KEANIUM_OXIDE,
        RESOURCE_LEMERGIUM_HYDRIDE,
        RESOURCE_LEMERGIUM_OXIDE,
        RESOURCE_ZYNTHIUM_HYDRIDE,
        RESOURCE_ZYNTHIUM_OXIDE,
        RESOURCE_GHODIUM_OXIDE
        ];

        for (let i = 0, len = theLabs.length; i < len; i++) {
            if (theLabs[i].memory.hasOwnProperty('mineral') && (theLabs[i].memory.mineral != null)) {
                if ((typeof global.labReact[theLabs[i].memory.mineral] == "undefined") || (theLabs[i].cooldown > 0)) continue;
                if ((compoundsToLimit.indexOf(theLabs[i].memory.mineral) >= 0) && (theLabs[i].mineralAmount >= 100)) continue;
                if (theLabs[i].memory.hasOwnProperty('lab1') && theLabs[i].memory.hasOwnProperty('lab2')) {
                    let lab1 = Game.getObjectById(theLabs[i].memory.lab1);
                    let lab2 = Game.getObjectById(theLabs[i].memory.lab2);
                    if ((lab1 != null) && (lab2 != null)) {
                        rRet = theLabs[i].runReaction(lab1,lab2);
                        if ((rRet != OK) && (rRet != ERR_NOT_ENOUGH_RESOURCES)) {
                            if (rRet == ERR_FULL) {
                                if (Game.time % 100 === 0) console.log(theLabs[i].room.name,"<span style='color:rgb(209, 169, 27)'>Lab making compound", theLabs[i].memory.mineral, "is full!</span>");
                            } else console.log(theLabs[i].room.name,"Lab reaction error",rRet,"for lab making compound", theLabs[i].memory.mineral, "from", lab1.memory.mineral, "+", lab2.memory.mineral);
                        }
                    }
                }
            }
        }
        return rRet;
    }
    ,
    run: function(theLabs) {
        let theRoom = theLabs[0].room;

        if (Game.time % 5 === 0) {
            var slsRet = this.setLabSources(theLabs);
            var drRet = false;
            if (slsRet) drRet = this.doReactions(theLabs);
            if (slsRet && (drRet == OK)) return true;
            else return false;
        }
    }
};

module.exports = labs;


Object.defineProperty(StructureLab.prototype, 'memory', {
    configurable: true,
    get: function() {
        if(_.isUndefined(this.room.memory.labs)) {
            this.room.memory.labs = {};
        }
        if(!_.isObject(this.room.memory.labs)) {
            return undefined;
        }
        return this.room.memory.labs[this.id] =
                this.room.memory.labs[this.id] || {};
    },
    set: function(value) {
        if(_.isUndefined(this.room.memory.labs)) {
            this.room.memory.labs = {};
        }
        if(!_.isObject(this.room.memory.labs)) {
            throw new Error('Could not set source memory');
        }
        this.room.memory.labs[this.id] = value;
    }
});