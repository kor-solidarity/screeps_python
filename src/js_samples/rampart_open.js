if (hostiles.length > 0) {
	let myRamparts = myRoom.find(FIND_MY_STRUCTURES, {
		filter: (structure) => {
			return (structure.structureType == STRUCTURE_RAMPART) && structure.isActive() && structure.isPublic;
		}
	});
	if (myRamparts.length > 0) {
		for (let rt = (myRamparts.length-1); rt >= 0; rt--) {
			myRamparts[rt].setPublic(false);
		}
	}
} else {
	if (Game.time % 10 === 0) {
		let myRamparts = myRoom.find(FIND_MY_STRUCTURES, {
			filter: (structure) => {
				return (structure.structureType == STRUCTURE_RAMPART) && structure.isActive() && !structure.isPublic;
			}
		});
		if (myRamparts.length > 0) {
			for (let rt = (myRamparts.length-1); rt >= 0; rt--) {
				myRamparts[rt].setPublic(true);
			}
		}
	}
}