

from bge import logic

from game3 import keymap, base, player, HUD, viewport

from mathutils import Vector


class ActorPlayer(player.CorePlayer):

	NAME = "Stick Man"
	INVENTORY = {"Shoulder_R": "WP_MachineGun", "Hip_R":"WP_HandGun"}

	def defaultData(self):
		self.env_dim = None

		dict = super().defaultData()
		dict["COOLDOWN"] = 0
		return dict

	def applyContainerProps(self, cls):
		cls.gravity = self.gravity.copy()
		cls.air_drag = cls.gravity.length/9.8
		cls.env_dim = self.objects["Mesh"].color

	def PS_SetVisible(self):
		super().PS_SetVisible()

		if self.env_dim != None:
			self.objects["Mesh"].color = self.env_dim
			self.env_dim = None
			return

		cls = self.getParent()
		amb = 0
		if cls != None:
			amb = cls.dict.get("DIM", amb)
		self.objects["Mesh"].color = (amb+1, amb+1, amb+1, 1.0)

	def ST_Freeze(self):
		self.objects["Mesh"].color = (1,1,1,1)

	def weaponLoop(self):
		cls = self.active_weapon
		evt = self.getFirstEvent("WEAPON", "TYPE")
		if cls == None or evt == None:
			return

		self.sendEvent("WP_ANIM", cls)

		## RANGED ##
		if self.data["WPDATA"]["CURRENT"] == "RANGED":
			if keymap.BINDS["ATTACK_ONE"].tap() == True:
				self.sendEvent("WP_FIRE", cls, "PRIMARY", "TAP")
			elif keymap.BINDS["ATTACK_ONE"].active() == True:
				self.sendEvent("WP_FIRE", cls, "PRIMARY")

			if keymap.BINDS["ATTACK_TWO"].tap() == True:
				self.sendEvent("WP_FIRE", cls, "SECONDARY", "TAP")
			elif keymap.BINDS["ATTACK_TWO"].active() == True:
				self.sendEvent("WP_FIRE", cls, "SECONDARY")

			return

		## MELEE ##
		if self.data["WPDATA"]["CURRENT"] == "MELEE":
			anim = self.ANIMSET+"Melee"+evt.getProp("TYPE")+"Attack"

			if self.data["COOLDOWN"] == 0:
				self.sendEvent("WP_CLEAR", cls)

				if keymap.BINDS["ATTACK_ONE"].tap() == True:
					hand = cls.data["HAND"].split("_")[1]
					self.doAnim(NAME=anim+hand, FRAME=(0,45), LAYER=1)
					self.data["COOLDOWN"] = 50

			else:
				self.data["COOLDOWN"] -= 1

				self.sendEvent("WP_FIRE", cls)

			self.sendEvent("WP_BLADE", cls)


class TRPlayer(ActorPlayer):

	EDGECLIMB_TIME = 60
	WALL_ALIGN = True

	def defaultData(self):
		self.rayorder = "NONE"
		self.wallraydist = self.WALL_DIST
		self.wallrayto = self.createVector(vec=(0, self.WALL_DIST, 0))
		self.wallrayup = self.createVector(vec=(0, self.WALL_DIST, self.EDGE_H-self.GND_H+0.3))

		dict = super().defaultData()
		dict["WALLJUMPS"] = 0
		return dict

	def defaultStates(self):
		super().defaultStates()
		self.active_post.insert(0, self.PS_Edge)

	def findWall(self):
		wall, nrm = self.checkWall()

		if wall < 80 and nrm != None:
			return True
		return False

	def checkEdge(self, edge):
		rayto = edge+self.owner.getAxisVect([0,-1,0.1])
		rayfrom = edge+self.owner.getAxisVect([0,0,0.1])
		OBJ, PNT, NRM = self.owner.rayCast(rayto, rayfrom, self.WALL_DIST, "GROUND", 1, 1, 0)
		if OBJ == None:
			return True
		return False

	def wallJump(self, nrm):
		owner = self.objects["Root"]
		axis = owner.worldOrientation.inverted()*nrm

		align = axis.copy()
		align[2] = 0
		align.normalize()
		align = owner.worldOrientation*align

		jump = axis.copy()
		jump[2] += 1.5
		jump.normalize()
		jump = owner.worldOrientation*jump
		owner.worldLinearVelocity = jump*8

		self.alignPlayer(axis=align)

		if self.data["CAMERA"]["State"] != "THIRD":
			vref = viewport.getDirection([0,1,0])
			angle = vref.angle(align, 0)
			if angle >= 3.1:
				viewport.getObject("Root").applyRotation((0,0,0.1), True)

		self.data["ENERGY"] -= 5

		#self.doPlayerAnim("JUMP")
		self.doAnim(NAME=self.ANIMSET+"WallJump", FRAME=(0,2), PRIORITY=2, MODE="PLAY", BLEND=2)

	def PS_Edge(self):
		owner = self.objects["Root"]
		rayup = self.getWorldSpace(owner, self.wallrayup)
		rayto = self.getWorldSpace(owner, self.wallrayto)

		#if owner.get("XX", None) == None:
		#	owner["XX"] = owner.scene.addObject("Gimbal", owner, 0)
		#	owner["XX"].setParent(owner)

		#guide = owner["XX"]

		self.objects["Character"]["DEBUG1"] = self.rayorder

		if self.groundhit != None or self.gravity.length <= 0.1:
			#self.rayorder = "NONE"
			return

		EDGEOBJ, EDGEPNT, EDGENRM = owner.rayCast(rayto, rayup, self.EDGE_H+0.6, "GROUND", 1, 1, 0)

		if EDGEOBJ != None:
		#	guide.worldPosition = EDGEPNT
			angle = owner.getAxisVect((0,0,1)).angle(EDGENRM, 0)
			angle = round(self.toDeg(angle), 2)
			ledge = self.getLocalSpace(owner, EDGEPNT)
			dist = ledge[2]
			offset = self.EDGE_H-self.GND_H

			if self.rayorder == "END":
				if abs(dist-offset) > 0.11:
					self.rayorder = "NONE"
				else:
					return

			## Vault ##
			if dist >= -0.25 and dist < 0.75 and keymap.BINDS["PLR_JUMP"].tap() == True:
				if angle < self.SLOPE and self.motion["Move"][1] > 0.1 and self.checkEdge(EDGEPNT) == True:
					self.resetAcceleration()
					self.jump_timer = int(self.EDGECLIMB_TIME*0.33)
					self.ST_EdgeClimb_Set()

			## Ledge Grab ##
			if owner.localLinearVelocity[2] < 0 and self.jump_state != "NONE":
				CHK = None
				if angle < self.SLOPE and abs(dist-offset) < 0.1:
					CHK = self.checkEdge(EDGEPNT)
				if CHK == True:
					WP = self.getLocalSpace(owner, EDGEPNT)
					WP[2] = offset
					WP = EDGEPNT-(owner.worldOrientation*WP)
					owner.worldPosition = list(WP)
					self.ST_Hanging_Set()

		else:
		#	guide.worldPosition = rayup-owner.getAxisVect((0,0,self.EDGE_H+0.6))
			if self.rayorder == "END":
				self.rayorder = "NONE"

	## WALL JUMP STATE ##
	def ST_Advanced_Set(self, wall=None):
		owner = self.objects["Root"]

		if wall == None:
			wall = self.findWall()

		if wall == True and owner.localLinearVelocity[2] > -4 and self.data["ENERGY"] > 15:
			owner.setDamping(0, 0)
			self.data["HUD"]["Target"] = None
			self.data["WALLJUMPS"] = 0
			self.active_state = self.ST_Wall

	def ST_Wall(self):
		self.getInputs()

		owner = self.objects["Root"]

		ground, angle = self.checkGround()

		wall, nrm = self.checkWall()

		self.jump_state = "FALLING"

		if self.data["CAMERA"]["State"] != "THIRD":
			self.alignCamera(0.2)

		if nrm != None and wall < 80:
			self.doAnim(NAME=self.ANIMSET+"WallJump", FRAME=(0,0), PRIORITY=3, MODE="LOOP", BLEND=10)
			if self.WALL_ALIGN == True:
				self.doMoveAlign(axis=nrm*-1, up=False)
			if self.data["WALLJUMPS"] == 0 or keymap.BINDS["TOGGLEMODE"].tap() == True:
				if self.data["ENERGY"] > 15:
					self.wallJump(nrm)
					self.data["WALLJUMPS"] += 1
		else:
			self.doPlayerAnim("FALLING")

			if self.motion["Move"].length > 0.01:
				move = self.motion["Move"].normalized()
				vref = viewport.getDirection((move[0], move[1], 0))
				owner.applyForce(vref*5, False)

		self.alignToGravity(owner)

		if owner.localLinearVelocity[2] < 0.01 and ground != None:
			self.ST_Walking_Set()

		elif owner.localLinearVelocity[2] < -2:
			self.ST_Walking_Set()

		self.objects["Character"]["DEBUG2"] = str(self.jump_state)

	def ST_Walking_Set(self):
		self.doAnim(STOP=True)
		self.resetAcceleration()
		self.data["WALLJUMPS"] = 0
		self.active_state = self.ST_Walking

	## EDGE HANG STATE ##
	def ST_Hanging_Set(self):
		self.resetAcceleration()

		self.objects["Root"].worldLinearVelocity = (0,0,0)

		self.rayorder = "HANG_INIT"
		self.jump_state = "HANGING"
		self.jump_timer = 0
		self.data["HUD"]["Target"] = None

		self.active_state = self.ST_Hanging

	def ST_Hanging(self):
		self.getInputs()

		owner = self.objects["Root"]

		self.jump_state = "HANGING"

		owner.worldLinearVelocity = (0,0,0)

		if self.checkGround(simple=True) == None:
			self.jump_state = "NONE"
			rayup = self.getWorldSpace(owner, self.wallrayup)
			rayto = self.getWorldSpace(owner, self.wallrayto)
			offset = self.EDGE_H-self.GND_H

			edge = self.checkGround(simple=True, ray=(rayto, rayup, 0.3))

			if edge != None:
				EDPNT = self.getLocalSpace(owner, edge[1])
				diff = EDPNT[2]-offset
				if abs(diff) > 0.1 or self.checkEdge(edge[1]) == False:
					edge = None
				else:
					self.groundhit = edge
					self.getGroundPoint(edge[0])


			rayfrom = owner.worldPosition+owner.getAxisVect((0,0,offset-0.05))
			rayto = rayfrom+owner.getAxisVect((0,1,0))

			TROBJ, TRPNT, TRNRM = owner.rayCast(rayto, rayfrom, self.WALL_DIST+0.3, "GROUND", 1, 1, 0)

			X = 0
			if self.rayorder == "HANG_INIT":
				self.rayorder = "HANGING"
				self.alignToGravity()
			elif TROBJ != None and edge != None:
				wall = owner.worldOrientation.inverted()*TRNRM
				wall[2] = 0
				wall = wall.normalized()

				point = wall*(self.WALL_DIST-0.05)
				point = owner.worldOrientation*point
				owner.worldPosition = (TRPNT+point)-owner.getAxisVect((0,0,offset-0.05-diff))

				move = self.motion["Move"]
				mref = viewport.getDirection((move[0], move[1], 0))
				mref = owner.worldOrientation.inverted()*mref
				if abs(mref[0]) > 0.5:
					X = 1-(2*(mref[0]<0))
				owner.localLinearVelocity[0] = (X*0.01)*60

				align = owner.worldOrientation*wall
				self.alignPlayer(0.5, axis=-align)
			else:
				self.alignToGravity()

			if self.ANIMOBJ == None:
				pass
			elif abs(X) > 0.01:
				self.doAnim(NAME=self.ANIMSET+"EdgeTR", FRAME=(1,60), MODE="LOOP", BLEND=10)
			else:
				self.doAnim(NAME=self.ANIMSET+"EdgeIdle", FRAME=(0,0), MODE="LOOP", BLEND=5)

		else:
			edge = None

		if keymap.BINDS["PLR_DUCK"].tap() == True or edge == None:
			self.ST_EdgeFall_Set()

		elif keymap.BINDS["PLR_JUMP"].tap() == True:
			self.ST_EdgeClimb_Set()

		elif keymap.BINDS["TOGGLEMODE"].tap() == True:
			wall = self.findWall()
			if wall == True:
				self.ST_EdgeFall_Set()
				self.ST_Advanced_Set(wall)

		self.objects["Character"]["DEBUG2"] = str(self.jump_state)

	def ST_EdgeClimb_Set(self):
		owner = self.objects["Root"]
		char = self.objects["Character"]
		rayup = self.getWorldSpace(owner, self.wallrayup)
		rayto = self.getWorldSpace(owner, self.wallrayto)
		SH = None

		edge = self.checkGround(simple=True, ray=(rayto, rayup, 2.0))

		if edge != None:
			EDPNT = self.getLocalSpace(owner, edge[1])
			self.groundhit = edge
			self.getGroundPoint(edge[0])

			rayto = edge[1]+owner.getAxisVect((0, 0.3, 2))
			rayfrom = owner.worldPosition+owner.getAxisVect((0, 0, self.EYE_H-self.GND_H))

			SH, SP, SN = owner.rayCast(rayto, rayfrom, 0, "GROUND", 1, 1, 0)

		if SH != None:
			self.doAnim(STOP=True)
			self.doJump(5)
			self.rayorder = "END"
			self.active_state = self.ST_Walking

		elif edge != None:
			self.doAnim(STOP=True)
			self.doAnim(NAME=self.ANIMSET+"EdgeClimb", FRAME=(self.jump_timer, self.EDGECLIMB_TIME+10), MODE="PLAY")
			target = self.groundhit[1]+owner.getAxisVect((0, 0, self.GND_H))
			loctar = self.getLocalSpace(owner, target)
			owner.worldPosition = target
			viewport.setCameraPosition(-loctar)
			self.rayorder = loctar.copy()
			self.jump_state = "NONE"
			self.jump_timer = 0
			self.active_state = self.ST_EdgeClimb

	def ST_EdgeClimb(self):
		owner = self.objects["Root"]
		char = self.objects["Character"]

		self.jump_state = "NONE"
		self.jump_timer += 1

		owner.worldLinearVelocity = (0,0,0)

		time = self.EDGECLIMB_TIME

		fac = self.jump_timer/time

		ground = self.checkGround(simple=True)

		lerp = -self.rayorder*(1-fac)

		if ground != None:
			self.groundhit = ground
			self.getGroundPoint(ground[0])

		self.alignToGravity()

		if self.jump_timer >= time or ground == None:
			self.doAnim(STOP=True)
			self.doPlayerAnim("RESET")
			self.rayorder = "END"
			self.jump_state = "NONE"
			self.jump_timer = 0
			lerp = [0,0,0]
			self.active_state = self.ST_Walking

		viewport.setCameraPosition(lerp)

	def ST_EdgeFall_Set(self):
		self.rayorder = "END"
		self.jump_state = "FALLING"
		self.jump_timer = 0
		self.doAnim(STOP=True)
		self.active_state = self.ST_Walking

