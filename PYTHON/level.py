

## LEVEL MODULES ##

import math
import mathutils

from bge import logic, events, render, types

from game3 import GAMEPATH, keymap, settings, config, base, player, viewport, world


CHKPNT = settings.json.dumps(base.PROFILE)


def INIT(cont):
	global CHKPNT

	owner = cont.owner
	scene = owner.scene

	status = base.GAME(cont)

	if status == "DONE":
		name = base.WORLD["PLAYERS"].get("1", None)

		if name != None:
			plr = base.PLAYER_CLASSES.get(name, None)
			if plr != None and plr.data["HEALTH"] <= 0:
				logic.globalDict["PROFILES"][base.CURRENT["Profile"]] = settings.json.loads(CHKPNT)
				world.openBlend("RESUME")


# Teleport
def TP_COLCB(OBJ):
	pass

def TELEPORT(cont):

	owner = cont.owner
	scene = owner.scene

	if "GFX" not in owner:
		owner.setVisible(False, False)
		if "GFX_Teleport" not in scene.objectsInactive:
			return
		owner["ANIM"] = 0
		owner["COLLIDE"] = []
		owner["GFX"] = scene.addObject("GFX_Teleport", owner, 0)
		owner["GFX"].setParent(owner)
		owner["GFX"].color = owner.color
		owner["HALO"] = owner.scene.addObject("GFX_Halo", owner, 0)
		owner["HALO"].setParent(owner)
		owner["HALO"].color = (owner.color[0], owner.color[1], owner.color[2], 0.5)
		owner["HALO"].localScale = (1.5, 1.5, 1.5)
		owner["HALO"]["LOCAL"] = True
		owner["HALO"]["AXIS"] = None

		owner.collisionCallbacks.append(TP_COLCB)

	name = owner.get("OBJECT", "")

	if "CAMERA" in owner:
		del owner["CAMERA"]

	for cls in owner["COLLIDE"]:
		if keymap.BINDS["ACTIVATE"].tap() == True:
			if name in scene.objects:
				target = scene.objects[name]
				cls.teleportTo(target.worldPosition.copy(), target.worldOrientation.copy())

	if len(owner["COLLIDE"]) > 0:
		if owner["ANIM"] == 0:
			if owner["GFX"].isPlayingAction(0) == False:
				owner["GFX"].playAction("GFX_Teleport", 0, 20)
				owner["ANIM"] = 1

	elif owner["ANIM"] == 1:
		if owner["GFX"].isPlayingAction(0) == False:
			owner["GFX"].playAction("GFX_Teleport", 20, 0)
			owner["ANIM"] = 0

	owner["COLLIDE"] = []


# Apply Force When Stepped
def JUMPPAD(cont):

	owner = cont.owner

	plr = owner.get("RAYFOOT", None)

	force = [
		owner.get("X", 0),
		owner.get("Y", 0),
		owner.get("Z", 0)]

	if plr != None:
		root = plr.objects.get("Root", None)
		if root != None:
			plr.jump_state = "JUMP"
			root.worldLinearVelocity = owner.worldOrientation*plr.createVector(vec=force)

	owner["RAYFOOT"] = None


# Simple World Door
def DOOR(cont):

	owner = cont.owner

	ray = owner.get("RAYCAST", None)
	cls = None

	if  ray != None:
		if keymap.BINDS["ACTIVATE"].tap():
			cls = ray

	door = owner.get("OBJECT", owner.name)

	if cls != None:
		gd = logic.globalDict
		scn = owner.get("SCENE", None)
		map = owner.get("MAP", "")+".blend"
		if map in gd["BLENDS"]:
			world.sendObjects(map, door, [cls])
			world.openBlend(map, scn)
			owner["MAP"] = ""

	if "CAMERA" in owner:
		del owner["CAMERA"]

	owner["RAYCAST"] = None

	world.loadObjects(owner.name, owner)


# Simple World Zone
def ZONE(cont):

	owner = cont.owner

	cls = None

	if "COLLIDE" not in owner:
		owner["COLLIDE"] = []
		owner["FAILS"] = []
		owner["ZONE"] = False
		owner["TIMER"] = 0

	for hit in owner["COLLIDE"]:
		if hit.PORTAL == True:
			vehicle = hit.data.get("PORTAL", None)
			if vehicle == True and owner.get("VEHICLE", True) == False:
				vehicle = False
			if vehicle in [None, True]:
				cls = hit

	if owner["TIMER"] > 120:
		owner["TIMER"] = 200
		owner.color = (0, 1, 0, 0.5)
	else:
		owner["TIMER"] += 1
		owner.color = (1, 0, 0, 0.5)

	door = owner.get("OBJECT", owner.name)

	if cls != None:
		if owner["TIMER"] == 200:
			gd = logic.globalDict
			scn = owner.get("SCENE", None)
			map = owner.get("MAP", "")+".blend"
			if map in gd["BLENDS"]:
				world.sendObjects(map, door, [cls], zone=owner)
				world.openBlend(map, scn)
				owner["MAP"] = ""
		else:
			owner["TIMER"] = 0

	for prop in ["CAMERA", "GROUND"]:
		if prop in owner:
			del owner[prop]

	owner["COLLIDE"] = []

	world.loadObjects(owner.name, owner)

# Is Near
def NEAR(cont):

	owner = cont.owner

	dist = owner.getDistanceTo(owner.scene.active_camera)

	if owner.get("RANGE", 0) > dist:
		for a in cont.actuators:
			cont.activate(a)
	else:
		for a in cont.actuators:
			cont.deactivate(a)


# Scale and Color Over Time
def SMOKE(cont):

	owner = cont.owner

	s = owner.localScale
	r = owner["SCALE"]/owner["TIME"]
	x = owner["FRAME"]/owner["TIME"]

	owner.localScale = (s[0]+r, s[1]+r, s[2]+r)
	owner.color[0] = 1-x

	if "MOVE" in owner:
		owner.worldPosition += owner["MOVE"]

	if owner["FRAME"] > owner["TIME"]:
		owner.endObject()

	owner["FRAME"] += 1


# Define Floating UI Elements
def FACEME(cont):

	owner = cont.owner
	scene = owner.scene

	camera = scene.active_camera

	VECT = (0,0,1)

	AXIS = owner.get("AXIS", None)
	LOCAL = owner.get("LOCAL", False)

	if AXIS == None:
		if LOCAL == True:
			owner.alignAxisToVect(owner.getVectTo(camera)[1], 2, 1.0)
		else:
			owner.worldOrientation = camera.worldOrientation

	elif AXIS == "Z":

		owner.alignAxisToVect(owner.getVectTo(camera)[1], 2, 1.0)

		if LOCAL == True and owner.parent != None:
			VECT = owner.parent.getAxisVect( (0,0,1) )

		owner.alignAxisToVect(VECT, 1, 1.0)

	elif AXIS == "Y":

		owner.alignAxisToVect(owner.getVectTo(camera)[1], 2, 1.0)

		if owner.parent != None:
			VECT = owner.parent.getAxisVect( (0,1,0) )

		owner.alignAxisToVect(VECT, 1, 1.0)


# Random Scale
def SCALE_RAND(cont):

	owner = cont.owner

	R = logic.getRandomFloat()

	X = owner.get("Xfac", None)
	Y = owner.get("Yfac", None)
	Z = owner.get("Zfac", None)
	E = owner.get("Efac", None)

	SIZE = owner.get("SIZE", None)

	if SIZE == None:
		if E == None:
			owner["SIZE"] = 1.0
		else:
			owner["SIZE"] = owner.energy
		return

	SPD = owner.get("SPEED", 1)

	if SPD >= 2:
		owner["RAND_LIST"] = owner.get("RAND_LIST", [1.0]*SPD)
		owner["RAND_LIST"].insert(0, R)
		owner["RAND_LIST"].pop()

		R = 0
		for i in owner["RAND_LIST"]:
			R += i
		R = R/SPD

	if X != None:
		owner.localScale[0] = ((R*X) + (1-X))*SIZE
	if Y != None:
		owner.localScale[1] = ((R*Y) + (1-Y))*SIZE
	if Z != None:
		owner.localScale[2] = ((R*Z) + (1-Z))*SIZE
	if E != None:
		R = R+(R/2)
		owner.energy = ((R*E) + (1-E))*SIZE


# Define Sky Tracking Functions
def SKY(cont):

	owner = cont.owner
	scene = owner.scene

	owner.worldPosition[0] = scene.active_camera.worldPosition[0]
	owner.worldPosition[1] = scene.active_camera.worldPosition[1]


# Define Shadow Tracking Functions
def SUN(cont):

	owner = cont.owner
	scene = owner.scene

	Z = owner.get("Z", None)

	if viewport.VIEWCLASS != None and scene.active_camera == viewport.getObject("Camera"):
		wp = viewport.VIEWCLASS.getWorldPosition()
	else:
		wp = scene.active_camera.worldPosition

	if Z == False or Z == None:
		owner.worldPosition[0] = wp[0]
		owner.worldPosition[1] = wp[1]

	if Z == True or Z == None:
		owner.worldPosition[2] = wp[2]


# Grass Builder
def GRASS(cont):

	owner = cont.owner
	scene = owner.scene

	destr = owner.get("END", False)
	grass = owner.get("OBJECT", "Grass")
	upnrm = owner.get("AXIS", 1)
	rtfac = owner.get("RAND", 1.0)
	matid = owner.get("MATID", None)

	if destr == None:
		return

	mesh = owner.meshes[0]

	if matid == None:
		owner["MATID"] = 0
		for id in range(len(mesh.materials)):
			if mesh.getMaterialName(id) == "MAGrass":
				owner["MATID"] = id
		matid = owner["MATID"]

	vlen = mesh.getVertexArrayLength(matid)

	for vid in range(vlen):
		vertex = mesh.getVertex(matid, vid)
		rotate = [0,0,0]
		rotate[upnrm] = logic.getRandomFloat()*3*rtfac

		obj = scene.addObject(grass, owner, 0)
		obj.worldPosition = vertex.XYZ
		obj.alignAxisToVect(vertex.normal, upnrm, 1.0)
		obj.applyRotation(rotate, True)
		if owner.parent != None:
			obj.setParent(owner.parent, False, False)

	if destr == True:
		owner.endObject()
	else:
		owner["END"] = None


# Tree of Lods
def TREELOD(cont):

	owner = cont.owner
	scene = owner.scene

	name = owner.get("OBJECT", owner.name.split(".")[0])
	dcdb = owner.get("DBLIST", [])
	objs = owner.get("OBJECTS", [])
	last = owner.get("OLDOBJ", None)
	tree = owner.get("KDTREE", None)

	if tree == None:
		for child in owner.children:
			rf = logic.getRandomFloat
			wp = child.worldPosition+base.ORIGIN_OFFSET+mathutils.Vector(((rf()-0.5)*8,(rf()-0.5)*8,0))
			wo = child.worldOrientation* mathutils.Euler((0,0,rf()*6)).to_matrix()
			ws = mathutils.Vector((1,1,1))*((rf()*0.6)+0.7)
			dcdb.append([wp, wo, ws, None])
			child.endObject()

		tree = mathutils.kdtree.KDTree(len(dcdb))
		for i in range(len(dcdb)):
			tree.insert(dcdb[i][0], i)

		tree.balance()

		owner["DBLIST"] = dcdb
		owner["KDTREE"] = tree

		n = owner.get("N", 100)
		if n >= len(dcdb):
			n = len(dcdb)
		for i in range(n):
			obj = scene.addObject(name, owner, 0)
			obj.setParent(owner, False, False)
			objs.append(obj)

		owner["OBJECTS"] = objs

	if viewport.VIEWCLASS == None:
		camobj = scene.active_camera
	else:
		camobj = viewport.getObject("Root")

	of = base.ORIGIN_OFFSET
	co = camobj.worldPosition+of

	if owner.get("CO_T", None) == None:
		owner["CO_T"] = co
	elif (co-owner["CO_T"]).length < owner.get("D", 2):
		return
	else:
		owner["CO_T"] = co

	near = tree.find_n(co, len(objs))
	pool = []

	for kd in near:
		pnt, id, dist = kd
		pool.append(id)

	owner["OLDOBJ"] = pool

	if last != None:
		orph = list( set(last).difference(set(pool)) )

	for i in range(len(near)):
		pnt, id, dist = near[i]
		wp, wo, ws, ob = dcdb[id]

		if ob == None:
			if last == None:
				ob = objs[i]
			else:
				old = orph.pop()
				ob = dcdb[old][3]
				dcdb[old][3] = None

			ob.worldPosition = wp-of
			ob.worldOrientation = wo
			ob.localScale = ws
			dcdb[id][3] = ob


# Light Lods
LIGHTBOX = {}
def LIGHTLOD(cont):
	global LIGHTBOX
	owner = cont.owner
	scene = owner.scene

	name = owner.get("NAME", owner.name.split(".")[0])
	z_sc = owner.get("Z_SC", 1.0)
	zoff = owner.get("Z", 0)
	nlgt = owner.get("LIGHTS", None)

	box = LIGHTBOX.get(name, [])

	if nlgt == None:
		for child in owner.children:
			wp = child.worldPosition+base.ORIGIN_OFFSET
			wo = child.worldOrientation.copy()
			dc = {"Z_SC":z_sc, "Z":zoff, "D_SC":1.0}
			if owner.get("color", False) == True:
				dc["color"] = (owner.color[0], owner.color[1], owner.color[2])
			for key in child.getPropertyNames():
				if key == "Efac":
					dc["BUFFER"] = [1.0]*int(child.get("SPEED", 1))
				if key == "color":
					dc["color"] = (child.color[0], child.color[1], child.color[2])
				else:
					dc[key] = child[key]
			wp[2] *= dc["Z_SC"]
			box.append([wp, wo, owner, dc])
			if owner.get("CHILD", False) == False:
				child.endObject()

		LIGHTBOX[name] = box
		owner["LIGHTS"] = []

	if owner.name in scene.objectsInactive:
		return

	if nlgt == None:
		nlgt = []
		for obj in scene.objects:
			if obj.parent == None:
				split = obj.name.split(".")
				if len(split) == 3 and split[0] == name and split[1] == "Light":
					nlgt.append(obj)
					for i in ["energy", "distance", "spotsize", "spotblend", "color"]:
						owner[i] = owner.get(i, getattr(obj, i, None))

		owner["NAME"] = name
		owner["LIGHTS"] = nlgt

	if viewport.VIEWCLASS == None:
		camobj = scene.active_camera
	else:
		camobj = viewport.getObject("Root")

	co = camobj.worldPosition+base.ORIGIN_OFFSET

	if owner.get("CO", None) == None:
		owner["CO"] = co
	elif (co-owner["CO"]).length < owner.get("D", 2):
		return
	else:
		owner["CO"] = co

	for i in box.copy():
		if i[2].invalid == True:
			box.remove(i)

	box.sort(key=lambda x: (x[0]-mathutils.Vector((co[0],co[1],co[2]*x[3]["Z_SC"]))).length*x[3]["D_SC"] )

	for i in range(len(nlgt)):
		if i >= len(box):
			nlgt[i].visible = False
			continue

		nlgt[i].visible = True
		dc = box[i][3]
		wp = box[i][0].copy()
		wo = box[i][1].copy()
		wp[2] *= 1/dc["Z_SC"]
		wp[2] += dc["Z"]
		nlgt[i].worldPosition = wp-base.ORIGIN_OFFSET
		nlgt[i].worldOrientation = wo

		a = "energy"
		v = dc.get(a, owner.get(a, None))
		if v != None and "BUFFER" in dc:
			dc["BUFFER"].insert(0, logic.getRandomFloat())
			dc["BUFFER"].pop()
			R = 0
			for rnd in dc["BUFFER"]:
				R += rnd
			R = R/len(dc["BUFFER"])

			E = dc["Efac"]
			R = R+(R/2)
			v = ((R*E)+(1-E))*v

		if v != None:
			setattr(nlgt[i], a, v)

		for a in ["distance", "spotsize", "spotblend", "color"]:
			v = dc.get(a, owner.get(a, None))
			if v != None:
				setattr(nlgt[i], a, v)


# Define Camera Path
def CAMNODE(cont):

	owner = cont.owner
	scene = owner.scene
	mesh = owner.meshes[0]

	matid = owner.get("MATID", None)

	if matid == None: #or type(matid) == str:
		owner["MATID"] = 0
		name = "CamPath"
		if type(matid) == str:
			name = matid
		for id in range(len(mesh.materials)):
			if mesh.getMaterialName(id) == "MA"+name:
				owner["MATID"] = id
		matid = owner["MATID"]

	tree = owner.get("_KD_TREE", None)

	if tree == None:
		vlen = mesh.getVertexArrayLength(matid)
		owner["_KD_TREE"] = mathutils.kdtree.KDTree(vlen)
		tree = owner["_KD_TREE"]

		for vid in range(vlen):
			vertex = mesh.getVertex(matid, vid)
			vpos = owner.worldOrientation*vertex.XYZ
			vpos = owner.worldPosition+vpos
			tree.insert(list(vpos), vid)
			print(vpos)

		tree.balance()

	owner["CAMNODE"] = True

	for prop in ["CAMERA", "GROUND"]:
		if prop in owner:
			del owner[prop]


# Align to Camera Path
def CAMPATH(cont):
	if viewport.VIEWCLASS == None:
		return

	camobj = viewport.getObject("Root")
	vec = None
	rayto = camobj.worldPosition-camobj.getAxisVect((0,0,1))

	rayOBJ, rayPNT, rayNRM = camobj.rayCast(rayto, None, 100, "CAMNODE", 1, 1, 0)

	if rayOBJ != None:
		state = rayOBJ.get("TYPE", None)
		if state == "RADIUS":
			axis = rayOBJ.get("AXIS", 1)
			vec = camobj.worldPosition-rayOBJ.worldPosition
			vec.normalize()
			vec = camobj.worldOrientation.inverted()*vec
			vec[2] = 0
			vec = camobj.worldOrientation*vec
			if abs(axis) == 0:
				z = 3.1415/2
				if axis < 0:
					z = -z
				vec.rotate(mathutils.Euler((0,0,z)))
		else:
			points = rayOBJ["_KD_TREE"].find_n(camobj.worldPosition, 2)
			vec = points[1][0]-points[0][0]
			vec.normalize()
			if camobj.getAxisVect((0,1,0)).dot(vec) < 0:
				if camobj.getAxisVect((0,1,0)).dot(-vec) > 0:
					vec = -vec

	if vec != None:
		viewport.VIEWCLASS.track = vec


# Set Realtime Cubemap Origin
def REFL(cont):

	owner = cont.owner

	if base.config.UPBGE_FIX == True:

		cube = owner.meshes[0].materials[0].textures[0]

		if cube.renderer != None:
			cube.renderer.autoUpdate = False
			if owner.get("CLIP_START", None):
				cube.renderer.clipStart = owner["CLIP_START"]
			cube.renderer.viewpointObject = owner
			cube.renderer.update()

	owner.setVisible(False, True)


# Define Texture UV Panning Functions
def UVT(cont):

	owner = cont.owner
	scene = owner.scene

	mesh = owner.meshes[0]

	if owner.get("MATID", None) == None:
		owner["MATID"] = 0
		for id in range(len(mesh.materials)):
			if mesh.getMaterialName(id) == "MAWater":
				owner["MATID"] = id

	TX = owner["TX"]*0.001
	TY = owner["TY"]*0.001

	owner["UVX"] += abs(TX)
	owner["UVY"] += abs(TY)

	if owner["UVX"] > 0.99:
		TX = -1
		owner["UVX"] = 0.0
	if owner["UVY"] > 0.99:
		TY = -1
		owner["UVY"] = 0.0

	scale = [owner.get("SCALEX", None), owner.get("SCALEY", None)]

	if scale[0] == "RESET":
		s = owner.worldScale
		print(s)
		scale[0] = s[0]
	if scale[1] == "RESET":
		s = owner.worldScale
		print(s)
		scale[1] = s[1]

	for v_id in range(mesh.getVertexArrayLength(owner["MATID"])):
		vertex = mesh.getVertex(owner["MATID"], v_id)

		if scale[0] != None:
			vertex.u  *= scale[0]
			vertex.u2 *= scale[0]
		vertex.u  += TX
		vertex.u2 += TX
		if scale[1] != None:
			vertex.v  *= scale[1]
			vertex.v2 *= scale[1]
		vertex.v  += TY
		vertex.v2 += TY

	owner["SCALEX"] = None
	owner["SCALEY"] = None



