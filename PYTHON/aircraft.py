
## AIRCRAFT OBJECTS ##


import math

from bge import logic

from game3 import vehicle, keymap, HUD, viewport, input


class WeaponsFirebird(HUD.Weapons):

	OBJECT = "FirebirdPylons"

	def ST_Startup(self):
		self.blinker = 0

	def ST_Active(self, plr):
		weap = plr.data["WPDATA"]

		root = self.objects["Root"]

		wh = ["G", "1", "2", "3", "C"]
		p = plr.data["PYLON"]
		s = wh[p[0]]
		n = wh[p[1]]

		if self.blinker > 10:
			n = "X"
		if self.blinker > 20:
			self.blinker = -1
		self.blinker += 1

		if weap["ACTIVE"] == "NONE":
			root.color = (0.4, 0.4, 0.4, 0.5)
		else:
			root.color = (0.0, 0.0, 0.0, 0.5)

		## PYLONS ##
		for i in ["C0", "L1", "L2", "L3", "R1", "R2", "R3"]:
			cls = plr.getSlotChild(i)

			if weap["ACTIVE"] == "NONE":
				if s in i or n in i:
					self.objects[i].color = (0.0, 0.0, 0.0, 0.5)
				else:
					self.objects[i].color = (0.4, 0.4, 0.4, 0.5)
			else:
				if s in i:
					self.objects[i].color = (0.0, 1.0, 0.0, 0.5)
				elif n in i:
					self.objects[i].color = (0.8, 0.0, 0.0, 0.5)
				elif cls == None:
					self.objects[i].color = (0.0, 0.0, 0.0, 0.5)
				else:
					self.objects[i].color = (0.4, 0.4, 0.4, 0.5)

		## GUNS ##
		for i in ["LG", "RG"]:
			cls = plr.getSlotChild(i)

			x = 0
			if cls != None:
				x = cls.data["HUD"]["Stat"]/100

			if weap["ACTIVE"] == "NONE":
				if s in i or n in i:
					self.objects[i].color = (x, 1, 0.0, 1)
				else:
					self.objects[i].color = (x, 1, 0.5, 1)
			else:
				if s in i:
					self.objects[i].color = (x, 1, 1.0, 1)
				elif n in i:
					self.objects[i].color = (x, 1, 0.8, 1)
				elif cls == None:
					self.objects[i].color = (0, 1, 0.0, 1)
				else:
					self.objects[i].color = (x, 1, 0.5, 1)


class LayoutFirebird(HUD.HUDLayout):

	GROUP = "Core"
	MODULES = [HUD.Stats, HUD.Aircraft, HUD.MousePos, WeaponsFirebird] #HUD.Inventory]


class FireBird(vehicle.CoreAircraft):

	NAME = "VTOL Jet Plane"
	LANDACTION = "FirebirdRigLand"
	HUDLAYOUT = LayoutFirebird

	INVENTORY = {"LG":"WP_ZCannon", "RG":"WP_ZCannon", "L2":"WP_ZMissile", "R2":"WP_ZMissile"}
	SLOTS = {"ONE":"G", "TWO":"1", "THREE":"2", "FOUR":"3"}

	CAM_RANGE = (8, 18)
	CAM_ZOOM = 3
	CAM_MIN = 1
	CAM_SLOW = 8
	CAM_HEAD_G = 8

	WH_FRONT = 2.5
	WH_REAR = -1
	WH_WIDTH = 0.9
	WH_HEIGHT = 0.8

	VEH_LENGTH = 0.5

	VEH_ROLL = 0
	VEH_SPRING = 50
	VEH_DAMPING = 8
	VEH_FRICTION = 5

	WHEELS = {
		"Wheel_FC": {"CENTER":True},
		"Wheel_RR": {"REAR":True},
		"Wheel_RL": {"REAR":True, "LEFT":True} }

	SEATS = {
		"Seat_1": {"NAME":"Pilot", "DOOR":"Root", "CAMERA":[0,0.7,0.7], "ACTION":"SeatTall", "VISIBLE":True, "SPAWN":[-1.5,2,0]} }

	AERO = {"POWER":5000, "REVERSE":0.25, "HOVER":500, "LIFT":0.15, "TAIL":0, "DRAG":(2,0,5)}

	def defaultData(self):
		dict = super().defaultData()
		dict["GLASSFRAME"] = 120
		dict["COOLDOWN"] = 0
		dict["PYLON"] = [0, 0]

		return dict

	def applyModifier(self, dict):
		if "HEALTH" in dict:
			dict["HEALTH"] *= 0.25
		super().applyModifier(dict)

	def airDrag(self):
		linV = self.owner.localLinearVelocity
		grav = self.gravity.length
		mx = linV[1]
		if mx > 5000:
			mx = 5000
		dampLin = (9.8-grav)/(9.8/0.1)
		dampRot = (mx*0.002)+0.4

		if dampRot >= 0.7:
			dampRot = 0.7

		self.owner.setDamping(dampLin, dampRot)

		drag = list(self.AERO["DRAG"])
		drag[1] = (1-(self.data["LANDFRAME"]/100))+5
		drag[1] *= 0.1

		self.doDragForce(drag)

		if linV.length < 0.01:
			return

		tx, ty, tz = self.motion["Torque"]
		v = linV.normalized()
		l = ((linV.length*0.5)**2)*self.air_drag
		x = self.createVector(vec=(-1, tz*0.02, 0)).normalized()
		z = self.createVector(vec=( 0, tx*0.1,  1)).normalized()

		self.owner.applyTorque((z.dot(v)*l, 0, x.dot(v)*l*0.5), True)

	def ST_Startup(self):
		self.ANIMOBJ = self.objects["Rig"]
		self.doLandingGear(init=True)
		g = self.data["GLASSFRAME"]
		self.doAnim(NAME="FirebirdRigGlass", FRAME=(g-1,g), LAYER=1)
		self.active_post.append(self.airDrag)
		self.active_post.append(self.airLift)

	def stateSwitch(self, state=None):
		if state != None:
			pass
		elif self.driving_seat == ".":
			state = "DRIVER"
		else:
			state = self.SEATS[self.driving_seat].get("STATE", "DRIVER")

		if state == "DRIVER":
			self.data["COOLDOWN"] = 0
			self.doAnim(NAME="FirebirdRigGlass", FRAME=(0,-1), LAYER=1)
			self.active_state = self.ST_Active

		elif state == "ENTER":
			self.assignCamera()
			self.data["GLASSFRAME"] = 120
			self.doAnim(NAME="FirebirdRigGlass", FRAME=(120,0), LAYER=1)
			self.active_state = self.ST_Enter

		elif state == "EXIT":
			self.data["GLASSFRAME"] = 0
			self.doAnim(NAME="FirebirdRigGlass", FRAME=(0,120), LAYER=1)
			self.active_state = self.ST_Exit

		elif state == "IDLE":
			if self.removeFromSeat(self.driving_seat) == True:
				self.data["GLASSFRAME"] = 120
				self.doAnim(NAME="FirebirdRigGlass", FRAME=(120,121), LAYER=1)
				self.driving_seat = None
				self.active_state = self.ST_Idle
			else:
				self.stateSwitch("ENTER")

	def toggleWeapons(self, state=None):
		sl = ["LG", "L1", "L2", "L3", "RG", "R1", "R2", "R3"] #, "C0"]
		for slot in sl:
			cls = self.getSlotChild(slot)
			if cls != None:
				cls.stateSwitch(state)

	## ACTIVE STATE ##
	def ST_Active(self):
		self.getInputs()

		owner = self.objects["Root"]
		mesh = self.objects["Mesh"]

		torque = self.motion["Torque"]
		linV = owner.localLinearVelocity

		## FORCES ##
		power, hover = self.getEngineForce()

		fac = self.data["POWER"]/self.AERO["POWER"]
		mx = abs(linV[1])
		if mx > 5000:
			mx = 5000
		tqx = torque[0]*400 #*(400+(mx*0.8))
		tqy = torque[1]*(800+(mx*1.5))
		tqz = torque[2]*400 #*(400+(mx*0.2))

		ad = self.air_drag
		owner.applyTorque([tqx*ad, tqy*ad, tqz*ad], True)
		owner.applyForce([0, (power-(linV[1]*5*fac))*ad, hover*ad], True)

		## EXTRAS ##
		self.data["HUD"]["Power"] = abs(fac)*100*ad
		self.data["HUD"]["Lift"] = (self.data["HOVER"][0]/9.8)+((self.data["HOVER"][1]/self.AERO["HOVER"])*33)

		mesh.color[0] = abs(fac)*ad
		if mesh.color[1] < 1:
			mesh.color[1] += 0.01
		else:
			mesh.color[1] = 1

		#self.doAnim(NAME="ArmatureIdle", FRAME=(0,0), LAYER=2)

		for bone in list(self.objects["Rig"].channels):
			if bone.name == "ElevatorL":
				bone.rotation_euler = self.createVector(vec=[0,math.radians(-10*torque[0]),0])
			if bone.name == "ElevatorR":
				bone.rotation_euler = self.createVector(vec=[0,math.radians(10*torque[0]),0])
			if bone.name == "RollL":
				bone.rotation_euler = self.createVector(vec=[0,math.radians(30*torque[1]),0])
			if bone.name == "RollR":
				bone.rotation_euler = self.createVector(vec=[0,math.radians(30*torque[1]),0])
			if bone.name == "RudderL":
				bone.rotation_euler = self.createVector(vec=[0,math.radians(-10*torque[2]),0])
			if bone.name == "RudderR":
				bone.rotation_euler = self.createVector(vec=[0,math.radians(-10*torque[2]),0])

		self.objects["Rig"].update()

		steer = torque[2]*0.3
		brake = 0

		if keymap.BINDS["VEH_DESCEND"].active() == True:
			brake = 10

		self.setWheelSteering(steer, "FRONT")
		self.setWheelBrake(brake, "REAR")

		## WEAPONS ##
		wh = ["G", "3", "2", "1"]
		p = self.data["PYLON"]
		weap = self.data["WPDATA"]

		if weap["ACTIVE"] == "NONE":
			if keymap.BINDS["SHEATH"].tap() == True:
				weap["ACTIVE"] = "ACTIVE"
				p[1] = p[0]
				self.data["COOLDOWN"] = 0
				self.toggleWeapons(True)

		elif self.data["COOLDOWN"] < 60:
			if keymap.BINDS["WP_DOWN"].tap() == True:
				self.data["COOLDOWN"] = 0
				chk = 0
				while chk < 5:
					p[1] += 1
					if p[1] > (len(wh)-1):
						p[1] = 0

					s = ["L"+wh[p[1]], "R"+wh[p[1]]]
					for i in s:
						if self.getSlotChild(i) != None:
							chk = 5
					if p[1] == p[0]:
						chk = 5
					chk += 1

			if keymap.BINDS["WP_UP"].tap() == True:
				self.data["COOLDOWN"] = 0
				chk = 0
				while chk < 5:
					p[1] -= 1
					if p[1] < 0:
						p[1] = (len(wh)-1)

					s = ["L"+wh[p[1]], "R"+wh[p[1]]]
					for i in s:
						if self.getSlotChild(i) != None:
							chk = 5
					if p[1] == p[0]:
						chk = 5
					chk += 1

			if p[0] != p[1]:
				self.data["COOLDOWN"] += 1
			else:
				self.data["COOLDOWN"] = 0

			s = ["L"+wh[p[0]], "R"+wh[p[0]]]

			for i in s:
				cls = self.getSlotChild(i)
				if cls != None and keymap.BINDS["ATTACK_ONE"].active() == True:
					self.sendEvent("WP_FIRE", cls, "TAP")

			if keymap.BINDS["SHEATH"].tap() == True:
				self.data["COOLDOWN"] = 0
				p[1] = p[0]
				weap["ACTIVE"] = "NONE"
				self.toggleWeapons(False)

		else:
			self.data["COOLDOWN"] = 0
			p[0] = p[1]

		if keymap.BINDS["ENTERVEH"].tap() == True and linV.length < 10:
			self.stateSwitch("EXIT")

	def ST_Idle(self):
		self.setWheelBrake(1, "REAR")

		mesh = self.objects["Mesh"]
		if mesh.color[1] > 0:
			mesh.color[1] -= 0.01
		else:
			mesh.color[1] = 0

		if self.checkClicked() == True:
			self.stateSwitch("ENTER")

	def ST_Enter(self):
		self.setWheelBrake(1, "REAR")
		self.doCameraToggle()
		self.data["GLASSFRAME"] -= 1
		if self.data["GLASSFRAME"] <= 0:
			self.stateSwitch()

	def ST_Exit(self):
		self.setWheelBrake(1, "REAR")
		self.doCameraToggle()

		mesh = self.objects["Mesh"]
		if mesh.color[1] > 0:
			mesh.color[1] -= 0.01
		else:
			mesh.color[1] = 0

		self.data["GLASSFRAME"] += 1
		if self.data["GLASSFRAME"] >= 120:
			self.stateSwitch("IDLE")


class Ultralight(vehicle.CoreAircraft):

	NAME = "Prop Plane"

	INVENTORY = {}
	SLOTS = {}

	CAM_RANGE = (8, 16)
	CAM_HEIGHT = 0.2
	CAM_STEPS = 3
	CAM_ZOOM = 2
	CAM_SLOW = 15
	CAM_MIN = 1.5
	CAM_OFFSET = (0,0,0)

	MOUSE_CENTER = False
	MOUSE_ROLL = -1
	INPUT_SMOOTH = 0.03

	WH_OBJECT = "Wheel.Small"
	WH_MESH = None
	WH_RADIUS = 0.2
	WH_COLOR = None

	WH_HEIGHT = 0.0
	VEH_LENGTH = 0.7

	VEH_ROLL = 0
	VEH_SPRING = 50
	VEH_DAMPING = 8
	VEH_FRICTION = 5

	WHEELS = {
		"Wheel_FR": {"POS":[ 1,  1.0, -0.7] },
		"Wheel_FL": {"POS":[-1,  1.0, -0.7] },
		"Wheel_RC": {"POS":[ 0, -5.0, -0.0], "REAR":True, "STEER":True}
		}

	SEATS = {
		"Seat_1": {"NAME":"Pilot", "DOOR":"Door_1", "CAMERA":[-0.35, 0.3, 0.3], "ACTION":"SeatTall", "VISIBLE":True, "SPAWN":[-1.5, 0.5, -0.5]},
		"Seat_2": {"NAME":"CoPilot", "DOOR":"Door_2", "CAMERA":[0.35, 0.3, 0.3], "ACTION":"SeatTallP", "VISIBLE":True, "SPAWN":[1.5, 0.5, -0.5]}
		}

	AERO = {"POWER":30, "REVERSE":0, "HOVER":0, "LIFT":0.3, "TAIL":0, "DRAG":(0.1,0.01,0.2)}

	def airDrag(self):
		linV = self.owner.localLinearVelocity

		self.owner.setDamping(0.0, 0.7)

		self.doDragForce()

		if linV.length < 0.01:
			return

		v = linV.normalized()
		l = (linV.length*0.5)**2
		x = self.createVector(vec=[-1,0,0])
		z = self.createVector(vec=[0,0,1])

		self.owner.applyTorque([z.dot(v)*l, 0, x.dot(v)*l], True)

	def ST_Startup(self):
		self.ANIMOBJ = self.objects["Rig"]

		self.active_post.append(self.airLift)
		self.active_post.append(self.airDrag)

	## ACTIVE STATE ##
	def ST_Active(self):
		self.getInputs()

		owner = self.objects["Root"]
		mesh = self.objects["Mesh"]

		force = self.motion["Force"]
		torque = self.motion["Torque"]
		linV = owner.localLinearVelocity
		mx = (linV[1]*0.1)**2

		power, hover = self.getEngineForce()
		fac = power/self.AERO["POWER"]

		eng = self.objects["Eng"]["Y"]
		y = power-(linV[1]*0.5*fac)

		owner.applyForce((0,y,0), True)

		owner.applyTorque((torque[0]*4*mx, torque[1]*8*mx, torque[2]*2*mx), True)

		p = torque[0]*-20
		y = torque[2]*-20
		self.objects["Surf"]["CP"].localOrientation = self.createMatrix(rot=[p,0,0])
		self.objects["Surf"]["CY"].localOrientation = self.createMatrix(rot=[0,0,y])

		r = torque[1]*20
		self.objects["Surf"]["CRL"].localOrientation = self.createMatrix(rot=[r,0,0])
		self.objects["Surf"]["CRR"].localOrientation = self.createMatrix(rot=[-r,0,0])

		## EXTRAS ##
		eng.color[0] += 0.03
		if eng.color[0] > 1:
			eng.color[0] = 1
		rpm = eng.color[0]
		eng.applyRotation([0,(fac+0.5)*rpm,0], True)
		self.data["HUD"]["Power"] = abs(fac)*100
		self.data["HUD"]["Lift"] = self.lift*2

		steer = torque[2]*-0.5
		brake = 0

		if keymap.BINDS["VEH_THROTTLEDOWN"].active() == True and power < 1:
			brake = 0.1

		self.setWheelSteering(steer, "REAR")
		self.setWheelBrake(brake, "FRONT")

		## Reset ##
		if keymap.BINDS["VEH_ACTION"].tap() == True:
			self.alignObject()

		if keymap.BINDS["ENTERVEH"].tap() == True and linV.length < 10:
			self.stateSwitch("IDLE")

	def ST_Idle(self):
		self.setWheelBrake(0.1, "FRONT")
		eng = self.objects["Eng"]["Y"]
		rpm = eng.color[0]
		if rpm > 0:
			eng.applyRotation([0,0.5*rpm,0], True)
			eng.color[0] -= 0.01
		else:
			eng.color[0] = 0

		if self.checkClicked() == True:
			self.stateSwitch()

