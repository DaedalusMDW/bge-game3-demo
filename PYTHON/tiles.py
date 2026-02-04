

from bge import logic

from game3 import base, world, keymap, HUD, viewport


class Donut(world.DynamicWorldTile):

	CONTAINER = "LOCK"
	NAME = "World Tile"

	def buildBorders(self):
		self.radius_inner = self.owner.get("MIN", 46)
		self.radius_outer = self.owner.get("MAX", 54)
		self.radius_width = self.owner.get("LEN", 6)
		self.radius_mass = self.owner.get("GRAV", 9.8)
		self.radius_quad = self.owner.get("QUAD", "")
		self.active_pre.insert(0, self.PR_BorderPatrol)

	def getLodLevel(self):
		return "ACTIVE"

	def applyContainerProps(self, cls):
		dvec = cls.getOwner().worldPosition-self.owner.worldPosition
		gz = base.mathutils.Matrix.Scale(0.0, 3, self.owner.getAxisVect((0,1,0)))
		dvec = dvec*gz

		cls.gravity = dvec.normalized()*self.radius_mass
		cls.air_drag = 1.0

	def checkCoords(self, cls):
		if cls.CONTAINER == "LOCK" or cls == self:
			return None

		lp = self.getLocalSpace(self.owner, cls.getOwner().worldPosition)
		tr = lp.copy()
		tr[1] = 0

		if abs(lp[1]) > self.radius_width:
			return False

		if tr.length < self.radius_inner:
			return False

		if tr.length > self.radius_outer:
			return False

		if "X" in self.radius_quad:
			if lp[0] < 0:
				return False

		if "Z" in self.radius_quad:
			if lp[2] < 0:
				return False

		return True

class Station(world.DynamicWorldTile):

	CONTAINER = "LOCK"
	NAME = "Space Station"
	LOD_ACTIVE = 500
	LOD_FREEZE = 2000
	LOD_PROXY = 50000
	OBJ_HIGH = ["Mesh", "Smooth", "Details", "COL", "Lights"]
	OBJ_LOW  = ["Mesh"]
	OBJ_PROXY = ["LOW"]


class AmbientTile(world.DynamicWorldTile):

	PROPAGATE = True

	def defaultData(self):
		self.env_dim = None
		self.env_col = self.owner.color

		dict = super().defaultData()
		return dict

	def ST_Startup(self):
		self.active_post.append(self.PS_Ambient)

	def applyContainerProps(self, cls):
		cls.gravity = self.owner.getAxisVect([0,0,1]).normalized()*-9.8
		cls.air_drag = 1
		cls.env_dim = list(self.env_col)

	def PS_Ambient(self):
		if self.env_dim == None:
			cls = self.getParent()
			amb = 0
			if cls != None:
				amb = cls.dict.get("DIM", amb)
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		self.env_col = list(self.env_dim)

		self.env_dim = None

class CityBase(AmbientTile):

	CONTAINER = "LOCK"
	LOD_ACTIVE = 2000
	LOD_FREEZE = 3000
	LOD_PROXY = 100000

class CityDistrict(AmbientTile):

	CONTAINER = "LOCK"
	PROPAGATE = False
	LOD_ACTIVE = 800
	LOD_FREEZE = 1500
	LOD_PROXY = 100000

class CityBuilding(CityDistrict):

	CONTAINER = "LOCK"
	PROPAGATE = False
	LOD_ACTIVE = 150
	LOD_FREEZE = 200
	LOD_PROXY = 100000


import random
from mathutils import Color, Vector

class AddBuilding(base.CoreObject):

	CONTAINER = "LOCK"
	OPTIONS = [
		"TallBuilding",
		"ShortBuilding",
		]

	def ST_Startup(self):
		fr = self.owner.worldPosition+self.owner.getAxisVect((0,0,500))
		to = fr+self.owner.getAxisVect((0,0,-1))

		#obj, pnt, nrm = self.owner.rayCast(to,fr,1000,"",1,0,0)

		#if obj != None:
		#	self.owner.worldPosition = pnt

		## Spawn Building ##
		name = random.choice(self.OPTIONS)
		dict = {"Object":name, "Data":None}
		newobj = self.spawnChild(dict, self.owner)

		## Parent to Spawner Parent ##
		pt = self.getParent()
		if pt != None:
			newobj["Class"].setContainerParent(pt)

		# self destruct
		self.endObject()


class VoidHut(AmbientTile):

	NAME = "A Hut in Space"
	CONTAINER = "LOCK"
	PROPAGATE = False
	LOD_ACTIVE = 200
	LOD_FREEZE = 500
	LOD_PROXY = 10000
	OBJ_HIGH = ["Mesh", "COL", "Lights"]
	OBJ_LOW  = ["Mesh"]
	OBJ_PROXY = ["LOW"]


	def applyContainerProps(self, cls):
		cls.gravity = self.owner.getAxisVect([0,0,1]).normalized()*-9.8
		cls.air_drag = 1
		cls.env_dim = list(self.env_col)

	def checkCoords(self, cls):
		if cls.invalid == True or cls.CONTAINER == "LOCK" or cls == self:
			return None

		lp = self.getLocalSpace(self.owner, cls.getOwner().worldPosition)

		if abs(lp[0]) < 1 and 0 < lp[1] < 10.5 and 0 < lp[2] < 2.5:
			return True

		lp[2] -= 4.5
		if lp.length < 9.5:
			return True

		return False


class PlanetTile(world.DynamicWorldTile):

	CONTAINER = "LOCK"
	PROPAGATE = True
	NAME = "Planet Tile"
	LOD_ACTIVE = 1500
	LOD_FREEZE = 7000
	LOD_PROXY = 100000
	OBJ_HIGH = ["Mesh", "Sea", "Details", "Atmo"]
	OBJ_LOW  = ["Mesh", "Atmo"]
	OBJ_PROXY = ["LOW", "Atmo"]

	COLOR_ATMO = []
	COLOR_SUN = []
	COLOR_MIST = []

	def defaultData(self):
		self.space_planet = self.owner.get("PLANET", 900)
		self.space_atmo = self.owner.get("ATMO", 400)
		self.space_mass = self.owner.get("GRAV", 9.8)
		self.space_air = self.owner.get("AIR", 1.0)
		self.space_sun = self.createVector()

		self.ramp_atmo = []
		for col in self.COLOR_ATMO:
			new = Color((0,0,0))
			new.hsv = list(col[1])
			self.ramp_atmo.append( (col[0], Vector(new)) )

		self.ramp_sun = []
		for col in self.COLOR_SUN:
			new = Color((0,0,0))
			new.hsv = list(col[1])
			self.ramp_sun.append( (col[0], Vector(new)) )

		self.ramp_mist = []
		for col in self.COLOR_MIST:
			new = Color((0,0,0))
			new.hsv = list(col[1])
			self.ramp_mist.append( (col[0], Vector(new)) )

		dict = super().defaultData()
		return dict

	def ST_Startup(self):
		self.active_post.append(self.PS_Ambient)

	def PS_Ambient(self):
		owner = self.owner
		scene = owner.scene

		self.space_sun = scene.get("_SUN_VECTOR", self.createVector())

		pos = scene.active_camera.worldPosition
		dvec = pos-owner.worldPosition
		svec = pos-self.space_sun
		dist = dvec.length-self.space_planet

		dt = svec.normalized().dot(dvec.normalized())
		mx = dist/self.space_atmo

		if dist < self.space_atmo:
			mx = 1.5-(mx*2)
			if mx < 0:
				mx = 0
			if mx > 1:
				mx = 1
			if len(self.ramp_sun) > 0:
				scene["_SUN_COLOR"] = (self.getEnvMix(dvec, svec, self.ramp_sun), mx)
			if dt > 0.2:
				scene["_SUN_COLOR"] = (self.createVector(), mx)
		if dist < self.space_atmo/4:
			mx = 1-(mx*4)
			if len(self.ramp_mist) > 0:
				scene["_MIST_COLOR"] = (self.getEnvMix(dvec, svec, self.ramp_mist), mx)

	def buildBorders(self):
		self.active_pre.insert(0, self.PR_BorderPatrol)

	def applyContainerProps(self, cls):
		owner = self.owner
		scene = owner.scene

		pos = cls.getOwner().worldPosition
		dvec = pos-owner.worldPosition
		svec = pos-self.space_sun
		dist = dvec.length

		mx = 1-((dist-self.space_planet)/self.space_atmo)
		ac = self.getEnvMix(dvec, svec, self.ramp_atmo)*mx

		cls.gravity = dvec.normalized()*-self.space_mass*mx
		cls.air_drag = self.space_air*(mx**2)
		cls.env_dim = (ac[0]+1, ac[1]+1, ac[2]+1, 1.0)

		wp = owner.worldPosition+owner.getAxisVect((0,0,self.space_planet))+base.ORIGIN_OFFSET
		cls.sendEvent("COMPASS", cls, "NORTH", POS=wp)

	def checkCoords(self, cls):
		if cls.invalid == True or cls == self:
			return None

		dvec = cls.getOwner().worldPosition-self.owner.worldPosition
		grav = self.space_atmo+self.space_planet

		if dvec.length < grav:
			if cls.CONTAINER in {"LOCK", "WORLD"}:
				self.sendEvent("LIGHTS", cls, "AMBIENT")

			if cls.CONTAINER == "LOCK":
				return None
			else:
				return True

		return False

	def getEnvMix(self, dvec, svec, ramp):
		dt = svec.normalized().dot(dvec.normalized())

		if len(ramp) == 0:
			dt = -dt
			if dt < 0:
				dt = 0
			obco = Vector(self.owner.color).resized(3)*dt
		else:
			dt = ((dt*0.5)+0.5)
			mx = 0.0
			sv, sc = ramp[0]
			ev, ec = ramp[0]

			for i in range(len(ramp)):
				v, c = ramp[i]

				if dt >= v:
					sv = v
					sc = c
				elif dt <= v and dt >= sv:
					ev = v
					ec = c
					break

			if dt < sv:
				mx = 0.0
			elif ev <= sv:
				mx = 0.0
			else:
				mx = (dt-sv)/(ev-sv)

			obco = sc.lerp(ec, mx)

		return obco


class IcePlanetTile(PlanetTile):

	NAME = "Ice Planet"

	COLOR_ATMO = [
	(0.1, (0.0, 0.0, 0.7) ),
	(0.4, (0.6, 0.2, 0.5) ),
	(0.6, (0.0, 0.0, 0.0) ),
	]

	COLOR_SUN = [
	(0.1, (0.0, 0.0, 0.5) ),
	(0.4, (0.15, 0.3, 0.4) ),
	(0.6, (0.0, 0.0, 0.0) ),
	]

	MIST_RANGE = 300
	COLOR_MIST = [
	(0.1, (0.0, 0.0, 0.9) ),
	(0.6, (0.57, 0.3, 0.3) ),
	]


class WaterPlanetTile(PlanetTile):

	NAME = "Water Planet"

	COLOR_ATMO = [
	(0.1, (0.6, 0.3, 0.4) ),
	(0.4, (0.6, 0.3, 0.2) ),
	(0.6, (0.6, 0.7, 0.1) ),
	]

	COLOR_SUN = [
	(0.1, (0.13, 0.15, 0.8) ),
	(0.4, (0.1, 0.7, 0.7) ),
	(0.6, (0.0, 0.0, 0.0) ),
	]

	MIST_RANGE = 300
	COLOR_MIST = [
	(0.1, (0.6, 0.3, 0.9) ),
	(0.6, (0.6, 0.7, 0.2) ),
	]


class LavaPlanetTile(PlanetTile):

	NAME = "Lava Planet"

	COLOR_SUN = [
	(0.1, (0.0, 0.0, 0.9) ),
	(0.4, (0.1, 0.3, 0.8) ),
	(0.6, (0.0, 0.0, 0.0) ),
	]

	MIST_RANGE = 500
	COLOR_MIST = [
	(0.1, (0.0, 0.0, 0.5) ),
	(0.6, (0.0, 0.0, 0.0) ),
	]

	def getEnvMix(self, dvec, svec, ramp):

		if len(ramp) > 0:
			return super().getEnvMix(dvec, svec, ramp)

		obco = Vector(self.owner.color).resized(3)
		dt = 1-((dvec.length-self.space_planet-33)/9)
		if dt < 0:
			dt = 0
		if dt > 1:
			dt = 1

		return obco*(dt**2)


class BigPlanet(PlanetTile):

	NAME = "Big Planet"
	LOD_ACTIVE = 15000
	LOD_FREEZE = 20000
	LOD_PROXY = 100000

	COLOR_ATMO = [
	(0.1, (0.11, 0.1, 0.5) ),
	(0.4, (0.15, 0.2, 0.3) ),
	(0.6, (0.0, 0.0, 0.0) ),
	]

	COLOR_SUN = [
	(0.1, (0.0, 0.0, 0.5) ),
	(0.4, (0.15, 0.3, 0.3) ),
	(0.6, (0.0, 0.0, 0.0) ),
	]

	MIST_RANGE = 700
	COLOR_MIST = [
	(0.1, (0.11, 0.2, 0.8) ),
	(0.6, (0.1, 0.2, 0.3) ),
	]


class PlanetSystem(world.CoreWorldTile):

	CONTAINER = "LOCK"
	NAME = "World Tile"
	LOD_ACTIVE = 40000
	LOD_FREEZE = 45000
	LOD_PROXY = 60000
	OBJ_HIGH = []
	OBJ_LOW  = []
	OBJ_PROXY = ["LOW"]


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
		cls.air_drag = (mx**2)*self.space_air
		#cls.env_dim = (ac[0]+1, ac[1]+1, ac[2]+1, 1.0)

		wp = self.owner.worldPosition+self.owner.getAxisVect((0,0,self.space_planet))+base.ORIGIN_OFFSET
		cls.sendEvent("COMPASS", cls, "NORTH", POS=wp)

	def checkCoords(self, cls):
		if cls.CONTAINER == "LOCK" or cls == self:
			return None

		return True


