

from bge import logic

from game3 import base, world, keymap, HUD, viewport


class PlanetTile(world.DynamicWorldTile):

	CONTAINER = "LOCK"
	NAME = "World Tile"
	LOD_ACTIVE = 1500
	LOD_FREEZE = 7000
	LOD_PROXY = 50000
	OBJ_HIGH = ["Mesh", "Sea", "Details", "Atmo"]
	OBJ_LOW  = ["Mesh", "Atmo"]
	OBJ_PROXY = ["LOW", "Atmo"]

	def buildBorders(self):
		self.space_planet = self.owner.get("PLANET", 900)
		self.space_atmo = self.owner.get("ATMO", 400)
		self.space_mass = self.owner.get("GRAV", 9.8)
		self.active_pre.insert(0, self.PR_BorderPatrol)

	def applyContainerProps(self, cls):
		dvec = cls.getOwner().worldPosition-self.owner.worldPosition
		svec = self.owner.worldPosition+base.ORIGIN_OFFSET
		dist = dvec.length
		grav = self.space_atmo+self.space_planet
		obco = self.owner.color

		mx = 1-((dist-self.space_planet)/self.space_atmo)
		dt = self.getEnvMix(dvec, svec)
		ac = self.createVector(vec=(obco[0], obco[1], obco[2]))*mx*dt

		cls.gravity = dvec.normalized()*-self.space_mass*mx
		cls.air_drag = cls.gravity.length/9.8
		cls.env_dim = (ac[0]+1, ac[1]+1, ac[2]+1, 1.0)

		wp = self.owner.worldPosition+self.owner.getAxisVect((0,0,self.space_planet))+base.ORIGIN_OFFSET
		cls.sendEvent("COMPASS", cls, "NORTH", POS=wp)

	def checkCoords(self, cls):
		if cls.CONTAINER == "LOCK" or cls == self:
			return None

		dvec = cls.getOwner().worldPosition-self.owner.worldPosition
		grav = self.space_atmo+self.space_planet

		if dvec.length < grav:
			return True

		return False

	def getEnvMix(self, dvec, svec):
		dt = svec.normalized().dot(-dvec.normalized())
		if dt < 0:
			dt = 0
		return dt


class LavaPlanetTile(PlanetTile):

	def getEnvMix(self, dvec, svec):
		dt = 1-((dvec.length-self.space_planet-33)/9)
		if dt < 0:
			dt = 0
		if dt > 1:
			dt = 1
		dt = dt**2
		return dt


class PlanetWorld(PlanetTile):

	def getLodLevel(self):
		return "ACTIVE"

	def applyContainerProps(self, cls):
		dvec = cls.getOwner().worldPosition-self.owner.worldPosition
		dist = dvec.length
		atmo = self.space_planet+self.space_atmo
		grav = self.space_planet+(self.space_atmo*2)
		obco = self.owner.color

		mx = (atmo-dist)/self.space_atmo
		if mx < 0:
			mx = 0
		if mx > 1:
			mx = 1

		gv = (grav-dist)/(self.space_atmo*2)
		if gv < 0:
			gv = 0
		if gv > 1:
			gv = 1

		ac = self.createVector(vec=(obco[0], obco[1], obco[2]))*mx

		cls.gravity = dvec.normalized()*-self.space_mass*gv
		cls.air_drag = mx
		#cls.env_dim = (ac[0]+1, ac[1]+1, ac[2]+1, 1.0)

		wp = self.owner.worldPosition+self.owner.getAxisVect((0,0,self.space_planet))+base.ORIGIN_OFFSET
		cls.sendEvent("COMPASS", cls, "NORTH", POS=wp)

	def checkCoords(self, cls):
		if cls.CONTAINER == "LOCK" or cls == self:
			return None

		return True

