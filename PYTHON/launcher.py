

## LAUNCHER ##

from bge import logic, render

DTR = [render.getWindowWidth(), render.getWindowHeight()]

from game3 import GAMEPATH, base, settings, keymap, world

DTR = logic.globalDict.get("_DESKTOP", DTR)
logic.globalDict["_DESKTOP"] = DTR

VER = "r1.0"


def RUN(cont):
	owner = cont.owner
	scene = owner.scene

	current = logic.globalDict["CURRENT"]
	profile = logic.globalDict["PROFILES"][current["Profile"]]

	map = profile["GLBData"].get("NEWLEVEL", None)
	scn = profile["GLBData"].get("NEWSCENE", None)

	if map == None or map not in logic.globalDict["BLENDS"]:
		if "Button.Maps.Resume" in scene.objects:
			scene.objects["Button.Maps.Resume"].endObject()

	#	if "Button.MapSelect" not in scene.objects:
	#		scene.addObject("Button.MapSelect", owner, 0)
	#else:
	#	if "Button.Launch" in scene.objects:
	#		scene.objects["Button.MapSelect"].endObject()
	#	if "Button.Resume" not in scene.objects:
	#		scene.addObject("Button.Resume", owner, 0)


def VERSION(cont):
	global VER
	cont.owner["Text"] = "Ver "+VER


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
	name = "Base"+VER

	if "_" not in current["Profile"]:
		name = current["Profile"]

	dict = profile

	settings.SaveJSON(path+name+"Profile.json", dict, "\t")
	settings.SaveJSON(GAMEPATH+"Graphics.cfg", logic.globalDict["GRAPHICS"])


def LOAD():
	global VER
	current = logic.globalDict["CURRENT"]

	path = GAMEPATH
	name = "Base"+VER

	if "_" not in current["Profile"]:
		name = current["Profile"]

	dict = settings.LoadJSON(path+name+"Profile.json")

	if dict == None:
		return None

	logic.globalDict["PROFILES"][current["Profile"]] = dict

	base.PROFILE = dict
	base.WORLD = dict["GLBData"]

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

	if s == "None":
		if "PLAYERS" in WORLD:
			del WORLD["PLAYERS"]

	else:
		if "PLAYERS" not in WORLD:
			WORLD["PLAYERS"] = {}
		WORLD["PLAYERS"]["1"] = s

