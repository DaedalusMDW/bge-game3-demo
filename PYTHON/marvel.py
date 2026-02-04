

from bge import logic

from game3 import base, world, door, vehicle, weapon, keymap, HUD, viewport

from mathutils import geometry, Vector, Matrix


SHIPMAN = None

if "MARVEL" not in base.WORLD:
	mvd = {"Object":"Zephyr1", "Data":None, "Portal":None}
	base.WORLD["MARVEL"] = {"Ship":mvd, "Dict":None, "Map":"", "Frame":0, "Traveling":None, "QJ":False}


class LandingZone(base.CoreObject):

	NAME = "Landing Zone"
	CONTAINER = "LOCK"

	def defaultData(self):
		self.env_dim = None
		self.env_col = self.owner.color

		dict = super().defaultData()
		dict["NAME"] = self.owner.get("NAME", self.owner.name)

		return dict

	def defaultStates(self):
		super().defaultStates()
		self.active_state = self.ST_Idle

	def ST_Idle(self):
		global SHIPMAN

		evt = self.getFirstEvent("LIGHTS", "AMBIENT")
		if evt != None:
			evt.sender.applyContainerProps(self)

		if self.env_dim == None:
			amb = 0
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		if base.ORIGIN_SHIFT == None:
			self.env_col = list(self.env_dim)
			self.owner.color = list(self.env_dim)

			self.env_dim = None

		if SHIPMAN != None:
			self.sendEvent("Z1LZ", SHIPMAN, NAME=self.data["NAME"])


class ZephyrShip(base.CoreObject):

	CONTAINER = "WORLD"
	UPDATE = "WORLD"

	ANIMSET = ""
	ANIMFRAMES = {"Depart":420, "Land":450, "Zone":250}

	HUDLAYOUT = HUD.LayoutCinema

	def defaultData(self):
		dict = super().defaultData()
		dict["HUD"] = {"Subtitles":None}
		return dict

	def doLoad(self):
		mvd = base.WORLD["MARVEL"]
		if mvd["Dict"] == None:
			mvd["Dict"] = self.dict
			mvd["Map"] = base.CURRENT["Level"]
			mvd["CurMap"] = base.CURRENT["Level"]
			mvd["LZ"] = "HOME"
			mvd["CurLZ"] = "HOME"
			self.active_state = self.ST_Disabled

		self.dict = mvd["Dict"]
		self.owner["DICT"] = self.dict

		super().doLoad()

	def ST_Startup(self):
		global SHIPMAN
		if SHIPMAN == None:
			SHIPMAN = self
		else:
			self.endObject()
			return

		owner = self.owner
		scene = owner.scene

		mvd = base.WORLD["MARVEL"]

		self.ship_obj = None
		self.ship_class = None
		self.ship_anim = None
		self.ship_lz = None
		self.ship_cam = None
		self.ship_safe = 0
		self.ship_zones = {}

		self.active_pre.append(self.PR_Zones)

		if mvd["Map"] == mvd["CurMap"] == base.CURRENT["Level"]:
			if mvd["LZ"] != mvd["CurLZ"]:
				print("Zephyr Zone Load")
				self.active_state = self.ST_Disabled
				#self.doShipCinematic("Zone")
			else:
				print("Zephyr Insta-Spawn")
				self.doShipSpawn()

		elif mvd["Map"] != mvd["CurMap"]:
			if mvd["Map"] == base.CURRENT["Level"]:
				if mvd["CurMap"] != base.CURRENT["Level"]:
					self.doShipCinematic("Land")

			elif mvd["Map"] != base.CURRENT["Level"]:
				if mvd["CurMap"] == base.CURRENT["Level"]: #and mvd["CurLZ"] == "HOME":
					self.doShipCinematic("Depart")
				#else:
				#	self.active_state = self.ST_Disabled
				#	print("Zephyr Zone Depart Load")

		else:
			mvd["LZ"] = "HOME"
			mvd["CurLZ"] = "HOME"

	def doShipSpawn(self):
		owner = self.owner
		scene = owner.scene

		if self.ship_anim != None:
			if scene.active_camera == self.ship_cam:
				scene.active_camera = base.SC_CAM
			self.ship_anim.endObject()
			self.ship_anim = None
			self.ship_cam = None

		mvd = base.WORLD["MARVEL"]

		if mvd["Map"]+owner.name in base.PROFILE["Portal"]:
			del base.PROFILE["Portal"][mvd["Map"]+owner.name]
		if mvd["CurMap"]+owner.name in base.PROFILE["Portal"]:
			del base.PROFILE["Portal"][mvd["CurMap"]+owner.name]

		mvd["Map"] = base.CURRENT["Level"]
		mvd["CurMap"] = base.CURRENT["Level"]

		mvd["CurLZ"] = mvd["LZ"]
		mvd["Traveling"] = None

		obj = owner
		if self.ship_lz != None:
			obj = self.ship_lz.owner

		if self.ship_obj == None:
			self.ship_obj = scene.addObject("Zephyr1", obj, 0)
			self.ship_obj["DICT"] = mvd["Ship"]
			self.ship_class = base.GETCLASS(self.ship_obj)

		self.ship_lz = None
		self.ship_safe = 0
		self.active_state = self.ST_Disabled

		print("Z SPAWN")

	def doShipCinematic(self, mode="Depart"):
		owner = self.owner
		scene = owner.scene

		mvd = base.WORLD["MARVEL"]

		self.ship_safe = 0
		if self.ship_class != None:
			self.ship_class.packObject(True, True)
			self.ship_class = None
			self.ship_obj = None

		if self.ship_anim != None:
			if scene.active_camera == self.ship_cam:
				scene.active_camera = base.SC_CAM
			self.ship_anim.endObject()
			self.ship_anim = None
			self.ship_cam = None

		if mvd["Traveling"] != base.CURRENT["Level"]:
			mvd["Frame"] = 0
			mvd["Traveling"] = None
		if scene.active_camera == base.SC_CAM and mvd["Frame"] <= 0:
			print("Z TRAVEL", base.CURRENT["Level"])
			mvd["Traveling"] = base.CURRENT["Level"]

		obj = owner
		if self.ship_lz != None:
			obj = self.ship_lz.owner

		self.ship_anim = scene.addObject("ZephyrCinematic", obj, 0)

		wrld = obj.get("FORCEWORLD", False)
		if mvd["Traveling"] != None:
			wrld = True

		if obj.get("ANIMWORLD", False) == True and mode != "Zone" and wrld == True:
			self.ship_anim.worldPosition = -base.ORIGIN_OFFSET
			self.ship_anim.worldOrientation = self.createMatrix()
		else:
			self.ship_anim.worldPosition = obj.worldPosition.copy()
			self.ship_anim.worldOrientation = obj.worldOrientation.copy()

		env = scene.addObject("Zephyr1.Mesh", self.ship_anim, 0)
		env.setParent(self.ship_anim, False, False)
		env.color = obj.color

		#ins = scene.addObject("Zephyr1.Floors", env, 0)
		#ins.setParent(env, False, False)
		gfx = scene.addObject("Zephyr1.GFX", env, 0)
		gfx.setParent(env, False, False)
		if base.WORLD["MARVEL"]["QJ"] == True:
			qjd = scene.addObject("Zephyr1.QJD", env, 0)
			qjd.color = obj.color
			qjd.setParent(env, False, False)

		self.ship_cam = self.ship_anim.children["ZephyrCinematic.Camera"]

		cam = self.ship_cam
		cam.near = base.config.CAMERA_CLIP[0]
		cam.far = base.config.CAMERA_CLIP[1]

		name = self.ANIMSET
		end = self.ANIMFRAMES[mode]

		if mode != "Zone" and wrld == True:
			name = obj.get("ANIMNAME", name)
			end = obj.get(mode.upper()+"FRAMES", end)
		elif mode == "Zone" and "ANIMZONE" in obj:
			name = obj["ANIMZONE"]
			end = obj.get("ZONEFRAMES", end)

		if mvd["Frame"] <= 0:
			mvd["Frame"] = end

		start = end-mvd["Frame"]

		self.doAnim(env, "Zephyr."+name+mode+"Ship", (start,end))
		self.doAnim(cam, "Zephyr."+name+mode+"Camera", (start,end))
		self.doAnim(gfx, "Zephyr."+name+mode+"GFX", (start,end))

		if mvd["Traveling"] != None:
			scene.active_camera = cam

			HUD.SetBlackScreen("FADE")

			if mvd["Map"]+owner.name not in base.PROFILE["Portal"]:
				base.PROFILE["Portal"][mvd["Map"]+owner.name] = {}
			if mvd["CurMap"]+owner.name not in base.PROFILE["Portal"]:
				base.PROFILE["Portal"][mvd["CurMap"]+owner.name] = {}

		mvd["Frame"] = end-start

		self.active_state = self.ST_Active

		print("Z ANIM")

	def PR_Zones(self):
		all = self.getAllEvents("Z1LZ")

		if self.ship_class == None:
			return

		self.sendEvent("Z1LZ", self.ship_class, NAME="HOME")

		self.ship_zones = {"HOME":self}
		for evt in all:
			s = evt.getProp("NAME", None)
			if s != None:
				self.ship_zones[s] = evt.sender
				self.sendEvent("Z1LZ", self.ship_class, NAME=s)

	def ST_Active(self):
		owner = self.owner
		scene = owner.scene

		mvd = base.WORLD["MARVEL"]

		if mvd["Frame"] <= 0:
			if mvd["Map"] != base.CURRENT["Level"]:
				mvd["CurLZ"] = mvd["LZ"]
				mvd["Frame"] = 0
				mvd["Traveling"] = None
				self.active_state = self.ST_Disabled

				if scene.active_camera == self.ship_cam:
					world.openBlend(mvd["Map"])

				elif self.ship_anim != None:
					mvd["CurMap"] = ""
					self.ship_anim.endObject()
					self.ship_anim = None
			else:
				self.doShipSpawn()
		else:
			mvd["Frame"] -= 1

			if self.ship_anim != None and self.ship_lz != None:
				for obj in self.ship_anim.childrenRecursive:
					obj.color = list(self.ship_lz.env_col)

	def ST_Disabled(self):
		lvl = base.CURRENT["Level"]
		mvd = base.WORLD["MARVEL"]

		lz = None
		dp = None

		all = self.getAllEvents("Z1LZ")
		for evt in all:
			s = evt.getProp("NAME", "")

			if mvd["CurLZ"] == s:
				dp = evt.sender

			elif mvd["LZ"] == s and self.ship_lz == None:
				self.ship_lz = evt.sender
				lz = s

		if mvd["LZ"] == "HOME" and mvd["CurLZ"] != "HOME":
			lz = "HOME"

		if mvd["LZ"] != mvd["CurLZ"]:
			self.ship_safe += 1
		if self.ship_safe > 300:
			print("WARNING: Zephyr - Cant find Zone")
			mvd["LZ"] = "HOME"
			lz = "HOME"

		for evt in all:
			s = evt.getProp("NAME", "")

		if mvd["Map"] != lvl and mvd["CurMap"] == lvl:
			if mvd["CurLZ"] != "HOME":
				self.ship_lz = dp
			mvd["LZ"] = "HOME"
			self.doShipCinematic("Depart")
			print("ZEPHYR DEPART")

		elif mvd["Map"] == lvl and mvd["CurMap"] != lvl:
			if mvd["CurLZ"] != "HOME":
				self.ship_lz = dp
			self.doShipCinematic("Land")
			print("ZEPHYR LAND")

		elif lz != None:
			if self.ship_class != None:
				self.ship_class.packObject(True, True)
				self.ship_class = None
				self.ship_obj = None
			self.doShipCinematic("Zone")
			print("ZEPHYR LZ", lz)

		else:
			self.ship_lz = None


class Zephyr(world.DynamicWorldTile):

	NAME = "Zephyr One"
	CONTAINER = "WORLD"
	UPDATE = "WORLD"
	OBJ_HIGH = ["Mesh", "Floors"]
	OBJ_LOW  = ["Mesh", "LOW"]
	OBJ_PROXY = ["Mesh", "LOW"]

	LOD_ACTIVE = 200
	LOD_FREEZE = 200
	LOD_PROXY = 1000

	def defaultData(self):
		self.env_dim = None
		self.env_local = [1,1,1,1]
		self.env_objects = [
		{"POS":self.createVector(vec=( 3.0,-6.0,-3.0)), "R":12, "C":(0.5, 0.5, 0.5)},
		{"POS":self.createVector(vec=(-2.5,-6.0,-3.0)), "R":12, "C":(0.5, 0.5, 0.5)},
		{"POS":self.createVector(vec=(-3.5,-1.0,-3.0)), "R":12, "C":(0.5, 0.5, 0.5)},

		{"POS":self.createVector(vec=( 3.0, 7.0, 0.5)), "R":10, "C":(0.5, 0.5, 0.5)},
		{"POS":self.createVector(vec=(-3.0, 7.0, 0.5)), "R":10, "C":(0.5, 0.5, 0.5)},

		{"POS":self.createVector(vec=(0, -3, 4)), "R":16},

		{"POS":self.createVector(vec=(0, 20, 1)), "R":20, "C":(0.2, 0.3, 1.0)},

		{"POS":self.createVector(vec=(-1.5, 28, 1.5)), "R":28},
		{"POS":self.createVector(vec=( 0.0,-15, 2.5)), "R":28}
		]

		self.lz_places = {}

		dict = super().defaultData()
		dict["DOCKED"] = "INIT"

		return dict

	def defaultChildren(self):
		items = []
		dict = {"Object":"QuinJet", "Data":None, "Parent":"Dock"}
		items.append(dict)
		return items

	def applyContainerProps(self, cls):
		super().applyContainerProps(cls)

		slot = cls.dict.get("Parent", None)
		if slot not in {None, True}:
			if slot == "Dock":
				cls.env_dim = list(self.env_local)
			return

		if cls.owner.name == "Z1Ramp":
			cls.env_dim = list(self.env_local)
			return
		if cls.owner.name == "Z1Dock":
			cls.env_dim = list(self.env_local)
			return

		pos = self.getLocalSpace(self.owner, cls.getOwner().worldPosition)
		ac = [1,1,1]

		for dc in self.env_objects:
			ref = dc["POS"]
			dst = dc["R"]
			vec = pos-ref
			if vec.length < dst:
				c = dc.get("C", (1,1,1))
				v = ((dst-vec.length)/dst)**2
				ac[0] += c[0]*v*0.7
				ac[1] += c[1]*v*0.7
				ac[2] += c[2]*v*0.7

		cls.env_dim = (ac[0], ac[1], ac[2], 1.0)

	def ST_Startup(self):
		owner = self.objects["Root"]
		scene = owner.scene
		self.active_post.append(self.PS_DoorGrav)
		self.active_pre.insert(0, self.PR_Ambient)

		self.objects["Sensor"]["COLLIDE"] = []

	def PR_Ambient(self):
		evt = self.getFirstEvent("LIGHTS", "AMBIENT")
		if evt != None:
			evt.sender.applyContainerProps(self)

		if self.env_dim == None:
			amb = 0
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		if base.ORIGIN_SHIFT == None:
			mesh = self.owner.childrenRecursive.get(self.owner.name+".Mesh", None)
			if mesh != None:
				mesh.color = self.env_dim

			self.env_local = list(self.env_dim)

			self.env_dim = None

	def ST_Disabled(self):
		## LODS ##
		lod = self.getLodLevel()
		if self.lod_state != lod:
			self.setLodState(lod)
		if self.lod_state != "ACTIVE":
			cls = self.getSlotChild("Dock")
			if cls == None:
				self.data["DOCKED"] = "INIT"
			return

		## RUN ##
		cls = self.getSlotChild("Dock")
		if cls == None:
			self.data["DOCKED"] = "NONE"
			base.WORLD["MARVEL"]["QJ"] = False
		else:
			if self.data["DOCKED"] == "INIT":
				self.data["DOCKED"] = "LOCKED"
			base.WORLD["MARVEL"]["QJ"] = True

		## Docking ##
		if self.data["DOCKED"] == "NONE":
			for cls in self.objects["Sensor"]["COLLIDE"]:
				self.sendEvent("DOCKING", cls, "ZEPHYR", GUIDE=self.objects["Guide"], TRACK=self.objects["Sensor"])

			self.objects["Sensor"]["COLLIDE"] = []

			evt = self.getFirstEvent("DOCKING", "QUINJET", "DOCKING")
			if evt != None:
				self.data["DOCKED"] = "DOCKING"

		if self.data["DOCKED"] == "DOCKING":
			evt = self.getFirstEvent("DOCKING", "QUINJET", "LOCKED")
			if evt != None:
				self.data["DOCKED"] = "LOCKED"

		if self.data["DOCKED"] == "LOCKED":
			evt = self.getFirstEvent("DOCKING", "QUINJET", "RELEASE")
			if evt != None:
				self.data["DOCKED"] = "RELEASE"

		## Buttons ##
		for key in self.objects.get("Map", {}):
			obj = self.objects["Map"][key]
			obj.color[0] = 0.0
			if base.CURRENT["Level"] == (key+".blend"):
				obj.color[0] = 1.0
			elif obj.get("RAYCAST", None) != None:
				obj.color[0] = 0.5
				if keymap.BINDS["ACTIVATE"].tap() == True:
					base.WORLD["MARVEL"]["Map"] = key+".blend"
			obj["RAYCAST"] = None
			obj["RAYNAME"] = obj.get("RAYNAME", key)

		## LZ Picker ##
		lz = self.objects["LZ"]
		all = self.getAllEvents("Z1LZ")

		chk = []
		for evt in all:
			name = evt.getProp("NAME", "")
			if name not in chk:
				chk.append(name)
			if name not in self.lz_places:
				pie = lz.scene.addObject("Z1LZ_Circle", lz, 0)
				pie.setParent(lz, False, False)
				self.lz_places[name] = pie

			pie = self.lz_places[name]
			pie["LZ"] = evt.sender
			pie["NAME"] = name

		for key in list(self.lz_places.keys()):
			if key not in chk:
				self.lz_places[key].endObject()
				del self.lz_places[key]

		x = len(chk)
		if x < 1:
			lz["RAYCAST"] = None
			lz["RAYNAME"] = ""
			return

		chk.sort()
		chk.remove("HOME")
		chk.insert(0, "HOME")

		ang = None
		loc = None
		if lz.get("RAYCAST", None) != None:
			plr = lz["RAYCAST"]
			fr = plr.rayhit[1]
			to = fr+plr.rayvec
			hit = geometry.intersect_line_plane(fr, to, lz.worldPosition, lz.getAxisVect((0,1,0)))
			loc = self.getLocalSpace(lz, hit)

		lz["RAYNAME"] = ""

		for i in range(x):
			obj = self.lz_places[chk[i]]
			f = i/x
			obj.localOrientation = self.createMatrix(rot=(0,f*360,0), deg=True)
			obj.color[0] = (1/x)*0.95
			obj.color[1] = 0.0
			if base.WORLD["MARVEL"]["LZ"] == obj["NAME"]:
				obj.color[1] = 1.0
			if loc != None and 0.2 < loc.length < 0.7:
				ref = obj.localOrientation*Vector((0,0,1))
				ang = ref.angle(loc, None)
				ang = self.toDeg(ang)
				if ang != None and ang < 360*(0.5/x):
					obj.color[1] += 0.5
					lz["RAYNAME"] = obj["NAME"]
					if keymap.BINDS["ACTIVATE"].tap() == True:
						base.WORLD["MARVEL"]["LZ"] = obj["NAME"]

		lz["RAYCAST"] = None

	def PS_DoorGrav(self):
		objlist = self.objects["Container"]

		for cls in self.getChildren():
			if cls.owner.name == "Z1Ramp":
				objlist["CBD"].worldOrientation = cls.objects["Mesh"].worldOrientation.copy()
			if cls.owner.name == "Z1Dock":
				if self.data["DOCKED"] not in ["INIT", "NONE"] or self.getFirstEvent("DOCKING", "QUINJET") != None:
					self.sendEvent("INTERACT", cls, "OPEN", LOCK="Z1QJD")
			if cls.owner.name == "Z1DockDoor":
				if self.data["DOCKED"] == "LOCKED":
					self.sendEvent("INTERACT", cls, "OPEN", LOCK="Z1QJD")


class QuinJet(vehicle.CoreAircraft):

	NAME = "QuinJet"
	LANDACTION = "QJLand"
	LANDFRAMES = [100, 0]

	INVENTORY = {"Gun":"WP_GatlingGun", "Missile_L":"WP_Missile", "Missile_R":"WP_Missile"}
	SLOTS = {"ONE":"Gun", "TWO":"Missile"}

	CAM_RANGE = (24, 40)
	CAM_STEPS = 2
	CAM_ZOOM = 0
	CAM_MIN = 1
	CAM_SLOW = 5
	CAM_HEIGHT = 0.2
	CAM_HEAD_G = 25
	CAM_OFFSET = (0,0,2)

	WH_FRONT = 6
	WH_REAR = -1.5
	WH_WIDTH = 2
	WH_HEIGHT = 1.8

	VEH_LENGTH = 0.7

	VEH_ROLL = 0
	VEH_SPRING = 80
	VEH_DAMPING = 8
	VEH_FRICTION = 5

	WHEELS = {
		"Wheel_FC": {"CENTER":True},
		"Wheel_RR": {"REAR":True},
		"Wheel_RL": {"REAR":True, "LEFT":True} }

	SEATS = {
		"Seat_1": {"NAME":"Pilot", "DOOR":"Door_1", "CAMERA":[-0.3,8.4,-0.4], "ACTION":"SeatTall", "VISIBLE":True, "SPAWN":[0,-6,-1.3]} }

	AERO = {"POWER":1000, "REVERSE":0.2, "HOVER":100, "LIFT":0, "TAIL":0, "DRAG":(0.2,0.1,0.6)}

	def defaultData(self):
		self.docking_point = None
		self.env_dim = None

		dict = super().defaultData()
		dict["DOCKED"] = "INIT"

		return dict

	def applyModifier(self, dict):
		if "HEALTH" in dict:
			dict["HEALTH"] *= 0.25
		super().applyModifier(dict)

	def createVehicle(self):
		if self.data["DOCKED"] != None:
			return
		super().createVehicle()

	def airDrag(self):
		owner = self.getOwner()

		linV = owner.worldLinearVelocity
		dampLin = 0.3
		dampRot = 0.6

		owner.setDamping(dampLin, dampRot)

		if linV.length > 30:
			self.doDragForce((0.2,0,0.5))

	def toggleWeapons(self, state):
		for slot in ["Gun", "Missile_L", "Missile_R"]:
			cls = self.getSlotChild(slot)
			if cls != None:
				cls.stateSwitch(state)

	def applyContainerProps(self, cls):
		super().applyContainerProps(cls)
		if cls.owner.name == "WP_GatlingGun":
			cls.env_dim = list(self.objects["Mesh"].color)

	def ST_Startup(self):
		self.ANIMOBJ = self.objects["Rig"]

		g = self.data.get("GLASSFRAME", 120)
		cls = self.getParent()

		if self.dict["Parent"] != "Dock" or cls == None:
			if self.data["DOCKED"] == "INIT":
				self.data["DOCKED"] = None
				self.createVehicle()
			if self.active_state == self.ST_Cruise:
				self.doAnim(NAME="QJHover", FRAME=(0,0), LAYER=2)
			else:
				self.doAnim(NAME="QJHover", FRAME=(100,100), LAYER=2)
		else:
			if self.data["DOCKED"] == "INIT":
				self.data["DOCKED"] = 0
				self.data["LANDSTATE"] = "FLY"
			self.doAnim(NAME="QJDock", FRAME=(120,120), LAYER=2)
			g = 120
			print("INIT DOCK")

		gfx = self.objects["GFX"]
		gfx.color = (1,0,1,1)

		self.doAnim(NAME="QJGlass", FRAME=(g,g), LAYER=1)
		self.data["GLASSFRAME"] = g

		self.doLandingGear(init=True)
		self.active_post.append(self.airDrag)
		self.active_post.append(self.PS_Ambient)

	def PS_Ambient(self):
		if self.env_dim == None:
			cls = self.getParent()
			amb = 0
			if cls != None:
				amb = cls.dict.get("DIM", amb)
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		self.objects["Mesh"].color = self.env_dim

		self.env_dim = None

	def stateSwitch(self, state=None):
		if state != None:
			pass
		elif self.driving_seat == ".":
			state = "DRIVER"
		else:
			state = self.SEATS[self.driving_seat].get("STATE", "DRIVER")

		g = 60
		if self.data["DOCKED"] != None:
			g = 0

		if state == "DRIVER":
			self.setPhysicsType("RIGID")
			self.data["DOCKED"] = None
			self.doAnim(NAME="QJHover", FRAME=(100,100), LAYER=2)
			self.doAnim(NAME="QJGlass", FRAME=(0,0), LAYER=1)
			self.toggleWeapons(True)
			self.active_state = self.ST_Active

		elif state == "ENTER":
			self.assignCamera()
			self.data["GLASSFRAME"] = 120
			if self.data["DOCKED"] != None:
				self.doAnim(NAME="QJDock", FRAME=(180,0), LAYER=2, BLEND=10)
			self.doAnim(NAME="QJGlass", FRAME=(120,0), LAYER=1)
			self.active_state = self.ST_Enter

		elif state == "EXIT":
			self.toggleWeapons(False)
			self.data["GLASSFRAME"] = g
			self.doAnim(NAME="QJGlass", FRAME=(g,120), LAYER=1)
			self.active_state = self.ST_Exit

		elif state == "IDLE":
			if self.removeFromSeat(self.driving_seat, force=None) == True:
				self.data["GLASSFRAME"] = 120
				self.doAnim(NAME="QJGlass", FRAME=(120,120), LAYER=1)
				self.driving_seat = None
				self.active_state = self.ST_Idle
			else:
				self.stateSwitch("ENTER")

		elif state == "HOVER":
			self.doAnim(NAME="QJHover", FRAME=(0,100), LAYER=2, BLEND=10)
			self.active_state = self.ST_Active

		elif state == "CRUISE":
			self.doAnim(NAME="QJHover", FRAME=(100,0), LAYER=2, BLEND=10)
			self.data["LANDSTATE"] = "FLY"
			self.active_state = self.ST_Cruise

		elif state == "DOCK":
			self.toggleWeapons(False)
			self.doAnim(NAME="QJDock", FRAME=(0,120), LAYER=2, BLEND=10)
			self.setPhysicsType("NONE")
			self.owner.localLinearVelocity = [0,0,0]
			self.owner.localAngularVelocity = [0,0,0]
			self.data["LINVEL"] = [0,0,0]
			self.data["ANGVEL"] = [0,0,0]
			self.data["DOCKED"] = 120
			self.active_state = self.ST_Docked

	## ACTIVE STATE ##
	def ST_Cruise(self):
		self.getInputs()
		self.data["LANDSTATE"] = "FLY"

		owner = self.objects["Root"]
		gfx = self.objects["GFX"]

		force = self.motion["Force"]
		torque = self.motion["Torque"]
		linV = owner.localLinearVelocity

		tqx = (torque[0])*400
		tqy = torque[1]+force[0]
		if abs(tqy) > 1.0:
			tqy = 1-(2*(tqy<0))
		tqy = tqy*800
		tqz = (torque[2])*(400-linV[1])

		owner.applyTorque((tqx, tqy, tqz), True)

		fry = 60+((force[1]+0.5)*40)

		owner.applyForce((0,fry*owner.mass,0), True)

		owner.applyForce(-self.gravity*owner.mass, False)

		self.data["HUD"]["Power"] = (force[1]+1)*50
		self.data["HUD"]["Lift"] = 0

		t = (force[1]+1)*0.5
		gfx.color[1] += (t-gfx.color[1])*0.1

		if keymap.BINDS["TOGGLEMODE"].tap() == True:
			self.stateSwitch("HOVER")

	def ST_Active(self):
		self.getInputs()

		owner = self.objects["Root"]
		gfx = self.objects["GFX"]

		force = self.motion["Force"]
		torque = self.motion["Torque"]
		linV = owner.localLinearVelocity
		exit = False

		## FORCES ##
		tqx = torque[0]*400
		tqy = torque[1]*400
		tqz = torque[2]*400

		owner.applyTorque((tqx, tqy, tqz), True)

		hv = owner.worldOrientation.inverted()*self.gravity.normalized()
		hv = hv.rotation_difference(Vector((0,0,-1))).to_euler()

		owner["X"] = self.toDeg(hv[0])
		owner["Y"] = self.toDeg(hv[1])
		owner["Z"] = self.toDeg(hv[2])

		for i in [0,1,2]:
			v = self.toDeg(hv[i])
			m = 0
			if i == 0:
				m = 20
			if v < -m:
				v = -m
			if v > m:
				v = m
			hv[i] = v

		hover = Vector((0,0,self.gravity.length*owner.mass))*self.createMatrix(rot=hv, deg=True)

		hover[0] += force[0]*owner.mass*10
		hover[1] += force[1]*owner.mass*10
		hover[2] += force[2]*owner.mass*10

		owner.applyForce(hover, True)

		if self.gravity.length > 0.1:
			up = self.gravity.normalized()
			tx = 0
			ty = up.dot(owner.getAxisVect((-1,0,0)))
			gz = up.dot(owner.getAxisVect((0,0,-1)))
			if gz < 0:
				ty = 1-(2*(ty<0))

			if self.data["LANDSTATE"] == "LAND":
				tx = up.dot(owner.getAxisVect((0,1,0)))
				rayto = owner.worldPosition+self.gravity

				if force[2] < 0.01 and owner.rayCastTo(rayto, 3, "GROUND") != None:
					if linV.length < 10:
						exit = True
					owner.applyForce([0,0,self.gravity.length*owner.mass*-0.5], True)

			owner.applyTorque((tx*owner.mass*20, ty*owner.mass*20, 0), True)

		## WEAPONS ##
		if keymap.BINDS["ATTACK_ONE"].active() == True:
			cls = self.getSlotChild("Gun")
			if cls != None:
				self.sendEvent("WP_FIRE", cls)

		if keymap.BINDS["ATTACK_TWO"].active() == True:
			for slot in ["Missile_L", "Missile_R"]:
				cls = self.getSlotChild(slot)
				if cls != None:
					self.sendEvent("WP_FIRE", cls, "TAP")

		## EXTRAS ##
		owner.addDebugProperty("X", True)
		owner.addDebugProperty("Y", True)
		owner.addDebugProperty("Z", True)

		self.data["HUD"]["Power"] = 0
		self.data["HUD"]["Lift"] = 0

		gfx.color[1] *= 0.95
		steer = torque[2]*0.3
		brake = 0

		if keymap.BINDS["VEH_DESCEND"].active() == True:
			brake = 10

		self.setWheelSteering(steer, "FRONT")
		self.setWheelBrake(brake, "REAR")

		evt = self.getFirstEvent("DOCKING", "ZEPHYR")
		if evt != None:
			pos = evt.getProp("GUIDE")
			trk = evt.getProp("TRACK")
			if pos != None and trk != None:
				vec = trk.worldPosition-owner.worldPosition
				if vec.length > 2:
					exit = "FLY"
				else:
					exit = "DOCK"

					self.doDragForce([10,10,10])
					self.data["HOVER"][0] = 1000

					fw = trk.getAxisVect([0,1,0])
					up = trk.getAxisVect([0,0,1])

					owner.worldPosition += vec*0.01
					owner.alignAxisToVect(fw, 1, 0.02)
					owner.alignAxisToVect(up, 2, 0.05)

					self.sendEvent("DOCKING", evt.sender, "QUINJET")
					self.data["LANDSTATE"] = "FLY"

		if exit == "DOCK":
			if keymap.BINDS["ENTERVEH"].tap() == True:
				self.docking_point = self.getTransformDiff(pos)
				self.stateSwitch("DOCK")
				self.setContainerParent(evt.sender, "Dock")
				self.sendEvent("DOCKING", evt.sender, "QUINJET", "DOCKING")
				owner.localPosition = self.docking_point[0]
				owner.localOrientation = self.docking_point[1]

		elif exit == True:
			if keymap.BINDS["ENTERVEH"].tap() == True:
				self.stateSwitch("EXIT")

		elif exit in [False, "FLY"] and self.data["LANDSTATE"] == "FLY":
			if keymap.BINDS["TOGGLEMODE"].tap() == True:
				self.stateSwitch("CRUISE")

	def ST_Idle(self):
		self.setWheelBrake(1, "REAR")
		owner = self.owner
		gfx = self.objects["GFX"]
		gfx.color[1] *= 0.95

		if self.checkClicked() == True:
			if self.data["DOCKED"] != None:
				self.sendEvent("DOCKING", self.getParent(), "QUINJET", "RELEASE")
			self.stateSwitch("ENTER")

	def ST_Enter(self):
		self.setWheelBrake(1, "REAR")
		self.doCameraToggle()
		owner = self.owner
		gfx = self.objects["GFX"]
		gfx.color[1] *= 0.95

		self.data["GLASSFRAME"] -= 1

		g = 60
		if self.data["DOCKED"] != None:
			g = -60
			if self.data["GLASSFRAME"] < 60:
				fac = (1/120)
				self.owner.localPosition += self.createVector(vec=(0,-2*fac,3*fac))
				ref = self.owner.localOrientation
				ori = self.createMatrix(rot=(-5*fac,0,0), deg=True)
				self.owner.localOrientation = ref*ori

		if self.data["GLASSFRAME"] <= g:
			if self.data["DOCKED"] != None:
				self.removeContainerParent()
			self.stateSwitch()

	def ST_Exit(self):
		self.setWheelBrake(1, "REAR")
		self.doCameraToggle()
		owner = self.owner
		gfx = self.objects["GFX"]
		gfx.color[1] *= 0.95

		self.data["GLASSFRAME"] += 1
		if self.data["GLASSFRAME"] >= 120:
			self.stateSwitch("IDLE")

	def ST_Docked(self):
		owner = self.owner
		gfx = self.objects["GFX"]
		gfx.color[1] *= 0.95

		pos = self.docking_point
		ref = [self.createVector(), self.createMatrix()]

		if self.data["DOCKED"] <= 0:
			owner.localPosition = ref[0]
			owner.localOrientation = ref[1]
			self.docking_point = None
			self.stateSwitch("EXIT")
			self.sendEvent("DOCKING", self.getParent(), "QUINJET", "LOCKED")

		else:
			fac = self.data["DOCKED"]*(1/120)
			owner.localPosition = ref[0].lerp(pos[0], fac)
			owner.localOrientation = (ref[1].to_quaternion().slerp(pos[1].to_quaternion(), fac)).to_matrix()
			self.data["DOCKED"] -= 1


class GatlingGun(weapon.CoreWeapon):

	NAME = "brrt"
	TYPE = "RANGED"

	def defaultData(self):
		self.env_dim = None
		dict = super().defaultData()
		dict["SPIN"] = 0
		return dict

	def ST_Startup(self):
		self.active_post.append(self.PS_Ambient)

	def PS_Ambient(self):
		if self.env_dim == None:
			cls = self.getParent()
			amb = 0
			if cls != None:
				amb = cls.dict.get("DIM", amb)
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		self.objects["Root"].color = self.env_dim
		self.objects["Barrel"].color = self.env_dim

		self.env_dim = None

	def ST_Active(self):
		owner = self.objects["Root"]
		barrel = self.objects["Barrel"]

		fire = self.getFirstEvent("WP_FIRE")

		if fire != None:
			self.data["SPIN"] += 1
			if self.data["SPIN"] > 50:
				self.data["SPIN"] = 50
		else:
			self.data["SPIN"] -= 1
			if self.data["SPIN"] < 0:
				self.data["SPIN"] = 0

		mat = self.createMatrix(rot=(0, self.data["SPIN"], 0), deg=True)
		barrel.localOrientation *= mat

		if self.data["COOLDOWN"] > 0:
			self.data["COOLDOWN"] -= 1

		elif self.data["SPIN"] >= 50 and fire != None:
			plrobj = self.owning_player.objects["Root"]
			sx, sy, sz = fire.getProp("SCALE", [1.5, 1.5, 1.5])
			rnd = logic.getRandomFloat()
			rndx = (logic.getRandomFloat()-0.5)*0.07
			rndy = (logic.getRandomFloat()-0.5)*0.07
			rvec = self.owner.getAxisVect((rndx,5,rndy)).normalized()

			ammo = owner.scene.addObject("AMMO_Bullet", barrel, 50)
			ammo.alignAxisToVect(ammo.getVectTo(base.SC_SCN.active_camera)[1], 2, 1.0)
			ammo.alignAxisToVect(rvec, 1, 1.0)
			ammo["ROOTOBJ"] = plrobj
			ammo["DAMAGE"] = 4
			ammo["LINV"] = plrobj.worldLinearVelocity*(1/60)
			ammo.localScale = (sx, 32+ammo["LINV"].length, sz)
			ammo.color = (1.0, 0.8, 0.5, 1)
			ammo.children[0].localScale = (1, 0.2+(rnd*0.8), 1)
			ammo.children[0].color = fire.getProp("COLOR", [1, 1, 0, 1])

			gfx = base.SC_SCN.addObject("GFX_MuzzleFlash", barrel, 0)
			gfx.worldPosition += self.owner.getAxisVect((0, 0.1, 0.1))
			gfx.setParent(barrel, False, False)
			gfx.localScale = (sx*2, sx*4, sx*2)
			gfx.children[0].color = (1,1,0,1)

			self.data["COOLDOWN"] = 2


class ZephyrCall(base.CoreObject):

	NAME = "Call The Calvary"
	GHOST = True
	CONTAINER = "LOCK"

	def defaultData(self):
		self.env_dim = None
		dict = super().defaultData()
		dict["ZONE"] = self.owner.get("ZONE", "HOME")
		return dict

	def ST_Startup(self):
		owner = self.owner
		self.cooldown = 10
		self.halo = owner.scene.addObject("GFX_Halo", owner, 0)
		self.halo.setParent(owner)
		self.halo.color = (owner.color[0], owner.color[1], owner.color[2], 1.0)
		self.halo["LOCAL"] = True
		self.halo["AXIS"] = None

		owner["RAYCAST"] = None
		owner["RAYNAME"] = ""

	def checkClicked(self):
		if self.owner["RAYCAST"] != None:
			if keymap.BINDS["ACTIVATE"].tap() == True:
				return True
		return False

	def clearRayProps(self):
		self.owner["RAYCAST"] = None

	def ST_Disabled(self):
		owner = self.getOwner()
		ray = self.checkClicked()

		zone = self.data["ZONE"]
		mvd = base.WORLD["MARVEL"]

		if mvd["Frame"] > 0:
			owner["RAYNAME"] = "...fr "+str(mvd["Frame"])
			self.cooldown = 10

		elif self.cooldown > 0:
			owner["RAYNAME"] = "...cd "+str(self.cooldown)
			self.cooldown -= 1

		elif mvd["Map"] == base.CURRENT["Level"]:
			if zone == mvd["CurLZ"]:
				owner["RAYNAME"] = "Send All Clear"
				if ray == True:
					x = ["Lighthouse.blend", "Tahiti.blend"]
					mvd["Map"] = owner.get("MAP", x[x[0]==base.CURRENT["Level"]])
					self.cooldown = 10
			elif zone in SHIPMAN.ship_zones:
				owner["RAYNAME"] = self.NAME+": "+zone
				if ray == True:
					mvd["LZ"] = zone
					self.cooldown = 10
			else:
				owner["RAYNAME"] = "ERROR: Bugle - "+zone+" Not Found"

		else:
			owner["RAYNAME"] = self.NAME
			if ray == True:
				mvd["Map"] = base.CURRENT["Level"]
				mvd["LZ"] = zone
				mvd["CurLZ"] = zone
				self.cooldown = 10


class DockDoor(door.CoreDoor):

	NAME = "QuinJet Bay"
	SPRING = "MOTOR"
	TIME = 5
	LOCK = "Z1QJD"
	ANIM = {"OPEN":(0,120), "CLOSE":(120,0)}

class DockHull(DockDoor):

	def defaultData(self):
		self.env_dim = None
		dict = super().defaultData()
		return dict

	def ST_Startup(self):
		self.active_post.append(self.PS_Ambient)

	def PS_Ambient(self):
		if self.env_dim == None:
			cls = self.getParent()
			amb = 0
			if cls != None:
				amb = cls.dict.get("DIM", amb)
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		self.objects["MeshFL"].color = self.env_dim
		self.objects["MeshFR"].color = self.env_dim
		self.objects["MeshRL"].color = self.env_dim
		self.objects["MeshRR"].color = self.env_dim

		self.env_dim = None

class SwingDoor(door.CoreDoor):

	NAME = "Door"
	SPRING = "SPRING"
	ANIM = {"OPEN":(0,60), "CLOSE":(60,0)}

class SlideDoor(door.CoreDoor):

	NAME = "Security Door"
	SPRING = "MOTOR"
	ANIM = {"OPEN":(0,60), "CLOSE":(60,0)}

class CargoRamp(door.CoreDoor):

	NAME = "Cargo Ramp"
	SPRING = "MOTOR"
	ANIM = {"OPEN":(0,300), "CLOSE":(300,0)}

	def defaultData(self):
		self.env_dim = None
		dict = super().defaultData()
		return dict

	def ST_Startup(self):
		self.active_post.append(self.PS_Ambient)

	def PS_Ambient(self):
		if self.env_dim == None:
			cls = self.getParent()
			amb = 0
			if cls != None:
				amb = cls.dict.get("DIM", amb)
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		self.objects["Mesh"].color = self.env_dim
		self.objects["Mesh2"].color = self.env_dim

		self.env_dim = None


