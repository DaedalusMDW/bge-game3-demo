

from bge import logic

from game3 import base, world, door, vehicle, weapon, keymap, HUD, viewport

from mathutils import Vector, Matrix


if "MARVEL" not in base.WORLD:
	dict = {"Object":"Zephyr1", "Data":None, "Portal":None}
	base.WORLD["MARVEL"] = {"Ship":dict, "Dict":None, "Map":"", "Frame":0, "QJ":False}


class ZephyrShip(base.CoreObject):

	CONTAINER = "WORLD"
	UPDATE = "WORLD"

	ANIMSET = ""
	ANIMFRAMES = {"Depart":420, "Land":450}

	HUDLAYOUT = HUD.LayoutCinema

	def defaultData(self):
		dict = super().defaultData()
		dict["HUD"] = {"Subtitles":None}
		return dict

	def doLoad(self):
		if base.WORLD["MARVEL"]["Dict"] == None:
			base.WORLD["MARVEL"]["Dict"] = self.dict
			base.WORLD["MARVEL"]["Map"] = base.CURRENT["Level"]
			base.WORLD["MARVEL"]["CurMap"] = base.CURRENT["Level"]
			self.active_state = self.ST_Disabled

		self.dict = base.WORLD["MARVEL"]["Dict"]
		self.owner["DICT"] = self.dict

		super().doLoad()

	def ST_Startup(self):
		owner = self.owner
		scene = owner.scene

		self.ship_obj = None
		self.ship_class = None
		self.ship_anim = None

		if base.WORLD["MARVEL"]["Map"] == base.WORLD["MARVEL"]["CurMap"] == base.CURRENT["Level"]:
			print("Zephyr Insta-Spawn")
			self.doShipSpawn()

	def doShipSpawn(self):
		owner = self.owner
		scene = owner.scene

		if self.ship_anim != None:
			self.ship_anim.endObject()
			self.ship_anim = None

		base.WORLD["MARVEL"]["Map"] = base.CURRENT["Level"]
		base.WORLD["MARVEL"]["CurMap"] = base.CURRENT["Level"]

		if self.ship_obj == None:
			self.ship_obj = scene.addObject("Zephyr1", owner, 0)
			self.ship_obj["DICT"] = base.WORLD["MARVEL"]["Ship"]
			self.ship_class = base.GETCLASS(self.ship_obj)

		if base.CURRENT["Level"]+owner.name in base.PROFILE["Portal"]:
			del base.PROFILE["Portal"][base.CURRENT["Level"]+owner.name]

		self.active_state = self.ST_Disabled

	def doShipCinematic(self, mode="Depart"):
		owner = self.owner
		scene = owner.scene

		if self.ship_class != None:
			self.ship_class.packObject(True, None)
			self.ship_class = None
			self.ship_obj = None
			print("ZEPHYR DEPART")

		self.ship_anim = scene.addObject("ZephyrCinematic", owner, 0)
		if owner.get("ANIMWORLD", False) == True:
			self.ship_anim.worldPosition = -base.ORIGIN_OFFSET
			self.ship_anim.worldOrientation = self.createMatrix()

		env = scene.addObject("Zephyr1", owner, 0)
		env.setParent(self.ship_anim, False, False)

		msh = scene.addObject("Zephyr1.Mesh", owner, 0)
		msh.setParent(env, False, False)
		#ins = scene.addObject("Zephyr1.Floors", owner, 0)
		#ins.setParent(env, False, False)
		gfx = scene.addObject("Zephyr1.GFX", owner, 0)
		gfx.setParent(env, False, False)
		if base.WORLD["MARVEL"]["QJ"] == True:
			qjd = scene.addObject("Zephyr1.QJD", owner, 0)
			qjd.setParent(env, False, False)

		cam = self.ship_anim.children["ZephyrCinematic.Camera"]
		cam.near = base.config.CAMERA_CLIP[0]
		cam.far = base.config.CAMERA_CLIP[1]
		name = owner.get("ANIMNAME", self.ANIMSET)
		end = owner.get(mode.upper()+"FRAMES", self.ANIMFRAMES[mode])
		self.doAnim(env, "Zephyr."+name+mode+"Ship", (0,end))
		self.doAnim(cam, "Zephyr."+name+mode+"Camera", (0,end))
		self.doAnim(gfx, "Zephyr."+name+mode+"GFX", (0,end))

		base.WORLD["MARVEL"]["CurMap"] = ""
		base.WORLD["MARVEL"]["Frame"] = end

		if scene.active_camera == base.SC_CAM:
			scene.active_camera = cam

		self.active_state = self.ST_Active

	def ST_Active(self):
		owner = self.owner
		scene = owner.scene

		if base.WORLD["MARVEL"]["Frame"] <= 0:
			if base.WORLD["MARVEL"]["Map"] != base.CURRENT["Level"]:
				self.active_state = self.ST_Disabled
				if scene.active_camera == self.ship_anim.children["ZephyrCinematic.Camera"]:
					base.PROFILE["Portal"][base.WORLD["MARVEL"]["Map"]+owner.name] = {}
					world.openBlend(base.WORLD["MARVEL"]["Map"])
				else:
					self.ship_anim.endObject()
					self.ship_anim = None
			else:
				self.doShipSpawn()
		else:
			base.WORLD["MARVEL"]["Frame"] -= 1

	def ST_Disabled(self):
		if base.WORLD["MARVEL"]["Map"] != base.CURRENT["Level"]:
			if base.WORLD["MARVEL"]["CurMap"] == base.CURRENT["Level"]:
				self.doShipCinematic("Depart")

		elif base.WORLD["MARVEL"]["Map"] == base.CURRENT["Level"]:
			if base.WORLD["MARVEL"]["CurMap"] != base.CURRENT["Level"]:
				self.doShipCinematic("Land")


class Zephyr(world.DynamicWorldTile):

	NAME = "Zephyr One"
	CONTAINER = "WORLD"
	UPDATE = "WORLD"
	OBJ_HIGH = ["Mesh", "Floors"]
	OBJ_LOW  = ["Mesh"]
	OBJ_PROXY = ["Mesh"]

	LOD_ACTIVE = 500
	LOD_FREEZE = 1000
	LOD_PROXY = 5000

	def defaultData(self):
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

	def ST_Disabled(self):
		## LODS ##
		lod = self.getLodLevel()
		if self.lod_state != lod:
			self.setLodState(lod)
		if lod != "ACTIVE":
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
			rayto = self.objects["Guide"].worldPosition.copy()
			rayfrom = rayto+self.owner.getAxisVect([0,0,6])

			rayobj, raypnt, raynrm = self.owner.rayCast(rayto, rayfrom, 7, "", 1, 0, 0)

			if rayobj != None:
				cls = rayobj.get("Class", None)
				self.sendEvent("DOCKING", cls, "ZEPHYR", GUIDE=self.objects["Guide"])

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
			obj.color = (0,0,0,1)
			if base.CURRENT["Level"] == (key+".blend"):
				obj.color = (0,1,0,1)
			elif obj.get("RAYCAST", None) != None:
				obj.color = (1,0,0,1)
				if keymap.BINDS["ACTIVATE"].tap() == True:
					base.WORLD["MARVEL"]["Map"] = key+".blend"
			obj["RAYCAST"] = None
			obj["RAYNAME"] = obj.get("RAYNAME", key)

	def PS_DoorGrav(self):
		objlist = self.objects["Container"]

		for cls in self.getChildren():
			if cls.NAME == "Cargo Ramp":
				objlist["CBD"].worldOrientation = cls.objects["Panel"][""].worldOrientation.copy()
			if cls.owner.name == "Z1Dock":
				if self.data["DOCKED"] not in ["INIT", "NONE"] or self.getFirstEvent("DOCKING", "QUINJET") != None:
					self.sendEvent("INTERACT", cls, LOCK="Z1QJD")
			if cls.owner.name == "Z1DockDoor":
				if self.data["DOCKED"] == "LOCKED":
					self.sendEvent("INTERACT", cls, LOCK="Z1QJD")


class QuinJet(vehicle.CoreAircraft):

	NAME = "QuinJet"
	LANDACTION = "QJLand"
	LANDFRAMES = [100, 0]

	INVENTORY = {"Gun_L":"WP_ZCannon", "Gun_R":"WP_ZCannon", "Missile_L":"WP_ZMissile", "Missile_R":"WP_ZMissile"}
	SLOTS = {"ONE":"Gun", "TWO":"Missile"}

	CAM_RANGE = (20, 36)
	CAM_ZOOM = 3
	CAM_MIN = 1
	CAM_SLOW = 5
	CAM_HEIGHT = 0.1
	CAM_HEAD_G = 25
	CAM_OFFSET = (0,0,1)

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

		self.doAnim(NAME="QJGlass", FRAME=(g,g), LAYER=1)
		self.data["GLASSFRAME"] = g

		self.doLandingGear(init=True)
		self.active_post.append(self.airDrag)

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
			self.active_state = self.ST_Active

		elif state == "ENTER":
			self.assignCamera()
			self.data["GLASSFRAME"] = 120
			if self.data["DOCKED"] != None:
				self.doAnim(NAME="QJDock", FRAME=(180,0), LAYER=2, BLEND=10)
			self.doAnim(NAME="QJGlass", FRAME=(120,0), LAYER=1)
			self.active_state = self.ST_Enter

		elif state == "EXIT":
			self.data["GLASSFRAME"] = g
			self.doAnim(NAME="QJGlass", FRAME=(g,120), LAYER=1)
			self.active_state = self.ST_Exit

		elif state == "IDLE":
			if self.removeFromSeat(self.driving_seat, force=None) == True:
				self.data["GLASSFRAME"] = 120
				self.doAnim(NAME="QJGlass", FRAME=(120,120), LAYER=1)
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
		mesh = self.objects["Mesh"]

		force = self.motion["Force"]
		torque = self.motion["Torque"]
		linV = owner.localLinearVelocity

		tqx = (torque[0])*400
		tqy = (torque[1]+force[0])*800
		tqz = (torque[2])*(400-linV[1])

		owner.applyTorque((tqx, tqy, tqz), True)

		fry = 60+((force[1]+0.5)*40)

		owner.applyForce((0,fry*owner.mass,0), True)

		owner.applyForce(-self.gravity*owner.mass, False)

		self.data["HUD"]["Power"] = (force[1]+1)*50
		self.data["HUD"]["Lift"] = 0

		t = (force[1]+1)*0.5
		mesh.color[1] += (t-mesh.color[1])*0.1

		if keymap.BINDS["TOGGLEMODE"].tap() == True:
			self.stateSwitch("HOVER")

	def ST_Active(self):
		self.getInputs()

		owner = self.objects["Root"]
		mesh = self.objects["Mesh"]

		force = self.motion["Force"]
		torque = self.motion["Torque"]
		linV = owner.localLinearVelocity

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
			ty = up.dot(owner.getAxisVect((-1,0,0)))
			gz = up.dot(owner.getAxisVect((0,0,-1)))
			if gz < 0:
				ty = 1-(2*(ty<0))

			owner.applyTorque((0, ty*owner.mass*20, 0), True)

			if self.data["LANDSTATE"] == "LAND":
				rayto = owner.worldPosition+self.gravity

				if force[2] < 0.01 and owner.rayCastTo(rayto, 3, "GROUND") != None:
					owner.applyForce([0,0,self.gravity.length*owner.mass*-0.5], True)

		## WEAPONS ##
		for slot in self.data["SLOTS"]:
			for side in ["_L", "_R"]:
				key = self.data["SLOTS"][slot]
				cls = self.getSlotChild(slot+side)
				if cls != None:
					#if keymap.BINDS[key].tap() == True:
					cls.stateSwitch(True)
					if slot == "Gun" and keymap.BINDS["ATTACK_ONE"].active() == True:
						self.sendEvent("WP_FIRE", cls)
					if slot == "Missile" and keymap.BINDS["ATTACK_TWO"].active() == True:
						self.sendEvent("WP_FIRE", cls, "TAP")

		## EXTRAS ##
		owner.addDebugProperty("X", True)
		owner.addDebugProperty("Y", True)
		owner.addDebugProperty("Z", True)

		self.data["HUD"]["Power"] = 0
		self.data["HUD"]["Lift"] = 0

		mesh.color[1] *= 0.95
		steer = torque[2]*0.3
		brake = 0

		if keymap.BINDS["VEH_DESCEND"].active() == True:
			brake = 10

		self.setWheelSteering(steer, "FRONT")
		self.setWheelBrake(brake, "REAR")

		evt = self.getFirstEvent("DOCKING", "ZEPHYR")
		if evt != None:
			pos = evt.getProp("GUIDE")
			if pos != None:
				self.doDragForce([10,10,10])
				self.data["HOVER"][0] = 1000

				fw = pos.getAxisVect([0,1,0])
				up = -self.gravity.normalized() #pos.getAxisVect([0,0,1])
				vec = (pos.worldPosition+(up*3))-owner.worldPosition
				owner.worldPosition += vec*0.01
				owner.alignAxisToVect(fw, 1, 0.02)
				owner.alignAxisToVect(up, 2, 0.05)
				self.sendEvent("DOCKING", evt.sender, "QUINJET")
				self.data["LANDSTATE"] = "FLY"

				if keymap.BINDS["ENTERVEH"].tap() == True:
					self.docking_point = self.getTransformDiff(pos)
					self.stateSwitch("DOCK")
					self.setContainerParent(evt.sender, "Dock")
					self.sendEvent("DOCKING", evt.sender, "QUINJET", "DOCKING")
					owner.localPosition = self.docking_point[0]
					owner.localOrientation = self.docking_point[1]

				for slot in self.data["SLOTS"]:
					for side in ["_L", "_R"]:
						key = self.data["SLOTS"][slot]
						cls = self.getSlotChild(side+slot)
						if cls != None:
							cls.stateSwitch(False)

		elif keymap.BINDS["ENTERVEH"].tap() == True and linV.length < 10:
			self.stateSwitch("EXIT")

		elif keymap.BINDS["TOGGLEMODE"].tap() == True:
			self.stateSwitch("CRUISE")

	def ST_Idle(self):
		self.setWheelBrake(1, "REAR")
		owner = self.owner
		mesh = self.objects["Mesh"]
		mesh.color[1] *= 0.95

		if self.checkClicked() == True:
			if self.data["DOCKED"] != None:
				self.sendEvent("DOCKING", self.getParent(), "QUINJET", "RELEASE")
			self.stateSwitch("ENTER")

	def ST_Enter(self):
		self.setWheelBrake(1, "REAR")
		self.doCameraToggle()
		owner = self.owner
		mesh = self.objects["Mesh"]
		mesh.color[1] *= 0.95

		self.data["GLASSFRAME"] -= 1

		g = 60
		if self.data["DOCKED"] != None:
			g = -60
			if self.data["GLASSFRAME"] < 60:
				fac = (1/120)
				self.owner.localPosition += self.createVector(vec=(0,0,3*fac))
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
		mesh = self.objects["Mesh"]
		mesh.color[1] *= 0.95

		self.data["GLASSFRAME"] += 1
		if self.data["GLASSFRAME"] >= 120:
			self.stateSwitch("IDLE")

	def ST_Docked(self):
		owner = self.owner
		mesh = self.objects["Mesh"]
		mesh.color[1] *= 0.95

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


class ZephyrCall(base.CoreObject):

	NAME = "Call The Calvary"
	GHOST = True

	def ST_Startup(self):
		owner = self.owner
		self.cooldown = 10
		self.halo = owner.scene.addObject("GFX_Halo", owner, 0)
		self.halo.setParent(owner)
		self.halo.color = (owner.color[0], owner.color[1], owner.color[2], 1.0)
		self.halo["LOCAL"] = True
		self.halo["AXIS"] = None

	def ST_Disabled(self):
		if base.WORLD["MARVEL"]["Frame"] > 0:
			self.owner["RAYNAME"] = "..."
			self.cooldown = 10
		elif self.cooldown > 0:
			self.owner["RAYNAME"] = "..."
			self.cooldown -= 1
		elif base.WORLD["MARVEL"]["Map"] == base.CURRENT["Level"]:
			self.owner["RAYNAME"] = "Send All Clear"
			if self.checkClicked() == True:
				x = ["Lighthouse.blend", "Tahiti.blend"]
				base.WORLD["MARVEL"]["Map"] = self.owner.get("MAP", x[x[0]==base.CURRENT["Level"]])
				self.cooldown = 10
		else:
			self.owner["RAYNAME"] = self.NAME
			if self.checkClicked() == True:
				base.WORLD["MARVEL"]["Map"] = base.CURRENT["Level"]
				base.WORLD["MARVEL"]["CurMap"] = None
				self.cooldown = 10


class DockDoor(door.CoreDoor):

	NAME = "QuinJet Bay"
	SPRING = "MOTOR"
	TIME = 5
	LOCK = "Z1QJD"
	ANIM = {"OPEN":(0,120), "CLOSE":(120,0)}

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


