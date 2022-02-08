
## GAME OBJECTS ##


from bge import logic

from game3 import base, keymap, attachment, weapon, powerup, viewport


class ZephyrPlayerWeapon(weapon.CorePlayerWeapon):

	def defaultStates(self):
		super().defaultStates()
		self.env_dim = None
		self.active_post.append(self.PS_SetVisible)

	def PS_SetVisible(self):
		if self.env_dim != None:
			self.objects["Mesh"].color = self.env_dim
			self.env_dim = None
			return

		cls = self.getParent()
		amb = 0
		if cls != None:
			amb = cls.dict.get("DIM", amb)
		self.objects["Mesh"].color = (amb+1, amb+1, amb+1, 1.0)


class MachineGun(ZephyrPlayerWeapon):

	NAME = "Basic SMG"
	SLOTS = ["Shoulder_R", "Shoulder_L"]
	TYPE = "RANGED"
	HAND = "MAIN"
	WAIT = 40

	def defaultData(self):
		dict = super().defaultData()
		dict["MAG"] = 30
		dict["STRAFE"] = None
		dict["RELOAD"] = False
		return dict

	def ST_Idle(self):
		if self.data["STRAFE"] != None:
			self.owning_player.data["STRAFE"] = self.data["STRAFE"]
			self.data["STRAFE"] = None

	def ST_Active(self):
		owner = self.owner
		plrobj = self.owning_player.objects["Root"]
		vec = viewport.getRayVec()
		#if self.owning_player.rayhit != None:
		#	vec = (self.owning_player.rayhit[1]-owner.worldPosition).normalized()

		self.data["HUD"]["Text"] = "Ammo: "+str(self.data["MAG"])
		self.data["HUD"]["Stat"] = (self.data["MAG"]/30)*100

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
				rndx = (logic.getRandomFloat()-0.5)*0.1
				rndy = (logic.getRandomFloat()-0.5)*0.1
				rvec = self.objects["Barrel"].getAxisVect((rndx,5,rndy)).normalized()
				#vec += self.objects["Barrel"].getAxisVect((rndx,0,rndy)).normalized()*0.1

				ammo = base.SC_SCN.addObject("AMMO_Bullet", self.objects["Barrel"], 50)
				ammo.alignAxisToVect(ammo.getVectTo(base.SC_SCN.active_camera)[1], 2, 1.0)
				ammo.alignAxisToVect(rvec, 1, 1.0)
				ammo["ROOTOBJ"] = plrobj
				ammo["DAMAGE"] = 1
				#ammo["LINV"] = plrobj.worldLinearVelocity*(1/60)
				ammo.localScale = (sx, 16+(rnd*4), sz)
				ammo.color = (1,1,0,1)
				ammo.children[0].localScale = (1, 0.1+(rnd*0.9), 1)
				ammo.children[0].color = pri.getProp("COLOR", [1, 1, 0, 1])

				gfx = base.SC_SCN.addObject("GFX_MuzzleFlash", self.objects["Barrel"], 0)
				gfx.setParent(self.objects["Barrel"], False, False)
				gfx.localScale = (0.5, 1.0, 0.5)
				gfx.children[0].color = (1,1,0,1)

				self.data["MAG"] -= 1
				self.data["COOLDOWN"] = 5

		else:
			self.data["COOLDOWN"] -= 1

		self.sendEvent("WEAPON", self.owning_player, "TYPE", TYPE="Rifle")

		if self.data["STRAFE"] == None:
			self.data["STRAFE"] = self.owning_player.data["STRAFE"]
		self.owning_player.data["STRAFE"] = True

		hrz = plrobj.getAxisVect((0,0,1))

		ang = self.toDeg(vec.angle(hrz))/180
		hand = self.data["HAND"].split("_")[1]
		anim = self.owning_player.ANIMSET+"RangedRifleAim"+hand
		self.owning_player.doAnim(NAME=anim, FRAME=(-5,25), LAYER=1, BLEND=10)
		self.owning_player.doAnim(LAYER=1, SET=ang*20)

		up = viewport.VIEWCLASS.objects["Rotate"].getAxisVect((1,0,0))
		fw = plrobj.getAxisVect((0,1,0))

		if fw.dot(vec) > 0.5 and vec.length > 0.01:
			self.objects["Mesh"].alignAxisToVect(vec.normalized(), 1, 1.0)
			self.objects["Mesh"].alignAxisToVect(up, 0, 1.0)
		else:
			self.objects["Mesh"].localOrientation = self.createMatrix()


class HandGun(ZephyrPlayerWeapon):

	NAME = "Basic Pistol"
	SLOTS = ["Hip_R", "Hip_L"]
	TYPE = "RANGED"
	HAND = "MAIN"
	WAIT = 20

	def defaultData(self):
		dict = super().defaultData()
		dict["MAG"] = 8
		dict["STRAFE"] = None
		dict["RELOAD"] = False
		return dict

	def ST_Active(self):
		owner = self.owner
		plrobj = self.owning_player.objects["Root"]
		vec = viewport.getRayVec()
		#if self.owning_player.rayhit != None:
		#	vec = (self.owning_player.rayhit[1]-owner.worldPosition).normalized()

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
				rvec = self.objects["Barrel"].getAxisVect((rndx,5,rndy)).normalized()
				#vec += self.objects["Barrel"].getAxisVect((rndx,0,rndy)).normalized()*0.1

				ammo = base.SC_SCN.addObject("AMMO_Bullet", self.objects["Barrel"], 50)
				ammo.alignAxisToVect(ammo.getVectTo(base.SC_SCN.active_camera)[1], 2, 1.0)
				ammo.alignAxisToVect(rvec, 1, 1.0)
				ammo["ROOTOBJ"] = plrobj
				ammo["DAMAGE"] = 4
				#ammo["LINV"] = plrobj.worldLinearVelocity*(1/60)
				ammo.localScale = (sx, 16+(rnd*4), sz)
				ammo.color = (1,1,0,1)
				ammo.children[0].localScale = (1, 0.1+(rnd*0.9), 1)
				ammo.children[0].color = pri.getProp("COLOR", [1, 1, 0, 1])

				gfx = base.SC_SCN.addObject("GFX_MuzzleFlash", self.objects["Barrel"], 0)
				gfx.setParent(self.objects["Barrel"], False, False)
				gfx.localScale = (0.5, 0.5, 0.5)
				gfx.children[0].color = (1,1,0,1)

				self.data["MAG"] -= 1
				self.data["COOLDOWN"] = 15

		else:
			self.data["COOLDOWN"] -= 1

		self.sendEvent("WEAPON", self.owning_player, "TYPE", TYPE="Pistol")

		if sec == None:
			self.objects["Mesh"].localOrientation = self.createMatrix()
			if self.data["STRAFE"] != None:
				self.owning_player.data["STRAFE"] = self.data["STRAFE"]
				self.data["STRAFE"] = None
				self.owning_player.doAnim(LAYER=1, STOP=True)
			if mv == False:
				self.doPlayerAnim("LOOP")
			else:
				self.owning_player.doAnim(LAYER=1, STOP=True)
			return
		else:
			if self.data["STRAFE"] == None:
				self.data["STRAFE"] = self.owning_player.data["STRAFE"]
				self.owning_player.doAnim(LAYER=1, STOP=True)
			self.owning_player.data["STRAFE"] = True

		hrz = plrobj.getAxisVect((0,0,1))

		ang = self.toDeg(vec.angle(hrz))/180
		hand = self.data["HAND"].split("_")[1]
		anim = self.owning_player.ANIMSET+"RangedPistolAim"+hand
		self.owning_player.doAnim(NAME=anim, FRAME=(-5,25), LAYER=1, BLEND=10)
		self.owning_player.doAnim(LAYER=1, SET=ang*20)

		up = viewport.VIEWCLASS.objects["Rotate"].getAxisVect((1,0,0))
		fw = plrobj.getAxisVect((0,1,0))

		if fw.dot(vec) > 0.5 and vec.length > 0.01:
			self.objects["Mesh"].alignAxisToVect(vec.normalized(), 1, 1.0)
			self.objects["Mesh"].alignAxisToVect(up, 0, 1.0)
		else:
			self.objects["Mesh"].localOrientation = self.createMatrix()


class PhysicsObject(base.CoreObject):

	NAME = ""
	GHOST = False
	PHYSICS = "RIGID"


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
	GFXBOX = {"Mesh":"BOX_Sphere", "Scale":(0.5, 1, 0.25)}
	GFXDROP = {"Mesh":"BOX_Sphere", "Scale":(0.5, 1, 0.25)}
	LOCK = 1

