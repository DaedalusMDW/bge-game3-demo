

## LEVEL MODULES ##

import math
import mathutils

from bge import logic, events, render, types, constraints

from game3 import GAMEPATH, keymap, settings, config, base, player, viewport, world


base.WORLD["CHECKPOINT_NAME"] = base.WORLD.get("CHECKPOINT_NAME", None)
CHKPNT = settings.json.dumps(base.PROFILE)


def INIT(cont):
	global CHKPNT

	owner = cont.owner
	scene = owner.scene

	status = base.GAME(cont)

	if status == "DONE":
		if owner.get("DIM", False) == True:
			for cls in logic.UPDATELIST:
				if hasattr(cls, "env_dim") == True:
					r = owner.color[0]
					g = owner.color[1]
					b = owner.color[2]
					cls.env_dim = (r+1, g+1, b+1, 1)

		name = base.WORLD["PLAYERS"].get("1", None)

		if name != None:
			plr = base.PLAYER_CLASSES.get(name, None)
			if plr != None and plr.data["HEALTH"] <= 0:
				logic.globalDict["PROFILES"][base.CURRENT["Profile"]] = settings.json.loads(CHKPNT)
				world.openBlend("RESUME")


def TP_COLCB(OBJ):
	pass


# Checkpoints
def CHECKPOINT_SAVE(cont):
	global CHKPNT
	owner = cont.owner
	name = owner.get("CHECKPOINT", cont.owner.name)

	if "COLLIDE" not in owner:
		owner["COLLIDE"] = []
		owner.collisionCallbacks.append(TP_COLCB)

	if name == base.WORLD["CHECKPOINT_NAME"] or "PLAYERS" not in base.WORLD:
		owner["COLLIDE"] = []
		return

	cur = base.WORLD["PLAYERS"].get("1", None)
	plr = None
	if cur != None:
		plr = base.PLAYER_CLASSES.get(cur, None)

	for cls in owner["COLLIDE"]:
		if plr != None and cls == plr:
			print("CHECKPOINT SAVE", name)
			check = []
			for cls in logic.UPDATELIST:
				if cls not in check:
					cls.doUpdate()
					check.append(cls)
			if logic.VIEWPORT != None:
				logic.VIEWPORT.doUpdate()
			base.WORLD["CHECKPOINT_NAME"] = name
			CHKPNT = settings.json.dumps(base.PROFILE)

	owner["COLLIDE"] = []


def CHECKPOINT_LOAD(cont):
	global CHKPNT
	owner = cont.owner
	if "COLLIDE" not in owner:
		owner["COLLIDE"] = []
		owner.collisionCallbacks.append(TP_COLCB)

	if "PLAYERS" not in base.WORLD:
		owner["COLLIDE"] = []
		return

	cur = base.WORLD["PLAYERS"].get("1", None)
	plr = None
	if cur != None:
		plr = base.PLAYER_CLASSES.get(cur, None)

	for cls in owner["COLLIDE"]:
		if plr != None and cls == plr:
			logic.globalDict["PROFILES"][base.CURRENT["Profile"]] = settings.json.loads(CHKPNT)
			world.openBlend("RESUME")

	owner["COLLIDE"] = []


# Raycast Clicker
def CLICKER(cont):

	owner = cont.owner

	owner["CLICK"] = False
	if  owner.get("RAYCAST", None) != None:
		if keymap.BINDS["ACTIVATE"].tap():
			owner["CLICK"] = True

	if base.LEVEL != None:
		chk = owner.get("SAVE", "")

		for prop in owner.getPropertyNames():
			if prop in chk:
				if "_LOAD" not in owner and ("_CLICKER_"+prop) in base.LEVEL:
					owner[prop] = base.LEVEL["_CLICKER_"+prop]
				else:
					base.LEVEL["_CLICKER_"+prop] = owner[prop]

		owner["_LOAD"] = True

	owner["RAYCAST"] = None


# Teleport
def TELEPORT(cont):

	owner = cont.owner
	scene = owner.scene

	if "GFX" not in owner:
		owner.visible = False
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

	if keymap.BINDS["ACTIVATE"].tap() == True and viewport.getController() in owner["COLLIDE"]:
		for cls in owner["COLLIDE"]:
			if name in scene.objects:
				target = scene.objects[name]
				cls.teleportTo(target.worldPosition.copy(), target.worldOrientation.copy())

	if len(owner["COLLIDE"]) > 0:
		owner["ANIM"] += 1
		if owner["ANIM"] > 20:
			owner["ANIM"] = 20
	else:
		owner["ANIM"] -= 1
		if owner["ANIM"] <= 0:
			owner["ANIM"] = -1

	dist = scene.active_camera.worldPosition-owner.worldPosition

	if dist.length > owner.get("DIST", 100):
		owner["GFX"].visible = False
		owner["HALO"].visible = False
	else:
		owner["GFX"].visible = True
		owner["HALO"].visible = True

	if owner["ANIM"] >= 0 and owner["GFX"].visible == True:
		owner["GFX"].playAction("GFX_Teleport", -5, 25, 0, 0, 5, logic.KX_ACTION_MODE_LOOP)
		owner["GFX"].setActionFrame(owner["ANIM"], 0)
	else:
		owner["GFX"].stopAction(0)

	owner["COLLIDE"] = []


# Apply Force When Stepped
def JUMPPAD(cont):

	owner = cont.owner

	plr = owner.get("RAYFOOT", None)

	x = owner.get("X", 0)
	y = owner.get("Y", 0)
	z = owner.get("Z", 0)

	vec = mathutils.Vector((x,y,z))

	if plr != None:
		root = plr.objects.get("Root", None)
		if root != None:
			plr.jump_state = "JUMP"
			root.worldLinearVelocity = owner.worldOrientation*vec

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

	cur = None
	plr = None
	if "PLAYERS" in base.WORLD:
		cur = base.WORLD["PLAYERS"].get("1", None)
		plr = None
		if cur != None:
			plr = base.PLAYER_CLASSES.get(cur, None)

	for hit in owner["COLLIDE"]:
		if getattr(hit, "PORTAL", None) == True and plr != None:
			if hit == plr:
				cls = hit
			elif owner.get("VEHICLE", True) == True:
				if plr in hit.getChildren():
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
	if "RC" not in owner:
		c = round(logic.getRandomFloat(), 2)
		owner.color[1] = c
		owner["RC"] = c

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
	camera = scene.active_camera

	vec = owner.worldPosition-camera.worldPosition

	owner.worldPosition[0] = camera.worldPosition[0]
	owner.worldPosition[1] = camera.worldPosition[1]


# Define Shadow Tracking Functions
def SUN(cont):

	owner = cont.owner
	scene = owner.scene

	Z = owner.get("Z", None)
	D = owner.get("D", 8)

	if viewport.VIEWCLASS != None and scene.active_camera == viewport.getObject("Camera"):
		wp = viewport.VIEWCLASS.getWorldPosition()
	else:
		wp = scene.active_camera.worldPosition

	vec = wp-owner.worldPosition

	if Z == False or Z == None:
		if abs(vec[0]) > D or abs(vec[1]) > D:
			owner.worldPosition[0] = wp[0]
			owner.worldPosition[1] = wp[1]

	if Z == True or Z == None:
		if abs(vec[2]) > D:
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
			for obj in [owner, child]:
				for key in obj.getPropertyNames():
					if key == "Efac":
						dc["BUFFER"] = [1.0]*int(obj.get("SPEED", 1))
					if key == "color":
						dc["color"] = (obj.color[0], obj.color[1], obj.color[2])
					else:
						dc[key] = obj[key]
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
					for i in ["energy", "distance", "color", "spotblend", "spotsize"]:
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
	#elif (co-owner["CO"]).length < owner.get("D", 2):
	#	return
	else:
		owner["CO"] = co

	for i in box.copy():
		if i[2].invalid == True:
			box.remove(i)

	box.sort(key=lambda x: (x[0]-mathutils.Vector((co[0],co[1],co[2]*x[3]["Z_SC"]))).length*x[3]["D_SC"] )

	for i in range(len(nlgt)):
		obj = nlgt[i]
		if i >= len(box):
			obj.visible = False
			continue

		obj.visible = True
		dc = box[i][3]
		wp = box[i][0].copy()
		wo = box[i][1].copy()
		wp[2] *= 1/dc["Z_SC"]
		wp[2] += dc["Z"]
		obj.worldPosition = wp-base.ORIGIN_OFFSET
		obj.worldOrientation = wo

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
			setattr(obj, a, v)

		if getattr(obj, "useShadow", False) == False:
			a = "spotsize"
			v = dc.get(a, owner.get(a, None))
			if v != None:
				setattr(obj, a, v)

		for a in ["distance", "color", "spotblend"]:
			v = dc.get(a, owner.get(a, None))
			if v != None:
				setattr(obj, a, v)


# Copy Armature to Physics (UPBGE020 only)
def RAGDOLL(cont):
	owner = cont.owner
	if "DESTROY" in owner:
		owner.endObject()
		return

	if owner.get("Class", None) == None:
		return

	plr = owner["Class"]
	if owner.isSuspendDynamics == False and plr.motion["World"].length > 0.1:
		print("RD IMP", plr.motion["World"])
		owner.worldLinearVelocity = plr.motion["World"]
		plr.motion["World"] = mathutils.Vector((0,0,0))
		plr.motion["Local"] = mathutils.Vector((0,0,0))


# Apply Constraint (UPBGE020 only)
def ADDCONSTRAINT(cont):
	owner = cont.owner

	if "_CONSTRAINT" in owner:
		if "DESTROY" in owner:
			constraints.removeConstraint(owner["_CONSTRAINT"].constraint_id)
			del owner["_CONSTRAINT"]
			owner["POSE_CON"].active = False
			owner["POSE_CON"].target = owner.scene.objectsInactive[owner.name]
			#owner.visible = True
			owner.endObject()
			return

		if "POSE_ORI" in owner:
			owner.worldOrientation = owner["POSE_ORI"]
			del owner["POSE_ORI"]
		if "POSE_POS" in owner:
			owner.worldPosition = owner["POSE_POS"]
			del owner["POSE_POS"]
		if "POSE_CON" in owner:
			if owner["POSE_CON"].active != True:
				owner["POSE_CON"].active = True
			#del owner["POSE_CON"]
		return

	if "DESTROY" in owner:
		return

	parent = owner.get("TARGET", None)
	ctype = owner.get("TYPE", "6DOF")
	joint = owner.children.get(owner.name+".Joint")

	if parent == None:
		#owner.endObject()
		return

	#owner.removeParent()
	for obj in [owner, parent]:
		obj.worldLinearVelocity = (0,0,0)
		obj.worldAngularVelocity = (0,0,0)
		obj.restoreDynamics()
		obj.enableRigidBody()

	objA = owner.getPhysicsId()
	objB = parent.getPhysicsId()
	ct = constraints.GENERIC_6DOF_CONSTRAINT
	if ctype == "HINGE":
		ct = constraints.LINEHINGE_CONSTRAINT
	if ctype == "BALL":
		ct = constraints.POINTTOPOINT_CONSTRAINT
	PX, PY, PZ = joint.localPosition
	AX, AY, AZ = joint.localOrientation.to_euler("XYZ")
	owner["_CONSTRAINT"] = constraints.createConstraint(objA, objB, ct, PX, PY, PZ, AX, AY, AZ, 128)

	pos = ["minPX", "maxPX", "minPY", "maxPY", "minPZ", "maxPZ"]
	rot = ["minAX", "maxAX", "minAY", "maxAY", "minAZ", "maxAZ"]

	for prop in pos+rot:
		joint[prop] = joint.get(prop, 0)

	if ctype == "BALL":
		return

	if ctype == "HINGE":
		min = math.radians(joint["minAX"])
		max = math.radians(joint["maxAX"])
		owner["_CONSTRAINT"].setParam(3, min, max)
		return

	param = ["AX", "AY", "AZ"]
	if ctype == "6DOF":
		param = param+["PX", "PY", "PZ"]

	for prop in param:
		axis = ["X", "Y", "Z"].index(prop[1])
		if prop[0] == "A":
			axis += 3
		min = math.radians(joint["min"+prop])
		max = math.radians(joint["max"+prop])
		owner["_CONSTRAINT"].setParam(axis, min, max)


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


