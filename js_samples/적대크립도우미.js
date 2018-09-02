//## I'd suggest initializing a 'Game.cache' object every tick. Here's mine for example:
// Per tick caching. call this early in your main loop or in an every-tick Memory initializer/helper
Game.cache = {
	structures: {}, structuresArray: {}, mySpawns: {}, freeSpawns: {},   // Structures
	creepsBySquad: {}, hostiles: {},                                     // creeps
	totalEnergy: {}, rooms: {},                                       };

// This checks for the Memory.allianceArray list set by the Alliance handling code
Object.defineProperty(Creep.prototype, "isFriendly", {
    get: function () {
        var FRIEND_LIST;
        if (Memory.allianceArray) {
            if ( typeof(Memory.allianceArray) == "string" ) Memory.allianceArray=JSON.parse( Memory.allianceArray );
            FRIEND_LIST = Memory.allianceArray.concat(['daerontinuviel']);
        } else {
			// If allianceArray isn't available, fall back to list of alliance members as of Aug 2017
            FRIEND_LIST = ["Shibdib","Rising","PostCrafter","wages123","SpaceRedleg","Donat","kirk"]
            .concat(["BrinkDaDrink","Tyac","herghost","arcath","picoplankton","nyoom","smokeman"])
            .concat(["daerontinuviel", "starking1"]); // Not alliance, non-aggression friends of Kirk
        }
        FRIEND_LIST = FRIEND_LIST.map(function(username) { return username.toLowerCase(); });
        return ( FRIEND_LIST.indexOf( this.owner.username.toLowerCase() ) !== -1 );
    }
});

Object.defineProperty(Room.prototype, "hostileCreeps", {
  // This caches hostileCreeps every tick for any room you call 'room.hostileCreeps' on.
  get: function () {
	if (!Game.cache) Game.cache = { 'hostiles':{} };
    if (!Game.cache.hostiles[this.name]) { // ToDo May need to modify when IVM launches and Game object persists
      Game.cache.hostiles[this.name] = this.find(FIND_HOSTILE_CREEPS,{
        filter: function(c) {
          if ( c.isFriendly ) { return false; }
          return true;
        }
      });

      // This allows you to place a flag named 'faux_hostile' in a room.
      // Use this to test non-tower automated defense code, e.g. spawning defenders or repairers.
      // If you use this, modify your tower code to handle the presence of that flag in the tower's room.
      var fauxHostile = Game.flags['faux_hostile'];
      if (fauxHostile && fauxHostile.room.name === this.name) {
        Logger.log('Found Faux Hostile in '+this.name);
        if (!this.memory.faux_hostile_tick) this.memory.faux_hostile_tick = Game.time;
        if (Game.time - this.memory.faux_hostile_tick >= 5 ) {
          Logger.log('Game.time: '+Game.time+', faux_hostile_tick: '+this.memory.faux_hostile_tick);
          fauxHostile.remove(); //Delete flag in 5 ticks
          this.memory.faux_hostile_tick = null;
          Logger.log('Removed Faux Hostile flag in '+this.name);
        } else {
          fauxHostile.memory.isFlag = true;
          Game.cache.hostiles[this.name].push(fauxHostile);
        }
      }

      // This sends an email notification if a non-friendly user enters any room you check for hostileCreeps
      // Example: All tower code should use this and trigger. But unowned rooms will also Notify if you call room.hostileCreeps in them
      for ( let c of Game.cache.hostiles[this.name]) {
        if ( !fauxHostile && ! c.isSourceKeeper() && ! c.isInvader() && this.controller && this.controller.my ) {
          Game.notify("User " + c.owner.username + " moved into room " + this.name + " with body " + JSON.stringify(c.body), 0);
        }
      }
    }
    return Game.cache.hostiles[this.name];
}});