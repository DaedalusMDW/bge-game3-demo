
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
				rndx = (logic.getRandomFloat()-0.5)*0.05
				rndy = (logic.getRandomFloat()-0.5)*0.05
				rvec = barrel.getAxisVect((rndx,5,rndy)).normalized()

				ammo = base.SC_SCN.addObject("AMMO_Bullet", barrel, 50)
				ammo.alignAxisToVect(ammo.getVectTo(camera)[1], 2, 1.0)
				ammo.alignAxisToVect(rvec, 1, 1.0)
				ammo["ROOTOBJ"] = plrobj
				ammo["DAMAGE"] = 1.0
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
				ammo["DAMAGE"] = 4.0
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

