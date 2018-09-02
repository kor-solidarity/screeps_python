try {
    if (Game.time % 100 === 0 || Memory.updateAlliance){
        var hostUsername = Game.shard.name == "shard0" ? "kirk" : "Shibdib";
        var hostSegmentId = 2; // 1 for a {}, 2 for a [] or names
        var segment = RawMemory.foreignSegment;
        if (!segment || segment.username.toLowerCase() !== hostUsername.toLowerCase()
            || segment.id != hostSegmentId) {
            //## Replace log() with your logger
            Logger.log('Updating activeForeignSegment to: '+ hostUsername +': '+hostSegmentId);
            RawMemory.setActiveForeignSegment(hostUsername, hostSegmentId);
            Memory.updateAlliance = true;
        } else {
            Memory.allianceArray = RawMemory.foreignSegment['data'];
            //## Replace log() with your logger
            Logger.log('Updating Alliance friendlies to: '+ JSON.stringify( Memory.allianceArray ));
            Memory.updateAlliance = false;
        }
    }
} catch(err) {
    console.log('Error in RawMemory.foreignSegment handling (alliance): '+err);
}