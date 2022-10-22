
## GAME OBJECTS ##

from mathutils import Vector
from bge import logic

from game3 import base, input, keymap, world, powerup, weapon, vehicle
from PYTHON import level


SILVERBIRD = None


def RUN(cont):
	global SILVERBIRD

	level.INIT(cont)

	if base.GAME_STATE == "DONE" and base.LEVEL.get("FIRSTRUN", False) == False:
		name = base.WORLD["PLAYERS"].get("1", "")
		plr = base.PLAYER_CLASSES.get(name, None)
		if plr != None:
			for cls in logic.UPDATELIST:
				if cls.owner.name == "Silverbird" and plr.container_parent != cls:
					print("SILVERBIRD FOUND - ATTEMPTING BIND:", cls, plr)
					cls.attachToSeat(plr, "Seat_1")
					cls.stateSwitch()
					SILVERBIRD = cls
					base.LEVEL["FIRSTRUN"] = True
					break


def PARKING(cont):
	owner = cont.owner
	cls = SILVERBIRD

	if "_SIZE" not in owner:
		sx = owner.get("X", 1)
		sy = owner.get("Y", 1)
		sz = owner.get("Z", 1)
		owner["_SIZE"] = (sx, sy, sz)
		obj = owner.children.get(owner.name+".Spawn", owner)
		owner["_SPAWN"] = obj.worldPosition

	if cls == None:
		return

	for chkpnt in cls.getOriginBounds():
		pnt = Vector(chkpnt)-owner.worldPosition
		pnt = owner.worldOrientation.inverted()*pnt

		check = True
		for i in [0,1,2]:
			if abs(pnt[i]) > owner["_SIZE"][i]:
				return

	cls.sendEvent("SILVERBIRD", cls, "PARKING", SPAWN=owner["_SPAWN"])

	if cls.active_state == cls.ST_Idle:
		cls.getOwner().worldPosition = owner.worldPosition
		cls.getOwner().worldOrientation = owner.worldOrientation


class LaserUpgrade(powerup.CorePowerup):

	NAME = "Laser Level"
	WAIT = -1
	DURATION = -1
	SCALE = 2
	STACK_GROUP = "LASER_POWER"
	STACK_TYPE = "ADD"
	STACK_LIMIT = 3
	MODIFIER = {"LASER_POWER":1}


class LaserQuad(powerup.CorePowerup):

	NAME = "Quad Lasers"
	WAIT = -1
	DURATION = -1
	SCALE = 2
	STACK_GROUP = "LASER_QUAD"
	STACK_TYPE = "ADD"
	STACK_LIMIT = 1
	MODIFIER = {"LASER_QUAD":True}


class MissilePack(powerup.CorePowerup):

	NAME = "Missiles"
	WAIT = -1
	SCALE = 2
	CAMPING = True
	MODIFIER = {}

	def defaultData(self):
		dict = super().defaultData()
		dict["COLLECTED"] = 0
		dict["AMMO"] = 0
		return dict

	def ST_Startup(self):
		self.active_post.append(self.PS_AmmoVis)

	def checkData(self, cls):
		self.sendEvent("POWERUP", cls, "CHECK", MISSILES=4)
		evt = self.getFirstEvent("POWERUP", "CHECK")
		if evt != None:
			ct = evt.getProp("MISSILES", 0)
			ma = 4-self.data["COLLECTED"]
			if ct > 0:
				if ct > ma:
					ct = ma
				self.data["AMMO"] = ct
				return True
		return False

	def sendPowerup(self):
		dict = {"MISSILES":self.data["AMMO"]}
		self.data["COLLECTED"] += self.data["AMMO"]
		self.data["AMMO"] = 0
		return dict

	def equipItem(self, cls, load=False):
		super().equipItem(cls, load)
		if self.data["COLLECTED"] < 4:
			self.data["COOLDOWN"] = 0

	def PS_AmmoVis(self):
		for i in [1,2,3,4]:
			self.objects[str(i)].visible = (self.data["COLLECTED"]<i)


class Shield(powerup.CoreStats):

	NAME = "Shield"
	WAIT = -1
	SCALE = 2
	MODIFIER = {"HEALTH":50, "LIMIT":195}


class Energy(powerup.CoreStats):

	NAME = "Energy"
	WAIT = -1
	SCALE = 2
	MODIFIER = {"ENERGY":20, "LIMIT":95}


class EnergyContainer(world.DynamicWorldTile):

	def getLodLevel(self):
		return "ACTIVE"

	def checkCoords(self, cls):
		if cls.CONTAINER == "LOCK" or cls == self:
			return None

		for chkpnt in cls.getOriginBounds():
			pnt = self.getLocalSpace(self.owner, chkpnt)

			if abs(pnt[0]) > self.owner.get("X", 3):
					return False
			if abs(pnt[1]) > self.owner.get("Y", 3):
					return False
			if abs(pnt[2]) > self.owner.get("Z", 3):
					return False

			return True

		return False

	def applyContainerProps(self, cls):
		cls.gravity = self.createVector()
		cls.air_drag = 1.0
		cls.env_dim = (1.5, 1.5, 1.0, 1)
		cls.addModifier(ENERGY=0.5)

class GreenContainer(world.DynamicWorldTile):

	def getLodLevel(self):
		return "ACTIVE"

	def checkCoords(self, cls):
		if cls.CONTAINER == "LOCK" or cls == self:
			return None

		for chkpnt in cls.getOriginBounds():
			pnt = self.getLocalSpace(self.owner, chkpnt)

			for i in [0,1,2]:
				if abs(pnt[i]) > 3.1:
					return False

			return True

		return False

	def applyContainerProps(self, cls):
		cls.gravity = self.owner.getAxisVect((0,0,-9.8))
		cls.air_drag = 1.0
		x = (cls.owner.worldPosition-self.owner.worldPosition).length/4
		if x > 1:
			x = 1
		cls.env_dim = (1.2-(x*0.2), 2.0-x, 1.2-(x*0.2), 1)


class MorphMissile(weapon.CoreWeapon):

	NAME = "Morph Missile"
	TYPE = "RANGED"

	def defaultData(self):
		self.ammo_vis = None
		dict = super().defaultData()
		dict["AMMO"] = ".".join([self.owner.name, "STK"])
		return dict

	def ST_Active(self):
		owner = self.owner
		scene = owner.scene
		plrobj = self.owning_player.owner

		fire = self.getFirstEvent("WP_FIRE", "TAP")
		mstp = self.getFirstEvent("WP_AMMO")

		if mstp != None:
			m = mstp.getProp("TYPE")
			if m != None:
				self.data["AMMO"] = ".".join([owner.name, m])
				if self.ammo_vis != None:
					self.ammo_vis.endObject()
					self.ammo_vis = None

		if self.ammo_vis == None:
			gfx = scene.addObject(self.data["AMMO"], owner, 0)
			gfx.setParent(owner, False, False)
			gfx.localPosition = self.createVector()
			gfx.localOrientation = self.createMatrix()
			self.ammo_vis = gfx

		if self.data["COOLDOWN"] == 0:
			if fire != None:
				ammo = scene.addObject("AMMO_MorphMissile", owner, 0)
				#point = self.getLocalSpace(plrobj, owner.worldPosition)
				#ammo.worldLinearVelocity = plrobj.getVelocity(point)
				ammo.worldPosition = owner.worldPosition+owner.getAxisVect((0,1,0))
				ammo["ROOTOBJ"] = plrobj
				ammo["DAMAGE"] = 100
				ammo["RADIUS"] = 8
				ammo["IMPULSE"] = 50
				ammo["SCALE"] = 4
				ammo["TIME"] = 600
				gfx = scene.addObject(self.data["AMMO"], owner, 0)
				gfx.setParent(ammo, False, False)
				gfx.localPosition = self.createVector()
				gfx.localOrientation = self.createMatrix()
				gfx.localScale = (2,2,2)
				#ammo["TARGET"] = self.target

				self.data["COOLDOWN"] = 30

		else:
			self.data["COOLDOWN"] -= 1


class Silverbird(vehicle.CoreAircraft):

	NAME = "Silverbird"
	HUDLAYOUT = None

	INVENTORY = {
		"L1":"WP_LaserCannon",
		"R1":"WP_LaserCannon",
		"L2":"WP_LaserCannon",
		"R2":"WP_LaserCannon",
		"L3":"WP_MorphMissile",
		"R3":"WP_MorphMissile"
		}

	CAM_TYPE = "FIRST"
	CAM_RANGE = (4, 16)
	CAM_ZOOM = 3
	CAM_MIN = 1
	CAM_SLOW = 3
	CAM_HEAD_G = 40

	WH_FRONT = 2
	WH_REAR = -1
	WH_WIDTH = 3
	WH_HEIGHT = 1

	VEH_LENGTH = 0.4

	VEH_ROLL = 0
	VEH_SPRING = 50
	VEH_DAMPING = 10
	VEH_FRICTION = 1

	WHEELS = {}
	#	"Wheel_FC": {"CENTER":True},
	#	"Wheel_RR": {"REAR":True},
	#	"Wheel_RL": {"REAR":True, "LEFT":True} }

	SEATS = {
		"Seat_1": {"NAME":"Pilot", "DOOR":"Root", "CAMERA":[0,0.4,0.7], "ACTION":"SeatLow", "VISIBLE":True, "SPAWN":[0,0.5,2]} }

	AERO = {"POWER":5000, "REVERSE":1.0, "HOVER":0, "LIFT":0, "TAIL":0, "DRAG":(1,1,1)}

	def defaultData(self):
		self.lasers = {"POWER":1, "QUAD":False}
		self.oldlas = self.lasers.copy()
		self.align = True
		self.expnt = None
		self.shdhp = 0

		dict = super().defaultData()
		dict["COOLDOWN"] = 0
		dict["THRUSTERS"] = {"CAP":100, "STATE":True, "ACTIVE":False, "ALIGN":True}
		dict["LASERS"] = {"LEVEL":1, "QUAD":False}
		dict["MISSILES"] = {"STATE":"", "SIDE":"L3", "AMMO":20, "TIMER":0, "TYPES":["STK", "PRX", "HOM"]}

		return dict

	def manageStatAttr(self):
		if self.data["HEALTH"] < 0:
			self.data["HEALTH"] = -1
		if self.data["ENERGY"] < 0:
			self.data["ENERGY"] = 0

		if self.data["HEALTH"] > 200:
			self.data["HEALTH"] = 200
		if self.data["ENERGY"] > 100:
			self.data["ENERGY"] = 100

		self.shdhp *= 0.98
		self.owner["DEBUG"] = self.shdhp

		for evt in self.getAllEvents("POWERUP", "CHECK"):
			ma = evt.getProp("MISSILES")
			if ma != None:
				ct = 20-self.data["MISSILES"]["AMMO"]
				self.sendEvent("POWERUP", evt.sender, "CHECK", MISSILES=ct)

	def applyModifier(self, dict):
		hdo = self.objects["HUD"]
		thr = self.data["THRUSTERS"]
		las = self.data["LASERS"]
		mis = self.data["MISSILES"]

		if "HEALTH" in dict:
			if dict["HEALTH"] > 0:
				hdo["BG"].color[2] = 1
			elif dict["HEALTH"] < 0 and "VEC" in dict:
				fwd = self.createVector(vec=(0,1,0))
				vec = self.createVector(vec=dict["VEC"]).normalized()*-1
				vec = self.owner.worldOrientation.inverted()*vec
				top = vec[2]
				vec[2] = 0
				vec = vec.normalized()
				ang = vec.to_track_quat("Y", "Z").to_euler()
				VX, VY, VZ = [self.toDeg(ang[0]), self.toDeg(ang[1]), self.toDeg(ang[2])]

				hdo["HIT_FL"].color = (0.5, 0, float(90>=VZ>30), 1)
				hdo["HIT_FR"].color = (0.5, 0, float(-90<=VZ<-30), 1)
				hdo["HIT_RL"].color = (0.5, 0, float(150>=VZ>90), 1)
				hdo["HIT_RR"].color = (0.5, 0, float(-150<=VZ<-90), 1)
				if abs(top) > 0.7:
					x = 0.5-(top>0)
					hdo["HIT_FL"].color = (0.5+x, 0, 1, 1)
					hdo["HIT_FR"].color = (0.5+x, 0, 1, 1)
					hdo["HIT_RL"].color = (0.5+x, 0, 1, 1)
					hdo["HIT_RR"].color = (0.5+x, 0, 1, 1)
				elif abs(VZ) > 150:
					hdo["HIT_RL"].color = (0.5, 0, 1, 1)
					hdo["HIT_RR"].color = (0.5, 0, 1, 1)

				gfx = self.owner.scene.addObject("GFX_ShieldBubble", self.owner, 0)
				gfx.setParent(self.owner, False, False)
				gfx.localPosition = (0,0,0)
				vec = self.createVector(vec=dict["POS"])-self.owner.worldPosition
				gfx.alignAxisToVect(vec.normalized(), 2, 1.0)
				self.shdhp += abs(dict["HEALTH"])
				x = self.shdhp/100
				if x < 0:
					x = 0
				if x > 1:
					x = 1
				gfx.children[0].color[1] = self.data["HEALTH"]/50
				gfx.children[0].color[2] = 1-x

			dict["HEALTH"] *= 0.1

		if "ENERGY" in dict:
			if dict["ENERGY"] > 0 and self.data["ENERGY"] < 100:
				hdo["BGL"].color[2] = 1

		if "AFTERBURNER" in dict:
			if thr["STATE"] == None:
				thr["STATE"] = True

		if "LASER_POWER" in dict:
			self.lasers["POWER"] += 1
			if self.lasers["POWER"] > self.oldlas["POWER"]:
				self.oldlas["POWER"] = self.lasers["POWER"]
				las["LEVEL"] = self.lasers["POWER"]
				hdo["BGL"].color[2] = 1

		if "LASER_QUAD" in dict:
			self.lasers["QUAD"] = True
			if self.lasers["QUAD"] > self.oldlas["QUAD"]:
				self.oldlas["QUAD"] = self.lasers["QUAD"]
				las["QUAD"] = self.lasers["QUAD"]
				hdo["BGL"].color[2] = 1

		if "MISSILES" in dict:
			mis["AMMO"] += dict["MISSILES"]
			if mis["AMMO"] > 20:
				mis["AMMO"] = 20
			hdo["BGR"].color[2] = 1


		for var in ["PRX", "HOM", "STK"]:
			if ("MIS_"+var) in dict:
				if var not in mis["TYPES"]:
					mis["TYPES"].append(var)
					mis["AMMO"] = 20
					hdo["BGR"].color[2] = 1

		super().applyModifier(dict)

	def getMouseInput(self):
		self.data["HUD"]["Target"] = None

		if self.data["CAMERA"]["Orbit"] <= 0 and self.MOUSE_CONTROL == True:
			X, Y = keymap.MOUSELOOK.axis()
			X *= 25
			Y *= 25

			self.motion["Mouse"][0] = X
			self.motion["Mouse"][1] = Y
			return X, Y

		else:
			self.motion["Mouse"][0] = 0
			self.motion["Mouse"][1] = 0
			return 0, 0

	def getInputs(self):
		KB = self.custom_binds
		FR = self.motion["Force"]
		TQ = self.motion["Torque"]

		## INPUTS ##
		frx = KB["STRAFERIGHT"].axis() - KB["STRAFELEFT"].axis()
		fry = KB["THROTTLEUP"].axis() - KB["THROTTLEDOWN"].axis()
		frz = KB["ASCEND"].axis() - KB["DESCEND"].axis()

		tqx = KB["PITCHUP"].axis() - KB["PITCHDOWN"].axis()
		tqy = KB["BANKRIGHT"].axis() - KB["BANKLEFT"].axis()
		tqz = KB["YAWLEFT"].axis() - KB["YAWRIGHT"].axis()

		if abs(frx) <= abs(FR[0]):
			FR[0] = frx
		if abs(fry) <= abs(FR[1]):
			FR[1] = fry
		if abs(frz) <= abs(FR[2]):
			FR[2] = frz

		FR[0] += (frx-FR[0])*0.35
		FR[1] += (fry-FR[1])*0.35
		FR[2] += (frz-FR[2])*0.35

		if abs(tqx) <= abs(TQ[0]):
			TQ[0] = tqx
		if abs(tqy) <= abs(TQ[1]):
			TQ[1] = tqy
		if abs(tqz) <= abs(TQ[2]):
			TQ[2] = tqz

		TQ[0] += (tqx-TQ[0])*0.2
		TQ[1] += (tqy-TQ[1])*0.2
		TQ[2] += (tqz-TQ[2])*0.2

		POS_X, POS_Y = self.getMouseInput()

		TQ[0] += POS_Y
		TQ[2] += POS_X

		for m in [FR, TQ]:
			for i in [0,1,2]:
				if abs(m[i]) > 1:
					m[i] = 1-(2*(m[i]<0))

	def removeFromSeat(self, key, force=False):
		owner = self.getOwner()

		cls = self.player_seats[key]
		if cls == None:
			self.driving_seat = None
			return True

		if self.expnt == None:
			return False

		cls.doAnim(STOP=True)
		cls.exitVehicle(self.expnt)
		cls.removeContainerParent()
		cls.data["LINVEL"] = [0,0,0]

		self.player_seats[key] = None
		self.driving_seat = None
		self.expnt = None

		return True

	def airDrag(self):
		dampLin = 0.0
		dampRot = 0.98

		self.objects["Root"].setDamping(dampLin, dampRot)

		linV = self.objects["Root"].localLinearVelocity

		drag = self.AERO["DRAG"]

		DRAG_X = linV[0]*drag[0]*200
		DRAG_Y = linV[1]*drag[1]*200
		DRAG_Z = linV[2]*drag[2]*200

		self.objects["Root"].applyForce((-DRAG_X, -DRAG_Y, -DRAG_Z), True)

	def airLift(self):
		owner = self.objects["Root"]

		grav = self.gravity
		mass = owner.mass

		owner.applyForce(-grav*mass, False)

		if self.data["THRUSTERS"]["ALIGN"] == True and grav.length > 0.1:
			self.align = True
			up = grav.normalized()
			ty = up.dot(owner.getAxisVect((-1,0,0)))
			gy = up.dot(owner.getAxisVect((0,1,0)))
			gz = up.dot(owner.getAxisVect((0,0,-1)))
			if gz < 0:
				ty = 1-(2*(ty<0))
			if abs(gy) > 0.866:
				ty = 0
				self.align = False
			if abs(self.motion["Torque"][1]) > 0.1:
				ty = 0

			owner.applyTorque((0, ty*4000, 0), True)
		else:
			self.align = False

		self.setWheelBrake(1, "REAR")

	def fireFX(self):
		rand = 0
		for i in self.randlist:
			rand += i
		rand = (rand/3)

		self.objects["Fire"].localScale[1] = rand

		fac = self.motion["Force"][1]
		if self.data["THRUSTERS"]["ACTIVE"] == True:
			fac = 2
		mxfire = (fac*0.5)+0.3
		self.randlist.insert(0, (logic.getRandomFloat()*0.1)+mxfire)
		self.randlist.pop()

	def ST_Startup(self):
		self.randlist = [0.1]*3
		self.active_post.append(self.airDrag)
		self.active_post.append(self.airLift)
		self.active_post.append(self.fireFX)

		self.custom_binds = {
			"THROTTLEUP":    input.KeyBase("00",  "WKEY",           "",  JOYAXIS=(1, "NEG", "A")),
			"THROTTLEDOWN":  input.KeyBase("01",  "SKEY",           "",  JOYAXIS=(1, "POS", "A")),
			"YAWLEFT":       input.KeyBase("02",  "LEFTARROWKEY",   "",  JOYAXIS=(2, "NEG", "A")),
			"YAWRIGHT":      input.KeyBase("03",  "RIGHTARROWKEY",  "",  JOYAXIS=(2, "POS", "A")),
			"PITCHUP":       input.KeyBase("04",  "DOWNARROWKEY",   "",  JOYAXIS=(3, "NEG", "A")),
			"PITCHDOWN":     input.KeyBase("05",  "UPARROWKEY",     "",  JOYAXIS=(3, "POS", "A")),
			"BANKLEFT":      input.KeyBase("06",  "QKEY",           ""  ),
			"BANKRIGHT":     input.KeyBase("07",  "EKEY",           ""  ),
			"ASCEND":        input.KeyBase("08",  "SPACEKEY",       "",  JOYAXIS=(5, "SLIDER", "A")),
			"DESCEND":       input.KeyBase("09",  "CKEY",           "",  JOYAXIS=(4, "SLIDER", "A")),
			"STRAFELEFT":    input.KeyBase("10",  "AKEY",           "",  JOYAXIS=(0, "NEG", "A")),
			"STRAFERIGHT":   input.KeyBase("11",  "DKEY",           "",  JOYAXIS=(0, "POS", "A")),
			"BOOST":         input.KeyBase("12",  "LEFTSHIFTKEY",   "",  JOYBUTTON=10),
			#"STRAFE":        input.KeyBase("13",  "LEFTALTKEY",     "",  JOYBUTTON=0),
			#"ROLL":          input.KeyBase("13",  "NONE",           "",  JOYBUTTON=0),

			"PRIMARY":       input.KeyBase("20",  "ONEKEY",         "",  JOYBUTTON=2),
			"SECONDARY":     input.KeyBase("21",  "TWOKEY",         "",  JOYBUTTON=1),
			"ENGINES":       input.KeyBase("22",  "THREEKEY",       "",  JOYBUTTON=3),

			"SET_UP":        input.KeyBase("22",  "UPARROWKEY",     "",  JOYBUTTON=11),
			"SET_DOWN":      input.KeyBase("23",  "DOWNARROWKEY",   "",  JOYBUTTON=12),
			"SET_LEFT":      input.KeyBase("24",  "LEFTARROWKEY",   "",  JOYBUTTON=13),
			"SET_RIGHT":     input.KeyBase("25",  "RIGHTARROWKEY",  "",  JOYBUTTON=14),

			"ATTACK_ONE":    input.KeyBase("30",  "LEFTMOUSE",      "",  JOYBUTTON=0),
			"ATTACK_TWO":    input.KeyBase("31",  "RIGHTMOUSE",     "",  JOYBUTTON=9)
		}

		for slot in ["L1", "L2", "L3", "R1", "R2", "R3"]:
			cls = self.getSlotChild(slot)
			cls.stateSwitch(state=True)

		self.owner["DEBUG"] = 0.0
		self.owner.addDebugProperty("DEBUG", True)

		hdo = self.objects["HUD"]
		hdo["LVL"].color = (0,1,1,1)
		hdo["QUAD"].color = (1,1,0,1)
		hdo["AFB"].color = (1,1,0,1)
		for s in ["FL", "FR", "RL", "RR"]:
			hdo["HIT_"+s].color = (0.5,0,0,1)

	## ACTIVE STATE ##
	def ST_Active(self):
		self.getInputs()

		KB = self.custom_binds
		FR = self.motion["Force"]
		TQ = self.motion["Torque"]

		owner = self.objects["Root"]

		ST_PRI = KB["PRIMARY"].active()
		ST_SEC = KB["SECONDARY"].active()
		ST_ENG = KB["ENGINES"].active()

		las = self.data["LASERS"]
		mis = self.data["MISSILES"]
		thr = self.data["THRUSTERS"]

		## FORCES ##
		frx = FR[0] * 7000
		fry = FR[1] * 7000
		frz = FR[2] * 7000

		tqx = TQ[0] * 3000
		tqy = TQ[1] * 3500
		tqz = TQ[2] * 4000

		thr["ACTIVE"] = False
		if thr["STATE"] == True:
			if thr["CAP"] > 0 and KB["BOOST"].active() == True:
				fry = 21000
				thr["ACTIVE"] = True
				thr["CAP"] -= 0.3
				if thr["CAP"] < 0:
					thr["CAP"] = 0
			elif thr["CAP"] < 100:
				thr["CAP"] += 0.1
				if thr["CAP"] > 100:
					thr["CAP"] = 100
				self.data["ENERGY"] -= 0.01

		if ST_PRI == False and ST_SEC == False and ST_ENG == False:
			owner.applyTorque([tqx, tqy, tqz], True)
			owner.applyForce([frx, fry, frz], True)

		## WEAPONS ##
		if self.data["COOLDOWN"] <= 0:
			if KB["ATTACK_ONE"].active() == True and self.data["ENERGY"] > 0:
				dmg = 6
				eng = 1.0
				col = (1,0,0,1)
				if self.lasers["POWER"] >= 2 and las["LEVEL"] == 2:
					dmg = 8
					eng = 1.1
					col = (1,0,1,1)
				if self.lasers["POWER"] >= 3 and las["LEVEL"] == 3:
					dmg = 10
					eng = 1.3
					col = (0,0.5,1,1)
				if self.lasers["POWER"] == 4 and las["LEVEL"] == 4:
					dmg = 12
					eng = 1.6
					col = (0,1,0,1)

				self.sendEvent("WP_FIRE", self.getSlotChild("L1"), DAMAGE=dmg, COLOR=col)
				self.sendEvent("WP_FIRE", self.getSlotChild("R1"), DAMAGE=dmg, COLOR=col)
				if self.lasers["QUAD"] == True and las["QUAD"] == True:
					eng *= 2
					self.sendEvent("WP_FIRE", self.getSlotChild("L2"), DAMAGE=dmg, COLOR=col)
					self.sendEvent("WP_FIRE", self.getSlotChild("R2"), DAMAGE=dmg, COLOR=col)

				self.data["ENERGY"] -= eng*0.25
				self.data["COOLDOWN"] = 15

		else:
			self.data["COOLDOWN"] -= 1

		side = mis["SIDE"]+str(mis["STATE"])

		if mis["TIMER"] <= 0:
			if KB["ATTACK_TWO"].active() == True and mis["AMMO"] > 0:
				if side == "L3":
					self.sendEvent("WP_AMMO", self.getSlotChild("L3"), TYPE=mis["TYPES"][0])
					self.sendEvent("WP_FIRE", self.getSlotChild("L3"), "TAP")
					mis["SIDE"] = "R3"
				elif side == "R3":
					self.sendEvent("WP_AMMO", self.getSlotChild("R3"), TYPE=mis["TYPES"][0])
					self.sendEvent("WP_FIRE", self.getSlotChild("R3"), "TAP")
					mis["SIDE"] = "L3"
				mis["AMMO"] -= 1
				mis["STATE"] = "CD"
				mis["TIMER"] = 50
		else:
			mis["TIMER"] -= 1
			if mis["AMMO"] <= 0:
				mis["STATE"] = "EM"
			elif mis["TIMER"] <= 0:
				mis["STATE"] = ""

		if ST_PRI == True:
			if KB["SET_LEFT"].tap() == True:
				las["LEVEL"] -= 1*(las["LEVEL"]>1)
			if KB["SET_RIGHT"].tap() == True:
				las["LEVEL"] += 1*(las["LEVEL"]<self.lasers["POWER"])
			if KB["SET_UP"].tap() == True:
				las["QUAD"] = (self.lasers["QUAD"]==True)
			if KB["SET_DOWN"].tap() == True:
				las["QUAD"] = False

		if ST_SEC == True:
			if KB["SET_LEFT"].tap() == True:
				mis["TYPES"].insert(0, mis["TYPES"].pop())
				self.sendEvent("WP_AMMO", self.getSlotChild("L3"), TYPE=mis["TYPES"][0])
				self.sendEvent("WP_AMMO", self.getSlotChild("R3"), TYPE=mis["TYPES"][0])
				print(mis["TYPES"])
			if KB["SET_RIGHT"].tap() == True:
				mis["TYPES"].append(mis["TYPES"].pop(0))
				self.sendEvent("WP_AMMO", self.getSlotChild("L3"), TYPE=mis["TYPES"][0])
				self.sendEvent("WP_AMMO", self.getSlotChild("R3"), TYPE=mis["TYPES"][0])
				print(mis["TYPES"])
			#if KB["SET_UP"].tap() == True:
			#if KB["SET_DOWN"].tap() == True:

		if ST_ENG == True:
			if KB["SET_LEFT"].tap() == True:
				thr["ALIGN"] = False
			elif KB["SET_RIGHT"].tap() == True:
				thr["ALIGN"] = True
			elif KB["SET_UP"].tap() == True:
				thr["STATE"] = True
			elif KB["SET_DOWN"].tap() == True:
				thr["STATE"] = False
		if thr["STATE"] != None:
			if self.data["ENERGY"] < 12.5:
				thr["STATE"] = False

		## EXTRAS ##
		hdo = self.objects["HUD"]

		hdo["DMG"].color[0] = self.data["HEALTH"]/100
		hdo["BG"].color[0] = (self.data["HEALTH"]>17.5)
		hdo["ENG"].color[0] = self.data["ENERGY"]/100
		hdo["BGL"].color[0] = (self.data["ENERGY"]>0)
		hdo["LVL"].color[0] = (las["LEVEL"]/4)
		hdo["QUAD"].color[0] = float(las["QUAD"])
		hdo["QUAD"].color[2] = float(self.lasers["QUAD"])
		hdo["MIS"].color[0] = (mis["AMMO"]/20)
		hdo["BGR"].color[0] = (mis["AMMO"]>0)
		hdo["MSL"].color[0] = (side=="L3")
		hdo["MSR"].color[0] = (side=="R3")
		hdo["BG"].color[2] *= 0.97
		hdo["BGL"].color[2] *= 0.97
		hdo["BGR"].color[2] *= 0.97
		hdo["AFB"].color[0] = (thr["CAP"]/100)*(thr["STATE"]==True)
		hdo["AFB"].color[2] = (thr["STATE"]!=None)
		hdo["ALGN"].color[0] = (self.align==True)
		hdo["ALGN"].color[2] = (thr["ALIGN"]==True)
		hdo["EXIT"].color[0] = 0

		dc = 100
		fx = 0
		rayto = owner.worldPosition+owner.getAxisVect((0,4,0))
		rayfrom = owner.worldPosition #+owner.getAxisVect((0,2,0))

		rayobj, raypnt, raynrm = owner.rayCast(rayto, rayfrom, dc, "", 1, 1, 0)

		dist = None
		if rayobj != None:
			ray = raypnt-rayfrom
			dist = dc-ray.length
		if dist != None:
			fx = (((dist/dc)**3.5)*0.1)+0.01

		hdo["AIML"].localPosition = (-fx, 0, -fx)
		hdo["AIMR"].localPosition = (fx, 0, -fx)
		hdo["AIMC"].localPosition = (0,0,-fx)
		hdo["AIMC"].localScale = (fx*10,1,1)

		for s in ["FL", "FR", "RL", "RR"]:
			hdo["HIT_"+s].color[2] *= 0.98

		#self.data["HUD"]["Power"] = (POWER+1)*50
		#self.data["HUD"]["Lift"] = (CLIMB+1)*50

		## END ##
		self.lasers["POWER"] = 1
		self.lasers["QUAD"] = False

		if keymap.BINDS["TOGGLECAM"].tap() == True:
			if self.data["CAMERA"]["State"] == "THIRD":
				self.setCameraState("SEAT")
			else:
				self.setCameraState("THIRD")

		evt = self.getFirstEvent("SILVERBIRD", "PARKING")

		if evt != None:
			self.expnt = evt.getProp("SPAWN")
		else:
			self.expnt = None

		if self.expnt != None:
			hdo["EXIT"].color[0] = 1
			if keymap.BINDS["ENTERVEH"].tap() == True:
				self.stateSwitch("IDLE")

	def ST_Idle(self):
		self.lasers["POWER"] = 1
		self.lasers["QUAD"] = False

		if self.checkClicked() == True:
			self.stateSwitch()


class Suzanne(base.CoreAdvanced):

	INVENTORY = {"M1":"WP_LaserCannon"}

	def defaultStates(self):
		self.active_pre = []
		self.active_state = self.ST_Active
		self.active_post = []

	def defaultData(self):
		dict = super().defaultData()
		dict["COOLDOWN"] = 0
		return dict

	def applyModifier(self, dict):
		if "HEALTH" in dict:
			if dict["HEALTH"] < 0 and "POS" in dict:
				self.shdhp += abs(dict["HEALTH"])
				i = abs(dict["HEALTH"])/50
				x = self.shdhp/50
				if x < 0:
					x = 0
				if x > 1:
					x = 1
				while i > 0:
					gfx = self.owner.scene.addObject("GFX_ShieldBubble", self.owner, 0)
					gfx.setParent(self.owner, False, False)
					gfx.localPosition = (0,0,0)
					gfx.localScale = (0.67, 0.67, 0.67)
					vec = self.createVector(vec=dict["POS"])-self.owner.worldPosition
					gfx.alignAxisToVect(vec.normalized(), 2, 1.0)
					gfx.children[0].color[1] = ((self.data["HEALTH"]-25)/50)
					gfx.children[0].color[2] = 1-x
					i -= 1

		super().applyModifier(dict)

	def ST_Startup(self):
		self.shdhp = 0
		self.laser = self.getSlotChild("M1")
		self.laser.stateSwitch(state=True)

	def ST_Active(self):
		global SILVERBIRD

		owner = self.owner
		scene = owner.scene

		if self.data["COOLDOWN"] <= 0:
			self.sendEvent("WP_FIRE", self.laser, DAMAGE=20, COLOR=(1, 0.7, 0, 1), SCALE=(6,8,6))
			self.data["COOLDOWN"] = 30
		else:
			self.data["COOLDOWN"] -= 1

		if self.data["HEALTH"] <= 0:
			bom = scene.addObject("AOE_Bomb", owner, 0)
			bom.localScale = (4, 4, 4)
			bom.color = (1,0.8,0,1)
			bom["DAMAGE"] = 10
			bom["IMPULSE"] = 10.0
			self.destroy()

		self.shdhp *= 0.95

