
## GAME OBJECTS ##


from bge import logic

from game3 import base, keymap, attachment, weapon, powerup, viewport


class SceneObject(base.CoreObject):

	NAME = ""
	GHOST = False
	INTERACT = False
	PHYSICS = "NONE"

class PhysicsObject(SceneObject):

	NAME = ""
	PHYSICS = "RIGID"

	def ST_Startup(self):
		self.addCollisionCallBack()


class JetPack(attachment.CoreAttachment):

	NAME = "JetPack"
	SLOTS = ["Back"]
	SCALE = 0.74
	OFFSET = (0, 0.03, 0.1)
	ENABLE = True
	POWER = 16
	FUEL = 10000
	BURNRATE = 30
	CHARGERATE = 17

	def defaultData(self):
		self.power = self.createVector(3)
		self.env_dim = None

		dict = super().defaultData()
		dict["FUEL"] = self.FUEL
		dict["BURN"] = self.BURNRATE
		dict["CHARGE"] = self.CHARGERATE

		return dict

	def doEffects(self, state=None):
		if state in ["INIT", "STOP"]:
			self.randlist = [0]*3
			self.objects["Fire"].localScale = (1, 1, 0)
			return

		rand = 0

		for i in self.randlist:
			rand += i
		rand = (rand/3)

		self.objects["Fire"].localScale = (1, 1, rand)

		self.randlist.insert(0, (logic.getRandomFloat()*0.25)+self.power.length)
		self.randlist.pop()

	def ST_Startup(self):
		self.doEffects("INIT")
		self.active_pre.append(self.PR_Modifiers)

	def ST_Enable(self):
		self.data["ENABLE"] = True
		self.active_state = self.ST_Active

	def ST_Stop(self):
		self.doEffects("STOP")
		if self.owning_player.jump_state == "JETPACK":
			self.owning_player.jump_state = "B_JUMP"

		self.data["ENABLE"] = False
		self.active_state = self.ST_Idle

	def PR_Modifiers(self):
		if self.owning_player == None:
			self.owner.color = (1,1,1,1)
			self.env_dim = None
			return

		if self.env_dim != None:
			self.owner.color = self.env_dim
			self.env_dim = None
		else:
			self.owner.color = (1,1,1,1)

		newburn = self.BURNRATE
		newcharge = self.CHARGERATE

		for dict in self.owning_player.data["MODIFIERS"].copy():
			if "FUEL" in dict:
				self.data["FUEL"] += dict["FUEL"]
				if self.data["FUEL"] > self.FUEL:
					self.data["FUEL"] = self.FUEL
				if self.data["FUEL"] < 0:
					self.data["FUEL"] = 0
			if "JETBURN" in dict:
				newburn = dict["JETBURN"]
			if "JETCHARGE" in dict:
				newcharge = dict["JETCHARGE"]

		self.data["BURN"] = newburn
		self.data["CHARGE"] = newcharge

		self.data["HUD"]["Stat"] = round( (self.data["FUEL"]/self.FUEL)*100 )
		self.data["HUD"]["Text"] = str(self.data["HUD"]["Stat"])

	def ST_Active(self):
		plr = self.owning_player
		owner = self.objects["Root"]

		self.power[0] = 0
		self.power[1] = 0
		self.power[2] = 0

		if plr.objects["Root"] != None:
			if plr.jump_state == "B_JUMP":
				plr.jump_state = "JETPACK"
			elif plr.jump_state == "FLYING" and keymap.BINDS["PLR_JUMP"].active() == True:
				plr.jump_state = "JETPACK_FLY"

		if plr.jump_state == "JETPACK":
			if self.data["FUEL"] > 0 and plr.gravity.length > 1:
				self.power = plr.objects["Root"].getAxisVect((0,0,1))

				if plr.motion["Move"].length > 0.01:
					move = plr.motion["Move"].normalized()
					mref = viewport.getDirection((move[0], move[1], 0))
					self.power += mref

					self.power.normalize()

				linLV = plr.objects["Root"].localLinearVelocity*(1/60)
				linLV[2] = 0
				linWV = plr.objects["Root"].worldOrientation*linLV

				if plr.data.get("STRAFE", False) == True or plr.data["CAMERA"]["State"] != "THIRD":
					plr.doMoveAlign()
					#plr.alignPlayer(factor=0.2)
				else: #if linLV.length > 0.001:
					#plr.alignPlayer(factor=0.2, axis=linWV)
					plr.doMoveAlign(axis=linWV*0.2)

				plr.objects["Root"].applyForce(self.power*self.POWER*(plr.gravity.length/9.8), False)
				self.data["FUEL"] -= self.data["BURN"]
			else:
				plr.jump_state = "B_JUMP"

		elif plr.jump_state == "JETPACK_FLY":
			if self.data["FUEL"] > 0 and plr.objects["Root"] != None:
				self.power = plr.objects["Root"].getAxisVect((0,0,1))
				plr.objects["Root"].applyForce(self.power*self.POWER, False)
				self.data["FUEL"] -= self.data["BURN"]
			else:
				plr.jump_state = "FLYING"

		else:
			self.randlist = [0]*3
			if self.data["FUEL"] < self.FUEL:
				self.data["FUEL"] += self.data["CHARGE"]
			else:
				self.data["FUEL"] = self.FUEL

		if self.data["FUEL"] < 0:
			self.data["FUEL"] = 0

		self.doEffects()


class JetFuel(powerup.CorePowerup):

	NAME = "Jetpack Fuel"
	MODIFIER = {"FUEL":10000}
	WAIT = 1000
	CAMPING = True
	SCALE = 2
	COLOR = (1.0, 0.5, 0.5, 1)

	def checkData(self, cls):
		state = False
		objlist = ["INV_JetPack", "INV_Firefly", "INV_JumpPack"]

		for dict in cls.dict["Children"]:
			if dict["Object"] in objlist and dict["Data"].get("FUEL", 10000) < 9999:
				state = True
		return state


class JetTime(powerup.CorePowerup):

	NAME = "Efficient Jet Fuel"
	MODIFIER = {"JETBURN":10}
	DURATION = 600
	WAIT = 1000
	STACK_TYPE = "REPLACE"
	STACK_LIMIT = 1
	CAMPING = True
	SCALE = 2
	COLOR = (0.5, 1.0, 0.5, 1)

	def checkData(self, cls):
		for dict in cls.dict["Children"]:
			if dict["Object"] == "INV_JetPack":
				return True
		return False


class MachineGun(weapon.CorePlayerWeapon):

	NAME = "Basic SMG"
	SLOTS = ["Shoulder_R", "Shoulder_L"]
	TYPE = "RANGED"
	HAND = "MAIN"
	WAIT = 40
	SCALE = 1.0
	OFFSET = (0, -0.25, -0.05)

	def defaultData(self):
		self.env_dim = None

		dict = super().defaultData()
		dict["MAG"] = 30
		dict["STRAFE"] = None
		dict["RELOAD"] = False

		return dict

	def PS_HandSocket(self):
		super().PS_HandSocket()

		if self.env_dim != None:
			self.objects["Mesh"].color = self.env_dim
			self.env_dim = None
		else:
			self.objects["Mesh"].color = (1,1,1,1)

	def ST_Startup(self):
		self.data["HUD"]["Text"] = "Ammo: "+str(self.data["MAG"])
		self.data["HUD"]["Stat"] = (self.data["MAG"]/30)*100

	def ST_Idle(self):
		if self.data["STRAFE"] != None:
			self.owning_player.data["STRAFE"] = self.data["STRAFE"]
			self.data["STRAFE"] = None

	def ST_Active(self):
		owner = self.owner
		camera = base.SC_SCN.active_camera

		mesh = self.objects["Mesh"]
		barrel = self.objects["Barrel"]

		plr = self.owning_player
		plrobj = plr.objects["Root"]

		vec = viewport.getRayVec()

		pri = self.getFirstEvent("WP_FIRE", "PRIMARY")
		pri_tap = self.getFirstEvent("WP_FIRE", "PRIMARY", "TAP")
		sec = self.getFirstEvent("WP_FIRE", "SECONDARY")
		sec_tap = self.getFirstEvent("WP_FIRE", "SECONDARY", "TAP")

		if self.data["RELOAD"] == True:
			self.data["COOLDOWN"] -= 1
			self.data["HUD"]["Text"] = "RELOADING"
			self.data["HUD"]["Stat"] = (1-(self.data["COOLDOWN"]/60))*100
			if self.data["COOLDOWN"] <= 0:
				self.data["RELOAD"] = False
				self.data["MAG"] = 30
			vec = plrobj.getAxisVect((0,1,1))

		elif self.data["COOLDOWN"] <= 0:
			if self.data["MAG"] <= 0:
				self.data["MAG"] = 0
				self.data["RELOAD"] = True
				self.data["COOLDOWN"] = 60

			elif pri != None:
				sx, sy, sz = pri.getProp("SCALE", [0.25, 0.25, 0.25])
				rnd = logic.getRandomFloat()
				rndx = (logic.getRandomFloat()-0.5)*0.05
				rndy = (logic.getRandomFloat()-0.5)*0.05
				rvec = barrel.getAxisVect((rndx,5,rndy)).normalized()

				ammo = base.SC_SCN.addObject("AMMO_Bullet", barrel, 50)
				ammo.alignAxisToVect(ammo.getVectTo(camera)[1], 2, 1.0)
				ammo.alignAxisToVect(rvec, 1, 1.0)
				ammo["ROOTOBJ"] = plrobj
				ammo["DAMAGE"] = 10.0
				#ammo["LINV"] = plrobj.worldLinearVelocity*(1/60)
				ammo.localScale = (sx, 16+(rnd*4), sz)
				ammo.color = (1.0, 0.8, 0.5, 1)
				ammo.children[0].localScale = (1, 0.1+(rnd*0.9), 1)
				ammo.children[0].color = pri.getProp("COLOR", [1, 1, 0, 1])

				gfx = base.SC_SCN.addObject("GFX_MuzzleFlash", barrel, 0)
				gfx.setParent(barrel, False, False)
				gfx.localScale = (1.0, 2.0, 1.0)
				gfx.children[0].color = (1,1,0,1)

				rndx = (logic.getRandomFloat()*2.0)-1.0
				rndy = (logic.getRandomFloat()*1.0)-0.0
				mesh.worldPosition -= barrel.getAxisVect((0, 0.04, 0))
				mesh.localOrientation *= self.createMatrix(rot=(rndy, 0, rndx), deg=True)

				self.data["MAG"] -= 1
				self.data["COOLDOWN"] = 5

		else:
			self.data["COOLDOWN"] -= 1

		self.data["HUD"]["Text"] = "Ammo: "+str(self.data["MAG"])
		self.data["HUD"]["Stat"] = (self.data["MAG"]/30)*100

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
			mesh.localPosition *= 0.8
			mesh.alignAxisToVect(vec.normalized(), 1, 0.2)
			mesh.alignAxisToVect(up, 0, 0.2)
		else:
			mesh.localPosition = self.createVector()
			mesh.localOrientation = self.createMatrix()


class HandGun(weapon.CorePlayerWeapon):

	NAME = "Basic Pistol"
	SLOTS = ["Hip_R", "Hip_L"]
	TYPE = "RANGED"
	HAND = "MAIN"
	WAIT = 20
	SCALE = 0.7
	OFFSET = (0, -0.08, -0.04)

	def defaultData(self):
		self.env_dim = None

		dict = super().defaultData()
		dict["MAG"] = 8
		dict["STRAFE"] = None
		dict["RELOAD"] = False

		return dict

	def PS_HandSocket(self):
		super().PS_HandSocket()

		if self.env_dim != None:
			self.objects["Mesh"].color = self.env_dim
			self.env_dim = None
		else:
			self.objects["Mesh"].color = (1,1,1,1)

	def ST_Startup(self):
		self.data["HUD"]["Text"] = "Ammo: "+str(self.data["MAG"])
		self.data["HUD"]["Stat"] = (self.data["MAG"]/8)*100

	def ST_Active(self):
		owner = self.owner
		camera = base.SC_SCN.active_camera

		mesh = self.objects["Mesh"]
		barrel = self.objects["Barrel"]

		plr = self.owning_player
		plrobj = plr.objects["Root"]

		vec = viewport.getRayVec()

		self.data["HUD"]["Text"] = "Ammo: "+str(self.data["MAG"])
		self.data["HUD"]["Stat"] = (self.data["MAG"]/8)*100

		pri = self.getFirstEvent("WP_FIRE", "PRIMARY")
		pri_tap = self.getFirstEvent("WP_FIRE", "PRIMARY", "TAP")
		sec = self.getFirstEvent("WP_FIRE", "SECONDARY")
		sec_tap = self.getFirstEvent("WP_FIRE", "SECONDARY", "TAP")

		mv = False
		if plrobj.worldLinearVelocity.length*(1.60) > 0.01:
			mv = True
			sec = None
			sec_tap = None

		if self.data["RELOAD"] == True:
			self.data["COOLDOWN"] -= 1
			self.data["HUD"]["Text"] = "RELOADING"
			self.data["HUD"]["Stat"] = (1-(self.data["COOLDOWN"]/60))*100
			if self.data["COOLDOWN"] <= 0:
				self.data["RELOAD"] = False
				self.data["MAG"] = 8
			sec = None

		elif self.data["COOLDOWN"] <= 0:
			if self.data["MAG"] <= 0:
				self.data["MAG"] = 0
				self.data["RELOAD"] = True
				self.data["COOLDOWN"] = 60

			elif pri_tap != None and sec != None:
				sx, sy, sz = pri.getProp("SCALE", [0.25, 0.25, 0.25])
				rnd = logic.getRandomFloat()
				rndx = (logic.getRandomFloat()-0.5)*0.02
				rndy = (logic.getRandomFloat()-0.5)*0.02
				rvec = barrel.getAxisVect((rndx,5,rndy)).normalized()

				ammo = base.SC_SCN.addObject("AMMO_Bullet", barrel, 50)
				ammo.alignAxisToVect(ammo.getVectTo(camera)[1], 2, 1.0)
				ammo.alignAxisToVect(rvec, 1, 1.0)
				ammo["ROOTOBJ"] = plrobj
				ammo["DAMAGE"] = 40.0
				#ammo["LINV"] = plrobj.worldLinearVelocity*(1/60)
				ammo.localScale = (sx, 16+(rnd*4), sz)
				ammo.color = (1.0, 0.8, 0.5, 1)
				ammo.children[0].localScale = (1, 0.1+(rnd*0.9), 1)
				ammo.children[0].color = pri.getProp("COLOR", [1, 1, 0, 1])

				gfx = base.SC_SCN.addObject("GFX_MuzzleFlash", barrel, 0)
				gfx.setParent(barrel, False, False)
				gfx.localScale = (1.0, 1.0, 1.0)
				gfx.children[0].color = (1,1,0,1)

				mesh.worldPosition -= barrel.getAxisVect((0, 0.03, 0))
				mesh.localOrientation *= self.createMatrix(rot=(20, 0, 0), deg=True)

				self.data["MAG"] -= 1
				self.data["COOLDOWN"] = 15

		else:
			self.data["COOLDOWN"] -= 1

		self.sendEvent("WEAPON", plr, "TYPE", TYPE="Pistol")

		if sec == None:
			mesh.localPosition = self.createVector()
			mesh.localOrientation = self.createMatrix()
			if self.data["STRAFE"] != None:
				plr.data["STRAFE"] = self.data["STRAFE"]
				self.data["STRAFE"] = None
				plr.doAnim(LAYER=1, STOP=True)
			if mv == False:
				self.doPlayerAnim("LOOP")
			else:
				plr.doAnim(LAYER=1, STOP=True)
			return
		else:
			if self.data["STRAFE"] == None:
				self.data["STRAFE"] = plr.data["STRAFE"]
				plr.doAnim(LAYER=1, STOP=True)
			plr.data["STRAFE"] = True

		hrz = plrobj.getAxisVect((0,0,1))
		ang = self.toDeg(vec.angle(hrz))/180

		hand = plr.HAND.get(self.data["HAND"], "").split("_")
		if len(hand) > 1:
			anim = plr.ANIMSET+"RangedPistolAim"+hand[1]
			plr.doAnim(NAME=anim, FRAME=(-5,25), LAYER=1, BLEND=10)
			plr.doAnim(LAYER=1, SET=ang*20)

		up = viewport.VIEWCLASS.objects["Rotate"].getAxisVect((1,0,0))
		fw = plrobj.getAxisVect((0,1,0))

		if fw.dot(vec) > 0.5 and vec.length > 0.01:
			mesh.localPosition *= 0.8
			mesh.alignAxisToVect(vec.normalized(), 1, 0.3)
			mesh.alignAxisToVect(up, 0, 0.3)
		else:
			mesh.localPosition = self.createVector()
			mesh.localOrientation = self.createMatrix()


class GravGun(weapon.CorePlayerWeapon):

	NAME = "Not a Gun"
	SLOTS = ["Hip_R", "Hip_L"]
	TYPE = "RANGED"
	HAND = "MAIN"
	WAIT = 20
	SCALE = 0.7
	OFFSET = (0, -0.08, -0.04)

	def defaultData(self):
		self.env_dim = None
		self.target = None
		self.gravlock = False
		self.beam = 100
		self.wp_id = None

		dict = super().defaultData()
		dict["STRAFE"] = None

		return dict

	def PS_HandSocket(self):
		super().PS_HandSocket()

		if self.env_dim != None:
			self.objects["Mesh"].color = self.env_dim
			self.env_dim = None
		else:
			self.objects["Mesh"].color = (1,1,1,1)

		self.gimbal.visible = False
		if self.target != None:
			self.gimbal.visible = True

	def ST_Startup(self):
		self.data["HUD"]["Text"] = ""
		self.data["HUD"]["Stat"] = 100

		self.gimbal = self.owner.scene.addObject("Gimbal", self.owner, 0)
		#self.gimbal.setParent(self.objects["Mesh"], False, False)
		self.gimbal.visible = False

	def ST_Stop(self):
		self.gravlock = False
		self.target = None
		self.beam = 100
		super().ST_Stop()

	def ST_Active(self):
		owner = self.owner
		camera = base.SC_SCN.active_camera

		mesh = self.objects["Mesh"]
		barrel = self.objects["Barrel"]

		plr = self.owning_player
		plrobj = plr.objects["Root"]

		vec = viewport.getRayVec()

		self.data["HUD"]["Text"] = ""
		self.data["HUD"]["Stat"] = round((self.beam/30)*100)

		pri = self.getFirstEvent("WP_FIRE", "PRIMARY")
		pri_tap = self.getFirstEvent("WP_FIRE", "PRIMARY", "TAP")
		sec = self.getFirstEvent("WP_FIRE", "SECONDARY")
		sec_tap = self.getFirstEvent("WP_FIRE", "SECONDARY", "TAP")

		if self.data["COOLDOWN"] <= 0:
			if self.target != None:
				if pri_tap != None or self.target.invalid == True:
					self.gravlock = False
					self.target = None
					self.beam = 30
					self.data["COOLDOWN"] = 10
				else:
					self.data["HUD"]["Text"] = self.target.NAME
					self.gimbal.visible = True
					if keymap.BINDS["WP_UP"].tap() == True and self.beam < 30:
						self.beam += 1
					if keymap.BINDS["WP_DOWN"].tap() == True and self.beam > 5:
						self.beam -= 1

					pos = barrel.worldPosition+(vec.normalized()*self.beam)
					tgt = self.target.getOwner()

					force = pos-tgt.worldPosition
					tgt.applyForce(force*tgt.mass)

					## Gravity Negate ##
					grav = owner.scene.gravity
					cls = tgt.get("Class", None)
					if cls != None and cls.invalid != True:
						grav = cls.gravity
						self.sendEvent("MODIFIERS", cls, IMPULSE=grav.length)
						tgt.applyForce(-grav*tgt.mass, False)

					## Damping ##
					LV = tgt.localLinearVelocity
					if force.length < LV.length*4:
						mx = (1-(force.length/(LV.length*4)))
					else:
						mx = 0
					tgt.applyForce(-LV*mx*tgt.mass, True)

					self.gimbal.worldPosition = pos

			elif sec != None and plr.raycls != None:
				pos = plr.raycls.getOwner().worldPosition
				ref = plr.owner.worldPosition-pos
				if ref.length < 30:
					self.data["HUD"]["Text"] = plr.raycls.NAME
					self.data["HUD"]["Stat"] = round(ref.length)
					if pri_tap != None and plr.raycls.getOwner().getPhysicsId() != 0:
						self.target = plr.raycls
						self.gravlock = True
						self.beam = round(ref.length)
						self.gimbal.worldPosition = pos

		else:
			self.data["HUD"]["Stat"] = (self.data["COOLDOWN"]/10)*100
			self.data["COOLDOWN"] -= 1

		self.sendEvent("WEAPON", plr, "TYPE", TYPE="Pistol")

		if sec == None and self.gravlock == False:
			mesh.localPosition = self.createVector()
			mesh.localOrientation = self.createMatrix()
			if self.data["STRAFE"] != None:
				plr.data["STRAFE"] = self.data["STRAFE"]
				self.data["STRAFE"] = None
				plr.doAnim(LAYER=1, STOP=True)
			if plrobj.worldLinearVelocity.length*(1.60) < 0.01:
				self.doPlayerAnim("LOOP")
			else:
				plr.doAnim(LAYER=1, STOP=True)
			return
		else:
			if self.data["STRAFE"] == None:
				self.data["STRAFE"] = plr.data["STRAFE"]
				plr.doAnim(LAYER=1, STOP=True)
			plr.data["STRAFE"] = True

		hrz = plrobj.getAxisVect((0,0,1))
		ang = self.toDeg(vec.angle(hrz))/180

		hand = plr.HAND.get(self.data["HAND"], "").split("_")
		if len(hand) > 1:
			anim = plr.ANIMSET+"RangedPistolAim"+hand[1]
			plr.doAnim(NAME=anim, FRAME=(-5,25), LAYER=1, BLEND=10)
			plr.doAnim(LAYER=1, SET=ang*20)

		up = viewport.VIEWCLASS.objects["Rotate"].getAxisVect((1,0,0))
		fw = plrobj.getAxisVect((0,1,0))

		if fw.dot(vec) > 0.5 and vec.length > 0.01:
			mesh.localPosition *= 0.8
			mesh.alignAxisToVect(vec.normalized(), 1, 0.3)
			mesh.alignAxisToVect(up, 0, 0.3)
		else:
			mesh.localPosition = self.createVector()
			mesh.localOrientation = self.createMatrix()


class BasicSword(weapon.CorePlayerWeapon):

	NAME = "Pirate Sword"
	SLOTS = ["Hip_L", "Hip_R"]
	TYPE = "MELEE"
	OFFSET = (0, 0.025, -0.325)
	SCALE = 1.0
	BLADELENGTH = 1

	def defaultData(self):
		self.hitlist = []
		self.env_dim = None

		dict = super().defaultData()
		return dict

	def ST_Active(self):
		plr = self.owning_player

		if self.getFirstEvent("WP_FIRE") != None:
			obj = self.objects.get("Blade", self.owner)
			rfm = obj.worldPosition
			rto = rfm+obj.getAxisVect((0,0,1))

			rayOBJ, rayPNT, rayNRM = plr.getOwner().rayCast(rto, rfm, self.BLADELENGTH, "", 1, 0, 0)

			if rayOBJ != None and rayOBJ not in self.hitlist:
				rayOBJ.get("MODIFIERS", []).append({"HEALTH":-20})
				self.hitlist.append(rayOBJ)
		else:
			self.sendEvent("WP_CLEAR")

		if self.getFirstEvent("WP_CLEAR") != None:
			#for obj in self.hitlist:
			#	obj.get("MODIFIERS", []).append({"HEALTH":-20})
			self.hitlist = []

		if self.getFirstEvent("WP_ANIM") != None:
			self.doPlayerAnim("LOOP")

		self.sendEvent("WEAPON", plr, "TYPE", TYPE="Sword")


class SimpleStaff(weapon.CorePlayerWeapon):

	NAME = "Glorified Stick"
	SLOTS = ["Shoulder_R", "Shoulder_L"]
	TYPE = "MELEE"
	HAND = "MAIN"
	OFFSET = (0.0, -0.05, -0.1)
	SCALE = 2.0

	def defaultData(self):
		self.ori_qt = [self.createMatrix().to_quaternion(), self.createMatrix(mirror="YZ").to_quaternion()]
		self.env_dim = None

		dict = super().defaultData()

		return dict

	def PS_ManageBlade(self):
		mesh = self.objects["Mesh"]

		if self.active_state == self.ST_Enable:
			fac = (self.data["COOLDOWN"]/self.WAIT)
		elif self.active_state == self.ST_Stop:
			fac = 1-(self.data["COOLDOWN"]/self.WAIT)
		else:
			fac = 0

		fac = (fac*2)-1

		if fac > 0:
			quat = self.ori_qt[1].slerp(self.ori_qt[0], fac)
			mesh.localOrientation = quat.to_matrix()

		self.data["HUD"]["Text"] = "Staff"

		if self.env_dim != None:
			mesh.color = self.env_dim
			self.env_dim = None
		else:
			mesh.color = (1,1,1,1)

	def ST_Startup(self):
		self.active_post.append(self.PS_ManageBlade)

	def ST_Active(self):
		plr = self.owning_player
		self.sendEvent("WEAPON", plr, "TYPE", TYPE="Staff")

		if self.getFirstEvent("WP_ANIM") != None:
			self.doPlayerAnim("LOOP")


class SmallHealth(powerup.CoreStats):

	NAME = "Health"
	MODIFIER = {"HEALTH":20}
	SCALE = 0.5
	WAIT = 600
	COLOR = (0.7, 1.0, 0.7, 1)


class SmallEnergy(powerup.CoreStats):

	NAME = "Energy"
	MODIFIER = {"ENERGY":20}
	SCALE = 0.5
	WAIT = 600
	COLOR = (1.0, 0.7, 1.0, 1)


class SuperHealth(powerup.CoreStats):

	NAME = "Super Powerup"
	MODIFIER = {"HEALTH":200, "ENERGY":200, "LIMIT":200}
	LIMIT = 200
	WAIT = 36000
	SCALE = 2


class SimpleKey(powerup.CoreKey):

	SCALE = 0.4
	OFFSET = (0,0,0)
	GFXBOX = {"Mesh":"BOX_Drop", "Scale":(0.5, 1, 0.25)}
	GFXDROP = {"Mesh":"BOX_Drop", "Scale":(0.5, 1, 0.25)}
	LOCK = 1

