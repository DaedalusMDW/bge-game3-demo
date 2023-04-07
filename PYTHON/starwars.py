

import math

from bge import logic

from game3 import base, keymap, viewport, HUD, vehicle, weapon
from PYTHON import objects, characters

HYPERLANES = []


class HyperLane(base.CoreObject):

	NAME = "Hyper Bacon"
	CONTAINER = "WORLD"

	def defaultData(self):
		dict = super().defaultData()
		dict["NAME"] = self.owner.get("NAME", self.owner.name)
		dict["RADIUS"] = self.owner.get("RADIUS", 0)

		return dict

	def ST_Startup(self):
		global HYPERLANES

		if self not in HYPERLANES:
			HYPERLANES.append(self)


class HyperRing(base.CoreObject):

	NAME = "Hyperspace Ring"
	CONTAINER = "WORLD"
	GHOST = True
	SPEED = 50

	def defaultStates(self):
		self.active_pre = []
		self.active_state = self.ST_Idle
		self.active_post = []

	def defaultData(self):
		self.docking_point = None
		self.gfx = None

		dict = super().defaultData()
		dict["DOCKED"] = "NONE"
		dict["FRAME"] = 0
		dict["BACON"] = None

		return dict

	def ST_Startup(self):
		self.objects["Fire"].color = (1,1,0,1)
		self.objects["Guide"].visible = False
		self.objects["HUD"].visible = False
		self.objects["HUD"].color = (0.5,0.5,0.5,1)
		f = self.data["FRAME"]
		e = 0
		if self.data["DOCKED"] in ["LOCKED", "DOCKING"]:
			e = 90
		self.doAnim("Rig", "HyperRingClamps", (f,e))

	def stateSwitch(self, state):
		if state == "DOCK":
			self.objects["Guide"].visible = False
			self.objects["HUD"].visible = False
			self.data["DOCKED"] = "DOCKING"
			self.data["FRAME"] = 0
			self.doAnim("Rig", "HyperRingClamps", (0,90))
			self.active_state = self.ST_Docking

		if state == "ACTIVE":
			self.objects["Guide"].visible = False
			self.objects["HUD"].visible = True
			self.data["DOCKED"] = "LOCKED"
			self.data["FRAME"] = 0
			self.data["BACON"] = None
			self.active_state = self.ST_Active

		if state == "TRAVEL":
			self.objects["Guide"].visible = False
			self.objects["HUD"].visible = False
			self.active_state = self.ST_Travel

		if state == "RELEASE":
			self.objects["Guide"].visible = False
			self.objects["HUD"].visible = False
			self.data["DOCKED"] = "RELEASE"
			self.data["FRAME"] = 180
			self.doAnim("Rig", "HyperRingClamps", (90,0))
			self.active_state = self.ST_Docking

		if state == "IDLE":
			self.objects["Guide"].visible = True
			self.objects["HUD"].visible = False
			self.data["DOCKED"] = "NONE"
			self.data["FRAME"] = 0
			self.data["BACON"] = None
			self.active_state = self.ST_Idle

	def ST_Idle(self):
		owner = self.owner
		guide = self.objects["Guide"]

		rayto = self.objects["Guide"].worldPosition.copy()
		rayfrom = rayto+owner.getAxisVect([0,0,1])

		rayobj, raypnt, raynrm = owner.rayCast(rayto, rayfrom, 2, "", 1, 0, 0)

		if rayobj != None:
			cls = rayobj.get("Class", None)

			pnt = guide.worldPosition-rayobj.worldPosition
			lp = rayobj.worldOrientation.inverted()*pnt
			lr = rayobj.worldOrientation.inverted()*guide.worldOrientation

			r = lr.to_euler()
			rx = self.toDeg(r[0])
			ry = self.toDeg(r[1])
			rz = self.toDeg(r[2])

			if lp.length < 0.2 and rx < 5 and ry < 5 and rz < 5:
				self.sendEvent("DOCKING", cls, "HYPERRING", GUIDE=guide)

		self.objects["Guide"].visible = True

		evt = self.getFirstEvent("DOCKING", "STARFIGHTER", "DOCKING")
		if evt != None:
			self.stateSwitch("DOCK")

	def ST_Active(self):
		global HYPERLANES

		owner = self.owner
		hud = self.objects["HUD"]
		cls = self.getSlotChild("Dock")

		yref = owner.worldOrientation*self.createVector(vec=(0,1,0))

		hud.visible = True
		hud.color = (0.5,0.5,0.5,1)

		x = 360
		t = None
		for i in HYPERLANES:
			vec = i.owner.worldPosition-owner.worldPosition
			if vec.length > (i.data["RADIUS"]+(self.SPEED*2)):
				ang = self.toDeg(yref.angle(vec.normalized()))
				tan = self.toDeg(i.data["RADIUS"]/vec.length)
				if tan < 2:
					tan = 2
				if ang < tan and ang < x:
					x = ang
					t = i

		evt = self.getFirstEvent("DOCKING", "STARFIGHTER", "PUNCHIT")
		if t != None:
			hud.color = (0,1,0,1)
			if evt != None:
				pos = t.owner.worldPosition+base.ORIGIN_OFFSET
				vec = t.owner.worldPosition-owner.worldPosition
				pos -= vec.normalized()*t.data["RADIUS"]
				self.data["BACON"] = list(pos)
				self.stateSwitch("TRAVEL")
				return

		release = False
		evt = self.getFirstEvent("DOCKING", "STARFIGHTER", "RELEASE")
		if evt != None:
			release = True

		if release == True:
			self.stateSwitch("RELEASE")
			return

		evt = self.getFirstEvent("INPUT", "STARFIGHTER")
		if evt != None:
			X, Y, Z = evt.getProp("ROTATE", [0,0,0])
			owner.worldOrientation = owner.worldOrientation*self.createMatrix(rot=(X,Y,Z), deg=False)

	def ST_Travel(self):
		owner = self.owner

		if self.gfx == None:
			self.gfx = owner.scene.addObject("GFX_Hyper", owner, 0)
			self.gfx.setParent(owner, False, False)

		self.gfx["FRAME"] = self.data["FRAME"]

		pos = self.createVector(vec=self.data["BACON"])
		vec = pos-(owner.worldPosition+base.ORIGIN_OFFSET)
		fac = (self.data["FRAME"]/60)**2
		if fac > 1:
			fac = 1

		if self.data["FRAME"] < 60 or self.data["FRAME"] > 65:
			self.data["FRAME"] += 1
		elif vec.length < self.SPEED*30:
			self.data["FRAME"] = 70

		owner.worldPosition += vec.normalized()*self.SPEED*fac

		if vec.length <= self.SPEED*2:
			self.gfx.endObject()
			self.gfx = None
			self.objects["Fire"].color = (1,1,0,1)
			self.stateSwitch("RELEASE")
		else:
			owner.alignAxisToVect(vec, 1, 0.1)
			self.objects["Fire"].color = (1,1,1,1)

	def ST_Docking(self):
		owner = self.owner
		guide = self.objects["Guide"]
		cls = self.getSlotChild("Dock")
		obj = cls.getOwner()

		if self.data["DOCKED"] == "DOCKING":
			obj.localPosition *= 0.95
			obj.alignAxisToVect(guide.getAxisVect((0,1,0)), 1, 0.05)
			obj.alignAxisToVect(guide.getAxisVect((0,0,1)), 2, 0.05)
			self.data["FRAME"] += 1
			if self.data["FRAME"] >= 90:
				obj.localPosition = self.createVector()
				obj.localOrientation = self.createMatrix()
				self.sendEvent("DOCKING", cls, "HYPERRING", "LOCKED")
				self.stateSwitch("ACTIVE")

		if self.data["DOCKED"] == "RELEASE":
			self.data["FRAME"] -= 1
			if self.data["FRAME"] <= 90:
				pos = self.createVector(vec=(0,-1,-2))
				obj.localPosition += (pos-obj.localPosition)*0.05
			if self.data["FRAME"] <= 0:
				self.sendEvent("DOCKING", cls, "HYPERRING", "RELEASE")
				self.stateSwitch("IDLE")


class Starfighter(vehicle.CoreAircraft):

	NAME = "Jedi Starfighter"
	LANDACTION = "StarfighterRigLand"

	INVENTORY = {"Cannon_L":"WP_LaserCannon", "Cannon_R":"WP_LaserCannon"}
	SLOTS = {"ONE":"Cannon_L", "TWO":"Cannon_R"}

	CAM_RANGE = (4, 16)
	CAM_ZOOM = 3
	CAM_MIN = 1
	#CAM_SLOW = 3
	CAM_HEAD_G = 40

	WH_FRONT = 3
	WH_REAR = -1
	WH_WIDTH = 1
	WH_HEIGHT = 0.3

	VEH_LENGTH = 0.3

	VEH_ROLL = 0
	VEH_SPRING = 50
	VEH_DAMPING = 10
	VEH_FRICTION = 10

	WHEELS = {
		"Wheel_FC": {"CENTER":True},
		"Wheel_RR": {"REAR":True},
		"Wheel_RL": {"REAR":True, "LEFT":True} }

	SEATS = {
		"Seat_1": {"NAME":"Pilot", "DOOR":"Root", "CAMERA":[0,-1.75,0.65], "ACTION":"SeatLow", "VISIBLE":True, "SPAWN":[-1.5,-2.5,0]} }

	AERO = {"POWER":10000, "REVERSE":0.2, "HOVER":500, "LIFT":0, "TAIL":0, "DRAG":(2,0.2,2)}

	def defaultData(self):
		self.env_dim = None

		dict = super().defaultData()
		dict["ATTACKMODE"] = True
		dict["FLYMODE"] = 0
		dict["COOLDOWN"] = 0
		dict["HARDPOINT"] = "R"

		return dict

	def applyModifier(self, dict):
		if "HEALTH" in dict:
			dict["HEALTH"] *= 0.25
		super().applyModifier(dict)

	def airDrag(self):
		linV = self.owner.localLinearVelocity

		dampLin = 0.0
		dampRot = (linV.length*0.01)+0.6

		if dampRot >= 0.8:
			dampRot = 0.8

		self.objects["Root"].setDamping(dampLin, dampRot)

		self.doDragForce()

		scale = abs(linV[1])
		if scale < 10:
			scale = 10

		fac = self.data["POWER"]/self.AERO["POWER"]

		DRAG_X = linV[0]*5*scale
		DRAG_Y = linV[1]*(50+((1-fac)*(scale-10)))
		DRAG_Z = linV[2]*5*scale

		self.owner.applyForce((-DRAG_X, -DRAG_Y, -DRAG_Z), True)

		#self.owner["SPEED"] = str(round(linV[1],2))
		#self.owner.addDebugProperty("SPEED", True)

	def airLift(self):
		owner = self.getOwner()
		linV = owner.localLinearVelocity

		self.lift = 0

		if self.data["FLYMODE"] != 0:
			self.lift = owner.mass*self.gravity.length
			owner.applyForce(-self.gravity*owner.mass, False)

		#self.owner["LIFT"] = self.lift
		#self.owner.addDebugProperty("LIFT", True)

	def toggleWeapons(self, state=None):
		if state == None:
			self.data["ATTACKMODE"] ^= True
		elif state == True:
			self.data["ATTACKMODE"] = True
		else:
			self.data["ATTACKMODE"] = False

		for slot in ["Cannon_L", "Cannon_R"]:
			cls = self.getSlotChild(slot)
			cls.stateSwitch(state=self.data["ATTACKMODE"])

	def fireWeapons(self, mode):
		if mode == "DUAL":
			self.sendEvent("WP_FIRE", self.getSlotChild("Cannon_L"))
			self.sendEvent("WP_FIRE", self.getSlotChild("Cannon_R"))

		elif mode == "STAGGERED":
			slot = "Cannon_"+self.data["HARDPOINT"]

			self.sendEvent("WP_FIRE", self.getSlotChild(slot))

			if self.data["HARDPOINT"] == "R":
				self.data["HARDPOINT"] = "L"
			else:
				self.data["HARDPOINT"] = "R"

	def ST_Startup(self):
		self.ANIMOBJ = self.objects["Rig"]
		self.objects["Fire"].color = (0,0,1,1)
		self.doLandingGear(init=True)
		g = self.data.get("GLASSFRAME", 120)
		self.doAnim(NAME="StarfighterRigGlass", FRAME=(g,g), LAYER=1)
		self.data["GLASSFRAME"] = g
		self.active_post.append(self.airDrag)
		self.active_post.append(self.airLift)
		self.active_post.append(self.PS_Ambient)
		self.toggleWeapons(self.data["ATTACKMODE"])

	def stateSwitch(self, state=None):
		if state != None:
			pass
		elif self.driving_seat == ".":
			state = "DRIVER"
		else:
			state = self.SEATS[self.driving_seat].get("STATE", "DRIVER")

		if state == "DRIVER":
			self.setPhysicsType("RIGID")
			self.doAnim(NAME="StarfighterRigGlass", FRAME=(0,-1), LAYER=1)
			self.active_state = self.ST_Active

		elif state == "ENTER":
			self.assignCamera()
			self.data["GLASSFRAME"] = 120
			self.doAnim(NAME="StarfighterRigGlass", FRAME=(120,0), LAYER=1)
			self.active_state = self.ST_Enter

		elif state == "EXIT":
			self.data["GLASSFRAME"] = 0
			self.doAnim(NAME="StarfighterRigGlass", FRAME=(0,120), LAYER=1)
			self.active_state = self.ST_Exit

		elif state == "IDLE":
			self.setPhysicsType("RIGID")
			if self.removeFromSeat(self.driving_seat) == True:
				self.data["GLASSFRAME"] = 120
				self.doAnim(NAME="StarfighterRigGlass", FRAME=(120,121), LAYER=1)
				self.active_state = self.ST_Idle
				self.sendEvent("DOCKING", self.getParent(), "STARFIGHTER", "RELEASE")
			else:
				self.stateSwitch("ENTER")

		elif state == "DOCK":
			self.setPhysicsType("NONE")
			self.data["POWER"] = 0
			self.data["LANDSTATE"] = "FLY"
			self.owner.localLinearVelocity = [0,0,0]
			self.owner.localAngularVelocity = [0,0,0]
			self.data["LINVEL"] = [0,0,0]
			self.data["ANGVEL"] = [0,0,0]
			self.active_state = self.ST_Docked

		elif state == "RELEASE":
			self.setPhysicsType("RIGID")
			self.data["POWER"] = 0
			self.data["LANDSTATE"] = "FLY"
			self.owner.localLinearVelocity = [0,0,0]
			self.owner.localAngularVelocity = [0,0,0]
			self.active_state = self.ST_Active

	def applyContainerProps(self, cls):
		super().applyContainerProps(cls)
		cls.env_dim = list(self.objects["Mesh"].color)

	def PS_Ambient(self):
		if self.env_dim == None:
			cls = self.getParent()
			amb = 0
			if cls != None:
				amb = cls.dict.get("DIM", amb)
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		self.objects["Mesh"].color = self.env_dim

		self.env_dim = None

	## ACTIVE STATE ##
	def ST_Active(self):
		self.getInputs()

		owner = self.objects["Root"]
		mesh = self.objects["Fire"]

		force = self.motion["Force"]
		torque = self.motion["Torque"]
		linV = owner.localLinearVelocity

		## FORCES ##
		power, hz = self.getEngineForce()

		fac = self.data["POWER"]/self.AERO["POWER"]

		mx = abs(linV.length)
		if mx > 100:
			mx = 100

		if self.gravity.length < 1:
			strafe = force[0]*500
			self.data["HOVER"][0] = 1000
			self.data["HOVER"][1] = 0
			#self.data["HUD"]["Lift"] = ((force[2]+1)/2)*100
		else:
			strafe = force[0]*200
			#self.data["HUD"]["Lift"] = (self.data["HOVER"][0]/9.8)+((self.data["HOVER"][1]/self.AERO["HOVER"])*33)

		## FLY mODES ##
		if self.data["FLYMODE"] == 0:
			power = force[1]*1000
			hover = (force[2]*500)+(owner.mass*self.gravity.length)
			fac = (force[1]*0.1)
			self.data["POWER"] = 0

			tqx = torque[0]*300
			tqy = torque[1]*150
			tqz = torque[2]*500

			self.data["HOVER"][0] = 1000
			self.data["HOVER"][1] = 0

			if keymap.BINDS["TOGGLEMODE"].tap() == True and self.data["LANDSTATE"] == "FLY":
				self.data["LANDSTATE"] = "FLYLOCK"
				self.data["FLYMODE"] = 1

			self.objects["HUD"]["HV"].color[0] = 1
			self.objects["HUD"]["HV"].color[1] = 0

		else:
			power += 3000
			power *= (self.data["FLYMODE"]/100)
			hover = force[2]*1000
			strafe = 0 #force[0]*1000

			tqx = torque[0]*(300+(mx*6))
			tqy = torque[1]+force[0]
			if abs(tqy) > 1.0:
				tqy = 1-(2*(tqy<0))
			tqy = tqy*(300+(mx*6))
			tqz = torque[2]*(300+(mx*6))

			self.data["HOVER"][0] = 1000
			self.data["HOVER"][1] = 0

			if self.data["FLYMODE"] < 100:
				self.data["FLYMODE"] += 1
			else:
				self.data["FLYMODE"] = 100

			if keymap.BINDS["TOGGLEMODE"].tap() == True:
				self.data["LANDSTATE"] = "FLY"
				self.data["FLYMODE"] = 0

			#self.data["HUD"]["Lift"] = ((force[2]+1)/2)*100
			self.objects["HUD"]["HV"].color[0] = 0
			self.objects["HUD"]["HV"].color[1] = 0

		self.data["HUD"]["Lift"] = ((force[2]+1)/2)*100

		## LANDING GEAR ##
		if self.data["LANDSTATE"] == "LAND":
			power *= 0.5
			rayobj = False
			if self.gravity.length >= 1 and force[2] < 0.1:
				rayto = owner.worldPosition+owner.getAxisVect((0,0,-1))
				rayobj = owner.rayCastTo(rayto, 0.8, "GROUND")

			if rayobj == None:
				power *= 0.5
				hover *= 0.5

				up = self.gravity.normalized()
				tx = (self.toDeg(up.angle(owner.getAxisVect((0,-1,0))))-90)/90
				ty = (self.toDeg(up.angle(owner.getAxisVect((1,0,0))))-90)/90
				gz = up.dot(owner.getAxisVect((0,0,-1)))
				if gz < 0:
					hover = force[2]*200
					owner.applyForce(-self.gravity*owner.mass, False)
					tx = 1-(2*(tx<0))
					ty = 1-(2*(ty<0))
				else:
					owner.applyForce(-self.gravity*owner.mass*0.5, False)
				owner.applyTorque((tx*300, ty*200, 0), True)
			elif rayobj != False:
				power = 0
				strafe = 0
				hover = 0
				fac = 0
				self.data["HUD"]["Lift"] = 0
				self.data["HOVER"][0] = 0

			self.objects["HUD"]["LG"].color[0] = 1
			self.objects["HUD"]["LG"].color[1] = 1*(self.data["LANDFRAME"]>1)

		else:
			self.objects["HUD"]["LG"].color[0] = 0
			self.objects["HUD"]["LG"].color[1] = 1*(self.data["LANDFRAME"]<99)

		owner.applyForce([strafe, power, hover], True)
		owner.applyTorque([tqx, tqy, tqz], True)

		## EXTRAS ##
		mesh.color[0] = fac*(fac>0)
		#cb = (1-abs(fac*(fac<0)))
		mesh.color[1] += (1-mesh.color[1])*0.02

		self.data["HUD"]["Power"] = abs(fac)*100

		self.setWheelBrake(10, "REAR")

		## WEAPONS ##
		if self.data["ATTACKMODE"] == True:
			self.objects["HUD"]["WP"].color[0] = 1
			self.objects["HUD"]["WP"].color[1] = 1

			if self.data["COOLDOWN"] == 0:
				self.objects["HUD"]["WP"].color[1] = 0
				if keymap.BINDS["ATTACK_ONE"].active() == True:
					self.fireWeapons("STAGGERED")
					self.data["COOLDOWN"] = 10
				elif keymap.BINDS["ATTACK_TWO"].active() == True:
					self.data["COOLDOWN"] = -200

			elif self.data["COOLDOWN"] <= -5:
				pew = []
				for i in range(8):
					pew.append((-200+(i*10)))
				if self.data["COOLDOWN"] in pew:
					self.data["ENERGY"] -= 10
					self.fireWeapons("DUAL")
				if self.data["COOLDOWN"] >= -200+(70):
					self.data["ENERGY"] += 1
				if self.data["COOLDOWN"] >= -40:
					self.data["COOLDOWN"] = 0
					self.data["ENERGY"] = 100
				self.data["COOLDOWN"] += 1

			else:
				self.data["COOLDOWN"] -= 1

		else:
			self.objects["HUD"]["WP"].color[0] = 0
			self.objects["HUD"]["WP"].color[1] = 0

		## TOGGLES ##
		evt = self.getFirstEvent("DOCKING", "HYPERRING")
		if evt != None and self.data["FLYMODE"] == 0:
			pos = evt.getProp("GUIDE")
			if pos != None:
				ref = self.getTransformDiff(pos)

				self.setContainerParent(evt.sender, "Dock")
				self.sendEvent("DOCKING", evt.sender, "STARFIGHTER", "DOCKING")
				self.stateSwitch("DOCK")

				owner.localPosition = ref[0]
				owner.localOrientation = ref[1]

		elif self.data["COOLDOWN"] == 0:
			if keymap.BINDS["SHEATH"].tap() == True:
				self.toggleWeapons()

			if keymap.BINDS["ENTERVEH"].tap() == True and linV.length < 10:
				self.stateSwitch("EXIT")

	def ST_Docked(self):
		self.getInputs()

		owner = self.objects["Root"]
		mesh = self.objects["Fire"]

		cls = self.getParent()

		force = self.motion["Force"]
		torque = self.motion["Torque"]

		if force[1] <= -0.9 or force[2] <= -0.9:
			self.sendEvent("DOCKING", cls, "STARFIGHTER", "RELEASE")

		elif force[1] >= 0.9:
			self.sendEvent("DOCKING", cls, "STARFIGHTER", "PUNCHIT")

		else:
			rot = [torque[0]/100, torque[1]/100, torque[2]/100]
			self.sendEvent("INPUT", cls, "STARFIGHTER", ROTATE=rot)

		self.data["LANDSTATE"] = "FLYLOCK"

		self.data["HUD"]["Power"] = 0
		self.data["HUD"]["Lift"] = 0

		self.objects["HUD"]["LG"].color[0] = 0
		self.objects["HUD"]["LG"].color[1] = 0
		self.objects["HUD"]["WP"].color[0] = 0
		self.objects["HUD"]["WP"].color[1] = 0

		evt = self.getFirstEvent("DOCKING", "HYPERRING", "RELEASE")
		if evt != None:
			self.removeContainerParent()
			self.stateSwitch("RELEASE")

	def ST_Idle(self):
		self.setWheelBrake(10, "REAR")

		if self.checkClicked() == True:
			self.stateSwitch("ENTER")

	def ST_Enter(self):
		self.setWheelBrake(10, "REAR")
		self.doCameraToggle()

		self.data["GLASSFRAME"] -= 1
		if self.data["GLASSFRAME"] <= 0:
			self.stateSwitch()

	def ST_Exit(self):
		self.setWheelBrake(10, "REAR")
		self.doCameraToggle()

		mesh = self.objects["Fire"]
		mesh.color[1] += (0-mesh.color[1])*0.02

		self.data["GLASSFRAME"] += 1
		if self.data["GLASSFRAME"] >= 120:
			mesh.color[1] = 0
			self.stateSwitch("IDLE")


class LaserCannon(weapon.CoreWeapon):

	NAME = "Standard Laser Cannon"
	TYPE = "RANGED"

	def ST_Active(self):
		owner = self.owner

		fire = self.getFirstEvent("WP_FIRE")

		if fire != None:
			plrobj = self.owning_player.objects["Root"]
			sx, sy, sz = fire.getProp("SCALE", [3, 8, 3])
			ammo = base.SC_SCN.addObject("AMMO_Laser", owner, 200)
			ammo.alignAxisToVect(ammo.getVectTo(base.SC_SCN.active_camera)[1], 2, 1.0)
			ammo.alignAxisToVect(owner.getAxisVect((0,1,0)), 1, 1.0)
			ammo["ROOTOBJ"] = plrobj
			ammo["DAMAGE"] = float(fire.getProp("DAMAGE", 40))
			ammo["LINV"] = plrobj.worldLinearVelocity*(1/60)
			ammo.localScale = (sx, sy+ammo["LINV"].length, sz)
			ammo.color = (1,1,1,1)
			ammo.children[0].color = fire.getProp("COLOR", [0, 1, 0, 1])

			gfx = base.SC_SCN.addObject("GFX_MuzzleFlash", owner, 0)
			gfx.setParent(owner, False, False)
			gfx.localScale = (sx, sx*2, sx)
			gfx.children[0].color = (1,1,1,1)


class Ahsoka(characters.TRPlayer):

	NAME = 'Ahsoka "Snips" Tano'
	CLASS = "Light"
	WP_TYPE = "MELEE"
	INVENTORY = {"Hip_L": "WP_LightSaber_A", "Hip_R": "WP_LightSaber_As"}
	SLOTS = {"FOUR":"Shoulder_L", "FIVE":"Back", "SIX":"Shoulder_R"}
	OFFSET = (0, 0.03, 0.14)
	SPEED = 0.12
	JUMP = 7
	GND_H = 1.0
	EYE_H = 1.535
	EDGE_H = 1.93
	CROUCH_H = 0.4
	ACCEL = 15
	ANIMSET = "Snippy"
	CAM_TYPE = "THIRD"
	CAM_HEIGHT = 0.15
	CAM_MIN = 0.3
	EDGECLIMB_TIME = 90

	def defaultStates(self):
		super().defaultStates()
		self.active_post.insert(0, self.PS_Abilities)

	def defaultData(self):
		dict = super().defaultData()
		dict["ATTACKCHAIN"] = "NONE"

		return dict

	def runModifiers(self):
		self.data["SPEED"] = self.SPEED
		self.data["RECHARGE"] = 0.08

		super().runModifiers()

	def applyModifier(self, dict):
		if "HEALTH" in dict and "DEFENSE" in dict:
			self.data["ENERGY"] -= (dict["DEFENSE"]/2)

		super().applyModifier(dict)

	def doPlayerAnim(self, action="IDLE", blend=10):
		if self.ANIMOBJ == None or self.data["HEALTH"] <= 0:
			return

		if action in ["IDLE", "RESET"]:
			if action == "RESET":
				self.doAnim(STOP=True)
				self.doAnim(NAME=self.ANIMSET+"Jumping", FRAME=(0,0))
			elif self.data["WPDATA"]["ACTIVE"] == "ACTIVE":
				self.doAnim(NAME=self.ANIMSET+"MeleeAttack", FRAME=(0,0), PRIORITY=3, MODE="LOOP", BLEND=blend)
			else:
				self.doAnim(NAME=self.ANIMSET+"Jumping", FRAME=(0,0), PRIORITY=3, MODE="LOOP", BLEND=blend)
			self.lastaction = [action, 0]

		elif action == "BLOCK":
			self.doAnim(NAME=self.ANIMSET+"MeleeBlock", FRAME=(0,0), PRIORITY=3, MODE="LOOP", BLEND=blend)
			self.lastaction = [action, 0]

		elif self.data["WPDATA"]["ACTIVE"] == "ACTIVE":
			if action == "FORWARD":
				self.doAnim(NAME=self.ANIMSET+"MeleeRunning", FRAME=(0,39), PRIORITY=3, MODE="LOOP", BLEND=blend)
				setframe = 39

			elif action == "STRAFE_L":
				self.doAnim(NAME=self.ANIMSET+"MeleeStrafeL", FRAME=(0,39), PRIORITY=3, MODE="LOOP", BLEND=blend)
				setframe = 39

			elif action == "STRAFE_R":
				self.doAnim(NAME=self.ANIMSET+"MeleeStrafeR", FRAME=(0,39), PRIORITY=3, MODE="LOOP", BLEND=blend)
				setframe = 39

			else:
				super().doPlayerAnim(action, blend)
				return

			if self.lastaction[0] != action:
				self.lastaction[0] = action
				self.doAnim(SET=self.lastaction[1]*setframe)

			self.lastaction[1] = self.doAnim(CHECK="FRAME")/setframe

		else:
			super().doPlayerAnim(action, blend)

	def doPlayerOnGround(self):
		owner = self.objects["Root"]
		char = self.objects["Character"]

		move = self.motion["Move"].normalized()
		speed = self.motion["Move"].length

		attack = self.data["ATTACKCHAIN"]
		ac = attack.split("_")[0]

		linLV = self.motion["Local"].copy()
		linLV[2] = 0
		lv = linLV.normalized()

		if attack == "BLOCK":
			mx = 0.05
		elif ac == "PLACE":
			mx = 0.0
		elif self.data["RUN"] == False or speed <= 0.7 or self.data["SPEED"] <= 0:
			mx = 0.035
		elif lv[1] < 0 and abs(lv[1]) > 0.5:
			mx = 0.05
		else:
			mx = self.data["SPEED"]

		vref = viewport.getDirection((move[0], move[1], 0))
		self.doMovement(vref, mx)
		self.doMoveAlign(up=False)

		action = "IDLE"

		if attack == "BLOCK":
			action = "BLOCK"

		elif linLV.length > 0.1 and ac not in ["STAND", "PLACE"]:
			action = "FORWARD"

			if lv[1] < 0:
				action = "BACKWARD"
			if lv[0] > 0 and abs(lv[1]) < 0.5:
				action = "STRAFE_R"
			if lv[0] < 0 and abs(lv[1]) < 0.5:
				action = "STRAFE_L"

			if linLV.length <= (0.04*60):
				action = "WALK_"+action

		self.doPlayerAnim(action, blend=10)

		## Jump/Crouch ##
		if keymap.BINDS["PLR_JUMP"].tap() == True:
			self.doJump(height=3.0, move=1.0, align=True)
		elif keymap.BINDS["PLR_DUCK"].active() == True:
			self.doCrouch(True)

	def PS_Abilities(self):
		owner = self.objects["Root"]
		if owner == None:
			return

		tx = 120
		if self.jump_state == "A_JUMP" and self.gravity.length > 1:
			if self.data["ENERGY"] > 5 and self.jump_timer < tx:
				vec = self.gravity.normalized()
				mx = (tx-self.jump_timer)/tx
				owner.applyForce(-vec*mx*15, False)
				self.data["ENERGY"] -= 0.4

	def weaponLoop(self):
		pri = self.getSlotChild("Hip_L")
		sec = self.getSlotChild("Hip_R")
		move = self.motion["Move"]
		linLV = self.motion["Local"].copy()
		linLV[2] = 0
		ac = self.data["ATTACKCHAIN"].split("_")[0]

		if (move.length > 0.01 and ac == "STAND") or (self.jump_state != "NONE" and ac not in ["NONE", "JUMP"]):
			self.doAnim(STOP=True, LAYER=0)
			self.doAnim(STOP=True, LAYER=1)
			self.data["ATTACKCHAIN"] = "NONE"
			self.data["COOLDOWN"] = 0

			self.sendEvent("WP_CLEAR", pri)
			self.sendEvent("WP_CLEAR", sec)
			return

		anim = self.ANIMSET+"MeleeAttack"

		if self.data["COOLDOWN"] <= 0:
			self.sendEvent("WP_CLEAR", pri)
			self.sendEvent("WP_CLEAR", sec)

			if self.jump_state != "NONE":
				if self.motion["Local"][2] > 0:
					if keymap.BINDS["ATTACK_ONE"].tap() == True:
						self.doAnim(NAME=anim+"Spin", FRAME=(0,40), LAYER=1, PRIORITY=0, BLEND=0)
						self.data["COOLDOWN"] = 40
						self.data["ATTACKCHAIN"] = "JUMP_SPIN"
						#if self.motion["Local"][2] < 2:
						#	self.objects["Root"].localLinearVelocity[2] = 2
				#else:
					#

			elif self.data["ATTACKCHAIN"] == "BLOCK":
				self.addModifier(SHIELD=self.data["ENERGY"])
				if keymap.BINDS["ATTACK_TWO"].active() == False:
					self.data["ATTACKCHAIN"] = "NONE"

			elif keymap.BINDS["ATTACK_TWO"].active() == True:
				self.doAnim(STOP=True, LAYER=0)
				self.doAnim(STOP=True, LAYER=1)
				self.data["COOLDOWN"] = 0
				self.data["ATTACKCHAIN"] = "BLOCK"

			elif move.length > 0.01 and keymap.BINDS["ATTACK_ONE"].tap() == True:
				if abs(move[0]) < abs(move[1]):
					if move[1] > 0.01:
						self.doAnim(NAME=anim+"Fast", FRAME=(0,35), LAYER=1, PRIORITY=0, BLEND=0)
						self.data["COOLDOWN"] = 35
						self.data["ATTACKCHAIN"] = "FORWARD_ONE"
					if move[1] < -0.01 and linLV.length < 2.5:
						self.doAnim(NAME=anim+"3", FRAME=(0,60), LAYER=1, PRIORITY=0, BLEND=0)
						self.data["COOLDOWN"] = 60
						self.data["ATTACKCHAIN"] = "PLACE_SPIN"

			elif self.data["ATTACKCHAIN"] == "NONE":
				if keymap.BINDS["ATTACK_ONE"].tap() == True:
					self.doAnim(NAME=anim, FRAME=(0,50), LAYER=0, PRIORITY=2, BLEND=10)
					self.data["COOLDOWN"] = 50
					self.data["ATTACKCHAIN"] = "STAND_ONE"

			elif self.data["ATTACKCHAIN"] == "STAND_ONE":
				if keymap.BINDS["ATTACK_ONE"].tap() == True:
					self.doAnim(NAME=anim, FRAME=(50,100), LAYER=0, PRIORITY=2, BLEND=10)
					self.data["COOLDOWN"] = 50
					self.data["ATTACKCHAIN"] = "STAND_TWO"

				#elif keymap.BINDS["ATTACK_ONE"].active() == True:
				#	self.doAnim(NAME=anim, FRAME=(50,50), LAYER=0, PRIORITY=2, BLEND=10)
				#	self.data["COOLDOWN"] = 0
				#	self.data["ENERGY"] -= 0.1

				elif self.data["COOLDOWN"] <= -300:
					self.doAnim(STOP=True, LAYER=0)
					self.doAnim(STOP=True, LAYER=1)
					#self.doAnim(NAME=anim+"Fail", FRAME=(0,10), LAYER=0, PRIORITY=2, BLEND=10)
					self.data["COOLDOWN"] = 0
					self.data["ATTACKCHAIN"] = "NONE"

				else:
					self.doAnim(NAME=anim, FRAME=(50,50), LAYER=0, PRIORITY=2, BLEND=10)
					self.data["COOLDOWN"] -= 1

			elif self.data["ATTACKCHAIN"] != "NONE":
				self.data["ATTACKCHAIN"] = "NONE"

		else:
			self.sendEvent("WP_FIRE", pri)
			self.sendEvent("WP_FIRE", sec)

			self.data["COOLDOWN"] -= 1

		self.objects["Character"]["DEBUG2"] = self.data["ATTACKCHAIN"]+": "+str(self.data["COOLDOWN"])

	def weaponManager(self):
		weap = self.data["WPDATA"]

		if self.player_id == None:
			weap["CURRENT"] = "NONE"
			weap["ACTIVE"] = "NONE"
			self.active_weapon = None
			return

		pri = self.getSlotChild("Hip_L")
		sec = self.getSlotChild("Hip_R")

		self.data["STRAFE"] = False

		if pri == None:
			if sec != None:
				pri = sec
			else:
				weap["CURRENT"] = "NONE"
				weap["ACTIVE"] = "NONE"
				self.active_weapon = None
				return

		weap["CURRENT"] = "MELEE"

		dict = weap["WHEEL"][weap["CURRENT"]]
		dict["ID"] = 0

		## STATE MANAGER ##
		if weap["ACTIVE"] == "ACTIVE":
			L = pri.stateSwitch(True)
			self.sendEvent("WP_HAND", pri, "MAIN")
			R = None
			if sec != None:
				R = sec.stateSwitch(True)
				self.sendEvent("WP_HAND", sec, "OFF")

			self.active_weapon = pri

			if L == True:
				self.sendEvent("WP_BLADE", pri)
				self.weaponLoop()
			if R == True:
				self.sendEvent("WP_BLADE", sec)

			self.data["STRAFE"] = True

			if keymap.BINDS["SHEATH"].tap() == True:
				self.doAnim(STOP=True, LAYER=0)
				self.doAnim(STOP=True, LAYER=1)
				self.data["ATTACKCHAIN"] = "NONE"
				weap["ACTIVE"] = "NONE"

		elif weap["ACTIVE"] == "NONE":
			pri.stateSwitch(False)
			if sec != None:
				sec.stateSwitch(False)

			self.active_weapon = None

			if keymap.BINDS["SHEATH"].tap() == True:
				weap["ACTIVE"] = "ACTIVE"


class LaserGun(weapon.CorePlayerWeapon):

	NAME = "Yup, its a gun -_-"
	SLOTS = ["Shoulder_R", "Shoulder_L"]
	TYPE = "RANGED"
	HAND = "MAIN"
	WAIT = 40
	SCALE = 1.0
	OFFSET = (0, -0.22, -0.06)

	def defaultData(self):
		self.env_dim = None

		dict = super().defaultData()
		dict["ROCKETS"] = 1
		dict["STRAFE"] = None

		return dict

	def PS_HandSocket(self):
		super().PS_HandSocket()

		if self.env_dim != None:
			self.objects["Mesh"].color = self.env_dim
			self.env_dim = None
		else:
			self.objects["Mesh"].color = (1,1,1,1)

	def ST_Startup(self):
		self.data["HUD"]["Text"] = "Rockets: "+str(self.data["ROCKETS"])
		self.data["HUD"]["Stat"] = 100*(self.data["ROCKETS"]>0)

	def ST_Idle(self):
		if self.data["STRAFE"] != None:
			self.owning_player.data["STRAFE"] = self.data["STRAFE"]
			self.data["STRAFE"] = None

	def ST_Active(self):
		owner = self.owner
		plr = self.owning_player
		plrobj = plr.objects["Root"]
		vec = viewport.getRayVec()
		#if plr.rayhit != None:
		#	vec = (plr.rayhit[1]-owner.worldPosition).normalized()

		self.data["HUD"]["Text"] = "Rockets: "+str(self.data["ROCKETS"])
		self.data["HUD"]["Stat"] = 100*(self.data["ROCKETS"]>0)

		pri = self.getFirstEvent("WP_FIRE", "PRIMARY")
		pri_tap = self.getFirstEvent("WP_FIRE", "PRIMARY", "TAP")
		sec = self.getFirstEvent("WP_FIRE", "SECONDARY")
		sec_tap = self.getFirstEvent("WP_FIRE", "SECONDARY", "TAP")

		if sec != None:
			if self.data["ROCKETS"] <= 0:
				if self.data["COOLDOWN"] >= 100:
					self.data["HUD"]["Text"] = "RELOADING: "+str(int(100-self.data["COOLDOWN"]))
					self.data["HUD"]["Stat"] = 100-((self.data["COOLDOWN"]-100)/0.3)
					vec = plrobj.getAxisVect([0,0,1])

				if self.data["COOLDOWN"] <= 10 and sec_tap != None:
					self.data["COOLDOWN"] = 130

				if 90 < self.data["COOLDOWN"] <= 100:
					self.data["ROCKETS"] = 1
					self.data["COOLDOWN"] = 0

			elif self.data["COOLDOWN"] <= 10 and sec_tap != None:
				ammo = base.SC_SCN.addObject("AMMO_Rocket", self.objects["Barrel"], 0)
				ammo["ROOTOBJ"] = plrobj
				ammo["TIME"] = 300
				ammo.localScale = (1, 1, 1)
				#vec += self.objects["Barrel"].getAxisVect((0,0,1))
				self.data["COOLDOWN"] = 10
				self.data["ROCKETS"] = 0

		elif self.data["COOLDOWN"] > 20:
			self.data["COOLDOWN"] = 0

		if self.data["COOLDOWN"] <= 0:
			if pri != None:
				sx, sy, sz = pri.getProp("SCALE", [1, 2, 1])
				rndx = (logic.getRandomFloat()-0.5)*0.1
				rndy = (logic.getRandomFloat()-0.5)*0.1
				rvec = self.objects["Barrel"].getAxisVect((rndx,5,rndy)).normalized()
				#vec += self.objects["Barrel"].getAxisVect((rndx,0,rndy)).normalized()*0.1

				ammo = base.SC_SCN.addObject("AMMO_Laser", self.objects["Barrel"], 100)
				ammo.alignAxisToVect(ammo.getVectTo(base.SC_SCN.active_camera)[1], 2, 1.0)
				ammo.alignAxisToVect(rvec, 1, 1.0)
				ammo["ROOTOBJ"] = plrobj
				ammo["DAMAGE"] = 15.0
				#ammo["LINV"] = plrobj.worldLinearVelocity*(1/60)
				ammo.localScale = (sx, sy, sz)
				ammo.color = (1,1,1,1)
				ammo.children[0].color = pri.getProp("COLOR", [0, 0.5, 1, 1])

				gfx = base.SC_SCN.addObject("GFX_MuzzleFlash", self.objects["Barrel"], 0)
				gfx.setParent(self.objects["Barrel"], False, False)
				gfx.localScale = (1.0, 1.0, 1.0)
				gfx.children[0].color = (1,1,1,1)
				self.data["COOLDOWN"] = 10

		else:
			self.data["COOLDOWN"] -= 1

		self.sendEvent("WEAPON", plr, "TYPE", TYPE="Rifle")

		if self.data["STRAFE"] == None:
			self.data["STRAFE"] = plr.data["STRAFE"]
		plr.data["STRAFE"] = True

		hrz = plrobj.getAxisVect((0,0,1))
		ang = self.toDeg(vec.angle(hrz))/180

		hand = plr.HAND.get(self.data["HAND"], "").split("_")
		if len(hand) > 1:
			anim = plr.ANIMSET+"RangedRifleAim"+hand[1]
			plr.doAnim(NAME=anim, FRAME=(-5,25), LAYER=1, BLEND=10)
			plr.doAnim(LAYER=1, SET=ang*20)

		up = viewport.VIEWCLASS.objects["Rotate"].getAxisVect((1,0,0))
		fw = plrobj.getAxisVect((0,1,0))

		if fw.dot(vec) > 0.5 and vec.length > 0.01:
			self.objects["Mesh"].alignAxisToVect(vec.normalized(), 1, 1.0)
			self.objects["Mesh"].alignAxisToVect(up, 0, 1.0)
		else:
			self.objects["Mesh"].localOrientation = self.createMatrix()


class Lightsaber(objects.BasicSword):

	NAME = "Lightsaber"
	HAND = "AUTO"
	WAIT = 30
	SCALE = 0.7
	OFFSET = (0,0,0)
	BLADETYPE = "GFX_LightSaber.Blade"
	BLADECOLOR = (1,1,1,1)
	BLADESIZE = 1
	BLADELENGTH = 1
	BLADETIME = 10

	def addBlade(self):
		blade = self.objects["Blade"]
		self.gfx_blade = blade.scene.addObject(self.BLADETYPE, blade, 0)
		self.gfx_blade.setParent(blade)
		self.gfx_blade.color = self.BLADECOLOR
		self.gfx_blade.visible = False
		self.gfx_blade["SIZE"] = self.BLADESIZE
		self.gfx_blade.localPosition = (0,0,0)
		self.gfx_blade.localScale = (1,0,1)
		if self.PS_ManageBlade not in self.active_post:
			self.active_post.append(self.PS_ManageBlade)
		self.env_dim = None

	def ST_Startup(self):
		self.addBlade()

	def PS_ManageBlade(self):
		blade = self.gfx_blade
		vis = False
		fac = 0
		evt = self.getFirstEvent("WP_BLADE")

		if evt != None:
			blade.localScale[1] += self.BLADELENGTH/self.BLADETIME
		else:
			blade.localScale[1] -= self.BLADELENGTH/self.BLADETIME

		if blade.localScale[1] <= 0:
			blade.localScale[1] = 0
		if blade.localScale[1] >= self.BLADELENGTH:
			blade.localScale[1] = self.BLADELENGTH

		if blade.localScale[1] > 0.05:
			vis = self.objects["Mesh"].visible

		blade.setVisible(vis, True)

		if self.env_dim != None:
			self.objects["Mesh"].color = self.env_dim
			self.env_dim = None
		else:
			self.objects["Mesh"].color = (1,1,1,1)


class LightsaberO(Lightsaber):

	NAME = "Knights Lightsaber"
	BLADECOLOR = (0,0.3,1,1)

class LightsaberW(Lightsaber):

	NAME = "Masters Lightsaber"
	BLADECOLOR = (0.4,0,1,1)

class LightsaberV(Lightsaber):

	NAME = "Ergonomic Lightsaber"
	BLADETYPE = "GFX_LightSaber.BladeToon"
	BLADECOLOR = (1,0,0,1)
	BLADESIZE = 0.8

class LightsaberYs(Lightsaber):

	NAME = "Ahsoka's Other Lightsaber"
	SLOTS = ["Hip_R"]
	HAND = "OFF"
	BLADECOLOR = (1,1,0,1)
	BLADETYPE = "GFX_LightSaber.BladeToon"
	BLADELENGTH = 0.7

class LightsaberG(Lightsaber):

	NAME = "Ahsoka's Lightsaber"
	SLOTS = ["Hip_L"]
	HAND = "MAIN"
	BLADECOLOR = (0,1,0,1)
	BLADETYPE = "GFX_LightSaber.BladeToon"

