function raid(creep, guardflag, attackflag, retreatflag) {
    if(creep.getActiveBodyparts(RANGED_ATTACK) > 0) {
        creep.rangedMassAttack();
        if(Game.flags[attackflag] == undefined) {
            var enemiesUF = creep.room.find(FIND_HOSTILE_CREEPS);
            var enemies = [];
            for(var enemyUF of enemiesUF) {
                for(var ally of allianceArray) {
                    if(enemyUF.owner.username == ally) {
                        var dontattack = true;
                    }
                }
                if(dontattack != true) {
                    enemies.push(enemyUF);
                }
            }
            if(enemies.length < enemiesUF.length) {
                creep.cancelOrder('rangedMassAttack');
            }
        if(enemies.length > 0) {
            creep.say('Engaging', true);
            var Closest = creep.pos.findClosestByRange(enemies);
            var Distance = creep.pos.getRangeTo(Closest);
                if(Distance < 3) {
                    var goals = _.map(enemies, function(enemy) {
                        return { pos: enemy.pos, range: 5 };
                        });
                    var F = PathFinder.search(creep.pos, goals, {flee: true});
                    creep.cancelOrder('rangedMassAttack');
                    creep.rangedAttack(Closest);
                    var position = F.path[0];
                    creep.move(creep.pos.getDirectionTo(position));
                    var evading = true;
                }
                if(Distance == 3) {
                    creep.cancelOrder('rangedMassAttack');
                    creep.rangedAttack(Closest);
                }
                if(Distance > 3) {
                    creep.moveTo(Closest);
                }
            }
        else {
                if(Game.flags[guardflag] != undefined) {
                creep.moveTo(Game.flags[guardflag].pos);
                }
        }
        }
        else {
            creep.moveTo(Game.flags[attackflag]);
        }
    }
    else {
        if(Game.flags[retreatflag] != undefined) {
            creep.moveTo(Game.flags[retreatflag].pos);
        }
    }
    var wounded = [];
    var allyCreeps = creep.room.find(FIND_MY_CREEPS);
    for(var allyCreep of allyCreeps) {
        if(allyCreep.hits < allyCreep.hitsMax) {
            wounded.push(allyCreep);
        }
    }
    var closest = creep.findClosestByRange(wounded);
    if(creep.getRangeTo(closest) < 2) {
    creep.heal(closest);
    }
    else {
        creep.rangedHeal(closest);
    }
}