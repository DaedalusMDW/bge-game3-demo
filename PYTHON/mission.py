

from bge import logic

from game3 import base, world, keymap, HUD, viewport

SUB_NAMES = {
	"Actor": (0.0, 1.0, 0.0),
	"Ahsoka": (1.0, 0.67, 0.0)
}

SUB_SWITCH = {
	"Actor": {"NAME":"Actor", "LINE":"<PLACEHOLDER>", "TIME":90, "ACTION":"EmoteWave", "FRAMES":(0,120)},
	"Ahsoka": {"NAME":"Ahsoka", "LINE":"Time to see a jedi in action!", "TIME":60}
}


class Cinema(HUD.Cinema):

	OBJECT = "Cinema"
	COLORSHEET = SUB_NAMES

class LayoutCinema(HUD.HUDLayout):

	MODULES = [Cinema]


class CoreMission(base.CoreObject):

	HUDLAYOUT = LayoutCinema

	def defaultData(self):
		dict = super().defaultData()
		dict["HUD"] = {"Subtitles":None}
		return dict


class SwitchPlayer(CoreMission):

	UPDATE = True

	def loadChildren(self):
		self.dict["Children"] = []
		self.dict["PlayerChildren"] = []

	def ST_Startup(self):
		owner = self.objects["Root"]
		scene = owner.scene

		del owner["GROUND"]

		name = owner.get("PLAYER", "Actor")
		name = self.data.get("CHAR_NAME", name)
		anim = owner.get("ACTION", "Jumping")
		anim = self.data.get("IDLE_ANIM", anim)

		self.data["CHAR_NAME"] = name
		self.data["IDLE_ANIM"] = anim

		self.chars = {"CUR":None, "NEW":None, "PID":None}

		if name not in scene.objectsInactive:
			print("SPAWN ERROR: Player Switch object not found", name)

		elif name not in list(base.WORLD["PLAYERS"].values())+list(base.PLAYER_CLASSES.keys()):
			self.chars["CUR"] = scene.addObject(name, owner, 0)
			self.chars["CUR"]["DICT"] = base.PROFILE["PLRData"].get(name, {"Object":name, "Data":None})
			self.chars["CUR"]["PID"] = -1
			cls = base.GETCLASS(self.chars["CUR"])
			#cls.switchPlayerPassive()
			cls.setContainerParent(self)
			self.chars["CUR"].setParent(owner)
			self.chars["CUR"].localPosition = self.createVector()
			self.chars["CUR"].localOrientation = self.createMatrix()

			cls.doAnim(NAME=cls.ANIMSET+anim, FRAME=(0,0))

			self.objects["Root"]["RAYNAME"] = cls.NAME
			self.active_state = self.ST_Disabled
		else:
			print("SPAWN WARNING: Player Switch object is active", name)
			self.endObject()

		self.anim_timer = 0

	def ST_Disabled(self):
		if self.checkClicked() == True:
			self.ST_Active_Set()

	def ST_Active_Set(self):
		owner = self.objects["Root"]
		plr = owner["RAYCAST"]

		if plr == None or self.chars["CUR"] == None:
			return

		self.chars["NEW"] = plr.objects["Character"]

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
		s = SUB_SWITCH.get(nc, None)
		s = SUB_SWITCH.get(nc+nn, s)

		self.data["HUD"]["Subtitles"] = s

		a = "Jumping"
		f = (0,0)

		if s != None:
			a = s.get("ACTION", a)
			f = s.get("FRAMES", f)

		cls = self.chars["CUR"]["Class"]
		cls.doAnim(NAME=cls.ANIMSET+a, FRAME=f)

		HUD.SetLayout(self)

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

		owner["RAYNAME"] = self.chars["CUR"]["Class"].NAME

		self.data["CHAR_NAME"] = self.chars["CUR"].name

		self.data["HUD"]["Subtitles"] = None

		self.anim_timer = 0
		self.active_state = self.ST_Disabled

