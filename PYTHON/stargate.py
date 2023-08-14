

from bge import logic

from game3 import base, keymap, world, vehicle, viewport, HUD


if "STARGATE" not in base.WORLD:
	base.WORLD["STARGATE"] = [None, None]

STARGATES = {}

ADDRESS = {

	"MILKYWAY":{
		"1A:1B:1C:1D:1E:1F:1P": "SGC Game",
		"2A:2B:2C:2D:2E:2F:1P": "Abydos Game",
		"1A:2B:1C:2D:1E:2F:1P": "SunlevelUP",
		"1A:1B:1C:1D:1E:1F:1O:1P": "Midway",
		"2A:2B:2C:2D:2E:2F:1O:1P": "Mountain GameTiles",
	},

	"PEGASUS":{
		"1A:1B:1C:1D:1E:1F:1P": "Atlantis Room",
		"2A:2B:2C:2D:2E:2F:1P": "Village Game",
		"1A:2B:1C:2D:1E:2F:1P": "Planet Gravity",
		"1A:1B:1C:1D:1E:1F:1O:1P": "Midway",
		"2A:2B:2C:2D:2E:2F:1O:1P": "Mountain GameTiles"
	}
}


class LayoutGateship(HUD.HUDLayout):

	GROUP = "Core"
	MODULES = [HUD.Stats, HUD.Interact]

class Gateship(vehicle.CoreAircraft):

	NAME = "Puddle Jumper"
	HUDLAYOUT = LayoutGateship #LayoutAircraft

	CAM_TYPE = "FIRST"
	CAM_ORBIT = 1
	CAM_RANGE = (10, 25)
	CAM_ZOOM = 1
	CAM_STEPS = 3
	CAM_HEIGHT = 0.1
	CAM_MIN = 1.0
	CAM_SLOW = 3.0
	CAM_HEAD_G = 0
	CAM_OFFSET = (0,0,1)

	WH_FRONT = 3
	WH_REAR = -3
	WH_WIDTH = 1.8
	WH_HEIGHT = 1.0
	WH_RADIUS = 0.2

	VEH_LENGTH = 0.2

	VEH_ROLL = 0
	VEH_SPRING = 50
	VEH_DAMPING = 10
	VEH_FRICTION = 1

	WHEELS = {
		"Wheel_FR": {},
		"Wheel_FL": {"LEFT":True},
		"Wheel_RR": {"REAR":True},
		"Wheel_RL": {"REAR":True, "LEFT":True} }

	SEATS = {
		"Seat_B": {"NAME":"Ramp",    "DOOR":"Door_1", "CAMERA":[0,0,0], "VISIBLE":False, "SPAWN":[0,-6,-0.3], "STATE":"WALKING"},
		"DHD":    {"NAME":"DHD",     "DOOR":"DHD",    "CAMERA":[0,2.3,0.5], "VISIBLE":False, "SPAWN":[0,0,0], "STATE":"DHD"},
		"Seat_1": {"NAME":"Pilot",   "DOOR":"Seat_1", "CAMERA":[0,0.1,0.75], "ACTION":"SeatTall", "VISIBLE":True, "SPAWN":[0,0,0], "STATE":"DRIVER"},
		"Seat_2": {"NAME":"CoPilot", "DOOR":"Seat_2", "CAMERA":[0,0.1,0.75], "ACTION":"SeatTall", "VISIBLE":True, "SPAWN":[0,0,0], "STATE":"PASSIVE"},
		"Seat_3": {"NAME":"Support", "DOOR":"Seat_3", "CAMERA":[0,0.1,0.75], "ACTION":"SeatTall", "VISIBLE":True, "SPAWN":[0,0,0], "STATE":"PASSIVE"},
		"Seat_4": {"NAME":"Support", "DOOR":"Seat_4", "CAMERA":[0,0.1,0.75], "ACTION":"SeatTall", "VISIBLE":True, "SPAWN":[0,0,0], "STATE":"PASSIVE"}
		}

	AERO = {"POWER":20000, "REVERSE":1.0, "HOVER":0, "LIFT":0, "TAIL":0, "DRAG":(1,1,1)}

	def defaultData(self):
		dict = super().defaultData()
		dict["MODE"] = "CLOSED"
		dict["FRAMES"] = 0
		dict["WALK"] = -3
		dict["DOORSTATE"] = "OPEN"
		dict["DOORFRAMES"] = 360
		dict["SEATFRAMES"] = {"Seat_1":0, "Seat_2":0}
		dict["LASTSTATE"] = "IDLE"

		return dict

	def ST_Startup(self):
		global STARGATES
		if "PEGASUS" not in STARGATES:
			STARGATES["PEGASUS"] = {"Gate":None, "DHD":None}
		self.STARGATE = STARGATES["PEGASUS"]

		self.active_post.append(self.airDrag)
		self.active_post.append(self.airLift)
		self.active_post.append(self.PS_Anim)
		self.stargate = None

		for key in self.objects["DHD_Keys"]:
			obj = self.objects["DHD_Keys"][key]
			obj.color[0] = 0

	def airDrag(self):
		dampLin = 0.0
		dampRot = 0.8

		self.objects["Root"].setDamping(dampLin, dampRot)

		linV = self.objects["Root"].localLinearVelocity

		drag = self.AERO["DRAG"]
		mx = (self.data["MODE"]=="OPEN")
		DRAG_X = linV[0]*drag[0]*(200+(mx*200))
		DRAG_Y = linV[1]*drag[1]*(100+(mx*-50))
		DRAG_Z = linV[2]*drag[2]*(200+(mx*200))

		self.objects["Root"].applyForce((-DRAG_X, -DRAG_Y, -DRAG_Z), True)

	def airLift(self):
		owner = self.objects["Root"]

		grav = -self.gravity
		mass = owner.mass

		owner.applyForce(grav*mass, False)

		if self.data["MODE"] == "OPEN":
			return

		rayto = owner.worldPosition+owner.getAxisVect([0,0,-1])
		rayobj = owner.rayCastTo(rayto, 1.6, "GROUND")

		if rayobj != None and self.motion["Force"][2] < 0.01:
			owner.applyForce([0,0,-mass], True)
			self.setWheelBrake(1, "REAR")

	def setCameraState(self, state=None):
		if state == None:
			state = self.data["CAMERA"]["State"]
		else:
			self.data["CAMERA"]["State"] = state

		if state == "SEAT":
			viewport.setState("SEAT")
			pos = self.SEATS.get(self.driving_seat, {}).get("CAMERA", [0,0,0])
			viewport.setCameraPosition(pos)
			self.setPlayerVisibility(self.driving_seat, False)

		elif state == "FIRST":
			viewport.setState("FIRST")
			viewport.setCameraPosition([0,self.data["WALK"],0.6])

		elif state == "THIRD":
			viewport.setState("THIRD")
			viewport.setCameraPosition(self.CAM_OFFSET)
			self.setPlayerVisibility(self.driving_seat)

		viewport.setEyeHeight(0)
		viewport.setEyePitch(0)

	def assignCamera(self, parent=None, state=None):
		if parent == None:
			parent = self.getOwner()

		viewport.setCamera(self)
		viewport.setParent(parent)

		self.setCameraState(state)

		if self.data["LASTSTATE"] in ["DRIVER", "PASSIVE"]:
			HUD.SetLayout(self, vehicle.LayoutAircraft)

		elif self.data["LASTSTATE"] in ["WALKING", "DHD"]:
			HUD.SetLayout(self, LayoutGateship)

		else:
			HUD.SetLayout(self, None)

	def stateSwitch(self, state=None):
		if state != None:
			pass
		elif self.driving_seat == ".":
			state = "DRIVER"
		else:
			state = self.SEATS[self.driving_seat].get("STATE", "DRIVER")

		self.data["LASTSTATE"] = state
		self.motion["Rotate"] = self.createVector()

		if state == "IDLE":
			if self.removeFromSeat(self.driving_seat) == True:
				self.active_state = self.ST_Idle

		elif state == "DRIVER":
			self.assignCamera(self.seatobj[self.driving_seat], "SEAT")

			self.data["CAMERA"]["Orbit"] = False
			self.data["DOORSTATE"] = "CLOSING"
			self.active_state = self.ST_Active

		elif state == "WALKING":
			self.assignCamera(self.getOwner(), "FIRST")

			self.data["CAMERA"]["Orbit"] = True
			self.setPlayerVisibility(self.driving_seat, False)
			self.active_state = self.ST_Walking

		elif state == "DHD":
			self.assignCamera(self.getOwner(), "SEAT")

			self.data["CAMERA"]["Orbit"] = True
			self.setPlayerVisibility(self.driving_seat, False)
			self.active_state = self.ST_Dialing

		elif state == "PASSIVE":
			self.assignCamera(self.seatobj[self.driving_seat], "SEAT")

			self.data["CAMERA"]["Orbit"] = True
			self.active_state = self.ST_Passive

		elif state == "WAIT":
			self.data["CAMERA"]["Orbit"] = False
			self.active_state = self.ST_Wait

	def PS_Anim(self):
		owner = self.getOwner()

		if self.data["MODE"] == "OPENING":
			self.data["FRAMES"] += 1
		elif self.data["MODE"] == "CLOSING":
			self.data["FRAMES"] -= 1
		if self.data["FRAMES"] <= 0:
			self.data["MODE"] = "CLOSED"
			self.data["FRAMES"] = 0
		elif self.data["FRAMES"] >= 120:
			self.data["MODE"] = "OPEN"
			self.data["FRAMES"] = 120

		for key in ["Pod_L", "Eng_L", "Pod_R", "Eng_R"]:
			obj = self.objects[key]
			self.doAnim(obj, "NONE", (-5,125), MODE="LOOP")
			self.doAnim(obj, SET=self.data["FRAMES"])

		if self.data["DOORSTATE"] == "OPENING":
			self.data["DOORFRAMES"] += 1
		elif self.data["DOORSTATE"] == "CLOSING":
			self.data["DOORFRAMES"] -= 1
		if self.data["DOORFRAMES"] <= 0:
			self.data["DOORSTATE"] = "CLOSED"
			self.data["DOORFRAMES"] = 0
		elif self.data["DOORFRAMES"] >= 360:
			self.data["DOORSTATE"] = "OPEN"
			self.data["DOORFRAMES"] = 360

		self.doAnim("Door", "NONE", (-5,365), MODE="LOOP")
		self.doAnim("Door", SET=self.data["DOORFRAMES"])

		for key in ["Seat_1", "Seat_2", "Seat_3", "Seat_4"]:
			x = -1
			if key == self.driving_seat and self.active_state != self.ST_Wait:
				x = 1
			self.data["SEATFRAMES"][key] = self.data["SEATFRAMES"].get(key, 0)+x
			if self.data["SEATFRAMES"][key] < 0:
				self.data["SEATFRAMES"][key] = 0
			if self.data["SEATFRAMES"][key] > 60:
				self.data["SEATFRAMES"][key] = 60
			obj = self.objects[key]
			self.doAnim(obj, "NONE", (-5,65), MODE="LOOP")
			self.doAnim(obj, SET=self.data["SEATFRAMES"][key])

		for key in ["Col_L", "Col_R", "Col_D"]:
			obj = self.objects[key]
			pod = obj.parent
			pos = obj.localPosition.copy()
			ori = obj.localOrientation.copy()
			obj.removeParent()
			obj.setParent(pod, True, False)
			obj.localPosition = pos
			obj.localOrientation = ori

	def ST_Idle(self):
		if self.checkClicked() == True:
			self.stateSwitch()

	def ST_Walking(self):
		owner = self.objects["Root"]

		self.data["CAMERA"]["State"] = "FIRST"
		self.data["CAMERA"]["Orbit"] = True

		FORWARD = keymap.BINDS["PLR_FORWARD"].axis(clip=False) - keymap.BINDS["PLR_BACKWARD"].axis(clip=False)
		STRAFE = keymap.BINDS["PLR_STRAFERIGHT"].axis(clip=False) - keymap.BINDS["PLR_STRAFELEFT"].axis(clip=False)
		MOVE = keymap.input.JoinAxis(STRAFE, FORWARD)
		MOVE = viewport.getDirection(MOVE)
		MOVE = owner.worldOrientation.inverted()*MOVE

		vec = MOVE-self.motion["Force"]
		if vec.length <= (1/10):
			self.motion["Force"] = MOVE
		else:
			self.motion["Force"] += vec.normalized()*(1/10)

		if self.motion["Force"][1] < 0 and self.data["WALK"] > -3:
			self.data["WALK"] += self.motion["Force"][1]*0.05
		elif self.motion["Force"][1] > 0 and self.data["WALK"] < 2:
			self.data["WALK"] += self.motion["Force"][1]*0.05
		else:
			self.motion["Force"] *= 0

		viewport.setCameraPosition([0,self.data["WALK"],0.6])

		self.rotateCamera()

		self.data["HUD"]["Target"] = (0.5, 0.5)

		rayfrom = viewport.getObject("Rotate").worldPosition
		rvec = owner.worldOrientation.inverted()*viewport.getRayVec()
		x = 180
		key = None
		for i in ["Seat_1", "Seat_2", "Seat_3", "Seat_4", "Door_1", "DHD"]:
			obj = self.objects[i]
			rayto = obj.worldPosition
			tvec = owner.worldOrientation.inverted()*(rayto-rayfrom)
			angle = self.toDeg(rvec.angle(tvec))
			if angle < 30 and angle < x and tvec.length < 2:
				key = i
				self.data["HUD"]["Text"] = obj.get("RAYNAME", i)
				self.data["HUD"]["Color"] = (0,1,0,1)
				x = angle

		if key == "Door_1":
			exit = (MOVE[1]<-0.1 and self.data["WALK"]<=-3)
			if keymap.BINDS["ACTIVATE"].tap() == True:
				if self.data["DOORSTATE"] != "OPEN":
					self.data["DOORSTATE"] = "OPENING"
				else:
					exit = True
			if self.data["DOORSTATE"] == "OPEN" and exit == True:
				self.stateSwitch("IDLE")

		elif key != None and keymap.BINDS["ACTIVATE"].tap() == True:
			self.attachToSeat(self.player_seats[self.driving_seat], key)
			self.data["DOORSTATE"] = "CLOSING"
			self.data["HUD"]["Target"] = None
			self.stateSwitch()

	def ST_Dialing(self):
		owner = self.objects["Root"]

		self.data["CAMERA"]["State"] = "FIRST"
		self.data["CAMERA"]["Orbit"] = True
		self.data["HUD"]["Target"] = (0.5, 0.5)

		exit = False
		if keymap.BINDS["ENTERVEH"].tap() == True:
			self.attachToSeat(self.player_seats[self.driving_seat], "Seat_B")
			self.stateSwitch()
			exit = True

		self.rotateCamera()

		rayfrom = viewport.getObject("Rotate").worldPosition
		rvec = owner.worldOrientation.inverted()*viewport.getRayVec()
		x = 180
		key = None
		for i in ["Seat_1", "Seat_2"]:
			obj = self.objects[i]
			rayto = obj.worldPosition
			tvec = owner.worldOrientation.inverted()*(rayto-rayfrom)
			angle = self.toDeg(rvec.angle(tvec))
			if angle < 30 and angle < x:
				key = i
				self.data["HUD"]["Text"] = obj.get("RAYNAME", i)
				self.data["HUD"]["Color"] = (0,1,0,1)
				x = angle

		if key != None and keymap.BINDS["ACTIVATE"].tap() == True:
			self.attachToSeat(self.player_seats[self.driving_seat], key)
			self.data["DOORSTATE"] = "CLOSING"
			self.data["HUD"]["Target"] = None
			self.stateSwitch()
			exit = True

		if self.stargate == None:
			if self.STARGATE["Gate"] != None:
				self.stargate = self.STARGATE["Gate"]["Data"]
			return

		x = 180
		obj = None
		for key in self.objects["DHD_Keys"]:
			btn = self.objects["DHD_Keys"][key]
			rayto = btn.worldPosition
			tvec = owner.worldOrientation.inverted()*(rayto-rayfrom)
			angle = self.toDeg(rvec.angle(tvec))
			btn.color[0] = 0
			btn["ACTIVE"] = True
			if angle < 10 and angle < x:
				obj = key
				self.data["HUD"]["Text"] = btn.get("RAYNAME", key)
				self.data["HUD"]["Color"] = (0,1,0,1)
				x = angle

			if key in self.stargate["ADDRESS"]:
				btn.color[0] = 1
				btn["ACTIVE"] = False

		if obj != None and exit == False:
			self.objects["DHD_Keys"][obj].color[0] += 0.5

		if obj != None and keymap.BINDS["ACTIVATE"].tap() == True:
			if obj == "Button":
				if self.stargate["DIAL"] == False and "1P" in self.stargate["ADDRESS"]:
					self.stargate["DIAL"] = True
				else:
					self.stargate["ADDRESS"] = []

			elif self.stargate["DIAL"] == False:
				if self.objects["DHD_Keys"][obj]["ACTIVE"] == True and len(self.stargate["ADDRESS"]) < 9:
					self.stargate["ADDRESS"].append(obj)

	def ST_Active(self):
		self.getInputs()

		owner = self.objects["Root"]
		force = self.motion["Force"]
		torque = self.motion["Torque"]
		linV = owner.localLinearVelocity

		if self.data["MODE"] == "OPEN":
			power, hover = self.getEngineForce()
			fac = self.data["POWER"]/self.AERO["POWER"]

			frx = force[0]*4000
			fry = power-(linV[1]*0.5*fac)
			frz = force[2]*4000

			tqx = torque[0]*3000
			tqy = torque[1]*2000
			tqz = torque[2]*3000

			owner.applyTorque([tqx, tqy, tqz], True)

		else:
			self.data["POWER"] = 0
			fac = 0.5+(force[1]*0.5)

			frx = force[0]*1500
			fry = force[1]*1500
			frz = force[2]*1500
			if keymap.SYSTEM["SHIFT"].checkModifiers() == True:
				fry *= 2

			tqx = torque[0]*2000
			tqy = torque[1]*500
			tqz = torque[2]*2000

			owner.applyTorque([tqx, tqy, tqz], True)

		owner.applyForce([frx, fry, frz], True)

		## EXTRAS ##
		self.data["HUD"]["Power"] = abs(fac)*100
		self.data["HUD"]["Lift"] = 50+(force[2]*50)

		if keymap.BINDS["TOGGLEMODE"].tap() == True:
			if self.data["MODE"] == "CLOSED":
				self.data["MODE"] = "OPENING"
			elif self.data["MODE"] == "OPEN":
				self.data["MODE"] = "CLOSING"

		if self.data["CAMERA"]["State"] == "THIRD":
			viewport.setParent(owner)
		else:
			viewport.setParent(self.seatobj[self.driving_seat])

		if keymap.BINDS["ENTERVEH"].tap() == True:
			self.data["POWER"] = 0
			self.stateSwitch("WAIT")

	def ST_Passive(self):
		self.getInputs()
		owner = self.objects["Root"]

		if keymap.BINDS["ENTERVEH"].tap() == True:
			self.stateSwitch("WAIT")

	def ST_Wait(self):
		owner = self.objects["Root"]

		if keymap.BINDS["ENTERVEH"].tap() == True or self.data["SEATFRAMES"].get(self.driving_seat, 0) <= 0:
			self.attachToSeat(self.player_seats[self.driving_seat], "Seat_B")
			self.stateSwitch()


class IrisControl(base.CoreObject):

	NAME = "Iris Control Switch"
	GALAXY = "MILKYWAY"
	UPDATE = False

	def ST_Startup(self):
		self.objects["Root"].color = (0,0,0,1)
		self.active_state = self.ST_Disabled

	def ST_Active(self):
		owner = self.objects["Root"]
		gate = self.STARGATE["Gate"]["Data"]

		if gate["IRIS"]["State"] == "OPEN" and gate["IRIS"]["Timer"] <= 0:
			if self.checkClicked() == True:
				gate["IRIS"]["State"] = "CLOSE"

		elif gate["IRIS"]["State"] == "CLOSE" and gate["IRIS"]["Timer"] >= 120:
			if self.checkClicked() == True:
				gate["IRIS"]["State"] = "OPEN"

		owner.color[0] = (gate["IRIS"]["State"]=="CLOSE")

		owner["RAYCAST"] = None

	def ST_Disabled(self):
		global STARGATES
		if self.GALAXY in STARGATES:
			self.STARGATE = STARGATES[self.GALAXY]
			if self.STARGATE["Gate"] != None:
				self.active_state = self.ST_Active


class CoreGate(base.CoreObject):

	NAME = "Stargate"
	GALAXY = "MILKYWAY"
	GHOST = True
	OFFTIME = 100
	CONTAINER = "WORLD"

	def defaultData(self):
		dict = super().defaultData()
		dict["CHEVRON"] = [0]*9
		dict["ADDRESS"] = []
		dict["MANUAL"] = None
		dict["DIAL"] = False
		dict["TIMER"] = 0
		dict["IRIS"] = {"State":"OPEN", "Timer":0}

		return dict

	def ST_Startup(self):
		global ADDRESS, STARGATES

		if self.GALAXY not in STARGATES:
			STARGATES[self.GALAXY] = {"Gate":None, "DHD":None}

		self.LOOKUP = ADDRESS[self.GALAXY]
		self.STARGATE = STARGATES[self.GALAXY]

		self.STARGATE["Gate"] = self.dict


		del self.objects["Root"]["RAYCAST"]

		self.active_pre.append(self.PR_Iris)

		self.puddle = None
		self.effect = None
		self.back = []

		self.doTrack("START")

		if base.WORLD["STARGATE"][0] == self.GALAXY and base.WORLD["STARGATE"][1] != None:
			self.data["ADDRESS"] = base.WORLD["STARGATE"][1]

		for id in range(len(self.data["CHEVRON"])):
			key = str(int(id+1))
			obj = self.objects["Chevron"][key]
			if len(self.data["ADDRESS"]) >= id+1:
				self.data["CHEVRON"][id] = self.OFFTIME
				obj.color[0] = 1
			else:
				self.data["CHEVRON"][id] = 0
				obj.color[0] = 0
			#self.doAnim(obj, "ChevronKey", (0,0), LAYER=0, PRIORITY=3, MODE="LOOP")

		map = None
		scn = None
		if len(self.data["ADDRESS"]) != 0:
			lookup = ":".join(self.data["ADDRESS"])
			map = self.LOOKUP.get(lookup, "")
			split = map.split("\\")
			map = split[0]+".blend"
			if len(split) >= 2:
				scn = split[1]
			else:
				scn = base.CURRENT["Scene"]

		if map == base.CURRENT["Level"] and scn == base.CURRENT["Scene"]:
			self.doTrack("ON")
			self.addPuddle()
			world.loadObjects("STARGATE", self.puddle)
			self.ST_Shutdown_Set()
			print("STARGATTED")

	def doTrack(self, state):
		pass

	def addPuddle(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]

		self.puddle = scene.addObject("GFX_Puddle", owner, 0)
		self.effect = scene.addObject("GFX_Effect", owner, 0)

		self.puddle.setParent(owner)
		self.effect.setParent(owner)

		self.puddle.color = [1,1,1,0]
		self.effect.color = [1,1,1,1]

		self.setLights("START")

	def doEventHorizon(self, state):
		if state == "END":
			self.doTrack("OFF")
			self.setLights("ZERO")

			if self.puddle != None:
				self.puddle.endObject()
				self.puddle = None
			if self.effect != None:
				self.effect.endObject()
				self.effect = None

			return

		if state in ["ON", "LOAD"] and len(self.data["ADDRESS"]) != 0:
			lookup = ":".join(self.data["ADDRESS"])
			map = self.LOOKUP.get(lookup, "")
			split = map.split("\\")
			map = split[0]
			if len(split) >= 2:
				scn = split[1]
			else:
				scn = None

			if map != "" and base.CURRENT["Level"] != (map+".blend"):
				self.doTrack("ON")
				self.addPuddle()

				self.puddle.localOrientation = self.createMatrix(mirror="XY")
				for child in self.puddle.childrenRecursive:
					child.localPosition[1] *= -1

				self.puddle["MAP"] = map
				self.puddle["SCENE"] = scn
				self.puddle["COLLIDE"] = []

		frame = (0, 60)

		if state == "OFF":
			frame = (60, 0)
			self.setLights("END")

		if state == "LOAD":
			frame = (60, 60)

		if self.puddle != None:
			self.doAnim(OBJECT=self.puddle, NAME="PuddleColor", FRAME=frame)
			self.doAnim(OBJECT=self.effect, NAME="EffectColor", FRAME=frame)

	def setLights(self, state):
		if self.puddle == None:
			return

		point_0 = self.puddle.childrenRecursive["GFX_PuddlePoint_0"]
		point_1 = self.puddle.childrenRecursive["GFX_PuddlePoint_1"]

		if state == "ZERO":
			self.doAnim(OBJECT=point_0, NAME="PointEnergy", FRAME=(0,0))
			self.doAnim(OBJECT=point_1, NAME="PointEnergy", FRAME=(0,0))

		if state == "OFF":
			state = 2
			self.doAnim(OBJECT=point_0, NAME="PointEnergy", FRAME=(160,220))

		elif state == "ON":
			state = -2
			self.doAnim(OBJECT=point_0, NAME="PointEnergy", FRAME=(220,160))

		elif state == "END":
			state = 2
			self.doAnim(OBJECT=point_1, NAME="PointEnergy", FRAME=(140,220))
			if self.data["IRIS"]["Timer"] < 55:
				self.doAnim(OBJECT=point_0, NAME="PointEnergy", FRAME=(140,220))

		elif state == "START":
			state = 0
			self.doAnim(OBJECT=point_1, NAME="PointEnergy", FRAME=(0,100))
			if self.data["IRIS"]["Timer"] < 55:
				self.doAnim(OBJECT=point_0, NAME="PointEnergy", FRAME=(0,100))

	def doPuddle(self):
		if self.puddle == None:
			self.doEventHorizon("LOAD")
			return None

		cur = None
		plr = None
		if "PLAYERS" in base.WORLD:
			cur = base.WORLD["PLAYERS"].get("1", None)
			plr = None
			if cur != None:
				plr = base.PLAYER_CLASSES.get(cur, None)

		player = None

		for hit in self.puddle["COLLIDE"]:
			if getattr(hit, "PORTAL", None) == True and plr != None:
				if hit == plr:
					player = hit
				elif plr in hit.getChildren():
					player = hit

			nrm = self.puddle.getAxisVect([0,-1,0])
			vec = self.puddle.getVectTo(hit.owner)[1]
			if nrm.dot(vec) < 0.01:
				if hit not in self.back:
					self.back.append(hit)

		clr = []
		for chk in self.back:
			if chk not in self.puddle["COLLIDE"]:
				clr.append(chk)

		if player in self.back:
			player = None

		for i in clr:
			self.back.remove(i)

		self.puddle["COLLIDE"] = []

		if self.data["IRIS"]["State"] == "OPEN":
			return player
		return None

	def clearRayProps(self):
		return

	def PR_Iris(self):
		pass

	def ST_Disabled(self):
		check = len(self.data["ADDRESS"])
		lock = True

		#if self.data["MANUAL"] != None:
		#	self.data["ADDRESS"].append(self.data["MANUAL"])
		#	self.doAnim(NAME="7", FRAME=(0, 100))
		#	self.data["MANUAL"] = None

		for id in range(len(self.data["CHEVRON"])):
			key = id+1
			obj = self.objects["Chevron"][str(int(key))]

			if check >= key:
				if self.data["CHEVRON"][id] < 20:
					self.data["CHEVRON"][id] += 1
					lock = False
				else:
					self.data["CHEVRON"][id] = self.OFFTIME
			else:
				if self.data["CHEVRON"][id] > 0:
					self.data["CHEVRON"][id] -= 1

			obj.color[0] = self.data["CHEVRON"][id]/20

		if self.data["DIAL"] == True and lock == True:
			lookup = ":".join(self.data["ADDRESS"])
			if lookup in self.LOOKUP:
				print(lookup)
				self.ST_Active_Set()
			else:
				self.data["DIAL"] = False
				self.data["ADDRESS"] = []

	def ST_Active_Set(self):
		self.data["DIAL"] = None
		self.data["TIMER"] = 0
		self.active_state = self.ST_Active
		self.doEventHorizon("ON")

	def ST_Active(self):
		self.data["TIMER"] += 1

		player = self.doPuddle()

		if player != None:
			gd = logic.globalDict
			map = self.puddle.get("MAP", "")+".blend"
			scn = self.puddle.get("SCENE", None)
			door = self.objects["Root"].name
			if map in gd["BLENDS"]:
				base.WORLD["STARGATE"] = [self.GALAXY, self.data["ADDRESS"]]
				self.puddle["MAP"] = ""

				## LAUNDERING FIX ##
				lp, lr = player.getTransformDiff(self.puddle, cmp=True)
				player.dict["Zone"] = [lp, lr]
				player.dict["Zone"][0][1] *= -1
				## END ##

				world.sendObjects(map, "STARGATE", [player])
				self.data["DIAL"] = False
				self.data["ADDRESS"] = []
				self.active_state = self.ST_Disabled
				world.openBlend(map, scn)

		elif self.data["TIMER"] > 36000 or len(self.data["ADDRESS"]) == 0:
			self.ST_Shutdown_Set()

	def ST_Shutdown_Set(self):
		self.data["DIAL"] = None
		self.data["TIMER"] = 10
		base.WORLD["STARGATE"] = [None, None]
		self.active_state = self.ST_Shutdown

	def ST_Shutdown(self):
		check = True

		if self.data["TIMER"] > 1:
			self.data["TIMER"] += 1
			if self.data["TIMER"] > 30:
				self.data["TIMER"] = 0
				self.data["ADDRESS"] = []
				self.doEventHorizon("OFF")
			return

		for id in range(len(self.data["CHEVRON"])):
			key = id+1
			obj = self.objects["Chevron"][str(int(key))]

			if self.data["CHEVRON"][id] > 0:
				self.data["CHEVRON"][id] -= 1
				check = False

			fac = self.data["CHEVRON"][id]
			if self.data["CHEVRON"][id] > 20:
				fac = 20

			obj.color[0] = (fac/20)

		if check == True:
			self.ST_Disabled_Set()

	def ST_Disabled_Set(self):
		self.data["DIAL"] = False
		self.data["ADDRESS"] = []
		self.active_state = self.ST_Disabled
		self.doEventHorizon("END")

	def PS_Chevron(self):
		pass


class CoreDHD(base.CoreObject):

	NAME = "Stargate DHD"
	GALAXY = "MILKYWAY"
	OFFTIME = 100
	CONTAINER = "WORLD"

	def defaultData(self):
		dict = super().defaultData()
		dict["TIMER"] = 0
		dict["ACTIVE"] = True
		dict["BUTTONS"] = {}

		return dict

	def ST_Startup(self):
		global ADDRESS, STARGATES

		if self.GALAXY not in STARGATES:
			STARGATES[self.GALAXY] = {"Gate":None, "DHD":None}

		self.STARGATE = STARGATES[self.GALAXY]

		self.STARGATE["DHD"] = self.dict

		self.stargate = None

		del self.objects["Root"]["RAYCAST"]
		del self.objects["Button"]["GROUND"]

		for key in self.objects["Keys"]:
			self.data["BUTTONS"][key] = 0
			obj = self.objects["Keys"][key]
			obj["RAYCAST"] = None
			obj["RAYNAME"] = key
			obj.color = [0,0,0,1]

			del obj["GROUND"]

		self.objects["Button"]["RAYCAST"] = None
		self.objects["Button"]["RAYNAME"] = "Enter"
		self.objects["Button"].color = [0,0,0,1]

	def doButton(self, key, fade):
		obj = self.objects["Keys"][key]

		if key in self.stargate["ADDRESS"]:
			self.data["BUTTONS"][key] += 1
			if self.data["BUTTONS"][key] >= fade:
				self.data["BUTTONS"][key] = self.OFFTIME
				obj.color[0] = 1
			else:
				obj.color[0] = self.data["BUTTONS"][key]/fade

		else:
			self.data["BUTTONS"][key] -= 1
			if self.data["BUTTONS"][key] <= 0 or fade <= 0:
				self.data["BUTTONS"][key] = 0
				obj.color[0] = 0.5*(obj["RAYCAST"]!=None)
			elif self.data["BUTTONS"][key] > fade:
				obj.color[0] = 1
			else:
				obj.color[0] = (self.data["BUTTONS"][key]/fade)

	def checkClicked(self, obj):
		if obj["RAYCAST"] != None:
			if keymap.BINDS["ACTIVATE"].tap() == True:
				return True
			return False
		return None

	def clearRayProps(self):
		for key in self.objects["Keys"]:
			self.doButton(key, 20)
			self.objects["Keys"][key]["RAYCAST"] = None

		self.objects["Button"]["RAYCAST"] = None

	## STATE IDLE ##
	def ST_Disabled(self):
		button = self.objects["Button"]

		if self.data["ACTIVE"] == False:
			if self.data["TIMER"] < 20:
				self.data["TIMER"] += 1
				button.color[0] = self.data["TIMER"]/20
			else:
				if len(self.stargate["ADDRESS"]) > 0:
					self.stargate["DIAL"] = True
				self.data["TIMER"] = self.OFFTIME
				button.color[0] = 1
				self.active_state = self.ST_Active
			return

		for key in self.objects["Keys"]:
			obj = self.objects["Keys"][key]
			chk = self.checkClicked(obj)
			if chk == True:
				self.stargate["ADDRESS"].append(key)

		if self.stargate["DIAL"] == True:
			self.data["ACTIVE"] = False
			print(self.NAME, "AUTO-DIAL")
		elif self.checkClicked(button) == True and self.data["TIMER"] <= 0:
			self.data["ACTIVE"] = False
		else:
			button.color[0] = 0
			self.data["TIMER"] = 0
			self.data["ACTIVE"] = True

	## STATE ACTIVE ##
	def ST_Active(self):
		button = self.objects["Button"]
		button.color[0] = 1

		if self.checkClicked(button) == True or len(self.stargate["ADDRESS"]) == 0:
			self.stargate["ADDRESS"] = []
			self.active_state = self.ST_Shutdown

	## SHUTDOWN STATE ##
	def ST_Shutdown(self):
		self.data["TIMER"] -= 1

		if self.data["TIMER"] <= 0:
			self.data["TIMER"] = 0
			self.objects["Button"].color[0] = 0
		elif self.data["TIMER"] < 20:
			self.objects["Button"].color[0] = (self.data["TIMER"]/20)
		else:
			self.objects["Button"].color[0] = 1

		if self.data["TIMER"] <= 0:
			self.data["ACTIVE"] = True
			self.active_state = self.ST_Disabled

	def RUN(self):
		if self.stargate == None:
			if self.STARGATE["Gate"] != None:
				self.stargate = self.STARGATE["Gate"]["Data"]
				for key in self.objects["Keys"]:
					self.doButton(key, 0)
			return

		self.runPre()
		self.runStates()
		self.runPost()
		self.clearRayProps()


class RedGate(CoreGate):

	NAME = "Milkyway Stargate"
	RING = ["1P", "2J", "1J", "1K", "1N", "1B",
		"1S", "2M", "1M", "2B", "1H", "1F",
		"__", "2H", "2P", "2S", "2I", "2G",
		"1Q", "1L", "1I", "1R", "2F", "1D",
		"2K", "2E", "2N", "2A", "1C", "2R",
		"2O", "1O", "2C", "1E", "2Q", "2L",
		"1G", "1A", "2D"]

	def doTrack(self, state):
		if state == "DIALING":
			self.objects["Track"].applyRotation((0, 0.01, 0), True)

	def PR_Iris(self):
		iris = self.objects["IrisRig"]
		mesh = self.objects["IrisMesh"]
		COL = self.objects["IrisCOL"]

		data = self.data["IRIS"]

		if data["State"] == "OPEN" and data["Timer"] >= 0:
			#COL.reinstancePhysicsMesh()
			#COL.replaceMesh(COL.meshes[0], True, True)

			data["Timer"] -= 1
			if data["Timer"] == 120:
				self.setLights("ON")

		elif data["State"] == "CLOSE" and data["Timer"] <= 120:
			#COL.reinstancePhysicsMesh()
			#COL.replaceMesh(COL.meshes[0], True, True)

			data["Timer"] += 1
			if data["Timer"] == 60:
				self.setLights("OFF")

		self.doAnim(OBJECT=iris, NAME="IrisAction", FRAME=(-5,125), MODE="LOOP")
		self.doAnim(OBJECT=iris, SET=data["Timer"])

		COL.reinstancePhysicsMesh()
		mesh.visible = True #(data["Timer"]>0)


class RedDHD(CoreDHD):

	NAME = "Milkyway DHD"


class BlueGate(CoreGate):

	NAME = "Pegasus Stargate"
	GALAXY = "PEGASUS"

	def doTrack(self, state):
		if state == "OFF" or state == "START":
			self.objects["Track"].color[0] = 0
		if state == "ON" or state == "DIALING":
			self.objects["Track"].color[0] = 1


class BlueDHD(CoreDHD):

	NAME = "Pegasus DHD"
	GALAXY = "PEGASUS"


