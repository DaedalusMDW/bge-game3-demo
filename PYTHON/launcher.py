

## LAUNCHER ##

from bge import logic, render, texture

DTR = [render.getWindowWidth(), render.getWindowHeight()]

from game3 import GAMEPATH, firstrun, base, settings, config, keymap, world

DTR = logic.globalDict.get("_DESKTOP", DTR)
logic.globalDict["_DESKTOP"] = DTR

VER = "3.1 alpha"


def RUN(cont):
	owner = cont.owner
	scene = owner.scene

	current = logic.globalDict["CURRENT"]
	profile = logic.globalDict["PROFILES"][current["Profile"]]

	map = profile["GLBData"].get("NEWLEVEL", None)
	scn = profile["GLBData"].get("NEWSCENE", None)

	if "Button.Maps.Resume" in scene.objects:
		if map == None or map not in logic.globalDict["BLENDS"]:
			scene.objects["Button.Maps.Resume"].endObject()
		else:
			scene.objects["Button.Maps.Resume"].setVisible(True, True)


def VERSION(cont):
	global VER
	cont.owner.resolution = 0.4
	cont.owner["Text"] = "Release "+VER


def LOGO(cont):
	owner = cont.owner
	t = owner.get("FRAME", 330)

	if keymap.SYSTEM["ESCAPE"].tap() == True or keymap.SYSTEM["UI_SKIP"].tap() or firstrun == False or t < 0:
		owner.scene.replace("Scene")
		owner.endObject()

	owner["FRAME"] = t-1


def VIDEO(cont):
	owner = cont.owner

	if keymap.SYSTEM["ESCAPE"].tap() == True or keymap.SYSTEM["UI_SKIP"].tap() or firstrun == False:
		owner.scene.replace("Scene")
		owner.endObject()
		return

	if "TEXTURE" not in owner:
		owner["VIDEO"] = texture.VideoFFmpeg(GAMEPATH+owner["FILE"])
		owner["VIDEO"].play()
		owner["TEXTURE"] = texture.Texture(owner)
		owner["TEXTURE"].source = owner["VIDEO"]

	if owner["TIME"] >= owner["FRAMES"]/60:
		owner["SCENE"] = "DONE"
	else:
		owner["TEXTURE"].refresh(True)
		owner["TIME"] += (1/60)


def OPEN(cont):
	s = cont.owner.get("MAP", "")

	split = s.split("\\")
	map = split[0]+".blend"
	scn = None
	if len(split) > 1:
		scn = split[1]

	if map in logic.globalDict["BLENDS"]:
		world.openBlend(map, scn)


def RESUME(cont):
	current = logic.globalDict["CURRENT"]
	profile = logic.globalDict["PROFILES"][current["Profile"]]

	map = profile["GLBData"].get("NEWLEVEL", None)
	scn = profile["GLBData"].get("NEWSCENE", None)

	if map == None or map not in logic.globalDict["BLENDS"]:
		return

	world.openBlend(map, scn)


def KEYMAP(cont):
	world.openBlend("KEYMAP")


def DEBUG(cont):
	s = cont.owner.get("SETTING", None)
	debug = logic.globalDict["GRAPHICS"]["Debug"]

	if s in [True, False]:
		debug[0] = s

		settings.SaveJSON(GAMEPATH+"Graphics.cfg", logic.globalDict["GRAPHICS"])

	render.showFramerate(debug[1] and debug[0])
	render.showProfile(False)
	render.showProperties(debug[3] and debug[0])


def RESOLUTION(cont):
	X = None
	Y = None

	if "FULLSCREEN" in cont.owner:
		logic.globalDict["GRAPHICS"]["Fullscreen"] ^= True
		fs = logic.globalDict["GRAPHICS"]["Fullscreen"]
		dk = logic.globalDict["_DESKTOP"]
		render.setWindowSize(dk[0], dk[1])
		render.setFullScreen(fs)
		rs = logic.globalDict["GRAPHICS"]["Resolution"]
		X = rs[0]
		Y = rs[1]

	elif "X" in cont.owner and "Y" in cont.owner:
		X = cont.owner["X"]
		if X % 2 != 0:
			X -= 1

		Y = cont.owner["Y"]
		if Y % 2 != 0:
			Y -= 1


	if X != None and Y != None:
		render.setWindowSize(X, Y)
	else:
		return

	X = render.getWindowWidth()
	Y = render.getWindowHeight()

	logic.globalDict["GRAPHICS"]["Resolution"] = [X,Y]

	settings.SaveJSON(GAMEPATH+"Graphics.cfg", logic.globalDict["GRAPHICS"])


def VSYNC(cont):
	s = cont.owner.get("SETTING", None)

	if s in [True, False]:
		logic.globalDict["GRAPHICS"]["Vsync"] = s

		settings.SaveJSON(GAMEPATH+"Graphics.cfg", logic.globalDict["GRAPHICS"])


def SHADERS(cont):
	s = cont.owner.get("SETTING", None)

	if s in ["LOW", "MEDIUM", "HIGH"]:
		logic.globalDict["GRAPHICS"]["Shaders"] = s

		settings.SaveJSON(GAMEPATH+"Graphics.cfg", logic.globalDict["GRAPHICS"])


def SHADOWS(cont):
	s = cont.owner.get("SETTING", None)

	if s in [True, False]:
		logic.globalDict["GRAPHICS"]["Shadows"] = s

		settings.SaveJSON(GAMEPATH+"Graphics.cfg", logic.globalDict["GRAPHICS"])


def MIPMAP(cont):
	s = cont.owner.get("SETTING", None)

	if s in ["NONE", "NORMAL", "FAR"]:
		logic.globalDict["GRAPHICS"]["Mipmap"] = s

		settings.SaveJSON(GAMEPATH+"Graphics.cfg", logic.globalDict["GRAPHICS"])


def SAVE():
	global VER
	current = logic.globalDict["CURRENT"]
	profile = logic.globalDict["PROFILES"][current["Profile"]]

	path = GAMEPATH
	name = "Base"+VER.strip().replace(".","",3)

	if "_" not in current["Profile"]:
		name = current["Profile"]

	dict = profile

	settings.SaveJSON(path+name+"Profile.json", dict, "\t")
	settings.SaveJSON(GAMEPATH+"Graphics.cfg", logic.globalDict["GRAPHICS"])

	print("Profile Saved:", name+"Profile.json")


def LOAD():
	global VER
	current = logic.globalDict["CURRENT"]

	path = GAMEPATH
	name = "Base"+VER.strip().replace(".","",3)

	if "_" not in current["Profile"]:
		name = current["Profile"]

	dict = settings.LoadJSON(path+name+"Profile.json")

	if dict == None:
		return None

	logic.globalDict["PROFILES"][current["Profile"]] = dict

	base.PROFILE = dict
	base.WORLD = dict["GLBData"]

	print("Profile Loaded:", name+"Profile.json")

	return dict


def LOGIN(cont):
	s = cont.owner.get("PROFILE", "None")

	s = s.capitalize()

	if s in ["None", "Guest", "Base"]:
		SAVE()
		logic.globalDict["CURRENT"]["Profile"] = "__guest__"
		LOAD()

	elif s in logic.globalDict["PROFILES"]:
		SAVE()
		logic.globalDict["CURRENT"]["Profile"] = s
		LOAD()

	else:
		SAVE()
		logic.globalDict["CURRENT"]["Profile"] = s
		dict = LOAD()
		if dict == None:
			dict = settings.GenerateProfileData()
			logic.globalDict["PROFILES"][s] = dict


def PLAYER(cont):
	s = cont.owner.get("PLAYER", "None")

	current = logic.globalDict["CURRENT"]
	profile = logic.globalDict["PROFILES"][current["Profile"]]
	WORLD = profile["GLBData"]

	print("PLAYER ENTRY:", s)

	if s == "None":
		if "PLAYERS" in WORLD:
			del WORLD["PLAYERS"]

	else:
		if s == "":
			d = WORLD.get("PLAYERS", {})
			cont.owner["PLAYER"] = d.get("1", "")
		else:
			s = s.strip("\n")
			s = s.strip("\t")
			if "PLAYERS" not in WORLD:
				WORLD["PLAYERS"] = {}
			WORLD["PLAYERS"]["1"] = s

