

from bge import logic

from game3 import keymap, base, player, HUD, viewport

from mathutils import Vector


class ActorPlayer(player.CorePlayer):

	NAME = "Stick Man"
	INVENTORY = {}

	SLOPE = 50

	def defaultData(self):
		self.env_dim = None
		self.npc_leader = None
		self.npc_follow = []
		self.npc_state = 0
		self.npc_portal = None
		self.npc_spot = None
		self.npc_spot_obj = self.owner.scene.addObject("GFX_Spot", self.owner, 0)
		self.npc_spot_obj.setParent(self.owner)
		self.npc_spot_obj.localPosition = (0,0,-0.97)
		self.npc_spot_obj.visible = False
		self.ragdollparts = None
		self.ragdollstate = "INIT"
		self.ragdollwait = 10

		dict = super().defaultData()
		dict["COOLDOWN"] = 0
		dict["NPC_LEAD"] = False
		dict["RAGDOLL"] = False

		return dict

	def defaultStates(self):
		super().defaultStates()
		self.active_pre.append(self.PR_EventsNPC)
		self.active_post.append(self.PS_Ambient)

	def doLoad(self):
		super().doLoad()

		cls = self.getParent()

		print("- LOAD -", self.NAME, self.data["NPC_LEAD"], cls)

		if self.data["NPC_LEAD"] == True and cls != None:
			self.removeContainerParent()
			self.sendEvent("NPC", cls, "FOLLOW", "SEND")
			self.npc_leader = cls

	def doUpdate(self):
		print("- UPDATE -", self.NAME, self.data["NPC_LEAD"], self.getParent())

		for cls in self.npc_follow:
			if cls not in self.getChildren() and self.player_id != None:
				print("- LINK -", self.NAME, cls.NAME, cls.getParent())
				cls.setContainerParent(self)
				cls.dict["Portal"] = self.dict["Object"]
				cls.npc_portal = "FOLLOW"

		self.npc_follow = []

		super().doUpdate()

		if self.npc_portal == "FOLLOW":
			if self.active_state == self.ST_IdleRD:
				self.data["POS"] = [0, -1.5, 0.5]
			else:
				self.data["POS"] = [0, -0.5, 0]

	def teleportTo(self, pos=None, ori=None, vel=False, cam=True):
		super().teleportTo(pos, ori, vel, cam)

		owner = self.getOwner()

		for cls in self.npc_follow:
			obj = cls.getOwner()
			obj.worldPosition = owner.worldPosition+owner.getAxisVect((0,-0.5,0))

	def switchPlayerActive(self, ID=None):
		self.npc_follow = []
		self.npc_leader = None
		self.npc_state = -2
		self.data["NPC_LEAD"] = False
		super().switchPlayerActive(ID)

	def switchPlayerPassive(self):
		self.npc_follow = []
		self.npc_leader = None
		self.npc_state = -2
		self.data["NPC_LEAD"] = False
		return super().switchPlayerPassive()

	def switchPlayerNPC(self):
		self.npc_state = -2
		if self.active_state not in {self.ST_Ragdoll, self.ST_IdleRD}:
			self.ragdollwait = 0
			super().switchPlayerNPC()
		elif self.active_state == self.ST_Ragdoll:
			self.endObject()

	def applyModifier(self, dict):
		if "IMPULSE" in dict:
			self.jump_state = "JUMP"
			if self.data["NPC_LEAD"] == True:
				self.npc_state = -1

		super().applyModifier(dict)

	def destroy(self):
		if self.ragdollparts != None:
			for name in self.ragdollparts:
				obj = self.ragdollparts[name]
				obj["DESTROY"] = True

		self.ragdollparts = None
		self.ragdollstate = "INIT"

		if self.objects["Root"] == None and self.owner.parent != None:
			self.owner.removeParent()

		super().destroy()

	def manageStatAttr(self):
		if self.active_state in {self.ST_Ragdoll, self.ST_IdleRD}:
			return

		if self.data["HEALTH"] <= 0:
			self.data["HEALTH"] = -1

			for cls in list(self.attachments):
				vec = self.createVector()
				for i in [0,1,2]:
					vec[i] += ((logic.getRandomFloat()*2)-1)*0.3
				pos = list(self.owner.worldPosition+vec)
				cls.dropItem(pos)

			if self.data["NPC_LEAD"] == True:
				self.npc_follow = []
				self.npc_leader = None
				self.npc_state = -2
				self.data["NPC_LEAD"] = False

			if ("Ragdoll"+self.owner.name) in base.SC_SCN.objectsInactive:
				if self.objects["Root"] != None:
					self.motion["World"] = self.objects["Root"].worldLinearVelocity.copy()
				else:
					self.motion["World"] = self.createVector()

				print("RD WV", self.motion["World"])
				self.doAnim(STOP=True)
				self.active_state = self.ST_Ragdoll

			elif self.player_id == None:
				self.endObject(False)

		super().manageStatAttr()

	def applyContainerProps(self, cls):
		super().applyContainerProps(cls)
		cls.env_dim = list(self.objects["Mesh"].color)

	def PR_EventsNPC(self):
		self.npc_follow = []

		all = self.getAllEvents("NPC", "FOLLOW", "SEND")
		for evt in all:
			cls = evt.sender
			self.sendEvent("NPC", cls, "FOLLOW", "LOOP")
			if cls not in self.npc_follow:
				self.npc_follow.append(cls)
				#print("- FOLLOW -", cls.NAME, evt.getProp("INTERACT"))

	def PS_Ambient(self):
		if self.env_dim == None:
			cls = self.getParent()
			amb = 0
			if cls != None:
				amb = cls.dict.get("DIM", amb)
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		self.objects["Mesh"].color = self.env_dim

		self.env_dim = None

		obj = self.npc_spot_obj
		if self.npc_spot != None:
			obj.visible = True
			obj.color = list(self.npc_spot)
			self.npc_spot = None
		else:
			obj.visible = False

	def ST_IdleRD(self):
		self.ST_Ragdoll()
		char = self.owner

		all = self.getAllEvents("INTERACT", "SEND")
		for evt in all:
			self.sendEvent("INTERACT", evt.sender, "RECEIVE")

		flw = self.getFirstEvent("NPC", "FOLLOW", "LOOP")
		if flw != None:
			self.sendEvent("NPC", flw.sender, "FOLLOW", "SEND")

		act = self.getFirstEvent("INTERACT", "ACTOR")
		evt = self.getFirstEvent("INTERACT", "ACTOR", "TAP")

		if self.ragdollparts == None:
			return

		if evt != None and self.npc_state == -2:
			self.npc_state = 0

		if act != None and self.npc_state >= 0:
			self.npc_state += 1

		if flw != None:
			if self.npc_state < -2:
				self.npc_state = -2
		elif self.npc_state < -10:
			self.npc_leader = None
			self.npc_state = -2
		elif self.npc_state >= 0:
			self.npc_state = -3
		else:
			self.npc_state -= 1

		if self.npc_leader == None or self.npc_leader.invalid == True:
			self.npc_state = -1

		if self.npc_state > 30 or self.npc_state == -1:
			if self.npc_state == -1:
				print("RD BREAK")
				self.data["NPC_LEAD"] = False
			self.npc_state = -2
			for name in self.ragdollparts:
				obj = self.ragdollparts[name]
				obj["DESTROY"] = True
			self.ragdollparts = None
			self.ragdollstate = "INIT"
			self.active_state = self.ST_Idle
			self.switchPlayerNPC()
			return

		elif act == None:
			if self.npc_state >= 0:
				self.npc_state = 0

		if self.npc_leader != None:
			plr = self.npc_leader.owner
			pos = char.worldPosition-plr.worldPosition
			pos = plr.worldOrientation.inverted()*pos
		else:
			plr = None
			pos = self.createVector()

		for name in self.ragdollparts:
			obj = self.ragdollparts[name]
			if plr != None:
				vec = obj.worldPosition-plr.worldPosition
				vec = plr.worldOrientation.inverted()*vec
				z = (0.5-vec[2])*obj.mass*2
				zref = self.createVector(vec=(0,0,z))
				vec[2] = 0
				if name == "root":
					mx = (vec.length-2.0)*obj.mass*4
					if mx < 0:
						mx = 0
					zref = zref+(vec.normalized()*-mx)
				if name == "head":
					mx = (vec.length-1.0)*obj.mass*4
					if mx < 0:
						mx = 0
					zref = zref+(vec.normalized()*-mx)
				zref = plr.worldOrientation*zref
				obj.applyForce(zref, False)
				if name == "root":
					up = self.gravity.normalized()
					tx = up.dot(obj.getAxisVect((0,0,-1)))
					gz = up.dot(obj.getAxisVect((0,-1,0)))
					if gz < 0:
						tx = 1-(2*(tx<0))

					obj.applyTorque((tx*obj.mass*1, 0, 0), True)

			obj.applyForce(-obj.worldLinearVelocity*obj.mass, False)
			obj.applyForce(-self.gravity*obj.mass, False)

	def ST_Idle(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]
		char = self.owner

		self.gposoffset = owner.getAxisVect((0,0,1))*self.GND_H
		ground, angle = self.checkGround()

		owner.setDamping(0, 0)

		plr = None
		vec = self.createVector()
		vref = self.createVector()

		all = self.getAllEvents("INTERACT", "SEND")
		for evt in all:
			self.sendEvent("INTERACT", evt.sender, "RECEIVE", TYPE="RAY")

		flw = self.getFirstEvent("NPC", "FOLLOW", "LOOP")

		if self.data["NPC_LEAD"] == True:
			act = self.getFirstEvent("INTERACT", "ACTOR")
			evt = self.getFirstEvent("INTERACT", "ACTOR", "TAP")

			if evt != None and self.npc_state == -2:
				self.npc_state = 0

			if act == None and self.npc_state >= 1:
				self.npc_state = -1

			if self.npc_state >= 0:
				if act != None:
					self.npc_state += 1
				else:
					self.npc_state = 0

			if flw != None:
				if self.npc_state < -2:
					self.npc_state = -2
				self.npc_leader = flw.sender

				plr = flw.sender.owner
				vec = plr.worldPosition-char.worldPosition
				vref = vec.normalized()

				if vec.length > 10:
					self.npc_state = -1
				else:
					self.npc_spot = (0,1,0,1)
					self.sendEvent("NPC", flw.sender, "FOLLOW", "SEND")

				if self.npc_state > 30 and ("Ragdoll"+self.owner.name) in base.SC_SCN.objectsInactive:
					self.npc_state = -2
					self.active_state = self.ST_IdleRD

			elif self.npc_state < -10:
				self.npc_leader = None
				self.npc_state = -2
				self.data["NPC_LEAD"] = False
				print("BREAK FOLLOW", self.NAME)

			elif self.npc_state >= 0:
				self.npc_state = -3
			else:
				self.npc_state -= 1

			if self.npc_state == -1:
				plr = None
				vec = self.createVector()
				vref = self.createVector()

				self.npc_leader = None
				self.npc_state = -2
				self.data["NPC_LEAD"] = False
				print("STOP FOLLOW", self.NAME)

		else:
			act = self.getFirstEvent("INTERACT", "ACTOR")
			evt = self.getFirstEvent("INTERACT", "ACTOR", "TAP")

			if evt != None and self.npc_state == -2:
				self.npc_state = 0

			if act != None:
				self.sendEvent("NPC", act.sender, "FOLLOW", "SEND", INTERACT=True)

			if act == None and self.npc_state >= 1:
				self.npc_state = -1

			if self.npc_state >= 0:
				if act != None:
					self.npc_state += 1
				else:
					self.npc_state = 0

			for obj in self.collisionList:
				cls = obj.get("Class", None)
				if "COLLIDE" in obj and cls != None:
					self.npc_spot = (1,0,0,1)
					self.sendEvent("INTERACT", cls, "SEND", OBJECT=obj, TYPE="COLLIDE")

			veh = self.getAllEvents("INTERACT", "RECEIVE")
			if self.npc_state > 30:
				for vd in veh:
					if vd != None:
						self.npc_leader = None
						self.npc_state = -2
						l = vd.getProp("LOCK", "")
						o = vd.getProp("OBJECT", None)
						self.npc_spot = None
						self.sendEvent("INTERACT", vd.sender, "TAP", "ACTOR", OBJECT=o, LOCK=l)
				return

			if flw != None and self.npc_state == -1:
				self.sendEvent("NPC", flw.sender, "FOLLOW", "SEND")
				self.npc_leader = flw.sender
				self.npc_state = -2
				self.data["NPC_LEAD"] = True
				print("START FOLLOW", self.NAME)

			if act == None:
				all = self.getAllEvents("SWITCHER", "SEND")
				for evt in all:
					self.npc_spot = None
					self.sendEvent("SWITCHER", evt.sender, "RECEIVE")

		char["DEBUG2"] = self.npc_state

		if ground != None:
			if self.jump_state != "NONE":
				self.jump_timer = 0
				self.jump_state = "NONE"
				vel = self.motion["World"]*(1/60)
				self.resetAcceleration(vel)
				self.doPlayerAnim("LAND")

			owner.worldLinearVelocity = (0,0,0)

			mx = 0
			if plr != None and abs(vec.length-1.5) > 0.5:
				mx = (vec.length-1.5)/20
			if mx < -0.035:
				mx = -0.035
			if mx > self.data["SPEED"]:
				mx = self.data["SPEED"]

			self.doMovement(vref, mx)
			self.doMoveAlign(axis=vref, up=False)

			linLV = self.motion["Local"].copy()
			linLV[2] = 0
			action = "IDLE"

			if linLV.length > 0.01:
				action = "FORWARD"

				if linLV[1] < 0:
					action = "BACKWARD"
				if linLV[0] > 0.5 and abs(linLV[1]) < 0.5:
					action = "STRAFE_R"
				if linLV[0] < -0.5 and abs(linLV[1]) < 0.5:
					action = "STRAFE_L"

				if linLV.length <= (0.05*60):
					action = "WALK_"+action

			self.doPlayerAnim(action, blend=10)

		elif self.gravity.length <= 0.1:
			self.doPlayerAnim("FALLING")
			self.jump_state = "FLOATED"

			mx = 0
			if plr != None:
				mx = (vec.length-2)
				self.doMoveAlign(axis=vref, up=plr.getAxisVect((0,0,1)))

			owner.applyForce(owner.worldLinearVelocity*-2, False)
			owner.applyForce(vref*5*mx, False)

		elif self.jump_state == "NONE":
			self.doJump(height=1, move=0.5)

		else:
			self.jump_state = "FALLING"
			self.jump_timer += 1

			mx = 0
			if vec.length > 0.1:
				mx = (vec.length-2)

			axis = owner.worldLinearVelocity*(1/60)*0.1
			self.doMoveAlign(axis, up=False, margin=0.001)
			self.doPlayerAnim("FALLING")

			owner.applyForce(vref*5*mx, False)

		self.alignToGravity()

	def ST_Freeze(self):
		self.npc_follow = []
		if self.active_state == self.ST_IdleRD:
			self.ST_IdleRD()
		elif self.active_state == self.ST_Ragdoll:
			self.ST_Ragdoll()
		else:
			self.npc_leader = None
			self.npc_state = -2
			self.data["NPC_LEAD"] = False

		super().ST_Freeze()
		self.PS_Ambient()

	def ST_Ragdoll(self):
		scene = self.owner.scene
		char = self.owner
		rig = self.objects["Rig"]

		if base.ORIGIN_SHIFT != None:
			return
		if self.ragdollwait > 0:
			self.ragdollwait -= 1
			return

		if self.ragdollparts == None:
			self.resetGroundRay()
			self.resetAcceleration()
			self.removePhysicsBox()

			self.ragdollparts = {}
			newobj = scene.addObject("Ragdoll"+char.name, char, 0)
			#gimbal = scene.addObject("Gimbal", char, 0)

			rdroot = newobj.children[newobj.name+".root"]
			rdroot["Class"] = self

			rdroot.removeParent()
			rdroot.worldLinearVelocity = (0,0,0)
			rdroot.worldAngularVelocity = (0,0,0)
			rdroot.disableRigidBody()
			rdroot.suspendDynamics()

			rdroot.worldPosition = self.objects["RagdollHelper"].worldPosition.copy()
			rdroot.worldOrientation = self.objects["RagdollHelper"].worldOrientation.copy()

			for obj in list(rdroot.childrenRecursive):
				bn = obj.get("BONE", None)
				if bn != None:
					obj["Class"] = self
					obj["TARGET"] = obj.parent
					obj.removeParent()
					obj.worldLinearVelocity = (0,0,0)
					obj.worldAngularVelocity = (0,0,0)
					obj.disableRigidBody()
					obj.suspendDynamics()
					self.ragdollparts[bn] = obj

			char.setParent(rdroot, False, False)

			for bone in rig.channels:
				if bone.name in self.ragdollparts:
					obj = self.ragdollparts[bone.name]
					jnt = obj.children[obj.name+".Joint"]

					bp = self.getWorldSpace(rig, bone.pose_head)
					br = self.getWorldRotation(rig, bone.pose_matrix.to_3x3())

					br = obj.worldOrientation.inverted()*br
					br = br*jnt.localOrientation.inverted()

					obj["POSE_ORI"] = obj.worldOrientation*br
					obj["POSE_POS"] = bp + (obj.worldOrientation*-jnt.localPosition)

					obj["POSE_CON"] = rig.constraints[bone.name+":"+bone.name]
					obj["POSE_CON"].target = jnt
					#obj["POSE_CON"].active = True

					#gimbal = scene.addObject("Gimbal", char, 0)
					#gimbal.worldPosition = obj["POSE_POS"]
					#gimbal.worldOrientation = obj["POSE_ORI"]

			self.ragdollparts["root"] = rdroot
			self.ragdollstate = "ACTIVE"
			newobj.endObject()

		else:
			for name in self.ragdollparts:
				obj = self.ragdollparts[name]

				#LV = obj.localLinearVelocity.copy()
				#LV -= (obj.worldOrientation.inverted()*self.air_linv)
				#dragX = LV[0]*0.5*obj.mass*self.air_drag
				#dragY = LV[1]*0.5*obj.mass*self.air_drag
				#dragZ = LV[2]*0.5*obj.mass*self.air_drag
				#obj.applyForce((-dragX, -dragY, -dragZ), True)

				obj.applyForce(-self.owner.scene.gravity*obj.mass, False)
				obj.applyForce(self.gravity*obj.mass, False)

		#if base.ORIGIN_SHIFT != None:
		#	self.endObject()
		#	return
		#	self.ragdollstate = "ORIGIN"
		#	for name in self.ragdollparts:
		#		obj = self.ragdollparts[name]
		#		obj.disableRigidBody()
		#		obj.suspendDynamics()
		#elif self.ragdollstate == "ORIGIN":
		#	self.ragdollstate = "ACTIVE"
		#	for name in self.ragdollparts:
		#		obj = self.ragdollparts[name]
		#		obj.restoreDynamics()
		#		obj.enableRigidBody()

		self.doAnim(MODE="LOOP", BLEND=0)
		#rig.update()

	def weaponLoop(self):
		cls = self.active_weapon
		evt = self.getFirstEvent("WEAPON", "TYPE")
		if cls == None or evt == None:
			return

		self.sendEvent("WP_ANIM", cls)

		## RANGED ##
		if self.data["WPDATA"]["CURRENT"] == "RANGED":
			#vec = viewport.getRayVec()
			#hrz = self.owner.getAxisVect([0,0,1])
			#ang = self.toDeg(vec.angle(hrz))/180
			#hand = self.HAND.get(cls.data["HAND"], "").split("_")
			#if len(hand) > 1:
			#	anim = "Ranged"+evt.getProp("TYPE")+"Aim"+hand[1]
			#	self.doAnim(NAME=anim, FRAME=(-5,25), LAYER=1, BLEND=10)
			#	self.doAnim(LAYER=1, SET=ang*20)

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
					h = cls.data["HAND"]
					hand = self.HAND.get(h, "").split("_")
					if len(hand) > 1:
						self.doAnim(NAME=anim+hand[1], FRAME=(0,45), LAYER=1+(h=="OFF"))
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
		self.wallfootto = self.createVector(vec=(0, self.WALL_DIST, -self.GND_H))
		self.wallfootup = self.createVector(vec=(0, self.WALL_DIST, 0))
		self.wallnrm = None

		dict = super().defaultData()
		dict["WALLJUMPS"] = 0
		dict["CLIMBRATE"] = 1

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
		y = self.WALL_DIST
		rayto = edge+self.owner.getAxisVect([0,0,0.1])
		rayfrom = edge+self.owner.getAxisVect([0,-y,-0.1])
		OBJ, PNT, NRM = self.owner.rayCast(rayto, rayfrom, 0, "GROUND", 1, 1, 0)
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
		jump[2] += 1.25
		jump.normalize()
		jump = owner.worldOrientation*jump
		owner.worldLinearVelocity = jump*self.JUMP*1.1

		self.alignPlayer(axis=align)

		if self.data["CAMERA"]["State"] != "THIRD":
			vref = viewport.getDirection([0,1,0])
			angle = vref.angle(align, 0)
			if angle >= 3.1:
				viewport.getObject("Root").applyRotation((0,0,0.1), True)

		self.data["ENERGY"] -= 10

		#self.doPlayerAnim("JUMP")
		self.doAnim(NAME=self.ANIMSET+"WallJump", FRAME=(0,2), PRIORITY=2, MODE="PLAY", BLEND=2)

	def PS_Edge(self):
		owner = self.objects["Root"]
		if owner == None or self.player_id == None:
			return

		#if owner.get("XX", None) == None:
		#	owner["XX"] = owner.scene.addObject("Gimbal", owner, 0)
		#	#owner["XX"].setParent(owner)

		#guide = owner["XX"]

		#self.objects["Character"]["DEBUG1"] = self.rayorder

		if self.groundhit != None or self.gravity.length <= 0.1 or self.active_weapon != None:
			#self.rayorder = "NONE"
			return

		move = self.motion["Move"].normalized()
		vref = viewport.getDirection((move[0], move[1], 0))
		mref = owner.worldOrientation.inverted()*vref
		fdot = owner.getAxisVect((0,1,0)).dot(vref)

		rayup = self.getWorldSpace(owner, self.wallrayup)
		rayto = self.getWorldSpace(owner, self.wallrayto)

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
			if dist >= -0.4 and dist < 0.75 and keymap.BINDS["PLR_JUMP"].tap() == True:
				if angle < self.SLOPE and fdot > 0.5 and self.checkEdge(EDGEPNT) == True:
					self.resetAcceleration()
					start = round(self.EDGECLIMB_TIME*0.333)
					self.ST_EdgeClimb_Set(start)
					return

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
					return

		else:
		#	guide.worldPosition = rayup-owner.getAxisVect((0,0,self.EDGE_H+0.6))
			if self.rayorder == "END":
				self.rayorder = "NONE"

		## Scramble ##
		rayup = self.getWorldSpace(owner, self.wallfootup)
		rayto = self.getWorldSpace(owner, self.wallfootto)

		EDGEOBJ, EDGEPNT, EDGENRM = owner.rayCast(rayto, rayup, 0, "GROUND", 1, 1, 0)

		if EDGEOBJ != None:
		#	guide.worldPosition = EDGEPNT
			angle = owner.getAxisVect((0,0,1)).angle(EDGENRM, 0)
			angle = round(self.toDeg(angle), 2)
			ledge = self.getLocalSpace(owner, EDGEPNT)
			dist = ledge[2]
			offset = self.EDGE_H-self.GND_H
			wall = self.findWall()

			if keymap.BINDS["PLR_JUMP"].tap() == True and angle < self.SLOPE:
				if 2 > owner.localLinearVelocity[2] > 0 and wall == True:
					owner.localLinearVelocity = (0, 0, 2)
					return
		#else:
		#	guide.worldPosition = rayto

		if keymap.BINDS["PLR_JUMP"].tap() == True and fdot < -0.8:
			self.ST_Advanced_Set()
			return

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
			if self.data["WALLJUMPS"] == 0 or keymap.BINDS["TOGGLEMODE"].tap() == True or keymap.BINDS["PLR_JUMP"].tap() == True:
				if self.data["ENERGY"] > 15:
					self.wallJump(nrm)
					self.data["WALLJUMPS"] += 1
		else:
			self.doPlayerAnim("FALLING")

			if self.motion["Move"].length > 0.01:
				move = self.motion["Move"].normalized()
				vref = viewport.getDirection((move[0], move[1], 0))
				owner.applyForce(vref*2, False)

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
		self.wallnrm = None
		self.jump_state = "HANGING"
		self.jump_timer = 0
		self.data["HUD"]["Target"] = None

		self.active_state = self.ST_Hanging

	def ST_Hanging(self):
		self.getInputs()

		owner = self.objects["Root"]

		self.jump_state = "HANGING"

		owner.worldLinearVelocity = (0,0,0)

		move = self.motion["Move"].normalized()
		vref = viewport.getDirection((move[0], move[1], 0))
		mref = owner.worldOrientation.inverted()*vref
		fdot = owner.getAxisVect((0,1,0)).dot(vref)

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
			if self.wallnrm != None:
				rayto = rayfrom+self.wallnrm
				self.wallnrm = None
			else:
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
				self.wallnrm = owner.worldOrientation*-wall

				point = wall*(self.WALL_DIST-0.05)
				point = owner.worldOrientation*point
				owner.worldPosition = (TRPNT+point)-owner.getAxisVect((0,0,offset-0.05-diff))

				if abs(mref[0]) > 0.5:
					X = 1-(2*(mref[0]<0))
				owner.localLinearVelocity[0] = (X*0.015)*60

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

		elif keymap.BINDS["TOGGLEMODE"].tap() == True or (keymap.BINDS["PLR_JUMP"].tap() == True and fdot < -0.8):
			wall = self.findWall()
			if wall == True:
				self.ST_EdgeFall_Set()
				self.ST_Advanced_Set(wall)

		elif keymap.BINDS["PLR_JUMP"].tap() == True:
			self.ST_EdgeClimb_Set()

		self.objects["Character"]["DEBUG2"] = str(self.jump_state)

	def ST_EdgeClimb_Set(self, start=0):
		owner = self.objects["Root"]
		char = self.objects["Character"]
		rayup = self.getWorldSpace(owner, self.wallrayup)
		rayto = self.getWorldSpace(owner, self.wallrayto)
		SH = None

		edge = self.checkGround(simple=True, ray=(rayto, rayup, 2.0))

		if edge != None:
			self.groundhit = edge
			self.getGroundPoint(edge[0])

			rayto = edge[1]+owner.getAxisVect((0, 0.5, 0.1))
			rayfrom = owner.worldPosition+owner.getAxisVect((0, 0, self.EDGE_H))

			SH, SP, SN = owner.rayCast(rayto, rayfrom, 0, "GROUND", 1, 1, 0)

		if SH != None:
			if self.jump_state == "NONE":
				self.doAnim(STOP=True)
				self.doJump(5, 3)
				self.rayorder = "END"
				self.active_state = self.ST_Walking

		elif edge != None:
			self.doAnim(STOP=True)
			self.doAnim(NAME=self.ANIMSET+"EdgeClimb", FRAME=(start, self.EDGECLIMB_TIME+10), MODE="PLAY")
			target = self.groundhit[1]+owner.getAxisVect((0, 0, self.GND_H))
			loctar = self.getLocalSpace(owner, target)
			owner.worldPosition = target
			viewport.setCameraPosition(-loctar)
			self.rayorder = loctar.copy()
			self.jump_state = "NONE"
			self.jump_timer = 0
			self.data["CLIMBRATE"] = self.EDGECLIMB_TIME/(self.EDGECLIMB_TIME-start)
			self.active_state = self.ST_EdgeClimb

	def ST_EdgeClimb(self):
		self.getInputs()

		owner = self.objects["Root"]
		char = self.objects["Character"]

		self.jump_state = "NONE"
		self.jump_timer += self.data["CLIMBRATE"]

		owner.worldLinearVelocity = (0,0,0)

		time = self.EDGECLIMB_TIME
		scale = (1/self.data["CLIMBRATE"])
		start = time-(time*scale)

		fac = self.jump_timer/time

		ground = self.checkGround(simple=True)

		lerp = -self.rayorder*(1-fac)

		if ground != None:
			self.groundhit = ground
			self.getGroundPoint(ground[0])

		self.doAnim(NAME=self.ANIMSET+"EdgeClimb", FRAME=(0, self.EDGECLIMB_TIME+10), MODE="LOOP")
		frame = (self.jump_timer*scale)+(start)
		self.doAnim(SET=frame)

		self.alignToGravity()

		if self.jump_timer >= time or ground == None:
			self.doAnim(STOP=True)
			self.doPlayerAnim("RESET")
			self.rayorder = "END"
			self.jump_state = "NONE"
			self.jump_timer = 0
			self.climbrate = 1
			lerp = [0,0,0]
			self.active_state = self.ST_Walking

		viewport.setCameraPosition(lerp)

	def ST_EdgeFall_Set(self):
		self.rayorder = "END"
		self.jump_state = "FALLING"
		self.jump_timer = 0
		self.doAnim(STOP=True)
		self.active_state = self.ST_Walking


class InventoryRed(HUD.Inventory):

	def ST_Startup(self):
		self.objects["Items"].localPosition = (-10, -17, 0)
		self.objects["Items"].localOrientation = self.createMatrix(deg=True, rot=[0,0,90])

class LayoutRed(player.ActorLayout):

	MODULES = [HUD.Stats, HUD.Aircraft, InventoryRed] #, HUD.Weapons]

class GreenPlayer(ActorPlayer):

	NAME = "Green Actor"
	CLASS = "Standard"
	WP_TYPE = "RANGED"
	HAND = {"MAIN":"Hand_R", "OFF":"Hand_L"}
	INVENTORY = {"Hip_R":"WP_GravGun"}
	#OFFSET = (0, 0.05, 0.1)
	#SPEED = 0.1
	#ACCEL = 20
	#JUMP = 5
	#EYE_H = 1.658
	#EDGE_H = 2.0
	CAM_TYPE = "THIRD"

class RedPlayer(ActorPlayer):

	NAME = "Red Actor"
	CLASS = "Standard"
	WP_TYPE = "RANGED"
	HAND = {"MAIN":"Hand_R", "OFF":"Hand_L"}
	INVENTORY = {"Back":"INV_JetPack", "Shoulder_R": "WP_MachineGun", "Hip_R":"WP_HandGun"}
	#OFFSET = (0, 0.05, 0.1)
	SPEED = 0.1
	ACCEL = 20
	JUMP = 5
	#EYE_H = 1.658
	#EDGE_H = 2.0
	CAM_TYPE = "THIRD"

	def defaultData(self):
		dict = super().defaultData()
		dict["NERF"] = False

		return dict

	def ST_Advanced_Set(self):
		owner = self.objects["Root"]

		keymap.MOUSELOOK.center()

		if self.jump_state != "FLYING":
			if self.gravity.length <= 0.1:
				return
			self.alignToGravity(owner, axis=1, neg=True)
			vref = viewport.getDirection((0,1,0))
			owner.alignAxisToVect(vref, 2, 1.0)

		if self.jump_state == "NONE":
			owner.localLinearVelocity[1] -= 3

		owner.setDamping(0.8, 0.9)

		self.setPhysicsType("RIGID")

		if self.data["CAMERA"]["State"] == "THIRD":
			self.data["CAMERA"]["Slow"] = 12
			self.data["CAMERA"]["Distance"] = 5
			eye = 0
		else:
			self.data["CAMERA"]["Slow"] = 0
			self.data["CAMERA"]["Distance"] = 0
			eye = self.EYE_H-self.GND_H

		self.data["CAMERA"]["Orbit"] = False
		self.data["CAMERA"]["AutoZoom"] = False

		if self.jump_state != "FLYING":
			viewport.VIEWCLASS.doCameraFollow(owner, 0, False, run=True)
			viewport.VIEWCLASS.dist = self.data["CAMERA"]["Distance"]

			viewport.setEyeHeight(eye=[0,0,eye], set=True)
			viewport.setEyePitch(90, set=True)

		HUD.SetLayout(self, LayoutRed)

		self.objects["Wings"].color = (0,1,1,1)

		self.data["HUD"]["Target"] = None
		self.data["HUD"]["Power"] = 0
		self.data["HUD"]["Lift"] = 0
		self.data["HUD"]["Forward"] = [0,0,1]

		self.jump_state = "FLYING"
		self.active_state = self.ST_Flying

	def ST_Walking_Set(self):
		keymap.MOUSELOOK.center()

		self.jump_state = "FALLING"
		self.data["CAMERA"]["Slow"] = 0
		self.data["CAMERA"]["Orbit"] = True
		self.data["CAMERA"]["AutoZoom"] = self.CAM_AUTOZOOM
		self.data["CAMERA"]["Distance"] = None

		self.objects["Wings"].color = (1,1,1,1)

		if self.gravity.length > 0.1:
			self.alignCamera(axis=(0,0,1), up=-self.gravity.normalized())
		viewport.setEyePitch(0, set=True)
		self.assignCamera()

		self.alignPlayer()

		self.setPhysicsType("DYNAMIC")
		self.objects["Root"].setDamping(0, 0)

		HUD.SetLayout(self)
		self.resetAcceleration()
		self.doAnim(STOP=True)

		self.active_state = self.ST_Walking

	def ST_Flying(self):
		self.getInputs()

		owner = self.objects["Root"]
		linWV = owner.worldLinearVelocity

		wall = self.checkWall(axis=owner.getAxisVect((0,0,1)), simple=1)

		if keymap.BINDS["TOGGLEMODE"].tap() == True or self.gravity.length <= 0.1:
			self.ST_Walking_Set()
			return
		if wall != None:
			if "COLLIDE" not in wall[0]:
				self.ST_Walking_Set()
				return

		owner.applyForce(-self.gravity, False)

		ORIX = 0
		ORIY = 0
		if self.gravity.length > 0.1:
			GZ = self.gravity.normalized()
			ORIX = ((self.toDeg(owner.getAxisVect((1,0,0)).angle(GZ))-90)/90)
			#ORIX = ORIX*abs(ORIX)
			ORIY = ((self.toDeg(owner.getAxisVect((0,0,1)).angle(GZ))-90)/90)
			#ORIY = ORIY*abs(ORIY)

		FORWARD = keymap.BINDS["PLR_FORWARD"].axis() - keymap.BINDS["PLR_BACKWARD"].axis()
		STRAFE = keymap.BINDS["PLR_STRAFERIGHT"].axis() - keymap.BINDS["PLR_STRAFELEFT"].axis()

		TURN = keymap.BINDS["PLR_TURNLEFT"].axis() - keymap.BINDS["PLR_TURNRIGHT"].axis()
		LOOK = keymap.BINDS["PLR_LOOKUP"].axis() - keymap.BINDS["PLR_LOOKDOWN"].axis()

		msX, msY = keymap.MOUSELOOK.axis()
		TURN = (msX*80)+(TURN) #*abs(TURN))
		LOOK = (-msY*120)+(LOOK) #*abs(LOOK))

		if abs(TURN) > 1:
			TURN = 1-(2*(TURN<0))
		if abs(LOOK) > 1:
			LOOK = 1-(2*(LOOK<0))

		move = [STRAFE, FORWARD]
		rotate = [LOOK, 0, TURN]

		#if self.data["ENERGY"] < 1:
		#	self.data["NERF"] = True

		#if self.data["NERF"] == True:
		#	move[1] = -1
		#	if self.data["ENERGY"] > 10:
		#		self.data["NERF"] = False

		POWER = (25-(ORIY*20))
		POWER = POWER+(POWER*(move[1]*0.5))
		DRAG = move[1]*-0.2

		BANK = ((rotate[2]*0.4)-(rotate[2]*DRAG))
		PITCH = ((rotate[0]*1)-(rotate[0]*DRAG))
		YAW = ((move[0]*0.4)-(move[0]*DRAG))

		YAWROLL = (ORIX*-0.4)+(YAW*(abs(0.8*ORIX)+0.2))

		owner.applyForce((0, 0, POWER), True)
		owner.applyTorque((-PITCH, YAWROLL, -BANK), True)

		#if self.jump_state == "JETPACK_FLY":
		#	diff = 1*self.data["RECHARGE"]

		#	check = self.data["ENERGY"]+diff
		#	if check <= 100:
		#		self.data["ENERGY"] += diff
		#	elif self.data["ENERGY"] < 100:
		#		self.data["ENERGY"] = 100

		#elif move[1] > 0:
		#	self.data["ENERGY"] -= abs(move[1])*0.3

		#elif self.data["NERF"] == False:
		#	diff = abs(move[1])*self.data["RECHARGE"]

		#	check = self.data["ENERGY"]+diff
		#	if check <= 100:
		#		self.data["ENERGY"] += diff
		#	elif self.data["ENERGY"] < 100:
		#		self.data["ENERGY"] = 100

		self.doAnim(NAME=self.ANIMSET+"Flying", FRAME=(20,20), MODE="LOOP", BLEND=10)

		self.data["HUD"]["Power"] = (1+move[1])*50

		self.objects["Character"]["DEBUG1"] = ORIX
		self.objects["Character"]["DEBUG2"] = ORIY

		## Slow Camera ##
		if self.data["CAMERA"]["State"] == "THIRD":
			self.data["CAMERA"]["Slow"] = 12
			self.data["CAMERA"]["Distance"] = 5
			eye = 0
		else:
			self.data["CAMERA"]["Slow"] = 0
			self.data["CAMERA"]["Distance"] = 0
			eye = self.EYE_H-self.GND_H

		viewport.setEyeHeight(eye=[0,0,eye], set=True)
		viewport.setEyePitch(90, set=True)

		self.jump_state = "FLYING"


class BluePlayer(TRPlayer):

	NAME = "Blue Actor"
	CLASS = "Standard"
	WP_TYPE = "MELEE"
	INVENTORY = {"Shoulder_L": "WP_SimpleStaff", "Shoulder_R":"WP_LaserGun"}
	#OFFSET = (0, 0.1, 0.18)
	SPEED = 0.12
	JUMP = 6
	#EYE_H = 1.527
	#EDGE_H = 1.85
	ACCEL = 15
	CAM_TYPE = "THIRD"

