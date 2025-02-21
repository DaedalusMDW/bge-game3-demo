

from bge import logic

from game3 import base, world, keymap, HUD, viewport

import PYTHON.subtitles as subtitles


class Cinema(HUD.Cinema):

	OBJECT = "Cinema"
	COLORSHEET = subtitles.NAMES

class LayoutCinema(HUD.HUDLayout):

	MODULES = [Cinema]


class CoreMission(base.CoreObject):

	HUDLAYOUT = LayoutCinema

	def defaultData(self):
		self.env_dim = None
		self.env_col = [0,0,0,1]

		dict = super().defaultData()
		dict["HUD"] = {"Subtitles":None}
		return dict

	def applyContainerProps(self, cls):
		super().applyContainerProps(cls)
		cls.env_dim = list(self.env_col)


class SwitchPlayer(CoreMission):

	UPDATE = True

	def loadChildren(self):
		self.dict["Children"] = []
		self.dict["PlayerChildren"] = []

	def ST_Startup(self):
		owner = self.objects["Root"]
		scene = owner.scene

		self.spot = scene.addObject("GFX_Spot", owner, 0)
		self.spot.setParent(owner)
		self.spot.localPosition = (0, 0, -0.98)

		name = owner.get("PLAYER", "")
		name = self.data.get("CHAR_NAME", name)
		anim = owner.get("ACTION", "Jumping")
		anim = self.data.get("IDLE_ANIM", anim)
		seat = owner.get("SEAT", False)
		seat = self.data.get("SEAT_ANIM", seat)

		self.data["CHAR_NAME"] = name
		self.data["IDLE_ANIM"] = anim
		self.data["SEAT_ANIM"] = seat

		self.chars = {"CUR":None, "NEW":None, "PID":None}

		if name in ["", "NONE"] or name not in scene.objectsInactive:
			name = None
			print("SPAWN ERROR: Player Switch object not found", name)

		if name == None or name in list(base.WORLD["PLAYERS"].values())+list(base.PLAYER_CLASSES.keys()):
			self.col = owner.scene.addObject("BOX_Sphere", owner, 0)
			self.col.setParent(owner)
			self.col.localPosition = self.createVector()
			self.col.localOrientation = self.createMatrix()
			self.col.localScale = (0.5, 0.5, 0.5)
			self.col["COLLIDE"] = []

			self.data["CHAR_NAME"] = None
			self.col["RAYNAME"] = "Player Switcher"

			self.spot.color = (1,0,0,1)
			self.spot.visible = True

			self.active_state = self.ST_Empty

			print("SPAWN WARNING: Player Switch object -", name)
		else:
			self.chars["CUR"] = scene.addObject(name, owner, 0)
			self.chars["CUR"]["DICT"] = base.PROFILE["PLRData"].get(name, {"Object":name, "Data":None})
			self.chars["CUR"]["PID"] = -1

			cls = base.GETCLASS(self.chars["CUR"])
			cls.setContainerParent(self)

			cls.doAnim(NAME=cls.ANIMSET+anim, FRAME=(0,0))

			self.chars["CUR"].setParent(owner)
			self.chars["CUR"].localPosition = self.createVector()
			self.chars["CUR"].localOrientation = self.createMatrix()

			if self.data["SEAT_ANIM"] == True:
				self.chars["CUR"].localPosition[2] = cls.OFFSET[2]

			self.col = scene.addObject(cls.HITBOX, owner, 0)
			self.col.setParent(owner)
			self.col.localPosition = self.createVector()
			self.col.localOrientation = self.createMatrix()
			self.col.suspendDynamics(False)

			self.col["RAYCAST"] = None
			self.col["RAYNAME"] = cls.NAME

			self.spot.color = (0,0,1,1)
			self.spot.visible = True

			self.active_state = self.ST_Disabled

		self.anim_timer = 0

		self.active_post.insert(0, self.PS_Ambient)

	def PS_Ambient(self):
		if self.env_dim == None:
			cls = self.getParent()
			amb = 0
			if cls != None:
				amb = cls.dict.get("DIM", amb)
			self.env_dim = (amb+1, amb+1, amb+1, 1.0)

		self.env_col = list(self.env_dim)
		self.env_dim = None

	def ST_Empty_Set(self):
		owner = self.objects["Root"]
		plr = self.col["RAYCAST"]

		if plr == None or self.chars["CUR"] == None:
			return

		cls = self.chars["CUR"]["Class"]
		cls.removeContainerParent()
		cls.switchPlayerNPC()

		plr.sendEvent("INTERACT", cls, "ACTOR", "TAP")

		self.chars["CUR"] = None

		self.col.endObject()
		self.col = owner.scene.addObject("BOX_Sphere", owner, 0)
		self.col.setParent(owner)
		self.col.localPosition = self.createVector()
		self.col.localOrientation = self.createMatrix()
		self.col.localScale = (0.5, 0.5, 0.5)
		self.col["COLLIDE"] = []

		self.data["CHAR_NAME"] = None
		self.col["RAYNAME"] = "Player Switcher"

		self.spot.color = (1,0,0,1)
		self.spot.visible = True

		self.anim_timer = 0
		self.active_state = self.ST_Empty

	def ST_Empty(self):
		owner = self.objects["Root"]

		t = 1
		for cls in self.col["COLLIDE"]:
			if cls != None:
				t = 0
				self.sendEvent("SWITCHER", cls, "SEND")

		self.col["COLLIDE"] = []

		evt = self.getFirstEvent("SWITCHER", "RECEIVE")

		if evt == None:
			self.anim_timer = 0
			self.spot.color = (1, t, t, 1)
		else:
			self.anim_timer += 1

			t = self.anim_timer/120
			self.spot.color = (1-t, 0, t, 1)

			if self.anim_timer > 120:
				evt.sender.switchPlayerPassive()
				evt.sender.setContainerParent(self)
				evt.sender.doAnim(NAME=evt.sender.ANIMSET+self.data["IDLE_ANIM"], FRAME=(0,0))

				self.chars["CUR"] = evt.sender.owner

				self.chars["CUR"].setParent(owner)
				self.chars["CUR"].localPosition = self.createVector()
				self.chars["CUR"].localOrientation = self.createMatrix()

				if self.data["SEAT_ANIM"] == True:
					self.chars["CUR"].localPosition[2] = evt.sender.OFFSET[2]

				self.data["CHAR_NAME"] = self.chars["CUR"].name

				self.col.endObject()
				self.col = owner.scene.addObject(evt.sender.HITBOX, owner, 0)
				self.col.setParent(owner)
				self.col.localPosition = self.createVector()
				self.col.localOrientation = self.createMatrix()
				self.col.suspendDynamics(False)

				self.col["RAYCAST"] = None
				self.col["RAYNAME"] = evt.sender.NAME

				self.spot.color = (0,0,1,1)
				self.spot.visible = True

				self.anim_timer = -5
				self.active_state = self.ST_Disabled

	def ST_Disabled(self):
		key = False
		if self.col["RAYCAST"] != None:
			if keymap.BINDS["ACTIVATE"].active() == True:
				key = True

		if self.anim_timer >= 60:
			self.ST_Empty_Set()
		elif key == False:
			if self.anim_timer >= 1:
				self.ST_Active_Set()
			if self.anim_timer < 0:
				self.anim_timer += 1
		elif self.anim_timer >= 0:
			self.anim_timer += 1

		self.col["RAYCAST"] = None

	def ST_Active_Set(self):
		owner = self.objects["Root"]
		plr = self.col["RAYCAST"]

		if plr == None or self.chars["CUR"] == None:
			return

		self.chars["NEW"] = plr.owner

		self.chars["PID"] = plr.switchPlayerPassive()

		plr.setContainerParent(self)

		self.chars["NEW"].worldPosition = self.objects["New"].worldPosition.copy()
		self.chars["NEW"].worldOrientation = self.objects["New"].worldOrientation.copy()
		self.chars["NEW"].setVisible(True, True)

		plr.doAnim(NAME=plr.ANIMSET+"Jumping", FRAME=(0,0))

		self.objects["Cam"].near = base.config.CAMERA_CLIP[0]
		self.objects["Cam"].far = base.config.CAMERA_CLIP[1]
		owner.scene.active_camera = self.objects["Cam"]

		nc = self.chars["CUR"].name
		nn = self.chars["NEW"].name
		s = subtitles.SWITCH.get(nc, None)
		s = subtitles.SWITCH.get(nc+nn, s)

		self.data["HUD"]["Subtitles"] = s

		a = "Jumping"
		f = (0,0)

		if s != None:
			a = s.get("ACTION", a)
			f = s.get("FRAMES", f)

		cls = self.chars["CUR"]["Class"]
		cls.doAnim(NAME=cls.ANIMSET+a, FRAME=f)

		HUD.SetLayout(self)

		self.anim_timer = 0
		self.active_state = self.ST_Active

	def ST_Active(self):
		owner = self.objects["Root"]

		time = 60
		if self.data["HUD"]["Subtitles"] != None:
			time = self.data["HUD"]["Subtitles"].get("TIME", time)

		if self.anim_timer == time:
			self.ST_Disabled_Set()
		else:
			self.anim_timer += 1

	def ST_Disabled_Set(self):
		owner = self.objects["Root"]

		plr = self.chars["CUR"]["Class"]
		plr.doAnim(NAME=plr.ANIMSET+"Jumping", FRAME=(0,0))

		cls = self.chars["NEW"]["Class"]
		cls.doAnim(NAME=cls.ANIMSET+self.data["IDLE_ANIM"], FRAME=(0,0))

		self.chars["CUR"].worldPosition = self.objects["New"].worldPosition.copy()
		self.chars["CUR"].worldOrientation = self.objects["New"].worldOrientation.copy()

		plr.removeContainerParent()
		plr.switchPlayerActive(self.chars["PID"])

		viewport.loadCamera()

		self.chars["CUR"] = self.chars["NEW"]
		self.chars["NEW"] = None
		self.chars["PID"] = None

		self.chars["CUR"].setParent(owner)
		self.chars["CUR"].localPosition = self.createVector()
		self.chars["CUR"].localOrientation = self.createMatrix()

		if self.data["SEAT_ANIM"] == True:
			self.chars["CUR"].localPosition[2] = cls.OFFSET[2]

		self.col["RAYCAST"] = None
		self.col["RAYNAME"] = self.chars["CUR"]["Class"].NAME

		self.data["CHAR_NAME"] = self.chars["CUR"].name

		self.data["HUD"]["Subtitles"] = None

		self.anim_timer = -5
		self.active_state = self.ST_Disabled

