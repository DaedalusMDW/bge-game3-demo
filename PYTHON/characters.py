

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

