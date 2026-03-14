

from bge import logic

from game3 import base, world, door, vehicle, weapon, keymap, HUD, viewport


class CoreSeaport(base.CoreObject):

	NAME = "Ship"

	CONTAINER = "WORLD"
	UPDATE = "WORLD"

	OBJECT = "Ship"
	ANIMSET = "Sailing"
	ANIMFRAMES = {"Depart":400, "Land":400}

	HUDLAYOUT = HUD.LayoutCinema

	def defaultData(self):
		dict = super().defaultData()
		dict["HUD"] = {"Subtitles":None}
		return dict

	def doLoad(self):
		name = "PIRATE"+self.OBJECT

		if name not in base.WORLD:
			dict = {"Object":self.OBJECT, "Data":None, "Portal":None}
			base.WORLD[name] = {"Ship":dict, "Dict":self.dict, "Frame":0}
			base.WORLD[name]["Map"] = base.CURRENT["Level"]
			base.WORLD[name]["CurMap"] = base.CURRENT["Level"]
			self.active_state = self.ST_Disabled

		self.worldcache = base.WORLD[name]
		self.dict = self.worldcache["Dict"]

		super().doLoad()

	def ST_Startup(self):
		owner = self.owner
		scene = owner.scene

		self.ship_obj = None
		self.ship_class = None
		self.ship_anim = None

		if self.worldcache["Map"] == self.worldcache["CurMap"] == base.CURRENT["Level"]:
			print("Ship Insta-Spawn")
			self.doShipSpawn()

	def doShipSpawn(self):
		owner = self.owner
		scene = owner.scene

		if self.ship_anim != None:
			self.ship_anim.endObject()
			self.ship_anim = None

		self.worldcache["Map"] = base.CURRENT["Level"]
		self.worldcache["CurMap"] = base.CURRENT["Level"]

		if self.ship_obj == None:
			self.ship_obj = scene.addObject(self.OBJECT, owner, 0)
			self.ship_obj["DICT"] = self.worldcache["Ship"]
			self.ship_class = base.GETCLASS(self.ship_obj)

		if base.CURRENT["Level"]+owner.name in base.PROFILE["Portal"]:
			del base.PROFILE["Portal"][base.CURRENT["Level"]+owner.name]

		self.active_state = self.ST_Disabled

	def doShipCinematic(self, mode="Depart"):
		owner = self.owner
		scene = owner.scene

		if self.ship_class != None:
			self.ship_class.packObject(True, None, force=True)
			self.ship_class = None
			self.ship_obj = None
			print("SHIP DEPART")

		self.ship_anim = scene.addObject("ShipCinematic", owner, 0)
		if owner.get("ANIMWORLD", False) == True:
			self.ship_anim.worldPosition = -base.ORIGIN_OFFSET
			self.ship_anim.worldOrientation = self.createMatrix()

		env = scene.addObject(self.OBJECT, owner, 0)
		env.setParent(self.ship_anim, False, False)

		for i in {"Mesh", "Details", "COL"}:
			n = ".".join([self.OBJECT, i])
			if n in scene.objectsInactive:
				msh = scene.addObject(n, owner, 0)
				msh.setParent(env, False, False)

		cam = self.ship_anim.children["ShipCinematic.Camera"]
		cam.near = base.config.CAMERA_CLIP[0]
		cam.far = base.config.CAMERA_CLIP[1]
		name = owner.get("ANIMNAME", self.ANIMSET)
		end = owner.get(mode.upper()+"FRAMES", self.ANIMFRAMES[mode])

		self.doAnim(env, "Boat."+name+mode+"Ship", (0,end))
		self.doAnim(cam, "Boat."+name+mode+"Camera", (0,end))

		self.worldcache["CurMap"] = ""
		self.worldcache["Frames"] = end

		if scene.active_camera == base.SC_CAM:
			scene.active_camera = cam

		self.active_state = self.ST_Active

	def ST_Active(self):
		owner = self.owner
		scene = owner.scene

		if self.worldcache["Frames"] <= 0:
			if self.worldcache["Map"] != base.CURRENT["Level"]:
				self.active_state = self.ST_Disabled
				if scene.active_camera == self.ship_anim.children["ShipCinematic.Camera"]:
					base.PROFILE["Portal"][self.worldcache["Map"]+owner.name] = {}
					world.openBlend(self.worldcache["Map"])
				else:
					self.ship_anim.endObject()
					self.ship_anim = None
			else:
				self.doShipSpawn()
		else:
			self.worldcache["Frames"] -= 1

	def ST_Disabled(self):
		if self.worldcache["Map"] == base.CURRENT["Level"]:
			if self.worldcache["CurMap"] != base.CURRENT["Level"]:
				self.doShipCinematic("Land")

		elif self.worldcache["Map"] != base.CURRENT["Level"]:
			if self.worldcache["CurMap"] == base.CURRENT["Level"]:
				self.doShipCinematic("Depart")

class RapySeaport(CoreSeaport):

	OBJECT = "Red1"
	ANIMSET = "Aliens"


class CoreShip(world.DynamicWorldTile):

	NAME = "Pirate Ship"

	CONTAINER = "WORLD"
	UPDATE = "WORLD"

	LOD_ACTIVE = 300
	LOD_FREEZE = 600
	LOD_PROXY = 900
	OBJ_HIGH = ["Mesh", "Details", "COL"]
	OBJ_LOW  = ["LOW"]
	OBJ_PROXY = ["LOW"]

	def ST_Startup(self):
		self.active_pre.insert(0, self.PR_DoorGrav)

	def PR_DoorGrav(self):
		for key in self.objects["Map"]:
			obj = self.objects["Map"][key]
			obj.color = (0,0,0,1)
			if base.CURRENT["Level"] == (key+".blend"):
				obj.color = (0,1,0,1)
			elif obj.get("RAYCAST", None) != None:
				obj.color = (1,0,0,1)
				if keymap.BINDS["ACTIVATE"].tap() == True:
					base.WORLD["PIRATE"+self.owner.name]["Map"] = key+".blend"
			obj["RAYCAST"] = None
			obj["RAYNAME"] = key

class Red1(CoreShip):

	NAME = "RedOne"

	LOD_ACTIVE = 500
	LOD_FREEZE = 1000
	LOD_PROXY = 10000
	OBJ_HIGH = ["Mesh", "COL"]
	OBJ_LOW  = ["Mesh"]
	OBJ_PROXY = ["Mesh"]


